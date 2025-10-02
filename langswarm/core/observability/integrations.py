"""
LangSwarm V2 Observability Integrations

Specific observability integrations for V2 components including agents,
tools, sessions, memory, and workflows with standardized monitoring patterns.
"""

from typing import Dict, Optional, Any
from datetime import datetime

from .interfaces import ObservabilityConfig
from .provider import ObservabilityProvider, create_observability_provider


class ComponentObservability:
    """Base class for component-specific observability"""
    
    def __init__(self, component_name: str, provider: Optional[ObservabilityProvider] = None):
        """
        Initialize component observability.
        
        Args:
            component_name: Name of the component for tagging
            provider: Observability provider (creates default if None)
        """
        self.component_name = component_name
        self.provider = provider or create_observability_provider()
    
    def log_operation(self, operation: str, level: str = "info", **kwargs):
        """Log component operation"""
        self.provider.log_with_trace_context(
            level, 
            f"{self.component_name}: {operation}",
            self.component_name,
            operation=operation,
            **kwargs
        )
    
    def trace_operation(self, operation: str, **tags):
        """Trace component operation"""
        operation_name = f"{self.component_name}.{operation}"
        return self.provider.tracer.start_span(
            operation_name, 
            component=self.component_name,
            **tags
        )
    
    def record_metric(self, metric_name: str, value: float, metric_type: str = "counter", **tags):
        """Record component metric"""
        full_metric_name = f"{self.component_name}.{metric_name}"
        tags['component'] = self.component_name
        
        if metric_type == "counter":
            self.provider.metrics.increment_counter(full_metric_name, value, **tags)
        elif metric_type == "gauge":
            self.provider.metrics.set_gauge(full_metric_name, value, **tags)
        elif metric_type == "histogram":
            self.provider.metrics.record_histogram(full_metric_name, value, **tags)
        elif metric_type == "timer":
            self.provider.metrics.record_timer(full_metric_name, value, **tags)


class AgentObservability(ComponentObservability):
    """Observability integration for V2 agents"""
    
    def __init__(self, provider: Optional[ObservabilityProvider] = None):
        super().__init__("agent", provider)
    
    def trace_agent_creation(self, agent_id: str, provider: str, model: str):
        """Trace agent creation"""
        with self.trace_operation("create", agent_id=agent_id, provider=provider, model=model):
            self.log_operation(f"Creating agent {agent_id}", "info", 
                             agent_id=agent_id, provider=provider, model=model)
            self.record_metric("created", 1.0, "counter", provider=provider, model=model)
    
    def trace_message_processing(self, agent_id: str, message_length: int):
        """Trace agent message processing"""
        return self.provider.trace_and_log_operation(
            f"agent.process_message",
            self.component_name
        )
    
    def record_response_time(self, agent_id: str, duration_ms: float, provider: str, model: str):
        """Record agent response time"""
        self.record_metric("response_time_ms", duration_ms, "histogram",
                          agent_id=agent_id, provider=provider, model=model)
    
    def record_token_usage(self, agent_id: str, input_tokens: int, output_tokens: int, provider: str):
        """Record token usage"""
        self.record_metric("tokens.input", input_tokens, "counter", 
                          agent_id=agent_id, provider=provider)
        self.record_metric("tokens.output", output_tokens, "counter",
                          agent_id=agent_id, provider=provider)
        self.record_metric("tokens.total", input_tokens + output_tokens, "counter",
                          agent_id=agent_id, provider=provider)
    
    def record_error(self, agent_id: str, error_type: str, provider: str, model: str):
        """Record agent error"""
        self.log_operation(f"Agent error: {error_type}", "error",
                          agent_id=agent_id, error_type=error_type, provider=provider, model=model)
        self.record_metric("errors", 1.0, "counter",
                          agent_id=agent_id, error_type=error_type, provider=provider, model=model)


class ToolObservability(ComponentObservability):
    """Observability integration for V2 tools"""
    
    def __init__(self, provider: Optional[ObservabilityProvider] = None):
        super().__init__("tool", provider)
    
    def trace_tool_execution(self, tool_name: str, method: str, parameters: Dict[str, Any]):
        """Trace tool execution"""
        param_count = len(parameters) if parameters else 0
        return self.trace_operation("execute", 
                                   tool_name=tool_name, 
                                   method=method,
                                   param_count=param_count)
    
    def record_execution_time(self, tool_name: str, method: str, duration_ms: float, success: bool):
        """Record tool execution time"""
        status = "success" if success else "failure"
        self.record_metric("execution_time_ms", duration_ms, "histogram",
                          tool_name=tool_name, method=method, status=status)
        self.record_metric("executions", 1.0, "counter",
                          tool_name=tool_name, method=method, status=status)
    
    def record_tool_error(self, tool_name: str, method: str, error_type: str):
        """Record tool execution error"""
        self.log_operation(f"Tool execution failed: {tool_name}.{method}", "error",
                          tool_name=tool_name, method=method, error_type=error_type)
        self.record_metric("errors", 1.0, "counter",
                          tool_name=tool_name, method=method, error_type=error_type)
    
    def trace_tool_registry_operation(self, operation: str, tool_name: str):
        """Trace tool registry operations"""
        return self.trace_operation(f"registry.{operation}", tool_name=tool_name)


class SessionObservability(ComponentObservability):
    """Observability integration for V2 sessions"""
    
    def __init__(self, provider: Optional[ObservabilityProvider] = None):
        super().__init__("session", provider)
    
    def trace_session_creation(self, session_id: str, user_id: str, provider: str, backend: str):
        """Trace session creation"""
        with self.trace_operation("create", session_id=session_id, user_id=user_id, 
                                 provider=provider, backend=backend):
            self.log_operation(f"Creating session {session_id}", "info",
                             session_id=session_id, user_id=user_id, provider=provider, backend=backend)
            self.record_metric("created", 1.0, "counter", provider=provider, backend=backend)
    
    def trace_message_handling(self, session_id: str, role: str, message_length: int):
        """Trace session message handling"""
        return self.trace_operation("handle_message", 
                                   session_id=session_id, 
                                   role=role,
                                   message_length=message_length)
    
    def record_session_duration(self, session_id: str, duration_minutes: float, provider: str):
        """Record session duration"""
        self.record_metric("duration_minutes", duration_minutes, "histogram",
                          session_id=session_id, provider=provider)
    
    def record_message_count(self, session_id: str, message_count: int, provider: str):
        """Record message count in session"""
        self.record_metric("message_count", message_count, "gauge",
                          session_id=session_id, provider=provider)
    
    def record_session_error(self, session_id: str, error_type: str, operation: str):
        """Record session error"""
        self.log_operation(f"Session error in {operation}: {error_type}", "error",
                          session_id=session_id, error_type=error_type, operation=operation)
        self.record_metric("errors", 1.0, "counter",
                          session_id=session_id, error_type=error_type, operation=operation)


class MemoryObservability(ComponentObservability):
    """Observability integration for V2 memory system"""
    
    def __init__(self, provider: Optional[ObservabilityProvider] = None):
        super().__init__("memory", provider)
    
    def trace_memory_operation(self, operation: str, backend: str, session_id: Optional[str] = None):
        """Trace memory operations"""
        return self.trace_operation(operation, backend=backend, session_id=session_id)
    
    def record_memory_usage(self, backend: str, sessions: int, messages: int, storage_mb: float):
        """Record memory usage statistics"""
        self.record_metric("sessions", sessions, "gauge", backend=backend)
        self.record_metric("messages", messages, "gauge", backend=backend)
        self.record_metric("storage_mb", storage_mb, "gauge", backend=backend)
    
    def record_operation_time(self, operation: str, backend: str, duration_ms: float, success: bool):
        """Record memory operation time"""
        status = "success" if success else "failure"
        self.record_metric("operation_time_ms", duration_ms, "histogram",
                          operation=operation, backend=backend, status=status)
        self.record_metric("operations", 1.0, "counter",
                          operation=operation, backend=backend, status=status)
    
    def record_search_performance(self, backend: str, query_time_ms: float, results_count: int):
        """Record memory search performance"""
        self.record_metric("search.query_time_ms", query_time_ms, "histogram", backend=backend)
        self.record_metric("search.results_count", results_count, "histogram", backend=backend)
        self.record_metric("search.queries", 1.0, "counter", backend=backend)
    
    def record_memory_error(self, operation: str, backend: str, error_type: str):
        """Record memory operation error"""
        self.log_operation(f"Memory operation failed: {operation}", "error",
                          operation=operation, backend=backend, error_type=error_type)
        self.record_metric("errors", 1.0, "counter",
                          operation=operation, backend=backend, error_type=error_type)


class WorkflowObservability(ComponentObservability):
    """Observability integration for V2 workflows"""
    
    def __init__(self, provider: Optional[ObservabilityProvider] = None):
        super().__init__("workflow", provider)
    
    def trace_workflow_execution(self, workflow_id: str, workflow_type: str, step_count: int):
        """Trace workflow execution"""
        return self.trace_operation("execute", 
                                   workflow_id=workflow_id,
                                   workflow_type=workflow_type,
                                   step_count=step_count)
    
    def trace_step_execution(self, workflow_id: str, step_name: str, step_type: str):
        """Trace individual step execution"""
        return self.trace_operation("execute_step",
                                   workflow_id=workflow_id,
                                   step_name=step_name,
                                   step_type=step_type)
    
    def record_workflow_duration(self, workflow_id: str, duration_ms: float, success: bool):
        """Record workflow execution duration"""
        status = "success" if success else "failure"
        self.record_metric("execution_time_ms", duration_ms, "histogram",
                          workflow_id=workflow_id, status=status)
        self.record_metric("executions", 1.0, "counter",
                          workflow_id=workflow_id, status=status)
    
    def record_step_performance(self, workflow_id: str, step_name: str, step_type: str, 
                               duration_ms: float, success: bool):
        """Record step execution performance"""
        status = "success" if success else "failure"
        self.record_metric("step.execution_time_ms", duration_ms, "histogram",
                          workflow_id=workflow_id, step_name=step_name, 
                          step_type=step_type, status=status)
        self.record_metric("step.executions", 1.0, "counter",
                          workflow_id=workflow_id, step_name=step_name,
                          step_type=step_type, status=status)
    
    def record_workflow_error(self, workflow_id: str, step_name: Optional[str], error_type: str):
        """Record workflow execution error"""
        error_location = f"step {step_name}" if step_name else "workflow"
        self.log_operation(f"Workflow error in {error_location}: {error_type}", "error",
                          workflow_id=workflow_id, step_name=step_name, error_type=error_type)
        self.record_metric("errors", 1.0, "counter",
                          workflow_id=workflow_id, step_name=step_name, error_type=error_type)


# Convenience functions to create component observability instances
def create_agent_observability(provider: Optional[ObservabilityProvider] = None) -> AgentObservability:
    """Create agent observability instance"""
    return AgentObservability(provider)


def create_tool_observability(provider: Optional[ObservabilityProvider] = None) -> ToolObservability:
    """Create tool observability instance"""
    return ToolObservability(provider)


def create_session_observability(provider: Optional[ObservabilityProvider] = None) -> SessionObservability:
    """Create session observability instance"""
    return SessionObservability(provider)


def create_memory_observability(provider: Optional[ObservabilityProvider] = None) -> MemoryObservability:
    """Create memory observability instance"""
    return MemoryObservability(provider)


def create_workflow_observability(provider: Optional[ObservabilityProvider] = None) -> WorkflowObservability:
    """Create workflow observability instance"""
    return WorkflowObservability(provider)


def create_all_observability_integrations(provider: Optional[ObservabilityProvider] = None) -> Dict[str, ComponentObservability]:
    """Create all component observability integrations"""
    return {
        "agent": create_agent_observability(provider),
        "tool": create_tool_observability(provider),
        "session": create_session_observability(provider),
        "memory": create_memory_observability(provider),
        "workflow": create_workflow_observability(provider)
    }
