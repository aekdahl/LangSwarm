#!/usr/bin/env python3
"""
LangSwarm - Absolute Minimal Example
===================================

This is the simplest possible working example of LangSwarm.
Just 3 lines of code to create and use an AI agent.

Requirements:
- Python 3.8+
- pip install langswarm openai
- export OPENAI_API_KEY="your-key-here"

Usage:
    python minimal_example.py
"""

import asyncio
from langswarm.core.agents import create_openai_agent

async def main():
    # Create agent (1 line)
    agent = create_openai_agent(model="gpt-3.5-turbo")
    
    # Chat with agent (1 line)
    response = await agent.chat("Hello! Say 'Hi' back.")
    
    # Print response (1 line)
    print(f"Agent: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
