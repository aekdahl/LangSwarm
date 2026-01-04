# 🐞 Debugging & Observability

LangSwarm provides a **zero-overhead, opt-in observability system** that integrates tracing, logging, and metrics. It is designed to be invisible in production unless enabled, but powerful enough for deep debugging when needed.

## 🚀 Quick Start

To enable full debug tracing (console output + detailed logs), initialize the observability system at the start of your application.

```python
from langswarm.core.agents import AgentBuilder
from langswarm.core.observability.auto_instrumentation import (
    initialize_auto_instrumentation
)
from langswarm.core.observability.provider import create_development_observability

# 1. Initialize Observability (do this once at startup)
# This automatically instruments all Agents, Tools, and Workflows
provider = initialize_auto_instrumentation(
    create_development_observability()
)

# 2. Run your code normally
async def main():
    agent = await AgentBuilder("debugger").build()
    await agent.chat("Hello!") 
    # Output will now show detailed traces:
    # [INFO] Started operation: agent.chat
    # [INFO] Started operation: llm.request
    # ...

# 3. Clean up
await provider.stop()
```

## ⚙️ Configuration

For more control, configure the `ObservabilityProvider` manually.

### Development Mode
Best for local debugging. Logs to console and memory buffers.

```python
from langswarm.core.observability.auto_instrumentation import initialize_auto_instrumentation
from langswarm.core.observability.provider import create_development_observability

initialize_auto_instrumentation(create_development_observability())
```

### Production Mode
Best for deployment. Logs to files, samples traces (10%), and handles I/O asynchronously to avoid blocking the main thread.

```python
from langswarm.core.observability.provider import create_production_observability

config = create_production_observability(
    log_file_path="/var/log/langswarm/app.log",
    opentelemetry_enabled=True,
    otlp_endpoint="http://otel-collector:4317"
)

initialize_auto_instrumentation(config)
```

## 🔍 How It Works

LangSwarm uses a **Global Observer** pattern. 

1.  **Auto-Instrumentation**: All core components (`BaseAgent`, `ToolRegistry`, etc.) inherit from `AutoInstrumentedMixin`.
2.  **Global Provider**: The `initialize_auto_instrumentation()` function sets a global provider instance.
3.  **Zero-Overhead**: If no provider is set (default), the instrumentation hooks are no-ops with negligible performance cost.

### Manual Instrumentation

If you write custom components, you can hook into this system using the `AutoInstrumentedMixin` or decorators.

#### Using Mixin
```python
from langswarm.core.observability.auto_instrumentation import AutoInstrumentedMixin

class MyCustomService(AutoInstrumentedMixin):
    async def do_work(self):
        # Automatically creates a span: "mycustomservice.do_work"
        async with self._auto_trace_async("do_work"):
            self._auto_log("info", "Working...")
```

#### Using Decorators
```python
from langswarm.core.observability.auto_instrumentation import instrument_agent_operation

@instrument_agent_operation("custom_action")
async def my_function():
    print("This is traced!")
```

## 📊 Trace Analysis

When enabled, traces are structured JSON objects containing:
-   `trace_id`: Unique ID for the entire transaction.
-   `span_id`: ID for the specific operation.
-   `parent_id`: ID of the calling operation.
-   `component`: The system component (e.g., `agent`, `tool`).
-   `duration_ms`: Execution time.

### Example Console Output
```text
[INFO] [agent] Started operation: agent.chat (trace_id=abc-123)
[INFO] [tool] Executing tool: filesystem (trace_id=abc-123)
[INFO] [agent] Completed operation: agent.chat (duration=1200ms)
```

## 📈 Metrics & Telemetry

Beyond traces, LangSwarm automatically collects metrics to track health and performance.

### Automatic Metrics
- `agent.chat.duration_seconds`: Histogram of response times.
- `agent.chat.input_tokens`: Counter for input tokens.
- `agent.chat.output_tokens`: Counter for output tokens.
- `tool.execution.errors_total`: Counter for tool failures.

### Custom Metrics
You can record your own business metrics using the mixin or helper:

```python
from langswarm.core.observability.auto_instrumentation import auto_record_metric

# Record a counter
auto_record_metric(
    "business.sales.completed", 
    1.0, 
    "counter", 
    region="us-east", 
    product="premium"
)

# Record a histogram (latency)
auto_record_metric("api.latency_ms", 350.0, "histogram")
```

## 📡 OpenTelemetry Integration

LangSwarm supports exporting all traces and metrics to OTLP-compatible backends (Jaeger, Honeycomb, DataDog, etc.).

### Installation
```bash
pip install langswarm[opentelemetry]
```

### Configuration (Environment Variables)
The easiest way to enable OTel is via environment variables:

```bash
# Service Identity
export OTEL_SERVICE_NAME="langswarm-app"

# Exporter Endpoint (e.g., Jaeger or Collector)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Optional Headers (e.g., for Honeycomb/DataDog)
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=YOUR_KEY"
```

### Automatic startup
When `opentelemetry_enabled=True` is passed to the provider (or configured via env vars), LangSwarm automatically:
1.  Batches traces for performance.
2.  Exports metrics (counters/histograms) to the configured endpoint.
3.  Handles connection failures gracefully (logs warning, doesn't crash app).
