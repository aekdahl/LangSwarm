#!/usr/bin/env python3
"""
Chatbot with memory - remembers conversation
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create agent with memory enabled
    agent = create_agent(
        model="gpt-3.5-turbo",
        memory=True  # Remembers conversation
    )
    
    # First message
    await agent.chat("My name is Alice and I love pizza.")
    
    # Test memory - agent should remember the name
    response = await agent.chat("What's my name and what do I love?")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable") 
        exit(1)
    asyncio.run(main())