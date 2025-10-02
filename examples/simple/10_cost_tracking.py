#!/usr/bin/env python3
"""
Track costs and token usage
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create agent with cost tracking
    agent = create_agent(
        model="gpt-3.5-turbo",
        track_costs=True
    )
    
    # Have some conversations
    await agent.chat("Hello, how are you?")
    await agent.chat("Tell me about machine learning.")
    await agent.chat("What's the weather like?")
    
    # Check costs
    stats = agent.get_usage_stats()
    print(f"Total tokens used: {stats['total_tokens']}")
    print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
    print(f"Number of requests: {stats['request_count']}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())