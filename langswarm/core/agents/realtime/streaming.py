"""
LangSwarm V2 Streaming Response Manager

Advanced streaming response management for real-time agent interactions
with chunk processing, response aggregation, and streaming optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from datetime import datetime
import uuid

from .interfaces import (
    StreamingChunk, RealtimeMessage, RealtimeEvent, RealtimeConfiguration,
    StreamingType, RealtimeMessageType, StreamingError
)


class StreamingResponseManager:
    """
    Manager for streaming response processing and delivery.
    
    Handles chunked response streaming, aggregation, and optimization
    for real-time agent interactions.
    """
    
    def __init__(self, config: RealtimeConfiguration):
        """
        Initialize streaming response manager.
        
        Args:
            config: Real-time configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Streaming state
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        self._chunk_processors: Dict[str, 'ChunkProcessor'] = {}
        self._response_aggregators: Dict[str, 'ResponseAggregator'] = {}
        
        # Stream management
        self._stream_counter = 0
        self._max_concurrent_streams = 100
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "total_streams": 0,
            "active_streams": 0,
            "chunks_processed": 0,
            "responses_aggregated": 0,
            "average_stream_duration": 0.0,
            "total_bytes_streamed": 0
        }
        
        self._logger.debug("Streaming response manager initialized")
    
    async def start(self) -> None:
        """Start streaming response manager"""
        try:
            self._logger.info("Starting streaming response manager")
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self._logger.info("Streaming response manager started")
            
        except Exception as e:
            self._logger.error(f"Failed to start streaming response manager: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop streaming response manager"""
        try:
            self._logger.info("Stopping streaming response manager")
            
            # Stop all active streams
            for stream_id in list(self._active_streams.keys()):
                await self.stop_stream(stream_id)
            
            # Stop background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self._logger.info("Streaming response manager stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping streaming response manager: {e}")
    
    async def create_stream(self, message: RealtimeMessage, agent_id: str) -> str:
        """
        Create new streaming response.
        
        Args:
            message: Original message to stream response for
            agent_id: Agent providing the response
            
        Returns:
            Stream ID for the created stream
        """
        try:
            if len(self._active_streams) >= self._max_concurrent_streams:
                raise StreamingError("Maximum concurrent streams reached")
            
            stream_id = str(uuid.uuid4())
            self._stream_counter += 1
            
            # Create stream metadata
            stream_info = {
                "stream_id": stream_id,
                "message_id": message.id,
                "agent_id": agent_id,
                "created_at": datetime.utcnow(),
                "status": "active",
                "chunk_count": 0,
                "total_bytes": 0,
                "last_activity": datetime.utcnow()
            }
            
            self._active_streams[stream_id] = stream_info
            
            # Create chunk processor for this stream
            processor = ChunkProcessor(stream_id, self.config)
            self._chunk_processors[stream_id] = processor
            
            # Create response aggregator
            aggregator = ResponseAggregator(stream_id, self.config)
            self._response_aggregators[stream_id] = aggregator
            
            # Update statistics
            self._stats["total_streams"] += 1
            self._stats["active_streams"] = len(self._active_streams)
            
            self._logger.info(f"Created streaming response: {stream_id}")
            return stream_id
            
        except Exception as e:
            self._logger.error(f"Failed to create stream for message {message.id}: {e}")
            raise StreamingError(f"Stream creation failed: {e}")
    
    async def add_chunk(self, stream_id: str, content: str, chunk_type: StreamingType = StreamingType.TEXT_DELTA, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add chunk to streaming response.
        
        Args:
            stream_id: Stream identifier
            content: Chunk content
            chunk_type: Type of streaming chunk
            metadata: Optional chunk metadata
            
        Returns:
            True if chunk added successfully
        """
        try:
            if stream_id not in self._active_streams:
                self._logger.warning(f"Stream {stream_id} not found")
                return False
            
            stream_info = self._active_streams[stream_id]
            
            # Create chunk
            chunk = StreamingChunk(
                type=chunk_type,
                content=content,
                index=stream_info["chunk_count"],
                metadata=metadata or {}
            )
            
            # Process chunk
            processor = self._chunk_processors[stream_id]
            processed_chunk = await processor.process_chunk(chunk)
            
            # Add to aggregator
            aggregator = self._response_aggregators[stream_id]
            await aggregator.add_chunk(processed_chunk)
            
            # Update stream info
            stream_info["chunk_count"] += 1
            stream_info["total_bytes"] += len(content.encode('utf-8'))
            stream_info["last_activity"] = datetime.utcnow()
            
            # Update statistics
            self._stats["chunks_processed"] += 1
            self._stats["total_bytes_streamed"] += len(content.encode('utf-8'))
            
            self._logger.debug(f"Added chunk to stream {stream_id}: {len(content)} bytes")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to add chunk to stream {stream_id}: {e}")
            return False
    
    async def complete_stream(self, stream_id: str) -> Optional[RealtimeMessage]:
        """
        Complete streaming response and get final aggregated message.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Final aggregated message or None if failed
        """
        try:
            if stream_id not in self._active_streams:
                self._logger.warning(f"Stream {stream_id} not found")
                return None
            
            stream_info = self._active_streams[stream_id]
            aggregator = self._response_aggregators[stream_id]
            
            # Get final aggregated response
            final_message = await aggregator.get_final_response()
            
            # Mark stream as completed
            stream_info["status"] = "completed"
            stream_info["completed_at"] = datetime.utcnow()
            
            # Calculate stream duration
            duration = (stream_info["completed_at"] - stream_info["created_at"]).total_seconds()
            
            # Update statistics
            self._stats["responses_aggregated"] += 1
            current_avg = self._stats["average_stream_duration"]
            total_completed = self._stats["responses_aggregated"]
            self._stats["average_stream_duration"] = ((current_avg * (total_completed - 1)) + duration) / total_completed
            
            self._logger.info(f"Completed stream {stream_id}: {stream_info['chunk_count']} chunks, {duration:.2f}s")
            
            # Schedule cleanup
            asyncio.create_task(self._cleanup_stream(stream_id, delay=60))  # Cleanup after 1 minute
            
            return final_message
            
        except Exception as e:
            self._logger.error(f"Failed to complete stream {stream_id}: {e}")
            return None
    
    async def stop_stream(self, stream_id: str) -> bool:
        """
        Stop streaming response.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            True if stopped successfully
        """
        try:
            if stream_id not in self._active_streams:
                return False
            
            stream_info = self._active_streams[stream_id]
            stream_info["status"] = "stopped"
            stream_info["stopped_at"] = datetime.utcnow()
            
            # Cleanup resources
            await self._cleanup_stream(stream_id)
            
            self._logger.info(f"Stopped stream: {stream_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to stop stream {stream_id}: {e}")
            return False
    
    async def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of streaming response.
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Stream status information or None if not found
        """
        if stream_id in self._active_streams:
            stream_info = self._active_streams[stream_id].copy()
            
            # Add current chunk processor and aggregator status
            if stream_id in self._chunk_processors:
                stream_info["processor_stats"] = await self._chunk_processors[stream_id].get_statistics()
            
            if stream_id in self._response_aggregators:
                stream_info["aggregator_stats"] = await self._response_aggregators[stream_id].get_statistics()
            
            return stream_info
        
        return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get streaming manager statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            **self._stats,
            "max_concurrent_streams": self._max_concurrent_streams,
            "stream_details": {
                stream_id: stream_info
                for stream_id, stream_info in self._active_streams.items()
            }
        }
    
    async def _cleanup_stream(self, stream_id: str, delay: int = 0) -> None:
        """Cleanup stream resources"""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Remove from active streams
            if stream_id in self._active_streams:
                del self._active_streams[stream_id]
            
            # Cleanup processors
            if stream_id in self._chunk_processors:
                del self._chunk_processors[stream_id]
            
            if stream_id in self._response_aggregators:
                del self._response_aggregators[stream_id]
            
            # Update statistics
            self._stats["active_streams"] = len(self._active_streams)
            
            self._logger.debug(f"Cleaned up stream: {stream_id}")
            
        except Exception as e:
            self._logger.error(f"Error cleaning up stream {stream_id}: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up inactive streams"""
        while True:
            try:
                current_time = datetime.utcnow()
                streams_to_cleanup = []
                
                for stream_id, stream_info in self._active_streams.items():
                    # Cleanup streams inactive for more than 5 minutes
                    last_activity = stream_info.get("last_activity", stream_info["created_at"])
                    if (current_time - last_activity).total_seconds() > 300:
                        streams_to_cleanup.append(stream_id)
                
                # Cleanup inactive streams
                for stream_id in streams_to_cleanup:
                    await self._cleanup_stream(stream_id)
                
                # Sleep for cleanup interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self) -> None:
        """Background task for monitoring stream health"""
        while True:
            try:
                # Log periodic statistics
                if len(self._active_streams) > 0:
                    self._logger.info(f"Streaming manager: {len(self._active_streams)} active streams")
                
                # Monitor resource usage
                total_memory = sum(
                    stream_info.get("total_bytes", 0)
                    for stream_info in self._active_streams.values()
                )
                
                if total_memory > 100 * 1024 * 1024:  # 100MB threshold
                    self._logger.warning(f"High memory usage in streaming: {total_memory / 1024 / 1024:.1f}MB")
                
                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)


class ChunkProcessor:
    """
    Processor for individual streaming chunks.
    
    Handles chunk validation, transformation, and optimization
    for streaming responses.
    """
    
    def __init__(self, stream_id: str, config: RealtimeConfiguration):
        """
        Initialize chunk processor.
        
        Args:
            stream_id: Stream identifier
            config: Real-time configuration
        """
        self.stream_id = stream_id
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{stream_id}")
        
        # Processing state
        self._chunks_processed = 0
        self._total_bytes = 0
        self._processing_time = 0.0
        
        # Processing options
        self._enable_compression = True
        self._enable_deduplication = True
        self._enable_optimization = True
    
    async def process_chunk(self, chunk: StreamingChunk) -> StreamingChunk:
        """
        Process streaming chunk.
        
        Args:
            chunk: Chunk to process
            
        Returns:
            Processed chunk
        """
        start_time = datetime.utcnow()
        
        try:
            processed_chunk = chunk
            
            # Apply processing steps
            if self._enable_optimization:
                processed_chunk = await self._optimize_chunk(processed_chunk)
            
            if self._enable_compression:
                processed_chunk = await self._compress_chunk(processed_chunk)
            
            if self._enable_deduplication:
                processed_chunk = await self._deduplicate_chunk(processed_chunk)
            
            # Update statistics
            self._chunks_processed += 1
            self._total_bytes += len(chunk.content.encode('utf-8'))
            self._processing_time += (datetime.utcnow() - start_time).total_seconds()
            
            return processed_chunk
            
        except Exception as e:
            self._logger.error(f"Failed to process chunk: {e}")
            return chunk  # Return original chunk on error
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get chunk processor statistics"""
        avg_processing_time = self._processing_time / max(self._chunks_processed, 1)
        
        return {
            "stream_id": self.stream_id,
            "chunks_processed": self._chunks_processed,
            "total_bytes": self._total_bytes,
            "processing_time": self._processing_time,
            "average_processing_time": avg_processing_time,
            "settings": {
                "compression": self._enable_compression,
                "deduplication": self._enable_deduplication,
                "optimization": self._enable_optimization
            }
        }
    
    async def _optimize_chunk(self, chunk: StreamingChunk) -> StreamingChunk:
        """Optimize chunk content"""
        # Placeholder for chunk optimization
        return chunk
    
    async def _compress_chunk(self, chunk: StreamingChunk) -> StreamingChunk:
        """Compress chunk content"""
        # Placeholder for chunk compression
        return chunk
    
    async def _deduplicate_chunk(self, chunk: StreamingChunk) -> StreamingChunk:
        """Remove duplicate content from chunk"""
        # Placeholder for chunk deduplication
        return chunk


class ResponseAggregator:
    """
    Aggregator for streaming response chunks.
    
    Combines streaming chunks into final coherent responses
    with proper formatting and structure.
    """
    
    def __init__(self, stream_id: str, config: RealtimeConfiguration):
        """
        Initialize response aggregator.
        
        Args:
            stream_id: Stream identifier
            config: Real-time configuration
        """
        self.stream_id = stream_id
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{stream_id}")
        
        # Aggregation state
        self._chunks: List[StreamingChunk] = []
        self._content_buffer = []
        self._metadata_buffer = {}
        
        # Statistics
        self._chunks_aggregated = 0
        self._total_content_length = 0
    
    async def add_chunk(self, chunk: StreamingChunk) -> None:
        """
        Add chunk to aggregation.
        
        Args:
            chunk: Streaming chunk to add
        """
        try:
            self._chunks.append(chunk)
            
            # Process chunk content based on type
            if chunk.type == StreamingType.TEXT_DELTA:
                self._content_buffer.append(chunk.content)
            elif chunk.type == StreamingType.COMPLETE:
                # Mark as final chunk
                chunk.is_final = True
            
            # Aggregate metadata
            self._metadata_buffer.update(chunk.metadata)
            
            # Update statistics
            self._chunks_aggregated += 1
            self._total_content_length += len(chunk.content)
            
        except Exception as e:
            self._logger.error(f"Failed to add chunk to aggregation: {e}")
    
    async def get_final_response(self) -> RealtimeMessage:
        """
        Get final aggregated response message.
        
        Returns:
            Final aggregated message
        """
        try:
            # Combine all content
            final_content = "".join(self._content_buffer)
            
            # Create final message
            final_message = RealtimeMessage(
                type=RealtimeMessageType.TEXT,
                content=final_content,
                metadata={
                    **self._metadata_buffer,
                    "stream_id": self.stream_id,
                    "chunk_count": len(self._chunks),
                    "aggregated_at": datetime.utcnow().isoformat()
                }
            )
            
            self._logger.debug(f"Aggregated {len(self._chunks)} chunks into final message")
            return final_message
            
        except Exception as e:
            self._logger.error(f"Failed to create final response: {e}")
            # Return empty message on error
            return RealtimeMessage(
                type=RealtimeMessageType.ERROR,
                content="Failed to aggregate response",
                metadata={"error": str(e), "stream_id": self.stream_id}
            )
    
    async def get_partial_response(self) -> RealtimeMessage:
        """
        Get partial aggregated response (work in progress).
        
        Returns:
            Partial aggregated message
        """
        try:
            # Combine content so far
            partial_content = "".join(self._content_buffer)
            
            partial_message = RealtimeMessage(
                type=RealtimeMessageType.TEXT,
                content=partial_content,
                metadata={
                    **self._metadata_buffer,
                    "stream_id": self.stream_id,
                    "chunk_count": len(self._chunks),
                    "is_partial": True,
                    "aggregated_at": datetime.utcnow().isoformat()
                }
            )
            
            return partial_message
            
        except Exception as e:
            self._logger.error(f"Failed to create partial response: {e}")
            return RealtimeMessage(
                type=RealtimeMessageType.ERROR,
                content="Failed to aggregate partial response",
                metadata={"error": str(e), "stream_id": self.stream_id}
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get response aggregator statistics"""
        return {
            "stream_id": self.stream_id,
            "chunks_aggregated": self._chunks_aggregated,
            "total_content_length": self._total_content_length,
            "content_buffer_size": len(self._content_buffer),
            "metadata_keys": len(self._metadata_buffer)
        }


# Factory functions
def create_streaming_manager(config: RealtimeConfiguration) -> StreamingResponseManager:
    """Create a new streaming response manager"""
    return StreamingResponseManager(config)


async def process_streaming_response(message: RealtimeMessage, agent_id: str, content_generator: AsyncIterator[str], manager: StreamingResponseManager) -> Optional[RealtimeMessage]:
    """
    Process a complete streaming response.
    
    Args:
        message: Original message
        agent_id: Agent providing response
        content_generator: Generator yielding content chunks
        manager: Streaming response manager
        
    Returns:
        Final aggregated response or None if failed
    """
    try:
        # Create stream
        stream_id = await manager.create_stream(message, agent_id)
        
        # Process chunks
        async for content in content_generator:
            await manager.add_chunk(stream_id, content)
        
        # Complete stream and get final response
        final_response = await manager.complete_stream(stream_id)
        return final_response
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to process streaming response: {e}")
        return None
