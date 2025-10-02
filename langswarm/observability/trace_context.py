"""
Trace Context for V2 Debug System

Provides correlation IDs and hierarchical span tracking for complete request tracing.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class EventLevel(Enum):
    """Trace event levels"""
    USER_INTERACTION = "USER_INTERACTION"
    AGENT_PROCESSING = "AGENT_PROCESSING"
    MIDDLEWARE = "MIDDLEWARE"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    WORKFLOW = "WORKFLOW"
    ERROR = "ERROR"
    PERFORMANCE = "PERFORMANCE"


@dataclass
class TraceEvent:
    """Individual trace event"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    timestamp: datetime
    level: EventLevel
    event: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "event": self.event,
            "data": self.data,
            "duration_ms": self.duration_ms
        }


@dataclass
class TraceContext:
    """Trace context for correlation and hierarchical tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _start_time: float = field(default_factory=time.time)
    _events: List[TraceEvent] = field(default_factory=list)
    
    @classmethod
    def create_new(cls, user_id: Optional[str] = None, session_id: Optional[str] = None) -> 'TraceContext':
        """Create a new root trace context"""
        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id
        )
    
    def create_child_span(self, name: str) -> 'TraceContext':
        """Create child span for nested operations"""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            user_id=self.user_id,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
            metadata={**self.metadata, "span_name": name}
        )
    
    def log_event(self, level: EventLevel, event: str, data: Dict[str, Any]) -> TraceEvent:
        """Log a trace event"""
        trace_event = TraceEvent(
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            timestamp=datetime.now(),
            level=level,
            event=event,
            data={**data, **self.metadata}
        )
        
        self._events.append(trace_event)
        return trace_event
    
    def complete_span(self) -> float:
        """Complete the span and return duration"""
        duration_ms = (time.time() - self._start_time) * 1000
        
        # Add completion event
        self.log_event(
            EventLevel.PERFORMANCE,
            "span_completed",
            {
                "span_name": self.metadata.get("span_name", "unknown"),
                "duration_ms": duration_ms
            }
        )
        
        return duration_ms
    
    def get_all_events(self) -> List[TraceEvent]:
        """Get all events from this context"""
        return self._events.copy()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the trace context"""
        self.metadata[key] = value


class TraceManager:
    """Global trace manager for collecting and correlating events"""
    
    def __init__(self):
        self._active_traces: Dict[str, TraceContext] = {}
        self._all_events: List[TraceEvent] = []
    
    def register_trace(self, trace_context: TraceContext) -> None:
        """Register a trace context"""
        self._active_traces[trace_context.trace_id] = trace_context
    
    def add_event(self, event: TraceEvent) -> None:
        """Add event to global collection"""
        self._all_events.append(event)
    
    def get_trace_events(self, trace_id: str) -> List[TraceEvent]:
        """Get all events for a specific trace"""
        return [event for event in self._all_events if event.trace_id == trace_id]
    
    def get_all_events(self) -> List[TraceEvent]:
        """Get all events"""
        return self._all_events.copy()
    
    def clear(self) -> None:
        """Clear all traces and events"""
        self._active_traces.clear()
        self._all_events.clear()


# Global trace manager instance
_trace_manager = TraceManager()


def get_trace_manager() -> TraceManager:
    """Get the global trace manager"""
    return _trace_manager

