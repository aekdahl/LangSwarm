"""
Simple Sequential Planning Example

Demonstrates basic hierarchical planning with brainstorm → verify → plan → execute.
"""

import asyncio
import os
from langswarm.core.planning import (
    Coordinator, TaskBrief, DEFAULT_POLICIES
)
from langswarm.core.agents import create_openai_agent


async def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        return
    
    # Create LLM for planning
    print("🤖 Creating planner agent...")
    planner_llm = create_openai_agent(
        name="planner",
        model="gpt-4",
        system_prompt="You are an intelligent planning assistant. Help break down tasks into concrete steps."
    )
    
    # Define task
    print("\n📋 Defining task...")
    brief = TaskBrief(
        objective="Research AI agents and write a summary article",
        inputs={
            "topic": "AI agents and multi-agent systems",
            "target_length": "500 words"
        },
        required_outputs={
            "article": "markdown document",
            "sources": "list of references"
        },
        acceptance_tests=[
            {
                "name": "has_content",
                "type": "assertion",
                "assertion": "len(output.article) > 100"
            },
            {
                "name": "has_sources",
                "type": "assertion",
                "assertion": "len(output.sources) > 0"
            }
        ],
        constraints={
            "cost_usd": 2.0,
            "latency_sec": 180  # 3 minutes
        },
        metadata={
            "owner": "user",
            "purpose": "demo"
        }
    )
    
    # Create coordinator
    print("🎯 Initializing coordinator...")
    coordinator = Coordinator(config={
        "llm": planner_llm,
        "policies": DEFAULT_POLICIES,
        "escalation": {
            "oncall_team": "demo-team"
        }
    })
    
    # Execute with adaptive planning
    print("\n🚀 Starting execution with adaptive planning...\n")
    print("=" * 60)
    
    result = await coordinator.execute_task(brief)
    
    # Display results
    print("\n" + "=" * 60)
    print("\n📊 Execution Results:")
    print(f"   Status: {result.status}")
    print(f"   Steps completed: {len(result.artifacts)}")
    print(f"   Plan version: v{result.plan.version}")
    print(f"   Cost: ${result.metrics.get('cost_usd', 0):.2f}")
    print(f"   Latency: {result.metrics.get('latency_ms', 0) / 1000:.1f}s")
    print(f"   Tokens: {result.metrics.get('tokens_in', 0) + result.metrics.get('tokens_out', 0)}")
    
    if result.status == "completed":
        print("\n✅ Task completed successfully!")
        
        # Show artifacts
        print("\n📦 Artifacts produced:")
        for step_id, artifact in result.artifacts.items():
            print(f"   {step_id}: {type(artifact).__name__}")
    
    elif result.status == "halted":
        print("\n⏸️ Execution halted - human intervention required")
    
    else:
        print(f"\n❌ Execution failed with status: {result.status}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Hierarchical Planning System - Simple Example")
    print("=" * 60)
    asyncio.run(main())




