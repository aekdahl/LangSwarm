# LangSwarm V2 Observability Guide

**Production-ready monitoring, logging, tracing, and metrics for comprehensive system visibility**

## 🎯 Overview

LangSwarm V2 provides a unified observability system that delivers comprehensive monitoring, structured logging, distributed tracing, and metrics collection across all components. The system is designed for both development debugging and production monitoring with minimal performance overhead.

**Key Benefits:**
- **Unified System**: Single observability provider managing logging, tracing, and metrics
- **Correlation**: Automatic correlation between logs, traces, and metrics with trace IDs
- **Performance**: Minimal overhead with configurable sampling (< 5% CPU, < 10MB memory)
- **Production Ready**: Development and production presets with enterprise features
- **Integration**: Deep integration with all V2 components (agents, tools, sessions, memory, workflows)
- **Zero Dependencies**: No external observability dependencies required

---

## 🚀 Quick Start

### **Basic Observability Setup**

```python
from langswarm.core.observability import ObservabilityProvider

# Development setup with full debugging
observability = ObservabilityProvider.create_development()

# Production setup with optimized performance
observability = ObservabilityProvider.create_production()

# Custom configuration
observability = ObservabilityProvider.create({
    "logging": {
        "level": "INFO",
        "output": "file",
        "file_path": "logs/langswarm.log"
    },
    "tracing": {
        "enabled": True,
        "sampling_rate": 0.1  # 10% sampling
    },
    "metrics": {
        "enabled": True,
        "export_interval": 60
    }
})

# Initialize observability for the application
await observability.initialize()
print("✅ Observability system initialized")
```

### **Component Integration**

```python
from langswarm.core.observability.integrations import (
    AgentObservability,
    ToolObservability,
    SessionObservability
)

# Enable observability for agents
agent_obs = AgentObservability(observability)
await agent_obs.initialize()

# Enable observability for tools
tool_obs = ToolObservability(observability) 
await tool_obs.initialize()

# Enable observability for sessions
session_obs = SessionObservability(observability)
await session_obs.initialize()

print("✅ Component observability enabled")
```

---

## 📊 Logging System

### **Structured Logging**

```python
from langswarm.core.observability import V2Logger

# Get logger instance
logger = observability.get_logger("my_component")

# Structured logging with context
logger.info(
    "Processing user request",
    user_id="user123",
    request_type="chat",
    component="agent_system"
)

logger.error(
    "Failed to process request",
    user_id="user123",
    error_code="TIMEOUT",
    error_details={"timeout_seconds": 30},
    component="agent_system"
)

# Trace correlation (automatic trace ID injection)
with observability.tracer.start_span("user_request") as span:
    logger.info("Request started", span_id=span.span_id)
    # Process request
    logger.info("Request completed", span_id=span.span_id)
```

### **Log Configuration**

```python
# Development logging configuration
dev_config = {
    "logging": {
        "level": "DEBUG",
        "output": "console",  # Console output for development
        "format": "detailed",  # Include all context
        "correlation": True,   # Include trace correlation
        "color": True         # Colored console output
    }
}

# Production logging configuration  
prod_config = {
    "logging": {
        "level": "INFO",
        "output": "file",
        "file_path": "/var/log/langswarm/app.log",
        "format": "json",      # Structured JSON logs
        "rotation": {
            "max_size": "100MB",
            "backup_count": 10
        },
        "correlation": True    # Include trace IDs
    }
}

# Custom logging with filtering
custom_config = {
    "logging": {
        "level": "INFO",
        "output": "both",      # Console and file
        "filters": {
            "exclude_components": ["debug_tool"],
            "min_level_by_component": {
                "agent_system": "WARN",
                "session_system": "INFO"
            }
        }
    }
}
```

### **Log Output Examples**

**Development Console Output:**
```
[2024-01-15 14:30:15.123] INFO  [agent_system] Processing user request
  └── user_id: user123
  └── request_type: chat
  └── trace_id: abc123def456
  └── span_id: span789

[2024-01-15 14:30:15.145] ERROR [agent_system] Failed to process request
  └── user_id: user123
  └── error_code: TIMEOUT
  └── error_details: {"timeout_seconds": 30}
  └── trace_id: abc123def456
  └── span_id: span789
```

**Production JSON Output:**
```json
{
  "timestamp": "2024-01-15T14:30:15.123Z",
  "level": "INFO",
  "component": "agent_system",
  "message": "Processing user request",
  "context": {
    "user_id": "user123",
    "request_type": "chat"
  },
  "trace_id": "abc123def456",
  "span_id": "span789",
  "service": "langswarm_v2",
  "version": "2.0.0"
}
```

---

## 🔍 Distributed Tracing

### **Automatic Tracing**

```python
from langswarm.core.observability import V2Tracer

# Get tracer instance
tracer = observability.get_tracer("my_service")

# Manual span creation
with tracer.start_span("user_request_processing") as span:
    span.set_attribute("user_id", "user123")
    span.set_attribute("request_type", "chat")
    
    # Nested spans automatically inherit parent context
    with tracer.start_span("agent_processing") as agent_span:
        agent_span.set_attribute("agent_type", "chat_agent")
        # Process with agent
        
    with tracer.start_span("response_generation") as response_span:
        response_span.set_attribute("model", "gpt-4")
        # Generate response

# Decorator-based tracing
@tracer.trace_function
async def process_user_message(user_id: str, message: str) -> str:
    """Function automatically traced with parameters"""
    # Function execution automatically creates span
    return await agent.process_message(message)

# Class method tracing
class ChatAgent:
    @tracer.trace_method
    async def generate_response(self, message: str) -> str:
        """Method automatically traced with class context"""
        return await self.model.generate(message)
```

### **Span Hierarchy and Context**

```python
# Complex operation with nested spans
async def handle_user_request(user_id: str, message: str):
    with tracer.start_span("user_request") as root_span:
        root_span.set_attributes({
            "user_id": user_id,
            "message_length": len(message),
            "service": "chat_service"
        })
        
        # Authentication span
        with tracer.start_span("authentication") as auth_span:
            auth_span.set_attribute("auth_method", "token")
            user = await authenticate_user(user_id)
            auth_span.set_attribute("auth_success", user is not None)
        
        # Agent processing span
        with tracer.start_span("agent_processing") as agent_span:
            agent_span.set_attribute("agent_id", "chat_agent_v2")
            
            # Memory retrieval span
            with tracer.start_span("memory_retrieval") as memory_span:
                memory_span.set_attribute("memory_backend", "vector")
                context = await get_user_context(user_id)
                memory_span.set_attribute("context_items", len(context))
            
            # Response generation span
            with tracer.start_span("response_generation") as gen_span:
                gen_span.set_attribute("model", "gpt-4")
                gen_span.set_attribute("max_tokens", 2048)
                response = await generate_response(message, context)
                gen_span.set_attribute("response_length", len(response))
        
        # Response logging
        root_span.set_attribute("response_generated", True)
        root_span.set_status("SUCCESS")
        
        return response
```

### **Trace Configuration**

```python
# Development tracing (full tracing)
dev_tracing = {
    "tracing": {
        "enabled": True,
        "sampling_rate": 1.0,  # Trace everything
        "span_processor": "simple",
        "exporter": "console",
        "include_attributes": True,
        "include_events": True
    }
}

# Production tracing (sampled)
prod_tracing = {
    "tracing": {
        "enabled": True,
        "sampling_rate": 0.1,  # Sample 10%
        "span_processor": "batch",
        "exporter": "otlp",  # OpenTelemetry Protocol
        "endpoint": "http://jaeger:14268/api/traces",
        "max_span_attributes": 50,
        "max_events_per_span": 20
    }
}

# Component-specific sampling
custom_tracing = {
    "tracing": {
        "enabled": True,
        "sampling_rules": [
            {"component": "agent_system", "rate": 0.5},
            {"component": "tool_system", "rate": 0.2},
            {"component": "session_system", "rate": 0.1},
            {"operation": "error", "rate": 1.0}  # Always trace errors
        ]
    }
}
```

---

## 📈 Metrics Collection

### **Built-in Metrics**

```python
from langswarm.core.observability import V2Metrics

# Get metrics instance
metrics = observability.get_metrics()

# Counter metrics
metrics.increment_counter(
    "requests_total",
    labels={"component": "agent", "status": "success"}
)

metrics.increment_counter(
    "errors_total", 
    labels={"component": "agent", "error_type": "timeout"}
)

# Gauge metrics (current values)
metrics.set_gauge(
    "active_sessions",
    value=42,
    labels={"component": "session_manager"}
)

metrics.set_gauge(
    "memory_usage_mb",
    value=256.5,
    labels={"component": "vector_store"}
)

# Histogram metrics (distributions)
metrics.record_histogram(
    "request_duration_ms",
    value=1250.0,
    labels={"component": "agent", "operation": "chat"}
)

metrics.record_histogram(
    "token_usage",
    value=150,
    labels={"model": "gpt-4", "operation": "completion"}
)

# Timer context manager
with metrics.timer("operation_duration", labels={"operation": "user_request"}):
    # Timed operation
    result = await process_request()
```

### **Custom Metrics**

```python
# Define custom metrics for your application
class ChatServiceMetrics:
    def __init__(self, metrics: V2Metrics):
        self.metrics = metrics
        
        # Application-specific counters
        self.message_counter = metrics.create_counter(
            "chat_messages_total",
            description="Total chat messages processed"
        )
        
        self.user_counter = metrics.create_counter(
            "active_users_total", 
            description="Total active users"
        )
        
        # Application-specific gauges
        self.queue_size_gauge = metrics.create_gauge(
            "message_queue_size",
            description="Current message queue size"
        )
        
        # Application-specific histograms
        self.response_time_histogram = metrics.create_histogram(
            "response_time_seconds",
            description="Chat response time distribution",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
    
    def record_message_processed(self, user_id: str, message_type: str):
        """Record a processed message"""
        self.message_counter.increment(labels={
            "user_id": user_id,
            "message_type": message_type
        })
    
    def update_queue_size(self, size: int):
        """Update current queue size"""
        self.queue_size_gauge.set(size)
    
    def record_response_time(self, duration: float, success: bool):
        """Record response time"""
        self.response_time_histogram.observe(
            duration,
            labels={"success": str(success).lower()}
        )

# Usage
chat_metrics = ChatServiceMetrics(metrics)
chat_metrics.record_message_processed("user123", "question")
chat_metrics.update_queue_size(15)
chat_metrics.record_response_time(1.25, True)
```

### **Metrics Export**

```python
# Export metrics for monitoring systems
metrics_data = await metrics.export_metrics()

print("Current Metrics:")
for metric_name, metric_data in metrics_data.items():
    print(f"  {metric_name}: {metric_data['value']} ({metric_data['type']})")
    if metric_data.get('labels'):
        for label_key, label_value in metric_data['labels'].items():
            print(f"    {label_key}: {label_value}")

# Prometheus format export
prometheus_output = await metrics.export_prometheus_format()
print("\nPrometheus Format:")
print(prometheus_output)

# JSON format export
json_output = await metrics.export_json_format()
print("\nJSON Format:")
print(json_output)
```

---

## 🔧 Component Observability

### **Agent System Observability**

```python
from langswarm.core.observability.integrations import AgentObservability

# Enable agent observability
agent_obs = AgentObservability(observability)
await agent_obs.initialize()

# Agent operations are automatically tracked
from langswarm.core.agents import AgentBuilder

agent = (AgentBuilder()
    .with_provider("openai")
    .with_model("gpt-4")
    .with_system_prompt("You are a helpful assistant")
    .build())

# This operation is automatically traced and logged
response = await agent.generate_response("Hello!")

# Automatic metrics collected:
# - agent_requests_total
# - agent_response_time_seconds  
# - agent_errors_total
# - agent_token_usage_total
```

### **Tool System Observability**

```python
from langswarm.core.observability.integrations import ToolObservability

# Enable tool observability
tool_obs = ToolObservability(observability)
await tool_obs.initialize()

# Tool executions are automatically monitored
from langswarm.core.tools import ToolRegistry

registry = ToolRegistry()
calculator = registry.get_tool("calculator")

# This execution is automatically traced
result = await calculator.execute("add", {"a": 5, "b": 3})

# Automatic metrics collected:
# - tool_executions_total
# - tool_execution_time_seconds
# - tool_errors_total
# - tool_success_rate
```

### **Session System Observability**

```python
from langswarm.core.observability.integrations import SessionObservability

# Enable session observability
session_obs = SessionObservability(observability)
await session_obs.initialize()

# Session operations are automatically monitored
from langswarm.core.session import create_session_manager

manager = create_session_manager(storage="sqlite")
session = await manager.create_session("user123", "openai", "gpt-4")

# These operations are automatically traced and logged
await session.send_message("Hello!")
messages = await session.get_messages()

# Automatic metrics collected:
# - session_creations_total
# - session_messages_total
# - session_duration_seconds
# - session_errors_total
```

### **Memory System Observability**

```python
from langswarm.core.observability.integrations import MemoryObservability

# Enable memory observability
memory_obs = MemoryObservability(observability)
await memory_obs.initialize()

# Memory operations are automatically tracked
from langswarm.core.memory import MemoryFactory

memory = MemoryFactory.create("vector", config={
    "vector_store": "sqlite",
    "db_path": "memory.db"
})

# These operations are automatically traced
await memory.save("user123", "key", "value")
value = await memory.load("user123", "key")

# Automatic metrics collected:
# - memory_operations_total
# - memory_operation_time_seconds
# - memory_storage_size_bytes
# - memory_cache_hits_total
```

### **Workflow System Observability**

```python
from langswarm.core.observability.integrations import WorkflowObservability

# Enable workflow observability
workflow_obs = WorkflowObservability(observability)
await workflow_obs.initialize()

# Workflow executions are automatically monitored
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder()
    .add_step("analyze", analyzer_tool)
    .add_step("respond", response_tool)
    .build())

# This execution is automatically traced end-to-end
result = await workflow.execute({"input": "user message"})

# Automatic metrics collected:
# - workflow_executions_total
# - workflow_execution_time_seconds
# - workflow_step_duration_seconds
# - workflow_errors_total
```

---

## ⚙️ Configuration and Presets

### **Development Configuration**

```python
# Optimized for debugging and development
development_config = {
    "logging": {
        "level": "DEBUG",
        "output": "console",
        "format": "detailed",
        "color": True,
        "correlation": True
    },
    "tracing": {
        "enabled": True,
        "sampling_rate": 1.0,  # Trace everything
        "exporter": "console",
        "include_stack_traces": True
    },
    "metrics": {
        "enabled": True,
        "export_interval": 10,  # Frequent exports
        "include_histograms": True
    },
    "integrations": {
        "all_components": True,
        "detailed_spans": True,
        "parameter_logging": True
    }
}

# Apply development configuration
observability = ObservabilityProvider.create(development_config)
```

### **Production Configuration**

```python
# Optimized for performance and production monitoring
production_config = {
    "logging": {
        "level": "INFO",
        "output": "file",
        "file_path": "/var/log/langswarm/app.log",
        "format": "json",
        "rotation": {
            "max_size": "100MB",
            "backup_count": 10
        },
        "correlation": True
    },
    "tracing": {
        "enabled": True,
        "sampling_rate": 0.1,  # 10% sampling
        "exporter": "otlp",
        "endpoint": "http://jaeger:14268/api/traces",
        "batch_processor": True,
        "max_export_batch_size": 512
    },
    "metrics": {
        "enabled": True,
        "export_interval": 60,
        "prometheus_endpoint": "/metrics",
        "exclude_labels": ["user_id"]  # Privacy
    },
    "integrations": {
        "essential_components": True,
        "error_only_spans": False,
        "parameter_logging": False  # Performance
    },
    "performance": {
        "max_spans_per_trace": 100,
        "max_attributes_per_span": 20,
        "span_timeout_seconds": 300
    }
}

# Apply production configuration
observability = ObservabilityProvider.create(production_config)
```

### **Environment-Based Configuration**

```python
import os

# Configuration based on environment variables
env_config = {
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "output": os.getenv("LOG_OUTPUT", "console"),
        "file_path": os.getenv("LOG_FILE_PATH", "logs/app.log")
    },
    "tracing": {
        "enabled": os.getenv("TRACING_ENABLED", "true").lower() == "true",
        "sampling_rate": float(os.getenv("TRACING_SAMPLING_RATE", "0.1")),
        "endpoint": os.getenv("TRACING_ENDPOINT", "http://localhost:14268")
    },
    "metrics": {
        "enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
        "export_interval": int(os.getenv("METRICS_INTERVAL", "60"))
    }
}

observability = ObservabilityProvider.create(env_config)
```

---

## 🎯 Performance and Best Practices

### **Performance Characteristics**

- **Logging**: 500+ operations/second with minimal overhead
- **Tracing**: 200+ operations/second with 10% sampling
- **Metrics**: 800+ operations/second with efficient collection
- **Memory**: < 10MB additional memory usage
- **CPU**: < 5% additional CPU usage under normal load

### **Best Practices**

#### **Development**
- Use full tracing and debug logging for comprehensive debugging
- Enable parameter logging for detailed troubleshooting
- Use console output for immediate feedback
- Enable colored output for better readability

#### **Production**
- Use appropriate sampling rates (5-10% for tracing)
- Configure log rotation to manage disk space
- Use structured JSON logging for log aggregation
- Monitor metrics export performance
- Filter sensitive data from logs and traces

#### **Performance Optimization**
- Use batch processors for high-throughput scenarios
- Configure appropriate buffer sizes
- Monitor observability system overhead
- Use async operations for non-blocking performance

#### **Security Considerations**
- Exclude sensitive data from logs and traces
- Use secure endpoints for external exporters
- Implement access controls for observability data
- Configure data retention policies

---

## 🔍 Debugging and Troubleshooting

### **Common Debugging Patterns**

```python
# Debugging agent issues
async def debug_agent_processing():
    with tracer.start_span("debug_agent") as span:
        span.set_attribute("debug_session", True)
        
        logger.debug("Starting agent debug session")
        
        try:
            # Agent processing with detailed logging
            result = await agent.process_with_debug("test message")
            
            logger.debug("Agent processing completed", 
                        result_length=len(result),
                        processing_time=span.get_duration())
            
        except Exception as e:
            logger.error("Agent processing failed",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        stack_trace=traceback.format_exc())
            span.set_status("ERROR", str(e))
            raise

# Debugging with correlation
async def debug_with_correlation():
    correlation_id = "debug_session_123"
    
    with tracer.start_span("debug_operation", 
                          attributes={"correlation_id": correlation_id}) as span:
        
        logger.info("Debug operation started", 
                   correlation_id=correlation_id)
        
        # All nested operations will include correlation_id
        await process_with_nested_operations()
        
        logger.info("Debug operation completed",
                   correlation_id=correlation_id)
```

### **Error Investigation**

```python
# Comprehensive error tracking
async def investigate_error():
    try:
        result = await problematic_operation()
    except Exception as e:
        # Capture comprehensive error context
        error_context = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "component": "user_service",
            "operation": "process_request",
            "user_id": "user123",
            "timestamp": datetime.now().isoformat(),
            "trace_id": tracer.get_current_trace_id(),
            "span_id": tracer.get_current_span_id(),
            "stack_trace": traceback.format_exc()
        }
        
        logger.error("Operation failed with comprehensive context",
                    **error_context)
        
        # Record error metrics
        metrics.increment_counter("errors_total", labels={
            "component": "user_service",
            "error_type": type(e).__name__
        })
        
        raise
```

---

**LangSwarm V2's observability system provides comprehensive monitoring and debugging capabilities while maintaining excellent performance characteristics, making it suitable for both development and production environments.**
