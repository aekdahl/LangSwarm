import pytest
import os
import tempfile
import yaml
from pathlib import Path
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
from langswarm.core.wrappers.generic import AgentWrapper


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with test configuration files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        
        # Create tools.yaml
        tools_config = {
            "tools": [
                {
                    "id": "test_filesystem",
                    "type": "mcpfilesystem",
                    "description": "Test filesystem tool",
                    "local_mode": True,
                    "pattern": "direct",
                    "methods": [
                        {"read_file": "Read file contents"},
                        {"list_directory": "List directory contents"}
                    ]
                },
                {
                    "id": "test_analytics",
                    "type": "mcpanalytics", 
                    "description": "Test analytics tool",
                    "local_mode": True,
                    "pattern": "intent",
                    "main_workflow": "analytics_workflow"
                }
            ]
        }
        
        with open(config_dir / "tools.yaml", "w") as f:
            yaml.dump(tools_config, f)
        
        # Create agents.yaml
        agents_config = {
            "agents": [
                {
                    "id": "test_direct_agent",
                    "agent_type": "openai",
                    "model": "gpt-4o-mini",
                    "system_prompt": """You are a test agent that uses direct MCP patterns.
                    Available tools:
                    - test_filesystem: File operations
                      Methods: read_file(path), list_directory(path)
                    
                    Return JSON format:
                    {"mcp": {"tool": "test_filesystem", "method": "read_file", "params": {"path": "/tmp/file"}}}
                    """
                },
                {
                    "id": "test_intent_agent",
                    "agent_type": "openai", 
                    "model": "gpt-4o",
                    "system_prompt": """You are a test agent that uses intent-based MCP patterns.
                    Available tools:
                    - test_analytics: Data analysis (describe your analysis needs)
                    
                    Return JSON format:
                    {"mcp": {"tool": "test_analytics", "intent": "analyze data", "context": "details"}}
                    """
                }
            ]
        }
        
        with open(config_dir / "agents.yaml", "w") as f:
            yaml.dump(agents_config, f)
            
        # Create workflows.yaml
        workflows_config = {
            "workflows": {
                "direct_test_workflow": [
                    {
                        "id": "direct_pattern_test",
                        "steps": [
                            {
                                "id": "direct_call",
                                "agent": "test_direct_agent",
                                "input": "${context.user_input}",
                                "output": {"to": "user"}
                            }
                        ]
                    }
                ],
                "intent_test_workflow": [
                    {
                        "id": "intent_pattern_test",
                        "steps": [
                            {
                                "id": "intent_call",
                                "agent": "test_intent_agent", 
                                "input": "${context.user_input}",
                                "output": {"to": "user"}
                            }
                        ]
                    }
                ]
            }
        }
        
        with open(config_dir / "workflows.yaml", "w") as f:
            yaml.dump(workflows_config, f)
            
        yield config_dir


class TestEnhancedMCPIntegration:
    """Integration tests for enhanced MCP patterns"""
    
    def test_config_loading_with_enhanced_patterns(self, temp_config_dir):
        """Test that enhanced pattern configurations load correctly"""
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Verify tools were loaded with enhanced pattern attributes
        assert len(tools) == 2
        
        # Check filesystem tool (direct pattern)
        filesystem_tool = next((t for t in tools if t.id == "test_filesystem"), None)
        assert filesystem_tool is not None
        assert filesystem_tool.type == "mcpfilesystem"
        assert getattr(filesystem_tool, 'local_mode', False) is True
        assert getattr(filesystem_tool, 'pattern', None) == "direct"
        
        # Check analytics tool (intent pattern)
        analytics_tool = next((t for t in tools if t.id == "test_analytics"), None)
        assert analytics_tool is not None
        assert analytics_tool.type == "mcpanalytics"
        assert getattr(analytics_tool, 'local_mode', False) is True
        assert getattr(analytics_tool, 'pattern', None) == "intent"
        
        # Verify agents were loaded
        assert len(agents) >= 2
        agent_ids = [agent.id for agent in agents]
        assert "test_direct_agent" in agent_ids
        assert "test_intent_agent" in agent_ids
        
        # Verify workflows were loaded
        assert "direct_test_workflow" in workflows
        assert "intent_test_workflow" in workflows
    
    @pytest.mark.skip(reason="Requires actual MCP tools and OpenAI API")
    def test_end_to_end_direct_pattern(self, temp_config_dir):
        """End-to-end test of direct pattern (requires real tools)"""
        # This test would require actual MCP filesystem tool and OpenAI API
        # Skipped in CI but useful for manual testing
        
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        executor = WorkflowExecutor(workflows, agents)
        
        # Test direct pattern
        result = executor.run_workflow(
            "direct_test_workflow",
            "Read the file /tmp/test.txt using the filesystem tool"
        )
        
        # Would verify that the result contains file content
        assert result is not None
    
    @pytest.mark.skip(reason="Requires actual MCP tools and OpenAI API")
    def test_end_to_end_intent_pattern(self, temp_config_dir):
        """End-to-end test of intent pattern (requires real tools)"""
        # This test would require actual MCP analytics tool and OpenAI API
        # Skipped in CI but useful for manual testing
        
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        executor = WorkflowExecutor(workflows, agents)
        
        # Test intent pattern
        result = executor.run_workflow(
            "intent_test_workflow", 
            "Analyze sales data for trends and patterns"
        )
        
        # Would verify that the result contains analysis
        assert result is not None
    
    def test_agent_wrapper_with_enhanced_patterns(self, temp_config_dir):
        """Test AgentWrapper with enhanced MCP patterns"""
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Create agent wrapper with middleware enabled
        agent = AgentWrapper(
            name="test_enhanced_agent",
            tools=tools,
            allow_middleware=True
        )
        
        # Verify middleware is properly configured
        assert hasattr(agent, 'to_middleware')
        assert agent.__allow_middleware is True
        
        # Verify tool registry is populated
        tool_registry = agent.tool_registry
        assert hasattr(tool_registry, 'get_tool')
        
        # Test that tools can be retrieved
        filesystem_tool = tool_registry.get_tool("test_filesystem")
        assert filesystem_tool is not None
        assert filesystem_tool.id == "test_filesystem"


class TestConfigurationValidation:
    """Test configuration validation for enhanced patterns"""
    
    def test_invalid_pattern_configuration(self, temp_config_dir):
        """Test validation of invalid pattern configurations"""
        # Create invalid configuration
        invalid_tools_config = {
            "tools": [
                {
                    "id": "invalid_tool",
                    "type": "mcpinvalid",
                    "description": "Invalid tool configuration",
                    # Missing both local_mode and mcp_url
                    "pattern": "direct"
                }
            ]
        }
        
        with open(temp_config_dir / "tools_invalid.yaml", "w") as f:
            yaml.dump(invalid_tools_config, f)
        
        # Configuration should load but tool validation might fail during usage
        # This tests the robustness of the configuration system
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        # Should not raise exception during loading
        workflows, agents, brokers, tools, tools_metadata = loader.load()
    
    def test_mixed_local_remote_configuration(self, temp_config_dir):
        """Test configuration with mixed local and remote tools"""
        mixed_tools_config = {
            "tools": [
                {
                    "id": "local_tool",
                    "type": "mcplocal",
                    "description": "Local tool",
                    "local_mode": True,
                    "pattern": "direct"
                },
                {
                    "id": "remote_tool", 
                    "type": "mcpremote",
                    "description": "Remote tool",
                    "mcp_url": "stdio://remote_tool",
                    "pattern": "intent"
                }
            ]
        }
        
        with open(temp_config_dir / "tools_mixed.yaml", "w") as f:
            yaml.dump(mixed_tools_config, f)
        
        loader = LangSwarmConfigLoader(config_path=str(temp_config_dir))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Verify both tools loaded correctly
        local_tool = next((t for t in tools if t.id == "local_tool"), None)
        assert local_tool is not None
        assert getattr(local_tool, 'local_mode', False) is True
        
        remote_tool = next((t for t in tools if t.id == "remote_tool"), None)
        assert remote_tool is not None
        assert getattr(remote_tool, 'mcp_url', None) == "stdio://remote_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 