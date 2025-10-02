"""
LangSwarm V2 Session Management Interfaces

Clean, provider-aligned session interfaces that leverage native LLM provider
session capabilities (OpenAI threads, Anthropic conversations, etc.) while
providing a unified abstraction layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


class MessageRole(Enum):
    """Message role enumeration aligned with provider standards"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"


class SessionBackend(Enum):
    """Session storage backend types"""
    PROVIDER_NATIVE = "provider_native"  # Use provider's native session handling
    LOCAL_MEMORY = "local_memory"       # In-memory sessions
    LOCAL_SQLITE = "local_sqlite"       # SQLite persistence
    EXTERNAL_DB = "external_db"         # External database
    HYBRID = "hybrid"                   # Provider native + local backup


@dataclass
class SessionMessage:
    """Unified message format aligned with provider standards"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    # Provider-specific fields
    provider_message_id: Optional[str] = None
    token_count: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class SessionContext:
    """Session context information"""
    session_id: str
    user_id: str
    provider: str
    model: str
    backend: SessionBackend
    
    # Session configuration
    max_messages: int = 100
    auto_archive: bool = True
    persist_messages: bool = True
    
    # Provider-specific context
    provider_session_id: Optional[str] = None  # OpenAI thread ID, etc.
    provider_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.provider_context is None:
            self.provider_context = {}


@dataclass
class SessionMetrics:
    """Session metrics and analytics"""
    message_count: int = 0
    total_tokens: int = 0
    session_duration: float = 0.0  # seconds
    last_activity: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ISessionStorage(ABC):
    """Interface for session storage backends"""
    
    @abstractmethod
    async def save_session(self, session_id: str, messages: List[SessionMessage], 
                          context: SessionContext) -> bool:
        """Save session data"""
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[tuple[List[SessionMessage], SessionContext]]:
        """Load session data"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    async def list_sessions(self, user_id: Optional[str] = None, 
                           status: Optional[SessionStatus] = None,
                           limit: int = 100) -> List[SessionContext]:
        """List sessions"""
        pass
    
    @abstractmethod
    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get session metrics"""
        pass


class IProviderSession(ABC):
    """Interface for provider-native session management"""
    
    @abstractmethod
    async def create_provider_session(self, user_id: str, **kwargs) -> str:
        """Create a provider-native session (thread, conversation, etc.)"""
        pass
    
    @abstractmethod
    async def get_provider_session(self, provider_session_id: str) -> Optional[Dict[str, Any]]:
        """Get provider session information"""
        pass
    
    @abstractmethod
    async def send_message(self, provider_session_id: str, message: str, 
                          role: MessageRole = MessageRole.USER) -> SessionMessage:
        """Send message through provider session"""
        pass
    
    @abstractmethod
    async def get_messages(self, provider_session_id: str, 
                          limit: Optional[int] = None) -> List[SessionMessage]:
        """Get messages from provider session"""
        pass
    
    @abstractmethod
    async def delete_provider_session(self, provider_session_id: str) -> bool:
        """Delete provider session"""
        pass


class ISessionManager(ABC):
    """Interface for unified session management"""
    
    @abstractmethod
    async def create_session(self, user_id: str, provider: str, model: str,
                           backend: SessionBackend = SessionBackend.PROVIDER_NATIVE,
                           **kwargs) -> 'Session':
        """Create a new session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional['Session']:
        """Get existing session"""
        pass
    
    @abstractmethod
    async def list_user_sessions(self, user_id: str, limit: int = 100) -> List['Session']:
        """List sessions for a user"""
        pass
    
    @abstractmethod
    async def archive_session(self, session_id: str) -> bool:
        """Archive a session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass


class ISession(ABC):
    """Interface for session instances"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Get session ID"""
        pass
    
    @property
    @abstractmethod
    def user_id(self) -> str:
        """Get user ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> SessionStatus:
        """Get session status"""
        pass
    
    @property
    @abstractmethod
    def context(self) -> SessionContext:
        """Get session context"""
        pass
    
    @property
    @abstractmethod
    def metrics(self) -> SessionMetrics:
        """Get session metrics"""
        pass
    
    @abstractmethod
    async def send_message(self, content: str, role: MessageRole = MessageRole.USER,
                          **kwargs) -> SessionMessage:
        """Send a message in this session"""
        pass
    
    @abstractmethod
    async def get_messages(self, limit: Optional[int] = None) -> List[SessionMessage]:
        """Get messages from this session"""
        pass
    
    @abstractmethod
    async def add_system_message(self, content: str) -> SessionMessage:
        """Add a system message"""
        pass
    
    @abstractmethod
    async def clear_messages(self) -> bool:
        """Clear session messages"""
        pass
    
    @abstractmethod
    async def update_context(self, **kwargs) -> bool:
        """Update session context"""
        pass
    
    @abstractmethod
    async def archive(self) -> bool:
        """Archive this session"""
        pass


class ISessionLifecycleHook(ABC):
    """Interface for session lifecycle hooks"""
    
    async def on_session_created(self, session: ISession) -> None:
        """Called when a session is created"""
        pass
    
    async def on_message_sent(self, session: ISession, message: SessionMessage) -> None:
        """Called when a message is sent"""
        pass
    
    async def on_message_received(self, session: ISession, message: SessionMessage) -> None:
        """Called when a message is received"""
        pass
    
    async def on_session_archived(self, session: ISession) -> None:
        """Called when a session is archived"""
        pass
    
    async def on_session_deleted(self, session: ISession) -> None:
        """Called when a session is deleted"""
        pass


class ISessionMiddleware(ABC):
    """Interface for session middleware"""
    
    @abstractmethod
    async def process_outgoing_message(self, session: ISession, message: SessionMessage) -> SessionMessage:
        """Process outgoing message"""
        pass
    
    @abstractmethod
    async def process_incoming_message(self, session: ISession, message: SessionMessage) -> SessionMessage:
        """Process incoming message"""
        pass


class SessionError(Exception):
    """Base session error"""
    pass


class SessionNotFoundError(SessionError):
    """Session not found error"""
    pass


class ProviderSessionError(SessionError):
    """Provider session error"""
    pass


class SessionStorageError(SessionError):
    """Session storage error"""
    pass
