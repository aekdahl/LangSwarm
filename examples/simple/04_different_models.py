#!/usr/bin/env python3
"""
Using different AI models for different tasks
Setup: pip install langswarm openai anthropic && export API keys
"""
import asyncio
import os
from langswarm import create_agent

async def main():
    # Fast model for simple tasks
    quick_assistant = create_agent(model="gpt-3.5-turbo")
    
    # Powerful model for complex tasks  
    smart_assistant = create_agent(model="gpt-4")
    
    # Simple task - use fast model
    summary = await quick_assistant.chat("Summarize: Python is a programming language.")
    print(f"Quick summary: {summary}")
    
    # Complex task - use powerful model
    analysis = await smart_assistant.chat("Analyze the pros and cons of Python vs JavaScript")
    print(f"Detailed analysis: {analysis}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())