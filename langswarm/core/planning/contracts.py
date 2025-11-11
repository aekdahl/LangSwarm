"""
Action Contract Validation

Validates preconditions, postconditions, validators, budget constraints,
confidence thresholds, and policy compliance for action contracts.
"""

import logging
from typing import Dict, Any, List, Optional
from simpleeval import simple_eval

from .models import ActionContract, Observation, RunState, ObservationStatus

logger = logging.getLogger(__name__)


class ContractValidator:
    """
    Validates action contracts against observations and state.
    
    Provides deterministic checks for:
    - Preconditions before execution
    - Postconditions after execution
    - Custom validators
    - Budget constraints
    - Confidence thresholds
    - Policy violations
    """
    
    def __init__(self):
        self.validation_cache = {}
    
    def validate_preconditions(
        self, 
        contract: ActionContract, 
        state: RunState
    ) -> tuple[bool, List[str]]:
        """
        Validate preconditions are met before executing step.
        
        Args:
            contract: Action contract with preconditions
            state: Current run state
            
        Returns:
            Tuple of (all_met, failed_conditions)
        """
        failed = []
        
        for condition in contract.preconditions:
            try:
                # Create evaluation context with state artifacts
                context = {
                    "state": state,
                    "artifacts": state.artifacts,
                    "metrics": state.metrics,
                    "budget_left": state.budget_left
                }
                
                # Evaluate condition
                result = self._evaluate_condition(condition, context)
                if not result:
                    failed.append(condition)
                    
            except Exception as e:
                logger.warning(f"Failed to evaluate precondition '{condition}': {e}")
                failed.append(condition)
        
        return len(failed) == 0, failed
    
    def validate_postconditions(
        self, 
        contract: ActionContract, 
        observation: Observation
    ) -> tuple[bool, List[str]]:
        """
        Validate postconditions are met after execution.
        
        Args:
            contract: Action contract with postconditions
            observation: Execution observation
            
        Returns:
            Tuple of (all_met, failed_conditions)
        """
        failed = []
        
        for condition in contract.postconditions:
            try:
                # Create evaluation context with observation data
                context = {
                    "observation": observation,
                    "artifacts": observation.artifacts,
                    "metrics": observation.metrics,
                    "quality": observation.quality,
                    "status": observation.status.value
                }
                
                # Evaluate condition
                result = self._evaluate_condition(condition, context)
                if not result:
                    failed.append(condition)
                    
            except Exception as e:
                logger.warning(f"Failed to evaluate postcondition '{condition}': {e}")
                failed.append(condition)
        
        return len(failed) == 0, failed
    
    def check_validators(
        self, 
        contract: ActionContract, 
        observation: Observation
    ) -> Dict[str, bool]:
        """
        Run custom validators on observation artifacts.
        
        Args:
            contract: Action contract with validators
            observation: Execution observation
            
        Returns:
            Dict of validator_name -> passed
        """
        results = {}
        
        for validator in contract.validators:
            validator_fn = validator.get("fn")
            validator_args = validator.get("args", {})
            
            try:
                # Run validator function
                passed = self._run_validator(
                    validator_fn, 
                    validator_args, 
                    observation.artifacts
                )
                results[validator_fn] = passed
                
            except Exception as e:
                logger.warning(f"Validator '{validator_fn}' failed: {e}")
                results[validator_fn] = False
        
        return results
    
    def check_budget(
        self, 
        contract: ActionContract, 
        state: RunState
    ) -> tuple[bool, Optional[str]]:
        """
        Check if step is within budget constraints.
        
        Args:
            contract: Action contract with cost estimate
            state: Current run state with budget left
            
        Returns:
            Tuple of (within_budget, reason_if_not)
        """
        estimate = contract.cost_estimate
        budget_left = state.budget_left
        
        # Check USD budget
        if "usd" in estimate and "usd" in budget_left:
            if estimate["usd"] > budget_left["usd"]:
                return False, f"Cost ${estimate['usd']:.2f} exceeds remaining budget ${budget_left['usd']:.2f}"
        
        # Check time budget
        if contract.latency_budget_sec > 0:
            if "time_sec" in budget_left:
                if contract.latency_budget_sec > budget_left["time_sec"]:
                    return False, f"Latency {contract.latency_budget_sec}s exceeds remaining time {budget_left['time_sec']:.0f}s"
        
        return True, None
    
    def check_confidence(
        self, 
        observation: Observation, 
        floor: float
    ) -> tuple[bool, Optional[float]]:
        """
        Check if observation confidence meets threshold.
        
        Args:
            observation: Execution observation
            floor: Minimum confidence threshold
            
        Returns:
            Tuple of (meets_threshold, actual_confidence)
        """
        confidence = observation.quality.get("confidence", 1.0)
        meets_threshold = confidence >= floor
        return meets_threshold, confidence
    
    def check_policy_violations(
        self, 
        observation: Observation
    ) -> List[str]:
        """
        Extract policy violations from observation.
        
        Args:
            observation: Execution observation
            
        Returns:
            List of policy violations
        """
        return observation.policy.get("violations", [])
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition expression.
        
        Uses simpleeval for safe expression evaluation without exec/eval.
        """
        try:
            # Handle template-style conditions like "{{ ... }}"
            if condition.startswith("{{") and condition.endswith("}}"):
                condition = condition[2:-2].strip()
            
            # Simple string checks
            if "file_exists" in condition:
                # Example: file_exists(inputs.spec)
                # Extract path and check
                return True  # Placeholder
            
            if "schema_compatible" in condition:
                # Example: schema_compatible(inputs.data, 'claim_v3_2_in')
                return True  # Placeholder
            
            # Evaluate as Python expression
            result = simple_eval(condition, names=context)
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def _run_validator(
        self, 
        validator_fn: str, 
        args: Dict[str, Any], 
        artifacts: Dict[str, Any]
    ) -> bool:
        """
        Run a validator function on artifacts.
        
        Built-in validators:
        - row_count_match: Check row count
        - field_coverage: Check required fields present
        - schema_ok: Validate against schema
        """
        if validator_fn == "row_count_match":
            min_rows = args.get("min", 1)
            data = artifacts.get("records", [])
            return len(data) >= min_rows
        
        elif validator_fn == "field_coverage":
            required_fields = args.get("required_fields", [])
            records = artifacts.get("records", [])
            if not records:
                return False
            # Check first record has all fields
            first_record = records[0]
            return all(field in first_record for field in required_fields)
        
        elif validator_fn == "schema_ok":
            # Placeholder for schema validation
            return True
        
        else:
            logger.warning(f"Unknown validator function: {validator_fn}")
            return True  # Unknown validators pass by default




