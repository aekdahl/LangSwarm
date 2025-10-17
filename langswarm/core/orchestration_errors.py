"""
Orchestration-specific error handling for LangSwarm.

Provides clear, actionable error messages for common orchestration issues
to help developers quickly identify and resolve problems.
"""
from typing import List, Optional, Dict, Any
from langswarm.core.errors import LangSwarmError, ErrorContext


class OrchestrationError(LangSwarmError):
    """Base class for all orchestration-related errors."""
    pass


class AgentNotFoundError(OrchestrationError):
    """Raised when a workflow references an agent that isn't registered."""
    
    def __init__(
        self, 
        agent_id: str, 
        available_agents: Optional[List[str]] = None,
        workflow_id: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.available_agents = available_agents or []
        self.workflow_id = workflow_id
        
        # Build helpful message
        message = f"Agent '{agent_id}' not found in registry"
        if workflow_id:
            message += f" (referenced in workflow '{workflow_id}')"
        
        # Create suggestion
        suggestion = self._build_suggestion()
        
        context = ErrorContext(
            component="AgentRegistry",
            operation="get_agent",
            metadata={
                "agent_id": agent_id,
                "available_agents": self.available_agents,
                "workflow_id": workflow_id
            }
        )
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for resolving the error."""
        suggestions = [
            f"Make sure to register agent '{self.agent_id}' before using it in workflows:",
            f"",
            f"  from langswarm import create_openai_agent, register_agent",
            f"  ",
            f"  # Create the agent",
            f"  {self.agent_id} = await create_openai_agent(",
            f"      name='{self.agent_id}',",
            f"      model='gpt-3.5-turbo',",
            f"      system_prompt='Your agent instructions'",
            f"  )",
            f"  ",
            f"  # Register it for orchestration",
            f"  register_agent({self.agent_id})",
        ]
        
        if self.available_agents:
            suggestions.extend([
                "",
                "Currently registered agents:",
                *[f"  • {agent}" for agent in self.available_agents[:5]]
            ])
            
            # Check for similar names
            similar = [a for a in self.available_agents 
                      if self.agent_id.lower() in a.lower() or a.lower() in self.agent_id.lower()]
            if similar:
                suggestions.extend([
                    "",
                    "Did you mean one of these?",
                    *[f"  • {agent}" for agent in similar]
                ])
        
        return "\n".join(suggestions)


class WorkflowExecutionError(OrchestrationError):
    """Raised when workflow execution fails."""
    
    def __init__(
        self,
        workflow_id: str,
        step_id: Optional[str] = None,
        error: Optional[Exception] = None,
        message: Optional[str] = None
    ):
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.original_error = error
        
        # Build message
        if message:
            base_message = message
        elif error:
            base_message = f"Workflow '{workflow_id}' failed: {str(error)}"
        else:
            base_message = f"Workflow '{workflow_id}' failed"
            
        if step_id:
            base_message += f" at step '{step_id}'"
        
        # Create context
        context = ErrorContext(
            component="WorkflowEngine",
            operation="execute_workflow",
            metadata={
                "workflow_id": workflow_id,
                "step_id": step_id,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        # Build suggestion
        suggestion = self._build_suggestion()
        
        super().__init__(base_message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for debugging workflow failures."""
        suggestions = ["To debug workflow execution issues:"]
        
        if self.step_id:
            suggestions.extend([
                "",
                f"1. Check that agent for step '{self.step_id}' is properly registered",
                "2. Verify the input data format matches what the agent expects",
                "3. Check agent logs for more details about the failure"
            ])
        
        if self.original_error:
            error_type = type(self.original_error).__name__
            
            if "API" in error_type or "api" in str(self.original_error).lower():
                suggestions.extend([
                    "",
                    "API-related error detected:",
                    "• Verify your API key is set correctly",
                    "• Check API rate limits and quotas",
                    "• Ensure the model name is valid"
                ])
            elif "timeout" in str(self.original_error).lower():
                suggestions.extend([
                    "",
                    "Timeout error detected:",
                    "• Consider increasing timeout settings",
                    "• Check if the task is too complex",
                    "• Try breaking into smaller subtasks"
                ])
        
        suggestions.extend([
            "",
            "Enable debug logging for more details:",
            "  import logging",
            "  logging.basicConfig(level=logging.DEBUG)"
        ])
        
        return "\n".join(suggestions)


class WorkflowValidationError(OrchestrationError):
    """Raised when workflow configuration is invalid."""
    
    def __init__(
        self,
        workflow_id: str,
        validation_errors: List[str],
        workflow_data: Optional[Dict[str, Any]] = None
    ):
        self.workflow_id = workflow_id
        self.validation_errors = validation_errors
        self.workflow_data = workflow_data
        
        # Build message
        message = f"Workflow '{workflow_id}' validation failed:"
        for error in validation_errors:
            message += f"\n  • {error}"
        
        # Create context
        context = ErrorContext(
            component="WorkflowValidator",
            operation="validate_workflow",
            metadata={
                "workflow_id": workflow_id,
                "error_count": len(validation_errors),
                "errors": validation_errors
            }
        )
        
        # Build suggestion
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for fixing validation errors."""
        suggestions = ["Fix the following validation issues:"]
        
        # Check common issues
        for error in self.validation_errors:
            if "empty" in error.lower():
                suggestions.extend([
                    "",
                    "Empty workflow detected. Add at least one agent:",
                    "  workflow = create_simple_workflow(",
                    "      workflow_id='my_workflow',",
                    "      name='My Workflow',",
                    "      agent_chain=['agent1', 'agent2']",
                    "  )"
                ])
            elif "agent" in error.lower() and "not found" in error.lower():
                suggestions.extend([
                    "",
                    "Missing agent reference. Ensure all agents are registered:",
                    "  register_agent(my_agent)"
                ])
            elif "circular" in error.lower():
                suggestions.extend([
                    "",
                    "Circular dependency detected. Review your workflow:",
                    "• Ensure agents don't reference each other in a loop",
                    "• Use conditional steps to break cycles if needed"
                ])
        
        return "\n".join(suggestions)


class AgentExecutionError(OrchestrationError):
    """Raised when an agent fails during workflow execution."""
    
    def __init__(
        self,
        agent_id: str,
        step_id: str,
        error: Optional[Exception] = None,
        input_data: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.step_id = step_id
        self.original_error = error
        self.input_data = input_data
        
        # Build message
        message = f"Agent '{agent_id}' failed at step '{step_id}'"
        if error:
            message += f": {str(error)}"
        
        # Create context
        context = ErrorContext(
            component="AgentExecutor",
            operation="execute_agent",
            metadata={
                "agent_id": agent_id,
                "step_id": step_id,
                "error_type": type(error).__name__ if error else None,
                "has_input": input_data is not None
            }
        )
        
        # Build suggestion
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for agent execution failures."""
        suggestions = [f"Debug agent '{self.agent_id}' execution:"]
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "none" in error_str or "null" in error_str:
                suggestions.extend([
                    "",
                    "Null/None error detected:",
                    "• Check if the agent is properly initialized",
                    "• Verify the agent has required configuration",
                    "• Ensure previous steps provided valid output"
                ])
            elif "key" in error_str:
                suggestions.extend([
                    "",
                    "Key error detected:",
                    "• Check the input data structure",
                    "• Verify agent expects the provided data format",
                    "• Add data validation in your workflow"
                ])
        
        if self.input_data is not None:
            suggestions.extend([
                "",
                "Input data provided to agent:",
                f"  Type: {type(self.input_data).__name__}",
                f"  Preview: {str(self.input_data)[:100]}..."
            ])
        
        suggestions.extend([
            "",
            "Test the agent independently:",
            f"  agent = get_agent('{self.agent_id}')",
            "  result = await agent.execute('test input')"
        ])
        
        return "\n".join(suggestions)


class DataPassingError(OrchestrationError):
    """Raised when data cannot be passed between workflow steps."""
    
    def __init__(
        self,
        from_step: str,
        to_step: str,
        reason: str,
        data_preview: Optional[str] = None
    ):
        self.from_step = from_step
        self.to_step = to_step
        self.reason = reason
        self.data_preview = data_preview
        
        message = f"Failed to pass data from '{from_step}' to '{to_step}': {reason}"
        
        context = ErrorContext(
            component="WorkflowDataFlow",
            operation="pass_data",
            metadata={
                "from_step": from_step,
                "to_step": to_step,
                "reason": reason
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for data passing issues."""
        suggestions = ["Fix data passing between workflow steps:"]
        
        if "serializ" in self.reason.lower():
            suggestions.extend([
                "",
                "Serialization error detected:",
                "• Ensure data is JSON-serializable",
                "• Convert complex objects to dictionaries",
                "• Remove circular references"
            ])
        elif "type" in self.reason.lower():
            suggestions.extend([
                "",
                "Type mismatch detected:",
                "• Check that output type matches expected input",
                "• Add type conversion between steps if needed",
                "• Use consistent data formats throughout workflow"
            ])
        
        if self.data_preview:
            suggestions.extend([
                "",
                "Data preview:",
                f"  {self.data_preview[:200]}..."
            ])
        
        suggestions.extend([
            "",
            "Add data validation between steps:",
            "  # In your workflow definition",
            "  .add_validation_step(validate_data)",
            "  .add_transform_step(transform_for_next_agent)"
        ])
        
        return "\n".join(suggestions)


# Convenience functions for creating common errors
def agent_not_found(agent_id: str, available_agents: Optional[List[str]] = None) -> AgentNotFoundError:
    """Create an AgentNotFoundError with context."""
    return AgentNotFoundError(agent_id, available_agents)


def workflow_failed(
    workflow_id: str, 
    step_id: Optional[str] = None,
    error: Optional[Exception] = None
) -> WorkflowExecutionError:
    """Create a WorkflowExecutionError with context."""
    return WorkflowExecutionError(workflow_id, step_id, error)


def validation_failed(
    workflow_id: str,
    errors: List[str]
) -> WorkflowValidationError:
    """Create a WorkflowValidationError with context."""
    return WorkflowValidationError(workflow_id, errors)


def agent_failed(
    agent_id: str,
    step_id: str,
    error: Optional[Exception] = None
) -> AgentExecutionError:
    """Create an AgentExecutionError with context."""
    return AgentExecutionError(agent_id, step_id, error)


def data_passing_failed(
    from_step: str,
    to_step: str,
    reason: str
) -> DataPassingError:
    """Create a DataPassingError with context."""
    return DataPassingError(from_step, to_step, reason)