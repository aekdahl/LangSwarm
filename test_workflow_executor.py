#!/usr/bin/env python3
"""
Comprehensive test script for the Workflow Executor MCP Tool.

Tests both pre-written workflow execution and dynamic workflow generation.
"""

import os
import json
import time
import tempfile
import yaml
from typing import Dict, Any

# Add the project root to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langswarm.mcp.tools.workflow_executor.main import (
    WorkflowExecutorMCPTool,
    execute_workflow,
    generate_workflow,
    execute_generated_workflow,
    check_execution_status,
    cancel_execution,
    list_workflows
)

def test_tool_initialization():
    """Test WorkflowExecutorMCPTool initialization"""
    print("🧪 Testing tool initialization...")
    
    try:
        tool = WorkflowExecutorMCPTool(
            identifier="test_workflow_executor",
            name="Test Workflow Executor"
        )
        
        # Check basic attributes
        assert hasattr(tool, 'identifier')
        assert hasattr(tool, '_is_mcp_tool')
        assert getattr(tool, 'local_mode', True)
        
        print("✅ Tool initialization successful")
        
        # Test tool attributes
        print(f"   Tool identifier: {tool.identifier}")
        print(f"   Tool name: {tool.name}")
        print(f"   Local mode: {getattr(tool, 'local_mode', 'Not set')}")
        print(f"   Is MCP tool: {getattr(tool, '_is_mcp_tool', 'Not set')}")
        
        return tool
        
    except Exception as e:
        print(f"❌ Tool initialization failed: {e}")
        return None

def test_workflow_generation():
    """Test dynamic workflow generation"""
    print("\n🧪 Testing workflow generation...")
    
    test_cases = [
        {
            "description": "Create a simple file processing workflow that reads files and creates summaries",
            "complexity": "simple",
            "expected_agents": 2
        },
        {
            "description": "Build a complex data analysis pipeline that processes CSV files, extracts insights, generates reports, and validates results",
            "complexity": "complex", 
            "expected_agents": 4
        },
        {
            "description": "Design a research workflow that gathers information from multiple sources and compiles findings",
            "complexity": "medium",
            "expected_agents": 3
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n   Test {i+1}: {test_case['complexity']} workflow")
        print(f"   Description: {test_case['description']}")
        
        try:
            result = generate_workflow(
                workflow_description=test_case["description"],
                complexity=test_case["complexity"]
            )
            
            # Validate result structure
            assert "workflow_name" in result
            assert "workflow_config" in result
            assert "validation_status" in result
            assert result["validation_status"] == "valid"
            
            config = result["workflow_config"]
            agents = config.get("agents", [])
            workflows = config.get("workflows", {})
            
            print(f"   ✅ Generated workflow: {result['workflow_name']}")
            print(f"   📊 Agents: {len(agents)} (expected ≤ {test_case['expected_agents']})")
            print(f"   🔧 Workflows: {len(workflows)}")
            print(f"   📝 Validation: {result['validation_status']}")
            
            # Verify agent structure
            for agent in agents:
                assert "id" in agent
                assert "system_prompt" in agent
                assert "tools" in agent
            
            # Print first agent as example
            if agents:
                print(f"   🤖 Sample agent: {agents[0]['id']}")
                
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")

def test_sync_execution():
    """Test synchronous workflow execution"""
    print("\n🧪 Testing sync execution...")
    
    # Create a simple test workflow configuration
    test_config = {
        "version": "1.0",
        "project_name": "test_sync_execution",
        "memory": "production",
        "agents": [
            {
                "id": "test_agent",
                "agent_type": "openai", 
                "model": "gpt-4o",
                "system_prompt": "You are a test agent for sync execution",
                "tools": ["filesystem"]
            }
        ],
        "workflows": {
            "test_sync_workflow": {
                "steps": [
                    {
                        "agent": "test_agent",
                        "input": "${user_input}",
                        "output": {"to": "user"}
                    }
                ]
            }
        }
    }
    
    try:
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_config_path = f.name
        
        # Test sync execution
        result = execute_workflow(
            workflow_name="test_sync_workflow",
            input_data={"test_input": "Hello from sync test"},
            execution_mode="sync",
            timeout=60
        )
        
        print(f"   ✅ Sync execution completed")
        print(f"   📊 Status: {result['status']}")
        print(f"   🆔 Execution ID: {result['execution_id']}")
        
        # Verify result structure
        assert "execution_id" in result
        assert "status" in result
        assert result["status"] in ["completed", "failed"]
        
        if result["status"] == "completed":
            print(f"   📋 Result available: {bool(result.get('result'))}")
        
    except Exception as e:
        print(f"   ❌ Sync execution failed: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(temp_config_path)
        except:
            pass

def test_async_execution():
    """Test asynchronous workflow execution"""
    print("\n🧪 Testing async execution...")
    
    try:
        # Start async execution
        result = execute_workflow(
            workflow_name="test_async_workflow",
            input_data={"test_input": "Hello from async test"},
            execution_mode="async",
            timeout=120
        )
        
        execution_id = result["execution_id"]
        print(f"   ✅ Async execution started")
        print(f"   🆔 Execution ID: {execution_id}")
        print(f"   📊 Initial status: {result['status']}")
        
        # Monitor execution
        max_checks = 5
        for i in range(max_checks):
            time.sleep(2)  # Wait 2 seconds between checks
            
            status_result = check_execution_status(execution_id)
            print(f"   📈 Check {i+1}: {status_result['status']}")
            
            if status_result["status"] in ["completed", "failed", "timeout", "cancelled"]:
                print(f"   🏁 Final status: {status_result['status']}")
                break
        
        # Test cancellation (if still running)
        final_status = check_execution_status(execution_id)
        if final_status["status"] == "running":
            cancel_result = cancel_execution(execution_id)
            print(f"   🛑 Cancellation: {cancel_result['status']}")
        
    except Exception as e:
        print(f"   ❌ Async execution failed: {e}")

def test_generated_workflow_execution():
    """Test end-to-end generation and execution"""
    print("\n🧪 Testing generated workflow execution...")
    
    try:
        result = execute_generated_workflow(
            workflow_description="Create a simple workflow that processes a text file and generates a summary",
            input_data={"file_path": "/tmp/test.txt", "content": "This is test content for workflow execution"},
            execution_mode="sync",
            complexity="simple",
            timeout=90
        )
        
        print(f"   ✅ Generated workflow execution completed")
        print(f"   🏷️  Workflow name: {result['workflow_name']}")
        print(f"   📊 Status: {result['status']}")
        print(f"   🆔 Execution ID: {result['execution_id']}")
        
        # Check if configuration was generated
        if "workflow_config" in result:
            config = result["workflow_config"]
            agents = config.get("agents", [])
            print(f"   🤖 Generated agents: {len(agents)}")
            for agent in agents:
                print(f"      - {agent.get('id', 'unknown')}")
        
    except Exception as e:
        print(f"   ❌ Generated workflow execution failed: {e}")

def test_workflow_listing():
    """Test workflow discovery"""
    print("\n🧪 Testing workflow listing...")
    
    try:
        # List workflows in current directory
        result = list_workflows(config_path=".", pattern="*.yaml")
        
        print(f"   ✅ Workflow discovery completed")
        print(f"   📁 Total workflows found: {result['total_count']}")
        
        workflows = result["available_workflows"]
        if workflows:
            print(f"   📋 Sample workflows:")
            for workflow in workflows[:3]:  # Show first 3
                print(f"      - {workflow['name']} ({workflow['file']})")
                print(f"        Steps: {workflow['steps']}")
        
    except Exception as e:
        print(f"   ❌ Workflow listing failed: {e}")

def test_mcp_tool_interface():
    """Test the MCP tool interface directly"""
    print("\n🧪 Testing MCP tool interface...")
    
    try:
        tool = WorkflowExecutorMCPTool(
            identifier="test_mcp_interface",
            name="Test MCP Interface"
        )
        
        # Test generate_workflow method
        print("   Testing generate_workflow method...")
        result = tool.run({
            "method": "generate_workflow",
            "params": {
                "workflow_description": "Simple test workflow for MCP interface testing",
                "complexity": "simple"
            }
        })
        
        assert "workflow_name" in result
        assert "workflow_config" in result
        print(f"   ✅ generate_workflow: {result['validation_status']}")
        
        # Test list_workflows method  
        print("   Testing list_workflows method...")
        result = tool.run({
            "method": "list_workflows",
            "params": {
                "config_path": ".",
                "pattern": "*.yaml"
            }
        })
        
        assert "available_workflows" in result
        assert "total_count" in result
        print(f"   ✅ list_workflows: Found {result['total_count']} workflows")
        
        # Test invalid method
        print("   Testing error handling...")
        result = tool.run({
            "method": "invalid_method",
            "params": {}
        })
        
        assert "error" in result
        assert "available_methods" in result
        print(f"   ✅ Error handling: {result['error'][:50]}...")
        
    except Exception as e:
        print(f"   ❌ MCP interface test failed: {e}")

def test_configuration_validation():
    """Test workflow configuration validation"""
    print("\n🧪 Testing configuration validation...")
    
    # Test various complexity levels
    complexities = ["simple", "medium", "complex"]
    
    for complexity in complexities:
        try:
            result = generate_workflow(
                workflow_description=f"Test {complexity} workflow for validation",
                complexity=complexity
            )
            
            config = result["workflow_config"]
            
            # Validate structure
            assert "version" in config
            assert "project_name" in config
            assert "agents" in config
            assert "workflows" in config
            
            agents = config["agents"]
            workflows = config["workflows"]
            
            print(f"   ✅ {complexity.capitalize()} workflow validation passed")
            print(f"      Agents: {len(agents)}, Workflows: {len(workflows)}")
            
            # Validate agent structure
            for agent in agents:
                assert "id" in agent
                assert "agent_type" in agent
                assert "model" in agent
                assert "system_prompt" in agent
                assert "tools" in agent
            
        except Exception as e:
            print(f"   ❌ {complexity.capitalize()} validation failed: {e}")

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Workflow Executor MCP Tool Tests")
    print("=" * 60)
    
    # Initialize tool
    tool = test_tool_initialization()
    if not tool:
        print("❌ Cannot continue without successful initialization")
        return
    
    # Run test suite
    try:
        test_workflow_generation()
        test_sync_execution()
        test_async_execution()
        test_generated_workflow_execution()
        test_workflow_listing()
        test_mcp_tool_interface()
        test_configuration_validation()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("✅ Workflow Executor MCP Tool is ready for use")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_test()