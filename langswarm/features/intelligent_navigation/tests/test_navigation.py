"""
Test Suite for Intelligent Navigation System

This module contains comprehensive tests for the navigation system,
including unit tests, integration tests, and workflow examples.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from langswarm.features.intelligent_navigation.navigator import (
    WorkflowNavigator, 
    NavigationTool, 
    NavigationChoice,
    NavigationContext
)
from langswarm.features.intelligent_navigation.tracker import (
    NavigationTracker, 
    NavigationDecision,
    NavigationAnalytics
)
from langswarm.features.intelligent_navigation.config import (
    NavigationConfig,
    NavigationStep,
    NavigationRule,
    NavigationCondition,
    StepType,
    NavigationMode
)
from langswarm.features.intelligent_navigation.exceptions import (
    NavigationError,
    InvalidStepError,
    NoAvailableStepsError,
    NavigationTimeoutError
)


class TestNavigationConfig:
    """Test configuration and condition evaluation"""
    
    def test_step_availability_basic(self):
        """Test basic step availability checking"""
        step = NavigationStep(
            id="test_step",
            name="Test Step",
            description="Test step",
            type=StepType.AGENT
        )
        
        # Should be available with no conditions
        assert step.is_available({})
        assert step.is_available({"any": "context"})
    
    def test_step_availability_with_conditions(self):
        """Test step availability with conditions"""
        step = NavigationStep(
            id="technical_step",
            name="Technical Step",
            description="Technical support step",
            type=StepType.AGENT,
            conditions=[
                NavigationCondition(
                    field="output.category",
                    operator="eq",
                    value="technical"
                )
            ]
        )
        
        # Should be available when condition is met
        context = {"output": {"category": "technical"}}
        assert step.is_available(context)
        
        # Should not be available when condition is not met
        context = {"output": {"category": "billing"}}
        assert not step.is_available(context)
        
        # Should not be available when field doesn't exist
        context = {"output": {}}
        assert not step.is_available(context)
    
    def test_navigation_config_available_steps(self):
        """Test getting available steps from navigation config"""
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="always_available",
                    name="Always Available",
                    description="Always available step",
                    type=StepType.AGENT
                ),
                NavigationStep(
                    id="conditional",
                    name="Conditional Step",
                    description="Conditional step",
                    type=StepType.AGENT,
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="technical"
                        )
                    ]
                )
            ]
        )
        
        # Test with context that makes conditional step available
        context = {"output": {"category": "technical"}}
        available = config.get_available_steps(context)
        assert len(available) == 2
        
        # Test with context that makes conditional step unavailable
        context = {"output": {"category": "billing"}}
        available = config.get_available_steps(context)
        assert len(available) == 1
        assert available[0].id == "always_available"
    
    def test_conditional_routing(self):
        """Test conditional routing rules"""
        config = NavigationConfig(
            mode=NavigationMode.CONDITIONAL,
            steps=[
                NavigationStep(
                    id="target_step",
                    name="Target Step",
                    description="Target step",
                    type=StepType.AGENT
                )
            ],
            rules=[
                NavigationRule(
                    conditions=[
                        NavigationCondition(
                            field="output.priority",
                            operator="eq",
                            value="critical"
                        )
                    ],
                    target_step="target_step",
                    priority=10
                )
            ]
        )
        
        # Should route to target step when rule matches
        context = {"output": {"priority": "critical"}}
        target = config.get_conditional_target(context)
        assert target == "target_step"
        
        # Should not route when rule doesn't match
        context = {"output": {"priority": "normal"}}
        target = config.get_conditional_target(context)
        assert target is None


class TestNavigationTracker:
    """Test navigation decision tracking and analytics"""
    
    def setup_method(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.tracker = NavigationTracker(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_track_decision(self):
        """Test tracking a navigation decision"""
        decision = NavigationDecision(
            decision_id="test_decision_1",
            workflow_id="test_workflow",
            step_id="test_step",
            agent_id="test_agent",
            chosen_step="next_step",
            available_steps=["next_step", "other_step"],
            reasoning="This is the best choice",
            confidence=0.9,
            context_hash="abc123",
            timestamp=datetime.now(),
            execution_time_ms=250.0
        )
        
        self.tracker.track_decision(decision)
        
        # Verify decision was stored
        decisions = self.tracker.get_decisions()
        assert len(decisions) == 1
        assert decisions[0].decision_id == "test_decision_1"
        assert decisions[0].chosen_step == "next_step"
    
    def test_get_decisions_with_filters(self):
        """Test retrieving decisions with filters"""
        # Create test decisions
        decisions = [
            NavigationDecision(
                decision_id=f"decision_{i}",
                workflow_id="test_workflow",
                step_id="test_step",
                agent_id="test_agent",
                chosen_step="next_step",
                available_steps=["next_step", "other_step"],
                reasoning="Test reasoning",
                confidence=0.8,
                context_hash="abc123",
                timestamp=datetime.now() - timedelta(hours=i),
                execution_time_ms=200.0
            )
            for i in range(5)
        ]
        
        for decision in decisions:
            self.tracker.track_decision(decision)
        
        # Test workflow filter
        workflow_decisions = self.tracker.get_decisions(workflow_id="test_workflow")
        assert len(workflow_decisions) == 5
        
        # Test agent filter
        agent_decisions = self.tracker.get_decisions(agent_id="test_agent")
        assert len(agent_decisions) == 5
        
        # Test time filter
        recent_decisions = self.tracker.get_decisions(
            start_time=datetime.now() - timedelta(hours=2)
        )
        assert len(recent_decisions) == 3
    
    def test_analytics_generation(self):
        """Test analytics generation"""
        # Create test decisions with different patterns
        decisions = [
            NavigationDecision(
                decision_id=f"decision_{i}",
                workflow_id="test_workflow",
                step_id="routing_step",
                agent_id="test_agent",
                chosen_step="technical_support" if i % 2 == 0 else "billing_support",
                available_steps=["technical_support", "billing_support", "general_support"],
                reasoning="Test reasoning",
                confidence=0.7 + (i % 3) * 0.1,
                context_hash="abc123",
                timestamp=datetime.now() - timedelta(minutes=i),
                execution_time_ms=200.0 + i * 50
            )
            for i in range(10)
        ]
        
        for decision in decisions:
            self.tracker.track_decision(decision)
        
        # Generate analytics
        analytics = self.tracker.get_analytics()
        
        assert analytics.total_decisions == 10
        assert analytics.avg_confidence > 0.7
        assert len(analytics.most_common_paths) > 0
        assert "routing_step -> technical_support" in [p["path"] for p in analytics.most_common_paths]
        assert analytics.performance_metrics["avg_execution_time_ms"] > 200


class TestWorkflowNavigator:
    """Test the main workflow navigator"""
    
    def setup_method(self):
        """Set up test navigator"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.navigator = WorkflowNavigator(tracking_db=self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_navigate_with_manual_mode(self):
        """Test navigation with manual mode"""
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    type=StepType.AGENT
                ),
                NavigationStep(
                    id="step2",
                    name="Step 2",
                    description="Second step",
                    type=StepType.AGENT
                )
            ]
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"test": "data"},
            step_history=[]
        )
        
        # Mock agent choice
        with patch.object(self.navigator, '_get_agent_choice') as mock_choice:
            mock_choice.return_value = NavigationChoice(
                step_id="step1",
                reasoning="This is the best choice",
                confidence=0.9
            )
            
            result = self.navigator.navigate(config, context)
            
            assert result.chosen_step == "step1"
            assert result.reasoning == "This is the best choice"
            assert result.confidence == 0.9
    
    def test_navigate_with_conditional_mode(self):
        """Test navigation with conditional mode"""
        config = NavigationConfig(
            mode=NavigationMode.CONDITIONAL,
            steps=[
                NavigationStep(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    type=StepType.AGENT
                )
            ],
            rules=[
                NavigationRule(
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="technical"
                        )
                    ],
                    target_step="step1",
                    priority=10
                )
            ]
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"output": {"category": "technical"}},
            step_history=[]
        )
        
        result = self.navigator.navigate(config, context)
        
        assert result.chosen_step == "step1"
        assert result.reasoning == "Conditional routing rule matched"
    
    def test_navigate_with_no_available_steps(self):
        """Test navigation when no steps are available"""
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    type=StepType.AGENT,
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="technical"
                        )
                    ]
                )
            ]
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"output": {"category": "billing"}},  # Doesn't match condition
            step_history=[]
        )
        
        with pytest.raises(NoAvailableStepsError):
            self.navigator.navigate(config, context)
    
    def test_navigate_with_fallback(self):
        """Test navigation with fallback step"""
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    type=StepType.AGENT,
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="technical"
                        )
                    ]
                ),
                NavigationStep(
                    id="fallback_step",
                    name="Fallback Step",
                    description="Fallback step",
                    type=StepType.AGENT
                )
            ],
            fallback_step="fallback_step"
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"output": {"category": "billing"}},  # Doesn't match condition
            step_history=[]
        )
        
        result = self.navigator.navigate(config, context)
        
        assert result.chosen_step == "fallback_step"
        assert "fallback" in result.reasoning.lower()


class TestNavigationTool:
    """Test the navigation tool for agents"""
    
    def setup_method(self):
        """Set up test tool"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.navigator = WorkflowNavigator(tracking_db=self.temp_db.name)
        self.tool = NavigationTool(self.navigator)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_tool_schema(self):
        """Test navigation tool schema"""
        schema = self.tool.get_schema()
        
        assert schema["name"] == "navigate_workflow"
        assert schema["description"]
        assert "step_id" in schema["parameters"]["properties"]
        assert "reasoning" in schema["parameters"]["properties"]
        assert "confidence" in schema["parameters"]["properties"]
    
    def test_tool_execution(self):
        """Test navigation tool execution"""
        # Set up navigation context
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="target_step",
                    name="Target Step",
                    description="Target step",
                    type=StepType.AGENT
                )
            ]
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"test": "data"},
            step_history=[]
        )
        
        self.tool.set_context(config, context)
        
        # Execute tool
        result = self.tool.execute({
            "step_id": "target_step",
            "reasoning": "This is the best choice",
            "confidence": 0.9
        })
        
        assert result["status"] == "success"
        assert result["chosen_step"] == "target_step"
        assert result["reasoning"] == "This is the best choice"
        assert result["confidence"] == 0.9
    
    def test_tool_invalid_step(self):
        """Test navigation tool with invalid step"""
        config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=[
                NavigationStep(
                    id="valid_step",
                    name="Valid Step",
                    description="Valid step",
                    type=StepType.AGENT
                )
            ]
        )
        
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="navigation_step",
            context_data={"test": "data"},
            step_history=[]
        )
        
        self.tool.set_context(config, context)
        
        # Execute tool with invalid step
        result = self.tool.execute({
            "step_id": "invalid_step",
            "reasoning": "This won't work",
            "confidence": 0.9
        })
        
        assert result["status"] == "error"
        assert "invalid step" in result["error"].lower()


class TestIntegration:
    """Integration tests for the complete navigation system"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.navigator = WorkflowNavigator(tracking_db=self.temp_db.name)
        self.tool = NavigationTool(self.navigator)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_complete_navigation_flow(self):
        """Test complete navigation flow from config to execution"""
        # Create a realistic support routing configuration
        config = NavigationConfig(
            mode=NavigationMode.HYBRID,
            steps=[
                NavigationStep(
                    id="technical_support",
                    name="Technical Support",
                    description="Route to technical support",
                    type=StepType.AGENT,
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="technical"
                        )
                    ]
                ),
                NavigationStep(
                    id="billing_support",
                    name="Billing Support",
                    description="Route to billing support",
                    type=StepType.AGENT,
                    conditions=[
                        NavigationCondition(
                            field="output.category",
                            operator="eq",
                            value="billing"
                        )
                    ]
                ),
                NavigationStep(
                    id="general_support",
                    name="General Support",
                    description="Route to general support",
                    type=StepType.AGENT
                )
            ],
            rules=[
                NavigationRule(
                    conditions=[
                        NavigationCondition(
                            field="output.priority",
                            operator="eq",
                            value="critical"
                        )
                    ],
                    target_step="technical_support",
                    priority=10
                )
            ],
            fallback_step="general_support"
        )
        
        # Test conditional routing (critical priority)
        context = NavigationContext(
            workflow_id="support_workflow",
            current_step="routing_decision",
            context_data={
                "output": {
                    "category": "billing",
                    "priority": "critical"
                }
            },
            step_history=[]
        )
        
        result = self.navigator.navigate(config, context)
        
        # Should route to technical_support due to high priority rule
        assert result.chosen_step == "technical_support"
        assert "conditional routing" in result.reasoning.lower()
        
        # Verify decision was tracked
        decisions = self.navigator.tracker.get_decisions()
        assert len(decisions) == 1
        assert decisions[0].chosen_step == "technical_support"
        
        # Test manual routing (normal priority)
        context.context_data["output"]["priority"] = "normal"
        
        with patch.object(self.navigator, '_get_agent_choice') as mock_choice:
            mock_choice.return_value = NavigationChoice(
                step_id="billing_support",
                reasoning="Customer has billing issue",
                confidence=0.85
            )
            
            result = self.navigator.navigate(config, context)
            
            assert result.chosen_step == "billing_support"
            assert result.confidence == 0.85
        
        # Verify both decisions were tracked
        decisions = self.navigator.tracker.get_decisions()
        assert len(decisions) == 2
        
        # Test analytics
        analytics = self.navigator.tracker.get_analytics()
        assert analytics.total_decisions == 2
        assert analytics.avg_confidence > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 