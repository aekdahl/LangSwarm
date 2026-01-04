# OpenTelemetry Examples

This section provides comprehensive examples of integrating LangSwarm with OpenTelemetry for production-grade observability.

The source code for these examples is available in the `examples/opentelemetry/` directory.

## 1. Hybrid Instrumentation
**File:** `examples/opentelemetry/hybrid_instrumentation_example.py`

Demonstrates the **Hybrid Approach**: zero-config auto-instrumentation for core features, plus manual tracing for custom logic.

- **Auto-Instrumentation**: Automatically traces agent chats, LLM calls, and tool usage.
- **Manual Tracing**: Decorators `@instrument_agent_operation` and `@auto_instrument_function` for your custom code.

```python
from langswarm.core.observability import (
    auto_instrument_function,
    instrument_agent_operation
)

# Your custom business logic gets full traces
@auto_instrument_function("data_processing", "custom_component")
async def process_data(data: dict):
    # ...
```

## 2. Jaeger Integration
**File:** `examples/opentelemetry/jaeger_example.py`

Shows how to export traces to Jaeger for distributed trace visualization.

- **Setup**: Configures `opentelemetry_jaeger_endpoint`.
- **Result**: Visualizes the full request lifecycle (User -> Agent -> LLM -> Tool -> Result).

## 3. Prometheus Metrics
**File:** `examples/opentelemetry/prometheus_example.py`

Demonstrates exporting metrics to Prometheus.

- **Metrics Exposed**:
    - `langswarm_agent_requests_total`
    - `langswarm_agent_response_time_seconds`
    - `langswarm_tool_executions_total`
    - `langswarm_active_agents`
- **Config**: Sets up a scraping endpoint at `:8000/metrics`.

## 4. Multi-Exporter Setup
**File:** `examples/opentelemetry/multi_exporter_example.py`

A production-ready configuration that sends traces to Jaeger/OTLP and metrics to Prometheus simultaneously.

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    # Send traces to Jaeger
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
    # AND expose metrics for Prometheus
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000
)
```

## Running the Examples

A `docker-compose.yml` is provided in the examples directory to spin up the observability stack (Jaeger, Prometheus, Grafana).

```bash
# 1. Start the stack
cd examples/opentelemetry
docker-compose up -d

# 2. Run an example
python hybrid_instrumentation_example.py

# 3. View traces
# Open http://localhost:16686 (Jaeger)
```
