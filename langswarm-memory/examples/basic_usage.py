"""
Basic Usage Example for AgentMem

Demonstrates creating a memory manager, managing sessions, and storing/retrieving messages.
"""

import asyncio
from agentmem import (
    create_memory_manager,
    Message,
    MessageRole,
)


async def main():
    print("=== AgentMem Basic Usage Example ===\n")
    
    # Create memory manager with in-memory backend (for demo)
    print("1. Creating memory manager...")
    manager = create_memory_manager("in_memory")  # In-memory backend
    await manager.backend.connect()
    print("✓ Connected to memory backend\n")
    
    # Create a session
    print("2. Creating session...")
    session = await manager.create_session(
        user_id="demo_user",
        agent_id="demo_agent"
    )
    print(f"✓ Created session: {session.session_id}\n")
    
    # Add messages
    print("3. Adding messages to conversation...")
    await session.add_message(Message(
        role=MessageRole.USER,
        content="Hello! Can you help me with Python?"
    ))
    print("✓ Added user message")
    
    await session.add_message(Message(
        role=MessageRole.ASSISTANT,
        content="Of course! I'd be happy to help you with Python. What would you like to know?"
    ))
    print("✓ Added assistant message")
    
    await session.add_message(Message(
        role=MessageRole.USER,
        content="How do I read a file in Python?"
    ))
    print("✓ Added user message")
    
    await session.add_message(Message(
        role=MessageRole.ASSISTANT,
        content="You can read a file using:\n```python\nwith open('file.txt', 'r') as f:\n    content = f.read()\n```"
    ))
    print("✓ Added assistant message\n")
    
    # Get all messages
    print("4. Retrieving conversation history...")
    messages = await session.get_messages()
    print(f"✓ Retrieved {len(messages)} messages\n")
    
    # Display conversation
    print("5. Conversation:")
    print("-" * 60)
    for msg in messages:
        role_display = msg.role.value.upper()
        content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"{role_display}: {content_preview}")
    print("-" * 60 + "\n")
    
    # Get session metadata
    print("6. Session metadata:")
    print(f"   Session ID: {session.metadata.session_id}")
    print(f"   User ID: {session.metadata.user_id}")
    print(f"   Agent ID: {session.metadata.agent_id}")
    print(f"   Status: {session.metadata.status.value}")
    print(f"   Created: {session.metadata.created_at}")
    print(f"   Messages: {len(messages)}")
    print()
    
    # Demonstrate token-limited context
    print("7. Getting recent context (token-limited)...")
    context = await session.get_recent_context(max_tokens=100)
    print(f"✓ Retrieved {len(context)} recent messages within token limit\n")
    
    # Clean up
    print("8. Cleaning up...")
    await session.close()
    await manager.backend.disconnect()
    print("✓ Session closed and disconnected\n")
    
    print("=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())

