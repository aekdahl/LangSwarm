# Navigation Tracking and Analytics System

## Overview

The LangSwarm intelligent navigation system includes comprehensive tracking and analytics capabilities to monitor navigation decisions, analyze performance, and provide optimization insights.

## Components

### 1. NavigationTracker
Core tracking engine that stores and analyzes navigation decisions.

### 2. NavigationDashboard  
Web-based real-time dashboard for monitoring navigation performance.

### 3. Navigation CLI
Command-line interface for analytics, reporting, and data management.

## Data Collection

### Automatic Tracking
Every navigation decision is automatically tracked with:

- **Decision ID**: Unique identifier for each decision
- **Workflow ID**: Which workflow made the decision
- **Step Information**: Current step and chosen next step
- **Agent ID**: Which agent made the decision
- **Reasoning**: Agent's explanation for the choice
- **Confidence**: Agent's confidence level (0.0-1.0)
- **Execution Time**: How long the decision took
- **Context Hash**: Fingerprint of the decision context
- **Metadata**: Additional context and step history

### Data Structure
```python
@dataclass
class NavigationDecision:
    decision_id: str
    workflow_id: str
    step_id: str
    agent_id: str
    chosen_step: str
    available_steps: List[str]
    reasoning: str
    confidence: float
    context_hash: str
    timestamp: datetime
    execution_time_ms: float
    metadata: Dict[str, Any]
```

## Analytics Capabilities

### Performance Metrics
- **Response Time**: Average, min, max decision times
- **Confidence Levels**: Distribution of agent confidence
- **Success Rate**: Percentage of successful vs failed decisions
- **Error Analysis**: Common failure patterns

### Pattern Analysis
- **Most Common Paths**: Frequently taken navigation routes
- **Decision Patterns**: Behavior by step and workflow
- **Context Correlations**: How context affects decisions
- **Temporal Trends**: Performance over time

### Optimization Insights
Automatically generated suggestions for:
- **Low Confidence Issues**: When agents are uncertain
- **Performance Problems**: Slow decision times
- **Pattern Anomalies**: Unexpected routing behavior
- **Loop Detection**: Potential infinite cycles

## Web Dashboard

### Starting the Dashboard
```bash
# Using the CLI
python -m langswarm.features.intelligent_navigation.cli dashboard --port 8080

# Or programmatically
from langswarm.features.intelligent_navigation.dashboard import create_navigation_dashboard

dashboard = create_navigation_dashboard("navigation_decisions.db", port=8080)
dashboard.run("0.0.0.0")
```

### Dashboard Features
- **Real-time Metrics**: Live decision counts and confidence
- **Performance Monitoring**: Response times and error rates
- **Workflow Analytics**: Per-workflow performance
- **Optimization Insights**: Actionable recommendations
- **Historical Trends**: Charts and graphs of decision patterns

### API Endpoints
- `GET /`: Main dashboard page
- `GET /api/metrics`: Real-time dashboard metrics
- `GET /api/analytics/{workflow_id}`: Workflow-specific analytics
- `GET /api/decisions`: Recent navigation decisions
- `GET /api/insights`: Optimization recommendations
- `GET /api/performance`: System health metrics
- `GET /api/workflows`: List of workflows with data

## Command Line Interface

### Installation
```bash
pip install tabulate  # For table formatting
```

### Usage Examples

#### View Analytics Summary
```bash
python -m langswarm.features.intelligent_navigation.cli analytics
python -m langswarm.features.intelligent_navigation.cli analytics --workflow "support_routing" --days 7
```

#### Recent Decisions
```bash
python -m langswarm.features.intelligent_navigation.cli recent --limit 50
python -m langswarm.features.intelligent_navigation.cli recent --workflow "support_routing"
```

#### Export Reports
```bash
python -m langswarm.features.intelligent_navigation.cli export report.json
python -m langswarm.features.intelligent_navigation.cli export detailed_report.json --workflow "support_routing" --days 90
```

#### List Workflows
```bash
python -m langswarm.features.intelligent_navigation.cli workflows
```

#### Start Dashboard
```bash
python -m langswarm.features.intelligent_navigation.cli dashboard --port 8080 --host 0.0.0.0
```

#### Data Management
```bash
python -m langswarm.features.intelligent_navigation.cli clear --days 90 --confirm
```

## Programmatic Usage

### Basic Analytics
```python
from langswarm.features.intelligent_navigation.tracker import NavigationTracker

# Initialize tracker
tracker = NavigationTracker("navigation_decisions.db")

# Get analytics for last 30 days
analytics = tracker.get_analytics(days=30)
print(f"Total decisions: {analytics.total_decisions}")
print(f"Average confidence: {analytics.avg_confidence:.2%}")

# Get recent decisions
decisions = tracker.get_decisions(limit=100)
for decision in decisions:
    print(f"{decision.timestamp}: {decision.workflow_id} -> {decision.chosen_step}")
```

### Workflow-Specific Analysis
```python
# Analyze specific workflow
workflow_analytics = tracker.get_analytics(workflow_id="customer_support", days=7)

# Get optimization suggestions
for suggestion in workflow_analytics.optimization_suggestions:
    print(f"💡 {suggestion}")

# Export data
tracker.export_analytics("workflow_report.json", workflow_id="customer_support")
```

### Real-time Monitoring
```python
# Get decision history for a workflow
history = tracker.get_decision_history("customer_support", limit=50)

# Monitor performance
performance = analytics.performance_metrics
if performance["avg_execution_time_ms"] > 1000:
    print("⚠️ Slow navigation decisions detected")
```

## Integration with Navigation System

### Automatic Tracking
Tracking is automatically enabled when using the NavigationTool:

```python
# In workflow configuration
navigation:
  available_steps: [...]
  tracking_enabled: true  # Enable tracking
  fallback_step: "general_inquiry"
```

### Manual Tracking
```python
from langswarm.features.intelligent_navigation.navigator import NavigationDecision
from datetime import datetime

# Create decision record
decision = NavigationDecision(
    decision_id="unique_id",
    workflow_id="my_workflow",
    step_id="current_step",
    agent_id="routing_agent",
    chosen_step="next_step",
    available_steps=["option1", "option2", "option3"],
    reasoning="User needs technical support",
    confidence=0.9,
    context_hash="abc123",
    timestamp=datetime.now(),
    execution_time_ms=250.0,
    metadata={"user_tier": "premium"}
)

# Track the decision
tracker.track_decision(decision)
```

## Performance Optimization

### Database Optimization
- **Automatic Cleanup**: Old decisions are periodically cleaned
- **Indexing**: Optimized queries for common operations
- **Batch Operations**: Efficient bulk data operations

### Memory Management
- **Lazy Loading**: Data loaded on demand
- **Connection Pooling**: Efficient database connections
- **Context Hashing**: Efficient context comparison

### Scalability Features
- **Configurable Retention**: Control data retention periods
- **Export/Import**: Move data between environments
- **Incremental Analytics**: Process only new data when possible

## Monitoring and Alerts

### Health Checks
The system automatically monitors:
- **Decision Volume**: Unusual spikes or drops
- **Confidence Trends**: Decreasing agent confidence
- **Error Rates**: Failed navigation attempts
- **Performance Degradation**: Slow response times

### Alert Conditions
Automatic alerts for:
- Average confidence below 50%
- Error rate above 10% 
- Response time above 1000ms
- Potential infinite loops detected

### Custom Monitoring
```python
# Set up custom monitoring
analytics = tracker.get_analytics(days=1)

# Check for issues
if analytics.avg_confidence < 0.6:
    alert("Low confidence in navigation decisions")

if analytics.performance_metrics["avg_execution_time_ms"] > 500:
    alert("Slow navigation performance detected")
```

## Troubleshooting

### Common Issues

#### No Data Showing
- Verify tracking is enabled in workflow configuration
- Check database file permissions and location
- Ensure NavigationTool is properly initialized

#### Slow Performance
- Clear old data: `cli clear --days 30`
- Check database size and consider archiving
- Review query patterns and indexing

#### Missing Decisions
- Verify NavigationTool has access to tracker instance
- Check error logs for tracking failures
- Ensure proper context is set before navigation

### Debugging Tips
```python
# Enable debug logging
import logging
logging.getLogger("langswarm.features.intelligent_navigation").setLevel(logging.DEBUG)

# Check tracker status
decisions = tracker.get_decisions(limit=1)
print(f"Last decision: {decisions[0] if decisions else 'None found'}")

# Verify database
import sqlite3
with sqlite3.connect("navigation_decisions.db") as conn:
    cursor = conn.execute("SELECT COUNT(*) FROM navigation_decisions")
    print(f"Total decisions in DB: {cursor.fetchone()[0]}")
```

## Best Practices

### Data Management
1. **Regular Cleanup**: Clear old data to maintain performance
2. **Backup Strategy**: Export important analytics before cleanup
3. **Monitoring**: Set up regular health checks
4. **Retention Policy**: Define appropriate data retention periods

### Analytics Usage
1. **Baseline Metrics**: Establish performance baselines
2. **Trend Analysis**: Monitor changes over time
3. **Actionable Insights**: Focus on optimization suggestions
4. **Validation**: Test optimizations and measure impact

### Dashboard Deployment
1. **Security**: Secure dashboard access in production
2. **Performance**: Use caching for large datasets
3. **Monitoring**: Monitor dashboard performance itself
4. **Backup**: Ensure dashboard configuration is backed up

This comprehensive tracking and analytics system provides deep insights into navigation performance, enabling continuous optimization of AI-driven workflow routing. 