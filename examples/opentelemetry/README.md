# LangSwarm OpenTelemetry Examples

This directory contains complete examples demonstrating how to integrate LangSwarm with various observability platforms using OpenTelemetry.

## 📁 Files

- **`jaeger_example.py`** - Export traces to Jaeger for distributed tracing
- **`prometheus_example.py`** - Export metrics to Prometheus for monitoring
- **`multi_exporter_example.py`** - Export to multiple platforms simultaneously
- **`docker-compose.yml`** - Complete observability stack (Jaeger + Prometheus + Grafana)
- **`prometheus.yml`** - Prometheus configuration for scraping LangSwarm metrics

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install langswarm[opentelemetry]
```

### 2. Start Observability Stack

```bash
# Start Jaeger, Prometheus, and Grafana
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Run Examples

```bash
# Jaeger tracing example
python jaeger_example.py

# Prometheus metrics example  
python prometheus_example.py

# Multi-exporter example
python multi_exporter_example.py
```

### 4. View Results

- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 📊 What You'll See

### Jaeger Traces

The examples generate realistic distributed traces showing:

- **Agent operations** - Chat requests, response generation
- **Workflow execution** - Multi-step processes with nested spans
- **Tool usage** - Individual tool invocations and results
- **Error tracking** - Failed operations with error details
- **Performance data** - Operation durations and resource usage

### Prometheus Metrics

The examples export comprehensive metrics including:

- **Counters**: `langswarm_agent_requests_total`, `langswarm_tool_executions_total`
- **Histograms**: `langswarm_agent_response_time_seconds`, `langswarm_tool_execution_time_seconds`
- **Gauges**: `langswarm_active_agents`, `langswarm_memory_usage_mb`

### Example Prometheus Queries

```promql
# Request rate by agent type
rate(langswarm_agent_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, langswarm_agent_response_time_seconds)

# Error rate by tool
rate(langswarm_tool_executions_total{status="error"}[5m]) / rate(langswarm_tool_executions_total[5m])

# Active agents over time
langswarm_active_agents
```

## 🔧 Configuration Examples

### Environment Variables

```bash
# Jaeger
export JAEGER_ENDPOINT="http://localhost:14268/api/traces"

# OTLP (for DataDog, New Relic, etc.)
export OTLP_ENDPOINT="https://api.datadoghq.com/api/v2/otlp"
export OTLP_TOKEN="your-api-key"

# Prometheus
export PROMETHEUS_PORT="8000"
```

### Code Configuration

```python
from langswarm.core.observability import ObservabilityConfig

# Jaeger only
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces"
)

# Prometheus only
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000
)

# Multiple exporters
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
    opentelemetry_otlp_endpoint="http://localhost:4317",
    opentelemetry_prometheus_enabled=True,
    opentelemetry_prometheus_port=8000
)
```

## 🌐 Platform-Specific Examples

### DataDog

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_otlp_endpoint="https://api.datadoghq.com/api/v2/otlp",
    opentelemetry_otlp_headers={"DD-API-KEY": "your-api-key"}
)
```

### New Relic

```python
config = ObservabilityConfig(
    opentelemetry_enabled=True,
    opentelemetry_otlp_endpoint="https://otlp.nr-data.net:4317",
    opentelemetry_otlp_headers={"api-key": "your-license-key"}
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

## 🛠️ Troubleshooting

### Common Issues

1. **"Connection refused" errors**
   - Ensure observability services are running: `docker-compose ps`
   - Check port availability: `netstat -tulpn | grep :4317`

2. **No traces appearing in Jaeger**
   - Verify Jaeger endpoint configuration
   - Check sampling rate (should be > 0)
   - Look for export errors in logs

3. **Prometheus not scraping metrics**
   - Verify metrics endpoint: `curl http://localhost:8000/metrics`
   - Check Prometheus targets: http://localhost:9090/targets
   - Ensure firewall allows access to port 8000

### Debug Mode

Enable debug logging to troubleshoot:

```python
import logging
logging.getLogger("langswarm.core.observability.opentelemetry_exporter").setLevel(logging.DEBUG)
```

## 📚 Next Steps

- Explore the [OpenTelemetry Integration Guide](../../docs/observability/opentelemetry-integration.md)
- Set up alerting rules in Prometheus
- Create custom Grafana dashboards
- Integrate with your production observability platform
