"""
Navigation Analytics Dashboard API

This module provides a FastAPI-based dashboard for real-time navigation
analytics, performance monitoring, and optimization insights.
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import logging

from .tracker import NavigationTracker, NavigationDecision, NavigationAnalytics

logger = logging.getLogger(__name__)


class DashboardMetrics(BaseModel):
    """Real-time dashboard metrics"""
    total_decisions_today: int
    avg_confidence_today: float
    decisions_per_hour: List[Dict[str, Any]]
    top_workflows: List[Dict[str, Any]]
    performance_status: str
    alerts: List[str]


class NavigationInsight(BaseModel):
    """Navigation optimization insight"""
    workflow_id: str
    insight_type: str
    title: str
    description: str
    impact: str
    suggested_action: str
    confidence: float


class NavigationDashboard:
    """
    Navigation analytics dashboard providing real-time insights,
    performance monitoring, and optimization recommendations.
    """
    
    def __init__(self, tracker: NavigationTracker, port: int = 8080):
        self.tracker = tracker
        self.app = FastAPI(title="Navigation Analytics Dashboard", version="1.0.0")
        self.port = port
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes for the dashboard"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard page"""
            return self._render_dashboard_html()
        
        @self.app.get("/api/metrics", response_model=DashboardMetrics)
        async def get_metrics():
            """Get real-time dashboard metrics"""
            return await self._get_dashboard_metrics()
        
        @self.app.get("/api/analytics/{workflow_id}")
        async def get_workflow_analytics(workflow_id: str, days: int = Query(30, ge=1, le=365)):
            """Get analytics for a specific workflow"""
            analytics = self.tracker.get_analytics(workflow_id=workflow_id, days=days)
            return analytics
        
        @self.app.get("/api/decisions")
        async def get_decisions(
            workflow_id: Optional[str] = Query(None),
            agent_id: Optional[str] = Query(None),
            hours: int = Query(24, ge=1, le=168),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Get recent navigation decisions"""
            start_time = datetime.now() - timedelta(hours=hours)
            decisions = self.tracker.get_decisions(
                workflow_id=workflow_id,
                agent_id=agent_id,
                start_time=start_time,
                limit=limit
            )
            
            return {
                "decisions": [
                    {
                        "decision_id": d.decision_id,
                        "workflow_id": d.workflow_id,
                        "step_id": d.step_id,
                        "chosen_step": d.chosen_step,
                        "reasoning": d.reasoning,
                        "confidence": d.confidence,
                        "timestamp": d.timestamp.isoformat(),
                        "execution_time_ms": d.execution_time_ms
                    }
                    for d in decisions
                ],
                "total_count": len(decisions),
                "filters": {
                    "workflow_id": workflow_id,
                    "agent_id": agent_id,
                    "hours": hours
                }
            }
        
        @self.app.get("/api/insights")
        async def get_insights(workflow_id: Optional[str] = Query(None)):
            """Get optimization insights and recommendations"""
            insights = await self._generate_insights(workflow_id)
            return {"insights": insights}
        
        @self.app.get("/api/performance")
        async def get_performance_metrics():
            """Get performance metrics and health status"""
            return await self._get_performance_metrics()
        
        @self.app.get("/api/workflows")
        async def get_workflows():
            """Get list of workflows with navigation data"""
            decisions = self.tracker.get_decisions(limit=10000)
            
            workflow_stats = {}
            for decision in decisions:
                wf_id = decision.workflow_id
                if wf_id not in workflow_stats:
                    workflow_stats[wf_id] = {
                        "workflow_id": wf_id,
                        "total_decisions": 0,
                        "avg_confidence": 0.0,
                        "last_activity": None,
                        "most_common_step": None
                    }
                
                stats = workflow_stats[wf_id]
                stats["total_decisions"] += 1
                stats["avg_confidence"] = (
                    (stats["avg_confidence"] * (stats["total_decisions"] - 1) + decision.confidence) 
                    / stats["total_decisions"]
                )
                
                if not stats["last_activity"] or decision.timestamp > stats["last_activity"]:
                    stats["last_activity"] = decision.timestamp.isoformat()
            
            return {"workflows": list(workflow_stats.values())}
        
        @self.app.post("/api/clear-old-data")
        async def clear_old_data(days: int = Query(90, ge=30, le=365)):
            """Clear old navigation data"""
            try:
                self.tracker.clear_old_decisions(days=days)
                return {"message": f"Successfully cleared data older than {days} days"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_dashboard_metrics(self) -> DashboardMetrics:
        """Generate real-time dashboard metrics"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's decisions
        today_decisions = self.tracker.get_decisions(start_time=today_start, limit=10000)
        
        # Calculate hourly distribution
        hourly_counts = {}
        for i in range(24):
            hour_start = today_start + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            count = len([d for d in today_decisions if hour_start <= d.timestamp < hour_end])
            hourly_counts[i] = count
        
        decisions_per_hour = [
            {"hour": f"{i:02d}:00", "count": hourly_counts.get(i, 0)}
            for i in range(24)
        ]
        
        # Top workflows
        workflow_counts = {}
        for decision in today_decisions:
            wf_id = decision.workflow_id
            workflow_counts[wf_id] = workflow_counts.get(wf_id, 0) + 1
        
        top_workflows = [
            {"workflow_id": wf_id, "decision_count": count}
            for wf_id, count in sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Performance status
        avg_confidence = sum(d.confidence for d in today_decisions) / len(today_decisions) if today_decisions else 0.0
        performance_status = "excellent" if avg_confidence > 0.8 else "good" if avg_confidence > 0.6 else "needs_attention"
        
        # Alerts
        alerts = []
        if avg_confidence < 0.5:
            alerts.append("Low average confidence detected - review navigation logic")
        
        error_decisions = [d for d in today_decisions if d.chosen_step == "ERROR"]
        if len(error_decisions) > len(today_decisions) * 0.1:
            alerts.append("High error rate detected - check navigation configuration")
        
        return DashboardMetrics(
            total_decisions_today=len(today_decisions),
            avg_confidence_today=avg_confidence,
            decisions_per_hour=decisions_per_hour,
            top_workflows=top_workflows,
            performance_status=performance_status,
            alerts=alerts
        )
    
    async def _generate_insights(self, workflow_id: Optional[str] = None) -> List[NavigationInsight]:
        """Generate optimization insights"""
        analytics = self.tracker.get_analytics(workflow_id=workflow_id, days=30)
        insights = []
        
        # Low confidence insight
        if analytics.avg_confidence < 0.7:
            insights.append(NavigationInsight(
                workflow_id=workflow_id or "all",
                insight_type="confidence",
                title="Low Navigation Confidence",
                description=f"Average confidence is {analytics.avg_confidence:.2f}, below optimal threshold of 0.7",
                impact="Medium",
                suggested_action="Review step descriptions and context data quality",
                confidence=0.9
            ))
        
        # Performance insight
        avg_time = analytics.performance_metrics.get("avg_execution_time_ms", 0)
        if avg_time > 500:
            insights.append(NavigationInsight(
                workflow_id=workflow_id or "all",
                insight_type="performance",
                title="Slow Navigation Decisions",
                description=f"Average decision time is {avg_time:.1f}ms, above optimal threshold of 500ms",
                impact="Low",
                suggested_action="Optimize step evaluation logic or reduce available options",
                confidence=0.8
            ))
        
        # Pattern analysis
        if analytics.most_common_paths:
            dominant_path = analytics.most_common_paths[0]
            if dominant_path["percentage"] > 70:
                insights.append(NavigationInsight(
                    workflow_id=workflow_id or "all",
                    insight_type="pattern",
                    title="Dominant Navigation Path",
                    description=f"Path '{dominant_path['path']}' accounts for {dominant_path['percentage']:.1f}% of decisions",
                    impact="Medium",
                    suggested_action="Consider if this path should be made the default or if more variety is needed",
                    confidence=0.7
                ))
        
        return insights
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        analytics = self.tracker.get_analytics(days=7)
        
        return {
            "system_health": {
                "total_decisions_week": analytics.total_decisions,
                "average_confidence": analytics.avg_confidence,
                "error_rate": analytics.performance_metrics.get("low_confidence_decisions", 0) / max(analytics.total_decisions, 1),
                "avg_response_time_ms": analytics.performance_metrics.get("avg_execution_time_ms", 0)
            },
            "optimization_status": {
                "suggestions_count": len(analytics.optimization_suggestions),
                "critical_issues": len([s for s in analytics.optimization_suggestions if "loop" in s.lower()]),
                "performance_grade": self._calculate_performance_grade(analytics)
            },
            "trends": {
                "confidence_trend": "stable",  # Would need historical data to calculate
                "volume_trend": "stable",
                "error_trend": "stable"
            }
        }
    
    def _calculate_performance_grade(self, analytics: NavigationAnalytics) -> str:
        """Calculate overall performance grade"""
        score = 0
        
        # Confidence score (40% weight)
        if analytics.avg_confidence >= 0.8:
            score += 40
        elif analytics.avg_confidence >= 0.6:
            score += 30
        elif analytics.avg_confidence >= 0.4:
            score += 20
        
        # Performance score (30% weight)
        avg_time = analytics.performance_metrics.get("avg_execution_time_ms", 1000)
        if avg_time <= 200:
            score += 30
        elif avg_time <= 500:
            score += 20
        elif avg_time <= 1000:
            score += 10
        
        # Error rate score (30% weight)
        error_rate = analytics.performance_metrics.get("low_confidence_decisions", 0) / max(analytics.total_decisions, 1)
        if error_rate <= 0.05:
            score += 30
        elif error_rate <= 0.15:
            score += 20
        elif error_rate <= 0.3:
            score += 10
        
        if score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _render_dashboard_html(self) -> str:
        """Render the main dashboard HTML page"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Navigation Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { text-align: center; margin: 10px 0; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2563eb; }
        .metric-label { color: #6b7280; margin-top: 5px; }
        .alert { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status-excellent { color: #059669; }
        .status-good { color: #d97706; }
        .status-needs_attention { color: #dc2626; }
        h1 { color: #1f2937; text-align: center; }
        h2 { color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
    </style>
</head>
<body>
    <h1>🧭 Navigation Analytics Dashboard</h1>
    
    <div class="dashboard">
        <div class="card">
            <h2>📊 Today's Metrics</h2>
            <div id="metrics-content">Loading...</div>
        </div>
        
        <div class="card">
            <h2>📈 Hourly Decisions</h2>
            <canvas id="hourlyChart" width="400" height="200"></canvas>
        </div>
        
        <div class="card">
            <h2>🏆 Top Workflows</h2>
            <div id="workflows-content">Loading...</div>
        </div>
        
        <div class="card">
            <h2>🔍 System Health</h2>
            <div id="performance-content">Loading...</div>
        </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
        <h2>💡 Optimization Insights</h2>
        <div id="insights-content">Loading...</div>
    </div>

    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                const [metrics, performance, insights] = await Promise.all([
                    fetch('/api/metrics').then(r => r.json()),
                    fetch('/api/performance').then(r => r.json()),
                    fetch('/api/insights').then(r => r.json())
                ]);
                
                updateMetrics(metrics);
                updateChart(metrics.decisions_per_hour);
                updateWorkflows(metrics.top_workflows);
                updatePerformance(performance);
                updateInsights(insights.insights);
                
            } catch (error) {
                console.error('Failed to load dashboard:', error);
            }
        }
        
        function updateMetrics(metrics) {
            const statusClass = `status-${metrics.performance_status}`;
            const alertsHtml = metrics.alerts.map(alert => `<div class="alert">${alert}</div>`).join('');
            
            document.getElementById('metrics-content').innerHTML = `
                <div class="metric">
                    <div class="metric-value">${metrics.total_decisions_today}</div>
                    <div class="metric-label">Decisions Today</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${(metrics.avg_confidence_today * 100).toFixed(1)}%</div>
                    <div class="metric-label">Avg Confidence</div>
                </div>
                <div class="metric">
                    <div class="metric-value ${statusClass}">${metrics.performance_status.replace('_', ' ')}</div>
                    <div class="metric-label">Performance Status</div>
                </div>
                ${alertsHtml}
            `;
        }
        
        function updateChart(hourlyData) {
            const ctx = document.getElementById('hourlyChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: hourlyData.map(d => d.hour),
                    datasets: [{
                        label: 'Decisions per Hour',
                        data: hourlyData.map(d => d.count),
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
        
        function updateWorkflows(workflows) {
            const html = workflows.map(wf => `
                <div style="margin: 10px 0; padding: 10px; background: #f9fafb; border-radius: 4px;">
                    <strong>${wf.workflow_id}</strong><br>
                    <small>${wf.decision_count} decisions</small>
                </div>
            `).join('');
            document.getElementById('workflows-content').innerHTML = html || '<p>No workflows found</p>';
        }
        
        function updatePerformance(performance) {
            const health = performance.system_health;
            const grade = performance.optimization_status.performance_grade;
            
            document.getElementById('performance-content').innerHTML = `
                <div class="metric">
                    <div class="metric-value">${grade}</div>
                    <div class="metric-label">Performance Grade</div>
                </div>
                <div style="margin-top: 15px;">
                    <div>Response Time: ${health.avg_response_time_ms.toFixed(1)}ms</div>
                    <div>Error Rate: ${(health.error_rate * 100).toFixed(1)}%</div>
                    <div>Week Total: ${health.total_decisions_week} decisions</div>
                </div>
            `;
        }
        
        function updateInsights(insights) {
            const html = insights.map(insight => `
                <div style="margin: 10px 0; padding: 15px; background: #fefce8; border-left: 4px solid #eab308; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #92400e;">${insight.title}</h4>
                    <p style="margin: 5px 0; color: #78716c;">${insight.description}</p>
                    <p style="margin: 5px 0; font-weight: bold; color: #1f2937;">Action: ${insight.suggested_action}</p>
                    <small style="color: #6b7280;">Impact: ${insight.impact} | Confidence: ${(insight.confidence * 100).toFixed(0)}%</small>
                </div>
            `).join('');
            document.getElementById('insights-content').innerHTML = html || '<p>No insights available. System is performing well! 🎉</p>';
        }
        
        // Load dashboard on page load and refresh every 30 seconds
        loadDashboard();
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "0.0.0.0"):
        """Run the dashboard server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=self.port)


# Convenience function to create and run dashboard
def create_navigation_dashboard(tracking_db: str = "navigation_decisions.db", port: int = 8080) -> NavigationDashboard:
    """Create a navigation dashboard instance"""
    tracker = NavigationTracker(tracking_db)
    return NavigationDashboard(tracker, port) 