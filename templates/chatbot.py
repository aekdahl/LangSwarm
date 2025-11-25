#!/usr/bin/env python3
"""
Simple Chatbot Template
Conversational chatbot with personality and memory.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent

async def main():
    # Create a friendly chatbot with memory
    agent = create_agent(
        name="chatbot",
        model="gpt-3.5-turbo",
        system_prompt="""You are a friendly and helpful chatbot.
        Be conversational, engaging, and supportive.""",
        memory=True  # Remember conversation history
    )
    
    # Have a conversation
    response = await agent.chat("Hi! I'm working on a Python project.")
    print(f"Bot: {response}\n")
    
    response = await agent.chat("What should I know about async programming?")
    print(f"Bot: {response}\n")
    
    # Memory allows follow-up questions
    response = await agent.chat("Can you explain that in simpler terms?")
    print(f"Bot: {response}")

if __name__ == "__main__":
    asyncio.run(main())

