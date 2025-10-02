# Unified Pipeline System - LangSwarm V2

## Overview

LangSwarm V2 uses a **single, unified pipeline** that includes all capabilities by default. Features like token tracking are not separate "enhanced" pipelines, but built-in capabilities that can be enabled or disabled through configuration.

## Core Principle: One Pipeline, Many Configurations

### ❌ Wrong Approach (Multiple Pipeline Types)
```python
# BAD: Different pipelines for different features
standard_pipeline = create_standard_pipeline()      # Basic features
enhanced_pipeline = create_enhanced_pipeline()      # With token tracking
production_pipeline = create_production_pipeline()   # Production features
```

### ✅ Correct Approach (One Pipeline, Different Configs)
```python
# GOOD: One pipeline type, configured differently
pipeline = create_pipeline()  # Always the same structure

# Configure for different needs
pipeline = create_pipeline(get_production_config())   # Production settings
pipeline = create_pipeline(get_development_config())  # Development settings
pipeline = create_pipeline(custom_config)             # Custom settings
```

## The Unified Pipeline

### Default Capabilities (Always Available)

Every LangSwarm V2 pipeline includes these capabilities:

1. **Context Management** - Request/response context handling
2. **Routing** - Route requests to appropriate handlers
3. **Validation** - Request parameter validation
4. **Token Tracking** - Monitor token usage and costs
5. **Execution** - Execute the actual request
6. **Error Handling** - Comprehensive error management
7. **Observability** - Metrics, tracing, and logging

### Configuration-Driven Enablement

```python
# Default configuration (sensible defaults)
default_config = {
    "token_tracking": {
        "enabled": True,           # Always available
        "budget_enforcement": False, # Safe default
        "context_monitoring": True,
        "performance_tracking": True
    },
    "observability": {
        "enabled": True,
        "metrics": True,
        "tracing": True,
        "logging": True
    },
    "error_handling": {
        "enabled": True,
        "retry_logic": True,
        "graceful_degradation": True
    }
}

# Create pipeline with defaults
pipeline = create_pipeline()  # Uses defaults above

# Or customize configuration
custom_config = {
    "token_tracking": {
        "budget_enforcement": True  # Enable enforcement
    }
}
pipeline = create_pipeline(custom_config)
```

## Core Usage Patterns

### 1. Default Usage (Recommended)
```python
from langswarm.core.middleware import create_pipeline

# Create pipeline with sensible defaults
pipeline = create_pipeline()

# Features included:
# ✅ Token tracking (enabled)
# ❌ Budget enforcement (disabled for safety)
# ✅ Context monitoring (enabled)
# ✅ Observability (enabled)
# ✅ Error handling (enabled)
```

### 2. Environment-Specific Configuration
```python
from langswarm.core.middleware import (
    create_pipeline,
    get_production_config,
    get_development_config
)

# Production: All features enabled with enforcement
prod_pipeline = create_pipeline(get_production_config())

# Development: Tracking enabled, no enforcement
dev_pipeline = create_pipeline(get_development_config())
```

### 3. Custom Configuration
```python
# Define exactly what you need
config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "budget_limits": {
            "daily_token_limit": 100000,
            "cost_limit_usd": 50.0
        }
    },
    "observability": {
        "enabled": True,
        "tracing": False  # Disable for performance
    }
}

pipeline = create_pipeline(config)
```

## Why This Approach Is Better

### 1. **Separation of Concerns**
- Pipeline structure is separate from configuration
- Features are capabilities, not pipeline types
- Environment differences are configuration, not architecture

### 2. **Simplicity**
```python
# Simple: One way to create pipelines
pipeline = create_pipeline(config)

# Complex: Multiple pipeline types (what we avoid)
# standard_pipeline = create_standard_pipeline()
# enhanced_pipeline = create_enhanced_pipeline()
# production_pipeline = create_production_pipeline()
```

### 3. **Flexibility**
```python
# Runtime configuration changes
pipeline = create_pipeline()

# Later, enable budget enforcement
pipeline.configure({
    "token_tracking": {
        "budget_enforcement": True
    }
})
```

### 4. **No Feature Segregation**
All features are always available. Users don't need to choose between "basic" and "enhanced" versions.

## Migration from Multiple Pipeline Types

### If You Were Using "Enhanced" Pipelines

```python
# Old approach (deprecated)
from langswarm.core.middleware import create_enhanced_pipeline

enhanced_pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=False
)

# New approach (recommended)
from langswarm.core.middleware import create_pipeline

pipeline = create_pipeline({
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": False
    }
})
```

### If You Were Using Environment-Specific Pipelines

```python
# Old approach (multiple pipeline types)
prod_pipeline = create_production_pipeline()
dev_pipeline = create_development_pipeline()

# New approach (one pipeline, different configs)
prod_pipeline = create_pipeline(get_production_config())
dev_pipeline = create_pipeline(get_development_config())
```

## Configuration Reference

### Token Tracking Configuration
```python
"token_tracking": {
    "enabled": True,                    # Enable token tracking
    "budget_enforcement": False,        # Enforce budget limits
    "context_monitoring": True,         # Monitor context sizes
    "performance_tracking": True,       # Track performance metrics
    "budget_limits": {
        "daily_token_limit": 100000,
        "session_token_limit": 10000,
        "cost_limit_usd": 50.0
    },
    "alerts": {
        "token_alert_threshold": 0.8,   # Alert at 80% of limit
        "cost_alert_threshold": 0.8,
        "context_alert_threshold": 0.9
    }
}
```

### Observability Configuration
```python
"observability": {
    "enabled": True,        # Enable observability
    "metrics": True,        # Collect metrics
    "tracing": True,        # Enable tracing
    "logging": True,        # Enable logging
    "log_level": "INFO"     # Log level
}
```

### Error Handling Configuration
```python
"error_handling": {
    "enabled": True,            # Enable error handling
    "retry_logic": True,        # Enable retry on failures
    "graceful_degradation": True, # Graceful failure handling
    "max_retries": 3           # Maximum retry attempts
}
```

## Common Configuration Patterns

### Development
```python
dev_config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": False,    # No enforcement in dev
        "context_monitoring": True
    },
    "observability": {
        "enabled": True,
        "tracing": False,              # Less overhead
        "log_level": "DEBUG"
    },
    "error_handling": {
        "retry_logic": False           # Fail fast in dev
    }
}
```

### Production
```python
prod_config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,     # Enforce in production
        "context_monitoring": True,
        "budget_limits": {
            "daily_token_limit": 1000000,
            "cost_limit_usd": 100.0
        }
    },
    "observability": {
        "enabled": True,
        "metrics": True,
        "tracing": True,
        "log_level": "INFO"
    },
    "error_handling": {
        "enabled": True,
        "retry_logic": True,
        "graceful_degradation": True
    }
}
```

### Testing/CI
```python
test_config = {
    "token_tracking": {
        "enabled": False               # Disable for faster tests
    },
    "observability": {
        "enabled": False,              # Minimal overhead
        "logging": False
    },
    "error_handling": {
        "retry_logic": False,          # No retries in tests
        "graceful_degradation": False
    }
}
```

## Backward Compatibility

### Legacy Function Support
The old "enhanced pipeline" functions still work but are deprecated:

```python
# Still works (deprecated)
from langswarm.core.middleware import create_enhanced_pipeline

pipeline = create_enhanced_pipeline()  # Shows deprecation warning

# Preferred approach
from langswarm.core.middleware import create_pipeline

pipeline = create_pipeline()  # Default configuration
```

### Migration Path
```python
# Existing deployment
current_config = get_existing_config()

# Upgrade to include token tracking
new_config = upgrade_existing_pipeline_config(
    current_config,
    enable_token_tracking=True,
    enable_budget_enforcement=False  # Start conservatively
)

pipeline = create_pipeline(new_config)
```

## Benefits of the Unified Approach

### 1. **Conceptual Simplicity**
- One pipeline type to learn
- Configuration-driven behavior
- No feature segregation

### 2. **Easier Testing**
```python
# Test with minimal configuration
test_pipeline = create_pipeline(get_testing_config())

# Test with full features
full_pipeline = create_pipeline(get_production_config())
```

### 3. **Gradual Feature Adoption**
```python
# Start with defaults
pipeline = create_pipeline()

# Later, enable more features
config = pipeline.get_config()
config["token_tracking"]["budget_enforcement"] = True
pipeline.configure(config)
```

### 4. **Clear Separation of Concerns**
- Pipeline = Request processing structure
- Configuration = Feature enablement and behavior
- Environment = Different configurations, same pipeline

## Conclusion

The unified pipeline system eliminates the artificial distinction between "standard" and "enhanced" pipelines. Instead, LangSwarm V2 provides:

- **One pipeline architecture** with all capabilities built-in
- **Configuration-driven feature enablement** for different environments
- **Sensible defaults** that work out of the box
- **Gradual adoption** through configuration changes
- **No feature segregation** - all users have access to all capabilities

This approach is simpler, more flexible, and follows better software engineering principles than having multiple pipeline types.
