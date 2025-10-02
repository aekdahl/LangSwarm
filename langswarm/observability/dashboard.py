"""
Real-time Dashboard for LangSwarm V2 Tool System

Provides web-based monitoring dashboard with real-time metrics,
performance visualization, and system health monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError:
    FastAPI = None
    WebSocket = None
    WebSocketDisconnect = None
    uvicorn = None

from .analytics import get_analytics, AnalyticsEvent, EventType

logger = logging.getLogger(__name__)


class DashboardManager:
    """
    Manages the real-time dashboard for monitoring the tool system.
    
    Features:
    - Real-time metrics display
    - Tool usage visualization
    - Performance monitoring
    - Cost tracking
    - Error analysis
    - Alert notifications
    """
    
    def __init__(self):
        self.app = None
        self.websocket_clients: List[WebSocket] = []
        self.analytics = get_analytics()
        self._running = False
        
        # Subscribe to analytics alerts
        self.analytics.add_alert_callback(self._handle_alert)
        
        if FastAPI:
            self._setup_app()
    
    def _setup_app(self):
        """Setup FastAPI application"""
        self.app = FastAPI(title="LangSwarm V2 Monitoring Dashboard")
        
        # Routes
        self.app.get("/")(self.dashboard_home)
        self.app.get("/api/metrics")(self.get_metrics)
        self.app.get("/api/performance")(self.get_performance)
        self.app.get("/api/events")(self.get_events)
        self.app.websocket("/ws")(self.websocket_endpoint)
    
    async def dashboard_home(self):
        """Serve the dashboard HTML"""
        return HTMLResponse(content=self._get_dashboard_html())
    
    async def get_metrics(self, period: str = "hour"):
        """Get current usage metrics"""
        try:
            metrics = self.analytics.get_usage_metrics(period)
            return {
                "timestamp": datetime.now().isoformat(),
                "period": period,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "average_execution_time": metrics.average_execution_time,
                "total_cost": metrics.total_cost,
                "most_used_tools": metrics.most_used_tools,
                "most_used_providers": metrics.most_used_providers,
                "error_patterns": metrics.error_patterns
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}
    
    async def get_performance(self):
        """Get performance metrics"""
        try:
            performance = self.analytics.get_performance_metrics()
            return {
                "timestamp": datetime.now().isoformat(),
                "tool_performance": performance.tool_performance,
                "provider_performance": performance.provider_performance,
                "latency_percentiles": performance.latency_percentiles,
                "throughput_metrics": performance.throughput_metrics
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_events(self, limit: int = 100, event_type: Optional[str] = None):
        """Get recent events"""
        try:
            events = self.analytics.export_events()
            
            # Filter by event type if specified
            if event_type:
                events = [e for e in events if e.get("event_type") == event_type]
            
            # Sort by timestamp (newest first) and limit
            events = sorted(events, key=lambda x: x["timestamp"], reverse=True)[:limit]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "count": len(events),
                "events": events
            }
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return {"error": str(e)}
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        self.websocket_clients.append(websocket)
        
        try:
            while True:
                # Send periodic updates
                await asyncio.sleep(1)
                
                # Send real-time metrics
                metrics = await self.get_metrics()
                performance = await self.get_performance()
                
                update = {
                    "type": "metrics_update",
                    "data": {
                        "metrics": metrics,
                        "performance": performance
                    }
                }
                
                await websocket.send_text(json.dumps(update))
                
        except WebSocketDisconnect:
            self.websocket_clients.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if websocket in self.websocket_clients:
                self.websocket_clients.remove(websocket)
    
    async def _handle_alert(self, alert_data: Dict[str, Any]):
        """Handle analytics alerts and broadcast to dashboard"""
        # Broadcast alert to all connected clients
        alert_message = {
            "type": "alert",
            "data": alert_data
        }
        
        message = json.dumps(alert_message)
        disconnected_clients = []
        
        for websocket in self.websocket_clients:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send alert to client: {e}")
                disconnected_clients.append(websocket)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.websocket_clients:
                self.websocket_clients.remove(client)
    
    def _get_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangSwarm V2 Monitoring Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem; }
        .header h1 { font-size: 1.5rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 1rem; }
        .metric { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
        .metric-value { font-weight: bold; color: #27ae60; }
        .error { color: #e74c3c; }
        .alert { background: #f39c12; color: white; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
        .chart-container { height: 200px; background: #ecf0f1; border-radius: 4px; margin-top: 1rem; display: flex; align-items: center; justify-content: center; }
        .tool-list { max-height: 200px; overflow-y: auto; }
        .tool-item { display: flex; justify-content: space-between; padding: 0.25rem 0; border-bottom: 1px solid #ecf0f1; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 0.5rem; }
        .status-healthy { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-error { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛠️ LangSwarm V2 Monitoring Dashboard</h1>
        <p>Real-time monitoring for LLM-agnostic tool system</p>
    </div>
    
    <div class="container">
        <div id="alerts"></div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span id="system-status"><span class="status-indicator status-healthy"></span>Healthy</span>
                </div>
                <div class="metric">
                    <span>Total Requests:</span>
                    <span class="metric-value" id="total-requests">-</span>
                </div>
                <div class="metric">
                    <span>Success Rate:</span>
                    <span class="metric-value" id="success-rate">-</span>
                </div>
                <div class="metric">
                    <span>Avg Response Time:</span>
                    <span class="metric-value" id="avg-response-time">-</span>
                </div>
                <div class="metric">
                    <span>Total Cost (Hour):</span>
                    <span class="metric-value" id="total-cost">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔧 Most Used Tools</h3>
                <div class="tool-list" id="tool-list">
                    <div class="tool-item">
                        <span>Loading...</span>
                        <span>-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🤖 Provider Performance</h3>
                <div class="tool-list" id="provider-list">
                    <div class="tool-item">
                        <span>Loading...</span>
                        <span>-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div class="metric">
                    <span>P95 Latency:</span>
                    <span class="metric-value" id="p95-latency">-</span>
                </div>
                <div class="metric">
                    <span>P99 Latency:</span>
                    <span class="metric-value" id="p99-latency">-</span>
                </div>
                <div class="chart-container">
                    <span>📈 Performance Chart</span>
                </div>
            </div>
            
            <div class="card">
                <h3>❌ Recent Errors</h3>
                <div class="tool-list" id="error-list">
                    <div class="tool-item">
                        <span>No errors</span>
                        <span class="metric-value">✅</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Usage Trends</h3>
                <div class="chart-container">
                    <span>📊 Usage Trend Chart</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'metrics_update') {
                updateMetrics(data.data.metrics);
                updatePerformance(data.data.performance);
            } else if (data.type === 'alert') {
                showAlert(data.data);
            }
        };
        
        function updateMetrics(metrics) {
            if (metrics.error) {
                console.error('Metrics error:', metrics.error);
                return;
            }
            
            document.getElementById('total-requests').textContent = metrics.total_requests || 0;
            document.getElementById('success-rate').textContent = 
                metrics.success_rate ? (metrics.success_rate * 100).toFixed(1) + '%' : '0%';
            document.getElementById('avg-response-time').textContent = 
                metrics.average_execution_time ? metrics.average_execution_time.toFixed(2) + 's' : '0s';
            document.getElementById('total-cost').textContent = 
                metrics.total_cost ? '$' + metrics.total_cost.toFixed(2) : '$0.00';
            
            // Update tool list
            const toolList = document.getElementById('tool-list');
            toolList.innerHTML = '';
            (metrics.most_used_tools || []).forEach(([tool, count]) => {
                const item = document.createElement('div');
                item.className = 'tool-item';
                item.innerHTML = `<span>${tool}</span><span>${count}</span>`;
                toolList.appendChild(item);
            });
            
            // Update provider list
            const providerList = document.getElementById('provider-list');
            providerList.innerHTML = '';
            (metrics.most_used_providers || []).forEach(([provider, count]) => {
                const item = document.createElement('div');
                item.className = 'tool-item';
                item.innerHTML = `<span>${provider}</span><span>${count}</span>`;
                providerList.appendChild(item);
            });
            
            // Update error list
            const errorList = document.getElementById('error-list');
            errorList.innerHTML = '';
            if (metrics.error_patterns && metrics.error_patterns.length > 0) {
                metrics.error_patterns.forEach(([error, count]) => {
                    const item = document.createElement('div');
                    item.className = 'tool-item';
                    item.innerHTML = `<span class="error">${error.substring(0, 30)}...</span><span>${count}</span>`;
                    errorList.appendChild(item);
                });
            } else {
                const item = document.createElement('div');
                item.className = 'tool-item';
                item.innerHTML = '<span>No errors</span><span class="metric-value">✅</span>';
                errorList.appendChild(item);
            }
        }
        
        function updatePerformance(performance) {
            if (performance.error) {
                console.error('Performance error:', performance.error);
                return;
            }
            
            const p95 = performance.latency_percentiles?.p95;
            const p99 = performance.latency_percentiles?.p99;
            
            document.getElementById('p95-latency').textContent = 
                p95 ? p95.toFixed(2) + 's' : '-';
            document.getElementById('p99-latency').textContent = 
                p99 ? p99.toFixed(2) + 's' : '-';
        }
        
        function showAlert(alert) {
            const alertsContainer = document.getElementById('alerts');
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert';
            alertDiv.innerHTML = `
                <strong>⚠️ ${alert.alert_type.toUpperCase()}</strong><br>
                ${alert.message}<br>
                <small>${new Date(alert.timestamp).toLocaleString()}</small>
            `;
            
            alertsContainer.appendChild(alertDiv);
            
            // Remove alert after 10 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 10000);
        }
        
        // Initial load
        fetch('/api/metrics')
            .then(response => response.json())
            .then(updateMetrics)
            .catch(console.error);
        
        fetch('/api/performance')
            .then(response => response.json())
            .then(updatePerformance)
            .catch(console.error);
    </script>
</body>
</html>
        """
    
    async def start_dashboard(self, host: str = "localhost", port: int = 8000):
        """Start the dashboard server"""
        if not self.app:
            raise RuntimeError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        self._running = True
        logger.info(f"Starting LangSwarm V2 Dashboard at http://{host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def stop_dashboard(self):
        """Stop the dashboard server"""
        self._running = False


# Global dashboard instance
_global_dashboard = DashboardManager()


def get_dashboard() -> DashboardManager:
    """Get the global dashboard manager"""
    return _global_dashboard


async def start_monitoring_dashboard(host: str = "localhost", port: int = 8000):
    """Start the monitoring dashboard"""
    dashboard = get_dashboard()
    await dashboard.start_dashboard(host, port)
