#!/usr/bin/env python3
"""
Load configuration from YAML file
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import load_config

async def main():
    # Create minimal config file
    config_yaml = """
version: "2.0"
agents:
  - id: "helper"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a helpful coding assistant."
"""
    
    # Save config to file
    with open("simple_config.yaml", "w") as f:
        f.write(config_yaml)
    
    # Load and use the config
    config = load_config("simple_config.yaml")
    agent = config.get_agent("helper")
    
    # Use the agent
    response = await agent.chat("Explain what a Python list is in one sentence.")
    print(f"AI: {response}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())