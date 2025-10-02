#!/usr/bin/env python3
"""
LangSwarm Orchestration MVP - The Real Minimum Viable Product
============================================================

This demonstrates LangSwarm's core value: ORCHESTRATING multiple agents
to work together on a task. This is what makes LangSwarm special.

The MVP: Two agents collaborate to solve a problem
- Agent 1: Researcher (gathers information)
- Agent 2: Summarizer (creates final answer)

Requirements:
- Python 3.8+
- pip install langswarm openai
- export OPENAI_API_KEY="your-key-here"

Usage:
    python orchestration_mvp.py
"""

import asyncio
from langswarm.core.agents import create_openai_agent, register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

async def main():
    print("🚀 LangSwarm Orchestration MVP")
    print("=" * 50)
    
    # Create two specialized agents
    print("🤖 Creating specialized agents...")
    researcher = create_openai_agent(
        name="researcher",
        model="gpt-3.5-turbo",
        system_prompt="You are a research specialist. Gather comprehensive information on topics."
    )
    
    summarizer = create_openai_agent(
        name="summarizer", 
        model="gpt-3.5-turbo",
        system_prompt="You are a summary specialist. Create clear, concise summaries from research."
    )
    
    print("✅ Agents created: researcher + summarizer")
    
    # Register agents so workflows can find them
    print("\n📝 Registering agents...")
    register_agent(researcher)
    register_agent(summarizer)
    print("✅ Agents registered in global registry")
    
    # Create workflow that orchestrates them
    print("\n🔄 Creating orchestration workflow...")
    workflow = create_simple_workflow(
        workflow_id="research_and_summarize",
        name="Research and Summarize Workflow",
        agent_chain=["researcher", "summarizer"]
    )
    
    print("✅ Workflow created: researcher → summarizer")
    
    # Execute the orchestrated workflow
    print("\n⚡ Executing orchestrated workflow...")
    engine = get_workflow_engine()
    
    # Run the workflow
    result = await engine.execute_workflow(
        workflow=workflow,
        input_data={"input": "What are the key benefits of AI in healthcare?"}
    )
    
    print(f"\n🎉 Orchestration Result:")
    print(f"Status: {result.status}")
    print(f"Final Output: {result.output}")
    
    print(f"\n📊 Workflow Steps Executed:")
    for step_id, step_result in result.step_results.items():
        print(f"  {step_id}: {step_result.status}")

if __name__ == "__main__":
    asyncio.run(main())
