#!/usr/bin/env python3
"""
Agent with file system tools
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create agent with file access
    agent = create_agent(
        model="gpt-3.5-turbo",
        tools=["filesystem"],
        system_prompt="You can read and write files to help users."
    )
    
    # Ask agent to create a file
    response = await agent.chat("Create a file called 'hello.txt' with the text 'Hello World!'")
    print(f"AI: {response}")
    
    # Ask agent to read the file back
    response = await agent.chat("Read the contents of hello.txt")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())