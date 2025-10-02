"""
Enhanced Middleware Pipeline Factory with Token Tracking

Provides factory functions to create middleware pipelines with token tracking
capabilities while maintaining backward compatibility with existing code.
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


def create_enhanced_pipeline(
    enable_token_tracking: bool = True,
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True,
    token_tracking_config: Optional[Dict[str, Any]] = None,
    custom_interceptors: Optional[List] = None
) -> Pipeline:
    """
    Create an enhanced middleware pipeline with token tracking capabilities.
    
    Args:
        enable_token_tracking: Whether to include token tracking interceptor
        enable_budget_enforcement: Whether to enforce token budget limits
        enable_context_monitoring: Whether to monitor context sizes
        token_tracking_config: Additional configuration for token tracking
        custom_interceptors: Additional custom interceptors to include
    
    Returns:
        Configured Pipeline with token tracking
    """
    
    builder = PipelineBuilder()
    
    # Add standard interceptors with proper ordering
    builder.add_interceptor(ContextInterceptor(priority=100))
    builder.add_interceptor(RoutingInterceptor(priority=200))
    builder.add_interceptor(ValidationInterceptor(priority=300))
    
    # Add token tracking interceptor before execution
    if enable_token_tracking:
        token_interceptor = create_token_tracking_interceptor(
            enable_budget_enforcement=enable_budget_enforcement,
            enable_context_monitoring=enable_context_monitoring,
            priority=450  # Before execution, after validation
        )
        builder.add_interceptor(token_interceptor)
        
        logger.info(
            f"Added token tracking interceptor with budget_enforcement={enable_budget_enforcement}, "
            f"context_monitoring={enable_context_monitoring}"
        )
    
    # Add execution interceptor
    builder.add_interceptor(ExecutionInterceptor(priority=500))
    
    # Add error handling and observability
    builder.add_interceptor(ErrorInterceptor(priority=600))
    builder.add_interceptor(ObservabilityInterceptor(priority=700))
    
    # Add any custom interceptors
    if custom_interceptors:
        for interceptor in custom_interceptors:
            builder.add_interceptor(interceptor)
    
    return builder.build()


def create_production_pipeline(
    token_budget_config: Optional[Dict[str, Any]] = None,
    enable_all_monitoring: bool = True
) -> Pipeline:
    """
    Create a production-ready pipeline with comprehensive token tracking,
    budget enforcement, and monitoring.
    
    Args:
        token_budget_config: Configuration for token budget management
        enable_all_monitoring: Whether to enable all monitoring features
    
    Returns:
        Production-ready Pipeline
    """
    
    return create_enhanced_pipeline(
        enable_token_tracking=True,
        enable_budget_enforcement=bool(token_budget_config),
        enable_context_monitoring=enable_all_monitoring,
        token_tracking_config=token_budget_config
    )


def create_development_pipeline(
    enable_token_tracking: bool = True
) -> Pipeline:
    """
    Create a development pipeline with token tracking but no enforcement.
    
    Args:
        enable_token_tracking: Whether to track tokens (useful for testing)
    
    Returns:
        Development Pipeline
    """
    
    return create_enhanced_pipeline(
        enable_token_tracking=enable_token_tracking,
        enable_budget_enforcement=False,  # No enforcement in dev
        enable_context_monitoring=enable_token_tracking
    )


def create_minimal_pipeline() -> Pipeline:
    """
    Create a minimal pipeline without token tracking for maximum performance.
    
    Returns:
        Minimal Pipeline
    """
    
    return create_enhanced_pipeline(
        enable_token_tracking=False,
        enable_budget_enforcement=False,
        enable_context_monitoring=False
    )


def create_legacy_compatible_pipeline() -> Pipeline:
    """
    Create a pipeline that's compatible with existing LangSwarm v2 deployments.
    This includes token tracking but disabled by default to avoid breaking changes.
    
    Returns:
        Legacy-compatible Pipeline
    """
    
    builder = PipelineBuilder()
    
    # Standard interceptors in existing order
    builder.add_interceptor(ContextInterceptor(priority=100))
    builder.add_interceptor(RoutingInterceptor(priority=200))
    builder.add_interceptor(ValidationInterceptor(priority=300))
    builder.add_interceptor(ExecutionInterceptor(priority=500))
    builder.add_interceptor(ObservabilityInterceptor(priority=700))
    
    return builder.build()


def upgrade_pipeline_with_token_tracking(
    existing_pipeline: Pipeline,
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True
) -> Pipeline:
    """
    Upgrade an existing pipeline with token tracking capabilities.
    
    Args:
        existing_pipeline: Existing pipeline to upgrade
        enable_budget_enforcement: Whether to enable budget enforcement
        enable_context_monitoring: Whether to enable context monitoring
    
    Returns:
        Upgraded Pipeline with token tracking
    """
    
    try:
        # Get existing interceptors
        existing_interceptors = getattr(existing_pipeline, '_interceptors', [])
        
        # Create new builder
        builder = PipelineBuilder()
        
        # Add existing interceptors
        for interceptor in existing_interceptors:
            builder.add_interceptor(interceptor)
        
        # Add token tracking interceptor with appropriate priority
        token_interceptor = create_token_tracking_interceptor(
            enable_budget_enforcement=enable_budget_enforcement,
            enable_context_monitoring=enable_context_monitoring,
            priority=450  # Before execution
        )
        builder.add_interceptor(token_interceptor)
        
        logger.info("Successfully upgraded pipeline with token tracking")
        return builder.build()
        
    except Exception as e:
        logger.error(f"Failed to upgrade pipeline with token tracking: {e}")
        return existing_pipeline  # Return original pipeline if upgrade fails


# Configuration templates for common use cases
PRODUCTION_CONFIG = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "context_monitoring": True,
        "budget_limits": {
            "daily_token_limit": 1000000,
            "session_token_limit": 50000,
            "cost_limit_usd": 100.0
        },
        "alerts": {
            "token_threshold": 0.8,
            "cost_threshold": 0.8,
            "context_threshold": 0.9
        }
    }
}

DEVELOPMENT_CONFIG = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": False,
        "context_monitoring": True,
        "budget_limits": {
            "daily_token_limit": 100000,
            "session_token_limit": 10000,
            "cost_limit_usd": 10.0
        }
    }
}

TESTING_CONFIG = {
    "token_tracking": {
        "enabled": False,  # Disabled for faster tests
        "budget_enforcement": False,
        "context_monitoring": False
    }
}


def create_pipeline_from_config(config: Dict[str, Any]) -> Pipeline:
    """
    Create a pipeline from configuration dictionary.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Configured Pipeline
    """
    
    token_config = config.get("token_tracking", {})
    
    return create_enhanced_pipeline(
        enable_token_tracking=token_config.get("enabled", True),
        enable_budget_enforcement=token_config.get("budget_enforcement", False),
        enable_context_monitoring=token_config.get("context_monitoring", True),
        token_tracking_config=token_config
    )


# Backward compatibility aliases
def create_default_pipeline() -> Pipeline:
    """
    Create default pipeline with token tracking enabled but no enforcement.
    This maintains backward compatibility while adding observability.
    """
    return create_enhanced_pipeline(
        enable_token_tracking=True,
        enable_budget_enforcement=False,
        enable_context_monitoring=True
    )


def create_v2_enhanced_pipeline(config: Optional[Dict[str, Any]] = None) -> Pipeline:
    """
    Create the enhanced V2 pipeline with all features enabled.
    
    Args:
        config: Optional configuration for the pipeline
    
    Returns:
        Enhanced V2 Pipeline
    """
    
    if config:
        return create_pipeline_from_config(config)
    else:
        return create_production_pipeline()
