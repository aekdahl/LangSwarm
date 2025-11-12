"""
OpenAI Integration Example for AgentMem

Demonstrates using AgentMem with OpenAI's API for a conversational chatbot
with persistent memory.
"""

import asyncio
import os
from agentmem import (
    create_memory_manager,
    Message,
    MessageRole,
)


async def chat_with_memory(user_message: str, user_id: str = "default_user"):
    """
    Chat with OpenAI while maintaining conversation history in AgentMem.
    
    Args:
        user_message: The user's message
        user_id: Unique identifier for the user
        
    Returns:
        The assistant's response
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        print("ERROR: OpenAI package not installed")
        print("Install it with: pip install openai")
        return None
    
    # Initialize OpenAI client
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Initialize memory manager with SQLite backend
    manager = create_memory_manager("sqlite", db_path="chat_memory.db")
    await manager.backend.connect()
    
    try:
        # Get or create session for this user
        session_id = f"session_{user_id}"
        session = await manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id
        )
        
        # Add user message to memory
        await session.add_message(Message(
            role=MessageRole.USER,
            content=user_message
        ))
        
        # Get conversation history
        messages = await session.get_messages()
        
        # Convert to OpenAI format
        openai_messages = [msg.to_openai_format() for msg in messages]
        
        # Get AI response
        print("Thinking...")
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=500
        )
        
        assistant_message = response.choices[0].message.content
        
        # Save assistant response to memory
        await session.add_message(Message(
            role=MessageRole.ASSISTANT,
            content=assistant_message
        ))
        
        return assistant_message
        
    finally:
        await manager.backend.disconnect()


async def main():
    print("=== AgentMem + OpenAI Chat Example ===\n")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        return
    
    print("Chat with AI (type 'exit' to quit, 'history' to see conversation)\n")
    
    user_id = "demo_user"
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'history':
            # Show conversation history
            manager = create_memory_manager("sqlite", db_path="chat_memory.db")
            await manager.backend.connect()
            session = await manager.get_session(f"session_{user_id}")
            if session:
                messages = await session.get_messages()
                print("\n--- Conversation History ---")
                for msg in messages:
                    role = msg.role.value.upper()
                    print(f"{role}: {msg.content}")
                print("--- End History ---\n")
            await manager.backend.disconnect()
            continue
        
        # Get AI response
        response = await chat_with_memory(user_input, user_id)
        
        if response:
            print(f"AI: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())



