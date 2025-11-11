"""
Example 02: Simple Retrospective Validation

Demonstrates:
- Fast inline validation (immediate)
- Heavy async retrospects (background)
- Speculative continuation (downstream proceeds while retrospects run)
- Auto-rollback on retrospect failure

This shows the power of "low latency now, correctness later" - execution
continues quickly with basic checks, while heavy validation runs async.
"""

import asyncio
import os
from langswarm.core.planning import (
    Coordinator, TaskBrief, ActionContract, DEFAULT_POLICIES
)
from langswarm.core.agents import create_openai_agent


async def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY environment variable")
        return
    
    print("=" * 70)
    print("  Retrospective Validation Demo")
    print("  Fast path: immediate, Slow path: async background validation")
    print("=" * 70)
    
    # Create LLM for planning
    print("\n🤖 Creating planner agent...")
    planner_llm = create_openai_agent(
        name="planner",
        model="gpt-4",
        system_prompt="You are an intelligent planning assistant."
    )
    
    # Define task with retrospective validation
    print("\n📋 Defining task with retrospective validation...")
    brief = TaskBrief(
        objective="Process and validate expense data",
        inputs={
            "data_source": "sample_expenses.csv",
            "schema_version": "v3.2"
        },
        required_outputs={
            "validated_records": "json",
            "error_report": "json"
        },
        acceptance_tests=[
            {
                "name": "has_records",
                "type": "assertion",
                "assertion": "len(output.validated_records) > 0"
            }
        ],
        constraints={
            "cost_usd": 2.0,
            "latency_sec": 180
        },
        metadata={
            "owner": "demo-user",
            "purpose": "retrospect-demo"
        }
    )
    
    # Create coordinator with retrospects enabled
    print("🎯 Initializing coordinator with retrospective validation...")
    coordinator = Coordinator(config={
        "llm": planner_llm,
        "policies": DEFAULT_POLICIES,
        "enable_retrospects": True,  # Enable retrospective validation
        "escalation": {
            "oncall_team": "demo-team"
        }
    })
    
    # Execute with retrospective validation
    print("\n🚀 Starting execution...")
    print("   → Fast inline checks run immediately")
    print("   → Heavy retrospects run async in background")
    print("   → Execution continues speculatively\n")
    print("=" * 70)
    
    result = await coordinator.execute_task(brief)
    
    # Display results
    print("\n" + "=" * 70)
    print("\n📊 Execution Results:")
    print(f"   Status: {result.status}")
    print(f"   Steps completed: {len(result.artifacts)}")
    print(f"   Plan version: v{result.plan.version}")
    print(f"   Cost: ${result.metrics.get('cost_usd', 0):.2f}")
    print(f"   Latency: {result.metrics.get('latency_ms', 0) / 1000:.1f}s")
    
    # Show lineage info
    lineage_stats = coordinator.lineage.get_stats()
    print(f"\n📈 Lineage Tracking:")
    print(f"   Artifacts tracked: {lineage_stats['nodes']}")
    print(f"   Checkpoints: {lineage_stats['checkpoints']}")
    print(f"   Dependencies: {lineage_stats['edges']}")
    
    # Show retrospect status
    retro_stats = coordinator.retrospect_runner.get_stats()
    print(f"\n🔍 Retrospective Validation:")
    print(f"   Total retrospects: {retro_stats['total']}")
    print(f"   ✅ Passed: {retro_stats['ok']}")
    print(f"   ❌ Failed: {retro_stats['failed']}")
    print(f"   ⏳ Pending: {retro_stats['pending']}")
    print(f"   🔄 Running: {retro_stats['running']}")
    
    if retro_stats['failed'] > 0:
        print("\n⚠️  Failed Retrospects:")
        for retro_id in coordinator.retrospect_runner.get_all_failed():
            job = coordinator.retrospect_runner.jobs[retro_id]
            print(f"      • {retro_id}: {job.reason}")
        
        # Show replay info
        replay_stats = coordinator.replay_manager.get_stats()
        print(f"\n🔄 Replay Manager:")
        print(f"   Invalidation tickets: {replay_stats['tickets']}")
        print(f"   Replay actions: {replay_stats['replay_actions']}")
        print(f"   Cancel actions: {replay_stats['cancel_actions']}")
    
    if result.status == "completed":
        print("\n✅ Task completed successfully!")
        print("\n💡 Key Benefits of Retrospective Validation:")
        print("   1. Low latency - execution didn't wait for heavy checks")
        print("   2. High quality - thorough validation ran in background")
        print("   3. Auto-rollback - failed retrospects trigger replay")
        print("   4. Lineage tracking - full audit trail maintained")
    
    elif result.status == "halted":
        print("\n⏸️  Execution halted - human intervention required")
    
    else:
        print(f"\n❌ Execution ended with status: {result.status}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Hierarchical Planning + Retrospective Validation")
    print("  Example: Fast path + slow path validation")
    print("=" * 70)
    asyncio.run(main())



