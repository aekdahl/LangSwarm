"""
Workflow Interfaces for LangSwarm V2

Clean, type-safe interfaces for the modernized workflow system.
Replaces complex YAML-based workflow definitions with clear,
programmatic interfaces while maintaining full backward compatibility.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable, AsyncIterator
from dataclasses import dataclass, field


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Individual step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ExecutionMode(Enum):
    """Workflow execution modes"""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"
    PARALLEL = "parallel"


class StepType(Enum):
    """Types of workflow steps"""
    AGENT = "agent"          # Execute agent with input
    TOOL = "tool"            # Execute tool function
    CONDITION = "condition"  # Conditional branching
    PARALLEL = "parallel"    # Parallel execution
    LOOP = "loop"           # Loop execution
    TRANSFORM = "transform"  # Data transformation
    VALIDATE = "validate"    # Data validation
    DELAY = "delay"         # Delay/wait step


@dataclass
class WorkflowContext:
    """Context passed through workflow execution"""
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get context variable with default"""
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set context variable"""
        self.variables[name] = value
    
    def get_step_output(self, step_id: str, default: Any = None) -> Any:
        """Get output from previous step"""
        return self.step_outputs.get(step_id, default)
    
    def set_step_output(self, step_id: str, output: Any) -> None:
        """Set step output"""
        self.step_outputs[step_id] = output


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    execution_id: str
    status: WorkflowStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Whether workflow completed successfully"""
        return self.status == WorkflowStatus.COMPLETED and self.error is None


@dataclass  
class StepResult:
    """Result of individual step execution"""
    step_id: str
    status: StepStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Whether step completed successfully"""
        return self.status == StepStatus.COMPLETED and self.error is None


class IWorkflowStep(ABC):
    """Interface for workflow step implementations"""
    
    @property
    @abstractmethod
    def step_id(self) -> str:
        """Unique step identifier"""
        pass
    
    @property  
    @abstractmethod
    def step_type(self) -> StepType:
        """Type of this step"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable step name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """Step description"""
        pass
    
    @abstractmethod
    async def execute(self, context: WorkflowContext) -> StepResult:
        """Execute this step with the given context"""
        pass
    
    @abstractmethod
    def validate(self, context: WorkflowContext) -> List[str]:
        """Validate step configuration, return list of errors"""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """List of step IDs this step depends on"""
        return []
    
    @property
    def timeout(self) -> Optional[float]:
        """Step execution timeout in seconds"""
        return None
    
    @property
    def retry_config(self) -> Optional[Dict[str, Any]]:
        """Retry configuration for this step"""
        return None


class IWorkflow(ABC):
    """Interface for workflow implementations"""
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """Unique workflow identifier"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable workflow name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """Workflow description"""
        pass
    
    @property
    @abstractmethod
    def steps(self) -> List[IWorkflowStep]:
        """List of workflow steps in execution order"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Optional[Dict[str, Any]]:
        """Input validation schema"""
        pass
    
    @property
    @abstractmethod
    def output_schema(self) -> Optional[Dict[str, Any]]:
        """Output validation schema"""
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate workflow configuration, return list of errors"""
        pass
    
    @property
    def execution_mode(self) -> ExecutionMode:
        """Preferred execution mode"""
        return ExecutionMode.SYNC
    
    @property
    def timeout(self) -> Optional[float]:
        """Workflow execution timeout in seconds"""
        return None
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Workflow metadata"""
        return {}


class IWorkflowExecution(ABC):
    """Interface for workflow execution tracking"""
    
    @property
    @abstractmethod
    def execution_id(self) -> str:
        """Unique execution identifier"""
        pass
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """ID of workflow being executed"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> WorkflowStatus:
        """Current execution status"""
        pass
    
    @property
    @abstractmethod
    def start_time(self) -> datetime:
        """Execution start time"""
        pass
    
    @property
    @abstractmethod
    def end_time(self) -> Optional[datetime]:
        """Execution end time"""
        pass
    
    @property
    @abstractmethod
    def context(self) -> WorkflowContext:
        """Current execution context"""
        pass
    
    @property
    @abstractmethod
    def step_statuses(self) -> Dict[str, StepStatus]:
        """Current status of all steps"""
        pass
    
    @abstractmethod
    async def wait_for_completion(self, timeout: Optional[float] = None) -> WorkflowResult:
        """Wait for workflow to complete"""
        pass
    
    @abstractmethod
    async def cancel(self, reason: str = "Cancelled by user") -> bool:
        """Cancel workflow execution"""
        pass
    
    @abstractmethod
    async def pause(self) -> bool:
        """Pause workflow execution"""
        pass
    
    @abstractmethod
    async def resume(self) -> bool:
        """Resume paused workflow execution"""
        pass


class IWorkflowEngine(ABC):
    """Interface for workflow execution engine"""
    
    @abstractmethod
    async def execute_workflow(
        self,
        workflow: IWorkflow,
        input_data: Dict[str, Any],
        execution_mode: ExecutionMode = ExecutionMode.SYNC,
        context_variables: Optional[Dict[str, Any]] = None
    ) -> Union[WorkflowResult, IWorkflowExecution]:
        """Execute a workflow"""
        pass
    
    @abstractmethod
    async def execute_workflow_stream(
        self,
        workflow: IWorkflow,
        input_data: Dict[str, Any],
        context_variables: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Union[StepResult, WorkflowResult]]:
        """Execute workflow with streaming results"""
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[IWorkflowExecution]:
        """Get execution by ID"""
        pass
    
    @abstractmethod
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[IWorkflowExecution]:
        """List workflow executions"""
        pass


class IWorkflowRegistry(ABC):
    """Interface for workflow registry"""
    
    @abstractmethod
    async def register_workflow(self, workflow: IWorkflow) -> bool:
        """Register a workflow"""
        pass
    
    @abstractmethod
    async def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow"""
        pass
    
    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """Get workflow by ID"""
        pass
    
    @abstractmethod
    async def list_workflows(self) -> List[IWorkflow]:
        """List all registered workflows"""
        pass
    
    @abstractmethod
    async def workflow_exists(self, workflow_id: str) -> bool:
        """Check if workflow exists"""
        pass


class IWorkflowValidator(ABC):
    """Interface for workflow validation"""
    
    @abstractmethod
    def validate_workflow(self, workflow: IWorkflow) -> List[str]:
        """Validate complete workflow"""
        pass
    
    @abstractmethod
    def validate_step(self, step: IWorkflowStep, workflow: IWorkflow) -> List[str]:
        """Validate individual step within workflow context"""
        pass
    
    @abstractmethod
    def validate_input(self, workflow: IWorkflow, input_data: Dict[str, Any]) -> List[str]:
        """Validate input data against workflow schema"""
        pass
    
    @abstractmethod
    def validate_dependencies(self, workflow: IWorkflow) -> List[str]:
        """Validate step dependencies are satisfied"""
        pass


class IWorkflowBuilder(ABC):
    """Interface for fluent workflow builder"""
    
    @abstractmethod
    def start(self, workflow_id: str, name: str) -> 'IWorkflowBuilder':
        """Start building a new workflow"""
        pass
    
    @abstractmethod
    def description(self, description: str) -> 'IWorkflowBuilder':
        """Set workflow description"""
        pass
    
    @abstractmethod
    def add_step(self, step: IWorkflowStep) -> 'IWorkflowBuilder':
        """Add a step to the workflow"""
        pass
    
    @abstractmethod
    def add_agent_step(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable],
        name: Optional[str] = None
    ) -> 'IWorkflowBuilder':
        """Add an agent execution step"""
        pass
    
    @abstractmethod
    def add_tool_step(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable],
        name: Optional[str] = None
    ) -> 'IWorkflowBuilder':
        """Add a tool execution step"""
        pass
    
    @abstractmethod
    def add_condition_step(
        self,
        step_id: str,
        condition: Callable[[WorkflowContext], bool],
        true_step: str,
        false_step: Optional[str] = None,
        name: Optional[str] = None
    ) -> 'IWorkflowBuilder':
        """Add a conditional step"""
        pass
    
    @abstractmethod
    def add_parallel_steps(
        self,
        parallel_id: str,
        steps: List[IWorkflowStep],
        name: Optional[str] = None
    ) -> 'IWorkflowBuilder':
        """Add parallel execution steps"""
        pass
    
    @abstractmethod
    def set_input_schema(self, schema: Dict[str, Any]) -> 'IWorkflowBuilder':
        """Set input validation schema"""
        pass
    
    @abstractmethod
    def set_output_schema(self, schema: Dict[str, Any]) -> 'IWorkflowBuilder':
        """Set output validation schema"""
        pass
    
    @abstractmethod
    def set_execution_mode(self, mode: ExecutionMode) -> 'IWorkflowBuilder':
        """Set execution mode"""
        pass
    
    @abstractmethod
    def set_timeout(self, timeout: float) -> 'IWorkflowBuilder':
        """Set workflow timeout"""
        pass
    
    @abstractmethod
    def build(self) -> IWorkflow:
        """Build the complete workflow"""
        pass


class IWorkflowMonitor(ABC):
    """Interface for workflow monitoring and observability"""
    
    @abstractmethod
    async def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get execution performance metrics"""
        pass
    
    @abstractmethod
    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow aggregated metrics"""
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall workflow system metrics"""
        pass
    
    @abstractmethod
    async def subscribe_to_execution(
        self,
        execution_id: str,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> str:
        """Subscribe to execution events"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        pass


# Type aliases for convenience
WorkflowInput = Dict[str, Any]
WorkflowOutput = Any
StepInput = Dict[str, Any]
StepOutput = Any

# Callback types
StepExecutor = Callable[[WorkflowContext], StepResult]
ConditionEvaluator = Callable[[WorkflowContext], bool]
DataTransformer = Callable[[Any, WorkflowContext], Any]
ValidationRule = Callable[[Any, WorkflowContext], List[str]]

# Event types for monitoring
WorkflowEvent = Dict[str, Any]
StepEvent = Dict[str, Any]
