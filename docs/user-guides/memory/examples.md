# Examples

This guide provides practical examples of using LangSwarm Memory in different scenarios, from basic in-memory usage to integration with LLMs and production-grade backends.

## Basic Usage

The simplest way to get started is using the `in_memory` backend. This is useful for testing or short-lived scripts where persistence isn't required.

```python
import asyncio
from langswarm_memory import create_memory_manager, Message, MessageRole

async def main():
    # 1. Create memory manager
    manager = create_memory_manager("in_memory")
    await manager.backend.connect()
    
    # 2. Create a session for a specific user and agent
    session = await manager.create_session(
        user_id="demo_user",
        agent_id="demo_agent"
    )
    
    # 3. Add messages to the history
    await session.add_message(Message(
        role=MessageRole.USER,
        content="Hello! Can you help me with Python?"
    ))
    
    await session.add_message(Message(
        role=MessageRole.ASSISTANT,
        content="Of course! What would you like to know?"
    ))
    
    # 4. Retrieve conversation history
    messages = await session.get_messages()
    for msg in messages:
        print(f"{msg.role.value}: {msg.content}")

    # 5. Get recent context (token-limited)
    # Useful for fitting history into LLM context windows
    context = await session.get_recent_context(max_tokens=100)
    
    # Clean up
    await session.close()
    await manager.backend.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Integrating with OpenAI

This example demonstrates how to use LangSwarm Memory as the persistent storage for a chat application using OpenAI's API.

```python
import os
import asyncio
from openai import AsyncOpenAI
from langswarm_memory import create_memory_manager, Message, MessageRole

async def chat_loop():
    # Setup
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    manager = create_memory_manager("sqlite", db_path="chat.db")
    await manager.backend.connect()
    
    user_id = "user_123"
    session = await manager.get_or_create_session(
        session_id=f"session_{user_id}", 
        user_id=user_id
    )

    print("Chat started (type 'quit' to exit)")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break

        # 1. Store User Message
        await session.add_message(Message(
            role=MessageRole.USER, 
            content=user_input
        ))

        # 2. Get History & Call LLM
        history = await session.get_messages()
        openai_msgs = [msg.to_openai_format() for msg in history]
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_msgs
        )
        answer = response.choices[0].message.content
        print(f"AI: {answer}")

        # 3. Store Assistant Response
        await session.add_message(Message(
            role=MessageRole.ASSISTANT, 
            content=answer
        ))

    await manager.backend.disconnect()
```

## Production with Redis

For distributed applications or when sharing memory across multiple agent instances, use the Redis backend.

```python
import os
import asyncio
from langswarm_memory import RedisBackend, MemoryManager, Message, MessageRole

async def main():
    # 1. Configure Redis Backend
    backend = RedisBackend(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        key_prefix="langswarm:",
        ttl=3600  # Auto-expire sessions after 1 hour
    )
    
    await backend.connect()
    
    # 2. Initialize Manager
    manager = MemoryManager(backend)
    await manager.start()

    # 3. Use session as normal
    session = await manager.create_session(user_id="prod_user", agent_id="agent_v1")
    
    await session.add_message(Message(
        role=MessageRole.USER,
        content="This message is stored in Redis!"
    ))
    
    # Check health and stats
    health = await backend.health_check()
    print(f"Redis Connected: {health['connected']}")
    
    stats = await backend.get_usage_stats()
    print(f"Active Sessions: {stats.active_sessions}")

    await manager.stop()
    await backend.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```
