# Planning Examples

This section provides comprehensive examples of the **Hierarchical Planning System** in action. These examples demonstrate adaptive replanning, policy-driven decisions, retrospective validation, and complex lineage tracking.

The source code for these examples is available in the `examples/planning/` directory of the repository.

## 1. Simple Sequential Execution
**File:** `examples/planning/01_simple_sequential.py`

Demonstrates the basic loop: `Brainstorm → Verify → Plan → Execute`.

- **Goal**: Research AI agents and write a summary.
- **Key Concepts**:
    - `TaskBrief` definition.
    - `Coordinator` initialization.
    - Basic assertions and constraints.

```python
# Key snippet from 01_simple_sequential.py
brief = TaskBrief(
    objective="Research AI agents and write a summary article",
    inputs={
        "topic": "AI agents and multi-agent systems",
        "target_length": "500 words"
    },
    required_outputs={
        "article": "markdown document",
        "sources": "list of references"
    },
    metrics=["cost_usd", "latency_sec"]
)
```

## 2. Retrospective Validation
**File:** `examples/planning/02_with_retrospects.py` and `03_with_gates_and_retrospects.py`

Demonstrates how to run fast execution with deep, asynchronous validation in the background.

- **Fast Path**: Inline validators run immediately.
- **Slow Path**: Async "retrospects" run in the background.
- **Auto-Rollback**: If a retrospect fails, the system invalidates the affected steps and replays them.

## 3. Complex Lineage & Diamond Patterns
**File:** `examples/planning/06_advanced_lineage.py`

A sophisticated example showing parallel execution branches that merge (Diamond DAG) and how lineage tracking handles failures.

- **Scenario**: Multi-source data analysis (Load A, B, C -> Process -> Join -> Analyze).
- **Feature**: **Selective Invalidation**. If `Process A` fails a retrospective check:
    - `Process A` and its dependents (`Join`, `Analyze`) are invalidated.
    - `Process B` and `Process C` are **cached** and untouched.
    - The system replays only the affected path.

```python
# Define a retrospect that might trigger a rollback
process_a = ActionContract(
    id="process_a",
    # ...
    retrospects=[{
        "id": "deep_customer_validation",
        "async": True,
        "on_fail": {
            "invalidate_downstream": True,
            "replay_from": "process_a",
            "patch": {
                "ops": [{"op": "param_update", "target": "process_a", "params": {"strict": True}}]
            }
        }
    }]
)
```

## 4. Full Expense Processing Workflow
**File:** `examples/planning/04_expense_summary_complete.py`

A complete end-to-end business workflow matching a formal specification.

- **Stages**: Ingest → Normalize → Reconcile → Aggregate → Publish.
- **Gates**: "Promotion Gates" block publication until all retrospective checks pass.
- **SLA**: Enforces strict budget and latency constraints.

## How to Run
You can run any of these examples directly from the repository root:

```bash
# Run the simple example
python examples/planning/01_simple_sequential.py

# Run the advanced lineage example
python examples/planning/06_advanced_lineage.py
```
