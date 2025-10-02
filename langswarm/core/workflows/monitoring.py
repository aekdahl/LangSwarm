"""
Workflow Monitoring and Debugging Tools for LangSwarm V2

Comprehensive monitoring, observability, and debugging tools
for the V2 workflow system. Provides real-time monitoring,
performance metrics, and debugging utilities.
"""

import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, AsyncIterator
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

from .interfaces import (
    IWorkflowMonitor, IWorkflowExecution, WorkflowStatus, StepStatus,
    WorkflowEvent, StepEvent, WorkflowResult, StepResult
)


@dataclass
class ExecutionMetrics:
    """Metrics for workflow execution"""
    execution_id: str
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    step_count: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    average_step_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of steps"""
        if self.step_count == 0:
            return 1.0
        return self.completed_steps / self.step_count
    
    @property
    def is_complete(self) -> bool:
        """Whether execution is complete"""
        return self.end_time is not None


@dataclass
class WorkflowMetrics:
    """Aggregated metrics for a workflow"""
    workflow_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: Optional[float] = None
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    last_execution: Optional[datetime] = None
    execution_times: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions
    
    def add_execution(self, execution_time: float, success: bool):
        """Add an execution result to metrics"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        self.execution_times.append(execution_time)
        self.last_execution = datetime.now(timezone.utc)
        
        # Update timing statistics
        if self.average_execution_time is None:
            self.average_execution_time = execution_time
            self.min_execution_time = execution_time
            self.max_execution_time = execution_time
        else:
            # Calculate rolling average
            self.average_execution_time = (
                (self.average_execution_time * (self.total_executions - 1) + execution_time) 
                / self.total_executions
            )
            self.min_execution_time = min(self.min_execution_time, execution_time)
            self.max_execution_time = max(self.max_execution_time, execution_time)


@dataclass
class SystemMetrics:
    """System-wide workflow metrics"""
    total_workflows: int = 0
    total_executions: int = 0
    active_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_system_load: Optional[float] = None
    uptime: Optional[float] = None
    
    @property
    def system_success_rate(self) -> float:
        """Calculate system-wide success rate"""
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions


class WorkflowMonitor(IWorkflowMonitor):
    """
    Comprehensive workflow monitoring and observability system.
    
    Features:
    - Real-time execution monitoring
    - Performance metrics collection
    - Event subscription and notification
    - Debugging and tracing utilities
    - System health monitoring
    """
    
    def __init__(self):
        self._execution_metrics: Dict[str, ExecutionMetrics] = {}
        self._workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self._system_metrics = SystemMetrics()
        self._subscribers: Dict[str, Callable] = {}
        self._event_history: deque = deque(maxlen=1000)
        self._start_time = datetime.now(timezone.utc)
        
        # Monitoring state
        self._active_executions: Set[str] = set()
        self._monitoring_enabled = True
        
        # Performance tracking
        self._recent_events: deque = deque(maxlen=100)
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    async def track_execution_start(self, execution: IWorkflowExecution):
        """Track the start of a workflow execution"""
        if not self._monitoring_enabled:
            return
        
        execution_id = execution.execution_id
        workflow_id = execution.workflow_id
        
        # Create execution metrics
        metrics = ExecutionMetrics(
            execution_id=execution_id,
            workflow_id=workflow_id,
            start_time=execution.start_time,
            step_count=len(execution.context.workflow.steps) if hasattr(execution.context, 'workflow') else 0
        )
        
        self._execution_metrics[execution_id] = metrics
        self._active_executions.add(execution_id)
        
        # Update system metrics
        self._system_metrics.active_executions += 1
        
        # Create and emit event
        event = {
            "type": "execution_started",
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step_count": metrics.step_count
        }
        
        await self._emit_event(event)
        self.logger.info(f"Started tracking execution {execution_id} for workflow {workflow_id}")
    
    async def track_execution_end(self, execution: IWorkflowExecution, result: WorkflowResult):
        """Track the end of a workflow execution"""
        if not self._monitoring_enabled:
            return
        
        execution_id = execution.execution_id
        workflow_id = execution.workflow_id
        
        # Update execution metrics
        if execution_id in self._execution_metrics:
            metrics = self._execution_metrics[execution_id]
            metrics.end_time = datetime.now(timezone.utc)
            metrics.total_execution_time = result.execution_time
            
            if result.step_results:
                metrics.completed_steps = sum(1 for r in result.step_results.values() if r.success)
                metrics.failed_steps = sum(1 for r in result.step_results.values() if not r.success)
                
                # Calculate average step time
                step_times = [r.execution_time for r in result.step_results.values() if r.execution_time]
                if step_times:
                    metrics.average_step_time = sum(step_times) / len(step_times)
        
        # Update workflow metrics
        if workflow_id not in self._workflow_metrics:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
        
        workflow_metrics = self._workflow_metrics[workflow_id]
        workflow_metrics.add_execution(
            result.execution_time or 0.0,
            result.success
        )
        
        # Update system metrics
        self._system_metrics.total_executions += 1
        if result.success:
            self._system_metrics.successful_executions += 1
        else:
            self._system_metrics.failed_executions += 1
        
        if execution_id in self._active_executions:
            self._active_executions.remove(execution_id)
            self._system_metrics.active_executions -= 1
        
        # Create and emit event
        event = {
            "type": "execution_completed",
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": result.status.value,
            "execution_time": result.execution_time,
            "success": result.success,
            "step_results": len(result.step_results) if result.step_results else 0
        }
        
        await self._emit_event(event)
        self.logger.info(f"Completed tracking execution {execution_id}: {result.status.value}")
    
    async def track_step_execution(self, execution_id: str, step_result: StepResult):
        """Track individual step execution"""
        if not self._monitoring_enabled:
            return
        
        # Create and emit step event
        event = {
            "type": "step_completed",
            "execution_id": execution_id,
            "step_id": step_result.step_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": step_result.status.value,
            "execution_time": step_result.execution_time,
            "success": step_result.success
        }
        
        await self._emit_event(event)
        
        if step_result.error:
            self.logger.warning(f"Step {step_result.step_id} failed in execution {execution_id}: {step_result.error}")
    
    async def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get metrics for a specific execution"""
        if execution_id not in self._execution_metrics:
            return {"error": f"No metrics found for execution {execution_id}"}
        
        metrics = self._execution_metrics[execution_id]
        
        return {
            "execution_id": metrics.execution_id,
            "workflow_id": metrics.workflow_id,
            "start_time": metrics.start_time.isoformat(),
            "end_time": metrics.end_time.isoformat() if metrics.end_time else None,
            "total_execution_time": metrics.total_execution_time,
            "step_count": metrics.step_count,
            "completed_steps": metrics.completed_steps,
            "failed_steps": metrics.failed_steps,
            "success_rate": metrics.success_rate,
            "average_step_time": metrics.average_step_time,
            "is_complete": metrics.is_complete
        }
    
    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for a workflow"""
        if workflow_id not in self._workflow_metrics:
            # Return empty metrics instead of error for better UX
            return {
                "workflow_id": workflow_id,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 1.0,
                "average_execution_time": None,
                "min_execution_time": None,
                "max_execution_time": None,
                "last_execution": None
            }
        
        metrics = self._workflow_metrics[workflow_id]
        
        return {
            "workflow_id": metrics.workflow_id,
            "total_executions": metrics.total_executions,
            "successful_executions": metrics.successful_executions,
            "failed_executions": metrics.failed_executions,
            "success_rate": metrics.success_rate,
            "average_execution_time": metrics.average_execution_time,
            "min_execution_time": metrics.min_execution_time,
            "max_execution_time": metrics.max_execution_time,
            "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        return {
            "total_workflows": len(self._workflow_metrics),
            "total_executions": self._system_metrics.total_executions,
            "active_executions": len(self._active_executions),
            "successful_executions": self._system_metrics.successful_executions,
            "failed_executions": self._system_metrics.failed_executions,
            "system_success_rate": self._system_metrics.system_success_rate,
            "uptime_seconds": uptime,
            "monitoring_enabled": self._monitoring_enabled,
            "event_history_size": len(self._event_history),
            "subscribers": len(self._subscribers)
        }
    
    async def subscribe_to_execution(
        self,
        execution_id: str,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> str:
        """Subscribe to events for a specific execution"""
        subscription_id = f"exec_{execution_id}_{len(self._subscribers)}"
        
        def filtered_callback(event: Dict[str, Any]):
            if event.get("execution_id") == execution_id:
                callback(subscription_id, event)
        
        self._subscribers[subscription_id] = filtered_callback
        return subscription_id
    
    async def subscribe_to_workflow(
        self,
        workflow_id: str,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> str:
        """Subscribe to events for a specific workflow"""
        subscription_id = f"workflow_{workflow_id}_{len(self._subscribers)}"
        
        def filtered_callback(event: Dict[str, Any]):
            if event.get("workflow_id") == workflow_id:
                callback(subscription_id, event)
        
        self._subscribers[subscription_id] = filtered_callback
        return subscription_id
    
    async def subscribe_to_all_events(
        self,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> str:
        """Subscribe to all workflow events"""
        subscription_id = f"all_{len(self._subscribers)}"
        
        def all_callback(event: Dict[str, Any]):
            callback(subscription_id, event)
        
        self._subscribers[subscription_id] = all_callback
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        if subscription_id in self._subscribers:
            del self._subscribers[subscription_id]
            return True
        return False
    
    async def _emit_event(self, event: Dict[str, Any]):
        """Emit an event to all subscribers"""
        # Add to event history
        self._event_history.append(event)
        self._recent_events.append(event)
        
        # Notify subscribers
        for subscription_id, callback in self._subscribers.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error in subscriber {subscription_id}: {e}")
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return list(self._event_history)[-limit:]
    
    def get_active_executions(self) -> List[str]:
        """Get list of currently active execution IDs"""
        return list(self._active_executions)
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export all metrics in the specified format"""
        data = {
            "system_metrics": await self.get_system_metrics(),
            "workflow_metrics": {
                wf_id: await self.get_workflow_metrics(wf_id)
                for wf_id in self._workflow_metrics.keys()
            },
            "execution_metrics": {
                exec_id: await self.get_execution_metrics(exec_id)
                for exec_id in self._execution_metrics.keys()
            },
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def enable_monitoring(self):
        """Enable workflow monitoring"""
        self._monitoring_enabled = True
        self.logger.info("Workflow monitoring enabled")
    
    def disable_monitoring(self):
        """Disable workflow monitoring"""
        self._monitoring_enabled = False
        self.logger.info("Workflow monitoring disabled")
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        self._execution_metrics.clear()
        self._workflow_metrics.clear()
        self._system_metrics = SystemMetrics()
        self._event_history.clear()
        self._recent_events.clear()
        self._active_executions.clear()
        self.logger.info("All metrics cleared")


class WorkflowDebugger:
    """
    Advanced debugging utilities for workflow development and troubleshooting.
    
    Features:
    - Step-by-step execution tracing
    - Variable and context inspection
    - Performance profiling
    - Error analysis and suggestions
    """
    
    def __init__(self, monitor: WorkflowMonitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        self._trace_enabled = False
        self._trace_data: Dict[str, List[Dict[str, Any]]] = {}
    
    def enable_tracing(self):
        """Enable detailed execution tracing"""
        self._trace_enabled = True
        self.logger.info("Workflow tracing enabled")
    
    def disable_tracing(self):
        """Disable execution tracing"""
        self._trace_enabled = False
        self.logger.info("Workflow tracing disabled")
    
    async def trace_execution(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get detailed trace for an execution"""
        return self._trace_data.get(execution_id, [])
    
    async def analyze_failures(self, workflow_id: str) -> Dict[str, Any]:
        """Analyze failure patterns for a workflow"""
        workflow_metrics = await self.monitor.get_workflow_metrics(workflow_id)
        
        if "error" in workflow_metrics:
            return workflow_metrics
        
        analysis = {
            "workflow_id": workflow_id,
            "total_executions": workflow_metrics["total_executions"],
            "failed_executions": workflow_metrics["failed_executions"],
            "failure_rate": 1 - workflow_metrics["success_rate"],
            "recommendations": []
        }
        
        # Add recommendations based on failure patterns
        if workflow_metrics["failed_executions"] > 0:
            failure_rate = 1 - workflow_metrics["success_rate"]
            
            if failure_rate > 0.5:
                analysis["recommendations"].append(
                    "High failure rate detected. Review workflow configuration and step dependencies."
                )
            
            if failure_rate > 0.2:
                analysis["recommendations"].append(
                    "Consider adding error handling and retry logic to critical steps."
                )
        
        return analysis
    
    async def performance_analysis(self, workflow_id: str) -> Dict[str, Any]:
        """Analyze performance characteristics of a workflow"""
        workflow_metrics = await self.monitor.get_workflow_metrics(workflow_id)
        
        if "error" in workflow_metrics:
            return workflow_metrics
        
        analysis = {
            "workflow_id": workflow_id,
            "performance_summary": {
                "average_time": workflow_metrics["average_execution_time"],
                "min_time": workflow_metrics["min_execution_time"],
                "max_time": workflow_metrics["max_execution_time"],
                "time_variance": None
            },
            "recommendations": []
        }
        
        # Calculate time variance if we have data
        avg_time = workflow_metrics["average_execution_time"]
        max_time = workflow_metrics["max_execution_time"]
        
        if avg_time and max_time:
            if max_time > avg_time * 3:
                analysis["recommendations"].append(
                    "High execution time variance detected. Review for bottlenecks."
                )
            
            if avg_time > 30:  # 30 second threshold
                analysis["recommendations"].append(
                    "Long average execution time. Consider optimizing step execution or adding parallelization."
                )
        
        return analysis


# Global monitor instance
_workflow_monitor = WorkflowMonitor()
_workflow_debugger = WorkflowDebugger(_workflow_monitor)


def get_workflow_monitor() -> WorkflowMonitor:
    """Get the global workflow monitor"""
    return _workflow_monitor


def get_workflow_debugger() -> WorkflowDebugger:
    """Get the global workflow debugger"""
    return _workflow_debugger
