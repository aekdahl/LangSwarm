# tests/synapse/tools/dynamic_forms/test_dynamic_forms.py

import pytest
import json
from datetime import datetime
import yaml
import os
from unittest.mock import patch, MagicMock

from langswarm.mcp.tools.dynamic_forms.main import (
    DynamicFormsMCPTool,
    generate_form_schema,
    load_form_definitions,
    server
)

class TestDynamicFormsMCPTool:
    """Test suite for the Dynamic Forms MCP Tool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = DynamicFormsMCPTool(
            identifier="test-dynamic-forms",
            name="Test Dynamic Forms Tool"
        )
    
    def test_tool_initialization(self):
        """Test tool initialization and basic properties"""
        assert self.tool.identifier == "test-dynamic-forms"
        assert self.tool.name == "Test Dynamic Forms Tool"
        assert "Generate dynamic configuration forms based on user-defined YAML schemas" in self.tool.description
        assert hasattr(self.tool, 'mcp_server')
        # Check instance attribute to avoid Pydantic issues
        assert hasattr(self.tool, '_is_mcp_tool')
        assert self.tool._is_mcp_tool is True
    
    def test_generate_form_schema_method_routing(self):
        """Test MCP method routing for generate_form_schema"""
        input_data = {
            "method": "generate_form_schema",
            "params": {
                "form_type": "ui"
            }
        }
        
        result = self.tool.run(input_data)
        
        assert "form_schema" in result
        assert result["form_schema"]["form_type"] == "ui"
        assert result["form_schema"]["title"] == "User Interface Settings"
    
    def test_unknown_method_handling(self):
        """Test handling of unknown methods"""
        input_data = {
            "method": "unknown_method"
        }
        
        result = self.tool.run(input_data)
        
        assert "Unknown method" in result
        assert "generate_form_schema" in result
    
    def test_get_available_forms(self):
        """Test getting available form types"""
        available_forms = self.tool.get_available_forms()
        
        assert isinstance(available_forms, list)
        assert "general" in available_forms
        assert "ui" in available_forms
        assert "ai" in available_forms
        assert "system" in available_forms
    
    def test_get_form_definition(self):
        """Test getting form definition from YAML"""
        form_def = self.tool.get_form_definition("general")
        
        assert form_def is not None
        assert "title" in form_def
        assert "description" in form_def
        assert "fields" in form_def
        assert form_def["title"] == "General Settings Configuration"

class TestFormSchemaGeneration:
    """Test suite for form schema generation functions"""
    
    def test_generate_form_schema_general(self):
        """Test generating general configuration form schema"""
        result = generate_form_schema(form_type="general")
        
        assert "form_schema" in result
        schema = result["form_schema"]
        
        assert schema["form_type"] == "general"
        assert schema["title"] == "General Settings Configuration"
        assert len(schema["sections"]) == 1
        
        section = schema["sections"][0]
        assert section["title"] == "General Settings"
        
        # Check specific fields that actually exist in the implementation
        field_ids = [field["id"] for field in section["fields"]]
        assert "app_name" in field_ids
        assert "display_name" in field_ids
        assert "language" in field_ids
        assert "timezone" in field_ids
        assert "debug_mode" in field_ids
        assert "max_users" in field_ids
    
    def test_generate_form_schema_ui(self):
        """Test generating UI preferences form schema"""
        result = generate_form_schema(form_type="ui")
        
        schema = result["form_schema"]
        assert schema["form_type"] == "ui"
        assert schema["title"] == "User Interface Settings"
        
        section = schema["sections"][0]
        field_ids = [field["id"] for field in section["fields"]]
        assert "theme" in field_ids
        assert "language" in field_ids
        assert "notifications" in field_ids
    
    def test_generate_form_schema_ai(self):
        """Test generating AI behavior form schema"""
        result = generate_form_schema(form_type="ai")
        
        schema = result["form_schema"]
        assert schema["form_type"] == "ai"
        assert schema["title"] == "AI Configuration"
        
        section = schema["sections"][0]
        field_ids = [field["id"] for field in section["fields"]]
        assert "model" in field_ids
        assert "temperature" in field_ids
        assert "max_tokens" in field_ids
    
    def test_generate_form_schema_system(self):
        """Test generating system settings form schema"""
        result = generate_form_schema(form_type="system")
        
        schema = result["form_schema"]
        assert schema["form_type"] == "system"
        assert schema["title"] == "System Configuration"
        
        section = schema["sections"][0]
        field_ids = [field["id"] for field in section["fields"]]
        assert "log_level" in field_ids
    
    def test_generate_form_schema_invalid_type(self):
        """Test error handling for invalid form types"""
        with pytest.raises(ValueError) as exc_info:
            generate_form_schema(form_type="invalid")
        
        assert "Invalid form_type 'invalid'" in str(exc_info.value)
        assert "Available types:" in str(exc_info.value)
    
    def test_generate_form_schema_with_context(self):
        """Test form schema generation with user context"""
        user_context = {
            "user_id": "123",
            "role": "admin",
            "preferences": ["dark_theme"]
        }
        
        result = generate_form_schema(
            form_type="general",
            user_context=user_context
        )
        
        schema = result["form_schema"]
        assert schema["user_context"] == user_context
        assert schema["metadata"]["generated_by"] == "dynamic-forms-mcp-tool"
    
    def test_generate_form_schema_with_included_fields(self):
        """Test form schema generation with included fields filter"""
        result = generate_form_schema(
            form_type="ui",
            included_fields=["theme", "language"]
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        field_ids = [field["id"] for field in section["fields"]]
        
        assert len(field_ids) == 2
        assert "theme" in field_ids
        assert "language" in field_ids
        assert "notifications" not in field_ids
    
    def test_generate_form_schema_with_excluded_fields(self):
        """Test form schema generation with excluded fields filter"""
        result = generate_form_schema(
            form_type="ui",
            excluded_fields=["notifications"]
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        field_ids = [field["id"] for field in section["fields"]]
        
        assert "notifications" not in field_ids
        assert "theme" in field_ids
        assert "language" in field_ids
    
    def test_generate_form_schema_with_empty_included_fields(self):
        """Test form schema generation with empty included fields list"""
        result = generate_form_schema(
            form_type="ui",
            included_fields=[]
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        
        assert len(section["fields"]) == 0
    
    def test_generate_form_schema_with_current_settings(self):
        """Test form schema generation with current settings for pre-population"""
        current_settings = {
            "display_name": "Test User",
            "language": "es",
            "timezone": "Europe/Madrid"
        }
        
        result = generate_form_schema(
            form_type="general",
            current_settings=current_settings
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        
        # Check that fields have been pre-populated with current settings
        for field in section["fields"]:
            if field["id"] in current_settings:
                assert field["default_value"] == current_settings[field["id"]]
    
    def test_generate_form_schema_metadata(self):
        """Test form schema metadata generation"""
        result = generate_form_schema(form_type="general")
        
        schema = result["form_schema"]
        metadata = schema["metadata"]
        
        assert metadata["generated_by"] == "dynamic-forms-mcp-tool"
        assert metadata["version"] == "2.0.0"
        assert "field_count" in metadata
        assert "filters_applied" in metadata
        assert "created_at" in schema
        assert isinstance(schema["created_at"], str)

class TestYAMLConfiguration:
    """Test suite for YAML configuration loading"""
    
    def test_load_form_definitions(self):
        """Test loading form definitions from YAML"""
        forms, field_types = load_form_definitions()
        
        assert isinstance(forms, dict)
        assert isinstance(field_types, dict)
        
        # Check that all expected forms are present
        expected_forms = ["general", "ui", "ai", "system"]
        for form_type in expected_forms:
            assert form_type in forms
            assert "title" in forms[form_type]
            assert "description" in forms[form_type]
            assert "fields" in forms[form_type]
    
    def test_yaml_field_types(self):
        """Test YAML field type definitions"""
        forms, field_types = load_form_definitions()
        
        # Check that field types are properly defined
        expected_field_types = ["text", "select", "multiselect", "toggle", "slider", "number", "email", "password", "textarea"]
        for field_type in expected_field_types:
            assert field_type in field_types
            assert "properties" in field_types[field_type]
    
    def test_yaml_form_structure(self):
        """Test YAML form structure validation"""
        forms, field_types = load_form_definitions()
        
        # Check general form structure
        general_form = forms["general"]
        assert general_form["title"] == "General Settings Configuration"
        assert len(general_form["fields"]) == 6
        
        # Check that fields have required properties
        for field in general_form["fields"]:
            assert "id" in field
            assert "label" in field
            assert "type" in field

class TestMCPServerIntegration:
    """Test suite for MCP server integration"""
    
    def test_server_initialization(self):
        """Test MCP server initialization"""
        assert server.name == "dynamic-forms"
        assert server.local_mode is True
        assert "Generate dynamic configuration forms based on YAML definitions" in server.description
    
    def test_server_tasks_registration(self):
        """Test that tasks are properly registered with the server"""
        # Check that the task is registered
        assert "generate_form_schema" in server.tasks
        
        # Check task details
        task = server.tasks["generate_form_schema"]
        assert task["description"] == "Generate form schema from YAML configuration"
        assert task["input_model"].__name__ == "FormSchemaInput"
        assert task["output_model"].__name__ == "FormSchemaOutput"
    
    def test_server_call_task_form_schema(self):
        """Test calling server task for form schema generation"""
        if server.local_mode:
            # In local mode, test direct function call
            result = generate_form_schema(form_type="ui")
            assert "form_schema" in result
            assert result["form_schema"]["form_type"] == "ui"
    
    def test_server_schema_generation(self):
        """Test server schema generation for validation"""
        # Test that the server can generate input/output schemas
        if server.local_mode:
            # In local mode, verify function works
            result = generate_form_schema(form_type="general")
            assert "form_schema" in result
            
            # Verify output structure
            schema = result["form_schema"]
            assert "form_id" in schema
            assert "title" in schema
            assert "sections" in schema
            assert "metadata" in schema

class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_form_schema_invalid_type_error(self):
        """Test error handling for invalid form types"""
        with pytest.raises(ValueError) as exc_info:
            generate_form_schema(form_type="nonexistent")
        
        assert "Invalid form_type 'nonexistent'" in str(exc_info.value)
    
    def test_tool_run_with_invalid_input(self):
        """Test tool run with invalid input data"""
        tool = DynamicFormsMCPTool(
            identifier="test-dynamic-forms",
            name="Test Tool"
        )
        
        # Test with missing method
        result = tool.run({})
        assert "Unknown method" in result or "error" in result
        
        # Test with invalid method
        result = tool.run({"method": "invalid_method"})
        assert "Unknown method" in result or "error" in result
    
    def test_field_filtering_edge_cases(self):
        """Test edge cases in field filtering"""
        # Test with non-existent included fields
        result = generate_form_schema(
            form_type="ui",
            included_fields=["nonexistent_field"]
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        assert len(section["fields"]) == 0
        
        # Test with non-existent excluded fields (should work normally)
        result = generate_form_schema(
            form_type="ui",
            excluded_fields=["nonexistent_field"]
        )
        
        schema = result["form_schema"]
        section = schema["sections"][0]
        assert len(section["fields"]) > 0  # Should have all fields

class TestPerformanceAndValidation:
    """Test suite for performance and validation"""
    
    def test_form_schema_generation_performance(self):
        """Test form schema generation performance"""
        import time
        
        start_time = time.time()
        result = generate_form_schema(form_type="general")
        end_time = time.time()
        
        # Should be very fast (< 1 second for sure)
        assert end_time - start_time < 1.0
        assert "form_schema" in result
    
    def test_form_schema_size_limits(self):
        """Test form schema size is within reasonable limits"""
        result = generate_form_schema(form_type="system")
        
        # Convert to JSON and check size
        json_str = json.dumps(result)
        assert len(json_str) < 50000  # Less than 50KB
    
    def test_field_count_validation(self):
        """Test field count validation"""
        result = generate_form_schema(form_type="general")
        
        schema = result["form_schema"]
        field_count = schema["metadata"]["field_count"]
        actual_field_count = len(schema["sections"][0]["fields"])
        
        assert field_count == actual_field_count
    
    def test_form_structure_validation(self):
        """Test form structure validation"""
        result = generate_form_schema(form_type="ui")
        
        schema = result["form_schema"]
        
        # Check required top-level fields
        required_fields = ["form_id", "title", "description", "form_type", "sections", "metadata", "created_at"]
        for field in required_fields:
            assert field in schema
        
        # Check section structure
        section = schema["sections"][0]
        assert "id" in section
        assert "title" in section
        assert "description" in section
        assert "fields" in section
        
        # Check field structure
        for field in section["fields"]:
            assert "id" in field
            assert "label" in field
            assert "type" in field 