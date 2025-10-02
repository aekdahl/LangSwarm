"""
Navigation Configuration Schema

This module defines the schema for navigation-enabled workflows,
including validation, documentation, and configuration utilities.
"""

import json
import yaml
from typing import Dict, List, Optional, Any, Union, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError


class NavigationMode(str, Enum):
    """Available navigation modes"""
    MANUAL = "manual"           # Agent chooses from available steps
    CONDITIONAL = "conditional" # Rule-based routing only
    HYBRID = "hybrid"          # Combination of manual and conditional
    WEIGHTED = "weighted"      # Probabilistic routing based on weights


class ConditionOperator(str, Enum):
    """Available condition operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    REGEX = "regex"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


@dataclass
class NavigationCondition:
    """Configuration for a single navigation condition"""
    field: str
    operator: ConditionOperator
    value: Any
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
            "description": self.description
        }


@dataclass
class NavigationRule:
    """Configuration for a conditional navigation rule"""
    conditions: List[NavigationCondition]
    target_step: str
    priority: int = 0
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "target_step": self.target_step,
            "priority": self.priority,
            "description": self.description
        }


@dataclass
class NavigationStep:
    """Configuration for a navigation step option"""
    id: str
    name: str
    description: str
    conditions: List[NavigationCondition] = field(default_factory=list)
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions] if self.conditions else None,
            "weight": self.weight if self.weight != 1.0 else None,
            "metadata": self.metadata if self.metadata else None
        }


@dataclass
class NavigationConfig:
    """Complete navigation configuration for a workflow step"""
    mode: NavigationMode = NavigationMode.MANUAL
    available_steps: List[NavigationStep] = field(default_factory=list)
    rules: List[NavigationRule] = field(default_factory=list)
    fallback_step: Optional[str] = None
    timeout_seconds: int = 30
    max_attempts: int = 3
    prompt_template: Optional[str] = None
    tracking_enabled: bool = True
    analytics_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        config = {
            "mode": self.mode.value,
            "available_steps": [step.to_dict() for step in self.available_steps],
            "fallback_step": self.fallback_step,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
            "tracking_enabled": self.tracking_enabled,
            "analytics_enabled": self.analytics_enabled
        }
        
        # Only include optional fields if they have values
        if self.rules:
            config["rules"] = [rule.to_dict() for rule in self.rules]
        if self.prompt_template:
            config["prompt_template"] = self.prompt_template
        if self.metadata:
            config["metadata"] = self.metadata
            
        return config


class NavigationSchemaValidator:
    """Validates navigation configurations against JSON schema"""
    
    def __init__(self):
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the navigation configuration JSON schema"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Navigation Configuration Schema",
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["manual", "conditional", "hybrid", "weighted"],
                    "default": "manual",
                    "description": "Navigation decision mode"
                },
                "available_steps": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/navigation_step"
                    },
                    "minItems": 1,
                    "description": "List of available navigation target steps"
                },
                "rules": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/navigation_rule"
                    },
                    "description": "Conditional routing rules (optional)"
                },
                "fallback_step": {
                    "type": "string",
                    "description": "Default step when no valid options available"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 30,
                    "description": "Maximum time to wait for navigation decision"
                },
                "max_attempts": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                    "description": "Maximum retry attempts for failed navigation"
                },
                "prompt_template": {
                    "type": "string",
                    "description": "Custom prompt template for navigation decisions"
                },
                "tracking_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable decision tracking and analytics"
                },
                "analytics_enabled": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Enable analytics collection"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional configuration metadata"
                }
            },
            "required": ["available_steps"],
            "definitions": {
                "navigation_step": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$",
                            "description": "Unique step identifier"
                        },
                        "name": {
                            "type": "string",
                            "minLength": 1,
                            "description": "Human-readable step name"
                        },
                        "description": {
                            "type": "string",
                            "minLength": 1,
                            "description": "Step description for agent context"
                        },
                        "conditions": {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/navigation_condition"
                            },
                            "description": "Conditions for step availability"
                        },
                        "weight": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 10.0,
                            "default": 1.0,
                            "description": "Step selection weight for weighted mode"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional step metadata"
                        }
                    },
                    "required": ["id", "name", "description"]
                },
                "navigation_rule": {
                    "type": "object",
                    "properties": {
                        "conditions": {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/navigation_condition"
                            },
                            "minItems": 1,
                            "description": "Conditions that must be met for rule activation"
                        },
                        "target_step": {
                            "type": "string",
                            "description": "Step to navigate to when rule matches"
                        },
                        "priority": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "Rule priority (higher values evaluated first)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Human-readable rule description"
                        }
                    },
                    "required": ["conditions", "target_step"]
                },
                "navigation_condition": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "minLength": 1,
                            "description": "Field path to evaluate (e.g., 'output.category')"
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["eq", "ne", "gt", "lt", "gte", "lte", "contains", "not_contains", 
                                   "in", "not_in", "exists", "not_exists", "regex", "starts_with", "ends_with"],
                            "description": "Comparison operator"
                        },
                        "value": {
                            "description": "Value to compare against (type depends on operator)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Human-readable condition description"
                        }
                    },
                    "required": ["field", "operator", "value"]
                }
            }
        }
    
    def validate(self, config: Dict[str, Any]) -> None:
        """Validate navigation configuration against schema"""
        try:
            validate(instance=config, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Navigation configuration validation failed: {e.message}")
    
    def validate_with_details(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration and return detailed results"""
        try:
            validate(instance=config, schema=self.schema)
            return {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": [e.message],
                "warnings": []
            }


class NavigationConfigBuilder:
    """Builder class for creating navigation configurations"""
    
    def __init__(self):
        self.config = NavigationConfig()
    
    def set_mode(self, mode: Union[NavigationMode, str]) -> 'NavigationConfigBuilder':
        """Set navigation mode"""
        if isinstance(mode, str):
            mode = NavigationMode(mode)
        self.config.mode = mode
        return self
    
    def add_step(self, step_id: str, name: str, description: str, 
                 conditions: Optional[List[NavigationCondition]] = None,
                 weight: float = 1.0, 
                 metadata: Optional[Dict[str, Any]] = None) -> 'NavigationConfigBuilder':
        """Add a navigation step option"""
        step = NavigationStep(
            id=step_id,
            name=name,
            description=description,
            conditions=conditions or [],
            weight=weight,
            metadata=metadata or {}
        )
        self.config.available_steps.append(step)
        return self
    
    def add_condition_step(self, step_id: str, name: str, description: str,
                          field: str, operator: Union[ConditionOperator, str], value: Any,
                          condition_description: Optional[str] = None) -> 'NavigationConfigBuilder':
        """Add a step with a single condition"""
        if isinstance(operator, str):
            operator = ConditionOperator(operator)
        
        condition = NavigationCondition(
            field=field,
            operator=operator,
            value=value,
            description=condition_description
        )
        
        return self.add_step(step_id, name, description, conditions=[condition])
    
    def add_rule(self, target_step: str, conditions: List[NavigationCondition],
                 priority: int = 0, description: Optional[str] = None) -> 'NavigationConfigBuilder':
        """Add a conditional routing rule"""
        rule = NavigationRule(
            conditions=conditions,
            target_step=target_step,
            priority=priority,
            description=description
        )
        self.config.rules.append(rule)
        return self
    
    def set_fallback(self, step_id: str) -> 'NavigationConfigBuilder':
        """Set fallback step"""
        self.config.fallback_step = step_id
        return self
    
    def set_timeout(self, seconds: int) -> 'NavigationConfigBuilder':
        """Set navigation timeout"""
        self.config.timeout_seconds = seconds
        return self
    
    def set_tracking(self, enabled: bool = True) -> 'NavigationConfigBuilder':
        """Enable/disable tracking"""
        self.config.tracking_enabled = enabled
        return self
    
    def set_analytics(self, enabled: bool = True) -> 'NavigationConfigBuilder':
        """Enable/disable analytics"""
        self.config.analytics_enabled = enabled
        return self
    
    def set_prompt_template(self, template: str) -> 'NavigationConfigBuilder':
        """Set custom prompt template"""
        self.config.prompt_template = template
        return self
    
    def build(self) -> NavigationConfig:
        """Build the final configuration"""
        # Validate the configuration
        validator = NavigationSchemaValidator()
        config_dict = self.config.to_dict()
        validator.validate(config_dict)
        
        return self.config
    
    def to_yaml(self) -> str:
        """Export configuration as YAML"""
        config = self.build()
        return yaml.dump(config.to_dict(), default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Export configuration as JSON"""
        config = self.build()
        return json.dumps(config.to_dict(), indent=2)


class NavigationConfigLoader:
    """Utility for loading and parsing navigation configurations"""
    
    def __init__(self):
        self.validator = NavigationSchemaValidator()
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> NavigationConfig:
        """Load configuration from dictionary"""
        # Validate first
        self.validator.validate(config_dict)
        
        # Parse conditions and rules
        available_steps = []
        for step_data in config_dict.get("available_steps", []):
            conditions = []
            for cond_data in step_data.get("conditions", []):
                condition = NavigationCondition(
                    field=cond_data["field"],
                    operator=ConditionOperator(cond_data["operator"]),
                    value=cond_data["value"],
                    description=cond_data.get("description")
                )
                conditions.append(condition)
            
            step = NavigationStep(
                id=step_data["id"],
                name=step_data["name"],
                description=step_data["description"],
                conditions=conditions,
                weight=step_data.get("weight", 1.0),
                metadata=step_data.get("metadata", {})
            )
            available_steps.append(step)
        
        # Parse rules
        rules = []
        for rule_data in config_dict.get("rules", []):
            conditions = []
            for cond_data in rule_data["conditions"]:
                condition = NavigationCondition(
                    field=cond_data["field"],
                    operator=ConditionOperator(cond_data["operator"]),
                    value=cond_data["value"],
                    description=cond_data.get("description")
                )
                conditions.append(condition)
            
            rule = NavigationRule(
                conditions=conditions,
                target_step=rule_data["target_step"],
                priority=rule_data.get("priority", 0),
                description=rule_data.get("description")
            )
            rules.append(rule)
        
        # Create configuration
        config = NavigationConfig(
            mode=NavigationMode(config_dict.get("mode", "manual")),
            available_steps=available_steps,
            rules=rules,
            fallback_step=config_dict.get("fallback_step"),
            timeout_seconds=config_dict.get("timeout_seconds", 30),
            max_attempts=config_dict.get("max_attempts", 3),
            prompt_template=config_dict.get("prompt_template"),
            tracking_enabled=config_dict.get("tracking_enabled", True),
            analytics_enabled=config_dict.get("analytics_enabled", True),
            metadata=config_dict.get("metadata", {})
        )
        
        return config
    
    def load_from_yaml(self, yaml_path: Union[str, Path]) -> NavigationConfig:
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return self.load_from_dict(config_dict)
    
    def load_from_json(self, json_path: Union[str, Path]) -> NavigationConfig:
        """Load configuration from JSON file"""
        with open(json_path, 'r') as f:
            config_dict = json.load(f)
        return self.load_from_dict(config_dict)


# Convenience functions
def create_navigation_config() -> NavigationConfigBuilder:
    """Create a new navigation configuration builder"""
    return NavigationConfigBuilder()


def validate_navigation_config(config: Dict[str, Any]) -> None:
    """Validate a navigation configuration dictionary"""
    validator = NavigationSchemaValidator()
    validator.validate(config)


def load_navigation_config(source: Union[str, Path, Dict[str, Any]]) -> NavigationConfig:
    """Load navigation configuration from various sources"""
    loader = NavigationConfigLoader()
    
    if isinstance(source, dict):
        return loader.load_from_dict(source)
    elif isinstance(source, (str, Path)):
        path = Path(source)
        if path.suffix.lower() in ['.yml', '.yaml']:
            return loader.load_from_yaml(path)
        elif path.suffix.lower() == '.json':
            return loader.load_from_json(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")


# Export the schema for external use
def get_navigation_schema() -> Dict[str, Any]:
    """Get the navigation configuration JSON schema"""
    validator = NavigationSchemaValidator()
    return validator.schema 