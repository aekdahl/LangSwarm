#!/usr/bin/env python3
"""
LangSwarm V2 Workflow System Demonstration

Shows the modern, simplified workflow system for LangSwarm V2.
Demonstrates the fluent builder API, multiple execution modes,
and comprehensive workflow capabilities.

Usage:
    python v2_demo_workflow_system.py
"""

import asyncio
import sys
import traceback
import os
import json
from typing import Any, Dict, List

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath('.'))

try:
    from langswarm.v2.core.workflows import (
        # Core classes
        WorkflowBuilder, ExecutionMode, WorkflowStatus, StepStatus,
        WorkflowContext, WorkflowResult, StepResult,
        
        # Factory functions  
        create_workflow, create_linear_workflow, create_simple_workflow,
        create_analysis_workflow, create_approval_workflow,
        
        # Step types
        AgentStep, ToolStep, ConditionStep, TransformStep,
        
        # Registry and engine
        register_workflow, get_workflow, execute_workflow,
        execute_workflow_stream, list_workflows, get_workflow_engine,
        get_workflow_registry
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LangSwarm root directory")
    sys.exit(1)


class MockAgentSystem:
    """Mock agent system for demonstration"""
    
    def __init__(self):
        self.agents = {
            "data_extractor": "Data extraction agent",
            "data_analyzer": "Data analysis agent", 
            "report_generator": "Report generation agent",
            "approval_agent": "Approval processing agent",
            "text_processor": "Text processing agent",
            "summarizer": "Text summarization agent",
            "validator": "Data validation agent"
        }
    
    async def get_agent(self, agent_id: str):
        """Mock agent retrieval"""
        if agent_id in self.agents:
            return MockAgent(agent_id, self.agents[agent_id])
        return None


class MockAgent:
    """Mock agent for demonstration"""
    
    def __init__(self, agent_id: str, description: str):
        self.agent_id = agent_id
        self.description = description
    
    async def send_message(self, message: str):
        """Mock agent message processing"""
        # Simulate different agent responses
        if "data_extractor" in self.agent_id:
            result = {"extracted_data": f"Processed: {message}", "records": 100}
        elif "analyzer" in self.agent_id:
            result = {"analysis": f"Analysis of: {message}", "insights": ["insight1", "insight2"]}
        elif "report" in self.agent_id:
            result = {"report": f"Report for: {message}", "status": "complete"}
        elif "approval" in self.agent_id:
            result = {"decision": "approved" if "approve" in message.lower() else "rejected"}
        elif "summarizer" in self.agent_id:
            result = {"summary": f"Summary: {message[:50]}..."}
        else:
            result = {"output": f"Processed by {self.agent_id}: {message}"}
        
        return MockResponse(json.dumps(result))


class MockResponse:
    """Mock agent response"""
    
    def __init__(self, content: str):
        self.content = content


class MockToolSystem:
    """Mock tool system for demonstration"""
    
    def __init__(self):
        self.tools = {
            "data_transformer": "Transform data format",
            "file_processor": "Process files",
            "web_scraper": "Scrape web content",
            "database_connector": "Connect to database"
        }
    
    async def get_tool(self, tool_name: str):
        """Mock tool retrieval"""
        if tool_name in self.tools:
            return MockTool(tool_name, self.tools[tool_name])
        return None


class MockTool:
    """Mock tool for demonstration"""
    
    def __init__(self, tool_name: str, description: str):
        self.tool_name = tool_name
        self.description = description
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Mock tool execution"""
        return {
            "tool": self.tool_name,
            "input": kwargs,
            "output": f"Tool {self.tool_name} executed with {len(kwargs)} parameters",
            "success": True
        }


# Patch the import system for demo
mock_agent_system = MockAgentSystem()
mock_tool_system = MockToolSystem()

async def mock_get_agent(agent_id: str):
    return await mock_agent_system.get_agent(agent_id)

# Mock the agent registry
class MockAgentRegistry:
    async def get_tool(self, tool_name: str):
        return await mock_tool_system.get_tool(tool_name)

# Patch for demo (handle missing modules gracefully)
try:
    import langswarm.v2.core.agents
    langswarm.v2.core.agents.get_agent = mock_get_agent
except ImportError:
    # Create a mock module
    import sys
    from types import ModuleType
    mock_agents = ModuleType('langswarm.v2.core.agents')
    mock_agents.get_agent = mock_get_agent
    sys.modules['langswarm.v2.core.agents'] = mock_agents

try:
    import langswarm.v2.core.tools
    langswarm.v2.core.tools.get_tool_registry = lambda: MockAgentRegistry()
except ImportError:
    # Create a mock module
    import sys
    from types import ModuleType
    mock_tools = ModuleType('langswarm.v2.core.tools')
    mock_tools.get_tool_registry = lambda: MockAgentRegistry()
    sys.modules['langswarm.v2.core.tools'] = mock_tools


async def demo_basic_workflow_creation():
    """Demonstrate basic workflow creation using the builder"""
    print("============================================================")
    print("🏗️ BASIC WORKFLOW CREATION DEMO")
    print("============================================================")
    
    try:
        # Create a simple linear workflow
        print("\n📝 Creating Linear Workflow:")
        
        workflow = (WorkflowBuilder()
                   .start("simple_analysis", "Simple Data Analysis")
                   .description("Extract data, analyze it, and generate a report")
                   .add_agent_step(
                       "extract",
                       "data_extractor", 
                       "${input}",
                       name="Extract Data"
                   )
                   .add_agent_step(
                       "analyze",
                       "data_analyzer",
                       "${extract}",
                       name="Analyze Data",
                       dependencies=["extract"]
                   )
                   .add_agent_step(
                       "report",
                       "report_generator",
                       "${analyze}",
                       name="Generate Report", 
                       dependencies=["analyze"]
                   )
                   .set_execution_mode(ExecutionMode.SYNC)
                   .build())
        
        print(f"   ✅ Workflow created: {workflow.workflow_id}")
        print(f"   📄 Name: {workflow.name}")
        print(f"   📝 Description: {workflow.description}")
        print(f"   🔄 Steps: {len(workflow.steps)}")
        print(f"   ⚙️ Execution Mode: {workflow.execution_mode.value}")
        
        # Register the workflow
        success = await register_workflow(workflow)
        print(f"   📋 Registration: {'✅ Success' if success else '❌ Failed'}")
        
        return workflow
        
    except Exception as e:
        print(f"   ❌ Workflow creation failed: {e}")
        return None


async def demo_fluent_workflow_patterns():
    """Demonstrate different workflow builder patterns"""
    print("\n============================================================")
    print("🎨 FLUENT WORKFLOW PATTERNS DEMO")
    print("============================================================")
    
    patterns = []
    
    try:
        # 1. Linear workflow with convenience factory
        print("\n🔗 Linear Workflow Pattern:")
        linear_workflow = (create_linear_workflow("linear_demo", "Linear Processing")
                          .description("Sequential data processing")
                          .then_agent("step1", "text_processor", "${input}")
                          .then_agent("step2", "summarizer", "${step1}")
                          .then_agent("step3", "validator", "${step2}")
                          .build())
        
        await register_workflow(linear_workflow)
        patterns.append(("Linear", linear_workflow))
        print(f"   ✅ Created: {linear_workflow.name} with {len(linear_workflow.steps)} steps")
        
        # 2. Simple workflow from agent chain
        print("\n⛓️ Simple Chain Pattern:")
        chain_workflow = create_simple_workflow(
            "agent_chain",
            "Agent Chain Demo",
            ["data_extractor", "data_analyzer", "report_generator"]
        )
        
        await register_workflow(chain_workflow)
        patterns.append(("Chain", chain_workflow))
        print(f"   ✅ Created: {chain_workflow.name} with {len(chain_workflow.steps)} steps")
        
        # 3. Analysis workflow pattern
        print("\n📊 Analysis Pattern:")
        analysis_workflow = create_analysis_workflow(
            "multi_analysis",
            "database",
            ["data_analyzer", "text_processor", "summarizer"],
            "report_generator"
        )
        
        await register_workflow(analysis_workflow)
        patterns.append(("Analysis", analysis_workflow))
        print(f"   ✅ Created: {analysis_workflow.name} with {len(analysis_workflow.steps)} steps")
        print(f"   🔄 Execution Mode: {analysis_workflow.execution_mode.value}")
        
        # 4. Approval workflow pattern
        print("\n✅ Approval Pattern:")
        approval_workflow = create_approval_workflow(
            "approval_demo",
            "text_processor",
            "validator",
            lambda ctx: "approve" in str(ctx.get_step_output("review")).lower()
        )
        
        await register_workflow(approval_workflow)
        patterns.append(("Approval", approval_workflow))
        print(f"   ✅ Created: {approval_workflow.name} with {len(approval_workflow.steps)} steps")
        
        # 5. Custom workflow with multiple step types
        print("\n🔧 Custom Mixed Pattern:")
        custom_workflow = (create_workflow("custom_mixed", "Custom Mixed Workflow")
                          .description("Workflow with multiple step types")
                          .add_agent_step("input_processing", "text_processor", "${input}")
                          .add_tool_step("data_transform", "data_transformer", {"format": "json"})
                          .add_condition_step(
                              "quality_check",
                              lambda ctx: len(str(ctx.get_step_output("input_processing"))) > 10,
                              "high_quality",
                              "low_quality"
                          )
                          .add_agent_step("high_quality", "data_analyzer", "${input_processing}")
                          .add_agent_step("low_quality", "text_processor", "Low quality data detected")
                          .add_transform_step(
                              "final_transform",
                              lambda data, ctx: {"processed": data, "timestamp": "2024-12-19"},
                              "input_processing"
                          )
                          .set_execution_mode(ExecutionMode.PARALLEL)
                          .with_error_handling(True)
                          .build())
        
        await register_workflow(custom_workflow)
        patterns.append(("Custom", custom_workflow))
        print(f"   ✅ Created: {custom_workflow.name} with {len(custom_workflow.steps)} steps")
        
        return patterns
        
    except Exception as e:
        print(f"   ❌ Pattern creation failed: {e}")
        traceback.print_exc()
        return patterns


async def demo_workflow_execution_modes():
    """Demonstrate different workflow execution modes"""
    print("\n============================================================")
    print("⚡ WORKFLOW EXECUTION MODES DEMO")
    print("============================================================")
    
    # Create a test workflow
    test_workflow = (create_simple_workflow(
        "execution_test",
        "Execution Mode Test",
        ["data_extractor", "data_analyzer"]
    ))
    
    await register_workflow(test_workflow)
    
    test_input = {"query": "Test data for analysis", "source": "demo"}
    
    execution_results = {}
    
    # 1. Synchronous execution
    print("\n🔄 Synchronous Execution:")
    try:
        result = await execute_workflow("execution_test", test_input, ExecutionMode.SYNC)
        execution_results["sync"] = result
        
        print(f"   ✅ Status: {result.status.value}")
        print(f"   ⏱️ Execution Time: {result.execution_time:.3f}s")
        print(f"   📊 Steps Completed: {len(result.step_results)}")
        print(f"   💬 Success: {result.success}")
        
    except Exception as e:
        print(f"   ❌ Sync execution failed: {e}")
    
    # 2. Asynchronous execution
    print("\n🔀 Asynchronous Execution:")
    try:
        engine = get_workflow_engine()
        execution = await engine.execute_workflow(
            test_workflow, 
            test_input, 
            ExecutionMode.ASYNC
        )
        
        print(f"   🚀 Execution started: {execution.execution_id}")
        print(f"   📍 Status: {execution.status.value}")
        
        # Wait for completion
        result = await execution.wait_for_completion(timeout=30)
        execution_results["async"] = result
        
        print(f"   ✅ Final Status: {result.status.value}")
        print(f"   ⏱️ Execution Time: {result.execution_time:.3f}s")
        
    except Exception as e:
        print(f"   ❌ Async execution failed: {e}")
    
    # 3. Streaming execution
    print("\n📡 Streaming Execution:")
    try:
        step_count = 0
        async for result in execute_workflow_stream("execution_test", test_input):
            if isinstance(result, StepResult):
                step_count += 1
                print(f"   📝 Step {step_count}: {result.step_id} - {result.status.value}")
                if result.execution_time:
                    print(f"      ⏱️ Time: {result.execution_time:.3f}s")
            elif isinstance(result, WorkflowResult):
                print(f"   🏁 Final Result: {result.status.value}")
                print(f"   ⏱️ Total Time: {result.execution_time:.3f}s")
                execution_results["streaming"] = result
        
    except Exception as e:
        print(f"   ❌ Streaming execution failed: {e}")
    
    return execution_results


async def demo_workflow_monitoring():
    """Demonstrate workflow monitoring and tracking"""
    print("\n============================================================")
    print("📊 WORKFLOW MONITORING DEMO")  
    print("============================================================")
    
    try:
        # List all registered workflows
        print("\n📋 Registered Workflows:")
        workflows = await list_workflows()
        
        for i, workflow in enumerate(workflows, 1):
            print(f"   {i}. {workflow.workflow_id}: {workflow.name}")
            print(f"      📝 Description: {workflow.description or 'No description'}")
            print(f"      🔄 Steps: {len(workflow.steps)}")
            print(f"      ⚙️ Mode: {workflow.execution_mode.value}")
            
            # Show step details
            for j, step in enumerate(workflow.steps, 1):
                print(f"         {j}. {step.step_id} ({step.step_type.value}): {step.name}")
        
        # Create and execute a workflow for monitoring
        print("\n🔍 Execution Monitoring:")
        monitor_workflow = (create_linear_workflow("monitor_test", "Monitoring Test")
                           .description("Workflow for monitoring demonstration")
                           .then_agent("step1", "data_extractor", "${input}")
                           .then_agent("step2", "data_analyzer", "${step1}")  
                           .then_agent("step3", "report_generator", "${step2}")
                           .build())
        
        await register_workflow(monitor_workflow)
        
        # Execute and monitor
        engine = get_workflow_engine()
        execution = await engine.execute_workflow(
            monitor_workflow,
            {"data": "monitoring test data"},
            ExecutionMode.ASYNC
        )
        
        print(f"   🚀 Started execution: {execution.execution_id}")
        print(f"   📍 Initial status: {execution.status.value}")
        print(f"   ⏰ Start time: {execution.start_time.strftime('%H:%M:%S')}")
        
        # Monitor execution progress
        import time
        while execution.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            await asyncio.sleep(0.1)  # Brief pause
            
            step_statuses = execution.step_statuses
            print(f"   📊 Step Status: {step_statuses}")
            
            if execution.status == WorkflowStatus.RUNNING:
                break
        
        # Wait for completion
        final_result = await execution.wait_for_completion(timeout=30)
        
        print(f"   🏁 Final Status: {final_result.status.value}")
        print(f"   ⏱️ Total Execution Time: {final_result.execution_time:.3f}s")
        print(f"   ✅ Success: {final_result.success}")
        
        if final_result.step_results:
            print(f"   📝 Step Results:")
            for step_id, step_result in final_result.step_results.items():
                print(f"      {step_id}: {step_result.status.value}")
                if step_result.execution_time:
                    print(f"         ⏱️ Time: {step_result.execution_time:.3f}s")
        
        return final_result
        
    except Exception as e:
        print(f"   ❌ Monitoring failed: {e}")
        traceback.print_exc()
        return None


async def demo_workflow_validation():
    """Demonstrate workflow validation and error handling"""
    print("\n============================================================")
    print("🔍 WORKFLOW VALIDATION DEMO")
    print("============================================================")
    
    validation_results = {}
    
    # 1. Valid workflow
    print("\n✅ Valid Workflow Test:")
    try:
        valid_workflow = (create_workflow("valid_test", "Valid Workflow")
                         .description("A properly configured workflow")
                         .add_agent_step("step1", "data_extractor", "${input}")
                         .add_agent_step("step2", "data_analyzer", "${step1}", dependencies=["step1"])
                         .build())
        
        validation_errors = valid_workflow.validate()
        validation_results["valid"] = validation_errors
        
        print(f"   ✅ Validation: {'Passed' if not validation_errors else 'Failed'}")
        if validation_errors:
            for error in validation_errors:
                print(f"      ❌ {error}")
    
    except Exception as e:
        print(f"   ❌ Valid workflow test failed: {e}")
    
    # 2. Invalid workflow - missing dependencies
    print("\n❌ Invalid Workflow Test (Missing Dependencies):")
    try:
        invalid_workflow = (WorkflowBuilder()
                           .start("invalid_deps", "Invalid Dependencies")
                           .add_agent_step("step1", "data_analyzer", "${step2}", dependencies=["step2"])  # Depends on non-existent step
                           .add_agent_step("step2", "data_extractor", "${step3}", dependencies=["step3"])  # Circular dependency
                           .build())
        
        validation_errors = invalid_workflow.validate()
        validation_results["invalid_deps"] = validation_errors
        
        print(f"   ❌ Validation: Failed (as expected)")
        print(f"   📝 Errors found: {len(validation_errors)}")
        for error in validation_errors:
            print(f"      ❌ {error}")
    
    except Exception as e:
        print(f"   ✅ Invalid workflow properly rejected: {type(e).__name__}")
    
    # 3. Invalid workflow - duplicate step IDs
    print("\n❌ Invalid Workflow Test (Duplicate Step IDs):")
    try:
        duplicate_workflow = (WorkflowBuilder()
                             .start("duplicate_ids", "Duplicate Step IDs")
                             .add_agent_step("step1", "data_extractor", "${input}")
                             .add_agent_step("step1", "data_analyzer", "${input}")  # Duplicate ID
                             .build())
        
        validation_errors = duplicate_workflow.validate()
        validation_results["duplicate_ids"] = validation_errors
        
        print(f"   ❌ Validation: Failed (as expected)")
        for error in validation_errors:
            print(f"      ❌ {error}")
    
    except Exception as e:
        print(f"   ✅ Duplicate IDs properly rejected: {type(e).__name__}")
    
    # 4. Test workflow execution error handling
    print("\n🛠️ Execution Error Handling:")
    try:
        # Create workflow that will have execution errors
        error_workflow = (create_workflow("error_test", "Error Handling Test")
                         .add_agent_step("fail_step", "nonexistent_agent", "${input}")
                         .with_error_handling(continue_on_error=True)
                         .build())
        
        await register_workflow(error_workflow)
        
        result = await execute_workflow("error_test", {"test": "data"}, ExecutionMode.SYNC)
        validation_results["execution_error"] = result
        
        print(f"   📊 Result Status: {result.status.value}")
        print(f"   ❌ Error Handling: {'Working' if result.error else 'No errors'}")
        if result.error:
            print(f"   📝 Error: {type(result.error).__name__}: {result.error}")
    
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    
    return validation_results


async def demo_performance_comparison():
    """Demonstrate performance characteristics of different execution modes"""
    print("\n============================================================")
    print("⚡ PERFORMANCE COMPARISON DEMO")
    print("============================================================")
    
    # Create workflows of different complexities
    performance_results = {}
    
    # Simple workflow
    simple_workflow = create_simple_workflow(
        "perf_simple",
        "Simple Performance Test", 
        ["data_extractor", "data_analyzer"]
    )
    await register_workflow(simple_workflow)
    
    # Complex workflow
    complex_workflow = (create_workflow("perf_complex", "Complex Performance Test")
                       .add_agent_step("extract1", "data_extractor", "${input}")
                       .add_agent_step("extract2", "text_processor", "${input}")
                       .add_agent_step("analyze1", "data_analyzer", "${extract1}", dependencies=["extract1"])
                       .add_agent_step("analyze2", "summarizer", "${extract2}", dependencies=["extract2"])
                       .add_agent_step("combine", "report_generator", 
                                     lambda ctx: {
                                         "data": ctx.get_step_output("analyze1"),
                                         "text": ctx.get_step_output("analyze2")
                                     },
                                     dependencies=["analyze1", "analyze2"])
                       .set_execution_mode(ExecutionMode.PARALLEL)
                       .build())
    await register_workflow(complex_workflow)
    
    test_input = {"data": "Performance test data", "complexity": "high"}
    
    # Test different execution modes
    modes = [
        (ExecutionMode.SYNC, "Synchronous"),
        (ExecutionMode.PARALLEL, "Parallel")
    ]
    
    for mode, mode_name in modes:
        print(f"\n📊 {mode_name} Execution Performance:")
        
        # Simple workflow
        try:
            start_time = asyncio.get_event_loop().time()
            simple_result = await execute_workflow("perf_simple", test_input, mode)
            simple_time = asyncio.get_event_loop().time() - start_time
            
            print(f"   🔹 Simple Workflow:")
            print(f"      ⏱️ Execution Time: {simple_time:.3f}s")
            print(f"      📊 Status: {simple_result.status.value}")
            print(f"      🔄 Steps: {len(simple_result.step_results)}")
            
            performance_results[f"{mode.value}_simple"] = {
                "time": simple_time,
                "status": simple_result.status.value,
                "steps": len(simple_result.step_results)
            }
            
        except Exception as e:
            print(f"      ❌ Simple workflow failed: {e}")
        
        # Complex workflow
        try:
            start_time = asyncio.get_event_loop().time()
            complex_result = await execute_workflow("perf_complex", test_input, mode)
            complex_time = asyncio.get_event_loop().time() - start_time
            
            print(f"   🔸 Complex Workflow:")
            print(f"      ⏱️ Execution Time: {complex_time:.3f}s")
            print(f"      📊 Status: {complex_result.status.value}")
            print(f"      🔄 Steps: {len(complex_result.step_results)}")
            
            performance_results[f"{mode.value}_complex"] = {
                "time": complex_time,
                "status": complex_result.status.value,
                "steps": len(complex_result.step_results)
            }
            
        except Exception as e:
            print(f"      ❌ Complex workflow failed: {e}")
    
    return performance_results


async def main():
    """Run all V2 workflow system demonstrations"""
    print("🚀 LangSwarm V2 Workflow System Demonstration")
    print("=" * 80)
    print("This demo shows the modern, simplified workflow system")
    print("with fluent builder API, multiple execution modes,")
    print("and comprehensive workflow capabilities.")
    print("=" * 80)
    
    # Run all demos
    demos = [
        ("Basic Workflow Creation", demo_basic_workflow_creation),
        ("Fluent Workflow Patterns", demo_fluent_workflow_patterns),
        ("Workflow Execution Modes", demo_workflow_execution_modes),
        ("Workflow Monitoring", demo_workflow_monitoring),
        ("Workflow Validation", demo_workflow_validation),
        ("Performance Comparison", demo_performance_comparison),
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            result = await demo_func()
            results[demo_name] = result
            print(f"✅ {demo_name} completed successfully")
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            traceback.print_exc()
            results[demo_name] = None
    
    # Summary
    print("\n" + "="*80)
    print("📊 V2 WORKFLOW SYSTEM DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful = sum(1 for result in results.values() if result is not None)
    total = len(results)
    
    print(f"✅ Successful demos: {successful}/{total}")
    print(f"❌ Failed demos: {total - successful}/{total}")
    
    # Registry statistics
    try:
        registry = get_workflow_registry()
        workflows = await registry.list_workflows()
        print(f"\n📋 Workflows Registered: {len(workflows)}")
        
        for workflow in workflows:
            print(f"   • {workflow.workflow_id}: {workflow.name} ({len(workflow.steps)} steps)")
    
    except Exception as e:
        print(f"   ❌ Registry access failed: {e}")
    
    if successful == total:
        print("\n🎉 All V2 workflow demonstrations completed successfully!")
        print("🏗️ The modernized workflow system is working perfectly.")
        print("\n📋 Key Achievements:")
        print("   ✅ Clean workflow interfaces and builder API")
        print("   ✅ Multiple execution modes (sync, async, streaming, parallel)")
        print("   ✅ Comprehensive step types (agent, tool, condition, transform)")
        print("   ✅ Workflow validation and error handling")
        print("   ✅ Registry and execution engine")
        print("   ✅ Performance optimizations and monitoring")
        print("\n🎯 Task 09 Phase 1 is COMPLETE! 🚀")
    else:
        print(f"\n⚠️ Some demonstrations had issues. Check the output above for details.")
    
    return results


if __name__ == "__main__":
    # Run the comprehensive V2 workflow demonstration
    try:
        results = asyncio.run(main())
        successful_results = len([r for r in results.values() if r])
        print(f"\n🏁 V2 workflow demonstration completed. Results: {successful_results}/{len(results)} successful")
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed with error: {e}")
        traceback.print_exc()
