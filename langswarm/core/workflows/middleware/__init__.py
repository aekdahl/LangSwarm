"""
Workflow V2 Middleware Integration Package

Advanced middleware integration for the V2 workflow system providing:
- Workflow-specific interceptors and policies
- Request routing based on complexity and type
- Context enrichment and validation
- Result transformation and formatting
- Comprehensive audit and compliance logging

Usage:
    from langswarm.core.workflows.middleware import (
        create_workflow_pipeline,
        WorkflowMiddlewareManager,
        WorkflowPolicy
    )
    
    # Create workflow-enhanced pipeline
    pipeline = create_workflow_pipeline()
    
    # Execute workflow with middleware
    manager = WorkflowMiddlewareManager()
    result = await manager.execute_workflow_with_middleware(
        workflow_id="my_workflow",
        input_data={"key": "value"},
        execution_mode="async"
    )
"""

from .interceptors import (
    WorkflowRoutingInterceptor,
    WorkflowValidationInterceptor,
    WorkflowContextEnrichmentInterceptor,
    WorkflowResultTransformationInterceptor,
    WorkflowAuditInterceptor,
    WorkflowRequestType,
    WorkflowComplexity,
    WorkflowPolicy,
    WorkflowRoutingConfig,
    create_workflow_interceptors
)

from .pipeline import (
    WorkflowMiddlewarePipeline,
    create_workflow_pipeline,
    create_enhanced_workflow_pipeline
)

from .manager import (
    WorkflowMiddlewareManager,
    WorkflowExecutionContext,
    WorkflowExecutionResult
)

from .router import (
    WorkflowRequestRouter,
    RouteConfiguration,
    create_workflow_router
)

from .policies import (
    PolicyManager,
    SecurityPolicy,
    CompliancePolicy,
    create_default_policies
)

__all__ = [
    # Core interceptors
    'WorkflowRoutingInterceptor',
    'WorkflowValidationInterceptor', 
    'WorkflowContextEnrichmentInterceptor',
    'WorkflowResultTransformationInterceptor',
    'WorkflowAuditInterceptor',
    
    # Data types and enums
    'WorkflowRequestType',
    'WorkflowComplexity',
    'WorkflowPolicy',
    'WorkflowRoutingConfig',
    
    # Pipeline components
    'WorkflowMiddlewarePipeline',
    'create_workflow_pipeline',
    'create_enhanced_workflow_pipeline',
    
    # Management components
    'WorkflowMiddlewareManager',
    'WorkflowExecutionContext',
    'WorkflowExecutionResult',
    
    # Routing components
    'WorkflowRequestRouter',
    'RouteConfiguration',
    'create_workflow_router',
    
    # Policy components
    'PolicyManager',
    'SecurityPolicy',
    'CompliancePolicy',
    'create_default_policies',
    
    # Factory functions
    'create_workflow_interceptors'
]
