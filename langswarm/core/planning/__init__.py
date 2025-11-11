"""
LangSwarm Hierarchical Planning System

A sophisticated planning and execution system with reactive control, adaptive replanning,
and policy-driven escalation for complex multi-agent workflows.

Key Components:
- TaskBrief: Define objectives, inputs, outputs, tests, and constraints
- Plan: Versioned DAG of action contracts with dependencies
- Coordinator: Main control loop with brainstorm → verify → plan → execute → sense → act/replan
- Controller: Policy-driven decisions (continue/retry/alternate/replan/escalate)
- Escalation: S1-S4 severity-based routing with human-in-the-loop
- Patcher: Plan versioning and auditable diffs

Usage:
    from langswarm.core.planning import Coordinator, TaskBrief
    
    # Define task
    brief = TaskBrief(
        objective="Process expense reports",
        inputs={"data_source": "gs://..."},
        required_outputs={"report": "parquet"},
        acceptance_tests=[...],
        constraints={"cost_usd": 5.0, "latency_sec": 120}
    )
    
    # Create coordinator with existing LangSwarm components
    coordinator = Coordinator(config={
        "llm": llm_provider,
        "agents": agent_registry,
        "tools": tool_registry,
        "policies": DEFAULT_POLICIES,
        "escalation": escalation_config
    })
    
    # Execute with adaptive replanning
    result = await coordinator.execute_task(brief)
"""

from .models import (
    TaskBrief,
    ActionContract,
    Plan,
    PlanPatch,
    Observation,
    RunState,
    Decision,
    BrainstormResult,
    CapabilityVerification,
    EscalationPayload,
    # Retrospective validation models
    Provenance,
    Checkpoint,
    RetrospectJob,
    RetrospectStatus,
    InvalidationTicket
)

from .policies import DEFAULT_POLICIES, PolicyConfig

from .coordinator import Coordinator

from .planner import Planner

from .executor import Executor

from .controller import Controller

from .verifier import Verifier

from .contracts import ContractValidator

from .patcher import PlanPatcher

from .escalation import EscalationRouter

from .schema import PlanningYAMLParser, PLANNING_SCHEMA

# Retrospective validation components
from .lineage import LineageGraph, compute_artifact_hash, create_artifact_id

from .retrospect import RetrospectRunner

from .replay import ReplayManager

__all__ = [
    # Core data models
    "TaskBrief",
    "ActionContract",
    "Plan",
    "PlanPatch",
    "Observation",
    "RunState",
    "Decision",
    "BrainstormResult",
    "CapabilityVerification",
    "EscalationPayload",
    
    # Retrospective validation models
    "Provenance",
    "Checkpoint",
    "RetrospectJob",
    "RetrospectStatus",
    "InvalidationTicket",
    
    # Main components
    "Coordinator",
    "Planner",
    "Executor",
    "Controller",
    "Verifier",
    "ContractValidator",
    "PlanPatcher",
    "EscalationRouter",
    
    # Retrospective validation components
    "LineageGraph",
    "RetrospectRunner",
    "ReplayManager",
    "compute_artifact_hash",
    "create_artifact_id",
    
    # Configuration
    "DEFAULT_POLICIES",
    "PolicyConfig",
    
    # Schema and parsing
    "PlanningYAMLParser",
    "PLANNING_SCHEMA",
]

__version__ = "1.0.0"


