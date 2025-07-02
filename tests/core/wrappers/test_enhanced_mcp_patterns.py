import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langswarm.core.wrappers.middleware import MiddlewareMixin


class MockMCPTool:
    """Mock MCP tool for testing enhanced patterns"""
    def __init__(self, tool_id, tool_type, local_mode=False, pattern="direct", main_workflow=None):
        self.id = tool_id
        self.type = tool_type
        self.local_mode = local_mode
        self.pattern = pattern
        self.main_workflow = main_workflow or "main_workflow"
        self.mcp_url = None if local_mode else f"stdio://{tool_id}"
        
    def run(self, payload):
        """Legacy compatibility method"""
        return {"result": f"Legacy run for {self.id}"}


class MockToolRegistry:
    """Mock tool registry for testing"""
    def __init__(self):
        self.tools = {}
        
    def get_tool(self, tool_id):
        return self.tools.get(tool_id)
        
    def register_tool(self, tool_id, tool):
        self.tools[tool_id] = tool


class MockRAGRegistry:
    def get_rag(self, name):
        return None


class MockPluginRegistry:
    def get_plugin(self, name):
        return None


@pytest.fixture
def enhanced_middleware():
    """Create middleware with enhanced MCP pattern support"""
    tool_registry = MockToolRegistry()
    rag_registry = MockRAGRegistry()
    plugin_registry = MockPluginRegistry()
    
    # Register test tools
    tool_registry.register_tool("filesystem", MockMCPTool(
        "filesystem", "mcpfilesystem", local_mode=True, pattern="direct"
    ))
    tool_registry.register_tool("github_mcp", MockMCPTool(
        "github_mcp", "mcpgithubtool", local_mode=False, pattern="intent"
    ))
    tool_registry.register_tool("local_analytics", MockMCPTool(
        "local_analytics", "mcpanalytics", local_mode=True, pattern="intent"
    ))
    
    middleware = MiddlewareMixin(
        tool_registry=tool_registry,
        rag_registry=rag_registry,
        plugin_registry=plugin_registry
    )
    
    # Mock required attributes
    middleware.name = "test-agent"
    middleware.timeout = 5
    middleware.log_event = Mock()
    
    return middleware


class TestEnhancedMCPPatterns:
    """Test suite for enhanced MCP patterns"""
    
    def test_direct_pattern_local_mode(self, enhanced_middleware):
        """Test direct pattern with local mode"""
        agent_input = {
            "mcp": {
                "tool": "filesystem",
                "method": "read_file",
                "params": {"path": "/tmp/test.txt"}
            }
        }
        
        # Mock the mcp_call function
        with patch('langswarm.core.utils.workflows.functions.mcp_call') as mock_mcp_call:
            mock_mcp_call.return_value = {"content": "file content", "path": "/tmp/test.txt"}
            
            status, result = enhanced_middleware.to_middleware(agent_input)
            
            assert status == 201
            result_data = json.loads(result)
            assert "content" in result_data
            
            # Verify local:// URL was used
            mock_mcp_call.assert_called_once()
            call_args = mock_mcp_call.call_args
            assert call_args[1]["mcp_url"] == "local://filesystem"
    
    def test_intent_based_pattern_local(self, enhanced_middleware):
        """Test intent-based pattern with local tool"""
        agent_input = {
            "mcp": {
                "tool": "local_analytics",
                "intent": "analyze sales trends for Q4",
                "context": "Focus on regional performance"
            }
        }
        
        # Mock the workflow execution
        with patch.object(enhanced_middleware, 'use_mcp_workflow') as mock_workflow:
            mock_workflow.return_value = {
                "analysis_type": "sales_trends",
                "insights": ["Regional growth in West"]
            }
            
            status, result = enhanced_middleware.to_middleware(agent_input)
            
            assert status == 201
            result_data = json.loads(result)
            assert "analysis_type" in result_data
            
            # Verify workflow was called with correct parameters
            mock_workflow.assert_called_once_with(
                tool_id="local_analytics",
                intent="analyze sales trends for Q4",
                context="Focus on regional performance"
            )
    
    def test_missing_tool_field(self, enhanced_middleware):
        """Test error handling when tool field is missing"""
        agent_input = {
            "mcp": {
                "method": "read_file",
                "params": {"path": "/tmp/test.txt"}
            }
        }
        
        status, result = enhanced_middleware.to_middleware(agent_input)
        
        assert status == 400
        assert "missing 'tool' field" in result
    
    def test_missing_intent_and_method(self, enhanced_middleware):
        """Test error handling when both intent and method are missing"""
        agent_input = {
            "mcp": {
                "tool": "filesystem",
                "params": {"path": "/tmp/test.txt"}
            }
        }
        
        status, result = enhanced_middleware.to_middleware(agent_input)
        
        assert status == 400
        assert "must have either 'intent' or 'method' field" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 