# LangSwarm V2 Memory System API Reference

**Complete API documentation for the unified LangSwarm V2 memory system**

## 🎯 Overview

LangSwarm V2 introduces a completely unified memory system that dramatically simplifies the complex V1 memory ecosystem. The new system provides clean, type-safe interfaces aligned with major LLM providers, supporting multiple backend storage options with a 75% reduction in complexity.

**Key Features:**
- **Unified Interface**: All memory operations through consistent API
- **LLM Provider Alignment**: Native OpenAI and Anthropic format support
- **Multiple Backends**: SQLite, Redis, In-Memory storage options
- **Type Safety**: Full type annotations with async/await support
- **Session Management**: Complete conversation lifecycle management
- **Auto-Summarization**: Intelligent conversation summarization

---

## 🏗️ Memory Architecture

### **Core Interfaces**

```python
from langswarm.core.memory.interfaces import (
    Message, SessionMetadata, ConversationSummary,
    IMemorySession, IMemoryBackend, IMemoryManager
)

# Universal message format aligned with LLM providers
@dataclass
class Message:
    role: MessageRole  # system, user, assistant, tool
    content: str
    timestamp: datetime
    message_id: str
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    function_call: Optional[Dict[str, Any]] = None  # OpenAI format
    tool_calls: Optional[List[Dict[str, Any]]] = None  # Multi-tool support

# Session configuration and state
@dataclass 
class SessionMetadata:
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE
    max_messages: int = 1000
    max_tokens: int = 32000
    auto_summarize_threshold: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

# Automatic conversation summarization
@dataclass
class ConversationSummary:
    summary_id: str
    session_id: str
    summary_text: str
    message_count: int
    token_count: int
    created_at: datetime
    summary_type: SummaryType  # auto, manual, periodic
```

### **Memory Session Interface**

```python
class IMemorySession:
    """Core interface for memory session operations"""
    
    # Properties
    session_id: str
    metadata: SessionMetadata
    
    # Message operations
    async def add_message(self, message: Message) -> None:
        """Add a message to the session"""
        pass
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        roles: Optional[List[MessageRole]] = None
    ) -> List[Message]:
        """Retrieve messages with optional filtering"""
        pass
    
    async def get_recent_messages(self, token_limit: int = 4000) -> List[Message]:
        """Get recent messages within token limit"""
        pass
    
    async def get_conversation_context(self, max_tokens: int = 8000) -> List[Message]:
        """Get conversation context optimized for LLM providers"""
        pass
    
    # Session management
    async def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update session metadata"""
        pass
    
    async def archive_session(self) -> None:
        """Archive the session"""
        pass
    
    async def delete_session(self) -> None:
        """Delete the session and all messages"""
        pass
    
    # Summarization
    async def create_summary(self, summary_type: SummaryType = SummaryType.AUTO) -> ConversationSummary:
        """Create conversation summary"""
        pass
    
    async def get_summaries(self) -> List[ConversationSummary]:
        """Get all summaries for this session"""
        pass
```

### **Memory Backend Interface**

```python
class IMemoryBackend:
    """Core interface for memory storage backends"""
    
    # Connection management
    async def connect(self) -> None:
        """Connect to the backend storage"""
        pass
    
    async def disconnect(self) -> None:
        """Disconnect from backend storage"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health and connectivity"""
        pass
    
    # Session operations
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new memory session"""
        pass
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Retrieve existing session"""
        pass
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions with filtering and pagination"""
        pass
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass
    
    # Cleanup operations
    async def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions"""
        pass
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get backend usage statistics"""
        pass
```

### **Memory Manager Interface**

```python
class IMemoryManager:
    """Unified memory management interface"""
    
    # Manager properties
    backend: IMemoryBackend
    
    # Session management
    async def create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **metadata
    ) -> IMemorySession:
        """Create new session with optional metadata"""
        pass
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get existing session"""
        pass
    
    async def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> IMemorySession:
        """Get existing session or create new one"""
        pass
    
    # Global operations
    async def cleanup_all_sessions(self, max_age_days: int = 30) -> int:
        """Clean up all expired sessions"""
        pass
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide memory statistics"""
        pass
    
    async def shutdown(self) -> None:
        """Shutdown memory manager and cleanup resources"""
        pass
```

---

## 🔧 Backend Implementations

### **In-Memory Backend**

```python
from langswarm.core.memory.backends import InMemoryBackend

# Fast development and testing backend
backend = InMemoryBackend()

# Features:
- Zero setup required
- Fast operations (sub-millisecond)
- Session persistence during runtime
- No external dependencies
- Perfect for development and testing

# Usage:
await backend.connect()
session = await backend.create_session(SessionMetadata(
    session_id="test_session",
    user_id="user_123"
))
```

### **SQLite Backend**

```python
from langswarm.core.memory.backends import SQLiteBackend

# Persistent local storage backend
backend = SQLiteBackend(
    db_path="memory.db",  # or ":memory:" for in-memory SQLite
    enable_wal=True,      # Write-Ahead Logging for performance
    enable_foreign_keys=True
)

# Features:
- File and memory modes
- Automatic schema management
- Indexed queries for performance
- Transaction safety with rollback
- Foreign key referential integrity

# Usage:
await backend.connect()  # Creates database and tables automatically
session = await backend.create_session(metadata)
messages = await session.get_messages(limit=50)
```

### **Redis Backend**

```python
from langswarm.core.memory.backends import RedisBackend

# Distributed high-performance storage
backend = RedisBackend(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    pool_size=10,
    ttl_seconds=86400  # 24 hour TTL
)

# Features:
- Connection pooling
- TTL-based session expiration
- Key namespacing for organization
- JSON serialization/deserialization
- Cloud Redis compatibility

# Usage:
await backend.connect()
session = await backend.create_session(metadata)
# Sessions automatically expire based on TTL
```

---

## ⚙️ Configuration System

### **Configuration Patterns**

```python
from langswarm.core.memory import initialize_memory, create_memory_manager

# Pattern 1: Boolean configuration (auto-select backend)
initialize_memory(memory=True)  # → InMemoryBackend for development

# Pattern 2: Environment-based configuration
initialize_memory(memory="development")   # → InMemoryBackend
initialize_memory(memory="testing")       # → SQLite in-memory
initialize_memory(memory="production")    # → SQLite file-based

# Pattern 3: Backend-specific configuration
initialize_memory(memory="sqlite")        # → SQLite with defaults
initialize_memory(memory="redis")         # → Redis with defaults

# Pattern 4: Custom configuration
memory_config = {
    "backend": "sqlite",
    "config": {
        "db_path": "/data/memory.db",
        "enable_wal": True,
        "pool_size": 20
    }
}
initialize_memory(memory=memory_config)

# Pattern 5: Direct manager creation
manager = create_memory_manager(
    backend="redis",
    host="redis.example.com",
    port=6379,
    password="secret"
)
```

### **Memory Factory**

```python
from langswarm.core.memory.factory import MemoryFactory, MemoryConfiguration

# Factory for backend creation
factory = MemoryFactory()

# Register custom backend
factory.register_backend("custom", CustomBackend)

# Create manager with validation
config = MemoryConfiguration.from_string("development")
manager = await factory.create_manager(config)

# Auto-detection of available backends
available_backends = factory.get_available_backends()
print(f"Available: {available_backends}")  # ['in_memory', 'sqlite', 'redis']
```

---

## 💬 LLM Provider Integration

### **OpenAI Format Support**

```python
from langswarm.core.memory import (
    create_openai_message, 
    messages_to_openai_format,
    MemorySessionContext
)

# Create OpenAI-compatible messages
user_msg = create_openai_message("user", "Hello, how are you?")
assistant_msg = create_openai_message("assistant", "I'm doing well, thank you!")

# Function call support
function_msg = create_openai_message(
    "assistant", 
    content=None,
    function_call={
        "name": "get_weather",
        "arguments": '{"location": "San Francisco"}'
    }
)

# Add to session
async with MemorySessionContext(user_id="user123") as session:
    await session.add_message(user_msg)
    await session.add_message(assistant_msg)
    await session.add_message(function_msg)
    
    # Get in OpenAI format for API calls
    openai_messages = messages_to_openai_format(await session.get_messages())
    
    # Direct OpenAI API usage
    import openai
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=openai_messages
    )
```

### **Anthropic Format Support**

```python
from langswarm.core.memory import (
    create_anthropic_message,
    messages_to_anthropic_format
)

# Create Anthropic-compatible messages
user_msg = create_anthropic_message("user", "Analyze this document")
assistant_msg = create_anthropic_message("assistant", "I'll analyze it for you.")

# Tool call support
tool_msg = create_anthropic_message(
    "assistant",
    content=[
        {"type": "text", "text": "I'll use a tool to help."},
        {
            "type": "tool_use",
            "id": "tool_123",
            "name": "document_analyzer",
            "input": {"document": "content"}
        }
    ]
)

# Convert to Anthropic format
async with MemorySessionContext(user_id="user123") as session:
    await session.add_message(user_msg)
    await session.add_message(tool_msg)
    
    # Get in Anthropic format
    anthropic_messages = messages_to_anthropic_format(await session.get_messages())
    
    # Direct Anthropic API usage
    import anthropic
    client = anthropic.Anthropic()
    response = await client.messages.create(
        model="claude-3-opus-20240229",
        messages=anthropic_messages,
        max_tokens=1000
    )
```

### **Universal Message Format**

```python
# Universal format works with any provider
from langswarm.core.memory.interfaces import Message, MessageRole

# Create universal message
universal_msg = Message(
    role=MessageRole.USER,
    content="What's the weather like?",
    metadata={"location": "user_query"}
)

# System message with function definitions
system_msg = Message(
    role=MessageRole.SYSTEM,
    content="You are a helpful assistant with access to weather tools.",
    metadata={
        "functions": [
            {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        ]
    }
)

# Tool response message
tool_msg = Message(
    role=MessageRole.TOOL,
    content='{"temperature": 72, "condition": "sunny"}',
    metadata={
        "tool_call_id": "call_123",
        "tool_name": "get_weather"
    }
)
```

---

## 📊 Session Management

### **Session Lifecycle**

```python
from langswarm.core.memory import get_global_memory_manager
from langswarm.core.memory.interfaces import SessionStatus

# Get global memory manager
memory = get_global_memory_manager()

# Create session with metadata
session = await memory.create_session(
    user_id="user_123",
    session_id="chat_456",
    max_messages=500,
    max_tokens=16000,
    auto_summarize_threshold=50,
    custom_metadata={"app": "chatbot", "version": "2.0"}
)

# Add conversation messages
await session.add_message(create_openai_message("user", "Hello!"))
await session.add_message(create_openai_message("assistant", "Hi there!"))

# Get recent conversation context
context = await session.get_conversation_context(max_tokens=4000)
print(f"Context has {len(context)} messages")

# Update session configuration
await session.update_metadata({
    "max_tokens": 32000,
    "custom_field": "value"
})

# Archive session when done
await session.archive_session()
```

### **Message Filtering and Retrieval**

```python
from langswarm.core.memory.interfaces import MessageRole
from datetime import datetime, timedelta

# Get messages with filtering
recent_messages = await session.get_messages(
    limit=20,
    since=datetime.now() - timedelta(hours=1),
    roles=[MessageRole.USER, MessageRole.ASSISTANT]
)

# Get conversation context optimized for token limits
context = await session.get_recent_messages(token_limit=4000)

# Get all user messages
user_messages = await session.get_messages(roles=[MessageRole.USER])

# Get messages since specific time
morning_messages = await session.get_messages(
    since=datetime.now().replace(hour=9, minute=0, second=0)
)
```

### **Conversation Summarization**

```python
from langswarm.core.memory.interfaces import SummaryType

# Automatic summarization (triggered by threshold)
# No action needed - happens automatically when message count exceeds threshold

# Manual summarization
summary = await session.create_summary(summary_type=SummaryType.MANUAL)
print(f"Summary: {summary.summary_text}")
print(f"Covers {summary.message_count} messages, {summary.token_count} tokens")

# Get all summaries
summaries = await session.get_summaries()
for summary in summaries:
    print(f"{summary.created_at}: {summary.summary_text[:100]}...")

# Periodic summarization (automated background process)
# Configure during session creation:
session = await memory.create_session(
    user_id="user_123",
    auto_summarize_threshold=100,  # Summarize every 100 messages
    summary_strategy="periodic"    # or "rolling", "manual"
)
```

---

## 🔍 Analytics and Monitoring

### **Usage Statistics**

```python
# Backend-level statistics
backend_stats = await memory.backend.get_usage_stats()
print(f"Total sessions: {backend_stats['total_sessions']}")
print(f"Total messages: {backend_stats['total_messages']}")
print(f"Storage size: {backend_stats['storage_size_mb']}MB")

# System-wide statistics
system_stats = await memory.get_system_stats()
print(f"Active sessions: {system_stats['active_sessions']}")
print(f"Archived sessions: {system_stats['archived_sessions']}")
print(f"Messages per session (avg): {system_stats['avg_messages_per_session']}")
print(f"Memory usage: {system_stats['memory_usage_mb']}MB")

# Session-specific analytics
session_stats = {
    "message_count": len(await session.get_messages()),
    "token_count": sum(msg.token_count or 0 for msg in await session.get_messages()),
    "conversation_duration": session.metadata.updated_at - session.metadata.created_at,
    "summary_count": len(await session.get_summaries())
}
```

### **Health Monitoring**

```python
# Backend health check
health = await memory.backend.health_check()
print(f"Backend status: {health['status']}")      # healthy/degraded/unhealthy
print(f"Connection: {health['connected']}")        # True/False
print(f"Response time: {health['response_time_ms']}ms")
print(f"Last error: {health.get('last_error', 'None')}")

# Check specific backend features
if health['status'] == 'healthy':
    # Safe to perform operations
    session = await memory.get_or_create_session("user_123")
else:
    print(f"Backend unhealthy: {health.get('error', 'Unknown error')}")
    # Implement fallback or retry logic
```

### **Cleanup and Maintenance**

```python
# Clean up expired sessions
expired_count = await memory.cleanup_all_sessions(max_age_days=30)
print(f"Cleaned up {expired_count} expired sessions")

# Backend-specific cleanup
if isinstance(memory.backend, SQLiteBackend):
    # Vacuum database to reclaim space
    await memory.backend.vacuum_database()

if isinstance(memory.backend, RedisBackend):
    # Redis cleanup happens automatically via TTL
    ttl_info = await memory.backend.get_ttl_stats()
    print(f"Sessions expiring in next hour: {ttl_info['expiring_1h']}")

# Manual session cleanup
inactive_sessions = await memory.backend.list_sessions(
    status=SessionStatus.ACTIVE,
    limit=1000
)

for session_meta in inactive_sessions:
    if session_meta.updated_at < datetime.now() - timedelta(days=7):
        await memory.backend.delete_session(session_meta.session_id)
```

---

## 🔧 Context Managers

### **MemorySessionContext**

```python
from langswarm.core.memory import MemorySessionContext

# Basic session context (auto-creates session)
async with MemorySessionContext(user_id="user_123") as session:
    await session.add_message(create_openai_message("user", "Hello!"))
    messages = await session.get_messages()
    # Session automatically managed

# Specific session ID
async with MemorySessionContext(session_id="existing_session") as session:
    await session.add_message(create_openai_message("user", "Continue chat"))
    # Uses existing session or creates with this ID

# Custom session configuration
async with MemorySessionContext(
    user_id="user_123",
    max_tokens=16000,
    auto_summarize_threshold=50
) as session:
    # Session created with custom configuration
    await session.add_message(create_openai_message("user", "Start conversation"))

# Error handling
try:
    async with MemorySessionContext(user_id="user_123") as session:
        await session.add_message(invalid_message)
except MemoryError as e:
    print(f"Memory error: {e}")
    # Session is properly cleaned up even on error
```

### **Global Memory Context**

```python
from langswarm.core.memory import (
    setup_global_memory,
    get_global_memory_manager,
    shutdown_global_memory
)

# Application startup
async def startup():
    await setup_global_memory("production")
    print("Memory system initialized")

# Application usage
async def handle_request(user_id: str, message: str):
    memory = get_global_memory_manager()
    session = await memory.get_or_create_session(user_id)
    
    await session.add_message(create_openai_message("user", message))
    context = await session.get_conversation_context()
    
    return context

# Application shutdown
async def shutdown():
    await shutdown_global_memory()
    print("Memory system shut down")
```

---

## 🔄 Migration Support

### **V1 to V2 Migration Interface**

```python
from langswarm.core.memory.interfaces import IMemoryMigrator

class V1MemoryMigrator(IMemoryMigrator):
    """Migrate V1 memory data to V2 format"""
    
    async def migrate_sessions(
        self,
        source_backend: str,
        target_backend: IMemoryBackend,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Migrate sessions from V1 to V2"""
        pass
    
    async def migrate_messages(
        self,
        session_mapping: Dict[str, str],
        target_backend: IMemoryBackend
    ) -> Dict[str, Any]:
        """Migrate messages with session mapping"""
        pass
    
    async def validate_migration(
        self,
        source_stats: Dict[str, Any],
        target_stats: Dict[str, Any]
    ) -> bool:
        """Validate migration completeness"""
        pass

# Usage
migrator = V1MemoryMigrator()
migration_result = await migrator.migrate_sessions(
    source_backend="v1_sqlite",
    target_backend=memory.backend
)
```

---

## 📚 Best Practices

### **Performance Optimization**
- **Connection Pooling**: Use Redis backend for high-concurrency applications
- **Token Limits**: Set appropriate `max_tokens` for conversation context
- **Batch Operations**: Process multiple messages together when possible
- **Cleanup Strategy**: Implement regular cleanup of expired sessions

### **Memory Management**
- **Session Limits**: Set reasonable `max_messages` to prevent unbounded growth
- **Auto-Summarization**: Use automatic summarization for long conversations
- **Backend Selection**: Choose appropriate backend for your use case
- **Monitoring**: Monitor memory usage and session statistics

### **Security Considerations**
- **User Isolation**: Ensure proper user_id isolation in multi-tenant applications
- **Data Encryption**: Use encrypted Redis backends for sensitive data
- **Access Control**: Implement proper authentication before session access
- **Data Retention**: Follow data retention policies with automated cleanup

### **Error Handling**
- **Graceful Degradation**: Implement fallback strategies for backend failures
- **Connection Recovery**: Handle backend reconnection scenarios
- **Transaction Safety**: Use proper transaction handling for data consistency
- **Monitoring Alerts**: Set up alerts for backend health issues

---

**The LangSwarm V2 memory system provides a clean, unified interface for conversation management with native LLM provider support, multiple backend options, and production-ready features for scalable AI applications.**
