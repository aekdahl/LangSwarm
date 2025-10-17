"""
OpenTelemetry Integration for LangSwarm V2 Observability

Provides OpenTelemetry export capabilities for traces, metrics, and logs
to external observability tools like Jaeger, Prometheus, Grafana, etc.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field

from ..utils.optional_imports import OptionalImportManager

# Optional OpenTelemetry imports
otel_imports = OptionalImportManager()

# Helper to get OpenTelemetry modules lazily
def get_otel_module(module_name: str):
    return otel_imports.try_import(module_name, feature_name="OpenTelemetry observability")

from .interfaces import (
    IObservabilityProvider, ObservabilityConfig, TraceSpan, MetricPoint, LogEvent,
    SpanStatus, MetricType, LogLevel, ObservabilityError
)

logger = logging.getLogger(__name__)


@dataclass
class OpenTelemetryConfig:
    """OpenTelemetry-specific configuration"""
    enabled: bool = False
    
    # Service information
    service_name: str = "langswarm"
    service_version: str = "2.0.0"
    service_namespace: str = "langswarm"
    
    # OTLP configuration
    otlp_endpoint: Optional[str] = None
    otlp_headers: Dict[str, str] = field(default_factory=dict)
    otlp_insecure: bool = True
    
    # Jaeger configuration
    jaeger_endpoint: Optional[str] = None
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    
    # Prometheus configuration
    prometheus_enabled: bool = False
    prometheus_port: int = 8000
    prometheus_host: str = "0.0.0.0"
    
    # Export configuration
    export_traces: bool = True
    export_metrics: bool = True
    export_logs: bool = False  # Not yet supported by all exporters
    
    # Batch processing
    batch_span_processor_max_queue_size: int = 2048
    batch_span_processor_schedule_delay_millis: int = 5000
    batch_span_processor_export_timeout_millis: int = 30000
    batch_span_processor_max_export_batch_size: int = 512


class OpenTelemetryExporter:
    """
    OpenTelemetry exporter for LangSwarm observability data.
    
    Bridges LangSwarm's internal observability system with OpenTelemetry
    to enable export to external observability tools.
    """
    
    def __init__(self, config: OpenTelemetryConfig):
        """
        Initialize OpenTelemetry exporter.
        
        Args:
            config: OpenTelemetry configuration
        """
        self.config = config
        self._initialized = False
        self._trace_provider = None
        self._metric_provider = None
        self._tracer = None
        self._meter = None
        self._span_processors = []
        self._metric_readers = []
        
        # Check if OpenTelemetry is available
        if not otel_imports.check_availability():
            if config.enabled:
                logger.warning(
                    "OpenTelemetry integration is enabled but dependencies are not installed. "
                    "Install with: pip install langswarm[opentelemetry]"
                )
            return
        
        self._otel_available = True
        
        if config.enabled:
            self._initialize_opentelemetry()
    
    def _initialize_opentelemetry(self):
        """Initialize OpenTelemetry providers and exporters"""
        if not self._otel_available:
            return
        
        try:
            # Import OpenTelemetry modules
            trace = otel_imports.get_import('opentelemetry.trace')
            metrics = otel_imports.get_import('opentelemetry.metrics')
            trace_sdk = otel_imports.get_import('opentelemetry.sdk.trace')
            metrics_sdk = otel_imports.get_import('opentelemetry.sdk.metrics')
            Resource = otel_imports.get_import('opentelemetry.sdk.resources')
            
            # Create resource
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "service.namespace": self.config.service_namespace,
            })
            
            # Initialize tracing
            if self.config.export_traces:
                self._initialize_tracing(trace_sdk, resource)
            
            # Initialize metrics
            if self.config.export_metrics:
                self._initialize_metrics(metrics_sdk, resource)
            
            self._initialized = True
            logger.info("OpenTelemetry exporter initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            raise ObservabilityError(f"OpenTelemetry initialization failed: {e}")
    
    def _initialize_tracing(self, trace_sdk, resource):
        """Initialize OpenTelemetry tracing"""
        # Create trace provider
        self._trace_provider = trace_sdk.TracerProvider(resource=resource)
        
        # Add span processors based on configuration
        if self.config.otlp_endpoint:
            self._add_otlp_span_exporter()
        
        if self.config.jaeger_endpoint:
            self._add_jaeger_span_exporter()
        
        # Set global trace provider
        trace = otel_imports.get_import('opentelemetry.trace')
        trace.set_tracer_provider(self._trace_provider)
        
        # Get tracer
        self._tracer = trace.get_tracer(
            self.config.service_name,
            self.config.service_version
        )
    
    def _add_otlp_span_exporter(self):
        """Add OTLP span exporter"""
        try:
            OTLPSpanExporter = otel_imports.get_import('opentelemetry.exporter.otlp.proto.grpc.trace_exporter')
            BatchSpanProcessor = otel_imports.get_import('opentelemetry.sdk.trace.export')
            
            exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self.config.otlp_headers,
                insecure=self.config.otlp_insecure
            )
            
            processor = BatchSpanProcessor(
                exporter,
                max_queue_size=self.config.batch_span_processor_max_queue_size,
                schedule_delay_millis=self.config.batch_span_processor_schedule_delay_millis,
                export_timeout_millis=self.config.batch_span_processor_export_timeout_millis,
                max_export_batch_size=self.config.batch_span_processor_max_export_batch_size
            )
            
            self._trace_provider.add_span_processor(processor)
            self._span_processors.append(processor)
            logger.info(f"Added OTLP span exporter: {self.config.otlp_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to add OTLP span exporter: {e}")
    
    def _add_jaeger_span_exporter(self):
        """Add Jaeger span exporter"""
        try:
            JaegerExporter = otel_imports.get_import('opentelemetry.exporter.jaeger.thrift')
            BatchSpanProcessor = otel_imports.get_import('opentelemetry.sdk.trace.export')
            
            exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_agent_host,
                agent_port=self.config.jaeger_agent_port,
                collector_endpoint=self.config.jaeger_endpoint
            )
            
            processor = BatchSpanProcessor(exporter)
            self._trace_provider.add_span_processor(processor)
            self._span_processors.append(processor)
            logger.info(f"Added Jaeger span exporter: {self.config.jaeger_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to add Jaeger span exporter: {e}")
    
    def _initialize_metrics(self, metrics_sdk, resource):
        """Initialize OpenTelemetry metrics"""
        # Create metric readers based on configuration
        readers = []
        
        if self.config.otlp_endpoint:
            readers.append(self._create_otlp_metric_reader())
        
        if self.config.prometheus_enabled:
            readers.append(self._create_prometheus_metric_reader())
        
        # Create metrics provider
        self._metric_provider = metrics_sdk.MeterProvider(
            resource=resource,
            metric_readers=readers
        )
        
        # Set global metrics provider
        metrics = otel_imports.get_import('opentelemetry.metrics')
        metrics.set_meter_provider(self._metric_provider)
        
        # Get meter
        self._meter = metrics.get_meter(
            self.config.service_name,
            self.config.service_version
        )
        
        self._metric_readers = readers
    
    def _create_otlp_metric_reader(self):
        """Create OTLP metric reader"""
        try:
            OTLPMetricExporter = otel_imports.get_import('opentelemetry.exporter.otlp.proto.grpc.metric_exporter')
            PeriodicExportingMetricReader = otel_imports.get_import('opentelemetry.sdk.metrics.export')
            
            exporter = OTLPMetricExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self.config.otlp_headers,
                insecure=self.config.otlp_insecure
            )
            
            reader = PeriodicExportingMetricReader(
                exporter=exporter,
                export_interval_millis=60000  # 60 seconds
            )
            
            logger.info(f"Created OTLP metric reader: {self.config.otlp_endpoint}")
            return reader
            
        except Exception as e:
            logger.error(f"Failed to create OTLP metric reader: {e}")
            return None
    
    def _create_prometheus_metric_reader(self):
        """Create Prometheus metric reader"""
        try:
            PrometheusMetricReader = otel_imports.get_import('opentelemetry.exporter.prometheus')
            
            reader = PrometheusMetricReader(
                port=self.config.prometheus_port,
                host=self.config.prometheus_host
            )
            
            logger.info(f"Created Prometheus metric reader on {self.config.prometheus_host}:{self.config.prometheus_port}")
            return reader
            
        except Exception as e:
            logger.error(f"Failed to create Prometheus metric reader: {e}")
            return None
    
    def export_span(self, span: TraceSpan):
        """
        Export a LangSwarm TraceSpan to OpenTelemetry.
        
        Args:
            span: LangSwarm trace span to export
        """
        if not self._initialized or not self._tracer:
            return
        
        try:
            # Convert LangSwarm span to OpenTelemetry span
            with self._tracer.start_as_current_span(
                span.operation_name,
                start_time=int(span.start_time.timestamp() * 1_000_000_000)  # nanoseconds
            ) as otel_span:
                # Set span attributes
                if span.component:
                    otel_span.set_attribute("component", span.component)
                
                # Set custom tags as attributes
                for key, value in span.tags.items():
                    otel_span.set_attribute(key, str(value))
                
                # Add span logs as events
                for log_entry in span.logs:
                    otel_span.add_event(
                        log_entry.get("message", ""),
                        attributes=log_entry
                    )
                
                # Set span status
                if span.status == SpanStatus.ERROR:
                    otel_span.set_status(trace.Status(trace.StatusCode.ERROR))
                elif span.status == SpanStatus.OK:
                    otel_span.set_status(trace.Status(trace.StatusCode.OK))
                
                # Set end time if available
                if span.end_time:
                    otel_span.end(int(span.end_time.timestamp() * 1_000_000_000))
                    
        except Exception as e:
            logger.error(f"Failed to export span to OpenTelemetry: {e}")
    
    def export_metric(self, metric: MetricPoint):
        """
        Export a LangSwarm MetricPoint to OpenTelemetry.
        
        Args:
            metric: LangSwarm metric point to export
        """
        if not self._initialized or not self._meter:
            return
        
        try:
            # Create or get the appropriate metric instrument
            if metric.metric_type == MetricType.COUNTER:
                counter = self._meter.create_counter(
                    name=metric.name,
                    description=f"Counter metric: {metric.name}"
                )
                counter.add(metric.value, attributes=metric.tags)
                
            elif metric.metric_type == MetricType.GAUGE:
                gauge = self._meter.create_gauge(
                    name=metric.name,
                    description=f"Gauge metric: {metric.name}"
                )
                gauge.set(metric.value, attributes=metric.tags)
                
            elif metric.metric_type == MetricType.HISTOGRAM:
                histogram = self._meter.create_histogram(
                    name=metric.name,
                    description=f"Histogram metric: {metric.name}"
                )
                histogram.record(metric.value, attributes=metric.tags)
                
        except Exception as e:
            logger.error(f"Failed to export metric to OpenTelemetry: {e}")
    
    async def flush(self):
        """Flush all pending telemetry data"""
        if not self._initialized:
            return
        
        try:
            # Flush span processors
            for processor in self._span_processors:
                if hasattr(processor, 'force_flush'):
                    processor.force_flush()
            
            # Flush metric readers
            for reader in self._metric_readers:
                if hasattr(reader, 'force_flush'):
                    reader.force_flush()
                    
        except Exception as e:
            logger.error(f"Failed to flush OpenTelemetry data: {e}")
    
    async def shutdown(self):
        """Shutdown OpenTelemetry exporter"""
        if not self._initialized:
            return
        
        try:
            # Shutdown span processors
            for processor in self._span_processors:
                if hasattr(processor, 'shutdown'):
                    processor.shutdown()
            
            # Shutdown metric readers
            for reader in self._metric_readers:
                if hasattr(reader, 'shutdown'):
                    reader.shutdown()
            
            self._initialized = False
            logger.info("OpenTelemetry exporter shutdown completed")
            
        except Exception as e:
            logger.error(f"Failed to shutdown OpenTelemetry exporter: {e}")


class OpenTelemetryIntegration:
    """
    Integration layer between LangSwarm observability and OpenTelemetry.
    
    Automatically exports traces and metrics from LangSwarm's observability
    system to configured OpenTelemetry exporters.
    """
    
    def __init__(self, observability_provider: IObservabilityProvider, 
                 otel_config: OpenTelemetryConfig):
        """
        Initialize OpenTelemetry integration.
        
        Args:
            observability_provider: LangSwarm observability provider
            otel_config: OpenTelemetry configuration
        """
        self.observability_provider = observability_provider
        self.otel_config = otel_config
        self.exporter = OpenTelemetryExporter(otel_config)
        self._active = False
    
    async def start(self):
        """Start OpenTelemetry integration"""
        if self.otel_config.enabled and not self._active:
            # TODO: Hook into observability provider to automatically export data
            # This would require extending the observability provider interfaces
            # to support export callbacks or observers
            self._active = True
            logger.info("OpenTelemetry integration started")
    
    async def stop(self):
        """Stop OpenTelemetry integration"""
        if self._active:
            await self.exporter.shutdown()
            self._active = False
            logger.info("OpenTelemetry integration stopped")
    
    def export_span_manually(self, span: TraceSpan):
        """Manually export a span (for testing or explicit export)"""
        if self._active:
            self.exporter.export_span(span)
    
    def export_metric_manually(self, metric: MetricPoint):
        """Manually export a metric (for testing or explicit export)"""
        if self._active:
            self.exporter.export_metric(metric)
