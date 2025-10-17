"""
LangSwarm E2E Test Monitoring and Debugging System

Real-time monitoring, performance analysis, and debugging tools
for comprehensive E2E test execution and system health monitoring.
"""

import asyncio
import json
import time
import psutil
import threading
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import logging


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    open_connections: int
    process_count: int


@dataclass
class TestMetrics:
    """Test-specific performance metrics."""
    test_id: str
    test_name: str
    timestamp: datetime
    status: str
    duration_ms: float
    api_calls: int
    tokens_used: int
    cost_usd: float
    memory_peak_mb: float
    cpu_peak_percent: float
    errors: List[str]
    warnings: List[str]


class SystemMonitor:
    """Real-time system monitoring during test execution."""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[SystemMetrics] = []
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[SystemMetrics], None]] = []
    
    def add_callback(self, callback: Callable[[SystemMetrics], None]):
        """Add callback for real-time metrics processing."""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """Start system monitoring in background thread."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        # Initialize baseline measurements
        net_io_start = psutil.net_io_counters()
        disk_io_start = psutil.disk_io_counters()
        
        while self.is_monitoring:
            try:
                # Current measurements
                net_io = psutil.net_io_counters()
                disk_io = psutil.disk_io_counters() 
                memory = psutil.virtual_memory()
                
                # Calculate deltas (handle None values)
                net_sent_mb = 0
                net_recv_mb = 0
                disk_read_mb = 0
                disk_write_mb = 0
                
                if net_io and net_io_start:
                    net_sent_mb = (net_io.bytes_sent - net_io_start.bytes_sent) / (1024 * 1024)
                    net_recv_mb = (net_io.bytes_recv - net_io_start.bytes_recv) / (1024 * 1024)
                
                if disk_io and disk_io_start:
                    disk_read_mb = (disk_io.read_bytes - disk_io_start.read_bytes) / (1024 * 1024)
                    disk_write_mb = (disk_io.write_bytes - disk_io_start.write_bytes) / (1024 * 1024)
                
                # Get connection count safely
                connection_count = 0
                try:
                    connection_count = len(psutil.net_connections())
                except (psutil.AccessDenied, AttributeError):
                    pass
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(timezone.utc),
                    cpu_percent=psutil.cpu_percent(),
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb,
                    network_sent_mb=net_sent_mb,
                    network_recv_mb=net_recv_mb,
                    open_connections=connection_count,
                    process_count=len(psutil.pids())
                )
                
                self.metrics_history.append(metrics)
                
                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logging.warning(f"Monitoring callback failed: {e}")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logging.error(f"System monitoring error: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_summary(self, last_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Get monitoring summary for specified time period."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        metrics = self.metrics_history
        
        if last_seconds:
            cutoff = datetime.now(timezone.utc).timestamp() - last_seconds
            metrics = [m for m in metrics if m.timestamp.timestamp() > cutoff]
        
        if not metrics:
            return {"error": "No metrics in specified time period"}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        
        return {
            "time_period_s": last_seconds,
            "sample_count": len(metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "peak_used_mb": max(m.memory_used_mb for m in metrics)
            },
            "network": {
                "total_sent_mb": sum(m.network_sent_mb for m in metrics),
                "total_recv_mb": sum(m.network_recv_mb for m in metrics)
            },
            "disk": {
                "total_read_mb": sum(m.disk_io_read_mb for m in metrics),
                "total_write_mb": sum(m.disk_io_write_mb for m in metrics)
            }
        }


class TestDatabase:
    """SQLite database for storing test execution history."""
    
    def __init__(self, db_path: str = "e2e_test_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    total_tests INTEGER,
                    passed INTEGER,
                    failed INTEGER,
                    errors INTEGER,
                    skipped INTEGER,
                    duration_s REAL,
                    total_cost_usd REAL,
                    total_tokens INTEGER,
                    config_hash TEXT
                );
                
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    test_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL,
                    api_calls INTEGER,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    error_message TEXT,
                    created_at TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
                );
                
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_io_read_mb REAL,
                    disk_io_write_mb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results (run_id);
                CREATE INDEX IF NOT EXISTS idx_system_metrics_run_id ON system_metrics (run_id);
                CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results (status);
            """)
    
    def store_test_run(self, run_data: Dict[str, Any]) -> str:
        """Store test run summary."""
        run_id = run_data.get("run_id", f"run_{int(time.time())}")
        summary = run_data.get("summary", {})
        performance = run_data.get("performance", {})
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO test_runs 
                (run_id, timestamp, total_tests, passed, failed, errors, skipped,
                 duration_s, total_cost_usd, total_tokens, config_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                run_data.get("timestamp"),
                summary.get("total", 0),
                summary.get("passed", 0),
                summary.get("failed", 0),
                summary.get("errors", 0),
                summary.get("skipped", 0),
                performance.get("total_duration_s", 0),
                performance.get("total_cost_usd", 0),
                performance.get("total_tokens", 0),
                run_data.get("config_hash", "")
            ))
        
        return run_id
    
    def store_test_result(self, run_id: str, test_result: Dict[str, Any]):
        """Store individual test result."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO test_results 
                (run_id, test_id, test_name, status, duration_ms, api_calls,
                 tokens_used, cost_usd, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                test_result.get("test_id"),
                test_result.get("test_name"),
                test_result.get("status"),
                test_result.get("duration_ms", 0),
                test_result.get("api_calls", 0),
                test_result.get("tokens_used", 0),
                test_result.get("cost_estimate", 0),
                json.dumps(test_result.get("errors", [])),
                datetime.now(timezone.utc).isoformat()
            ))
    
    def store_system_metrics(self, run_id: str, metrics: List[SystemMetrics]):
        """Store system metrics for a test run."""
        with sqlite3.connect(self.db_path) as conn:
            for metric in metrics:
                conn.execute("""
                    INSERT INTO system_metrics 
                    (run_id, timestamp, cpu_percent, memory_percent, memory_used_mb,
                     disk_io_read_mb, disk_io_write_mb, network_sent_mb, network_recv_mb)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    metric.timestamp.isoformat(),
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.memory_used_mb,
                    metric.disk_io_read_mb,
                    metric.disk_io_write_mb,
                    metric.network_sent_mb,
                    metric.network_recv_mb
                ))
    
    def get_test_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent test run history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM test_runs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        cutoff = (datetime.now(timezone.utc).timestamp() - (days * 24 * 3600))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Success rate trend
            success_rates = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(CAST(passed AS FLOAT) / total_tests * 100) as success_rate,
                    COUNT(*) as runs
                FROM test_runs 
                WHERE timestamp > datetime(?, 'unixepoch')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (cutoff,)).fetchall()
            
            # Performance trend
            performance = conn.execute("""
                SELECT 
                    AVG(duration_s) as avg_duration,
                    AVG(total_cost_usd) as avg_cost,
                    AVG(total_tokens) as avg_tokens
                FROM test_runs 
                WHERE timestamp > datetime(?, 'unixepoch')
            """, (cutoff,)).fetchone()
            
            # Most common failures
            failures = conn.execute("""
                SELECT 
                    test_name,
                    COUNT(*) as failure_count,
                    GROUP_CONCAT(DISTINCT error_message) as error_types
                FROM test_results 
                WHERE status IN ('FAIL', 'ERROR')
                  AND created_at > datetime(?, 'unixepoch')
                GROUP BY test_name
                ORDER BY failure_count DESC
                LIMIT 10
            """, (cutoff,)).fetchall()
            
            return {
                "success_rate_trend": [dict(row) for row in success_rates],
                "performance_averages": dict(performance) if performance else {},
                "common_failures": [dict(row) for row in failures]
            }


class RealTimeDebugger:
    """Real-time debugging and alerting system."""
    
    def __init__(self, alert_thresholds: Dict[str, float] = None):
        self.alert_thresholds = alert_thresholds or {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "cost_per_test": 0.50,
            "test_duration_s": 60.0,
            "error_rate": 0.3
        }
        self.alerts: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("e2e_debugger")
    
    def check_system_health(self, metrics: SystemMetrics):
        """Check system health and trigger alerts."""
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "message": f"High CPU usage: {metrics.cpu_percent:.1f}%",
                "timestamp": metrics.timestamp,
                "value": metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"]
            })
        
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "message": f"High memory usage: {metrics.memory_percent:.1f}%",
                "timestamp": metrics.timestamp,
                "value": metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"]
            })
        
        for alert in alerts:
            self.alerts.append(alert)
            self.logger.warning(f"ALERT: {alert['message']}")
    
    def check_test_performance(self, test_metrics: TestMetrics):
        """Check individual test performance."""
        alerts = []
        
        duration_s = test_metrics.duration_ms / 1000
        if duration_s > self.alert_thresholds["test_duration_s"]:
            alerts.append({
                "type": "performance",
                "level": "warning", 
                "message": f"Slow test: {test_metrics.test_name} ({duration_s:.1f}s)",
                "test_id": test_metrics.test_id,
                "value": duration_s,
                "threshold": self.alert_thresholds["test_duration_s"]
            })
        
        if test_metrics.cost_usd > self.alert_thresholds["cost_per_test"]:
            alerts.append({
                "type": "cost",
                "level": "warning",
                "message": f"Expensive test: {test_metrics.test_name} (${test_metrics.cost_usd:.3f})",
                "test_id": test_metrics.test_id,
                "value": test_metrics.cost_usd,
                "threshold": self.alert_thresholds["cost_per_test"]
            })
        
        for alert in alerts:
            self.alerts.append(alert)
            self.logger.warning(f"TEST ALERT: {alert['message']}")
    
    def get_active_alerts(self, last_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cutoff = datetime.now(timezone.utc).timestamp() - (last_minutes * 60)
        
        return [
            alert for alert in self.alerts
            if alert.get("timestamp", datetime.now(timezone.utc)).timestamp() > cutoff
        ]
    
    def generate_debug_report(self) -> Dict[str, Any]:
        """Generate comprehensive debugging report."""
        recent_alerts = self.get_active_alerts(60)  # Last hour
        
        alert_summary = {}
        for alert in recent_alerts:
            alert_type = alert.get("type", "unknown")
            alert_summary[alert_type] = alert_summary.get(alert_type, 0) + 1
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(recent_alerts),
            "alert_types": alert_summary,
            "recent_alerts": recent_alerts[-10:],  # Last 10 alerts
            "system_health": "degraded" if len(recent_alerts) > 5 else "good",
            "recommendations": self._generate_recommendations(recent_alerts)
        }
    
    def _generate_recommendations(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on alerts."""
        recommendations = []
        
        system_alerts = [a for a in alerts if a.get("type") == "system"]
        performance_alerts = [a for a in alerts if a.get("type") == "performance"]
        cost_alerts = [a for a in alerts if a.get("type") == "cost"]
        
        if system_alerts:
            recommendations.append("Consider reducing test parallelism to lower system load")
            recommendations.append("Monitor system resources before running tests")
        
        if performance_alerts:
            recommendations.append("Review slow tests for optimization opportunities")
            recommendations.append("Consider implementing test timeouts")
        
        if cost_alerts:
            recommendations.append("Review expensive tests and consider mocking")
            recommendations.append("Set stricter cost limits for test execution")
        
        return recommendations


@asynccontextmanager
async def monitoring_context(monitor_interval: float = 1.0, store_metrics: bool = True):
    """Context manager for test monitoring with automatic cleanup."""
    
    monitor = SystemMonitor(monitor_interval)
    debugger = RealTimeDebugger()
    database = TestDatabase() if store_metrics else None
    
    # Set up monitoring callbacks
    monitor.add_callback(debugger.check_system_health)
    
    try:
        monitor.start_monitoring()
        
        yield {
            "monitor": monitor,
            "debugger": debugger,
            "database": database
        }
        
    finally:
        monitor.stop_monitoring()
        
        # Generate final report
        debug_report = debugger.generate_debug_report()
        
        print("\n🔍 DEBUGGING SUMMARY")
        print("-" * 40)
        print(f"System Health: {debug_report['system_health'].upper()}")
        print(f"Total Alerts: {debug_report['total_alerts']}")
        
        if debug_report['recommendations']:
            print("\n💡 Recommendations:")
            for rec in debug_report['recommendations']:
                print(f"  • {rec}")