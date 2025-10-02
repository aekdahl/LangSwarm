"""
LangSwarm V2 Observability Interfaces

Core interfaces for unified observability system providing logging,
tracing, metrics, and monitoring across all V2 components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, ContextManager
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class SpanStatus(Enum):
    """Trace span status enumeration"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class LogEvent:
    """Structured log event"""
    timestamp: datetime
    level: LogLevel
    message: str
    component: str
    operation: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class TraceSpan:
    """Distributed trace span"""
    span_id: str
    trace_id: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    parent_span_id: Optional[str] = None
    status: SpanStatus = SpanStatus.OK
    component: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.span_id:
            self.span_id = str(uuid.uuid4())
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        if self.start_time is None:
            self.start_time = datetime.utcnow()
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None


@dataclass
class MetricPoint:
    """Metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ObservabilityConfig:
    """Observability system configuration"""
    enabled: bool = True
    
    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "structured"  # structured, text
    log_output: str = "console"     # console, file, both
    log_file_path: Optional[str] = None
    
    # Tracing configuration
    tracing_enabled: bool = True
    trace_sampling_rate: float = 1.0  # 0.0 to 1.0
    trace_export_url: Optional[str] = None
    
    # Metrics configuration
    metrics_enabled: bool = True
    metrics_export_interval: int = 60  # seconds
    metrics_export_url: Optional[str] = None
    
    # OpenTelemetry configuration
    opentelemetry_enabled: bool = False
    opentelemetry_service_name: str = "langswarm"
    opentelemetry_service_version: str = "2.0.0"
    opentelemetry_otlp_endpoint: Optional[str] = None
    opentelemetry_otlp_headers: Dict[str, str] = field(default_factory=dict)
    opentelemetry_jaeger_endpoint: Optional[str] = None
    opentelemetry_prometheus_enabled: bool = False
    opentelemetry_prometheus_port: int = 8000
    
    # Component filtering
    enabled_components: Optional[List[str]] = None
    disabled_components: Optional[List[str]] = None
    
    # Performance settings
    async_processing: bool = True
    buffer_size: int = 1000
    flush_interval: int = 5  # seconds


class ILogger(ABC):
    """Interface for structured logging"""
    
    @abstractmethod
    def debug(self, message: str, component: str = None, **kwargs):
        """Log debug message"""
        pass
    
    @abstractmethod
    def info(self, message: str, component: str = None, **kwargs):
        """Log info message"""
        pass
    
    @abstractmethod
    def warning(self, message: str, component: str = None, **kwargs):
        """Log warning message"""
        pass
    
    @abstractmethod
    def error(self, message: str, component: str = None, **kwargs):
        """Log error message"""
        pass
    
    @abstractmethod
    def critical(self, message: str, component: str = None, **kwargs):
        """Log critical message"""
        pass
    
    @abstractmethod
    def log(self, level: LogLevel, message: str, component: str = None, **kwargs):
        """Log message at specified level"""
        pass


class ITracer(ABC):
    """Interface for distributed tracing"""
    
    @abstractmethod
    def start_span(self, operation_name: str, parent_span_id: Optional[str] = None,
                   **tags) -> ContextManager[TraceSpan]:
        """Start a new trace span"""
        pass
    
    @abstractmethod
    def get_current_span(self) -> Optional[TraceSpan]:
        """Get the current active span"""
        pass
    
    @abstractmethod
    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID"""
        pass
    
    @abstractmethod
    def add_span_tag(self, key: str, value: Any):
        """Add tag to current span"""
        pass
    
    @abstractmethod
    def add_span_log(self, message: str, **kwargs):
        """Add log entry to current span"""
        pass


class IMetrics(ABC):
    """Interface for metrics collection"""
    
    @abstractmethod
    def increment_counter(self, name: str, value: float = 1.0, **tags):
        """Increment a counter metric"""
        pass
    
    @abstractmethod
    def set_gauge(self, name: str, value: float, **tags):
        """Set a gauge metric value"""
        pass
    
    @abstractmethod
    def record_histogram(self, name: str, value: float, **tags):
        """Record a histogram value"""
        pass
    
    @abstractmethod
    def start_timer(self, name: str, **tags) -> ContextManager:
        """Start a timer context manager"""
        pass
    
    @abstractmethod
    def record_timer(self, name: str, duration_ms: float, **tags):
        """Record a timer duration"""
        pass


class IObservabilityProvider(ABC):
    """Interface for unified observability provider"""
    
    @property
    @abstractmethod
    def logger(self) -> ILogger:
        """Get logger instance"""
        pass
    
    @property
    @abstractmethod
    def tracer(self) -> ITracer:
        """Get tracer instance"""
        pass
    
    @property
    @abstractmethod
    def metrics(self) -> IMetrics:
        """Get metrics instance"""
        pass
    
    @abstractmethod
    async def start(self):
        """Start observability provider"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop observability provider"""
        pass
    
    @abstractmethod
    async def flush(self):
        """Flush all pending data"""
        pass
    
    @abstractmethod
    def configure(self, config: ObservabilityConfig):
        """Configure observability provider"""
        pass


class ObservabilityError(Exception):
    """Base observability error"""
    pass


class TracingError(ObservabilityError):
    """Tracing-specific error"""
    pass


class MetricsError(ObservabilityError):
    """Metrics-specific error"""
    pass


class LoggingError(ObservabilityError):
    """Logging-specific error"""
    pass
