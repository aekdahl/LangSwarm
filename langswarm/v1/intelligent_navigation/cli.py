"""
Navigation Analytics CLI

Command-line interface for viewing navigation analytics, 
generating reports, and managing navigation data.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional
import tabulate

from .tracker import NavigationTracker
from .dashboard import create_navigation_dashboard


def print_analytics_summary(tracker: NavigationTracker, workflow_id: Optional[str] = None, days: int = 30):
    """Print a summary of navigation analytics"""
    analytics = tracker.get_analytics(workflow_id=workflow_id, days=days)
    
    print(f"\n{'='*60}")
    print(f"🧭 NAVIGATION ANALYTICS SUMMARY")
    print(f"{'='*60}")
    
    if workflow_id:
        print(f"Workflow: {workflow_id}")
    else:
        print("All Workflows")
    
    print(f"Time Period: Last {days} days")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Basic metrics
    print("📊 BASIC METRICS")
    print("-" * 20)
    print(f"Total Decisions: {analytics.total_decisions}")
    print(f"Average Confidence: {analytics.avg_confidence:.2%}")
    print()
    
    # Performance metrics
    print("⚡ PERFORMANCE METRICS")
    print("-" * 25)
    performance = analytics.performance_metrics
    print(f"Avg Response Time: {performance.get('avg_execution_time_ms', 0):.1f}ms")
    print(f"Min Response Time: {performance.get('min_execution_time_ms', 0):.1f}ms")
    print(f"Max Response Time: {performance.get('max_execution_time_ms', 0):.1f}ms")
    print(f"Low Confidence Decisions: {performance.get('low_confidence_decisions', 0)}")
    print(f"High Confidence Decisions: {performance.get('high_confidence_decisions', 0)}")
    print()
    
    # Common paths
    if analytics.most_common_paths:
        print("🛤️  MOST COMMON PATHS")
        print("-" * 22)
        for i, path in enumerate(analytics.most_common_paths[:10], 1):
            print(f"{i:2d}. {path['path']} ({path['count']} times, {path['percentage']:.1f}%)")
        print()
    
    # Optimization suggestions
    if analytics.optimization_suggestions:
        print("💡 OPTIMIZATION SUGGESTIONS")
        print("-" * 30)
        for i, suggestion in enumerate(analytics.optimization_suggestions, 1):
            print(f"{i}. {suggestion}")
        print()
    else:
        print("💡 OPTIMIZATION SUGGESTIONS")
        print("-" * 30)
        print("✅ No issues detected. System is performing optimally!")
        print()


def print_recent_decisions(tracker: NavigationTracker, workflow_id: Optional[str] = None, limit: int = 20):
    """Print recent navigation decisions"""
    decisions = tracker.get_decisions(workflow_id=workflow_id, limit=limit)
    
    if not decisions:
        print("No navigation decisions found.")
        return
    
    print(f"\n🕐 RECENT NAVIGATION DECISIONS (Last {len(decisions)})")
    print("=" * 80)
    
    # Create table data
    table_data = []
    for decision in decisions:
        table_data.append([
            decision.timestamp.strftime('%m-%d %H:%M'),
            decision.workflow_id[:20] + "..." if len(decision.workflow_id) > 20 else decision.workflow_id,
            decision.step_id[:15] + "..." if len(decision.step_id) > 15 else decision.step_id,
            decision.chosen_step[:15] + "..." if len(decision.chosen_step) > 15 else decision.chosen_step,
            f"{decision.confidence:.1%}",
            f"{decision.execution_time_ms:.0f}ms",
            decision.reasoning[:30] + "..." if len(decision.reasoning) > 30 else decision.reasoning
        ])
    
    headers = ["Time", "Workflow", "From Step", "To Step", "Confidence", "Time", "Reasoning"]
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    print()


def export_analytics_report(tracker: NavigationTracker, output_file: str, workflow_id: Optional[str] = None, days: int = 30):
    """Export detailed analytics report to JSON"""
    analytics = tracker.get_analytics(workflow_id=workflow_id, days=days)
    decisions = tracker.get_decisions(workflow_id=workflow_id, limit=10000)
    
    report = {
        "export_timestamp": datetime.now().isoformat(),
        "workflow_id": workflow_id,
        "time_period_days": days,
        "analytics": {
            "total_decisions": analytics.total_decisions,
            "avg_confidence": analytics.avg_confidence,
            "most_common_paths": analytics.most_common_paths,
            "decision_patterns": analytics.decision_patterns,
            "performance_metrics": analytics.performance_metrics,
            "optimization_suggestions": analytics.optimization_suggestions
        },
        "recent_decisions": [
            {
                "decision_id": d.decision_id,
                "workflow_id": d.workflow_id,
                "step_id": d.step_id,
                "chosen_step": d.chosen_step,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat(),
                "execution_time_ms": d.execution_time_ms,
                "metadata": d.metadata
            }
            for d in decisions[:100]  # Include last 100 decisions
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"✅ Analytics report exported to: {output_file}")


def list_workflows(tracker: NavigationTracker):
    """List all workflows with navigation data"""
    decisions = tracker.get_decisions(limit=10000)
    
    workflow_stats = {}
    for decision in decisions:
        wf_id = decision.workflow_id
        if wf_id not in workflow_stats:
            workflow_stats[wf_id] = {
                "total_decisions": 0,
                "avg_confidence": 0.0,
                "last_activity": None,
                "first_activity": None
            }
        
        stats = workflow_stats[wf_id]
        stats["total_decisions"] += 1
        stats["avg_confidence"] = (
            (stats["avg_confidence"] * (stats["total_decisions"] - 1) + decision.confidence) 
            / stats["total_decisions"]
        )
        
        if not stats["last_activity"] or decision.timestamp > stats["last_activity"]:
            stats["last_activity"] = decision.timestamp
        
        if not stats["first_activity"] or decision.timestamp < stats["first_activity"]:
            stats["first_activity"] = decision.timestamp
    
    if not workflow_stats:
        print("No workflows found with navigation data.")
        return
    
    print(f"\n🗂️  WORKFLOWS WITH NAVIGATION DATA")
    print("=" * 60)
    
    table_data = []
    for wf_id, stats in sorted(workflow_stats.items(), key=lambda x: x[1]["total_decisions"], reverse=True):
        table_data.append([
            wf_id[:30] + "..." if len(wf_id) > 30 else wf_id,
            stats["total_decisions"],
            f"{stats['avg_confidence']:.1%}",
            stats["last_activity"].strftime('%Y-%m-%d %H:%M') if stats["last_activity"] else "N/A"
        ])
    
    headers = ["Workflow ID", "Decisions", "Avg Confidence", "Last Activity"]
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Navigation Analytics CLI")
    parser.add_argument("--db", default="navigation_decisions.db", help="Database file path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Show analytics summary")
    analytics_parser.add_argument("--workflow", help="Specific workflow ID")
    analytics_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    
    # Recent decisions command
    recent_parser = subparsers.add_parser("recent", help="Show recent decisions")
    recent_parser.add_argument("--workflow", help="Specific workflow ID")
    recent_parser.add_argument("--limit", type=int, default=20, help="Number of decisions to show")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export analytics report")
    export_parser.add_argument("output_file", help="Output JSON file")
    export_parser.add_argument("--workflow", help="Specific workflow ID")
    export_parser.add_argument("--days", type=int, default=30, help="Number of days to include")
    
    # List workflows command
    list_parser = subparsers.add_parser("workflows", help="List all workflows")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument("--port", type=int, default=8080, help="Port for web dashboard")
    dashboard_parser.add_argument("--host", default="0.0.0.0", help="Host for web dashboard")
    
    # Clear old data command
    clear_parser = subparsers.add_parser("clear", help="Clear old navigation data")
    clear_parser.add_argument("--days", type=int, default=90, help="Clear data older than this many days")
    clear_parser.add_argument("--confirm", action="store_true", help="Confirm deletion without prompt")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tracker
    try:
        tracker = NavigationTracker(args.db)
    except Exception as e:
        print(f"❌ Failed to initialize tracker: {e}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "analytics":
            print_analytics_summary(tracker, args.workflow, args.days)
        
        elif args.command == "recent":
            print_recent_decisions(tracker, args.workflow, args.limit)
        
        elif args.command == "export":
            export_analytics_report(tracker, args.output_file, args.workflow, args.days)
        
        elif args.command == "workflows":
            list_workflows(tracker)
        
        elif args.command == "dashboard":
            print(f"🚀 Starting navigation dashboard on http://{args.host}:{args.port}")
            print("Press Ctrl+C to stop")
            dashboard = create_navigation_dashboard(args.db, args.port)
            dashboard.run(args.host)
        
        elif args.command == "clear":
            if not args.confirm:
                confirm = input(f"Are you sure you want to clear data older than {args.days} days? (y/N): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    return
            
            tracker.clear_old_decisions(args.days)
            print(f"✅ Cleared navigation data older than {args.days} days")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 