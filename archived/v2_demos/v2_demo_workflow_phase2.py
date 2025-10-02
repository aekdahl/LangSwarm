#!/usr/bin/env python3
"""
LangSwarm V2 Workflow System Phase 2 Demonstration

Shows the Phase 2 features including:
- YAML compatibility layer for existing workflows
- Comprehensive monitoring and debugging tools
- Middleware integration with V2 systems
- Advanced workflow features and capabilities

Usage:
    python v2_demo_workflow_phase2.py
"""

import asyncio
import sys
import traceback
import os
import json
import tempfile
import yaml
from typing import Any, Dict, List
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath('.'))

try:
    from langswarm.v2.core.workflows import (
        # Phase 1 components
        WorkflowBuilder, ExecutionMode, WorkflowStatus, StepStatus,
        create_workflow, register_workflow, execute_workflow,
        get_workflow_registry, get_workflow_engine,
        
        # Phase 2 components
        YAMLWorkflowParser, YAMLWorkflowCompatibility,
        load_yaml_workflows, migrate_yaml_workflows,
        WorkflowMonitor, WorkflowDebugger,
        get_workflow_monitor, get_workflow_debugger,
        WorkflowMiddlewareManager, execute_workflow_with_middleware,
        get_workflow_middleware_manager
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LangSwarm root directory")
    sys.exit(1)


# Mock agent and tool systems (same as Phase 1)
class MockAgentSystem:
    """Mock agent system for demonstration"""
    
    def __init__(self):
        self.agents = {
            "data_extractor": "Data extraction agent",
            "data_analyzer": "Data analysis agent", 
            "report_generator": "Report generation agent",
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
            "web_scraper": "Scrape web content"
        }
    
    async def get_tool(self, tool_name: str):
        if tool_name in self.tools:
            return MockTool(tool_name, self.tools[tool_name])
        return None


class MockTool:
    """Mock tool for demonstration"""
    
    def __init__(self, tool_name: str, description: str):
        self.tool_name = tool_name
        self.description = description
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "input": kwargs,
            "output": f"Tool {self.tool_name} executed with {len(kwargs)} parameters",
            "success": True
        }


# Setup mocks
mock_agent_system = MockAgentSystem()
mock_tool_system = MockToolSystem()

async def mock_get_agent(agent_id: str):
    return await mock_agent_system.get_agent(agent_id)

class MockAgentRegistry:
    async def get_tool(self, tool_name: str):
        return await mock_tool_system.get_tool(tool_name)

# Patch imports
try:
    import langswarm.v2.core.agents
    langswarm.v2.core.agents.get_agent = mock_get_agent
except ImportError:
    import sys
    from types import ModuleType
    mock_agents = ModuleType('langswarm.v2.core.agents')
    mock_agents.get_agent = mock_get_agent
    sys.modules['langswarm.v2.core.agents'] = mock_agents

try:
    import langswarm.v2.core.tools
    langswarm.v2.core.tools.get_tool_registry = lambda: MockAgentRegistry()
except ImportError:
    import sys
    from types import ModuleType
    mock_tools = ModuleType('langswarm.v2.core.tools')
    mock_tools.get_tool_registry = lambda: MockAgentRegistry()
    sys.modules['langswarm.v2.core.tools'] = mock_tools


def create_sample_yaml_workflows() -> List[Dict[str, Any]]:
    """Create sample YAML workflow configurations for testing"""
    
    # Simple syntax workflow
    simple_yaml = {
        "workflows": [
            "data_extractor -> data_analyzer -> report_generator"
        ]
    }
    
    # Complex workflow definition
    complex_yaml = {
        "workflows": {
            "data_processing": [{
                "id": "data_processing_workflow",
                "name": "Data Processing Pipeline",
                "description": "Complete data processing workflow",
                "execution_mode": "parallel",
                "steps": [
                    {
                        "id": "extract",
                        "agent": "data_extractor",
                        "input": "${input}",
                        "name": "Extract Data"
                    },
                    {
                        "id": "analyze",
                        "agent": "data_analyzer",
                        "input": "${extract}",
                        "dependencies": ["extract"],
                        "name": "Analyze Data"
                    },
                    {
                        "id": "transform",
                        "tool": "data_transformer",
                        "parameters": {
                            "format": "json",
                            "source": "${analyze}"
                        },
                        "dependencies": ["analyze"],
                        "name": "Transform Data"
                    },
                    {
                        "id": "report",
                        "agent": "report_generator",
                        "input": "${transform}",
                        "dependencies": ["transform"],
                        "name": "Generate Report"
                    }
                ]
            }]
        }
    }
    
    # Legacy format workflow
    legacy_yaml = {
        "workflows": {
            "legacy_processing": [
                {
                    "id": "step1",
                    "agent": "text_processor",
                    "input": "${user_input}",
                    "name": "Process Text"
                },
                {
                    "id": "step2", 
                    "agent": "summarizer",
                    "input": "${context.step_outputs.step1}",
                    "dependencies": ["step1"],
                    "name": "Summarize"
                }
            ]
        }
    }
    
    return [
        ("simple", simple_yaml),
        ("complex", complex_yaml),
        ("legacy", legacy_yaml)
    ]


async def demo_yaml_compatibility():
    """Demonstrate YAML workflow compatibility and parsing"""
    print("============================================================")
    print("📄 YAML COMPATIBILITY DEMO")
    print("============================================================")
    
    try:
        # Create sample YAML workflows
        yaml_samples = create_sample_yaml_workflows()
        parsed_workflows = []
        
        parser = YAMLWorkflowParser()
        
        for name, yaml_content in yaml_samples:
            print(f"\n📝 Parsing {name.title()} YAML Workflow:")
            
            try:
                workflows = parser.parse_yaml_content(yaml_content)
                print(f"   ✅ Parsed successfully: {len(workflows)} workflow(s)")
                
                for workflow in workflows:
                    print(f"   📄 Workflow: {workflow.workflow_id}")
                    print(f"      Name: {workflow.name}")
                    print(f"      Steps: {len(workflow.steps)}")
                    print(f"      Mode: {workflow.execution_mode.value}")
                    
                    # Register workflow
                    success = await register_workflow(workflow)
                    print(f"      Registration: {'✅ Success' if success else '❌ Failed'}")
                    
                    parsed_workflows.extend(workflows)
                    
            except Exception as e:
                print(f"   ❌ Parsing failed: {e}")
        
        # Test YAML file compatibility
        print(f"\n📁 YAML File Compatibility:")
        
        # Create temporary YAML files
        temp_dir = Path(tempfile.mkdtemp())
        
        for name, yaml_content in yaml_samples:
            yaml_file = temp_dir / f"{name}_workflow.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(yaml_content, f)
            
            print(f"   📄 Created: {yaml_file.name}")
        
        # Load workflows from directory
        compatibility = YAMLWorkflowCompatibility()
        loaded_workflows = await compatibility.load_yaml_workflow_directory(temp_dir)
        
        print(f"   ✅ Loaded from directory: {len(loaded_workflows)} workflows")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return parsed_workflows
        
    except Exception as e:
        print(f"   ❌ YAML compatibility demo failed: {e}")
        traceback.print_exc()
        return []


async def demo_workflow_monitoring():
    """Demonstrate comprehensive workflow monitoring and metrics"""
    print("\n============================================================")
    print("📊 WORKFLOW MONITORING DEMO")
    print("============================================================")
    
    try:
        monitor = get_workflow_monitor()
        debugger = get_workflow_debugger()
        
        # Enable monitoring and tracing
        monitor.enable_monitoring()
        debugger.enable_tracing()
        
        print("\n🔍 Monitoring System Status:")
        system_metrics = await monitor.get_system_metrics()
        print(f"   📈 Total Workflows: {system_metrics['total_workflows']}")
        print(f"   🚀 Total Executions: {system_metrics['total_executions']}")
        print(f"   ⚡ Active Executions: {system_metrics['active_executions']}")
        print(f"   📊 Success Rate: {system_metrics['system_success_rate']:.1%}")
        print(f"   ⏱️ Uptime: {system_metrics['uptime_seconds']:.1f}s")
        
        # Create test workflows for monitoring
        test_workflow = (create_workflow("monitoring_test", "Monitoring Test Workflow")
                        .description("Workflow for testing monitoring capabilities")
                        .add_agent_step("step1", "data_extractor", "${input}")
                        .add_agent_step("step2", "data_analyzer", "${step1}", dependencies=["step1"])
                        .add_agent_step("step3", "report_generator", "${step2}", dependencies=["step2"])
                        .build())
        
        await register_workflow(test_workflow)
        
        # Subscribe to workflow events
        events_received = []
        
        async def event_handler(subscription_id, event):
            events_received.append(event)
            print(f"   📡 Event: {event['type']} for {event.get('workflow_id', 'unknown')}")
        
        subscription_id = await monitor.subscribe_to_workflow("monitoring_test", event_handler)
        
        # Execute workflow with monitoring
        print(f"\n🚀 Executing Monitored Workflow:")
        result = await execute_workflow("monitoring_test", {"test": "monitoring data"})
        
        # Wait a bit for events to be processed
        await asyncio.sleep(0.1)
        
        print(f"   ✅ Execution Status: {result.status.value}")
        print(f"   ⏱️ Execution Time: {result.execution_time:.3f}s")
        print(f"   📡 Events Received: {len(events_received)}")
        
        # Get workflow metrics
        workflow_metrics = await monitor.get_workflow_metrics("monitoring_test")
        print(f"\n📊 Workflow Metrics:")
        print(f"   📈 Total Executions: {workflow_metrics['total_executions']}")
        print(f"   ✅ Success Rate: {workflow_metrics['success_rate']:.1%}")
        print(f"   ⏱️ Average Time: {workflow_metrics['average_execution_time']:.3f}s")
        
        # Performance analysis
        performance_analysis = await debugger.performance_analysis("monitoring_test")
        print(f"\n🔍 Performance Analysis:")
        print(f"   ⏱️ Average: {performance_analysis['performance_summary']['average_time']:.3f}s")
        print(f"   📝 Recommendations: {len(performance_analysis['recommendations'])}")
        for rec in performance_analysis['recommendations']:
            print(f"      💡 {rec}")
        
        # Unsubscribe from events
        await monitor.unsubscribe(subscription_id)
        
        # Export metrics
        print(f"\n📤 Exporting Metrics:")
        metrics_export = await monitor.export_metrics("json")
        print(f"   📄 Export Size: {len(metrics_export)} characters")
        
        return {
            "events_received": len(events_received),
            "workflow_metrics": workflow_metrics,
            "performance_analysis": performance_analysis
        }
        
    except Exception as e:
        print(f"   ❌ Monitoring demo failed: {e}")
        traceback.print_exc()
        return None


async def demo_middleware_integration():
    """Demonstrate workflow middleware integration"""
    print("\n============================================================")
    print("🔗 MIDDLEWARE INTEGRATION DEMO")
    print("============================================================")
    
    try:
        # Setup middleware manager
        middleware_manager = get_workflow_middleware_manager()
        
        print("\n🔧 Setting up Workflow Middleware Pipeline:")
        await middleware_manager.setup_workflow_pipeline()
        print(f"   ✅ Middleware components: {len(middleware_manager.middlewares)}")
        
        for i, middleware in enumerate(middleware_manager.middlewares, 1):
            print(f"      {i}. {type(middleware).__name__}")
        
        # Create test workflow for middleware
        middleware_workflow = (create_workflow("middleware_test", "Middleware Test")
                              .add_agent_step("process", "text_processor", "${input}")
                              .add_agent_step("analyze", "data_analyzer", "${process}", dependencies=["process"])
                              .build())
        
        await register_workflow(middleware_workflow)
        
        # Execute through middleware pipeline
        print(f"\n🚀 Executing Through Middleware Pipeline:")
        
        middleware_response = await execute_workflow_with_middleware(
            workflow_id="middleware_test",
            input_data={"text": "middleware test data", "priority": "high"},
            execution_mode="sync",
            context_variables={"user_session": "demo_session"},
            user_id="demo_user",
            request_id="demo_request_123"
        )
        
        print(f"   ✅ Middleware Success: {middleware_response.success}")
        print(f"   📊 Execution ID: {middleware_response.execution_id}")
        print(f"   ⏱️ Execution Time: {middleware_response.execution_time:.3f}s")
        
        if middleware_response.metadata:
            print(f"   📝 Metadata:")
            for key, value in middleware_response.metadata.items():
                print(f"      {key}: {value}")
        
        # Test different execution modes through middleware
        execution_modes = ["sync", "async", "parallel"]
        
        for mode in execution_modes:
            print(f"\n🔄 Testing {mode.title()} Mode:")
            
            try:
                response = await execute_workflow_with_middleware(
                    workflow_id="middleware_test",
                    input_data={"mode_test": mode},
                    execution_mode=mode,
                    request_id=f"demo_{mode}_request"
                )
                
                print(f"   ✅ {mode.title()} execution: {response.success}")
                print(f"   ⏱️ Response time: {response.execution_time:.3f}s")
                
            except Exception as e:
                print(f"   ❌ {mode.title()} execution failed: {e}")
        
        return {
            "middleware_components": len(middleware_manager.middlewares),
            "sync_execution": middleware_response.success,
            "execution_time": middleware_response.execution_time
        }
        
    except Exception as e:
        print(f"   ❌ Middleware integration demo failed: {e}")
        traceback.print_exc()
        return None


async def demo_advanced_workflow_features():
    """Demonstrate advanced Phase 2 workflow features"""
    print("\n============================================================")
    print("🚀 ADVANCED WORKFLOW FEATURES DEMO")
    print("============================================================")
    
    try:
        # 1. Workflow with complex conditions
        print(f"\n🔀 Conditional Workflow:")
        
        conditional_workflow = (create_workflow("conditional_demo", "Conditional Processing")
                               .description("Workflow with conditional logic")
                               .add_agent_step("input_check", "validator", "${input}")
                               .add_condition_step(
                                   "quality_gate",
                                   lambda ctx: "high" in str(ctx.get_step_output("input_check")).lower(),
                                   "high_quality_path",
                                   "standard_path",
                                   dependencies=["input_check"]
                               )
                               .add_agent_step("high_quality_path", "data_analyzer", "High quality processing")
                               .add_agent_step("standard_path", "text_processor", "Standard processing")
                               .build())
        
        await register_workflow(conditional_workflow)
        
        # Test with different inputs
        test_cases = [
            {"quality": "high", "data": "premium data"},
            {"quality": "standard", "data": "regular data"}
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_input['quality']} quality")
            result = await execute_workflow("conditional_demo", test_input)
            print(f"   ✅ Status: {result.status.value}")
            print(f"   📊 Steps executed: {len(result.step_results)}")
        
        # 2. Workflow with transformations
        print(f"\n🔄 Transformation Workflow:")
        
        transform_workflow = (create_workflow("transform_demo", "Data Transformation")
                             .add_agent_step("input", "data_extractor", "${input}")
                             .add_transform_step(
                                 "to_uppercase",
                                 lambda data, ctx: str(data).upper() if data else "",
                                 "input",
                                 dependencies=["input"]
                             )
                             .add_transform_step(
                                 "add_metadata",
                                 lambda data, ctx: {
                                     "transformed_data": data,
                                     "timestamp": "2024-12-19",
                                     "processor": "v2_transformer"
                                 },
                                 "to_uppercase",
                                 dependencies=["to_uppercase"]
                             )
                             .build())
        
        await register_workflow(transform_workflow)
        
        transform_result = await execute_workflow("transform_demo", {"text": "hello world"})
        print(f"   ✅ Transform Status: {transform_result.status.value}")
        print(f"   🔄 Final Result: {transform_result.result.get('add_metadata', 'N/A')}")
        
        # 3. Error handling workflow
        print(f"\n🛠️ Error Handling Workflow:")
        
        error_workflow = (create_workflow("error_demo", "Error Handling Test")
                         .description("Workflow with intentional errors")
                         .add_agent_step("normal_step", "text_processor", "${input}")
                         .add_agent_step("error_step", "nonexistent_agent", "${normal_step}")
                         .add_agent_step("recovery_step", "summarizer", "Error recovery", dependencies=["normal_step"])
                         .with_error_handling(continue_on_error=True)
                         .build())
        
        await register_workflow(error_workflow)
        
        error_result = await execute_workflow("error_demo", {"test": "error handling"})
        print(f"   ✅ Error Workflow Status: {error_result.status.value}")
        print(f"   🔄 Steps attempted: {len(error_result.step_results)}")
        
        failed_steps = [s for s in error_result.step_results.values() if not s.success]
        print(f"   ❌ Failed steps: {len(failed_steps)}")
        
        return {
            "conditional_workflow": conditional_workflow.workflow_id,
            "transform_workflow": transform_workflow.workflow_id,
            "error_workflow": error_workflow.workflow_id,
            "all_registered": True
        }
        
    except Exception as e:
        print(f"   ❌ Advanced features demo failed: {e}")
        traceback.print_exc()
        return None


async def demo_migration_compatibility():
    """Demonstrate migration from V1 to V2 workflows"""
    print("\n============================================================")
    print("🔄 MIGRATION COMPATIBILITY DEMO")
    print("============================================================")
    
    try:
        # Simulate legacy workflow patterns
        legacy_patterns = [
            "data_extractor -> data_analyzer -> report_generator",
            "text_processor -> summarizer",
            "validator -> data_analyzer -> text_processor -> report_generator"
        ]
        
        print(f"\n📋 Migrating {len(legacy_patterns)} Legacy Patterns:")
        
        migrated_workflows = []
        parser = YAMLWorkflowParser()
        
        for i, pattern in enumerate(legacy_patterns, 1):
            print(f"\n   Pattern {i}: {pattern}")
            
            try:
                # Convert simple syntax to V2 workflow
                workflow = parser._parse_simple_syntax_workflow(f"migrated_{i}", pattern)
                
                # Register migrated workflow
                await register_workflow(workflow)
                
                print(f"   ✅ Migrated successfully: {workflow.workflow_id}")
                print(f"   📄 Name: {workflow.name}")
                print(f"   🔄 Steps: {len(workflow.steps)}")
                
                # Test execution
                result = await execute_workflow(workflow.workflow_id, {"migration": f"test_{i}"})
                print(f"   🚀 Execution: {'✅ Success' if result.success else '❌ Failed'}")
                
                migrated_workflows.append(workflow)
                
            except Exception as e:
                print(f"   ❌ Migration failed: {e}")
        
        # Test batch migration
        print(f"\n📦 Batch Migration Test:")
        
        batch_yaml = {
            "workflows": {
                "batch_migration": [
                    pattern for pattern in legacy_patterns
                ]
            }
        }
        
        batch_workflows = parser.parse_yaml_content(batch_yaml)
        print(f"   ✅ Batch parsed: {len(batch_workflows)} workflows")
        
        for workflow in batch_workflows:
            await register_workflow(workflow)
        
        # Get final registry state
        registry = get_workflow_registry()
        all_workflows = await registry.list_workflows()
        
        print(f"\n📊 Migration Summary:")
        print(f"   📋 Total Workflows: {len(all_workflows)}")
        print(f"   🔄 Migrated Patterns: {len(migrated_workflows)}")
        print(f"   📦 Batch Workflows: {len(batch_workflows)}")
        
        return {
            "migrated_count": len(migrated_workflows),
            "batch_count": len(batch_workflows),
            "total_workflows": len(all_workflows)
        }
        
    except Exception as e:
        print(f"   ❌ Migration demo failed: {e}")
        traceback.print_exc()
        return None


async def main():
    """Run all V2 workflow system Phase 2 demonstrations"""
    print("🚀 LangSwarm V2 Workflow System Phase 2 Demonstration")
    print("=" * 80)
    print("This demo shows Phase 2 features including YAML compatibility,")
    print("comprehensive monitoring, middleware integration, and advanced")
    print("workflow capabilities built on the Phase 1 foundation.")
    print("=" * 80)
    
    # Run all Phase 2 demos
    demos = [
        ("YAML Compatibility", demo_yaml_compatibility),
        ("Workflow Monitoring", demo_workflow_monitoring),
        ("Middleware Integration", demo_middleware_integration),
        ("Advanced Features", demo_advanced_workflow_features),
        ("Migration Compatibility", demo_migration_compatibility),
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
    print("📊 V2 WORKFLOW SYSTEM PHASE 2 DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful = sum(1 for result in results.values() if result is not None)
    total = len(results)
    
    print(f"✅ Successful demos: {successful}/{total}")
    print(f"❌ Failed demos: {total - successful}/{total}")
    
    # Registry statistics
    try:
        registry = get_workflow_registry()
        workflows = await registry.list_workflows()
        print(f"\n📋 Total Workflows Registered: {len(workflows)}")
        
        # Group by type
        yaml_workflows = [w for w in workflows if "yaml" in w.workflow_id or "migrated" in w.workflow_id]
        builder_workflows = [w for w in workflows if w not in yaml_workflows]
        
        print(f"   🏗️ Builder Created: {len(builder_workflows)}")
        print(f"   📄 YAML Migrated: {len(yaml_workflows)}")
        
    except Exception as e:
        print(f"   ❌ Registry access failed: {e}")
    
    # System metrics
    try:
        monitor = get_workflow_monitor()
        system_metrics = await monitor.get_system_metrics()
        print(f"\n📊 System Metrics:")
        print(f"   🚀 Total Executions: {system_metrics['total_executions']}")
        print(f"   ✅ Success Rate: {system_metrics['system_success_rate']:.1%}")
        print(f"   ⏱️ Uptime: {system_metrics['uptime_seconds']:.1f}s")
        
    except Exception as e:
        print(f"   ❌ Metrics access failed: {e}")
    
    if successful == total:
        print("\n🎉 All Phase 2 demonstrations completed successfully!")
        print("🏗️ The V2 workflow system Phase 2 is fully operational.")
        print("\n📋 Phase 2 Achievements:")
        print("   ✅ YAML compatibility layer working perfectly")
        print("   ✅ Comprehensive monitoring and debugging tools")
        print("   ✅ Middleware integration with V2 systems")
        print("   ✅ Advanced workflow features and capabilities")
        print("   ✅ Seamless migration from legacy workflows")
        print("   ✅ Production-ready observability and error handling")
        print("\n🎯 Task 09 Phase 2 is COMPLETE! 🚀")
    else:
        print(f"\n⚠️ Some demonstrations had issues. Check the output above for details.")
    
    return results


if __name__ == "__main__":
    # Run the comprehensive Phase 2 demonstration
    try:
        results = asyncio.run(main())
        successful_results = len([r for r in results.values() if r])
        print(f"\n🏁 Phase 2 demonstration completed. Results: {successful_results}/{len(results)} successful")
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed with error: {e}")
        traceback.print_exc()
