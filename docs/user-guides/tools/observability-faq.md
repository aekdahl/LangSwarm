---
title: "Observability & Providers FAQ"
description: "Common questions about tracing and multi-provider setup"
---

# Observability & LiteLLM FAQ

## How do I enable Langfuse Tracing?

LangSwarm supports **Zero-Config Observability**.

1.  Set your environment variables:
    ```bash
    export LANGFUSE_PUBLIC_KEY="pk-lf-..."
    export LANGFUSE_SECRET_KEY="sk-lf-..."
    export LANGFUSE_HOST="https://cloud.langfuse.com" # Optional, defaults to cloud
    ```

2.  Import `langswarm`. That's it!
    *   **LiteLLM Users**: Tracing is automatically registered via callbacks.
    *   **OpenAI Users**: The client is automatically wrapped with `langfuse.openai`.

## How do I specify different providers with LiteLLM?

When using `ProviderType.LITELLM`, you specify the underlying provider using **model prefixes**.

### Examples

| Provider | Model String Pattern | Example |
| :--- | :--- | :--- |
| **OpenAI** | `gpt-*` or `openai/gpt-*` | `.model("gpt-4o")` |
| **Anthropic** | `anthropic/<model>` | `.model("anthropic/claude-3-opus-20240229")` |
| **Google Vertex** | `vertex_ai/<model>` | `.model("vertex_ai/gemini-1.5-pro")` |
| **Google AI Studio** | `gemini/<model>` | `.model("gemini/gemini-1.5-flash")` |
| **Ollama** | `ollama/<model>` | `.model("ollama/llama3")` |
| **Azure** | `azure/<deployment>` | `.model("azure/gpt-4-turbo")` |

### Code Example

```python
from langswarm import AgentBuilder, ProviderType

# Use Claude 3 via LiteLLM
agent = (
    AgentBuilder()
    .name("ClaudeWorker")
    .provider(ProviderType.LITELLM)  # or OPENAI if you just want GPT
    .model("anthropic/claude-3-sonnet-20240229")
    .build()
)

# Use Gemini Pro via LiteLLM
agent = (
    AgentBuilder()
    .name("GeminiWorker")
    .provider(ProviderType.LITELLM)
    .model("gemini/gemini-1.5-pro")
    .build()
)
```

## Why isn't my trace showing up?

1.  **Check Environment**: Ensure `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are printed in `os.environ` (don't print the actual values!).
2.  **Check Install**: Ensure `pip install langfuse` is run.
3.  **Check Logs**: LangSwarm logs a ✅ message at startup if it enables tracing.
