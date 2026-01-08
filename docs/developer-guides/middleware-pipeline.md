# Middleware Pipeline & Enhanced Processing

LangSwarm introduces a robust Middleware Pipeline that processes all agent interactions. This system provides a unified way to handle:
- **Routing**: Determining which code should execute a request.
- **Validation**: Ensuring requests are strict and valid.
- **Token Tracking**: Monitoring usage and enforcing budgets.
- **Observability**: Providing traces and metrics.
- **Error Handling**: Standardized error management.

## 1. Pipeline Integration

The `BaseAgent` class now integrates with the middleware pipeline. By default, every agent uses a `default_pipeline` that includes all standard interceptors (Routing, Validation, TokenTracking, Execution, Observability).

### Custom Pipeline

You can inject a custom pipeline when creating an agent:

```python
from langswarm.core.agents import AgentBuilder
from langswarm.core.middleware import create_enhanced_pipeline

# Create a pipeline with specific token tracking settings
custom_pipeline = create_enhanced_pipeline(
    enable_token_tracking=True,
    enable_budget_enforcement=True, # Enforce budgets
    token_tracking_config={
        "budget_limits": {"daily_token_limit": 50000}
    }
)

# Inject into agent
agent = AgentBuilder().openai().pipeline(custom_pipeline).build()
```

## 2. Configuring Token Tracking

Token tracking works "out of the box" so you typically don't need to configure it unless you want to **enforce budgets**.

### Default Behavior
- **Enabled**: Yes
- **Monitoring**: Yes (logs usage, updates metrics)
- **Enforcement**: No (requests are not blocked)

### Enabling Enforcement via Config
You can enable enforcement by passing a custom pipeline as shown above, or by relying on the default defaults and configuring the `TokenTrackingInterceptor` if you build your pipeline manually.

## 3. Dynamic Routing

The `RoutingInterceptor` is responsible for finding the "handler" for a request.

In legacy systems, "routing" often meant "find the tool definition".
In LangSwarm `BaseAgent.chat`, the **Agent itself** is the handler.

**Dynamic Routing Logic:**
1.  When `BaseAgent.chat("Hello")` is called, it creates a `RequestContext`.
2.  It injects **itself** (or a specific internal closure) as the `handler` in the request metadata.
    ```python
    metadata={
        "handler": chat_handler, # The function to execute
        "handler_type": "internal"
    }
    ```
3.  The `RoutingInterceptor` sees this existing handler and says, "Oh, you already know who executes this. I will pass it through."
4.  The `ExecutionInterceptor` then executes that handler.

This allows the same pipeline to handle:
- **Tools**: Router looks up tool in registry -> Execution calls tool.
- **Chat**: Agent provides handler -> Execution calls agent.

## 4. Streaming Support Requirements

Currently, `agent.stream_chat()` **bypasses** the middleware pipeline.

**Why?**
The current pipeline architecture expects every step to return a complete `IResponseContext` object (awaitable). Streaming requires returning an `AsyncGenerator`.

**Requirements to support Streaming in Pipeline:**
1.  **Response Object Update**: `IResponseContext` must be able to wrap an async generator.
2.  **Interceptor Updates**: 
    - `TokenTrackingInterceptor`: Must wrap the output stream to count tokens as chunks are yielded (accumulating them).
    - `ExecutionInterceptor`: Must detect streaming requests and call `stream_message` instead of `chat`.
    - `ErrorInterceptor`: Must handle errors that occur *during* streaming (mid-stream).
3.  **Pipeline Processor**: `pipeline.process()` needs to handle the fact that the "result" is not fully available when the function returns.

**Workaround:**
For now, `stream_chat` handles its own basic instrumentation locally within `BaseAgent`, mirroring what the pipeline does but without the full interceptor stack.
