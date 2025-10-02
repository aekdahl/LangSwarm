# LangSwarm V2 Workflow Monitoring & Debugging

**Comprehensive guide for monitoring, debugging, and analyzing workflow execution**

## 🎯 Overview

LangSwarm V2 provides a comprehensive monitoring and debugging system for workflow execution. Get real-time insights, performance metrics, execution tracing, and automated failure analysis to ensure your workflows run smoothly in production.

**Key Features:**
- **Real-time Monitoring**: Live execution tracking and status updates
- **Performance Analytics**: Execution metrics, bottleneck detection, optimization recommendations
- **Event System**: Comprehensive event publishing and subscription
- **Debugging Tools**: Step-by-step execution analysis and failure investigation
- **Health Monitoring**: System health and performance tracking

---

## 🚀 Quick Start

### **Basic Monitoring Setup**

```python
from langswarm.core.workflows import get_workflow_monitor, execute_workflow

# Get the global workflow monitor
monitor = get_workflow_monitor()

# Subscribe to workflow events
async def on_workflow_event(event):
    print(f"Event: {event.type} - {event.workflow_id} - {event.data}")

await monitor.subscribe_to_events(on_workflow_event)

# Execute workflow with monitoring
result = await execute_workflow("my_workflow", {"input": "data"})

# Get execution metrics
metrics = await monitor.get_execution_metrics(result.execution_id)
print(f"Duration: {metrics.total_duration_ms}ms")
print(f"Success rate: {metrics.success_rate}")
```

### **Real-time Workflow Monitoring**

```python
# Monitor specific workflow in real-time
async def workflow_callback(event):
    if event.type == "step_started":
        print(f"▶️ Starting step: {event.step_id}")
    elif event.type == "step_completed":
        print(f"✅ Completed step: {event.step_id} ({event.duration_ms}ms)")
    elif event.type == "step_failed":
        print(f"❌ Failed step: {event.step_id} - {event.error}")

await monitor.subscribe_to_workflow("data_analysis", workflow_callback)

# Start workflow - events will be sent to callback
result = await execute_workflow("data_analysis", {"input": "sample data"})
```

---

## 📊 Workflow Monitor

### **WorkflowMonitor Features**

```python
from langswarm.core.workflows.monitoring import WorkflowMonitor

# Create monitor instance
monitor = WorkflowMonitor()

# Real-time monitoring capabilities
await monitor.start_monitoring()

# Subscribe to different event types
await monitor.subscribe_to_events(callback, event_types=["step_completed", "workflow_failed"])
await monitor.subscribe_to_workflow("specific_workflow", workflow_specific_callback)
await monitor.subscribe_to_executions(execution_callback)

# Get comprehensive metrics
workflow_metrics = await monitor.get_workflow_metrics("workflow_id")
execution_metrics = await monitor.get_execution_metrics("execution_id")
system_metrics = await monitor.get_system_metrics()
```

### **Event Types**

```python
# Available event types for subscription
event_types = [
    # Workflow-level events
    "workflow_started",
    "workflow_completed", 
    "workflow_failed",
    "workflow_cancelled",
    
    # Step-level events
    "step_started",
    "step_completed",
    "step_failed",
    "step_retried",
    "step_skipped",
    
    # Execution events
    "execution_created",
    "execution_queued",
    "execution_running",
    "execution_finished",
    
    # System events
    "system_health_check",
    "performance_alert",
    "resource_warning"
]

# Subscribe to specific events
await monitor.subscribe_to_events(callback, event_types=["step_failed", "workflow_failed"])
```

### **Metrics Collection**

#### **Execution Metrics**
```python
# Get detailed execution metrics
execution_metrics = await monitor.get_execution_metrics("exec_123")

print(f"Execution ID: {execution_metrics.execution_id}")
print(f"Workflow ID: {execution_metrics.workflow_id}")
print(f"Status: {execution_metrics.status}")
print(f"Start Time: {execution_metrics.start_time}")
print(f"End Time: {execution_metrics.end_time}")
print(f"Total Duration: {execution_metrics.total_duration_ms}ms")
print(f"Step Count: {execution_metrics.step_count}")
print(f"Successful Steps: {execution_metrics.successful_steps}")
print(f"Failed Steps: {execution_metrics.failed_steps}")
print(f"Success Rate: {execution_metrics.success_rate:.2%}")

# Step-level metrics
for step_id, step_metrics in execution_metrics.step_metrics.items():
    print(f"Step {step_id}:")
    print(f"  Duration: {step_metrics.duration_ms}ms")
    print(f"  Status: {step_metrics.status}")
    print(f"  Retry Count: {step_metrics.retry_count}")
```

#### **Workflow Metrics**
```python
# Get aggregated workflow metrics
workflow_metrics = await monitor.get_workflow_metrics("data_analysis")

print(f"Workflow: {workflow_metrics.workflow_id}")
print(f"Total Executions: {workflow_metrics.total_executions}")
print(f"Successful Executions: {workflow_metrics.successful_executions}")
print(f"Failed Executions: {workflow_metrics.failed_executions}")
print(f"Success Rate: {workflow_metrics.success_rate:.2%}")
print(f"Average Duration: {workflow_metrics.average_duration_ms}ms")
print(f"Min Duration: {workflow_metrics.min_duration_ms}ms")
print(f"Max Duration: {workflow_metrics.max_duration_ms}ms")
print(f"P95 Duration: {workflow_metrics.p95_duration_ms}ms")

# Performance trends
print(f"Last 24h Executions: {workflow_metrics.executions_24h}")
print(f"Last 7d Success Rate: {workflow_metrics.success_rate_7d:.2%}")
print(f"Performance Trend: {workflow_metrics.performance_trend}")  # improving/degrading/stable
```

#### **System Metrics**
```python
# Get system-wide metrics
system_metrics = await monitor.get_system_metrics()

print(f"Total Workflows: {system_metrics.total_workflows}")
print(f"Active Executions: {system_metrics.active_executions}")
print(f"Queued Executions: {system_metrics.queued_executions}")
print(f"System Load: {system_metrics.system_load}")
print(f"Memory Usage: {system_metrics.memory_usage_mb}MB")
print(f"CPU Usage: {system_metrics.cpu_usage_percent}%")
print(f"Throughput: {system_metrics.executions_per_hour}/hour")

# Health indicators
print(f"Overall Health: {system_metrics.health_score}/100")
for component, health in system_metrics.component_health.items():
    print(f"  {component}: {health.status} ({health.score}/100)")
```

---

## 🔍 Workflow Debugger

### **WorkflowDebugger Features**

```python
from langswarm.core.workflows.monitoring import WorkflowDebugger

# Create debugger instance
debugger = WorkflowDebugger()

# Analyze failed execution
failed_execution_id = "exec_failed_123"
analysis = await debugger.analyze_execution_failure(failed_execution_id)

print(f"Failure Analysis for {failed_execution_id}:")
print(f"Root Cause: {analysis.root_cause}")
print(f"Failed Step: {analysis.failed_step_id}")
print(f"Error Type: {analysis.error_type}")
print(f"Failure Pattern: {analysis.failure_pattern}")

print("\nRecommendations:")
for recommendation in analysis.recommendations:
    print(f"  - {recommendation.action}: {recommendation.description}")
    print(f"    Impact: {recommendation.expected_impact}")
```

### **Execution Tracing**

```python
# Get detailed execution trace
trace = await debugger.get_execution_trace("exec_123")

print(f"Execution Trace for {trace.execution_id}:")
print(f"Workflow: {trace.workflow_id}")
print(f"Total Steps: {len(trace.step_traces)}")

for step_trace in trace.step_traces:
    print(f"\nStep: {step_trace.step_id}")
    print(f"  Type: {step_trace.step_type}")
    print(f"  Status: {step_trace.status}")
    print(f"  Start: {step_trace.start_time}")
    print(f"  Duration: {step_trace.duration_ms}ms")
    
    if step_trace.inputs:
        print(f"  Inputs: {step_trace.inputs}")
    if step_trace.outputs:
        print(f"  Outputs: {step_trace.outputs}")
    if step_trace.error:
        print(f"  Error: {step_trace.error}")
    
    # Show variable resolution
    if step_trace.template_resolution:
        print(f"  Template Resolution:")
        for template, resolved in step_trace.template_resolution.items():
            print(f"    {template} -> {resolved}")
```

### **Performance Analysis**

```python
# Analyze workflow performance
performance_analysis = await debugger.analyze_workflow_performance("data_analysis")

print(f"Performance Analysis for data_analysis:")
print(f"Average Execution Time: {performance_analysis.average_duration_ms}ms")
print(f"Performance Rating: {performance_analysis.performance_rating}/100")

# Bottleneck identification
print("\nBottlenecks:")
for bottleneck in performance_analysis.bottlenecks:
    print(f"  Step: {bottleneck.step_id}")
    print(f"  Avg Duration: {bottleneck.average_duration_ms}ms")
    print(f"  % of Total Time: {bottleneck.time_percentage:.1f}%")
    print(f"  Recommendation: {bottleneck.recommendation}")

# Performance recommendations
print("\nOptimization Recommendations:")
for rec in performance_analysis.recommendations:
    print(f"  {rec.priority}: {rec.title}")
    print(f"    {rec.description}")
    print(f"    Expected Improvement: {rec.expected_improvement}")
```

### **Failure Pattern Analysis**

```python
# Analyze failure patterns across executions
failure_analysis = await debugger.analyze_failure_patterns("data_analysis", days=7)

print(f"Failure Pattern Analysis (Last 7 days):")
print(f"Total Failures: {failure_analysis.total_failures}")
print(f"Failure Rate: {failure_analysis.failure_rate:.2%}")

# Common failure patterns
print("\nCommon Failure Patterns:")
for pattern in failure_analysis.patterns:
    print(f"  Pattern: {pattern.name}")
    print(f"  Occurrences: {pattern.count}")
    print(f"  Steps Affected: {pattern.affected_steps}")
    print(f"  Root Cause: {pattern.root_cause}")
    print(f"  Suggested Fix: {pattern.suggested_fix}")

# Failure hotspots
print("\nFailure Hotspots:")
for hotspot in failure_analysis.hotspots:
    print(f"  Step: {hotspot.step_id}")
    print(f"  Failure Rate: {hotspot.failure_rate:.2%}")
    print(f"  Common Errors: {hotspot.common_errors}")
```

---

## 📈 Performance Monitoring

### **Real-time Performance Tracking**

```python
# Monitor performance in real-time
async def performance_monitor():
    """Real-time performance monitoring"""
    
    while True:
        # Get current system metrics
        metrics = await monitor.get_system_metrics()
        
        # Check for performance issues
        if metrics.cpu_usage_percent > 80:
            print(f"⚠️ High CPU usage: {metrics.cpu_usage_percent}%")
        
        if metrics.memory_usage_mb > 1000:
            print(f"⚠️ High memory usage: {metrics.memory_usage_mb}MB")
        
        if metrics.active_executions > 50:
            print(f"⚠️ High execution load: {metrics.active_executions} active")
        
        # Check workflow health
        unhealthy_workflows = await monitor.get_unhealthy_workflows()
        for workflow_id, health in unhealthy_workflows.items():
            print(f"🔴 Unhealthy workflow: {workflow_id} - {health.issue}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# Start performance monitoring
asyncio.create_task(performance_monitor())
```

### **Performance Alerts**

```python
# Configure performance alerts
alert_config = {
    "execution_duration_threshold": 300000,  # 5 minutes in ms
    "failure_rate_threshold": 0.1,           # 10% failure rate
    "memory_usage_threshold": 1000,          # 1GB memory usage
    "queue_length_threshold": 20             # 20 queued executions
}

await monitor.configure_alerts(alert_config)

# Alert callback
async def handle_performance_alert(alert):
    print(f"🚨 Performance Alert: {alert.type}")
    print(f"Severity: {alert.severity}")
    print(f"Description: {alert.description}")
    print(f"Affected Component: {alert.component}")
    print(f"Recommended Action: {alert.recommended_action}")
    
    # Take automated action for critical alerts
    if alert.severity == "critical":
        if alert.type == "high_failure_rate":
            # Pause new executions
            await monitor.pause_workflow_executions(alert.workflow_id)
        elif alert.type == "memory_exhaustion":
            # Trigger garbage collection
            await monitor.trigger_memory_cleanup()

await monitor.subscribe_to_alerts(handle_performance_alert)
```

### **Historical Performance Analysis**

```python
# Analyze historical performance trends
historical_analysis = await monitor.get_historical_analysis(
    workflow_id="data_analysis",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

print(f"30-Day Performance Analysis:")
print(f"Total Executions: {historical_analysis.total_executions}")
print(f"Average Success Rate: {historical_analysis.average_success_rate:.2%}")
print(f"Performance Trend: {historical_analysis.performance_trend}")

# Daily breakdown
for day, day_metrics in historical_analysis.daily_metrics.items():
    print(f"{day}: {day_metrics.executions} executions, "
          f"{day_metrics.success_rate:.1%} success, "
          f"{day_metrics.avg_duration_ms}ms avg")

# Performance improvements/degradations
for change in historical_analysis.performance_changes:
    print(f"Performance Change on {change.date}:")
    print(f"  Type: {change.type}")  # improvement/degradation
    print(f"  Magnitude: {change.percentage_change:.1f}%")
    print(f"  Likely Cause: {change.likely_cause}")
```

---

## 🔧 Custom Monitoring

### **Custom Event Publishers**

```python
from langswarm.core.workflows.monitoring import WorkflowEvent

# Publish custom events during workflow execution
class CustomWorkflowStep:
    async def execute(self, context, inputs):
        # Publish custom event
        event = WorkflowEvent(
            type="custom_step_started",
            workflow_id=context.workflow_id,
            execution_id=context.execution_id,
            step_id=self.step_id,
            data={
                "custom_metric": "value",
                "step_config": self.config
            }
        )
        await monitor.publish_event(event)
        
        # Perform step logic
        result = await self._perform_operation(inputs)
        
        # Publish completion event
        completion_event = WorkflowEvent(
            type="custom_step_completed",
            workflow_id=context.workflow_id,
            execution_id=context.execution_id,
            step_id=self.step_id,
            data={
                "result_size": len(str(result)),
                "processing_time": self.processing_time
            }
        )
        await monitor.publish_event(completion_event)
        
        return result
```

### **Custom Metrics Collection**

```python
# Define custom metrics collector
class CustomMetricsCollector:
    def __init__(self):
        self.custom_metrics = {}
    
    async def collect_metrics(self, execution_id: str):
        """Collect custom metrics for execution"""
        
        # Business-specific metrics
        execution_trace = await debugger.get_execution_trace(execution_id)
        
        # Calculate custom metrics
        data_volume = sum(
            len(str(step.outputs)) for step in execution_trace.step_traces
            if step.outputs
        )
        
        ai_cost = sum(
            step.metadata.get("cost", 0) for step in execution_trace.step_traces
            if step.step_type == "agent"
        )
        
        quality_score = self._calculate_quality_score(execution_trace)
        
        # Store custom metrics
        self.custom_metrics[execution_id] = {
            "data_volume_bytes": data_volume,
            "ai_cost_dollars": ai_cost,
            "quality_score": quality_score,
            "business_value": self._calculate_business_value(execution_trace)
        }
        
        return self.custom_metrics[execution_id]
    
    def _calculate_quality_score(self, trace):
        """Calculate custom quality score"""
        # Your custom quality calculation logic
        return 0.95
    
    def _calculate_business_value(self, trace):
        """Calculate business value delivered"""
        # Your custom business value calculation
        return 100.0

# Use custom metrics collector
custom_collector = CustomMetricsCollector()

# Collect metrics after execution
result = await execute_workflow("business_workflow", inputs)
custom_metrics = await custom_collector.collect_metrics(result.execution_id)

print(f"Custom Metrics:")
print(f"  Data Volume: {custom_metrics['data_volume_bytes']} bytes")
print(f"  AI Cost: ${custom_metrics['ai_cost_dollars']:.2f}")
print(f"  Quality Score: {custom_metrics['quality_score']:.2%}")
print(f"  Business Value: {custom_metrics['business_value']}")
```

### **Custom Dashboards**

```python
# Create custom monitoring dashboard
class WorkflowDashboard:
    def __init__(self, monitor: WorkflowMonitor):
        self.monitor = monitor
        self.dashboard_data = {}
    
    async def generate_dashboard(self, workflow_ids: List[str]):
        """Generate dashboard data for workflows"""
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "workflows": {},
            "system_overview": await self.monitor.get_system_metrics()
        }
        
        for workflow_id in workflow_ids:
            workflow_metrics = await self.monitor.get_workflow_metrics(workflow_id)
            recent_executions = await self.monitor.get_recent_executions(workflow_id, limit=10)
            
            dashboard["workflows"][workflow_id] = {
                "status": self._determine_workflow_health(workflow_metrics),
                "metrics": {
                    "total_executions": workflow_metrics.total_executions,
                    "success_rate": workflow_metrics.success_rate,
                    "avg_duration_ms": workflow_metrics.average_duration_ms,
                    "executions_24h": workflow_metrics.executions_24h
                },
                "recent_executions": [
                    {
                        "execution_id": exec.execution_id,
                        "status": exec.status,
                        "duration_ms": exec.total_duration_ms,
                        "timestamp": exec.start_time.isoformat()
                    }
                    for exec in recent_executions
                ],
                "performance_trend": workflow_metrics.performance_trend
            }
        
        return dashboard
    
    def _determine_workflow_health(self, metrics):
        """Determine workflow health status"""
        if metrics.success_rate >= 0.95:
            return "healthy"
        elif metrics.success_rate >= 0.8:
            return "warning"
        else:
            return "critical"

# Use custom dashboard
dashboard = WorkflowDashboard(monitor)
dashboard_data = await dashboard.generate_dashboard([
    "data_analysis", "content_processing", "approval_workflow"
])

# Export dashboard data
import json
with open("workflow_dashboard.json", "w") as f:
    json.dump(dashboard_data, f, indent=2)
```

---

## 📊 Monitoring Best Practices

### **Event Subscription Strategy**
- **Selective Subscriptions**: Subscribe only to events you need to avoid overhead
- **Event Filtering**: Use event type filters to reduce noise
- **Async Handlers**: Keep event handlers async and fast
- **Error Handling**: Handle exceptions in event callbacks gracefully

### **Metrics Collection**
- **Regular Collection**: Collect metrics at consistent intervals
- **Storage Management**: Archive old metrics to prevent storage bloat
- **Aggregation**: Use pre-aggregated metrics for dashboards
- **Custom Metrics**: Add business-specific metrics that matter to your use case

### **Performance Monitoring**
- **Baseline Establishment**: Establish performance baselines for comparison
- **Trend Analysis**: Monitor trends rather than just current values
- **Proactive Alerts**: Set up alerts before problems become critical
- **Capacity Planning**: Use metrics for capacity planning and scaling decisions

### **Debugging Workflow**
- **Systematic Analysis**: Follow a systematic approach to debugging failures
- **Context Preservation**: Preserve execution context for post-mortem analysis
- **Pattern Recognition**: Look for patterns in failures and performance issues
- **Documentation**: Document common issues and their solutions

---

## 🚀 Production Monitoring Setup

```python
# Complete production monitoring setup
async def setup_production_monitoring():
    """Complete production monitoring configuration"""
    
    # Initialize monitor with production config
    monitor = WorkflowMonitor(config={
        "event_buffer_size": 10000,
        "metrics_retention_days": 30,
        "performance_sample_rate": 0.1,  # Sample 10% for performance
        "enable_detailed_tracing": False  # Disable in production for performance
    })
    
    # Configure alerts
    await monitor.configure_alerts({
        "execution_duration_threshold": 600000,  # 10 minutes
        "failure_rate_threshold": 0.05,         # 5% failure rate
        "memory_usage_threshold": 2000,         # 2GB memory
        "queue_length_threshold": 50            # 50 queued executions
    })
    
    # Set up critical event handlers
    async def critical_alert_handler(alert):
        # Send to alerting system (PagerDuty, Slack, etc.)
        await send_alert_to_operations_team(alert)
        
        # Take automated recovery actions
        if alert.type == "high_failure_rate":
            await monitor.pause_workflow_executions(alert.workflow_id)
        elif alert.type == "resource_exhaustion":
            await monitor.trigger_scale_up()
    
    await monitor.subscribe_to_alerts(critical_alert_handler, severity=["critical", "high"])
    
    # Start background monitoring
    await monitor.start_monitoring()
    
    # Set up metrics export
    async def export_metrics():
        while True:
            metrics = await monitor.export_all_metrics()
            await send_metrics_to_datadog(metrics)  # or your metrics system
            await asyncio.sleep(60)  # Export every minute
    
    asyncio.create_task(export_metrics())
    
    return monitor

# Production setup
production_monitor = await setup_production_monitoring()
```

---

**LangSwarm V2's monitoring and debugging system provides comprehensive observability into workflow execution, enabling proactive performance optimization, rapid issue resolution, and reliable production operations.**
