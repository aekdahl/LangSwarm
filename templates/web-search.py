#!/usr/bin/env python3
"""
Web Search Research Assistant Template
AI assistant with real-time web search capabilities.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent

async def main():
    # Create research assistant with web search
    agent = create_agent(
        name="researcher",
        model="gpt-4",
        system_prompt="""You are a research assistant with web search capabilities.
        - Search for current, accurate information
        - Always cite your sources
        - Verify information from multiple sources when possible
        - Distinguish between facts and opinions""",
        tools=["web_search"],
        memory=True
    )
    
    # Research current topics
    response = await agent.chat("What are the latest developments in AI safety research?")
    print(f"Researcher: {response}\n")
    
    # Follow-up with more specific questions
    response = await agent.chat("What did you find about alignment techniques?")
    print(f"Researcher: {response}")

if __name__ == "__main__":
    asyncio.run(main())

