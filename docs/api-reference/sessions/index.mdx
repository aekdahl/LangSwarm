# LangSwarm V2 Session Management API Reference

**Complete API reference for the V2 session management system**

## 🎯 Overview

LangSwarm V2's session management API provides a comprehensive, type-safe interface for managing conversational AI sessions. The API replaces the complex V1 session architecture with a clean, provider-aligned system that leverages native LLM provider capabilities while providing a unified abstraction layer.

**Core Modules:**
- **`interfaces`**: Type-safe session interfaces and data structures
- **`base`**: Core session implementation with unified management
- **`storage`**: Efficient storage backends (in-memory, SQLite)
- **`providers`**: Native provider integration (OpenAI, Anthropic, Mock)

---

## 📦 Package API

### **Main Package Interface**

```python
from langswarm.core.session import (
    # Session Management
    create_session_manager,
    create_simple_session,
    SessionManager,
    
    # Session Interfaces
    ISession,
    ISessionManager,
    ISessionStorage,
    IProviderSession,
    ISessionMiddleware,
    ISessionLifecycleHook,
    
    # Session Data Structures
    SessionMessage,
    SessionContext,
    SessionMetrics,
    SessionConfig,
    SessionStatus,
    
    # Storage Backends
    InMemorySessionStorage,
    SQLiteSessionStorage,
    StorageFactory,
    
    # Provider Sessions
    OpenAIProviderSession,
    AnthropicProviderSession,
    MockProviderSession,
    ProviderSessionFactory,
    
    # Middleware & Hooks
    BaseSessionMiddleware,
    BaseSessionLifecycleHook,
    
    # Configuration
    SessionManagerConfig,
    StorageConfig,
    ProviderConfig,
    
    # Exceptions
    SessionError,
    SessionNotFoundError,
    StorageError,
    ProviderError
)
```

---

## 🏗️ Core Interfaces

### **ISession**

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

class ISession(ABC):
    """Core session interface for conversational AI interactions"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Unique session identifier"""
    
    @property
    @abstractmethod
    def user_id(self) -> str:
        """User identifier for this session"""
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """LLM provider (openai, anthropic, etc.)"""
    
    @property
    @abstractmethod
    def model(self) -> str:
        """Model name"""
    
    @property
    @abstractmethod
    def status(self) -> SessionStatus:
        """Current session status"""
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Session creation timestamp"""
    
    @property
    @abstractmethod
    def last_activity(self) -> datetime:
        """Last activity timestamp"""
    
    @property
    @abstractmethod
    def message_count(self) -> int:
        """Number of messages in session"""
    
    @abstractmethod
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message and get response"""
    
    @abstractmethod
    async def send_system_message(
        self,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send system message"""
    
    @abstractmethod
    async def get_messages(
        self,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[SessionMessage]:
        """Retrieve messages with optional filtering"""
    
    @abstractmethod
    async def get_message(self, message_id: str) -> SessionMessage:
        """Get specific message by ID"""
    
    @abstractmethod
    async def clear_messages(self) -> None:
        """Clear all messages from session"""
    
    @abstractmethod
    async def update_context(self, context: Dict[str, Any]) -> None:
        """Update session context"""
    
    @abstractmethod
    async def get_context(self) -> SessionContext:
        """Get current session context"""
    
    @abstractmethod
    async def get_metrics(self) -> SessionMetrics:
        """Get session usage metrics"""
    
    @abstractmethod
    async def archive(self) -> None:
        """Archive the session"""
    
    @abstractmethod
    async def delete(self) -> None:
        """Delete the session"""
    
    @abstractmethod
    async def export_conversation(self) -> Dict[str, Any]:
        """Export conversation data"""
```

### **ISessionManager**

```python
class ISessionManager(ABC):
    """Session manager interface for creating and managing sessions"""
    
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        provider: str,
        model: str,
        session_config: Optional[SessionConfig] = None,
        provider_config: Optional[Dict[str, Any]] = None
    ) -> ISession:
        """Create a new session"""
    
    @abstractmethod
    async def get_session(self, session_id: str) -> ISession:
        """Retrieve session by ID"""
    
    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[ISession]:
        """Get user's sessions with filtering"""
    
    @abstractmethod
    async def search_sessions(
        self,
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[ISession]:
        """Search sessions with criteria"""
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete session by ID"""
    
    @abstractmethod
    async def archive_session(self, session_id: str) -> None:
        """Archive session by ID"""
    
    @abstractmethod
    async def cleanup_inactive_sessions(
        self,
        days: int = 30,
        status: Optional[SessionStatus] = None
    ) -> int:
        """Clean up inactive sessions"""
    
    @abstractmethod
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get session analytics"""
    
    @abstractmethod
    def add_middleware(self, middleware: ISessionMiddleware) -> None:
        """Add message processing middleware"""
    
    @abstractmethod
    def add_lifecycle_hook(self, hook: ISessionLifecycleHook) -> None:
        """Add session lifecycle hook"""
```

### **ISessionStorage**

```python
class ISessionStorage(ABC):
    """Storage backend interface for session persistence"""
    
    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str,
        config: SessionConfig,
        context: SessionContext
    ) -> None:
        """Create session in storage"""
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
    
    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update session data"""
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete session from storage"""
    
    @abstractmethod
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List sessions with filtering"""
    
    @abstractmethod
    async def add_message(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Add message to session"""
    
    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[SessionMessage]:
        """Get session messages"""
    
    @abstractmethod
    async def clear_messages(self, session_id: str) -> None:
        """Clear all messages from session"""
    
    @abstractmethod
    async def update_context(
        self,
        session_id: str,
        context: SessionContext
    ) -> None:
        """Update session context"""
    
    @abstractmethod
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get storage analytics"""
    
    @abstractmethod
    async def cleanup(
        self,
        older_than: datetime,
        status: Optional[SessionStatus] = None
    ) -> int:
        """Clean up old sessions"""
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check storage health"""
    
    @abstractmethod
    async def close(self) -> None:
        """Close storage connections"""
```

---

## 🔧 Data Structures

### **SessionMessage**

```python
@dataclass
class SessionMessage:
    """Unified message format across all providers"""
    
    message_id: str
    session_id: str
    role: str                    # "user", "assistant", "system"
    content: str
    timestamp: datetime
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Provider-specific fields
    provider_message_id: Optional[str] = None
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Message metrics
    token_count: Optional[int] = None
    processing_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMessage':
        """Create from dictionary"""
        
    def to_provider_format(self, provider: str) -> Dict[str, Any]:
        """Convert to provider-specific format"""
```

### **SessionContext**

```python
@dataclass
class SessionContext:
    """Session context and metadata"""
    
    session_id: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    provider_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    
    # Context versioning
    version: int = 1
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update context with new values"""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get context value with dot notation support"""
        
    def set(self, key: str, value: Any) -> None:
        """Set context value with dot notation support"""
        
    def merge(self, other_context: 'SessionContext') -> None:
        """Merge with another context"""
```

### **SessionConfig**

```python
@dataclass
class SessionConfig:
    """Session configuration and settings"""
    
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Limits and timeouts
    max_messages: Optional[int] = None
    max_tokens_per_message: Optional[int] = None
    session_timeout_minutes: Optional[int] = None
    
    # Auto-management
    auto_archive_after: Optional[timedelta] = None
    auto_delete_after: Optional[timedelta] = None
    
    # Provider-specific settings
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate configuration and return errors"""
        
    def merge_with(self, other: 'SessionConfig') -> 'SessionConfig':
        """Merge with another configuration"""
```

### **SessionMetrics**

```python
@dataclass
class SessionMetrics:
    """Session usage metrics and analytics"""
    
    session_id: str
    
    # Message metrics
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    system_messages: int = 0
    
    # Token metrics
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Timing metrics
    session_duration: timedelta = field(default_factory=lambda: timedelta(0))
    avg_response_time_ms: float = 0.0
    total_response_time_ms: float = 0.0
    
    # Usage metrics
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    
    # Provider metrics
    provider_calls: int = 0
    provider_errors: int = 0
    
    # Cost metrics (if available)
    estimated_cost: Optional[float] = None
    
    def update_with_message(self, message: SessionMessage) -> None:
        """Update metrics with new message"""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/export"""
```

### **SessionStatus**

```python
from enum import Enum

class SessionStatus(Enum):
    """Session status enumeration"""
    
    ACTIVE = "active"           # Session is active and can receive messages
    IDLE = "idle"              # Session is idle (no recent activity)
    ARCHIVED = "archived"       # Session is archived (read-only)
    DELETED = "deleted"         # Session is marked for deletion
    ERROR = "error"            # Session has errors
    
    @classmethod
    def from_string(cls, value: str) -> 'SessionStatus':
        """Convert string to enum value"""
        
    def is_active(self) -> bool:
        """Check if session accepts new messages"""
        
    def can_transition_to(self, new_status: 'SessionStatus') -> bool:
        """Check if transition to new status is valid"""
```

---

## 🏭 Session Manager

### **SessionManager**

```python
class SessionManager(ISessionManager):
    """Main session manager implementation"""
    
    def __init__(
        self,
        storage: ISessionStorage,
        provider_factory: ProviderSessionFactory,
        config: Optional[SessionManagerConfig] = None
    ):
        """Initialize session manager"""
        
    async def create_session(
        self,
        user_id: str,
        provider: str,
        model: str,
        session_config: Optional[SessionConfig] = None,
        provider_config: Optional[Dict[str, Any]] = None
    ) -> ISession:
        """Create new session with provider integration"""
        
    async def get_session(self, session_id: str) -> ISession:
        """Retrieve existing session"""
        
    async def get_user_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[ISession]:
        """Get user sessions with filtering"""
        
    async def search_sessions(
        self,
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[ISession]:
        """Search sessions with multiple criteria"""
        
    async def delete_session(self, session_id: str) -> None:
        """Delete session and cleanup resources"""
        
    async def archive_session(self, session_id: str) -> None:
        """Archive session (make read-only)"""
        
    async def cleanup_inactive_sessions(
        self,
        days: int = 30,
        status: Optional[SessionStatus] = None
    ) -> int:
        """Clean up old/inactive sessions"""
        
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        
    def add_middleware(self, middleware: ISessionMiddleware) -> None:
        """Add message processing middleware"""
        
    def add_lifecycle_hook(self, hook: ISessionLifecycleHook) -> None:
        """Add session lifecycle event hook"""
        
    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage performance"""
        
    async def export_sessions(
        self,
        user_id: Optional[str] = None,
        format: str = "json"
    ) -> Any:
        """Export session data"""
        
    async def health_check(self) -> Dict[str, Any]:
        """Check manager and storage health"""
        
    async def close(self) -> None:
        """Close manager and cleanup resources"""
```

### **Convenience Functions**

```python
def create_session_manager(
    storage: Union[str, ISessionStorage] = "memory",
    providers: Dict[str, str] = None,
    storage_config: Dict[str, Any] = None,
    provider_config: Dict[str, Any] = None,
    middleware: List[ISessionMiddleware] = None,
    hooks: List[ISessionLifecycleHook] = None,
    preset: Optional[str] = None
) -> SessionManager:
    """Create session manager with configuration
    
    Args:
        storage: Storage backend ("memory", "sqlite", or ISessionStorage instance)
        providers: Provider API keys {"openai": "key", "anthropic": "key"}
        storage_config: Storage-specific configuration
        provider_config: Provider-specific configuration
        middleware: List of middleware to add
        hooks: List of lifecycle hooks to add
        preset: Configuration preset ("development", "production")
        
    Returns:
        Configured SessionManager instance
    """

async def create_simple_session(
    user_id: str,
    provider: str = "mock",
    model: str = "mock-model",
    storage: str = "memory"
) -> ISession:
    """Create simple session for quick testing
    
    Args:
        user_id: User identifier
        provider: LLM provider
        model: Model name
        storage: Storage backend
        
    Returns:
        Ready-to-use session instance
    """
```

---

## 💾 Storage Backends

### **InMemorySessionStorage**

```python
class InMemorySessionStorage(ISessionStorage):
    """Fast in-memory storage for development and testing"""
    
    def __init__(self, max_sessions: int = 1000):
        """Initialize in-memory storage
        
        Args:
            max_sessions: Maximum number of sessions to store
        """
        
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str,
        config: SessionConfig,
        context: SessionContext
    ) -> None:
        """Create session in memory"""
        
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from memory"""
        
    async def health_check(self) -> Dict[str, Any]:
        """Check memory usage and performance"""
        
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage statistics"""
        
    async def clear_all(self) -> None:
        """Clear all sessions (testing utility)"""
```

### **SQLiteSessionStorage**

```python
class SQLiteSessionStorage(ISessionStorage):
    """Persistent SQLite storage for production use"""
    
    def __init__(
        self,
        db_path: str = "sessions.db",
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        enable_wal: bool = True,
        auto_vacuum: bool = True
    ):
        """Initialize SQLite storage
        
        Args:
            db_path: Database file path
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Connection timeout seconds
            enable_wal: Enable WAL mode for better concurrency
            auto_vacuum: Enable automatic database vacuuming
        """
        
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str,
        config: SessionConfig,
        context: SessionContext
    ) -> None:
        """Create session in SQLite database"""
        
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from database"""
        
    async def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        
    async def backup_database(self, backup_path: str) -> None:
        """Create database backup"""
        
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
    async def migrate_schema(self, target_version: int) -> None:
        """Migrate database schema to target version"""
```

### **StorageFactory**

```python
class StorageFactory:
    """Factory for creating storage backend instances"""
    
    @staticmethod
    def create(
        backend: str,
        config: Dict[str, Any] = None
    ) -> ISessionStorage:
        """Create storage backend instance
        
        Args:
            backend: Backend type ("memory", "sqlite")
            config: Backend-specific configuration
            
        Returns:
            Storage backend instance
            
        Raises:
            ValueError: If backend type is not supported
        """
        
    @staticmethod
    def register_backend(
        name: str,
        backend_class: type,
        config_schema: Dict[str, Any] = None
    ) -> None:
        """Register custom storage backend"""
        
    @staticmethod
    def list_backends() -> List[str]:
        """List available storage backends"""
```

---

## 🔌 Provider Sessions

### **IProviderSession**

```python
class IProviderSession(ABC):
    """Interface for provider-specific session implementations"""
    
    @property
    @abstractmethod
    def provider_session_id(self) -> Optional[str]:
        """Provider-specific session ID (e.g., OpenAI thread ID)"""
        
    @abstractmethod
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message using provider API"""
        
    @abstractmethod
    async def get_provider_metadata(self) -> Dict[str, Any]:
        """Get provider-specific metadata"""
        
    @abstractmethod
    async def update_provider_config(self, config: Dict[str, Any]) -> None:
        """Update provider-specific configuration"""
        
    @abstractmethod
    async def cleanup_provider_resources(self) -> None:
        """Clean up provider-specific resources"""
```

### **OpenAIProviderSession**

```python
class OpenAIProviderSession(IProviderSession):
    """OpenAI provider session using native threads API"""
    
    def __init__(
        self,
        api_key: str,
        session_id: str,
        model: str,
        config: Dict[str, Any] = None
    ):
        """Initialize OpenAI provider session
        
        Args:
            api_key: OpenAI API key
            session_id: LangSwarm session ID
            model: OpenAI model name
            config: OpenAI-specific configuration
        """
        
    @property
    def thread_id(self) -> Optional[str]:
        """OpenAI thread ID"""
        
    async def create_thread(
        self,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create OpenAI thread"""
        
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message to OpenAI thread"""
        
    async def get_thread_messages(self) -> List[SessionMessage]:
        """Get all messages from OpenAI thread"""
        
    async def update_thread_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update OpenAI thread metadata"""
        
    async def delete_thread(self) -> None:
        """Delete OpenAI thread"""
        
    async def get_thread_runs(self) -> List[Dict[str, Any]]:
        """Get thread runs information"""
```

### **AnthropicProviderSession**

```python
class AnthropicProviderSession(IProviderSession):
    """Anthropic provider session using conversation management"""
    
    def __init__(
        self,
        api_key: str,
        session_id: str,
        model: str,
        config: Dict[str, Any] = None
    ):
        """Initialize Anthropic provider session
        
        Args:
            api_key: Anthropic API key
            session_id: LangSwarm session ID
            model: Anthropic model name
            config: Anthropic-specific configuration
        """
        
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message using Anthropic API"""
        
    async def get_conversation_history(self) -> List[SessionMessage]:
        """Get conversation history"""
        
    async def update_system_prompt(self, system_prompt: str) -> None:
        """Update system prompt for conversation"""
        
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
```

### **MockProviderSession**

```python
class MockProviderSession(IProviderSession):
    """Mock provider session for testing and development"""
    
    def __init__(
        self,
        session_id: str,
        model: str = "mock-model",
        config: Dict[str, Any] = None
    ):
        """Initialize mock provider session
        
        Args:
            session_id: LangSwarm session ID
            model: Mock model name
            config: Mock-specific configuration
        """
        
    def set_response_pattern(self, pattern: str) -> None:
        """Set response pattern for mock responses
        
        Args:
            pattern: Response pattern with {input} placeholder
        """
        
    def set_response_delay(self, delay_ms: float) -> None:
        """Set artificial delay for responses"""
        
    def set_error_rate(self, error_rate: float) -> None:
        """Set error rate for testing error handling"""
        
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message and get mock response"""
```

### **ProviderSessionFactory**

```python
class ProviderSessionFactory:
    """Factory for creating provider session instances"""
    
    def __init__(self, provider_configs: Dict[str, Dict[str, Any]]):
        """Initialize factory with provider configurations
        
        Args:
            provider_configs: Provider configurations
                {
                    "openai": {"api_key": "key"},
                    "anthropic": {"api_key": "key"},
                    "mock": {}
                }
        """
        
    async def create_provider_session(
        self,
        provider: str,
        session_id: str,
        model: str,
        config: Dict[str, Any] = None
    ) -> IProviderSession:
        """Create provider session instance"""
        
    def register_provider(
        self,
        name: str,
        provider_class: type,
        default_config: Dict[str, Any] = None
    ) -> None:
        """Register custom provider"""
        
    def list_providers(self) -> List[str]:
        """List available providers"""
        
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get provider information and capabilities"""
```

---

## 🔧 Middleware System

### **ISessionMiddleware**

```python
class ISessionMiddleware(ABC):
    """Interface for session message middleware"""
    
    @abstractmethod
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Process message before storage/sending
        
        Args:
            session_id: Session identifier
            message: Message to process
            context: Session context
            
        Returns:
            Processed message
        """
        
    async def on_error(
        self,
        session_id: str,
        error: Exception,
        context: SessionContext
    ) -> None:
        """Handle middleware errors"""
        pass
```

### **BaseSessionMiddleware**

```python
class BaseSessionMiddleware(ISessionMiddleware):
    """Base middleware with common functionality"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Base implementation - override in subclasses"""
        return message
        
    def should_process(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> bool:
        """Determine if message should be processed"""
        return True
```

### **Built-in Middleware**

```python
class LoggingMiddleware(BaseSessionMiddleware):
    """Log all messages for debugging and monitoring"""
    
    def __init__(self, log_level: str = "INFO", include_content: bool = True):
        super().__init__()
        self.log_level = log_level
        self.include_content = include_content

class SecurityMiddleware(BaseSessionMiddleware):
    """Filter sensitive information and validate content"""
    
    def __init__(self, filters: List[str] = None):
        super().__init__()
        self.filters = filters or ["ssn", "credit_card", "email"]

class MetricsMiddleware(BaseSessionMiddleware):
    """Collect message and session metrics"""
    
    def __init__(self, metrics_collector: Any = None):
        super().__init__()
        self.metrics_collector = metrics_collector

class RateLimitMiddleware(BaseSessionMiddleware):
    """Apply rate limiting to messages"""
    
    def __init__(self, messages_per_minute: int = 60):
        super().__init__()
        self.messages_per_minute = messages_per_minute
```

---

## 🔗 Lifecycle Hooks

### **ISessionLifecycleHook**

```python
class ISessionLifecycleHook(ABC):
    """Interface for session lifecycle event hooks"""
    
    async def on_session_created(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str
    ) -> None:
        """Called when session is created"""
        pass
        
    async def on_session_deleted(self, session_id: str) -> None:
        """Called when session is deleted"""
        pass
        
    async def on_session_archived(self, session_id: str) -> None:
        """Called when session is archived"""
        pass
        
    async def on_message_sent(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Called when message is sent"""
        pass
        
    async def on_message_received(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Called when message is received"""
        pass
        
    async def on_context_updated(
        self,
        session_id: str,
        context: SessionContext
    ) -> None:
        """Called when context is updated"""
        pass
        
    async def on_session_error(
        self,
        session_id: str,
        error: Exception
    ) -> None:
        """Called when session error occurs"""
        pass
```

### **Built-in Hooks**

```python
class MetricsCollectionHook(ISessionLifecycleHook):
    """Collect comprehensive session metrics"""
    
    def __init__(self, metrics_backend: Any = None):
        self.metrics_backend = metrics_backend

class AlertingHook(ISessionLifecycleHook):
    """Send alerts for important session events"""
    
    def __init__(self, alert_config: Dict[str, Any] = None):
        self.alert_config = alert_config

class AuditLoggingHook(ISessionLifecycleHook):
    """Log all session events for audit purposes"""
    
    def __init__(self, audit_logger: Any = None):
        self.audit_logger = audit_logger

class CleanupHook(ISessionLifecycleHook):
    """Automatic cleanup of session resources"""
    
    def __init__(self, cleanup_config: Dict[str, Any] = None):
        self.cleanup_config = cleanup_config
```

---

## ❌ Exception Handling

### **Session Exceptions**

```python
class SessionError(Exception):
    """Base session management error"""
    
    def __init__(
        self,
        message: str,
        session_id: str = None,
        error_code: str = None,
        context: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.session_id = session_id
        self.error_code = error_code
        self.context = context or {}

class SessionNotFoundError(SessionError):
    """Session not found in storage"""

class SessionStateError(SessionError):
    """Invalid session state for operation"""

class StorageError(SessionError):
    """Storage backend error"""

class ProviderError(SessionError):
    """LLM provider error"""

class MiddlewareError(SessionError):
    """Middleware processing error"""

class ConfigurationError(SessionError):
    """Session configuration error"""

# Usage with error handling
try:
    session = await manager.get_session("session_123")
except SessionNotFoundError:
    session = await manager.create_session("user123", "openai", "gpt-4")
except ProviderError as e:
    logger.error(f"Provider error: {e}")
    # Fall back to mock provider
    session = await manager.create_session("user123", "mock", "mock-model")
except SessionError as e:
    logger.error(f"Session error: {e}")
    raise
```

---

## 🌍 Global Session Management

### **Global Session Manager**

```python
# Global session manager for application-wide access
_global_session_manager: Optional[SessionManager] = None

def set_global_session_manager(manager: SessionManager) -> None:
    """Set global session manager instance"""
    global _global_session_manager
    _global_session_manager = manager

def get_global_session_manager() -> Optional[SessionManager]:
    """Get global session manager instance"""
    return _global_session_manager

async def get_or_create_session(
    user_id: str,
    provider: str = "mock",
    model: str = "mock-model"
) -> ISession:
    """Get or create session using global manager"""
    manager = get_global_session_manager()
    if not manager:
        raise SessionError("No global session manager configured")
    
    # Try to find existing active session
    sessions = await manager.get_user_sessions(
        user_id=user_id,
        status=SessionStatus.ACTIVE,
        limit=1
    )
    
    if sessions:
        return sessions[0]
    
    # Create new session
    return await manager.create_session(user_id, provider, model)

# Context manager for session management
class SessionContext:
    """Context manager for session operations"""
    
    def __init__(self, session: ISession):
        self.session = session
        
    async def __aenter__(self) -> ISession:
        return self.session
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Handle errors, maybe archive session
            await self.session.archive()
        # Session cleanup handled by manager
```

---

**LangSwarm V2's session management API provides a comprehensive, type-safe interface for managing conversational AI sessions with native provider capabilities, efficient storage, and enterprise-grade features.**
