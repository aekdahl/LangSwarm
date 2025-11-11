# AgentMem

**Enterprise-grade conversational memory for AI agents**

AgentMem provides session-based conversation management, multiple storage backends, and seamless integration with major LLM providers.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/agentmem.svg)](https://pypi.org/project/agentmem/)

---

## Features

✨ **Session Management** - Organize conversations with persistent sessions  
💾 **Multiple Backends** - SQLite, Redis, In-Memory, and vector stores  
🔄 **Auto-Summarization** - Automatic conversation compression when limits reached  
📊 **Token Management** - Keep context within model limits  
🎯 **LLM Provider Integration** - Native OpenAI and Anthropic format support  
⚡ **Async First** - Built for high-performance async applications  

---

## Quick Start

### Installation

```bash
pip install agentmem
```

Optional dependencies:
```bash
pip install agentmem[redis]      # Redis backend
pip install agentmem[vector]     # Vector store support
pip install agentmem[chromadb]   # ChromaDB vector store
pip install agentmem[all]        # All optional dependencies
```

### Basic Usage

```python
import asyncio
from agentmem import create_memory_manager, Message, MessageRole

async def main():
    # Create memory manager with SQLite backend
    manager = create_memory_manager("sqlite", db_path="conversations.db")
    await manager.backend.connect()
    
    # Create a session
    session = await manager.create_session(user_id="user123")
    
    # Add messages
    await session.add_message(Message(
        role=MessageRole.USER,
        content="Hello! What's the capital of France?"
    ))
    
    await session.add_message(Message(
        role=MessageRole.ASSISTANT,
        content="The capital of France is Paris."
    ))
    
    # Get conversation history
    messages = await session.get_messages()
    print(f"Conversation has {len(messages)} messages")
    
    # Get recent context (token-limited)
    context = await session.get_recent_context(max_tokens=2000)

asyncio.run(main())
```

### With OpenAI

```python
import asyncio
from openai import AsyncOpenAI
from agentmem import create_memory_manager, Message, MessageRole

async def chat_with_memory(user_message: str, user_id: str = "default"):
    # Initialize
    openai_client = AsyncOpenAI()
    manager = create_memory_manager("sqlite", db_path="chat.db")
    await manager.backend.connect()
    
    # Get or create session
    session = await manager.get_or_create_session(
        session_id=f"session_{user_id}",
        user_id=user_id
    )
    
    # Add user message
    await session.add_message(Message(
        role=MessageRole.USER,
        content=user_message
    ))
    
    # Get conversation history
    messages = await session.get_messages()
    
    # Convert to OpenAI format
    openai_messages = [msg.to_openai_format() for msg in messages]
    
    # Get AI response
    response = await openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=openai_messages
    )
    
    assistant_message = response.choices[0].message.content
    
    # Save assistant response
    await session.add_message(Message(
        role=MessageRole.ASSISTANT,
        content=assistant_message
    ))
    
    return assistant_message

# Run
asyncio.run(chat_with_memory("What's the weather like?"))
```

---

## Backends

### In-Memory (Development)
```python
from agentmem import InMemoryBackend

backend = InMemoryBackend()
await backend.connect()
```

### SQLite (Production)
```python
from agentmem import SQLiteBackend

backend = SQLiteBackend(db_path="memory.db")
await backend.connect()
```

### Redis (Distributed)
```python
from agentmem import RedisBackend

backend = RedisBackend(
    host="localhost",
    port=6379,
    password="secret"  # optional
)
await backend.connect()
```

---

## Advanced Features

### Auto-Summarization

Automatically compress conversations when they exceed thresholds:

```python
session = await manager.create_session(
    user_id="user123",
    max_messages=100,
    auto_summarize=True,
    summary_threshold=50  # Summarize after 50 messages
)
```

### Token Management

Keep context within model limits:

```python
# Get recent messages that fit within token budget
context = await session.get_recent_context(max_tokens=2000)

# Convert to your LLM format
openai_messages = [msg.to_openai_format() for msg in context]
anthropic_messages = [msg.to_anthropic_format() for msg in context]
```

### Session Metadata

Track additional information:

```python
session = await manager.create_session(
    user_id="user123",
    agent_id="support_agent",
    workflow_id="customer_support",
    tags=["support", "billing"],
    properties={"priority": "high", "department": "sales"}
)
```

### Clean Up Expired Sessions

```python
# Cleanup sessions that have expired
deleted_count = await manager.cleanup_expired_sessions()
print(f"Cleaned up {deleted_count} expired sessions")
```

---

## Configuration Patterns

### Development
```python
# Fast, non-persistent
manager = create_memory_manager("memory")
```

### Testing
```python
# In-memory SQLite
manager = create_memory_manager("sqlite", db_path=":memory:")
```

### Production
```python
# Persistent SQLite with custom settings
manager = create_memory_manager("sqlite", 
    db_path="/var/app/conversations.db",
    pool_size=10,
    timeout=30
)
```

### Distributed
```python
# Redis for multi-instance deployments
manager = create_memory_manager("redis",
    host="redis.example.com",
    port=6379,
    db=0,
    password=os.getenv("REDIS_PASSWORD")
)
```

---

## API Reference

### Core Classes

- **Message**: Universal message format with role, content, and metadata
- **SessionMetadata**: Session configuration and state
- **ConversationSummary**: Automatically generated conversation summaries
- **MemoryUsage**: Memory usage statistics

### Interfaces

- **IMemorySession**: Session management interface
- **IMemoryBackend**: Backend storage interface  
- **IMemoryManager**: High-level memory management interface

### Factory Functions

- **create_memory_manager()**: Create a memory manager with specified backend
- **create_memory_backend()**: Create a backend instance directly

---

## Integration Examples

### LangChain

```python
from langchain.memory import ConversationBufferMemory
from agentmem import create_memory_manager

# Use agentmem as LangChain memory backend
manager = create_memory_manager("sqlite")
# ... integrate with LangChain chains
```

### LlamaIndex

```python
from llama_index import ChatMemoryBuffer
from agentmem import create_memory_manager

# Use agentmem with LlamaIndex
manager = create_memory_manager("sqlite")
# ... integrate with LlamaIndex agents
```

---

## Roadmap

### Phase 1 (Current) - Conversational Memory
- ✅ Session management
- ✅ Multiple backends (SQLite, Redis, In-Memory)
- ✅ Auto-summarization
- ✅ Token management
- ✅ LLM provider integration

### Phase 2 (Planned) - Agent Memory
- 🔜 6 memory types (Working, Episodic, Semantic, Procedural, Emotional, Preference)
- 🔜 Personalization engine
- 🔜 Context compression strategies
- 🔜 Memory analytics and optimization
- 🔜 Long-term semantic memory with vector search

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: [https://github.com/aekdahl/agentmem](https://github.com/aekdahl/agentmem)
- **Issues**: [https://github.com/aekdahl/agentmem/issues](https://github.com/aekdahl/agentmem/issues)
- **Discussions**: [https://github.com/aekdahl/agentmem/discussions](https://github.com/aekdahl/agentmem/discussions)

---

## Acknowledgments

AgentMem is extracted from [LangSwarm](https://github.com/aekdahl/langswarm), a multi-agent AI orchestration framework. It represents Phase 1 of the memory system, focusing on conversational memory management.

---

**Built with ❤️ for the AI agent community**



