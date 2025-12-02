"""
LangSwarm V2 Workflow System

Modern, simplified workflow orchestration system for LangSwarm V2.
Provides clean interfaces, fluent builder pattern, and comprehensive
execution engine while maintaining full backward compatibility.

Key Features:
- Clean, type-safe interfaces
- Fluent workflow builder API  
- Multiple execution modes (sync, async, streaming, parallel)
- Integration with V2 middleware and error handling
- YAML compatibility layer
- Comprehensive monitoring and debugging
"""

from typing import List

# Core interfaces
from .interfaces import (
    # Enums
    WorkflowStatus,
    StepStatus, 
    ExecutionMode,
    StepType,
    
    # Data classes
    WorkflowContext,
    WorkflowResult,
    StepResult,
    
    # Interfaces
    IWorkflow,
    IWorkflowStep,
    IWorkflowExecution,
    IWorkflowEngine,
    IWorkflowRegistry,
    IWorkflowValidator,
    IWorkflowBuilder,
    IWorkflowMonitor,
    
    # Type aliases
    WorkflowInput,
    WorkflowOutput,
    StepInput,
    StepOutput,
    StepExecutor,
    ConditionEvaluator,
    DataTransformer,
    ValidationRule,
    WorkflowEvent,
    StepEvent
)

# Base implementations
from .base import (
    BaseWorkflowStep,
    AgentStep,
    ToolStep,
    ConditionStep,
    TransformStep,
    BaseWorkflow,
    WorkflowExecution,
    WorkflowRegistry,
    get_workflow_registry
)

# Execution engine
from .engine import (
    WorkflowExecutionEngine,
    get_workflow_engine
)

# Backward compatibility alias
WorkflowExecutor = WorkflowExecutionEngine

# Builder pattern
from .builder import (
    WorkflowBuilder,
    LinearWorkflowBuilder,
    ParallelWorkflowBuilder,
    create_workflow,
    create_linear_workflow,
    create_parallel_workflow,
    create_simple_workflow,
    create_analysis_workflow,
    create_approval_workflow
)

# YAML compatibility (Phase 2)
from .yaml_parser import (
    YAMLWorkflowParser,
    YAMLWorkflowCompatibility,
    get_yaml_compatibility,
    load_yaml_workflows,
    migrate_yaml_workflows
)

# Monitoring and debugging (Phase 2)
from .monitoring import (
    WorkflowMonitor,
    WorkflowDebugger,
    ExecutionMetrics,
    WorkflowMetrics,
    SystemMetrics,
    get_workflow_monitor,
    get_workflow_debugger
)

# Middleware integration (Phase 2)
from .middleware_integration import (
    WorkflowMiddlewareRequest,
    WorkflowMiddlewareResponse,
    WorkflowExecutionMiddleware,
    WorkflowContextMiddleware,
    WorkflowErrorMiddleware,
    WorkflowMetricsMiddleware,
    WorkflowMiddlewareManager,
    get_workflow_middleware_manager,
    execute_workflow_with_middleware
)

# Convenience functions for common operations
async def register_workflow(workflow: IWorkflow) -> bool:
    """Register a workflow in the global registry"""
    registry = get_workflow_registry()
    return await registry.register_workflow(workflow)

async def get_workflow(workflow_id: str) -> IWorkflow:
    """Get a workflow from the global registry"""
    registry = get_workflow_registry()
    workflow = await registry.get_workflow(workflow_id)
    if not workflow:
        raise ValueError(f"Workflow '{workflow_id}' not found")
    return workflow

async def execute_workflow(
    workflow_id: str,
    input_data: WorkflowInput,
    execution_mode: ExecutionMode = ExecutionMode.SYNC
) -> WorkflowResult:
    """Execute a registered workflow by ID"""
    workflow = await get_workflow(workflow_id)
    engine = get_workflow_engine()
    
    result = await engine.execute_workflow(workflow, input_data, execution_mode)
    
    if isinstance(result, IWorkflowExecution):
        # Async execution, wait for completion
        return await result.wait_for_completion()
    else:
        # Sync execution, return result directly
        return result

async def execute_workflow_stream(
    workflow_id: str,
    input_data: WorkflowInput
):
    """Execute a workflow with streaming results"""
    workflow = await get_workflow(workflow_id)
    engine = get_workflow_engine()
    
    async for result in engine.execute_workflow_stream(workflow, input_data):
        yield result

async def list_workflows() -> List[IWorkflow]:
    """List all registered workflows"""
    registry = get_workflow_registry()
    return await registry.list_workflows()

async def list_executions(
    workflow_id: str = None,
    status: WorkflowStatus = None,
    limit: int = 100
) -> List[IWorkflowExecution]:
    """List workflow executions"""
    engine = get_workflow_engine()
    return await engine.list_executions(workflow_id, status, limit)

# Package metadata
__version__ = "2.0.0"
__author__ = "LangSwarm Team"
__description__ = "Modern workflow orchestration for LangSwarm V2"

# Public API
__all__ = [
    # Enums
    "WorkflowStatus",
    "StepStatus", 
    "ExecutionMode",
    "StepType",
    
    # Data classes
    "WorkflowContext",
    "WorkflowResult",
    "StepResult",
    
    # Interfaces
    "IWorkflow",
    "IWorkflowStep",
    "IWorkflowExecution",
    "IWorkflowEngine",
    "IWorkflowRegistry",
    "IWorkflowValidator",
    "IWorkflowBuilder",
    "IWorkflowMonitor",
    
    # Base implementations
    "BaseWorkflowStep",
    "AgentStep",
    "ToolStep",
    "ConditionStep",
    "TransformStep",
    "BaseWorkflow",
    "WorkflowExecution",
    "WorkflowRegistry",
    
    # Engine
    "WorkflowExecutionEngine",
    "WorkflowExecutor",  # Alias for backward compatibility
    
    # Builders
    "WorkflowBuilder",
    "LinearWorkflowBuilder", 
    "ParallelWorkflowBuilder",
    
    # Factory functions
    "create_workflow",
    "create_linear_workflow",
    "create_parallel_workflow",
    "create_simple_workflow",
    "create_analysis_workflow",
    "create_approval_workflow",
    
    # Registry functions
    "get_workflow_registry",
    "get_workflow_engine",
    
    # Convenience functions
    "register_workflow",
    "get_workflow",
    "execute_workflow",
    "execute_workflow_stream",
    "list_workflows",
    "list_executions",
    
    # YAML compatibility (Phase 2)
    "YAMLWorkflowParser",
    "YAMLWorkflowCompatibility",
    "get_yaml_compatibility",
    "load_yaml_workflows",
    "migrate_yaml_workflows",
    
    # Monitoring and debugging (Phase 2)
    "WorkflowMonitor",
    "WorkflowDebugger",
    "ExecutionMetrics",
    "WorkflowMetrics",
    "SystemMetrics",
    "get_workflow_monitor",
    "get_workflow_debugger",
    
    # Middleware integration (Phase 2)
    "WorkflowMiddlewareRequest",
    "WorkflowMiddlewareResponse",
    "WorkflowExecutionMiddleware",
    "WorkflowContextMiddleware",
    "WorkflowErrorMiddleware",
    "WorkflowMetricsMiddleware",
    "WorkflowMiddlewareManager",
    "get_workflow_middleware_manager",
    "execute_workflow_with_middleware",
    
    # Type aliases
    "WorkflowInput",
    "WorkflowOutput",
    "StepInput",
    "StepOutput",
    "StepExecutor",
    "ConditionEvaluator",
    "DataTransformer",
    "ValidationRule",
    "WorkflowEvent",
    "StepEvent"
]
