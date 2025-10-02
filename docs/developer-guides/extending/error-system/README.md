# Extending the LangSwarm V2 Error System

**Guide for developers building custom errors and error handling in LangSwarm V2**

## 🎯 Overview

The LangSwarm V2 error system is designed to be extensible while maintaining consistency. This guide shows you how to create custom error types, extend error handling, and integrate with the centralized error management system.

---

## 🏗️ Creating Custom Error Types

### **Basic Custom Error**

```python
from langswarm.core.errors import LangSwarmError, ErrorCategory, ErrorSeverity

class MyCustomError(LangSwarmError):
    """Custom error for my specific use case"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,  # Choose appropriate category
            severity=ErrorSeverity.ERROR,       # Choose appropriate severity
            **kwargs
        )
```

### **Specialized Custom Error with Context**

```python
from langswarm.core.errors import (
    LangSwarmError, ErrorCategory, ErrorContext, ErrorSeverity
)

class DatabaseConnectionError(LangSwarmError):
    """Database connection specific error with rich context"""
    
    def __init__(
        self, 
        database_type: str, 
        connection_string: str, 
        underlying_error: Exception = None,
        **kwargs
    ):
        # Create rich context
        context = ErrorContext(
            component="database_connector",
            operation="establish_connection",
            metadata={
                "database_type": database_type,
                "connection_string": self._sanitize_connection_string(connection_string),
                "error_type": type(underlying_error).__name__ if underlying_error else None
            }
        )
        
        # Create helpful suggestion
        suggestion = self._generate_suggestion(database_type, underlying_error)
        
        super().__init__(
            message=f"Failed to connect to {database_type} database",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            context=context,
            suggestion=suggestion,
            cause=underlying_error,
            **kwargs
        )
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Remove sensitive information from connection string"""
        # Remove password and other sensitive data
        import re
        return re.sub(r'password=[^;]+', 'password=***', conn_str)
    
    def _generate_suggestion(self, db_type: str, error: Exception) -> str:
        """Generate contextual suggestion based on error type"""
        if "timeout" in str(error).lower():
            return f"Check {db_type} server responsiveness and network connectivity"
        elif "authentication" in str(error).lower():
            return f"Verify {db_type} username and password"
        elif "not found" in str(error).lower():
            return f"Ensure {db_type} server is running and accessible"
        else:
            return f"Check {db_type} server configuration and logs"
```

### **Custom Error with Recovery Strategy**

```python
from langswarm.core.errors import LangSwarmError, ErrorCategory
from typing import Callable, Any

class RetryableOperationError(LangSwarmError):
    """Error that includes retry strategy"""
    
    def __init__(
        self, 
        message: str, 
        operation: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ):
        self.operation = operation
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            suggestion=f"Operation will be retried up to {max_retries} times",
            **kwargs
        )
    
    def should_retry(self) -> bool:
        """Check if operation should be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry counter"""
        self.retry_count += 1
        self.suggestion = f"Retry {self.retry_count}/{self.max_retries} failed, {self.max_retries - self.retry_count} attempts remaining"
```

---

## 🔧 Custom Error Categories

### **Creating New Error Categories**

```python
from enum import Enum
from langswarm.core.errors import ErrorCategory

# Extend existing categories for your domain
class CustomErrorCategory(Enum):
    """Custom error categories for domain-specific errors"""
    
    # Extend base categories
    CONFIGURATION = ErrorCategory.CONFIGURATION.value
    AGENT = ErrorCategory.AGENT.value
    TOOL = ErrorCategory.TOOL.value
    
    # Add custom categories
    EXTERNAL_API = "external_api"
    DATA_PROCESSING = "data_processing"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION = "integration"

class ExternalAPIError(LangSwarmError):
    """Error for external API failures"""
    
    def __init__(self, api_name: str, message: str, **kwargs):
        self.api_name = api_name
        super().__init__(
            message=f"{api_name} API error: {message}",
            category=CustomErrorCategory.EXTERNAL_API,  # Use custom category
            **kwargs
        )
```

### **Custom Severity Levels**

```python
from langswarm.core.errors import ErrorSeverity

class ExtendedErrorSeverity(Enum):
    """Extended severity levels for custom requirements"""
    
    # Base severity levels
    CRITICAL = ErrorSeverity.CRITICAL.value
    ERROR = ErrorSeverity.ERROR.value
    WARNING = ErrorSeverity.WARNING.value
    INFO = ErrorSeverity.INFO.value
    
    # Custom severity levels
    DEGRADED = "degraded"      # Service degraded but operational
    MAINTENANCE = "maintenance" # Planned maintenance mode
    THROTTLED = "throttled"    # Rate limited but recoverable
```

---

## 🔄 Custom Error Handlers

### **Domain-Specific Error Handler**

```python
from langswarm.core.errors import ErrorHandler, LangSwarmError, ErrorSeverity
from typing import Any, Optional

class CustomErrorHandler(ErrorHandler):
    """Custom error handler with domain-specific logic"""
    
    def __init__(self, notification_service=None, monitoring_service=None):
        super().__init__()
        self.notification_service = notification_service
        self.monitoring_service = monitoring_service
    
    def handle_error(self, error: LangSwarmError, context: dict = None) -> Any:
        """Handle error with custom logic"""
        
        # Call base handler first
        result = super().handle_error(error, context)
        
        # Add custom handling
        self._notify_on_error(error)
        self._update_monitoring(error)
        self._apply_custom_recovery(error)
        
        return result
    
    def _notify_on_error(self, error: LangSwarmError):
        """Send notifications based on error severity"""
        if self.notification_service:
            if error.severity == ErrorSeverity.CRITICAL:
                self.notification_service.send_alert(
                    level="critical",
                    message=error.message,
                    context=error.context
                )
            elif error.severity == ErrorSeverity.ERROR:
                self.notification_service.send_notification(
                    level="error",
                    message=error.message
                )
    
    def _update_monitoring(self, error: LangSwarmError):
        """Update monitoring metrics"""
        if self.monitoring_service:
            self.monitoring_service.increment_counter(
                metric=f"errors.{error.category.value}",
                tags={
                    "severity": error.severity.value,
                    "component": error.context.component if error.context else "unknown"
                }
            )
    
    def _apply_custom_recovery(self, error: LangSwarmError):
        """Apply domain-specific recovery strategies"""
        if isinstance(error, DatabaseConnectionError):
            self._handle_database_error(error)
        elif isinstance(error, ExternalAPIError):
            self._handle_api_error(error)
    
    def _handle_database_error(self, error: DatabaseConnectionError):
        """Handle database connection errors"""
        # Switch to backup database, enable read-only mode, etc.
        pass
    
    def _handle_api_error(self, error: ExternalAPIError):
        """Handle external API errors"""
        # Use cached data, switch to backup API, etc.
        pass
```

### **Error Handler with Recovery Strategies**

```python
from langswarm.core.errors import ErrorHandler, RecoveryStrategy
from typing import Dict, Type, Callable

class RecoveryAwareErrorHandler(ErrorHandler):
    """Error handler with pluggable recovery strategies"""
    
    def __init__(self):
        super().__init__()
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
    
    def register_recovery_strategy(
        self, 
        error_type: Type[Exception], 
        strategy: Callable[[Exception], Any]
    ):
        """Register a recovery strategy for specific error type"""
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: LangSwarmError, context: dict = None) -> Any:
        """Handle error with registered recovery strategies"""
        
        # Try registered recovery strategy first
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                try:
                    return strategy(error)
                except Exception as recovery_error:
                    # Recovery failed, fall back to base handling
                    self.log_recovery_failure(error, recovery_error)
        
        # Fall back to base error handling
        return super().handle_error(error, context)
    
    def log_recovery_failure(self, original_error: Exception, recovery_error: Exception):
        """Log when recovery strategy fails"""
        logger.warning(
            f"Recovery strategy failed for {type(original_error).__name__}: {recovery_error}"
        )

# Usage
handler = RecoveryAwareErrorHandler()

# Register recovery strategies
handler.register_recovery_strategy(
    DatabaseConnectionError,
    lambda error: switch_to_backup_database()
)

handler.register_recovery_strategy(
    ExternalAPIError,
    lambda error: use_cached_response(error.api_name)
)
```

---

## 🧩 Error Context Extensions

### **Rich Error Context Builder**

```python
from langswarm.core.errors import ErrorContext
from datetime import datetime
from typing import Dict, Any, Optional

class RichErrorContext(ErrorContext):
    """Extended error context with additional tracking"""
    
    def __init__(
        self,
        component: str,
        operation: str,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        **kwargs
    ):
        super().__init__(component, operation, **kwargs)
        self.request_id = request_id
        self.trace_id = trace_id
        self.environment = environment
        self.version = version
    
    def add_performance_data(self, execution_time: float, memory_usage: int):
        """Add performance metrics to context"""
        self.metadata.update({
            "execution_time_ms": execution_time,
            "memory_usage_mb": memory_usage
        })
    
    def add_user_context(self, user_id: str, session_id: str, ip_address: str):
        """Add user context information"""
        self.user_id = user_id
        self.session_id = session_id
        self.metadata["ip_address"] = ip_address
    
    def add_system_context(self, hostname: str, process_id: int):
        """Add system context information"""
        self.metadata.update({
            "hostname": hostname,
            "process_id": process_id,
            "thread_id": threading.current_thread().ident
        })

def create_rich_context(component: str, operation: str) -> RichErrorContext:
    """Factory function for creating rich error context"""
    import os
    import socket
    import uuid
    
    return RichErrorContext(
        component=component,
        operation=operation,
        request_id=str(uuid.uuid4()),
        environment=os.getenv("ENVIRONMENT", "development"),
        version=os.getenv("APP_VERSION", "unknown"),
        hostname=socket.gethostname(),
        process_id=os.getpid()
    )
```

### **Context Manager for Error Tracking**

```python
from contextlib import contextmanager
from langswarm.core.errors import LangSwarmError
import time

@contextmanager
def error_tracking_context(component: str, operation: str):
    """Context manager that automatically tracks errors with rich context"""
    
    start_time = time.time()
    context = create_rich_context(component, operation)
    
    try:
        yield context
    except Exception as e:
        # Enhance any exception with rich context
        execution_time = (time.time() - start_time) * 1000
        context.add_performance_data(execution_time, get_memory_usage())
        
        if isinstance(e, LangSwarmError):
            # Update existing LangSwarm error with rich context
            e.context = context
        else:
            # Convert regular exception to LangSwarm error
            enhanced_error = LangSwarmError(
                message=str(e),
                context=context,
                cause=e
            )
            raise enhanced_error from e
        raise

# Usage
def my_operation():
    with error_tracking_context("my_component", "complex_operation") as ctx:
        # Your operation code here
        risky_operation()
        
        # Add additional context as needed
        ctx.add_user_context("user123", "session456", "192.168.1.1")
```

---

## 🔌 Integration Patterns

### **Framework Integration**

```python
from langswarm.core.errors import LangSwarmError, ErrorHandler
from flask import Flask, jsonify
from fastapi import FastAPI, HTTPException

# Flask integration
def create_flask_error_handler(app: Flask, error_handler: ErrorHandler):
    """Integrate LangSwarm error handling with Flask"""
    
    @app.errorhandler(LangSwarmError)
    def handle_langswarm_error(error: LangSwarmError):
        # Handle the error
        result = error_handler.handle_error(error)
        
        # Convert to Flask response
        response_data = {
            "error": error.message,
            "category": error.category.value,
            "severity": error.severity.value
        }
        
        if error.suggestion:
            response_data["suggestion"] = error.suggestion
        
        status_code = 500 if error.severity.value in ["critical", "error"] else 400
        return jsonify(response_data), status_code

# FastAPI integration
def create_fastapi_error_handler(app: FastAPI, error_handler: ErrorHandler):
    """Integrate LangSwarm error handling with FastAPI"""
    
    @app.exception_handler(LangSwarmError)
    async def handle_langswarm_error(request, error: LangSwarmError):
        # Handle the error
        result = error_handler.handle_error(error)
        
        # Convert to HTTPException
        status_code = 500 if error.severity.value in ["critical", "error"] else 400
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": error.message,
                "category": error.category.value,
                "suggestion": error.suggestion
            }
        )
```

### **Logging Integration**

```python
import logging
from langswarm.core.errors import LangSwarmError

class LangSwarmErrorFormatter(logging.Formatter):
    """Custom log formatter for LangSwarm errors"""
    
    def format(self, record):
        if hasattr(record, 'exc_info') and record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            if isinstance(exc_value, LangSwarmError):
                # Format LangSwarm errors specially
                record.msg = self._format_langswarm_error(exc_value)
        
        return super().format(record)
    
    def _format_langswarm_error(self, error: LangSwarmError) -> str:
        """Format LangSwarm error for logging"""
        lines = [
            f"LangSwarm Error: {error.message}",
            f"Category: {error.category.value}",
            f"Severity: {error.severity.value}"
        ]
        
        if error.context:
            lines.append(f"Component: {error.context.component}")
            lines.append(f"Operation: {error.context.operation}")
        
        if error.suggestion:
            lines.append(f"Suggestion: {error.suggestion}")
        
        return " | ".join(lines)

# Setup logging with custom formatter
logger = logging.getLogger("langswarm")
handler = logging.StreamHandler()
handler.setFormatter(LangSwarmErrorFormatter())
logger.addHandler(handler)
```

---

## 🧪 Testing Custom Errors

### **Error Testing Framework**

```python
import pytest
from langswarm.core.errors import LangSwarmError, ErrorSeverity, ErrorCategory

class ErrorTestCase:
    """Base class for testing custom errors"""
    
    def assert_error_properties(
        self, 
        error: LangSwarmError, 
        expected_message: str,
        expected_category: ErrorCategory,
        expected_severity: ErrorSeverity = ErrorSeverity.ERROR
    ):
        """Assert error has expected properties"""
        assert isinstance(error, LangSwarmError)
        assert error.message == expected_message
        assert error.category == expected_category
        assert error.severity == expected_severity
    
    def assert_error_context(
        self, 
        error: LangSwarmError,
        expected_component: str,
        expected_operation: str
    ):
        """Assert error context is correct"""
        assert error.context is not None
        assert error.context.component == expected_component
        assert error.context.operation == expected_operation

# Test custom error types
class TestCustomErrors(ErrorTestCase):
    
    def test_database_connection_error(self):
        """Test DatabaseConnectionError creation and properties"""
        error = DatabaseConnectionError(
            database_type="PostgreSQL",
            connection_string="postgresql://user:pass@localhost:5432/db",
            underlying_error=ConnectionRefusedError("Connection refused")
        )
        
        self.assert_error_properties(
            error,
            "Failed to connect to PostgreSQL database",
            ErrorCategory.NETWORK
        )
        
        self.assert_error_context(
            error,
            "database_connector",
            "establish_connection"
        )
        
        assert error.suggestion is not None
        assert "password=***" in error.context.metadata["connection_string"]
    
    def test_retryable_operation_error(self):
        """Test RetryableOperationError retry logic"""
        def mock_operation():
            return "success"
        
        error = RetryableOperationError(
            message="Network timeout",
            operation=mock_operation,
            max_retries=3
        )
        
        # Test retry logic
        assert error.should_retry() is True
        assert error.retry_count == 0
        
        error.increment_retry()
        assert error.retry_count == 1
        assert error.should_retry() is True
        
        # Exhaust retries
        error.increment_retry()
        error.increment_retry()
        assert error.retry_count == 3
        assert error.should_retry() is False

# Test error handler integration
class TestCustomErrorHandler(ErrorTestCase):
    
    def test_custom_handler_notification(self):
        """Test that custom handler sends notifications"""
        notification_service = MockNotificationService()
        handler = CustomErrorHandler(notification_service=notification_service)
        
        critical_error = LangSwarmError(
            message="Critical failure",
            severity=ErrorSeverity.CRITICAL
        )
        
        handler.handle_error(critical_error)
        
        assert notification_service.alerts_sent == 1
        assert notification_service.last_alert_level == "critical"
```

---

## 📚 Best Practices

### **Error Design Principles**

1. **Be Specific**: Create specific error types for different failure modes
2. **Include Context**: Always provide rich context about what went wrong
3. **Actionable Messages**: Include suggestions for how to resolve the issue
4. **Consistent Categorization**: Use appropriate categories and severities
5. **Preserve Cause**: Chain exceptions to maintain debugging information

### **Error Handling Guidelines**

1. **Fail Fast**: Don't hide errors, make them visible early
2. **Graceful Degradation**: Provide fallback behavior when possible
3. **Log Appropriately**: Log errors at appropriate levels
4. **Monitor Metrics**: Track error rates and patterns
5. **User Experience**: Provide user-friendly error messages

### **Performance Considerations**

1. **Lazy Context Building**: Only build rich context when needed for debugging
2. **Error Caching**: Cache error templates for frequently occurring errors
3. **Avoid Deep Stack Traces**: Don't create unnecessarily deep error chains
4. **Structured Logging**: Use structured logging for better performance

---

**The LangSwarm V2 error system is designed to be both powerful and extensible. By following these patterns, you can create robust error handling that improves both developer and user experience.**
