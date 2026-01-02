# LangSwarm V2 Token Tracking and Context Size Monitoring System

## Overview

This document proposes a comprehensive token usage and context size tracking system for LangSwarm V2 that integrates seamlessly with the existing architecture without breaking any functionality.

## Goals

1. **Real-time token tracking** - Track input, output, and total tokens for all LLM interactions
2. **Context size monitoring** - Monitor conversation context sizes and context windows
3. **Cost estimation** - Provide accurate cost tracking per interaction and session
4. **Performance monitoring** - Track token/second rates and efficiency metrics
5. **Non-intrusive integration** - Leverage existing middleware and observability systems
6. **Alerting and limits** - Set token budget limits and usage alerts
7. **Historical analytics** - Provide usage trends and optimization insights

## Architecture Design

### Core Components

#### 1. Token Tracking Middleware (`TokenTrackingInterceptor`)
- Intercepts all agent interactions through the V2 middleware pipeline
- Automatically captures token usage from provider responses
- Calculates context sizes and token efficiency metrics
- Integrates with existing observability system

#### 2. Context Size Monitor (`ContextSizeMonitor`)
- Tracks conversation context sizes in real-time
- Monitors context window utilization per model
- Provides context compression triggers
- Alerts on approaching context limits

#### 3. Token Usage Aggregator (`TokenUsageAggregator`)
- Aggregates token usage across sessions, agents, and workflows
- Provides usage analytics and trends
- Integrates with existing cost management system
- Maintains usage history and statistics

#### 4. Enhanced Cost Integration
- Extends existing `CostManagementSystem` with token-specific features
- Real-time cost tracking per token
- Budget enforcement and alerting
- Usage optimization recommendations

### Integration Points

#### 1. Middleware Pipeline Integration
```python
# Enhanced pipeline with token tracking
pipeline = Pipeline([
    ContextInterceptor(),           # Existing
    RoutingInterceptor(),          # Existing  
    ValidationInterceptor(),       # Existing
    TokenTrackingInterceptor(),    # NEW - Token tracking
    ExecutionInterceptor(),        # Existing
    ObservabilityInterceptor()     # Existing - Enhanced with token metrics
])
```

#### 2. Provider Integration
- Enhance all providers (`OpenAIProvider`, `AnthropicProvider`, etc.) to emit standardized token events
- Add context size calculation utilities
- Integrate with token tracking middleware

#### 3. Observability Integration
- Extend existing metrics system with token-specific metrics
- Add token usage to tracing spans
- Enhance logging with token information

## Implementation Plan

### Phase 1: Core Token Tracking Infrastructure

#### 1.1 Token Tracking Interfaces
```python
@dataclass
class TokenUsageEvent:
    """Token usage event for tracking"""
    session_id: str
    agent_id: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    context_size: int
    max_context_size: int
    cost_estimate: float
    timestamp: datetime
    operation_type: str  # "chat", "tool_call", "function_call"
    metadata: Dict[str, Any]

@dataclass  
class ContextSizeInfo:
    """Context size information"""
    current_size: int
    max_size: int
    utilization_percent: float
    messages_count: int
    compression_recommended: bool
    compression_urgency: str  # "none", "low", "medium", "high", "critical"
```

#### 1.2 Token Tracking Middleware
```python
class TokenTrackingInterceptor(BaseInterceptor):
    """Middleware interceptor for token usage tracking"""
    
    def __init__(self, priority: int = 450):  # Before execution, after validation
        super().__init__(name="token_tracking", priority=priority)
        self.token_aggregator = TokenUsageAggregator()
        self.context_monitor = ContextSizeMonitor()
    
    async def _process(self, context: IRequestContext, next_interceptor) -> IResponseContext:
        # Pre-execution: Calculate input context size
        pre_context_info = await self._calculate_context_size(context)
        
        # Execute next interceptor
        response = await next_interceptor(context)
        
        # Post-execution: Extract token usage and track
        if response.is_success():
            token_event = await self._extract_token_usage(context, response, pre_context_info)
            await self._track_token_usage(token_event)
            await self._check_limits_and_alerts(token_event)
        
        return response
```

#### 1.3 Context Size Monitor
```python
class ContextSizeMonitor:
    """Monitor conversation context sizes and utilization"""
    
    async def calculate_context_info(self, session: IAgentSession, model: str) -> ContextSizeInfo:
        """Calculate current context size and utilization"""
        
    async def should_compress_context(self, context_info: ContextSizeInfo) -> bool:
        """Determine if context compression is needed"""
        
    async def get_compression_strategy(self, context_info: ContextSizeInfo) -> Dict[str, Any]:
        """Get recommended compression strategy"""
```

### Phase 2: Enhanced Observability and Metrics

#### 2.1 Token Metrics Integration
```python
# Extended metrics for token tracking
class TokenMetrics:
    """Token-specific metrics"""
    
    def record_token_usage(self, provider: str, model: str, 
                          input_tokens: int, output_tokens: int, cost: float):
        self.metrics.increment_counter(f"tokens.input.{provider}.{model}", input_tokens)
        self.metrics.increment_counter(f"tokens.output.{provider}.{model}", output_tokens)
        self.metrics.increment_counter(f"tokens.total.{provider}.{model}", input_tokens + output_tokens)
        self.metrics.set_gauge(f"cost.per_token.{provider}.{model}", cost / (input_tokens + output_tokens))
    
    def record_context_utilization(self, model: str, utilization: float):
        self.metrics.set_gauge(f"context.utilization.{model}", utilization)
    
    def record_tokens_per_second(self, provider: str, model: str, tokens_per_sec: float):
        self.metrics.set_gauge(f"performance.tokens_per_second.{provider}.{model}", tokens_per_sec)
```

#### 2.2 Enhanced Tracing
```python
# Add token information to trace spans
async def enhance_span_with_tokens(span: TraceSpan, token_event: TokenUsageEvent):
    span.tags.update({
        "tokens.input": token_event.input_tokens,
        "tokens.output": token_event.output_tokens,
        "tokens.total": token_event.total_tokens,
        "context.size": token_event.context_size,
        "context.utilization": token_event.context_size / token_event.max_context_size,
        "cost.estimate": token_event.cost_estimate,
        "model": token_event.model,
        "provider": token_event.provider
    })
```

### Phase 3: Advanced Features

#### 3.1 Token Budget Management
```python
class TokenBudgetManager:
    """Manage token budgets and limits"""
    
    async def check_budget_limit(self, user_id: str, session_id: str, 
                               projected_tokens: int) -> BudgetCheckResult:
        """Check if operation is within budget limits"""
        
    async def enforce_token_limit(self, limit_config: TokenLimitConfig) -> bool:
        """Enforce token usage limits"""
        
    async def get_budget_recommendations(self, usage_pattern: Dict) -> List[str]:
        """Get budget optimization recommendations"""
```

#### 3.2 Context Optimization
```python
class ContextOptimizer:
    """Optimize conversation contexts for token efficiency"""
    
    async def compress_context(self, session: IAgentSession, 
                             target_size: int, strategy: str) -> IAgentSession:
        """Compress context to target size"""
        
    async def optimize_for_model(self, session: IAgentSession, 
                               model: str) -> IAgentSession:
        """Optimize context for specific model"""
```

## Non-Breaking Integration Strategy

### 1. Middleware Integration
- Add `TokenTrackingInterceptor` to the default pipeline
- Use priority system to ensure proper order
- Make token tracking optional via configuration
- Graceful degradation if tracking fails

### 2. Provider Enhancement
- Add token extraction utilities to base provider class
- Implement provider-specific token calculation
- Maintain backward compatibility with existing provider APIs
- Add opt-in token tracking for custom providers

### 3. Observability Extension
- Extend existing metrics without changing interfaces
- Add token metrics as additional metric types
- Enhance existing tracing with token information
- Keep token data optional in log events

### 4. Configuration Integration
```yaml
# Enhanced V2 configuration with token tracking
observability:
  token_tracking:
    enabled: true
    track_context_size: true
    track_costs: true
    budget_limits:
      daily_token_limit: 1000000
      session_token_limit: 50000
      cost_limit_usd: 100.0
    alerts:
      token_threshold: 0.8  # Alert at 80% of limit
      context_threshold: 0.9  # Alert at 90% context utilization
    optimization:
      auto_compress_context: true
      compression_threshold: 0.85
```

## Usage Examples

### 1. Basic Token Tracking
```python
# Automatic token tracking through middleware
agent = await get_agent("gpt-4-agent")
response = await agent.chat("Hello, world!")

# Token information automatically tracked and available
print(f"Tokens used: {response.metadata.get('token_usage')}")
print(f"Cost estimate: {response.metadata.get('cost_estimate')}")
```

### 2. Context Monitoring
```python
# Get context information
context_info = await agent.get_context_info()
print(f"Context utilization: {context_info.utilization_percent}%")

if context_info.compression_recommended:
    # Automatic context compression
    await agent.optimize_context()
```

### 3. Budget Management
```python
# Set token budget
budget_manager = TokenBudgetManager()
await budget_manager.set_budget("user_123", daily_limit=10000, cost_limit=50.0)

# Check budget before operation
budget_check = await budget_manager.check_budget("user_123", projected_tokens=500)
if budget_check.within_limit:
    response = await agent.chat(message)
else:
    print(f"Budget exceeded: {budget_check.reason}")
```

### 4. Analytics and Monitoring
```python
# Get usage analytics
analytics = await token_aggregator.get_usage_analytics(
    user_id="user_123",
    time_range=("2024-01-01", "2024-01-31")
)

print(f"Total tokens: {analytics.total_tokens}")
print(f"Average cost per session: {analytics.avg_cost_per_session}")
print(f"Most expensive model: {analytics.most_expensive_model}")
```

## Metrics and Monitoring

### Token Usage Metrics
- `tokens.input.{provider}.{model}` - Input tokens used
- `tokens.output.{provider}.{model}` - Output tokens generated
- `tokens.total.{provider}.{model}` - Total tokens consumed
- `tokens.cost.{provider}.{model}` - Cost in USD
- `tokens.rate.{provider}.{model}` - Tokens per second

### Context Metrics  
- `context.size.{model}` - Current context size
- `context.utilization.{model}` - Context window utilization (0.0-1.0)
- `context.compression.count` - Number of context compressions
- `context.compression.efficiency` - Compression efficiency ratio

### Performance Metrics
- `performance.tokens_per_second.{provider}.{model}` - Processing speed
- `performance.cost_per_token.{provider}.{model}` - Cost efficiency
- `performance.context_efficiency.{model}` - Context utilization efficiency

### Budget Metrics
- `budget.utilization.{user_id}` - Budget utilization percentage
- `budget.alerts.{user_id}` - Budget alert triggers
- `budget.overages.{user_id}` - Budget overages

## Implementation Timeline

### Week 1-2: Core Infrastructure
- Implement `TokenUsageEvent` and `ContextSizeInfo` interfaces
- Create `TokenTrackingInterceptor` middleware
- Enhance provider base classes with token extraction

### Week 3-4: Observability Integration
- Extend metrics system with token metrics
- Enhance tracing with token information
- Update logging with token data

### Week 5-6: Advanced Features
- Implement `ContextSizeMonitor` and optimization
- Create `TokenBudgetManager` with limits and alerts
- Add configuration integration

### Week 7-8: Testing and Documentation
- Comprehensive testing across all providers
- Performance impact assessment
- Documentation and usage examples
- Migration guide for existing deployments

## Backward Compatibility

This system is designed to be completely backward compatible:

1. **Optional by default** - Token tracking can be disabled
2. **Graceful degradation** - System works if token tracking fails
3. **No breaking changes** - Existing APIs remain unchanged
4. **Progressive enhancement** - Features can be enabled incrementally

## Conclusion

This comprehensive token tracking and context size monitoring system will provide LangSwarm V2 with production-ready observability for token usage while maintaining the system's modularity and performance. The non-intrusive design ensures existing functionality continues to work while providing powerful new capabilities for cost management and optimization.
