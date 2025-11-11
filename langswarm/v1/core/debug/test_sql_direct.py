#!/usr/bin/env python3
"""
Direct SQL Database MCP Tool Test
=================================

Test the SQL Database MCP tool directly without agents.
"""

import sys
import os
sys.path.insert(0, '.')

from langswarm.v1.core.config import LangSwarmConfigLoader

def test_sql_database_direct():
    """Test the SQL Database tool directly"""
    
    print("🔄 Testing SQL Database MCP Tool directly...")
    
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
            tools = tools_dict
        
        # Get the SQL database tool
        sql_tool = tools.get('sql_db')
        if not sql_tool:
            print("❌ Could not find sql_db tool")
            return False
            
        print(f"✅ SQL tool loaded: {sql_tool.identifier}")
        
        # Test database info
        print(f"\n📋 Test 1: Get Database Info")
        try:
            if hasattr(sql_tool, 'server') and sql_tool.server:
                result = sql_tool.server.call_task("get_database_info", {"include_schema": True})
                if result.get('success'):
                    print(f"   ✅ Database info retrieved")
                    print(f"   📊 Tables found: {len(result.get('tables', []))}")
                    for table in result.get('tables', [])[:3]:  # Show first 3 tables
                        print(f"      - {table.get('name', 'Unknown')}: {table.get('row_count', 0)} rows")
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            else:
                print("   ❌ Tool server not available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test simple query
        print(f"\n📋 Test 2: Simple Query")
        try:
            if hasattr(sql_tool, 'server') and sql_tool.server:
                query = "SELECT name, email, department FROM users WHERE active = 1 LIMIT 5"
                result = sql_tool.server.call_task("execute_query", {"query": query})
                if result.get('success'):
                    print(f"   ✅ Query executed successfully")
                    print(f"   📊 Rows returned: {result.get('row_count', 0)}")
                    print(f"   📋 Columns: {', '.join(result.get('columns', []))}")
                    print(f"   ⏱️ Execution time: {result.get('execution_time_ms', 0):.2f}ms")
                else:
                    print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
            else:
                print("   ❌ Tool server not available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test query with limit
        print(f"\n📋 Test 3: Query with Views")
        try:
            if hasattr(sql_tool, 'server') and sql_tool.server:
                query = "SELECT * FROM order_summary"
                result = sql_tool.server.call_task("execute_query", {"query": query})
                if result.get('success'):
                    print(f"   ✅ View query executed successfully")
                    print(f"   📊 Departments found: {result.get('row_count', 0)}")
                    # Show some sample data
                    if result.get('results') and len(result['results']) > 0:
                        first_row = result['results'][0]
                        print(f"   📋 Sample: {first_row}")
                else:
                    print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
            else:
                print("   ❌ Tool server not available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print(f"\n🎉 SQL Database direct testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sql_database_direct()
