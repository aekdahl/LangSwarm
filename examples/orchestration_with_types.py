#!/usr/bin/env python3
"""
Multi-Agent Orchestration Example with Full Type Hints

This example demonstrates LangSwarm's core value proposition:
orchestrating multiple AI agents to collaborate on tasks.

With the enhanced type hints, IDEs can provide better autocomplete
and catch type errors before runtime.
"""
import asyncio
import os
from typing import Dict, Any, Optional

# Import orchestration components with full type information
from langswarm.core.agents import (
    create_openai_agent_sync,  # Synchronous agent creation
    register_agent,            # Agent registration for orchestration
    BaseAgent,                 # Base agent type
    IAgent                     # Agent interface
)
from langswarm.core.workflows import (
    create_simple_workflow,    # Workflow creation
    get_workflow_engine,       # Workflow engine access
    IWorkflow,                 # Workflow interface
    WorkflowResult,           # Result type
    WorkflowStatus            # Status enum
)


async def demonstrate_typed_orchestration() -> None:
    """
    Demonstrate multi-agent orchestration with full type annotations.
    
    This example shows how type hints improve the development experience
    by providing clear interfaces and catching errors early.
    """
    
    print("🎯 Multi-Agent Orchestration with Type Hints")
    print("=" * 60)
    
    # Step 1: Create specialized agents with type annotations
    print("\n1️⃣ Creating typed agents...")
    
    # The return type BaseAgent is now clear
    researcher: BaseAgent = create_openai_agent_sync(
        name="researcher",
        model="gpt-3.5-turbo",
        system_prompt="You are a research specialist. Provide comprehensive information.",
        temperature=0.7
    )
    print(f"✅ Created {researcher.agent_id}: BaseAgent")
    
    summarizer: BaseAgent = create_openai_agent_sync(
        name="summarizer",
        model="gpt-3.5-turbo", 
        system_prompt="You are a summary specialist. Create concise summaries.",
        temperature=0.5
    )
    print(f"✅ Created {summarizer.agent_id}: BaseAgent")
    
    # Step 2: Register agents with type-checked function
    print("\n2️⃣ Registering agents for orchestration...")
    
    # register_agent returns bool indicating success
    success: bool = register_agent(researcher)
    print(f"✅ Registered researcher: {success}")
    
    success = register_agent(summarizer)
    print(f"✅ Registered summarizer: {success}")
    
    # Step 3: Create workflow with type annotations
    print("\n3️⃣ Creating typed workflow...")
    
    # create_simple_workflow returns IWorkflow
    workflow: IWorkflow = create_simple_workflow(
        workflow_id="research_and_summarize",
        name="Research and Summarize Workflow",
        agent_chain=["researcher", "summarizer"],
        input_data=None  # Optional[Dict[str, Any]]
    )
    print(f"✅ Created workflow: {workflow.workflow_id}")
    
    # Step 4: Execute with typed engine
    print("\n4️⃣ Executing orchestrated workflow...")
    
    # Get typed workflow engine
    engine = get_workflow_engine()
    
    # Input data with proper typing
    input_data: Dict[str, Any] = {
        "input": "What are the key benefits of type hints in Python?"
    }
    
    try:
        # Execute workflow - returns WorkflowResult
        result: WorkflowResult = await engine.execute_workflow(
            workflow=workflow,
            input_data=input_data,
            execution_mode=None,  # Uses default SYNC mode
            context_variables=None  # Optional context
        )
        
        # Access typed result properties
        print("\n✨ Orchestration Complete!")
        print(f"Status: {result.status}")  # WorkflowStatus enum
        print(f"Execution ID: {result.execution_id}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        # Check status with type-safe enum
        if result.status == WorkflowStatus.COMPLETED:
            print(f"\n📝 Final Result:\n{result.result}")
        elif result.status == WorkflowStatus.FAILED:
            print(f"\n❌ Error: {result.error}")
            
        # Access step results with proper typing
        if result.step_results:
            print("\n📊 Step Results:")
            for step_id, step_result in result.step_results.items():
                print(f"  {step_id}: {type(step_result)}")
                
    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")
        # With type hints, IDEs can suggest proper error handling
    
    # Demonstrate type benefits
    print("\n💡 Type Hint Benefits:")
    print("  • IDE autocomplete for all methods and properties")
    print("  • Early error detection before runtime")
    print("  • Clear documentation of expected types")
    print("  • Better refactoring support")
    print("  • Improved code readability")


async def demonstrate_async_creation() -> None:
    """Demonstrate async agent creation with full tool injection."""
    
    print("\n\n🔄 Async Agent Creation (with tool injection)")
    print("=" * 60)
    
    # Async version includes automatic tool injection
    from langswarm.core.agents import create_openai_agent  # async version
    
    # Create agent asynchronously
    agent: BaseAgent = await create_openai_agent(
        name="analyst",
        model="gpt-3.5-turbo",
        system_prompt="You are a data analyst.",
        temperature=0.3,
        # Additional typed parameters
        max_tokens=1000,
        tools=["calculator", "web_search"]  # Optional[List[str]]
    )
    
    print(f"✅ Created async agent with tools: {agent.agent_id}")


def main() -> None:
    """Run the typed orchestration demonstration."""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Note: OPENAI_API_KEY not set")
        print("   Set it to test with real API calls:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\n   Continuing with demonstration...\n")
    
    # Run async demonstrations
    asyncio.run(demonstrate_typed_orchestration())
    asyncio.run(demonstrate_async_creation())
    
    print("\n🎉 Type hints make orchestration development easier!")


if __name__ == "__main__":
    main()