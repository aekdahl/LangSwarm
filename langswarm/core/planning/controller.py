"""
Controller Decision Logic

Policy-driven decision-making: continue/retry/alternate/replan/escalate
"""

import logging
from typing import Optional

from .models import (
    ActionContract, Observation, RunState, Plan, Decision, 
    DecisionAction, Severity, ObservationStatus
)
from .contracts import ContractValidator
from .verifier import Verifier
from .policies import PolicyConfig

logger = logging.getLogger(__name__)


class Controller:
    """
    Policy-driven controller for deciding next actions.
    
    Follows decision tree:
    1. Check policy violations → escalate S1
    2. Check postconditions → continue if met
    3. Try local recovery (retry/alternate)
    4. Check budget/time guardrails → escalate S2
    5. Check confidence/drift → replan
    6. Default → replan
    """
    
    def __init__(self, policies: PolicyConfig):
        """
        Initialize controller with policies.
        
        Args:
            policies: PolicyConfig with thresholds and weights
        """
        self.policies = policies if isinstance(policies, PolicyConfig) else PolicyConfig.from_dict(policies)
        self.validator = ContractValidator()
        self.verifier = Verifier()
        self.decision_history = []
    
    def decide(
        self,
        step: ActionContract,
        observation: Observation,
        state: RunState,
        plan: Plan
    ) -> Decision:
        """
        Main decision function following policy tree.
        
        Args:
            step: Action contract that was executed
            observation: Execution observation
            state: Current run state
            plan: Current plan
            
        Returns:
            Decision with action, reason, and optional patch/next_step
        """
        logger.info(f"Making decision for step '{step.id}' with status {observation.status.value}")
        
        # 0) Policy hard-stops
        violations = self.validator.check_policy_violations(observation)
        if violations:
            decision = Decision(
                action=DecisionAction.ESCALATE,
                reason=f"policy_violation: {', '.join(violations)}",
                severity=Severity.S1
            )
            self._record_decision(decision, step, observation)
            return decision
        
        # 1) Success path - postconditions met
        if observation.status == ObservationStatus.OK:
            postconditions_met, failed = self.validator.validate_postconditions(step, observation)
            if postconditions_met:
                decision = Decision(
                    action=DecisionAction.CONTINUE,
                    reason="postconditions_met"
                )
                self._record_decision(decision, step, observation)
                return decision
        
        # 2) Local recovery - retry
        if self._can_retry(step, observation, state):
            decision = Decision(
                action=DecisionAction.RETRY,
                reason="transient_error_detected"
            )
            self._record_decision(decision, step, observation)
            return decision
        
        # 3) Local recovery - alternate
        if self._can_alternate(step, observation):
            alt_step = self._get_alternate_step(step)
            decision = Decision(
                action=DecisionAction.ALTERNATE,
                reason="alternate_available",
                next_step=alt_step
            )
            self._record_decision(decision, step, observation)
            return decision
        
        # 4) Budget/time guardrails
        if self._projected_overrun(state, plan):
            decision = Decision(
                action=DecisionAction.ESCALATE,
                reason="budget_overrun",
                severity=Severity.S2
            )
            self._record_decision(decision, step, observation)
            return decision
        
        # 5) Low confidence / data integrity
        confidence_met, actual_conf = self.validator.check_confidence(
            observation, 
            step.confidence_floor
        )
        
        if not confidence_met:
            if self._is_sla_imminent(state):
                decision = Decision(
                    action=DecisionAction.ESCALATE,
                    reason=f"low_confidence_critical: {actual_conf:.2f} < {step.confidence_floor}",
                    severity=Severity.S2
                )
            else:
                decision = Decision(
                    action=DecisionAction.REPLAN,
                    reason=f"low_confidence: {actual_conf:.2f} < {step.confidence_floor}"
                )
            self._record_decision(decision, step, observation)
            return decision
        
        # Check data integrity drift
        drift = self.verifier.check_integrity_drift(state, self.policies.to_dict()["thresholds"])
        if drift > self.policies.thresholds["integrity"]:
            decision = Decision(
                action=DecisionAction.REPLAN,
                reason=f"data_integrity_drift: {drift:.1%} > {self.policies.thresholds['integrity']:.1%}"
            )
            self._record_decision(decision, step, observation)
            return decision
        
        # 6) Default - replan
        decision = Decision(
            action=DecisionAction.REPLAN,
            reason=f"unknown_failure: status={observation.status.value}"
        )
        self._record_decision(decision, step, observation)
        return decision
    
    def _can_retry(
        self, 
        step: ActionContract, 
        observation: Observation,
        state: RunState
    ) -> bool:
        """
        Check if step can be retried.
        
        Retries are allowed for:
        - Transient errors (rate limits, timeouts, 5xx)
        - Soft fails with retry budget remaining
        """
        # Check if we've exceeded retry limit
        retry_count = self._get_retry_count(step.id, state)
        if retry_count >= self.policies.get_max_retries():
            return False
        
        # Check if observation indicates transient error
        if observation.status == ObservationStatus.SOFT_FAIL:
            # Check notes for transient error indicators
            notes_lower = observation.notes.lower()
            for error_type in self.policies.retry["transient_errors"]:
                if error_type in notes_lower:
                    return True
        
        return False
    
    def _can_alternate(
        self, 
        step: ActionContract, 
        observation: Observation
    ) -> bool:
        """
        Check if alternate fallback is available.
        """
        if not step.fallbacks:
            return False
        
        # Check for alternate type fallbacks
        for fallback in step.fallbacks:
            if fallback.get("type") == "alternate":
                return True
        
        return False
    
    def _get_alternate_step(self, step: ActionContract) -> Optional[ActionContract]:
        """
        Get alternate step from fallbacks.
        """
        for fallback in step.fallbacks:
            if fallback.get("type") == "alternate":
                # Create alternate step
                alt_agent = fallback.get("agent")
                alt_params = fallback.get("params", {})
                
                # Clone original step with alternates
                alt_step = ActionContract(
                    id=f"{step.id}_alt",
                    intent=step.intent,
                    agent_or_tool=alt_agent or step.agent_or_tool,
                    inputs={**step.inputs, **alt_params},
                    outputs=step.outputs,
                    preconditions=step.preconditions,
                    postconditions=step.postconditions,
                    validators=step.validators,
                    cost_estimate=step.cost_estimate,
                    latency_budget_sec=step.latency_budget_sec,
                    confidence_floor=step.confidence_floor
                )
                
                return alt_step
        
        return None
    
    def _projected_overrun(self, state: RunState, plan: Plan) -> bool:
        """
        Check if remaining budget is insufficient.
        
        Considers:
        - Remaining USD budget
        - Remaining time budget
        - Buffer for safety (from policies)
        """
        buffer = self.policies.thresholds["budget_buffer"]
        
        # Estimate remaining cost
        remaining_steps = [s for s in plan.steps if s.id not in state.artifacts]
        estimated_cost = sum(s.cost_estimate.get("usd", 0) for s in remaining_steps)
        estimated_time = sum(s.latency_budget_sec for s in remaining_steps)
        
        # Check USD budget
        budget_usd = state.budget_left.get("usd", float('inf'))
        if estimated_cost > budget_usd * (1 - buffer):
            logger.warning(f"Projected cost overrun: ${estimated_cost:.2f} > ${budget_usd:.2f}")
            return True
        
        # Check time budget
        budget_time = state.budget_left.get("time_sec", float('inf'))
        if estimated_time > budget_time * (1 - buffer):
            logger.warning(f"Projected time overrun: {estimated_time:.0f}s > {budget_time:.0f}s")
            return True
        
        return False
    
    def _is_sla_imminent(self, state: RunState) -> bool:
        """
        Check if SLA deadline is approaching.
        
        Returns True if less than 10% of time budget remains.
        """
        if "time_sec" not in state.budget_left:
            return False
        
        time_left = state.budget_left["time_sec"]
        total_time = state.plan.task_brief.constraints.get("latency_sec", float('inf'))
        
        if total_time == float('inf'):
            return False
        
        time_used_pct = 1.0 - (time_left / total_time)
        return time_used_pct > 0.9  # Less than 10% time remaining
    
    def _get_retry_count(self, step_id: str, state: RunState) -> int:
        """
        Get number of times this step has been retried.
        """
        # Count retries from decision history
        retries = 0
        for decision_record in self.decision_history:
            if (decision_record.get("step_id") == step_id and 
                decision_record.get("action") == DecisionAction.RETRY):
                retries += 1
        return retries
    
    def _record_decision(
        self, 
        decision: Decision, 
        step: ActionContract,
        observation: Observation
    ) -> None:
        """Record decision for history tracking"""
        self.decision_history.append({
            "step_id": step.id,
            "action": decision.action,
            "reason": decision.reason,
            "observation_status": observation.status.value,
            "timestamp": decision.timestamp
        })




