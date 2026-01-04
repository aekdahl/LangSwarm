# 🧠 Hierarchical Planning System

LangSwarm provides a sophisticated, standalone planning system for complex, multi-step autonomous tasks. It features adaptive replanning, policy-driven decision making, and human-in-the-loop escalation.

> [!NOTE]
> This is an **Advanced API** (`langswarm.core.planning`). It operates independently of standard `AgentBuilder` workflows but wraps your existing agents and tools.

## 🚀 Quick Start

The planning system is orchestrated by the `Coordinator`. You give it a `TaskBrief` and a set of agents/tools, and it manages the execution loop (Brainstorm → Verify → Plan → Execute → Sense → Act).

```python
import asyncio
from langswarm.core.planning import Coordinator, TaskBrief, DEFAULT_POLICIES
from langswarm.core.agents import create_openai_agent

async def main():
    # 1. Create a "Brain" for the planner
    planner_llm = create_openai_agent(name="planner", model="gpt-4o")

    # 2. Define the Task
    brief = TaskBrief(
        objective="Analyze Q1 expense reports and generate a summary",
        inputs={"data": "s3://expenses/2024/q1/*.csv"},
        required_outputs={"report": "markdown"},
        constraints={"cost_usd": 5.0} # Optional budget
    )

    # 3. Initialize Coordinator (automatically discovers agents/tools if not provided explicitly)
    coordinator = Coordinator(config={
        "llm": planner_llm,
        "policies": DEFAULT_POLICIES, # Configurable thresholds for retries/escalation
    })

    # 4. Execute
    print("🤖 Starting autonomous execution...")
    result = await coordinator.execute_task(brief)

    print(f"Status: {result.status}")
    print(f"Final Plan Version: v{result.plan.version}")

asyncio.run(main())
```

## 🧩 Core Architecture

The system is built on a "Sense-Think-Act" loop enhanced with hierarchical planning:

1.  **Planner**: Generates and evolves the plan (DAG of `ActionContract`s).
2.  **Executor**: Executes individual steps using standard LangSwarm agents or tools.
3.  **Controller**: monitoring the state and deciding the next move (Continue, Retry, Replan, or Escalate).
4.  **Verifier**: Runs acceptance tests and gates.

### The Execution Loop

When you call `execution_task`, the Coordinator follows this rigorous process:

1.  **Brainstorm**: Generates multiple potential approaches.
2.  **Verify Capabilities**: Checks if required tools/agents exist *before* starting.
3.  **Generate Plan**: Creates the initial execution graph.
4.  **Execute & Observe**: Runs steps and captures standardized `Observation`s.
5.  **Adaptive Control**: If a step fails, the Controller decides whether to retry, patch the plan, or ask for human help.

## 🔑 Key Concepts

### Task Brief
The contract between you and the planner.

```python
TaskBrief(
    objective="Migrate database schema",
    inputs={"source": "postgres_prod", "target": "postgres_v2"},
    constraints={"latency_sec": 600},
    acceptance_tests=["check_row_counts_match"]
)
```

### Escalation (Human-in-the-Loop)
If the system hits a critical issue or budget limit, it can "escalate" to a human operator instead of failing silently.

```python
# Defined in policies
"escalation_triggers": {
    "budget_overrun": Severity.S2,    # Pause and ask
    "integrity_check_failed": Severity.S1 # Critical stop
}
```

## 🔍 Retrospective Validation

For critical tasks where "it looks okay" isn't enough, you can enable **Retrospective Validation**. This runs deep, asynchronous checks *after* a step completes, without blocking the main execution.

If a retrospect fails later, the Coordinator automatically:
1.  **Invalidates** the step and all downstream artifacts.
2.  **Rolls back** to the last valid checkpoint.
3.  **Compensates** for side effects (if defined).
4.  **Replays** the plan from the safe point.

```python
# Enable in Coordinator
coordinator = Coordinator(config={
    "llm": planner_llm,
    "enable_retrospects": True
})

# Define in TaskBrief steps
ActionContract(
    id="ingest_data",
    intent="Load massive CSV",
    # ...
    retrospects=[{
        "id": "deep_integrity_check",
        "async": True, # Run in background
        "checks": [
            "schema_strict(output)", 
            "no_duplicates(output, col='id')"
        ],
        "on_fail": {
            "invalidate_downstream": True,
            "replay_from": "ingest_data"
        }
    }]
)
```

## 🛡️ Safety & Policies

The behavior of the planner is governed by `PolicyConfig`. You can tune these to be aggressive (fast, risky) or conservative (careful, rigorous).

```python
from langswarm.core.planning import PolicyConfig

policies = PolicyConfig(
    max_retries=3,
    max_replans=2, # How many times can it rewrite the plan?
    confidence_threshold=0.8
)
```
