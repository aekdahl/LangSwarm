# langswarm/mcp/tools/dynamic_forms/main.py

import os
import yaml
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool
from langswarm.mcp.tools.template_loader import get_cached_tool_template

# === Simple Pydantic Models ===
class FormSchemaInput(BaseModel):
    form_type: str = Field(..., description="Type of form: general, ui, ai, system")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context for customization")
    included_fields: Optional[List[str]] = Field(None, description="Specific fields to include")
    excluded_fields: Optional[List[str]] = Field(None, description="Specific fields to exclude")
    current_settings: Optional[Dict[str, Any]] = Field(None, description="Current settings for pre-population")

class FormSchemaOutput(BaseModel):
    form_schema: Dict[str, Any]

# === Core Functions ===
def load_form_definitions(user_config_path: Optional[str] = None):
    """
    Load form definitions from user's main tools.yaml configuration.
    Falls back to basic form types if no user configuration is found.
    """
    forms = {}
    field_types = {
        "text": {"properties": ["min_length", "max_length", "pattern", "placeholder", "help_text"]},
        "email": {"properties": ["placeholder", "help_text"]},
        "password": {"properties": ["min_length", "max_length", "placeholder", "help_text"]},
        "number": {"properties": ["min_value", "max_value", "step", "unit", "placeholder", "help_text"]},
        "select": {"properties": ["options", "default_value", "help_text"], "required_properties": ["options"]},
        "multiselect": {"properties": ["options", "default_value", "help_text"], "required_properties": ["options"]},
        "toggle": {"properties": ["default_value", "help_text"]},
        "slider": {"properties": ["min_value", "max_value", "step", "unit", "default_value", "help_text"], "required_properties": ["min_value", "max_value"]},
        "textarea": {"properties": ["rows", "placeholder", "help_text", "min_length", "max_length"]}
    }
    
    # Try to load from user configuration
    if user_config_path and os.path.exists(user_config_path):
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Extract forms from tools configuration
            tools = config.get('tools', [])
            for tool in tools:
                if tool.get('id') == 'dynamic-forms' or tool.get('type') == 'mcpforms':
                    forms = tool.get('forms', {})
                    break
        except Exception as e:
            print(f"Warning: Could not load user configuration from {user_config_path}: {e}")
    
    # If no forms found, provide basic example forms
    if not forms:
        forms = {
            "basic": {
                "title": "Basic Configuration",
                "description": "Simple configuration form",
                "fields": [
                    {
                        "id": "name",
                        "label": "Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Enter your name"
                    },
                    {
                        "id": "enabled",
                        "label": "Enabled",
                        "type": "toggle",
                        "default_value": True,
                        "help_text": "Enable this feature"
                    }
                ]
            }
        }
    
    return forms, field_types

def generate_form_schema(
    form_type: str,
    user_context: Optional[Dict[str, Any]] = None,
    included_fields: Optional[List[str]] = None,
    excluded_fields: Optional[List[str]] = None,
    current_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate form schema from user configuration"""
    
    # Try to determine user config path from environment or user context
    user_config_path = None
    if user_context and 'config_path' in user_context:
        user_config_path = user_context['config_path']
    elif 'LANGSWARM_CONFIG_PATH' in os.environ:
        user_config_path = os.environ['LANGSWARM_CONFIG_PATH']
    
    # Load form definitions
    forms, field_types = load_form_definitions(user_config_path)
    
    # Validate form type
    if form_type not in forms:
        raise ValueError(f"Invalid form_type '{form_type}'. Available types: {list(forms.keys())}")
    
    form_def = forms[form_type]
    fields = form_def['fields'].copy()
    
    # Apply field filtering
    if included_fields is not None:
        if len(included_fields) == 0:
            fields = []
        else:
            fields = [f for f in fields if f['id'] in included_fields]
    
    if excluded_fields:
        fields = [f for f in fields if f['id'] not in excluded_fields]
    
    # Apply current settings pre-population
    if current_settings:
        for field in fields:
            field_id = field['id']
            if field_id in current_settings:
                field['default_value'] = current_settings[field_id]
    
    # Build form schema
    form_schema = {
        "form_id": f"{form_type}_form_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": f"{form_def['title']} Configuration",
        "description": f"Configure your {form_def['description'].lower()}",
        "form_type": form_type,
        "sections": [
            {
                "id": f"{form_type}_section",
                "title": form_def['title'],
                "description": form_def['description'],
                "fields": fields
            }
        ],
        "metadata": {
            "generated_by": "dynamic-forms-mcp-tool",
            "version": "2.0.0",
            "field_count": len(fields),
            "filters_applied": {
                "included_fields": included_fields,
                "excluded_fields": excluded_fields,
                "has_current_settings": bool(current_settings)
            },
            "config_source": user_config_path or "default"
        },
        "created_at": datetime.now().isoformat(),
        "user_context": user_context
    }
    
    return {"form_schema": form_schema}

# === MCP Server Setup ===
server = BaseMCPToolServer(
    name="dynamic-forms",
    description="Generate dynamic configuration forms based on YAML definitions",
    local_mode=True
)

server.add_task(
    name="generate_form_schema",
    description="Generate form schema from YAML configuration",
    input_model=FormSchemaInput,
    output_model=FormSchemaOutput,
    handler=generate_form_schema
)

# Build app (None if local_mode=True)
app = server.build_app()

# === Simplified Tool Class ===
class DynamicFormsMCPTool(BaseTool):
    """
    Simplified Dynamic Forms MCP tool
    
    Loads form definitions from user's main configuration and generates pure JSON schemas.
    No text responses - frontend handles all rendering.
    """
    
    _is_mcp_tool = True
    _bypass_pydantic = True
    
    def __init__(self, identifier: str, name: str, description: str = "", instruction: str = "", brief: str = "", user_config_path: str = None, **kwargs):
        # Load template values for defaults
        current_dir = os.path.dirname(__file__)
        template_values = get_cached_tool_template(current_dir)
        
        # Set defaults from template if not provided
        description = description or template_values.get('description', 'Generate dynamic configuration forms from user-defined YAML schemas')
        instruction = instruction or template_values.get('instruction', 'Use this tool to create form schemas for frontend rendering from user configuration')
        brief = brief or template_values.get('brief', 'Dynamic forms from user config')
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
        # Store user config path for dynamic loading
        self.user_config_path = user_config_path
        
        super().__init__(
            name=name,
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
    
    def run(self, input_data=None):
        """Execute form generation method"""
        method_handlers = {
            "generate_form_schema": generate_form_schema,
        }
        
        return self._handle_mcp_structured_input(input_data, method_handlers)
    
    def get_available_forms(self):
        """Get list of available form types from user configuration"""
        forms, _ = load_form_definitions(self.user_config_path)
        return list(forms.keys())
    
    def get_form_definition(self, form_type: str):
        """Get raw form definition from user configuration"""
        forms, _ = load_form_definitions(self.user_config_path)
        return forms.get(form_type)

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        print("Forms will be loaded from user's main tools.yaml configuration")
        
        # Try to show available forms if config path is available
        user_config_path = os.environ.get('LANGSWARM_CONFIG_PATH')
        if user_config_path:
            forms, _ = load_form_definitions(user_config_path)
            print(f"Available forms: {list(forms.keys())}")
        else:
            print("Set LANGSWARM_CONFIG_PATH environment variable to show available forms")
    else:
        uvicorn.run("langswarm.mcp.tools.dynamic_forms.main:app", host="0.0.0.0", port=4030, reload=True) 