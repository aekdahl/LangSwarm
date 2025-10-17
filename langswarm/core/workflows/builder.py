"""
Workflow Builder for LangSwarm V2

Fluent API for creating workflows programmatically.
Provides an intuitive, type-safe way to build complex workflows
without writing YAML or dealing with complex configuration structures.
"""

import uuid
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass

from .interfaces import (
    IWorkflow, IWorkflowStep, IWorkflowBuilder,
    WorkflowContext, ExecutionMode, StepType
)
from .base import (
    BaseWorkflow, AgentStep, ToolStep, ConditionStep, TransformStep
)


class WorkflowBuilder(IWorkflowBuilder):
    """
    Fluent workflow builder providing an intuitive API for creating workflows.
    
    Example usage:
        workflow = (WorkflowBuilder()
            .start("data_analysis", "Data Analysis Workflow")
            .description("Analyze data and generate report")
            .add_agent_step("extract", "data_extractor", {"source": "database"})
            .add_tool_step("transform", "data_transformer", {"format": "json"})
            .add_agent_step("analyze", "data_analyzer", lambda ctx: ctx.get_step_output("transform"))
            .add_agent_step("report", "report_generator", "${analyze}")
            .set_execution_mode(ExecutionMode.PARALLEL)
            .build())
    """
    
    def __init__(self):
        self._workflow_id: Optional[str] = None
        self._name: Optional[str] = None
        self._description: Optional[str] = None
        self._steps: List[IWorkflowStep] = []
        self._input_schema: Optional[Dict[str, Any]] = None
        self._output_schema: Optional[Dict[str, Any]] = None
        self._execution_mode: ExecutionMode = ExecutionMode.SYNC
        self._timeout: Optional[float] = None
        self._metadata: Dict[str, Any] = {}
    
    def start(self, workflow_id: str, name: str) -> 'WorkflowBuilder':
        """Start building a new workflow"""
        self._workflow_id = workflow_id
        self._name = name
        return self
    
    def description(self, description: str) -> 'WorkflowBuilder':
        """Set workflow description"""
        self._description = description
        return self
    
    def add_step(self, step: IWorkflowStep) -> 'WorkflowBuilder':
        """Add a custom step to the workflow"""
        self._steps.append(step)
        return self
    
    def add_agent_step(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> 'WorkflowBuilder':
        """Add an agent execution step"""
        step = AgentStep(
            step_id=step_id,
            agent_id=agent_id,
            input_data=input_data,
            name=name,
            description=description,
            dependencies=dependencies,
            timeout=timeout
        )
        self._steps.append(step)
        return self
    
    def add_tool_step(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> 'WorkflowBuilder':
        """Add a tool execution step"""
        step = ToolStep(
            step_id=step_id,
            tool_name=tool_name,
            parameters=parameters,
            name=name,
            description=description,
            dependencies=dependencies,
            timeout=timeout
        )
        self._steps.append(step)
        return self
    
    def add_condition_step(
        self,
        step_id: str,
        condition: Callable[[WorkflowContext], bool],
        true_step: str,
        false_step: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> 'WorkflowBuilder':
        """Add a conditional step"""
        step = ConditionStep(
            step_id=step_id,
            condition=condition,
            true_step=true_step,
            false_step=false_step,
            name=name,
            description=description,
            dependencies=dependencies
        )
        self._steps.append(step)
        return self
    
    def add_transform_step(
        self,
        step_id: str,
        transformer: Callable[[Any, WorkflowContext], Any],
        input_source: str = "input",
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> 'WorkflowBuilder':
        """Add a data transformation step"""
        step = TransformStep(
            step_id=step_id,
            transformer=transformer,
            input_source=input_source,
            name=name,
            description=description,
            dependencies=dependencies
        )
        self._steps.append(step)
        return self
    
    def add_parallel_steps(
        self,
        parallel_id: str,
        steps: List[IWorkflowStep],
        name: Optional[str] = None
    ) -> 'WorkflowBuilder':
        """Add parallel execution steps"""
        # For now, we'll add steps individually with no dependencies between them
        # A more sophisticated implementation could create a ParallelStep container
        for step in steps:
            self._steps.append(step)
        return self
    
    def set_input_schema(self, schema: Dict[str, Any]) -> 'WorkflowBuilder':
        """Set input validation schema"""
        self._input_schema = schema
        return self
    
    def set_output_schema(self, schema: Dict[str, Any]) -> 'WorkflowBuilder':
        """Set output validation schema"""
        self._output_schema = schema
        return self
    
    def set_execution_mode(self, mode: ExecutionMode) -> 'WorkflowBuilder':
        """Set execution mode"""
        self._execution_mode = mode
        return self
    
    def set_timeout(self, timeout: float) -> 'WorkflowBuilder':
        """Set workflow timeout"""
        self._timeout = timeout
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'WorkflowBuilder':
        """Set workflow metadata"""
        self._metadata[key] = value
        return self
    
    def with_error_handling(self, continue_on_error: bool = True) -> 'WorkflowBuilder':
        """Configure error handling behavior"""
        self._metadata['continue_on_error'] = continue_on_error
        return self
    
    def build(self) -> IWorkflow:
        """Build the complete workflow"""
        if not self._workflow_id:
            raise ValueError("Workflow ID is required")
        
        if not self._name:
            raise ValueError("Workflow name is required")
        
        workflow = BaseWorkflow(
            _workflow_id=self._workflow_id,
            _name=self._name,
            _description=self._description,
            _steps=self._steps.copy(),
            _input_schema=self._input_schema,
            _output_schema=self._output_schema,
            _execution_mode=self._execution_mode,
            _timeout=self._timeout,
            _metadata=self._metadata.copy()
        )
        
        # Validate the built workflow
        errors = workflow.validate()
        if errors:
            raise ValueError(f"Invalid workflow configuration: {', '.join(errors)}")
        
        return workflow


# Convenience builders for common patterns

class LinearWorkflowBuilder(WorkflowBuilder):
    """Builder for linear (sequential) workflows"""
    
    def then_agent(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable] = None,
        name: Optional[str] = None
    ) -> 'LinearWorkflowBuilder':
        """Add next agent step in sequence"""
        # Auto-create dependency on previous step
        dependencies = []
        if self._steps:
            dependencies = [self._steps[-1].step_id]
        
        # Auto-resolve input from previous step if not provided
        if input_data is None and self._steps:
            input_data = f"${{{self._steps[-1].step_id}}}"
        
        self.add_agent_step(
            step_id=step_id,
            agent_id=agent_id,
            input_data=input_data,
            name=name,
            dependencies=dependencies
        )
        return self
    
    def then_tool(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable] = None,
        name: Optional[str] = None
    ) -> 'LinearWorkflowBuilder':
        """Add next tool step in sequence"""
        dependencies = []
        if self._steps:
            dependencies = [self._steps[-1].step_id]
        
        self.add_tool_step(
            step_id=step_id,
            tool_name=tool_name,
            parameters=parameters or {},
            name=name,
            dependencies=dependencies
        )
        return self
    
    def then_transform(
        self,
        step_id: str,
        transformer: Callable[[Any, WorkflowContext], Any],
        name: Optional[str] = None
    ) -> 'LinearWorkflowBuilder':
        """Add next transformation step in sequence"""
        dependencies = []
        input_source = "input"
        
        if self._steps:
            dependencies = [self._steps[-1].step_id]
            input_source = self._steps[-1].step_id
        
        self.add_transform_step(
            step_id=step_id,
            transformer=transformer,
            input_source=input_source,
            name=name,
            dependencies=dependencies
        )
        return self


class ParallelWorkflowBuilder(WorkflowBuilder):
    """Builder for parallel execution workflows"""
    
    def __init__(self):
        super().__init__()
        self._current_parallel_group: List[IWorkflowStep] = []
    
    def add_parallel_agent(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable],
        name: Optional[str] = None
    ) -> 'ParallelWorkflowBuilder':
        """Add agent step to current parallel group"""
        step = AgentStep(
            step_id=step_id,
            agent_id=agent_id,
            input_data=input_data,
            name=name
        )
        self._current_parallel_group.append(step)
        return self
    
    def add_parallel_tool(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable],
        name: Optional[str] = None
    ) -> 'ParallelWorkflowBuilder':
        """Add tool step to current parallel group"""
        step = ToolStep(
            step_id=step_id,
            tool_name=tool_name,
            parameters=parameters,
            name=name
        )
        self._current_parallel_group.append(step)
        return self
    
    def finish_parallel_group(self) -> 'ParallelWorkflowBuilder':
        """Finish current parallel group and add steps to workflow"""
        for step in self._current_parallel_group:
            self._steps.append(step)
        self._current_parallel_group = []
        return self
    
    def build(self) -> IWorkflow:
        """Build workflow, finishing any open parallel group"""
        if self._current_parallel_group:
            self.finish_parallel_group()
        return super().build()


# Convenience factory functions

def create_workflow(workflow_id: str, name: str) -> WorkflowBuilder:
    """Create a new workflow builder"""
    return WorkflowBuilder().start(workflow_id, name)


def create_linear_workflow(workflow_id: str, name: str) -> LinearWorkflowBuilder:
    """Create a linear workflow builder"""
    return LinearWorkflowBuilder().start(workflow_id, name)


def create_parallel_workflow(workflow_id: str, name: str) -> ParallelWorkflowBuilder:
    """Create a parallel workflow builder"""
    return ParallelWorkflowBuilder().start(workflow_id, name)


def create_simple_workflow(
    workflow_id: str,
    name: str,
    agent_chain: List[str],
    input_data: Optional[Dict[str, Any]] = None
) -> IWorkflow:
    """
    Create a simple linear workflow for multi-agent orchestration.
    
    This is the primary way to orchestrate multiple agents working together.
    Each agent in the chain receives the output from the previous agent,
    enabling collaborative task completion.
    
    Args:
        workflow_id: Unique workflow identifier
        name: Human-readable workflow name  
        agent_chain: List of agent IDs to execute in sequence
        input_data: Initial input data template (defaults to {"input": "..."})
    
    Returns:
        IWorkflow: Complete workflow ready for execution
        
    Raises:
        ValueError: If agent_chain is empty
        
    Example:
        >>> # Create and register specialized agents
        >>> researcher = await create_openai_agent("researcher")
        >>> summarizer = await create_openai_agent("summarizer")
        >>> register_agent(researcher)
        >>> register_agent(summarizer)
        >>> 
        >>> # Create orchestration workflow
        >>> workflow = create_simple_workflow(
        ...     workflow_id="research_task",
        ...     name="Research and Summarize",
        ...     agent_chain=["researcher", "summarizer"]
        ... )
        >>> 
        >>> # Execute orchestrated workflow
        >>> engine = get_workflow_engine()
        >>> result = await engine.execute_workflow(
        ...     workflow,
        ...     {"input": "AI in healthcare"}
        ... )
    """
    if not agent_chain:
        raise ValueError("Agent chain cannot be empty")
    
    builder = create_linear_workflow(workflow_id, name)
    
    for i, agent_id in enumerate(agent_chain):
        step_id = f"step_{i+1}_{agent_id}"
        
        if i == 0:
            # First step gets input data
            step_input = input_data or "${input}"
        else:
            # Subsequent steps get output from previous step
            prev_step_id = f"step_{i}_{agent_chain[i-1]}"
            step_input = f"${{{prev_step_id}}}"
        
        builder.then_agent(
            step_id=step_id,
            agent_id=agent_id,
            input_data=step_input,
            name=f"Execute {agent_id}"
        )
    
    return builder.build()


def create_analysis_workflow(
    workflow_id: str,
    data_source: str,
    analyzer_agents: List[str],
    reporter_agent: str = "report_generator"
) -> IWorkflow:
    """
    Create a common analysis workflow pattern.
    
    Pattern: Data extraction → Multiple parallel analyzers → Report generation
    """
    builder = create_workflow(workflow_id, f"Analysis Workflow: {workflow_id}")
    
    # Data extraction step
    builder.add_agent_step(
        "extract_data",
        "data_extractor",
        {"source": data_source},
        name="Extract Data"
    )
    
    # Parallel analysis steps
    analysis_step_ids = []
    for i, analyzer in enumerate(analyzer_agents):
        step_id = f"analyze_{i+1}_{analyzer}"
        analysis_step_ids.append(step_id)
        
        builder.add_agent_step(
            step_id,
            analyzer,
            lambda ctx: ctx.get_step_output("extract_data"),
            name=f"Analysis: {analyzer}",
            dependencies=["extract_data"]
        )
    
    # Report generation step (depends on all analysis steps)
    builder.add_agent_step(
        "generate_report",
        reporter_agent,
        lambda ctx: {
            "analysis_results": [ctx.get_step_output(step_id) for step_id in analysis_step_ids]
        },
        name="Generate Report",
        dependencies=analysis_step_ids
    )
    
    builder.set_execution_mode(ExecutionMode.PARALLEL)
    return builder.build()


def create_approval_workflow(
    workflow_id: str,
    processor_agent: str,
    reviewer_agent: str,
    approval_condition: Callable[[WorkflowContext], bool]
) -> IWorkflow:
    """
    Create an approval workflow with conditional execution.
    
    Pattern: Process → Review → Conditional approval/rejection
    """
    builder = create_workflow(workflow_id, f"Approval Workflow: {workflow_id}")
    
    # Processing step
    builder.add_agent_step(
        "process",
        processor_agent,
        "${input}",
        name="Process Request"
    )
    
    # Review step
    builder.add_agent_step(
        "review",
        reviewer_agent,
        lambda ctx: ctx.get_step_output("process"),
        name="Review Request",
        dependencies=["process"]
    )
    
    # Conditional approval
    builder.add_condition_step(
        "approval_check",
        approval_condition,
        true_step="approve",
        false_step="reject",
        name="Check Approval",
        dependencies=["review"]
    )
    
    # Approval step
    builder.add_agent_step(
        "approve",
        "approval_agent",
        lambda ctx: {
            "request": ctx.get_step_output("process"),
            "review": ctx.get_step_output("review"),
            "action": "approve"
        },
        name="Approve Request"
    )
    
    # Rejection step
    builder.add_agent_step(
        "reject",
        "approval_agent",
        lambda ctx: {
            "request": ctx.get_step_output("process"),
            "review": ctx.get_step_output("review"),
            "action": "reject"
        },
        name="Reject Request"
    )
    
    return builder.build()
