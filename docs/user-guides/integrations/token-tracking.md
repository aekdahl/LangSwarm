# LangSwarm V2 Token Tracking Integration Guide

## Overview

This guide provides step-by-step instructions for integrating the comprehensive token tracking system into existing LangSwarm V2 deployments without breaking functionality.

## Quick Start

### 1. Enable Basic Token Tracking

```python
from langswarm.core.middleware import create_pipeline
from langswarm.core.observability import initialize_observability

# Initialize observability
initialize_observability()

# Create pipeline with token tracking
pipeline = create_pipeline({
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": False,  # Start without enforcement
        "context_monitoring": True
    }
})

# Use pipeline in your agent system
agent.use_pipeline(pipeline)
```

### 2. Enable Budget Enforcement

```python
from langswarm.core.observability import TokenBudgetConfig

# Configure budget
budget_config = TokenBudgetConfig(
    daily_token_limit=100000,
    session_token_limit=10000,
    cost_limit_usd=10.0,
    enforce_limits=True
)

# Create pipeline with enforcement
pipeline = create_pipeline({
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "context_monitoring": True
    }
})

# Configure budget for specific users
token_interceptor = pipeline.get_interceptor("token_tracking")
await token_interceptor.configure_budget("user_123", budget_config)
```

### 3. Use Configuration Templates

```python
from langswarm.core.config.token_config import get_production_config
from langswarm.core.middleware.enhanced_pipeline import create_pipeline_from_config

# Load production configuration
config = get_production_config()

# Create pipeline from configuration
pipeline = create_pipeline_from_config(config.to_dict())
```

## Integration Strategies

### Strategy 1: Gradual Migration (Recommended)

For existing production deployments, we recommend a gradual migration approach:

#### Phase 1: Enable Tracking Only
```python
# Enable token tracking without enforcement
pipeline = create_pipeline({
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": False,
        "context_monitoring": True
    }
})
```

**Duration**: 1-2 weeks  
**Goal**: Collect baseline usage data

#### Phase 2: Enable Alerting
```python
from langswarm.core.config.token_config import get_migration_config

config = get_migration_config()
# Alerts enabled, enforcement disabled
pipeline = create_pipeline_from_config(config.to_dict())
```

**Duration**: 1 week  
**Goal**: Monitor usage patterns and set appropriate limits

#### Phase 3: Enable Enforcement
```python
# Update configuration to enable enforcement
config.update_config({
    "token_tracking": {
        "enforcement": {
            "enforce_limits": True
        }
    }
})
pipeline = create_pipeline_from_config(config.to_dict())
```

**Duration**: Ongoing  
**Goal**: Full token management with enforcement

### Strategy 2: New Deployment

For new deployments, you can enable all features immediately:

```python
from langswarm.core.middleware import create_pipeline

# Full production setup
pipeline = create_pipeline({
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "context_monitoring": True,
        "budget_limits": {
            "daily_token_limit": 1000000,
            "session_token_limit": 50000,
            "cost_limit_usd": 100.0
        },
        "enforcement": {
            "enforce_limits": True,
            "auto_compress_context": True
        }
    },
    "observability": {
        "enabled": True
    }
})
```

### Strategy 3: Development Environment

For development environments:

```python
from langswarm.core.config.token_config import get_development_config

config = get_development_config()
pipeline = create_pipeline_from_config(config.to_dict())

# Development features:
# - Token tracking enabled
# - Budget enforcement disabled
# - Lower limits for testing
# - Debug logging enabled
```

## Configuration Management

### Environment-Based Configuration

```python
import os
from langswarm.core.config.token_config import get_auto_config

# Set environment
os.environ['LANGSWARM_ENV'] = 'production'  # or 'development', 'testing'

# Auto-detect and load appropriate config
config = get_auto_config()
pipeline = create_pipeline_from_config(config.to_dict())
```

### Custom Configuration

```python
from langswarm.core.config.token_config import TokenTrackingConfig

# Create custom configuration
custom_config = {
    "token_tracking": {
        "enabled": True,
        "budget_enforcement": True,
        "budget_limits": {
            "daily_token_limit": 500000,
            "cost_limit_usd": 50.0
        }
    }
}

config = TokenTrackingConfig.from_dict(custom_config)
pipeline = create_pipeline_from_config(config.to_dict())
```

### Configuration from File

```yaml
# config.yaml
production:
  token_tracking:
    enabled: true
    budget_enforcement: true
    budget_limits:
      daily_token_limit: 1000000
      cost_limit_usd: 100.0
```

```python
from langswarm.core.config.token_config import TokenTrackingConfig

config = TokenTrackingConfig.from_file("config.yaml")
pipeline = create_pipeline_from_config(config.to_dict())
```

## Monitoring and Observability

### Accessing Usage Statistics

```python
# Get token tracking interceptor
token_interceptor = pipeline.get_interceptor("token_tracking")

# Get user usage
user_usage = await token_interceptor.get_user_usage("user_123")
print(f"Total tokens: {user_usage.get('total_tokens', 0)}")
print(f"Total cost: ${user_usage.get('total_cost', 0.0):.2f}")

# Get session usage
session_usage = await token_interceptor.get_session_usage("session_456")
print(f"Session tokens: {session_usage.get('total_tokens', 0)}")

# Get tracking statistics
stats = await token_interceptor.get_tracking_stats()
print(f"Events tracked: {stats['events_tracked']}")
```

### Usage Analytics

```python
from langswarm.core.observability import TokenUsageAggregator

aggregator = TokenUsageAggregator()

# Get comprehensive analytics
analytics = await aggregator.get_usage_analytics(
    user_id="user_123",
    time_range=(start_date, end_date),
    group_by="model"
)

print(f"Total tokens: {analytics['total_tokens']:,}")
print(f"Total cost: ${analytics['total_cost']:.2f}")
print(f"Cost per token: ${analytics['cost_per_token']:.6f}")
```

### Budget Management

```python
from langswarm.core.observability import TokenBudgetManager

budget_manager = TokenBudgetManager(aggregator)

# Set budget for user
await budget_manager.set_budget("user_123", budget_config)

# Check budget status
status = await budget_manager.get_budget_status("user_123")
print(f"Daily utilization: {status['utilization']['daily_tokens']['percentage']:.1f}%")

# Get recommendations
recommendations = await budget_manager.get_budget_recommendations("user_123")
for rec in recommendations:
    print(f"💡 {rec}")
```

### Context Monitoring

```python
from langswarm.core.observability import ContextSizeMonitor

context_monitor = ContextSizeMonitor()

# Calculate context info for session
context_info = await context_monitor.calculate_context_info(
    session=agent_session,
    model="gpt-4o",
    additional_tokens=500
)

print(f"Context utilization: {context_info.utilization_percent:.1f}%")
if context_info.compression_recommended:
    print(f"⚠️ Compression recommended: {context_info.compression_urgency.value}")
    
    # Get compression recommendation
    rec = await context_monitor.get_compression_recommendation(context_info)
    print(f"Strategy: {rec['strategy']}")
    print(f"Target size: {rec['target_size']:,} tokens")
```

## Error Handling and Resilience

### Graceful Degradation

The token tracking system is designed to fail gracefully:

```python
try:
    # Token tracking operations
    response = await agent.chat("Hello, world!")
except Exception as e:
    # Token tracking errors don't affect core functionality
    logger.warning(f"Token tracking error: {e}")
    # Response is still available
    print(response.content)
```

### Handling Budget Exceeded

```python
from langswarm.core.middleware.interfaces import ResponseStatus

response = await agent.chat("Expensive query")

if response.status == ResponseStatus.ERROR:
    error_type = response.metadata.get("error_type")
    if error_type == "budget_exceeded":
        print("Budget limit reached. Consider:")
        print("- Increasing daily limits")
        print("- Using a less expensive model")
        print("- Enabling context compression")
```

### Configuration Validation

```python
from langswarm.core.config.token_config import validate_config

# Validate configuration before use
errors = validate_config(config)
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Configuration is valid")
    pipeline = create_pipeline_from_config(config.to_dict())
```

## Performance Considerations

### Asynchronous Processing

Token tracking uses asynchronous processing by default to minimize impact:

```python
# Configure async processing
config = {
    "token_tracking": {
        "performance": {
            "async_tracking": True,
            "batch_size": 100,
            "buffer_size": 1000
        }
    }
}
```

### Memory Management

The system automatically manages memory usage:

```python
# Configure retention
config = {
    "token_tracking": {
        "performance": {
            "retention_days": 30,  # Keep data for 30 days
            "cleanup_interval": 24  # Cleanup every 24 hours
        }
    }
}
```

### High-Volume Deployments

For high-volume deployments, use enterprise configuration:

```python
from langswarm.core.config.token_config import get_enterprise_config

config = get_enterprise_config()
# Features:
# - Larger buffers and batch sizes
# - Reduced logging verbosity
# - Optimized performance settings
```

## Migration from Existing Systems

### From V1 to V2 with Token Tracking

```python
# Legacy V1 system
from langswarm.v1 import Agent as V1Agent

# Migration to V2 with token tracking
from langswarm.core.agents import BaseAgent
from langswarm.core.middleware import create_enhanced_pipeline

# Create V2 agent with token tracking
v2_agent = BaseAgent(
    agent_id="migrated-agent",
    configuration=v1_agent.config,  # Reuse existing config
    pipeline=create_pipeline({"token_tracking": {"enabled": True}})
)

# Token usage is now automatically tracked
response = await v2_agent.chat("Hello")
print(f"Tokens used: {response.metadata.get('token_usage', {})}")
```

### Preserving Existing Workflows

```python
# Upgrade existing pipeline with token tracking
from langswarm.core.middleware.enhanced_pipeline import upgrade_pipeline_with_token_tracking

# Existing pipeline
existing_pipeline = create_legacy_pipeline()

# Upgrade with token tracking
enhanced_pipeline = upgrade_pipeline_with_token_tracking(
    existing_pipeline,
    enable_budget_enforcement=False,  # Start conservatively
    enable_context_monitoring=True
)

# Use upgraded pipeline
agent.use_pipeline(enhanced_pipeline)
```

## Best Practices

### 1. Start Conservative
- Begin with tracking only, no enforcement
- Monitor usage patterns for 1-2 weeks
- Set limits based on observed patterns

### 2. Use Appropriate Configurations
- Development: Low limits, no enforcement
- Staging: Production-like limits with alerts
- Production: Full enforcement with monitoring

### 3. Monitor Regularly
```python
# Set up regular monitoring
async def monitor_token_usage():
    stats = await token_interceptor.get_tracking_stats()
    if stats['budgets_enforced'] > 0:
        logger.warning(f"Budget enforcement triggered {stats['budgets_enforced']} times")
```

### 4. Handle Budget Exceeded Gracefully
```python
async def handle_budget_exceeded(user_id: str):
    # Notify user
    await notify_user(user_id, "Token budget exceeded")
    
    # Suggest alternatives
    suggestions = await budget_manager.get_budget_recommendations(user_id)
    await send_suggestions(user_id, suggestions)
    
    # Consider temporary limit increase
    if is_premium_user(user_id):
        await increase_temporary_limit(user_id)
```

### 5. Use Context Compression Wisely
```python
# Configure context compression
if context_info.compression_recommended:
    if context_info.compression_urgency == CompressionUrgency.CRITICAL:
        # Force compression
        await agent.compress_context(strategy="aggressive")
    elif context_info.compression_urgency == CompressionUrgency.HIGH:
        # Suggest compression to user
        await suggest_compression(user_id)
```

## Troubleshooting

### Common Issues

#### 1. Token tracking not working
```python
# Check if tracking is enabled
if not config.is_enabled():
    logger.warning("Token tracking is disabled")

# Check interceptor is in pipeline
token_interceptor = pipeline.get_interceptor("token_tracking")
if not token_interceptor:
    logger.error("Token tracking interceptor not found in pipeline")
```

#### 2. Budget enforcement too strict
```python
# Check current usage vs limits
budget_status = await budget_manager.get_budget_status("user_123")
utilization = budget_status['utilization']['daily_tokens']['percentage']

if utilization > 90:
    # Consider increasing limits or using compression
    await budget_manager.set_budget(user_id, increased_budget_config)
```

#### 3. High memory usage
```python
# Reduce retention period
config.update_config({
    "token_tracking": {
        "performance": {
            "retention_days": 7,  # Reduce from 30 to 7 days
            "batch_size": 50      # Reduce batch size
        }
    }
})
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("langswarm.core.observability.token_tracking").setLevel(logging.DEBUG)
logging.getLogger("langswarm.core.middleware.interceptors.token_tracking").setLevel(logging.DEBUG)

# Check tracking events
stats = await token_interceptor.get_tracking_stats()
logger.debug(f"Tracking stats: {stats}")
```

## Conclusion

The LangSwarm V2 token tracking system provides comprehensive monitoring and management capabilities while maintaining backward compatibility. By following this integration guide, you can gradually enable features based on your needs and deployment environment.

For additional support or questions, please refer to the main documentation or create an issue in the LangSwarm repository.
