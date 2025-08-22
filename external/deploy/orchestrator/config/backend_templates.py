"""
Backend configuration templates for the unified orchestrator
"""
from typing import Dict, Any, List


# Backend templates for frontend
BACKEND_TEMPLATES = {
    "aaf": {
        "name": "AAF Backend",
        "description": "LangSwarm-powered chatbot backend with full lifecycle management",
        "capabilities": {
            "create": True,
            "adopt": True,
            "delete": True,
            "update_prompts": True,
            "remove_from_admin": False
        },
        "features": {
            "demo_management": True,
            "knowledge_base": True,
            "multi_tools": True,
            "prompt_management": True,
            "config_editor": True,
            "websocket_chat": True
        },
        "deployment": {
            "image_base": "europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend",
            "health_endpoint": "/health",
            "config_endpoint": "/api/config",
            "default_memory": "2Gi",
            "default_cpu": "1",
            "default_max_instances": 10
        },
        "configuration_fields": [
            {
                "name": "instance_name",
                "label": "Instance Name",
                "type": "text",
                "placeholder": "aaf-instance-example",
                "required": True,
                "description": "Unique name for the Cloud Run service"
            },
            {
                "name": "openai_api_key",
                "label": "OpenAI API Key",
                "type": "password",
                "placeholder": "sk-...",
                "required": True,
                "description": "OpenAI API key for LLM access"
            },
            {
                "name": "bigquery_dataset_id",
                "label": "BigQuery Dataset ID",
                "type": "text",
                "placeholder": "aaf_sessions",
                "required": True,
                "description": "BigQuery dataset for session storage"
            },
            {
                "name": "crawl4ai_base_url",
                "label": "Crawl4AI Base URL",
                "type": "text",
                "placeholder": "https://crawl4ai-service.run.app",
                "required": True,
                "description": "Base URL for Crawl4AI MCP server"
            },
            {
                "name": "image_tag",
                "label": "Image Tag",
                "type": "select",
                "options": ["latest", "stable", "main-app-route", "debug-endpoints"],
                "default": "latest",
                "description": "Docker image tag to deploy"
            },
            {
                "name": "memory",
                "label": "Memory Allocation",
                "type": "select",
                "options": ["1Gi", "2Gi", "4Gi", "8Gi"],
                "default": "2Gi",
                "description": "Memory allocation for the service"
            },
            {
                "name": "cpu",
                "label": "CPU Allocation",
                "type": "select",
                "options": ["1", "2", "4"],
                "default": "1",
                "description": "CPU allocation for the service"
            },
            {
                "name": "max_instances",
                "label": "Max Instances",
                "type": "number",
                "min": 1,
                "max": 100,
                "default": 10,
                "description": "Maximum number of concurrent instances"
            }
        ],
        "prompt_fields": [
            {
                "name": "system_prompt",
                "label": "System Prompt",
                "type": "textarea",
                "placeholder": "You are a helpful assistant...",
                "required": True,
                "description": "The main system prompt for the AI agent"
            },
            {
                "name": "model",
                "label": "AI Model",
                "type": "select",
                "options": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
                "default": "gpt-4o",
                "description": "The AI model to use"
            },
            {
                "name": "temperature",
                "label": "Temperature",
                "type": "range",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.7,
                "description": "Controls randomness in responses (0 = deterministic, 1 = creative)"
            },
            {
                "name": "welcome_message",
                "label": "Welcome Message",
                "type": "text",
                "placeholder": "Hello! How can I help you today?",
                "description": "Initial message shown to users"
            }
        ]
    },
    
    "custom": {
        "name": "Custom Backend",
        "description": "Existing custom AI backend with prompt management only",
        "capabilities": {
            "create": False,
            "adopt": True,
            "delete": False,
            "update_prompts": True,
            "remove_from_admin": True
        },
        "features": {
            "demo_management": False,
            "knowledge_base": False,
            "multi_tools": False,
            "prompt_management": True
        },
        "deployment": {
            "health_endpoint": "/health",
            "config_endpoint": "/api/prompts",
            "adoption_only": True
        },
        "adoption_fields": [
            {
                "name": "service_name",
                "label": "Cloud Run Service Name",
                "type": "text",
                "placeholder": "custom-backend-instance-123",
                "required": True,
                "description": "The existing Cloud Run service name to adopt",
                "validation": {
                    "pattern": "^[a-z]([a-z0-9-]*[a-z0-9])?$",
                    "message": "Must be a valid Cloud Run service name"
                }
            },
            {
                "name": "expected_version",
                "label": "Expected Backend Version",
                "type": "text",
                "placeholder": "v1.2.3",
                "description": "Optional: Expected version for validation"
            },
            {
                "name": "api_key",
                "label": "API Key (if required)",
                "type": "password",
                "placeholder": "Optional authentication key",
                "description": "API key if the backend requires authentication"
            }
        ],
        "prompt_fields": [
            # Note: These are fallback examples - actual fields loaded from service's schema endpoint
            # Custom backends only need simple prompt management, no complex features
            {
                "name": "system_prompt",
                "label": "System Prompt",
                "type": "textarea",
                "placeholder": "You are a helpful assistant...",
                "required": True,
                "description": "The main system prompt for the AI"
            },
            {
                "name": "assistant_name",
                "label": "Assistant Name",
                "type": "text",
                "placeholder": "AI Assistant",
                "default": "AI Assistant",
                "description": "How the AI introduces itself"
            },
            {
                "name": "response_style",
                "label": "Response Style",
                "type": "select",
                "options": ["professional", "casual", "technical", "friendly"],
                "default": "professional",
                "description": "The tone and style of responses"
            }
        ]
    }
}


def get_backend_template(backend_type: str) -> Dict[str, Any]:
    """Get template for a specific backend type"""
    if backend_type not in BACKEND_TEMPLATES:
        raise ValueError(f"Unknown backend type: {backend_type}")
    
    return BACKEND_TEMPLATES[backend_type]


def get_supported_backend_types() -> List[str]:
    """Get list of supported backend types"""
    return list(BACKEND_TEMPLATES.keys())


def validate_configuration(backend_type: str, config: Dict[str, Any], field_type: str = "configuration") -> Dict[str, str]:
    """Validate configuration against template"""
    template = get_backend_template(backend_type)
    
    field_key = f"{field_type}_fields"
    if field_type == "adoption":
        field_key = "adoption_fields"
    elif field_type == "prompts":
        field_key = "prompt_fields"
    
    fields = template.get(field_key, [])
    errors = {}
    
    for field in fields:
        field_name = field["name"]
        value = config.get(field_name)
        
        # Check required fields
        if field.get("required") and (not value or str(value).strip() == ""):
            errors[field_name] = f"{field['label']} is required"
            continue
        
        # Skip validation if value is empty and field is not required
        if not value:
            continue
        
        # Type-specific validation
        if field["type"] == "number":
            try:
                num_value = float(value)
                if "min" in field and num_value < field["min"]:
                    errors[field_name] = f"{field['label']} must be at least {field['min']}"
                if "max" in field and num_value > field["max"]:
                    errors[field_name] = f"{field['label']} must be at most {field['max']}"
            except (ValueError, TypeError):
                errors[field_name] = f"{field['label']} must be a valid number"
        
        elif field["type"] == "range":
            try:
                range_value = float(value)
                if range_value < field.get("min", 0) or range_value > field.get("max", 1):
                    errors[field_name] = f"{field['label']} must be between {field.get('min', 0)} and {field.get('max', 1)}"
            except (ValueError, TypeError):
                errors[field_name] = f"{field['label']} must be a valid number"
        
        # Pattern validation
        validation = field.get("validation", {})
        if "pattern" in validation:
            import re
            if not re.match(validation["pattern"], str(value)):
                errors[field_name] = validation.get("message", f"{field['label']} format is invalid")
    
    return errors


def get_default_configuration(backend_type: str, field_type: str = "configuration") -> Dict[str, Any]:
    """Get default configuration values for a backend type"""
    template = get_backend_template(backend_type)
    
    field_key = f"{field_type}_fields"
    if field_type == "adoption":
        field_key = "adoption_fields"
    elif field_type == "prompts":
        field_key = "prompt_fields"
    
    fields = template.get(field_key, [])
    defaults = {}
    
    for field in fields:
        if "default" in field:
            defaults[field["name"]] = field["default"]
    
    return defaults
