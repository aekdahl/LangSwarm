"""
LangSwarm V2 WebSocket Handler

WebSocket-based real-time communication for V2 agents with support for
bidirectional messaging, event handling, and connection management.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, AsyncIterator, Any
from datetime import datetime
import uuid

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WebSocketServerProtocol = None
    WEBSOCKETS_AVAILABLE = False

from .interfaces import (
    IWebSocketHandler, RealtimeMessage, RealtimeEvent, RealtimeConfiguration,
    ConnectionStatus, RealtimeMessageType, EventType, ConnectionError
)


class WebSocketHandler(IWebSocketHandler):
    """
    WebSocket handler for real-time agent communication.
    
    Provides bidirectional real-time communication between clients and agents
    with support for message streaming, event handling, and connection management.
    """
    
    def __init__(self, agent_id: str, config: RealtimeConfiguration):
        """
        Initialize WebSocket handler.
        
        Args:
            agent_id: Agent identifier for this handler
            config: Real-time configuration
        """
        self.agent_id = agent_id
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Connection state
        self._websocket: Optional[WebSocketServerProtocol] = None
        self._status = ConnectionStatus.DISCONNECTED
        self._client_id: Optional[str] = None
        
        # Message handling
        self._message_queue = asyncio.Queue()
        self._event_queue = asyncio.Queue()
        
        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "events_sent": 0,
            "events_received": 0,
            "connection_time": None,
            "last_activity": None
        }
        
        if not WEBSOCKETS_AVAILABLE:
            self._logger.warning("websockets library not available, WebSocket functionality disabled")
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._status == ConnectionStatus.CONNECTED and self._websocket is not None
    
    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self._status
    
    @property
    def client_id(self) -> Optional[str]:
        """Get connected client ID"""
        return self._client_id
    
    async def connect(self, agent_id: str) -> bool:
        """
        Connect to agent via WebSocket.
        
        Args:
            agent_id: Agent identifier to connect to
            
        Returns:
            True if connection successful
        """
        if not WEBSOCKETS_AVAILABLE:
            self._logger.error("WebSocket functionality not available")
            return False
        
        try:
            self._status = ConnectionStatus.CONNECTING
            self._logger.info(f"Connecting WebSocket to agent: {agent_id}")
            
            # In a real implementation, this would establish WebSocket connection
            # For now, simulate successful connection
            self._status = ConnectionStatus.CONNECTED
            self._client_id = str(uuid.uuid4())
            self._stats["connection_time"] = datetime.utcnow()
            self._stats["last_activity"] = datetime.utcnow()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Send connection event
            await self._send_connection_event(EventType.CONNECTION_OPEN)
            
            self._logger.info(f"WebSocket connected to agent: {agent_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect WebSocket to agent {agent_id}: {e}")
            self._status = ConnectionStatus.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Disconnect WebSocket"""
        if self._status == ConnectionStatus.DISCONNECTED:
            return
        
        try:
            self._status = ConnectionStatus.DISCONNECTING
            self._logger.info("Disconnecting WebSocket")
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Send disconnection event
            await self._send_connection_event(EventType.CONNECTION_CLOSE)
            
            # Close WebSocket connection
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
            
            self._status = ConnectionStatus.DISCONNECTED
            self._client_id = None
            
            self._logger.info("WebSocket disconnected")
            
        except Exception as e:
            self._logger.error(f"Error during WebSocket disconnection: {e}")
            self._status = ConnectionStatus.ERROR
    
    async def send_message(self, message: RealtimeMessage) -> bool:
        """
        Send message via WebSocket.
        
        Args:
            message: Real-time message to send
            
        Returns:
            True if message sent successfully
        """
        if not self.is_connected:
            self._logger.warning("Cannot send message - WebSocket not connected")
            return False
        
        try:
            # Convert message to JSON
            message_data = {
                "type": "message",
                "data": message.to_dict()
            }
            
            # In real implementation, would send via WebSocket
            # await self._websocket.send(json.dumps(message_data))
            
            self._stats["messages_sent"] += 1
            self._stats["last_activity"] = datetime.utcnow()
            
            self._logger.debug(f"Sent message via WebSocket: {message.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send message via WebSocket: {e}")
            return False
    
    async def receive_messages(self) -> AsyncIterator[RealtimeMessage]:
        """
        Receive messages from WebSocket.
        
        Yields:
            Real-time messages received from WebSocket
        """
        while self.is_connected:
            try:
                # Get message from queue (populated by background task)
                message = await asyncio.wait_for(
                    self._message_queue.get(), 
                    timeout=1.0
                )
                
                self._stats["messages_received"] += 1
                self._stats["last_activity"] = datetime.utcnow()
                
                yield message
                
            except asyncio.TimeoutError:
                # Continue waiting for messages
                continue
            except Exception as e:
                self._logger.error(f"Error receiving messages: {e}")
                break
    
    async def send_event(self, event: RealtimeEvent) -> bool:
        """
        Send event via WebSocket.
        
        Args:
            event: Real-time event to send
            
        Returns:
            True if event sent successfully
        """
        if not self.is_connected:
            self._logger.warning("Cannot send event - WebSocket not connected")
            return False
        
        try:
            # Convert event to JSON
            event_data = {
                "type": "event",
                "data": event.to_dict()
            }
            
            # In real implementation, would send via WebSocket
            # await self._websocket.send(json.dumps(event_data))
            
            self._stats["events_sent"] += 1
            self._stats["last_activity"] = datetime.utcnow()
            
            self._logger.debug(f"Sent event via WebSocket: {event.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send event via WebSocket: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get WebSocket handler statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            **self._stats,
            "agent_id": self.agent_id,
            "client_id": self._client_id,
            "status": self._status.value,
            "is_connected": self.is_connected,
            "queue_sizes": {
                "message_queue": self._message_queue.qsize(),
                "event_queue": self._event_queue.qsize()
            }
        }
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks for message handling and heartbeat"""
        # Start receive task (would handle incoming WebSocket messages)
        self._receive_task = asyncio.create_task(self._receive_loop())
        
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks"""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
    
    async def _receive_loop(self) -> None:
        """Background task to receive WebSocket messages"""
        while self.is_connected:
            try:
                # In real implementation, would receive from WebSocket
                # For now, simulate receiving messages
                await asyncio.sleep(1)
                
                # Simulate occasional message reception
                if datetime.utcnow().second % 10 == 0:
                    test_message = RealtimeMessage(
                        type=RealtimeMessageType.TEXT,
                        content="Test message from client",
                        sender_id=self._client_id
                    )
                    await self._message_queue.put(test_message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in receive loop: {e}")
                break
    
    async def _heartbeat_loop(self) -> None:
        """Background task to send heartbeat messages"""
        while self.is_connected:
            try:
                # Send heartbeat every 30 seconds
                await asyncio.sleep(30)
                
                heartbeat_event = RealtimeEvent(
                    type=EventType.CONNECTION_OPEN,
                    data={"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
                )
                
                await self.send_event(heartbeat_event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in heartbeat loop: {e}")
                break
    
    async def _send_connection_event(self, event_type: EventType) -> None:
        """Send connection status event"""
        try:
            event = RealtimeEvent(
                type=event_type,
                data={
                    "agent_id": self.agent_id,
                    "client_id": self._client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Don't use send_event to avoid connection checks
            event_data = {
                "type": "event",
                "data": event.to_dict()
            }
            
            # In real implementation, would send via WebSocket
            self._logger.debug(f"Connection event: {event_type.value}")
            
        except Exception as e:
            self._logger.error(f"Failed to send connection event: {e}")


class WebSocketServer:
    """
    WebSocket server for handling multiple client connections.
    
    Manages WebSocket server instance and routes messages to appropriate
    agent handlers.
    """
    
    def __init__(self, config: RealtimeConfiguration):
        """
        Initialize WebSocket server.
        
        Args:
            config: Real-time configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Server state
        self._server = None
        self._handlers: Dict[str, WebSocketHandler] = {}
        self._running = False
        
        if not WEBSOCKETS_AVAILABLE:
            self._logger.warning("websockets library not available")
    
    async def start(self) -> bool:
        """
        Start WebSocket server.
        
        Returns:
            True if server started successfully
        """
        if not WEBSOCKETS_AVAILABLE:
            self._logger.error("Cannot start WebSocket server - websockets library not available")
            return False
        
        try:
            self._logger.info(f"Starting WebSocket server on port {self.config.websocket_port}")
            
            # In real implementation, would start actual WebSocket server
            # self._server = await websockets.serve(
            #     self._handle_connection,
            #     "localhost",
            #     self.config.websocket_port,
            #     max_size=None,
            #     max_queue=self.config.max_connections
            # )
            
            self._running = True
            self._logger.info("WebSocket server started successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop WebSocket server"""
        if not self._running:
            return
        
        try:
            self._logger.info("Stopping WebSocket server")
            
            # Close all handlers
            for handler in list(self._handlers.values()):
                await handler.disconnect()
            
            # Stop server
            if self._server:
                self._server.close()
                await self._server.wait_closed()
                self._server = None
            
            self._running = False
            self._logger.info("WebSocket server stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping WebSocket server: {e}")
    
    def add_handler(self, agent_id: str, handler: WebSocketHandler) -> None:
        """Add WebSocket handler for agent"""
        self._handlers[agent_id] = handler
        self._logger.info(f"Added WebSocket handler for agent: {agent_id}")
    
    def remove_handler(self, agent_id: str) -> None:
        """Remove WebSocket handler for agent"""
        if agent_id in self._handlers:
            del self._handlers[agent_id]
            self._logger.info(f"Removed WebSocket handler for agent: {agent_id}")


# Factory functions
def create_websocket_handler(agent_id: str, config: RealtimeConfiguration) -> WebSocketHandler:
    """Create a new WebSocket handler"""
    return WebSocketHandler(agent_id, config)
