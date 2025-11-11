"""
Example 06: Advanced Lineage Tracking with Complex Dependencies

Demonstrates:
- Parallel branches that merge (diamond pattern)
- Content-addressed artifacts with lineage tracking
- Selective invalidation (only affected branch)
- Impact analysis for rollback decisions
- Visualize lineage graph
- Partial replay (only affected branches)
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


async def visualize_lineage(coordinator):
    """Visualize the artifact lineage graph"""
    print("\n📊 Artifact Lineage Graph:")
    print("=" * 80)
    
    if not hasattr(coordinator, 'lineage_graph'):
        print("  (Lineage tracking not available)")
        return
    
    graph = coordinator.lineage_graph
    
    # Show all artifacts and their dependencies
    for artifact_id in graph.graph:
        parents = graph.graph[artifact_id]
        if parents:
            print(f"  {artifact_id}")
            print(f"    ← depends on: {', '.join(parents)}")
        else:
            print(f"  {artifact_id} (root)")
    
    print("\n" + "=" * 80)


async def demonstrate_impact_analysis(coordinator, failed_artifact_id):
    """Demonstrate impact analysis for a failed artifact"""
    print(f"\n🔍 Impact Analysis for Failed Artifact: {failed_artifact_id}")
    print("=" * 80)
    
    if not hasattr(coordinator, 'lineage_graph'):
        print("  (Lineage tracking not available)")
        return
    
    graph = coordinator.lineage_graph
    
    # Get downstream impacted artifacts
    impacted = graph.downstream_of(failed_artifact_id)
    
    print(f"  Impacted artifacts: {len(impacted)}")
    for artifact_id in impacted:
        print(f"    • {artifact_id}")
    
    # Find earliest valid ancestor for replay
    earliest = graph.find_earliest_valid_ancestor(impacted)
    print(f"\n  Replay from: {earliest}")
    print(f"  Steps to replay: {len(impacted) + 1}")
    
    print("=" * 80)


async def main():
    print("=" * 80)
    print("Example 06: Advanced Lineage Tracking")
    print("=" * 80)
    
    # Define task brief
    task_brief = TaskBrief(
        objective="Multi-source data analysis with parallel processing",
        inputs={
            "source_a": "customers.csv",
            "source_b": "orders.csv",
            "source_c": "products.csv"
        },
        required_outputs={
            "unified_report": "parquet",
            "analysis_summary": "json"
        },
        acceptance_tests=[
            {"name": "all_sources_included", "assertion": "output.sources == ['a', 'b', 'c']"},
            {"name": "analysis_complete", "assertion": "output.completeness >= 0.95"}
        ],
        constraints={
            "cost_usd": 4.0,
            "latency_sec": 180
        }
    )
    
    # Root: Load source A
    load_a = ActionContract(
        id="load_a",
        intent="Load customer data",
        agent_or_tool="csv_loader",
        inputs={"path": "customers.csv"},
        outputs={"data_a": "dataframe"},
        postconditions=["len(output.data_a) > 0"],
        cost_estimate={"usd": 0.10, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=20.0
    )
    
    # Root: Load source B
    load_b = ActionContract(
        id="load_b",
        intent="Load order data",
        agent_or_tool="csv_loader",
        inputs={"path": "orders.csv"},
        outputs={"data_b": "dataframe"},
        postconditions=["len(output.data_b) > 0"],
        cost_estimate={"usd": 0.10, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=20.0
    )
    
    # Root: Load source C
    load_c = ActionContract(
        id="load_c",
        intent="Load product data",
        agent_or_tool="csv_loader",
        inputs={"path": "products.csv"},
        outputs={"data_c": "dataframe"},
        postconditions=["len(output.data_c) > 0"],
        cost_estimate={"usd": 0.10, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=20.0
    )
    
    # Branch 1: Process A with retrospect (may fail)
    process_a = ActionContract(
        id="process_a",
        intent="Clean and enrich customer data",
        agent_or_tool="data_processor",
        inputs={"data": "{{ load_a.data_a }}"},
        outputs={"processed_a": "dataframe", "quality": "float"},
        postconditions=["output.quality >= 0.80"],
        cost_estimate={"usd": 0.20, "tokens_in": 2000, "tokens_out": 400},
        latency_budget_sec=30.0,
        
        # RETROSPECT: Deep validation (may catch issues)
        retrospects=[
            {
                "id": "deep_customer_validation",
                "async": True,
                "checks": [
                    "duplicate_detection(output.processed_a)",
                    "referential_integrity(output.processed_a)",
                    "data_quality_score(output.processed_a, min=0.95)"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "process_a",
                    "patch": {
                        "ops": [{"op": "param_update", "target": "process_a", "params": {"strict": True}}]
                    },
                    "escalate": {
                        "severity": "S3",
                        "message": "Customer data quality below threshold"
                    }
                }
            }
        ]
    )
    
    # Branch 2: Process B (no retrospect, always succeeds)
    process_b = ActionContract(
        id="process_b",
        intent="Aggregate order statistics",
        agent_or_tool="aggregator",
        inputs={"data": "{{ load_b.data_b }}"},
        outputs={"processed_b": "dataframe", "totals": "json"},
        postconditions=["output.totals.order_count > 0"],
        cost_estimate={"usd": 0.15, "tokens_in": 1500, "tokens_out": 300},
        latency_budget_sec=25.0
    )
    
    # Branch 3: Process C (no retrospect, always succeeds)
    process_c = ActionContract(
        id="process_c",
        intent="Categorize products",
        agent_or_tool="categorizer",
        inputs={"data": "{{ load_c.data_c }}"},
        outputs={"processed_c": "dataframe", "categories": "list"},
        postconditions=["len(output.categories) > 0"],
        cost_estimate={"usd": 0.12, "tokens_in": 1200, "tokens_out": 250},
        latency_budget_sec=22.0
    )
    
    # Merge 1: Join A and B
    join_ab = ActionContract(
        id="join_ab",
        intent="Join customer and order data",
        agent_or_tool="joiner",
        inputs={
            "left": "{{ process_a.processed_a }}",
            "right": "{{ process_b.processed_b }}",
            "on": "customer_id"
        },
        outputs={"joined_ab": "dataframe"},
        postconditions=["len(output.joined_ab) > 0"],
        cost_estimate={"usd": 0.18, "tokens_in": 2500, "tokens_out": 500},
        latency_budget_sec=30.0
    )
    
    # Merge 2: Join AB and C (final merge)
    join_abc = ActionContract(
        id="join_abc",
        intent="Join customer-order data with product data",
        agent_or_tool="joiner",
        inputs={
            "left": "{{ join_ab.joined_ab }}",
            "right": "{{ process_c.processed_c }}",
            "on": "product_id"
        },
        outputs={"unified": "dataframe"},
        postconditions=["len(output.unified) > 0"],
        cost_estimate={"usd": 0.20, "tokens_in": 3000, "tokens_out": 600},
        latency_budget_sec=35.0
    )
    
    # Final: Analyze unified data
    analyze = ActionContract(
        id="analyze",
        intent="Generate analysis summary from unified data",
        agent_or_tool="analyzer",
        inputs={"data": "{{ join_abc.unified }}"},
        outputs={"summary": "json", "report": "dataframe"},
        postconditions=["output.summary.completeness >= 0.95"],
        cost_estimate={"usd": 0.25, "tokens_in": 4000, "tokens_out": 800},
        latency_budget_sec=40.0,
        
        # RETROSPECT: Final validation
        retrospects=[
            {
                "id": "final_analysis_validation",
                "async": True,
                "checks": [
                    "cross_source_consistency(output.summary)",
                    "business_logic_validation(output.summary)",
                    "statistical_outlier_check(output.summary)"
                ],
                "on_fail": {
                    "invalidate_downstream": True,
                    "replay_from": "analyze",
                    "escalate": {
                        "severity": "S2",
                        "message": "Final analysis validation failed"
                    }
                }
            }
        ]
    )
    
    # Publish final results
    publish = ActionContract(
        id="publish",
        intent="Publish unified report and analysis",
        agent_or_tool="publisher",
        inputs={
            "report": "{{ join_abc.unified }}",
            "summary": "{{ analyze.summary }}"
        },
        outputs={"uri": "string", "success": "bool"},
        side_effects=["write_to_storage", "notify_stakeholders"],
        
        # Wait for retrospects
        requires_retro_green=["deep_customer_validation", "final_analysis_validation"],
        
        gates=[
            {
                "type": "promotion",
                "assertion": "retro_green('deep_customer_validation') AND retro_green('final_analysis_validation')",
                "on_fail": {
                    "decision": "cancel",
                    "escalate": {"severity": "S3", "message": "Retrospects not green"}
                }
            }
        ],
        
        cost_estimate={"usd": 0.10, "tokens_in": 0, "tokens_out": 0},
        latency_budget_sec=20.0
    )
    
    # Create plan with diamond DAG pattern
    plan = Plan(
        plan_id="complex_lineage_example",
        version=0,
        task_brief=task_brief,
        steps=[load_a, load_b, load_c, process_a, process_b, process_c, join_ab, join_abc, analyze, publish],
        dag={
            # Three independent roots
            "load_a": [],
            "load_b": [],
            "load_c": [],
            
            # Three parallel branches
            "process_a": ["load_a"],
            "process_b": ["load_b"],
            "process_c": ["load_c"],
            
            # First merge: A + B
            "join_ab": ["process_a", "process_b"],
            
            # Second merge: AB + C (diamond converges)
            "join_abc": ["join_ab", "process_c"],
            
            # Final steps
            "analyze": ["join_abc"],
            "publish": ["analyze"]
        },
        metadata={
            "created": datetime.now(timezone.utc).isoformat(),
            "author": "example_06",
            "description": "Complex lineage with parallel branches and diamond pattern",
            "dag_pattern": "diamond"
        }
    )
    
    # Execute plan
    print("\n📋 Executing plan: complex_lineage_example\n")
    print("DAG Pattern (Diamond):")
    print("       load_a    load_b    load_c")
    print("          |        |        |")
    print("       process_a process_b process_c")
    print("           \\      /          /")
    print("            join_ab         /")
    print("                 \\         /")
    print("                  join_abc")
    print("                     |")
    print("                  analyze")
    print("                     |")
    print("                  publish")
    print()
    
    coordinator = Coordinator()
    
    try:
        result = await coordinator.execute_task(plan)
        
        print("\n" + "=" * 80)
        print("✅ COMPLEX PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Plan Version: {result.plan.version}")
        print(f"Steps Executed: {len(result.steps_executed)}")
        print(f"Total Cost: ${result.metrics.get('total_cost_usd', 0):.4f}")
        print(f"Total Time: {result.metrics.get('total_time_sec', 0):.2f}s")
        
        # Visualize lineage
        await visualize_lineage(coordinator)
        
        # Demonstrate impact analysis
        print("\n💡 Scenario: If 'process_a' retrospect fails:")
        await demonstrate_impact_analysis(coordinator, "process_a/processed_a")
        
        print("\n📊 Selective Invalidation:")
        print("  If process_a retrospect fails:")
        print("    ✅ Branch B (process_b) is NOT affected")
        print("    ✅ Branch C (process_c) is NOT affected")
        print("    ❌ join_ab IS affected (depends on process_a)")
        print("    ❌ join_abc IS affected (depends on join_ab)")
        print("    ❌ analyze IS affected (depends on join_abc)")
        print("    ❌ publish IS affected (depends on analyze)")
        print()
        print("  Replay strategy:")
        print("    1. Invalidate: process_a, join_ab, join_abc, analyze, publish")
        print("    2. Keep cached: load_a, load_b, load_c, process_b, process_c")
        print("    3. Replay from: process_a (with stricter params)")
        print("    4. Cascade through: join_ab → join_abc → analyze → publish")
        print("    5. Result: Only affected branch replays, others reuse cache")
        
        print("\n💡 Key Features Demonstrated:")
        print("  • Parallel branches execute independently")
        print("  • Content-addressed artifacts (immutable, hashable)")
        print("  • Lineage graph tracks all dependencies")
        print("  • Impact analysis identifies affected artifacts")
        print("  • Selective invalidation (only replay affected branch)")
        print("  • Unaffected branches reuse cached results")
        print("  • Efficient partial replay reduces cost and latency")
        
        # Show retrospect status
        print("\n🔍 Retrospective Validation:")
        if hasattr(coordinator, 'retrospect_runner'):
            for retro_id, job in coordinator.retrospect_runner.jobs.items():
                status_icon = "✅" if job.status.value == "ok" else "⏳" if job.status.value == "pending" else "❌"
                print(f"  {status_icon} {retro_id}: {job.status.value}")
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        print("\nThis demonstrates how lineage tracking enables:")
        print("  • Precise impact analysis")
        print("  • Minimal replay scope")
        print("  • Cost-effective error recovery")


if __name__ == "__main__":
    asyncio.run(main())

