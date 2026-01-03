---
title: "Token Tracking"
description: "Monitor costs and enforce budgets"
---

# 💰 Token Tracking

LangSwarm provides built-in token tracking and cost estimation for all major providers (OpenAI, Anthropic, Gemini, etc.), powered by LiteLLM.

## 🚀 Quick Enable

Enable tracking on any agent with a single builder method.

```python
from langswarm.core.agents import AgentBuilder

agent = await (AgentBuilder("analyst")
    .openai()
    .model("gpt-4o")
    .cost_tracking(True)  # Enable tracking
    .build())
    
# Chat normally
await agent.chat("Analyze this report...")

# Get real-time stats
stats = await agent.get_usage_stats()
print(f"Total Cost: ${stats.total_cost:.4f}")
print(f"Tokens Used: {stats.total_tokens}")
```

## 🛑 Budget Enforcement

Prevent runaway costs by setting daily or session limits.

```python
agent = await (AgentBuilder("bounded_agent")
    .openai()
    .model("gpt-4o")
    .cost_tracking(enabled=True)
    
    # Budget Configuration
    .cost_limit_daily(5.00)      # $5.00 USD per day
    .token_limit_daily(100_000)  # 100k tokens per day
    
    # Actions on limit reached
    .on_limit_reached("error")   # or "warning"
    .build())
```

If a limit is exceeded, the agent will raise a `BudgetExceededError`.

## 📊 Usage Analytics

You can access granular usage data for reporting.

### Per-Session Stats
```python
# Create a specific session
response = await agent.chat("Hello", session_id="session_123")

# Get usage for that session only
session_stats = await agent.get_session_usage("session_123")
print(f"Session Cost: ${session_stats.cost}")
```

### Global Aggregation
```python
from langswarm.core.observability import get_global_usage

# Get total usage across ALL agents in the process
global_stats = get_global_usage()

for model, usage in global_stats.by_model.items():
    print(f"{model}: {usage.cost:.4f}")
```

## 🧠 Context Management

Token tracking works with memory to optimize context usage.

```python
agent = await (AgentBuilder("memory_agent")
    .openai()
    .memory_enabled(True)
    .max_tokens(4096)
    
    # Auto-summarize when context gets full
    .auto_compress_context(True) 
    .build())
```

## 🔧 Supported Providers

Costs are calculated using up-to-date pricing from the [LiteLLM Model Cost Map](https://github.com/BerriAI/litellm).

- **OpenAI**: GPT-4o, GPT-4-Turbo, GPT-3.5
- **Anthropic**: Claude 3.5 Sonnet, Opus, Haiku
- **Google**: Gemini 1.5 Pro, Flash
- **Cohere**: Command R+
- **Mistral**: Mistral Large, Small
