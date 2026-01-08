# Token Budgeting & Cost Analysis

LangSwarm includes a sophisticated **Token Accounting & Budgeting System** designed to give you precise control over cost and usage.

This system allows you to:
- **Track everything**: Monitor token usage across all agents, sessions, and users.
- **Estimate costs**: Get real-time cost estimates using centralized pricing (OpenAI, Anthropic, etc.).
- **Enforce limits**: Set daily limits, session caps, and total cost budgets to prevent unexpected bills.

## 1. Quick Start

By default, token tracking is **enabled** in observation mode (monitoring only). To start **enforcing** budgets, you need to configure a custom pipeline.

### Enabling Enforcement

You can enable budget enforcement when building an agent by injecting a configured pipeline:

```python
from langswarm.core.agents import AgentBuilder
from langswarm.core.middleware import create_enhanced_pipeline
from langswarm.core.observability import TokenBudgetConfig

# 1. Define your budget limits
budget_config = TokenBudgetConfig(
    daily_token_limit=100000,    # 100k tokens per day
    session_token_limit=10000,   # 10k tokens per session (prevents runaway loops)
    cost_limit_usd=5.00,         # $5.00 hard cap per day
    enforce_limits=True
)

# 2. Create a pipeline with enforcement enabled
pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=True,
    # Note: In a real app, you would load the user's specific budget 
    # from a database inside the interceptor or via a separate service.
    # The pipeline config here sets the *default* behavior.
)

# 3. Build the agent
agent = AgentBuilder().openai().pipeline(pipeline).build()
```

## 2. Cost Estimation

The system includes a centralized `CostEstimator` that standardizes pricing logic across providers.

### Automatic Fallback
If a provider (like a custom local model wrapper or an incomplete API implementation) returns usage statistics but **no cost data**, the `TokenTrackingInterceptor` automatically uses the `CostEstimator` to calculate the cost based on the model name.

This ensures your cost reports are accurate even when underlying APIs are inconsistent.

### Supported Models
The `CostEstimator` supports current pricing for:
- **OpenAI**: GPT-4o, GPT-4o-mini, O1-preview, etc.
- **Anthropic**: Claude 3.5 Sonnet, Haiku, Opus.
- **Legacy**: GPT-4 Turbo, GPT-3.5 Turbo.

## 3. Budget Manager

The `TokenBudgetManager` is the core logic component responsible for checking limits.

### How it works
1.  **Check**: Before an agent executes a request, the `TokenTrackingInterceptor` asks the `TokenBudgetManager` if the user has enough budget.
2.  **Estimate**: It estimates the cost of the *incoming* request (prompt).
3.  **Validate**: It checks:
    -   Has the user exceeded their daily token limit?
    -   Has the session exceeded its safety limit?
    -   Has the user exceeded their daily dollar cost limit?
4.  **Enforce**: If any check fails, the request is **rejected** with a `BudgetExceededError` before any API call is made.

### Programmatic Access
You can access the budget manager directly if you need to check status in your UI:

```python
from langswarm.core.middleware.interceptors.token_tracking import TokenTrackingInterceptor

# ... assuming you have access to your active interceptor ...
status = await interceptor.get_budget_status(user_id="user_123")

print(f"Daily Utilization: {status['utilization']['daily_tokens']}%")
print(f"Remaining Budget: ${status['config']['cost_limit_usd'] - status['utilization']['cost_usd']}")
```

## 4. Analytics & Persistence

Token usage events are aggregated by the `TokenUsageAggregator`.

- **In-Memory Default**: By default, aggregation is in-memory for speed.
- **Persistence**: For production, you should extend `TokenUsageAggregator` to flush events to a database (PostgreSQL/TimescaleDB) periodically.
