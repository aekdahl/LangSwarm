"""
Custom Exceptions for Intelligent Navigation

This module defines custom exceptions used throughout the navigation system
for better error handling and debugging.
"""


class NavigationError(Exception):
    """Base exception for navigation-related errors"""
    
    def __init__(self, message: str, step_id: str = None, workflow_id: str = None):
        self.message = message
        self.step_id = step_id
        self.workflow_id = workflow_id
        super().__init__(self.message)


class InvalidStepError(NavigationError):
    """Raised when an invalid step is selected or referenced"""
    
    def __init__(self, step_id: str, available_steps: list = None, workflow_id: str = None):
        self.available_steps = available_steps or []
        message = f"Invalid step '{step_id}'"
        if available_steps:
            message += f". Available steps: {', '.join(available_steps)}"
        super().__init__(message, step_id, workflow_id)


class NoAvailableStepsError(NavigationError):
    """Raised when no steps are available for navigation"""
    
    def __init__(self, workflow_id: str = None, context: dict = None):
        self.context = context
        message = "No steps available for navigation"
        if context:
            message += f" with context: {context}"
        super().__init__(message, workflow_id=workflow_id)


class NavigationTimeoutError(NavigationError):
    """Raised when navigation decision takes too long"""
    
    def __init__(self, timeout_seconds: int, step_id: str = None, workflow_id: str = None):
        self.timeout_seconds = timeout_seconds
        message = f"Navigation decision timed out after {timeout_seconds} seconds"
        super().__init__(message, step_id, workflow_id)


class InvalidNavigationConfigError(NavigationError):
    """Raised when navigation configuration is invalid"""
    
    def __init__(self, config_issue: str, workflow_id: str = None):
        self.config_issue = config_issue
        message = f"Invalid navigation configuration: {config_issue}"
        super().__init__(message, workflow_id=workflow_id)


class AgentNavigationError(NavigationError):
    """Raised when agent fails to make navigation decision"""
    
    def __init__(self, agent_id: str, reason: str, step_id: str = None, workflow_id: str = None):
        self.agent_id = agent_id
        self.reason = reason
        message = f"Agent '{agent_id}' failed to navigate: {reason}"
        super().__init__(message, step_id, workflow_id)


class ConditionEvaluationError(NavigationError):
    """Raised when condition evaluation fails"""
    
    def __init__(self, condition: str, context: dict, error: str, step_id: str = None, workflow_id: str = None):
        self.condition = condition
        self.context = context
        self.error = error
        message = f"Condition evaluation failed for '{condition}': {error}"
        super().__init__(message, step_id, workflow_id)


class NavigationLoopError(NavigationError):
    """Raised when an infinite navigation loop is detected"""
    
    def __init__(self, loop_steps: list, workflow_id: str = None):
        self.loop_steps = loop_steps
        message = f"Navigation loop detected: {' -> '.join(loop_steps)}"
        super().__init__(message, workflow_id=workflow_id)


class InsufficientPermissionsError(NavigationError):
    """Raised when agent lacks permissions for navigation decision"""
    
    def __init__(self, agent_id: str, required_permissions: list, step_id: str = None, workflow_id: str = None):
        self.agent_id = agent_id
        self.required_permissions = required_permissions
        message = f"Agent '{agent_id}' lacks required permissions: {', '.join(required_permissions)}"
        super().__init__(message, step_id, workflow_id)


class NavigationContextError(NavigationError):
    """Raised when navigation context is invalid or missing"""
    
    def __init__(self, context_issue: str, step_id: str = None, workflow_id: str = None):
        self.context_issue = context_issue
        message = f"Navigation context error: {context_issue}"
        super().__init__(message, step_id, workflow_id) 