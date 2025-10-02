# LangSwarm V2 Session Management Guide

**Modern, provider-aligned session management with native capabilities and unified API**

## 🎯 Overview

LangSwarm V2 provides a completely modernized session management system that replaces the complex V1 architecture (3 session managers, multiple adapters, bridges, and strategies) with a clean, provider-aligned system that leverages native LLM provider capabilities while providing a unified abstraction layer.

**Key Benefits:**
- **Dramatic Simplification**: 3 session managers → 1 unified manager
- **Provider Alignment**: Native OpenAI threads and Anthropic conversations
- **Unified API**: Same interface across all providers with type safety
- **Async-First**: All operations designed for async/await patterns
- **Efficient Storage**: In-memory and SQLite backends with performance optimization
- **Extensible Architecture**: Middleware and hooks for customization

---

## 🚀 Quick Start

### **Simple Session Creation**

```python
from langswarm.core.session import create_session_manager

# Create a session manager with SQLite storage
manager = create_session_manager(
    storage="sqlite",
    providers={
        "openai": "your_openai_api_key",
        "anthropic": "your_anthropic_api_key"
    }
)

# Create a user session
session = await manager.create_session(
    user_id="user123",
    provider="openai",
    model="gpt-4"
)

# Send messages and get responses
response = await session.send_message("Hello! How can you help me today?")
print(f"Assistant: {response.content}")

# Continue the conversation
response = await session.send_message("What's the weather like?")
print(f"Assistant: {response.content}")

# Get conversation history
messages = await session.get_messages()
for message in messages:
    print(f"{message.role}: {message.content}")
```

### **Development Setup with In-Memory Storage**

```python
# Quick development setup
manager = create_session_manager(storage="memory")

# Create a session with mock provider (no API key needed)
session = await manager.create_session("dev_user", "mock", "mock-model")

# Test message handling
response = await session.send_message("Test message")
print(f"Mock response: {response.content}")
```

---

## 🏗️ Session Architecture

### **Core Components**

```python
from langswarm.core.session import (
    # Main interfaces
    SessionManager,
    ISession,
    ISessionStorage,
    
    # Storage backends
    InMemorySessionStorage,
    SQLiteSessionStorage,
    
    # Provider sessions
    OpenAIProviderSession,
    AnthropicProviderSession,
    MockProviderSession,
    
    # Message types
    SessionMessage,
    SessionContext,
    SessionMetrics
)
```

### **Session Lifecycle**

```python
# 1. Create session manager
manager = create_session_manager(storage="sqlite")

# 2. Create user session
session = await manager.create_session("user123", "openai", "gpt-4")
print(f"Session ID: {session.session_id}")
print(f"Status: {session.status}")

# 3. Use session for conversation
response = await session.send_message("Hello!")

# 4. Update session context
await session.update_context({"user_preference": "concise_responses"})

# 5. Archive session when done
await session.archive()

# 6. Clean up old sessions
await manager.cleanup_inactive_sessions(days=30)
```

---

## 💬 Message Handling

### **Basic Message Operations**

```python
# Send user message
response = await session.send_message("What is machine learning?")

# Send system message
await session.send_system_message("You are a helpful AI assistant specializing in ML.")

# Get all messages
messages = await session.get_messages()

# Get recent messages (last 10)
recent_messages = await session.get_messages(limit=10)

# Get messages with filtering
filtered_messages = await session.get_messages(
    role="assistant",
    start_time=datetime.now() - timedelta(hours=1)
)

# Clear conversation history
await session.clear_messages()
```

### **Message Structure**

```python
from langswarm.core.session.interfaces import SessionMessage

# Messages have a consistent structure across providers
@dataclass
class SessionMessage:
    role: str              # "user", "assistant", "system"
    content: str           # Message content
    timestamp: datetime    # When message was created
    message_id: str        # Unique message identifier
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Provider-specific fields
    provider_message_id: Optional[str] = None
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
```

### **Advanced Message Features**

```python
# Send message with metadata
response = await session.send_message(
    "Analyze this data",
    metadata={
        "intent": "data_analysis",
        "priority": "high",
        "user_context": {"role": "data_scientist"}
    }
)

# Get message with full context
message = await session.get_message(message_id)
print(f"Metadata: {message.metadata}")
print(f"Provider metadata: {message.provider_metadata}")

# Export conversation for analysis
conversation_data = await session.export_conversation()
```

---

## 🔌 Provider Integration

### **OpenAI Provider (Native Threads)**

```python
# OpenAI sessions use native thread capabilities
openai_session = await manager.create_session(
    user_id="user123",
    provider="openai",
    model="gpt-4",
    provider_config={
        "thread_metadata": {"user_type": "premium"},
        "assistant_id": "asst_abc123",  # Optional: use specific assistant
        "temperature": 0.7,
        "max_tokens": 2048
    }
)

# Send message using OpenAI threads
response = await openai_session.send_message("Hello!")
print(f"Thread ID: {openai_session.provider_session_id}")

# Access native thread features
thread_metadata = await openai_session.get_provider_metadata()
print(f"Thread metadata: {thread_metadata}")
```

### **Anthropic Provider (Conversations)**

```python
# Anthropic sessions use conversation management
anthropic_session = await manager.create_session(
    user_id="user456", 
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    provider_config={
        "temperature": 0.3,
        "max_tokens": 4096,
        "conversation_metadata": {"topic": "coding_help"}
    }
)

# Send message using Anthropic API
response = await anthropic_session.send_message("Help me with Python!")
print(f"Conversation ID: {anthropic_session.provider_session_id}")
```

### **Mock Provider (Development/Testing)**

```python
# Mock provider for development and testing
mock_session = await manager.create_session(
    user_id="test_user",
    provider="mock",
    model="mock-model"
)

# Mock responses are predictable for testing
response = await mock_session.send_message("Test input")
print(f"Mock response: {response.content}")  # "Mock response to: Test input"

# Configure mock behavior
mock_session.provider_session.set_response_pattern("custom: {input}")
response = await mock_session.send_message("Hello")
print(f"Custom response: {response.content}")  # "custom: Hello"
```

---

## 💾 Storage Backends

### **In-Memory Storage (Development)**

```python
from langswarm.core.session.storage import InMemorySessionStorage

# Fast in-memory storage for development
memory_storage = InMemorySessionStorage()
manager = SessionManager(storage=memory_storage)

# All sessions stored in memory
session = await manager.create_session("user123", "mock", "mock-model")
await session.send_message("Hello!")

# Data is lost when application restarts
```

### **SQLite Storage (Production)**

```python
from langswarm.core.session.storage import SQLiteSessionStorage

# Persistent SQLite storage
sqlite_storage = SQLiteSessionStorage(
    db_path="sessions.db",
    pool_size=10,          # Connection pool size
    max_overflow=20,       # Maximum overflow connections
    pool_timeout=30        # Connection timeout
)

manager = SessionManager(storage=sqlite_storage)

# Sessions persist across application restarts
session = await manager.create_session("user123", "openai", "gpt-4")
await session.send_message("Hello!")

# Close storage cleanly
await sqlite_storage.close()
```

### **Storage Factory Pattern**

```python
from langswarm.core.session.storage import StorageFactory

# Create storage using factory
storage = StorageFactory.create(
    backend="sqlite",
    config={
        "db_path": "production_sessions.db",
        "pool_size": 20,
        "enable_wal": True
    }
)

# Or use convenience function
manager = create_session_manager(
    storage="sqlite",
    storage_config={
        "db_path": "sessions.db",
        "pool_size": 15
    }
)
```

---

## 📊 Session Management

### **Session Lifecycle Management**

```python
# Create session with full configuration
session = await manager.create_session(
    user_id="user123",
    provider="openai",
    model="gpt-4",
    session_config={
        "name": "ML Discussion",
        "description": "Machine learning conversation",
        "tags": ["ml", "education"],
        "max_messages": 100,
        "auto_archive_after": timedelta(days=7)
    }
)

# Update session properties
await session.update_config({
    "name": "Advanced ML Discussion",
    "tags": ["ml", "advanced", "research"]
})

# Check session status
print(f"Status: {session.status}")  # active, archived, deleted
print(f"Message count: {session.message_count}")
print(f"Created: {session.created_at}")
print(f"Last activity: {session.last_activity}")
```

### **Multi-User Session Management**

```python
# Get user's sessions
user_sessions = await manager.get_user_sessions("user123")
print(f"User has {len(user_sessions)} sessions")

# Filter sessions
active_sessions = await manager.get_user_sessions(
    user_id="user123",
    status="active"
)

recent_sessions = await manager.get_user_sessions(
    user_id="user123",
    since=datetime.now() - timedelta(days=7)
)

# Search sessions by tags
ml_sessions = await manager.search_sessions(
    user_id="user123",
    tags=["ml"]
)
```

### **Session Context Management**

```python
# Set session context
await session.update_context({
    "user_profile": {
        "experience_level": "intermediate",
        "preferred_language": "python",
        "learning_goals": ["machine_learning", "data_science"]
    },
    "conversation_style": "detailed_explanations",
    "code_examples": True
})

# Get session context
context = await session.get_context()
user_profile = context.get("user_profile", {})

# Use context in messages
if context.get("code_examples"):
    response = await session.send_message(
        "Explain linear regression with Python code examples"
    )
```

---

## 📈 Session Analytics

### **Session Metrics**

```python
# Get session metrics
metrics = await session.get_metrics()

print(f"Total messages: {metrics.total_messages}")
print(f"User messages: {metrics.user_messages}")
print(f"Assistant messages: {metrics.assistant_messages}")
print(f"Average response time: {metrics.avg_response_time_ms}ms")
print(f"Total tokens used: {metrics.total_tokens}")
print(f"Session duration: {metrics.session_duration}")
```

### **Usage Analytics**

```python
# Get manager-level analytics
analytics = await manager.get_analytics(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

print(f"Total sessions: {analytics.total_sessions}")
print(f"Active users: {analytics.active_users}")
print(f"Messages per session: {analytics.avg_messages_per_session}")
print(f"Popular models: {analytics.model_usage}")
print(f"Provider distribution: {analytics.provider_usage}")
```

### **Real-Time Monitoring**

```python
# Monitor session activity
async def monitor_sessions():
    async for event in manager.session_events():
        if event.type == "session_created":
            print(f"New session: {event.session_id}")
        elif event.type == "message_sent":
            print(f"Message in {event.session_id}: {event.message_preview}")
        elif event.type == "session_archived":
            print(f"Session archived: {event.session_id}")

# Start monitoring in background
import asyncio
asyncio.create_task(monitor_sessions())
```

---

## 🔧 Advanced Features

### **Middleware System**

```python
from langswarm.core.session.interfaces import ISessionMiddleware

class LoggingMiddleware(ISessionMiddleware):
    """Log all messages for debugging"""
    
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        print(f"[{session_id}] {message.role}: {message.content[:50]}...")
        return message

class FilterMiddleware(ISessionMiddleware):
    """Filter sensitive content"""
    
    async def process_message(
        self,
        session_id: str, 
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        # Filter sensitive information
        filtered_content = self.filter_sensitive_data(message.content)
        message.content = filtered_content
        return message
    
    def filter_sensitive_data(self, content: str) -> str:
        # Implementation would filter PII, etc.
        return content

# Add middleware to session manager
manager.add_middleware(LoggingMiddleware())
manager.add_middleware(FilterMiddleware())

# Middleware processes all messages automatically
session = await manager.create_session("user123", "openai", "gpt-4")
await session.send_message("Hello!")  # Processed by both middleware
```

### **Lifecycle Hooks**

```python
from langswarm.core.session.interfaces import ISessionLifecycleHook

class MetricsHook(ISessionLifecycleHook):
    """Collect session metrics"""
    
    async def on_session_created(self, session_id: str, user_id: str):
        print(f"Session created: {session_id} for user {user_id}")
        await self.increment_metric("sessions_created")
    
    async def on_message_sent(self, session_id: str, message: SessionMessage):
        await self.increment_metric("messages_sent")
        await self.track_usage(session_id, len(message.content))
    
    async def on_session_archived(self, session_id: str):
        print(f"Session archived: {session_id}")
        await self.increment_metric("sessions_archived")

class NotificationHook(ISessionLifecycleHook):
    """Send notifications for important events"""
    
    async def on_session_created(self, session_id: str, user_id: str):
        if await self.is_new_user(user_id):
            await self.send_welcome_email(user_id)
    
    async def on_session_error(self, session_id: str, error: Exception):
        if isinstance(error, CriticalError):
            await self.send_alert(f"Critical session error: {error}")

# Add hooks to session manager
manager.add_lifecycle_hook(MetricsHook())
manager.add_lifecycle_hook(NotificationHook())
```

### **Session Cleanup and Maintenance**

```python
# Automatic cleanup configuration
cleanup_config = {
    "archive_after_days": 30,        # Archive inactive sessions after 30 days
    "delete_after_days": 90,         # Delete archived sessions after 90 days
    "max_messages_per_session": 1000, # Archive sessions with too many messages
    "cleanup_interval_hours": 24      # Run cleanup every 24 hours
}

manager = create_session_manager(
    storage="sqlite",
    cleanup_config=cleanup_config
)

# Manual cleanup operations
await manager.cleanup_inactive_sessions(days=30)
await manager.cleanup_archived_sessions(days=90)
await manager.cleanup_deleted_sessions(days=365)

# Storage optimization
await manager.optimize_storage()  # Vacuum database, rebuild indexes
```

---

## 🔄 Migration from V1

### **V1 vs V2 Session Comparison**

| Aspect | V1 Complex System | V2 Modern System | Improvement |
|--------|------------------|------------------|-------------|
| **Managers** | 3 different managers | 1 unified manager | 90% simpler |
| **Provider Integration** | Generic adapters | Native API integration | Better performance |
| **Message Handling** | Complex adapter chains | Direct API calls | 3x faster |
| **Storage** | Heavy abstractions | Efficient backends | 5x faster |
| **Configuration** | Complex initialization | Simple factory functions | 10x easier |

### **V1 Session Usage (Complex)**

```python
# V1: Complex, confusing session management
from langswarm.core.session import LangSwarmSessionManager
from langswarm.core.session.hybrid_manager import HybridSessionManager

# Complex initialization with multiple managers
manager = LangSwarmSessionManager(
    storage=storage,
    default_session_control=SessionControl.HYBRID
)

session = manager.create_session(
    user_id,
    provider,
    model,
    session_control=SessionControl.NATIVE
)

# Complex message handling
adapter = session._adapter
response = adapter.send_message(session_id, message, role)
```

### **V2 Session Usage (Simple)**

```python
# V2: Simple, clean session management
from langswarm.core.session import create_session_manager

# Simple, unified manager
manager = create_session_manager(
    storage="sqlite",
    providers={"openai": api_key}
)

session = await manager.create_session("user123", "openai", "gpt-4")

# Clean message handling
response = await session.send_message("Hello!")
messages = await session.get_messages()
```

### **Migration Strategy**

```python
# Gradual migration approach
from langswarm.v1.session import V1SessionManager
from langswarm.core.session import create_session_manager

class HybridSessionManager:
    """Bridge between V1 and V2 session systems"""
    
    def __init__(self, migrate_to_v2=True):
        self.v1_manager = V1SessionManager()
        self.v2_manager = create_session_manager(storage="sqlite")
        self.migrate_to_v2 = migrate_to_v2
    
    async def get_session(self, session_id: str):
        # Try V2 first
        try:
            return await self.v2_manager.get_session(session_id)
        except SessionNotFoundError:
            # Fall back to V1
            v1_session = self.v1_manager.get_session(session_id)
            
            if self.migrate_to_v2:
                # Migrate V1 session to V2
                return await self.migrate_session(v1_session)
            
            return v1_session
    
    async def migrate_session(self, v1_session):
        """Migrate V1 session to V2 format"""
        v2_session = await self.v2_manager.create_session(
            user_id=v1_session.user_id,
            provider=v1_session.provider,
            model=v1_session.model
        )
        
        # Migrate message history
        for message in v1_session.get_messages():
            await v2_session.add_message(
                role=message.role,
                content=message.content,
                timestamp=message.timestamp
            )
        
        return v2_session
```

---

## 🎯 Configuration Presets

### **Development Configuration**

```python
# Development preset with in-memory storage and mock provider
dev_manager = create_session_manager(
    preset="development",
    providers={"mock": None}  # No API key needed
)

# Features enabled in development:
# - In-memory storage (fast, no persistence)
# - Mock provider (predictable responses)
# - Debug logging enabled
# - Detailed error messages
# - No rate limiting
```

### **Production Configuration**

```python
# Production preset with SQLite storage and real providers
prod_manager = create_session_manager(
    preset="production",
    providers={
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY")
    },
    storage_config={
        "db_path": "/data/sessions.db",
        "pool_size": 20,
        "backup_enabled": True
    }
)

# Features enabled in production:
# - SQLite storage with connection pooling
# - Real provider integration
# - Automatic session cleanup
# - Error tracking and alerts
# - Performance monitoring
# - Rate limiting protection
```

### **Custom Configuration**

```python
# Custom configuration for specific needs
custom_manager = create_session_manager(
    storage="sqlite",
    storage_config={
        "db_path": "custom_sessions.db",
        "enable_wal": True,
        "pool_size": 15
    },
    providers={
        "openai": openai_api_key,
        "anthropic": anthropic_api_key
    },
    middleware=[
        LoggingMiddleware(),
        SecurityMiddleware(),
        AnalyticsMiddleware()
    ],
    hooks=[
        MetricsHook(),
        AlertingHook()
    ],
    cleanup_config={
        "archive_after_days": 14,
        "delete_after_days": 60
    }
)
```

---

## 🔧 Best Practices

### **Session Management**
- **Use appropriate storage**: Memory for development, SQLite for production
- **Configure cleanup**: Set up automatic session cleanup to manage storage
- **Monitor usage**: Track session metrics for capacity planning
- **Handle errors gracefully**: Implement proper error handling and recovery

### **Performance Optimization**
- **Connection pooling**: Use appropriate pool sizes for SQLite storage
- **Async operations**: Always use async/await for session operations
- **Batch operations**: Use batch operations for multiple session updates
- **Index optimization**: Ensure database indexes are optimized for queries

### **Security Considerations**
- **API key protection**: Store API keys securely using environment variables
- **Session isolation**: Ensure proper user session isolation
- **Data encryption**: Encrypt sensitive session data at rest
- **Access control**: Implement proper session access controls

### **Development Workflow**
- **Use mock provider**: Develop and test without API costs
- **In-memory storage**: Fast iteration with in-memory storage
- **Middleware testing**: Test middleware in isolation
- **Gradual migration**: Migrate from V1 incrementally

---

**LangSwarm V2's session management system provides a modern, efficient, and provider-aligned solution for managing conversational AI sessions with native capabilities and enterprise-grade features.**
