#!/usr/bin/env python3
"""
Minimal LangSwarm Configuration
The absolute minimum to get started with LangSwarm.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent

async def main():
    # Minimal configuration - just specify the model
    agent = create_agent(model="gpt-3.5-turbo")
    
    # Start chatting
    response = await agent.chat("Hello! What can you help me with?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())

