"""
Base Workflow Implementations for LangSwarm V2

Concrete implementations of workflow interfaces providing
the foundation for the modernized workflow system.
"""

import asyncio
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Callable, AsyncIterator
from dataclasses import dataclass, field

from .interfaces import (
    IWorkflow, IWorkflowStep, IWorkflowExecution,
    WorkflowContext, WorkflowResult, StepResult,
    WorkflowStatus, StepStatus, StepType, ExecutionMode
)

logger = logging.getLogger(__name__)


@dataclass
class BaseWorkflowStep(IWorkflowStep):
    """Base implementation of workflow step"""
    
    _step_id: str
    _step_type: StepType
    _name: str
    _description: Optional[str] = None
    _dependencies: List[str] = field(default_factory=list)
    _timeout: Optional[float] = None
    _retry_config: Optional[Dict[str, Any]] = None
    
    @property
    def step_id(self) -> str:
        return self._step_id
    
    @property
    def step_type(self) -> StepType:
        return self._step_type
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def dependencies(self) -> List[str]:
        return self._dependencies
    
    @property
    def timeout(self) -> Optional[float]:
        return self._timeout
    
    @property
    def retry_config(self) -> Optional[Dict[str, Any]]:
        return self._retry_config
    
    async def execute(self, context: WorkflowContext) -> StepResult:
        """Base execution with timing and error handling"""
        start_time = time.time()
        
        try:
            logger.debug(f"Executing step {self.step_id}: {self.name}")
            
            # Call the actual step implementation
            result = await self._execute_impl(context)
            
            execution_time = time.time() - start_time
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                metadata={"step_type": self.step_type.value}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Step {self.step_id} failed: {e}")
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error=e,
                execution_time=execution_time,
                metadata={"step_type": self.step_type.value}
            )
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_impl")
    
    def validate(self, context: WorkflowContext) -> List[str]:
        """Base validation - override in subclasses"""
        errors = []
        
        if not self.step_id:
            errors.append("Step ID is required")
        
        if not self.name:
            errors.append("Step name is required")
        
        return errors


class AgentStep(BaseWorkflowStep):
    """Step that executes an agent with input"""
    
    def __init__(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.AGENT,
            _name=name or f"Agent: {agent_id}",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.agent_id = agent_id
        self.input_data = input_data
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute agent with the given input"""
        # Resolve input data
        if callable(self.input_data):
            agent_input = self.input_data(context)
        elif isinstance(self.input_data, str):
            # Template string - replace variables
            agent_input = self._resolve_template(self.input_data, context)
        else:
            agent_input = self.input_data
        
        # Get agent from V2 agent system
        from langswarm.core.agents import get_agent
        
        agent = await get_agent(self.agent_id)
        if not agent:
            raise ValueError(f"Agent '{self.agent_id}' not found")
        
        # Inject shared memory manager if provided in context and agent doesn't have one
        memory_manager = context.variables.get("_memory_manager")
        if memory_manager and hasattr(agent, '_memory_manager') and agent._memory_manager is None:
            agent._memory_manager = memory_manager
            logger.debug(f"Injected shared memory manager into agent '{self.agent_id}'")
        
        # Create consistent session_id for conversation context isolation
        # Priority: user-provided session_id > workflow execution session_id
        session_id = context.variables.get("session_id") or f"{context.workflow_id}_{context.execution_id}"
        
        # Execute agent with session_id for proper memory isolation
        if isinstance(agent_input, str):
            # Text input
            response = await agent.send_message(agent_input, session_id=session_id)
            return response.content
        else:
            # Structured input
            response = await agent.send_message(str(agent_input), session_id=session_id)
            return response.content
    
    def _resolve_template(self, template: str, context: WorkflowContext) -> str:
        """Resolve template variables in input string"""
        # Simple template resolution - can be enhanced
        result = template
        
        # Replace context variables: ${variable_name}
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
        
        # Replace step outputs: ${step_id.output}
        for step_id, output in context.step_outputs.items():
            result = result.replace(f"${{{step_id}}}", str(output))
        
        return result
    
    def validate(self, context: WorkflowContext) -> List[str]:
        errors = super().validate(context)
        
        if not self.agent_id:
            errors.append("Agent ID is required")
        
        return errors


class ToolStep(BaseWorkflowStep):
    """Step that executes a tool with parameters"""
    
    def __init__(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.TOOL,
            _name=name or f"Tool: {tool_name}",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.tool_name = tool_name
        self.parameters = parameters
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute tool with the given parameters"""
        # Resolve parameters
        if callable(self.parameters):
            tool_params = self.parameters(context)
        else:
            tool_params = self.parameters
        
        # Get tool from V2 tool system
        from langswarm.core.tools import get_tool_registry
        
        registry = get_tool_registry()
        tool = await registry.get_tool(self.tool_name)
        
        if not tool:
            raise ValueError(f"Tool '{self.tool_name}' not found")
        
        # Execute tool
        result = await tool.execute(**tool_params)
        return result
    
    def validate(self, context: WorkflowContext) -> List[str]:
        errors = super().validate(context)
        
        if not self.tool_name:
            errors.append("Tool name is required")
        
        return errors


class ConditionStep(BaseWorkflowStep):
    """Step that performs conditional execution"""
    
    def __init__(
        self,
        step_id: str,
        condition: Callable[[WorkflowContext], bool],
        true_step: str,
        false_step: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.CONDITION,
            _name=name or "Condition",
            _description=description,
            _dependencies=dependencies or [],
        )
        self.condition = condition
        self.true_step = true_step
        self.false_step = false_step
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Evaluate condition and return next step"""
        try:
            condition_result = self.condition(context)
            
            if condition_result:
                next_step = self.true_step
            else:
                next_step = self.false_step
            
            return {
                "condition_result": condition_result,
                "next_step": next_step
            }
            
        except Exception as e:
            raise ValueError(f"Condition evaluation failed: {e}")
    
    def validate(self, context: WorkflowContext) -> List[str]:
        errors = super().validate(context)
        
        if not callable(self.condition):
            errors.append("Condition must be callable")
        
        if not self.true_step:
            errors.append("True step is required")
        
        return errors


class TransformStep(BaseWorkflowStep):
    """Step that transforms data"""
    
    def __init__(
        self,
        step_id: str,
        transformer: Callable[[Any, WorkflowContext], Any],
        input_source: str = "input",
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.TRANSFORM,
            _name=name or "Transform",
            _description=description,
            _dependencies=dependencies or [],
        )
        self.transformer = transformer
        self.input_source = input_source
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Transform data using the transformer function"""
        # Get input data
        if self.input_source == "input":
            input_data = context.variables.get("input")
        else:
            input_data = context.get_step_output(self.input_source)
        
        # Apply transformation
        result = self.transformer(input_data, context)
        return result
    
    def validate(self, context: WorkflowContext) -> List[str]:
        errors = super().validate(context)
        
        if not callable(self.transformer):
            errors.append("Transformer must be callable")
        
        return errors


@dataclass  
class BaseWorkflow(IWorkflow):
    """Base implementation of workflow"""
    
    _workflow_id: str
    _name: str
    _description: Optional[str] = None
    _steps: List[IWorkflowStep] = field(default_factory=list)
    _input_schema: Optional[Dict[str, Any]] = None
    _output_schema: Optional[Dict[str, Any]] = None
    _execution_mode: ExecutionMode = ExecutionMode.SYNC
    _timeout: Optional[float] = None
    _metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def workflow_id(self) -> str:
        return self._workflow_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def steps(self) -> List[IWorkflowStep]:
        return self._steps
    
    @property
    def input_schema(self) -> Optional[Dict[str, Any]]:
        return self._input_schema
    
    @property
    def output_schema(self) -> Optional[Dict[str, Any]]:
        return self._output_schema
    
    @property
    def execution_mode(self) -> ExecutionMode:
        return self._execution_mode
    
    @property
    def timeout(self) -> Optional[float]:
        return self._timeout
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
    def add_step(self, step: IWorkflowStep) -> None:
        """Add a step to the workflow"""
        self._steps.append(step)
    
    def validate(self) -> List[str]:
        """Validate workflow configuration"""
        errors = []
        
        if not self.workflow_id:
            errors.append("Workflow ID is required")
        
        if not self.name:
            errors.append("Workflow name is required")
        
        if not self.steps:
            errors.append("Workflow must have at least one step")
        
        # Validate step IDs are unique
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique")
        
        # Validate step dependencies
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step {step.step_id} depends on non-existent step {dep}")
        
        # Validate individual steps
        dummy_context = WorkflowContext(
            workflow_id=self.workflow_id,
            execution_id="validation"
        )
        
        for step in self.steps:
            step_errors = step.validate(dummy_context)
            for error in step_errors:
                errors.append(f"Step {step.step_id}: {error}")
        
        return errors


class WorkflowExecution(IWorkflowExecution):
    """Implementation of workflow execution tracking"""
    
    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        context: WorkflowContext
    ):
        self._execution_id = execution_id
        self._workflow_id = workflow_id
        self._status = WorkflowStatus.PENDING
        self._start_time = datetime.now(timezone.utc)
        self._end_time: Optional[datetime] = None
        self._context = context
        self._step_statuses: Dict[str, StepStatus] = {}
        self._completion_future: Optional[asyncio.Future] = None
        self._result: Optional[WorkflowResult] = None
    
    @property
    def execution_id(self) -> str:
        return self._execution_id
    
    @property
    def workflow_id(self) -> str:
        return self._workflow_id
    
    @property
    def status(self) -> WorkflowStatus:
        return self._status
    
    @property
    def start_time(self) -> datetime:
        return self._start_time
    
    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time
    
    @property
    def context(self) -> WorkflowContext:
        return self._context
    
    @property
    def step_statuses(self) -> Dict[str, StepStatus]:
        return self._step_statuses.copy()
    
    def update_status(self, status: WorkflowStatus) -> None:
        """Update execution status"""
        self._status = status
        
        if status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            self._end_time = datetime.now(timezone.utc)
            
            if self._completion_future and not self._completion_future.done():
                self._completion_future.set_result(self._result)
    
    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """Update step status"""
        self._step_statuses[step_id] = status
    
    def set_result(self, result: WorkflowResult) -> None:
        """Set final result"""
        self._result = result
    
    async def wait_for_completion(self, timeout: Optional[float] = None) -> WorkflowResult:
        """Wait for workflow to complete"""
        if self._status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return self._result
        
        if not self._completion_future:
            self._completion_future = asyncio.Future()
        
        try:
            return await asyncio.wait_for(self._completion_future, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Workflow {self.execution_id} did not complete within {timeout} seconds")
    
    async def cancel(self, reason: str = "Cancelled by user") -> bool:
        """Cancel workflow execution"""
        if self._status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return False
        
        self.update_status(WorkflowStatus.CANCELLED)
        self._context.metadata["cancellation_reason"] = reason
        
        logger.info(f"Workflow {self.execution_id} cancelled: {reason}")
        return True
    
    async def pause(self) -> bool:
        """Pause workflow execution"""
        if self._status != WorkflowStatus.RUNNING:
            return False
        
        self.update_status(WorkflowStatus.PAUSED)
        logger.info(f"Workflow {self.execution_id} paused")
        return True
    
    async def resume(self) -> bool:
        """Resume paused workflow execution"""
        if self._status != WorkflowStatus.PAUSED:
            return False
        
        self.update_status(WorkflowStatus.RUNNING)
        logger.info(f"Workflow {self.execution_id} resumed")
        return True


class WorkflowRegistry:
    """Simple in-memory workflow registry"""
    
    def __init__(self):
        self._workflows: Dict[str, IWorkflow] = {}
    
    async def register_workflow(self, workflow: IWorkflow) -> bool:
        """Register a workflow"""
        try:
            # Validate workflow before registration
            errors = workflow.validate()
            if errors:
                logger.error(f"Cannot register invalid workflow {workflow.workflow_id}: {errors}")
                return False
            
            self._workflows[workflow.workflow_id] = workflow
            logger.info(f"Registered workflow: {workflow.workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.workflow_id}: {e}")
            return False
    
    async def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            logger.info(f"Unregistered workflow: {workflow_id}")
            return True
        return False
    
    async def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """Get workflow by ID"""
        return self._workflows.get(workflow_id)
    
    async def list_workflows(self) -> List[IWorkflow]:
        """List all registered workflows"""
        return list(self._workflows.values())
    
    async def workflow_exists(self, workflow_id: str) -> bool:
        """Check if workflow exists"""
        return workflow_id in self._workflows


# Global registry instance
_workflow_registry = WorkflowRegistry()


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry"""
    return _workflow_registry
