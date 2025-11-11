"""
Example 04: Complete Expense Summary Workflow with Retrospects

This is the full example from the planning specification.

Demonstrates:
- Multi-step expense processing pipeline
- Normalize → Reconcile → Aggregate → Publish
- Retrospective validation on normalize (schema strict, dedupe, consistency)
- Promotion gate on publish (requires retro green)
- Auto-rollback and replay with alternate on retrospect failure
"""

import asyncio
from datetime import datetime, timezone
from langswarm.core.planning import (
    TaskBrief,
    ActionContract,
    Plan,
    Coordinator,
    RunState
)


async def main():
    print("=" * 80)
    print("Example 04: Complete Expense Summary Workflow")
    print("=" * 80)
    
    # Define task brief
    task_brief = TaskBrief(
        objective="Generate weekly expense summary report for Q4 2025",
        inputs={
            "data_source": "gs://expenses/q4/*.csv",
            "schema_version": "v3.2",
            "time_window": "2025-10-01..2025-10-07"
        },
        required_outputs={
            "summary_report": "parquet",
            "reconciliation_report": "json"
        },
        acceptance_tests=[
            {"name": "row_count", "assertion": "output.count > 0"},
            {"name": "reconciliation", "assertion": "abs(output.delta_pct) <= 0.5"},
            {"name": "schema", "assertion": "schema_ok(output, 'claim_v3_2')"}
        ],
        constraints={
            "cost_usd": 3.0,
            "latency_sec": 120,
            "privacy": "financial_data",
            "security_level": "confidential"
        },
        metadata={
            "owner": "@finance-team",
            "oncall": "finance-ops",
            "department": "finance",
            "project": "expense_automation"
        }
    )
    
    # Step 1: Ingest raw expense data
    ingest = ActionContract(
        id="ingest",
        intent="Load raw expense claims from GCS",
        agent_or_tool="gcs_reader",
        inputs={
            "path": "gs://expenses/q4/*.csv",
            "format": "csv"
        },
        outputs={
            "raw_data": "dataframe",
            "record_count": "int"
        },
        preconditions=[
            "gcs_bucket_accessible('expenses')",
            "files_exist('gs://expenses/q4/*.csv')"
        ],
        postconditions=[
            "output.record_count > 0",
            "output.raw_data.columns.contains('date', 'amount', 'employee_id')"
        ],
        cost_estimate={"usd": 0.05, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=10.0
    )
    
    # Step 2: Normalize expense data with retrospective validation
    normalize = ActionContract(
        id="normalize",
        intent="Normalize raw expense claims to v3.2 schema",
        agent_or_tool="transformer",
        inputs={
            "spec": "schemas/claim_v3_2.yaml",
            "data": "{{ ingest.raw_data }}"
        },
        outputs={
            "records": "dataframe",
            "error_rate": "float"
        },
        preconditions=[
            "file_exists('schemas/claim_v3_2.yaml')",
            "schema_compatible(inputs.data, 'claim_v3_2_in')"
        ],
        postconditions=[
            "schema_ok(output.records, 'claim_v3_2')",
            "output.error_rate <= 0.02"  # Allow 2% error rate inline
        ],
        validators=[
            {"fn": "row_count_match", "args": {"tolerance": 0.02}},
            {"fn": "field_coverage", "args": {"required_fields": ["date", "amount", "tax", "category"]}}
        ],
        cost_estimate={"usd": 0.08, "tokens_in": 3000, "tokens_out": 500},
        latency_budget_sec=20.0,
        confidence_floor=0.8,
        
        fallbacks=[
            {"type": "retry", "max": 2, "backoff_sec": 5},
            {"type": "alternate", "agent": "transformer_alt", "params": {"strict": False}}
        ],
        
        # RETROSPECT: Strict validation (runs async after fast inline checks pass)
        retrospects=[
            {
                "id": "retro_normalize_v3_2_strict",
                "async": True,
                "checks": [
                    "schema_ok_strict(output.records, 'claim_v3_2')",  # Stricter schema check
                    "dedupe_exact(output.records, key=['employee_id', 'receipt_id'])",  # No duplicates
                    "amount_tax_consistency(output.records)"  # Business rule: amount >= tax
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "normalize",
                    "patch": {
                        "ops": [
                            {
                                "op": "alternate",
                                "target": "normalize",
                                "with": {
                                    "agent": "transformer_alt",
                                    "params": {"strict": True, "dedupe": True}
                                }
                            }
                        ]
                    },
                    "escalate": {
                        "severity": "S2",
                        "notify": ["ops#fin-data"],
                        "message": "Strict schema or reconciliation fail in normalize"
                    }
                }
            }
        ],
        
        escalation={
            "severity": "S3",
            "notify": ["ops#fin-data"],
            "on_violation": ["data_integrity", "budget_overrun"]
        }
    )
    
    # Step 3: Reconcile with external source
    reconcile = ActionContract(
        id="reconcile",
        intent="Reconcile normalized claims with Firestore summary",
        agent_or_tool="reconciler",
        inputs={
            "a": "{{ normalize.records }}",
            "b": "firestore:claims_summary?range={{ window }}"
        },
        outputs={
            "delta": "json",
            "delta_pct": "float"
        },
        postconditions=[
            "abs(output.delta.total_pct) <= 0.5"  # Allow 0.5% discrepancy
        ],
        cost_estimate={"usd": 0.10, "tokens_in": 4000, "tokens_out": 800},
        latency_budget_sec=25.0,
        
        fallbacks=[
            {"type": "retry", "max": 1},
            {
                "type": "alternate",
                "agent": "reconciler_alt",
                "params": {"strategy": "grouped_match", "tolerance": 0.3}
            }
        ],
        
        gates=[
            {
                "type": "postcondition",
                "assertion": "abs(output.delta.total_pct) <= 0.5",
                "on_fail": {
                    "decision": "replan",
                    "escalate": {
                        "if": "abs(output.delta.total_pct) > 1.0",
                        "severity": "S2",
                        "notify": ["ops#fin-data"],
                        "message": "Reconciliation drift {{ output.delta.total_pct }}% > 1.0%"
                    }
                }
            }
        ]
    )
    
    # Step 4: Aggregate summary statistics
    aggregate = ActionContract(
        id="aggregate",
        intent="Calculate summary statistics and totals",
        agent_or_tool="aggregator",
        inputs={
            "data": "{{ normalize.records }}",
            "delta": "{{ reconcile.delta }}"
        },
        outputs={
            "table": "dataframe",
            "summary": "json"
        },
        postconditions=[
            "output.summary.total_amount > 0",
            "output.table.shape[0] > 0"
        ],
        cost_estimate={"usd": 0.05, "tokens_in": 2000, "tokens_out": 300},
        latency_budget_sec=15.0
    )
    
    # Step 5: Publish to staging
    publish_staging = ActionContract(
        id="publish_staging",
        intent="Publish aggregated report to staging bucket",
        agent_or_tool="gcs_writer",
        inputs={
            "data": "{{ aggregate.table }}",
            "path": "gs://reports/staging/weekly/{{ window }}.parquet"
        },
        outputs={
            "uri": "string",
            "success": "bool"
        },
        side_effects=["write_to_gcs"],
        cost_estimate={"usd": 0.02, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=10.0
    )
    
    # Step 6: Promote to production (with retro green gate)
    publish_prod = ActionContract(
        id="publish_prod",
        intent="Promote report to production only if retrospect is green",
        agent_or_tool="promoter",
        inputs={
            "source": "gs://reports/staging/weekly/{{ window }}.parquet",
            "destination": "gs://reports/production/weekly/{{ window }}.parquet"
        },
        outputs={
            "uri": "string",
            "success": "bool"
        },
        side_effects=["write_to_prod_gcs", "send_notification"],
        
        # PROMOTION GATE: Don't publish to prod until retrospect is green
        gates=[
            {
                "type": "promotion",
                "assertion": "retro_green('retro_normalize_v3_2_strict')",
                "on_fail": {
                    "decision": "cancel",
                    "escalate": {
                        "severity": "S3",
                        "message": "Retrospect not green; promotion halted"
                    }
                }
            },
            {
                "type": "budget",
                "assertion": "budget_left_usd >= 0.20",
                "on_fail": {
                    "decision": "escalate",
                    "severity": "S2",
                    "notify": ["ops#fin-data"],
                    "message": "Budget nearly exhausted; publish would exceed cap"
                }
            }
        ],
        
        # Must wait for retrospect validation before promoting
        requires_retro_green=["retro_normalize_v3_2_strict"],
        
        cost_estimate={"usd": 0.02, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=10.0,
        
        escalation={
            "severity": "S2",
            "notify": ["ops#fin-data", "finance-team"],
            "on_violation": ["policy", "budget_overrun"]
        }
    )
    
    # Create plan
    plan = Plan(
        plan_id="weekly_expense_summary",
        version=0,
        task_brief=task_brief,
        steps=[ingest, normalize, reconcile, aggregate, publish_staging, publish_prod],
        dag={
            "ingest": [],
            "normalize": ["ingest"],
            "reconcile": ["normalize"],
            "aggregate": ["normalize", "reconcile"],
            "publish_staging": ["aggregate"],
            "publish_prod": ["publish_staging"]
        },
        metadata={
            "created": datetime.now(timezone.utc).isoformat(),
            "author": "finance-ops",
            "description": "Weekly expense summary with retrospective validation",
            "sla_sec": 120,
            "budget_usd": 3.0
        }
    )
    
    # Execute plan
    print("\n📋 Executing plan: weekly_expense_summary\n")
    
    coordinator = Coordinator()
    
    try:
        result = await coordinator.execute_task(plan)
        
        print("\n" + "=" * 80)
        print("✅ EXPENSE WORKFLOW COMPLETE")
        print("=" * 80)
        print(f"Plan Version: {result.plan.version}")
        print(f"Steps Executed: {len(result.steps_executed)}")
        print(f"Total Cost: ${result.metrics.get('total_cost_usd', 0):.4f}")
        print(f"Total Time: {result.metrics.get('total_time_sec', 0):.2f}s")
        print(f"Budget Remaining: ${task_brief.constraints['cost_usd'] - result.metrics.get('total_cost_usd', 0):.4f}")
        
        # Show retrospect status
        print("\n🔍 Retrospective Validation:")
        if hasattr(coordinator, 'retrospect_runner'):
            for retro_id, job in coordinator.retrospect_runner.jobs.items():
                status_icon = "✅" if job.status.value == "ok" else "⏳" if job.status.value == "pending" else "❌"
                print(f"  {status_icon} {retro_id}: {job.status.value}")
                if job.reason:
                    print(f"     Reason: {job.reason}")
        
        # Show promotion
        print("\n🎯 Production Promotion:")
        if "publish_prod" in result.steps_executed:
            print("  ✅ Report promoted to production")
            print(f"     URI: {result.artifacts.get('publish_prod', {}).get('uri', 'N/A')}")
        else:
            print("  ⏳ Waiting for retrospect validation")
        
        print("\n📊 Pipeline Summary:")
        print(f"  • Ingested: {result.artifacts.get('ingest', {}).get('record_count', 0)} records")
        print(f"  • Normalized: {len(result.artifacts.get('normalize', {}).get('records', []))} records")
        print(f"  • Reconciliation Delta: {result.artifacts.get('reconcile', {}).get('delta_pct', 0):.2%}")
        print(f"  • Aggregated: {result.artifacts.get('aggregate', {}).get('summary', {})}")
        
        print("\n💡 Key Features Demonstrated:")
        print("  • Fast inline validation allows pipeline to proceed")
        print("  • Async retrospect runs strict checks without blocking")
        print("  • Promotion gate prevents prod publish until retro green")
        print("  • Auto-rollback and replay if retrospect fails")
        print("  • Budget and SLA enforcement throughout")
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        print("\nFailure demonstrates:")
        print("  • Controller decision tree (retry → alternate → replan → escalate)")
        print("  • Budget/SLA guardrails")
        print("  • Escalation with clear severity levels")


if __name__ == "__main__":
    asyncio.run(main())

