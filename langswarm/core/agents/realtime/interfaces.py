"""
LangSwarm V2 Agent Real-time Interfaces

Type-safe interfaces for real-time agent capabilities including WebSocket
communication, server-sent events, voice conversations, and live collaboration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncIterator, Union, Callable
import uuid


class RealtimeMessageType(Enum):
    """Types of real-time messages"""
    TEXT = "text"
    AUDIO = "audio"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class EventType(Enum):
    """Types of real-time events"""
    MESSAGE_START = "message_start"
    MESSAGE_CHUNK = "message_chunk"
    MESSAGE_END = "message_end"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    VOICE_START = "voice_start"
    VOICE_END = "voice_end"
    PARTICIPANT_JOIN = "participant_join"
    PARTICIPANT_LEAVE = "participant_leave"
    CONNECTION_OPEN = "connection_open"
    CONNECTION_CLOSE = "connection_close"


class StreamingType(Enum):
    """Types of streaming responses"""
    TEXT_DELTA = "text_delta"
    AUDIO_CHUNK = "audio_chunk"
    TOOL_OUTPUT = "tool_output"
    STATUS_UPDATE = "status_update"
    COMPLETE = "complete"


class VoiceState(Enum):
    """Voice conversation states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


class CollaborationRole(Enum):
    """Collaboration participant roles"""
    OBSERVER = "observer"
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    ADMIN = "admin"


class ConnectionStatus(Enum):
    """Connection status states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class RealtimeMessage:
    """Real-time message structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: RealtimeMessageType = RealtimeMessageType.TEXT
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sender_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
            "session_id": self.session_id
        }


@dataclass 
class RealtimeEvent:
    """Real-time event structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.MESSAGE_START
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }


@dataclass
class StreamingChunk:
    """Streaming response chunk"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: StreamingType = StreamingType.TEXT_DELTA
    content: str = ""
    index: int = 0
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "index": self.index,
            "is_final": self.is_final,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class VoiceSegment:
    """Voice conversation segment"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audio_data: bytes = b""
    duration: float = 0.0
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CollaborationState:
    """Live collaboration session state"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: Dict[str, CollaborationRole] = field(default_factory=dict)
    active_speaker: Optional[str] = None
    shared_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RealtimeConfiguration:
    """Configuration for real-time features"""
    # WebSocket settings
    websocket_enabled: bool = True
    websocket_port: int = 8765
    websocket_path: str = "/ws"
    max_connections: int = 1000
    
    # Server-sent events settings
    sse_enabled: bool = True
    sse_path: str = "/events"
    heartbeat_interval: int = 30
    
    # Voice settings
    voice_enabled: bool = False
    voice_sample_rate: int = 16000
    voice_chunk_size: int = 1024
    voice_format: str = "wav"
    
    # Collaboration settings
    collaboration_enabled: bool = True
    max_participants: int = 10
    session_timeout: int = 3600
    
    # Streaming settings
    streaming_buffer_size: int = 4096
    streaming_timeout: int = 30
    chunk_size: int = 512


class IRealtimeAgent(ABC):
    """Interface for real-time agent capabilities"""
    
    @property
    @abstractmethod
    def is_realtime_enabled(self) -> bool:
        """Check if real-time features are enabled"""
        pass
    
    @property
    @abstractmethod
    def supported_realtime_features(self) -> List[str]:
        """List of supported real-time features"""
        pass
    
    @abstractmethod
    async def start_realtime_session(self, config: RealtimeConfiguration) -> 'IRealtimeSession':
        """Start a new real-time session"""
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        message: RealtimeMessage,
        session_id: str
    ) -> AsyncIterator[StreamingChunk]:
        """Stream a response in real-time"""
        pass
    
    @abstractmethod
    async def handle_realtime_event(
        self,
        event: RealtimeEvent,
        session_id: str
    ) -> Optional[RealtimeEvent]:
        """Handle incoming real-time event"""
        pass


class IRealtimeSession(ABC):
    """Interface for real-time session management"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Session identifier"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> ConnectionStatus:
        """Current connection status"""
        pass
    
    @property
    @abstractmethod
    def participants(self) -> List[str]:
        """Active participants"""
        pass
    
    @abstractmethod
    async def send_message(self, message: RealtimeMessage) -> bool:
        """Send a real-time message"""
        pass
    
    @abstractmethod
    async def send_event(self, event: RealtimeEvent) -> bool:
        """Send a real-time event"""
        pass
    
    @abstractmethod
    async def add_participant(self, participant_id: str, role: CollaborationRole = CollaborationRole.PARTICIPANT) -> bool:
        """Add participant to session"""
        pass
    
    @abstractmethod
    async def remove_participant(self, participant_id: str) -> bool:
        """Remove participant from session"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the real-time session"""
        pass


class IWebSocketHandler(ABC):
    """Interface for WebSocket communication"""
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        pass
    
    @abstractmethod
    async def connect(self, agent_id: str) -> bool:
        """Connect to agent via WebSocket"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect WebSocket"""
        pass
    
    @abstractmethod
    async def send_message(self, message: RealtimeMessage) -> bool:
        """Send message via WebSocket"""
        pass
    
    @abstractmethod
    async def receive_messages(self) -> AsyncIterator[RealtimeMessage]:
        """Receive messages from WebSocket"""
        pass
    
    @abstractmethod
    async def send_event(self, event: RealtimeEvent) -> bool:
        """Send event via WebSocket"""
        pass


class ISSEHandler(ABC):
    """Interface for Server-Sent Events"""
    
    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Check if SSE stream is active"""
        pass
    
    @abstractmethod
    async def start_stream(self, agent_id: str) -> None:
        """Start SSE stream"""
        pass
    
    @abstractmethod
    async def stop_stream(self) -> None:
        """Stop SSE stream"""
        pass
    
    @abstractmethod
    async def send_event(self, event: RealtimeEvent) -> bool:
        """Send event via SSE"""
        pass
    
    @abstractmethod
    async def send_chunk(self, chunk: StreamingChunk) -> bool:
        """Send streaming chunk via SSE"""
        pass


class IVoiceConversation(ABC):
    """Interface for voice conversation management"""
    
    @property
    @abstractmethod
    def state(self) -> VoiceState:
        """Current voice conversation state"""
        pass
    
    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Check if voice conversation is active"""
        pass
    
    @abstractmethod
    async def start_conversation(self, agent_id: str) -> bool:
        """Start voice conversation with agent"""
        pass
    
    @abstractmethod
    async def stop_conversation(self) -> None:
        """Stop voice conversation"""
        pass
    
    @abstractmethod
    async def send_audio(self, audio_data: bytes) -> bool:
        """Send audio data to agent"""
        pass
    
    @abstractmethod
    async def receive_audio(self) -> AsyncIterator[VoiceSegment]:
        """Receive audio from agent"""
        pass
    
    @abstractmethod
    async def process_speech(self, audio_data: bytes) -> Optional[str]:
        """Process speech to text"""
        pass


class ILiveCollaboration(ABC):
    """Interface for live collaboration sessions"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Collaboration session ID"""
        pass
    
    @property
    @abstractmethod
    def state(self) -> CollaborationState:
        """Current collaboration state"""
        pass
    
    @property
    @abstractmethod
    def participant_count(self) -> int:
        """Number of active participants"""
        pass
    
    @abstractmethod
    async def create_session(self, creator_id: str) -> str:
        """Create new collaboration session"""
        pass
    
    @abstractmethod
    async def join_session(self, session_id: str, participant_id: str, role: CollaborationRole = CollaborationRole.PARTICIPANT) -> bool:
        """Join collaboration session"""
        pass
    
    @abstractmethod
    async def leave_session(self, participant_id: str) -> bool:
        """Leave collaboration session"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: RealtimeMessage, sender_id: str) -> bool:
        """Broadcast message to all participants"""
        pass
    
    @abstractmethod
    async def update_shared_context(self, updates: Dict[str, Any]) -> bool:
        """Update shared collaboration context"""
        pass


# Exception classes
class RealtimeError(Exception):
    """Base exception for real-time operations"""
    pass


class ConnectionError(RealtimeError):
    """Exception for connection-related errors"""
    pass


class StreamingError(RealtimeError):
    """Exception for streaming-related errors"""
    pass


class VoiceError(RealtimeError):
    """Exception for voice-related errors"""
    pass
