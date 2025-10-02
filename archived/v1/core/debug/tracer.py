"""
LangSwarm Debug and Tracing System

This module provides comprehensive debug and tracing capabilities for LangSwarm.
It creates structured, step-by-step logs that can be used for:
1. Debugging issues and understanding execution flow
2. Story-telling - explaining what agents are doing

Key Features:
- Hierarchical tracing with trace_id/span_id for nested operations
- JSON-structured logs for easy parsing and analysis
- File-based output with configurable paths
- Minimal performance impact when disabled
- Integration with existing agent and workflow systems
"""

import json
import time
import uuid
import threading
import inspect
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field


@dataclass
class TraceEvent:
    """Single trace event with all contextual information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    timestamp: str
    event_type: str  # START, END, INFO, ERROR, TOOL_CALL, AGENT_RESPONSE, etc.
    component: str   # agent, workflow, tool, middleware, etc.
    operation: str   # chat, execute_step, tool_call, etc.
    level: str      # DEBUG, INFO, WARN, ERROR
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    source_file: Optional[str] = None      # File where log was generated
    source_line: Optional[int] = None      # Line number where log was generated
    source_function: Optional[str] = None  # Function where log was generated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class DebugTracer:
    """
    Main debug tracer class that handles structured logging and tracing.
    
    Design principles:
    - Thread-safe for concurrent operations
    - Hierarchical spans for nested operations
    - Configurable output with minimal overhead when disabled
    - Rich context capture for debugging and story-telling
    """
    
    def __init__(self, enabled: bool = False, output_file: Optional[str] = None):
        self.enabled = enabled
        self.output_file = output_file or "langswarm_debug.jsonl"
        self.events: List[TraceEvent] = []
        self.current_spans: Dict[str, str] = {}  # thread_id -> current_span_id
        self.span_stack: Dict[str, List[str]] = {}  # thread_id -> span_stack
        self.lock = threading.Lock()
        
        # Ensure output directory exists
        if self.enabled:
            Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_thread_id(self) -> str:
        """Get current thread identifier"""
        return str(threading.current_thread().ident)
    
    def _generate_ids(self) -> tuple[str, str]:
        """Generate trace_id and span_id"""
        return str(uuid.uuid4()), str(uuid.uuid4())
    
    def _get_caller_info(self, skip_frames: int = 2) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """Get information about where the log call originated, skipping debug infrastructure"""
        try:
            # Get the current frame and walk up the stack
            frame = inspect.currentframe()
            
            # First, skip the basic frames (this method, log_event)
            for _ in range(skip_frames):
                frame = frame.f_back
                if frame is None:
                    return None, None, None
            
            # Now look for the first frame that's NOT in debug infrastructure
            # This helps us find the actual LangSwarm component that triggered the event
            original_frame = frame
            attempts = 0
            max_attempts = 20  # Prevent infinite loops
            
            while frame is not None and attempts < max_attempts:
                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                
                # Skip frames from our debug infrastructure
                skip_files = ['debug_cases.py', 'tracer.py', 'integration.py', 'cli.py']
                if any(skip_file in filename for skip_file in skip_files):
                    frame = frame.f_back
                    attempts += 1
                    continue
                    
                # Also skip generic wrapper functions that don't add much value
                skip_functions = ['run', 'execute', '__call__', 'wrapper', '__enter__', '__exit__']
                if function_name in skip_functions:
                    frame = frame.f_back
                    attempts += 1
                    continue
                
                # Found a meaningful frame, process and return it
                break
                
            # If we couldn't find a good frame, fall back to the original
            if frame is None or attempts >= max_attempts:
                frame = original_frame
            
            # Extract file, line, and function information
            filename = frame.f_code.co_filename
            line_number = frame.f_lineno
            function_name = frame.f_code.co_name
            
            # Make filename relative to project root for readability
            try:
                # Try to make path relative to current working directory
                filename = str(Path(filename).relative_to(Path.cwd()))
            except ValueError:
                # If that fails, just use the basename
                filename = Path(filename).name
            
            return filename, line_number, function_name
            
        except Exception:
            # If anything goes wrong, just return None values
            return None, None, None
    
    def _get_current_span(self) -> Optional[str]:
        """Get current span for this thread"""
        thread_id = self._get_thread_id()
        return self.current_spans.get(thread_id)
    
    def _set_current_span(self, span_id: str):
        """Set current span for this thread"""
        thread_id = self._get_thread_id()
        self.current_spans[thread_id] = span_id
        
        # Initialize span stack if needed
        if thread_id not in self.span_stack:
            self.span_stack[thread_id] = []
        
        self.span_stack[thread_id].append(span_id)
    
    def _pop_current_span(self):
        """Pop current span and restore parent"""
        thread_id = self._get_thread_id()
        if thread_id in self.span_stack and self.span_stack[thread_id]:
            self.span_stack[thread_id].pop()
            # Set current span to parent (if exists)
            if self.span_stack[thread_id]:
                self.current_spans[thread_id] = self.span_stack[thread_id][-1]
            else:
                self.current_spans.pop(thread_id, None)
    
    def log_event(
        self,
        event_type: str,
        component: str,
        operation: str,
        message: str,
        level: str = "INFO",
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a single trace event"""
        if not self.enabled:
            return
        
        # Use provided IDs or generate new ones
        if not trace_id or not span_id:
            current_span = self._get_current_span()
            if current_span:
                trace_id = trace_id or self._find_trace_id_for_span(current_span)
                span_id = span_id or current_span
            else:
                new_trace_id, new_span_id = self._generate_ids()
                trace_id = trace_id or new_trace_id
                span_id = span_id or new_span_id
        
        # Find parent span
        thread_id = self._get_thread_id()
        parent_span_id = None
        if thread_id in self.span_stack and len(self.span_stack[thread_id]) > 1:
            parent_span_id = self.span_stack[thread_id][-2]
        
        # Get caller information
        source_file, source_line, source_function = self._get_caller_info(skip_frames=3)
        
        event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            component=component,
            operation=operation,
            level=level,
            message=message,
            data=data or {},
            duration_ms=duration_ms,
            source_file=source_file,
            source_line=source_line,
            source_function=source_function
        )
        
        with self.lock:
            self.events.append(event)
            # Write immediately to file for real-time debugging
            self._write_event_to_file(event)
    
    def _find_trace_id_for_span(self, span_id: str) -> Optional[str]:
        """Find trace_id for a given span_id"""
        for event in reversed(self.events):
            if event.span_id == span_id:
                return event.trace_id
        return None
    
    def _write_event_to_file(self, event: TraceEvent):
        """Write single event to file"""
        try:
            with open(self.output_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            print(f"Failed to write trace event: {e}")
    
    @contextmanager
    def trace_operation(
        self,
        component: str,
        operation: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        """
        Context manager for tracing operations with automatic START/END events
        
        Usage:
        with tracer.trace_operation("agent", "chat", "Processing user query"):
            # Your operation here
            pass
        """
        if not self.enabled:
            yield None
            return
        
        # Generate IDs
        if not trace_id:
            trace_id, span_id = self._generate_ids()
        else:
            span_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        # Set current span
        self._set_current_span(span_id)
        
        # Log START event
        self.log_event(
            event_type="START",
            component=component,
            operation=operation,
            message=f"Starting {operation}: {message}",
            data=data,
            trace_id=trace_id,
            span_id=span_id
        )
        
        try:
            yield {"trace_id": trace_id, "span_id": span_id}
        except Exception as e:
            # Log ERROR event
            self.log_event(
                event_type="ERROR",
                component=component,
                operation=operation,
                message=f"Error in {operation}: {str(e)}",
                level="ERROR",
                data={"error": str(e), "error_type": type(e).__name__},
                trace_id=trace_id,
                span_id=span_id
            )
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log END event
            self.log_event(
                event_type="END",
                component=component,
                operation=operation,
                message=f"Completed {operation}",
                data={"duration_ms": duration_ms},
                trace_id=trace_id,
                span_id=span_id,
                duration_ms=duration_ms
            )
            
            # Pop current span
            self._pop_current_span()
    
    def trace_agent_query(self, agent_name: str, query: str, trace_id: Optional[str] = None):
        """Convenience method for tracing agent queries"""
        return self.trace_operation(
            component="agent",
            operation="chat",
            message=f"Agent {agent_name} processing query",
            data={"agent_name": agent_name, "query": query},
            trace_id=trace_id
        )
    
    def trace_workflow_step(self, workflow_id: str, step_id: str, step_data: Dict[str, Any], trace_id: Optional[str] = None):
        """Convenience method for tracing workflow steps"""
        return self.trace_operation(
            component="workflow",
            operation="execute_step",
            message=f"Executing step {step_id} in workflow {workflow_id}",
            data={"workflow_id": workflow_id, "step_id": step_id, "step_data": step_data},
            trace_id=trace_id
        )
    
    def trace_tool_call(self, tool_name: str, method: str, params: Dict[str, Any], trace_id: Optional[str] = None):
        """Convenience method for tracing tool calls"""
        return self.trace_operation(
            component="tool",
            operation="call",
            message=f"Calling tool {tool_name}.{method}",
            data={"tool_name": tool_name, "method": method, "params": params},
            trace_id=trace_id
        )
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary statistics for a specific trace"""
        trace_events = [e for e in self.events if e.trace_id == trace_id]
        
        if not trace_events:
            return {"error": "Trace not found"}
        
        # Calculate total duration
        start_events = [e for e in trace_events if e.event_type == "START"]
        end_events = [e for e in trace_events if e.event_type == "END"]
        
        total_duration = 0
        if start_events and end_events:
            start_time = min(e.timestamp for e in start_events)
            end_time = max(e.timestamp for e in end_events)
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            total_duration = (end_dt - start_dt).total_seconds() * 1000
        
        # Count events by type
        event_counts = {}
        for event in trace_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Find errors
        errors = [e for e in trace_events if e.level == "ERROR"]
        
        return {
            "trace_id": trace_id,
            "total_events": len(trace_events),
            "total_duration_ms": total_duration,
            "event_counts": event_counts,
            "errors": len(errors),
            "components": list(set(e.component for e in trace_events)),
            "operations": list(set(e.operation for e in trace_events))
        }
    
    def clear_events(self):
        """Clear all stored events (useful for testing)"""
        with self.lock:
            self.events.clear()
            self.current_spans.clear()
            self.span_stack.clear()
    
    def export_trace(self, trace_id: str, output_file: str):
        """Export specific trace to a separate file"""
        trace_events = [e for e in self.events if e.trace_id == trace_id]
        
        with open(output_file, 'w') as f:
            for event in trace_events:
                f.write(json.dumps(event.to_dict()) + '\n')


# Global tracer instance
_global_tracer: Optional[DebugTracer] = None


def initialize_debug_tracer(enabled: bool = False, output_file: Optional[str] = None) -> DebugTracer:
    """Initialize the global debug tracer"""
    global _global_tracer
    _global_tracer = DebugTracer(enabled=enabled, output_file=output_file)
    return _global_tracer


def get_debug_tracer() -> Optional[DebugTracer]:
    """Get the global debug tracer instance"""
    return _global_tracer


def trace_event(
    event_type: str,
    component: str,
    operation: str,
    message: str,
    level: str = "INFO",
    data: Optional[Dict[str, Any]] = None
):
    """Convenience function to log trace event using global tracer"""
    if _global_tracer:
        _global_tracer.log_event(event_type, component, operation, message, level, data)


def trace_operation(component: str, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
    """Convenience function to trace operation using global tracer"""
    if _global_tracer:
        return _global_tracer.trace_operation(component, operation, message, data)
    else:
        # Return a no-op context manager if tracer is not initialized
        from contextlib import nullcontext
        return nullcontext()


# Decorator for automatic tracing
def traced(component: str, operation: str = None):
    """
    Decorator to automatically trace function calls
    
    Usage:
    @traced("agent", "chat")
    def chat_method(self, query):
        return self._call_agent(query)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            message = f"Calling {func.__name__}"
            
            # Try to extract meaningful context
            data = {}
            if args:
                # If first arg looks like self, get class name
                if hasattr(args[0], '__class__'):
                    data["class"] = args[0].__class__.__name__
                    if hasattr(args[0], 'name'):
                        data["instance_name"] = args[0].name
            
            with trace_operation(component, op_name, message, data):
                return func(*args, **kwargs)
        return wrapper
    return decorator
