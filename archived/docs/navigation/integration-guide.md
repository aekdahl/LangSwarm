# Integration Guide: Intelligent Navigation System

## Overview

This guide explains how to integrate the Intelligent Workflow Navigation system into the existing LangSwarm codebase without breaking changes. The integration follows a phased approach to ensure compatibility and smooth transition.

## Integration Strategy

### Phase 1: Standalone Module (✅ Complete)
- Create independent navigation module
- Develop core functionality
- Build comprehensive tests
- Create documentation

### Phase 2: Workflow Integration (Pending)
- Integrate with existing workflow execution
- Add navigation step type support
- Maintain backward compatibility

### Phase 3: UI Integration (Pending)
- Add navigation dashboard
- Integrate with existing UI components
- Create navigation visualizations

### Phase 4: Advanced Features (Pending)
- A/B testing framework
- Machine learning optimization
- Advanced analytics

## Core Integration Points

### 1. Workflow Step Type Registration

**File:** `langswarm/core/config.py`

```python
# Add to existing step types
STEP_TYPES = {
    'agent': AgentStep,
    'webhook': WebhookStep,
    'condition': ConditionStep,
    'navigation': NavigationStep,  # NEW
    # ... existing types
}

class NavigationStep(WorkflowStep):
    """Navigation step that allows agents to choose next step"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.navigation_config = self._parse_navigation_config(config.get('navigation', {}))
        self.navigator = self._create_navigator()
    
    def _parse_navigation_config(self, config: Dict) -> NavigationConfig:
        """Parse navigation configuration from YAML"""
        from langswarm.features.intelligent_navigation import NavigationConfig
        return NavigationConfig.from_dict(config)
    
    def _create_navigator(self) -> WorkflowNavigator:
        """Create navigation instance"""
        from langswarm.features.intelligent_navigation import WorkflowNavigator
        return WorkflowNavigator()
    
    async def execute(self, context: ExecutionContext) -> StepResult:
        """Execute navigation step"""
        try:
            # Create navigation context
            nav_context = NavigationContext(
                workflow_id=context.workflow_id,
                current_step=self.id,
                context_data=context.data,
                step_history=context.step_history
            )
            
            # Perform navigation
            result = await self.navigator.navigate_async(
                self.navigation_config, 
                nav_context
            )
            
            # Return step result with navigation decision
            return StepResult(
                step_id=self.id,
                output=result.to_dict(),
                next_step=result.chosen_step,
                metadata={
                    'navigation_decision': result.decision_id,
                    'reasoning': result.reasoning,
                    'confidence': result.confidence
                }
            )
            
        except Exception as e:
            logger.error(f"Navigation step failed: {e}")
            # Fall back to configured fallback step
            fallback = self.navigation_config.fallback_step
            if fallback:
                return StepResult(
                    step_id=self.id,
                    output={'error': str(e)},
                    next_step=fallback,
                    metadata={'fallback_used': True}
                )
            raise
```

### 2. Tool Registration

**File:** `langswarm/core/wrappers/generic.py`

```python
# Add navigation tool to available tools
def _get_navigation_tools(self) -> List[Dict]:
    """Get navigation tools if in navigation context"""
    tools = []
    
    # Check if we're in a navigation step
    if hasattr(self.context, 'navigation_config') and self.context.navigation_config:
        from langswarm.features.intelligent_navigation import NavigationTool
        
        nav_tool = NavigationTool(self.context.navigator)
        nav_tool.set_context(
            self.context.navigation_config, 
            self.context.navigation_context
        )
        
        tools.append(nav_tool.get_schema())
    
    return tools

# Modify existing get_tools method
def get_tools(self) -> List[Dict]:
    """Get all available tools including navigation"""
    tools = []
    
    # Add existing tools
    tools.extend(self._get_existing_tools())
    
    # Add navigation tools if applicable
    tools.extend(self._get_navigation_tools())
    
    return tools
```

### 3. Configuration Schema Updates

**File:** `langswarm/core/config.py`

```python
# Add navigation step schema validation
NAVIGATION_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["navigation"]},
        "navigation": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["manual", "conditional", "hybrid"]},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string"},
                            "conditions": {"type": "array"},
                            "weight": {"type": "number"}
                        },
                        "required": ["id", "name", "description", "type"]
                    }
                },
                "rules": {"type": "array"},
                "fallback_step": {"type": "string"},
                "timeout_seconds": {"type": "number"},
                "max_attempts": {"type": "number"}
            },
            "required": ["mode", "steps"]
        }
    },
    "required": ["id", "type", "navigation"]
}

# Add to existing schema validation
def validate_workflow_schema(workflow_data: Dict) -> None:
    """Validate workflow schema including navigation steps"""
    for step in workflow_data.get('steps', []):
        if step.get('type') == 'navigation':
            validate_schema(step, NAVIGATION_STEP_SCHEMA)
```

### 4. Database Integration

**File:** `langswarm/core/session/models.py`

```python
# Add navigation decision tracking to session models
class NavigationDecisionRecord(Base):
    """Database model for navigation decisions"""
    __tablename__ = 'navigation_decisions'
    
    decision_id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    workflow_id = Column(String)
    step_id = Column(String)
    agent_id = Column(String)
    chosen_step = Column(String)
    available_steps = Column(JSON)
    reasoning = Column(Text)
    confidence = Column(Float)
    context_hash = Column(String)
    timestamp = Column(DateTime)
    execution_time_ms = Column(Float)
    metadata = Column(JSON)
    
    # Relationship to session
    session = relationship("SessionRecord", back_populates="navigation_decisions")

# Add relationship to existing SessionRecord
class SessionRecord(Base):
    # ... existing fields ...
    
    # Add navigation decisions relationship
    navigation_decisions = relationship(
        "NavigationDecisionRecord", 
        back_populates="session",
        cascade="all, delete-orphan"
    )
```

### 5. Analytics Integration

**File:** `langswarm/core/analytics/navigation.py`

```python
"""Navigation analytics integration"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from langswarm.features.intelligent_navigation import NavigationTracker
from langswarm.core.session.models import NavigationDecisionRecord

class NavigationAnalyticsIntegration:
    """Integration layer for navigation analytics"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.tracker = NavigationTracker()
    
    def track_session_decision(self, decision_data: Dict, session_id: str):
        """Track navigation decision with session context"""
        
        # Create navigation decision record
        decision_record = NavigationDecisionRecord(
            decision_id=decision_data['decision_id'],
            session_id=session_id,
            workflow_id=decision_data['workflow_id'],
            step_id=decision_data['step_id'],
            agent_id=decision_data['agent_id'],
            chosen_step=decision_data['chosen_step'],
            available_steps=decision_data['available_steps'],
            reasoning=decision_data['reasoning'],
            confidence=decision_data['confidence'],
            context_hash=decision_data['context_hash'],
            timestamp=datetime.now(),
            execution_time_ms=decision_data['execution_time_ms'],
            metadata=decision_data.get('metadata', {})
        )
        
        # Save to session database
        self.session_manager.save_navigation_decision(decision_record)
        
        # Also track in navigation system
        from langswarm.features.intelligent_navigation import NavigationDecision
        nav_decision = NavigationDecision(
            decision_id=decision_data['decision_id'],
            workflow_id=decision_data['workflow_id'],
            step_id=decision_data['step_id'],
            agent_id=decision_data['agent_id'],
            chosen_step=decision_data['chosen_step'],
            available_steps=decision_data['available_steps'],
            reasoning=decision_data['reasoning'],
            confidence=decision_data['confidence'],
            context_hash=decision_data['context_hash'],
            timestamp=datetime.now(),
            execution_time_ms=decision_data['execution_time_ms'],
            metadata=decision_data.get('metadata', {})
        )
        
        self.tracker.track_decision(nav_decision)
    
    def get_session_navigation_analytics(self, session_id: str) -> Dict:
        """Get navigation analytics for a specific session"""
        decisions = self.session_manager.get_navigation_decisions(session_id)
        
        if not decisions:
            return {
                'total_decisions': 0,
                'avg_confidence': 0.0,
                'decision_paths': [],
                'performance_metrics': {}
            }
        
        # Calculate session-specific analytics
        total_decisions = len(decisions)
        avg_confidence = sum(d.confidence for d in decisions) / total_decisions
        
        decision_paths = [
            f"{d.step_id} -> {d.chosen_step}"
            for d in decisions
        ]
        
        performance_metrics = {
            'avg_execution_time_ms': sum(d.execution_time_ms for d in decisions) / total_decisions,
            'min_execution_time_ms': min(d.execution_time_ms for d in decisions),
            'max_execution_time_ms': max(d.execution_time_ms for d in decisions),
            'total_navigation_time_ms': sum(d.execution_time_ms for d in decisions)
        }
        
        return {
            'total_decisions': total_decisions,
            'avg_confidence': avg_confidence,
            'decision_paths': decision_paths,
            'performance_metrics': performance_metrics
        }
```

### 6. UI Integration Points

**File:** `langswarm/ui/components/navigation_dashboard.py`

```python
"""Navigation dashboard UI components"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from langswarm.features.intelligent_navigation import NavigationTracker

class NavigationDashboard:
    """Streamlit dashboard for navigation analytics"""
    
    def __init__(self, tracker: NavigationTracker):
        self.tracker = tracker
    
    def render(self):
        """Render the navigation dashboard"""
        st.title("🧭 Intelligent Navigation Analytics")
        
        # Sidebar filters
        st.sidebar.header("Filters")
        
        # Date range filter
        end_date = st.sidebar.date_input("End Date", datetime.now().date())
        start_date = st.sidebar.date_input(
            "Start Date", 
            (datetime.now() - timedelta(days=30)).date()
        )
        
        # Workflow filter
        workflow_filter = st.sidebar.text_input("Workflow ID (optional)")
        
        # Get analytics data
        analytics = self.tracker.get_analytics(
            workflow_id=workflow_filter if workflow_filter else None,
            days=(end_date - start_date).days
        )
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Decisions", analytics.total_decisions)
        
        with col2:
            st.metric("Avg Confidence", f"{analytics.avg_confidence:.2f}")
        
        with col3:
            avg_time = analytics.performance_metrics.get('avg_execution_time_ms', 0)
            st.metric("Avg Decision Time", f"{avg_time:.0f}ms")
        
        with col4:
            high_confidence = analytics.performance_metrics.get('high_confidence_decisions', 0)
            st.metric("High Confidence %", f"{(high_confidence/analytics.total_decisions*100):.1f}%")
        
        # Most common paths chart
        st.subheader("Most Common Navigation Paths")
        
        if analytics.most_common_paths:
            paths_df = pd.DataFrame(analytics.most_common_paths)
            fig = px.bar(
                paths_df.head(10), 
                x='count', 
                y='path',
                orientation='h',
                title="Top 10 Navigation Paths"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        st.subheader("Performance Metrics")
        
        perf_metrics = analytics.performance_metrics
        metrics_df = pd.DataFrame([
            {"Metric": "Average Execution Time", "Value": f"{perf_metrics.get('avg_execution_time_ms', 0):.1f}ms"},
            {"Metric": "Min Execution Time", "Value": f"{perf_metrics.get('min_execution_time_ms', 0):.1f}ms"},
            {"Metric": "Max Execution Time", "Value": f"{perf_metrics.get('max_execution_time_ms', 0):.1f}ms"},
            {"Metric": "Low Confidence Decisions", "Value": str(perf_metrics.get('low_confidence_decisions', 0))},
            {"Metric": "High Confidence Decisions", "Value": str(perf_metrics.get('high_confidence_decisions', 0))}
        ])
        
        st.dataframe(metrics_df, use_container_width=True)
        
        # Optimization suggestions
        if analytics.optimization_suggestions:
            st.subheader("🔍 Optimization Suggestions")
            for suggestion in analytics.optimization_suggestions:
                st.info(suggestion)
        
        # Raw decision data
        with st.expander("Raw Decision Data"):
            decisions = self.tracker.get_decisions(
                workflow_id=workflow_filter if workflow_filter else None,
                start_time=datetime.combine(start_date, datetime.min.time()),
                end_time=datetime.combine(end_date, datetime.max.time())
            )
            
            if decisions:
                decisions_df = pd.DataFrame([
                    {
                        "Timestamp": d.timestamp,
                        "Workflow": d.workflow_id,
                        "Step": d.step_id,
                        "Chosen": d.chosen_step,
                        "Confidence": d.confidence,
                        "Reasoning": d.reasoning[:100] + "..." if len(d.reasoning) > 100 else d.reasoning
                    }
                    for d in decisions
                ])
                
                st.dataframe(decisions_df, use_container_width=True)
```

## Migration Path

### 1. Backward Compatibility

The navigation system is designed to be fully backward compatible:

```python
# Existing workflows continue to work unchanged
existing_workflow = {
    "id": "existing_workflow",
    "steps": [
        {
            "id": "step1",
            "type": "agent",
            "agent": "analyzer",
            "output": {"to": "step2"}  # Direct routing still works
        }
    ]
}

# New navigation-enabled workflows
navigation_workflow = {
    "id": "navigation_workflow",
    "steps": [
        {
            "id": "step1",
            "type": "agent",
            "agent": "analyzer",
            "output": {"to": "navigation_step"}
        },
        {
            "id": "navigation_step",
            "type": "navigation",  # New step type
            "navigation": {
                "mode": "hybrid",
                "steps": [
                    # ... navigation options
                ]
            }
        }
    ]
}
```

### 2. Feature Flags

Use feature flags to enable navigation gradually:

```python
# langswarm/core/config.py
class LangSwarmConfig:
    def __init__(self):
        self.features = {
            'intelligent_navigation': os.getenv('LANGSWARM_ENABLE_NAVIGATION', 'false').lower() == 'true',
            'navigation_analytics': os.getenv('LANGSWARM_ENABLE_NAV_ANALYTICS', 'false').lower() == 'true',
            'navigation_dashboard': os.getenv('LANGSWARM_ENABLE_NAV_DASHBOARD', 'false').lower() == 'true'
        }
    
    def is_navigation_enabled(self) -> bool:
        return self.features['intelligent_navigation']
```

### 3. Database Migration

Add navigation tables to existing database:

```python
# Migration script: langswarm/core/migrations/add_navigation_tables.py
def upgrade():
    """Add navigation decision tracking tables"""
    
    # Create navigation decisions table
    op.create_table(
        'navigation_decisions',
        sa.Column('decision_id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('sessions.id')),
        sa.Column('workflow_id', sa.String()),
        sa.Column('step_id', sa.String()),
        sa.Column('agent_id', sa.String()),
        sa.Column('chosen_step', sa.String()),
        sa.Column('available_steps', sa.JSON()),
        sa.Column('reasoning', sa.Text()),
        sa.Column('confidence', sa.Float()),
        sa.Column('context_hash', sa.String()),
        sa.Column('timestamp', sa.DateTime()),
        sa.Column('execution_time_ms', sa.Float()),
        sa.Column('metadata', sa.JSON())
    )
    
    # Create indexes
    op.create_index('idx_navigation_workflow', 'navigation_decisions', ['workflow_id'])
    op.create_index('idx_navigation_timestamp', 'navigation_decisions', ['timestamp'])
    op.create_index('idx_navigation_session', 'navigation_decisions', ['session_id'])

def downgrade():
    """Remove navigation tables"""
    op.drop_table('navigation_decisions')
```

### 4. Configuration Updates

Update configuration loading to support navigation:

```python
# langswarm/core/config.py
def _load_workflow_steps(self, steps_data: List[Dict]) -> List[WorkflowStep]:
    """Load workflow steps including navigation steps"""
    steps = []
    
    for step_data in steps_data:
        step_type = step_data.get('type', 'agent')
        
        if step_type == 'navigation':
            # Validate navigation config
            if not self.config.is_navigation_enabled():
                raise ValueError("Navigation feature is not enabled")
            
            # Create navigation step
            step = NavigationStep(step_data)
            steps.append(step)
        else:
            # Create regular step
            step = self._create_step(step_type, step_data)
            steps.append(step)
    
    return steps
```

## Testing Strategy

### 1. Unit Tests

```python
# Test navigation step creation
def test_navigation_step_creation():
    config = {
        "id": "nav_step",
        "type": "navigation",
        "navigation": {
            "mode": "manual",
            "steps": [
                {
                    "id": "option1",
                    "name": "Option 1",
                    "description": "First option",
                    "type": "agent"
                }
            ]
        }
    }
    
    step = NavigationStep(config)
    assert step.navigation_config.mode == NavigationMode.MANUAL
    assert len(step.navigation_config.steps) == 1
```

### 2. Integration Tests

```python
# Test navigation in workflow execution
def test_navigation_workflow_execution():
    workflow_config = {
        "id": "test_workflow",
        "steps": [
            {
                "id": "analyze",
                "type": "agent",
                "agent": "analyzer",
                "output": {"to": "navigate"}
            },
            {
                "id": "navigate",
                "type": "navigation",
                "navigation": {
                    "mode": "conditional",
                    "steps": [...],
                    "rules": [...]
                }
            }
        ]
    }
    
    # Execute workflow
    result = execute_workflow(workflow_config, test_input)
    
    # Verify navigation decision was tracked
    assert result.navigation_decisions
    assert len(result.navigation_decisions) == 1
```

### 3. Performance Tests

```python
# Test navigation performance
def test_navigation_performance():
    # Setup large navigation config
    large_config = create_large_navigation_config(50)  # 50 navigation options
    
    # Measure navigation time
    start_time = time.time()
    result = navigator.navigate(large_config, context)
    end_time = time.time()
    
    # Should complete within reasonable time
    assert (end_time - start_time) < 2.0  # 2 seconds max
    assert result.chosen_step is not None
```

## Deployment Considerations

### 1. Feature Rollout

```bash
# Enable navigation for specific workflows
export LANGSWARM_ENABLE_NAVIGATION=true
export LANGSWARM_NAVIGATION_WORKFLOWS="support_routing,order_processing"

# Start with analytics disabled
export LANGSWARM_ENABLE_NAV_ANALYTICS=false

# Enable dashboard for admin users only
export LANGSWARM_ENABLE_NAV_DASHBOARD=true
export LANGSWARM_NAV_DASHBOARD_USERS="admin,manager"
```

### 2. Monitoring

```python
# Add navigation metrics to monitoring
from langswarm.core.monitoring import add_metric

def track_navigation_metrics():
    """Track navigation performance metrics"""
    
    # Decision time metrics
    add_metric('navigation_decision_time', result.execution_time_ms)
    
    # Confidence metrics
    add_metric('navigation_confidence', result.confidence)
    
    # Error rate metrics
    if result.error:
        add_metric('navigation_errors', 1)
```

### 3. Scaling Considerations

```python
# Cache navigation configurations
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_navigation_config(workflow_id: str) -> NavigationConfig:
    """Cache navigation configurations for performance"""
    return load_navigation_config(workflow_id)

# Use connection pooling for tracking database
class NavigationTracker:
    def __init__(self):
        self.db_pool = create_connection_pool(
            database_url=os.getenv('NAVIGATION_DB_URL'),
            max_connections=50
        )
```

## Security Considerations

### 1. Access Control

```python
# Restrict navigation configuration access
def validate_navigation_permissions(user_id: str, workflow_id: str):
    """Validate user can modify navigation for workflow"""
    if not user_has_permission(user_id, f'navigation:{workflow_id}'):
        raise InsufficientPermissionsError(
            f"User {user_id} cannot modify navigation for workflow {workflow_id}"
        )
```

### 2. Data Privacy

```python
# Anonymize sensitive data in navigation tracking
def anonymize_navigation_context(context: Dict) -> Dict:
    """Remove sensitive data from navigation context"""
    sensitive_fields = ['user_id', 'email', 'phone', 'ssn']
    
    clean_context = context.copy()
    for field in sensitive_fields:
        if field in clean_context:
            clean_context[field] = hash_sensitive_data(clean_context[field])
    
    return clean_context
```

## Performance Optimization

### 1. Caching Strategy

```python
# Cache navigation decisions for similar contexts
class NavigationCache:
    def __init__(self):
        self.cache = {}
    
    def get_cached_decision(self, context_hash: str) -> Optional[NavigationChoice]:
        """Get cached navigation decision"""
        return self.cache.get(context_hash)
    
    def cache_decision(self, context_hash: str, decision: NavigationChoice):
        """Cache navigation decision"""
        self.cache[context_hash] = decision
```

### 2. Async Processing

```python
# Async navigation processing
async def navigate_async(config: NavigationConfig, context: NavigationContext) -> NavigationChoice:
    """Async navigation processing"""
    
    # Process steps availability in parallel
    availability_tasks = [
        check_step_availability(step, context)
        for step in config.steps
    ]
    
    availability_results = await asyncio.gather(*availability_tasks)
    
    # Get available steps
    available_steps = [
        step for step, available in zip(config.steps, availability_results)
        if available
    ]
    
    # Continue with navigation logic
    return await process_navigation(available_steps, context)
```

---

This integration guide provides a comprehensive roadmap for incorporating the intelligent navigation system into LangSwarm while maintaining backward compatibility and ensuring smooth deployment. The phased approach allows for gradual rollout and testing of the new functionality. 