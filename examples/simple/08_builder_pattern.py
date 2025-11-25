#!/usr/bin/env python3
"""
Advanced agent configuration using builder pattern
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm.core.agents import AgentBuilder

async def main():
    # Advanced configuration using builder pattern
    agent = await (
        AgentBuilder()
        .name("advanced-assistant")
        .openai()
        .model("gpt-3.5-turbo")
        .system_prompt("You are a helpful coding assistant with expert knowledge.")
        .temperature(0.7)
        .max_tokens(1000)
        .memory_enabled(True)
        .streaming(False)
        .build()
    )
    
    # Use the agent
    response = await agent.chat("Explain what a Python list is in one sentence.")
    print(f"AI: {response}")
    
    # Test memory
    response = await agent.chat("Can you elaborate on that?")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())