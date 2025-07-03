#!/usr/bin/env python3
"""
Complete YAML Configuration Example: Enhanced MCP Patterns with Filesystem Tool

This example shows how to use YAML configuration files to set up and use
MCP tools with the enhanced middleware patterns.

Run this example:
1. Ensure your YAML files are configured properly
2. Run: python test_filesystem_example.py

The key insight: Your agent MUST list the tools it uses in the "tools" field!
"""

import os
import tempfile
from pathlib import Path

# Import LangSwarm components
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor


def create_test_file():
    """Create a temporary test file for demonstration"""
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "demo.txt")
    
    with open(test_file, 'w') as f:
        f.write("Hello from Enhanced MCP Patterns!\nThis file was read using YAML configuration.\n")
    
    print(f"📄 Created test file: {test_file}")
    return test_file, test_dir


def test_yaml_configuration():
    """Test the YAML configuration approach"""
    print("🚀 Testing YAML Configuration with Enhanced MCP Patterns")
    print("=" * 60)
    
    # Load configuration from YAML files in current directory
    config_path = "."  # Current directory with tools.yaml, agents.yaml, workflows.yaml
    
    try:
        print("🔧 Loading configuration from YAML files...")
        loader = LangSwarmConfigLoader(config_path=config_path)
        workflows, agents, brokers, tools = loader.load()
        
        print(f"✅ Loaded {len(tools)} tools")
        print(f"✅ Loaded {len(agents)} agents")
        print(f"✅ Loaded {len(workflows)} workflows")
        
        # Print loaded tools for verification
        print("\n📋 Loaded Tools:")
        for tool in tools:
            print(f"  - {tool.identifier}: {tool.description}")
            print(f"    Type: {tool.type}")
            print(f"    Local mode: {getattr(tool, 'local_mode', False)}")
        
        # Print loaded agents
        print("\n👥 Loaded Agents:")
        for agent_id, agent in agents.items():
            print(f"  - {agent_id}: {type(agent).__name__}")
            
            # Check if agent has tool registry
            if hasattr(agent, 'tool_registry'):
                print(f"    Tool registry: {agent.tool_registry}")
                if hasattr(agent.tool_registry, 'list_tools'):
                    tools_list = agent.tool_registry.list_tools()
                    print(f"    Registered tools: {tools_list}")
            else:
                print("    No tool registry found")
        
        return True, loader, workflows, agents, tools
        
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, None, None


def test_workflow_execution(loader, workflows, agents):
    """Test executing a workflow with the filesystem tool"""
    print("\n🧪 Testing Workflow Execution")
    print("-" * 40)
    
    try:
        # Create test file
        test_file, test_dir = create_test_file()
        
        # Create workflow executor
        executor = WorkflowExecutor(workflows, agents)
        
        # Test workflow execution with filesystem operation
        user_input = f'''Read the file {test_file}'''
        
        print(f"📝 User input: {user_input}")
        
        # Execute the workflow
        result = executor.run_workflow(
            "simple_filesystem_workflow", 
            user_input=user_input
        )
        
        print(f"✅ Workflow result: {result}")
        
        # Cleanup
        os.unlink(test_file)
        os.rmdir(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_agent_interaction(agents):
    """Test direct agent interaction with middleware"""
    print("\n🧪 Testing Direct Agent Interaction")
    print("-" * 40)
    
    try:
        # Get the filesystem agent
        filesystem_agent = agents.get("filesystem_agent")
        if not filesystem_agent:
            print("❌ filesystem_agent not found in loaded agents")
            return False
        
        # Create test file
        test_file, test_dir = create_test_file()
        
        # Test direct MCP call through agent
        mcp_request = {
            "mcp": {
                "tool": "filesystem",
                "method": "read_file",
                "params": {"path": test_file}
            }
        }
        
        print(f"📝 MCP request: {mcp_request}")
        
        # Check if agent has middleware capability
        if hasattr(filesystem_agent, 'to_middleware'):
            status, result = filesystem_agent.to_middleware(mcp_request)
            print(f"✅ Status: {status}")
            print(f"✅ Result: {result}")
            success = True
        else:
            print("❌ Agent does not have middleware capability")
            success = False
        
        # Cleanup
        os.unlink(test_file)
        os.rmdir(test_dir)
        
        return success
        
    except Exception as e:
        print(f"❌ Agent Interaction Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution function"""
    print("🎯 Enhanced MCP Patterns - Complete YAML Configuration Example")
    print("=" * 70)
    
    # Test 1: Load YAML configuration
    config_success, loader, workflows, agents, tools = test_yaml_configuration()
    
    if not config_success:
        print("\n💥 Configuration failed - check your YAML files!")
        print("\nRequired files:")
        print("  - tools.yaml: Define your MCP tools")
        print("  - agents.yaml: Define agents that use tools (include 'tools: [filesystem]')")
        print("  - workflows.yaml: Define workflows that use agents")
        return False
    
    # Test 2: Workflow execution
    workflow_success = test_workflow_execution(loader, workflows, agents)
    
    # Test 3: Direct agent interaction  
    agent_success = test_direct_agent_interaction(agents)
    
    # Results
    print("\n📊 Test Results")
    print("-" * 20)
    print(f"Configuration: {'✅ PASS' if config_success else '❌ FAIL'}")
    print(f"Workflow:      {'✅ PASS' if workflow_success else '❌ FAIL'}")
    print(f"Agent Direct:  {'✅ PASS' if agent_success else '❌ FAIL'}")
    
    overall_success = config_success and (workflow_success or agent_success)
    print(f"\nOverall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        print("\n🎉 YAML configuration is working correctly!")
        print("🔑 Key Point: Your agent MUST include 'tools: [filesystem]' in agents.yaml")
        print("💡 The enhanced MCP patterns work seamlessly with YAML configuration")
        print("💡 No manual coding required - everything is configured via YAML!")
    else:
        print("\n❌ Please check your YAML configuration files")
        print("💡 Ensure your agent includes the tools it needs in the 'tools' list")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 