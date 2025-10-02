#!/usr/bin/env python3
"""
Stream AI responses as they're generated
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create agent with streaming enabled
    agent = create_agent(
        model="gpt-3.5-turbo",
        stream=True
    )
    
    print("AI is thinking...")
    
    # Stream the response
    async for chunk in agent.chat_stream("Write a short story about a robot learning to cook."):
        print(chunk, end="", flush=True)
    
    print("\n\nDone!")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())