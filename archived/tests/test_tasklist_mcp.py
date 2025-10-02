#!/usr/bin/env python3
"""
Test script for the new Tasklist MCP Tool
"""

import sys
import os
sys.path.append('/Users/alexanderekdahl/Docker/LangSwarm')

from langswarm.mcp.tools.tasklist.main import TasklistMCPTool

def test_tasklist_mcp_tool():
    """Test the tasklist MCP tool functionality"""
    
    print("🧪 Testing Tasklist MCP Tool")
    print("=" * 50)
    
    # Initialize the tool
    tool = TasklistMCPTool(identifier="test_tasklist")
    print(f"✅ Tool initialized: {tool.name}")
    print(f"🏷️  Identifier: {tool.identifier}")
    print(f"🔧 Local mode: {getattr(tool, 'local_mode', True)}")
    print()
    
    # Test 1: Create a task
    print("📝 Test 1: Creating a task")
    result1 = tool.run({
        "method": "create_task",
        "params": {
            "description": "Write comprehensive tests for the tasklist tool",
            "priority": 1,
            "notes": "Include unit tests and integration tests"
        }
    })
    print(f"Result: {result1}")
    print()
    
    # Test 2: Create another task
    print("📝 Test 2: Creating another task")
    result2 = tool.run({
        "method": "create_task", 
        "params": {
            "description": "Update documentation with new MCP tool info",
            "priority": 2
        }
    })
    print(f"Result: {result2}")
    print()
    
    # Test 3: List all tasks
    print("📋 Test 3: Listing all tasks")
    result3 = tool.run({
        "method": "list_tasks",
        "params": {}
    })
    print(f"Result: {result3}")
    print()
    
    # Test 4: Update a task
    print("✏️  Test 4: Updating task-1")
    result4 = tool.run({
        "method": "update_task",
        "params": {
            "task_id": "task-1",
            "completed": True,
            "notes": "Tests completed successfully"
        }
    })
    print(f"Result: {result4}")
    print()
    
    # Test 5: Get specific task
    print("🔍 Test 5: Getting task details")
    result5 = tool.run({
        "method": "get_task",
        "params": {
            "task_id": "task-1"
        }
    })
    print(f"Result: {result5}")
    print()
    
    # Test 6: Delete a task
    print("🗑️  Test 6: Deleting task-2")
    result6 = tool.run({
        "method": "delete_task",
        "params": {
            "task_id": "task-2"
        }
    })
    print(f"Result: {result6}")
    print()
    
    # Test 7: List tasks after deletion
    print("📋 Test 7: Final task list")
    result7 = tool.run({
        "method": "list_tasks",
        "params": {}
    })
    print(f"Result: {result7}")
    print()
    
    # Test 8: Error handling - invalid task ID
    print("❌ Test 8: Error handling - invalid task ID")
    result8 = tool.run({
        "method": "get_task",
        "params": {
            "task_id": "task-999"
        }
    })
    print(f"Result: {result8}")
    print()
    
    # Test 9: Error handling - invalid method
    print("❌ Test 9: Error handling - invalid method")
    result9 = tool.run({
        "method": "invalid_method",
        "params": {}
    })
    print(f"Result: {result9}")
    print()
    
    print("🎯 All tests completed!")
    print("Check tasklist_data.json for persistence verification")

if __name__ == "__main__":
    test_tasklist_mcp_tool()