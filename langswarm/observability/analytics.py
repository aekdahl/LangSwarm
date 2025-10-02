"""
Enhanced Analytics and Monitoring for LangSwarm V2 Tool System

Provides comprehensive observability, usage analytics, performance monitoring,
and business intelligence for the tool system.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events tracked by the analytics system"""
    TOOL_EXECUTION = "tool_execution"
    TOOL_ERROR = "tool_error"
    AGENT_CREATION = "agent_creation"
    AGENT_MESSAGE = "agent_message"
    PROVIDER_SWITCH = "provider_switch"
    COST_THRESHOLD = "cost_threshold"
    PERFORMANCE_ALERT = "performance_alert"
    USAGE_PATTERN = "usage_pattern"


@dataclass
class AnalyticsEvent:
    """Individual analytics event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TOOL_EXECUTION
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    execution_time: float = 0.0
    cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "provider": self.provider,
            "model": self.model,
            "execution_time": self.execution_time,
            "cost": self.cost,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class UsageMetrics:
    """Usage metrics for a specific time period"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time: float = 0.0
    total_cost: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    most_used_tools: List[Tuple[str, int]] = field(default_factory=list)
    most_used_providers: List[Tuple[str, int]] = field(default_factory=list)
    error_patterns: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance metrics for tools and providers"""
    tool_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    provider_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    latency_percentiles: Dict[str, float] = field(default_factory=dict)
    throughput_metrics: Dict[str, float] = field(default_factory=dict)


class AnalyticsCollector:
    """
    Collects and aggregates analytics events for the tool system.
    
    Features:
    - Real-time event collection
    - Usage pattern analysis
    - Performance monitoring
    - Cost tracking
    - Error analysis
    - Trend detection
    """
    
    def __init__(self, max_events: int = 10000, retention_days: int = 30):
        self.max_events = max_events
        self.retention_days = retention_days
        
        # Event storage
        self._events: deque = deque(maxlen=max_events)
        self._events_by_type: Dict[EventType, deque] = {
            event_type: deque(maxlen=max_events // len(EventType))
            for event_type in EventType
        }
        
        # Real-time metrics
        self._hourly_metrics: Dict[str, UsageMetrics] = {}
        self._daily_metrics: Dict[str, UsageMetrics] = {}
        self._tool_counters = defaultdict(int)
        self._provider_counters = defaultdict(int)
        self._error_counters = defaultdict(int)
        
        # Performance tracking
        self._execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._cost_tracking: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Alerts and thresholds
        self._alert_callbacks: List[callable] = []
        self._performance_thresholds = {
            "max_execution_time": 30.0,  # seconds
            "max_error_rate": 0.1,       # 10%
            "max_cost_per_hour": 10.0    # dollars
        }
        
        self._logger = logging.getLogger(f"{__name__}.collector")
    
    async def record_event(self, event: AnalyticsEvent):
        """Record a new analytics event"""
        try:
            # Add to main event store
            self._events.append(event)
            self._events_by_type[event.event_type].append(event)
            
            # Update real-time counters
            self._update_counters(event)
            
            # Update metrics
            await self._update_metrics(event)
            
            # Check for alerts
            await self._check_alerts(event)
            
            self._logger.debug(f"Recorded event: {event.event_type.value} for tool {event.tool_name}")
            
        except Exception as e:
            self._logger.error(f"Failed to record analytics event: {e}")
    
    def _update_counters(self, event: AnalyticsEvent):
        """Update real-time counters"""
        if event.tool_name:
            self._tool_counters[event.tool_name] += 1
        
        if event.provider:
            self._provider_counters[event.provider] += 1
        
        if not event.success and event.error_message:
            self._error_counters[event.error_message] += 1
        
        # Track performance metrics
        if event.execution_time > 0:
            key = f"{event.tool_name}_{event.provider}" if event.tool_name and event.provider else "unknown"
            self._execution_times[key].append(event.execution_time)
        
        if event.cost > 0:
            key = f"{event.provider}_{event.model}" if event.provider and event.model else "unknown"
            self._cost_tracking[key].append(event.cost)
    
    async def _update_metrics(self, event: AnalyticsEvent):
        """Update hourly and daily metrics"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d %H:00")
        day_key = now.strftime("%Y-%m-%d")
        
        # Update hourly metrics
        if hour_key not in self._hourly_metrics:
            self._hourly_metrics[hour_key] = UsageMetrics()
        
        hourly = self._hourly_metrics[hour_key]
        hourly.total_requests += 1
        if event.success:
            hourly.successful_requests += 1
        else:
            hourly.failed_requests += 1
        
        hourly.total_execution_time += event.execution_time
        hourly.total_cost += event.cost
        
        # Update daily metrics
        if day_key not in self._daily_metrics:
            self._daily_metrics[day_key] = UsageMetrics()
        
        daily = self._daily_metrics[day_key]
        daily.total_requests += 1
        if event.success:
            daily.successful_requests += 1
        else:
            daily.failed_requests += 1
        
        daily.total_execution_time += event.execution_time
        daily.total_cost += event.cost
    
    async def _check_alerts(self, event: AnalyticsEvent):
        """Check for alert conditions"""
        # High execution time alert
        if event.execution_time > self._performance_thresholds["max_execution_time"]:
            await self._trigger_alert(
                "high_execution_time",
                f"Tool {event.tool_name} took {event.execution_time:.2f}s to execute",
                event
            )
        
        # Error rate alert
        if not event.success:
            error_rate = self._calculate_recent_error_rate()
            if error_rate > self._performance_thresholds["max_error_rate"]:
                await self._trigger_alert(
                    "high_error_rate",
                    f"Error rate is {error_rate:.2%} (threshold: {self._performance_thresholds['max_error_rate']:.2%})",
                    event
                )
        
        # Cost alert
        hourly_cost = self._calculate_hourly_cost()
        if hourly_cost > self._performance_thresholds["max_cost_per_hour"]:
            await self._trigger_alert(
                "high_cost",
                f"Hourly cost is ${hourly_cost:.2f} (threshold: ${self._performance_thresholds['max_cost_per_hour']:.2f})",
                event
            )
    
    async def _trigger_alert(self, alert_type: str, message: str, event: AnalyticsEvent):
        """Trigger an alert"""
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.now(),
            "event": event.to_dict()
        }
        
        for callback in self._alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                self._logger.error(f"Alert callback failed: {e}")
    
    def _calculate_recent_error_rate(self, minutes: int = 60) -> float:
        """Calculate error rate for recent time period"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_events = [e for e in self._events if e.timestamp >= cutoff]
        
        if not recent_events:
            return 0.0
        
        errors = sum(1 for e in recent_events if not e.success)
        return errors / len(recent_events)
    
    def _calculate_hourly_cost(self) -> float:
        """Calculate cost for current hour"""
        now = datetime.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        hourly_events = [e for e in self._events if e.timestamp >= hour_start]
        return sum(e.cost for e in hourly_events)
    
    def get_usage_metrics(self, period: str = "hour") -> UsageMetrics:
        """Get usage metrics for specified period"""
        now = datetime.now()
        
        if period == "hour":
            key = now.strftime("%Y-%m-%d %H:00")
            metrics = self._hourly_metrics.get(key, UsageMetrics())
        elif period == "day":
            key = now.strftime("%Y-%m-%d")
            metrics = self._daily_metrics.get(key, UsageMetrics())
        else:
            # Custom period - calculate from events
            metrics = self._calculate_period_metrics(period)
        
        # Calculate derived metrics
        if metrics.total_requests > 0:
            metrics.success_rate = metrics.successful_requests / metrics.total_requests
            metrics.average_execution_time = metrics.total_execution_time / metrics.total_requests
        
        # Top tools and providers
        metrics.most_used_tools = list(self._tool_counters.most_common(10))
        metrics.most_used_providers = list(self._provider_counters.most_common(10))
        metrics.error_patterns = list(self._error_counters.most_common(10))
        
        return metrics
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for tools and providers"""
        metrics = PerformanceMetrics()
        
        # Tool performance
        for key, times in self._execution_times.items():
            if times:
                tool_name = key.split('_')[0]
                metrics.tool_performance[tool_name] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "p95_time": self._percentile(list(times), 95)
                }
        
        # Provider performance
        provider_times = defaultdict(list)
        for key, times in self._execution_times.items():
            if '_' in key:
                provider = key.split('_')[1]
                provider_times[provider].extend(times)
        
        for provider, times in provider_times.items():
            if times:
                metrics.provider_performance[provider] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "p95_time": self._percentile(times, 95)
                }
        
        # Overall latency percentiles
        all_times = []
        for times in self._execution_times.values():
            all_times.extend(times)
        
        if all_times:
            metrics.latency_percentiles = {
                "p50": self._percentile(all_times, 50),
                "p90": self._percentile(all_times, 90),
                "p95": self._percentile(all_times, 95),
                "p99": self._percentile(all_times, 99)
            }
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _calculate_period_metrics(self, period: str) -> UsageMetrics:
        """Calculate metrics for custom period"""
        # This would implement custom period calculations
        # For now, return empty metrics
        return UsageMetrics()
    
    def add_alert_callback(self, callback: callable):
        """Add alert callback function"""
        self._alert_callbacks.append(callback)
    
    def export_events(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export events for external analysis"""
        events = list(self._events)
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        return [event.to_dict() for event in events]
    
    def cleanup_old_events(self):
        """Clean up events older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        # Clean main events
        self._events = deque(
            (e for e in self._events if e.timestamp >= cutoff),
            maxlen=self.max_events
        )
        
        # Clean categorized events
        for event_type in EventType:
            self._events_by_type[event_type] = deque(
                (e for e in self._events_by_type[event_type] if e.timestamp >= cutoff),
                maxlen=self.max_events // len(EventType)
            )


# Global analytics collector instance
_global_analytics = AnalyticsCollector()


def get_analytics() -> AnalyticsCollector:
    """Get the global analytics collector"""
    return _global_analytics


async def record_tool_execution(
    tool_name: str,
    provider: str,
    model: str,
    execution_time: float,
    cost: float,
    success: bool,
    error_message: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    **metadata
):
    """Convenience function to record tool execution"""
    event = AnalyticsEvent(
        event_type=EventType.TOOL_EXECUTION,
        tool_name=tool_name,
        provider=provider,
        model=model,
        execution_time=execution_time,
        cost=cost,
        success=success,
        error_message=error_message,
        user_id=user_id,
        agent_id=agent_id,
        metadata=metadata
    )
    
    await _global_analytics.record_event(event)


async def record_agent_creation(
    agent_id: str,
    provider: str,
    model: str,
    tools: List[str],
    user_id: Optional[str] = None,
    **metadata
):
    """Convenience function to record agent creation"""
    event = AnalyticsEvent(
        event_type=EventType.AGENT_CREATION,
        agent_id=agent_id,
        provider=provider,
        model=model,
        user_id=user_id,
        metadata={**metadata, "tools": tools}
    )
    
    await _global_analytics.record_event(event)
