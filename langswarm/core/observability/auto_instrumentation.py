"""
LangSwarm V2 Automatic Instrumentation System

Provides automatic observability instrumentation for core LangSwarm operations
using a hybrid approach: key operations are auto-instrumented, detailed tracing
remains manual for fine-grained control.
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, Any, Dict, Callable, AsyncIterator
from datetime import datetime

from .interfaces import ObservabilityConfig
from .provider import ObservabilityProvider

logger = logging.getLogger(__name__)

# Global observability provider for automatic instrumentation
_global_observability_provider: Optional[ObservabilityProvider] = None


def set_global_observability_provider(provider: ObservabilityProvider):
    """Set the global observability provider for automatic instrumentation"""
    global _global_observability_provider
    _global_observability_provider = provider
    logger.info("Global observability provider set for automatic instrumentation")


def get_global_observability_provider() -> Optional[ObservabilityProvider]:
    """Get the global observability provider"""
    return _global_observability_provider


def is_auto_instrumentation_enabled() -> bool:
    """Check if automatic instrumentation is enabled"""
    provider = get_global_observability_provider()
    return provider is not None and provider.config.enabled


@contextmanager
def auto_trace_operation(operation_name: str, component: str, **tags):
    """
    Automatically trace an operation if observability is enabled.
    
    This is the core context manager used by all automatic instrumentation.
    """
    provider = get_global_observability_provider()
    
    if not provider or not provider.config.tracing_enabled:
        # No-op if observability not available or disabled
        yield None
        return
    
    # Use the provider's tracer to create a span
    with provider.tracer.start_span(operation_name, component=component, **tags) as span:
        if span:
            span.add_tag("auto_instrumented", True)
            span.add_tag("component", component)
        yield span


@asynccontextmanager
async def auto_trace_async_operation(operation_name: str, component: str, **tags):
    """
    Automatically trace an async operation if observability is enabled.
    """
    provider = get_global_observability_provider()
    
    if not provider or not provider.config.tracing_enabled:
        # No-op if observability not available or disabled
        yield None
        return
    
    # Use the provider's tracer to create a span
    with provider.tracer.start_span(operation_name, component=component, **tags) as span:
        if span:
            span.add_tag("auto_instrumented", True)
            span.add_tag("component", component)
        yield span


def auto_record_metric(metric_name: str, value: float, metric_type: str = "counter", **tags):
    """
    Automatically record a metric if observability is enabled.
    """
    provider = get_global_observability_provider()
    
    if not provider or not provider.config.metrics_enabled:
        return
    
    # Add auto-instrumentation tag
    tags["auto_instrumented"] = "true"
    
    # Record the metric
    if metric_type == "counter":
        provider.metrics.increment_counter(metric_name, value, **tags)
    elif metric_type == "gauge":
        provider.metrics.set_gauge(metric_name, value, **tags)
    elif metric_type == "histogram":
        provider.metrics.record_histogram(metric_name, value, **tags)
    elif metric_type == "timer":
        provider.metrics.record_timer(metric_name, value, **tags)


def auto_log_operation(level: str, message: str, component: str, **kwargs):
    """
    Automatically log an operation if observability is enabled.
    """
    provider = get_global_observability_provider()
    
    if not provider:
        return
    
    # Add auto-instrumentation context
    kwargs["auto_instrumented"] = True
    kwargs["component"] = component
    
    # Log with trace context if available
    provider.log_with_trace_context(level, message, component, **kwargs)


class AutoInstrumentedMixin:
    """
    Mixin class that provides automatic instrumentation capabilities
    to any class that inherits from it.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._component_name = getattr(self, '_component_name', self.__class__.__name__.lower())
    
    def _auto_trace(self, operation_name: str, **tags):
        """Create an auto-traced context manager for this component"""
        full_operation_name = f"{self._component_name}.{operation_name}"
        return auto_trace_operation(full_operation_name, self._component_name, **tags)
    
    async def _auto_trace_async(self, operation_name: str, **tags):
        """Create an auto-traced async context manager for this component"""
        full_operation_name = f"{self._component_name}.{operation_name}"
        return auto_trace_async_operation(full_operation_name, self._component_name, **tags)
    
    def _auto_record_metric(self, metric_name: str, value: float, metric_type: str = "counter", **tags):
        """Record a metric for this component"""
        full_metric_name = f"{self._component_name}.{metric_name}"
        tags["component"] = self._component_name
        auto_record_metric(full_metric_name, value, metric_type, **tags)
    
    def _auto_log(self, level: str, message: str, **kwargs):
        """Log a message for this component"""
        kwargs["component"] = self._component_name
        auto_log_operation(level, message, **kwargs)


def auto_instrument_function(operation_name: Optional[str] = None, component: Optional[str] = None):
    """
    Decorator to automatically instrument a function with tracing and metrics.
    
    Usage:
        @auto_instrument_function("chat_request", "agent")
        async def chat(self, message: str):
            # Function automatically traced and metrics recorded
            return response
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        comp_name = component or "unknown"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                
                async with auto_trace_async_operation(op_name, comp_name) as span:
                    try:
                        # Add function metadata to span
                        if span:
                            span.add_tag("function.name", func.__name__)
                            span.add_tag("function.module", func.__module__)
                            span.add_tag("function.args_count", len(args))
                            span.add_tag("function.kwargs_count", len(kwargs))
                        
                        # Execute function
                        result = await func(*args, **kwargs)
                        
                        # Record success metrics
                        duration = time.time() - start_time
                        auto_record_metric(f"{op_name}.duration_seconds", duration, "histogram", 
                                         component=comp_name, status="success")
                        auto_record_metric(f"{op_name}.calls_total", 1.0, "counter",
                                         component=comp_name, status="success")
                        
                        if span:
                            span.add_tag("success", True)
                            span.add_tag("duration_ms", duration * 1000)
                        
                        return result
                        
                    except Exception as e:
                        # Record error metrics
                        duration = time.time() - start_time
                        auto_record_metric(f"{op_name}.duration_seconds", duration, "histogram",
                                         component=comp_name, status="error")
                        auto_record_metric(f"{op_name}.calls_total", 1.0, "counter",
                                         component=comp_name, status="error")
                        auto_record_metric(f"{op_name}.errors_total", 1.0, "counter",
                                         component=comp_name, error_type=type(e).__name__)
                        
                        if span:
                            span.add_tag("success", False)
                            span.add_tag("error", True)
                            span.add_tag("error.type", type(e).__name__)
                            span.add_tag("error.message", str(e))
                            span.set_status("error")
                        
                        auto_log_operation("error", f"Function {op_name} failed: {e}", component=comp_name,
                                         error_type=type(e).__name__, error_message=str(e))
                        raise
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                
                with auto_trace_operation(op_name, comp_name) as span:
                    try:
                        # Add function metadata to span
                        if span:
                            span.add_tag("function.name", func.__name__)
                            span.add_tag("function.module", func.__module__)
                            span.add_tag("function.args_count", len(args))
                            span.add_tag("function.kwargs_count", len(kwargs))
                        
                        # Execute function
                        result = func(*args, **kwargs)
                        
                        # Record success metrics
                        duration = time.time() - start_time
                        auto_record_metric(f"{op_name}.duration_seconds", duration, "histogram",
                                         component=comp_name, status="success")
                        auto_record_metric(f"{op_name}.calls_total", 1.0, "counter",
                                         component=comp_name, status="success")
                        
                        if span:
                            span.add_tag("success", True)
                            span.add_tag("duration_ms", duration * 1000)
                        
                        return result
                        
                    except Exception as e:
                        # Record error metrics
                        duration = time.time() - start_time
                        auto_record_metric(f"{op_name}.duration_seconds", duration, "histogram",
                                         component=comp_name, status="error")
                        auto_record_metric(f"{op_name}.calls_total", 1.0, "counter",
                                         component=comp_name, status="error")
                        auto_record_metric(f"{op_name}.errors_total", 1.0, "counter",
                                         component=comp_name, error_type=type(e).__name__)
                        
                        if span:
                            span.add_tag("success", False)
                            span.add_tag("error", True)
                            span.add_tag("error.type", type(e).__name__)
                            span.add_tag("error.message", str(e))
                            span.set_status("error")
                        
                        auto_log_operation("error", f"Function {op_name} failed: {e}", component=comp_name,
                                         error_type=type(e).__name__, error_message=str(e))
                        raise
            
            return sync_wrapper
    
    return decorator


def initialize_auto_instrumentation(config: Optional[ObservabilityConfig] = None):
    """
    Initialize automatic instrumentation with the given configuration.
    
    This should be called early in the application lifecycle to enable
    automatic instrumentation for all components.
    """
    if config is None:
        config = ObservabilityConfig()
    
    # Create and set global observability provider
    from .provider import ObservabilityProvider
    provider = ObservabilityProvider(config)
    set_global_observability_provider(provider)
    
    logger.info("Automatic instrumentation initialized")
    return provider


async def start_auto_instrumentation():
    """Start the automatic instrumentation system"""
    provider = get_global_observability_provider()
    if provider:
        await provider.start()
        logger.info("Automatic instrumentation started")


async def stop_auto_instrumentation():
    """Stop the automatic instrumentation system"""
    provider = get_global_observability_provider()
    if provider:
        await provider.stop()
        logger.info("Automatic instrumentation stopped")


# Convenience functions for common instrumentation patterns
def instrument_agent_operation(operation_name: str):
    """Decorator specifically for agent operations"""
    return auto_instrument_function(operation_name, "agent")


def instrument_tool_operation(operation_name: str):
    """Decorator specifically for tool operations"""
    return auto_instrument_function(operation_name, "tool")


def instrument_workflow_operation(operation_name: str):
    """Decorator specifically for workflow operations"""
    return auto_instrument_function(operation_name, "workflow")


def instrument_memory_operation(operation_name: str):
    """Decorator specifically for memory operations"""
    return auto_instrument_function(operation_name, "memory")


def instrument_session_operation(operation_name: str):
    """Decorator specifically for session operations"""
    return auto_instrument_function(operation_name, "session")
