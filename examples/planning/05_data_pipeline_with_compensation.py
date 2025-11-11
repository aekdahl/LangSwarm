"""
Example 05: Data Pipeline with Side Effects and Compensation

Demonstrates:
- ETL pipeline with external database writes (side effects)
- Retrospective validation catches data quality issues
- Compensation actions undo side effects on rollback
- Saga-style compensating transactions
- Clean rollback and replay story
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
    print("Example 05: ETL Pipeline with Compensation")
    print("=" * 80)
    
    # Define task brief
    task_brief = TaskBrief(
        objective="ETL pipeline: Extract orders, Transform, Load to warehouse",
        inputs={
            "source_db": "postgres://orders_db",
            "date_range": "2025-10-01..2025-10-07"
        },
        required_outputs={
            "warehouse_table": "orders_fact",
            "loaded_count": "int"
        },
        acceptance_tests=[
            {"name": "row_count", "assertion": "output.loaded_count > 0"},
            {"name": "data_quality", "assertion": "output.quality_score >= 0.95"}
        ],
        constraints={
            "cost_usd": 5.0,
            "latency_sec": 300,
            "data_integrity": "critical"
        }
    )
    
    # Step 1: Extract from source database
    extract = ActionContract(
        id="extract",
        intent="Extract orders from source database",
        agent_or_tool="db_extractor",
        inputs={
            "connection": "postgres://orders_db",
            "query": "SELECT * FROM orders WHERE date BETWEEN '2025-10-01' AND '2025-10-07'"
        },
        outputs={
            "raw_data": "dataframe",
            "row_count": "int"
        },
        preconditions=[
            "db_accessible('postgres://orders_db')",
            "table_exists('orders')"
        ],
        postconditions=[
            "output.row_count > 0"
        ],
        cost_estimate={"usd": 0.10, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=30.0
    )
    
    # Step 2: Transform with data quality checks
    transform = ActionContract(
        id="transform",
        intent="Transform and clean orders data",
        agent_or_tool="data_transformer",
        inputs={
            "data": "{{ extract.raw_data }}",
            "rules": "transform_rules.yaml"
        },
        outputs={
            "transformed": "dataframe",
            "quality_score": "float",
            "warnings": "list"
        },
        postconditions=[
            "output.quality_score >= 0.85",  # Allow 85% inline (fast check)
            "len(output.warnings) < 100"
        ],
        validators=[
            {"fn": "schema_valid", "args": {"schema": "orders_fact_schema"}},
            {"fn": "no_nulls", "args": {"required_cols": ["order_id", "amount", "customer_id"]}}
        ],
        cost_estimate={"usd": 0.20, "tokens_in": 5000, "tokens_out": 1000},
        latency_budget_sec=45.0,
        confidence_floor=0.85,
        
        # RETROSPECT: Deep data quality validation
        retrospects=[
            {
                "id": "deep_data_quality_check",
                "async": True,
                "checks": [
                    "referential_integrity_check(output.transformed, 'customers', 'products')",
                    "outlier_detection(output.transformed, threshold=0.99)",
                    "business_rule_validation(output.transformed, rules='strict')",
                    "cross_table_consistency(output.transformed, 'inventory', 'shipping')"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "transform",
                    "patch": {
                        "ops": [
                            {
                                "op": "param_update",
                                "target": "transform",
                                "params": {
                                    "strict_mode": True,
                                    "quality_threshold": 0.98,
                                    "fix_outliers": True
                                }
                            }
                        ]
                    },
                    "escalate": {
                        "severity": "S2",
                        "notify": ["data-ops", "data-quality-team"],
                        "message": "Deep data quality check failed - found integrity issues"
                    }
                }
            }
        ]
    )
    
    # Step 3: Load to staging warehouse (with side effects)
    load_staging = ActionContract(
        id="load_staging",
        intent="Load transformed data to staging warehouse table",
        agent_or_tool="warehouse_loader",
        inputs={
            "data": "{{ transform.transformed }}",
            "table": "staging.orders_fact",
            "mode": "append"
        },
        outputs={
            "loaded_count": "int",
            "table_uri": "string"
        },
        
        # SIDE EFFECT: Writes to external database
        side_effects=["write_to_staging_warehouse"],
        
        postconditions=[
            "output.loaded_count == len(inputs.data)"
        ],
        
        # COMPENSATION: Delete staging data if we need to rollback
        compensation={
            "action": "delete_staging_data",
            "params": {
                "table": "staging.orders_fact",
                "where": "batch_id = {{ execution.batch_id }}"
            },
            "description": "Delete inserted rows from staging table"
        },
        
        cost_estimate={"usd": 0.30, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=60.0
    )
    
    # Step 4: Validate in staging
    validate_staging = ActionContract(
        id="validate_staging",
        intent="Validate data in staging warehouse",
        agent_or_tool="warehouse_validator",
        inputs={
            "table": "staging.orders_fact",
            "batch_id": "{{ execution.batch_id }}"
        },
        outputs={
            "validation_report": "json",
            "passed": "bool"
        },
        postconditions=[
            "output.passed == True",
            "output.validation_report.errors == 0"
        ],
        cost_estimate={"usd": 0.15, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=30.0,
        
        # RETROSPECT: Cross-warehouse validation
        retrospects=[
            {
                "id": "cross_warehouse_validation",
                "async": True,
                "checks": [
                    "compare_with_source(staging.orders_fact, source.orders)",
                    "check_aggregate_totals(staging.orders_fact)",
                    "verify_foreign_keys(staging.orders_fact)"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "load_staging",
                    "escalate": {
                        "severity": "S1",
                        "notify": ["data-ops", "on-call"],
                        "message": "Cross-warehouse validation failed - data corruption detected"
                    }
                }
            }
        ]
    )
    
    # Step 5: Promote to production warehouse (with side effects and compensation)
    promote_to_prod = ActionContract(
        id="promote_to_prod",
        intent="Promote validated data to production warehouse",
        agent_or_tool="warehouse_promoter",
        inputs={
            "source_table": "staging.orders_fact",
            "dest_table": "prod.orders_fact",
            "batch_id": "{{ execution.batch_id }}"
        },
        outputs={
            "promoted_count": "int",
            "success": "bool"
        },
        
        # SIDE EFFECT: Writes to production warehouse
        side_effects=["write_to_prod_warehouse", "update_metadata_tables", "trigger_downstream_pipelines"],
        
        # PROMOTION GATE: Don't promote until retrospects are green
        gates=[
            {
                "type": "promotion",
                "assertion": "retro_green('deep_data_quality_check') AND retro_green('cross_warehouse_validation')",
                "on_fail": {
                    "decision": "cancel",
                    "escalate": {
                        "severity": "S2",
                        "message": "Cannot promote - retrospective validations not complete or failed"
                    }
                }
            }
        ],
        
        requires_retro_green=["deep_data_quality_check", "cross_warehouse_validation"],
        
        # COMPENSATION: Rollback production data if needed
        compensation={
            "action": "rollback_production_data",
            "params": {
                "table": "prod.orders_fact",
                "where": "batch_id = {{ execution.batch_id }}",
                "also_rollback": ["metadata_tables", "downstream_triggers"]
            },
            "description": "Rollback production insert and cascade to dependent systems"
        },
        
        cost_estimate={"usd": 0.50, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=60.0,
        
        escalation={
            "severity": "S1",
            "notify": ["data-ops", "on-call", "product-team"],
            "on_violation": ["data_integrity", "policy"]
        }
    )
    
    # Step 6: Cleanup staging
    cleanup = ActionContract(
        id="cleanup",
        intent="Clean up staging data after successful promotion",
        agent_or_tool="cleanup_runner",
        inputs={
            "table": "staging.orders_fact",
            "batch_id": "{{ execution.batch_id }}"
        },
        outputs={
            "deleted_count": "int"
        },
        side_effects=["delete_from_staging"],
        cost_estimate={"usd": 0.05, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=15.0
    )
    
    # Create plan
    plan = Plan(
        plan_id="etl_with_compensation",
        version=0,
        task_brief=task_brief,
        steps=[extract, transform, load_staging, validate_staging, promote_to_prod, cleanup],
        dag={
            "extract": [],
            "transform": ["extract"],
            "load_staging": ["transform"],
            "validate_staging": ["load_staging"],
            "promote_to_prod": ["validate_staging"],
            "cleanup": ["promote_to_prod"]
        },
        metadata={
            "created": datetime.now(timezone.utc).isoformat(),
            "author": "data-ops",
            "description": "ETL pipeline with side effects and saga-style compensation",
            "execution_id": f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        }
    )
    
    # Execute plan
    print("\n📋 Executing ETL pipeline: etl_with_compensation\n")
    
    coordinator = Coordinator()
    
    try:
        result = await coordinator.execute_task(plan)
        
        print("\n" + "=" * 80)
        print("✅ ETL PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Plan Version: {result.plan.version}")
        print(f"Steps Executed: {len(result.steps_executed)}")
        print(f"Total Cost: ${result.metrics.get('total_cost_usd', 0):.4f}")
        print(f"Total Time: {result.metrics.get('total_time_sec', 0):.2f}s")
        
        # Show side effects and compensations
        print("\n🔄 Side Effects & Compensations:")
        for step in plan.steps:
            if step.side_effects:
                print(f"  • {step.id}:")
                print(f"    Side Effects: {', '.join(step.side_effects)}")
                if step.compensation:
                    print(f"    Compensation: {step.compensation['action']}")
                    print(f"      Description: {step.compensation['description']}")
        
        # Show retrospect status
        print("\n🔍 Retrospective Validation:")
        if hasattr(coordinator, 'retrospect_runner'):
            for retro_id, job in coordinator.retrospect_runner.jobs.items():
                status_icon = "✅" if job.status.value == "ok" else "⏳" if job.status.value == "pending" else "❌"
                print(f"  {status_icon} {retro_id}: {job.status.value}")
                
                # If retrospect failed, show compensation triggered
                if job.status.value == "fail":
                    print(f"     ⚠️  Compensation would be triggered:")
                    print(f"        - Rollback staging data (load_staging)")
                    print(f"        - Rollback production data (promote_to_prod)")
                    print(f"        - Replay from failed step with stricter params")
        
        # Show promotion status
        print("\n🎯 Production Promotion:")
        if "promote_to_prod" in result.steps_executed:
            print("  ✅ Data promoted to production warehouse")
            print(f"     Rows: {result.artifacts.get('promote_to_prod', {}).get('promoted_count', 0)}")
            print("  ✅ Staging cleanup completed")
        else:
            print("  ⏳ Waiting for retrospect validation before promotion")
        
        print("\n📊 Pipeline Metrics:")
        print(f"  • Extracted: {result.artifacts.get('extract', {}).get('row_count', 0)} rows")
        print(f"  • Quality Score: {result.artifacts.get('transform', {}).get('quality_score', 0):.2%}")
        print(f"  • Staged: {result.artifacts.get('load_staging', {}).get('loaded_count', 0)} rows")
        print(f"  • Promoted: {result.artifacts.get('promote_to_prod', {}).get('promoted_count', 0)} rows")
        
        print("\n💡 Key Features Demonstrated:")
        print("  • Side effects tracked for each step (DB writes, triggers)")
        print("  • Compensation actions defined for rollback")
        print("  • Saga-style compensating transactions")
        print("  • Retrospect failure triggers automatic compensation")
        print("  • Clean rollback story: delete staging → rollback prod → replay")
        print("  • Promotion gate prevents prod write until retros green")
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        print("\nOn failure, compensation would:")
        print("  1. Delete inserted data from staging warehouse")
        print("  2. Rollback any production writes (if already promoted)")
        print("  3. Clean up metadata and downstream triggers")
        print("  4. Generate compensation audit log")
        print("  5. Replay from earliest safe checkpoint")


if __name__ == "__main__":
    asyncio.run(main())

