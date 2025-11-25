"""
Workflow Execution Engine for LangSwarm V2

Modern, efficient workflow execution engine that integrates
with the V2 middleware system for comprehensive observability,
error handling, and performance optimization.
"""

import asyncio
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, AsyncIterator, Set, TYPE_CHECKING
from dataclasses import dataclass

from .interfaces import (
    IWorkflow, IWorkflowStep, IWorkflowEngine, IWorkflowExecution,
    WorkflowContext, WorkflowResult, StepResult,
    WorkflowStatus, StepStatus, ExecutionMode
)
from .base import WorkflowExecution, get_workflow_registry
from ..observability.auto_instrumentation import (
    AutoInstrumentedMixin, auto_trace_operation, auto_record_metric, auto_log_operation
)
from ..orchestration_errors import (
    AgentNotFoundError, WorkflowExecutionError, AgentExecutionError,
    DataPassingError, agent_not_found, workflow_failed, agent_failed
)

# Type hint for memory manager without importing (avoid circular imports)
if TYPE_CHECKING:
    from langswarm.core.memory import IMemoryManager

# Import V2 systems
try:
    from langswarm.core.error import get_error_handler
    from langswarm.core.middleware import get_middleware_pipeline
except ImportError:
    get_error_handler = None
    get_middleware_pipeline = None

logger = logging.getLogger(__name__)


class WorkflowExecutionEngine(IWorkflowEngine, AutoInstrumentedMixin):
    """
    Modern workflow execution engine with automatic instrumentation that provides:
    - Integration with V2 middleware pipeline
    - Comprehensive error handling and recovery
    - Multiple execution modes (sync, async, streaming, parallel)
    - Step dependency resolution
    - Execution monitoring and observability
    """
    
    def __init__(self):
        self._executions: Dict[str, WorkflowExecution] = {}
        self._registry = get_workflow_registry()
        
        # Integration with V2 systems
        self._error_handler = get_error_handler() if get_error_handler else None
        self._middleware = get_middleware_pipeline() if get_middleware_pipeline else None
        
        # Set component name for auto-instrumentation
        self._component_name = "workflow"
        
        # Initialize auto-instrumentation mixin
        super().__init__()
    
    async def execute_workflow(
        self,
        workflow: IWorkflow,
        input_data: Dict[str, Any],
        execution_mode: ExecutionMode = ExecutionMode.SYNC,
        context_variables: Optional[Dict[str, Any]] = None,
        memory_manager: Optional["IMemoryManager"] = None
    ) -> Union[WorkflowResult, IWorkflowExecution]:
        """Execute a multi-agent workflow with automatic orchestration.
        
        This method orchestrates the execution of multiple agents according to
        the workflow definition, automatically passing data between agents.
        
        Args:
            workflow: The workflow to execute (created with create_simple_workflow)
            input_data: Initial input data (typically {"input": "your query"})
            execution_mode: How to execute (SYNC waits for completion, ASYNC returns immediately)
            context_variables: Additional variables available to all agents
            memory_manager: Optional shared memory manager for all agents in the workflow.
                When provided, all agents share the same memory backend for session
                persistence and conversation history.
            
        Returns:
            WorkflowResult: For SYNC mode - contains final result and status
            IWorkflowExecution: For ASYNC mode - can be monitored for progress
            
        Raises:
            WorkflowError: If workflow execution fails
            AgentError: If an individual agent fails
            
        Example:
            >>> # Synchronous execution (wait for result)
            >>> result = await engine.execute_workflow(
            ...     workflow=my_workflow,
            ...     input_data={"input": "Research AI safety"}
            ... )
            >>> print(result.result)  # Final output from last agent
            >>> 
            >>> # With shared memory for all agents
            >>> from langswarm.core.memory import create_memory_manager
            >>> manager = create_memory_manager("sqlite", db_path="workflow.db")
            >>> await manager.backend.connect()
            >>> result = await engine.execute_workflow(
            ...     workflow=my_workflow,
            ...     input_data={"input": "Research AI safety"},
            ...     memory_manager=manager
            ... )
        """
        
        # Create execution context
        execution_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow.workflow_id,
            execution_id=execution_id,
            variables=context_variables or {},
        )
        
        # Add input data to context
        context.variables.update(input_data)
        
        # Store memory manager in context for agents to access
        if memory_manager:
            context.variables["_memory_manager"] = memory_manager
        
        # Create execution tracking
        execution = WorkflowExecution(execution_id, workflow.workflow_id, context)
        self._executions[execution_id] = execution
        
        with self._auto_trace("execute",
                             workflow_id=workflow.workflow_id,
                             execution_id=execution_id,
                             execution_mode=execution_mode.value,
                             input_data_size=len(str(input_data)),
                             context_variables_count=len(context_variables) if context_variables else 0,
                             step_count=len(workflow.steps) if hasattr(workflow, 'steps') else 0) as span:
            
            try:
                self._auto_log("info", f"Starting workflow execution: {workflow.workflow_id}",
                              workflow_id=workflow.workflow_id,
                              execution_id=execution_id,
                              execution_mode=execution_mode.value)
                
                # Record workflow start metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       workflow_id=workflow.workflow_id,
                                       execution_mode=execution_mode.value,
                                       status="started")
                
                if span:
                    span.add_tag("workflow_started", True)
                
                if execution_mode == ExecutionMode.SYNC:
                    with self._auto_trace("execute_sync",
                                         workflow_id=workflow.workflow_id,
                                         execution_id=execution_id) as sync_span:
                        result = await self._execute_sync(workflow, execution)
                        
                        if sync_span:
                            sync_span.add_tag("result_success", result.success if result else False)
                            sync_span.add_tag("steps_executed", len(result.step_results) if result and result.step_results else 0)
                        
                        # Record completion metrics
                        self._auto_record_metric("executions_total", 1.0, "counter",
                                               workflow_id=workflow.workflow_id,
                                               execution_mode=execution_mode.value,
                                               status="completed" if result and result.success else "failed")
                        
                        return result
                
                elif execution_mode == ExecutionMode.ASYNC:
                    # Start async execution
                    asyncio.create_task(self._execute_async_instrumented(workflow, execution))
                    
                    # Record async start metrics
                    self._auto_record_metric("executions_total", 1.0, "counter",
                                           workflow_id=workflow.workflow_id,
                                           execution_mode=execution_mode.value,
                                           status="async_started")
                    
                    if span:
                        span.add_tag("async_execution", True)
                    
                    return execution
                
                elif execution_mode == ExecutionMode.STREAMING:
                    # Streaming mode returns the execution for monitoring
                    asyncio.create_task(self._execute_streaming_instrumented(workflow, execution))
                    
                    # Record streaming start metrics
                    self._auto_record_metric("executions_total", 1.0, "counter",
                                           workflow_id=workflow.workflow_id,
                                           execution_mode=execution_mode.value,
                                           status="streaming_started")
                    
                    if span:
                        span.add_tag("streaming_execution", True)
                    
                    return execution
                
                elif execution_mode == ExecutionMode.PARALLEL:
                    with self._auto_trace("execute_parallel",
                                         workflow_id=workflow.workflow_id,
                                         execution_id=execution_id) as parallel_span:
                        result = await self._execute_parallel(workflow, execution)
                        
                        if parallel_span:
                            parallel_span.add_tag("result_success", result.success if result else False)
                            parallel_span.add_tag("parallel_execution", True)
                        
                        # Record completion metrics
                        self._auto_record_metric("executions_total", 1.0, "counter",
                                               workflow_id=workflow.workflow_id,
                                               execution_mode=execution_mode.value,
                                               status="completed" if result and result.success else "failed")
                        
                        return result
                
                else:
                    error_msg = f"Unsupported execution mode: {execution_mode}"
                    
                    # Record error metrics
                    self._auto_record_metric("executions_total", 1.0, "counter",
                                           workflow_id=workflow.workflow_id,
                                           execution_mode=execution_mode.value,
                                           status="invalid_mode")
                    
                    if span:
                        span.add_tag("error", True)
                        span.add_tag("error_type", "invalid_execution_mode")
                        span.set_status("error")
                    
                    raise ValueError(error_msg)
                
            except Exception as e:
                logger.error(f"Workflow execution {execution_id} failed: {e}")
                execution.update_status(WorkflowStatus.FAILED)
                
                result = WorkflowResult(
                    execution_id=execution_id,
                    status=WorkflowStatus.FAILED,
                    error=e,
                    execution_time=time.time() - execution.start_time.timestamp()
                )
                execution.set_result(result)
                
                if execution_mode == ExecutionMode.SYNC:
                    return result
                else:
                    return execution
    
    async def execute_workflow_stream(
        self,
        workflow: IWorkflow,
        input_data: Dict[str, Any],
        context_variables: Optional[Dict[str, Any]] = None,
        memory_manager: Optional["IMemoryManager"] = None
    ) -> AsyncIterator[Union[StepResult, WorkflowResult]]:
        """Execute workflow with streaming step results"""
        
        execution_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow.workflow_id,
            execution_id=execution_id,
            variables=context_variables or {},
        )
        context.variables.update(input_data)
        
        # Store memory manager in context for agents to access
        if memory_manager:
            context.variables["_memory_manager"] = memory_manager
        
        execution = WorkflowExecution(execution_id, workflow.workflow_id, context)
        self._executions[execution_id] = execution
        
        execution.update_status(WorkflowStatus.RUNNING)
        start_time = time.time()
        
        try:
            # Execute steps and yield results
            step_results = {}
            
            for step in self._resolve_execution_order(workflow.steps):
                execution.update_step_status(step.step_id, StepStatus.RUNNING)
                
                # Execute step
                step_result = await self._execute_step(step, context, execution)
                step_results[step.step_id] = step_result
                
                # Update context with step output
                if step_result.success:
                    context.set_step_output(step.step_id, step_result.result)
                    execution.update_step_status(step.step_id, StepStatus.COMPLETED)
                else:
                    execution.update_step_status(step.step_id, StepStatus.FAILED)
                
                # Yield step result
                yield step_result
                
                # Stop on failure unless error handling is configured
                if not step_result.success and not self._should_continue_on_error(step, workflow):
                    break
            
            # Determine final status
            failed_steps = [r for r in step_results.values() if not r.success]
            final_status = WorkflowStatus.FAILED if failed_steps else WorkflowStatus.COMPLETED
            
            execution.update_status(final_status)
            execution_time = time.time() - start_time
            
            # Yield final result
            final_result = WorkflowResult(
                execution_id=execution_id,
                status=final_status,
                result=context.step_outputs,
                execution_time=execution_time,
                step_results=step_results
            )
            
            execution.set_result(final_result)
            yield final_result
            
        except Exception as e:
            logger.error(f"Streaming workflow execution {execution_id} failed: {e}")
            execution.update_status(WorkflowStatus.FAILED)
            
            final_result = WorkflowResult(
                execution_id=execution_id,
                status=WorkflowStatus.FAILED,
                error=e,
                execution_time=time.time() - start_time
            )
            
            execution.set_result(final_result)
            yield final_result
    
    async def _execute_sync(self, workflow: IWorkflow, execution: WorkflowExecution) -> WorkflowResult:
        """Execute workflow synchronously"""
        execution.update_status(WorkflowStatus.RUNNING)
        start_time = time.time()
        
        try:
            step_results = {}
            context = execution.context
            
            # Execute steps in dependency order
            execution_order = self._resolve_execution_order(workflow.steps)
            
            for step in execution_order:
                execution.update_step_status(step.step_id, StepStatus.RUNNING)
                
                # Execute step
                step_result = await self._execute_step(step, context, execution)
                step_results[step.step_id] = step_result
                
                # Update context with step output
                if step_result.success:
                    context.set_step_output(step.step_id, step_result.result)
                    execution.update_step_status(step.step_id, StepStatus.COMPLETED)
                else:
                    execution.update_step_status(step.step_id, StepStatus.FAILED)
                    
                    # Stop on failure unless configured otherwise
                    if not self._should_continue_on_error(step, workflow):
                        break
            
            # Determine final status
            failed_steps = [r for r in step_results.values() if not r.success]
            final_status = WorkflowStatus.FAILED if failed_steps else WorkflowStatus.COMPLETED
            
            execution.update_status(final_status)
            execution_time = time.time() - start_time
            
            result = WorkflowResult(
                execution_id=execution.execution_id,
                status=final_status,
                result=context.step_outputs,
                execution_time=execution_time,
                step_results=step_results
            )
            
            execution.set_result(result)
            return result
            
        except Exception as e:
            execution.update_status(WorkflowStatus.FAILED)
            execution_time = time.time() - start_time
            
            result = WorkflowResult(
                execution_id=execution.execution_id,
                status=WorkflowStatus.FAILED,
                error=e,
                execution_time=execution_time
            )
            
            execution.set_result(result)
            return result
    
    async def _execute_async(self, workflow: IWorkflow, execution: WorkflowExecution) -> None:
        """Execute workflow asynchronously"""
        try:
            result = await self._execute_sync(workflow, execution)
            execution.set_result(result)
        except Exception as e:
            logger.error(f"Async workflow execution failed: {e}")
            execution.update_status(WorkflowStatus.FAILED)
            
            result = WorkflowResult(
                execution_id=execution.execution_id,
                status=WorkflowStatus.FAILED,
                error=e
            )
            execution.set_result(result)
    
    async def _execute_streaming(self, workflow: IWorkflow, execution: WorkflowExecution) -> None:
        """Execute workflow in streaming mode (internal)"""
        # This is handled by execute_workflow_stream, but we keep it for completeness
        await self._execute_async(workflow, execution)
    
    async def _execute_parallel(self, workflow: IWorkflow, execution: WorkflowExecution) -> WorkflowResult:
        """Execute workflow with parallel step execution where possible"""
        execution.update_status(WorkflowStatus.RUNNING)
        start_time = time.time()
        
        try:
            step_results = {}
            context = execution.context
            
            # Group steps by dependency level for parallel execution
            dependency_levels = self._group_by_dependency_level(workflow.steps)
            
            for level_steps in dependency_levels:
                # Execute all steps in this level in parallel
                tasks = []
                for step in level_steps:
                    execution.update_step_status(step.step_id, StepStatus.RUNNING)
                    task = asyncio.create_task(self._execute_step(step, context, execution))
                    tasks.append((step, task))
                
                # Wait for all steps in this level to complete
                for step, task in tasks:
                    step_result = await task
                    step_results[step.step_id] = step_result
                    
                    if step_result.success:
                        context.set_step_output(step.step_id, step_result.result)
                        execution.update_step_status(step.step_id, StepStatus.COMPLETED)
                    else:
                        execution.update_step_status(step.step_id, StepStatus.FAILED)
            
            # Determine final status
            failed_steps = [r for r in step_results.values() if not r.success]
            final_status = WorkflowStatus.FAILED if failed_steps else WorkflowStatus.COMPLETED
            
            execution.update_status(final_status)
            execution_time = time.time() - start_time
            
            result = WorkflowResult(
                execution_id=execution.execution_id,
                status=final_status,
                result=context.step_outputs,
                execution_time=execution_time,
                step_results=step_results
            )
            
            execution.set_result(result)
            return result
            
        except Exception as e:
            execution.update_status(WorkflowStatus.FAILED)
            execution_time = time.time() - start_time
            
            result = WorkflowResult(
                execution_id=execution.execution_id,
                status=WorkflowStatus.FAILED,
                error=e,
                execution_time=execution_time
            )
            
            execution.set_result(result)
            return result
    
    async def _execute_step(
        self, 
        step: IWorkflowStep, 
        context: WorkflowContext,
        execution: WorkflowExecution
    ) -> StepResult:
        """Execute a single step with middleware integration"""
        logger.debug(f"Executing step {step.step_id} in workflow {context.workflow_id}")
        
        try:
            # Apply timeout if configured
            if step.timeout:
                step_result = await asyncio.wait_for(
                    step.execute(context),
                    timeout=step.timeout
                )
            else:
                step_result = await step.execute(context)
            
            return step_result
            
        except asyncio.TimeoutError:
            logger.error(f"Step {step.step_id} timed out after {step.timeout} seconds")
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error=TimeoutError(f"Step timed out after {step.timeout} seconds")
            )
        
        except Exception as e:
            logger.error(f"Step {step.step_id} failed: {e}")
            
            # Create more specific error if it's an agent step
            if hasattr(step, 'agent_id'):
                # Check if it's an agent not found error
                if "not found" in str(e).lower() or "no agent" in str(e).lower():
                    from langswarm.core.agents import list_agents
                    available = list_agents()
                    enhanced_error = agent_not_found(step.agent_id, available)
                else:
                    # General agent execution error
                    enhanced_error = agent_failed(
                        agent_id=step.agent_id,
                        step_id=step.step_id,
                        error=e
                    )
                e = enhanced_error
            
            # Handle step failure with error handler if available
            if self._error_handler:
                try:
                    await self._error_handler.handle_error(e, {
                        "workflow_id": context.workflow_id,
                        "execution_id": context.execution_id,
                        "step_id": step.step_id
                    })
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
            
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error=e
            )
    
    def _resolve_execution_order(self, steps: List[IWorkflowStep]) -> List[IWorkflowStep]:
        """Resolve step execution order based on dependencies"""
        ordered_steps = []
        remaining_steps = steps.copy()
        step_map = {step.step_id: step for step in steps}
        
        while remaining_steps:
            # Find steps with no unresolved dependencies
            ready_steps = []
            completed_step_ids = {step.step_id for step in ordered_steps}
            
            for step in remaining_steps:
                unresolved_deps = [dep for dep in step.dependencies if dep not in completed_step_ids]
                if not unresolved_deps:
                    ready_steps.append(step)
            
            if not ready_steps:
                # Circular dependency or missing dependency
                unresolved = [step.step_id for step in remaining_steps]
                raise ValueError(f"Circular dependency or missing steps detected: {unresolved}")
            
            # Add ready steps to execution order
            for step in ready_steps:
                ordered_steps.append(step)
                remaining_steps.remove(step)
        
        return ordered_steps
    
    def _group_by_dependency_level(self, steps: List[IWorkflowStep]) -> List[List[IWorkflowStep]]:
        """Group steps by dependency level for parallel execution"""
        levels = []
        remaining_steps = steps.copy()
        step_map = {step.step_id: step for step in steps}
        
        while remaining_steps:
            current_level = []
            completed_step_ids = set()
            
            # Collect all completed step IDs from previous levels
            for level in levels:
                for step in level:
                    completed_step_ids.add(step.step_id)
            
            # Find steps with no unresolved dependencies
            for step in remaining_steps.copy():
                unresolved_deps = [dep for dep in step.dependencies if dep not in completed_step_ids]
                if not unresolved_deps:
                    current_level.append(step)
                    remaining_steps.remove(step)
            
            if not current_level:
                # Circular dependency
                unresolved = [step.step_id for step in remaining_steps]
                raise ValueError(f"Circular dependency detected: {unresolved}")
            
            levels.append(current_level)
        
        return levels
    
    def _should_continue_on_error(self, step: IWorkflowStep, workflow: IWorkflow) -> bool:
        """Determine if workflow should continue after step failure"""
        # For now, simple logic - can be enhanced
        step_metadata = getattr(step, 'metadata', {})
        workflow_metadata = workflow.metadata
        
        return (
            step_metadata.get('continue_on_error', False) or
            workflow_metadata.get('continue_on_error', False)
        )
    
    async def get_execution(self, execution_id: str) -> Optional[IWorkflowExecution]:
        """Get execution by ID"""
        return self._executions.get(execution_id)
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[IWorkflowExecution]:
        """List workflow executions"""
        executions = list(self._executions.values())
        
        # Filter by workflow ID
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        # Filter by status
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by start time (newest first) and limit
        executions.sort(key=lambda e: e.start_time, reverse=True)
        return executions[:limit]


    async def _execute_async_instrumented(self, workflow: IWorkflow, execution: WorkflowExecution):
        """Execute async workflow with instrumentation"""
        with self._auto_trace("execute_async",
                             workflow_id=workflow.workflow_id,
                             execution_id=execution.execution_id) as span:
            try:
                result = await self._execute_async(workflow, execution)
                
                # Record completion metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       workflow_id=workflow.workflow_id,
                                       execution_mode="async",
                                       status="completed" if result and result.success else "failed")
                
                if span:
                    span.add_tag("async_completed", True)
                    span.add_tag("result_success", result.success if result else False)
                
                return result
                
            except Exception as e:
                # Record error metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       workflow_id=workflow.workflow_id,
                                       execution_mode="async",
                                       status="error")
                
                if span:
                    span.add_tag("error", True)
                    span.add_tag("error_type", type(e).__name__)
                    span.set_status("error")
                
                self._auto_log("error", f"Async workflow execution failed: {workflow.workflow_id}: {e}",
                              workflow_id=workflow.workflow_id,
                              execution_id=execution.execution_id,
                              error_type=type(e).__name__)
                raise
    
    async def _execute_streaming_instrumented(self, workflow: IWorkflow, execution: WorkflowExecution):
        """Execute streaming workflow with instrumentation"""
        with self._auto_trace("execute_streaming",
                             workflow_id=workflow.workflow_id,
                             execution_id=execution.execution_id) as span:
            try:
                result = await self._execute_streaming(workflow, execution)
                
                # Record completion metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       workflow_id=workflow.workflow_id,
                                       execution_mode="streaming",
                                       status="completed" if result and result.success else "failed")
                
                if span:
                    span.add_tag("streaming_completed", True)
                    span.add_tag("result_success", result.success if result else False)
                
                return result
                
            except Exception as e:
                # Record error metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       workflow_id=workflow.workflow_id,
                                       execution_mode="streaming",
                                       status="error")
                
                if span:
                    span.add_tag("error", True)
                    span.add_tag("error_type", type(e).__name__)
                    span.set_status("error")
                
                self._auto_log("error", f"Streaming workflow execution failed: {workflow.workflow_id}: {e}",
                              workflow_id=workflow.workflow_id,
                              execution_id=execution.execution_id,
                              error_type=type(e).__name__)
                raise


# Global engine instance
_workflow_engine = WorkflowExecutionEngine()


def get_workflow_engine() -> WorkflowExecutionEngine:
    """Get the global workflow execution engine for orchestrating agents.
    
    The workflow engine is responsible for executing workflows, managing
    agent coordination, and passing data between agents in the workflow.
    
    Returns:
        WorkflowExecutionEngine: The global engine instance
        
    Example:
        >>> engine = get_workflow_engine()
        >>> result = await engine.execute_workflow(
        ...     workflow=my_workflow,
        ...     input_data={"input": "Process this data"}
        ... )
        >>> print(f"Status: {result.status}")
        >>> print(f"Result: {result.result}")
    """
    return _workflow_engine
