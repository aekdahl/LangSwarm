#!/usr/bin/env python3
"""
Two agents working together
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Create two specialized agents
    researcher = create_agent(
        model="gpt-3.5-turbo",
        system_prompt="You research topics and gather facts."
    )
    
    writer = create_agent(
        model="gpt-3.5-turbo", 
        system_prompt="You write engaging articles from research."
    )
    
    # First agent researches
    topic = "artificial intelligence"
    research = await researcher.chat(f"Research key facts about {topic}")
    
    # Second agent writes based on research
    article = await writer.chat(f"Write a short article based on: {research}")
    print(f"Article:\n{article}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())