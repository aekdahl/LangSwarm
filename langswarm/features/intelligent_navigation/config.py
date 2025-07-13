"""
Configuration Schema for Intelligent Navigation

This module defines the configuration structure for navigation-enabled workflows,
including step definitions, navigation rules, and routing conditions.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class StepType(Enum):
    """Types of workflow steps"""
    AGENT = "agent"
    NAVIGATION = "navigation"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class NavigationMode(Enum):
    """Navigation decision modes"""
    MANUAL = "manual"          # Agent chooses from available steps
    CONDITIONAL = "conditional" # Rule-based routing
    HYBRID = "hybrid"          # Combination of manual and conditional
    WEIGHTED = "weighted"      # Probabilistic routing based on weights


@dataclass
class NavigationCondition:
    """Defines a condition for automatic step routing"""
    field: str                    # Field to evaluate (e.g., "output.status")
    operator: str                 # Comparison operator (eq, ne, gt, lt, contains, etc.)
    value: Any                    # Value to compare against
    description: str = ""         # Human-readable description


@dataclass
class NavigationRule:
    """Defines a navigation rule for conditional routing"""
    conditions: List[NavigationCondition]
    target_step: str
    priority: int = 0
    description: str = ""


@dataclass
class NavigationStep:
    """Defines a step that can be selected during navigation"""
    id: str
    name: str
    description: str
    type: StepType
    agent_id: Optional[str] = None
    conditions: List[NavigationCondition] = field(default_factory=list)
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_available(self, context: Dict[str, Any]) -> bool:
        """Check if this step is available given the current context"""
        if not self.conditions:
            return True
            
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True
    
    def _evaluate_condition(self, condition: NavigationCondition, context: Dict[str, Any]) -> bool:
        """Evaluate a single condition against context"""
        try:
            # Extract field value from context
            field_parts = condition.field.split('.')
            value = context
            for part in field_parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return False
            
            # Evaluate condition
            if condition.operator == "eq":
                return value == condition.value
            elif condition.operator == "ne":
                return value != condition.value
            elif condition.operator == "gt":
                return value > condition.value
            elif condition.operator == "lt":
                return value < condition.value
            elif condition.operator == "gte":
                return value >= condition.value
            elif condition.operator == "lte":
                return value <= condition.value
            elif condition.operator == "contains":
                return condition.value in value
            elif condition.operator == "not_contains":
                return condition.value not in value
            elif condition.operator == "in":
                return value in condition.value
            elif condition.operator == "not_in":
                return value not in condition.value
            elif condition.operator == "exists":
                return value is not None
            elif condition.operator == "not_exists":
                return value is None
            else:
                return False
                
        except Exception:
            return False


@dataclass
class NavigationConfig:
    """Configuration for navigation-enabled workflow step"""
    mode: NavigationMode
    steps: List[NavigationStep]
    rules: List[NavigationRule] = field(default_factory=list)
    prompt_template: str = ""
    max_attempts: int = 3
    timeout_seconds: int = 30
    fallback_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_available_steps(self, context: Dict[str, Any]) -> List[NavigationStep]:
        """Get list of available steps given current context"""
        available = []
        for step in self.steps:
            if step.is_available(context):
                available.append(step)
        return available
    
    def get_conditional_target(self, context: Dict[str, Any]) -> Optional[str]:
        """Get target step based on conditional rules"""
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if self._evaluate_rule(rule, context):
                return rule.target_step
        
        return None
    
    def _evaluate_rule(self, rule: NavigationRule, context: Dict[str, Any]) -> bool:
        """Evaluate if all conditions in a rule are met"""
        for condition in rule.conditions:
            step = NavigationStep(id="temp", name="temp", description="temp", type=StepType.AGENT)
            if not step._evaluate_condition(condition, context):
                return False
        return True


@dataclass
class NavigationWorkflow:
    """Complete navigation workflow configuration"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    navigation_steps: List[Dict[str, Any]] = field(default_factory=list)
    global_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_data: Dict[str, Any]) -> 'NavigationWorkflow':
        """Create NavigationWorkflow from YAML data"""
        return cls(
            id=yaml_data.get('id', ''),
            name=yaml_data.get('name', ''),
            description=yaml_data.get('description', ''),
            version=yaml_data.get('version', '1.0.0'),
            navigation_steps=yaml_data.get('navigation_steps', []),
            global_config=yaml_data.get('global_config', {}),
            metadata=yaml_data.get('metadata', {})
        )
    
    def to_yaml(self) -> Dict[str, Any]:
        """Convert NavigationWorkflow to YAML format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'navigation_steps': self.navigation_steps,
            'global_config': self.global_config,
            'metadata': self.metadata
        }


# Default navigation prompt template
DEFAULT_NAVIGATION_PROMPT = """
You are navigating through a workflow and need to select the next step.

## Current Context:
{context}

## Available Steps:
{available_steps}

## Previous Steps:
{step_history}

## Instructions:
Please select the most appropriate next step based on the current context and your understanding of the workflow goals.

Use the `navigate_workflow` tool to make your selection. Include your reasoning for the choice.

Consider:
- The current output and context
- The goal of the workflow
- Any conditions or requirements
- The logical flow of the process
"""

# Example navigation workflow configuration
EXAMPLE_NAVIGATION_CONFIG = {
    "id": "support_routing",
    "name": "Intelligent Support Routing",
    "description": "AI-driven customer support ticket routing",
    "version": "1.0.0",
    "navigation_steps": [
        {
            "id": "analyze_ticket",
            "type": "agent",
            "agent": "ticket_analyzer",
            "output": {
                "to": "routing_decision"
            }
        },
        {
            "id": "routing_decision",
            "type": "navigation",
            "navigation": {
                "mode": "hybrid",
                "steps": [
                    {
                        "id": "technical_support",
                        "name": "Technical Support",
                        "description": "Route to technical support team for technical issues",
                        "type": "agent",
                        "agent_id": "technical_agent",
                        "conditions": [
                            {
                                "field": "output.category",
                                "operator": "eq",
                                "value": "technical"
                            }
                        ],
                        "weight": 1.0
                    },
                    {
                        "id": "billing_support",
                        "name": "Billing Support",
                        "description": "Route to billing team for payment and billing issues",
                        "type": "agent",
                        "agent_id": "billing_agent",
                        "conditions": [
                            {
                                "field": "output.category",
                                "operator": "eq",
                                "value": "billing"
                            }
                        ],
                        "weight": 1.0
                    },
                    {
                        "id": "general_inquiry",
                        "name": "General Inquiry",
                        "description": "Handle general questions and inquiries",
                        "type": "agent",
                        "agent_id": "general_agent",
                        "weight": 0.5
                    },
                    {
                        "id": "escalate",
                        "name": "Escalate to Human",
                        "description": "Escalate complex issues to human agent",
                        "type": "agent",
                        "agent_id": "human_escalation",
                        "conditions": [
                            {
                                "field": "output.complexity",
                                "operator": "gt",
                                "value": 0.8
                            }
                        ],
                        "weight": 2.0
                    }
                ],
                "rules": [
                    {
                        "conditions": [
                            {
                                "field": "output.priority",
                                "operator": "eq",
                                "value": "critical"
                            }
                        ],
                        "target_step": "escalate",
                        "priority": 10,
                        "description": "Auto-escalate critical issues"
                    }
                ],
                "prompt_template": DEFAULT_NAVIGATION_PROMPT,
                "max_attempts": 3,
                "timeout_seconds": 30,
                "fallback_step": "general_inquiry"
            }
        }
    ],
    "global_config": {
        "tracking_enabled": True,
        "analytics_enabled": True,
        "optimization_enabled": True
    }
} 