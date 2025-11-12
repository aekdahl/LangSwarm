"""
Redis Backend Example for AgentMem

Demonstrates using AgentMem with Redis backend for distributed memory storage.
"""

import asyncio
import os
from agentmem import (
    RedisBackend,
    MemoryManager,
    Message,
    MessageRole,
    SessionMetadata,
)


async def main():
    print("=== AgentMem Redis Backend Example ===\n")
    
    # Configure Redis connection
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    
    print(f"Connecting to Redis at {redis_host}:{redis_port}...")
    
    # Create Redis backend
    backend = RedisBackend(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=0,
        key_prefix="agentmem:",
        ttl=3600  # Sessions expire after 1 hour
    )
    
    try:
        # Connect to Redis
        await backend.connect()
        print("✓ Connected to Redis\n")
        
        # Create memory manager
        manager = MemoryManager(backend)
        await manager.start()
        print("✓ Memory manager started\n")
        
        # Create a session
        print("Creating session...")
        session = await manager.create_session(
            user_id="redis_demo_user",
            agent_id="redis_demo_agent"
        )
        print(f"✓ Created session: {session.session_id}\n")
        
        # Add messages
        print("Adding messages...")
        messages_to_add = [
            ("USER", "Hello! Testing Redis backend."),
            ("ASSISTANT", "Hi! Redis backend is working perfectly."),
            ("USER", "Great! Can you tell me about Redis?"),
            ("ASSISTANT", "Redis is an in-memory data structure store used as a database, cache, and message broker."),
        ]
        
        for role_str, content in messages_to_add:
            role = MessageRole.USER if role_str == "USER" else MessageRole.ASSISTANT
            await session.add_message(Message(role=role, content=content))
            print(f"✓ Added {role_str} message")
        print()
        
        # Retrieve messages
        print("Retrieving messages...")
        messages = await session.get_messages()
        print(f"✓ Retrieved {len(messages)} messages\n")
        
        # Display conversation
        print("Conversation:")
        print("-" * 60)
        for msg in messages:
            role_display = msg.role.value.upper()
            print(f"{role_display}: {msg.content}")
        print("-" * 60 + "\n")
        
        # List all sessions
        print("Listing all sessions...")
        sessions = await backend.list_sessions()
        print(f"✓ Found {len(sessions)} sessions")
        for sess_meta in sessions:
            print(f"   - {sess_meta.session_id} (user: {sess_meta.user_id})")
        print()
        
        # Get usage statistics
        print("Getting usage statistics...")
        stats = await backend.get_usage_stats()
        print(f"✓ Session count: {stats.session_count}")
        print(f"✓ Message count: {stats.message_count}")
        print(f"✓ Active sessions: {stats.active_sessions}")
        print()
        
        # Health check
        print("Performing health check...")
        health = await backend.health_check()
        print(f"✓ Backend status: {health.get('status', 'unknown')}")
        print(f"✓ Connected: {health.get('connected', False)}")
        print()
        
        # Clean up
        print("Cleaning up...")
        await session.close()
        await manager.stop()
        await backend.disconnect()
        print("✓ Disconnected from Redis\n")
        
        print("=== Example Complete ===")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Redis server is running: redis-server")
        print("2. Check connection details (host, port, password)")
        print("3. Install Redis: pip install redis")
        
        if backend.is_connected:
            await backend.disconnect()


if __name__ == "__main__":
    asyncio.run(main())



