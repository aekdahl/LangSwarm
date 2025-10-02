"""
LangSwarm V2 Error Types

Comprehensive error type definitions with structured hierarchy,
rich context, and backward compatibility.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import sys


class ErrorSeverity(Enum):
    """Error severity levels for proper routing and handling"""
    CRITICAL = "critical"  # System halt required
    ERROR = "error"        # Operation failed, but system continues  
    WARNING = "warning"    # Potential issue, operation continues
    INFO = "info"          # Informational, no action needed


class ErrorCategory(Enum):
    """Error categories for better organization"""
    CONFIGURATION = "configuration"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    NETWORK = "network"
    PERMISSION = "permission"
    VALIDATION = "validation"


@dataclass
class ErrorContext:
    """Rich error context for debugging and user guidance"""
    component: str
    operation: str
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # Capture stack trace if not provided
        if self.stack_trace is None:
            self.stack_trace = ''.join(traceback.format_stack()[:-1])  # Exclude current frame
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            'component': self.component,
            'operation': self.operation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'metadata': self.metadata,
            'stack_trace': self.stack_trace
        }


class LangSwarmError(Exception):
    """
    Base error class for all LangSwarm V2 errors
    
    Provides structured error handling with rich context, severity levels,
    and user-friendly error messages with actionable suggestions.
    """
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.CONFIGURATION,
        context: Optional[ErrorContext] = None,
        suggestion: Optional[str] = None,
        cause: Optional[Exception] = None,
        user_facing: bool = True
    ):
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext("unknown", "unknown")
        self.suggestion = suggestion
        self.cause = cause
        self.user_facing = user_facing
        
        # Build formatted message
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message with context and suggestions"""
        if not self.user_facing:
            # Simple format for internal/debug errors
            return f"[{self.severity.value.upper()}] {self.message}"
        
        lines = [f"❌ {self.message}"]
        
        if self.context and self.context.component != "unknown":
            lines.append(f"🔍 Component: {self.context.component}")
            
        if self.context and self.context.operation != "unknown":
            lines.append(f"⚙️ Operation: {self.context.operation}")
        
        if self.suggestion:
            lines.append(f"💡 Suggestion: {self.suggestion}")
        
        if self.cause:
            lines.append(f"🔗 Caused by: {str(self.cause)}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context.to_dict() if self.context else None,
            'suggestion': self.suggestion,
            'cause': str(self.cause) if self.cause else None,
            'user_facing': self.user_facing,
            'formatted_message': str(self)
        }
    
    def is_critical(self) -> bool:
        """Check if this is a critical error requiring system halt"""
        return self.severity == ErrorSeverity.CRITICAL
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information"""
        debug_info = self.to_dict()
        if self.context and self.context.stack_trace:
            debug_info['stack_trace'] = self.context.stack_trace
        return debug_info


# Specific Error Types

class ConfigurationError(LangSwarmError):
    """Configuration-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )


class AgentError(LangSwarmError):
    """Agent-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AGENT,
            **kwargs
        )


class ToolError(LangSwarmError):
    """Tool execution errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.TOOL,
            **kwargs
        )


class WorkflowError(LangSwarmError):
    """Workflow execution errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.WORKFLOW,
            **kwargs
        )


class MemoryError(LangSwarmError):
    """Memory/storage related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.MEMORY,
            **kwargs
        )


class NetworkError(LangSwarmError):
    """Network/connectivity related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            **kwargs
        )


class PermissionError(LangSwarmError):
    """Permission/authorization related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            **kwargs
        )


class ValidationError(LangSwarmError):
    """Input/data validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )


class MiddlewareError(LangSwarmError):
    """Middleware processing errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.WORKFLOW,  # Middleware is part of workflow processing
            **kwargs
        )


class CriticalError(LangSwarmError):
    """Critical errors that require system halt"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


# Legacy Compatibility Aliases
# These will be removed in future versions but provide backward compatibility

# Common V1 error mappings
ConfigurationNotFoundError = ConfigurationError
InvalidAgentBehaviorError = AgentError  
UnknownToolError = ToolError
WorkflowNotFoundError = WorkflowError
InvalidWorkflowSyntaxError = ValidationError
InvalidMemoryTierError = ConfigurationError
ZeroConfigDependencyError = CriticalError
AgentToolError = ToolError
