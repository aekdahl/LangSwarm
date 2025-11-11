"""
Session Management Data Models
==============================

Core data structures for Priority 5: Native Thread IDs & Session Management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class SessionControl(Enum):
    """Session control strategy enumeration"""
    NATIVE = "native"      # Use provider's native session management
    LANGSWARM = "langswarm"  # Use LangSwarm's client-side management
    HYBRID = "hybrid"      # Intelligent combination of both


class MessageRole(Enum):
    """Message role enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    provider_message_id: Optional[str] = None  # Provider-specific message ID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "provider_message_id": self.provider_message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary format"""
        return cls(
            id=data["id"],
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            provider_message_id=data.get("provider_message_id")
        )


@dataclass
class SessionMetadata:
    """Metadata for a session"""
    user_id: str
    session_id: str
    provider: str
    model: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE
    session_control: SessionControl = SessionControl.HYBRID
    
    # Provider-specific IDs
    provider_thread_id: Optional[str] = None
    provider_conversation_id: Optional[str] = None
    provider_agent_id: Optional[str] = None
    
    # Session configuration
    context_limit: Optional[int] = None
    auto_truncate: bool = True
    summarization_enabled: bool = True
    
    # Statistics
    message_count: int = 0
    total_tokens: int = 0
    last_activity: Optional[datetime] = None
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "session_control": self.session_control.value,
            "provider_thread_id": self.provider_thread_id,
            "provider_conversation_id": self.provider_conversation_id,
            "provider_agent_id": self.provider_agent_id,
            "context_limit": self.context_limit,
            "auto_truncate": self.auto_truncate,
            "summarization_enabled": self.summarization_enabled,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """Create from dictionary format"""
        return cls(
            user_id=data["user_id"],
            session_id=data["session_id"],
            provider=data["provider"],
            model=data["model"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=SessionStatus(data["status"]),
            session_control=SessionControl(data["session_control"]),
            provider_thread_id=data.get("provider_thread_id"),
            provider_conversation_id=data.get("provider_conversation_id"),
            provider_agent_id=data.get("provider_agent_id"),
            context_limit=data.get("context_limit"),
            auto_truncate=data.get("auto_truncate", True),
            summarization_enabled=data.get("summarization_enabled", True),
            message_count=data.get("message_count", 0),
            total_tokens=data.get("total_tokens", 0),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            tags=data.get("tags", []),
            custom_metadata=data.get("custom_metadata", {})
        )


@dataclass
class ConversationHistory:
    """Represents conversation history for a session"""
    session_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    summary: Optional[str] = None
    total_tokens: int = 0
    truncated_at: Optional[datetime] = None
    
    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the history"""
        self.messages.append(message)
        self.total_tokens += len(message.content.split())  # Simple token estimation
    
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get the most recent messages"""
        return self.messages[-limit:]
    
    def get_messages_since(self, timestamp: datetime) -> List[ConversationMessage]:
        """Get messages since a specific timestamp"""
        return [msg for msg in self.messages if msg.timestamp > timestamp]
    
    def truncate_to_limit(self, context_limit: int) -> None:
        """Truncate history to fit within context limit"""
        if len(self.messages) > context_limit:
            # Keep system message if present and recent messages
            system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
            recent_messages = self.messages[-(context_limit - len(system_messages)):]
            
            self.messages = system_messages + recent_messages
            self.truncated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "summary": self.summary,
            "total_tokens": self.total_tokens,
            "truncated_at": self.truncated_at.isoformat() if self.truncated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationHistory':
        """Create from dictionary format"""
        return cls(
            session_id=data["session_id"],
            messages=[ConversationMessage.from_dict(msg) for msg in data.get("messages", [])],
            summary=data.get("summary"),
            total_tokens=data.get("total_tokens", 0),
            truncated_at=datetime.fromisoformat(data["truncated_at"]) if data.get("truncated_at") else None
        )


class LangSwarmSession:
    """
    Main session class for unified conversation management
    
    Provides a unified interface for session management across all providers
    with intelligent handling of native vs client-side session management.
    """
    
    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        provider: str = "openai",
        model: str = "gpt-4o",
        session_control: SessionControl = SessionControl.HYBRID,
        context_limit: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize a LangSwarm session
        
        Args:
            user_id: Unique user identifier
            session_id: Optional session ID (auto-generated if not provided)
            provider: LLM provider name
            model: Model name
            session_control: Session control strategy
            context_limit: Maximum context window size
            **kwargs: Additional session configuration
        """
        from uuid import uuid4
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = f"session_{uuid4().hex[:8]}"
        
        # Initialize metadata
        self.metadata = SessionMetadata(
            user_id=user_id,
            session_id=session_id,
            provider=provider,
            model=model,
            session_control=session_control,
            context_limit=context_limit,
            **{k: v for k, v in kwargs.items() if hasattr(SessionMetadata, k)}
        )
        
        # Initialize conversation history
        self.history = ConversationHistory(session_id=session_id)
        
        # Session adapter will be set by SessionManager
        self._adapter = None
        self._manager = None
    
    @property
    def session_id(self) -> str:
        """Get session ID"""
        return self.metadata.session_id
    
    @property
    def user_id(self) -> str:
        """Get user ID"""
        return self.metadata.user_id
    
    @property
    def provider(self) -> str:
        """Get provider"""
        return self.metadata.provider
    
    @property
    def model(self) -> str:
        """Get model"""
        return self.metadata.model
    
    @property
    def message_count(self) -> int:
        """Get message count"""
        return len(self.history.messages)
    
    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.metadata.status == SessionStatus.ACTIVE
    
    def add_message(self, content: str, role: MessageRole, **kwargs) -> ConversationMessage:
        """Add a message to the session"""
        from uuid import uuid4
        
        message = ConversationMessage(
            id=f"msg_{uuid4().hex[:8]}",
            role=role,
            content=content,
            **kwargs
        )
        
        self.history.add_message(message)
        self.metadata.message_count = len(self.history.messages)
        self.metadata.last_activity = datetime.now()
        self.metadata.updated_at = datetime.now()
        
        return message
    
    def get_messages(self, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Get conversation messages"""
        if limit:
            return self.history.get_recent_messages(limit)
        return self.history.messages
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Get messages in API format (role/content)"""
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {})
            }
            for msg in self.history.messages
        ]
    
    def archive(self) -> None:
        """Archive the session"""
        self.metadata.status = SessionStatus.ARCHIVED
        self.metadata.updated_at = datetime.now()
    
    def reactivate(self) -> None:
        """Reactivate an archived session"""
        self.metadata.status = SessionStatus.ACTIVE
        self.metadata.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format"""
        return {
            "metadata": self.metadata.to_dict(),
            "history": self.history.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LangSwarmSession':
        """Create session from dictionary format"""
        metadata = SessionMetadata.from_dict(data["metadata"])
        session = cls(
            user_id=metadata.user_id,
            session_id=metadata.session_id,
            provider=metadata.provider,
            model=metadata.model,
            session_control=metadata.session_control,
            context_limit=metadata.context_limit
        )
        session.metadata = metadata
        session.history = ConversationHistory.from_dict(data["history"])
        return session 