# LangSwarm V2 Tracing Standards

**Purpose**: Define comprehensive tracing requirements for all V2 migration tasks to ensure complete observability and debugging capabilities.

---

## 🎯 **Tracing Philosophy**

### **Core Principles**
1. **Comprehensive Coverage**: Trace all component interactions and data flow
2. **Minimal Overhead**: Tracing must not impact performance significantly
3. **Structured Data**: All trace data must be structured and searchable
4. **Context Preservation**: Maintain full request context throughout traces
5. **Production Safe**: Tracing must be safe for production environments

### **Tracing Goals**
- **Complete Visibility**: See exactly what happens during request processing
- **Performance Monitoring**: Track timing and resource usage
- **Error Debugging**: Full context for error investigation
- **System Understanding**: Help developers understand system behavior

---

## 📋 **Tracing Types Required**

### **1. Component Tracing**
**Purpose**: Track component lifecycle and interactions

**Requirements**:
- **Entry/Exit Points**: All public methods and functions
- **State Changes**: Component state transitions
- **Configuration**: Component initialization and configuration
- **Resource Usage**: Memory, connections, file handles

**Implementation Pattern**:
```python
# langswarm/v2/core/[component]/tracing.py
from langswarm.v2.core.observability import get_tracer
from typing import Any, Dict
import functools
import time

tracer = get_tracer(__name__)

def trace_component_method(operation_name: str = None):
    """Decorator for tracing component methods"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            operation = operation_name or f"{self.__class__.__name__}.{func.__name__}"
            
            with tracer.trace_operation(
                component=self.__class__.__name__,
                operation=operation,
                description=f"Executing {operation}"
            ) as span:
                # Add method arguments to trace context
                span.set_tag("args_count", len(args))
                span.set_tag("kwargs_keys", list(kwargs.keys()))
                
                # Add component state to trace
                if hasattr(self, '_get_trace_state'):
                    span.set_tag("component_state", self._get_trace_state())
                
                try:
                    start_time = time.time()
                    result = func(self, *args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Add result information to trace
                    span.set_tag("execution_time", execution_time)
                    span.set_tag("success", True)
                    
                    return result
                    
                except Exception as e:
                    span.set_tag("success", False)
                    span.set_tag("error_type", type(e).__name__)
                    span.set_tag("error_message", str(e))
                    raise
        
        return wrapper
    return decorator

class ComponentTracer:
    """Base class for component-specific tracing"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.tracer = get_tracer(f"component.{component_name}")
    
    def trace_initialization(self, config: Dict[str, Any]):
        """Trace component initialization"""
        with self.tracer.trace_operation(
            component=self.component_name,
            operation="initialize",
            description=f"Initializing {self.component_name}"
        ) as span:
            span.set_tag("config_keys", list(config.keys()))
            span.set_tag("config_size", len(str(config)))
    
    def trace_state_change(self, from_state: str, to_state: str, reason: str = None):
        """Trace component state changes"""
        with self.tracer.trace_operation(
            component=self.component_name,
            operation="state_change",
            description=f"State change: {from_state} → {to_state}"
        ) as span:
            span.set_tag("from_state", from_state)
            span.set_tag("to_state", to_state)
            if reason:
                span.set_tag("reason", reason)
```

**Required Trace Points**:
- [ ] **Component Initialization**: Constructor and setup methods
- [ ] **Public Method Entry/Exit**: All public API methods
- [ ] **State Changes**: Any component state modifications
- [ ] **Configuration Changes**: Runtime configuration updates
- [ ] **Resource Allocation/Deallocation**: Memory, connections, files

### **2. Error Tracing**
**Purpose**: Comprehensive error context and debugging information

**Requirements**:
- **Error Context**: Full context when errors occur
- **Error Propagation**: Track errors through component boundaries
- **Recovery Attempts**: Trace error recovery mechanisms
- **Error Analysis**: Data for error pattern analysis

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/error_tracing.py
from langswarm.v2.core.observability import get_tracer
from langswarm.v2.core.errors import LangSwarmError
import traceback
import sys

class ErrorTracer:
    """Specialized tracer for error scenarios"""
    
    def __init__(self):
        self.tracer = get_tracer("errors")
    
    def trace_error_occurrence(self, error: Exception, context: Dict[str, Any] = None):
        """Trace error occurrence with full context"""
        with self.tracer.trace_operation(
            component="error_handler",
            operation="error_occurrence",
            description=f"Error occurred: {type(error).__name__}"
        ) as span:
            # Basic error information
            span.set_tag("error_type", type(error).__name__)
            span.set_tag("error_message", str(error))
            span.set_tag("error_module", error.__class__.__module__)
            
            # Stack trace information
            tb = traceback.format_exception(type(error), error, error.__traceback__)
            span.set_tag("stack_trace", "".join(tb))
            span.set_tag("stack_depth", len(tb))
            
            # LangSwarm error context
            if isinstance(error, LangSwarmError):
                span.set_tag("severity", error.severity.value)
                span.set_tag("category", error.category.value)
                if error.context:
                    span.set_tag("error_component", error.context.component)
                    span.set_tag("error_operation", error.context.operation)
                    span.set_tag("error_metadata", error.context.metadata)
            
            # Additional context
            if context:
                for key, value in context.items():
                    span.set_tag(f"context_{key}", value)
    
    def trace_error_recovery(self, error: Exception, recovery_strategy: str, success: bool):
        """Trace error recovery attempts"""
        with self.tracer.trace_operation(
            component="error_handler",
            operation="error_recovery",
            description=f"Recovery attempt: {recovery_strategy}"
        ) as span:
            span.set_tag("original_error", type(error).__name__)
            span.set_tag("recovery_strategy", recovery_strategy)
            span.set_tag("recovery_success", success)
```

**Required Error Trace Points**:
- [ ] **Error Creation**: When errors are first created
- [ ] **Error Propagation**: When errors cross component boundaries
- [ ] **Error Handling**: When errors are caught and handled
- [ ] **Error Recovery**: When recovery mechanisms are attempted
- [ ] **Error Resolution**: When errors are resolved or escalated

### **3. Performance Tracing**
**Purpose**: Track timing, resource usage, and performance bottlenecks

**Requirements**:
- **Timing Measurements**: Execution time for all operations
- **Resource Monitoring**: CPU, memory, I/O usage
- **Bottleneck Detection**: Identify slow operations
- **Performance Trends**: Track performance over time

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/performance_tracing.py
from langswarm.v2.core.observability import get_tracer
import time
import psutil
import threading
from typing import Dict, Any

class PerformanceTracer:
    """Specialized tracer for performance monitoring"""
    
    def __init__(self):
        self.tracer = get_tracer("performance")
        self.process = psutil.Process()
    
    def trace_execution_time(self, operation: str, component: str = None):
        """Context manager for tracing execution time"""
        return self.ExecutionTimer(self.tracer, operation, component)
    
    def trace_resource_usage(self, operation: str, component: str = None):
        """Context manager for tracing resource usage"""
        return self.ResourceMonitor(self.tracer, operation, component, self.process)
    
    class ExecutionTimer:
        """Context manager for timing operations"""
        
        def __init__(self, tracer, operation: str, component: str = None):
            self.tracer = tracer
            self.operation = operation
            self.component = component or "unknown"
            self.start_time = None
            self.span = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            self.span = self.tracer.trace_operation(
                component=self.component,
                operation=self.operation,
                description=f"Timing {self.operation}"
            ).__enter__()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            execution_time = time.perf_counter() - self.start_time
            self.span.set_tag("execution_time_ms", execution_time * 1000)
            self.span.set_tag("execution_time_category", self._categorize_time(execution_time))
            self.span.__exit__(exc_type, exc_val, exc_tb)
        
        def _categorize_time(self, execution_time: float) -> str:
            """Categorize execution time for analysis"""
            if execution_time < 0.001:  # < 1ms
                return "very_fast"
            elif execution_time < 0.01:  # < 10ms
                return "fast"
            elif execution_time < 0.1:  # < 100ms
                return "normal"
            elif execution_time < 1.0:  # < 1s
                return "slow"
            else:
                return "very_slow"
    
    class ResourceMonitor:
        """Context manager for monitoring resource usage"""
        
        def __init__(self, tracer, operation: str, component: str, process):
            self.tracer = tracer
            self.operation = operation
            self.component = component
            self.process = process
            self.start_memory = None
            self.start_cpu_time = None
            self.span = None
        
        def __enter__(self):
            self.start_memory = self.process.memory_info().rss
            self.start_cpu_time = self.process.cpu_times()
            self.span = self.tracer.trace_operation(
                component=self.component,
                operation=self.operation,
                description=f"Resource monitoring {self.operation}"
            ).__enter__()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_memory = self.process.memory_info().rss
            end_cpu_time = self.process.cpu_times()
            
            memory_delta = end_memory - self.start_memory
            cpu_delta = (end_cpu_time.user - self.start_cpu_time.user) + \
                       (end_cpu_time.system - self.start_cpu_time.system)
            
            self.span.set_tag("memory_usage_bytes", end_memory)
            self.span.set_tag("memory_delta_bytes", memory_delta)
            self.span.set_tag("cpu_time_delta", cpu_delta)
            self.span.set_tag("memory_category", self._categorize_memory(memory_delta))
            
            self.span.__exit__(exc_type, exc_val, exc_tb)
        
        def _categorize_memory(self, memory_delta: int) -> str:
            """Categorize memory usage for analysis"""
            if memory_delta < 1024:  # < 1KB
                return "minimal"
            elif memory_delta < 1024 * 1024:  # < 1MB
                return "small"
            elif memory_delta < 10 * 1024 * 1024:  # < 10MB
                return "moderate"
            elif memory_delta < 100 * 1024 * 1024:  # < 100MB
                return "large"
            else:
                return "very_large"
```

**Required Performance Trace Points**:
- [ ] **Method Execution Time**: All public methods and critical internal methods
- [ ] **Resource Allocation**: Memory allocation, connection creation
- [ ] **I/O Operations**: File reads/writes, network requests
- [ ] **CPU-Intensive Operations**: Complex calculations, data processing
- [ ] **Bottleneck Points**: Known or suspected performance bottlenecks

### **4. Data Flow Tracing**
**Purpose**: Track data transformation and flow through the system

**Requirements**:
- **Data Transformation**: How data changes as it flows through components
- **Request/Response Flow**: Complete request lifecycle
- **State Management**: How state changes affect data flow
- **Inter-Component Communication**: Data passing between components

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/data_flow_tracing.py
from langswarm.v2.core.observability import get_tracer
from typing import Any, Dict
import json
import hashlib

class DataFlowTracer:
    """Specialized tracer for data flow and transformations"""
    
    def __init__(self):
        self.tracer = get_tracer("data_flow")
    
    def trace_data_input(self, operation: str, data: Any, component: str = None):
        """Trace data input to an operation"""
        with self.tracer.trace_operation(
            component=component or "unknown",
            operation=f"{operation}_input",
            description=f"Data input for {operation}"
        ) as span:
            self._add_data_metadata(span, data, "input")
    
    def trace_data_output(self, operation: str, data: Any, component: str = None):
        """Trace data output from an operation"""
        with self.tracer.trace_operation(
            component=component or "unknown",
            operation=f"{operation}_output",
            description=f"Data output for {operation}"
        ) as span:
            self._add_data_metadata(span, data, "output")
    
    def trace_data_transformation(self, operation: str, input_data: Any, output_data: Any, component: str = None):
        """Trace data transformation"""
        with self.tracer.trace_operation(
            component=component or "unknown",
            operation=f"{operation}_transform",
            description=f"Data transformation for {operation}"
        ) as span:
            self._add_data_metadata(span, input_data, "input")
            self._add_data_metadata(span, output_data, "output")
            
            # Calculate transformation metrics
            input_size = self._calculate_data_size(input_data)
            output_size = self._calculate_data_size(output_data)
            span.set_tag("size_change_bytes", output_size - input_size)
            span.set_tag("size_change_ratio", output_size / input_size if input_size > 0 else 0)
    
    def _add_data_metadata(self, span, data: Any, data_type: str):
        """Add data metadata to trace span"""
        prefix = f"{data_type}_"
        
        # Basic type information
        span.set_tag(f"{prefix}type", type(data).__name__)
        span.set_tag(f"{prefix}size_bytes", self._calculate_data_size(data))
        
        # Content-specific metadata
        if isinstance(data, (dict, list)):
            span.set_tag(f"{prefix}length", len(data))
            if isinstance(data, dict):
                span.set_tag(f"{prefix}keys", list(data.keys()) if len(data) < 10 else f"{len(data)} keys")
        elif isinstance(data, str):
            span.set_tag(f"{prefix}length", len(data))
            span.set_tag(f"{prefix}preview", data[:100] if len(data) > 100 else data)
        
        # Data fingerprint for change detection
        span.set_tag(f"{prefix}fingerprint", self._calculate_fingerprint(data))
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calculate approximate size of data in bytes"""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except:
            return 0
    
    def _calculate_fingerprint(self, data: Any) -> str:
        """Calculate fingerprint of data for change detection"""
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True, default=str)
            else:
                data_str = str(data)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:8]
        except:
            return "unknown"
```

**Required Data Flow Trace Points**:
- [ ] **Input Validation**: Data entering the system
- [ ] **Data Transformation**: Any data processing or modification
- [ ] **Inter-Component Data**: Data passed between components
- [ ] **Output Generation**: Final data leaving the system
- [ ] **State Changes**: Data changes that affect component state

---

## 🔧 **Tracing Infrastructure**

### **Core Tracing System**
```python
# langswarm/v2/core/observability/__init__.py
from .tracer import DebugTracer, get_tracer
from .context import TraceContext, get_current_context
from .span import TraceSpan
from .config import TracingConfig

__all__ = [
    'get_tracer',
    'TraceContext',
    'get_current_context',
    'TraceSpan',
    'TracingConfig'
]

# Global tracer configuration
_tracing_enabled = False
_trace_output_file = None

def enable_tracing(output_file: str = None, config: TracingConfig = None):
    """Enable tracing with optional configuration"""
    global _tracing_enabled, _trace_output_file
    _tracing_enabled = True
    _trace_output_file = output_file
    
def disable_tracing():
    """Disable tracing"""
    global _tracing_enabled
    _tracing_enabled = False

def is_tracing_enabled() -> bool:
    """Check if tracing is enabled"""
    return _tracing_enabled
```

### **Tracing Configuration**
```python
# langswarm/v2/core/observability/config.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class TracingConfig:
    """Configuration for tracing system"""
    
    # Output configuration
    output_file: Optional[str] = None
    output_format: str = "jsonl"  # jsonl, json, text
    
    # Filtering configuration
    enabled_components: List[str] = None  # None = all components
    disabled_components: List[str] = None
    min_duration_ms: float = 0.0  # Minimum duration to trace
    
    # Performance configuration
    max_trace_size: int = 10000  # Maximum traces in memory
    flush_interval: int = 100  # Flush every N traces
    
    # Context configuration
    include_stack_trace: bool = False
    include_environment: bool = False
    include_thread_info: bool = False
    
    # Debug configuration
    debug_mode: bool = False
    verbose_errors: bool = False
```

---

## 📊 **Trace Data Format**

### **Structured Trace Event**
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "trace_id": "abc123def456",
  "span_id": "def456ghi789",
  "parent_span_id": "789abc123def",
  "component": "error_system",
  "operation": "error_handling",
  "description": "Handling configuration error",
  "duration_ms": 12.5,
  "tags": {
    "error_type": "ConfigurationError",
    "error_message": "Invalid configuration format",
    "component_state": "initialized",
    "severity": "error",
    "recovery_attempted": true
  },
  "metadata": {
    "thread_id": "12345",
    "process_id": "67890",
    "memory_usage": 156789,
    "cpu_usage": 23.5
  }
}
```

### **Trace Analysis Tools**
```python
# langswarm/v2/core/observability/analysis.py
class TraceAnalyzer:
    """Tools for analyzing trace data"""
    
    def analyze_performance_bottlenecks(self, traces: List[Dict]) -> Dict[str, Any]:
        """Identify performance bottlenecks from traces"""
        pass
    
    def analyze_error_patterns(self, traces: List[Dict]) -> Dict[str, Any]:
        """Identify common error patterns"""
        pass
    
    def generate_component_report(self, component: str, traces: List[Dict]) -> Dict[str, Any]:
        """Generate component-specific analysis report"""
        pass
```

---

## 📋 **Tracing Checklist for Each Task**

### **Before Implementation**
- [ ] Tracing plan created for all component interactions
- [ ] Performance baseline established for comparison
- [ ] Trace data format defined for component
- [ ] Tracing infrastructure set up and tested

### **During Implementation**
- [ ] Component tracing added to all public methods
- [ ] Error tracing added to all error handling paths
- [ ] Performance tracing added to critical operations
- [ ] Data flow tracing added to data transformations

### **After Implementation**
- [ ] All trace points tested and validated
- [ ] Trace data analysis performed
- [ ] Performance impact measured and acceptable
- [ ] Tracing documentation updated

### **Before Task Completion**
- [ ] Tracing integration verified with observability system
- [ ] Trace data useful for debugging confirmed
- [ ] Performance overhead within acceptable limits
- [ ] Tracing lessons documented for future tasks

---

**Tracing is essential for understanding and debugging V2 system behavior!**
