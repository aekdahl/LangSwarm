"""
Pytest Configuration and Fixtures for Navigation Tests

This module provides shared fixtures and configuration for all navigation system tests.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock

from ..tracker import NavigationTracker, NavigationDecision
from ..navigator import NavigationTool, WorkflowNavigator, NavigationContext
from ..config import NavigationConfig, NavigationStep, NavigationMode, NavigationCondition
from ..schema import ConditionOperator
from ..schema import NavigationConfigBuilder


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def navigation_tracker(temp_db):
    """Create a NavigationTracker with temporary database"""
    return NavigationTracker(temp_db)


@pytest.fixture
def sample_navigation_decision():
    """Create a sample NavigationDecision for testing"""
    return NavigationDecision(
        decision_id="test_decision_001",
        workflow_id="test_workflow",
        step_id="routing_step",
        agent_id="test_agent",
        chosen_step="technical_support",
        available_steps=["technical_support", "billing_support", "general_support"],
        reasoning="Customer has technical issue requiring specialized support",
        confidence=0.85,
        context_hash="abc123def456",
        timestamp=datetime.now(),
        execution_time_ms=125.5,
        metadata={"category": "technical", "priority": "medium"}
    )


@pytest.fixture
def sample_decisions_batch():
    """Create a batch of sample decisions for testing"""
    base_time = datetime.now()
    decisions = []
    
    scenarios = [
        ("technical_support", 0.9, 120.0, "Technical API issue"),
        ("billing_support", 0.8, 90.0, "Billing inquiry"),
        ("technical_support", 0.85, 150.0, "Database connection problem"),
        ("general_support", 0.7, 200.0, "General question"),
        ("technical_support", 0.95, 110.0, "Critical system error"),
    ]
    
    for i, (chosen_step, confidence, exec_time, reasoning) in enumerate(scenarios):
        decision = NavigationDecision(
            decision_id=f"batch_decision_{i:03d}",
            workflow_id="batch_test_workflow",
            step_id="routing_step",
            agent_id="batch_test_agent",
            chosen_step=chosen_step,
            available_steps=["technical_support", "billing_support", "general_support"],
            reasoning=reasoning,
            confidence=confidence,
            context_hash=f"hash_{i}",
            timestamp=base_time + timedelta(minutes=i * 10),
            execution_time_ms=exec_time,
            metadata={"batch_id": i, "test_scenario": True}
        )
        decisions.append(decision)
    
    return decisions


@pytest.fixture
def navigation_config():
    """Create a sample NavigationConfig for testing"""
    steps = [
        NavigationStep(
            id="technical_support",
            name="Technical Support",
            description="Route technical issues to specialized support team",
            conditions=[
                NavigationCondition(
                    field="output.category",
                    operator=ConditionOperator.EQUALS,
                    value="technical"
                )
            ],
            weight=1.5
        ),
        NavigationStep(
            id="billing_support",
            name="Billing Support",
            description="Route billing and payment issues to billing team",
            conditions=[
                NavigationCondition(
                    field="output.category", 
                    operator=ConditionOperator.EQUALS,
                    value="billing"
                )
            ]
        ),
        NavigationStep(
            id="general_support",
            name="General Support",
            description="Handle general inquiries and miscellaneous issues"
        )
    ]
    
    return NavigationConfig(
        mode=NavigationMode.HYBRID,
        steps=steps,
        fallback_step="general_support",
        timeout_seconds=30,
        tracking_enabled=True
    )


@pytest.fixture
def navigation_context():
    """Create a sample NavigationContext for testing"""
    return NavigationContext(
        workflow_id="test_workflow",
        current_step="routing_decision",
        context_data={
            "output": {
                "category": "technical",
                "priority": "medium",
                "complexity": 0.7
            },
            "user": {
                "tier": "premium",
                "history": ["previous_issue"]
            }
        },
        step_history=[
            {"step": "intake", "timestamp": "2024-01-01T10:00:00Z"},
            {"step": "analysis", "timestamp": "2024-01-01T10:01:00Z"}
        ],
        available_steps=[
            {"id": "technical_support"},
            {"id": "billing_support"},
            {"id": "general_support"}
        ]
    )


@pytest.fixture
def navigation_tool(navigation_config, navigation_context):
    """Create a NavigationTool with mocked navigator"""
    mock_navigator = Mock()
    mock_navigator.tracker = Mock()
    
    tool = NavigationTool(mock_navigator)
    tool.set_context(navigation_config, navigation_context)
    
    return tool


@pytest.fixture
def workflow_navigator(temp_db):
    """Create a WorkflowNavigator with temporary database"""
    return WorkflowNavigator(tracking_db=temp_db)


@pytest.fixture
def config_builder():
    """Create a NavigationConfigBuilder for testing"""
    from ..schema import create_navigation_config
    return create_navigation_config()


@pytest.fixture
def mock_registry():
    """Create a mock tool registry for testing"""
    registry = Mock()
    registry.register_tool = Mock()
    return registry


@pytest.fixture
def populated_tracker(navigation_tracker, sample_decisions_batch):
    """Create a tracker populated with sample decisions"""
    for decision in sample_decisions_batch:
        navigation_tracker.track_decision(decision)
    return navigation_tracker


# Test configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark slow tests (those that use real databases or external services)
        elif any(keyword in item.name for keyword in ["database", "analytics", "export"]):
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.unit) 