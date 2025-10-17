#!/usr/bin/env python3
"""
Fixed test for MVP multi-agent orchestration example from MVP.md

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
        from langswarm.core.agents import AgentBuilder, register_agent
        from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
        
        print("✅ Imports successful")
        
        # Step 1: Create specialized agents using AgentBuilder directly
        print("\n📋 Step 1: Creating specialized agents...")
        
        # Use AgentBuilder with build_sync to avoid async issues
        researcher = (AgentBuilder("researcher")
                     .openai()
                     .model("gpt-3.5-turbo")
                     .system_prompt("You are a research specialist. Gather comprehensive information on the given topic.")
                     .build_sync())
        print("   ✅ Created researcher agent")
        
        summarizer = (AgentBuilder("summarizer")
                     .openai()
                     .model("gpt-3.5-turbo")
                     .system_prompt("You are a summary specialist. Create clear, concise summaries of the information provided.")
                     .build_sync())
        print("   ✅ Created summarizer agent")
        
        # Step 2: Register agents for orchestration
        print("\n📋 Step 2: Registering agents for orchestration...")
        
        register_agent(researcher)
        print("   ✅ Registered researcher agent")
        
        register_agent(summarizer)
        print("   ✅ Registered summarizer agent")
        
        # Step 3: Create workflow that orchestrates them
        print("\n📋 Step 3: Creating orchestration workflow...")
        
        # Try different parameter names
        try:
            # First try agent_chain
            workflow = create_simple_workflow(
                workflow_id="research_and_summarize",
                name="Research and Summarize Workflow",
                agent_chain=["researcher", "summarizer"]
            )
        except TypeError:
            # If that fails, try agents
            try:
                workflow = create_simple_workflow(
                    workflow_id="research_and_summarize",
                    name="Research and Summarize Workflow",
                    agents=["researcher", "summarizer"]
                )
            except TypeError:
                # If that fails too, try steps
                workflow = create_simple_workflow(
                    workflow_id="research_and_summarize",
                    name="Research and Summarize Workflow",
                    steps=["researcher", "summarizer"]
                )
        
        print("   ✅ Created workflow: researcher → summarizer")
        
        # Step 4: Execute the orchestrated workflow
        print("\n📋 Step 4: Executing orchestrated workflow...")
        print("   Topic: 'Benefits of AI in healthcare'")
        
        engine = get_workflow_engine()
        
        # Execute workflow
        result = await engine.execute_workflow(
            workflow=workflow,
            input_data={"input": "What are the benefits of AI in healthcare?"}
        )
        
        print("\n🎯 Orchestration Complete!")
        print("-" * 60)
        print(f"Status: {result.status}")
        if hasattr(result, 'execution_time') and result.execution_time:
            print(f"Execution Time: {result.execution_time:.2f}s")
        
        # Print the final result
        if result.result:
            print(f"\nFinal Result:\n{result.result}")
        elif result.step_results:
            print(f"\nStep Results:")
            for step, step_result in result.step_results.items():
                print(f"  {step}: {step_result}")
        else:
            print("\nNo result data available")
            
        print("-" * 60)
        
        if result.status.value == "completed":
            print("\n✅ MVP Test PASSED: Multi-agent orchestration works!")
            return True
        else:
            print(f"\n⚠️ Workflow completed with status: {result.status}")
            if result.error:
                print(f"   Error: {result.error}")
            return False
        
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
    print("🧪 LangSwarm MVP Test - Multi-Agent Orchestration (Fixed)\n")
    
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