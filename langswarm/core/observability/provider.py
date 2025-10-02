"""
LangSwarm V2 Observability Provider

Unified observability provider that integrates logging, tracing, and metrics
into a single, cohesive system for production-ready monitoring and debugging.
"""

import asyncio
import logging
from typing import Dict, Optional, Any

from .interfaces import IObservabilityProvider, ObservabilityConfig, LogLevel
from .logger import V2Logger, configure_logging
from .tracer import V2Tracer, configure_tracing  
from .metrics import V2Metrics, configure_metrics
from .opentelemetry_exporter import OpenTelemetryConfig, OpenTelemetryIntegration


class ObservabilityProvider(IObservabilityProvider):
    """
    Unified observability provider for V2 system.
    
    Integrates logging, tracing, and metrics with cross-component
    correlation and unified configuration management.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize observability provider.
        
        Args:
            config: Observability configuration
        """
        self.config = config
        self._logger = V2Logger(config)
        self._tracer = V2Tracer(config)
        self._metrics = V2Metrics(config)
        self._started = False
        
        # Initialize OpenTelemetry integration if enabled
        self._otel_integration = None
        if config.opentelemetry_enabled:
            otel_config = self._create_otel_config(config)
            self._otel_integration = OpenTelemetryIntegration(self, otel_config)
        
        # Configure correlation between components
        self._setup_correlation()
    
    def _create_otel_config(self, config: ObservabilityConfig) -> OpenTelemetryConfig:
        """Create OpenTelemetry configuration from observability config"""
        return OpenTelemetryConfig(
            enabled=config.opentelemetry_enabled,
            service_name=config.opentelemetry_service_name,
            service_version=config.opentelemetry_service_version,
            otlp_endpoint=config.opentelemetry_otlp_endpoint,
            otlp_headers=config.opentelemetry_otlp_headers,
            jaeger_endpoint=config.opentelemetry_jaeger_endpoint,
            prometheus_enabled=config.opentelemetry_prometheus_enabled,
            prometheus_port=config.opentelemetry_prometheus_port,
        )
    
    def _setup_correlation(self):
        """Set up correlation between logging, tracing, and metrics"""
        # The logger will get trace context from the tracer for correlation
        pass
    
    @property
    def logger(self) -> V2Logger:
        """Get logger instance"""
        return self._logger
    
    @property
    def tracer(self) -> V2Tracer:
        """Get tracer instance"""
        return self._tracer
    
    @property
    def metrics(self) -> V2Metrics:
        """Get metrics instance"""
        return self._metrics
    
    async def start(self):
        """Start observability provider"""
        if self._started:
            return
        
        try:
            # Configure global settings
            configure_logging(self.config)
            configure_tracing(self.config)
            configure_metrics(self.config)
            
            # Start OpenTelemetry integration if enabled
            if self._otel_integration:
                await self._otel_integration.start()
            
            self._started = True
            
            # Log startup
            self._logger.info("Observability provider started", 
                            component="observability",
                            operation="start",
                            config_enabled=self.config.enabled,
                            tracing_enabled=self.config.tracing_enabled,
                            metrics_enabled=self.config.metrics_enabled,
                            opentelemetry_enabled=self.config.opentelemetry_enabled)
            
            # Record startup metric
            self._metrics.increment_counter("observability.provider.started")
            
        except Exception as e:
            logging.error(f"Failed to start observability provider: {e}")
            raise
    
    async def stop(self):
        """Stop observability provider"""
        if not self._started:
            return
        
        try:
            # Log shutdown
            self._logger.info("Observability provider stopping", 
                            component="observability",
                            operation="stop")
            
            # Record shutdown metric
            self._metrics.increment_counter("observability.provider.stopped")
            
            # Flush all pending data
            await self.flush()
            
            # Stop OpenTelemetry integration
            if self._otel_integration:
                await self._otel_integration.stop()
            
            # Clean up resources
            self._logger.close()
            self._tracer.clear_completed_spans()
            
            self._started = False
            
        except Exception as e:
            logging.error(f"Failed to stop observability provider: {e}")
            raise
    
    async def flush(self):
        """Flush all pending data"""
        try:
            # Export any pending metrics
            exported_metrics = self._metrics.export_metrics()
            
            if exported_metrics and self.config.metrics_export_url:
                # In a real implementation, this would send to external system
                self._logger.debug(f"Exported {len(exported_metrics)} metrics",
                                 component="observability",
                                 operation="flush")
            
            # Flush OpenTelemetry data
            if self._otel_integration:
                await self._otel_integration.exporter.flush()
            
            # Flush logger if it has file output
            # (File stream flushing is handled in the logger)
            
        except Exception as e:
            self._logger.error(f"Failed to flush observability data: {e}",
                             component="observability",
                             operation="flush")
    
    def configure(self, config: ObservabilityConfig):
        """Configure observability provider"""
        self.config = config
        
        # Reconfigure components
        configure_logging(config)
        configure_tracing(config)
        configure_metrics(config)
        
        self._logger.info("Observability provider reconfigured",
                        component="observability",
                        operation="configure")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get observability system health status"""
        try:
            # Get current metrics
            all_metrics = self._metrics.get_all_metrics()
            
            # Get trace info
            current_span = self._tracer.get_current_span()
            current_trace_id = self._tracer.get_trace_id()
            
            return {
                "status": "healthy" if self._started else "stopped",
                "config": {
                    "enabled": self.config.enabled,
                    "log_level": self.config.log_level.value,
                    "tracing_enabled": self.config.tracing_enabled,
                    "metrics_enabled": self.config.metrics_enabled
                },
                "current_trace": {
                    "trace_id": current_trace_id,
                    "span_active": current_span is not None
                },
                "metrics_summary": {
                    "counters_count": len(all_metrics.get("counters", {})),
                    "gauges_count": len(all_metrics.get("gauges", {})),
                    "histograms_count": len(all_metrics.get("histogram_stats", {})),
                    "timers_count": len(all_metrics.get("timer_stats", {}))
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def log_with_trace_context(self, level: str, message: str, component: str = None, **kwargs):
        """Log message with automatic trace context correlation"""
        # Get current trace context
        current_span = self._tracer.get_current_span()
        if current_span:
            self._logger.set_trace_context(current_span.trace_id, current_span.span_id)
            kwargs.update({
                'operation': current_span.operation_name,
                'span_duration_ms': current_span.duration_ms
            })
        
        # Log with appropriate level
        if level.lower() == "debug":
            self._logger.debug(message, component, **kwargs)
        elif level.lower() == "info":
            self._logger.info(message, component, **kwargs)
        elif level.lower() == "warning":
            self._logger.warning(message, component, **kwargs)
        elif level.lower() == "error":
            self._logger.error(message, component, **kwargs)
        elif level.lower() == "critical":
            self._logger.critical(message, component, **kwargs)
    
    def trace_and_log_operation(self, operation_name: str, component: str = None):
        """Context manager that traces operation and logs start/end"""
        return TracedOperation(self, operation_name, component)
    
    def export_to_opentelemetry(self, spans: list = None, metrics: list = None):
        """
        Manually export spans and metrics to OpenTelemetry.
        
        Args:
            spans: List of TraceSpan objects to export
            metrics: List of MetricPoint objects to export
        """
        if not self._otel_integration:
            return
        
        if spans:
            for span in spans:
                self._otel_integration.export_span_manually(span)
        
        if metrics:
            for metric in metrics:
                self._otel_integration.export_metric_manually(metric)
    
    @property
    def opentelemetry_enabled(self) -> bool:
        """Check if OpenTelemetry integration is enabled"""
        return self._otel_integration is not None and self._otel_integration._active


class TracedOperation:
    """Context manager for traced operations with automatic logging"""
    
    def __init__(self, provider: ObservabilityProvider, operation_name: str, component: str = None):
        self.provider = provider
        self.operation_name = operation_name
        self.component = component or "unknown"
        self.span = None
    
    def __enter__(self):
        # Start span
        self.span_context = self.provider.tracer.start_span(self.operation_name)
        self.span = self.span_context.__enter__()
        
        # Log operation start
        self.provider.log_with_trace_context(
            "info", 
            f"Started operation: {self.operation_name}",
            self.component,
            operation="start"
        )
        
        # Record operation start metric
        self.provider.metrics.increment_counter(
            "operations.started",
            operation=self.operation_name,
            component=self.component
        )
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # Log operation end
            if exc_type is None:
                self.provider.log_with_trace_context(
                    "info",
                    f"Completed operation: {self.operation_name}",
                    self.component,
                    operation="complete"
                )
                
                # Record success metric
                self.provider.metrics.increment_counter(
                    "operations.completed",
                    operation=self.operation_name,
                    component=self.component,
                    status="success"
                )
            else:
                self.provider.log_with_trace_context(
                    "error",
                    f"Failed operation: {self.operation_name}",
                    self.component,
                    operation="error",
                    error_type=exc_type.__name__ if exc_type else None,
                    error_message=str(exc_val) if exc_val else None
                )
                
                # Record error metric
                self.provider.metrics.increment_counter(
                    "operations.failed",
                    operation=self.operation_name,
                    component=self.component,
                    error_type=exc_type.__name__ if exc_type else "unknown"
                )
        
        finally:
            # End span
            if self.span_context:
                self.span_context.__exit__(exc_type, exc_val, exc_tb)


def create_observability_provider(config: Optional[Dict[str, Any]] = None) -> ObservabilityProvider:
    """
    Create observability provider with configuration.
    
    Args:
        config: Configuration dictionary or ObservabilityConfig
        
    Returns:
        Configured observability provider
    """
    if config is None:
        config = {}
    
    if isinstance(config, dict):
        # Convert dict to ObservabilityConfig
        obs_config = ObservabilityConfig(**config)
    else:
        obs_config = config
    
    return ObservabilityProvider(obs_config)


def create_development_observability() -> ObservabilityProvider:
    """Create observability provider optimized for development"""
    config = ObservabilityConfig(
        enabled=True,
        log_level=LogLevel.DEBUG,
        log_format="text",
        log_output="console",
        tracing_enabled=True,
        trace_sampling_rate=1.0,
        metrics_enabled=True,
        async_processing=False,  # Synchronous for easier debugging
        buffer_size=100
    )
    
    return ObservabilityProvider(config)


def create_production_observability(
    log_file_path: str = "/var/log/langswarm/app.log",
    trace_export_url: Optional[str] = None,
    metrics_export_url: Optional[str] = None,
    opentelemetry_enabled: bool = False,
    otlp_endpoint: Optional[str] = None,
    jaeger_endpoint: Optional[str] = None
) -> ObservabilityProvider:
    """Create observability provider optimized for production"""
    config = ObservabilityConfig(
        enabled=True,
        log_level=LogLevel.INFO,
        log_format="structured",
        log_output="both",
        log_file_path=log_file_path,
        tracing_enabled=True,
        trace_sampling_rate=0.1,  # 10% sampling for performance
        trace_export_url=trace_export_url,
        metrics_enabled=True,
        metrics_export_url=metrics_export_url,
        opentelemetry_enabled=opentelemetry_enabled,
        opentelemetry_otlp_endpoint=otlp_endpoint,
        opentelemetry_jaeger_endpoint=jaeger_endpoint,
        async_processing=True,
        buffer_size=10000,
        flush_interval=10
    )
    
    return ObservabilityProvider(config)
