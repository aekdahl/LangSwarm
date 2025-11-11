"""
Memory Interfaces for AgentMem

Unified, clean interfaces for memory management that align with major LLM
providers and provide a consistent experience across all memory backends.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union, AsyncIterator, Tuple, Callable
from dataclasses import dataclass, field


class MessageRole(Enum):
    """Message roles aligned with LLM provider conventions"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"


class SessionStatus(Enum):
    """Session status states"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class MemoryBackendType(Enum):
    """Supported memory backend types"""
    IN_MEMORY = "in_memory"
    SQLITE = "sqlite"
    REDIS = "redis"
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    BIGQUERY = "bigquery"
    ELASTICSEARCH = "elasticsearch"
    MEMORY_PRO = "memory_pro"


@dataclass
class Message:
    """Universal message format aligned with LLM provider patterns"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Extended metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: Optional[int] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        data = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id
        }
        
        if self.metadata:
            data["metadata"] = self.metadata
        if self.token_count is not None:
            data["token_count"] = self.token_count
        if self.function_call:
            data["function_call"] = self.function_call
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary format"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"],
            metadata=data.get("metadata", {}),
            token_count=data.get("token_count"),
            function_call=data.get("function_call"),
            tool_calls=data.get("tool_calls")
        )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI message format"""
        msg = {
            "role": self.role.value,
            "content": self.content
        }
        
        if self.function_call:
            msg["function_call"] = self.function_call
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
            
        return msg
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic message format"""
        return {
            "role": "user" if self.role == MessageRole.USER else "assistant",
            "content": self.content
        }


@dataclass
class ConversationSummary:
    """Conversation summary for memory optimization"""
    summary: str
    message_count: int
    start_time: datetime
    end_time: datetime
    key_topics: List[str] = field(default_factory=list)
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionMetadata:
    """Session metadata and configuration"""
    session_id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    # Session configuration
    max_messages: int = 100
    max_tokens: Optional[int] = None
    auto_summarize: bool = True
    summary_threshold: int = 50
    
    # Session state
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    # Extended metadata
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def update_timestamp(self):
        """Update the last updated timestamp"""
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class MemoryUsage:
    """Memory usage statistics"""
    session_count: int = 0
    message_count: int = 0
    total_tokens: int = 0
    storage_size_bytes: int = 0
    active_sessions: int = 0
    last_cleanup: Optional[datetime] = None


class IMemorySession(ABC):
    """Interface for memory session management"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Get session ID"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> SessionMetadata:
        """Get session metadata"""
        pass
    
    @abstractmethod
    async def add_message(self, message: Message) -> bool:
        """Add a message to the session"""
        pass
    
    @abstractmethod
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        include_system: bool = True,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from the session"""
        pass
    
    @abstractmethod
    async def get_recent_context(self, max_tokens: Optional[int] = None) -> List[Message]:
        """Get recent messages that fit within token limit"""
        pass
    
    @abstractmethod
    async def clear_messages(self, keep_system: bool = True) -> bool:
        """Clear messages from session"""
        pass
    
    @abstractmethod
    async def get_summary(self) -> Optional[ConversationSummary]:
        """Get conversation summary if available"""
        pass
    
    @abstractmethod
    async def create_summary(self, force: bool = False) -> Optional[ConversationSummary]:
        """Create conversation summary"""
        pass
    
    @abstractmethod
    async def update_metadata(self, **kwargs) -> bool:
        """Update session metadata"""
        pass
    
    @abstractmethod
    async def close(self) -> bool:
        """Close the session"""
        pass


class IMemoryBackend(ABC):
    """Interface for memory backend implementations"""
    
    @property
    @abstractmethod
    def backend_type(self) -> MemoryBackendType:
        """Get backend type"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if backend is connected"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the memory backend"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the memory backend"""
        pass
    
    @abstractmethod
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new memory session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get an existing memory session"""
        pass
    
    @abstractmethod
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions with filtering"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its data"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions, return count deleted"""
        pass
    
    @abstractmethod
    async def get_usage_stats(self) -> MemoryUsage:
        """Get memory usage statistics"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Get backend health status"""
        pass


class IMemoryManager(ABC):
    """Interface for unified memory management"""
    
    @property
    @abstractmethod
    def backend(self) -> IMemoryBackend:
        """Get current memory backend"""
        pass
    
    @abstractmethod
    async def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> IMemorySession:
        """Create a new memory session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get or restore a memory session"""
        pass
    
    @abstractmethod
    async def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> IMemorySession:
        """Get existing session or create new one"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass
    
    @abstractmethod
    async def list_user_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: int = 50
    ) -> List[SessionMetadata]:
        """List sessions for a user"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        pass
    
    @abstractmethod
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system memory statistics"""
        pass


class IMemoryProvider(ABC):
    """Interface for specialized memory providers (e.g., MemoryPro)"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Get provider capabilities"""
        pass
    
    @abstractmethod
    async def analyze_conversation(self, messages: List[Message]) -> Dict[str, Any]:
        """Analyze conversation for insights"""
        pass
    
    @abstractmethod
    async def suggest_actions(self, session: IMemorySession) -> List[Dict[str, Any]]:
        """Suggest actions based on conversation history"""
        pass
    
    @abstractmethod
    async def extract_entities(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Extract entities from conversation"""
        pass
    
    @abstractmethod
    async def get_insights(self, session: IMemorySession) -> Dict[str, Any]:
        """Get conversation insights and analytics"""
        pass


class IMemoryMigrator(ABC):
    """Interface for memory data migration"""
    
    @abstractmethod
    async def migrate_from_v1(
        self,
        source_config: Dict[str, Any],
        target_backend: IMemoryBackend,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Migrate memory data from V1 system"""
        pass
    
    @abstractmethod
    async def validate_migration(
        self,
        source_config: Dict[str, Any],
        target_backend: IMemoryBackend
    ) -> Dict[str, Any]:
        """Validate migration without performing it"""
        pass
    
    @abstractmethod
    async def backup_data(
        self,
        backend: IMemoryBackend,
        backup_path: str
    ) -> bool:
        """Backup memory data"""
        pass
    
    @abstractmethod
    async def restore_data(
        self,
        backend: IMemoryBackend,
        backup_path: str
    ) -> bool:
        """Restore memory data from backup"""
        pass


# Memory configuration types
MemoryConfig = Dict[str, Any]

# Event types for memory operations
MemoryEvent = Dict[str, Any]

# Search and query types
SearchQuery = Union[str, Dict[str, Any]]
SearchResult = Dict[str, Any]

# Batch operation types
BatchOperation = Dict[str, Any]
BatchResult = Dict[str, Any]

# Memory serialization formats
SerializationFormat = str  # "json", "pickle", "msgpack", etc.

# Type aliases for convenience
MessageList = List[Message]
SessionList = List[SessionMetadata]
MemoryCallback = Callable[[MemoryEvent], None]
ProgressCallback = Callable[[int, int, str], None]  # (current, total, status)
