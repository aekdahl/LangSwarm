# Enhanced Pipeline Factory - LangSwarm V2

## Overview

The Enhanced Pipeline Factory is a sophisticated system in LangSwarm V2 that creates middleware pipelines with advanced token tracking capabilities while maintaining backward compatibility with existing deployments.

## What is an "Enhanced Pipeline"?

An **Enhanced Pipeline** is a LangSwarm V2 middleware pipeline that includes:

1. **All standard V2 interceptors** (Context, Routing, Validation, Execution, Error, Observability)
2. **Token Tracking Interceptor** - New interceptor that monitors token usage and costs
3. **Configurable Features** - Budget enforcement, context monitoring, analytics
4. **Smart Ordering** - Proper interceptor priority ordering for optimal performance

### Standard Pipeline vs Enhanced Pipeline

```python
# Standard V2 Pipeline (existing)
standard_pipeline = Pipeline([
    ContextInterceptor(priority=100),
    RoutingInterceptor(priority=200), 
    ValidationInterceptor(priority=300),
    ExecutionInterceptor(priority=500),
    ObservabilityInterceptor(priority=700)
])

# Enhanced Pipeline (with token tracking)
enhanced_pipeline = Pipeline([
    ContextInterceptor(priority=100),
    RoutingInterceptor(priority=200),
    ValidationInterceptor(priority=300),
    TokenTrackingInterceptor(priority=450),  # ← NEW: Token tracking
    ExecutionInterceptor(priority=500),
    ErrorInterceptor(priority=600),
    ObservabilityInterceptor(priority=700)
])
```

## Factory Functions

### 1. `create_enhanced_pipeline()` - Main Factory Function

```python
def create_enhanced_pipeline(
    enable_token_tracking: bool = True,
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True,
    token_tracking_config: Optional[Dict[str, Any]] = None,
    custom_interceptors: Optional[List] = None
) -> Pipeline:
```

**What it does:**
- Creates a pipeline with configurable token tracking features
- Maintains proper interceptor ordering (priority-based)
- Allows gradual feature enablement
- Supports custom interceptors

**Parameters explained:**
- `enable_token_tracking`: Add token usage monitoring
- `enable_budget_enforcement`: Enforce token/cost limits
- `enable_context_monitoring`: Monitor conversation context sizes
- `token_tracking_config`: Advanced configuration options
- `custom_interceptors`: Additional interceptors to include

**Example:**
```python
# Basic enhanced pipeline
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,     # Track token usage
    enable_budget_enforcement=False, # No enforcement yet
    enable_context_monitoring=True   # Monitor context sizes
)

# Production pipeline with full features
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=True,  # Enforce limits
    enable_context_monitoring=True,
    token_tracking_config={
        "budget_limits": {
            "daily_token_limit": 1000000,
            "cost_limit_usd": 100.0
        }
    }
)
```

### 2. Deployment-Specific Factories

#### `create_production_pipeline()`
```python
def create_production_pipeline(
    token_budget_config: Optional[Dict[str, Any]] = None,
    enable_all_monitoring: bool = True
) -> Pipeline:
```

**Features:**
- Full token tracking enabled
- Budget enforcement enabled
- Context monitoring enabled
- Optimized for production use

**Example:**
```python
pipeline = create_production_pipeline(
    token_budget_config={
        "budget_limits": {
            "daily_token_limit": 1000000,
            "session_token_limit": 50000,
            "cost_limit_usd": 100.0
        },
        "enforcement": {
            "enforce_limits": True,
            "auto_compress_context": True
        }
    }
)
```

#### `create_development_pipeline()`
```python
def create_development_pipeline(
    enable_token_tracking: bool = True
) -> Pipeline:
```

**Features:**
- Token tracking enabled (for testing)
- Budget enforcement disabled
- Lower limits for development
- Debug-friendly configuration

#### `create_testing_pipeline()` / `create_minimal_pipeline()`
```python
def create_minimal_pipeline() -> Pipeline:
```

**Features:**
- Minimal overhead for tests
- Token tracking disabled (unless needed)
- Fast execution for CI/CD

## Backward Compatibility

### 1. Legacy Compatible Pipeline

```python
def create_legacy_compatible_pipeline() -> Pipeline:
    """
    Create a pipeline that's compatible with existing LangSwarm v2 deployments.
    This includes token tracking but disabled by default to avoid breaking changes.
    """
```

**What it provides:**
- Exact same interceptors as original V2 pipeline
- Token tracking available but disabled
- Zero breaking changes
- Drop-in replacement

### 2. Pipeline Upgrade Function

```python
def upgrade_pipeline_with_token_tracking(
    existing_pipeline: Pipeline,
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True
) -> Pipeline:
```

**How it works:**
1. Takes existing pipeline
2. Extracts current interceptors
3. Adds token tracking interceptor
4. Rebuilds pipeline with new capabilities
5. Returns upgraded pipeline

**Example:**
```python
# Existing deployment
old_pipeline = create_standard_v2_pipeline()

# Upgrade without breaking
new_pipeline = upgrade_pipeline_with_token_tracking(
    old_pipeline,
    enable_budget_enforcement=False,  # Start safe
    enable_context_monitoring=True
)

# Deploy upgraded pipeline
agent.use_pipeline(new_pipeline)
```

## Gradual Migration Support

### Phase 1: Add Tracking Only
```python
# Week 1-2: Just track, don't enforce
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=False,
    enable_context_monitoring=True
)
```

### Phase 2: Add Alerting
```python
# Week 3: Add budget monitoring
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=False,  # Still no enforcement
    enable_context_monitoring=True,
    token_tracking_config={
        "alerts": {
            "token_alert_threshold": 0.8,
            "cost_alert_threshold": 0.8
        }
    }
)
```

### Phase 3: Enable Enforcement
```python
# Week 4+: Full enforcement
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=True,  # Now enforcing limits
    enable_context_monitoring=True,
    token_tracking_config={
        "budget_limits": {
            "daily_token_limit": 1000000,
            "cost_limit_usd": 100.0
        },
        "enforcement": {
            "enforce_limits": True
        }
    }
)
```

## Configuration-Based Factory

### `create_pipeline_from_config()`
```python
def create_pipeline_from_config(config: Dict[str, Any]) -> Pipeline:
```

**Usage:**
```python
# From YAML config
config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "budget_limits": {
            "daily_token_limit": 500000,
            "cost_limit_usd": 50.0
        }
    }
}

pipeline = create_pipeline_from_config(config)
```

## Environment Detection

### `get_auto_config()` Integration
```python
from langswarm.core.config.token_config import get_auto_config

# Automatically detect environment and create appropriate pipeline
config = get_auto_config()  # Detects prod/dev/test environment
pipeline = create_pipeline_from_config(config.to_dict())
```

**Environment Detection Logic:**
- `LANGSWARM_ENV=production` → Production pipeline
- `LANGSWARM_ENV=development` → Development pipeline  
- `DEBUG=true` → Development pipeline
- `TESTING=true` → Testing pipeline
- Default → Development pipeline (safe)

## Interceptor Priority System

The Enhanced Pipeline Factory uses a priority-based ordering system:

```python
Priority  | Interceptor           | Purpose
----------|----------------------|----------------------------------
100       | ContextInterceptor   | Set up request context
200       | RoutingInterceptor   | Route to appropriate handler
300       | ValidationInterceptor| Validate request parameters
450       | TokenTrackingInterceptor | Track tokens (NEW)
500       | ExecutionInterceptor | Execute the actual request
600       | ErrorInterceptor     | Handle errors
700       | ObservabilityInterceptor | Log and trace
```

**Why this ordering?**
1. **Context first** - Set up request tracking
2. **Routing** - Determine what to execute
3. **Validation** - Ensure request is valid
4. **Token Tracking** - Check budgets BEFORE execution
5. **Execution** - Do the actual work
6. **Error Handling** - Catch and handle errors
7. **Observability** - Log everything

## Custom Interceptor Support

```python
# Add custom interceptors
custom_security_interceptor = SecurityInterceptor(priority=250)
custom_rate_limiter = RateLimitInterceptor(priority=350)

pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    custom_interceptors=[
        custom_security_interceptor,
        custom_rate_limiter
    ]
)
```

## Real-World Usage Examples

### 1. Existing Production Deployment (Zero Downtime Migration)
```python
# Current production pipeline
current_pipeline = create_standard_v2_pipeline()

# Upgrade with tracking only (no enforcement)
tracking_pipeline = upgrade_pipeline_with_token_tracking(
    current_pipeline,
    enable_budget_enforcement=False
)

# Deploy and monitor for 1 week
agent.use_pipeline(tracking_pipeline)

# Then enable enforcement
production_pipeline = create_production_pipeline(
    token_budget_config=production_budget_config
)
agent.use_pipeline(production_pipeline)
```

### 2. New Development Project
```python
# Start with development pipeline
dev_pipeline = create_development_pipeline()

# Track tokens but no enforcement
agent.use_pipeline(dev_pipeline)

# When ready for production
prod_pipeline = create_production_pipeline()
agent.use_pipeline(prod_pipeline)
```

### 3. Research/Experimentation
```python
# Research pipeline - track everything, enforce nothing
research_pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=False,  # No limits for research
    enable_context_monitoring=True,
    token_tracking_config={
        "retention_days": 365,  # Keep data for analysis
        "detailed_analytics": True
    }
)
```

## Benefits

### 1. **Non-Breaking Changes**
- Existing code continues to work unchanged
- Optional features can be enabled gradually
- Graceful degradation if tracking fails

### 2. **Flexible Configuration** 
- Environment-specific pipelines
- Feature toggles
- Custom interceptor support

### 3. **Production Ready**
- Battle-tested interceptor ordering
- Performance optimization
- Error handling and resilience

### 4. **Easy Migration**
- Upgrade existing pipelines
- Gradual feature enablement
- Zero-downtime deployment support

The Enhanced Pipeline Factory makes it easy to add sophisticated token tracking to any LangSwarm V2 deployment while maintaining the flexibility and reliability that production systems require.
