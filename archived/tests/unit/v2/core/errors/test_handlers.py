"""
Unit tests for LangSwarm V2 error handlers
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from io import StringIO
import logging

from langswarm.v2.core.errors.handlers import (
    ErrorHandler,
    handle_error,
    get_error_handler,
    register_recovery_strategy
)
from langswarm.v2.core.errors.types import (
    LangSwarmError,
    ConfigurationError,
    AgentError,
    ToolError,
    CriticalError,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext
)


class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = ErrorHandler()
        # Reset circuit breaker state
        self.handler._critical_error_count = 0
        self.handler._circuit_breaker_active = False
        self.handler._last_critical_error_time = 0
    
    def test_handler_initialization(self):
        """Test ErrorHandler initialization"""
        handler = ErrorHandler()
        
        assert len(handler._handlers) == 4  # CRITICAL, ERROR, WARNING, INFO
        assert len(handler._error_counts) == 0
        assert len(handler._error_history) == 0
        assert handler._max_history == 1000
        assert handler._critical_error_count == 0
        assert handler._circuit_breaker_active is False
    
    def test_handle_langswarm_error(self):
        """Test handling LangSwarmError directly"""
        error = ConfigurationError("Test config error")
        
        result = self.handler.handle(error, "test_component")
        
        assert result is True  # Should continue
        assert len(self.handler._error_history) == 1
        assert "configuration:test_component" in self.handler._error_counts
        assert self.handler._error_counts["configuration:test_component"] == 1
    
    def test_handle_generic_exception(self):
        """Test handling generic Python exceptions"""
        error = ValueError("Generic error")
        
        result = self.handler.handle(error, "test_component")
        
        assert result is True  # Should continue
        assert len(self.handler._error_history) == 1
        
        # Check that it was converted to LangSwarmError
        history_item = self.handler._error_history[0]
        assert "LangSwarmError" in history_item["error_type"]
    
    @patch('builtins.print')
    @patch('langswarm.v2.core.errors.handlers.logger')
    def test_handle_critical_error(self, mock_logger, mock_print):
        """Test handling critical errors"""
        error = CriticalError("System failure")
        
        result = self.handler.handle(error, "critical_component")
        
        assert result is False  # Should halt
        mock_logger.critical.assert_called()
        mock_print.assert_called()
        
        # Check print output contains system halt message
        print_call = mock_print.call_args[0][0]
        assert "CRITICAL FAILURE - SYSTEM HALTED" in print_call
    
    @patch('langswarm.v2.core.errors.handlers.logger')
    def test_handle_error_severity(self, mock_logger):
        """Test handling different error severities"""
        error_error = LangSwarmError("Error", severity=ErrorSeverity.ERROR)
        warning_error = LangSwarmError("Warning", severity=ErrorSeverity.WARNING)
        info_error = LangSwarmError("Info", severity=ErrorSeverity.INFO)
        
        # Test ERROR severity
        result = self.handler.handle(error_error)
        assert result is True
        mock_logger.error.assert_called()
        
        # Test WARNING severity
        result = self.handler.handle(warning_error)
        assert result is True
        mock_logger.warning.assert_called()
        
        # Test INFO severity
        result = self.handler.handle(info_error)
        assert result is True
        mock_logger.info.assert_called()
    
    def test_convert_to_langswarm_error_auth(self):
        """Test converting authentication errors"""
        auth_error = Exception("API key invalid")
        
        result = self.handler.handle(auth_error, "auth_component")
        
        assert result is False  # Auth errors are critical
        history_item = self.handler._error_history[0]
        assert "CriticalError" in history_item["error_type"]
        assert "auth_component" == history_item["component"]
    
    def test_convert_to_langswarm_error_config(self):
        """Test converting configuration errors"""
        config_error = Exception("YAML parse error")
        
        result = self.handler.handle(config_error, "config_component")
        
        assert result is True
        history_item = self.handler._error_history[0]
        assert "ConfigurationError" in history_item["error_type"]
        assert "config_component" == history_item["component"]
    
    def test_convert_to_langswarm_error_network(self):
        """Test converting network errors"""
        network_error = Exception("Connection timeout")
        
        result = self.handler.handle(network_error, "network_component")
        
        assert result is True
        history_item = self.handler._error_history[0]
        assert "NetworkError" in history_item["error_type"]
        assert "network_component" == history_item["component"]
    
    def test_convert_to_langswarm_error_permission(self):
        """Test converting permission errors"""
        perm_error = Exception("Access forbidden")
        
        result = self.handler.handle(perm_error, "file_component")
        
        assert result is True
        history_item = self.handler._error_history[0]
        assert "PermissionError" in history_item["error_type"]
        assert "file_component" == history_item["component"]
    
    def test_convert_to_langswarm_error_generic(self):
        """Test converting generic errors"""
        generic_error = Exception("Something went wrong")
        
        result = self.handler.handle(generic_error, "generic_component")
        
        assert result is True
        history_item = self.handler._error_history[0]
        assert "LangSwarmError" in history_item["error_type"]
        assert "generic_component" == history_item["component"]
    
    def test_error_counting(self):
        """Test error counting and tracking"""
        error1 = ConfigurationError("Error 1")
        error2 = ConfigurationError("Error 2")
        error3 = AgentError("Error 3")
        
        self.handler.handle(error1, "component1")
        self.handler.handle(error2, "component1")
        self.handler.handle(error3, "component2")
        
        assert self.handler._error_counts["configuration:component1"] == 2
        assert self.handler._error_counts["agent:component2"] == 1
        assert len(self.handler._error_history) == 3
    
    def test_error_history_trimming(self):
        """Test error history trimming when max size exceeded"""
        # Set small max history for testing
        self.handler._max_history = 3
        
        # Add more errors than max history
        for i in range(5):
            error = ConfigurationError(f"Error {i}")
            self.handler.handle(error, f"component{i}")
        
        # Should only keep last 3 errors
        assert len(self.handler._error_history) == 3
        
        # Should keep the last 3 errors (2, 3, 4)
        messages = [item["message"] for item in self.handler._error_history]
        assert "Error 2" in messages
        assert "Error 3" in messages
        assert "Error 4" in messages
        assert "Error 0" not in messages
        assert "Error 1" not in messages
    
    def test_circuit_breaker_activation(self):
        """Test circuit breaker activation on multiple critical errors"""
        # Set low threshold for testing
        self.handler._critical_error_threshold = 2
        
        # First critical error
        error1 = CriticalError("Critical 1")
        result1 = self.handler.handle(error1, "component1")
        assert result1 is False
        assert self.handler._circuit_breaker_active is False
        assert self.handler._critical_error_count == 1
        
        # Second critical error - should activate circuit breaker
        error2 = CriticalError("Critical 2")
        result2 = self.handler.handle(error2, "component2")
        assert result2 is False
        assert self.handler._circuit_breaker_active is True
        assert self.handler._critical_error_count == 2
        
        # Third critical error - should be suppressed by circuit breaker
        with patch('langswarm.v2.core.errors.handlers.logger') as mock_logger:
            error3 = CriticalError("Critical 3")
            result3 = self.handler.handle(error3, "component3")
            assert result3 is False
            mock_logger.critical.assert_called_with(
                "Circuit breaker active - suppressing additional critical errors"
            )
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset after timeout"""
        # Set up circuit breaker
        self.handler._critical_error_threshold = 1
        self.handler._circuit_breaker_timeout = 1  # 1 second timeout
        
        # Activate circuit breaker
        error1 = CriticalError("Critical")
        self.handler.handle(error1, "component")
        assert self.handler._circuit_breaker_active is True
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Handle another error - should reset circuit breaker first
        error2 = CriticalError("Critical 2")
        with patch('langswarm.v2.core.errors.handlers.logger') as mock_logger:
            result = self.handler.handle(error2, "component")
            assert result is False
            # Should log circuit breaker reset
            mock_logger.info.assert_called_with(
                "Circuit breaker reset - critical error timeout passed"
            )
    
    def test_recovery_strategy_registration(self):
        """Test recovery strategy registration"""
        def mock_recovery(error):
            return True
        
        self.handler.register_recovery_strategy("tool:ToolError", mock_recovery)
        
        assert "tool:ToolError" in self.handler._recovery_strategies
        assert self.handler._recovery_strategies["tool:ToolError"] == mock_recovery
    
    def test_recovery_strategy_execution(self):
        """Test recovery strategy execution"""
        recovery_called = False
        
        def mock_recovery(error):
            nonlocal recovery_called
            recovery_called = True
            return True
        
        # Register recovery strategy
        self.handler.register_recovery_strategy("tool:CriticalError", mock_recovery)
        
        # Create error that should halt but has recovery
        error = CriticalError("Tool failure", category=ErrorCategory.TOOL)
        
        # Mock the _handle_critical to return False
        with patch.object(self.handler, '_handle_critical', return_value=False):
            result = self.handler.handle(error, "tool_component")
        
        assert result is True  # Recovery should allow continuation
        assert recovery_called is True
    
    def test_recovery_strategy_failure(self):
        """Test recovery strategy failure handling"""
        def failing_recovery(error):
            raise Exception("Recovery failed")
        
        # Register failing recovery strategy
        self.handler.register_recovery_strategy("tool:CriticalError", failing_recovery)
        
        # Create error that needs recovery
        error = CriticalError("Tool failure", category=ErrorCategory.TOOL)
        
        with patch.object(self.handler, '_handle_critical', return_value=False):
            with patch('langswarm.v2.core.errors.handlers.logger') as mock_logger:
                result = self.handler.handle(error, "tool_component")
                
                assert result is False  # Should fail since recovery failed
                mock_logger.error.assert_called()
    
    def test_get_error_statistics(self):
        """Test getting error statistics"""
        # Add some errors
        error1 = ConfigurationError("Config error")
        error2 = AgentError("Agent error")
        
        self.handler.handle(error1, "component1")
        self.handler.handle(error2, "component2")
        
        stats = self.handler.get_error_statistics()
        
        assert isinstance(stats, dict)
        assert "error_counts" in stats
        assert "total_errors" in stats
        assert "critical_error_count" in stats
        assert "circuit_breaker_active" in stats
        assert "recent_errors" in stats
        
        assert stats["total_errors"] == 2
        assert stats["critical_error_count"] == 0
        assert stats["circuit_breaker_active"] is False
        assert len(stats["recent_errors"]) == 2
    
    def test_reset_statistics(self):
        """Test resetting error statistics"""
        # Add some errors
        error = ConfigurationError("Config error")
        self.handler.handle(error, "component")
        
        # Verify statistics exist
        assert len(self.handler._error_counts) > 0
        assert len(self.handler._error_history) > 0
        
        # Reset statistics
        self.handler.reset_statistics()
        
        # Verify statistics are cleared
        assert len(self.handler._error_counts) == 0
        assert len(self.handler._error_history) == 0
        assert self.handler._critical_error_count == 0
        assert self.handler._circuit_breaker_active is False


class TestGlobalErrorHandling:
    """Test global error handling functions"""
    
    def test_handle_error_function(self):
        """Test global handle_error function"""
        error = ConfigurationError("Global error test")
        
        result = handle_error(error, "global_component")
        
        assert result is True
        
        # Verify it was handled by global handler
        global_handler = get_error_handler()
        assert len(global_handler._error_history) > 0
    
    def test_get_error_handler(self):
        """Test getting global error handler"""
        handler = get_error_handler()
        
        assert isinstance(handler, ErrorHandler)
        assert handler is get_error_handler()  # Should be singleton
    
    def test_register_recovery_strategy_global(self):
        """Test global recovery strategy registration"""
        def mock_recovery(error):
            return True
        
        register_recovery_strategy("global:TestError", mock_recovery)
        
        global_handler = get_error_handler()
        assert "global:TestError" in global_handler._recovery_strategies


class TestErrorHandlerEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = ErrorHandler()
    
    def test_handle_none_error(self):
        """Test handling None as error"""
        # Should handle gracefully by converting to generic error
        result = self.handler.handle(None, "component")
        assert result is True  # Should continue after handling None error
    
    def test_handle_error_with_empty_component(self):
        """Test handling error with empty component name"""
        error = ConfigurationError("Test error")
        
        result = self.handler.handle(error, "")
        
        assert result is True
        assert len(self.handler._error_history) == 1
    
    def test_error_with_circular_cause(self):
        """Test error with circular causation (edge case)"""
        error1 = ConfigurationError("Error 1")
        error2 = ConfigurationError("Error 2", cause=error1)
        error1.cause = error2  # Create circular reference
        
        # Should handle gracefully without infinite recursion
        result = self.handler.handle(error2, "component")
        assert result is True
    
    def test_handler_with_very_long_error_message(self):
        """Test handler with extremely long error message"""
        long_message = "x" * 100000  # 100KB message
        error = ConfigurationError(long_message)
        
        result = self.handler.handle(error, "component")
        
        assert result is True
        assert len(self.handler._error_history) == 1
    
    def test_handler_with_unicode_error_message(self):
        """Test handler with unicode error message"""
        unicode_message = "测试错误 🚨 Tëst Érrör"
        error = ConfigurationError(unicode_message)
        
        result = self.handler.handle(error, "component")
        
        assert result is True
        history_item = self.handler._error_history[0]
        assert history_item["message"] == unicode_message
    
    @patch('time.time')
    def test_error_history_timestamp_handling(self, mock_time):
        """Test error history timestamp handling"""
        mock_time.return_value = 1234567890.0
        
        error = ConfigurationError("Time test")
        self.handler.handle(error, "component")
        
        history_item = self.handler._error_history[0]
        assert history_item["timestamp"] == 1234567890.0
