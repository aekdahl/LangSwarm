"""
LangSwarm V2 Unified Observability System

Comprehensive observability platform that provides logging, tracing, metrics,
and monitoring capabilities across all V2 components for production-ready
debugging and operational visibility.
"""

from typing import Optional, Dict, Any

from .interfaces import (
    # Core interfaces
    ILogger, ITracer, IMetrics, IObservabilityProvider,
    
    # Data structures
    LogEvent, TraceSpan, MetricPoint, ObservabilityConfig,
    
    # Enums
    LogLevel, MetricType, SpanStatus,
    
    # Exceptions
    ObservabilityError, TracingError, MetricsError
)

from .logger import (
    V2Logger, create_logger, get_logger, configure_logging
)

from .tracer import (
    V2Tracer, create_tracer, get_tracer, trace_function, trace_async_function
)

from .metrics import (
    V2Metrics, create_metrics, get_metrics, counter, gauge, histogram, timer
)

from .provider import (
    ObservabilityProvider, create_observability_provider,
    create_development_observability, create_production_observability
)

from .integrations import (
    AgentObservability, ToolObservability, SessionObservability,
    MemoryObservability, WorkflowObservability, create_all_observability_integrations
)

from .token_tracking import (
    TokenUsageEvent, ContextSizeInfo, TokenBudgetConfig, BudgetCheckResult,
    TokenUsageAggregator, ContextSizeMonitor, TokenBudgetManager,
    TokenEventType, CompressionUrgency
)

from .opentelemetry_exporter import (
    OpenTelemetryConfig, OpenTelemetryExporter, OpenTelemetryIntegration
)

from .auto_instrumentation import (
    set_global_observability_provider, get_global_observability_provider,
    initialize_auto_instrumentation, start_auto_instrumentation, stop_auto_instrumentation,
    AutoInstrumentedMixin, auto_instrument_function,
    instrument_agent_operation, instrument_tool_operation, instrument_workflow_operation,
    instrument_memory_operation, instrument_session_operation
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core interfaces
    'ILogger',
    'ITracer', 
    'IMetrics',
    'IObservabilityProvider',
    
    # Data structures
    'LogEvent',
    'TraceSpan',
    'MetricPoint',
    'ObservabilityConfig',
    
    # Enums
    'LogLevel',
    'MetricType',
    'SpanStatus',
    
    # Exceptions
    'ObservabilityError',
    'TracingError',
    'MetricsError',
    
    # Logger
    'V2Logger',
    'create_logger',
    'get_logger',
    'configure_logging',
    
    # Tracer
    'V2Tracer',
    'create_tracer',
    'get_tracer',
    'trace_function',
    'trace_async_function',
    
    # Metrics
    'V2Metrics',
    'create_metrics',
    'get_metrics',
    'counter',
    'gauge',
    'histogram',
    'timer',
    
    # Provider
    'ObservabilityProvider',
    'create_observability_provider',
    'create_development_observability',
    'create_production_observability',
    
    # Integrations
    'AgentObservability',
    'ToolObservability',
    'SessionObservability',
    'MemoryObservability',
    'WorkflowObservability',
    'create_all_observability_integrations',
    
    # Token Tracking
    'TokenUsageEvent',
    'ContextSizeInfo',
    'TokenBudgetConfig',
    'BudgetCheckResult',
    'TokenUsageAggregator',
    'ContextSizeMonitor', 
    'TokenBudgetManager',
    'TokenEventType',
    'CompressionUrgency',
    
    # OpenTelemetry Integration
    'OpenTelemetryConfig',
    'OpenTelemetryExporter',
    'OpenTelemetryIntegration',
    
    # Auto-Instrumentation
    'set_global_observability_provider',
    'get_global_observability_provider',
    'initialize_auto_instrumentation',
    'start_auto_instrumentation',
    'stop_auto_instrumentation',
    'AutoInstrumentedMixin',
    'auto_instrument_function',
    'instrument_agent_operation',
    'instrument_tool_operation',
    'instrument_workflow_operation',
    'instrument_memory_operation',
    'instrument_session_operation'
]

# Global observability provider
_global_provider: Optional[ObservabilityProvider] = None


def get_observability_provider() -> Optional[ObservabilityProvider]:
    """Get the global observability provider"""
    return _global_provider


def set_observability_provider(provider: ObservabilityProvider):
    """Set the global observability provider"""
    global _global_provider
    _global_provider = provider


def initialize_observability(config: Optional[Dict[str, Any]] = None):
    """Initialize global observability with configuration"""
    if not get_observability_provider():
        provider = create_observability_provider(config or {})
        set_observability_provider(provider)


# Convenience functions for quick access
def log_info(message: str, **kwargs):
    """Quick info logging"""
    provider = get_observability_provider()
    if provider:
        provider.logger.info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Quick error logging"""
    provider = get_observability_provider()
    if provider:
        provider.logger.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Quick debug logging"""
    provider = get_observability_provider()
    if provider:
        provider.logger.debug(message, **kwargs)


def trace_operation(operation_name: str):
    """Quick operation tracing"""
    provider = get_observability_provider()
    if provider:
        return provider.tracer.start_span(operation_name)
    else:
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()


def record_metric(name: str, value: float, metric_type: str = "gauge", **tags):
    """Quick metric recording"""
    provider = get_observability_provider()
    if provider:
        if metric_type == "counter":
            provider.metrics.increment_counter(name, value, **tags)
        elif metric_type == "gauge":
            provider.metrics.set_gauge(name, value, **tags)
        elif metric_type == "histogram":
            provider.metrics.record_histogram(name, value, **tags)
