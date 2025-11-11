"""
Main Coordinator for Hierarchical Planning System

Orchestrates the complete control loop:
brainstorm → verify → plan → execute → sense → act/replan
"""

import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .models import (
    TaskBrief, Plan, RunState, ActionContract, Observation,
    Decision, DecisionAction, EscalationPayload, Severity,
    ObservationStatus, Checkpoint, Provenance, RetrospectJob
)
from .planner import Planner
from .executor import Executor
from .controller import Controller
from .verifier import Verifier
from .patcher import PlanPatcher
from .escalation import EscalationRouter
from .contracts import ContractValidator
from .policies import PolicyConfig, DEFAULT_POLICIES
from .lineage import LineageGraph, compute_artifact_hash, create_artifact_id
from .retrospect import RetrospectRunner
from .replay import ReplayManager

logger = logging.getLogger(__name__)


class Coordinator:
    """
    Main coordinator orchestrating the entire hierarchical planning system.
    
    Control Loop:
    1. Brainstorm actions
    2. Verify capabilities (escalate if missing)
    3. Generate plan
    4. Execute step
    5. Observe results
    6. Decide: continue/retry/alternate/replan/escalate
    7. Apply patches as needed
    8. Resume from appropriate point
    
    Integrates all LangSwarm components transparently.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize coordinator with configuration.
        
        Args:
            config: Configuration dict with:
                - llm: LLM provider for planning
                - agents: Agent registry
                - tools: Tool registry
                - policies: PolicyConfig or dict
                - escalation: Escalation config
        """
        # Initialize components
        self.planner = Planner(
            llm_provider=config["llm"],
            agent_registry=config.get("agents"),
            tool_registry=config.get("tools")
        )
        
        self.executor = Executor(
            agent_registry=config.get("agents"),
            tool_registry=config.get("tools")
        )
        
        policies = config.get("policies", DEFAULT_POLICIES)
        if isinstance(policies, dict):
            policies = PolicyConfig.from_dict(policies)
        self.controller = Controller(policies=policies)
        
        self.verifier = Verifier()
        self.validator = ContractValidator()
        self.patcher = PlanPatcher()
        
        self.escalation = EscalationRouter(
            config=config.get("escalation", {})
        )
        
        # Retrospective validation components
        self.lineage = LineageGraph()
        self.retrospect_runner = RetrospectRunner(self.verifier)
        self.replay_manager = ReplayManager(self.lineage, self.patcher)
        
        self.policies = policies
        self.execution_history = []
        self.enable_retrospects = config.get("enable_retrospects", True)
    
    async def execute_task(self, task_brief: TaskBrief) -> RunState:
        """
        Main execution loop with adaptive replanning.
        
        Args:
            task_brief: Task definition
            
        Returns:
            Final RunState with results or failure
        """
        run_id = str(uuid.uuid4())
        logger.info(f"Starting task execution {run_id}: {task_brief.objective}")
        
        # Phase 1: Brainstorm
        logger.info("Phase 1: Brainstorming actions...")
        brainstorm = await self.planner.brainstorm_actions(task_brief)
        
        # Phase 2: Verify capabilities
        logger.info("Phase 2: Verifying capabilities...")
        capabilities = await self.planner.verify_capabilities(brainstorm, task_brief)
        
        # Check if escalation needed before starting
        if capabilities.escalation_required:
            logger.warning("Missing required capabilities, escalating early")
            payload = EscalationPayload(
                plan_id="pre-plan",
                severity=Severity.S2,
                trigger="missing_capabilities",
                step="capability_verification",
                observation={"missing": capabilities.missing_capabilities},
                last_actions=[],
                proposed_fix="Acquire missing capabilities: " + ", ".join(capabilities.missing_capabilities),
                next_safe_actions=["abort", "provide_capabilities"],
                links={}
            )
            await self.escalation.escalate(payload)
            
            # Return early with halted state
            return self._create_initial_state(run_id, None, task_brief, "halted_missing_capabilities")
        
        # Phase 3: Generate plan
        logger.info("Phase 3: Generating execution plan...")
        plan = await self.planner.generate_plan(task_brief, brainstorm, capabilities)
        version = 0
        
        # Initialize state
        state = self._init_state(run_id, task_brief, plan)
        
        # Phase 4-7: Execution loop
        logger.info("Phase 4-7: Executing plan with adaptive control...")
        replan_count = 0
        max_replans = self.policies.limits["max_replans"]
        
        while state.cursor < len(plan.steps) and state.status == "running":
            # Check for halt
            if self.escalation.is_halted(plan.plan_id):
                logger.warning(f"Execution halted for plan {plan.plan_id}")
                state.status = "halted"
                break
            
            # Check execution time limit
            elapsed = (datetime.now(timezone.utc) - state.created_at).total_seconds()
            if elapsed > self.policies.limits["max_execution_time_sec"]:
                logger.error("Execution time limit exceeded")
                state.status = "timeout"
                break
            
            # Get next step in topological order
            ordered_steps = plan.get_topological_order()
            if state.cursor >= len(ordered_steps):
                break
            
            step = ordered_steps[state.cursor]
            logger.info(f"Executing step {state.cursor + 1}/{len(ordered_steps)}: {step.id}")
            
            # Check preconditions
            preconditions_met, failed_preconditions = self.validator.validate_preconditions(step, state)
            if not preconditions_met:
                logger.warning(f"Preconditions not met: {failed_preconditions}")
                decision = Decision(
                    action=DecisionAction.REPLAN,
                    reason=f"preconditions_not_met: {', '.join(failed_preconditions)}"
                )
            else:
                # Execute step
                observation = await self.executor.execute_step(step, state)
                
                # Update state with observation
                state.update_from_observation(observation)
                
                # Emit checkpoint for retrospective validation
                if self.enable_retrospects:
                    checkpoint = self._emit_checkpoint(step, observation, state)
                    
                    # Schedule retrospects if configured
                    if step.retrospects:
                        await self._schedule_retrospects(step, checkpoint)
                
                # Verify (optional step-level validators)
                if step.validators:
                    validator_results = self.validator.check_validators(step, observation)
                    state.test_results[step.id] = validator_results
                
                # Decide next action
                decision = self.controller.decide(step, observation, state, plan)
            
            # Handle decision
            handled = await self._handle_decision(
                decision, step, state, plan, version, replan_count, max_replans
            )
            
            if not handled:
                # Decision handling failed, abort
                state.status = "failed"
                break
            
            # Check if plan was patched
            if decision.action == DecisionAction.REPLAN:
                # Plan was patched, reload it
                if decision.patch:
                    plan = self.patcher.apply_patch(plan, decision.patch)
                    version += 1
                    replan_count += 1
                    state.plan = plan
                    # Reset cursor to appropriate point
                    state.cursor = self._find_resume_point(plan, state)
                    continue
            
            # Move to next step
            if decision.action == DecisionAction.CONTINUE:
                state.cursor += 1
        
        # Final status
        if state.status == "running":
            state.status = "completed"
        
        logger.info(f"Task execution completed with status: {state.status}")
        
        # Record in history
        self.execution_history.append({
            "run_id": run_id,
            "plan_id": plan.plan_id,
            "final_version": version,
            "status": state.status,
            "steps_completed": len(state.artifacts),
            "replans": replan_count,
            "cost_usd": state.metrics.get("cost_usd", 0.0),
            "latency_sec": (state.updated_at - state.created_at).total_seconds()
        })
        
        return state
    
    async def _handle_decision(
        self,
        decision: Decision,
        step: ActionContract,
        state: RunState,
        plan: Plan,
        version: int,
        replan_count: int,
        max_replans: int
    ) -> bool:
        """
        Handle controller decision.
        
        Returns True if handled successfully, False to abort.
        """
        logger.info(f"Decision: {decision.action.value} - {decision.reason}")
        
        if decision.action == DecisionAction.CONTINUE:
            # Success, move on
            return True
        
        elif decision.action == DecisionAction.RETRY:
            # Retry the same step
            logger.info(f"Retrying step '{step.id}'")
            # Executor will handle retry in next iteration
            return True
        
        elif decision.action == DecisionAction.ALTERNATE:
            # Use alternate step
            if decision.next_step:
                logger.info(f"Using alternate: {decision.next_step.agent_or_tool}")
                # Execute alternate
                alt_observation = await self.executor.execute_step(decision.next_step, state)
                state.update_from_observation(alt_observation)
                
                # Record param change as patch
                patch = self.patcher.create_param_patch(
                    plan_id=plan.plan_id,
                    from_version=version,
                    step_id=step.id,
                    old_params={"agent_or_tool": step.agent_or_tool},
                    new_params={"agent_or_tool": decision.next_step.agent_or_tool},
                    reason=decision.reason
                )
                decision.patch = patch
                
                return True
            return False
        
        elif decision.action == DecisionAction.REPLAN:
            # Check replan limit
            if replan_count >= max_replans:
                logger.error(f"Max replans ({max_replans}) exceeded")
                state.status = "failed_max_replans"
                return False
            
            # Generate patch
            logger.info("Generating plan patch...")
            # Create observation from current state
            last_obs = Observation(
                action_id=step.id,
                status=ObservationStatus.SOFT_FAIL,
                artifacts=state.artifacts.get(step.id, {}),
                metrics=state.metrics,
                quality={"confidence": 0.5},
                policy={"violations": []},
                notes=decision.reason
            )
            
            patch = await self.planner.generate_patch(plan, state, last_obs)
            decision.patch = patch
            
            return True
        
        elif decision.action == DecisionAction.ESCALATE:
            # Escalate to humans
            logger.warning(f"Escalating: {decision.reason}")
            
            payload = self._create_escalation_payload(
                plan, step, state, decision
            )
            
            result = await self.escalation.escalate(payload)
            
            if result == "halted_awaiting_human":
                state.status = "halted"
                return False
            
            # For S2/S3, can continue with replan
            return True
        
        return False
    
    def _init_state(
        self,
        run_id: str,
        brief: TaskBrief,
        plan: Plan
    ) -> RunState:
        """Initialize run state"""
        return RunState(
            run_id=run_id,
            plan=plan,
            cursor=0,
            artifacts={},
            metrics={},
            test_results={},
            drift_metrics={},
            budget_left={
                "usd": brief.constraints.get("cost_usd", float('inf')),
                "time_sec": brief.constraints.get("latency_sec", float('inf'))
            },
            status="running"
        )
    
    def _create_initial_state(
        self,
        run_id: str,
        plan: Optional[Plan],
        brief: TaskBrief,
        status: str
    ) -> RunState:
        """Create initial state for early termination"""
        return RunState(
            run_id=run_id,
            plan=plan or Plan(
                plan_id="empty",
                version=0,
                task_brief=brief,
                steps=[],
                dag={}
            ),
            cursor=0,
            artifacts={},
            metrics={},
            test_results={},
            drift_metrics={},
            budget_left={"usd": 0, "time_sec": 0},
            status=status
        )
    
    def _find_resume_point(self, plan: Plan, state: RunState) -> int:
        """Find appropriate cursor position after replan"""
        # Resume from first uncompleted step
        for i, step in enumerate(plan.get_topological_order()):
            if step.id not in state.artifacts:
                return i
        return len(plan.steps)
    
    def _create_escalation_payload(
        self,
        plan: Plan,
        step: ActionContract,
        state: RunState,
        decision: Decision
    ) -> EscalationPayload:
        """Create escalation payload"""
        return EscalationPayload(
            plan_id=plan.plan_id,
            severity=decision.severity or Severity.S3,
            trigger=decision.reason.split(':')[0],  # Extract trigger type
            step=step.id,
            observation={
                "status": state.status,
                "metrics": state.metrics,
                "artifacts_count": len(state.artifacts)
            },
            last_actions=self.controller.decision_history[-3:] if self.controller.decision_history else [],
            proposed_fix=decision.patch.reason if decision.patch else None,
            next_safe_actions=["abort", "approve_replan", "provide_input"],
            links={
                "trace": f"/traces/{state.run_id}",
                "diff": f"/plans/{plan.plan_id}/diff/v{plan.version-1}/v{plan.version}" if plan.version > 0 else "",
                "artifact_preview": f"/artifacts/{state.run_id}/{step.id}"
            }
        )
    
    def _emit_checkpoint(
        self,
        step: ActionContract,
        observation: Observation,
        state: RunState
    ) -> Checkpoint:
        """
        Emit checkpoint for retrospective validation.
        
        Args:
            step: Action contract
            observation: Execution observation
            state: Current run state
            
        Returns:
            Checkpoint with provenance
        """
        # Compute artifact hash
        artifact_hash = compute_artifact_hash(observation.artifacts)
        
        # Create artifact ID
        artifact_id = create_artifact_id(
            step.id,
            "output",
            artifact_hash
        )
        
        # Create provenance
        provenance = Provenance(
            artifact_id=artifact_id,
            from_step=step.id,
            inputs=[],  # Would extract from step inputs
            tool={
                "name": step.agent_or_tool,
                "version": "1.0",  # Would extract actual version
                "provider": "langswarm"
            },
            params_hash=compute_artifact_hash(step.inputs),
            metrics=observation.metrics
        )
        
        # Create checkpoint
        checkpoint = Checkpoint(
            step_id=step.id,
            artifact_uri=f"memory://{state.run_id}/{step.id}",  # In-memory for now
            artifact_hash=artifact_hash,
            provenance=provenance,
            validated=observation.is_success()
        )
        
        # Add to lineage
        self.lineage.add_checkpoint(checkpoint)
        
        logger.debug(f"Emitted checkpoint for step '{step.id}': {artifact_id}")
        
        return checkpoint
    
    async def _schedule_retrospects(
        self,
        step: ActionContract,
        checkpoint: Checkpoint
    ) -> None:
        """
        Schedule retrospective validation jobs.
        
        Args:
            step: Action contract with retrospects
            checkpoint: Checkpoint with artifact
        """
        for retro_def in step.retrospects:
            retro_job = RetrospectJob(
                retro_id=retro_def.get("id", f"retro-{step.id}-{uuid.uuid4().hex[:8]}"),
                target_artifact=checkpoint.provenance.artifact_id,
                checks=retro_def.get("checks", []),
                async_execution=retro_def.get("async", True),
                on_fail=retro_def.get("on_fail", {})
            )
            
            # Schedule with runner
            await self.retrospect_runner.schedule(
                retro_job,
                artifact=checkpoint.provenance.metrics  # Pass artifact data
            )
            
            logger.info(
                f"Scheduled retrospect '{retro_job.retro_id}' "
                f"for step '{step.id}'"
            )
    
    def _check_promotion_gates(
        self,
        step: ActionContract
    ) -> tuple[bool, Optional[str]]:
        """
        Check if promotion gates are satisfied.
        
        Promotion gates require retrospects to be green before proceeding.
        
        Args:
            step: Action contract
            
        Returns:
            Tuple of (can_proceed, reason_if_not)
        """
        # Check if step requires retro green
        required_retros = step.metadata.get("requires_retro_green", [])
        
        if not required_retros:
            return True, None
        
        # Check each required retrospect
        for retro_id in required_retros:
            if not self.retrospect_runner.is_complete(retro_id):
                return False, f"Retrospect '{retro_id}' not yet complete"
            
            if not self.retrospect_runner.is_green(retro_id):
                status = self.retrospect_runner.get_status(retro_id)
                return False, f"Retrospect '{retro_id}' not green: {status}"
        
        return True, None


