# LangSwarm V2 Error System API Reference

**Complete API documentation for the LangSwarm V2 unified error system**

## 🎯 Overview

LangSwarm V2 introduces a unified error system that consolidates 483+ scattered error types into a structured, hierarchical system with rich context, centralized handling, and improved user experience.

**Key Features:**
- **Structured Hierarchy**: Severity + Category organization
- **Rich Context**: Component, operation, user guidance included
- **Centralized Handling**: Consistent error routing and recovery
- **Backward Compatibility**: V1 errors continue working
- **Performance Optimized**: Minimal overhead for error handling

---

## 📊 Error Hierarchy

### **Base Error Class**

#### `LangSwarmError`
**Base class for all LangSwarm V2 errors**

```python
from langswarm.core.errors import LangSwarmError, ErrorSeverity, ErrorCategory, ErrorContext

error = LangSwarmError(
    message="Configuration file not found",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CONFIGURATION,
    context=ErrorContext("config_loader", "load_file"),
    suggestion="Check that the config file exists and is readable",
    cause=FileNotFoundError("config.yaml not found")
)
```

**Constructor Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `str` | ✅ Yes | Human-readable error message |
| `severity` | `ErrorSeverity` | ❌ No | Error severity (default: ERROR) |
| `category` | `ErrorCategory` | ❌ No | Error category (default: CONFIGURATION) |
| `context` | `ErrorContext` | ❌ No | Rich error context |
| `suggestion` | `str` | ❌ No | User guidance for resolution |
| `cause` | `Exception` | ❌ No | Underlying exception that caused this error |

**Methods:**
- `_format_message() -> str`: Format error with context and suggestions
- `to_dict() -> Dict[str, Any]`: Serialize error for logging/debugging
- `get_severity() -> ErrorSeverity`: Get error severity level
- `get_category() -> ErrorCategory`: Get error category

---

## 🚨 Error Severity Levels

### `ErrorSeverity` Enum

```python
from langswarm.core.errors import ErrorSeverity

class ErrorSeverity(Enum):
    CRITICAL = "critical"  # System halt required
    ERROR = "error"        # Operation failed, system continues
    WARNING = "warning"    # Potential issue, operation continues
    INFO = "info"          # Informational, no action needed
```

**Severity Routing:**
- **CRITICAL**: Halt system operation, trigger alerts
- **ERROR**: Log error, attempt recovery, continue system operation
- **WARNING**: Log warning, continue operation with degraded functionality
- **INFO**: Informational logging only

---

## 📂 Error Categories

### `ErrorCategory` Enum

```python
from langswarm.core.errors import ErrorCategory

class ErrorCategory(Enum):
    CONFIGURATION = "configuration"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    NETWORK = "network"
    PERMISSION = "permission"
    VALIDATION = "validation"
```

**Category Usage:**
- **CONFIGURATION**: Config file issues, invalid settings
- **AGENT**: Agent creation, chat operations, model issues
- **TOOL**: Tool execution, parameter validation, tool failures
- **WORKFLOW**: Workflow execution, step failures, routing issues
- **MEMORY**: Memory operations, storage backend issues
- **NETWORK**: Network connectivity, API calls, timeouts
- **PERMISSION**: Access control, authentication, authorization
- **VALIDATION**: Input validation, parameter checking, format errors

---

## 📋 Error Context System

### `ErrorContext` Class

```python
from langswarm.core.errors import ErrorContext
from datetime import datetime

context = ErrorContext(
    component="config_loader",
    operation="load_agents_yaml",
    timestamp=datetime.now(),
    user_id="user_123",
    session_id="session_456",
    metadata={
        "file_path": "/path/to/agents.yaml",
        "line_number": 25,
        "config_section": "agents.my_agent"
    }
)
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `component` | `str` | Component where error occurred |
| `operation` | `str` | Specific operation that failed |
| `timestamp` | `datetime` | When the error occurred |
| `user_id` | `str` | User associated with the operation |
| `session_id` | `str` | Session where error occurred |
| `metadata` | `Dict[str, Any]` | Additional context data |

---

## 🏗️ Specific Error Types

### Configuration Errors

#### `ConfigurationError`
**Configuration-related errors**

```python
from langswarm.core.errors import ConfigurationError, ErrorContext

error = ConfigurationError(
    message="Missing required API key",
    context=ErrorContext("config_loader", "validate_openai_config"),
    suggestion="Set OPENAI_API_KEY environment variable or add to config file"
)
```

**Common Subtypes:**
- `ConfigFileNotFoundError`: Configuration file missing
- `InvalidConfigFormatError`: YAML/JSON parsing errors
- `MissingRequiredConfigError`: Required settings missing
- `InvalidConfigValueError`: Configuration values invalid

### Agent Errors

#### `AgentError`
**Agent-related errors**

```python
from langswarm.core.errors import AgentError, ErrorSeverity

error = AgentError(
    message="Failed to initialize agent with model gpt-4",
    severity=ErrorSeverity.ERROR,
    suggestion="Check API key validity and model availability"
)
```

**Common Subtypes:**
- `AgentInitializationError`: Agent creation failures
- `AgentChatError`: Chat operation failures
- `AgentModelError`: Model-specific issues
- `AgentMemoryError`: Memory integration issues

### Tool Errors

#### `ToolError`
**Tool execution errors**

```python
from langswarm.core.errors import ToolError, ErrorContext

error = ToolError(
    message="BigQuery tool execution failed",
    context=ErrorContext("bigquery_tool", "execute_query"),
    suggestion="Check BigQuery credentials and table permissions"
)
```

**Common Subtypes:**
- `ToolExecutionError`: Tool execution failures
- `ToolParameterError`: Invalid tool parameters
- `ToolPermissionError`: Tool access denied
- `ToolTimeoutError`: Tool execution timeout

### Critical Errors

#### `CriticalError`
**Critical errors requiring system halt**

```python
from langswarm.core.errors import CriticalError

error = CriticalError(
    message="Database connection pool exhausted",
    suggestion="Restart the application and check database connectivity"
)
```

**Usage:** Only for errors that require immediate system attention and potential shutdown.

---

## 🔧 Error Handler System

### `ErrorHandler` Class

```python
from langswarm.core.errors import ErrorHandler, ErrorSeverity

handler = ErrorHandler()

# Handle error with automatic routing
try:
    risky_operation()
except Exception as e:
    handled_error = handler.handle_error(e, context)
    
# Check if system should halt
if handler.should_halt():
    handler.emergency_shutdown()
```

**Methods:**
- `handle_error(error, context) -> LangSwarmError`: Process and route error
- `should_halt() -> bool`: Check if critical errors require system halt
- `emergency_shutdown()`: Perform graceful system shutdown
- `get_recovery_strategy(error) -> RecoveryStrategy`: Get recovery approach
- `reset_circuit_breaker()`: Reset error circuit breaker

### Circuit Breaker

```python
from langswarm.core.errors import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    half_open_max_calls=3
)

# Use circuit breaker
with breaker:
    result = unreliable_operation()
```

**States:**
- **CLOSED**: Normal operation, errors counted
- **OPEN**: Circuit tripped, calls fail fast
- **HALF_OPEN**: Testing recovery, limited calls allowed

---

## 🔄 Backward Compatibility

### Legacy Error Support

**All V1 errors continue to work:**

```python
# V1 code continues working unchanged
try:
    old_function()
except LangSwarmError as e:  # V1 error type
    handle_error(e)  # Still works

# V2 code gets enhanced features
try:
    new_function()
except LangSwarmError as e:  # V2 error type
    print(e.suggestion)  # New: User guidance
    print(e.context.component)  # New: Rich context
```

### Migration Utilities

```python
from langswarm.core.errors import migrate_error, create_v2_error

# Convert V1 error to V2
v1_error = SomeOldError("Something failed")
v2_error = migrate_error(v1_error)

# Create V2 error from V1 pattern
v2_error = create_v2_error(
    legacy_type=SomeOldError,
    message="Something failed",
    context=ErrorContext("component", "operation")
)
```

---

## 📊 Usage Examples

### Basic Error Creation

```python
from langswarm.core.errors import (
    ConfigurationError, AgentError, ToolError,
    ErrorContext, ErrorSeverity
)

# Simple error
error = ConfigurationError("Config file not found")

# Rich error with context
context = ErrorContext("config_loader", "load_file")
error = ConfigurationError(
    message="Invalid YAML syntax in config file",
    context=context,
    suggestion="Check YAML syntax using a validator"
)

# Critical error
error = CriticalError(
    message="Database connection failed",
    suggestion="Check database server status and restart application"
)
```

### Error Handling Patterns

```python
from langswarm.core.errors import ErrorHandler, ConfigurationError

handler = ErrorHandler()

def load_config():
    try:
        # Configuration loading logic
        config = load_yaml_file("config.yaml")
        return config
    except FileNotFoundError as e:
        error = ConfigurationError(
            message="Configuration file not found",
            cause=e,
            suggestion="Create config.yaml in the project root"
        )
        return handler.handle_error(error)
    except yaml.YAMLError as e:
        error = ConfigurationError(
            message="Invalid YAML syntax in configuration",
            cause=e,
            suggestion="Validate YAML syntax and fix formatting errors"
        )
        return handler.handle_error(error)
```

### Custom Error Types

```python
from langswarm.core.errors import LangSwarmError, ErrorCategory

class CustomIntegrationError(LangSwarmError):
    """Custom error for third-party integrations"""
    
    def __init__(self, service_name: str, message: str, **kwargs):
        self.service_name = service_name
        super().__init__(
            message=f"{service_name}: {message}",
            category=ErrorCategory.NETWORK,
            **kwargs
        )

# Usage
error = CustomIntegrationError(
    service_name="Slack API",
    message="Rate limit exceeded",
    suggestion="Wait 60 seconds before retrying"
)
```

---

## 🧪 Testing Error Scenarios

```python
import pytest
from langswarm.core.errors import ConfigurationError, ErrorSeverity

def test_configuration_error():
    error = ConfigurationError(
        message="Test error",
        suggestion="Test suggestion"
    )
    
    assert error.severity == ErrorSeverity.ERROR
    assert error.category == ErrorCategory.CONFIGURATION
    assert error.suggestion == "Test suggestion"
    assert "Test error" in str(error)

def test_error_context():
    context = ErrorContext("test_component", "test_operation")
    error = ConfigurationError("Test", context=context)
    
    assert error.context.component == "test_component"
    assert error.context.operation == "test_operation"
    assert error.context.timestamp is not None
```

---

## 📈 Performance Considerations

### Optimized Error Creation

```python
# Fast path - minimal error
error = ConfigurationError("Quick error")

# Rich path - full context (use when debugging)
if debug_mode:
    context = ErrorContext("component", "operation")
    error = ConfigurationError(
        message="Detailed error",
        context=context,
        suggestion="Detailed guidance"
    )
```

### Error Caching

```python
# Cache error context templates for better performance
from langswarm.core.errors import ErrorContextTemplate

template = ErrorContextTemplate("config_loader", "load_file")
context = template.create_context(metadata={"file": "config.yaml"})
```

---

**This V2 error system provides a robust foundation for error handling throughout LangSwarm while maintaining backward compatibility and improving the developer and user experience.**
