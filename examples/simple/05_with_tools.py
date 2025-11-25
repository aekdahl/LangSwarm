#!/usr/bin/env python3
"""
Agent with file system tools using code-first configuration.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm.core.agents import AgentBuilder

async def main():
    print("📂 File System Agent Demo")
    
    # Create agent with file access and explicit configuration
    # Note: 'filesystem' tool usually doesn't need config, but we show how to pass it
    agent = await (
        AgentBuilder()
        .name("file-agent")
        .openai()
        .model("gpt-3.5-turbo")
        .system_prompt("You can read and write files to help users.")
        .tools(["filesystem"])
        .tool_configs({
            "filesystem": {
                "base_path": "./workspace",  # Example config: restrict to workspace
                "allowed_extensions": [".txt", ".md"]
            }
        })
        .build()
    )
    
    # Ask agent to create a file
    print("\n1️⃣  Creating a file...")
    response = await agent.chat("Create a file called 'hello.txt' with the text 'Hello World!'")
    print(f"AI: {response}")
    
    # Ask agent to read the file back
    print("\n2️⃣  Reading the file...")
    response = await agent.chat("Read the contents of hello.txt")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())