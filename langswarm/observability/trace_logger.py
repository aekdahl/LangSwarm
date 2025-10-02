"""
Trace Logger for V2 Debug System

Provides structured logging for different components with configurable output formats.
"""

import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, TextIO
from datetime import datetime

from .trace_context import TraceContext, TraceEvent, EventLevel, get_trace_manager
from .formatters import ConsoleFormatter, JSONLFormatter, PerformanceFormatter


class TraceLevel(Enum):
    """Trace detail levels"""
    SUMMARY = "summary"          # Production default - key events only
    STANDARD = "standard"        # Development default - detailed but focused
    DETAILED = "detailed"        # Full payloads and performance metrics  
    VERBOSE = "verbose"          # Deep debugging with all internal operations


class TraceLogger:
    """Main trace logger for V2 system"""
    
    def __init__(self, 
                 level: TraceLevel = TraceLevel.STANDARD,
                 output_format: str = "console",
                 output_file: Optional[str] = None,
                 auto_file: bool = True):
        self.level = level
        self.output_format = output_format
        self.output_file = output_file
        self.trace_manager = get_trace_manager()
        self.file_handle: Optional[TextIO] = None
        
        # Auto-generate trace file if not specified
        if auto_file and not output_file:
            # Find the correct traces directory
            current_dir = Path.cwd()
            if current_dir.name == "debug":
                # We're already in the debug directory
                trace_dir = current_dir / "traces"
            else:
                # We're in the project root or elsewhere
                trace_dir = current_dir / "debug" / "traces"
            
            trace_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = str(trace_dir / f"trace_{timestamp}.jsonl")
        
        # Initialize formatters
        self.console_formatter = ConsoleFormatter()
        self.jsonl_formatter = JSONLFormatter()
        self.performance_formatter = PerformanceFormatter()
        
        # Open file if specified
        if self.output_file:
            self.file_handle = open(self.output_file, 'w')
            print(f"📁 Trace file: {self.output_file}")
    
    def __del__(self):
        if self.file_handle:
            self.file_handle.close()
        
    def _should_log_event(self, event_level: EventLevel, event_type: str) -> bool:
        """Determine if event should be logged based on trace level"""
        if self.level == TraceLevel.SUMMARY:
            return event_level in [EventLevel.USER_INTERACTION, EventLevel.ERROR] or \
                   event_type in ["query_received", "response_delivered", "tool_completed", "error_occurred"]
        elif self.level == TraceLevel.STANDARD:
            return event_level in [EventLevel.USER_INTERACTION, EventLevel.AGENT_PROCESSING, 
                                 EventLevel.TOOL_EXECUTION, EventLevel.ERROR]
        elif self.level == TraceLevel.DETAILED:
            return True  # Log everything except verbose internals
        else:  # VERBOSE
            return True  # Log absolutely everything
    
    def _log_event(self, trace_context: TraceContext, level: EventLevel, event: str, data: Dict[str, Any]) -> None:
        """Internal method to log an event"""
        if not self._should_log_event(level, event):
            return
            
        # Create and register the event
        trace_event = trace_context.log_event(level, event, data)
        self.trace_manager.add_event(trace_event)
        
        # Output the event immediately
        self._output_event(trace_event)
    
    def _output_event(self, event: TraceEvent) -> None:
        """Output a single event"""
        if self.output_format == "console":
            output = self.console_formatter.format_event(event)
            print(output)
        elif self.output_format == "jsonl":
            output = self.jsonl_formatter.format_event(event)
            print(output)
        
        # Always write to file if available (in JSONL format for analysis)
        if self.file_handle:
            jsonl_formatted = self.jsonl_formatter.format_event(event)
            self.file_handle.write(jsonl_formatted + '\n')
            self.file_handle.flush()
        elif self.output_format == "both":
            console_output = self.console_formatter.format_event(event)
            jsonl_output = self.jsonl_formatter.format_event(event)
            print(console_output)
            if self.output_file:
                with open(self.output_file, 'a') as f:
                    f.write(jsonl_output + '\n')
    
    # User Interaction Events
    def log_user_query(self, trace_context: TraceContext, query: str, context: Optional[Dict] = None) -> None:
        """Log initial user query"""
        self._log_event(trace_context, EventLevel.USER_INTERACTION, "query_received", {
            "query": query,
            "user_id": trace_context.user_id,
            "session_id": trace_context.session_id,
            "context": context or {}
        })
    
    def log_final_response(self, trace_context: TraceContext, response: str, metadata: Optional[Dict] = None) -> None:
        """Log final response to user"""
        duration_ms = trace_context.complete_span()
        self._log_event(trace_context, EventLevel.USER_INTERACTION, "response_delivered", {
            "response": response,
            "total_duration_ms": duration_ms,
            "metadata": metadata or {}
        })
    
    # Agent Processing Events
    def log_agent_invocation(self, trace_context: TraceContext, agent_config: Dict[str, Any]) -> None:
        """Log agent being invoked"""
        self._log_event(trace_context, EventLevel.AGENT_PROCESSING, "agent_invoked", {
            "agent_name": agent_config.get("name", "unknown"),
            "provider": agent_config.get("provider", "unknown"),
            "model": agent_config.get("model", "unknown"),
            "tools_available": agent_config.get("tools_available", []),
            "configuration": {
                k: v for k, v in agent_config.items() 
                if k not in ["name", "provider", "model", "tools_available"]
            }
        })
    
    def log_llm_request(self, trace_context: TraceContext, request: Dict[str, Any]) -> None:
        """Log LLM request (prompt, messages, etc.)"""
        self._log_event(trace_context, EventLevel.AGENT_PROCESSING, "llm_request", {
            "model": request.get("model", "unknown"),
            "messages": request.get("messages", []) if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None,
            "message_count": len(request.get("messages", [])),
            "tools": request.get("tools", []) if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None,
            "tool_count": len(request.get("tools", [])),
            "temperature": request.get("temperature"),
            "max_tokens": request.get("max_tokens"),
            "system_prompt_length": len(request.get("system_prompt", ""))
        })
    
    def log_llm_response(self, trace_context: TraceContext, response: Dict[str, Any]) -> None:
        """Log raw LLM response including tool calls"""
        self._log_event(trace_context, EventLevel.AGENT_PROCESSING, "llm_response", {
            "content": response.get("content", "") if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None,
            "content_length": len(response.get("content", "")),
            "tool_calls": response.get("tool_calls", []) if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None,
            "tool_calls_count": len(response.get("tool_calls", [])),
            "finish_reason": response.get("finish_reason", ""),
            "usage": response.get("usage", {}),
            "model": response.get("model", ""),
            "processing_time_ms": response.get("processing_time_ms", 0)
        })

    def log_agent_command(self, trace_context: TraceContext, command: Dict[str, Any]) -> None:
        """Log agent command/decision that triggers middleware"""
        self._log_event(trace_context, EventLevel.AGENT_PROCESSING, "agent_command", {
            "command_type": command.get("type", "unknown"),  # tool_call, text_response, workflow_step
            "tool_name": command.get("tool_name"),
            "method": command.get("method"),
            "parameters": command.get("parameters", {}),
            "intent": command.get("intent", ""),
            "reasoning": command.get("reasoning", "") if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None,
            "raw_command": command.get("raw_command", {}) if self.level == TraceLevel.VERBOSE else None
        })

    def log_agent_response(self, trace_context: TraceContext, response: Dict[str, Any]) -> None:
        """Log agent response generation"""
        self._log_event(trace_context, EventLevel.AGENT_PROCESSING, "response_generated", {
            "content_length": len(response.get("content", "")),
            "tools_used": response.get("tools_used", []),
            "token_usage": response.get("token_usage", {}),
            "processing_time_ms": response.get("processing_time_ms", 0)
        })
    
    # Middleware Events
    def log_middleware_start(self, trace_context: TraceContext, middleware_info: Dict[str, Any]) -> None:
        """Log middleware interceptor start"""
        self._log_event(trace_context, EventLevel.MIDDLEWARE, "interceptor_triggered", {
            "interceptor_name": middleware_info.get("name", "unknown"),
            "interceptor_type": middleware_info.get("type", "unknown"),
            "request_type": middleware_info.get("request_type", "unknown"),
            "input_summary": middleware_info.get("input_summary", {})
        })
    
    def log_middleware_complete(self, trace_context: TraceContext, result: Dict[str, Any]) -> None:
        """Log middleware interceptor completion"""
        self._log_event(trace_context, EventLevel.MIDDLEWARE, "interceptor_completed", {
            "action_taken": result.get("action", "unknown"),
            "route_decision": result.get("route", "unknown"),
            "processing_time_ms": result.get("processing_time_ms", 0)
        })
    
    # Tool Execution Events
    def log_tool_start(self, trace_context: TraceContext, tool_info: Dict[str, Any]) -> None:
        """Log tool execution start"""
        self._log_event(trace_context, EventLevel.TOOL_EXECUTION, "tool_called", {
            "tool_name": tool_info.get("name", "unknown"),
            "tool_type": tool_info.get("type", "unknown"),
            "method": tool_info.get("method", "unknown"),
            "parameters": tool_info.get("parameters", {}),
            "execution_context": tool_info.get("context", {})
        })
    
    def log_tool_success(self, trace_context: TraceContext, result: Dict[str, Any]) -> None:
        """Log successful tool execution"""
        self._log_event(trace_context, EventLevel.TOOL_EXECUTION, "tool_completed", {
            "success": True,
            "execution_time_ms": result.get("execution_time_ms", 0),
            "result_summary": result.get("result_summary", {}),
            "performance_metrics": result.get("performance_metrics", {}),
            "full_result": result.get("full_result", {}) if self.level in [TraceLevel.DETAILED, TraceLevel.VERBOSE] else None
        })
    
    def log_tool_error(self, trace_context: TraceContext, error_info: Dict[str, Any]) -> None:
        """Log tool execution error"""
        self._log_event(trace_context, EventLevel.ERROR, "tool_failed", {
            "success": False,
            "error": error_info.get("error", "unknown"),
            "error_type": error_info.get("error_type", "unknown"),
            "execution_time_ms": error_info.get("execution_time_ms", 0),
            "stack_trace": error_info.get("stack_trace", "") if self.level == TraceLevel.VERBOSE else None
        })
    
    # Workflow Events
    def log_workflow_start(self, trace_context: TraceContext, workflow_info: Dict[str, Any]) -> None:
        """Log workflow execution start"""
        self._log_event(trace_context, EventLevel.WORKFLOW, "workflow_started", {
            "workflow_id": workflow_info.get("id", "unknown"),
            "workflow_type": workflow_info.get("type", "unknown"),
            "steps_count": workflow_info.get("steps_count", 0),
            "execution_mode": workflow_info.get("execution_mode", "unknown")
        })
    
    def log_workflow_step(self, trace_context: TraceContext, step_info: Dict[str, Any]) -> None:
        """Log workflow step execution"""
        self._log_event(trace_context, EventLevel.WORKFLOW, "workflow_step", {
            "step_id": step_info.get("id", "unknown"),
            "step_type": step_info.get("type", "unknown"),
            "step_status": step_info.get("status", "unknown"),
            "duration_ms": step_info.get("duration_ms", 0)
        })
    
    # Error Events
    def log_error(self, trace_context: TraceContext, error: Exception, context: Optional[Dict] = None) -> None:
        """Log an error with full context"""
        self._log_event(trace_context, EventLevel.ERROR, "error_occurred", {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "stack_trace": repr(error) if self.level == TraceLevel.VERBOSE else None
        })
    
    # Performance and Summary
    def log_performance_summary(self, trace_context: TraceContext) -> None:
        """Log performance summary for the trace"""
        events = self.trace_manager.get_trace_events(trace_context.trace_id)
        
        if not events:
            return
            
        summary = self.performance_formatter.analyze_performance(events)
        
        self._log_event(trace_context, EventLevel.PERFORMANCE, "performance_summary", {
            "total_duration_ms": summary.get("total_duration_ms", 0),
            "component_breakdown": summary.get("component_breakdown", {}),
            "tool_performance": summary.get("tool_performance", {}),
            "cost_breakdown": summary.get("cost_breakdown", {}),
            "event_count": len(events)
        })
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get complete trace summary"""
        events = self.trace_manager.get_trace_events(trace_id)
        return {
            "trace_id": trace_id,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
            "performance": self.performance_formatter.analyze_performance(events)
        }
