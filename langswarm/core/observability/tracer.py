"""
LangSwarm V2 Distributed Tracer

Production-ready distributed tracing implementation with support for
span hierarchy, context propagation, and integration with logging.
"""

import asyncio
import functools
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional, Any, Callable, ContextManager, List
import uuid

from .interfaces import ITracer, TraceSpan, SpanStatus, ObservabilityConfig


class V2Tracer(ITracer):
    """
    Distributed tracer implementation for V2 observability system.
    
    Provides distributed tracing with span hierarchy, context propagation,
    and integration with logging for comprehensive request tracking.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize V2 tracer.
        
        Args:
            config: Observability configuration
        """
        self.config = config
        self._active_spans: Dict[str, TraceSpan] = {}
        self._span_stack: threading.local = threading.local()
        self._completed_spans: Dict[str, TraceSpan] = {}
        
        # Sampling configuration
        self._sampling_rate = config.trace_sampling_rate
        
        # Initialize span stack for current thread
        self._get_span_stack()
    
    def _get_span_stack(self) -> list:
        """Get span stack for current thread"""
        if not hasattr(self._span_stack, 'spans'):
            self._span_stack.spans = []
        return self._span_stack.spans
    
    def _should_sample(self) -> bool:
        """Determine if trace should be sampled"""
        if self._sampling_rate >= 1.0:
            return True
        if self._sampling_rate <= 0.0:
            return False
        
        import random
        return random.random() < self._sampling_rate
    
    @contextmanager
    def start_span(self, operation_name: str, parent_span_id: Optional[str] = None,
                   **tags) -> ContextManager[TraceSpan]:
        """Start a new trace span"""
        if not self.config.tracing_enabled or not self._should_sample():
            # Return no-op context manager
            yield None
            return
        
        # Get parent span info
        span_stack = self._get_span_stack()
        
        if parent_span_id is None and span_stack:
            parent_span = span_stack[-1]
            parent_span_id = parent_span.span_id
            trace_id = parent_span.trace_id
        else:
            trace_id = str(uuid.uuid4())
        
        # Create new span
        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            parent_span_id=parent_span_id,
            status=SpanStatus.OK,
            tags=tags
        )
        
        # Add to active spans and stack
        self._active_spans[span.span_id] = span
        span_stack.append(span)
        
        try:
            yield span
        except Exception as e:
            # Mark span as error
            span.status = SpanStatus.ERROR
            span.tags['error'] = True
            span.tags['error.message'] = str(e)
            span.tags['error.type'] = type(e).__name__
            raise
        finally:
            # Complete span
            span.end_time = datetime.utcnow()
            
            # Remove from active spans and stack
            if span.span_id in self._active_spans:
                del self._active_spans[span.span_id]
            
            if span_stack and span_stack[-1].span_id == span.span_id:
                span_stack.pop()
            
            # Store completed span
            self._completed_spans[span.span_id] = span
            
            # Export span if configured
            self._export_span(span)
    
    def get_current_span(self) -> Optional[TraceSpan]:
        """Get the current active span"""
        span_stack = self._get_span_stack()
        return span_stack[-1] if span_stack else None
    
    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID"""
        current_span = self.get_current_span()
        return current_span.trace_id if current_span else None
    
    def add_span_tag(self, key: str, value: Any):
        """Add tag to current span"""
        current_span = self.get_current_span()
        if current_span:
            current_span.tags[key] = value
    
    def add_span_log(self, message: str, **kwargs):
        """Add log entry to current span"""
        current_span = self.get_current_span()
        if current_span:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                **kwargs
            }
            current_span.logs.append(log_entry)
    
    def _export_span(self, span: TraceSpan):
        """Export completed span to external system"""
        if not self.config.trace_export_url:
            return
        
        # In a real implementation, this would export to a tracing backend
        # like Jaeger, Zipkin, or OpenTelemetry collector
        pass
    
    def get_span_by_id(self, span_id: str) -> Optional[TraceSpan]:
        """Get span by ID (active or completed)"""
        return self._active_spans.get(span_id) or self._completed_spans.get(span_id)
    
    def get_spans_by_trace_id(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace ID"""
        spans = []
        
        # Check active spans
        for span in self._active_spans.values():
            if span.trace_id == trace_id:
                spans.append(span)
        
        # Check completed spans
        for span in self._completed_spans.values():
            if span.trace_id == trace_id:
                spans.append(span)
        
        # Sort by start time
        spans.sort(key=lambda s: s.start_time)
        return spans
    
    def clear_completed_spans(self):
        """Clear completed spans to free memory"""
        self._completed_spans.clear()


# Decorator functions for automatic tracing
def trace_function(operation_name: Optional[str] = None, **span_tags):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get global tracer
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)
            
            # Add function info to tags
            tags = {
                'function.name': func.__name__,
                'function.module': func.__module__,
                **span_tags
            }
            
            with tracer.start_span(op_name, **tags) as span:
                if span:
                    # Add argument info (be careful with sensitive data)
                    span.tags['function.args_count'] = len(args)
                    span.tags['function.kwargs_count'] = len(kwargs)
                
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_async_function(operation_name: Optional[str] = None, **span_tags):
    """Decorator to trace async function execution"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get global tracer
            tracer = get_tracer()
            if not tracer:
                return await func(*args, **kwargs)
            
            # Add function info to tags
            tags = {
                'function.name': func.__name__,
                'function.module': func.__module__,
                'function.async': True,
                **span_tags
            }
            
            with tracer.start_span(op_name, **tags) as span:
                if span:
                    # Add argument info (be careful with sensitive data)
                    span.tags['function.args_count'] = len(args)
                    span.tags['function.kwargs_count'] = len(kwargs)
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global tracer registry
_tracers: Dict[str, V2Tracer] = {}
_default_config: Optional[ObservabilityConfig] = None


def configure_tracing(config: ObservabilityConfig):
    """Configure global tracing settings"""
    global _default_config
    _default_config = config


def create_tracer(name: str = "default", config: Optional[ObservabilityConfig] = None) -> V2Tracer:
    """Create a named tracer instance"""
    if config is None:
        config = _default_config or ObservabilityConfig()
    
    tracer = V2Tracer(config)
    _tracers[name] = tracer
    return tracer


def get_tracer(name: str = "default") -> Optional[V2Tracer]:
    """Get existing tracer by name"""
    return _tracers.get(name)


def get_or_create_tracer(name: str = "default", 
                        config: Optional[ObservabilityConfig] = None) -> V2Tracer:
    """Get existing tracer or create new one"""
    tracer = get_tracer(name)
    if tracer is None:
        tracer = create_tracer(name, config)
    return tracer


# Convenience functions for default tracer
def start_span(operation_name: str, **tags) -> ContextManager[TraceSpan]:
    """Start span with default tracer"""
    tracer = get_or_create_tracer()
    return tracer.start_span(operation_name, **tags)


def get_current_span() -> Optional[TraceSpan]:
    """Get current span from default tracer"""
    tracer = get_tracer()
    return tracer.get_current_span() if tracer else None


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from default tracer"""
    tracer = get_tracer()
    return tracer.get_trace_id() if tracer else None


def add_span_tag(key: str, value: Any):
    """Add tag to current span in default tracer"""
    tracer = get_tracer()
    if tracer:
        tracer.add_span_tag(key, value)


def add_span_log(message: str, **kwargs):
    """Add log to current span in default tracer"""
    tracer = get_tracer()
    if tracer:
        tracer.add_span_log(message, **kwargs)
