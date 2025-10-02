"""
Unit tests for LangSwarm V2 error types
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from langswarm.v2.core.errors.types import (
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
    CriticalError
)


class TestErrorSeverity:
    """Test ErrorSeverity enum"""
    
    def test_severity_values(self):
        """Test that severity enum has correct values"""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"
    
    def test_severity_ordering(self):
        """Test that severities can be compared"""
        # Note: Enum comparison is by identity, not value
        # We'll test this in the error handler where ordering matters
        assert ErrorSeverity.CRITICAL != ErrorSeverity.ERROR
        assert ErrorSeverity.WARNING != ErrorSeverity.INFO


class TestErrorCategory:
    """Test ErrorCategory enum"""
    
    def test_category_values(self):
        """Test that category enum has correct values"""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.AGENT.value == "agent"
        assert ErrorCategory.TOOL.value == "tool"
        assert ErrorCategory.WORKFLOW.value == "workflow"
        assert ErrorCategory.MEMORY.value == "memory"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.VALIDATION.value == "validation"


class TestErrorContext:
    """Test ErrorContext dataclass"""
    
    def test_context_creation_minimal(self):
        """Test creating context with minimal required fields"""
        context = ErrorContext("test_component", "test_operation")
        
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert isinstance(context.timestamp, datetime)
        assert context.user_id is None
        assert context.session_id is None
        assert context.request_id is None
        assert isinstance(context.metadata, dict)
        assert len(context.metadata) == 0
        assert isinstance(context.stack_trace, str)
        assert len(context.stack_trace) > 0
    
    def test_context_creation_full(self):
        """Test creating context with all fields"""
        timestamp = datetime.now()
        metadata = {"key": "value"}
        
        context = ErrorContext(
            component="test_component",
            operation="test_operation",
            timestamp=timestamp,
            user_id="user123",
            session_id="session456",
            request_id="req789",
            metadata=metadata,
            stack_trace="custom_stack_trace"
        )
        
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert context.timestamp == timestamp
        assert context.user_id == "user123"
        assert context.session_id == "session456" 
        assert context.request_id == "req789"
        assert context.metadata == metadata
        assert context.stack_trace == "custom_stack_trace"
    
    def test_context_to_dict(self):
        """Test converting context to dictionary"""
        context = ErrorContext(
            "test_component", 
            "test_operation",
            user_id="user123"
        )
        
        context_dict = context.to_dict()
        
        assert isinstance(context_dict, dict)
        assert context_dict["component"] == "test_component"
        assert context_dict["operation"] == "test_operation"
        assert context_dict["user_id"] == "user123"
        assert isinstance(context_dict["timestamp"], str)  # ISO format
        assert "metadata" in context_dict
        assert "stack_trace" in context_dict


class TestLangSwarmError:
    """Test LangSwarmError base class"""
    
    def test_error_creation_minimal(self):
        """Test creating error with minimal parameters"""
        error = LangSwarmError("Test error message")
        
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.ERROR
        assert error.category == ErrorCategory.CONFIGURATION
        assert isinstance(error.context, ErrorContext)
        assert error.suggestion is None
        assert error.cause is None
        assert error.user_facing is True
    
    def test_error_creation_full(self):
        """Test creating error with all parameters"""
        context = ErrorContext("test_component", "test_operation")
        cause = ValueError("Original error")
        
        error = LangSwarmError(
            message="Test error message",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.AGENT,
            context=context,
            suggestion="Try restarting",
            cause=cause,
            user_facing=False
        )
        
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.category == ErrorCategory.AGENT
        assert error.context == context
        assert error.suggestion == "Try restarting"
        assert error.cause == cause
        assert error.user_facing is False
    
    def test_error_message_formatting_user_facing(self):
        """Test error message formatting for user-facing errors"""
        context = ErrorContext("config_loader", "load_yaml")
        error = LangSwarmError(
            "Configuration file not found",
            context=context,
            suggestion="Check file path and permissions",
            user_facing=True
        )
        
        formatted = str(error)
        assert "❌ Configuration file not found" in formatted
        assert "🔍 Component: config_loader" in formatted
        assert "⚙️ Operation: load_yaml" in formatted
        assert "💡 Suggestion: Check file path and permissions" in formatted
    
    def test_error_message_formatting_internal(self):
        """Test error message formatting for internal errors"""
        error = LangSwarmError(
            "Internal processing error",
            severity=ErrorSeverity.WARNING,
            user_facing=False
        )
        
        formatted = str(error)
        assert formatted == "[WARNING] Internal processing error"
    
    def test_error_message_with_cause(self):
        """Test error message formatting with cause"""
        cause = ValueError("Original error")
        error = LangSwarmError(
            "Wrapper error",
            cause=cause,
            user_facing=True
        )
        
        formatted = str(error)
        assert "❌ Wrapper error" in formatted
        assert "🔗 Caused by: Original error" in formatted
    
    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        context = ErrorContext("test_component", "test_operation")
        error = LangSwarmError(
            "Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TOOL,
            context=context,
            suggestion="Test suggestion"
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "LangSwarmError"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "error"
        assert error_dict["category"] == "tool"
        assert error_dict["suggestion"] == "Test suggestion"
        assert error_dict["user_facing"] is True
        assert isinstance(error_dict["context"], dict)
        assert isinstance(error_dict["formatted_message"], str)
    
    def test_is_critical(self):
        """Test critical error detection"""
        critical_error = LangSwarmError("Critical", severity=ErrorSeverity.CRITICAL)
        regular_error = LangSwarmError("Regular", severity=ErrorSeverity.ERROR)
        
        assert critical_error.is_critical() is True
        assert regular_error.is_critical() is False
    
    def test_get_debug_info(self):
        """Test getting debug information"""
        context = ErrorContext("test_component", "test_operation")
        error = LangSwarmError("Test error", context=context)
        
        debug_info = error.get_debug_info()
        
        assert isinstance(debug_info, dict)
        assert "error_type" in debug_info
        assert "message" in debug_info
        assert "stack_trace" in debug_info
        assert debug_info["stack_trace"] is not None


class TestSpecificErrorTypes:
    """Test specific error type implementations"""
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Invalid config")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.message == "Invalid config"
    
    def test_agent_error(self):
        """Test AgentError"""
        error = AgentError("Agent failed")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.AGENT
        assert error.message == "Agent failed"
    
    def test_tool_error(self):
        """Test ToolError"""
        error = ToolError("Tool execution failed")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.TOOL
        assert error.message == "Tool execution failed"
    
    def test_workflow_error(self):
        """Test WorkflowError"""
        error = WorkflowError("Workflow failed")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.WORKFLOW
        assert error.message == "Workflow failed"
    
    def test_memory_error(self):
        """Test MemoryError"""
        error = MemoryError("Memory operation failed")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.MEMORY
        assert error.message == "Memory operation failed"
    
    def test_network_error(self):
        """Test NetworkError"""
        error = NetworkError("Network timeout")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.NETWORK
        assert error.message == "Network timeout"
    
    def test_permission_error(self):
        """Test PermissionError"""
        error = PermissionError("Access denied")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.PERMISSION
        assert error.message == "Access denied"
    
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input")
        
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.VALIDATION
        assert error.message == "Invalid input"
    
    def test_critical_error(self):
        """Test CriticalError"""
        error = CriticalError("System failure")
        
        assert isinstance(error, LangSwarmError)
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.message == "System failure"
        assert error.is_critical() is True


class TestLegacyCompatibility:
    """Test backward compatibility with V1 errors"""
    
    def test_legacy_error_aliases_exist(self):
        """Test that legacy error aliases are available"""
        from langswarm.v2.core.errors.types import (
            ConfigurationNotFoundError,
            InvalidAgentBehaviorError,
            UnknownToolError,
            WorkflowNotFoundError,
            InvalidWorkflowSyntaxError,
            InvalidMemoryTierError,
            ZeroConfigDependencyError,
            AgentToolError
        )
        
        # Test that aliases point to correct new types
        assert ConfigurationNotFoundError == ConfigurationError
        assert InvalidAgentBehaviorError == AgentError
        assert UnknownToolError == ToolError
        assert WorkflowNotFoundError == WorkflowError
        assert InvalidWorkflowSyntaxError == ValidationError
        assert InvalidMemoryTierError == ConfigurationError
        assert ZeroConfigDependencyError == CriticalError
        assert AgentToolError == ToolError
    
    def test_legacy_error_instantiation(self):
        """Test that legacy errors can be instantiated"""
        from langswarm.v2.core.errors.types import ConfigurationNotFoundError
        
        error = ConfigurationNotFoundError("Config not found")
        
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, LangSwarmError)
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.message == "Config not found"


class TestErrorEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_message(self):
        """Test error with empty message"""
        error = LangSwarmError("")
        assert error.message == ""
        assert "❌ " in str(error)
    
    def test_very_long_message(self):
        """Test error with very long message"""
        long_message = "x" * 10000
        error = LangSwarmError(long_message)
        
        assert error.message == long_message
        assert long_message in str(error)
    
    def test_unicode_message(self):
        """Test error with unicode characters"""
        unicode_message = "测试错误 🚨 Tëst Érrör"
        error = LangSwarmError(unicode_message)
        
        assert error.message == unicode_message
        assert unicode_message in str(error)
    
    def test_context_with_none_component(self):
        """Test context creation with None values"""
        # This should be handled gracefully
        context = ErrorContext(None, None)
        assert context.component is None
        assert context.operation is None
