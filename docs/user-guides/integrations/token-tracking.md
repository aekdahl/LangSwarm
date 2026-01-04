# Token Tracking & Usage

LangSwarm provides built-in support for tracking token usage across all LLM interactions. While the advanced Budgeting and Accounting system is currently in development, accurate usage data is available for every response.

## Accessing Token Usage

Standard usage statistics (prompt tokens, completion tokens, total tokens) are automatically extracted from the provider's response and available in the `metadata` of the `AgentResult` object.

### Example

```python
import asyncio
from langswarm.core.agents import AgentBuilder

async def main():
    agent = AgentBuilder.litellm().model("gpt-4o").build()
    
    result = await agent.run("Calculate the fibonacci of 10")
    
    # Access token usage from metadata
    usage = result.metadata.get("token_usage", {})
    
    print(f"Input Tokens: {usage.get('prompt_tokens')}")
    print(f"Output Tokens: {usage.get('completion_tokens')}")
    print(f"Total Tokens: {usage.get('total_tokens')}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Provider Support

Token usage tracking is supported for all major providers that expose this information, including:

- **OpenAI**
- **Anthropic**
- **Google Gemini**
- **Mistral**
- **LiteLLM** (Unified Interface)

## Roadmap: Unified Accounting System

We are actively developing a comprehensive **Token Accounting & Budgeting System** that will include:

- **Budget Enforcement**: Set daily/monthly limits per agent or user.
- **Cost Estimation**: Real-time dollar cost calculation based on model pricing.
- **Analytics**: Historical usage trends and optimization insights.

These features are currently in the design phase. You can view the [Investigation Reports](/archive/reports/token-tracking-system) for more details on the proposed architecture.
