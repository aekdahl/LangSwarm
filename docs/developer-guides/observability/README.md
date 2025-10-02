# LangSwarm V2 Observability Development Guide

**Advanced observability development patterns, custom integrations, and production deployment strategies**

## 🎯 Overview

This guide provides comprehensive information for developers working with LangSwarm V2's observability system. It covers advanced patterns, custom integrations, performance optimization, and production deployment strategies for building robust, monitorable applications.

**Key Areas:**
- **Custom Observability Integration**: Building observability into your components
- **Advanced Patterns**: Sophisticated monitoring and debugging techniques
- **Performance Optimization**: Minimizing observability overhead
- **Production Deployment**: Scalable observability architecture
- **Troubleshooting**: Debugging observability issues
- **External Integrations**: Connecting to monitoring platforms

---

## 🏗️ Custom Component Integration

### **Building Observability-Aware Components**

```python
from langswarm.core.observability import ObservabilityProvider, V2Logger, V2Tracer, V2Metrics
from typing import Optional
import asyncio
import time

class ObservableComponent:
    """Base class for components with built-in observability"""
    
    def __init__(
        self,
        component_name: str,
        observability_provider: Optional[ObservabilityProvider] = None
    ):
        self.component_name = component_name
        self.observability = observability_provider
        
        # Initialize observability components
        if self.observability:
            self.logger = self.observability.get_logger(component_name)
            self.tracer = self.observability.get_tracer(component_name)
            self.metrics = self.observability.get_metrics(component_name)
        else:
            # Provide no-op implementations
            self.logger = NoOpLogger()
            self.tracer = NoOpTracer()
            self.metrics = NoOpMetrics()
    
    async def initialize(self) -> None:
        """Initialize component with observability tracking"""
        with self.tracer.start_span(f"{self.component_name}_initialization") as span:
            start_time = time.time()
            
            try:
                span.set_attribute("component", self.component_name)
                self.logger.info("Component initialization started")
                
                # Perform actual initialization
                await self._initialize_impl()
                
                initialization_time = time.time() - start_time
                
                # Record success metrics
                self.metrics.increment_counter("component_initializations_total",
                                              labels={"component": self.component_name, "status": "success"})
                self.metrics.record_histogram("component_initialization_duration_seconds",
                                            initialization_time,
                                            labels={"component": self.component_name})
                
                span.set_status("OK", "Initialization completed successfully")
                self.logger.info("Component initialization completed",
                               initialization_time=initialization_time)
                
            except Exception as e:
                # Record error metrics
                self.metrics.increment_counter("component_initializations_total",
                                              labels={"component": self.component_name, "status": "error"})
                self.metrics.increment_counter("component_errors_total",
                                              labels={"component": self.component_name, "error_type": type(e).__name__})
                
                span.record_exception(e)
                span.set_status("ERROR", str(e))
                
                self.logger.error("Component initialization failed",
                                error_type=type(e).__name__,
                                error_message=str(e))
                raise
    
    async def _initialize_impl(self) -> None:
        """Override this method for actual initialization logic"""
        pass
    
    def observe_operation(self, operation_name: str):
        """Decorator for automatic operation observability"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                with self.tracer.start_span(f"{self.component_name}_{operation_name}") as span:
                    start_time = time.time()
                    
                    try:
                        span.set_attributes({
                            "component": self.component_name,
                            "operation": operation_name,
                            "args_count": len(args),
                            "kwargs_count": len(kwargs)
                        })
                        
                        self.logger.debug(f"Starting {operation_name}",
                                        operation=operation_name,
                                        args_count=len(args))
                        
                        # Execute operation
                        result = await func(*args, **kwargs)
                        
                        operation_time = time.time() - start_time
                        
                        # Record success metrics
                        self.metrics.increment_counter("component_operations_total",
                                                      labels={"component": self.component_name,
                                                             "operation": operation_name,
                                                             "status": "success"})
                        self.metrics.record_histogram("component_operation_duration_seconds",
                                                    operation_time,
                                                    labels={"component": self.component_name,
                                                           "operation": operation_name})
                        
                        span.set_status("OK", f"{operation_name} completed successfully")
                        self.logger.debug(f"Completed {operation_name}",
                                        operation=operation_name,
                                        duration=operation_time,
                                        result_type=type(result).__name__)
                        
                        return result
                        
                    except Exception as e:
                        operation_time = time.time() - start_time
                        
                        # Record error metrics
                        self.metrics.increment_counter("component_operations_total",
                                                      labels={"component": self.component_name,
                                                             "operation": operation_name,
                                                             "status": "error"})
                        self.metrics.increment_counter("component_errors_total",
                                                      labels={"component": self.component_name,
                                                             "operation": operation_name,
                                                             "error_type": type(e).__name__})
                        
                        span.record_exception(e)
                        span.set_status("ERROR", str(e))
                        
                        self.logger.error(f"Failed {operation_name}",
                                        operation=operation_name,
                                        duration=operation_time,
                                        error_type=type(e).__name__,
                                        error_message=str(e))
                        raise
            
            return wrapper
        return decorator

# Example usage
class CustomDataProcessor(ObservableComponent):
    """Custom component with built-in observability"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        super().__init__("data_processor", observability_provider)
        self.processed_count = 0
    
    async def _initialize_impl(self) -> None:
        """Initialize data processor"""
        # Simulate initialization work
        await asyncio.sleep(0.1)
        self.logger.info("Data processor initialized")
    
    @property
    def observe_operation(self):
        return super().observe_operation
    
    @observe_operation("process_data")
    async def process_data(self, data: dict) -> dict:
        """Process data with automatic observability"""
        self.processed_count += 1
        
        # Simulate data processing
        processed_data = {
            "original": data,
            "processed_at": time.time(),
            "processed_count": self.processed_count
        }
        
        # Update gauge metric
        self.metrics.set_gauge("processed_items_count", self.processed_count)
        
        return processed_data
    
    @observe_operation("batch_process")
    async def batch_process(self, data_batch: list) -> list:
        """Batch process data with detailed observability"""
        results = []
        
        # Add batch-specific span attributes
        with self.tracer.get_current_span() as span:
            span.set_attribute("batch_size", len(data_batch))
        
        for i, data_item in enumerate(data_batch):
            # Create nested span for each item
            with self.tracer.start_span(f"process_item_{i}") as item_span:
                item_span.set_attribute("item_index", i)
                item_span.set_attribute("item_size", len(str(data_item)))
                
                result = await self.process_data(data_item)
                results.append(result)
        
        return results
```

### **Custom Observability Integration**

```python
class CustomObservabilityIntegration:
    """Custom integration for specific component types"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        self.observability = observability_provider
        self.logger = observability_provider.get_logger("custom_integration")
        self.tracer = observability_provider.get_tracer("custom_integration")
        self.metrics = observability_provider.get_metrics("custom_integration")
        
        # Custom metrics
        self.setup_custom_metrics()
    
    def setup_custom_metrics(self):
        """Set up component-specific metrics"""
        self.request_counter = self.metrics.create_counter(
            "custom_requests_total",
            description="Total custom requests processed"
        )
        
        self.processing_time_histogram = self.metrics.create_histogram(
            "custom_processing_duration_seconds",
            description="Custom processing duration",
            buckets=[0.001, 0.01, 0.1, 1.0, 5.0, 10.0]
        )
        
        self.active_connections_gauge = self.metrics.create_gauge(
            "custom_active_connections",
            description="Number of active connections"
        )
    
    async def trace_custom_operation(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ):
        """Trace custom operation with comprehensive observability"""
        
        with self.tracer.start_span(f"custom_{operation_name}") as span:
            correlation_id = kwargs.get("correlation_id", f"custom_{int(time.time())}")
            
            span.set_attributes({
                "operation": operation_name,
                "correlation_id": correlation_id,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            })
            
            # Start operation logging
            self.logger.info(f"Starting custom operation: {operation_name}",
                           correlation_id=correlation_id,
                           operation=operation_name)
            
            start_time = time.time()
            
            try:
                # Execute operation with monitoring
                with self.processing_time_histogram.timer(labels={"operation": operation_name}):
                    result = await operation_func(*args, **kwargs)
                
                operation_time = time.time() - start_time
                
                # Record success
                self.request_counter.increment(labels={
                    "operation": operation_name,
                    "status": "success"
                })
                
                span.set_attributes({
                    "operation_time": operation_time,
                    "result_type": type(result).__name__,
                    "success": True
                })
                
                span.set_status("OK", f"Operation {operation_name} completed")
                
                self.logger.info(f"Custom operation completed: {operation_name}",
                               correlation_id=correlation_id,
                               operation=operation_name,
                               duration=operation_time,
                               success=True)
                
                return result
                
            except Exception as e:
                operation_time = time.time() - start_time
                
                # Record error
                self.request_counter.increment(labels={
                    "operation": operation_name,
                    "status": "error"
                })
                
                span.record_exception(e)
                span.set_status("ERROR", str(e))
                span.set_attributes({
                    "operation_time": operation_time,
                    "error_type": type(e).__name__,
                    "success": False
                })
                
                self.logger.error(f"Custom operation failed: {operation_name}",
                                correlation_id=correlation_id,
                                operation=operation_name,
                                duration=operation_time,
                                error_type=type(e).__name__,
                                error_message=str(e))
                
                raise
    
    def monitor_resource_usage(self):
        """Monitor custom resource usage"""
        import psutil
        
        # Monitor system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        self.metrics.set_gauge("system_cpu_percent", cpu_percent)
        self.metrics.set_gauge("system_memory_percent", memory_percent)
        
        # Log resource usage if high
        if cpu_percent > 80:
            self.logger.warning("High CPU usage detected",
                              cpu_percent=cpu_percent)
        
        if memory_percent > 80:
            self.logger.warning("High memory usage detected",
                              memory_percent=memory_percent)
    
    def create_custom_middleware(self):
        """Create observability middleware for custom frameworks"""
        
        def observability_middleware(request, response, next_handler):
            """Middleware for automatic request observability"""
            
            correlation_id = request.headers.get("x-correlation-id", f"req_{int(time.time())}")
            
            with self.tracer.start_span("custom_request") as span:
                span.set_attributes({
                    "http_method": request.method,
                    "http_path": request.path,
                    "correlation_id": correlation_id,
                    "user_agent": request.headers.get("user-agent", "unknown")
                })
                
                start_time = time.time()
                
                self.logger.info("Request started",
                               correlation_id=correlation_id,
                               method=request.method,
                               path=request.path)
                
                try:
                    # Process request
                    result = next_handler(request, response)
                    
                    request_time = time.time() - start_time
                    
                    # Record metrics
                    self.metrics.increment_counter("http_requests_total",
                                                  labels={
                                                      "method": request.method,
                                                      "status": str(response.status_code)
                                                  })
                    
                    self.metrics.record_histogram("http_request_duration_seconds",
                                                request_time,
                                                labels={
                                                    "method": request.method,
                                                    "path": request.path
                                                })
                    
                    span.set_attributes({
                        "http_status_code": response.status_code,
                        "request_time": request_time
                    })
                    
                    self.logger.info("Request completed",
                                   correlation_id=correlation_id,
                                   status_code=response.status_code,
                                   duration=request_time)
                    
                    return result
                    
                except Exception as e:
                    request_time = time.time() - start_time
                    
                    span.record_exception(e)
                    span.set_status("ERROR", str(e))
                    
                    self.logger.error("Request failed",
                                    correlation_id=correlation_id,
                                    error_type=type(e).__name__,
                                    error_message=str(e),
                                    duration=request_time)
                    
                    raise
        
        return observability_middleware
```

---

## 🎯 Advanced Observability Patterns

### **Distributed Context Propagation**

```python
import contextvars
from typing import Dict, Any

# Context variables for distributed tracing
current_trace_context = contextvars.ContextVar('trace_context', default=None)
current_correlation_id = contextvars.ContextVar('correlation_id', default=None)

class DistributedObservability:
    """Advanced distributed observability patterns"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        self.observability = observability_provider
        self.logger = observability_provider.get_logger("distributed")
        self.tracer = observability_provider.get_tracer("distributed")
        self.metrics = observability_provider.get_metrics("distributed")
    
    async def propagate_context(self, operation_func, context: Dict[str, Any] = None):
        """Propagate observability context across async operations"""
        
        # Get or create correlation ID
        correlation_id = context.get("correlation_id") if context else None
        if not correlation_id:
            correlation_id = current_correlation_id.get() or f"dist_{int(time.time())}"
        
        # Set context variables
        current_correlation_id.set(correlation_id)
        
        # Create distributed span
        with self.tracer.start_span("distributed_operation") as span:
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("distributed", True)
            
            # Set trace context
            trace_context = {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "correlation_id": correlation_id
            }
            current_trace_context.set(trace_context)
            
            self.logger.info("Distributed operation started",
                           correlation_id=correlation_id,
                           trace_id=span.trace_id)
            
            try:
                result = await operation_func()
                
                self.logger.info("Distributed operation completed",
                               correlation_id=correlation_id,
                               trace_id=span.trace_id)
                
                return result
                
            except Exception as e:
                self.logger.error("Distributed operation failed",
                                correlation_id=correlation_id,
                                trace_id=span.trace_id,
                                error_type=type(e).__name__)
                raise
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current distributed context"""
        return {
            "trace_context": current_trace_context.get(),
            "correlation_id": current_correlation_id.get()
        }
    
    async def cross_service_call(self, service_name: str, operation: str, payload: Dict[str, Any]):
        """Make cross-service call with context propagation"""
        
        # Get current context
        context = self.get_current_context()
        correlation_id = context.get("correlation_id")
        
        with self.tracer.start_span(f"cross_service_{service_name}_{operation}") as span:
            span.set_attributes({
                "service_name": service_name,
                "operation": operation,
                "correlation_id": correlation_id,
                "call_type": "cross_service"
            })
            
            # Add context to payload
            enriched_payload = {
                **payload,
                "_observability_context": context
            }
            
            self.logger.info("Cross-service call started",
                           service_name=service_name,
                           operation=operation,
                           correlation_id=correlation_id)
            
            try:
                # Simulate service call (replace with actual HTTP/gRPC call)
                result = await self._simulate_service_call(service_name, operation, enriched_payload)
                
                span.set_attribute("call_success", True)
                
                self.metrics.increment_counter("cross_service_calls_total",
                                              labels={
                                                  "service": service_name,
                                                  "operation": operation,
                                                  "status": "success"
                                              })
                
                self.logger.info("Cross-service call completed",
                               service_name=service_name,
                               operation=operation,
                               correlation_id=correlation_id)
                
                return result
                
            except Exception as e:
                span.set_attribute("call_success", False)
                span.record_exception(e)
                
                self.metrics.increment_counter("cross_service_calls_total",
                                              labels={
                                                  "service": service_name,
                                                  "operation": operation,
                                                  "status": "error"
                                              })
                
                self.logger.error("Cross-service call failed",
                                service_name=service_name,
                                operation=operation,
                                correlation_id=correlation_id,
                                error_type=type(e).__name__)
                raise
    
    async def _simulate_service_call(self, service_name: str, operation: str, payload: Dict[str, Any]):
        """Simulate external service call"""
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"status": "success", "data": f"Response from {service_name}"}

### **Performance Profiling Integration**

```python
import cProfile
import pstats
from io import StringIO

class PerformanceProfiler:
    """Advanced performance profiling with observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        self.observability = observability_provider
        self.logger = observability_provider.get_logger("profiler")
        self.tracer = observability_provider.get_tracer("profiler")
        self.metrics = observability_provider.get_metrics("profiler")
    
    def profile_operation(self, operation_name: str, detailed: bool = False):
        """Decorator for performance profiling with observability"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                with self.tracer.start_span(f"profiled_{operation_name}") as span:
                    
                    # Set up profiling
                    profiler = cProfile.Profile()
                    
                    self.logger.info(f"Starting profiled operation: {operation_name}",
                                   operation=operation_name,
                                   profiling_enabled=True)
                    
                    try:
                        # Start profiling
                        profiler.enable()
                        start_time = time.time()
                        
                        # Execute function
                        result = await func(*args, **kwargs)
                        
                        # Stop profiling
                        end_time = time.time()
                        profiler.disable()
                        
                        execution_time = end_time - start_time
                        
                        # Analyze profiling results
                        if detailed:
                            profile_stats = self._analyze_profile(profiler)
                            span.set_attributes(profile_stats)
                            
                            self.logger.info(f"Profiled operation completed: {operation_name}",
                                           operation=operation_name,
                                           execution_time=execution_time,
                                           **profile_stats)
                        else:
                            self.logger.info(f"Profiled operation completed: {operation_name}",
                                           operation=operation_name,
                                           execution_time=execution_time)
                        
                        # Record performance metrics
                        self.metrics.record_histogram("profiled_operation_duration_seconds",
                                                    execution_time,
                                                    labels={"operation": operation_name})
                        
                        span.set_attributes({
                            "execution_time": execution_time,
                            "profiling_enabled": True
                        })
                        
                        return result
                        
                    except Exception as e:
                        profiler.disable()
                        
                        self.logger.error(f"Profiled operation failed: {operation_name}",
                                        operation=operation_name,
                                        error_type=type(e).__name__)
                        
                        span.record_exception(e)
                        raise
            
            return wrapper
        return decorator
    
    def _analyze_profile(self, profiler: cProfile.Profile) -> Dict[str, Any]:
        """Analyze profiling results"""
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        
        # Get top functions by cumulative time
        stats = ps.get_stats_profile()
        
        total_calls = stats.total_calls
        total_time = stats.total_tt
        
        # Find most time-consuming functions
        top_functions = []
        for func_info, (cc, nc, tt, ct, callers) in stats.stats.items():
            if ct > 0.001:  # Only include functions taking > 1ms
                top_functions.append({
                    "function": f"{func_info[0]}:{func_info[1]}({func_info[2]})",
                    "cumulative_time": ct,
                    "total_time": tt,
                    "call_count": cc
                })
        
        # Sort by cumulative time
        top_functions.sort(key=lambda x: x["cumulative_time"], reverse=True)
        
        return {
            "total_calls": total_calls,
            "total_time": total_time,
            "top_function": top_functions[0]["function"] if top_functions else "none",
            "top_function_time": top_functions[0]["cumulative_time"] if top_functions else 0,
            "functions_analyzed": len(top_functions)
        }

### **Custom Alerting Integration**

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Callable, Optional

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    severity: AlertSeverity
    title: str
    description: str
    component: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: float
    correlation_id: Optional[str] = None

class AlertManager:
    """Custom alerting system integrated with observability"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        self.observability = observability_provider
        self.logger = observability_provider.get_logger("alerts")
        self.metrics = observability_provider.get_metrics("alerts")
        
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.thresholds = {}
        
        # Alert metrics
        self.alerts_counter = self.metrics.create_counter(
            "alerts_generated_total",
            description="Total alerts generated"
        )
    
    def add_threshold(
        self,
        metric_name: str,
        threshold: float,
        severity: AlertSeverity,
        comparison: str = "greater"  # greater, less, equal
    ):
        """Add alerting threshold for a metric"""
        self.thresholds[metric_name] = {
            "threshold": threshold,
            "severity": severity,
            "comparison": comparison
        }
        
        self.logger.info("Alert threshold configured",
                        metric_name=metric_name,
                        threshold=threshold,
                        severity=severity.value)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
    
    async def check_metrics_and_alert(self):
        """Check metrics against thresholds and generate alerts"""
        
        # Export current metrics
        current_metrics = await self.observability.get_metrics().export_metrics()
        
        for metric_name, threshold_config in self.thresholds.items():
            if metric_name in current_metrics:
                current_value = current_metrics[metric_name]["value"]
                threshold = threshold_config["threshold"]
                comparison = threshold_config["comparison"]
                severity = threshold_config["severity"]
                
                # Check threshold
                alert_triggered = False
                
                if comparison == "greater" and current_value > threshold:
                    alert_triggered = True
                elif comparison == "less" and current_value < threshold:
                    alert_triggered = True
                elif comparison == "equal" and current_value == threshold:
                    alert_triggered = True
                
                if alert_triggered:
                    alert = Alert(
                        severity=severity,
                        title=f"Metric threshold exceeded: {metric_name}",
                        description=f"Metric {metric_name} value {current_value} exceeds threshold {threshold}",
                        component="alerting",
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold=threshold,
                        timestamp=time.time()
                    )
                    
                    await self._fire_alert(alert)
    
    async def _fire_alert(self, alert: Alert):
        """Fire alert to all handlers"""
        
        # Log alert
        self.logger.log(
            alert.severity.value.upper(),
            f"ALERT: {alert.title}",
            alert_severity=alert.severity.value,
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold=alert.threshold,
            component=alert.component
        )
        
        # Record alert metric
        self.alerts_counter.increment(labels={
            "severity": alert.severity.value,
            "metric": alert.metric_name,
            "component": alert.component
        })
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error("Alert handler failed",
                                error_type=type(e).__name__,
                                error_message=str(e))

# Example alert handlers
def slack_alert_handler(alert: Alert):
    """Send alert to Slack (example implementation)"""
    # Implementation would send to Slack webhook
    print(f"Slack Alert: {alert.title} - {alert.description}")

def email_alert_handler(alert: Alert):
    """Send alert via email (example implementation)"""
    # Implementation would send email
    print(f"Email Alert: {alert.title} - {alert.description}")
```

---

## 🚀 Production Deployment Patterns

### **Scalable Observability Architecture**

```python
class ProductionObservabilitySetup:
    """Production-ready observability setup with external integrations"""
    
    @classmethod
    def create_production_observability(
        cls,
        service_name: str,
        service_version: str,
        environment: str = "production"
    ) -> ObservabilityProvider:
        """Create production observability configuration"""
        
        config = {
            "logging": {
                "level": "INFO",
                "output": "file",
                "file_path": f"/var/log/langswarm/{service_name}.log",
                "format": "json",
                "rotation": {
                    "max_size": "100MB",
                    "backup_count": 10
                },
                "correlation": True
            },
            "tracing": {
                "enabled": True,
                "sampling_rate": 0.1,  # 10% sampling for production
                "exporter": "otlp",
                "endpoint": os.getenv("TRACING_ENDPOINT", "http://jaeger:14268/api/traces"),
                "span_processor": "batch",
                "max_export_batch_size": 512,
                "export_timeout_millis": 30000
            },
            "metrics": {
                "enabled": True,
                "export_interval": 60,
                "prometheus_endpoint": "/metrics",
                "include_histograms": True,
                "exclude_labels": ["user_id", "session_id"],  # Privacy
                "custom_buckets": {
                    "request_duration": [0.001, 0.01, 0.1, 1.0, 5.0, 10.0, 30.0],
                    "response_size": [100, 1000, 10000, 100000, 1000000]
                }
            },
            "integrations": {
                "all_components": True,
                "detailed_spans": False,  # Reduce overhead
                "parameter_logging": False  # Privacy and performance
            },
            "performance": {
                "max_spans_per_trace": 100,
                "max_attributes_per_span": 20,
                "span_timeout_seconds": 300,
                "max_log_entry_size": 32768  # 32KB
            }
        }
        
        return ObservabilityProvider.create(config, service_name)
    
    @classmethod
    def setup_kubernetes_observability(cls, namespace: str, service_name: str):
        """Set up observability for Kubernetes deployment"""
        
        # Kubernetes-specific configuration
        k8s_config = {
            "logging": {
                "output": "console",  # Let Kubernetes handle log collection
                "format": "json",
                "include_kubernetes_metadata": True
            },
            "tracing": {
                "exporter": "otlp",
                "endpoint": f"http://jaeger-collector.{namespace}.svc.cluster.local:14268/api/traces"
            },
            "metrics": {
                "prometheus_endpoint": "/metrics",
                "kubernetes_labels": {
                    "namespace": namespace,
                    "service": service_name,
                    "version": os.getenv("APP_VERSION", "unknown")
                }
            }
        }
        
        return ObservabilityProvider.create(k8s_config, service_name)
    
    @classmethod
    def setup_cloud_observability(cls, cloud_provider: str, service_name: str):
        """Set up cloud-specific observability"""
        
        if cloud_provider == "aws":
            return cls._setup_aws_observability(service_name)
        elif cloud_provider == "gcp":
            return cls._setup_gcp_observability(service_name)
        elif cloud_provider == "azure":
            return cls._setup_azure_observability(service_name)
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
    
    @classmethod
    def _setup_aws_observability(cls, service_name: str):
        """AWS-specific observability setup"""
        config = {
            "logging": {
                "output": "cloudwatch",
                "cloudwatch_log_group": f"/aws/langswarm/{service_name}",
                "format": "json"
            },
            "tracing": {
                "exporter": "xray",
                "aws_region": os.getenv("AWS_REGION", "us-east-1")
            },
            "metrics": {
                "exporter": "cloudwatch",
                "namespace": f"LangSwarm/{service_name}"
            }
        }
        return ObservabilityProvider.create(config, service_name)
    
    @classmethod
    def _setup_gcp_observability(cls, service_name: str):
        """GCP-specific observability setup"""
        config = {
            "logging": {
                "output": "stackdriver",
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "format": "json"
            },
            "tracing": {
                "exporter": "cloud_trace",
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT")
            },
            "metrics": {
                "exporter": "monitoring",
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT")
            }
        }
        return ObservabilityProvider.create(config, service_name)
    
    @classmethod 
    def _setup_azure_observability(cls, service_name: str):
        """Azure-specific observability setup"""
        config = {
            "logging": {
                "output": "application_insights",
                "instrumentation_key": os.getenv("AZURE_INSTRUMENTATION_KEY"),
                "format": "json"
            },
            "tracing": {
                "exporter": "application_insights",
                "instrumentation_key": os.getenv("AZURE_INSTRUMENTATION_KEY")
            },
            "metrics": {
                "exporter": "application_insights",
                "instrumentation_key": os.getenv("AZURE_INSTRUMENTATION_KEY")
            }
        }
        return ObservabilityProvider.create(config, service_name)

### **Health Check Integration**

```python
from typing import Dict, List

class HealthCheckManager:
    """Comprehensive health checking with observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        self.observability = observability_provider
        self.logger = observability_provider.get_logger("health")
        self.metrics = observability_provider.get_metrics("health")
        
        self.health_checks: Dict[str, Callable] = {}
        
        # Health metrics
        self.health_status_gauge = self.metrics.create_gauge(
            "health_check_status",
            description="Health check status (1=healthy, 0=unhealthy)"
        )
        
        self.health_check_duration = self.metrics.create_histogram(
            "health_check_duration_seconds",
            description="Health check execution duration"
        )
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
        self.logger.info(f"Health check registered: {name}")
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return status"""
        
        overall_healthy = True
        results = {}
        
        with self.tracer.start_span("health_checks") as span:
            span.set_attribute("check_count", len(self.health_checks))
            
            for check_name, check_func in self.health_checks.items():
                with self.tracer.start_span(f"health_check_{check_name}") as check_span:
                    start_time = time.time()
                    
                    try:
                        # Run health check
                        check_result = await check_func()
                        
                        duration = time.time() - start_time
                        is_healthy = check_result.get("healthy", False)
                        
                        # Record metrics
                        self.health_status_gauge.set(
                            1 if is_healthy else 0,
                            labels={"check": check_name}
                        )
                        
                        self.health_check_duration.observe(
                            duration,
                            labels={"check": check_name}
                        )
                        
                        # Update overall status
                        if not is_healthy:
                            overall_healthy = False
                        
                        results[check_name] = {
                            "healthy": is_healthy,
                            "duration": duration,
                            "details": check_result.get("details", {}),
                            "message": check_result.get("message", "")
                        }
                        
                        check_span.set_attributes({
                            "healthy": is_healthy,
                            "duration": duration
                        })
                        
                        self.logger.debug(f"Health check completed: {check_name}",
                                        check_name=check_name,
                                        healthy=is_healthy,
                                        duration=duration)
                        
                    except Exception as e:
                        duration = time.time() - start_time
                        overall_healthy = False
                        
                        # Record error metrics
                        self.health_status_gauge.set(0, labels={"check": check_name})
                        
                        results[check_name] = {
                            "healthy": False,
                            "duration": duration,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                        
                        check_span.record_exception(e)
                        check_span.set_status("ERROR", str(e))
                        
                        self.logger.error(f"Health check failed: {check_name}",
                                        check_name=check_name,
                                        error_type=type(e).__name__,
                                        error_message=str(e))
            
            # Record overall health status
            self.health_status_gauge.set(
                1 if overall_healthy else 0,
                labels={"check": "overall"}
            )
            
            span.set_attribute("overall_healthy", overall_healthy)
        
        return {
            "healthy": overall_healthy,
            "checks": results,
            "timestamp": time.time()
        }

# Example health check functions
async def database_health_check():
    """Example database health check"""
    try:
        # Simulate database check
        await asyncio.sleep(0.01)
        return {
            "healthy": True,
            "message": "Database connection successful",
            "details": {"connection_pool_size": 10}
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Database connection failed: {e}",
            "details": {"error": str(e)}
        }

async def external_service_health_check():
    """Example external service health check"""
    try:
        # Simulate external service check
        await asyncio.sleep(0.05)
        return {
            "healthy": True,
            "message": "External service accessible",
            "details": {"response_time_ms": 50}
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"External service unavailable: {e}",
            "details": {"error": str(e)}
        }
```

---

## 🔧 Troubleshooting and Debugging

### **Common Issues and Solutions**

**Issue: High Observability Overhead**
```python
# Solution: Optimize sampling and filtering
config = {
    "tracing": {
        "sampling_rate": 0.01,  # Reduce to 1%
        "adaptive_sampling": True
    },
    "logging": {
        "level": "WARNING",  # Reduce log volume
        "exclude_components": ["debug_component"]
    },
    "metrics": {
        "exclude_labels": ["high_cardinality_label"]
    }
}
```

**Issue: Missing Trace Context**
```python
# Solution: Ensure proper context propagation
def ensure_trace_context(func):
    async def wrapper(*args, **kwargs):
        # Get current context
        context = current_trace_context.get()
        if not context:
            # Create new context if missing
            correlation_id = f"missing_ctx_{int(time.time())}"
            current_correlation_id.set(correlation_id)
        
        return await func(*args, **kwargs)
    return wrapper
```

**Issue: Metrics Memory Leak**
```python
# Solution: Regular metrics cleanup
class MetricsCleanup:
    def __init__(self, metrics: V2Metrics):
        self.metrics = metrics
        
    async def cleanup_old_metrics(self, max_age_hours: int = 24):
        """Clean up old metric data"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        await self.metrics.cleanup_old_data(cutoff_time)
```

---

**LangSwarm V2's observability development guide provides comprehensive patterns for building production-ready, observable applications with minimal performance overhead and maximum debugging capabilities.**
