"""
Tests for Navigation Tracking and Analytics

This module tests the tracking system including:
- Decision tracking and storage
- Analytics generation
- Performance metrics
- Data management
"""

import pytest
import tempfile
import time
import os
from datetime import datetime, timedelta
from typing import List

from ..tracker import (
    NavigationTracker, NavigationDecision, NavigationAnalytics
)


class TestNavigationDecision:
    """Test NavigationDecision data structure"""
    
    def test_navigation_decision_creation(self):
        """Test creating a NavigationDecision"""
        decision = NavigationDecision(
            decision_id="test_001",
            workflow_id="test_workflow",
            step_id="current_step",
            agent_id="test_agent",
            chosen_step="next_step",
            available_steps=["step1", "step2", "step3"],
            reasoning="Test reasoning for navigation",
            confidence=0.85,
            context_hash="abc123def456",
            timestamp=datetime.now(),
            execution_time_ms=150.5,
            metadata={"user_tier": "premium", "category": "technical"}
        )
        
        assert decision.decision_id == "test_001"
        assert decision.workflow_id == "test_workflow"
        assert decision.chosen_step == "next_step"
        assert len(decision.available_steps) == 3
        assert decision.confidence == 0.85
        assert decision.metadata["user_tier"] == "premium"


class TestNavigationTracker:
    """Test NavigationTracker functionality"""
    
    def setup_method(self):
        """Set up test environment with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.tracker = NavigationTracker(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_track_single_decision(self):
        """Test tracking a single navigation decision"""
        decision = NavigationDecision(
            decision_id="single_test",
            workflow_id="test_workflow",
            step_id="step1",
            agent_id="agent1",
            chosen_step="step2",
            available_steps=["step2", "step3"],
            reasoning="Moving to step2 based on user input",
            confidence=0.9,
            context_hash="hash123",
            timestamp=datetime.now(),
            execution_time_ms=100.0,
            metadata={}
        )
        
        # Track the decision
        self.tracker.track_decision(decision)
        
        # Retrieve and verify
        decisions = self.tracker.get_decisions(limit=1)
        assert len(decisions) == 1
        
        retrieved = decisions[0]
        assert retrieved.decision_id == "single_test"
        assert retrieved.workflow_id == "test_workflow"
        assert retrieved.chosen_step == "step2"
        assert retrieved.confidence == 0.9
    
    def test_track_multiple_decisions(self):
        """Test tracking multiple navigation decisions"""
        base_time = datetime.now()
        
        decisions = []
        for i in range(5):
            decision = NavigationDecision(
                decision_id=f"test_{i:03d}",
                workflow_id="test_workflow",
                step_id=f"step_{i}",
                agent_id="test_agent",
                chosen_step=f"step_{i+1}",
                available_steps=[f"step_{j}" for j in range(i+1, i+4)],
                reasoning=f"Test decision {i}",
                confidence=0.7 + (i * 0.05),
                context_hash=f"hash_{i}",
                timestamp=base_time + timedelta(seconds=i),
                execution_time_ms=50.0 + (i * 10),
                metadata={"sequence": i}
            )
            decisions.append(decision)
            self.tracker.track_decision(decision)
        
        # Retrieve all decisions
        retrieved = self.tracker.get_decisions(limit=10)
        assert len(retrieved) == 5
        
        # Should be in reverse chronological order
        assert retrieved[0].decision_id == "test_004"
        assert retrieved[4].decision_id == "test_000"
    
    def test_get_decisions_with_filters(self):
        """Test retrieving decisions with various filters"""
        base_time = datetime.now()
        
        # Create decisions for different workflows and agents
        decisions_data = [
            ("workflow_a", "agent_1", base_time),
            ("workflow_a", "agent_2", base_time + timedelta(hours=1)),
            ("workflow_b", "agent_1", base_time + timedelta(hours=2)),
            ("workflow_b", "agent_2", base_time + timedelta(hours=3)),
        ]
        
        for i, (workflow_id, agent_id, timestamp) in enumerate(decisions_data):
            decision = NavigationDecision(
                decision_id=f"filter_test_{i}",
                workflow_id=workflow_id,
                step_id="step1",
                agent_id=agent_id,
                chosen_step="step2",
                available_steps=["step2"],
                reasoning=f"Filter test {i}",
                confidence=0.8,
                context_hash=f"hash_{i}",
                timestamp=timestamp,
                execution_time_ms=100.0,
                metadata={}
            )
            self.tracker.track_decision(decision)
        
        # Test workflow filter
        workflow_a_decisions = self.tracker.get_decisions(workflow_id="workflow_a")
        assert len(workflow_a_decisions) == 2
        
        # Test agent filter
        agent_1_decisions = self.tracker.get_decisions(agent_id="agent_1")
        assert len(agent_1_decisions) == 2
        
        # Test combined filters
        specific_decisions = self.tracker.get_decisions(
            workflow_id="workflow_a", 
            agent_id="agent_1"
        )
        assert len(specific_decisions) == 1
        
        # Test time filter
        recent_decisions = self.tracker.get_decisions(
            start_time=base_time + timedelta(hours=1.5)
        )
        assert len(recent_decisions) == 2
    
    def test_analytics_generation(self):
        """Test analytics generation from tracked decisions"""
        base_time = datetime.now()
        
        # Create a realistic set of decisions
        decisions_data = [
            ("technical_support", 0.9, 120.0),
            ("technical_support", 0.8, 150.0),
            ("billing_support", 0.7, 80.0),
            ("general_support", 0.6, 200.0),
            ("technical_support", 0.85, 110.0),
        ]
        
        for i, (chosen_step, confidence, exec_time) in enumerate(decisions_data):
            decision = NavigationDecision(
                decision_id=f"analytics_test_{i}",
                workflow_id="analytics_workflow",
                step_id="routing_step",
                agent_id="router_agent",
                chosen_step=chosen_step,
                available_steps=["technical_support", "billing_support", "general_support"],
                reasoning=f"Analytics test decision {i}",
                confidence=confidence,
                context_hash=f"hash_{i}",
                timestamp=base_time + timedelta(minutes=i),
                execution_time_ms=exec_time,
                metadata={}
            )
            self.tracker.track_decision(decision)
        
        # Generate analytics
        analytics = self.tracker.get_analytics(workflow_id="analytics_workflow", days=1)
        
        assert analytics.total_decisions == 5
        assert 0.7 <= analytics.avg_confidence <= 0.9
        
        # Check performance metrics
        assert "avg_execution_time_ms" in analytics.performance_metrics
        assert analytics.performance_metrics["avg_execution_time_ms"] > 0
        
        # Check common paths
        assert len(analytics.most_common_paths) > 0
        technical_path = next((p for p in analytics.most_common_paths 
                              if "technical_support" in p["path"]), None)
        assert technical_path is not None
        assert technical_path["count"] == 3  # Three technical support decisions
    
    def test_analytics_optimization_suggestions(self):
        """Test optimization suggestions generation"""
        base_time = datetime.now()
        
        # Create decisions with low confidence to trigger suggestions
        for i in range(10):
            decision = NavigationDecision(
                decision_id=f"low_confidence_{i}",
                workflow_id="optimization_test",
                step_id="routing_step",
                agent_id="router_agent",
                chosen_step="fallback_step",
                available_steps=["step1", "step2", "fallback_step"],
                reasoning="Low confidence decision",
                confidence=0.3,  # Low confidence
                context_hash=f"hash_{i}",
                timestamp=base_time + timedelta(minutes=i),
                execution_time_ms=1500.0,  # High execution time
                metadata={}
            )
            self.tracker.track_decision(decision)
        
        analytics = self.tracker.get_analytics(workflow_id="optimization_test", days=1)
        
        # Should generate optimization suggestions
        assert len(analytics.optimization_suggestions) > 0
        
        # Check for specific suggestions
        suggestions_text = " ".join(analytics.optimization_suggestions)
        assert "confidence" in suggestions_text.lower() or "execution" in suggestions_text.lower()
    
    def test_decision_history(self):
        """Test getting decision history for a workflow"""
        base_time = datetime.now()
        
        # Create a sequence of decisions
        for i in range(5):
            decision = NavigationDecision(
                decision_id=f"history_{i}",
                workflow_id="history_workflow",
                step_id=f"step_{i}",
                agent_id="test_agent",
                chosen_step=f"step_{i+1}",
                available_steps=[f"step_{j}" for j in range(i+1, i+3)],
                reasoning=f"History decision {i}",
                confidence=0.8,
                context_hash=f"hash_{i}",
                timestamp=base_time + timedelta(minutes=i),
                execution_time_ms=100.0,
                metadata={}
            )
            self.tracker.track_decision(decision)
        
        # Get decision history
        history = self.tracker.get_decision_history("history_workflow", limit=10)
        
        assert len(history) == 5
        # Should be in reverse chronological order
        assert history[0]["step_id"] == "step_4"
        assert history[4]["step_id"] == "step_0"
        
        # Check history format
        for item in history:
            assert "timestamp" in item
            assert "step_id" in item
            assert "chosen_step" in item
            assert "reasoning" in item
            assert "confidence" in item
    
    def test_export_analytics(self):
        """Test exporting analytics to file"""
        # Create some test decisions
        decision = NavigationDecision(
            decision_id="export_test",
            workflow_id="export_workflow",
            step_id="step1",
            agent_id="test_agent",
            chosen_step="step2",
            available_steps=["step2", "step3"],
            reasoning="Export test decision",
            confidence=0.8,
            context_hash="hash123",
            timestamp=datetime.now(),
            execution_time_ms=100.0,
            metadata={}
        )
        self.tracker.track_decision(decision)
        
        # Export analytics
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            self.tracker.export_analytics(export_path, workflow_id="export_workflow")
            
            # Verify export file exists and contains data
            assert os.path.exists(export_path)
            
            import json
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            assert "export_timestamp" in exported_data
            assert "workflow_id" in exported_data
            assert "analytics" in exported_data
            assert exported_data["workflow_id"] == "export_workflow"
            
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_clear_old_decisions(self):
        """Test clearing old decisions"""
        base_time = datetime.now()
        
        # Create decisions at different times
        old_decision = NavigationDecision(
            decision_id="old_decision",
            workflow_id="cleanup_test",
            step_id="step1",
            agent_id="test_agent",
            chosen_step="step2",
            available_steps=["step2"],
            reasoning="Old decision",
            confidence=0.8,
            context_hash="hash_old",
            timestamp=base_time - timedelta(days=100),  # Very old
            execution_time_ms=100.0,
            metadata={}
        )
        
        recent_decision = NavigationDecision(
            decision_id="recent_decision",
            workflow_id="cleanup_test",
            step_id="step1",
            agent_id="test_agent",
            chosen_step="step2",
            available_steps=["step2"],
            reasoning="Recent decision",
            confidence=0.8,
            context_hash="hash_recent",
            timestamp=base_time,  # Recent
            execution_time_ms=100.0,
            metadata={}
        )
        
        # Track both decisions
        self.tracker.track_decision(old_decision)
        self.tracker.track_decision(recent_decision)
        
        # Verify both exist
        all_decisions = self.tracker.get_decisions(limit=10)
        assert len(all_decisions) == 2
        
        # Clear old decisions (older than 30 days)
        self.tracker.clear_old_decisions(days=30)
        
        # Verify only recent decision remains
        remaining_decisions = self.tracker.get_decisions(limit=10)
        assert len(remaining_decisions) == 1
        assert remaining_decisions[0].decision_id == "recent_decision"
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        # Create tracker with invalid database path
        invalid_tracker = NavigationTracker("/invalid/path/database.db")
        
        decision = NavigationDecision(
            decision_id="error_test",
            workflow_id="error_workflow",
            step_id="step1",
            agent_id="test_agent",
            chosen_step="step2",
            available_steps=["step2"],
            reasoning="Error test decision",
            confidence=0.8,
            context_hash="hash123",
            timestamp=datetime.now(),
            execution_time_ms=100.0,
            metadata={}
        )
        
        # Should not raise exception, just log error
        invalid_tracker.track_decision(decision)
        
        # Should return empty list on retrieval error
        decisions = invalid_tracker.get_decisions()
        assert decisions == []


class TestNavigationAnalytics:
    """Test NavigationAnalytics data structure"""
    
    def test_analytics_creation(self):
        """Test creating NavigationAnalytics"""
        analytics = NavigationAnalytics(
            total_decisions=100,
            avg_confidence=0.85,
            most_common_paths=[
                {"path": "step1 -> step2", "count": 50, "percentage": 50.0},
                {"path": "step1 -> step3", "count": 30, "percentage": 30.0}
            ],
            decision_patterns={
                "step1": {
                    "total_decisions": 80,
                    "avg_confidence": 0.8,
                    "most_chosen": {"step2": 50, "step3": 30}
                }
            },
            performance_metrics={
                "avg_execution_time_ms": 150.0,
                "min_execution_time_ms": 50.0,
                "max_execution_time_ms": 300.0
            },
            optimization_suggestions=[
                "Consider improving step descriptions for higher confidence",
                "Review slow decision patterns"
            ]
        )
        
        assert analytics.total_decisions == 100
        assert analytics.avg_confidence == 0.85
        assert len(analytics.most_common_paths) == 2
        assert len(analytics.optimization_suggestions) == 2


class TestTrackerIntegration:
    """Integration tests for the complete tracking system"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.tracker = NavigationTracker(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_realistic_workflow_tracking(self):
        """Test tracking a realistic workflow scenario"""
        base_time = datetime.now()
        
        # Simulate a customer support workflow over several hours
        workflow_scenarios = [
            # Morning - mostly technical issues
            ("technical_support", 0.9, 120.0, "Morning technical issue"),
            ("technical_support", 0.85, 150.0, "Another technical issue"),
            ("billing_support", 0.7, 80.0, "Billing question"),
            
            # Afternoon - mixed issues
            ("general_support", 0.6, 200.0, "General inquiry"),
            ("technical_support", 0.8, 130.0, "Technical problem"),
            ("escalation", 0.95, 300.0, "Complex issue requiring escalation"),
            
            # Evening - fewer issues
            ("billing_support", 0.75, 90.0, "Evening billing question"),
            ("general_support", 0.65, 180.0, "General question"),
        ]
        
        for i, (chosen_step, confidence, exec_time, reasoning) in enumerate(workflow_scenarios):
            decision = NavigationDecision(
                decision_id=f"realistic_{i:03d}",
                workflow_id="customer_support",
                step_id="routing_decision",
                agent_id="support_router",
                chosen_step=chosen_step,
                available_steps=["technical_support", "billing_support", "general_support", "escalation"],
                reasoning=reasoning,
                confidence=confidence,
                context_hash=f"context_{i}",
                timestamp=base_time + timedelta(hours=i),
                execution_time_ms=exec_time,
                metadata={
                    "time_of_day": "morning" if i < 3 else "afternoon" if i < 6 else "evening",
                    "complexity": "high" if chosen_step == "escalation" else "medium" if chosen_step == "technical_support" else "low"
                }
            )
            self.tracker.track_decision(decision)
        
        # Generate comprehensive analytics
        analytics = self.tracker.get_analytics(workflow_id="customer_support", days=1)
        
        # Verify analytics make sense
        assert analytics.total_decisions == 8
        assert 0.6 <= analytics.avg_confidence <= 1.0
        
        # Check that technical support is the most common path
        tech_support_paths = [p for p in analytics.most_common_paths 
                             if "technical_support" in p["path"]]
        assert len(tech_support_paths) > 0
        
        # Verify decision patterns
        assert "routing_decision" in analytics.decision_patterns
        routing_patterns = analytics.decision_patterns["routing_decision"]
        assert routing_patterns["total_decisions"] == 8
        
        # Check performance metrics
        perf = analytics.performance_metrics
        assert perf["avg_execution_time_ms"] > 0
        assert perf["min_execution_time_ms"] <= perf["avg_execution_time_ms"] <= perf["max_execution_time_ms"]
        
        # Verify we can get decision history
        history = self.tracker.get_decision_history("customer_support", limit=10)
        assert len(history) == 8


if __name__ == "__main__":
    pytest.main([__file__]) 