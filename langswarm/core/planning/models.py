"""
Core Data Models for Hierarchical Planning System

Defines all foundational data structures for task briefs, plans, observations,
decisions, and state management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal, Callable
from enum import Enum
import uuid


class ObservationStatus(Enum):
    """Status of a step execution observation"""
    OK = "ok"
    SOFT_FAIL = "soft_fail"
    HARD_FAIL = "hard_fail"


class DecisionAction(Enum):
    """Possible controller decisions"""
    CONTINUE = "continue"
    RETRY = "retry"
    ALTERNATE = "alternate"
    REPLAN = "replan"
    ESCALATE = "escalate"


class Severity(Enum):
    """Escalation severity levels"""
    S1 = "S1"  # Critical - halt execution, page on-call
    S2 = "S2"  # High - alert immediately, can replan once
    S3 = "S3"  # Medium - notify async, continue with replan
    S4 = "S4"  # Low - log for daily digest


@dataclass
class TaskBrief:
    """
    High-level description of a task to be planned and executed.
    
    The TaskBrief defines WHAT needs to be done, but not HOW. The planner
    will determine the HOW by brainstorming actions, verifying capabilities,
    and generating a concrete plan.
    
    Attributes:
        objective: Clear description of what needs to be accomplished
        inputs: Input data/parameters required (name -> spec)
        required_outputs: Expected outputs (name -> spec)
        acceptance_tests: List of tests that must pass for success
        constraints: Budget/latency/policy constraints
        metadata: Additional context (owner, oncall, tags, etc.)
    """
    objective: str
    inputs: Dict[str, Any]
    required_outputs: Dict[str, Any]
    acceptance_tests: List[Dict[str, Any]]
    constraints: Dict[str, Any]  # cost_usd, latency_sec, privacy, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.objective:
            raise ValueError("TaskBrief requires an objective")
        if "cost_usd" not in self.constraints:
            self.constraints["cost_usd"] = float('inf')
        if "latency_sec" not in self.constraints:
            self.constraints["latency_sec"] = float('inf')


@dataclass
class ActionContract:
    """
    Crisp contract for a single action/step with clear I/O expectations.
    
    Every step in a plan has an ActionContract that defines:
    - What inputs are required and their schemas
    - What outputs are expected and their schemas
    - Preconditions that must be true before execution
    - Postconditions that must be true after execution
    - Validators to check output quality
    - Cost/latency budgets
    - Fallback strategies
    - Escalation policies
    - Retrospective validation (async heavy validation)
    - Compensation for rollback
    
    This enables deterministic verification and policy-driven decisions.
    """
    id: str
    intent: str  # Human-readable description
    agent_or_tool: str  # Agent/tool to use
    inputs: Dict[str, Any]  # Input schema with type, required, format
    outputs: Dict[str, Any]  # Output schema with type, minItems, etc.
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    validators: List[Dict[str, Any]] = field(default_factory=list)
    cost_estimate: Dict[str, Any] = field(default_factory=dict)
    latency_budget_sec: float = 30.0
    confidence_floor: float = 0.8
    side_effects: List[str] = field(default_factory=list)
    fallbacks: List[Dict[str, Any]] = field(default_factory=list)
    escalation: Dict[str, Any] = field(default_factory=dict)
    gates: List[Dict[str, Any]] = field(default_factory=list)
    retrospects: List[Dict[str, Any]] = field(default_factory=list)  # Async validation
    compensation: Optional[Dict[str, Any]] = None  # Rollback actions
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults for cost_estimate"""
        if not self.cost_estimate:
            self.cost_estimate = {
                "usd": 0.0,
                "tokens_in": 0,
                "tokens_out": 0
            }


@dataclass
class Plan:
    """
    Versioned execution plan as a DAG of action contracts.
    
    Plans are generated from TaskBriefs and evolve through PlanPatches.
    Each version is tracked with auditable diffs.
    
    Attributes:
        plan_id: Unique identifier
        version: Incremental version number (starts at 0)
        task_brief: Original task definition
        steps: List of action contracts
        dag: Dependencies between steps (step_id -> [dependency_ids])
        metadata: Owner, oncall, budget, SLA, etc.
        created_at: When plan was first created
        updated_at: When plan was last modified
    """
    plan_id: str
    version: int
    task_brief: TaskBrief
    steps: List[ActionContract]
    dag: Dict[str, List[str]]  # step_id -> [dependency step_ids]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_step(self, step_id: str) -> Optional[ActionContract]:
        """Get step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_topological_order(self) -> List[ActionContract]:
        """Return steps in topological order respecting dependencies"""
        # Kahn's algorithm
        in_degree = {step.id: 0 for step in self.steps}
        for deps in self.dag.values():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0) + 1
        
        queue = [step.id for step in self.steps if in_degree[step.id] == 0]
        result = []
        
        while queue:
            step_id = queue.pop(0)
            step = self.get_step(step_id)
            if step:
                result.append(step)
            
            for dependent in self.dag.get(step_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result


@dataclass
class PlanPatch:
    """
    Auditable change to a plan with versioning.
    
    Patches are small, targeted modifications to plans in response to
    failures, drift, or changing conditions. All patches are logged
    for auditability and learning.
    
    Operations:
    - replace: Replace entire step
    - add_after: Insert new step after target
    - remove: Remove step
    - reorder: Change dependency structure
    - param_update: Update step parameters
    """
    patch_id: str
    plan_id: str
    from_version: int
    to_version: int
    reason: str
    ops: List[Dict[str, Any]]  # List of operations
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied_by: str = "coordinator"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """
    Standardized result from executing an action.
    
    Every step execution returns an Observation that includes:
    - Status (ok/soft_fail/hard_fail)
    - Artifacts produced
    - Metrics (cost, latency, tokens)
    - Quality measures (confidence, error rate)
    - Policy violations
    - Trace information
    
    This standard format enables deterministic controller decisions.
    """
    action_id: str
    status: ObservationStatus
    artifacts: Dict[str, Any]
    metrics: Dict[str, Any]  # tokens_in, tokens_out, cost_usd, latency_ms
    quality: Dict[str, Any]  # confidence, error_rate, tests
    policy: Dict[str, Any]  # violations list
    notes: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_success(self) -> bool:
        """Check if observation indicates success"""
        return self.status == ObservationStatus.OK and not self.policy.get("violations", [])


@dataclass
class RunState:
    """
    Current state of plan execution.
    
    Tracks all runtime information needed for decision-making:
    - Which step we're on (cursor)
    - Artifacts produced so far
    - Cumulative metrics (cost, latency, tokens)
    - Test results
    - Drift metrics
    - Remaining budget
    - Execution status
    """
    run_id: str
    plan: Plan
    cursor: int  # Current step index
    artifacts: Dict[str, Any]  # step_id -> artifacts
    metrics: Dict[str, Any]  # Cumulative cost, latency, tokens
    test_results: Dict[str, Any]  # test_name -> result
    drift_metrics: Dict[str, Any]  # Various drift measures
    budget_left: Dict[str, float]  # usd, tokens, time_sec
    status: str = "running"  # running, completed, halted, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_from_observation(self, obs: Observation) -> None:
        """Update state with observation data"""
        # Update artifacts
        self.artifacts[obs.action_id] = obs.artifacts
        
        # Update cumulative metrics
        self.metrics["cost_usd"] = self.metrics.get("cost_usd", 0.0) + obs.metrics.get("cost_usd", 0.0)
        self.metrics["latency_ms"] = self.metrics.get("latency_ms", 0) + obs.metrics.get("latency_ms", 0)
        self.metrics["tokens_in"] = self.metrics.get("tokens_in", 0) + obs.metrics.get("tokens_in", 0)
        self.metrics["tokens_out"] = self.metrics.get("tokens_out", 0) + obs.metrics.get("tokens_out", 0)
        
        # Update budget left
        self.budget_left["usd"] = self.budget_left.get("usd", float('inf')) - obs.metrics.get("cost_usd", 0.0)
        self.budget_left["time_sec"] = self.budget_left.get("time_sec", float('inf')) - (obs.metrics.get("latency_ms", 0) / 1000)
        
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class Decision:
    """
    Controller decision about how to proceed.
    
    After each step execution, the controller decides:
    - continue: Postconditions met, move to next step
    - retry: Transient failure, try again
    - alternate: Use fallback agent/tool
    - replan: Need to modify the plan
    - escalate: Human intervention required
    """
    action: DecisionAction
    reason: str
    patch: Optional[PlanPatch] = None
    next_step: Optional[ActionContract] = None
    param_overrides: Optional[Dict[str, Any]] = None
    severity: Optional[Severity] = None  # For escalate action
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BrainstormResult:
    """
    Result of brainstorming potential actions for a task.
    
    Before generating a concrete plan, the planner explores possible
    approaches and sequences of actions.
    """
    suggested_actions: List[Dict[str, Any]]  # Action ideas with descriptions
    reasoning: str
    alternatives: List[Dict[str, Any]]  # Alternative approaches
    estimated_steps: int
    estimated_cost_usd: float = 0.0
    estimated_latency_sec: float = 0.0
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityVerification:
    """
    Result of verifying we have tools/agents to execute brainstormed actions.
    
    Before committing to a plan, verify that all required capabilities exist.
    If not, escalate early rather than failing mid-execution.
    """
    verified: bool
    available_capabilities: Dict[str, List[str]]  # capability_type -> [names]
    missing_capabilities: List[str]
    suggested_workarounds: List[str]
    escalation_required: bool
    verification_details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationPayload:
    """
    Complete context for human escalation.
    
    When the system needs human intervention, provide all necessary
    context for quick decision-making.
    """
    plan_id: str
    severity: Severity
    trigger: str
    step: str
    observation: Dict[str, Any]
    last_actions: List[Dict[str, Any]]
    proposed_fix: Optional[str]
    next_safe_actions: List[str]
    links: Dict[str, str]  # trace, diff, artifact_preview
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Retrospective Validation Models
# ============================================================================


@dataclass
class Provenance:
    """
    Artifact lineage and provenance tracking.
    
    Records the complete history of how an artifact was produced:
    inputs, tool versions, parameters, and metrics.
    
    This enables:
    - Impact analysis for rollback
    - Reproducibility
    - Audit trails
    - Debugging
    """
    artifact_id: str  # e.g., "normalize/records@sha256:abc123..."
    from_step: str
    inputs: List[str]  # Parent artifact IDs
    tool: Dict[str, str]  # name, version, provider
    params_hash: str  # Hash of parameters used
    metrics: Dict[str, Any]  # cost, latency, tokens, confidence
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Checkpoint:
    """
    Immutable checkpoint of step execution with artifacts and provenance.
    
    Checkpoints enable:
    - Replay from any point
    - Retroactive validation
    - Lineage tracking
    - Artifact versioning
    """
    step_id: str
    artifact_uri: str  # Where artifact is stored
    artifact_hash: str  # Content hash (SHA-256)
    provenance: Provenance
    validated: bool = False  # Inline validation passed
    retro_status: Dict[str, str] = field(default_factory=dict)  # retro_id -> status
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_retro_green(self, retro_id: str) -> bool:
        """Check if specific retrospect is green"""
        return self.retro_status.get(retro_id) == "ok"
    
    def all_retro_green(self) -> bool:
        """Check if all retrospects are green"""
        return all(status == "ok" for status in self.retro_status.values())


class RetrospectStatus(Enum):
    """Status of retrospective validation job"""
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    FAIL = "fail"
    TIMEOUT = "timeout"


@dataclass
class RetrospectJob:
    """
    Asynchronous retrospective validation job.
    
    Retrospects run heavy validation in the background while
    execution continues speculatively. If retrospect fails,
    downstream artifacts are invalidated and replayed.
    """
    retro_id: str
    target_artifact: str  # Artifact ID to validate
    checks: List[str]  # Check names to run
    async_execution: bool = True
    status: RetrospectStatus = RetrospectStatus.PENDING
    reason: Optional[str] = None
    on_fail: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Check if retrospect has completed"""
        return self.status in [RetrospectStatus.OK, RetrospectStatus.FAIL, RetrospectStatus.TIMEOUT]
    
    def is_green(self) -> bool:
        """Check if retrospect passed"""
        return self.status == RetrospectStatus.OK


@dataclass
class InvalidationTicket:
    """
    Rollback instructions when retrospect fails.
    
    Describes:
    - What artifacts are invalid
    - What downstream artifacts are affected
    - Whether to replay or cancel
    - Optional plan patch to fix the issue
    """
    ticket_id: str
    trigger: str  # What caused invalidation
    root_artifact: str  # The artifact that failed validation
    downstream: List[str]  # All affected downstream artifacts
    action: Literal["replay", "cancel"]
    proposed_plan_patch: Optional[PlanPatch] = None
    compensation_actions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

