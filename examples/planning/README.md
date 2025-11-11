# Hierarchical Planning System Examples

This directory contains examples demonstrating the LangSwarm hierarchical planning system with adaptive replanning, policy-driven decisions, retrospective validation, and human-in-the-loop escalation.

## Quick Start Example

```python
import asyncio
from langswarm.core.planning import Coordinator, TaskBrief
from langswarm.core.agents import create_openai_agent
from langswarm.core.planning import DEFAULT_POLICIES

async def main():
    # Create LLM for planning
    planner_llm = create_openai_agent(
        name="planner",
        model="gpt-4",
        system_prompt="You are a planning assistant."
    )
    
    # Define task
    brief = TaskBrief(
        objective="Analyze expense data and generate summary report",
        inputs={"data_source": "gs://expenses/q4/*.csv"},
        required_outputs={"summary": "parquet", "errors": "json"},
        acceptance_tests=[
            {"name": "has_data", "type": "assertion", "assertion": "len(output) > 0"}
        ],
        constraints={"cost_usd": 5.0, "latency_sec": 300}
    )
    
    # Create coordinator
    coordinator = Coordinator(config={
        "llm": planner_llm,
        "policies": DEFAULT_POLICIES,
        "escalation": {
            "slack_webhook": "https://hooks.slack.com/...",
            "oncall_team": "finance-ops"
        }
    })
    
    # Execute with adaptive planning
    result = await coordinator.execute_task(brief)
    
    print(f"Status: {result.status}")
    print(f"Steps completed: {len(result.artifacts)}")
    print(f"Cost: ${result.metrics.get('cost_usd', 0):.2f}")
    print(f"Final plan version: v{result.plan.version}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example Files

### 01_simple_sequential.py
Basic sequential plan execution with gates and fallbacks.

**Demonstrates:**
- Creating a TaskBrief
- Defining ActionContracts with inputs/outputs
- Preconditions and postconditions
- Validators and gates
- Fallback strategies (retry, alternate)
- Sequential DAG execution

**Run:**
```bash
python examples/planning/01_simple_sequential.py
```

### 02_with_retrospects.py
Comprehensive retrospective validation example.

**Demonstrates:**
- Fast inline validation
- Async retrospective checks
- Lineage tracking
- Checkpoint emission
- Invalidation and replay
- Promotion gates
- Compensation actions

**Run:**
```bash
python examples/planning/02_with_retrospects.py
```

### 03_with_gates_and_retrospects.py
Combined gates and retrospective validation.

**Demonstrates:**
- Precondition/postcondition gates
- Async retrospective validation
- Promotion gates requiring retrospects
- Both gate failures and retrospect failures
- Security-critical validation (PII detection)
- Business rule validation
- Strict vs lenient validation

**Run:**
```bash
python examples/planning/03_with_gates_and_retrospects.py
```

### 04_expense_summary_complete.py
Full expense processing workflow (from specification).

**Demonstrates:**
- Multi-step pipeline: Ingest → Normalize → Reconcile → Aggregate → Publish
- Retrospects on normalize (schema strict, dedupe, consistency)
- Promotion gate on publish (requires retro green)
- Auto-rollback and replay with alternate on retrospect failure
- Budget and SLA enforcement
- Reconciliation with external data sources
- Staging to production promotion pattern

**Run:**
```bash
python examples/planning/04_expense_summary_complete.py
```

### 05_data_pipeline_with_compensation.py
ETL pipeline with side effects and compensation.

**Demonstrates:**
- Extract-Transform-Load workflow
- Side effects (database writes)
- Saga-style compensating actions
- Rollback on retrospect failure
- Multi-warehouse validation
- Staging → production promotion
- Clean rollback story

**Run:**
```bash
python examples/planning/05_data_pipeline_with_compensation.py
```

### 06_advanced_lineage.py
Complex dependencies with lineage tracking.

**Demonstrates:**
- Parallel branches (diamond DAG pattern)
- Content-addressed artifacts
- Lineage graph visualization
- Impact analysis for failures
- Selective invalidation (only affected branches)
- Partial replay (cache unaffected branches)
- Efficient error recovery

**Run:**
```bash
python examples/planning/06_advanced_lineage.py
```

## What Makes This Different?

### 1. Brainstorm Before Planning
Before generating a plan, the system explores possible approaches:
- What actions are needed?
- What are alternative sequences?
- Are there multiple valid approaches?

### 2. Early Capability Verification
Checks if required agents/tools exist BEFORE execution:
- Prevents mid-execution failures
- Escalates early if capabilities missing
- Suggests workarounds when possible

### 3. Retrospective Validation
Execute fast with lightweight checks, validate thoroughly later:
- **Fast path**: Inline validators for low latency
- **Slow path**: Async retrospects for correctness
- **Speculative continuation**: Proceed while retrospects run
- **Auto-rollback**: Invalidate + replay on retrospect failure
- **Promotion gates**: Block critical steps until retrospects green

### 4. Adaptive Replanning
When things go wrong, the system:
- Tries local recovery first (retry/alternate)
- Generates minimal patches to fix issues
- Maintains version history of all changes
- Learns from failures

### 5. Policy-Driven Decisions
Every decision follows a clear policy tree:
- Policy violations → Escalate S1 (halt)
- Success → Continue
- Transient error → Retry
- Better alternative available → Alternate
- Budget overrun → Escalate S2 (alert)
- Low confidence → Replan
- Unknown failure → Replan

### 6. Lineage & Compensation
Track artifact dependencies and enable clean rollback:
- **Checkpoints**: Immutable artifact snapshots
- **Provenance**: Track artifact dependencies
- **Impact Analysis**: Identify affected downstream artifacts
- **Compensation**: Undo side effects on rollback
- **Selective Replay**: Only replay affected branches

### 7. Human-in-the-Loop
Escalation happens at appropriate severity:
- **S1 (Critical)**: Halt, page on-call (policy violations, destructive ops)
- **S2 (High)**: Alert immediately, can replan once (budget overrun, SLA breach)
- **S3 (Medium)**: Notify async, continue (low confidence, drift)
- **S4 (Low)**: Log for digest (minor issues, successful recovery)

## Key Concepts

### TaskBrief
Defines WHAT needs to be done:
```python
TaskBrief(
    objective="Process expense reports",
    inputs={"source": "..."},
    required_outputs={"report": "..."},
    acceptance_tests=[...],
    constraints={"cost_usd": 5.0, "latency_sec": 300}
)
```

### ActionContract
Defines HOW a step should execute:
- Inputs/outputs with schemas
- Preconditions/postconditions
- Validators
- Cost/latency budgets
- Fallback strategies
- Escalation policies
- **Retrospects** (async validation)
- **Compensation** (rollback actions)

### Plan
Versioned DAG of action contracts:
- Steps with dependencies
- Evolves through patches
- Auditable history

### Observation
Standardized result from execution:
- Status (ok/soft_fail/hard_fail)
- Artifacts produced
- Metrics (cost, latency, tokens)
- Quality measures
- Policy violations

### Decision
Controller's next action:
- continue, retry, alternate, replan, or escalate
- With clear reasoning
- Optional patch or next step

### Checkpoint
Immutable artifact snapshot:
- Content hash for identity
- Provenance (inputs + tool versions)
- Timestamp
- Used for lineage tracking

### RetrospectJob
Async validation task:
- Runs heavy checks in background
- Status: pending/ok/fail
- Can invalidate downstream artifacts
- Triggers replay on failure

## Architecture Benefits

✅ **Low Latency + High Quality**: Fast inline checks + thorough async retrospects  
✅ **Deterministic**: Explicit contracts and policies  
✅ **Adaptive**: Automatic retry, alternate, replan based on observations  
✅ **Auditable**: Versioned plans, decision ledger, lineage tracking  
✅ **Safe**: Budget/SLA guardrails, compensation, escalation hooks  
✅ **Efficient**: Selective invalidation, partial replay, artifact caching

## Integration with LangSwarm

The planning system integrates seamlessly with existing LangSwarm:

- **Uses existing agents** (OpenAI, Anthropic, etc.)
- **Uses existing tools** (all MCP tools)
- **Uses existing observability** (tracing, metrics)
- **Uses existing error handling**
- **Uses existing memory** (for context)

No need to rebuild anything—it orchestrates what you already have!

## Next Steps

1. Try the simple examples (01, 02)
2. Explore retrospective validation (02, 03)
3. Study the complete expense workflow (04)
4. Learn compensation patterns (05)
5. Understand lineage tracking (06)
6. Define your own TaskBrief
7. Run with adaptive planning
8. Observe replanning and retrospects in action
9. Configure escalation for your team
