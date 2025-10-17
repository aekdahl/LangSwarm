#!/usr/bin/env python3
"""
Test the MVP multi-agent orchestration example from MVP.md

This demonstrates LangSwarm's core value proposition:
orchestrating multiple AI agents to collaborate on tasks.
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_mvp_orchestration():
    """Test the multi-agent orchestration MVP example"""
    
    print("🚀 Testing LangSwarm MVP: Multi-Agent Orchestration")
    print("=" * 60)
    
    # Ensure we have an API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Import required components
        from langswarm.core.agents import create_openai_agent, register_agent
        from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
        
        print("✅ Imports successful")
        
        # Step 1: Create specialized agents
        print("\n📋 Step 1: Creating specialized agents...")
        
        # Check if create_openai_agent returns a coroutine
        researcher_result = create_openai_agent(
            name="researcher",
            system_prompt="You are a research specialist. Gather comprehensive information on the given topic."
        )
        
        # If it's a coroutine, await it
        if asyncio.iscoroutine(researcher_result):
            researcher = await researcher_result
        else:
            researcher = researcher_result
            
        print("   ✅ Created researcher agent")
        
        summarizer_result = create_openai_agent(
            name="summarizer", 
            system_prompt="You are a summary specialist. Create clear, concise summaries of the information provided."
        )
        
        # If it's a coroutine, await it
        if asyncio.iscoroutine(summarizer_result):
            summarizer = await summarizer_result
        else:
            summarizer = summarizer_result
            
        print("   ✅ Created summarizer agent")
        
        # Step 2: Register agents for orchestration
        print("\n📋 Step 2: Registering agents for orchestration...")
        
        register_agent(researcher)
        print("   ✅ Registered researcher agent")
        
        register_agent(summarizer)
        print("   ✅ Registered summarizer agent")
        
        # Step 3: Create workflow that orchestrates them
        print("\n📋 Step 3: Creating orchestration workflow...")
        
        workflow = create_simple_workflow(
            workflow_id="research_and_summarize",
            name="Research and Summarize Workflow",
            agent_chain=["researcher", "summarizer"]  # researcher → summarizer
        )
        print("   ✅ Created workflow: researcher → summarizer")
        
        # Step 4: Execute the orchestrated workflow
        print("\n📋 Step 4: Executing orchestrated workflow...")
        print("   Topic: 'Benefits of AI in healthcare'")
        
        engine = get_workflow_engine()
        result = await engine.execute_workflow(
            workflow=workflow,
            input_data={"input": "What are the benefits of AI in healthcare?"}
        )
        
        print("\n🎯 Orchestration Complete!")
        print("-" * 60)
        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"\nFinal Result:\n{result.result}")
        print("-" * 60)
        
        print("\n✅ MVP Test PASSED: Multi-agent orchestration works!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Make sure LangSwarm is properly installed")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during orchestration: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the MVP test"""
    print("🧪 LangSwarm MVP Test - Multi-Agent Orchestration\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Run the async test
    try:
        success = asyncio.run(test_mvp_orchestration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()