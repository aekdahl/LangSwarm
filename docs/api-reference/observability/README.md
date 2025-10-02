# LangSwarm V2 Observability API Reference

**Complete API reference for the V2 observability system including logging, tracing, and metrics**

## 🎯 Overview

LangSwarm V2's observability system provides a unified interface for logging, distributed tracing, and metrics collection. The API is designed for high performance with minimal overhead (< 5% CPU, < 10MB memory) while providing comprehensive monitoring capabilities.

**Core Components:**
- **`ObservabilityProvider`**: Unified provider managing all observability components
- **`V2Logger`**: Structured logger with trace correlation
- **`V2Tracer`**: Distributed tracing with span hierarchy
- **`V2Metrics`**: Comprehensive metrics collection (counters, gauges, histograms, timers)
- **`integrations`**: Component-specific observability for all V2 systems

---

## 📦 Package API

### **Main Package Interface**

```python
from langswarm.core.observability import (
    # Main Provider
    ObservabilityProvider,
    
    # Core Components
    V2Logger,
    V2Tracer,
    V2Metrics,
    
    # Configuration
    ObservabilityConfig,
    LoggingConfig,
    TracingConfig,
    MetricsConfig,
    
    # Data Structures
    LogLevel,
    LogEntry,
    Span,
    SpanContext,
    MetricValue,
    MetricType,
    
    # Component Integrations
    AgentObservability,
    ToolObservability,
    SessionObservability,
    MemoryObservability,
    WorkflowObservability,
    
    # Exceptions
    ObservabilityError,
    ConfigurationError,
    TracingError,
    MetricsError
)
```

---

## 🏗️ Core Interfaces

### **ObservabilityProvider**

```python
class ObservabilityProvider:
    """Unified observability provider managing logging, tracing, and metrics"""
    
    def __init__(
        self,
        config: ObservabilityConfig,
        service_name: str = "langswarm_v2",
        service_version: str = "2.0.0"
    ):
        """Initialize observability provider
        
        Args:
            config: Observability configuration
            service_name: Service name for telemetry
            service_version: Service version for telemetry
        """
        
    @classmethod
    def create_development(
        cls,
        service_name: str = "langswarm_v2"
    ) -> 'ObservabilityProvider':
        """Create development configuration with full debugging
        
        Features:
        - DEBUG level logging
        - Console output with colors
        - Full tracing (100% sampling)
        - Detailed metrics
        
        Args:
            service_name: Service name for telemetry
            
        Returns:
            Configured observability provider
        """
        
    @classmethod
    def create_production(
        cls,
        service_name: str = "langswarm_v2",
        log_file: str = "logs/langswarm.log",
        tracing_endpoint: str = None
    ) -> 'ObservabilityProvider':
        """Create production configuration with optimized performance
        
        Features:
        - INFO level logging
        - File output with rotation
        - Sampled tracing (10% sampling)
        - Essential metrics only
        
        Args:
            service_name: Service name for telemetry
            log_file: Log file path
            tracing_endpoint: External tracing endpoint (optional)
            
        Returns:
            Configured observability provider
        """
        
    @classmethod
    def create(
        cls,
        config: dict,
        service_name: str = "langswarm_v2"
    ) -> 'ObservabilityProvider':
        """Create observability provider from configuration dictionary
        
        Args:
            config: Configuration dictionary
            service_name: Service name for telemetry
            
        Returns:
            Configured observability provider
        """
        
    async def initialize(self) -> None:
        """Initialize observability components
        
        Raises:
            ObservabilityError: If initialization fails
        """
        
    async def shutdown(self) -> None:
        """Shutdown observability components gracefully"""
        
    def get_logger(self, component: str = None) -> 'V2Logger':
        """Get logger instance for component
        
        Args:
            component: Component name (uses service name if None)
            
        Returns:
            Logger instance with component context
        """
        
    def get_tracer(self, component: str = None) -> 'V2Tracer':
        """Get tracer instance for component
        
        Args:
            component: Component name (uses service name if None)
            
        Returns:
            Tracer instance with component context
        """
        
    def get_metrics(self, component: str = None) -> 'V2Metrics':
        """Get metrics instance for component
        
        Args:
            component: Component name (uses service name if None)
            
        Returns:
            Metrics instance with component context
        """
        
    async def health_check(self) -> dict:
        """Check observability system health
        
        Returns:
            Health status for all components
        """
        
    async def get_status(self) -> dict:
        """Get comprehensive observability status
        
        Returns:
            Detailed status including performance metrics
        """
        
    def is_initialized(self) -> bool:
        """Check if observability system is initialized"""
        
    def get_configuration(self) -> ObservabilityConfig:
        """Get current observability configuration"""
```

---

## 📝 Logging API

### **V2Logger**

```python
class V2Logger:
    """Production-ready structured logger with trace correlation"""
    
    def __init__(
        self,
        component: str,
        config: LoggingConfig,
        tracer: 'V2Tracer' = None
    ):
        """Initialize logger
        
        Args:
            component: Component name for log context
            config: Logging configuration
            tracer: Tracer for correlation (optional)
        """
        
    def debug(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Log debug message with context
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        
    def info(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Log info message with context
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        
    def warning(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Log warning message with context
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        
    def error(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Log error message with context
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        
    def critical(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Log critical message with context
        
        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        
    def log(
        self,
        level: LogLevel,
        message: str,
        **kwargs
    ) -> None:
        """Log message at specified level
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context fields
        """
        
    def exception(
        self,
        message: str,
        exc_info: Exception = None,
        **kwargs
    ) -> None:
        """Log exception with stack trace
        
        Args:
            message: Log message
            exc_info: Exception info (uses current if None)
            **kwargs: Additional context fields
        """
        
    def bind_context(self, **kwargs) -> 'V2Logger':
        """Create logger with bound context
        
        Args:
            **kwargs: Context to bind
            
        Returns:
            New logger with bound context
        """
        
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for log entries
        
        Args:
            correlation_id: Correlation identifier
        """
        
    def get_correlation_id(self) -> str:
        """Get current correlation ID"""
        
    async def flush(self) -> None:
        """Flush pending log entries"""
```

### **LogLevel and LogEntry**

```python
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    component: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    correlation_id: Optional[str] = None
    service: str = "langswarm_v2"
    version: str = "2.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        
    def to_json(self) -> str:
        """Convert to JSON string"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary"""
```

---

## 🔍 Tracing API

### **V2Tracer**

```python
class V2Tracer:
    """Distributed tracer with span hierarchy and context propagation"""
    
    def __init__(
        self,
        component: str,
        config: TracingConfig
    ):
        """Initialize tracer
        
        Args:
            component: Component name for spans
            config: Tracing configuration
        """
        
    def start_span(
        self,
        operation_name: str,
        parent_span: 'Span' = None,
        attributes: Dict[str, Any] = None,
        kind: str = "INTERNAL"
    ) -> 'Span':
        """Start new span
        
        Args:
            operation_name: Name of the operation
            parent_span: Parent span (uses current if None)
            attributes: Initial span attributes
            kind: Span kind (INTERNAL, CLIENT, SERVER, etc.)
            
        Returns:
            New span instance
        """
        
    def get_current_span(self) -> Optional['Span']:
        """Get current active span"""
        
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        
    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID"""
        
    def trace_function(self, func_name: str = None):
        """Decorator for automatic function tracing
        
        Args:
            func_name: Custom function name (uses actual name if None)
            
        Returns:
            Decorator function
        """
        
    def trace_method(self, method_name: str = None):
        """Decorator for automatic method tracing
        
        Args:
            method_name: Custom method name (uses actual name if None)
            
        Returns:
            Decorator function
        """
        
    async def export_spans(self) -> List[Dict[str, Any]]:
        """Export current spans for external processing
        
        Returns:
            List of span data dictionaries
        """
        
    def set_sampling_rate(self, rate: float) -> None:
        """Update sampling rate
        
        Args:
            rate: Sampling rate (0.0 to 1.0)
        """
        
    def is_sampling(self) -> bool:
        """Check if current trace should be sampled"""

### **Span**

```python
class Span:
    """Distributed tracing span with context and lifecycle management"""
    
    def __init__(
        self,
        operation_name: str,
        span_context: 'SpanContext',
        tracer: 'V2Tracer'
    ):
        """Initialize span
        
        Args:
            operation_name: Name of the operation
            span_context: Span context with trace/span IDs
            tracer: Parent tracer
        """
        
    @property
    def span_id(self) -> str:
        """Get span ID"""
        
    @property
    def trace_id(self) -> str:
        """Get trace ID"""
        
    @property
    def parent_span_id(self) -> Optional[str]:
        """Get parent span ID"""
        
    @property
    def operation_name(self) -> str:
        """Get operation name"""
        
    @property
    def start_time(self) -> datetime:
        """Get span start time"""
        
    @property
    def end_time(self) -> Optional[datetime]:
        """Get span end time (None if not finished)"""
        
    @property
    def duration(self) -> Optional[timedelta]:
        """Get span duration (None if not finished)"""
        
    @property
    def is_finished(self) -> bool:
        """Check if span is finished"""
        
    def set_attribute(self, key: str, value: Any) -> 'Span':
        """Set span attribute
        
        Args:
            key: Attribute key
            value: Attribute value
            
        Returns:
            Self for chaining
        """
        
    def set_attributes(self, attributes: Dict[str, Any]) -> 'Span':
        """Set multiple span attributes
        
        Args:
            attributes: Dictionary of attributes
            
        Returns:
            Self for chaining
        """
        
    def add_event(
        self,
        name: str,
        attributes: Dict[str, Any] = None,
        timestamp: datetime = None
    ) -> 'Span':
        """Add event to span
        
        Args:
            name: Event name
            attributes: Event attributes
            timestamp: Event timestamp (uses current if None)
            
        Returns:
            Self for chaining
        """
        
    def set_status(self, status: str, description: str = None) -> 'Span':
        """Set span status
        
        Args:
            status: Status code (OK, ERROR, etc.)
            description: Status description
            
        Returns:
            Self for chaining
        """
        
    def record_exception(
        self,
        exception: Exception,
        attributes: Dict[str, Any] = None
    ) -> 'Span':
        """Record exception in span
        
        Args:
            exception: Exception to record
            attributes: Additional attributes
            
        Returns:
            Self for chaining
        """
        
    def finish(self, end_time: datetime = None) -> None:
        """Finish span
        
        Args:
            end_time: End time (uses current if None)
        """
        
    def __enter__(self) -> 'Span':
        """Context manager entry"""
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""

### **SpanContext**

```python
@dataclass
class SpanContext:
    """Span context with trace correlation information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 0
    trace_state: Dict[str, str] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if context is valid"""
        
    def with_span_id(self, span_id: str) -> 'SpanContext':
        """Create new context with different span ID"""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpanContext':
        """Create from dictionary"""
```

---

## 📊 Metrics API

### **V2Metrics**

```python
class V2Metrics:
    """Comprehensive metrics collection with counters, gauges, histograms, and timers"""
    
    def __init__(
        self,
        component: str,
        config: MetricsConfig
    ):
        """Initialize metrics
        
        Args:
            component: Component name for metrics
            config: Metrics configuration
        """
        
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Dict[str, str] = None
    ) -> None:
        """Increment counter metric
        
        Args:
            name: Metric name
            value: Increment value
            labels: Metric labels
        """
        
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None
    ) -> None:
        """Set gauge metric value
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels
        """
        
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None
    ) -> None:
        """Record histogram value
        
        Args:
            name: Metric name
            value: Value to record
            labels: Metric labels
        """
        
    def timer(
        self,
        name: str,
        labels: Dict[str, str] = None
    ) -> 'MetricTimer':
        """Create timer context manager
        
        Args:
            name: Metric name
            labels: Metric labels
            
        Returns:
            Timer context manager
        """
        
    def create_counter(
        self,
        name: str,
        description: str = "",
        unit: str = ""
    ) -> 'Counter':
        """Create counter metric
        
        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit
            
        Returns:
            Counter instance
        """
        
    def create_gauge(
        self,
        name: str,
        description: str = "",
        unit: str = ""
    ) -> 'Gauge':
        """Create gauge metric
        
        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit
            
        Returns:
            Gauge instance
        """
        
    def create_histogram(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        buckets: List[float] = None
    ) -> 'Histogram':
        """Create histogram metric
        
        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit
            buckets: Histogram buckets
            
        Returns:
            Histogram instance
        """
        
    async def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics
        
        Returns:
            Dictionary of metric data
        """
        
    async def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format
        
        Returns:
            Prometheus format string
        """
        
    async def export_json_format(self) -> str:
        """Export metrics in JSON format
        
        Returns:
            JSON format string
        """
        
    def get_metric_value(
        self,
        name: str,
        labels: Dict[str, str] = None
    ) -> Optional[float]:
        """Get current metric value
        
        Args:
            name: Metric name
            labels: Metric labels
            
        Returns:
            Current metric value
        """
        
    def reset_metrics(self) -> None:
        """Reset all metrics to zero"""
        
    def list_metrics(self) -> List[str]:
        """List all registered metric names"""

### **Metric Types**

```python
from enum import Enum

class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class MetricValue:
    """Metric value with metadata"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""

class Counter:
    """Counter metric for cumulative values"""
    
    def increment(self, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment counter"""
        
    def get_value(self, labels: Dict[str, str] = None) -> float:
        """Get current value"""

class Gauge:
    """Gauge metric for current values"""
    
    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """Set gauge value"""
        
    def increment(self, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment gauge"""
        
    def decrement(self, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Decrement gauge"""
        
    def get_value(self, labels: Dict[str, str] = None) -> float:
        """Get current value"""

class Histogram:
    """Histogram metric for distribution values"""
    
    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """Observe value"""
        
    def get_count(self, labels: Dict[str, str] = None) -> int:
        """Get observation count"""
        
    def get_sum(self, labels: Dict[str, str] = None) -> float:
        """Get sum of observations"""
        
    def get_buckets(self, labels: Dict[str, str] = None) -> Dict[float, int]:
        """Get bucket counts"""

class MetricTimer:
    """Timer context manager for timing operations"""
    
    def __init__(self, histogram: Histogram, labels: Dict[str, str] = None):
        """Initialize timer"""
        
    def __enter__(self) -> 'MetricTimer':
        """Start timing"""
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and record"""
        
    def stop(self) -> float:
        """Stop timing and return duration"""
```

---

## 🔧 Component Integrations

### **AgentObservability**

```python
class AgentObservability:
    """Agent system observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        """Initialize agent observability
        
        Args:
            observability_provider: Main observability provider
        """
        
    async def initialize(self) -> None:
        """Initialize agent observability hooks"""
        
    async def shutdown(self) -> None:
        """Shutdown agent observability"""
        
    def trace_agent_creation(self, agent_id: str, config: dict) -> None:
        """Trace agent creation
        
        Args:
            agent_id: Agent identifier
            config: Agent configuration
        """
        
    def trace_agent_request(
        self,
        agent_id: str,
        request: str,
        context: dict = None
    ) -> 'Span':
        """Trace agent request processing
        
        Args:
            agent_id: Agent identifier
            request: Request content
            context: Additional context
            
        Returns:
            Request span for nested operations
        """
        
    def record_agent_response(
        self,
        span: 'Span',
        response: str,
        metrics: dict = None
    ) -> None:
        """Record agent response
        
        Args:
            span: Request span
            response: Response content
            metrics: Response metrics (tokens, time, etc.)
        """
        
    def record_agent_error(
        self,
        span: 'Span',
        error: Exception
    ) -> None:
        """Record agent error
        
        Args:
            span: Request span
            error: Error that occurred
        """
```

### **ToolObservability**

```python
class ToolObservability:
    """Tool system observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        """Initialize tool observability"""
        
    async def initialize(self) -> None:
        """Initialize tool observability hooks"""
        
    def trace_tool_execution(
        self,
        tool_name: str,
        operation: str,
        parameters: dict = None
    ) -> 'Span':
        """Trace tool execution
        
        Args:
            tool_name: Tool name
            operation: Operation name
            parameters: Operation parameters
            
        Returns:
            Execution span
        """
        
    def record_tool_result(
        self,
        span: 'Span',
        result: Any,
        metrics: dict = None
    ) -> None:
        """Record tool execution result
        
        Args:
            span: Execution span
            result: Tool result
            metrics: Execution metrics
        """
        
    def record_tool_error(
        self,
        span: 'Span',
        error: Exception
    ) -> None:
        """Record tool execution error
        
        Args:
            span: Execution span
            error: Error that occurred
        """
```

### **SessionObservability**

```python
class SessionObservability:
    """Session system observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        """Initialize session observability"""
        
    async def initialize(self) -> None:
        """Initialize session observability hooks"""
        
    def trace_session_creation(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str
    ) -> None:
        """Trace session creation
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            provider: LLM provider
            model: Model name
        """
        
    def trace_message_processing(
        self,
        session_id: str,
        message: str,
        role: str = "user"
    ) -> 'Span':
        """Trace message processing
        
        Args:
            session_id: Session identifier
            message: Message content
            role: Message role
            
        Returns:
            Message processing span
        """
        
    def record_message_response(
        self,
        span: 'Span',
        response: str,
        metrics: dict = None
    ) -> None:
        """Record message response
        
        Args:
            span: Message processing span
            response: Response content
            metrics: Response metrics
        """
```

### **MemoryObservability**

```python
class MemoryObservability:
    """Memory system observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        """Initialize memory observability"""
        
    async def initialize(self) -> None:
        """Initialize memory observability hooks"""
        
    def trace_memory_operation(
        self,
        operation: str,
        key: str,
        backend: str = None
    ) -> 'Span':
        """Trace memory operation
        
        Args:
            operation: Operation type (save, load, delete, etc.)
            key: Memory key
            backend: Memory backend
            
        Returns:
            Operation span
        """
        
    def record_memory_result(
        self,
        span: 'Span',
        result: Any,
        metrics: dict = None
    ) -> None:
        """Record memory operation result
        
        Args:
            span: Operation span
            result: Operation result
            metrics: Operation metrics
        """
```

### **WorkflowObservability**

```python
class WorkflowObservability:
    """Workflow system observability integration"""
    
    def __init__(self, observability_provider: ObservabilityProvider):
        """Initialize workflow observability"""
        
    async def initialize(self) -> None:
        """Initialize workflow observability hooks"""
        
    def trace_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        input_data: dict = None
    ) -> 'Span':
        """Trace workflow execution
        
        Args:
            workflow_id: Workflow identifier
            workflow_name: Workflow name
            input_data: Input data
            
        Returns:
            Workflow execution span
        """
        
    def trace_workflow_step(
        self,
        parent_span: 'Span',
        step_name: str,
        step_type: str,
        input_data: dict = None
    ) -> 'Span':
        """Trace workflow step execution
        
        Args:
            parent_span: Parent workflow span
            step_name: Step name
            step_type: Step type
            input_data: Step input data
            
        Returns:
            Step execution span
        """
        
    def record_workflow_result(
        self,
        span: 'Span',
        result: Any,
        metrics: dict = None
    ) -> None:
        """Record workflow execution result
        
        Args:
            span: Execution span
            result: Workflow result
            metrics: Execution metrics
        """
```

---

## ⚙️ Configuration

### **ObservabilityConfig**

```python
@dataclass
class ObservabilityConfig:
    """Complete observability configuration"""
    logging: LoggingConfig
    tracing: TracingConfig
    metrics: MetricsConfig
    integrations: IntegrationsConfig = field(default_factory=lambda: IntegrationsConfig())
    performance: PerformanceConfig = field(default_factory=lambda: PerformanceConfig())
    
    @classmethod
    def development(cls) -> 'ObservabilityConfig':
        """Create development configuration"""
        
    @classmethod
    def production(cls) -> 'ObservabilityConfig':
        """Create production configuration"""
        
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ObservabilityConfig':
        """Create from configuration dictionary"""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        
    def validate(self) -> List[str]:
        """Validate configuration and return errors"""

### **LoggingConfig**

```python
@dataclass
class LoggingConfig:
    """Logging system configuration"""
    level: LogLevel = LogLevel.INFO
    output: str = "console"  # console, file, both
    format: str = "json"     # json, detailed, simple
    file_path: str = "logs/langswarm.log"
    rotation: Optional[Dict[str, Any]] = None
    correlation: bool = True
    color: bool = False
    filters: Optional[Dict[str, Any]] = None
    
    def validate(self) -> List[str]:
        """Validate logging configuration"""

### **TracingConfig**

```python
@dataclass
class TracingConfig:
    """Tracing system configuration"""
    enabled: bool = True
    sampling_rate: float = 0.1
    exporter: str = "console"  # console, otlp, jaeger
    endpoint: Optional[str] = None
    span_processor: str = "batch"  # simple, batch
    max_spans_per_trace: int = 100
    max_attributes_per_span: int = 50
    max_events_per_span: int = 20
    span_timeout_seconds: int = 300
    
    def validate(self) -> List[str]:
        """Validate tracing configuration"""

### **MetricsConfig**

```python
@dataclass
class MetricsConfig:
    """Metrics system configuration"""
    enabled: bool = True
    export_interval: int = 60
    prometheus_endpoint: Optional[str] = None
    include_histograms: bool = True
    max_label_count: int = 20
    exclude_labels: List[str] = field(default_factory=list)
    custom_buckets: Dict[str, List[float]] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate metrics configuration"""
```

---

## ❌ Exception Handling

### **Observability Exceptions**

```python
class ObservabilityError(Exception):
    """Base observability error"""
    
    def __init__(
        self,
        message: str,
        component: str = None,
        error_code: str = None,
        context: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.component = component
        self.error_code = error_code
        self.context = context or {}

class ConfigurationError(ObservabilityError):
    """Observability configuration error"""

class TracingError(ObservabilityError):
    """Tracing system error"""

class MetricsError(ObservabilityError):
    """Metrics system error"""

class IntegrationError(ObservabilityError):
    """Component integration error"""

# Usage with error handling
try:
    observability = ObservabilityProvider.create_production()
    await observability.initialize()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    # Fall back to development config
    observability = ObservabilityProvider.create_development()
    await observability.initialize()
except ObservabilityError as e:
    logger.error(f"Observability error: {e}")
    raise
```

---

## 🌍 Global Observability Management

### **Global Provider**

```python
# Global observability provider
_global_observability_provider: Optional[ObservabilityProvider] = None

def set_global_observability_provider(provider: ObservabilityProvider) -> None:
    """Set global observability provider"""
    global _global_observability_provider
    _global_observability_provider = provider

def get_global_observability_provider() -> Optional[ObservabilityProvider]:
    """Get global observability provider"""
    return _global_observability_provider

def get_logger(component: str = None) -> V2Logger:
    """Get logger from global provider"""
    provider = get_global_observability_provider()
    if not provider:
        raise ObservabilityError("No global observability provider configured")
    return provider.get_logger(component)

def get_tracer(component: str = None) -> V2Tracer:
    """Get tracer from global provider"""
    provider = get_global_observability_provider()
    if not provider:
        raise ObservabilityError("No global observability provider configured")
    return provider.get_tracer(component)

def get_metrics(component: str = None) -> V2Metrics:
    """Get metrics from global provider"""
    provider = get_global_observability_provider()
    if not provider:
        raise ObservabilityError("No global observability provider configured")
    return provider.get_metrics(component)

# Context manager for observability
class ObservabilityContext:
    """Context manager for observability operations"""
    
    def __init__(self, provider: ObservabilityProvider):
        self.provider = provider
        
    async def __aenter__(self) -> ObservabilityProvider:
        await self.provider.initialize()
        return self.provider
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.provider.shutdown()
```

---

**LangSwarm V2's observability API provides comprehensive monitoring capabilities with minimal performance overhead, making it suitable for both development debugging and production monitoring at scale.**
