"""
LangSwarm V2 Configuration System

Modern, modular configuration system that replaces the monolithic 4,600+ line
config.py with a clean, type-safe, validated system supporting:

- Single-file and multi-file configurations
- Environment variable substitution
- Schema validation and migration
- Template-based configuration
- V1 to V2 migration tools
- Configuration comparison and optimization

Usage:
    from langswarm.core.config import load_config, LangSwarmConfig
    
    # Load configuration
    config = load_config("langswarm.yaml")
    
    # Or use templates
    config = load_template("development_setup")
    
    # Validate configuration
    is_valid, issues = validate_config(config)
"""

from typing import Optional

from .schema import (
    # Core configuration classes
    LangSwarmConfig,
    AgentConfig,
    ToolConfig,
    WorkflowConfig,
    MemoryConfig,
    SecurityConfig,
    ObservabilityConfig,
    ServerConfig,
    
    # Enums
    ProviderType,
    MemoryBackend,
    WorkflowEngine,
    LogLevel,
    
    # Templates
    ConfigTemplates
)

from .loaders import (
    ConfigurationLoader,
    V1ConfigurationMigrator,
    load_config,
    load_template,
    migrate_v1_config,
    get_config_loader
)

from .validation import (
    ConfigurationValidator,
    ValidationIssue,
    ValidationSeverity,
    validate_config,
    format_validation_report
)

from .utils import (
    ConfigurationComparator,
    ConfigurationOptimizer,
    ConfigurationMerger,
    export_config_template,
    generate_config_diff,
    validate_config_environment
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core classes
    'LangSwarmConfig',
    'AgentConfig', 
    'ToolConfig',
    'WorkflowConfig',
    'MemoryConfig',
    'SecurityConfig',
    'ObservabilityConfig',
    'ServerConfig',
    
    # Enums
    'ProviderType',
    'MemoryBackend',
    'WorkflowEngine',
    'LogLevel',
    
    # Templates
    'ConfigTemplates',
    
    # Loading functions
    'ConfigurationLoader',
    'V1ConfigurationMigrator',
    'load_config',
    'load_template',
    'migrate_v1_config',
    'get_config_loader',
    
    # Validation
    'ConfigurationValidator',
    'ValidationIssue',
    'ValidationSeverity',
    'validate_config',
    'format_validation_report',
    
    # Utilities
    'ConfigurationComparator',
    'ConfigurationOptimizer', 
    'ConfigurationMerger',
    'export_config_template',
    'generate_config_diff',
    'validate_config_environment'
]

# Global configuration instance
_global_config: Optional[LangSwarmConfig] = None


def get_global_config() -> Optional[LangSwarmConfig]:
    """Get the global configuration instance"""
    return _global_config


def set_global_config(config: LangSwarmConfig):
    """Set the global configuration instance"""
    global _global_config
    _global_config = config


def initialize_config(config_path: Optional[str] = None) -> LangSwarmConfig:
    """
    Initialize the global configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Loaded configuration
    """
    config = load_config(config_path)
    set_global_config(config)
    return config


# Convenience functions for common operations
def create_simple_config(
    agent_name: str = "assistant",
    provider: ProviderType = ProviderType.OPENAI,
    model: str = "gpt-4o"
) -> LangSwarmConfig:
    """
    Create a simple configuration with one agent.
    
    Args:
        agent_name: Name of the agent
        provider: LLM provider to use
        model: Model to use
        
    Returns:
        Simple configuration
    """
    return LangSwarmConfig(
        name=f"Simple {agent_name.title()} Configuration",
        agents=[
            AgentConfig(
                id=agent_name,
                provider=provider,
                model=model,
                system_prompt=f"You are {agent_name}, a helpful AI assistant."
            )
        ]
    )


def create_development_config() -> LangSwarmConfig:
    """Create a development configuration with debug settings"""
    return ConfigTemplates.development_setup()


def create_production_config() -> LangSwarmConfig:
    """Create a production configuration with optimized settings"""
    return ConfigTemplates.production_setup()


# Error handling for configuration issues
class ConfigurationError(Exception):
    """Configuration-related error"""
    pass


# Re-export for convenience
from langswarm.core.errors import ConfigurationError, ValidationError


# =============================================================================
# V1 Backward Compatibility
# =============================================================================
# Many existing docs and user code import V1 classes from langswarm.core.config
# Re-export V1 classes here for backward compatibility
try:
    from langswarm.v1.core.config import (
        LangSwarmConfigLoader,
        WorkflowExecutor,
    )
    
    # Add to __all__ for discoverability
    __all__.extend([
        'LangSwarmConfigLoader',  # V1 compatibility
        'WorkflowExecutor',        # V1 compatibility
    ])
except ImportError:
    # V1 not available - that's okay, V2-only installations won't break
    LangSwarmConfigLoader = None
    WorkflowExecutor = None
