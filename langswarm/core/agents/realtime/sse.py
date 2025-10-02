"""
LangSwarm V2 Server-Sent Events Handler

Server-sent events (SSE) for real-time streaming of agent responses
with support for live response streaming and event broadcasting.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, AsyncIterator, Any, List
from datetime import datetime
import uuid

from .interfaces import (
    ISSEHandler, RealtimeEvent, StreamingChunk, RealtimeConfiguration,
    ConnectionStatus, EventType, StreamingType, StreamingError
)


class SSEHandler(ISSEHandler):
    """
    Server-Sent Events handler for real-time agent streaming.
    
    Provides one-way real-time communication from agents to clients
    with support for streaming responses, events, and status updates.
    """
    
    def __init__(self, agent_id: str, config: RealtimeConfiguration):
        """
        Initialize SSE handler.
        
        Args:
            agent_id: Agent identifier for this handler
            config: Real-time configuration
        """
        self.agent_id = agent_id
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Stream state
        self._active = False
        self._client_id: Optional[str] = None
        self._stream_id: Optional[str] = None
        
        # Event streaming
        self._event_queue = asyncio.Queue()
        self._chunk_queue = asyncio.Queue()
        
        # Background tasks
        self._stream_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "events_sent": 0,
            "chunks_sent": 0,
            "stream_start_time": None,
            "last_activity": None,
            "total_bytes_sent": 0
        }
        
        self._logger.debug(f"SSE handler initialized for agent: {agent_id}")
    
    @property
    def is_active(self) -> bool:
        """Check if SSE stream is active"""
        return self._active
    
    @property
    def client_id(self) -> Optional[str]:
        """Get connected client ID"""
        return self._client_id
    
    @property
    def stream_id(self) -> Optional[str]:
        """Get current stream ID"""
        return self._stream_id
    
    async def start_stream(self, agent_id: str) -> None:
        """
        Start SSE stream.
        
        Args:
            agent_id: Agent identifier to start stream for
        """
        if self._active:
            self._logger.warning("SSE stream already active")
            return
        
        try:
            self._logger.info(f"Starting SSE stream for agent: {agent_id}")
            
            self._active = True
            self._client_id = str(uuid.uuid4())
            self._stream_id = str(uuid.uuid4())
            self._stats["stream_start_time"] = datetime.utcnow()
            self._stats["last_activity"] = datetime.utcnow()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Send stream start event
            await self._send_stream_event("stream_start", {
                "agent_id": agent_id,
                "stream_id": self._stream_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self._logger.info(f"SSE stream started for agent: {agent_id}")
            
        except Exception as e:
            self._logger.error(f"Failed to start SSE stream for agent {agent_id}: {e}")
            self._active = False
            raise StreamingError(f"Failed to start SSE stream: {e}")
    
    async def stop_stream(self) -> None:
        """Stop SSE stream"""
        if not self._active:
            return
        
        try:
            self._logger.info("Stopping SSE stream")
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Send stream end event
            await self._send_stream_event("stream_end", {
                "stream_id": self._stream_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self._active = False
            self._client_id = None
            self._stream_id = None
            
            self._logger.info("SSE stream stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping SSE stream: {e}")
            self._active = False
    
    async def send_event(self, event: RealtimeEvent) -> bool:
        """
        Send event via SSE.
        
        Args:
            event: Real-time event to send
            
        Returns:
            True if event sent successfully
        """
        if not self._active:
            self._logger.warning("Cannot send event - SSE stream not active")
            return False
        
        try:
            # Add event to queue for streaming
            await self._event_queue.put(event)
            
            self._stats["events_sent"] += 1
            self._stats["last_activity"] = datetime.utcnow()
            
            self._logger.debug(f"Queued event for SSE stream: {event.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send event via SSE: {e}")
            return False
    
    async def send_chunk(self, chunk: StreamingChunk) -> bool:
        """
        Send streaming chunk via SSE.
        
        Args:
            chunk: Streaming chunk to send
            
        Returns:
            True if chunk sent successfully
        """
        if not self._active:
            self._logger.warning("Cannot send chunk - SSE stream not active")
            return False
        
        try:
            # Add chunk to queue for streaming
            await self._chunk_queue.put(chunk)
            
            self._stats["chunks_sent"] += 1
            self._stats["last_activity"] = datetime.utcnow()
            self._stats["total_bytes_sent"] += len(chunk.content.encode('utf-8'))
            
            self._logger.debug(f"Queued chunk for SSE stream: {chunk.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send chunk via SSE: {e}")
            return False
    
    async def stream_response(self, message_id: str, content_generator: AsyncIterator[str]) -> bool:
        """
        Stream a complete response via SSE.
        
        Args:
            message_id: Message identifier for the response
            content_generator: Async generator yielding content chunks
            
        Returns:
            True if streaming successful
        """
        if not self._active:
            self._logger.warning("Cannot stream response - SSE stream not active")
            return False
        
        try:
            # Send response start event
            start_event = RealtimeEvent(
                type=EventType.MESSAGE_START,
                data={"message_id": message_id, "timestamp": datetime.utcnow().isoformat()}
            )
            await self.send_event(start_event)
            
            # Stream content chunks
            chunk_index = 0
            async for content in content_generator:
                chunk = StreamingChunk(
                    type=StreamingType.TEXT_DELTA,
                    content=content,
                    index=chunk_index,
                    metadata={"message_id": message_id}
                )
                
                await self.send_chunk(chunk)
                chunk_index += 1
            
            # Send response end event
            end_chunk = StreamingChunk(
                type=StreamingType.COMPLETE,
                content="",
                index=chunk_index,
                is_final=True,
                metadata={"message_id": message_id}
            )
            await self.send_chunk(end_chunk)
            
            end_event = RealtimeEvent(
                type=EventType.MESSAGE_END,
                data={"message_id": message_id, "timestamp": datetime.utcnow().isoformat()}
            )
            await self.send_event(end_event)
            
            self._logger.info(f"Successfully streamed response for message: {message_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to stream response for message {message_id}: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get SSE handler statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            **self._stats,
            "agent_id": self.agent_id,
            "client_id": self._client_id,
            "stream_id": self._stream_id,
            "is_active": self._active,
            "queue_sizes": {
                "event_queue": self._event_queue.qsize(),
                "chunk_queue": self._chunk_queue.qsize()
            }
        }
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks for streaming and heartbeat"""
        # Start streaming task
        self._stream_task = asyncio.create_task(self._stream_loop())
        
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks"""
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
    
    async def _stream_loop(self) -> None:
        """Background task to stream events and chunks"""
        while self._active:
            try:
                # Check for events to stream
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                    await self._send_sse_event(event)
                except asyncio.TimeoutError:
                    pass
                
                # Check for chunks to stream
                try:
                    chunk = await asyncio.wait_for(self._chunk_queue.get(), timeout=0.1)
                    await self._send_sse_chunk(chunk)
                except asyncio.TimeoutError:
                    pass
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in stream loop: {e}")
                break
    
    async def _heartbeat_loop(self) -> None:
        """Background task to send heartbeat events"""
        while self._active:
            try:
                # Send heartbeat every interval
                await asyncio.sleep(self.config.heartbeat_interval)
                
                await self._send_stream_event("heartbeat", {
                    "timestamp": datetime.utcnow().isoformat(),
                    "stream_id": self._stream_id
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in heartbeat loop: {e}")
                break
    
    async def _send_sse_event(self, event: RealtimeEvent) -> None:
        """Send event via SSE protocol"""
        try:
            # Format as SSE event
            sse_data = f"event: {event.type.value}\n"
            sse_data += f"id: {event.id}\n"
            sse_data += f"data: {json.dumps(event.to_dict())}\n\n"
            
            # In real implementation, would send to SSE stream
            self._logger.debug(f"SSE Event: {event.type.value}")
            
        except Exception as e:
            self._logger.error(f"Failed to send SSE event: {e}")
    
    async def _send_sse_chunk(self, chunk: StreamingChunk) -> None:
        """Send chunk via SSE protocol"""
        try:
            # Format as SSE event
            sse_data = f"event: chunk\n"
            sse_data += f"id: {chunk.id}\n"
            sse_data += f"data: {json.dumps(chunk.to_dict())}\n\n"
            
            # In real implementation, would send to SSE stream
            self._logger.debug(f"SSE Chunk: {chunk.type.value}")
            
        except Exception as e:
            self._logger.error(f"Failed to send SSE chunk: {e}")
    
    async def _send_stream_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send stream control event"""
        try:
            sse_data = f"event: {event_type}\n"
            sse_data += f"data: {json.dumps(data)}\n\n"
            
            # In real implementation, would send to SSE stream
            self._logger.debug(f"SSE Stream Event: {event_type}")
            
        except Exception as e:
            self._logger.error(f"Failed to send stream event: {e}")


class SSEStream:
    """
    SSE stream manager for handling multiple client streams.
    
    Manages multiple SSE streams and provides routing and broadcasting
    capabilities for real-time events and chunks.
    """
    
    def __init__(self, config: RealtimeConfiguration):
        """
        Initialize SSE stream manager.
        
        Args:
            config: Real-time configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Stream management
        self._streams: Dict[str, SSEHandler] = {}
        self._active = False
        
        # Statistics
        self._stats = {
            "total_streams": 0,
            "active_streams": 0,
            "events_broadcast": 0,
            "chunks_broadcast": 0
        }
    
    async def start(self) -> bool:
        """
        Start SSE stream manager.
        
        Returns:
            True if started successfully
        """
        try:
            self._logger.info("Starting SSE stream manager")
            self._active = True
            self._logger.info("SSE stream manager started successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start SSE stream manager: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop SSE stream manager"""
        if not self._active:
            return
        
        try:
            self._logger.info("Stopping SSE stream manager")
            
            # Stop all streams
            for stream in list(self._streams.values()):
                await stream.stop_stream()
            
            self._active = False
            self._logger.info("SSE stream manager stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping SSE stream manager: {e}")
    
    def add_stream(self, agent_id: str, stream: SSEHandler) -> None:
        """Add SSE stream for agent"""
        self._streams[agent_id] = stream
        self._stats["total_streams"] += 1
        self._stats["active_streams"] = len(self._streams)
        self._logger.info(f"Added SSE stream for agent: {agent_id}")
    
    def remove_stream(self, agent_id: str) -> None:
        """Remove SSE stream for agent"""
        if agent_id in self._streams:
            del self._streams[agent_id]
            self._stats["active_streams"] = len(self._streams)
            self._logger.info(f"Removed SSE stream for agent: {agent_id}")
    
    async def broadcast_event(self, event: RealtimeEvent, agent_ids: Optional[List[str]] = None) -> int:
        """
        Broadcast event to multiple streams.
        
        Args:
            event: Event to broadcast
            agent_ids: List of agent IDs to broadcast to (None for all)
            
        Returns:
            Number of streams the event was sent to
        """
        targets = agent_ids or list(self._streams.keys())
        sent_count = 0
        
        for agent_id in targets:
            if agent_id in self._streams:
                try:
                    await self._streams[agent_id].send_event(event)
                    sent_count += 1
                except Exception as e:
                    self._logger.error(f"Failed to broadcast event to {agent_id}: {e}")
        
        self._stats["events_broadcast"] += sent_count
        return sent_count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get SSE stream manager statistics"""
        return {
            **self._stats,
            "is_active": self._active,
            "stream_details": {
                agent_id: await stream.get_statistics()
                for agent_id, stream in self._streams.items()
            }
        }


# Factory functions
def create_sse_handler(agent_id: str, config: RealtimeConfiguration) -> SSEHandler:
    """Create a new SSE handler"""
    return SSEHandler(agent_id, config)
