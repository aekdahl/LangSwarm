"""
LangSwarm Middleware System

Modern pipeline architecture with composable interceptors for request processing.
Provides clean separation of concerns, type safety, and comprehensive observability.

Usage:
    from langswarm.core.middleware import Pipeline, RequestContext
    
    # Create pipeline with interceptors
    pipeline = Pipeline([
        RoutingInterceptor(),
        ValidationInterceptor(),
        ExecutionInterceptor()
    ])
    
    # Process request
    context = RequestContext(action="tool_call", params={"id": "filesystem", "method": "read_file"})
    response = pipeline.process(context)
"""

from .interfaces import (
    IMiddlewareInterceptor,
    IMiddlewarePipeline,
    IRequestContext,
    IResponseContext,
    ResponseStatus
)

from .context import (
    RequestContext,
    ResponseContext,
    MiddlewareMetadata
)

from .pipeline import (
    Pipeline,
    PipelineBuilder,
    create_pipeline as create_legacy_pipeline,
    create_default_pipeline as create_legacy_default_pipeline
)

# Import the unified pipeline system
from .unified_pipeline import (
    create_pipeline,
    create_production_pipeline,
    create_development_pipeline,
    create_testing_pipeline,
    create_legacy_compatible_pipeline,
    get_production_config,
    get_development_config,
    get_testing_config,
    upgrade_existing_pipeline_config
)

from .interceptors import (
    BaseInterceptor,
    RoutingInterceptor,
    ValidationInterceptor,
    ExecutionInterceptor,
    ContextInterceptor,
    ErrorInterceptor,
    ObservabilityInterceptor,
    TokenTrackingInterceptor,
    create_token_tracking_interceptor
)

__all__ = [
    # Interfaces
    'IMiddlewareInterceptor',
    'IMiddlewarePipeline', 
    'IRequestContext',
    'IResponseContext',
    'ResponseStatus',
    
    # Context Objects
    'RequestContext',
    'ResponseContext',
    'MiddlewareMetadata',
    
    # Pipeline (Unified System)
    'Pipeline',
    'PipelineBuilder',
    'create_pipeline',  # New unified pipeline
    'create_production_pipeline',
    'create_development_pipeline', 
    'create_testing_pipeline',
    'create_legacy_compatible_pipeline',
    'get_production_config',
    'get_development_config',
    'get_testing_config',
    'upgrade_existing_pipeline_config',
    
    # Legacy pipeline functions (deprecated)
    'create_legacy_pipeline',
    'create_legacy_default_pipeline',
    
    # Interceptors
    'BaseInterceptor',
    'RoutingInterceptor',
    'ValidationInterceptor',
    'ExecutionInterceptor',
    'ContextInterceptor',
    'ErrorInterceptor',
    'ObservabilityInterceptor',
    'TokenTrackingInterceptor',
    'create_token_tracking_interceptor'
]
