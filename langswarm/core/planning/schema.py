"""
YAML Schema Extensions and Parser for Planning System

Defines schemas for TaskBriefs, Plans, and action contracts in YAML format.
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .models import (
    TaskBrief, Plan, ActionContract, PlanPatch, BrainstormResult,
    CapabilityVerification
)

logger = logging.getLogger(__name__)


# Schema definitions for validation
PLANNING_SCHEMA = {
    "task_brief": {
        "type": "object",
        "properties": {
            "objective": {"type": "string", "required": True},
            "inputs": {"type": "object"},
            "required_outputs": {"type": "object"},
            "acceptance_tests": {"type": "array"},
            "constraints": {
                "type": "object",
                "properties": {
                    "cost_usd": {"type": "number"},
                    "latency_sec": {"type": "number"},
                    "privacy": {"type": "string"},
                    "security_level": {"type": "string"}
                }
            },
            "metadata": {"type": "object"}
        }
    },
    "action_contract": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "required": True},
            "intent": {"type": "string", "required": True},
            "agent_or_tool": {"type": "string", "required": True},
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
            "preconditions": {"type": "array"},
            "postconditions": {"type": "array"},
            "validators": {"type": "array"},
            "cost_estimate": {
                "type": "object",
                "properties": {
                    "usd": {"type": "number"},
                    "tokens_in": {"type": "integer"},
                    "tokens_out": {"type": "integer"}
                }
            },
            "latency_budget_sec": {"type": "number"},
            "confidence_floor": {"type": "number"},
            "side_effects": {"type": "array"},
            "fallbacks": {"type": "array"},
            "escalation": {"type": "object"},
            "gates": {"type": "array"},
            "retrospects": {"type": "array"},
            "compensation": {"type": "object"},
            "requires_retro_green": {"type": "array"}
        }
    },
    "plan": {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "required": True},
            "version": {"type": "integer"},
            "task_brief": {"$ref": "#/task_brief"},
            "steps": {"type": "array", "items": {"$ref": "#/action_contract"}},
            "dag": {"type": "object"},
            "metadata": {"type": "object"}
        }
    }
}


class PlanningYAMLParser:
    """
    Parser for planning system YAML files.
    
    Supports:
    - TaskBrief definitions
    - Plan definitions
    - Action contract definitions
    - Plan patches
    """
    
    def __init__(self):
        self.schema = PLANNING_SCHEMA
    
    def parse_task_brief(self, yaml_path: str) -> TaskBrief:
        """
        Parse TaskBrief from YAML file.
        
        Example YAML:
        ```yaml
        objective: "Process expense reports for Q4"
        inputs:
          data_source: "gs://expenses/q4/*.csv"
          schema_version: "v3.2"
        required_outputs:
          summary_report: "parquet"
          error_log: "json"
        acceptance_tests:
          - name: "row_count"
            type: "assertion"
            assertion: "{{ output.count > 0 }}"
        constraints:
          cost_usd: 5.0
          latency_sec: 300
          privacy: "pii_restricted"
        metadata:
          owner: "@team-finance"
          oncall: "finance-ops"
        ```
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            TaskBrief instance
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return TaskBrief(
            objective=data["objective"],
            inputs=data.get("inputs", {}),
            required_outputs=data.get("required_outputs", {}),
            acceptance_tests=data.get("acceptance_tests", []),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {})
        )
    
    def parse_plan(self, yaml_path: str) -> Plan:
        """
        Parse Plan from YAML file.
        
        Example YAML:
        ```yaml
        plan_id: "expense_processing_2025"
        version: 0
        task_brief:
          objective: "Process expenses"
          # ... task brief fields
        steps:
          - id: "ingest"
            intent: "Load expense data from GCS"
            agent_or_tool: "gcs_reader"
            inputs:
              path: "gs://expenses/*.csv"
            outputs:
              data: "dataframe"
            postconditions:
              - "len(output.data) > 0"
          - id: "validate"
            intent: "Validate expense records"
            agent_or_tool: "validator"
            inputs:
              data: "{{ ingest.data }}"
        dag:
          ingest: []
          validate: ["ingest"]
        ```
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Plan instance
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse task brief
        task_brief = TaskBrief(**data["task_brief"])
        
        # Parse steps
        steps = [self._parse_action_contract(step_data) for step_data in data["steps"]]
        
        return Plan(
            plan_id=data["plan_id"],
            version=data.get("version", 0),
            task_brief=task_brief,
            steps=steps,
            dag=data.get("dag", {}),
            metadata=data.get("metadata", {})
        )
    
    def parse_action_contract(self, yaml_path: str) -> ActionContract:
        """
        Parse single ActionContract from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            ActionContract instance
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return self._parse_action_contract(data)
    
    def _parse_action_contract(self, data: Dict[str, Any]) -> ActionContract:
        """Parse ActionContract from dict"""
        return ActionContract(
            id=data["id"],
            intent=data["intent"],
            agent_or_tool=data["agent_or_tool"],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            preconditions=data.get("preconditions", []),
            postconditions=data.get("postconditions", []),
            validators=data.get("validators", []),
            cost_estimate=data.get("cost_estimate", {}),
            latency_budget_sec=data.get("latency_budget_sec", 30.0),
            confidence_floor=data.get("confidence_floor", 0.8),
            side_effects=data.get("side_effects", []),
            fallbacks=data.get("fallbacks", []),
            escalation=data.get("escalation", {}),
            gates=data.get("gates", []),
            retrospects=data.get("retrospects", []),
            compensation=data.get("compensation"),
            requires_retro_green=data.get("requires_retro_green", []),
            metadata=data.get("metadata", {})
        )
    
    def export_task_brief(self, brief: TaskBrief, yaml_path: str) -> None:
        """Export TaskBrief to YAML file"""
        data = {
            "objective": brief.objective,
            "inputs": brief.inputs,
            "required_outputs": brief.required_outputs,
            "acceptance_tests": brief.acceptance_tests,
            "constraints": brief.constraints,
            "metadata": brief.metadata
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def export_plan(self, plan: Plan, yaml_path: str) -> None:
        """Export Plan to YAML file"""
        data = {
            "plan_id": plan.plan_id,
            "version": plan.version,
            "task_brief": {
                "objective": plan.task_brief.objective,
                "inputs": plan.task_brief.inputs,
                "required_outputs": plan.task_brief.required_outputs,
                "acceptance_tests": plan.task_brief.acceptance_tests,
                "constraints": plan.task_brief.constraints,
                "metadata": plan.task_brief.metadata
            },
            "steps": [self._export_action_contract(step) for step in plan.steps],
            "dag": plan.dag,
            "metadata": plan.metadata
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def _export_action_contract(self, contract: ActionContract) -> Dict[str, Any]:
        """Export ActionContract to dict"""
        result = {
            "id": contract.id,
            "intent": contract.intent,
            "agent_or_tool": contract.agent_or_tool,
            "inputs": contract.inputs,
            "outputs": contract.outputs,
            "preconditions": contract.preconditions,
            "postconditions": contract.postconditions,
            "validators": contract.validators,
            "cost_estimate": contract.cost_estimate,
            "latency_budget_sec": contract.latency_budget_sec,
            "confidence_floor": contract.confidence_floor,
            "side_effects": contract.side_effects,
            "fallbacks": contract.fallbacks,
            "escalation": contract.escalation,
            "gates": contract.gates
        }
        
        # Add retrospect-related fields if present
        if contract.retrospects:
            result["retrospects"] = contract.retrospects
        if contract.compensation:
            result["compensation"] = contract.compensation
        if contract.requires_retro_green:
            result["requires_retro_green"] = contract.requires_retro_green
        
        return result


def validate_yaml_schema(data: Dict[str, Any], schema_name: str) -> tuple[bool, List[str]]:
    """
    Validate YAML data against schema.
    
    Args:
        data: Parsed YAML data
        schema_name: Name of schema to validate against
        
    Returns:
        Tuple of (valid, errors)
    """
    schema = PLANNING_SCHEMA.get(schema_name)
    if not schema:
        return False, [f"Unknown schema: {schema_name}"]
    
    errors = []
    
    # Check required fields
    required = [k for k, v in schema["properties"].items() 
                if isinstance(v, dict) and v.get("required")]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check types (simplified)
    for field, spec in schema["properties"].items():
        if field in data and isinstance(spec, dict):
            expected_type = spec.get("type")
            actual_value = data[field]
            
            if expected_type == "object" and not isinstance(actual_value, dict):
                errors.append(f"Field '{field}' should be object, got {type(actual_value).__name__}")
            elif expected_type == "array" and not isinstance(actual_value, list):
                errors.append(f"Field '{field}' should be array, got {type(actual_value).__name__}")
            elif expected_type == "string" and not isinstance(actual_value, str):
                errors.append(f"Field '{field}' should be string, got {type(actual_value).__name__}")
    
    return len(errors) == 0, errors




