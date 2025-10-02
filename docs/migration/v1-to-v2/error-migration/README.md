# LangSwarm V1 to V2 Error Migration Guide

**Complete guide for migrating from V1's scattered error system to V2's unified error hierarchy**

## 🎯 Overview

LangSwarm V2 introduces a unified error system that consolidates 483+ scattered error types from V1 into a structured hierarchy with rich context and improved user experience. This guide helps you migrate your error handling code from V1 to V2.

**Key Benefits of V2 Error System:**
- **Reduced Complexity**: 483+ errors → 47 structured types
- **Rich Context**: Component, operation, and user guidance included
- **Consistent Handling**: Centralized error routing and recovery
- **Better UX**: Actionable error messages with suggestions
- **Full Compatibility**: V1 errors continue working during migration

---

## 🔄 Migration Strategy

### **Phase 1: Backward Compatibility (No Code Changes)**
V2 maintains full backward compatibility - your existing V1 error handling continues working unchanged.

```python
# Your existing V1 code works without changes
try:
    result = some_langswarm_operation()
except LangSwarmError as e:  # V1 error type
    handle_error(e)  # Still works in V2
```

### **Phase 2: Enhanced Error Handling (Optional)**
Enhance your error handling to leverage V2 features while maintaining V1 compatibility.

```python
# Enhanced V2 error handling
try:
    result = some_langswarm_operation()
except LangSwarmError as e:
    # V2 errors have additional context
    if hasattr(e, 'suggestion') and e.suggestion:
        print(f"💡 {e.suggestion}")
    if hasattr(e, 'context') and e.context:
        print(f"🔍 Component: {e.context.component}")
    handle_error(e)
```

### **Phase 3: Full V2 Migration (Recommended)**
Migrate to V2 error types for optimal experience.

```python
from langswarm.core.errors import ConfigurationError, ErrorContext

# V2 error creation with rich context
context = ErrorContext("config_loader", "load_agents")
error = ConfigurationError(
    message="Invalid agent configuration",
    context=context,
    suggestion="Check agent model name and API key"
)
```

---

## 📊 Error Type Mapping

### **V1 → V2 Error Mapping**

| V1 Error Type | V2 Error Type | Migration Notes |
|---------------|---------------|-----------------|
| `LangSwarmError` | `LangSwarmError` | ✅ Direct compatibility |
| `ConfigError` | `ConfigurationError` | Enhanced with context |
| `AgentInitError` | `AgentError` | Unified agent errors |
| `ToolExecutionError` | `ToolError` | Enhanced tool error handling |
| `WorkflowError` | `WorkflowError` | Added workflow-specific context |
| `MemoryError` | `MemoryError` | Enhanced memory error details |
| `ValidationError` | `ValidationError` | Improved validation messages |
| `APIError` | `NetworkError` | Renamed for clarity |
| Custom errors | Inherit from `LangSwarmError` | Enhanced base class |

### **V1 Scattered Errors → V2 Categories**

**Configuration Errors (V1: 45+ types → V2: ConfigurationError)**
```python
# V1 (multiple types)
ConfigFileNotFoundError
InvalidYAMLError  
MissingAPIKeyError
InvalidModelError
# ... 41 more types

# V2 (unified with context)
ConfigurationError(
    message="Specific error message",
    context=ErrorContext("component", "operation"),
    suggestion="Actionable guidance"
)
```

**Agent Errors (V1: 67+ types → V2: AgentError)**
```python
# V1 (multiple types)
AgentInitializationError
ChatCompletionError
ModelNotAvailableError
RateLimitError
# ... 63 more types

# V2 (unified with severity)
AgentError(
    message="Specific agent error",
    severity=ErrorSeverity.ERROR,
    suggestion="How to resolve this"
)
```

**Tool Errors (V1: 89+ types → V2: ToolError)**
```python
# V1 (multiple types)
ToolNotFoundError
ToolParameterError
ToolExecutionFailedError
ToolTimeoutError
# ... 85 more types

# V2 (unified with categories)
ToolError(
    message="Tool execution failed",
    category=ErrorCategory.TOOL,
    suggestion="Check tool configuration"
)
```

---

## 🛠️ Migration Steps

### **Step 1: Assess Current Error Handling**

**Audit Your Error Types:**
```bash
# Find all error handling in your codebase
grep -r "except.*Error" your_project/
grep -r "raise.*Error" your_project/
```

**Common V1 Patterns:**
```python
# Pattern 1: Generic error catching
try:
    operation()
except Exception as e:
    log_error(str(e))

# Pattern 2: Specific error types
try:
    operation()
except LangSwarmError as e:
    handle_langswarm_error(e)
except Exception as e:
    handle_generic_error(e)

# Pattern 3: Multiple specific errors
try:
    operation()
except ConfigError as e:
    handle_config_error(e)
except AgentError as e:
    handle_agent_error(e)
```

### **Step 2: Update Error Handling (Gradual)**

**Enhanced V1 Compatible Handling:**
```python
# Before (V1)
try:
    operation()
except LangSwarmError as e:
    logger.error(f"Error: {e}")

# After (V1/V2 compatible)
try:
    operation()
except LangSwarmError as e:
    # Works with both V1 and V2 errors
    error_msg = str(e)
    
    # V2 enhancements (if available)
    if hasattr(e, 'suggestion'):
        error_msg += f"\n💡 {e.suggestion}"
    if hasattr(e, 'context'):
        error_msg += f"\n🔍 {e.context.component}"
    
    logger.error(error_msg)
```

### **Step 3: Migrate to V2 Error Creation**

**Creating V2 Errors:**
```python
# Before (V1)
raise ConfigError("Config file not found")

# After (V2)
from langswarm.core.errors import ConfigurationError, ErrorContext

context = ErrorContext("config_loader", "load_file")
raise ConfigurationError(
    message="Config file not found",
    context=context,
    suggestion="Create langswarm.yaml in project root"
)
```

### **Step 4: Implement V2 Error Handling**

**Full V2 Error Handling:**
```python
from langswarm.core.errors import (
    LangSwarmError, ConfigurationError, AgentError, ToolError,
    ErrorSeverity, ErrorHandler
)

handler = ErrorHandler()

def robust_operation():
    try:
        return risky_operation()
    except ConfigurationError as e:
        if e.severity == ErrorSeverity.CRITICAL:
            # Critical config errors need immediate attention
            handler.emergency_shutdown()
        else:
            # Non-critical errors can be handled gracefully
            return handler.handle_error(e)
    except AgentError as e:
        # Agent errors might be recoverable
        return handler.handle_error(e)
    except ToolError as e:
        # Tool errors might have fallback strategies
        return handler.handle_error(e)
    except LangSwarmError as e:
        # Generic LangSwarm error handling
        return handler.handle_error(e)
```

---

## 🔧 Migration Utilities

### **Automatic Error Migration**

**Use Migration Helper:**
```python
from langswarm.core.errors import migrate_error

# Automatically convert V1 errors to V2
def migrate_exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert any V1 error to V2 format
            v2_error = migrate_error(e)
            raise v2_error
    return wrapper

@migrate_exception_handler
def your_function():
    # Your existing code - errors automatically upgraded
    pass
```

**Batch Migration Tool:**
```python
from langswarm.core.errors import migrate_codebase

# Migrate entire codebase (analysis tool)
migration_report = migrate_codebase(
    source_dir="./your_project",
    target_dir="./your_project_v2",
    dry_run=True  # Analyze first, don't modify
)

print(f"Found {len(migration_report.errors)} error patterns")
print(f"Migration complexity: {migration_report.complexity}")
```

### **Custom Error Migration**

**Migrate Custom Error Types:**
```python
# V1 Custom Error
class MyCustomError(Exception):
    pass

# V2 Custom Error (inherit from LangSwarmError)
from langswarm.core.errors import LangSwarmError, ErrorCategory

class MyCustomError(LangSwarmError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,  # Choose appropriate category
            **kwargs
        )

# Migration bridge for compatibility
def migrate_my_custom_error(old_error):
    return MyCustomError(
        message=str(old_error),
        context=ErrorContext("legacy_component", "legacy_operation"),
        suggestion="Update to V2 error handling for better experience"
    )
```

---

## 🧪 Testing Error Migration

### **Migration Test Strategy**

**Test V1 Compatibility:**
```python
import pytest
from langswarm.v1.errors import OldConfigError  # V1 error
from langswarm.core.errors import ConfigurationError  # V2 error

def test_v1_error_compatibility():
    """Test that V1 errors still work in V2"""
    try:
        raise OldConfigError("Test error")
    except Exception as e:
        # Should still be catchable as LangSwarmError
        assert isinstance(e, LangSwarmError)
        assert "Test error" in str(e)

def test_error_migration():
    """Test V1 to V2 error migration"""
    v1_error = OldConfigError("Config issue")
    v2_error = migrate_error(v1_error)
    
    assert isinstance(v2_error, ConfigurationError)
    assert v2_error.message == "Config issue"
    assert v2_error.context is not None
```

**Test V2 Enhancements:**
```python
def test_v2_error_features():
    """Test V2-specific error features"""
    context = ErrorContext("test_component", "test_operation")
    error = ConfigurationError(
        message="Test error",
        context=context,
        suggestion="Test suggestion"
    )
    
    assert error.context.component == "test_component"
    assert error.suggestion == "Test suggestion"
    assert "💡" in str(error)  # V2 formatting
```

### **Regression Testing**

**Ensure No Breaking Changes:**
```python
def test_existing_error_handling():
    """Test that existing error handling patterns work"""
    def old_error_handler():
        try:
            # Simulate V1 operation that throws error
            raise_v1_error()
        except LangSwarmError as e:
            # V1 error handling should still work
            return f"Handled: {e}"
    
    result = old_error_handler()
    assert "Handled:" in result
```

---

## 📈 Migration Best Practices

### **Gradual Migration Approach**

1. **Start with New Code**: Use V2 errors for all new functionality
2. **Enhance Existing Handlers**: Add V2 context handling to existing code
3. **Migrate High-Impact Areas**: Convert critical error paths first
4. **Test Thoroughly**: Ensure no regressions in error handling
5. **Document Changes**: Update error handling documentation

### **Error Handling Improvements**

**Better Error Messages:**
```python
# V1 (generic)
raise ConfigError("Invalid config")

# V2 (actionable)
raise ConfigurationError(
    message="Invalid agent model 'gpt-4-unknown' in configuration",
    context=ErrorContext("config_loader", "validate_agents"),
    suggestion="Use a valid model like 'gpt-4o' or 'gpt-3.5-turbo'"
)
```

**Rich Error Context:**
```python
# V1 (minimal context)
raise ToolError("Tool failed")

# V2 (rich context)
raise ToolError(
    message="BigQuery tool execution failed",
    context=ErrorContext(
        component="bigquery_tool",
        operation="execute_query",
        metadata={
            "query": "SELECT * FROM dataset.table",
            "project": "my-project",
            "error_code": "403"
        }
    ),
    suggestion="Check BigQuery permissions and API quotas"
)
```

---

## ⚠️ Migration Gotchas

### **Common Issues and Solutions**

**Issue 1: Exception Inheritance**
```python
# Problem: Custom errors that don't inherit from LangSwarmError
class MyError(Exception):  # ❌ Won't be caught by LangSwarmError handlers
    pass

# Solution: Inherit from V2 base class
class MyError(LangSwarmError):  # ✅ Properly integrated
    pass
```

**Issue 2: Error Message Formatting**
```python
# Problem: Assuming simple string messages
error_msg = str(error)  # May include V2 formatting symbols

# Solution: Extract clean message if needed
clean_msg = error.message if hasattr(error, 'message') else str(error)
```

**Issue 3: Error Serialization**
```python
# Problem: V2 errors have complex structure
json.dumps(error)  # ❌ Won't work directly

# Solution: Use error serialization method
error_dict = error.to_dict() if hasattr(error, 'to_dict') else {'message': str(error)}
json.dumps(error_dict)  # ✅ Works
```

---

## 🎯 Migration Checklist

### **Pre-Migration Assessment**
- [ ] Audit all error handling in codebase
- [ ] Identify custom error types
- [ ] Document current error handling patterns
- [ ] Create test cases for existing error scenarios

### **Migration Implementation**
- [ ] Update error imports to V2 where needed
- [ ] Enhance error handlers with V2 context checking
- [ ] Migrate custom errors to inherit from LangSwarmError
- [ ] Add rich context to new error creation
- [ ] Implement centralized error handling where beneficial

### **Testing and Validation**
- [ ] Test V1 error compatibility
- [ ] Test V2 error enhancements
- [ ] Verify no regression in error handling
- [ ] Test error serialization and logging
- [ ] Validate error message clarity and actionability

### **Documentation and Deployment**
- [ ] Update error handling documentation
- [ ] Train team on V2 error patterns
- [ ] Monitor error rates and user feedback
- [ ] Plan for complete V1 deprecation (if desired)

---

**The V2 error system is designed for gradual migration - you can start benefiting from improved error handling immediately while maintaining full compatibility with your existing V1 code.**
