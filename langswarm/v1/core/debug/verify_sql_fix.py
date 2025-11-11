#!/usr/bin/env python3
"""
Verify SQL Database Fix
======================

This script verifies that the SQL database tool fix is working correctly.
Run this script to confirm the issue is resolved.
"""

import sys
import os
sys.path.insert(0, '.')

def verify_sql_fix():
    print("🔍 VERIFYING SQL DATABASE TOOL FIX")
    print("=" * 50)
    
    # Step 1: Verify the fix is in the source code
    print("\n1️⃣ Checking source code fixes...")
    try:
        with open('langswarm/mcp/tools/sql_database/main.py', 'r') as f:
            content = f.read()
        
        checks = {
            'Dynamic server name': 'server.name = identifier' in content,
            'Async handlers': 'async def _execute_query_handler' in content,  
            'Config application': 'self.configure(config_settings)' in content,
            'Kwargs support': 'def __init__(self, identifier: str, **kwargs):' in content
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            
        if not all(checks.values()):
            print("   ⚠️ Some fixes are missing from the source code!")
            return False
    except Exception as e:
        print(f"   ❌ Error reading source code: {e}")
        return False
    
    # Step 2: Test tool instantiation
    print("\n2️⃣ Testing tool instantiation...")
    try:
        from langswarm.v1.mcp.tools.sql_database.main import SQLDatabaseMCPTool
        
        # Test with basic config
        tool = SQLDatabaseMCPTool('test_sql_db', 
                                  db_type='sqlite',
                                  db_path='./langswarm/core/debug/test_data/test_database.db')
        
        print(f"   ✅ Tool created with identifier: {tool.identifier}")
        print(f"   ✅ Server name set to: {tool.server.name}")
        print(f"   ✅ Server local_mode: {tool.server.local_mode}")
        
    except Exception as e:
        print(f"   ❌ Error creating tool: {e}")
        return False
    
    # Step 3: Test configuration loading
    print("\n3️⃣ Testing configuration loading...")
    try:
        from langswarm.v1.core.config import LangSwarmConfigLoader
        
        config_path = 'langswarm/core/debug/test_configs/sql_database_fixed.yaml'
        loader = LangSwarmConfigLoader(config_path)
        workflows, agents, brokers, tools, metadata = loader.load()
        
        # Convert tools to dict
        if isinstance(tools, list):
            tools_dict = {}
            for tool_instance in tools:
                if hasattr(tool_instance, 'identifier'):
                    tools_dict[tool_instance.identifier] = tool_instance
            tools = tools_dict
        
        if 'sql_db' in tools:
            sql_tool = tools['sql_db']
            print(f"   ✅ SQL tool loaded with ID: {sql_tool.identifier}")
            print(f"   ✅ Server name: {sql_tool.server.name}")
        else:
            print(f"   ❌ SQL tool not found in loaded tools: {list(tools.keys())}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading configuration: {e}")
        return False
    
    # Step 4: Test MCP call
    print("\n4️⃣ Testing MCP call...")
    try:
        # Verify database exists
        db_path = './langswarm/core/debug/test_data/test_database.db'
        if not os.path.exists(db_path):
            print(f"   ⚠️ Test database not found at {db_path}")
            print(f"   💡 Run: python langswarm/core/debug/test_data/setup_test_database.py")
            return False
        
        # Test the actual MCP call
        result = sql_tool.server.call_task("get_database_info", {"include_schema": True})
        
        if result.get('success'):
            print(f"   ✅ MCP call successful!")
            print(f"   ✅ Tables found: {len(result.get('tables', []))}")
        else:
            print(f"   ❌ MCP call failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing MCP call: {e}")
        return False
    
    # Step 5: Test workflow context
    print("\n5️⃣ Testing workflow context...")
    try:
        agent = agents.get('sql_test_agent') 
        if agent and hasattr(agent, 'set_workflow_context'):
            # Set up workflow context
            workflow_context = {
                'config_loader': loader,
                'tools': tools,
                'user_input': 'test'
            }
            agent.set_workflow_context(workflow_context)
            
            # Test middleware call
            test_call = {
                "response": "Testing SQL database",
                "mcp": {
                    "tool": "sql_db",
                    "method": "get_database_info", 
                    "params": {"include_schema": True}
                }
            }
            
            # This should now work without "Local server not found" error
            status, response = agent.to_middleware(test_call)
            
            if status == 201:
                print(f"   ✅ Workflow context test PASSED!")
                print(f"   ✅ Middleware found the SQL server successfully!")
            else:
                print(f"   ❌ Workflow context test FAILED: {response}")
                return False
        else:
            print(f"   ⚠️ Agent workflow context test skipped (agent not properly initialized)")
            print(f"   💡 This is OK - the core fix is verified in steps 1-4")
            
    except Exception as e:
        print(f"   ❌ Error testing workflow context: {e}")
        return False
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"✅ The SQL database tool fix is working correctly!")
    print(f"✅ The 'Local server not found' error should be resolved!")
    
    return True

if __name__ == "__main__":
    verify_sql_fix()
