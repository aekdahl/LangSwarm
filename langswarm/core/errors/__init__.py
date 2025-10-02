"""
LangSwarm V2 Error System

Unified error handling system with structured hierarchy, rich context,
and backward compatibility with V1 errors.

Usage:
    from langswarm.core.errors import LangSwarmError, ConfigurationError
    
    # Create error with rich context
    error = ConfigurationError(
        "Invalid configuration format",
        context=ErrorContext("config_loader", "load_yaml"),
        suggestion="Check YAML syntax and required fields"
    )
"""

from .types import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    LangSwarmError,
    ConfigurationError,
    AgentError,
    ToolError,
    WorkflowError,
    MemoryError,
    NetworkError,
    PermissionError,
    ValidationError,
    MiddlewareError,
    CriticalError
)

from .handlers import (
    ErrorHandler,
    handle_error,
    get_error_handler,
    register_recovery_strategy
)

__all__ = [
    # Error Types
    'ErrorSeverity',
    'ErrorCategory', 
    'ErrorContext',
    'LangSwarmError',
    'ConfigurationError',
    'AgentError',
    'ToolError',
    'WorkflowError',
    'MemoryError',
    'NetworkError',
    'PermissionError',
    'ValidationError',
    'MiddlewareError',
    'CriticalError',
    
    # Error Handling
    'ErrorHandler',
    'handle_error',
    'get_error_handler',
    'register_recovery_strategy'
]
