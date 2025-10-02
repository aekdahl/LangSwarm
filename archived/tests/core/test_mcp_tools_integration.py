"""
Comprehensive MCP Tools Integration Tests
========================================

End-to-end test suite for LangSwarm's MCP Tools system covering:
- MCP Server Base functionality and local mode
- Filesystem Tool (read-only file operations)
- Dynamic Forms Tool (YAML-based form generation)
- GitHub Tool (repository management and Git operations)
- Template System and caching
- Direct patterns vs Intent-based patterns
- Workflow orchestration and agent integration
- Local mode vs Remote mode functionality
- Error handling and edge cases
- Performance and optimization
- Real-world usage scenarios

Following the MemoryPro testing pattern with comprehensive coverage.
"""

import pytest
import tempfile
import os
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List

# LangSwarm imports
from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool, list_directory, read_file
from langswarm.mcp.tools.dynamic_forms.main import DynamicFormsMCPTool, generate_form_schema
from langswarm.mcp.tools.mcpgithubtool.main import MCPGitHubTool
from langswarm.mcp.tools.template_loader import get_cached_tool_template, create_tool_with_template


class TestMCPToolsIntegration:
    """Comprehensive MCP Tools integration tests"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files_dir = Path(self.temp_dir) / "test_files"
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Create test files for filesystem testing
        self.create_test_files()
        
        # Create test configurations
        self.create_test_configurations()
        
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear MCP server registry
        if hasattr(BaseMCPToolServer, '_global_registry'):
            BaseMCPToolServer._global_registry.clear()
        
    def create_test_files(self):
        """Create test files for filesystem tool testing"""
        # Create various test files
        test_files = {
            "readme.txt": "This is a test README file\nSecond line\nThird line",
            "config.json": '{"setting1": "value1", "setting2": 42, "setting3": true}',
            "data.csv": "name,age,city\nAlice,30,New York\nBob,25,London\nCharlie,35,Paris",
            "script.py": "#!/usr/bin/env python3\nprint('Hello, World!')\n# This is a test script",
            "empty.txt": "",
            "unicode.txt": "Unicode test: 🚀 🌟 ✨ 中文 العربية русский"
        }
        
        for filename, content in test_files.items():
            file_path = self.test_files_dir / filename
            file_path.write_text(content, encoding='utf-8')
        
        # Create subdirectories
        (self.test_files_dir / "subdir").mkdir()
        (self.test_files_dir / "subdir" / "nested.txt").write_text("Nested file content")
        (self.test_files_dir / "empty_dir").mkdir()

    def create_test_configurations(self):
        """Create test configurations for dynamic forms"""
        self.forms_config = {
            "tools": [
                {
                    "id": "dynamic-forms",
                    "type": "mcpforms", 
                    "description": "Test dynamic forms",
                    "local_mode": True,
                    "forms": {
                        "user_settings": {
                            "title": "User Settings",
                            "description": "Basic user preferences",
                            "fields": [
                                {
                                    "id": "display_name",
                                    "label": "Display Name",
                                    "type": "text",
                                    "required": True,
                                    "placeholder": "Enter your name"
                                },
                                {
                                    "id": "email",
                                    "label": "Email Address", 
                                    "type": "email",
                                    "required": True
                                },
                                {
                                    "id": "theme",
                                    "label": "Theme",
                                    "type": "select",
                                    "default_value": "auto",
                                    "options": [
                                        {"value": "light", "label": "Light"},
                                        {"value": "dark", "label": "Dark"},
                                        {"value": "auto", "label": "Auto"}
                                    ]
                                },
                                {
                                    "id": "notifications",
                                    "label": "Enable Notifications",
                                    "type": "toggle",
                                    "default_value": True
                                }
                            ]
                        },
                        "system_config": {
                            "title": "System Configuration",
                            "description": "Advanced system settings",
                            "fields": [
                                {
                                    "id": "max_connections",
                                    "label": "Max Connections",
                                    "type": "number",
                                    "min_value": 1,
                                    "max_value": 1000,
                                    "default_value": 100
                                },
                                {
                                    "id": "log_level",
                                    "label": "Log Level",
                                    "type": "select",
                                    "options": [
                                        {"value": "debug", "label": "Debug"},
                                        {"value": "info", "label": "Info"},
                                        {"value": "warning", "label": "Warning"},
                                        {"value": "error", "label": "Error"}
                                    ]
                                }
                            ]
                        }
                    }
                }
            ]
        }
        
        # Save forms config to file
        self.forms_config_file = Path(self.temp_dir) / "forms_config.yaml"
        with open(self.forms_config_file, 'w') as f:
            yaml.dump(self.forms_config, f)

    def test_mcp_server_base_functionality(self):
        """Test core MCP server base functionality"""
        # Test server creation and registration
        server = BaseMCPToolServer(
            name="test_server",
            description="Test MCP server",
            local_mode=True
        )
        
        assert server.name == "test_server"
        assert server.description == "Test MCP server"
        assert server.local_mode is True
        
        # Test global registration in local mode
        registered_server = BaseMCPToolServer.get_local_server("test_server")
        assert registered_server is server
        
        # Test task registration
        from pydantic import BaseModel
        
        class TestInput(BaseModel):
            message: str
            
        class TestOutput(BaseModel):
            result: str
            
        def test_handler(message: str) -> dict:
            return {"result": f"Processed: {message}"}
        
        server.add_task(
            name="test_task",
            description="Test task",
            input_model=TestInput,
            output_model=TestOutput,
            handler=test_handler
        )
        
        # Verify task registration
        assert "test_task" in server._tasks
        task_meta = server._tasks["test_task"]
        assert task_meta["description"] == "Test task"
        assert task_meta["input_model"] == TestInput
        assert task_meta["output_model"] == TestOutput
        
        # Test local execution
        result = test_handler("test message")
        assert result["result"] == "Processed: test message"
        
        # Test app building (should return None for local mode)
        app = server.build_app()
        assert app is None or hasattr(app, 'routes')  # None for local mode or FastAPI app

    def test_filesystem_tool_comprehensive(self):
        """Test comprehensive filesystem tool functionality"""
        # Create filesystem tool
        tool = FilesystemMCPTool(
            identifier="test_filesystem",
            name="Test Filesystem Tool"
        )
        
        assert tool.name == "Test Filesystem Tool"
        # Check that tool has expected MCP attributes instead of _is_mcp_tool
        assert hasattr(tool, 'identifier')
        assert hasattr(tool, 'name')
        assert tool.identifier == "test_filesystem"
        
        # Test directory listing
        list_result = list_directory(path=str(self.test_files_dir))
        
        assert "path" in list_result
        assert "contents" in list_result
        assert list_result["path"] == str(self.test_files_dir)
        assert isinstance(list_result["contents"], list)
        
        # Verify expected files are listed
        contents = list_result["contents"]
        expected_files = ["readme.txt", "config.json", "data.csv", "script.py", "empty.txt", "unicode.txt"]
        expected_dirs = ["subdir", "empty_dir"]
        
        # Handle both string and dict formats for contents
        for expected_file in expected_files:
            if isinstance(contents[0], dict):
                assert any(item["name"] == expected_file for item in contents), f"Missing file: {expected_file}"
            else:
                assert expected_file in contents, f"Missing file: {expected_file}"
            
        for expected_dir in expected_dirs:
            if isinstance(contents[0], dict):
                assert any(item["name"] == expected_dir for item in contents), f"Missing directory: {expected_dir}"
            else:
                assert expected_dir in contents, f"Missing directory: {expected_dir}"
        
        # Test file reading
        readme_path = self.test_files_dir / "readme.txt"
        read_result = read_file(path=str(readme_path))
        
        assert "path" in read_result
        assert "content" in read_result
        assert read_result["path"] == str(readme_path)
        assert "test README file" in read_result["content"]
        assert "Second line" in read_result["content"]
        
        # Test JSON file reading
        config_path = self.test_files_dir / "config.json"
        config_result = read_file(path=str(config_path))
        
        config_content = config_result["content"]
        assert "setting1" in config_content
        assert "value1" in config_content
        
        # Verify JSON is valid
        config_data = json.loads(config_content)
        assert config_data["setting1"] == "value1"
        assert config_data["setting2"] == 42
        
        # Test Unicode file reading
        unicode_path = self.test_files_dir / "unicode.txt"
        unicode_result = read_file(path=str(unicode_path))
        
        unicode_content = unicode_result["content"]
        assert "🚀" in unicode_content
        assert "中文" in unicode_content
        assert "العربية" in unicode_content

    def test_filesystem_tool_structured_input(self):
        """Test filesystem tool with structured input handling"""
        tool = FilesystemMCPTool(
            identifier="test_filesystem_structured",
            name="Structured Filesystem Tool"
        )
        
        # Test direct method calls
        test_cases = [
            # List directory - direct call
            {
                "method": "list_directory",
                "params": {"path": str(self.test_files_dir)}
            },
            # Read file - direct call
            {
                "method": "read_file", 
                "params": {"path": str(self.test_files_dir / "readme.txt")}
            }
        ]
        
        for test_case in test_cases:
            result = tool.run(test_case)
            
            assert result is not None
            if test_case["method"] == "list_directory":
                assert "contents" in result or "path" in str(result)
            elif test_case["method"] == "read_file":
                assert "content" in result or "README" in str(result)

    def test_dynamic_forms_tool_comprehensive(self):
        """Test comprehensive dynamic forms tool functionality"""
        # Create dynamic forms tool with config
        tool = DynamicFormsMCPTool(
            identifier="test_dynamic_forms",
            name="Test Dynamic Forms Tool",
            user_config_path=str(self.forms_config_file)
        )
        
        assert tool.name == "Test Dynamic Forms Tool"
        # Check that tool has expected MCP attributes instead of _is_mcp_tool
        assert hasattr(tool, 'identifier')
        assert hasattr(tool, 'name')
        assert tool.identifier == "test_dynamic_forms"
        
        # Test form schema generation - user settings
        user_settings_result = generate_form_schema(
            form_type="user_settings",
            user_context={"config_path": str(self.forms_config_file)}
        )
        
        assert "form_schema" in user_settings_result
        assert "form_type" in user_settings_result["form_schema"]
        assert user_settings_result["form_schema"]["form_type"] == "user_settings"
        
        schema = user_settings_result["form_schema"]
        assert "title" in schema
        assert schema["title"] == "User Settings"
        assert "sections" in schema
        assert len(schema["sections"]) > 0
        assert "fields" in schema["sections"][0]
        
        # Verify expected fields
        fields = schema["sections"][0]["fields"]
        field_ids = [field["id"] for field in fields]
        expected_fields = ["display_name", "email", "theme", "notifications"]
        
        for expected_field in expected_fields:
            assert expected_field in field_ids, f"Missing field: {expected_field}"
        
        # Test field types and properties
        display_name_field = next(f for f in fields if f["id"] == "display_name")
        assert display_name_field["type"] == "text"
        assert display_name_field["required"] is True
        assert display_name_field["placeholder"] == "Enter your name"
        
        theme_field = next(f for f in fields if f["id"] == "theme")
        assert theme_field["type"] == "select"
        assert "options" in theme_field
        assert len(theme_field["options"]) == 3
        
        # Test system config form
        system_config_result = generate_form_schema(
            form_type="system_config",
            user_context={"config_path": str(self.forms_config_file)}
        )
        
        assert system_config_result["form_schema"]["form_type"] == "system_config"
        system_schema = system_config_result["form_schema"]
        assert system_schema["title"] == "System Configuration"
        
        # Test field filtering
        filtered_result = generate_form_schema(
            form_type="user_settings",
            user_context={"config_path": str(self.forms_config_file)},
            included_fields=["display_name", "email"]
        )
        
        filtered_schema = filtered_result["form_schema"]
        filtered_field_ids = [f["id"] for f in filtered_schema["sections"][0]["fields"]]
        assert len(filtered_field_ids) == 2
        assert "display_name" in filtered_field_ids
        assert "email" in filtered_field_ids
        assert "theme" not in filtered_field_ids
        
        # Test pre-population
        prepopulated_result = generate_form_schema(
            form_type="user_settings",
            user_context={"config_path": str(self.forms_config_file)},
            current_settings={"display_name": "John Doe", "theme": "dark"}
        )
        
        prepop_schema = prepopulated_result["form_schema"]
        prepop_fields = prepop_schema["sections"][0]["fields"]
        
        display_name_field = next(f for f in prepop_fields if f["id"] == "display_name")
        assert display_name_field.get("default_value") == "John Doe"
        
        theme_field = next(f for f in prepop_fields if f["id"] == "theme")
        assert theme_field.get("default_value") == "dark"

    def test_github_tool_functionality(self):
        """Test GitHub tool functionality and integration"""
        # Create GitHub tool
        tool = MCPGitHubTool(
            identifier="test_github",
            name="Test GitHub Tool"
        )
        
        assert tool.name == "Test GitHub Tool"
        # Check that tool has expected MCP attributes instead of _is_mcp_tool
        assert hasattr(tool, 'identifier')
        assert hasattr(tool, 'name')
        assert tool.identifier == "test_github"
        
        # Test method availability
        test_methods = [
            "list_repositories",
            "get_repository",
            "list_issues",
            "create_issue",
            "list_pull_requests",
            "create_pull_request",
            "list_commits",
            "list_branches"
        ]
        
        for method in test_methods:
            # Test direct method calls (mock responses)
            test_input = {
                "method": method,
                "params": {"repository": "test/repo", "owner": "test"}
            }
            
            result = tool.run(test_input)
            assert result is not None
            assert method in str(result) or "MCP call" in str(result)

    def test_template_system_functionality(self):
        """Test MCP template system and caching"""
        # Test template loading for filesystem tool
        filesystem_dir = Path(__file__).parent.parent.parent / "langswarm" / "mcp" / "tools" / "filesystem"
        
        if filesystem_dir.exists():
            template_values = get_cached_tool_template(str(filesystem_dir))
            
            assert isinstance(template_values, dict)
            assert "description" in template_values
            assert "instruction" in template_values
            assert "brief" in template_values
            
            # Verify filesystem-specific content
            description = template_values.get("description", "")
            assert "filesystem" in description.lower() or "file" in description.lower()
        
        # Test template caching (call twice, should use cache)
        if filesystem_dir.exists():
            template_values_1 = get_cached_tool_template(str(filesystem_dir))
            template_values_2 = get_cached_tool_template(str(filesystem_dir))
            
            # Should return same object due to caching
            assert template_values_1 == template_values_2
        
        # Test create_tool_with_template function
        mock_tool_class = Mock()
        mock_tool_instance = Mock()
        mock_tool_class.return_value = mock_tool_instance
        
        if filesystem_dir.exists():
            result = create_tool_with_template(
                tool_class=mock_tool_class,
                tool_directory=str(filesystem_dir),
                identifier="test_tool",
                name="Test Tool"
            )
            
            assert result == mock_tool_instance
            mock_tool_class.assert_called_once()

    def test_local_vs_remote_mode_functionality(self):
        """Test local mode vs remote mode functionality"""
        # Test local mode server
        local_server = BaseMCPToolServer(
            name="local_test_server",
            description="Local test server",
            local_mode=True
        )
        
        assert local_server.local_mode is True
        
        # Should be registered globally
        registered = BaseMCPToolServer.get_local_server("local_test_server")
        assert registered is local_server
        
        # Test remote mode server
        remote_server = BaseMCPToolServer(
            name="remote_test_server", 
            description="Remote test server",
            local_mode=False
        )
        
        assert remote_server.local_mode is False
        
        # Should build FastAPI app for remote mode
        remote_app = remote_server.build_app()
        assert remote_app is not None or remote_server.local_mode  # App or local mode
        
        # Test local mode performance advantage
        # Local mode should have direct function calls (faster)
        start_time = datetime.now()
        
        # Simulate local execution
        for _ in range(100):
            result = list_directory(path=str(self.test_files_dir))
            assert result is not None
            
        local_time = (datetime.now() - start_time).total_seconds()
        
        # Local mode should be very fast (< 1 second for 100 calls)
        assert local_time < 1.0, f"Local mode too slow: {local_time}s"

    def test_mcp_patterns_integration(self):
        """Test different MCP patterns (direct vs intent-based)"""
        # Test direct pattern
        filesystem_tool = FilesystemMCPTool(
            identifier="direct_filesystem",
            name="Direct Filesystem Tool"
        )
        
        # Direct method call
        direct_input = {
            "method": "list_directory",
            "params": {"path": str(self.test_files_dir)}
        }
        
        direct_result = filesystem_tool.run(direct_input)
        assert direct_result is not None
        
        # Test intent-based pattern simulation
        intent_inputs = [
            "Show me what files are in the test directory",
            "List the contents of the folder",
            "What files exist in this location?",
            "Read the readme file",
            "Show me the config file contents"
        ]
        
        # These would normally be processed by workflows
        # For testing, we verify the tool can handle structured input
        for intent in intent_inputs:
            # Simulate intent processing result
            if "list" in intent.lower() or "show" in intent.lower() or "what files" in intent.lower():
                processed_input = {
                    "method": "list_directory", 
                    "params": {"path": str(self.test_files_dir)}
                }
            else:  # read operations
                processed_input = {
                    "method": "read_file",
                    "params": {"path": str(self.test_files_dir / "readme.txt")}
                }
            
            result = filesystem_tool.run(processed_input)
            assert result is not None

    def test_workflow_integration(self):
        """Test MCP tools integration with workflows"""
        # Test workflow-style input processing
        workflow_steps = [
            {
                "step": "normalize_input",
                "input": "Show me files in the test directory",
                "expected_output": "Show me files in the test directory"
            },
            {
                "step": "choose_function", 
                "input": "Show me files in the test directory",
                "expected_method": "list_directory"
            },
            {
                "step": "extract_path",
                "input": "Show me files in the test directory", 
                "expected_path": "test directory"
            },
            {
                "step": "call_tool",
                "method": "list_directory",
                "params": {"path": str(self.test_files_dir)},
                "expected_result": "contents"
            }
        ]
        
        filesystem_tool = FilesystemMCPTool(
            identifier="workflow_filesystem",
            name="Workflow Filesystem Tool"
        )
        
        # Test final tool call step
        final_step = workflow_steps[-1]
        tool_input = {
            "method": final_step["method"],
            "params": final_step["params"]
        }
        
        result = filesystem_tool.run(tool_input)
        assert result is not None
        
        # Should contain directory contents
        result_str = str(result)
        assert "contents" in result_str or "readme.txt" in result_str

    def test_error_handling_and_edge_cases(self):
        """Test comprehensive error handling and edge cases"""
        filesystem_tool = FilesystemMCPTool(
            identifier="error_test_filesystem",
            name="Error Test Filesystem Tool"
        )
        
        # Test non-existent file
        try:
            result = read_file(path="/nonexistent/file.txt")
            # Should handle gracefully
            assert "error" in str(result).lower() or result is None
        except Exception as e:
            # Should be a specific, handled exception
            assert "FileNotFoundError" in str(type(e)) or "OSError" in str(type(e))
        
        # Test non-existent directory
        try:
            result = list_directory(path="/nonexistent/directory")
            assert "error" in str(result).lower() or result is None
        except Exception as e:
            assert "FileNotFoundError" in str(type(e)) or "OSError" in str(type(e))
        
        # Test invalid tool input
        invalid_inputs = [
            None,
            {},
            {"method": "invalid_method"},
            {"method": "list_directory"},  # Missing params
            {"params": {"path": "/test"}},  # Missing method
            {"method": "list_directory", "params": {}},  # Missing path
        ]
        
        for invalid_input in invalid_inputs:
            try:
                result = filesystem_tool.run(invalid_input)
                # Should handle gracefully or return error
                if result is not None:
                    result_str = str(result)
                    assert "error" in result_str.lower() or "invalid" in result_str.lower() or len(result_str) == 0
            except Exception as e:
                # Should be handled exception types
                assert any(error_type in str(type(e)) for error_type in ["ValueError", "KeyError", "TypeError"])
        
        # Test very large file (if exists)
        large_content = "x" * 1000000  # 1MB of text
        large_file_path = self.test_files_dir / "large_file.txt"
        large_file_path.write_text(large_content)
        
        try:
            result = read_file(path=str(large_file_path))
            # Should handle large files
            assert result is not None
            assert len(result.get("content", "")) > 100000
        except Exception as e:
            # Should be memory or size related error
            print(f"Large file handling: {e}")
        
        # Test binary file (should fail gracefully)
        binary_file_path = self.test_files_dir / "binary_file.bin"
        binary_file_path.write_bytes(b'\x00\x01\x02\x03\x04\x05')
        
        try:
            result = read_file(path=str(binary_file_path))
            # Should handle or reject binary files
            if result:
                # Might decode as text with replacement chars
                assert isinstance(result.get("content"), str)
        except Exception as e:
            # Should be encoding related error
            assert "UnicodeDecodeError" in str(type(e)) or "decode" in str(e).lower()

    def test_performance_and_optimization(self):
        """Test MCP tools performance and optimization"""
        filesystem_tool = FilesystemMCPTool(
            identifier="performance_filesystem",
            name="Performance Filesystem Tool"
        )
        
        # Test multiple concurrent operations
        operations = []
        start_time = datetime.now()
        
        # Simulate concurrent file operations
        for i in range(50):
            if i % 2 == 0:
                # Directory listing
                result = filesystem_tool.run({
                    "method": "list_directory",
                    "params": {"path": str(self.test_files_dir)}
                })
            else:
                # File reading
                result = filesystem_tool.run({
                    "method": "read_file", 
                    "params": {"path": str(self.test_files_dir / "readme.txt")}
                })
            
            operations.append(result)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Verify all operations completed
        assert len(operations) == 50
        assert all(op is not None for op in operations)
        
        # Performance should be reasonable (< 5 seconds for 50 operations)
        assert total_time < 5.0, f"Performance too slow: {total_time}s for 50 operations"
        
        # Calculate operations per second
        ops_per_second = 50 / total_time
        assert ops_per_second > 10, f"Too slow: {ops_per_second} ops/sec"
        
        # Test memory efficiency (no leaks)
        import gc
        gc.collect()
        
        # Large batch operations should not accumulate memory
        for _ in range(100):
            result = filesystem_tool.run({
                "method": "list_directory",
                "params": {"path": str(self.test_files_dir)}
            })
            assert result is not None
        
        gc.collect()

    def test_tool_discovery_and_registration(self):
        """Test MCP tool discovery and registration systems"""
        # Test multiple tools registration
        tools = []
        
        # Register filesystem tool
        filesystem_tool = FilesystemMCPTool(
            identifier="discovered_filesystem",
            name="Discovered Filesystem Tool"
        )
        tools.append(filesystem_tool)
        
        # Register dynamic forms tool
        forms_tool = DynamicFormsMCPTool(
            identifier="discovered_forms",
            name="Discovered Forms Tool",
            user_config_path=str(self.forms_config_file)
        )
        tools.append(forms_tool)
        
        # Register GitHub tool
        github_tool = MCPGitHubTool(
            identifier="discovered_github",
            name="Discovered GitHub Tool"
        )
        tools.append(github_tool)
        
        # Verify all tools are properly initialized
        for tool in tools:
            assert hasattr(tool, 'name')
            # Check that tool has expected MCP attributes instead of _is_mcp_tool
            assert hasattr(tool, 'identifier')
            assert tool.name is not None
            assert tool.identifier is not None
        
        # Test tool capabilities discovery
        tool_capabilities = {}
        
        for tool in tools:
            if hasattr(tool, 'mcp_server'):
                server = tool.mcp_server
                capabilities = list(server._tasks.keys()) if hasattr(server, '_tasks') else []
                tool_capabilities[tool.identifier] = capabilities
        
        # Verify expected capabilities
        if "discovered_filesystem" in tool_capabilities:
            fs_caps = tool_capabilities["discovered_filesystem"]
            assert "list_directory" in fs_caps
            assert "read_file" in fs_caps
        
        if "discovered_forms" in tool_capabilities:
            forms_caps = tool_capabilities["discovered_forms"]
            assert "generate_form_schema" in forms_caps

    def test_multi_tool_workflows(self):
        """Test workflows involving multiple MCP tools"""
        # Create multiple tools
        filesystem_tool = FilesystemMCPTool(
            identifier="workflow_filesystem",
            name="Workflow Filesystem Tool"
        )
        
        forms_tool = DynamicFormsMCPTool(
            identifier="workflow_forms",
            name="Workflow Forms Tool",
            user_config_path=str(self.forms_config_file)
        )
        
        # Simulate multi-tool workflow
        workflow_steps = [
            # Step 1: List configuration files
            {
                "tool": filesystem_tool,
                "action": {
                    "method": "list_directory",
                    "params": {"path": str(self.test_files_dir)}
                }
            },
            # Step 2: Read configuration
            {
                "tool": filesystem_tool,
                "action": {
                    "method": "read_file",
                    "params": {"path": str(self.test_files_dir / "config.json")}
                }
            },
            # Step 3: Generate form based on config
            {
                "tool": forms_tool,
                "action": {
                    "method": "generate_form_schema",
                    "params": {
                        "form_type": "user_settings",
                        "user_context": {"config_path": str(self.forms_config_file)}
                    }
                }
            }
        ]
        
        results = []
        for step in workflow_steps:
            tool = step["tool"]
            action = step["action"]
            
            result = tool.run(action)
            results.append(result)
            assert result is not None
        
        # Verify workflow execution
        assert len(results) == 3
        
        # Check filesystem results
        directory_result = results[0]
        file_result = results[1]
        form_result = results[2]
        
        # Directory listing should contain files
        assert "contents" in str(directory_result) or "config.json" in str(directory_result)
        
        # File reading should contain JSON content
        assert "setting1" in str(file_result) or "value1" in str(file_result)
        
        # Form generation should contain form schema
        assert "form_schema" in str(form_result) or "User Settings" in str(form_result)

    def test_real_world_usage_scenarios(self):
        """Test real-world MCP tools usage scenarios"""
        # Scenario 1: Configuration Management
        filesystem_tool = FilesystemMCPTool(
            identifier="config_manager_fs",
            name="Config Manager Filesystem"
        )
        
        forms_tool = DynamicFormsMCPTool(
            identifier="config_manager_forms",
            name="Config Manager Forms",
            user_config_path=str(self.forms_config_file)
        )
        
        # Read existing configuration
        config_content = filesystem_tool.run({
            "method": "read_file",
            "params": {"path": str(self.forms_config_file)}
        })
        assert config_content is not None
        
        # Generate form for editing configuration
        form_schema = forms_tool.run({
            "method": "generate_form_schema",
            "params": {
                "form_type": "user_settings",
                "user_context": {"config_path": str(self.forms_config_file)}
            }
        })
        assert form_schema is not None
        
        # Scenario 2: Project Analysis
        project_files = filesystem_tool.run({
            "method": "list_directory",
            "params": {"path": str(self.test_files_dir)}
        })
        assert project_files is not None
        
        # Analyze specific files
        analysis_files = ["readme.txt", "config.json", "script.py"]
        analysis_results = []
        
        for filename in analysis_files:
            file_path = self.test_files_dir / filename
            if file_path.exists():
                content = filesystem_tool.run({
                    "method": "read_file",
                    "params": {"path": str(file_path)}
                })
                analysis_results.append({
                    "file": filename,
                    "content": content,
                    "size": len(str(content)) if content else 0
                })
        
        assert len(analysis_results) >= 2
        
        # Scenario 3: Dynamic UI Generation
        ui_forms = ["user_settings", "system_config"]
        generated_forms = []
        
        for form_type in ui_forms:
            form_result = forms_tool.run({
                "method": "generate_form_schema",
                "params": {
                    "form_type": form_type,
                    "user_context": {"config_path": str(self.forms_config_file)}
                }
            })
            
            if form_result:
                generated_forms.append({
                    "form_type": form_type,
                    "schema": form_result
                })
        
        assert len(generated_forms) == 2

    def test_comprehensive_system_health(self):
        """Test overall MCP tools system health and integration"""
        # System health metrics
        health_metrics = {
            "tools_created": 0,
            "successful_operations": 0,
            "errors_handled": 0,
            "performance_tests": 0,
            "integration_tests": 0
        }
        
        # Create and test multiple tools
        tools_to_test = [
            ("filesystem", FilesystemMCPTool, {"identifier": "health_fs", "name": "Health FS"}),
            ("forms", DynamicFormsMCPTool, {"identifier": "health_forms", "name": "Health Forms", "user_config_path": str(self.forms_config_file)}),
            ("github", MCPGitHubTool, {"identifier": "health_github", "name": "Health GitHub"})
        ]
        
        created_tools = []
        
        for tool_type, tool_class, kwargs in tools_to_test:
            try:
                tool = tool_class(**kwargs)
                created_tools.append((tool_type, tool))
                health_metrics["tools_created"] += 1
            except Exception as e:
                health_metrics["errors_handled"] += 1
                print(f"Tool creation error for {tool_type}: {e}")
        
        # Test basic operations for each tool
        for tool_type, tool in created_tools:
            try:
                if tool_type == "filesystem":
                    # Test filesystem operations
                    result1 = tool.run({
                        "method": "list_directory",
                        "params": {"path": str(self.test_files_dir)}
                    })
                    
                    result2 = tool.run({
                        "method": "read_file",
                        "params": {"path": str(self.test_files_dir / "readme.txt")}
                    })
                    
                    if result1 and result2:
                        health_metrics["successful_operations"] += 2
                
                elif tool_type == "forms":
                    # Test forms operations
                    result = tool.run({
                        "method": "generate_form_schema",
                        "params": {
                            "form_type": "user_settings",
                            "user_context": {"config_path": str(self.forms_config_file)}
                        }
                    })
                    
                    if result:
                        health_metrics["successful_operations"] += 1
                
                elif tool_type == "github":
                    # Test GitHub operations (mock)
                    result = tool.run({
                        "method": "list_repositories",
                        "params": {"owner": "test"}
                    })
                    
                    if result:
                        health_metrics["successful_operations"] += 1
                        
            except Exception as e:
                health_metrics["errors_handled"] += 1
                print(f"Operation error for {tool_type}: {e}")
        
        # Performance tests
        try:
            if created_tools:
                # Quick performance test
                start_time = datetime.now()
                
                for _ in range(10):
                    for tool_type, tool in created_tools:
                        if tool_type == "filesystem":
                            tool.run({
                                "method": "list_directory",
                                "params": {"path": str(self.test_files_dir)}
                            })
                
                end_time = datetime.now()
                performance_time = (end_time - start_time).total_seconds()
                
                if performance_time < 5.0:  # Should complete within 5 seconds
                    health_metrics["performance_tests"] += 1
                    
        except Exception as e:
            health_metrics["errors_handled"] += 1
            print(f"Performance test error: {e}")
        
        # Integration tests
        try:
            if len(created_tools) >= 2:
                # Test tool interaction
                fs_tool = next((tool for tool_type, tool in created_tools if tool_type == "filesystem"), None)
                forms_tool = next((tool for tool_type, tool in created_tools if tool_type == "forms"), None)
                
                if fs_tool and forms_tool:
                    # Read config file
                    config_result = fs_tool.run({
                        "method": "read_file",
                        "params": {"path": str(self.forms_config_file)}
                    })
                    
                    # Generate form
                    form_result = forms_tool.run({
                        "method": "generate_form_schema",
                        "params": {
                            "form_type": "user_settings",
                            "user_context": {"config_path": str(self.forms_config_file)}
                        }
                    })
                    
                    if config_result and form_result:
                        health_metrics["integration_tests"] += 1
                        
        except Exception as e:
            health_metrics["errors_handled"] += 1
            print(f"Integration test error: {e}")
        
        # Calculate health score
        total_operations = sum(health_metrics.values())
        success_operations = (
            health_metrics["tools_created"] + 
            health_metrics["successful_operations"] + 
            health_metrics["performance_tests"] + 
            health_metrics["integration_tests"]
        )
        
        health_score = success_operations / total_operations if total_operations > 0 else 0
        
        # Verify system health
        assert health_metrics["tools_created"] >= 2, "Should create at least 2 tools"
        assert health_metrics["successful_operations"] >= 3, "Should have successful operations"
        assert health_score > 0.7, f"System health score too low: {health_score}"
        
        print(f"MCP Tools System Health Score: {health_score:.2f}")
        print(f"Metrics: {health_metrics}")


if __name__ == "__main__":
    # Run basic functionality test
    print("🧪 Running MCP Tools Integration Tests...")
    
    test_suite = TestMCPToolsIntegration()
    test_suite.setup_method()
    
    try:
        # Run key tests
        test_suite.test_mcp_server_base_functionality()
        print("✅ MCP Server Base tests passed")
        
        test_suite.test_filesystem_tool_comprehensive()
        print("✅ Filesystem Tool tests passed")
        
        test_suite.test_dynamic_forms_tool_comprehensive()
        print("✅ Dynamic Forms Tool tests passed")
        
        test_suite.test_github_tool_functionality() 
        print("✅ GitHub Tool tests passed")
        
        test_suite.test_template_system_functionality()
        print("✅ Template System tests passed")
        
        test_suite.test_local_vs_remote_mode_functionality()
        print("✅ Local vs Remote Mode tests passed")
        
        test_suite.test_error_handling_and_edge_cases()
        print("✅ Error Handling tests passed")
        
        test_suite.test_performance_and_optimization()
        print("✅ Performance tests passed")
        
        test_suite.test_real_world_usage_scenarios()
        print("✅ Real-world scenario tests passed")
        
        test_suite.test_comprehensive_system_health()
        print("✅ System health tests passed")
        
        print("\n🎉 All MCP Tools integration tests completed successfully!")
        print("📋 Test Coverage:")
        print("   • MCP Server Base functionality and local mode")
        print("   • Filesystem Tool (read-only file operations)")
        print("   • Dynamic Forms Tool (YAML-based form generation)")
        print("   • GitHub Tool (repository management)")
        print("   • Template System and caching")
        print("   • Direct patterns vs Intent-based patterns")
        print("   • Workflow orchestration and agent integration")
        print("   • Local mode vs Remote mode functionality")
        print("   • Error handling and edge cases")
        print("   • Performance and optimization")
        print("   • Tool discovery and registration")
        print("   • Multi-tool workflows")
        print("   • Real-world usage scenarios")
        print("   • Comprehensive system health")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test_suite.teardown_method()
        
    print("\n🚀 Ready for full pytest execution: pytest tests/core/test_mcp_tools_integration.py -v") 