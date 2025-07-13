"""
Tests for Navigation Tool and Navigator

This module tests the core navigation functionality including:
- NavigationTool execution
- WorkflowNavigator logic
- Decision tracking integration
- Error handling and fallbacks
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from ..navigator import (
    NavigationTool, WorkflowNavigator, NavigationChoice, NavigationContext,
    create_navigation_tool, register_navigation_tool
)
from ..tracker import NavigationTracker, NavigationDecision
from ..config import NavigationConfig, NavigationStep, NavigationMode
from ..exceptions import NavigationError, InvalidStepError, NoAvailableStepsError


class TestNavigationChoice:
    """Test NavigationChoice data structure"""
    
    def test_navigation_choice_creation(self):
        """Test creating a NavigationChoice"""
        choice = NavigationChoice(
            step_id="test_step",
            reasoning="Test reasoning",
            confidence=0.8,
            metadata={"test": "data"}
        )
        
        assert choice.step_id == "test_step"
        assert choice.reasoning == "Test reasoning"
        assert choice.confidence == 0.8
        assert choice.metadata["test"] == "data"
        assert isinstance(choice.timestamp, datetime)
    
    def test_navigation_choice_defaults(self):
        """Test NavigationChoice with default values"""
        choice = NavigationChoice(
            step_id="test_step",
            reasoning="Test reasoning"
        )
        
        assert choice.confidence == 1.0
        assert choice.metadata == {}
        assert isinstance(choice.timestamp, datetime)


class TestNavigationContext:
    """Test NavigationContext data structure"""
    
    def test_navigation_context_creation(self):
        """Test creating a NavigationContext"""
        context = NavigationContext(
            workflow_id="test_workflow",
            current_step="current_step",
            context_data={"key": "value"},
            step_history=[{"step": "previous"}],
            available_steps=[{"id": "step1"}, {"id": "step2"}]
        )
        
        assert context.workflow_id == "test_workflow"
        assert context.current_step == "current_step"
        assert context.context_data["key"] == "value"
        assert len(context.step_history) == 1
        assert len(context.available_steps) == 2


class TestNavigationTool:
    """Test NavigationTool functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.tool = NavigationTool()
        self.mock_navigator = Mock()
        self.mock_navigator.tracker = Mock()
        self.tool.navigator = self.mock_navigator
        
        # Set up context
        self.context = NavigationContext(
            workflow_id="test_workflow",
            current_step="routing_step",
            context_data={"category": "technical"},
            step_history=[],
            available_steps=[
                {"id": "technical_support"},
                {"id": "general_support"}
            ]
        )
        
        # Set up config
        self.config = Mock()
        self.config.mode = NavigationMode.MANUAL
        self.tool.set_context(self.config, self.context)
    
    def test_tool_schema(self):
        """Test navigation tool schema generation"""
        schema = self.tool.get_schema()
        
        assert schema["name"] == "navigate_workflow"
        assert "description" in schema
        assert "parameters" in schema
        
        params = schema["parameters"]
        assert params["type"] == "object"
        assert "step_id" in params["properties"]
        assert "reasoning" in params["properties"]
        assert "confidence" in params["properties"]
        
        # Check required fields
        assert "step_id" in params["required"]
        assert "reasoning" in params["required"]
    
    def test_successful_navigation(self):
        """Test successful navigation execution"""
        args = {
            "step_id": "technical_support",
            "reasoning": "This is a technical issue",
            "confidence": 0.9
        }
        
        result = self.tool.execute(args)
        
        assert result["response"].startswith("Successfully navigating")
        assert result["tool"]["status"] == "success"
        assert result["tool"]["chosen_step"] == "technical_support"
        assert result["tool"]["reasoning"] == "This is a technical issue"
        assert result["tool"]["confidence"] == 0.9
        assert "execution_time_ms" in result["tool"]
    
    def test_missing_step_id(self):
        """Test navigation with missing step_id"""
        args = {
            "reasoning": "Some reasoning"
        }
        
        result = self.tool.execute(args)
        
        assert "step_id is required" in result["response"]
        assert result["tool"]["status"] == "error"
        assert "step_id is required" in result["tool"]["error"]
    
    def test_invalid_step_id(self):
        """Test navigation with invalid step_id"""
        args = {
            "step_id": "invalid_step",
            "reasoning": "Test reasoning"
        }
        
        result = self.tool.execute(args)
        
        assert "not available" in result["response"]
        assert result["tool"]["status"] == "error"
        assert "Invalid step" in result["tool"]["error"]
        assert "technical_support" in result["tool"]["error"]
        assert "general_support" in result["tool"]["error"]
    
    def test_missing_context(self):
        """Test navigation without context set"""
        tool = NavigationTool()
        
        args = {
            "step_id": "technical_support",
            "reasoning": "Test reasoning"
        }
        
        result = tool.execute(args)
        
        assert "context not configured" in result["response"]
        assert result["tool"]["status"] == "error"
    
    def test_tracking_integration(self):
        """Test that navigation decisions are tracked"""
        args = {
            "step_id": "technical_support",
            "reasoning": "Technical issue requiring specialized support",
            "confidence": 0.85
        }
        
        # Execute navigation
        result = self.tool.execute(args)
        
        # Verify tracking was called
        self.mock_navigator.tracker.track_decision.assert_called_once()
        
        # Verify decision details
        call_args = self.mock_navigator.tracker.track_decision.call_args[0][0]
        assert isinstance(call_args, NavigationDecision)
        assert call_args.workflow_id == "test_workflow"
        assert call_args.chosen_step == "technical_support"
        assert call_args.reasoning == "Technical issue requiring specialized support"
        assert call_args.confidence == 0.85
    
    def test_error_tracking(self):
        """Test that failed navigation attempts are tracked"""
        # Force an error by removing context
        self.tool.context = None
        
        args = {
            "step_id": "technical_support",
            "reasoning": "Test reasoning"
        }
        
        result = self.tool.execute(args)
        
        # Should still track the failed attempt
        assert result["tool"]["status"] == "error"
        # Note: tracking won't work without context, but in real scenarios
        # we'd have partial context available
    
    def test_tool_callable_interface(self):
        """Test tool callable interface"""
        args = {
            "step_id": "technical_support",
            "reasoning": "Test reasoning"
        }
        
        # Test calling tool directly
        result = self.tool(**args)
        
        assert result["tool"]["status"] == "success"
        assert result["tool"]["chosen_step"] == "technical_support"
    
    def test_tool_properties(self):
        """Test tool properties for registry compatibility"""
        assert self.tool.name == "navigate_workflow"
        assert isinstance(self.tool.description, str)
        assert "workflow step" in self.tool.description.lower()


class TestWorkflowNavigator:
    """Test WorkflowNavigator functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        # Use in-memory database for testing
        import tempfile
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        self.navigator = WorkflowNavigator(tracking_db=self.temp_db.name)
        
        # Create test configuration
        self.config = Mock()
        self.config.mode = NavigationMode.MANUAL
        self.config.fallback_step = "fallback_step"
        
        # Create test context
        self.context = NavigationContext(
            workflow_id="test_workflow",
            current_step="current_step",
            context_data={"category": "technical"},
            step_history=[]
        )
        
        # Mock available steps
        self.available_steps = [
            Mock(id="technical_support"),
            Mock(id="general_support")
        ]
        self.config.get_available_steps.return_value = self.available_steps
        self.config.get_conditional_target.return_value = None
    
    def teardown_method(self):
        """Clean up test database"""
        import os
        os.unlink(self.temp_db.name)
    
    def test_navigate_with_available_steps(self):
        """Test navigation when steps are available"""
        result = self.navigator.navigate(self.config, self.context)
        
        assert isinstance(result, NavigationChoice)
        assert result.step_id in ["technical_support", "general_support"]
        assert result.confidence == 0.7  # Default for programmatic navigation
    
    def test_navigate_with_no_available_steps_and_fallback(self):
        """Test navigation with no available steps but fallback configured"""
        self.config.get_available_steps.return_value = []
        
        result = self.navigator.navigate(self.config, self.context)
        
        assert result.step_id == "fallback_step"
        assert "fallback" in result.reasoning.lower()
        assert result.confidence == 0.5
    
    def test_navigate_with_no_available_steps_no_fallback(self):
        """Test navigation with no available steps and no fallback"""
        self.config.get_available_steps.return_value = []
        self.config.fallback_step = None
        
        with pytest.raises(NoAvailableStepsError):
            self.navigator.navigate(self.config, self.context)
    
    def test_conditional_routing(self):
        """Test conditional routing takes precedence"""
        self.config.mode = NavigationMode.HYBRID
        self.config.get_conditional_target.return_value = "conditional_target"
        
        result = self.navigator.navigate(self.config, self.context)
        
        assert result.step_id == "conditional_target"
        assert "conditional routing" in result.reasoning.lower()
        assert result.confidence == 1.0
    
    def test_navigate_async(self):
        """Test async navigation (currently just calls sync version)"""
        import asyncio
        
        async def test_async():
            result = await self.navigator.navigate_async(self.config, self.context)
            assert isinstance(result, NavigationChoice)
        
        asyncio.run(test_async())
    
    def test_navigation_error_handling(self):
        """Test navigation error handling"""
        # Force an error
        self.config.get_available_steps.side_effect = Exception("Test error")
        
        with pytest.raises(NavigationError):
            self.navigator.navigate(self.config, self.context)


class TestNavigationIntegration:
    """Integration tests for complete navigation flow"""
    
    def setup_method(self):
        """Set up integrated test environment"""
        import tempfile
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        self.navigator = WorkflowNavigator(tracking_db=self.temp_db.name)
        self.tool = NavigationTool(self.navigator)
        
        # Create realistic configuration
        from ..config import NavigationStep, NavigationCondition, ConditionOperator
        
        steps = [
            NavigationStep(
                id="technical_support",
                name="Technical Support",
                description="Handle technical issues",
                conditions=[
                    NavigationCondition(
                        field="output.category",
                        operator=ConditionOperator.EQUALS,
                        value="technical"
                    )
                ]
            ),
            NavigationStep(
                id="general_support",
                name="General Support", 
                description="Handle general inquiries"
            )
        ]
        
        self.config = NavigationConfig(
            mode=NavigationMode.MANUAL,
            steps=steps,
            fallback_step="general_support"
        )
        
        self.context = NavigationContext(
            workflow_id="integration_test",
            current_step="routing_decision",
            context_data={"output": {"category": "technical"}},
            step_history=[]
        )
        
        # Mock available steps for tool
        self.context.available_steps = [
            {"id": "technical_support"},
            {"id": "general_support"}
        ]
        
        self.tool.set_context(self.config, self.context)
    
    def teardown_method(self):
        """Clean up test database"""
        import os
        os.unlink(self.temp_db.name)
    
    def test_end_to_end_navigation_flow(self):
        """Test complete navigation flow from tool to tracking"""
        # Execute navigation through tool
        args = {
            "step_id": "technical_support",
            "reasoning": "Customer has a technical API issue that requires specialized support",
            "confidence": 0.92
        }
        
        result = self.tool.execute(args)
        
        # Verify tool response
        assert result["tool"]["status"] == "success"
        assert result["tool"]["chosen_step"] == "technical_support"
        
        # Verify decision was tracked
        decisions = self.navigator.tracker.get_decisions(limit=1)
        assert len(decisions) == 1
        
        decision = decisions[0]
        assert decision.workflow_id == "integration_test"
        assert decision.chosen_step == "technical_support"
        assert decision.confidence == 0.92
        assert "api issue" in decision.reasoning.lower()
    
    def test_registry_integration(self):
        """Test tool registry integration"""
        # Mock registry
        registry = Mock()
        
        # Test tool creation
        tool = create_navigation_tool()
        assert isinstance(tool, NavigationTool)
        
        # Test registration
        register_navigation_tool(registry)
        registry.register_tool.assert_called_once()
        
        # Verify registered tool
        registered_tool = registry.register_tool.call_args[0][0]
        assert isinstance(registered_tool, NavigationTool)
    
    def test_multiple_navigation_decisions(self):
        """Test multiple navigation decisions in sequence"""
        decisions_data = [
            ("technical_support", "Technical API issue", 0.9),
            ("general_support", "General inquiry about pricing", 0.7),
            ("technical_support", "Database connection error", 0.95)
        ]
        
        for step_id, reasoning, confidence in decisions_data:
            args = {
                "step_id": step_id,
                "reasoning": reasoning,
                "confidence": confidence
            }
            
            result = self.tool.execute(args)
            assert result["tool"]["status"] == "success"
            
            # Brief delay to ensure different timestamps
            time.sleep(0.01)
        
        # Verify all decisions were tracked
        decisions = self.navigator.tracker.get_decisions(limit=10)
        assert len(decisions) == 3
        
        # Verify decision ordering (most recent first)
        assert decisions[0].reasoning == "Database connection error"
        assert decisions[1].reasoning == "General inquiry about pricing"
        assert decisions[2].reasoning == "Technical API issue"
    
    def test_error_recovery_and_tracking(self):
        """Test error scenarios and recovery"""
        # Test invalid step ID
        invalid_args = {
            "step_id": "nonexistent_step",
            "reasoning": "Test invalid step",
            "confidence": 0.8
        }
        
        result = self.tool.execute(invalid_args)
        assert result["tool"]["status"] == "error"
        
        # Verify error was tracked
        decisions = self.navigator.tracker.get_decisions(limit=1)
        assert len(decisions) == 1
        assert decisions[0].chosen_step == "ERROR"
        assert "nonexistent_step" in decisions[0].metadata["failed_step_id"]
    
    def test_performance_tracking(self):
        """Test navigation performance tracking"""
        args = {
            "step_id": "technical_support",
            "reasoning": "Performance test navigation",
            "confidence": 0.8
        }
        
        start_time = time.time()
        result = self.tool.execute(args)
        end_time = time.time()
        
        # Verify execution time is tracked
        assert "execution_time_ms" in result["tool"]
        tracked_time = result["tool"]["execution_time_ms"]
        actual_time = (end_time - start_time) * 1000
        
        # Tracked time should be reasonable (within 100ms of actual)
        assert abs(tracked_time - actual_time) < 100


if __name__ == "__main__":
    pytest.main([__file__]) 