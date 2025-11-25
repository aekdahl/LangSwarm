"""
LangSwarm V2 Configuration Loaders

Modern configuration loading system supporting:
- Single-file YAML configurations
- Multi-file configurations with includes
- Environment variable substitution
- Schema validation
- Migration from V1 configurations
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import re
from dataclasses import asdict

from .schema import LangSwarmConfig, ConfigTemplates
from langswarm.core.errors import ConfigurationError, ValidationError, ErrorContext
from .error_helpers import ConfigErrorHelper
from .enhanced_validator import EnhancedConfigValidator


logger = logging.getLogger(__name__)


class ConfigurationLoader:
    """
    Modern configuration loader for LangSwarm V2.
    
    Supports:
    - Single YAML file configurations
    - Multi-file configurations with includes
    - Environment variable substitution
    - Schema validation and migration
    - Template-based configuration
    """
    
    def __init__(self, search_paths: Optional[List[str]] = None):
        """
        Initialize configuration loader.
        
        Args:
            search_paths: Directories to search for configuration files
        """
        self.search_paths = search_paths or [
            ".",
            "config",
            "configs",
            os.path.expanduser("~/.langswarm"),
            "/etc/langswarm"
        ]
        self.loaded_files: List[str] = []
        self.environment_substitutions: Dict[str, str] = {}
    
    def load(self, config_path: Optional[str] = None) -> LangSwarmConfig:
        """
        Load configuration from file or auto-discover.
        
        Args:
            config_path: Specific configuration file path
            
        Returns:
            Loaded and validated LangSwarmConfig
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        try:
            # Determine configuration file
            if config_path:
                config_file = Path(config_path)
                if not config_file.exists():
                    raise ConfigErrorHelper.file_not_found(config_path, self.search_paths)
            else:
                config_file = self._auto_discover_config()
            
            logger.info(f"Loading configuration from: {config_file}")
            
            # Load and process configuration
            raw_config = self._load_yaml_file(config_file)
            processed_config = self._process_configuration(raw_config, config_file.parent)
            
            # Create and validate configuration object
            config = LangSwarmConfig.from_dict(processed_config)
            
            # Enhanced validation with better error messages
            validator = EnhancedConfigValidator()
            validation_errors = validator.validate_config(config)
            
            if validation_errors:
                # If there are multiple errors, show the first one with context about others
                primary_error = validation_errors[0]
                if len(validation_errors) > 1:
                    primary_error.suggestion += f"\n\nNote: Found {len(validation_errors) - 1} additional error(s). Fix this one first."
                raise primary_error
            
            # STRICT MODE: Validate runtime dependencies immediately
            self._validate_runtime_dependencies(config)
            
            logger.info(f"Configuration loaded successfully: {len(config.agents)} agents, {len(config.tools)} tools")
            return config
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            else:
                # Provide more context for common errors
                if "yaml" in str(e).lower():
                    raise ConfigurationError(
                        "Failed to parse configuration file",
                        suggestion="Check your YAML syntax. Common issues: incorrect indentation, missing colons, or unclosed quotes.",
                        cause=e
                    ) from e
                raise ConfigurationError(f"Failed to load configuration: {e}") from e
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> LangSwarmConfig:
        """
        Load configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Loaded and validated LangSwarmConfig
        """
        try:
            processed_config = self._substitute_environment_variables(config_dict)
            return LangSwarmConfig.from_dict(processed_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from dictionary: {e}") from e
    
    def load_template(self, template_name: str, **kwargs) -> LangSwarmConfig:
        """
        Load configuration from template.
        
        Args:
            template_name: Template name (simple_chatbot, development_setup, production_setup)
            **kwargs: Template parameters
            
        Returns:
            Template-based configuration
        """
        try:
            if template_name == "simple_chatbot":
                return ConfigTemplates.simple_chatbot(**kwargs)
            elif template_name == "development_setup":
                return ConfigTemplates.development_setup()
            elif template_name == "production_setup":
                return ConfigTemplates.production_setup()
            else:
                raise ConfigurationError(f"Unknown template: {template_name}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load template {template_name}: {e}") from e
    
    def save(self, config: LangSwarmConfig, output_path: str, format: str = "yaml"):
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            output_path: Output file path
            format: Output format (yaml, json)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = config.to_dict()
            
            if format.lower() == "yaml":
                with open(output_file, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2, sort_keys=False)
            elif format.lower() == "json":
                with open(output_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            else:
                raise ConfigurationError(f"Unsupported format: {format}")
            
            logger.info(f"Configuration saved to: {output_file}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e
    
    def _auto_discover_config(self) -> Path:
        """Auto-discover configuration file - STRICT MODE: fail if not found"""
        config_names = [
            "langswarm.yaml",
            "langswarm.yml",
            "config.yaml",
            "config.yml",
            ".langswarm.yaml",
            ".langswarm.yml"
        ]
        
        searched_paths = []
        for search_path in self.search_paths:
            search_dir = Path(search_path)
            searched_paths.append(str(search_dir))
            if not search_dir.exists():
                continue
                
            for config_name in config_names:
                config_file = search_dir / config_name
                if config_file.exists():
                    return config_file
        
        # STRICT MODE: No auto-generation - fail immediately
        raise ConfigErrorHelper.file_not_found(
            "langswarm.yaml",  # Most common expected filename
            searched_paths
        )
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Substitute environment variables
            content = self._substitute_environment_variables_in_text(content)
            
            # Parse YAML
            data = yaml.safe_load(content)
            self.loaded_files.append(str(file_path))
            
            return data or {}
            
        except yaml.YAMLError as e:
            raise ConfigErrorHelper.yaml_syntax_error(str(file_path), e) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load {file_path}",
                suggestion="Ensure the file exists and you have read permissions.",
                cause=e
            ) from e
    
    def _process_configuration(self, config_data: Dict[str, Any], base_path: Path) -> Dict[str, Any]:
        """Process configuration with includes and validation"""
        processed_config = config_data.copy()
        
        # Handle includes
        if 'includes' in processed_config:
            included_configs = self._process_includes(processed_config['includes'], base_path)
            processed_config = self._merge_configurations(included_configs + [processed_config])
            # Remove includes from final config
            processed_config.pop('includes', None)
        
        # Environment variable substitution
        processed_config = self._substitute_environment_variables(processed_config)
        
        return processed_config
    
    def _process_includes(self, includes: List[str], base_path: Path) -> List[Dict[str, Any]]:
        """Process include directives - STRICT MODE: all includes must exist"""
        included_configs = []
        
        for include_path in includes:
            # Resolve relative to base path
            if not os.path.isabs(include_path):
                include_file = base_path / include_path
            else:
                include_file = Path(include_path)
            
            # STRICT MODE: All include files must exist
            if not include_file.exists():
                raise ConfigurationError(
                    f"Required include file not found: {include_file}. "
                    f"All include files must exist and be accessible."
                )
            
            # Prevent circular includes
            if str(include_file) in self.loaded_files:
                raise ConfigurationError(
                    f"Circular include detected: {include_file}. "
                    f"Include files cannot reference each other in a circular manner."
                )
            
            logger.debug(f"Loading include: {include_file}")
            include_config = self._load_yaml_file(include_file)
            
            # Recursively process includes
            include_config = self._process_configuration(include_config, include_file.parent)
            included_configs.append(include_config)
        
        return included_configs
    
    def _merge_configurations(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        if not configs:
            return {}
        
        base_config = {}
        
        for config in configs:
            base_config = self._deep_merge(base_config, config)
        
        return base_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # For lists, append unique items
                result[key] = result[key] + [item for item in value if item not in result[key]]
            else:
                result[key] = value
        
        return result
    
    def _substitute_environment_variables_in_text(self, text: str) -> str:
        """Substitute environment variables in text using ${VAR} or $VAR syntax - STRICT MODE"""
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            default_value = match.group(3) if match.group(3) else None
            
            # Get environment variable
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                self.environment_substitutions[var_name] = env_value
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # STRICT MODE: No placeholders or warnings - fail immediately
                # Try to provide helpful context based on common variable names
                description = ""
                example = None
                if "API_KEY" in var_name:
                    provider = var_name.replace("_API_KEY", "").lower()
                    description = f"This appears to be an API key for {provider}."
                    example = "your-api-key-here"
                elif "PATH" in var_name:
                    description = "This appears to be a file or directory path."
                    example = "/path/to/resource"
                elif "URL" in var_name or "ENDPOINT" in var_name:
                    description = "This appears to be a URL or endpoint."
                    example = "https://api.example.com"
                
                raise ConfigErrorHelper.environment_variable_missing(
                    var_name,
                    description,
                    example
                )
        
        # Pattern matches ${VAR}, ${VAR:default}, $VAR
        pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*):?([^}]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        return re.sub(pattern, replace_var, text)
    
    def _validate_runtime_dependencies(self, config: LangSwarmConfig):
        """Validate that all runtime dependencies are accessible - STRICT MODE"""
        errors = []
        
        # Validate environment variables for all providers used
        providers_used = {agent.provider for agent in config.agents}
        env_var_map = {
            "openai": config.security.openai_api_key_env,
            "anthropic": config.security.anthropic_api_key_env,
            "gemini": config.security.gemini_api_key_env,
            "cohere": config.security.cohere_api_key_env,
        }
        
        for provider in providers_used:
            if provider.value in env_var_map:
                env_var = env_var_map[provider.value]
                if not os.getenv(env_var):
                    # Use the enhanced error helper for missing API keys
                    raise ConfigErrorHelper.missing_api_key(provider.value, env_var)
        
        # Validate memory backend accessibility
        if config.memory.backend.value == "redis":
            redis_url = config.memory.config.get("url", "redis://localhost:6379")
            try:
                # Try to import and connect to Redis
                import redis
                r = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
                r.ping()
            except ImportError:
                errors.append("Redis backend configured but 'redis' package not installed. Install with: pip install redis")
            except Exception as e:
                errors.append(f"Redis backend configured but not accessible at {redis_url}: {e}")
        
        elif config.memory.backend.value == "postgres":
            try:
                import psycopg2
                # Could add connection test here if connection string is provided
            except ImportError:
                errors.append("Postgres backend configured but 'psycopg2' package not installed. Install with: pip install psycopg2")
        
        elif config.memory.backend.value == "sqlite":
            db_path = config.memory.config.get("db_path", "langswarm.db")
            db_dir = os.path.dirname(os.path.abspath(db_path)) if os.path.dirname(db_path) else "."
            if not os.access(db_dir, os.W_OK):
                errors.append(f"SQLite database directory '{db_dir}' is not writable")
        
        elif config.memory.backend.value == "chromadb":
            try:
                import chromadb
            except ImportError:
                errors.append("ChromaDB backend configured but 'chromadb' package not installed. Install with: pip install chromadb")
        
        elif config.memory.backend.value == "qdrant":
            try:
                import qdrant_client
            except ImportError:
                errors.append("Qdrant backend configured but 'qdrant-client' package not installed. Install with: pip install qdrant-client")
        
        # Validate SSL configuration if enabled
        if config.server.ssl_enabled:
            if not config.server.ssl_cert_file or not config.server.ssl_key_file:
                errors.append("SSL enabled but ssl_cert_file or ssl_key_file not specified")
            else:
                if not os.path.exists(config.server.ssl_cert_file):
                    errors.append(f"SSL certificate file not found: {config.server.ssl_cert_file}")
                if not os.path.exists(config.server.ssl_key_file):
                    errors.append(f"SSL key file not found: {config.server.ssl_key_file}")
        
        # Validate log file accessibility if specified
        if config.observability.log_file:
            log_dir = os.path.dirname(os.path.abspath(config.observability.log_file))
            if not os.access(log_dir, os.W_OK):
                errors.append(f"Log file directory '{log_dir}' is not writable")
        
        # Validate trace output file accessibility if specified
        if config.observability.trace_output_file:
            trace_dir = os.path.dirname(os.path.abspath(config.observability.trace_output_file))
            if not os.access(trace_dir, os.W_OK):
                errors.append(f"Trace output directory '{trace_dir}' is not writable")
        
        if errors:
            # Create a comprehensive error with all issues
            raise ConfigurationError(
                "Configuration validation failed",
                context=ErrorContext(
                    component="ConfigurationValidator",
                    operation="validate_runtime_dependencies",
                    metadata={"error_count": len(errors)}
                ),
                suggestion=(
                    "Fix the following issues:\n" + 
                    "\n".join(f"  • {error}" for error in errors) +
                    "\n\nFor development, start with minimal configuration using SQLite memory backend."
                )
            )
    
    def _substitute_environment_variables(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration object"""
        if isinstance(obj, dict):
            return {key: self._substitute_environment_variables(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_environment_variables(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_environment_variables_in_text(obj)
        else:
            return obj


class V1ConfigurationMigrator:
    """
    Migrate V1 configurations to V2 format.
    
    Handles the complex V1 configuration patterns and converts them
    to the clean V2 schema.
    """
    
    def __init__(self):
        self.migration_warnings: List[str] = []
        self.migration_info: List[str] = []
    
    def migrate_from_v1(self, v1_config_path: str) -> LangSwarmConfig:
        """
        Migrate V1 configuration to V2.
        
        Args:
            v1_config_path: Path to V1 configuration directory or file
            
        Returns:
            Migrated V2 configuration
        """
        try:
            self.migration_warnings = []
            self.migration_info = []
            
            logger.info(f"Starting V1 to V2 configuration migration from: {v1_config_path}")
            
            # Load V1 configuration
            v1_data = self._load_v1_configuration(v1_config_path)
            
            # Convert to V2 format
            v2_config = self._convert_v1_to_v2(v1_data)
            
            # Log migration results
            if self.migration_warnings:
                logger.warning(f"Migration completed with {len(self.migration_warnings)} warnings:")
                for warning in self.migration_warnings:
                    logger.warning(f"  - {warning}")
            
            logger.info(f"Migration completed successfully. Converted {len(v2_config.agents)} agents, {len(v2_config.tools)} tools, {len(v2_config.workflows)} workflows")
            
            return v2_config
            
        except Exception as e:
            raise ConfigurationError(f"V1 to V2 migration failed: {e}") from e
    
    def _load_v1_configuration(self, config_path: str) -> Dict[str, Any]:
        """Load V1 configuration (simplified for demo)"""
        # This would implement the complex V1 loading logic
        # For now, we'll load a basic YAML structure
        
        config_file = Path(config_path)
        if config_file.is_file():
            # Single file
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        elif config_file.is_dir():
            # Multi-file configuration
            merged_config = {}
            
            # Look for common V1 files
            v1_files = [
                "agents.yaml", "agents.yml",
                "tools.yaml", "tools.yml", 
                "workflows.yaml", "workflows.yml",
                "config.yaml", "config.yml"
            ]
            
            for filename in v1_files:
                file_path = config_file / filename
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        file_data = yaml.safe_load(f) or {}
                        merged_config = self._deep_merge_v1(merged_config, file_data)
            
            return merged_config
        else:
            raise ConfigurationError(f"V1 configuration path not found: {config_path}")
    
    def _convert_v1_to_v2(self, v1_data: Dict[str, Any]) -> LangSwarmConfig:
        """Convert V1 data structure to V2 configuration"""
        
        # Start with basic V2 structure
        v2_data = {
            "version": "2.0",
            "name": v1_data.get("project_name", "Migrated from V1"),
            "agents": [],
            "tools": {},
            "workflows": [],
            "memory": {},
            "security": {},
            "observability": {},
            "server": {}
        }
        
        # Convert agents
        if "agents" in v1_data:
            v2_data["agents"] = self._convert_v1_agents(v1_data["agents"])
        
        # Convert tools
        if "tools" in v1_data:
            v2_data["tools"] = self._convert_v1_tools(v1_data["tools"])
        
        # Convert workflows  
        if "workflows" in v1_data:
            v2_data["workflows"] = self._convert_v1_workflows(v1_data["workflows"])
        
        # Convert memory configuration
        if "memory" in v1_data:
            v2_data["memory"] = self._convert_v1_memory(v1_data["memory"])
        
        # Convert other sections
        if "langswarm" in v1_data:
            self._convert_v1_langswarm_section(v1_data["langswarm"], v2_data)
        
        return LangSwarmConfig.from_dict(v2_data)
    
    def _convert_v1_agents(self, v1_agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert V1 agents to V2 format"""
        v2_agents = []
        
        for agent in v1_agents:
            v2_agent = {
                "id": agent.get("id", f"agent_{len(v2_agents)}"),
                "name": agent.get("name"),
                "provider": self._map_v1_provider(agent.get("agent_type", "openai")),
                "model": agent.get("model", "gpt-4o"),
                "system_prompt": agent.get("system_prompt"),
                "temperature": agent.get("temperature", 0.7),
                "max_tokens": agent.get("max_tokens"),
                "tools": agent.get("tools", []),
                "memory_enabled": agent.get("is_conversational", True),
                "streaming": agent.get("streaming", False)
            }
            
            # Clean up None values
            v2_agent = {k: v for k, v in v2_agent.items() if v is not None}
            v2_agents.append(v2_agent)
        
        return v2_agents
    
    def _convert_v1_tools(self, v1_tools: Union[List, Dict]) -> Dict[str, Dict[str, Any]]:
        """Convert V1 tools to V2 format"""
        v2_tools = {}
        
        if isinstance(v1_tools, list):
            # Tools as list
            for i, tool in enumerate(v1_tools):
                tool_id = tool.get("id", f"tool_{i}")
                v2_tools[tool_id] = {
                    "id": tool_id,
                    "type": tool.get("type", "utility"),
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "config": tool.get("config", {}),
                    "enabled": tool.get("enabled", True)
                }
        elif isinstance(v1_tools, dict):
            # Tools as dictionary
            for tool_id, tool_config in v1_tools.items():
                v2_tools[tool_id] = {
                    "id": tool_id,
                    "type": tool_config.get("type", "utility"),
                    "name": tool_config.get("name"),
                    "description": tool_config.get("description"),
                    "config": tool_config.get("config", {}),
                    "enabled": tool_config.get("enabled", True)
                }
        
        return v2_tools
    
    def _convert_v1_workflows(self, v1_workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert V1 workflows to V2 format"""
        v2_workflows = []
        
        for workflow in v1_workflows:
            v2_workflow = {
                "id": workflow.get("id", f"workflow_{len(v2_workflows)}"),
                "name": workflow.get("name"),
                "description": workflow.get("description"),
                "steps": workflow.get("steps", []),
                "engine": "v2_native"
            }
            
            # Handle simple syntax
            if "simple_syntax" in workflow:
                v2_workflow["simple_syntax"] = workflow["simple_syntax"]
            
            v2_workflows.append(v2_workflow)
        
        return v2_workflows
    
    def _convert_v1_memory(self, v1_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Convert V1 memory configuration to V2 format"""
        return {
            "enabled": v1_memory.get("enabled", True),
            "backend": "auto",  # V2 will auto-detect
            "config": v1_memory.get("config", {}),
            "max_messages": v1_memory.get("max_messages", 100)
        }
    
    def _convert_v1_langswarm_section(self, v1_langswarm: Dict[str, Any], v2_data: Dict[str, Any]):
        """Convert V1 langswarm section to V2 format"""
        
        # Update observability settings
        if "debug" in v1_langswarm:
            v2_data["observability"]["log_level"] = "DEBUG" if v1_langswarm["debug"] else "INFO"
        
        # Update security settings
        if "api_keys" in v1_langswarm:
            security = v2_data.setdefault("security", {})
            # Map V1 API key patterns to V2 environment variables
    
    def _map_v1_provider(self, v1_provider: str) -> str:
        """Map V1 provider names to V2 enum values"""
        provider_mapping = {
            "langchain-openai": "openai",
            "langchain-anthropic": "anthropic", 
            "openai": "openai",
            "anthropic": "anthropic",
            "azure-openai": "azure_openai",
            "gemini": "gemini",
            "cohere": "cohere"
        }
        
        mapped = provider_mapping.get(v1_provider.lower())
        if mapped is None:
            raise ConfigurationError(f"Unknown provider '{v1_provider}' in V1 configuration. Supported providers: {list(provider_mapping.keys())}")
        
        if mapped != v1_provider.lower():
            # Log the mapping but don't use warnings list since we're in strict mode
            logger.info(f"Mapped V1 provider '{v1_provider}' to V2 provider '{mapped}'")
        
        return mapped
    
    def _deep_merge_v1(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge V1 configurations"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_v1(result[key], value)
            else:
                result[key] = value
        
        return result


# Global configuration loader instance
_config_loader: Optional[ConfigurationLoader] = None


def get_config_loader() -> ConfigurationLoader:
    """Get the global configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigurationLoader()
    return _config_loader


def load_config(config_path: Optional[str] = None) -> LangSwarmConfig:
    """
    Convenience function to load configuration.
    
    DEPRECATED: Use code-first configuration instead.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Loaded configuration
    """
    import warnings
    warnings.warn(
        "YAML configuration is deprecated and will be removed in a future version. "
        "Please migrate to code-first configuration using AgentBuilder.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.warning("⚠️  YAML configuration is deprecated. Please migrate to code-first configuration.")
    
    loader = get_config_loader()
    return loader.load(config_path)


def load_template(template_name: str, **kwargs) -> LangSwarmConfig:
    """
    Convenience function to load configuration template.
    
    Args:
        template_name: Template name
        **kwargs: Template parameters
        
    Returns:
        Template-based configuration
    """
    loader = get_config_loader()
    return loader.load_template(template_name, **kwargs)


def migrate_v1_config(v1_config_path: str) -> LangSwarmConfig:
    """
    Convenience function to migrate V1 configuration.
    
    Args:
        v1_config_path: Path to V1 configuration
        
    Returns:
        Migrated V2 configuration
    """
    migrator = V1ConfigurationMigrator()
    return migrator.migrate_from_v1(v1_config_path)
