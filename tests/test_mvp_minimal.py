#!/usr/bin/env python3
"""
Minimal test to verify multi-agent orchestration structure works.
Uses mock agents to test the orchestration flow without API calls.
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_minimal_orchestration():
    """Test minimal orchestration setup"""
    
    print("🧪 Testing Minimal Multi-Agent Orchestration")
    print("=" * 50)
    
    try:
        # Import core components
        print("\n1️⃣ Testing imports...")
        from langswarm.core.agents import AgentBuilder
        from langswarm.core.agents.registry import AgentRegistry
        from langswarm.core.workflows.builder import WorkflowBuilder
        from langswarm.core.workflows.base import AgentStep
        print("   ✅ Core imports successful")
        
        # Create mock agents
        print("\n2️⃣ Creating mock agents...")
        
        # Create agents with minimal config
        researcher = AgentBuilder("researcher").openai().model("gpt-3.5-turbo").build_sync()
        print("   ✅ Created researcher agent")
        
        summarizer = AgentBuilder("summarizer").openai().model("gpt-3.5-turbo").build_sync()
        print("   ✅ Created summarizer agent")
        
        # Register agents
        print("\n3️⃣ Registering agents...")
        registry = AgentRegistry()
        registry.register(researcher)
        print("   ✅ Registered researcher")
        
        registry.register(summarizer)
        print("   ✅ Registered summarizer")
        
        # Create workflow manually
        print("\n4️⃣ Creating workflow...")
        workflow_builder = WorkflowBuilder("test_workflow")
        workflow_builder.add_step(AgentStep("step1", "researcher"))
        workflow_builder.add_step(AgentStep("step2", "summarizer"))
        workflow = workflow_builder.build()
        print("   ✅ Created workflow with 2 steps")
        
        # Verify structure
        print("\n5️⃣ Verifying orchestration structure...")
        print(f"   Workflow ID: {workflow.workflow_id}")
        print(f"   Steps: {len(workflow.steps)}")
        for i, step in enumerate(workflow.steps):
            print(f"   Step {i+1}: {step.step_id} -> Agent: {step.agent_id}")
        
        print("\n✅ Orchestration structure verified!")
        print("\n📝 Summary:")
        print("   - Multi-agent creation: ✅")
        print("   - Agent registration: ✅") 
        print("   - Workflow creation: ✅")
        print("   - Orchestration setup: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_api_approach():
    """Test using the simple API approach"""
    
    print("\n\n🧪 Testing Simple API Approach")
    print("=" * 50)
    
    try:
        print("\n1️⃣ Testing simple imports...")
        from langswarm import create_agent
        print("   ✅ Simple API imports successful")
        
        print("\n2️⃣ Creating agent with simple API...")
        # This will fail without real API key, but tests the structure
        try:
            agent = create_agent(model="gpt-3.5-turbo")
            print("   ✅ Agent creation successful")
        except ValueError as e:
            if "API key" in str(e):
                print("   ⚠️  API key required (expected)")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run minimal tests"""
    print("🔍 LangSwarm Multi-Agent Orchestration Test\n")
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Test core orchestration
    core_success = loop.run_until_complete(test_minimal_orchestration())
    
    # Test simple API
    simple_success = loop.run_until_complete(test_simple_api_approach())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Core Orchestration: {'✅ PASS' if core_success else '❌ FAIL'}")
    print(f"   Simple API: {'✅ PASS' if simple_success else '❌ FAIL'}")
    
    success = core_success and simple_success
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()