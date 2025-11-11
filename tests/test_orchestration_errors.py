#!/usr/bin/env python3
"""
Test the enhanced orchestration error handling.

This demonstrates how improved error messages help developers
quickly identify and fix orchestration issues.
"""
import asyncio
import sys
import os

# Add parent directory to path for imports  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langswarm.core.agents import AgentBuilder, register_agent, list_agents
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
from langswarm.core.orchestration_errors import (
    AgentNotFoundError, WorkflowExecutionError, AgentExecutionError
)


async def test_agent_not_found_error():
    """Test error when workflow references unregistered agent."""
    print("\n🧪 Test 1: Agent Not Found Error")
    print("=" * 50)
    
    try:
        # Create workflow that references non-existent agents
        workflow = create_simple_workflow(
            workflow_id="test_missing_agents",
            name="Test Missing Agents",
            agent_chain=["researcher", "summarizer"]  # These aren't registered!
        )
        
        engine = get_workflow_engine()
        result = await engine.execute_workflow(
            workflow=workflow,
            input_data={"input": "Test input"}
        )
        
    except Exception as e:
        print(f"\n❌ Error Type: {type(e).__name__}")
        print(f"\nError Message:\n{e}")
        
        if hasattr(e, 'suggestion'):
            print(f"\n💡 Suggestion:\n{e.suggestion}")


async def test_workflow_validation_error():
    """Test error with invalid workflow configuration."""
    print("\n\n🧪 Test 2: Workflow Validation Error")
    print("=" * 50)
    
    try:
        # Try to create invalid workflow
        workflow = create_simple_workflow(
            workflow_id="empty_workflow",
            name="Empty Workflow", 
            agent_chain=[]  # Empty chain!
        )
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 This shows input validation working correctly")


async def test_agent_execution_error():
    """Test error when agent fails during execution."""
    print("\n\n🧪 Test 3: Agent Execution Error") 
    print("=" * 50)
    
    try:
        # Create a mock agent that will fail
        mock_agent = AgentBuilder("failing_agent").openai().model("gpt-3.5-turbo").build_sync()
        register_agent(mock_agent)
        
        workflow = create_simple_workflow(
            workflow_id="test_failing_agent",
            name="Test Failing Agent",
            agent_chain=["failing_agent"]
        )
        
        # This will fail because we're using a test API key
        engine = get_workflow_engine()
        result = await engine.execute_workflow(
            workflow=workflow,
            input_data={"input": "Test input"}
        )
        
    except Exception as e:
        print(f"\n❌ Error Type: {type(e).__name__}")
        print(f"\nError Chain:")
        
        # Show error chain
        current = e
        depth = 0
        while current and depth < 5:
            print(f"  {'  ' * depth}→ {type(current).__name__}: {str(current)[:100]}...")
            if hasattr(current, '__cause__'):
                current = current.__cause__
            elif hasattr(current, 'original_error'):
                current = current.original_error
            else:
                break
            depth += 1


async def test_with_registered_agents():
    """Test with properly registered agents (but no API key)."""
    print("\n\n🧪 Test 4: With Registered Agents")
    print("=" * 50)
    
    # Create and register agents
    researcher = AgentBuilder("researcher").openai().model("gpt-3.5-turbo").build_sync()
    summarizer = AgentBuilder("summarizer").openai().model("gpt-3.5-turbo").build_sync()
    
    register_agent(researcher)
    register_agent(summarizer)
    
    print(f"✅ Registered agents: {list_agents()}")
    
    # Create workflow
    workflow = create_simple_workflow(
        workflow_id="research_workflow",
        name="Research Workflow",
        agent_chain=["researcher", "summarizer"]
    )
    
    print("✅ Created workflow with registered agents")
    
    try:
        engine = get_workflow_engine()
        result = await engine.execute_workflow(
            workflow=workflow,
            input_data={"input": "Test orchestration"}
        )
    except Exception as e:
        print(f"\n❌ Execution failed (expected without API key)")
        print(f"   Error: {type(e).__name__}")


async def demonstrate_error_improvements():
    """Show the improvements in error messages."""
    print("\n\n📊 Error Message Improvements")
    print("=" * 50)
    
    print("\n❌ Old Error Style:")
    print("   KeyError: 'researcher'")
    print("   TypeError: 'NoneType' object has no attribute 'execute'")
    
    print("\n✅ New Error Style:")
    print("   AgentNotFoundError: Agent 'researcher' not found in registry")
    print("   ")
    print("   Make sure to register agent 'researcher' before using it in workflows:")
    print("   ")
    print("     from langswarm import create_openai_agent, register_agent")
    print("     ")
    print("     # Create the agent")
    print("     researcher = await create_openai_agent(...)")
    print("     ")  
    print("     # Register it for orchestration")
    print("     register_agent(researcher)")
    print("   ")
    print("   Currently registered agents:")
    print("     • summarizer")
    print("     • analyzer")


async def main():
    """Run all error handling tests."""
    print("🔍 Testing Orchestration Error Handling")
    
    # Run tests
    await test_agent_not_found_error()
    await test_workflow_validation_error()
    await test_agent_execution_error()
    await test_with_registered_agents()
    await demonstrate_error_improvements()
    
    print("\n\n✅ Error handling tests complete!")
    print("\n💡 Key Benefits:")
    print("  • Clear identification of what went wrong")
    print("  • Actionable suggestions for fixing issues")
    print("  • Context about available alternatives")
    print("  • Example code showing correct usage")
    print("  • Reduced debugging time")


if __name__ == "__main__":
    # Set a test API key to avoid that specific error
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    asyncio.run(main())