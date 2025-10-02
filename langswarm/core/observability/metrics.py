"""
LangSwarm V2 Metrics Collection

Production-ready metrics collection implementation with support for
counters, gauges, histograms, and timers with configurable export.
"""

import time
import threading
from contextlib import contextmanager
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Optional, Any, ContextManager, List
import statistics

from .interfaces import IMetrics, MetricPoint, MetricType, ObservabilityConfig


class V2Metrics(IMetrics):
    """
    Metrics collection implementation for V2 observability system.
    
    Provides counters, gauges, histograms, and timers with configurable
    export and aggregation capabilities.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize V2 metrics.
        
        Args:
            config: Observability configuration
        """
        self.config = config
        self._lock = threading.Lock()
        
        # Metric storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Metric metadata (tags)
        self._metric_tags: Dict[str, Dict[str, str]] = {}
        
        # Export tracking
        self._last_export = datetime.utcnow()
        self._export_buffer: List[MetricPoint] = []
    
    def increment_counter(self, name: str, value: float = 1.0, **tags):
        """Increment a counter metric"""
        if not self.config.metrics_enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._counters[key] += value
            self._metric_tags[key] = tags
            
            # Add to export buffer
            self._add_to_export_buffer(MetricPoint(
                name=name,
                value=self._counters[key],
                metric_type=MetricType.COUNTER,
                timestamp=datetime.utcnow(),
                tags=tags
            ))
    
    def set_gauge(self, name: str, value: float, **tags):
        """Set a gauge metric value"""
        if not self.config.metrics_enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._gauges[key] = value
            self._metric_tags[key] = tags
            
            # Add to export buffer
            self._add_to_export_buffer(MetricPoint(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.utcnow(),
                tags=tags
            ))
    
    def record_histogram(self, name: str, value: float, **tags):
        """Record a histogram value"""
        if not self.config.metrics_enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._histograms[key].append(value)
            self._metric_tags[key] = tags
            
            # Keep histogram size manageable
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            
            # Add to export buffer
            self._add_to_export_buffer(MetricPoint(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                timestamp=datetime.utcnow(),
                tags=tags
            ))
    
    @contextmanager
    def start_timer(self, name: str, **tags) -> ContextManager:
        """Start a timer context manager"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_timer(name, duration_ms, **tags)
    
    def record_timer(self, name: str, duration_ms: float, **tags):
        """Record a timer duration"""
        if not self.config.metrics_enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._timers[key].append(duration_ms)
            self._metric_tags[key] = tags
            
            # Keep timer size manageable
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]
            
            # Add to export buffer
            self._add_to_export_buffer(MetricPoint(
                name=name,
                value=duration_ms,
                metric_type=MetricType.TIMER,
                timestamp=datetime.utcnow(),
                tags=tags
            ))
    
    def _get_metric_key(self, name: str, tags: Dict[str, str]) -> str:
        """Generate unique key for metric with tags"""
        if not tags:
            return name
        
        # Sort tags for consistent key generation
        sorted_tags = sorted(tags.items())
        tag_str = ','.join(f"{k}={v}" for k, v in sorted_tags)
        return f"{name}#{tag_str}"
    
    def _add_to_export_buffer(self, metric_point: MetricPoint):
        """Add metric point to export buffer"""
        self._export_buffer.append(metric_point)
        
        # Keep buffer size manageable
        if len(self._export_buffer) > self.config.buffer_size:
            self._export_buffer = self._export_buffer[-self.config.buffer_size:]
    
    def get_counter_value(self, name: str, **tags) -> float:
        """Get current counter value"""
        key = self._get_metric_key(name, tags)
        with self._lock:
            return self._counters.get(key, 0.0)
    
    def get_gauge_value(self, name: str, **tags) -> Optional[float]:
        """Get current gauge value"""
        key = self._get_metric_key(name, tags)
        with self._lock:
            return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, **tags) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._get_metric_key(name, tags)
        with self._lock:
            values = self._histograms.get(key, [])
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
    
    def get_timer_stats(self, name: str, **tags) -> Dict[str, float]:
        """Get timer statistics"""
        key = self._get_metric_key(name, tags)
        with self._lock:
            values = self._timers.get(key, [])
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'min_ms': min(values),
                'max_ms': max(values),
                'mean_ms': statistics.mean(values),
                'median_ms': statistics.median(values),
                'p95_ms': self._percentile(values, 95),
                'p99_ms': self._percentile(values, 99)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histogram_stats': {
                    name: self.get_histogram_stats(name.split('#')[0], 
                                                 **self._parse_tags_from_key(name))
                    for name in self._histograms.keys()
                },
                'timer_stats': {
                    name: self.get_timer_stats(name.split('#')[0],
                                             **self._parse_tags_from_key(name))
                    for name in self._timers.keys()
                }
            }
    
    def _parse_tags_from_key(self, key: str) -> Dict[str, str]:
        """Parse tags from metric key"""
        if '#' not in key:
            return {}
        
        _, tag_str = key.split('#', 1)
        tags = {}
        
        for tag_pair in tag_str.split(','):
            if '=' in tag_pair:
                k, v = tag_pair.split('=', 1)
                tags[k] = v
        
        return tags
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._metric_tags.clear()
            self._export_buffer.clear()
    
    def export_metrics(self) -> List[MetricPoint]:
        """Export current metrics for external consumption"""
        with self._lock:
            # Get current export buffer
            export_data = self._export_buffer.copy()
            
            # Clear export buffer
            self._export_buffer.clear()
            self._last_export = datetime.utcnow()
            
            return export_data


# Global metrics registry
_metrics: Dict[str, V2Metrics] = {}
_default_config: Optional[ObservabilityConfig] = None


def configure_metrics(config: ObservabilityConfig):
    """Configure global metrics settings"""
    global _default_config
    _default_config = config


def create_metrics(name: str = "default", config: Optional[ObservabilityConfig] = None) -> V2Metrics:
    """Create a named metrics instance"""
    if config is None:
        config = _default_config or ObservabilityConfig()
    
    metrics = V2Metrics(config)
    _metrics[name] = metrics
    return metrics


def get_metrics(name: str = "default") -> Optional[V2Metrics]:
    """Get existing metrics by name"""
    return _metrics.get(name)


def get_or_create_metrics(name: str = "default", 
                         config: Optional[ObservabilityConfig] = None) -> V2Metrics:
    """Get existing metrics or create new one"""
    metrics = get_metrics(name)
    if metrics is None:
        metrics = create_metrics(name, config)
    return metrics


# Convenience functions for default metrics
def counter(name: str, value: float = 1.0, **tags):
    """Increment counter in default metrics"""
    metrics = get_or_create_metrics()
    metrics.increment_counter(name, value, **tags)


def gauge(name: str, value: float, **tags):
    """Set gauge in default metrics"""
    metrics = get_or_create_metrics()
    metrics.set_gauge(name, value, **tags)


def histogram(name: str, value: float, **tags):
    """Record histogram value in default metrics"""
    metrics = get_or_create_metrics()
    metrics.record_histogram(name, value, **tags)


def timer(name: str, **tags) -> ContextManager:
    """Start timer in default metrics"""
    metrics = get_or_create_metrics()
    return metrics.start_timer(name, **tags)


def record_timer_value(name: str, duration_ms: float, **tags):
    """Record timer value in default metrics"""
    metrics = get_or_create_metrics()
    metrics.record_timer(name, duration_ms, **tags)
