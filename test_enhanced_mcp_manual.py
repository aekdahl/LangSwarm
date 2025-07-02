#!/usr/bin/env python3
"""
Manual Testing Script for Enhanced MCP Patterns

This script allows developers to test the enhanced MCP patterns without
requiring external services like OpenAI API or real MCP tools.

Run with: python test_enhanced_mcp_manual.py
"""

import os
import sys
import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langswarm.core.wrappers.middleware import MiddlewareMixin


class MockMCPTool:
    """Mock MCP tool for testing"""
    def __init__(self, tool_id, tool_type, local_mode=False, pattern="direct"):
        self.id = tool_id
        self.type = tool_type
        self.local_mode = local_mode
        self.pattern = pattern
        self.mcp_url = None if local_mode else f"stdio://{tool_id}"


class MockToolRegistry:
    def __init__(self):
        self.tools = {}
        
    def get_tool(self, tool_id):
        return self.tools.get(tool_id)
        
    def register_tool(self, tool_id, tool):
        self.tools[tool_id] = tool


def test_basic_functionality():
    """Test basic enhanced MCP functionality"""
    print("🧪 Testing Enhanced MCP Patterns")
    print("=" * 50)
    
    tool_registry = MockToolRegistry()
    tool_registry.register_tool("filesystem", MockMCPTool(
        "filesystem", "mcpfilesystem", local_mode=True, pattern="direct"
    ))
    
    middleware = MiddlewareMixin(
        tool_registry=tool_registry,
        rag_registry=Mock(),
        plugin_registry=Mock()
    )
    
    middleware.name = "test-agent"
    middleware.timeout = 5
    middleware.log_event = lambda *args, **kwargs: print(f"[LOG] {args[0]}")
    
    # Test direct pattern
    agent_input = {
        "mcp": {
            "tool": "filesystem",
            "method": "read_file",
            "params": {"path": "/tmp/test.txt"}
        }
    }
    
    with patch('langswarm.core.utils.workflows.functions.mcp_call') as mock_call:
        mock_call.return_value = {"content": "test content"}
        
        status, result = middleware.to_middleware(agent_input)
        
        print(f"✅ Status: {status}")
        print(f"✅ Result: {result}")
        
        if mock_call.called:
            call_args = mock_call.call_args
            mcp_url = call_args[1]["mcp_url"]
            print(f"✅ MCP URL: {mcp_url}")
            return status == 201
    
    return False


if __name__ == "__main__":
    print("🚀 Enhanced MCP Patterns - Basic Test")
    success = test_basic_functionality()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
