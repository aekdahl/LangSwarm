# LangSwarm V2 Memory User Guide

**Learn how to use the unified LangSwarm V2 memory system for conversation management**

## 🎯 Overview

LangSwarm V2 completely transforms memory management with a unified, simple system that replaces the complex V1 memory ecosystem. Store and retrieve conversations with native LLM provider support, automatic summarization, and multiple backend options.

**Key Benefits:**
- **75% Complexity Reduction**: Simple patterns replace complex configurations
- **LLM Provider Alignment**: Native OpenAI and Anthropic format support  
- **Multiple Backends**: SQLite, Redis, In-Memory storage options
- **Session Management**: Complete conversation lifecycle management
- **Auto-Summarization**: Intelligent conversation summarization

---

## 🚀 Quick Start

### **Simple Memory Setup**

```python
from langswarm.core.memory import initialize_memory, MemorySessionContext

# One-line setup for development
initialize_memory("development")

# Start using memory immediately
async with MemorySessionContext(user_id="user123") as session:
    # Add a user message
    from langswarm.core.memory import create_openai_message
    await session.add_message(create_openai_message("user", "Hello!"))
    
    # Add assistant response
    await session.add_message(create_openai_message("assistant", "Hi there! How can I help?"))
    
    # Get conversation history
    messages = await session.get_messages()
    print(f"Conversation has {len(messages)} messages")
```

### **Different Environment Setups**

```python
# Development - fast in-memory storage
initialize_memory("development")

# Testing - SQLite in-memory database
initialize_memory("testing") 

# Production - persistent SQLite database
initialize_memory("production")

# Custom configuration
initialize_memory(memory={
    "backend": "redis",
    "config": {
        "host": "redis.example.com",
        "port": 6379
    }
})
```

---

## 💾 Storage Backends

### **In-Memory Backend (Development)**

Perfect for development and testing:

```python
# Automatic selection for development
initialize_memory("development")

# Features:
# - Zero setup required
# - Fastest performance
# - No external dependencies  
# - Data lost when application stops
# - Perfect for testing
```

### **SQLite Backend (Local Persistence)**

Local file-based storage:

```python
# Automatic SQLite setup
initialize_memory("production")

# Custom SQLite configuration
initialize_memory(memory={
    "backend": "sqlite",
    "config": {
        "db_path": "/data/conversations.db",
        "enable_wal": True  # Better performance
    }
})

# Features:
# - Persistent local storage
# - No external services required
# - ACID transactions
# - Great for single-server deployments
```

### **Redis Backend (Distributed)**

High-performance distributed storage:

```python
# Redis configuration
initialize_memory(memory={
    "backend": "redis", 
    "config": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "optional_password",
        "pool_size": 10,
        "ttl_seconds": 86400  # 24 hour session expiration
    }
})

# Features:
# - High performance
# - Distributed/clustered support
# - Automatic session expiration
# - Perfect for multi-server deployments
```

---

## 💬 Working with Messages

### **Creating Messages**

```python
from langswarm.core.memory import (
    create_openai_message, 
    create_anthropic_message,
    MemorySessionContext
)

async with MemorySessionContext(user_id="user123") as session:
    # User messages
    user_msg = create_openai_message("user", "What's the weather like?")
    await session.add_message(user_msg)
    
    # Assistant responses
    assistant_msg = create_openai_message("assistant", "I'll check the weather for you.")
    await session.add_message(assistant_msg)
    
    # System messages
    system_msg = create_openai_message("system", "You are a helpful weather assistant.")
    await session.add_message(system_msg)
    
    # Tool/function calls
    function_msg = create_openai_message(
        "assistant",
        content=None,
        function_call={
            "name": "get_weather",
            "arguments": '{"location": "San Francisco"}'
        }
    )
    await session.add_message(function_msg)
```

### **Retrieving Messages**

```python
# Get all messages
all_messages = await session.get_messages()

# Get recent messages (last 20)
recent_messages = await session.get_messages(limit=20)

# Get messages from last hour
from datetime import datetime, timedelta
recent_time = datetime.now() - timedelta(hours=1)
hour_messages = await session.get_messages(since=recent_time)

# Get only user and assistant messages
from langswarm.core.memory.interfaces import MessageRole
conversation = await session.get_messages(
    roles=[MessageRole.USER, MessageRole.ASSISTANT]
)

# Get conversation context for LLM (within token limit)
context = await session.get_conversation_context(max_tokens=4000)
print(f"Context: {len(context)} messages, ~4000 tokens")
```

### **Message Filtering**

```python
# Filter by role
user_messages = await session.get_messages(roles=[MessageRole.USER])
assistant_messages = await session.get_messages(roles=[MessageRole.ASSISTANT])

# Filter by time range
morning_messages = await session.get_messages(
    since=datetime.now().replace(hour=9, minute=0, second=0),
    limit=50
)

# Get recent messages within token budget
recent_context = await session.get_recent_messages(token_limit=2000)

# Combine filters
filtered_messages = await session.get_messages(
    limit=10,
    since=datetime.now() - timedelta(hours=2),
    roles=[MessageRole.USER, MessageRole.ASSISTANT]
)
```

---

## 🔄 Session Management

### **Creating and Managing Sessions**

```python
from langswarm.core.memory import get_global_memory_manager

memory = get_global_memory_manager()

# Create session with auto-generated ID
session = await memory.create_session(user_id="user123")
print(f"Created session: {session.session_id}")

# Create session with specific ID
session = await memory.create_session(
    user_id="user123",
    session_id="chat_conversation_1"
)

# Get existing session
existing_session = await memory.get_session("chat_conversation_1")
if existing_session:
    print("Found existing session")

# Get or create pattern (common pattern)
session = await memory.get_or_create_session(
    user_id="user123",
    session_id="default_chat"
)
```

### **Session Configuration**

```python
# Create session with custom configuration
session = await memory.create_session(
    user_id="user123",
    max_messages=500,              # Limit conversation length
    max_tokens=16000,             # Token limit for context
    auto_summarize_threshold=100,  # Summarize every 100 messages
    metadata={
        "app": "customer_support",
        "department": "technical",
        "priority": "high"
    }
)

# Update session configuration
await session.update_metadata({
    "max_tokens": 32000,  # Increase token limit
    "status": "escalated",
    "assigned_agent": "agent_456"
})
```

### **Session Lifecycle**

```python
# Active session (default)
session = await memory.create_session(user_id="user123")
# Session is automatically active

# Archive session when conversation ends
await session.archive_session()
print("Session archived - no longer active")

# Delete session and all messages (permanent)
await session.delete_session()
print("Session deleted permanently")

# List user's sessions
from langswarm.core.memory.interfaces import SessionStatus

user_sessions = await memory.backend.list_sessions(
    user_id="user123",
    status=SessionStatus.ACTIVE,
    limit=20
)

for session_meta in user_sessions:
    print(f"Session {session_meta.session_id}: {session_meta.created_at}")
```

---

## 🤖 LLM Provider Integration

### **OpenAI Integration**

```python
import openai
from langswarm.core.memory import messages_to_openai_format

# Get conversation context
async with MemorySessionContext(user_id="user123") as session:
    # Add user message
    await session.add_message(create_openai_message("user", "Explain quantum computing"))
    
    # Get context for OpenAI API
    context_messages = await session.get_conversation_context(max_tokens=3000)
    openai_format = messages_to_openai_format(context_messages)
    
    # Call OpenAI API
    client = openai.AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=openai_format,
        max_tokens=1000
    )
    
    # Save assistant response
    assistant_message = create_openai_message("assistant", response.choices[0].message.content)
    await session.add_message(assistant_message)
```

### **Anthropic Integration**

```python
import anthropic
from langswarm.core.memory import messages_to_anthropic_format

# Get conversation context
async with MemorySessionContext(user_id="user123") as session:
    # Add user message
    await session.add_message(create_anthropic_message("user", "Write a poem about the ocean"))
    
    # Get context for Anthropic API
    context_messages = await session.get_conversation_context(max_tokens=8000)
    anthropic_format = messages_to_anthropic_format(context_messages)
    
    # Call Anthropic API
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-3-opus-20240229",
        messages=anthropic_format,
        max_tokens=1000
    )
    
    # Save assistant response
    assistant_message = create_anthropic_message("assistant", response.content[0].text)
    await session.add_message(assistant_message)
```

### **Function and Tool Calls**

```python
# OpenAI function calling
function_call_msg = create_openai_message(
    "assistant",
    content=None,
    function_call={
        "name": "search_knowledge_base",
        "arguments": '{"query": "machine learning", "limit": 5}'
    }
)
await session.add_message(function_call_msg)

# Function result
function_result = create_openai_message(
    "function",
    content='{"results": ["ML basics", "Neural networks", "Deep learning"]}',
    name="search_knowledge_base"
)
await session.add_message(function_result)

# Anthropic tool usage
tool_use_msg = create_anthropic_message(
    "assistant",
    content=[
        {"type": "text", "text": "I'll search for that information."},
        {
            "type": "tool_use",
            "id": "tool_123",
            "name": "web_search",
            "input": {"query": "latest AI research"}
        }
    ]
)
await session.add_message(tool_use_msg)

# Tool result
tool_result_msg = create_anthropic_message(
    "user",
    content=[
        {
            "type": "tool_result",
            "tool_use_id": "tool_123",
            "content": "Found 10 recent papers on AI research..."
        }
    ]
)
await session.add_message(tool_result_msg)
```

---

## 📝 Conversation Summarization

### **Automatic Summarization**

```python
# Configure auto-summarization when creating session
session = await memory.create_session(
    user_id="user123",
    auto_summarize_threshold=50  # Summarize every 50 messages
)

# Add messages - summarization happens automatically
for i in range(60):  # This will trigger auto-summarization
    await session.add_message(create_openai_message("user", f"Message {i}"))
    await session.add_message(create_openai_message("assistant", f"Response {i}"))

# Check summaries
summaries = await session.get_summaries()
print(f"Created {len(summaries)} automatic summaries")
```

### **Manual Summarization**

```python
from langswarm.core.memory.interfaces import SummaryType

# Create manual summary
summary = await session.create_summary(summary_type=SummaryType.MANUAL)
print(f"Summary: {summary.summary_text}")
print(f"Covers {summary.message_count} messages")

# View all summaries
all_summaries = await session.get_summaries()
for summary in all_summaries:
    print(f"{summary.created_at}: {summary.summary_text[:100]}...")
    print(f"  Type: {summary.summary_type}")
    print(f"  Messages: {summary.message_count}")
    print(f"  Tokens: {summary.token_count}")
```

### **Summary-Based Context**

```python
# Get context including summaries for very long conversations
full_context = await session.get_conversation_context(
    max_tokens=8000,
    include_summaries=True  # Include relevant summaries
)

# This gives you:
# 1. Relevant conversation summaries
# 2. Recent conversation messages
# 3. All within token limit
```

---

## 📊 Memory Analytics

### **Session Statistics**

```python
# Get session-level statistics
session_stats = {
    "total_messages": len(await session.get_messages()),
    "user_messages": len(await session.get_messages(roles=[MessageRole.USER])),
    "assistant_messages": len(await session.get_messages(roles=[MessageRole.ASSISTANT])),
    "total_tokens": sum(msg.token_count or 0 for msg in await session.get_messages()),
    "conversation_duration": session.metadata.updated_at - session.metadata.created_at,
    "summary_count": len(await session.get_summaries())
}

print(f"Session Statistics:")
for key, value in session_stats.items():
    print(f"  {key}: {value}")
```

### **System-Wide Analytics**

```python
# Get memory system statistics
memory = get_global_memory_manager()

# Backend usage statistics
backend_stats = await memory.backend.get_usage_stats()
print(f"Backend Statistics:")
print(f"  Total sessions: {backend_stats['total_sessions']}")
print(f"  Total messages: {backend_stats['total_messages']}")
print(f"  Storage size: {backend_stats.get('storage_size_mb', 'N/A')}MB")

# System-wide statistics
system_stats = await memory.get_system_stats()
print(f"System Statistics:")
print(f"  Active sessions: {system_stats['active_sessions']}")
print(f"  Average messages per session: {system_stats['avg_messages_per_session']}")
```

### **User Analytics**

```python
# Get all sessions for a user
user_sessions = await memory.backend.list_sessions(
    user_id="user123",
    limit=100
)

# Calculate user statistics
user_stats = {
    "total_sessions": len(user_sessions),
    "active_sessions": len([s for s in user_sessions if s.status == SessionStatus.ACTIVE]),
    "archived_sessions": len([s for s in user_sessions if s.status == SessionStatus.ARCHIVED]),
    "oldest_session": min(user_sessions, key=lambda s: s.created_at).created_at,
    "newest_session": max(user_sessions, key=lambda s: s.created_at).created_at
}

print(f"User {user_id} Statistics:")
for key, value in user_stats.items():
    print(f"  {key}: {value}")
```

---

## 🔧 Advanced Usage

### **Custom Message Metadata**

```python
# Add custom metadata to messages
from langswarm.core.memory.interfaces import Message, MessageRole
from datetime import datetime

custom_message = Message(
    role=MessageRole.USER,
    content="Help me with my project",
    timestamp=datetime.now(),
    message_id="msg_12345",
    metadata={
        "source": "mobile_app",
        "location": "San Francisco",
        "user_agent": "iOS App v2.1",
        "priority": "high",
        "department": "engineering"
    }
)

await session.add_message(custom_message)

# Query messages by metadata
messages_with_metadata = await session.get_messages()
high_priority = [
    msg for msg in messages_with_metadata 
    if msg.metadata.get("priority") == "high"
]
```

### **Batch Operations**

```python
# Add multiple messages efficiently
messages_to_add = [
    create_openai_message("user", "Question 1"),
    create_openai_message("assistant", "Answer 1"),
    create_openai_message("user", "Question 2"),
    create_openai_message("assistant", "Answer 2")
]

# Add messages in batch
for message in messages_to_add:
    await session.add_message(message)

# Note: Individual adds are atomic and safe
# Batch operations maintain consistency
```

### **Session Cleanup**

```python
# Clean up old sessions
memory = get_global_memory_manager()

# Clean up sessions older than 30 days
cleaned_count = await memory.cleanup_all_sessions(max_age_days=30)
print(f"Cleaned up {cleaned_count} old sessions")

# Manual cleanup with custom criteria
all_sessions = await memory.backend.list_sessions(limit=1000)
for session_meta in all_sessions:
    # Custom cleanup logic
    if (session_meta.status == SessionStatus.ARCHIVED and 
        (datetime.now() - session_meta.updated_at).days > 90):
        await memory.backend.delete_session(session_meta.session_id)
        print(f"Deleted old archived session: {session_meta.session_id}")
```

---

## 🚨 Error Handling

### **Connection Issues**

```python
from langswarm.core.memory.exceptions import MemoryConnectionError, MemoryError

try:
    # Initialize memory
    initialize_memory(memory={
        "backend": "redis",
        "config": {"host": "unreachable-host"}
    })
except MemoryConnectionError as e:
    print(f"Failed to connect to memory backend: {e}")
    # Fallback to local storage
    initialize_memory("development")
```

### **Session Errors**

```python
try:
    async with MemorySessionContext(user_id="user123") as session:
        await session.add_message(create_openai_message("user", "Hello"))
        messages = await session.get_messages()
        
except MemoryError as e:
    print(f"Memory operation failed: {e}")
    # Handle error gracefully
except Exception as e:
    print(f"Unexpected error: {e}")
    # Session context handles cleanup automatically
```

### **Graceful Degradation**

```python
# Implement fallback strategy
async def get_conversation_safely(user_id: str):
    try:
        memory = get_global_memory_manager()
        session = await memory.get_or_create_session(user_id)
        return await session.get_conversation_context()
    except MemoryError:
        # Fallback to empty conversation
        print("Memory unavailable, starting fresh conversation")
        return []
    except Exception as e:
        print(f"Unexpected memory error: {e}")
        return []
```

---

## 🔧 Production Tips

### **Performance Optimization**
- **Use Redis** for high-concurrency applications
- **Set token limits** appropriately for your LLM context windows
- **Enable auto-summarization** for long conversations
- **Monitor session cleanup** to prevent storage growth

### **Memory Management**
- **Set reasonable limits** on messages per session
- **Use session archiving** for completed conversations
- **Implement cleanup schedules** for old data
- **Monitor storage usage** regularly

### **Security Best Practices**
- **Isolate users** with proper user_id separation
- **Validate input** before storing messages
- **Use encrypted backends** for sensitive data
- **Implement access controls** in your application layer

### **Monitoring and Alerting**
- **Monitor backend health** with regular health checks
- **Track session and message counts** for capacity planning
- **Set up alerts** for connection failures
- **Monitor response times** for performance issues

---

## 📚 Complete Example

```python
import asyncio
from langswarm.core.memory import (
    initialize_memory, 
    MemorySessionContext, 
    create_openai_message,
    messages_to_openai_format
)

async def chatbot_example():
    """Complete example of memory usage in a chatbot"""
    
    # Initialize memory system
    initialize_memory("development")
    
    # Simulate a conversation
    user_id = "user_123"
    
    async with MemorySessionContext(
        user_id=user_id,
        max_tokens=4000,
        auto_summarize_threshold=20
    ) as session:
        
        # Add conversation messages
        conversations = [
            ("user", "Hi, I'm working on a Python project"),
            ("assistant", "Great! I'd be happy to help with Python. What are you building?"),
            ("user", "A web scraper using requests and BeautifulSoup"),
            ("assistant", "Excellent choice! What specific challenges are you facing?"),
            ("user", "How do I handle pagination in web scraping?"),
            ("assistant", "Here are several strategies for handling pagination...")
        ]
        
        for role, content in conversations:
            await session.add_message(create_openai_message(role, content))
        
        # Get conversation context for LLM
        context = await session.get_conversation_context(max_tokens=3000)
        print(f"Context has {len(context)} messages")
        
        # Convert to OpenAI format for API call
        openai_format = messages_to_openai_format(context)
        print(f"Ready for OpenAI API with {len(openai_format)} messages")
        
        # Get session statistics
        all_messages = await session.get_messages()
        print(f"Total conversation: {len(all_messages)} messages")
        
        # Check if summarization occurred
        summaries = await session.get_summaries()
        if summaries:
            print(f"Created {len(summaries)} summaries")
        
        return session.session_id

# Run the example
async def main():
    session_id = await chatbot_example()
    print(f"Conversation stored in session: {session_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

**LangSwarm V2 memory provides a simple, powerful way to manage AI conversations with native LLM provider support, automatic summarization, and production-ready features for scalable applications.**
