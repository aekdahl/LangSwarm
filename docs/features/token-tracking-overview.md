# Token Tracking System Overview - LangSwarm V2

## What is Token Tracking?

LangSwarm V2's Token Tracking System is a comprehensive solution for monitoring, managing, and optimizing token usage across all AI agent interactions. It provides real-time visibility into token consumption, costs, and performance metrics while maintaining backward compatibility with existing deployments.

## Key Features

### 🔍 **Real-time Token Monitoring**
- Track input, output, and total tokens for every LLM interaction
- Monitor token usage across sessions, users, and agents
- Real-time cost estimation with provider-specific pricing
- Performance metrics (tokens/second, efficiency ratios)

### 📊 **Context Size Management**
- Monitor conversation context sizes and utilization
- Model-specific context window tracking
- Intelligent compression recommendations
- Automatic context optimization

### 💰 **Budget Management**
- Configurable token and cost limits (daily, session, hourly)
- Real-time budget enforcement
- Usage alerts and notifications
- Optimization recommendations

### 📈 **Analytics & Insights**
- Historical usage patterns and trends
- Cost analysis by model, provider, and time period
- Performance optimization insights
- Usage forecasting and planning

## Architecture

### Components

1. **TokenTrackingInterceptor** - Middleware that automatically captures token usage
2. **ContextSizeMonitor** - Monitors context sizes and provides compression recommendations
3. **TokenUsageAggregator** - Aggregates usage data for analytics
4. **TokenBudgetManager** - Manages budgets and enforces limits

### Integration Points

- **Middleware Pipeline** - Non-intrusive interceptor integration
- **Observability System** - Metrics, tracing, and logging
- **Provider Integration** - Works with all LLM providers
- **Configuration System** - Environment-based configuration

## Benefits

### For Developers
- **Visibility** - Understand token usage patterns in your applications
- **Debugging** - Track down expensive operations and optimize
- **Testing** - Monitor token costs during development

### For Operations
- **Cost Control** - Set budgets and prevent runaway costs
- **Performance** - Monitor and optimize token efficiency
- **Compliance** - Track usage for audit and reporting

### For Business
- **Budgeting** - Accurate cost forecasting and planning
- **Optimization** - Identify opportunities to reduce costs
- **Scaling** - Plan capacity based on usage trends

## Quick Start Examples

### Basic Tracking
```python
from langswarm.core.middleware import create_enhanced_pipeline

# Enable basic token tracking
pipeline = create_enhanced_pipeline(enable_token_tracking=True)
agent.use_pipeline(pipeline)

# Token usage is now automatically tracked
response = await agent.chat("Hello, world!")
print(f"Tokens used: {response.metadata['token_usage']}")
```

### Budget Enforcement
```python
from langswarm.core.observability import TokenBudgetConfig

# Set up budget limits
budget = TokenBudgetConfig(
    daily_token_limit=100000,
    cost_limit_usd=50.0,
    enforce_limits=True
)

# Create pipeline with budget enforcement
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=True
)
```

### Production Configuration
```python
from langswarm.core.config.token_config import get_production_config

# Load production settings
config = get_production_config()
pipeline = create_pipeline_from_config(config.to_dict())

# Features enabled:
# - Token tracking and analytics
# - Budget enforcement with alerts
# - Context monitoring and compression
# - Performance optimization
```

## Use Cases

### 1. Development & Testing
- Track token usage during development
- Identify expensive operations
- Test budget limits and alerts
- Optimize prompt engineering

### 2. Cost Management
- Set daily/monthly token budgets
- Monitor costs across teams/projects
- Prevent budget overruns
- Optimize model selection

### 3. Performance Optimization
- Monitor context window utilization
- Implement automatic context compression
- Track processing speed and efficiency
- Identify bottlenecks

### 4. Compliance & Reporting
- Generate usage reports
- Track costs for billing/chargeback
- Monitor API quota usage
- Audit token consumption

## Getting Started

### 1. Choose Your Integration Strategy

**New Projects**: Start with full features enabled
```python
pipeline = create_production_pipeline()
```

**Existing Projects**: Gradual migration approach
```python
# Phase 1: Add tracking only
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=False
)
```

### 2. Configure for Your Environment

**Development**:
```python
config = get_development_config()  # Low limits, no enforcement
```

**Production**:
```python
config = get_production_config()   # Full features, enforcement
```

**Enterprise**:
```python
config = get_enterprise_config()   # High-volume optimization
```

### 3. Monitor and Optimize

- Review usage analytics regularly
- Adjust budgets based on patterns
- Enable context compression for efficiency
- Use cost optimization recommendations

## Documentation Structure

### Architecture & Design
- [Enhanced Pipeline Factory](../architecture/enhanced-pipeline-factory.md) - Pipeline creation and configuration
- [Token Tracking System](token-tracking-system.md) - Complete system design

### User Guides
- [Integration Guide](../user-guides/token-tracking-integration-guide.md) - Step-by-step implementation
- [Configuration Reference](../api-reference/token-tracking-config.md) - All configuration options

### Examples
- [Basic Usage Examples](../../examples/token_tracking_example.py) - Working code examples
- [Production Deployment](../deployment/token-tracking-production.md) - Production setup guide

## Next Steps

1. **Read the Integration Guide** - Learn how to add token tracking to your project
2. **Try the Examples** - Run the provided examples to see it in action
3. **Configure for Your Environment** - Choose appropriate settings for your use case
4. **Monitor and Optimize** - Use the analytics to optimize your token usage

The Token Tracking System is designed to be invisible when you don't need it, and powerful when you do. Start simple and enable more features as your needs grow.
