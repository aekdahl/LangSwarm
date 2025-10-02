"""
Smart defaults system for LangSwarm configuration.

Automatically fills in sensible defaults to reduce configuration complexity.
"""

from typing import Dict, Any, List, Optional
import copy


class SmartDefaults:
    """Applies intelligent defaults to configurations."""
    
    # Model to provider mapping
    MODEL_PROVIDERS = {
        # OpenAI models
        "gpt-4": "openai",
        "gpt-4-turbo": "openai",
        "gpt-4-turbo-preview": "openai",
        "gpt-4o": "openai",
        "gpt-4o-mini": "openai",
        "gpt-3.5-turbo": "openai",
        "gpt-3.5-turbo-16k": "openai",
        
        # Anthropic models
        "claude-3-opus": "anthropic",
        "claude-3-sonnet": "anthropic",
        "claude-3-haiku": "anthropic",
        "claude-2.1": "anthropic",
        "claude-2": "anthropic",
        "claude-instant": "anthropic",
        
        # Google models
        "gemini-pro": "google",
        "gemini-pro-vision": "google",
        "gemini-ultra": "google",
        "palm-2": "google",
        
        # Cohere models
        "command": "cohere",
        "command-light": "cohere",
        "command-nightly": "cohere",
        
        # Mistral models
        "mistral-tiny": "mistral",
        "mistral-small": "mistral",
        "mistral-medium": "mistral",
        "mistral-large": "mistral",
        "mixtral-8x7b": "mistral",
    }
    
    # Default agent settings by provider
    PROVIDER_DEFAULTS = {
        "openai": {
            "temperature": 0.7,
            "max_tokens": None,  # Use model default
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "system_prompt": "You are a helpful AI assistant. Be concise, accurate, and helpful."
        },
        "anthropic": {
            "temperature": 0.7,
            "max_tokens": None,
            "system_prompt": "You are Claude, a helpful AI assistant. Be thoughtful, balanced, and helpful."
        },
        "google": {
            "temperature": 0.7,
            "max_output_tokens": None,
            "top_p": 0.95,
            "top_k": 40,
            "system_prompt": "You are a helpful AI assistant. Provide clear and accurate responses."
        },
        "cohere": {
            "temperature": 0.7,
            "max_tokens": None,
            "system_prompt": "You are a helpful AI assistant. Be informative and clear."
        },
        "mistral": {
            "temperature": 0.7,
            "max_tokens": None,
            "top_p": 1.0,
            "system_prompt": "You are a helpful AI assistant. Provide accurate and useful responses."
        }
    }
    
    # Tool shortcuts
    TOOL_SHORTCUTS = {
        "filesystem": {
            "type": "mcp",
            "description": "File system operations",
            "local_mode": True,
            "settings": {
                "allowed_paths": ["."],
                "read_only": False
            }
        },
        "web_search": {
            "type": "mcp",
            "description": "Web search capabilities",
            "local_mode": True
        },
        "code_executor": {
            "type": "mcp",
            "description": "Execute code snippets",
            "local_mode": True,
            "settings": {
                "languages": ["python", "javascript", "bash"]
            }
        },
        "sql_database": {
            "type": "mcp",
            "description": "SQL database operations",
            "local_mode": True
        }
    }
    
    @classmethod
    def apply_defaults(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply smart defaults to a configuration."""
        config = copy.deepcopy(config)
        
        # Apply agent defaults
        cls._apply_agent_defaults(config)
        
        # Apply memory defaults
        cls._apply_memory_defaults(config)
        
        # Apply security defaults
        cls._apply_security_defaults(config)
        
        # Apply observability defaults
        cls._apply_observability_defaults(config)
        
        # Apply workflow defaults
        cls._apply_workflow_defaults(config)
        
        # Apply tool defaults
        cls._apply_tool_defaults(config)
        
        return config
    
    @classmethod
    def _apply_agent_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to agent configurations."""
        agents = config.get("agents", [])
        
        for agent in agents:
            # Auto-detect provider from model
            if "provider" not in agent and "model" in agent:
                model = agent["model"].lower()
                for model_prefix, provider in cls.MODEL_PROVIDERS.items():
                    if model.startswith(model_prefix):
                        agent["provider"] = provider
                        break
                else:
                    # Default to OpenAI if unknown
                    agent["provider"] = "openai"
            
            # Apply provider-specific defaults
            provider = agent.get("provider", "openai")
            if provider in cls.PROVIDER_DEFAULTS:
                defaults = cls.PROVIDER_DEFAULTS[provider]
                for key, value in defaults.items():
                    if key not in agent:
                        agent[key] = value
            
            # Ensure agent has an ID
            if "id" not in agent:
                agent["id"] = f"agent_{len(agents)}"
            
            # Set name from ID if not provided
            if "name" not in agent:
                agent["name"] = agent["id"].replace("_", " ").title()
    
    @classmethod
    def _apply_memory_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to memory configuration."""
        if "memory" not in config:
            config["memory"] = {
                "backend": "sqlite",
                "settings": {
                    "persist_directory": "./langswarm_data",
                    "enable_embeddings": False,
                    "ttl_seconds": 86400  # 24 hours
                }
            }
        else:
            memory = config["memory"]
            # Add default settings for each backend
            if "settings" not in memory:
                if memory.get("backend") == "sqlite":
                    memory["settings"] = {
                        "persist_directory": "./langswarm_data",
                        "enable_embeddings": False
                    }
                elif memory.get("backend") == "redis":
                    memory["settings"] = {
                        "host": "localhost",
                        "port": 6379,
                        "db": 0,
                        "ttl_seconds": 3600
                    }
    
    @classmethod
    def _apply_security_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to security configuration."""
        if "security" not in config:
            config["security"] = {
                "api_key_validation": True,
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "burst_size": 10
                },
                "input_sanitization": True,
                "max_input_length": 10000,
                "allowed_domains": ["*"]  # CORS
            }
    
    @classmethod
    def _apply_observability_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to observability configuration."""
        if "observability" not in config:
            config["observability"] = {
                "logging": {
                    "level": "INFO",
                    "format": "structured",
                    "output": "console"
                },
                "tracing": {
                    "enabled": False
                },
                "metrics": {
                    "enabled": False
                }
            }
    
    @classmethod
    def _apply_workflow_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to workflow configuration."""
        workflows = config.get("workflows", [])
        
        for i, workflow in enumerate(workflows):
            # Handle string shorthand
            if isinstance(workflow, str):
                workflow_dict = cls._parse_workflow_string(workflow, i)
                config["workflows"][i] = workflow_dict
            elif isinstance(workflow, dict):
                # Add default ID if missing
                if "id" not in workflow:
                    workflow["id"] = f"workflow_{i}"
                
                # Add default name if missing
                if "name" not in workflow:
                    workflow["name"] = workflow["id"].replace("_", " ").title()
    
    @classmethod
    def _parse_workflow_string(cls, workflow_str: str, index: int) -> Dict[str, Any]:
        """Parse workflow string shorthand into full configuration."""
        # Simple format: "agent1 -> agent2 -> user"
        # Conditional: "classifier -> (option1 | option2) -> user"
        # Parallel: "agent1, agent2, agent3 -> aggregator -> user"
        
        workflow_dict = {
            "id": f"workflow_{index}",
            "name": f"Workflow {index + 1}",
            "description": f"Auto-generated from: {workflow_str}",
            "steps": []
        }
        
        # Parse the workflow string (simplified for example)
        parts = workflow_str.split("->")
        for i, part in enumerate(parts):
            step = {
                "id": f"step_{i}",
                "agent": part.strip()
            }
            
            # Handle special cases
            if part.strip() == "user":
                workflow_dict["steps"][-1]["output"] = {"to": "user"}
            else:
                workflow_dict["steps"].append(step)
        
        return workflow_dict
    
    @classmethod
    def _apply_tool_defaults(cls, config: Dict[str, Any]) -> None:
        """Apply defaults to tool configuration."""
        tools = config.get("tools", {})
        
        # Handle list shorthand
        if isinstance(tools, list):
            tools_dict = {}
            for tool_name in tools:
                if tool_name in cls.TOOL_SHORTCUTS:
                    tools_dict[tool_name] = cls.TOOL_SHORTCUTS[tool_name]
                else:
                    # Unknown tool - create minimal config
                    tools_dict[tool_name] = {
                        "type": "mcp",
                        "local_mode": True
                    }
            config["tools"] = tools_dict
        
        # Apply defaults to existing tool configs
        for tool_name, tool_config in config.get("tools", {}).items():
            if not isinstance(tool_config, dict):
                continue
                
            # Add type if missing
            if "type" not in tool_config:
                tool_config["type"] = "mcp"
            
            # Add local_mode if missing
            if "local_mode" not in tool_config:
                tool_config["local_mode"] = True
    
    @classmethod
    def validate_minimal_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate that a configuration has the minimal required fields."""
        errors = []
        
        # Version is required
        if "version" not in config:
            errors.append("Missing required field: 'version'")
        
        # At least one agent is required
        if "agents" not in config or not config["agents"]:
            errors.append("At least one agent must be defined")
        
        # Each agent needs at least a model
        for i, agent in enumerate(config.get("agents", [])):
            if "model" not in agent and "provider" not in agent:
                errors.append(f"Agent {i} must have either 'model' or 'provider' defined")
        
        return errors


def apply_smart_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to apply smart defaults to a configuration."""
    return SmartDefaults.apply_defaults(config)