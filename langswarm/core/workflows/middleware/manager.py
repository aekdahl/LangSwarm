"""
Workflow Middleware Manager

Central management component for workflow middleware integration,
providing high-level API for workflow execution with full middleware support.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from langswarm.core.middleware import RequestContext, ResponseContext, ResponseStatus
from langswarm.core.errors import handle_error, ErrorContext

from .pipeline import (
    WorkflowMiddlewarePipeline, 
    WorkflowPipelineConfig,
    create_workflow_pipeline,
    create_enhanced_workflow_pipeline,
    create_production_pipeline
)
from .interceptors import WorkflowPolicy, WorkflowComplexity
from ..interfaces import WorkflowResult, WorkflowStatus, ExecutionMode, WorkflowContext
from ..engine import get_workflow_engine
from ..monitoring import get_workflow_monitor

logger = logging.getLogger(__name__)


class MiddlewareIntegrationMode(Enum):
    """Middleware integration modes"""
    DISABLED = "disabled"
    BASIC = "basic"
    ENHANCED = "enhanced"
    PRODUCTION = "production"
    CUSTOM = "custom"


@dataclass
class WorkflowExecutionContext:
    """Rich context for workflow execution with middleware"""
    workflow_id: str
    input_data: Dict[str, Any]
    execution_mode: ExecutionMode = ExecutionMode.SYNC
    context_variables: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    department: Optional[str] = None
    project_id: Optional[str] = None
    priority: str = "normal"
    timeout: Optional[timedelta] = None
    retry_attempts: int = 3
    policy_name: Optional[str] = None
    output_format: str = "standard"
    audit_level: str = "standard"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution through middleware"""
    success: bool
    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    step_count: int = 0
    parallel_steps: int = 0
    complexity: Optional[WorkflowComplexity] = None
    routing_strategy: Optional[str] = None
    validation_passed: bool = True
    audit_id: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    middleware_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class WorkflowMiddlewareManager:
    """
    Central manager for workflow middleware integration.
    
    Provides high-level API for:
    - Workflow execution with full middleware support
    - Pipeline configuration and management
    - Performance monitoring and optimization
    - Policy enforcement and compliance
    """
    
    def __init__(
        self, 
        integration_mode: MiddlewareIntegrationMode = MiddlewareIntegrationMode.ENHANCED,
        custom_pipeline: Optional[WorkflowMiddlewarePipeline] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize workflow middleware manager.
        
        Args:
            integration_mode: Level of middleware integration
            custom_pipeline: Custom pipeline to use (overrides integration_mode)
            config: Additional configuration options
        """
        self.integration_mode = integration_mode
        self.config = config or {}
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "middleware_overhead": 0.0
        }
        
        # Initialize pipeline based on mode
        self.pipeline = custom_pipeline or self._create_pipeline_for_mode(integration_mode)
        
        # Initialize components
        self.engine = get_workflow_engine()
        self.monitor = get_workflow_monitor()
        
        logger.info(f"Initialized WorkflowMiddlewareManager in {integration_mode.value} mode")
    
    def _create_pipeline_for_mode(self, mode: MiddlewareIntegrationMode) -> Optional[WorkflowMiddlewarePipeline]:
        """Create pipeline based on integration mode"""
        
        if mode == MiddlewareIntegrationMode.DISABLED:
            return None
        elif mode == MiddlewareIntegrationMode.BASIC:
            config = WorkflowPipelineConfig(
                enable_routing=True,
                enable_validation=True,
                enable_context_enrichment=False,
                enable_result_transformation=False,
                enable_audit_logging=False
            )
            return WorkflowMiddlewarePipeline(config)
        elif mode == MiddlewareIntegrationMode.ENHANCED:
            return create_enhanced_workflow_pipeline()
        elif mode == MiddlewareIntegrationMode.PRODUCTION:
            return create_production_pipeline()
        else:
            return create_workflow_pipeline()
    
    async def execute_workflow(
        self, 
        context: WorkflowExecutionContext
    ) -> WorkflowExecutionResult:
        """
        Execute workflow with full middleware integration.
        
        Args:
            context: Workflow execution context
            
        Returns:
            Workflow execution result with middleware metadata
        """
        
        start_time = time.time()
        execution_id = f"exec-{context.workflow_id}-{int(time.time() * 1000000)}"
        
        try:
            if self.integration_mode == MiddlewareIntegrationMode.DISABLED:
                # Direct execution without middleware
                result = await self._execute_direct(context, execution_id)
            else:
                # Execute through middleware pipeline
                result = await self._execute_with_middleware(context, execution_id)
            
            # Update statistics
            execution_time = time.time() - start_time
            await self._update_execution_stats(execution_time, result.success)
            
            result.execution_time = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._update_execution_stats(execution_time, False)
            
            error_context = ErrorContext(
                operation="workflow_middleware_execution",
                component="WorkflowMiddlewareManager",
                details={
                    "workflow_id": context.workflow_id,
                    "execution_id": execution_id,
                    "integration_mode": self.integration_mode.value
                }
            )
            
            # Return error result
            return WorkflowExecutionResult(
                success=False,
                workflow_id=context.workflow_id,
                execution_id=execution_id,
                status=WorkflowStatus.FAILED,
                error=e,
                execution_time=execution_time
            )
    
    async def _execute_with_middleware(
        self, 
        context: WorkflowExecutionContext, 
        execution_id: str
    ) -> WorkflowExecutionResult:
        """Execute workflow through middleware pipeline"""
        
        # Create middleware request context
        request_context = RequestContext(
            action="workflow_execution",
            params={
                "workflow_id": context.workflow_id,
                "input_data": context.input_data,
                "execution_mode": context.execution_mode.value,
                "context_variables": context.context_variables,
                "output_format": context.output_format
            },
            metadata={
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": context.request_id or execution_id,
                "department": context.department,
                "project_id": context.project_id,
                "priority": context.priority,
                "policy_name": context.policy_name,
                "audit_level": context.audit_level,
                "execution_id": execution_id,
                **context.metadata
            }
        )
        
        # Execute through pipeline
        response = await self.pipeline.process(request_context)
        
        # Convert response to workflow result
        return self._convert_response_to_result(response, context, execution_id)
    
    async def _execute_direct(
        self, 
        context: WorkflowExecutionContext, 
        execution_id: str
    ) -> WorkflowExecutionResult:
        """Execute workflow directly without middleware"""
        
        try:
            # Get workflow
            from .. import get_workflow
            workflow = await get_workflow(context.workflow_id)
            
            if not workflow:
                raise ValueError(f"Workflow {context.workflow_id} not found")
            
            # Execute workflow
            execution_context = WorkflowContext(
                workflow_id=context.workflow_id,
                input_data=context.input_data,
                variables=context.context_variables or {},
                execution_mode=context.execution_mode
            )
            
            result = await self.engine.execute_workflow(workflow, execution_context)
            
            return WorkflowExecutionResult(
                success=result.success,
                workflow_id=context.workflow_id,
                execution_id=execution_id,
                status=result.status,
                result=result.output_data,
                step_count=len(result.step_results) if result.step_results else 0
            )
            
        except Exception as e:
            return WorkflowExecutionResult(
                success=False,
                workflow_id=context.workflow_id,
                execution_id=execution_id,
                status=WorkflowStatus.FAILED,
                error=e
            )
    
    def _convert_response_to_result(
        self, 
        response: ResponseContext, 
        context: WorkflowExecutionContext, 
        execution_id: str
    ) -> WorkflowExecutionResult:
        """Convert middleware response to workflow result"""
        
        success = response.status == ResponseStatus.SUCCESS
        
        # Extract workflow result data
        result_data = response.data.get("result") if isinstance(response.data, dict) else response.data
        workflow_execution = response.data.get("workflow_execution", {}) if isinstance(response.data, dict) else {}
        performance = response.data.get("performance", {}) if isinstance(response.data, dict) else {}
        audit = response.data.get("audit", {}) if isinstance(response.data, dict) else {}
        
        return WorkflowExecutionResult(
            success=success,
            workflow_id=context.workflow_id,
            execution_id=execution_id,
            status=WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED,
            result=result_data,
            error=response.data.get("error") if not success else None,
            execution_time=performance.get("total_execution_time", 0.0),
            step_count=performance.get("step_count", 0),
            parallel_steps=performance.get("parallel_steps", 0),
            complexity=WorkflowComplexity(workflow_execution.get("complexity")) if workflow_execution.get("complexity") else None,
            routing_strategy=workflow_execution.get("routing_strategy"),
            validation_passed=response.metadata.get("validation_passed", True),
            audit_id=audit.get("trace_id"),
            performance_metrics=performance,
            middleware_metadata={
                "pipeline_execution_time": response.metadata.get("pipeline_execution_time"),
                "interceptor_count": response.metadata.get("pipeline_interceptor_count"),
                "routing_time": response.metadata.get("routing_time"),
                "validation_time": response.metadata.get("validation_time"),
                "transformation_time": response.metadata.get("transformation_time"),
                "audit_time": response.metadata.get("audit_time")
            }
        )
    
    async def _update_execution_stats(self, execution_time: float, success: bool):
        """Update execution statistics"""
        
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # Update average execution time
        total_time = (self.execution_stats["average_execution_time"] * 
                     (self.execution_stats["total_executions"] - 1) + execution_time)
        self.execution_stats["average_execution_time"] = total_time / self.execution_stats["total_executions"]
    
    async def execute_workflow_batch(
        self, 
        contexts: List[WorkflowExecutionContext],
        max_concurrent: int = 10
    ) -> List[WorkflowExecutionResult]:
        """
        Execute multiple workflows concurrently with middleware.
        
        Args:
            contexts: List of workflow execution contexts
            max_concurrent: Maximum concurrent executions
            
        Returns:
            List of workflow execution results
        """
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(context):
            async with semaphore:
                return await self.execute_workflow(context)
        
        tasks = [execute_with_semaphore(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(WorkflowExecutionResult(
                    success=False,
                    workflow_id=contexts[i].workflow_id,
                    execution_id=f"batch-error-{i}",
                    status=WorkflowStatus.FAILED,
                    error=result
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get middleware pipeline statistics"""
        
        if not self.pipeline:
            return {"integration_mode": "disabled"}
        
        pipeline_stats = self.pipeline.get_performance_stats()
        
        return {
            "integration_mode": self.integration_mode.value,
            "pipeline_stats": pipeline_stats,
            "execution_stats": self.execution_stats,
            "interceptor_count": self.pipeline.interceptor_count,
            "middleware_overhead": self._calculate_middleware_overhead()
        }
    
    def _calculate_middleware_overhead(self) -> float:
        """Calculate middleware overhead percentage"""
        
        if not self.pipeline or self.execution_stats["total_executions"] == 0:
            return 0.0
        
        # This is a simplified calculation
        # In practice, you'd compare with direct execution times
        pipeline_stats = self.pipeline.get_performance_stats()
        return max(0.0, pipeline_stats.get("average_execution_time", 0.0) - 
                  self.execution_stats["average_execution_time"])
    
    def reconfigure_pipeline(
        self, 
        new_mode: MiddlewareIntegrationMode,
        custom_pipeline: Optional[WorkflowMiddlewarePipeline] = None
    ):
        """Reconfigure middleware pipeline"""
        
        self.integration_mode = new_mode
        self.pipeline = custom_pipeline or self._create_pipeline_for_mode(new_mode)
        
        logger.info(f"Reconfigured WorkflowMiddlewareManager to {new_mode.value} mode")
    
    def add_custom_interceptor(self, interceptor, position: str = "end"):
        """Add custom interceptor to pipeline"""
        
        if self.pipeline:
            self.pipeline.add_custom_interceptor(interceptor, position)
            logger.info(f"Added custom interceptor {interceptor.name} to pipeline")
        else:
            logger.warning("Cannot add interceptor - middleware integration is disabled")


# Factory functions for common configurations
def create_development_manager() -> WorkflowMiddlewareManager:
    """Create development-friendly workflow middleware manager"""
    
    from .pipeline import create_development_pipeline
    pipeline = create_development_pipeline()
    
    return WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.CUSTOM,
        custom_pipeline=pipeline
    )


def create_production_manager() -> WorkflowMiddlewareManager:
    """Create production-ready workflow middleware manager"""
    
    return WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.PRODUCTION
    )


def create_performance_optimized_manager() -> WorkflowMiddlewareManager:
    """Create performance-optimized workflow middleware manager"""
    
    pipeline = create_enhanced_workflow_pipeline(performance_optimized=True)
    
    return WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.CUSTOM,
        custom_pipeline=pipeline
    )


# Global manager instance
_default_manager = None


def get_workflow_middleware_manager() -> WorkflowMiddlewareManager:
    """Get the default workflow middleware manager"""
    
    global _default_manager
    if _default_manager is None:
        _default_manager = WorkflowMiddlewareManager()
    
    return _default_manager


def set_workflow_middleware_manager(manager: WorkflowMiddlewareManager):
    """Set the default workflow middleware manager"""
    
    global _default_manager
    _default_manager = manager


# Convenience functions
async def execute_workflow_with_middleware(
    workflow_id: str,
    input_data: Dict[str, Any],
    execution_mode: ExecutionMode = ExecutionMode.SYNC,
    **kwargs
) -> WorkflowExecutionResult:
    """
    Convenience function to execute workflow with middleware.
    
    Args:
        workflow_id: ID of workflow to execute
        input_data: Input data for workflow
        execution_mode: Execution mode
        **kwargs: Additional context parameters
        
    Returns:
        Workflow execution result
    """
    
    context = WorkflowExecutionContext(
        workflow_id=workflow_id,
        input_data=input_data,
        execution_mode=execution_mode,
        **kwargs
    )
    
    manager = get_workflow_middleware_manager()
    return await manager.execute_workflow(context)
