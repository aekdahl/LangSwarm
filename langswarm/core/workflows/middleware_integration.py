"""
Workflow Middleware Integration for LangSwarm V2

Integrates the V2 workflow system with the V2 middleware pipeline
to provide comprehensive request routing, context management,
error handling, and observability.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .interfaces import IWorkflow, IWorkflowStep, WorkflowContext, WorkflowResult, StepResult
from .engine import get_workflow_engine
from .monitoring import get_workflow_monitor, get_workflow_debugger

# Import V2 middleware components
try:
    from langswarm.core.middleware import (
        IMiddleware, IMiddlewareRequest, IMiddlewareResponse,
        MiddlewareContext, get_middleware_pipeline
    )
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    # Define minimal interfaces for when middleware isn't available
    class IMiddleware:
        pass
    
    class IMiddlewareRequest:
        pass
    
    class IMiddlewareResponse:
        pass
    
    class MiddlewareContext:
        pass

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMiddlewareRequest(IMiddlewareRequest):
    """Middleware request for workflow execution"""
    workflow_id: str
    input_data: Dict[str, Any]
    execution_mode: str = "sync"
    context_variables: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @property
    def request_type(self) -> str:
        return "workflow_execution"


@dataclass
class WorkflowMiddlewareResponse(IMiddlewareResponse):
    """Middleware response for workflow execution"""
    result: Optional[WorkflowResult] = None
    execution_id: Optional[str] = None
    success: bool = False
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    @property
    def response_type(self) -> str:
        return "workflow_result"


class WorkflowExecutionMiddleware(IMiddleware):
    """
    Middleware for workflow execution that provides:
    - Request validation and preprocessing
    - Workflow execution coordination
    - Response processing and formatting
    - Error handling and recovery
    - Performance monitoring
    """
    
    def __init__(self):
        self.engine = get_workflow_engine()
        self.monitor = get_workflow_monitor()
        self.debugger = get_workflow_debugger()
        self.logger = logging.getLogger(__name__)
    
    async def process(
        self,
        request: IMiddlewareRequest,
        context: MiddlewareContext,
        next_middleware: callable
    ) -> IMiddlewareResponse:
        """Process workflow execution request"""
        
        # Check if this is a workflow request
        if not isinstance(request, WorkflowMiddlewareRequest):
            # Not a workflow request, pass to next middleware
            return await next_middleware(request, context)
        
        start_time = time.time()
        
        try:
            # Validate workflow request
            validation_result = await self._validate_request(request, context)
            if not validation_result["valid"]:
                return WorkflowMiddlewareResponse(
                    success=False,
                    error=ValueError(validation_result["error"]),
                    execution_time=time.time() - start_time
                )
            
            # Get workflow
            from . import get_workflow
            workflow = await get_workflow(request.workflow_id)
            
            # Prepare execution
            execution_mode = self._parse_execution_mode(request.execution_mode)
            
            # Execute workflow
            result = await self._execute_workflow(
                workflow,
                request.input_data,
                execution_mode,
                request.context_variables,
                context
            )
            
            execution_time = time.time() - start_time
            
            # Create response
            if isinstance(result, WorkflowResult):
                # Sync execution
                response = WorkflowMiddlewareResponse(
                    result=result,
                    execution_id=result.execution_id,
                    success=result.success,
                    execution_time=execution_time,
                    metadata={
                        "workflow_id": request.workflow_id,
                        "execution_mode": request.execution_mode,
                        "step_count": len(result.step_results) if result.step_results else 0
                    }
                )
            else:
                # Async execution - result is IWorkflowExecution
                response = WorkflowMiddlewareResponse(
                    execution_id=result.execution_id,
                    success=True,
                    execution_time=execution_time,
                    metadata={
                        "workflow_id": request.workflow_id,
                        "execution_mode": request.execution_mode,
                        "status": "async_started"
                    }
                )
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Workflow execution failed: {e}")
            
            return WorkflowMiddlewareResponse(
                success=False,
                error=e,
                execution_time=execution_time,
                metadata={
                    "workflow_id": request.workflow_id,
                    "error_type": type(e).__name__
                }
            )
    
    async def _validate_request(self, request: WorkflowMiddlewareRequest, context: MiddlewareContext) -> Dict[str, Any]:
        """Validate workflow execution request"""
        
        if not request.workflow_id:
            return {"valid": False, "error": "Workflow ID is required"}
        
        if not isinstance(request.input_data, dict):
            return {"valid": False, "error": "Input data must be a dictionary"}
        
        # Validate execution mode
        valid_modes = ["sync", "async", "streaming", "parallel"]
        if request.execution_mode not in valid_modes:
            return {"valid": False, "error": f"Invalid execution mode. Must be one of: {valid_modes}"}
        
        # Check if workflow exists
        from . import get_workflow_registry
        registry = get_workflow_registry()
        if not await registry.workflow_exists(request.workflow_id):
            return {"valid": False, "error": f"Workflow '{request.workflow_id}' not found"}
        
        return {"valid": True}
    
    def _parse_execution_mode(self, mode_str: str):
        """Parse execution mode string to enum"""
        from .interfaces import ExecutionMode
        
        mode_map = {
            "sync": ExecutionMode.SYNC,
            "async": ExecutionMode.ASYNC,
            "streaming": ExecutionMode.STREAMING,
            "parallel": ExecutionMode.PARALLEL
        }
        
        return mode_map.get(mode_str, ExecutionMode.SYNC)
    
    async def _execute_workflow(
        self,
        workflow: IWorkflow,
        input_data: Dict[str, Any],
        execution_mode,
        context_variables: Optional[Dict[str, Any]],
        middleware_context: MiddlewareContext
    ):
        """Execute workflow with monitoring integration"""
        
        # Create workflow execution
        result = await self.engine.execute_workflow(
            workflow,
            input_data,
            execution_mode,
            context_variables
        )
        
        # Track execution if monitoring is enabled
        if hasattr(result, 'execution_id') and hasattr(result, 'workflow_id'):
            # Async execution
            await self.monitor.track_execution_start(result)
        elif isinstance(result, WorkflowResult):
            # Sync execution - create dummy execution for tracking
            class DummyExecution:
                def __init__(self, execution_id: str, workflow_id: str):
                    self.execution_id = execution_id
                    self.workflow_id = workflow_id
                    self.start_time = datetime.now(timezone.utc)
            
            from datetime import datetime, timezone
            dummy_exec = DummyExecution(result.execution_id, workflow.workflow_id)
            await self.monitor.track_execution_start(dummy_exec)
            await self.monitor.track_execution_end(dummy_exec, result)
        
        return result


class WorkflowContextMiddleware(IMiddleware):
    """
    Middleware for managing workflow context and state.
    
    Provides:
    - Context variable management
    - Session state handling
    - Cross-workflow data sharing
    - Context cleanup and optimization
    """
    
    def __init__(self):
        self.context_store: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def process(
        self,
        request: IMiddlewareRequest,
        context: MiddlewareContext,
        next_middleware: callable
    ) -> IMiddlewareResponse:
        """Process request with context management"""
        
        # Add workflow context capabilities to middleware context
        if hasattr(context, 'workflow'):
            context.workflow_context = self._create_workflow_context(context)
        
        # Process request
        response = await next_middleware(request, context)
        
        # Clean up context if needed
        await self._cleanup_context(context)
        
        return response
    
    def _create_workflow_context(self, context: MiddlewareContext) -> Dict[str, Any]:
        """Create workflow-specific context"""
        return {
            "middleware_context": context,
            "request_id": getattr(context, 'request_id', None),
            "user_id": getattr(context, 'user_id', None),
            "session_id": getattr(context, 'session_id', None),
        }
    
    async def _cleanup_context(self, context: MiddlewareContext):
        """Clean up context after request processing"""
        # Implement context cleanup logic here
        pass


class WorkflowErrorMiddleware(IMiddleware):
    """
    Middleware for comprehensive workflow error handling.
    
    Provides:
    - Error classification and handling
    - Retry logic for transient failures
    - Error reporting and logging
    - Recovery strategies
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts: Dict[str, int] = {}
    
    async def process(
        self,
        request: IMiddlewareRequest,
        context: MiddlewareContext,
        next_middleware: callable
    ) -> IMiddlewareResponse:
        """Process request with error handling"""
        
        try:
            response = await next_middleware(request, context)
            
            # Check for workflow errors in response
            if isinstance(response, WorkflowMiddlewareResponse) and not response.success:
                await self._handle_workflow_error(request, response, context)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Middleware error: {e}")
            
            # Create error response
            return WorkflowMiddlewareResponse(
                success=False,
                error=e,
                metadata={
                    "error_type": type(e).__name__,
                    "middleware_error": True
                }
            )
    
    async def _handle_workflow_error(
        self,
        request: IMiddlewareRequest,
        response: WorkflowMiddlewareResponse,
        context: MiddlewareContext
    ):
        """Handle workflow execution errors"""
        
        if isinstance(request, WorkflowMiddlewareRequest):
            error_key = f"{request.workflow_id}_{type(response.error).__name__}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            self.logger.warning(
                f"Workflow {request.workflow_id} failed: {response.error} "
                f"(count: {self.error_counts[error_key]})"
            )


class WorkflowMetricsMiddleware(IMiddleware):
    """
    Middleware for collecting workflow performance metrics.
    
    Provides:
    - Request/response timing
    - Throughput measurement
    - Resource usage tracking
    - Performance analytics
    """
    
    def __init__(self):
        self.monitor = get_workflow_monitor()
        self.request_count = 0
        self.total_execution_time = 0.0
        self.logger = logging.getLogger(__name__)
    
    async def process(
        self,
        request: IMiddlewareRequest,
        context: MiddlewareContext,
        next_middleware: callable
    ) -> IMiddlewareResponse:
        """Process request with metrics collection"""
        
        start_time = time.time()
        
        # Process request
        response = await next_middleware(request, context)
        
        execution_time = time.time() - start_time
        
        # Collect metrics
        self.request_count += 1
        self.total_execution_time += execution_time
        
        # Add timing metadata to response
        if hasattr(response, 'metadata') and response.metadata is not None:
            response.metadata['middleware_execution_time'] = execution_time
            response.metadata['total_requests'] = self.request_count
            response.metadata['average_request_time'] = self.total_execution_time / self.request_count
        
        return response


class WorkflowMiddlewareManager:
    """
    Manager for workflow-specific middleware components.
    
    Coordinates:
    - Middleware registration and configuration
    - Pipeline setup and management
    - Integration with V2 middleware system
    """
    
    def __init__(self):
        self.middlewares = [
            WorkflowMetricsMiddleware(),
            WorkflowContextMiddleware(),
            WorkflowErrorMiddleware(),
            WorkflowExecutionMiddleware(),
        ]
        self.logger = logging.getLogger(__name__)
    
    async def setup_workflow_pipeline(self):
        """Setup workflow middleware pipeline"""
        if not MIDDLEWARE_AVAILABLE:
            self.logger.warning("V2 middleware system not available, using standalone mode")
            return
        
        try:
            pipeline = get_middleware_pipeline()
            
            # Register workflow middlewares
            for middleware in self.middlewares:
                await pipeline.add_middleware(middleware)
            
            self.logger.info(f"Registered {len(self.middlewares)} workflow middlewares")
            
        except Exception as e:
            self.logger.error(f"Failed to setup workflow middleware pipeline: {e}")
    
    async def execute_workflow_with_middleware(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        execution_mode: str = "sync",
        context_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> WorkflowMiddlewareResponse:
        """Execute workflow through middleware pipeline"""
        
        # Create workflow request
        request = WorkflowMiddlewareRequest(
            workflow_id=workflow_id,
            input_data=input_data,
            execution_mode=execution_mode,
            context_variables=context_variables,
            request_id=request_id,
            user_id=user_id
        )
        
        # Create middleware context
        context = MiddlewareContext() if MIDDLEWARE_AVAILABLE else type('Context', (), {})()
        
        # Execute through middleware pipeline
        if MIDDLEWARE_AVAILABLE:
            try:
                pipeline = get_middleware_pipeline()
                response = await pipeline.process(request, context)
                return response
            except Exception as e:
                self.logger.error(f"Middleware pipeline execution failed: {e}")
                # Fallback to direct execution
                return await self._execute_directly(request, context)
        else:
            # Direct execution when middleware not available
            return await self._execute_directly(request, context)
    
    async def _execute_directly(self, request: WorkflowMiddlewareRequest, context) -> WorkflowMiddlewareResponse:
        """Execute workflow directly without full middleware pipeline"""
        
        execution_middleware = WorkflowExecutionMiddleware()
        
        # Simple middleware chain
        async def next_middleware(req, ctx):
            return WorkflowMiddlewareResponse(success=True)
        
        return await execution_middleware.process(request, context, next_middleware)


# Global middleware manager
_workflow_middleware_manager = WorkflowMiddlewareManager()


def get_workflow_middleware_manager() -> WorkflowMiddlewareManager:
    """Get the global workflow middleware manager"""
    return _workflow_middleware_manager


# Convenience function for workflow execution with middleware
async def execute_workflow_with_middleware(
    workflow_id: str,
    input_data: Dict[str, Any],
    execution_mode: str = "sync",
    context_variables: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> WorkflowMiddlewareResponse:
    """Execute workflow through the middleware pipeline"""
    manager = get_workflow_middleware_manager()
    return await manager.execute_workflow_with_middleware(
        workflow_id=workflow_id,
        input_data=input_data,
        execution_mode=execution_mode,
        context_variables=context_variables,
        user_id=user_id,
        request_id=request_id
    )
