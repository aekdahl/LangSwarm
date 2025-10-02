# OpenTelemetry Integration for LangSwarm

**Export LangSwarm telemetry data to external observability tools using OpenTelemetry**

## 🎯 Overview

LangSwarm's OpenTelemetry integration enables you to export traces, metrics, and logs to any OpenTelemetry-compatible observability platform, including:

- **Jaeger** - Distributed tracing
- **Prometheus** - Metrics collection
- **Grafana** - Visualization and dashboards
- **DataDog** - APM and monitoring
- **New Relic** - Application performance monitoring
- **Honeycomb** - Observability platform
- **Any OTLP-compatible endpoint**

## 🚀 Quick Start

### Installation

Install LangSwarm with OpenTelemetry support:

```bash
pip install langswarm[opentelemetry]
```

### Basic Configuration

```python
from langswarm.core.observability import (
    ObservabilityConfig, initialize_auto_instrumentation, 
    start_auto_instrumentation
)

# Configure observability with OpenTelemetry
config = ObservabilityConfig(
    # Enable OpenTelemetry integration
    opentelemetry_enabled=True,
    opentelemetry_service_name="my-langswarm-app",
    opentelemetry_service_version="1.0.0",
    
    # OTLP endpoint (works with most platforms)
    opentelemetry_otlp_endpoint="http://localhost:4317",
    
    # Or use Jaeger directly
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
    
    # Enable Prometheus metrics
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000,
)

# Initialize automatic instrumentation
provider = initialize_auto_instrumentation(config)
await start_auto_instrumentation()

# Your LangSwarm code - key operations are automatically traced!
from langswarm.core.agents import BaseAgent, AgentConfiguration, ProviderType

agent_config = AgentConfiguration(provider=ProviderType.OPENAI, model="gpt-4")
agent = BaseAgent("my-agent", agent_config, provider)

await agent.initialize()  # ← Automatically traced
response = await agent.chat("Hello world")  # ← Automatically traced to OpenTelemetry
```

## 📊 Supported Exporters

### 1. OTLP (OpenTelemetry Protocol)

**Universal exporter that works with most observability platforms**

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_otlp_endpoint="http://your-otlp-endpoint:4317",
    opentelemetry_otlp_headers={
        "Authorization": "Bearer your-api-key"
    }
)
```

**Compatible platforms:**
- Jaeger (via OTLP receiver)
- DataDog (via OTLP)
- New Relic (via OTLP)
- Honeycomb (via OTLP)
- Grafana Cloud (via OTLP)

### 2. Jaeger

**Direct Jaeger integration for distributed tracing**

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_jaeger_endpoint="http://jaeger-collector:14268/api/traces"
)
```

### 3. Prometheus

**Metrics export for Prometheus scraping**

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000,  # Metrics available at :8000/metrics
    opentelemetry_prometheus_host="0.0.0.0"
)
```

## 🔧 Configuration Options

### Complete Configuration

```python
from langswarm.core.observability import ObservabilityConfig

config = ObservabilityConfig(
    # Basic observability
    enabled=True,
    log_level=LogLevel.INFO,
    tracing_enabled=True,
    metrics_enabled=True,
    
    # OpenTelemetry integration
    opentelemetry_enabled=True,
    
    # Service identification
    opentelemetry_service_name="langswarm-app",
    opentelemetry_service_version="1.0.0",
    
    # OTLP configuration
    opentelemetry_otlp_endpoint="http://localhost:4317",
    opentelemetry_otlp_headers={
        "Authorization": "Bearer your-token",
        "X-Custom-Header": "value"
    },
    
    # Jaeger configuration
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
    
    # Prometheus configuration
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000,
)
```

### Environment Variables

You can also configure OpenTelemetry using environment variables:

```bash
# Service information
export OTEL_SERVICE_NAME="langswarm-app"
export OTEL_SERVICE_VERSION="1.0.0"

# OTLP endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your-token"

# Jaeger endpoint
export OTEL_EXPORTER_JAEGER_ENDPOINT="http://localhost:14268/api/traces"
```

## 🏗️ Platform-Specific Setup

### Jaeger

1. **Start Jaeger (Docker)**:
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

2. **Configure LangSwarm**:
```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces"
)
```

3. **View traces**: http://localhost:16686

### Prometheus + Grafana

1. **Start Prometheus and Grafana**:
```yaml
# docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

2. **Configure Prometheus** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'langswarm'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

3. **Configure LangSwarm**:
```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000
)
```

### DataDog

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_otlp_endpoint="https://api.datadoghq.com/api/v2/otlp",
    opentelemetry_otlp_headers={
        "DD-API-KEY": "your-datadog-api-key"
    }
)
```

### Honeycomb

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_otlp_endpoint="https://api.honeycomb.io/v1/traces",
    opentelemetry_otlp_headers={
        "x-honeycomb-team": "your-api-key",
        "x-honeycomb-dataset": "langswarm"
    }
)
```

## 📈 What Gets Exported

LangSwarm uses a **hybrid approach** to observability:
- **Key operations are automatically instrumented** - Zero configuration required
- **Detailed tracing available manually** - For fine-grained control when needed

### Automatic Instrumentation ✨

**Agent Operations** (automatically traced):
- `agent.initialize` - Agent initialization and configuration
- `agent.chat` - Chat requests and responses
- `agent.provider_call` - LLM API calls with token usage
- Error handling and retry logic

**Tool Execution** (automatically traced):
- `tool.execute` - Tool method execution
- `tool.method_call` - Individual method calls
- Parameter validation and result processing
- Error handling and performance metrics

**Workflow Execution** (automatically traced):
- `workflow.execute` - Workflow execution (sync/async/parallel)
- `workflow.execute_sync` - Synchronous workflow execution
- `workflow.execute_async` - Asynchronous workflow execution
- Step-by-step progress and error handling

### Manual Instrumentation 🔧

For detailed tracing, use decorators and context managers:

```python
from langswarm.core.observability import (
    instrument_agent_operation, instrument_tool_operation,
    auto_instrument_function
)

# Agent-specific instrumentation
@instrument_agent_operation("custom_reasoning")
async def complex_reasoning(agent, query):
    # Automatically traced with agent context
    return reasoning_result

# Tool-specific instrumentation  
@instrument_tool_operation("data_validation")
async def validate_data(data):
    # Automatically traced with tool context
    return validation_result

# Generic instrumentation
@auto_instrument_function("business_logic", "custom_component")
async def process_business_logic(data):
    # Automatically traced with custom component
    return processed_data
```

**Trace attributes include:**
- Operation name and duration
- Component type (agent, tool, workflow, etc.)
- Success/failure status
- Input/output sizes
- Error messages and stack traces
- Custom tags and metadata

### Metrics

Exported metrics include:

- **Counters**: Operation counts, error counts, success rates
- **Gauges**: Active sessions, memory usage, queue sizes
- **Histograms**: Response times, token usage, cost tracking
- **Timers**: Operation durations, latency percentiles

**Example metrics:**
```
langswarm_operations_total{component="agent", status="success"}
langswarm_response_time_seconds{component="agent", operation="chat"}
langswarm_token_usage_total{model="gpt-4", operation="completion"}
langswarm_active_sessions{component="session_manager"}
```

## 🔍 Manual Export

For advanced use cases, you can manually export specific spans and metrics:

```python
from langswarm.core.observability import TraceSpan, MetricPoint, MetricType

# Get observability provider
provider = get_observability_provider()

# Create custom span
span = TraceSpan(
    span_id="custom-span-123",
    trace_id="trace-456",
    operation_name="custom_operation",
    start_time=datetime.utcnow(),
    component="custom_component",
    tags={"custom_tag": "value"}
)

# Create custom metric
metric = MetricPoint(
    name="custom_metric",
    value=42.0,
    metric_type=MetricType.GAUGE,
    timestamp=datetime.utcnow(),
    tags={"environment": "production"}
)

# Export to OpenTelemetry
provider.export_to_opentelemetry(
    spans=[span],
    metrics=[metric]
)
```

## 🛠️ Troubleshooting

### Common Issues

1. **OpenTelemetry dependencies not installed**:
```bash
pip install langswarm[opentelemetry]
```

2. **Connection refused to OTLP endpoint**:
   - Check endpoint URL and port
   - Verify firewall/network settings
   - Ensure OTLP receiver is running

3. **No traces appearing**:
   - Check sampling rate (should be > 0)
   - Verify endpoint configuration
   - Check logs for export errors

4. **Prometheus metrics not available**:
   - Verify port is not in use
   - Check firewall settings
   - Ensure Prometheus is configured to scrape the correct endpoint

### Debug Configuration

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("langswarm.core.observability.opentelemetry_exporter").setLevel(logging.DEBUG)

config = ObservabilityConfig(
    log_level=LogLevel.DEBUG,
    opentelemetry_enabled=True,
    # ... other config
)
```

### Health Check

Check if OpenTelemetry integration is working:

```python
provider = get_observability_provider()
health = provider.get_health_status()
print(f"OpenTelemetry enabled: {provider.opentelemetry_enabled}")
```

## 📚 Examples

See the `examples/` directory for complete working examples:

- `examples/opentelemetry/jaeger_example.py` - Jaeger integration
- `examples/opentelemetry/prometheus_example.py` - Prometheus metrics
- `examples/opentelemetry/datadog_example.py` - DataDog integration
- `examples/opentelemetry/multi_exporter_example.py` - Multiple exporters

## 🔗 Related Documentation

- [LangSwarm Observability Guide](./README.md)
- [Configuration Reference](../user-guides/configuration/)
- [Troubleshooting Guide](../troubleshooting/observability.md)
- [OpenTelemetry Official Docs](https://opentelemetry.io/docs/)
