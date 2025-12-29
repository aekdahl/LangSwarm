#!/usr/bin/env python3
"""
Debug Tools Tracing System

Enhanced tracing system specifically for debug tools testing with
comprehensive event tracking, hierarchical spans, and structured logging.
"""

import json
import time
import uuid
import threading
import inspect
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field


@dataclass
class TraceEvent:
    """Single trace event with comprehensive contextual information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    timestamp: str
    event_type: str  # START, END, INFO, ERROR, TOOL_CALL, AGENT_RESPONSE, etc.
    component: str   # tool, agent, workflow, cli, etc.
    operation: str   # search, query, execute, analyze, etc.
    level: str      # DEBUG, INFO, WARN, ERROR
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_function: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class DebugToolsTracer:
    """
    Enhanced tracer for debug tools testing with hierarchical spans
    and comprehensive event tracking.
    """
    
    def __init__(self, output_file: Optional[str] = None, enabled: bool = True):
        """
        Initialize tracer
        
        Args:
            output_file: File path for trace output (JSONL format)
            enabled: Whether tracing is enabled
        """
        self.enabled = enabled
        self.output_file = output_file
        self._lock = threading.Lock()
        self._span_stack = threading.local()
        self._active_spans: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self._event_count = 0
        self._start_time = time.time()
        
        if self.enabled and output_file:
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Write session start event
            self._write_session_start()
    
    def _get_span_stack(self) -> List[str]:
        """Get span stack for current thread"""
        if not hasattr(self._span_stack, 'spans'):
            self._span_stack.spans = []
        return self._span_stack.spans
    
    def _write_event(self, event: TraceEvent):
        """Write event to output file"""
        if not self.enabled or not self.output_file:
            return
        
        try:
            with open(self.output_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
                f.flush()
        except Exception as e:
            # Avoid recursive tracing errors
            print(f"Warning: Failed to write trace event: {e}")
    
    def _write_session_start(self):
        """Write session start event"""
        event = TraceEvent(
            trace_id="session",
            span_id="session_start",
            parent_span_id=None,
            timestamp=datetime.now().isoformat(),
            event_type="SESSION_START",
            component="tracer",
            operation="initialize",
            level="INFO",
            message="Debug tools tracing session started",
            data={
                "output_file": self.output_file,
                "pid": os.getpid() if 'os' in globals() else None,
                "thread_id": threading.get_ident()
            }
        )
        self._write_event(event)
    
    def _get_caller_info(self, skip_frames: int = 2) -> Dict[str, Optional[str]]:
        """Get information about the calling code"""
        try:
            frame = inspect.currentframe()
            for _ in range(skip_frames):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame:
                return {
                    "source_file": frame.f_code.co_filename,
                    "source_line": frame.f_lineno,
                    "source_function": frame.f_code.co_name
                }
        except Exception:
            pass
        
        return {
            "source_file": None,
            "source_line": None,
            "source_function": None
        }
    
    @contextmanager
    def trace_span(self, component: str, operation: str, message: str, 
                   trace_id: Optional[str] = None, **data):
        """
        Create a traced span with automatic START/END events
        
        Args:
            component: Component name (e.g., 'tool', 'agent', 'workflow')
            operation: Operation name (e.g., 'search', 'query', 'execute')
            message: Human-readable message
            trace_id: Optional trace ID (auto-generated if not provided)
            **data: Additional data to include in trace events
        """
        if not self.enabled:
            yield None
            return
        
        # Generate IDs
        span_id = str(uuid.uuid4())
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        # Get parent span
        span_stack = self._get_span_stack()
        parent_span_id = span_stack[-1] if span_stack else None
        
        # Get caller info
        caller_info = self._get_caller_info()
        
        # Record span start
        start_time = time.time()
        start_event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            timestamp=datetime.now().isoformat(),
            event_type="SPAN_START",
            component=component,
            operation=operation,
            level="INFO",
            message=f"Started {operation}",
            data=data,
            **caller_info
        )
        
        self._write_event(start_event)
        
        # Push span to stack
        span_stack.append(span_id)
        
        # Store span info
        with self._lock:
            self._active_spans[span_id] = {
                "trace_id": trace_id,
                "component": component,
                "operation": operation,
                "start_time": start_time,
                "data": data
            }
        
        try:
            yield {
                "trace_id": trace_id,
                "span_id": span_id,
                "tracer": self
            }
        except Exception as e:
            # Record error event
            error_event = TraceEvent(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                timestamp=datetime.now().isoformat(),
                event_type="ERROR",
                component=component,
                operation=operation,
                level="ERROR",
                message=f"Error in {operation}: {e}",
                data={
                    **data,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                **caller_info
            )
            self._write_event(error_event)
            raise
        finally:
            # Pop span from stack
            if span_stack and span_stack[-1] == span_id:
                span_stack.pop()
            
            # Calculate duration
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Record span end
            end_event = TraceEvent(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                timestamp=datetime.now().isoformat(),
                event_type="SPAN_END",
                component=component,
                operation=operation,
                level="INFO",
                message=f"Completed {operation}",
                data=data,
                duration_ms=duration_ms,
                **caller_info
            )
            
            self._write_event(end_event)
            
            # Remove from active spans
            with self._lock:
                self._active_spans.pop(span_id, None)
    
    def trace_event(self, event_type: str, component: str, operation: str,
                   message: str, level: str = "INFO", **data):
        """
        Record a single trace event
        
        Args:
            event_type: Type of event (INFO, TOOL_CALL, AGENT_RESPONSE, etc.)
            component: Component name
            operation: Operation name
            message: Human-readable message
            level: Log level (DEBUG, INFO, WARN, ERROR)
            **data: Additional data to include
        """
        if not self.enabled:
            return
        
        # Get current span context
        span_stack = self._get_span_stack()
        span_id = span_stack[-1] if span_stack else str(uuid.uuid4())
        parent_span_id = span_stack[-2] if len(span_stack) > 1 else None
        
        # Get trace ID from active span or generate new one
        trace_id = None
        if span_stack:
            with self._lock:
                span_info = self._active_spans.get(span_stack[-1])
                if span_info:
                    trace_id = span_info["trace_id"]
        
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        # Get caller info
        caller_info = self._get_caller_info()
        
        # Create and write event
        event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            component=component,
            operation=operation,
            level=level,
            message=message,
            data=data,
            **caller_info
        )
        
        self._write_event(event)
        self._event_count += 1
    
    def trace_tool_call(self, tool_name: str, method: str, params: Dict[str, Any],
                       result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """
        Trace a tool call with parameters and results
        
        Args:
            tool_name: Name of the tool
            method: Method being called
            params: Parameters passed to the tool
            result: Result from the tool (if successful)
            error: Error message (if failed)
        """
        event_type = "TOOL_CALL_SUCCESS" if error is None else "TOOL_CALL_ERROR"
        level = "INFO" if error is None else "ERROR"
        
        data = {
            "tool_name": tool_name,
            "method": method,
            "params": params
        }
        
        if result is not None:
            data["result"] = result
        if error is not None:
            data["error"] = error
        
        message = f"Tool call: {tool_name}.{method}"
        if error:
            message += f" (failed: {error})"
        
        self.trace_event(event_type, "tool", method, message, level, **data)
    
    def trace_agent_response(self, agent_id: str, input_text: str, 
                           response: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Trace an agent response
        
        Args:
            agent_id: ID of the agent
            input_text: Input provided to the agent
            response: Response from the agent
            metadata: Additional metadata about the response
        """
        data = {
            "agent_id": agent_id,
            "input_text": input_text,
            "response": response,
            "response_length": len(response)
        }
        
        if metadata:
            data["metadata"] = metadata
        
        self.trace_event(
            "AGENT_RESPONSE", "agent", "chat",
            f"Agent {agent_id} responded ({len(response)} chars)",
            "INFO", **data
        )
    
    def trace_workflow_step(self, workflow_id: str, step_id: str, step_type: str,
                          input_data: Any, output_data: Any = None, error: Optional[str] = None):
        """
        Trace a workflow step execution
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the step
            step_type: Type of step (agent, tool, condition, etc.)
            input_data: Input data for the step
            output_data: Output data from the step
            error: Error message if step failed
        """
        event_type = "WORKFLOW_STEP_SUCCESS" if error is None else "WORKFLOW_STEP_ERROR"
        level = "INFO" if error is None else "ERROR"
        
        data = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "step_type": step_type,
            "input_data": input_data
        }
        
        if output_data is not None:
            data["output_data"] = output_data
        if error is not None:
            data["error"] = error
        
        message = f"Workflow step: {workflow_id}.{step_id}"
        if error:
            message += f" (failed: {error})"
        
        self.trace_event(event_type, "workflow", "execute_step", message, level, **data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        current_time = time.time()
        session_duration = current_time - self._start_time
        
        return {
            "enabled": self.enabled,
            "output_file": self.output_file,
            "event_count": self._event_count,
            "session_duration_seconds": session_duration,
            "events_per_second": self._event_count / session_duration if session_duration > 0 else 0,
            "active_spans": len(self._active_spans),
            "current_thread_span_depth": len(self._get_span_stack())
        }
    
    def flush(self):
        """Flush any pending trace data"""
        if self.enabled and self.output_file:
            # Write session end event
            event = TraceEvent(
                trace_id="session",
                span_id="session_end",
                parent_span_id=None,
                timestamp=datetime.now().isoformat(),
                event_type="SESSION_END",
                component="tracer",
                operation="finalize",
                level="INFO",
                message="Debug tools tracing session ended",
                data=self.get_stats()
            )
            self._write_event(event)


# Global tracer instance
_global_tracer: Optional[DebugToolsTracer] = None


def get_tracer() -> Optional[DebugToolsTracer]:
    """Get the global tracer instance"""
    return _global_tracer


def enable_tracing(output_file: str) -> DebugToolsTracer:
    """
    Enable global tracing with output to specified file
    
    Args:
        output_file: Path to output file for traces
        
    Returns:
        The global tracer instance
    """
    global _global_tracer
    _global_tracer = DebugToolsTracer(output_file, enabled=True)
    return _global_tracer


def disable_tracing():
    """Disable global tracing"""
    global _global_tracer
    if _global_tracer:
        _global_tracer.flush()
        _global_tracer.enabled = False
    _global_tracer = None


# Convenience functions for common tracing operations
def trace_span(component: str, operation: str, message: str, **data):
    """Convenience function for tracing spans"""
    tracer = get_tracer()
    if tracer:
        return tracer.trace_span(component, operation, message, **data)
    else:
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()


def trace_event(event_type: str, component: str, operation: str, message: str, **data):
    """Convenience function for tracing events"""
    tracer = get_tracer()
    if tracer:
        tracer.trace_event(event_type, component, operation, message, **data)


def trace_tool_call(tool_name: str, method: str, params: Dict[str, Any], **kwargs):
    """Convenience function for tracing tool calls"""
    tracer = get_tracer()
    if tracer:
        tracer.trace_tool_call(tool_name, method, params, **kwargs)


def trace_agent_response(agent_id: str, input_text: str, response: str, **kwargs):
    """Convenience function for tracing agent responses"""
    tracer = get_tracer()
    if tracer:
        tracer.trace_agent_response(agent_id, input_text, response, **kwargs)


# Import os for PID tracking
import os
