#!/usr/bin/env python3
"""
Agent with web search capability
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create agent with web search
    agent = create_agent(
        model="gpt-4",
        tools=["web_search"],
        system_prompt="Search the web for current information and provide accurate answers."
    )
    
    # Ask for current information
    response = await agent.chat("What's the latest news about Python programming language?")
    print(f"AI: {response}")
    
    # Follow up with specific search
    response = await agent.chat("Search for Python 3.13 release notes")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())