"""
Example 03: Combined Gates and Retrospects

Demonstrates:
- Precondition/postcondition gates
- Async retrospective validation
- Promotion gates requiring retrospects
- Both gate failures and retrospect failures
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
    print("Example 03: Combined Gates and Retrospects")
    print("=" * 80)
    
    # Define task brief
    task_brief = TaskBrief(
        objective="Process user data with strict validation and gates",
        inputs={"raw_data": "user_profiles.csv"},
        required_outputs={"processed_data": "users.parquet"},
        acceptance_tests=[
            {"name": "schema_valid", "assertion": "schema_ok(output)"},
            {"name": "no_pii_leaks", "assertion": "pii_safe(output)"}
        ],
        constraints={
            "cost_usd": 2.0,
            "latency_sec": 120,
            "privacy": "pii_restricted"
        }
    )
    
    # Step 1: Ingest with precondition gate
    ingest = ActionContract(
        id="ingest",
        intent="Load user profile data from CSV",
        agent_or_tool="csv_reader",
        inputs={"path": "user_profiles.csv"},
        outputs={"data": "dataframe"},
        
        # GATE: Precondition - file must exist
        preconditions=[
            "file_exists('user_profiles.csv')",
            "file_size('user_profiles.csv') > 0"
        ],
        
        # GATE: Postcondition - data must be valid
        postconditions=[
            "len(output.data) > 0",
            "output.data.columns.contains('user_id', 'email', 'name')"
        ],
        
        validators=[
            {"fn": "schema_check", "args": {"required_cols": ["user_id", "email", "name"]}}
        ],
        
        gates=[
            {
                "type": "precondition",
                "assertion": "file_exists('user_profiles.csv')",
                "on_fail": {
                    "decision": "escalate",
                    "severity": "S2",
                    "message": "Input file missing"
                }
            },
            {
                "type": "postcondition",
                "assertion": "len(output.data) > 0",
                "on_fail": {
                    "decision": "replan",
                    "alternate": "fallback_loader"
                }
            }
        ],
        
        fallbacks=[
            {"type": "retry", "max": 1},
            {"type": "alternate", "agent": "robust_csv_reader"}
        ]
    )
    
    # Step 2: Sanitize PII with retrospects
    sanitize = ActionContract(
        id="sanitize",
        intent="Remove or mask PII from user data",
        agent_or_tool="pii_sanitizer",
        inputs={"data": "{{ ingest.data }}"},
        outputs={"sanitized": "dataframe", "pii_report": "json"},
        
        # GATE: Postcondition - no PII remaining
        postconditions=[
            "output.pii_report.pii_found == 0",
            "output.pii_report.confidence >= 0.95"
        ],
        
        confidence_floor=0.90,
        
        gates=[
            {
                "type": "postcondition",
                "assertion": "output.pii_report.pii_found == 0",
                "on_fail": {
                    "decision": "escalate",
                    "severity": "S1",  # Critical - PII leak
                    "message": "PII detected in sanitized output - SECURITY VIOLATION"
                }
            }
        ],
        
        # RETROSPECT: Deep PII scan (slow, runs async)
        retrospects=[
            {
                "id": "deep_pii_scan",
                "async": True,
                "checks": [
                    "deep_pii_regex_scan(output.sanitized)",
                    "ml_pii_detector(output.sanitized, threshold=0.99)",
                    "cross_reference_pii_db(output.sanitized)"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "sanitize",
                    "escalate": {
                        "severity": "S1",
                        "notify": ["security", "dpo"],
                        "message": "Retrospective PII scan found violations"
                    }
                }
            }
        ]
    )
    
    # Step 3: Validate with additional retrospects
    validate = ActionContract(
        id="validate",
        intent="Validate data integrity and business rules",
        agent_or_tool="data_validator",
        inputs={"data": "{{ sanitize.sanitized }}"},
        outputs={"validated": "dataframe", "validation_report": "json"},
        
        postconditions=[
            "output.validation_report.errors == 0",
            "output.validation_report.warnings <= 5"
        ],
        
        gates=[
            {
                "type": "postcondition",
                "assertion": "output.validation_report.errors == 0",
                "on_fail": {
                    "decision": "alternate",
                    "agent": "lenient_validator"
                }
            }
        ],
        
        # RETROSPECT: Business rule validation (slow)
        retrospects=[
            {
                "id": "business_rules_check",
                "async": True,
                "checks": [
                    "check_referential_integrity(output.validated)",
                    "validate_business_constraints(output.validated)",
                    "check_data_quality_score(output.validated, min_score=0.95)"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "validate",
                    "patch": {
                        "ops": [
                            {
                                "op": "param_update",
                                "target": "validate",
                                "params": {"strict_mode": True, "tolerance": 0.0}
                            }
                        ]
                    }
                }
            }
        ]
    )
    
    # Step 4: Publish with promotion gate
    publish = ActionContract(
        id="publish",
        intent="Publish validated data to production",
        agent_or_tool="data_publisher",
        inputs={"data": "{{ validate.validated }}", "destination": "prod_db"},
        outputs={"published": "bool", "record_count": "int"},
        
        side_effects=["write_to_prod_db", "send_notification"],
        
        # PROMOTION GATE: Don't publish until retrospects are green
        gates=[
            {
                "type": "promotion",
                "assertion": "retro_green('deep_pii_scan') AND retro_green('business_rules_check')",
                "on_fail": {
                    "decision": "cancel",
                    "escalate": {
                        "severity": "S2",
                        "message": "Cannot publish - retrospective validations not complete or failed"
                    }
                }
            }
        ],
        
        # Must wait for retrospects before publishing
        requires_retro_green=["deep_pii_scan", "business_rules_check"],
        
        escalation={
            "severity": "S1",
            "notify": ["ops", "security"],
            "on_violation": ["policy", "security"]
        }
    )
    
    # Create plan
    plan = Plan(
        plan_id="user_data_processing_with_gates",
        version=0,
        task_brief=task_brief,
        steps=[ingest, sanitize, validate, publish],
        dag={
            "ingest": [],
            "sanitize": ["ingest"],
            "validate": ["sanitize"],
            "publish": ["validate"]
        },
        metadata={
            "created": datetime.now(timezone.utc).isoformat(),
            "author": "example_03",
            "description": "User data processing with strict gates and retrospects"
        }
    )
    
    # Execute plan
    print("\n📋 Executing plan: user_data_processing_with_gates\n")
    
    coordinator = Coordinator()
    
    try:
        result = await coordinator.execute_task(plan)
        
        print("\n" + "=" * 80)
        print("✅ PLAN EXECUTION COMPLETE")
        print("=" * 80)
        print(f"Plan Version: {result.plan.version}")
        print(f"Steps Executed: {len(result.steps_executed)}")
        print(f"Total Cost: ${result.metrics.get('total_cost_usd', 0):.4f}")
        print(f"Total Time: {result.metrics.get('total_time_sec', 0):.2f}s")
        
        # Show gate enforcement
        print("\n🚪 Gate Enforcement Summary:")
        for step_id in result.steps_executed:
            if step_id in result.artifacts:
                artifact = result.artifacts[step_id]
                print(f"  • {step_id}: Passed all gates")
        
        # Show retrospect status
        print("\n🔍 Retrospect Status:")
        if hasattr(coordinator, 'retrospect_runner'):
            for retro_id, status in coordinator.retrospect_runner.jobs.items():
                print(f"  • {retro_id}: {status.status.value}")
        
        # Show promotion gates
        print("\n🎯 Promotion Gates:")
        print(f"  • publish: Waited for retrospects = {len(publish.requires_retro_green)}")
        
        print("\n📊 Artifacts:")
        for step_id, artifact in result.artifacts.items():
            print(f"  • {step_id}: {artifact}")
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        print("\nThis demonstrates:")
        print("  • Precondition gates prevent execution if inputs invalid")
        print("  • Postcondition gates validate outputs before continuing")
        print("  • Retrospect gates prevent promotion until heavy validation completes")
        print("  • Combination provides both speed (gates) and thoroughness (retrospects)")


if __name__ == "__main__":
    asyncio.run(main())

