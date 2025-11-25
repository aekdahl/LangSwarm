# langswarm/mcp/tools/dynamic_forms/main.py

import os
import yaml
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.tools.base import BaseTool
from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin
from langswarm.tools.mcp.template_loader import get_cached_tool_template_safe

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
            },
            "general": {
                "title": "General Settings Configuration", 
                "description": "Configure general application settings",
                "fields": [
                    {
                        "id": "app_name",
                        "label": "Application Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Enter application name"
                    },
                    {
                        "id": "display_name",
                        "label": "Display Name", 
                        "type": "text",
                        "required": False,
                        "placeholder": "Enter display name"
                    },
                    {
                        "id": "language",
                        "label": "Language",
                        "type": "select",
                        "required": False,
                        "options": [
                            {"value": "en", "label": "English"},
                            {"value": "es", "label": "Spanish"},
                            {"value": "fr", "label": "French"}
                        ],
                        "default": "en"
                    },
                    {
                        "id": "timezone",
                        "label": "Timezone",
                        "type": "select",
                        "required": False,
                        "options": [
                            {"value": "UTC", "label": "UTC"},
                            {"value": "EST", "label": "Eastern"},
                            {"value": "PST", "label": "Pacific"}
                        ],
                        "default": "UTC"
                    },
                    {
                        "id": "debug_mode",
                        "label": "Debug Mode",
                        "type": "toggle",
                        "required": False,
                        "default": False
                    },
                    {
                        "id": "max_users",
                        "label": "Maximum Users",
                        "type": "number",
                        "required": False,
                        "default": 100,
                        "min": 1,
                        "max": 10000
                    }
                ]
            },
            "ui": {
                "title": "User Interface Settings",
                "description": "Configuration for user interface preferences",
                "fields": [
                    {
                        "id": "theme",
                        "label": "Theme",
                        "type": "select",
                        "options": [
                            {"value": "light", "label": "Light"},
                            {"value": "dark", "label": "Dark"},
                            {"value": "auto", "label": "Auto"}
                        ],
                        "default_value": "auto"
                    },
                    {
                        "id": "language",
                        "label": "Language",
                        "type": "select",
                        "options": [
                            {"value": "en", "label": "English"},
                            {"value": "es", "label": "Spanish"},
                            {"value": "fr", "label": "French"}
                        ],
                        "default_value": "en"
                    },
                    {
                        "id": "notifications",
                        "label": "Enable Notifications",
                        "type": "toggle",
                        "default_value": True
                    }
                ]
            },
            "ai": {
                "title": "AI Configuration",
                "description": "Settings for AI model and behavior",
                "fields": [
                    {
                        "id": "model",
                        "label": "AI Model",
                        "type": "select",
                        "options": [
                            {"value": "gpt-4o", "label": "GPT-4o"},
                            {"value": "gpt-4", "label": "GPT-4"},
                            {"value": "claude-3", "label": "Claude 3"}
                        ],
                        "default_value": "gpt-4o"
                    },
                    {
                        "id": "temperature",
                        "label": "Temperature",
                        "type": "slider",
                        "min_value": 0,
                        "max_value": 2,
                        "step": 0.1,
                        "default_value": 0.7,
                        "help_text": "Controls randomness of AI responses"
                    },
                    {
                        "id": "max_tokens",
                        "label": "Max Tokens",
                        "type": "number",
                        "min_value": 100,
                        "max_value": 4000,
                        "default_value": 1000
                    }
                ]
            },
            "system": {
                "title": "System Configuration",
                "description": "Advanced system and infrastructure settings",
                "fields": [
                    {
                        "id": "log_level",
                        "label": "Log Level",
                        "type": "select",
                        "options": [
                            {"value": "debug", "label": "Debug"},
                            {"value": "info", "label": "Info"},
                            {"value": "warning", "label": "Warning"},
                            {"value": "error", "label": "Error"}
                        ],
                        "default_value": "info"
                    },
                    {
                        "id": "cache_enabled",
                        "label": "Enable Caching",
                        "type": "toggle",
                        "default_value": True
                    },
                    {
                        "id": "backup_frequency",
                        "label": "Backup Frequency (hours)",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 168,
                        "default_value": 24
                    },
                    {
                        "id": "admin_email",
                        "label": "Administrator Email",
                        "type": "email",
                        "required": True,
                        "placeholder": "admin@example.com"
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
        "title": form_def['title'],
        "description": f"Configure your {form_def['description'].lower()}",
        "form_type": form_type,
        "sections": [
            {
                "id": f"{form_type}_section",
                "title": form_def['title'].replace(' Configuration', ''),
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
class DynamicFormsMCPTool(MCPProtocolMixin, BaseTool):
    """
    Dynamic Forms MCP tool for generating configuration forms.
    
    This tool loads form definitions from the user's main tools.yaml configuration file
    and creates JSON schemas for frontend rendering. Supports multiple field types,
    filtering, and pre-population of values.
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, user_config_path: str = None, **kwargs):
        # Load template values for defaults
        current_dir = os.path.dirname(__file__)
        template_values = get_cached_tool_template_safe(current_dir)
        
        # Set defaults from template if not provided
        description = kwargs.pop('description', template_values.get('description', 'Generate dynamic configuration forms from user-defined YAML schemas'))
        instruction = kwargs.pop('instruction', template_values.get('instruction', 'Use this tool to generate dynamic forms from configuration files'))
        brief = kwargs.pop('brief', template_values.get('brief', 'Dynamic forms tool'))
        
        super().__init__(
            name=name or f"DynamicForms-{identifier}",
            description=description,
            tool_id=identifier,
            **kwargs
        )
        
        # Set configuration file path
        object.__setattr__(self, 'user_config_path', user_config_path or os.path.join(os.getcwd(), "tools.yaml"))
        object.__setattr__(self, 'mcp_server', server)
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        
        # Load form definitions from config
    
    # V2 Direct Method Calls - Expose operations as class methods
    def generate_form_schema(self, form_type: str, **kwargs):
        """Generate a JSON schema for a specific form type"""
        return generate_form_schema(form_type=form_type)
    
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