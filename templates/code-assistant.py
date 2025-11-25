#!/usr/bin/env python3
"""
AI Code Assistant Template
Expert programmer with file system access.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent

async def main():
    # Create coding assistant with file access
    agent = create_agent(
        name="coder",
        model="gpt-4",  # GPT-4 is better for code
        system_prompt="""You are an expert programmer and coding assistant.
        - Write clean, well-commented code
        - Follow best practices and design patterns
        - Explain your code when asked
        - Suggest improvements and optimizations""",
        tools=["filesystem"],  # Can read/write files
        memory=True
    )
    
    # Ask for code help
    response = await agent.chat(
        "Create a simple Python function to calculate Fibonacci numbers and save it to fib.py"
    )
    print(f"Assistant: {response}\n")
    
    # Review and improve
    response = await agent.chat("Can you add error handling and docstrings?")
    print(f"Assistant: {response}")

if __name__ == "__main__":
    asyncio.run(main())

