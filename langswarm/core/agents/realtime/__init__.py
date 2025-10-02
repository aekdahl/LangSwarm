"""
LangSwarm V2 Agent Real-time & Streaming Enhancements

Advanced real-time interaction capabilities for V2 agents including:
- WebSocket-based real-time agent communication
- Server-sent events for live response streaming  
- Real-time voice conversation support
- Live collaboration and multi-user sessions
- Real-time tool execution and feedback

Usage:
    from langswarm.core.agents.realtime import (
        RealtimeAgentManager, WebSocketHandler, SSEHandler,
        VoiceConversationManager, LiveCollaborationSession
    )
    
    # WebSocket-based real-time communication
    manager = RealtimeAgentManager()
    ws_handler = await manager.create_websocket_handler(agent_id="my_agent")
    
    # Server-sent events for streaming
    sse_handler = await manager.create_sse_handler(agent_id="my_agent")
    
    # Voice conversations
    voice_manager = VoiceConversationManager()
    session = await voice_manager.start_conversation(agent_id="my_agent")
    
    # Live collaboration
    collab_session = LiveCollaborationSession()
    await collab_session.add_participant(user_id="user1", agent_id="my_agent")
"""

from .interfaces import (
    # Core interfaces
    IRealtimeAgent, IRealtimeSession, IWebSocketHandler, ISSEHandler,
    IVoiceConversation, ILiveCollaboration,
    
    # Data structures  
    RealtimeMessage, RealtimeEvent, StreamingChunk, VoiceSegment,
    CollaborationState, RealtimeConfiguration,
    
    # Enums
    RealtimeMessageType, EventType, StreamingType, VoiceState,
    CollaborationRole, ConnectionStatus,
    
    # Exceptions
    RealtimeError, ConnectionError, StreamingError, VoiceError
)

from .manager import (
    RealtimeAgentManager, create_realtime_manager,
    get_realtime_manager, set_realtime_manager
)

from .websocket import (
    WebSocketHandler, WebSocketServer, create_websocket_handler
)

from .sse import (
    SSEHandler, SSEStream, create_sse_handler
)

from .voice import (
    VoiceConversationManager, VoiceProcessor, AudioStreamer,
    create_voice_conversation, start_voice_session
)

from .collaboration import (
    LiveCollaborationSession, CollaborationManager, ParticipantManager,
    create_collaboration_session, join_collaboration
)

from .streaming import (
    StreamingResponseManager, ChunkProcessor, ResponseAggregator,
    create_streaming_manager, process_streaming_response
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core interfaces
    'IRealtimeAgent',
    'IRealtimeSession',
    'IWebSocketHandler',
    'ISSEHandler',
    'IVoiceConversation',
    'ILiveCollaboration',
    
    # Data structures
    'RealtimeMessage',
    'RealtimeEvent',
    'StreamingChunk',
    'VoiceSegment',
    'CollaborationState',
    'RealtimeConfiguration',
    
    # Enums
    'RealtimeMessageType',
    'EventType',
    'StreamingType',
    'VoiceState',
    'CollaborationRole',
    'ConnectionStatus',
    
    # Exceptions
    'RealtimeError',
    'ConnectionError',
    'StreamingError',
    'VoiceError',
    
    # Manager
    'RealtimeAgentManager',
    'create_realtime_manager',
    'get_realtime_manager',
    'set_realtime_manager',
    
    # WebSocket
    'WebSocketHandler',
    'WebSocketServer',
    'create_websocket_handler',
    
    # Server-Sent Events
    'SSEHandler',
    'SSEStream',
    'create_sse_handler',
    
    # Voice
    'VoiceConversationManager',
    'VoiceProcessor',
    'AudioStreamer',
    'create_voice_conversation',
    'start_voice_session',
    
    # Collaboration
    'LiveCollaborationSession',
    'CollaborationManager',
    'ParticipantManager',
    'create_collaboration_session',
    'join_collaboration',
    
    # Streaming
    'StreamingResponseManager',
    'ChunkProcessor',
    'ResponseAggregator',
    'create_streaming_manager',
    'process_streaming_response'
]

# Global realtime manager
_global_realtime_manager = None

def get_global_realtime_manager():
    """Get the global realtime manager instance"""
    return _global_realtime_manager

def set_global_realtime_manager(manager):
    """Set the global realtime manager instance"""
    global _global_realtime_manager
    _global_realtime_manager = manager
