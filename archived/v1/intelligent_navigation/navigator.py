"""
Core Workflow Navigator Implementation

This module contains the main navigation logic that allows AI agents to 
intelligently select the next workflow step based on context and conditions.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .exceptions import NavigationError, InvalidStepError, NoAvailableStepsError
from .tracker import NavigationTracker, NavigationDecision

logger = logging.getLogger(__name__)


@dataclass
class NavigationChoice:
    """Represents an agent's navigation decision"""
    step_id: str
    reasoning: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NavigationContext:
    """Context for navigation decisions"""
    workflow_id: str
    current_step: str
    context_data: Dict[str, Any]
    step_history: List[Dict[str, Any]]
    available_steps: List[Dict[str, Any]] = field(default_factory=list)


class NavigationTool:
    """
    Tool that allows agents to navigate to different workflow steps.
    
    This tool integrates with LangSwarm's tool registry system and provides
    agents with the ability to select the next workflow step dynamically.
    """
    
    def __init__(self, navigator=None):
        self.navigator = navigator
        self.config = None
        self.context = None
        
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LangSwarm tool registry"""
        return {
            "name": "navigate_workflow",
            "description": "Navigate to the next workflow step based on current context and conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_id": {
                        "type": "string",
                        "description": "ID of the step to navigate to"
                    },
                    "reasoning": {
                        "type": "string", 
                        "description": "Explanation for why this step was chosen"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level in this choice (0.0 to 1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["step_id", "reasoning"]
            }
        }
    
    def set_context(self, config, context: NavigationContext):
        """Set navigation configuration and context"""
        self.config = config
        self.context = context
    
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigation tool"""
        start_time = time.time()
        
        try:
            step_id = args.get('step_id')
            reasoning = args.get('reasoning', '')
            confidence = args.get('confidence', 1.0)
            
            if not step_id:
                return {
                    "response": "Navigation failed - step_id is required",
                    "tool": {
                        "status": "error",
                        "error": "step_id is required"
                    }
                }
            
            if not self.context or not self.config:
                return {
                    "response": "Navigation failed - context not configured",
                    "tool": {
                        "status": "error",
                        "error": "Navigation context not set"
                    }
                }
            
            # Validate step is available
            available_step_ids = [step['id'] for step in self.context.available_steps]
            if step_id not in available_step_ids:
                return {
                    "response": f"Navigation failed - '{step_id}' is not available. Available steps: {', '.join(available_step_ids)}",
                    "tool": {
                        "status": "error",
                        "error": f"Invalid step '{step_id}'. Available steps: {', '.join(available_step_ids)}"
                    }
                }
            
            # Create navigation choice
            choice = NavigationChoice(
                step_id=step_id,
                reasoning=reasoning,
                confidence=confidence
            )
            
            # Track the navigation decision
            if self.navigator and hasattr(self.navigator, 'tracker'):
                execution_time = (time.time() - start_time) * 1000
                
                # Generate context hash for analytics
                context_str = json.dumps(self.context.context_data, sort_keys=True)
                context_hash = hashlib.md5(context_str.encode()).hexdigest()
                
                # Create decision record
                decision = NavigationDecision(
                    decision_id=f"{self.context.workflow_id}_{self.context.current_step}_{int(time.time() * 1000)}",
                    workflow_id=self.context.workflow_id,
                    step_id=self.context.current_step,
                    agent_id=getattr(self.context, 'agent_id', 'unknown'),
                    chosen_step=step_id,
                    available_steps=available_step_ids,
                    reasoning=reasoning,
                    confidence=confidence,
                    context_hash=context_hash,
                    timestamp=datetime.now(),
                    execution_time_ms=execution_time,
                    metadata={
                        "context_data": self.context.context_data,
                        "step_history": self.context.step_history[-5:] if self.context.step_history else []  # Last 5 steps
                    }
                )
                
                # Track the decision
                self.navigator.tracker.track_decision(decision)
            
            return {
                "response": f"Successfully navigating to step '{step_id}'. {reasoning}",
                "tool": {
                    "status": "success",
                    "chosen_step": step_id,
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "navigation_choice": choice,
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Track failed decision if possible
            if self.navigator and hasattr(self.navigator, 'tracker') and self.context:
                try:
                    context_str = json.dumps(self.context.context_data, sort_keys=True)
                    context_hash = hashlib.md5(context_str.encode()).hexdigest()
                    
                    failed_decision = NavigationDecision(
                        decision_id=f"{self.context.workflow_id}_{self.context.current_step}_failed_{int(time.time() * 1000)}",
                        workflow_id=self.context.workflow_id,
                        step_id=self.context.current_step,
                        agent_id=getattr(self.context, 'agent_id', 'unknown'),
                        chosen_step="ERROR",
                        available_steps=[step.get('id', 'unknown') for step in self.context.available_steps],
                        reasoning=f"Navigation failed: {str(e)}",
                        confidence=0.0,
                        context_hash=context_hash,
                        timestamp=datetime.now(),
                        execution_time_ms=execution_time,
                        metadata={"error": str(e), "failed_step_id": args.get('step_id', 'unknown')}
                    )
                    
                    self.navigator.tracker.track_decision(failed_decision)
                except Exception as tracking_error:
                    logger.warning(f"Failed to track navigation error: {tracking_error}")
            
            return {
                "response": f"Navigation failed with error: {str(e)}",
                "tool": {
                    "status": "error",
                    "error": str(e),
                    "execution_time_ms": execution_time
                }
            }
    
    # LangSwarm tool registry compatibility methods
    def __call__(self, **kwargs):
        """Make tool callable for LangSwarm compatibility"""
        return self.execute(kwargs)
        
    @property
    def name(self):
        """Tool name for registry"""
        return "navigate_workflow"
        
    @property
    def description(self):
        """Tool description for registry"""
        return "Navigate to the next workflow step based on current context and conditions"


class WorkflowNavigator:
    """
    Main workflow navigator that orchestrates intelligent step selection.
    
    This class manages navigation decisions, tracks analytics, and provides
    the core navigation logic for AI-driven workflow routing.
    """
    
    def __init__(self, tracking_db: str = "navigation_decisions.db"):
        self.tracker = NavigationTracker(tracking_db)
        
    def navigate(self, config, context: NavigationContext) -> NavigationChoice:
        """
        Navigate to the next workflow step.
        
        Args:
            config: NavigationConfig with available steps and rules
            context: NavigationContext with current workflow state
            
        Returns:
            NavigationChoice with selected step and reasoning
        """
        start_time = time.time()
        
        try:
            # Get available steps based on current context
            available_steps = config.get_available_steps(context.context_data)
            
            if not available_steps:
                if config.fallback_step:
                    return NavigationChoice(
                        step_id=config.fallback_step,
                        reasoning="No steps available, using fallback",
                        confidence=0.5
                    )
                else:
                    raise NoAvailableStepsError(context.workflow_id, context.context_data)
            
            # Check for conditional routing first
            if config.mode in ["conditional", "hybrid"]:
                conditional_target = config.get_conditional_target(context.context_data)
                if conditional_target:
                    return NavigationChoice(
                        step_id=conditional_target,
                        reasoning="Conditional routing rule matched",
                        confidence=1.0
                    )
            
            # For manual/hybrid mode, this would normally call the agent
            # In practice, the agent uses the NavigationTool to make the choice
            # This method is more for programmatic navigation
            
            # Default to first available step if no other logic applies
            chosen_step = available_steps[0]
            return NavigationChoice(
                step_id=chosen_step.id,
                reasoning="Default to first available step",
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise NavigationError(str(e), workflow_id=context.workflow_id)
        
        finally:
            execution_time = (time.time() - start_time) * 1000
            
    async def navigate_async(self, config, context: NavigationContext) -> NavigationChoice:
        """Async version of navigate"""
        # For now, just call the sync version
        # Could be enhanced with async processing later
        return self.navigate(config, context)
        
    def _get_agent_choice(self, available_steps: List, context: NavigationContext) -> NavigationChoice:
        """
        Get navigation choice from agent.
        
        In practice, this happens through the NavigationTool that the agent calls.
        This method is here for completeness but the real agent interaction
        happens through the tool calling mechanism.
        """
        # This would be called if we were doing direct agent interaction
        # But in Option 1, the agent uses the navigate_workflow tool instead
        raise NotImplementedError("Agent choice should be made through NavigationTool")


# Compatibility functions for LangSwarm tool registry
def create_navigation_tool():
    """Factory function to create navigation tool for registry"""
    return NavigationTool()


def register_navigation_tool(registry):
    """Register navigation tool with LangSwarm tool registry"""
    tool = create_navigation_tool()
    registry.register_tool(tool) 