"""
LangSwarm Unified Pipeline System

A single, comprehensive pipeline that includes all capabilities by default,
with configuration-driven feature enablement rather than multiple pipeline types.
"""

from typing import Optional, Dict, Any, List
import logging

from .pipeline import Pipeline, PipelineBuilder
from .interceptors import (
    ContextInterceptor,
    RoutingInterceptor,
    ValidationInterceptor,
    ExecutionInterceptor,
    ErrorInterceptor,
    ObservabilityInterceptor,
    TokenTrackingInterceptor,
    create_token_tracking_interceptor
)

logger = logging.getLogger(__name__)


class UnifiedPipelineConfig:
    """Configuration for the unified pipeline system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Default configuration - all features available but sensibly configured
        self.defaults = {
            "token_tracking": {
                "enabled": True,
                "budget_enforcement": False,  # Safe default
                "context_monitoring": True,
                "performance_tracking": True
            },
            "observability": {
                "enabled": True,
                "metrics": True,
                "tracing": True,
                "logging": True
            },
            "error_handling": {
                "enabled": True,
                "retry_logic": True,
                "graceful_degradation": True
            },
            "validation": {
                "enabled": True,
                "strict_mode": False
            }
        }
        
        # Merge user config with defaults
        self._merge_config()
    
    def _merge_config(self):
        """Merge user configuration with defaults"""
        for section, default_values in self.defaults.items():
            if section not in self.config:
                self.config[section] = {}
            
            for key, default_value in default_values.items():
                if key not in self.config[section]:
                    self.config[section][key] = default_value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(section, {}).get(key, default)
    
    def is_enabled(self, section: str, key: str = "enabled") -> bool:
        """Check if a feature is enabled"""
        return self.get(section, key, False)


def create_pipeline(config: Optional[Dict[str, Any]] = None) -> Pipeline:
    """
    Create the unified LangSwarm V2 pipeline with all capabilities.
    
    This is the ONE pipeline creation function. All features are included
    by default and can be enabled/disabled via configuration.
    
    Args:
        config: Configuration dictionary to control feature enablement
    
    Returns:
        Fully-capable Pipeline configured according to settings
    """
    
    pipeline_config = UnifiedPipelineConfig(config)
    builder = PipelineBuilder()
    
    # Core interceptors - always included
    builder.add_interceptor(ContextInterceptor(priority=100))
    builder.add_interceptor(RoutingInterceptor(priority=200))
    
    # Validation - configurable
    if pipeline_config.is_enabled("validation"):
        validation_config = pipeline_config.config.get("validation", {})
        builder.add_interceptor(ValidationInterceptor(
            priority=300,
            strict_mode=validation_config.get("strict_mode", False)
        ))
    
    # Token tracking - included by default, configurable
    if pipeline_config.is_enabled("token_tracking"):
        token_config = pipeline_config.config.get("token_tracking", {})
        token_interceptor = create_token_tracking_interceptor(
            enable_budget_enforcement=token_config.get("budget_enforcement", False),
            enable_context_monitoring=token_config.get("context_monitoring", True),
            priority=450
        )
        builder.add_interceptor(token_interceptor)
        
        logger.info(f"Token tracking enabled with budget_enforcement={token_config.get('budget_enforcement', False)}")
    
    # Execution - always included
    builder.add_interceptor(ExecutionInterceptor(priority=500))
    
    # Error handling - configurable  
    if pipeline_config.is_enabled("error_handling"):
        error_config = pipeline_config.config.get("error_handling", {})
        builder.add_interceptor(ErrorInterceptor(
            priority=600,
            enable_retry=error_config.get("retry_logic", True),
            graceful_degradation=error_config.get("graceful_degradation", True)
        ))
    
    # Observability - configurable
    if pipeline_config.is_enabled("observability"):
        builder.add_interceptor(ObservabilityInterceptor(priority=700))
    
    return builder.build()


# Environment-specific configurations (just config, not different pipelines!)

def get_production_config() -> Dict[str, Any]:
    """Production configuration - all features enabled with enforcement"""
    return {
        "token_tracking": {
            "enabled": True,
            "budget_enforcement": True,  # Enable enforcement in production
            "context_monitoring": True,
            "performance_tracking": True
        },
        "observability": {
            "enabled": True,
            "metrics": True,
            "tracing": True,
            "logging": True
        },
        "error_handling": {
            "enabled": True,
            "retry_logic": True,
            "graceful_degradation": True
        },
        "validation": {
            "enabled": True,
            "strict_mode": True  # Strict validation in production
        }
    }


def get_development_config() -> Dict[str, Any]:
    """Development configuration - tracking enabled, no enforcement"""
    return {
        "token_tracking": {
            "enabled": True,
            "budget_enforcement": False,  # No enforcement in dev
            "context_monitoring": True,
            "performance_tracking": True
        },
        "observability": {
            "enabled": True,
            "metrics": True,
            "tracing": False,  # Less overhead in dev
            "logging": True
        },
        "error_handling": {
            "enabled": True,
            "retry_logic": False,  # Fail fast in dev
            "graceful_degradation": False
        },
        "validation": {
            "enabled": True,
            "strict_mode": False  # Lenient validation in dev
        }
    }


def get_testing_config() -> Dict[str, Any]:
    """Testing configuration - minimal overhead for CI/CD"""
    return {
        "token_tracking": {
            "enabled": False,  # Disable for faster tests
            "budget_enforcement": False,
            "context_monitoring": False,
            "performance_tracking": False
        },
        "observability": {
            "enabled": False,  # Minimal logging for tests
            "metrics": False,
            "tracing": False,
            "logging": False
        },
        "error_handling": {
            "enabled": True,
            "retry_logic": False,
            "graceful_degradation": False
        },
        "validation": {
            "enabled": True,
            "strict_mode": True  # Strict validation for tests
        }
    }


# Convenience functions for common patterns

def create_production_pipeline() -> Pipeline:
    """Create pipeline with production configuration"""
    return create_pipeline(get_production_config())


def create_development_pipeline() -> Pipeline:
    """Create pipeline with development configuration"""
    return create_pipeline(get_development_config())


def create_testing_pipeline() -> Pipeline:
    """Create pipeline with testing configuration"""
    return create_pipeline(get_testing_config())


# Migration support for existing deployments

def create_legacy_compatible_pipeline() -> Pipeline:
    """
    Create a pipeline that matches the original V2 behavior.
    Token tracking available but disabled by default.
    """
    legacy_config = {
        "token_tracking": {
            "enabled": False,  # Disabled for legacy compatibility
            "budget_enforcement": False,
            "context_monitoring": False
        },
        "observability": {
            "enabled": True,
            "metrics": True,
            "tracing": True,
            "logging": True
        },
        "error_handling": {
            "enabled": True,
            "retry_logic": True,
            "graceful_degradation": True
        },
        "validation": {
            "enabled": True,
            "strict_mode": False
        }
    }
    
    return create_pipeline(legacy_config)


def upgrade_existing_pipeline_config(
    current_config: Dict[str, Any],
    enable_token_tracking: bool = True,
    enable_budget_enforcement: bool = False
) -> Dict[str, Any]:
    """
    Upgrade existing pipeline configuration to include token tracking.
    
    Args:
        current_config: Existing configuration
        enable_token_tracking: Whether to enable token tracking
        enable_budget_enforcement: Whether to enable budget enforcement
    
    Returns:
        Updated configuration with token tracking
    """
    
    updated_config = current_config.copy()
    
    # Add token tracking configuration
    if "token_tracking" not in updated_config:
        updated_config["token_tracking"] = {}
    
    updated_config["token_tracking"].update({
        "enabled": enable_token_tracking,
        "budget_enforcement": enable_budget_enforcement,
        "context_monitoring": enable_token_tracking,
        "performance_tracking": enable_token_tracking
    })
    
    return updated_config


# Backward compatibility aliases (deprecated but functional)

def create_enhanced_pipeline(
    enable_token_tracking: bool = True,
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True,
    **kwargs
) -> Pipeline:
    """
    DEPRECATED: Use create_pipeline() with configuration instead.
    
    This function exists for backward compatibility only.
    """
    
    import warnings
    warnings.warn(
        "create_enhanced_pipeline() is deprecated. Use create_pipeline() with configuration instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    config = {
        "token_tracking": {
            "enabled": enable_token_tracking,
            "budget_enforcement": enable_budget_enforcement,
            "context_monitoring": enable_context_monitoring
        }
    }
    
    return create_pipeline(config)


# The correct way to use the pipeline system

def get_recommended_usage_examples():
    """Examples of how to properly use the unified pipeline system"""
    
    examples = {
        "basic_usage": """
# Default pipeline with sensible defaults
pipeline = create_pipeline()

# Token tracking enabled, budget enforcement disabled
# All other features enabled with safe defaults
""",
        
        "custom_configuration": """
# Custom configuration
config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,  # Enable enforcement
        "context_monitoring": True
    },
    "observability": {
        "enabled": True,
        "tracing": False  # Disable tracing for performance
    }
}

pipeline = create_pipeline(config)
""",
        
        "environment_specific": """
# Production
pipeline = create_pipeline(get_production_config())

# Development  
pipeline = create_pipeline(get_development_config())

# Testing
pipeline = create_pipeline(get_testing_config())
""",
        
        "migration_from_legacy": """
# Current legacy deployment
old_config = {...}  # Your existing config

# Upgrade to include token tracking
new_config = upgrade_existing_pipeline_config(
    old_config,
    enable_token_tracking=True,
    enable_budget_enforcement=False  # Start safe
)

pipeline = create_pipeline(new_config)
""",
        
        "runtime_configuration": """
# Create pipeline with default config
pipeline = create_pipeline()

# Update configuration at runtime
pipeline.configure({
    "token_tracking": {
        "budget_enforcement": True  # Enable enforcement later
    }
})
"""
    }
    
    return examples
