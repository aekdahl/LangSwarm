#!/usr/bin/env python3
"""
Test SQL Database MCP Tool Debug Workflow
=========================================

Test script for debugging the SQL Database MCP tool with sample queries.
"""

import sys
import os
sys.path.insert(0, '.')

from langswarm.v1.core.config import LangSwarmConfigLoader

def test_sql_database_debug():
    """Test the SQL Database debug workflow with various queries"""
    
    print("🔄 Testing SQL Database MCP Tool Debug Workflow...")
    
    try:
        # Load the debug config 
        config_path = 'langswarm/core/debug/test_configs/sql_database_debug.yaml'
        loader = LangSwarmConfigLoader(config_path)
        workflows, agents, brokers, tools, metadata = loader.load()
        
        print("✅ Config loaded successfully!")
        
        # Convert tools list to dict if needed
        if isinstance(tools, list):
            tools_dict = {}
            for tool_instance in tools:
                if hasattr(tool_instance, 'identifier'):
                    tools_dict[tool_instance.identifier] = tool_instance
                elif hasattr(tool_instance, 'name'):
                    tools_dict[tool_instance.name] = tool_instance
                else:
                    tools_dict[type(tool_instance).__name__] = tool_instance
            tools = tools_dict
        
        print(f"✅ Loaded {len(tools)} tools: {list(tools.keys())}")
        
        # Get the test agent
        agent = agents.get('sql_test_agent')
        if not agent:
            print("❌ Could not find sql_test_agent")
            return False
            
        # Handle the case where agents is a dict of agent instances
        agent_name = getattr(agent, 'name', 'sql_test_agent')
        print(f"✅ Agent loaded: {agent_name}")
        
        # Set workflow context 
        workflow_context = {
            'config_loader': loader,
            'tools': tools,
            'user_input': 'test'
        }
        agent.set_workflow_context(workflow_context)
        
        # Test cases
        test_cases = [
            {
                "name": "Database Info",
                "description": "Get database structure and table information",
                "mcp_call": {
                    "response": "I'll show you what tables and data are available in the database.",
                    "mcp": {
                        "tool": "sql_db",
                        "method": "get_database_info",
                        "params": {"include_schema": True}
                    }
                }
            },
            {
                "name": "List Active Users",
                "description": "Query active users from the database",
                "mcp_call": {
                    "response": "I'll get a list of all active users from the database.",
                    "mcp": {
                        "tool": "sql_db",
                        "method": "execute_query", 
                        "params": {"query": "SELECT name, email, department FROM users WHERE active = 1 ORDER BY name"}
                    }
                }
            },
            {
                "name": "Recent Orders Summary",
                "description": "Get recent orders with customer information",
                "mcp_call": {
                    "response": "I'll show you recent orders with customer details.",
                    "mcp": {
                        "tool": "sql_db",
                        "method": "execute_query",
                        "params": {"query": "SELECT * FROM recent_orders LIMIT 5"}
                    }
                }
            },
            {
                "name": "Order Summary by Department",
                "description": "Get order statistics grouped by department", 
                "mcp_call": {
                    "response": "I'll provide an order summary broken down by department.",
                    "mcp": {
                        "tool": "sql_db",
                        "method": "execute_query",
                        "params": {"query": "SELECT * FROM order_summary"}
                    }
                }
            }
        ]
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['name']}")
            print(f"   Description: {test_case['description']}")
            
            try:
                status, response = agent.to_middleware(test_case['mcp_call'])
                print(f"   Status: {status}")
                
                if status == 201:
                    import json
                    result = json.loads(response)
                    
                    if result.get('success'):
                        print(f"   ✅ Query executed successfully")
                        if 'results' in result:
                            print(f"   📊 Rows returned: {result.get('row_count', 0)}")
                            if result.get('results'):
                                print(f"   📋 Columns: {', '.join(result.get('columns', []))}")
                        print(f"   ⏱️ Execution time: {result.get('execution_time_ms', 0):.2f}ms")
                    else:
                        print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"   ⚠️ Unexpected status: {status}")
                    print(f"   Response: {response[:200]}...")
                    
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        
        print(f"\n🎉 SQL Database debug workflow testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sql_database_debug()
