#!/usr/bin/env python3
"""
Simple chatbot example - 10 lines of actual code
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create a simple agent
    agent = create_agent(model="gpt-3.5-turbo")
    
    # Have a conversation
    response = await agent.chat("Hello! Tell me a fun fact about Python programming.")
    print(f"AI: {response}")
    
    # Follow up question
    response = await agent.chat("Tell me another one!")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())