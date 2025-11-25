#!/usr/bin/env python3
"""
Code-first configuration using standard templates.
This demonstrates the recommended way to configure agents without YAML.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm.core.agents import AgentBuilder
from langswarm.core.config.templates import (
    basic_agent_config, 
    memory_enabled_agent_config,
    tool_enabled_agent_config,
    bigquery_config
)

async def main():
    print("🚀 Starting Code-First Configuration Demo")

    # 1. Basic Agent using Template
    print("\n1️⃣  Creating Basic Agent...")
    basic_config = basic_agent_config(
        model="gpt-3.5-turbo",
        system_prompt="You are a concise assistant."
    )
    
    # Create agent from config dictionary
    agent_basic = await AgentBuilder.from_config(basic_config).build()
    response = await agent_basic.chat("Hello!")
    print(f"Basic Agent: {response}")

    # 2. Memory Agent using Template
    print("\n2️⃣  Creating Memory-Enabled Agent...")
    memory_config = memory_enabled_agent_config(model="gpt-4")
    
    # You can merge or override configs easily in Python
    memory_config["system_prompt"] = "You are a forgetful professor."
    
    agent_memory = await AgentBuilder.from_config(memory_config).build()
    await agent_memory.chat("My name is Alex.")
    response = await agent_memory.chat("What is my name?")
    print(f"Memory Agent: {response}")

    # 3. Tool Agent with Explicit Configuration
    print("\n3️⃣  Creating Tool-Enabled Agent (Configuration Only)...")
    
    # Define tool configurations
    bq_conf = bigquery_config(
        project_id="my-project",
        dataset_id="my_dataset"
    )
    
    tool_config = tool_enabled_agent_config(
        tools=["bigquery_vector_search"],
        tool_configs={"bigquery_vector_search": bq_conf}
    )
    
    print(f"Generated Tool Config: {tool_config}")
    # Note: We don't build this agent as we don't have actual BQ credentials set up
    # but this demonstrates how to structure the configuration.

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())