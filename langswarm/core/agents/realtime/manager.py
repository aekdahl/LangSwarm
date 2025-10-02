"""
LangSwarm V2 Real-time Agent Manager

Central manager for coordinating real-time agent capabilities including
WebSocket communication, SSE streaming, voice conversations, and live collaboration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .interfaces import (
    IRealtimeAgent, IRealtimeSession, IWebSocketHandler, ISSEHandler,
    IVoiceConversation, ILiveCollaboration,
    RealtimeConfiguration, RealtimeMessage, RealtimeEvent,
    ConnectionStatus, RealtimeError
)


class RealtimeAgentManager:
    """
    Central manager for real-time agent capabilities.
    
    Coordinates WebSocket connections, SSE streams, voice conversations,
    and live collaboration sessions across all V2 agents.
    """
    
    def __init__(self, config: Optional[RealtimeConfiguration] = None):
        """
        Initialize real-time agent manager.
        
        Args:
            config: Real-time configuration settings
        """
        self.config = config or RealtimeConfiguration()
        self._logger = logging.getLogger(__name__)
        
        # Active connections and sessions
        self._websocket_handlers: Dict[str, IWebSocketHandler] = {}
        self._sse_handlers: Dict[str, ISSEHandler] = {}
        self._voice_conversations: Dict[str, IVoiceConversation] = {}
        self._collaboration_sessions: Dict[str, ILiveCollaboration] = {}
        self._realtime_sessions: Dict[str, IRealtimeSession] = {}
        
        # Agent registry
        self._realtime_agents: Dict[str, IRealtimeAgent] = {}
        
        # Connection tracking
        self._connection_stats = {
            "websocket_connections": 0,
            "sse_streams": 0,
            "voice_conversations": 0,
            "collaboration_sessions": 0,
            "total_messages": 0,
            "total_events": 0
        }
        
        self._started = False
        self._logger.info("Real-time agent manager initialized")
    
    async def start(self) -> None:
        """Start the real-time manager"""
        if self._started:
            return
        
        self._logger.info("Starting real-time agent manager")
        
        # Initialize services based on configuration
        if self.config.websocket_enabled:
            await self._start_websocket_server()
        
        if self.config.sse_enabled:
            await self._start_sse_server()
        
        self._started = True
        self._logger.info("Real-time agent manager started successfully")
    
    async def stop(self) -> None:
        """Stop the real-time manager"""
        if not self._started:
            return
        
        self._logger.info("Stopping real-time agent manager")
        
        # Close all active connections
        await self._close_all_connections()
        
        self._started = False
        self._logger.info("Real-time agent manager stopped")
    
    async def register_agent(self, agent: IRealtimeAgent, agent_id: str) -> bool:
        """
        Register an agent for real-time capabilities.
        
        Args:
            agent: Real-time agent implementation
            agent_id: Unique agent identifier
            
        Returns:
            True if registration successful
        """
        try:
            if not agent.is_realtime_enabled:
                self._logger.warning(f"Agent {agent_id} does not support real-time features")
                return False
            
            self._realtime_agents[agent_id] = agent
            self._logger.info(f"Registered real-time agent: {agent_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from real-time capabilities.
        
        Args:
            agent_id: Agent identifier to unregister
            
        Returns:
            True if unregistration successful
        """
        try:
            if agent_id in self._realtime_agents:
                # Close any active connections for this agent
                await self._close_agent_connections(agent_id)
                del self._realtime_agents[agent_id]
                self._logger.info(f"Unregistered real-time agent: {agent_id}")
                return True
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def create_websocket_handler(self, agent_id: str) -> Optional[IWebSocketHandler]:
        """
        Create WebSocket handler for agent communication.
        
        Args:
            agent_id: Agent to create WebSocket handler for
            
        Returns:
            WebSocket handler instance or None if failed
        """
        try:
            if not self.config.websocket_enabled:
                raise RealtimeError("WebSocket not enabled in configuration")
            
            if agent_id not in self._realtime_agents:
                raise RealtimeError(f"Agent {agent_id} not registered for real-time")
            
            # Import here to avoid circular dependencies
            from .websocket import WebSocketHandler
            
            handler = WebSocketHandler(agent_id, self.config)
            await handler.connect(agent_id)
            
            self._websocket_handlers[agent_id] = handler
            self._connection_stats["websocket_connections"] += 1
            
            self._logger.info(f"Created WebSocket handler for agent: {agent_id}")
            return handler
            
        except Exception as e:
            self._logger.error(f"Failed to create WebSocket handler for {agent_id}: {e}")
            return None
    
    async def create_sse_handler(self, agent_id: str) -> Optional[ISSEHandler]:
        """
        Create Server-Sent Events handler for streaming.
        
        Args:
            agent_id: Agent to create SSE handler for
            
        Returns:
            SSE handler instance or None if failed
        """
        try:
            if not self.config.sse_enabled:
                raise RealtimeError("SSE not enabled in configuration")
            
            if agent_id not in self._realtime_agents:
                raise RealtimeError(f"Agent {agent_id} not registered for real-time")
            
            # Import here to avoid circular dependencies
            from .sse import SSEHandler
            
            handler = SSEHandler(agent_id, self.config)
            await handler.start_stream(agent_id)
            
            self._sse_handlers[agent_id] = handler
            self._connection_stats["sse_streams"] += 1
            
            self._logger.info(f"Created SSE handler for agent: {agent_id}")
            return handler
            
        except Exception as e:
            self._logger.error(f"Failed to create SSE handler for {agent_id}: {e}")
            return None
    
    async def create_voice_conversation(self, agent_id: str) -> Optional[IVoiceConversation]:
        """
        Create voice conversation for agent.
        
        Args:
            agent_id: Agent to create voice conversation for
            
        Returns:
            Voice conversation instance or None if failed
        """
        try:
            if not self.config.voice_enabled:
                raise RealtimeError("Voice not enabled in configuration")
            
            if agent_id not in self._realtime_agents:
                raise RealtimeError(f"Agent {agent_id} not registered for real-time")
            
            # Import here to avoid circular dependencies
            from .voice import VoiceConversationManager
            
            conversation = VoiceConversationManager(agent_id, self.config)
            await conversation.start_conversation(agent_id)
            
            self._voice_conversations[agent_id] = conversation
            self._connection_stats["voice_conversations"] += 1
            
            self._logger.info(f"Created voice conversation for agent: {agent_id}")
            return conversation
            
        except Exception as e:
            self._logger.error(f"Failed to create voice conversation for {agent_id}: {e}")
            return None
    
    async def create_collaboration_session(self, creator_id: str, agent_id: str) -> Optional[ILiveCollaboration]:
        """
        Create live collaboration session.
        
        Args:
            creator_id: User creating the session
            agent_id: Agent to include in collaboration
            
        Returns:
            Live collaboration session or None if failed
        """
        try:
            if not self.config.collaboration_enabled:
                raise RealtimeError("Collaboration not enabled in configuration")
            
            if agent_id not in self._realtime_agents:
                raise RealtimeError(f"Agent {agent_id} not registered for real-time")
            
            # Import here to avoid circular dependencies
            from .collaboration import LiveCollaborationSession
            
            session = LiveCollaborationSession(self.config)
            session_id = await session.create_session(creator_id)
            
            self._collaboration_sessions[session_id] = session
            self._connection_stats["collaboration_sessions"] += 1
            
            self._logger.info(f"Created collaboration session: {session_id}")
            return session
            
        except Exception as e:
            self._logger.error(f"Failed to create collaboration session: {e}")
            return None
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection statistics.
        
        Returns:
            Dictionary of connection statistics
        """
        return {
            **self._connection_stats,
            "active_websockets": len(self._websocket_handlers),
            "active_sse_streams": len(self._sse_handlers),
            "active_voice_conversations": len(self._voice_conversations),
            "active_collaboration_sessions": len(self._collaboration_sessions),
            "registered_agents": len(self._realtime_agents),
            "uptime": datetime.utcnow().isoformat(),
            "status": "running" if self._started else "stopped"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on real-time system.
        
        Returns:
            Health check results
        """
        health = {
            "status": "healthy" if self._started else "stopped",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "websocket": self.config.websocket_enabled,
                "sse": self.config.sse_enabled,
                "voice": self.config.voice_enabled,
                "collaboration": self.config.collaboration_enabled
            },
            "connections": await self.get_connection_stats(),
            "errors": []
        }
        
        # Check individual services
        try:
            if self.config.websocket_enabled:
                # Check WebSocket server health
                pass
            
            if self.config.sse_enabled:
                # Check SSE server health
                pass
                
        except Exception as e:
            health["errors"].append(str(e))
            health["status"] = "degraded"
        
        return health
    
    async def _start_websocket_server(self) -> None:
        """Start WebSocket server"""
        # Implementation would start actual WebSocket server
        self._logger.info(f"WebSocket server started on port {self.config.websocket_port}")
    
    async def _start_sse_server(self) -> None:
        """Start SSE server"""
        # Implementation would start actual SSE server
        self._logger.info(f"SSE server started on path {self.config.sse_path}")
    
    async def _close_all_connections(self) -> None:
        """Close all active connections"""
        # Close WebSocket handlers
        for handler in list(self._websocket_handlers.values()):
            try:
                await handler.disconnect()
            except Exception as e:
                self._logger.error(f"Error closing WebSocket handler: {e}")
        
        # Close SSE handlers
        for handler in list(self._sse_handlers.values()):
            try:
                await handler.stop_stream()
            except Exception as e:
                self._logger.error(f"Error closing SSE handler: {e}")
        
        # Close voice conversations
        for conversation in list(self._voice_conversations.values()):
            try:
                await conversation.stop_conversation()
            except Exception as e:
                self._logger.error(f"Error closing voice conversation: {e}")
        
        # Clear all dictionaries
        self._websocket_handlers.clear()
        self._sse_handlers.clear()
        self._voice_conversations.clear()
        self._collaboration_sessions.clear()
    
    async def _close_agent_connections(self, agent_id: str) -> None:
        """Close all connections for a specific agent"""
        # Close WebSocket handler
        if agent_id in self._websocket_handlers:
            try:
                await self._websocket_handlers[agent_id].disconnect()
                del self._websocket_handlers[agent_id]
            except Exception as e:
                self._logger.error(f"Error closing WebSocket for {agent_id}: {e}")
        
        # Close SSE handler
        if agent_id in self._sse_handlers:
            try:
                await self._sse_handlers[agent_id].stop_stream()
                del self._sse_handlers[agent_id]
            except Exception as e:
                self._logger.error(f"Error closing SSE for {agent_id}: {e}")
        
        # Close voice conversation
        if agent_id in self._voice_conversations:
            try:
                await self._voice_conversations[agent_id].stop_conversation()
                del self._voice_conversations[agent_id]
            except Exception as e:
                self._logger.error(f"Error closing voice conversation for {agent_id}: {e}")


# Factory functions
def create_realtime_manager(config: Optional[RealtimeConfiguration] = None) -> RealtimeAgentManager:
    """Create a new real-time agent manager"""
    return RealtimeAgentManager(config)


# Global manager instance
_global_manager: Optional[RealtimeAgentManager] = None


def get_realtime_manager() -> Optional[RealtimeAgentManager]:
    """Get the global real-time manager instance"""
    return _global_manager


def set_realtime_manager(manager: RealtimeAgentManager) -> None:
    """Set the global real-time manager instance"""
    global _global_manager
    _global_manager = manager
