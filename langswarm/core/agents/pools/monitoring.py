"""
LangSwarm V2 Connection Pool Monitoring

Comprehensive monitoring and health checking for connection pools with:
- Real-time health monitoring
- Performance metrics collection
- Alerting and notification system
- Automated remediation capabilities
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

from .interfaces import (
    IHealthChecker, IConnectionPool, ConnectionStatus,
    PoolStats, ConnectionStats, HealthCheckFailedError
)


@dataclass
class HealthAlert:
    """Health alert data structure"""
    alert_id: str
    provider: str
    connection_id: Optional[str]
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_name: str
    provider: str
    connection_id: Optional[str]
    value: float
    timestamp: datetime
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionMonitor:
    """
    Comprehensive connection pool monitor.
    
    Provides real-time monitoring, alerting, and automated remediation
    for connection pools across all providers.
    """
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        """
        Initialize connection monitor.
        
        Args:
            alert_callback: Optional callback function for alerts
        """
        self._pools: Dict[str, IConnectionPool] = {}
        self._health_checker = PoolHealthChecker()
        self._metrics_collector = MetricsCollector()
        self._alerts: List[HealthAlert] = []
        self._performance_metrics: deque = deque(maxlen=10000)
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._alert_callback = alert_callback
        self._shutdown_event = asyncio.Event()
        
        # Monitoring configuration
        self._monitoring_interval = 30  # seconds
        self._health_check_interval = 60  # seconds
        self._metrics_collection_interval = 15  # seconds
        self._alert_thresholds = self._get_default_thresholds()
        
        logging.info("Initialized Connection Monitor")
    
    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Get default alert thresholds"""
        return {
            "response_time_warning": 1000,  # ms
            "response_time_critical": 3000,  # ms
            "success_rate_warning": 90,  # percentage
            "success_rate_critical": 80,  # percentage
            "connection_failure_warning": 5,  # count
            "connection_failure_critical": 10,  # count
            "pool_utilization_warning": 80,  # percentage
            "pool_utilization_critical": 95,  # percentage
            "health_rate_warning": 80,  # percentage
            "health_rate_critical": 60,  # percentage
        }
    
    async def register_pool(self, provider: str, pool: IConnectionPool) -> None:
        """Register a connection pool for monitoring"""
        self._pools[provider] = pool
        
        # Start monitoring tasks for this provider
        await self._start_monitoring_tasks(provider)
        
        logging.info(f"Registered pool for monitoring: {provider}")
    
    async def unregister_pool(self, provider: str) -> None:
        """Unregister a connection pool from monitoring"""
        # Stop monitoring tasks
        await self._stop_monitoring_tasks(provider)
        
        # Remove from pools
        if provider in self._pools:
            self._pools.pop(provider)
        
        logging.info(f"Unregistered pool from monitoring: {provider}")
    
    async def _start_monitoring_tasks(self, provider: str) -> None:
        """Start monitoring tasks for a provider"""
        # Health monitoring task
        health_task = asyncio.create_task(
            self._health_monitoring_loop(provider),
            name=f"health_monitor_{provider}"
        )
        
        # Metrics collection task
        metrics_task = asyncio.create_task(
            self._metrics_collection_loop(provider),
            name=f"metrics_collector_{provider}"
        )
        
        # Performance analysis task
        analysis_task = asyncio.create_task(
            self._performance_analysis_loop(provider),
            name=f"performance_analysis_{provider}"
        )
        
        self._monitoring_tasks[provider] = {
            "health": health_task,
            "metrics": metrics_task,
            "analysis": analysis_task
        }
        
        logging.debug(f"Started monitoring tasks for provider: {provider}")
    
    async def _stop_monitoring_tasks(self, provider: str) -> None:
        """Stop monitoring tasks for a provider"""
        if provider in self._monitoring_tasks:
            tasks = self._monitoring_tasks.pop(provider)
            
            for task_name, task in tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            logging.debug(f"Stopped monitoring tasks for provider: {provider}")
    
    async def _health_monitoring_loop(self, provider: str) -> None:
        """Health monitoring loop for a provider"""
        while not self._shutdown_event.is_set():
            try:
                if provider in self._pools:
                    await self._perform_health_check(provider)
                
                await asyncio.sleep(self._health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in health monitoring loop for {provider}: {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def _metrics_collection_loop(self, provider: str) -> None:
        """Metrics collection loop for a provider"""
        while not self._shutdown_event.is_set():
            try:
                if provider in self._pools:
                    await self._collect_metrics(provider)
                
                await asyncio.sleep(self._metrics_collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in metrics collection loop for {provider}: {e}")
                await asyncio.sleep(self._metrics_collection_interval)
    
    async def _performance_analysis_loop(self, provider: str) -> None:
        """Performance analysis loop for a provider"""
        while not self._shutdown_event.is_set():
            try:
                if provider in self._pools:
                    await self._analyze_performance(provider)
                
                await asyncio.sleep(self._monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in performance analysis loop for {provider}: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _perform_health_check(self, provider: str) -> None:
        """Perform comprehensive health check for a provider"""
        try:
            pool = self._pools[provider]
            health_result = await self._health_checker.check_pool_health(pool)
            
            # Check for health issues and generate alerts
            await self._evaluate_health_alerts(provider, health_result)
            
            # Record health metrics
            await self._record_health_metrics(provider, health_result)
            
        except Exception as e:
            logging.error(f"Health check failed for provider {provider}: {e}")
            await self._generate_alert(
                provider=provider,
                alert_type="health_check_failed",
                severity="high",
                message=f"Health check failed: {str(e)}"
            )
    
    async def _collect_metrics(self, provider: str) -> None:
        """Collect performance metrics for a provider"""
        try:
            pool = self._pools[provider]
            stats = await pool.get_stats()
            
            # Record various metrics
            await self._record_performance_metrics(provider, stats)
            
            # Check for metric-based alerts
            await self._evaluate_performance_alerts(provider, stats)
            
        except Exception as e:
            logging.error(f"Metrics collection failed for provider {provider}: {e}")
    
    async def _analyze_performance(self, provider: str) -> None:
        """Analyze performance trends for a provider"""
        try:
            # Get recent metrics
            recent_metrics = self._get_recent_metrics(provider)
            
            if len(recent_metrics) < 5:
                return  # Not enough data for analysis
            
            # Analyze trends
            trends = self._analyze_trends(recent_metrics)
            
            # Generate insights and recommendations
            insights = await self._generate_performance_insights(provider, trends)
            
            # Check for trend-based alerts
            await self._evaluate_trend_alerts(provider, trends)
            
        except Exception as e:
            logging.error(f"Performance analysis failed for provider {provider}: {e}")
    
    async def _evaluate_health_alerts(self, provider: str, health_result: Dict[str, Any]) -> None:
        """Evaluate health check results for potential alerts"""
        try:
            total_connections = health_result.get("total_connections", 0)
            healthy_connections = health_result.get("healthy_connections", 0)
            unhealthy_connections = health_result.get("unhealthy_connections", 0)
            
            if total_connections > 0:
                health_rate = (healthy_connections / total_connections) * 100
                
                if health_rate < self._alert_thresholds["health_rate_critical"]:
                    await self._generate_alert(
                        provider=provider,
                        alert_type="health_rate_critical",
                        severity="critical",
                        message=f"Health rate critically low: {health_rate:.1f}%"
                    )
                elif health_rate < self._alert_thresholds["health_rate_warning"]:
                    await self._generate_alert(
                        provider=provider,
                        alert_type="health_rate_warning",
                        severity="medium",
                        message=f"Health rate below warning threshold: {health_rate:.1f}%"
                    )
            
            # Check for unhealthy connections
            if unhealthy_connections > 0:
                await self._generate_alert(
                    provider=provider,
                    alert_type="unhealthy_connections",
                    severity="medium",
                    message=f"{unhealthy_connections} unhealthy connections detected"
                )
        
        except Exception as e:
            logging.error(f"Error evaluating health alerts for {provider}: {e}")
    
    async def _evaluate_performance_alerts(self, provider: str, stats: PoolStats) -> None:
        """Evaluate performance metrics for potential alerts"""
        try:
            # Check response time
            if stats.avg_response_time_ms > self._alert_thresholds["response_time_critical"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="response_time_critical",
                    severity="critical",
                    message=f"Response time critically high: {stats.avg_response_time_ms:.0f}ms"
                )
            elif stats.avg_response_time_ms > self._alert_thresholds["response_time_warning"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="response_time_warning",
                    severity="medium",
                    message=f"Response time above warning threshold: {stats.avg_response_time_ms:.0f}ms"
                )
            
            # Check success rate
            if stats.success_rate < self._alert_thresholds["success_rate_critical"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="success_rate_critical",
                    severity="critical",
                    message=f"Success rate critically low: {stats.success_rate:.1f}%"
                )
            elif stats.success_rate < self._alert_thresholds["success_rate_warning"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="success_rate_warning",
                    severity="medium",
                    message=f"Success rate below warning threshold: {stats.success_rate:.1f}%"
                )
            
            # Check pool utilization
            if stats.utilization_rate > self._alert_thresholds["pool_utilization_critical"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="pool_utilization_critical",
                    severity="critical",
                    message=f"Pool utilization critically high: {stats.utilization_rate:.1f}%"
                )
            elif stats.utilization_rate > self._alert_thresholds["pool_utilization_warning"]:
                await self._generate_alert(
                    provider=provider,
                    alert_type="pool_utilization_warning",
                    severity="medium",
                    message=f"Pool utilization above warning threshold: {stats.utilization_rate:.1f}%"
                )
        
        except Exception as e:
            logging.error(f"Error evaluating performance alerts for {provider}: {e}")
    
    async def _evaluate_trend_alerts(self, provider: str, trends: Dict[str, Any]) -> None:
        """Evaluate performance trends for potential alerts"""
        try:
            # Check for degrading trends
            response_time_trend = trends.get("response_time_trend", "stable")
            success_rate_trend = trends.get("success_rate_trend", "stable")
            
            if response_time_trend == "increasing":
                await self._generate_alert(
                    provider=provider,
                    alert_type="response_time_degrading",
                    severity="medium",
                    message="Response time trend is increasing over time"
                )
            
            if success_rate_trend == "decreasing":
                await self._generate_alert(
                    provider=provider,
                    alert_type="success_rate_degrading",
                    severity="medium",
                    message="Success rate trend is decreasing over time"
                )
        
        except Exception as e:
            logging.error(f"Error evaluating trend alerts for {provider}: {e}")
    
    async def _generate_alert(self, provider: str, alert_type: str, severity: str, 
                            message: str, connection_id: Optional[str] = None,
                            metadata: Dict[str, Any] = None) -> None:
        """Generate an alert"""
        import uuid
        
        alert = HealthAlert(
            alert_id=str(uuid.uuid4()),
            provider=provider,
            connection_id=connection_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store alert
        self._alerts.append(alert)
        
        # Keep only recent alerts (last 1000)
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        # Call alert callback if provided
        if self._alert_callback:
            try:
                await self._alert_callback(alert)
            except Exception as e:
                logging.error(f"Error in alert callback: {e}")
        
        logging.warning(f"Generated alert [{severity}] for {provider}: {message}")
    
    async def _record_health_metrics(self, provider: str, health_result: Dict[str, Any]) -> None:
        """Record health metrics"""
        timestamp = datetime.utcnow()
        
        for metric_name, value in health_result.items():
            if isinstance(value, (int, float)):
                metric = PerformanceMetric(
                    metric_name=f"health_{metric_name}",
                    provider=provider,
                    connection_id=None,
                    value=float(value),
                    timestamp=timestamp
                )
                self._performance_metrics.append(metric)
    
    async def _record_performance_metrics(self, provider: str, stats: PoolStats) -> None:
        """Record performance metrics"""
        timestamp = datetime.utcnow()
        
        # Pool-level metrics
        pool_metrics = {
            "total_connections": stats.total_connections,
            "active_connections": stats.active_connections,
            "utilization_rate": stats.utilization_rate,
            "health_rate": stats.health_rate,
            "avg_response_time_ms": stats.avg_response_time_ms,
            "success_rate": stats.success_rate,
            "total_requests": stats.total_requests
        }
        
        for metric_name, value in pool_metrics.items():
            if value is not None:
                metric = PerformanceMetric(
                    metric_name=metric_name,
                    provider=provider,
                    connection_id=None,
                    value=float(value),
                    timestamp=timestamp
                )
                self._performance_metrics.append(metric)
        
        # Connection-level metrics
        for conn_stats in stats.connection_stats:
            connection_metrics = {
                "response_time_ms": conn_stats.avg_response_time_ms,
                "success_rate": conn_stats.success_rate,
                "total_requests": conn_stats.total_requests,
                "active_requests": conn_stats.current_active_requests
            }
            
            for metric_name, value in connection_metrics.items():
                if value is not None:
                    metric = PerformanceMetric(
                        metric_name=f"connection_{metric_name}",
                        provider=provider,
                        connection_id=conn_stats.connection_id,
                        value=float(value),
                        timestamp=timestamp
                    )
                    self._performance_metrics.append(metric)
    
    def _get_recent_metrics(self, provider: str, minutes: int = 10) -> List[PerformanceMetric]:
        """Get recent metrics for a provider"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            metric for metric in self._performance_metrics
            if metric.provider == provider and metric.timestamp >= cutoff
        ]
    
    def _analyze_trends(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance trends"""
        trends = {}
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in metrics:
            metrics_by_name[metric.metric_name].append(metric)
        
        # Analyze each metric type
        for metric_name, metric_list in metrics_by_name.items():
            if len(metric_list) < 3:
                continue
            
            # Sort by timestamp
            metric_list.sort(key=lambda x: x.timestamp)
            
            # Calculate trend
            values = [m.value for m in metric_list]
            if len(values) >= 3:
                # Simple trend analysis
                recent_avg = sum(values[-3:]) / 3
                older_avg = sum(values[:3]) / 3
                
                if recent_avg > older_avg * 1.1:
                    trend = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                trends[f"{metric_name}_trend"] = trend
                trends[f"{metric_name}_change"] = ((recent_avg - older_avg) / older_avg) * 100
        
        return trends
    
    async def _generate_performance_insights(self, provider: str, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance insights"""
        insights = {
            "provider": provider,
            "timestamp": datetime.utcnow().isoformat(),
            "trends": trends,
            "recommendations": []
        }
        
        # Generate recommendations based on trends
        for trend_key, trend_value in trends.items():
            if "response_time_trend" in trend_key and trend_value == "increasing":
                insights["recommendations"].append(
                    "Response times are increasing. Consider adding more connections or checking for network issues."
                )
            elif "success_rate_trend" in trend_key and trend_value == "decreasing":
                insights["recommendations"].append(
                    "Success rates are decreasing. Check for API issues or authentication problems."
                )
            elif "utilization_rate_trend" in trend_key and trend_value == "increasing":
                insights["recommendations"].append(
                    "Pool utilization is increasing. Consider scaling up the connection pool."
                )
        
        if not insights["recommendations"]:
            insights["recommendations"].append("Performance metrics are stable. No immediate actions needed.")
        
        return insights
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "providers": {},
            "alerts": {
                "active": [alert for alert in self._alerts if not alert.resolved],
                "recent": self._alerts[-10:],  # Last 10 alerts
                "summary": self._get_alert_summary()
            },
            "overall_health": await self._calculate_overall_health()
        }
        
        # Provider-specific data
        for provider, pool in self._pools.items():
            try:
                stats = await pool.get_stats()
                health = await pool.health_check()
                recent_metrics = self._get_recent_metrics(provider, minutes=5)
                
                dashboard["providers"][provider] = {
                    "stats": {
                        "total_connections": stats.total_connections,
                        "active_connections": stats.active_connections,
                        "utilization_rate": stats.utilization_rate,
                        "health_rate": stats.health_rate,
                        "avg_response_time_ms": stats.avg_response_time_ms,
                        "success_rate": stats.success_rate
                    },
                    "health": health,
                    "recent_metrics_count": len(recent_metrics),
                    "trends": self._analyze_trends(recent_metrics) if len(recent_metrics) > 3 else {}
                }
            except Exception as e:
                dashboard["providers"][provider] = {"error": str(e)}
        
        return dashboard
    
    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = [alert for alert in self._alerts if not alert.resolved]
        
        summary = {
            "total_active": len(active_alerts),
            "by_severity": defaultdict(int),
            "by_provider": defaultdict(int),
            "by_type": defaultdict(int)
        }
        
        for alert in active_alerts:
            summary["by_severity"][alert.severity] += 1
            summary["by_provider"][alert.provider] += 1
            summary["by_type"][alert.alert_type] += 1
        
        return dict(summary)
    
    async def _calculate_overall_health(self) -> Dict[str, Any]:
        """Calculate overall system health"""
        if not self._pools:
            return {"status": "unknown", "score": 0}
        
        total_score = 0
        provider_count = 0
        
        for provider, pool in self._pools.items():
            try:
                stats = await pool.get_stats()
                
                # Calculate provider score (0-100)
                health_score = stats.health_rate
                response_score = max(0, 100 - (stats.avg_response_time_ms / 20))
                success_score = stats.success_rate
                
                provider_score = (health_score + response_score + success_score) / 3
                total_score += provider_score
                provider_count += 1
                
            except Exception:
                provider_count += 1  # Count provider but with 0 score
        
        overall_score = total_score / provider_count if provider_count > 0 else 0
        
        if overall_score >= 80:
            status = "healthy"
        elif overall_score >= 60:
            status = "degraded"
        elif overall_score >= 40:
            status = "unhealthy"
        else:
            status = "critical"
        
        return {
            "status": status,
            "score": overall_score,
            "provider_count": provider_count
        }
    
    async def shutdown(self) -> None:
        """Shutdown the connection monitor"""
        logging.info("Shutting down Connection Monitor")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop all monitoring tasks
        for provider in list(self._monitoring_tasks.keys()):
            await self._stop_monitoring_tasks(provider)
        
        logging.info("Connection Monitor shutdown complete")


class PoolHealthChecker(IHealthChecker):
    """Health checker for connection pools"""
    
    async def check_connection_health(self, connection: Any) -> ConnectionStatus:
        """Check the health of a specific connection"""
        try:
            # This would be implemented by the specific pool
            # For now, assume healthy
            return ConnectionStatus.HEALTHY
        except Exception:
            return ConnectionStatus.UNHEALTHY
    
    async def check_pool_health(self, pool: IConnectionPool) -> Dict[str, Any]:
        """Check the health of an entire pool"""
        try:
            return await pool.health_check()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_health_recommendations(self, pool: IConnectionPool) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        try:
            health_result = await self.check_pool_health(pool)
            stats = await pool.get_stats()
            
            # Analyze health and provide recommendations
            if health_result.get("status") != "healthy":
                recommendations.append("Pool health check failed. Verify connection configurations.")
            
            if stats.health_rate < 80:
                recommendations.append("Low health rate. Check network connectivity and API keys.")
            
            if stats.utilization_rate > 90:
                recommendations.append("High utilization. Consider increasing pool size.")
            
            if stats.avg_response_time_ms > 2000:
                recommendations.append("High response times. Check for network latency or API issues.")
            
            if not recommendations:
                recommendations.append("Pool health is good. No immediate actions needed.")
        
        except Exception as e:
            recommendations.append(f"Unable to analyze pool health: {str(e)}")
        
        return recommendations


class MetricsCollector:
    """Metrics collector for connection pools"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self._metrics_storage: deque = deque(maxlen=50000)
        self._aggregated_metrics: Dict[str, Any] = {}
    
    async def collect_pool_metrics(self, provider: str, pool: IConnectionPool) -> None:
        """Collect metrics from a pool"""
        try:
            stats = await pool.get_stats()
            timestamp = datetime.utcnow()
            
            # Store detailed metrics
            metric_entry = {
                "provider": provider,
                "timestamp": timestamp,
                "stats": stats,
                "pool_config": pool.config
            }
            
            self._metrics_storage.append(metric_entry)
            
            # Update aggregated metrics
            await self._update_aggregated_metrics(provider, stats)
            
        except Exception as e:
            logging.error(f"Failed to collect metrics for {provider}: {e}")
    
    async def _update_aggregated_metrics(self, provider: str, stats: PoolStats) -> None:
        """Update aggregated metrics"""
        if provider not in self._aggregated_metrics:
            self._aggregated_metrics[provider] = {
                "total_requests": 0,
                "total_successful_requests": 0,
                "response_time_samples": deque(maxlen=1000),
                "last_updated": datetime.utcnow()
            }
        
        agg = self._aggregated_metrics[provider]
        agg["total_requests"] += stats.total_requests
        agg["total_successful_requests"] += stats.successful_requests
        agg["response_time_samples"].append(stats.avg_response_time_ms)
        agg["last_updated"] = datetime.utcnow()
    
    def get_metrics_summary(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics summary"""
        if provider and provider in self._aggregated_metrics:
            return {provider: self._aggregated_metrics[provider]}
        else:
            return dict(self._aggregated_metrics)
