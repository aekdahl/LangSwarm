#!/usr/bin/env python3
"""
Simple workflow: Question -> Research -> Answer
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
import os
from langswarm import create_workflow

async def main():
    # Define a simple workflow
    workflow = create_workflow("""
    researcher -> analyzer -> user
    """, agents=[
        {
            "id": "researcher", 
            "model": "gpt-3.5-turbo",
            "system_prompt": "Research the given topic thoroughly."
        },
        {
            "id": "analyzer",
            "model": "gpt-3.5-turbo", 
            "system_prompt": "Analyze research and provide clear conclusions."
        }
    ])
    
    # Run the workflow
    result = await workflow.run("What are the benefits of exercise?")
    print(f"Final result: {result}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        exit(1)
    asyncio.run(main())