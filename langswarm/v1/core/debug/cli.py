#!/usr/bin/env python3
"""
LangSwarm Debug CLI

Command-line interface for LangSwarm debug and tracing operations.

Usage:
    python -m langswarm.core.debug.cli run-case-1
    python -m langswarm.core.debug.cli run-all-basic
    python -m langswarm.core.debug.cli analyze-trace trace_file.jsonl
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from .debug_cases import (
    run_case_1, run_case_2, run_case_3, run_case_4, run_all_basic_cases,
    TestCaseRunner
)
from .config import (
    create_sample_debug_config, validate_debug_config, get_debug_config
)
from .tracer import DebugTracer, TraceEvent


def analyze_trace_file(file_path: str) -> Dict[str, Any]:
    """Analyze a trace file and return summary statistics"""
    
    if not Path(file_path).exists():
        return {"error": f"File not found: {file_path}"}
    
    events = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    event_data = json.loads(line)
                    events.append(TraceEvent(**event_data))
    except Exception as e:
        return {"error": f"Failed to parse trace file: {e}"}
    
    if not events:
        return {"error": "No events found in trace file"}
    
    # Group by trace_id
    traces = {}
    for event in events:
        if event.trace_id not in traces:
            traces[event.trace_id] = []
        traces[event.trace_id].append(event)
    
    # Calculate statistics
    stats = {
        "total_events": len(events),
        "total_traces": len(traces),
        "traces": {}
    }
    
    for trace_id, trace_events in traces.items():
        # Calculate duration
        start_events = [e for e in trace_events if e.event_type == "START"]
        end_events = [e for e in trace_events if e.event_type == "END"]
        
        duration_ms = 0
        if start_events and end_events:
            from datetime import datetime
            start_time = min(datetime.fromisoformat(e.timestamp) for e in start_events)
            end_time = max(datetime.fromisoformat(e.timestamp) for e in end_events)
            duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Count by event type
        event_counts = {}
        for event in trace_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Count by component
        component_counts = {}
        for event in trace_events:
            component_counts[event.component] = component_counts.get(event.component, 0) + 1
        
        # Find errors
        errors = [e for e in trace_events if e.level == "ERROR"]
        
        stats["traces"][trace_id] = {
            "events": len(trace_events),
            "duration_ms": duration_ms,
            "event_types": event_counts,
            "components": component_counts,
            "errors": len(errors),
            "error_messages": [e.message for e in errors]
        }
    
    return stats


def print_trace_analysis(stats: Dict[str, Any]):
    """Print formatted trace analysis"""
    
    if "error" in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    print("📊 Trace Analysis Summary")
    print("=" * 50)
    print(f"Total Events: {stats['total_events']}")
    print(f"Total Traces: {stats['total_traces']}")
    print()
    
    for trace_id, trace_stats in stats["traces"].items():
        print(f"🔍 Trace: {trace_id[:8]}...")
        print(f"   Events: {trace_stats['events']}")
        print(f"   Duration: {trace_stats['duration_ms']:.1f}ms")
        print(f"   Components: {', '.join(trace_stats['components'].keys())}")
        
        if trace_stats['errors'] > 0:
            print(f"   ❌ Errors: {trace_stats['errors']}")
            for error_msg in trace_stats['error_messages']:
                print(f"      - {error_msg}")
        else:
            print(f"   ✅ No errors")
        print()


def print_detailed_trace(file_path: str, trace_id: str = None):
    """Print detailed trace events"""
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    events = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    event_data = json.loads(line)
                    if not trace_id or event_data.get('trace_id') == trace_id:
                        events.append(TraceEvent(**event_data))
    except Exception as e:
        print(f"❌ Failed to parse trace file: {e}")
        return
    
    if not events:
        print("No matching events found")
        return
    
    print("📋 Detailed Trace Events")
    print("=" * 80)
    
    for event in events:
        timestamp = event.timestamp.split('.')[0]  # Remove microseconds
        indent = "  " * (len(event.span_id) % 3)  # Simple indentation based on span
        
        status_icon = {
            "START": "▶️",
            "END": "⏹️", 
            "INFO": "ℹ️",
            "ERROR": "❌",
            "TOOL_CALL": "🔧",
            "AGENT_RESPONSE": "🤖"
        }.get(event.event_type, "📝")
        
        print(f"{timestamp} {status_icon} {indent}{event.component}.{event.operation}")
        print(f"{' ' * len(timestamp)} {' ' * 2} {indent}{event.message}")
        
        # Show source file and line if available
        if hasattr(event, 'source_file') and event.source_file:
            source_info = f"{event.source_file}:{event.source_line}"
            if hasattr(event, 'source_function') and event.source_function:
                source_info += f" in {event.source_function}()"
            print(f"{' ' * len(timestamp)} {' ' * 2} {indent}📍 Source: {source_info}")
        
        if event.duration_ms:
            print(f"{' ' * len(timestamp)} {' ' * 2} {indent}Duration: {event.duration_ms:.1f}ms")
        
        if event.data and any(key not in ['duration_ms'] for key in event.data.keys()):
            relevant_data = {k: v for k, v in event.data.items() if k != 'duration_ms'}
            if relevant_data:
                print(f"{' ' * len(timestamp)} {' ' * 2} {indent}Data: {relevant_data}")
        print()


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="LangSwarm Debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m langswarm.core.debug.cli run-case-1
  python -m langswarm.core.debug.cli run-all-basic  
  python -m langswarm.core.debug.cli analyze debug_traces/case_1_simple_agent.jsonl
  python -m langswarm.core.debug.cli detail debug_traces/case_1_simple_agent.jsonl
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Debug case commands
    subparsers.add_parser('run-case-1', help='Run Case 1: Simple Agent')
    subparsers.add_parser('run-case-2', help='Run Case 2: Agent with Memory')
    subparsers.add_parser('run-case-3', help='Run Case 3: BigQuery Tool')
    subparsers.add_parser('run-case-4', help='Run Case 4: Agent with Tools')
    subparsers.add_parser('run-all-basic', help='Run all basic debug cases')
    
    # Configuration commands
    subparsers.add_parser('init-config', help='Create a sample debug configuration file')
    subparsers.add_parser('validate-config', help='Validate debug configuration')
    subparsers.add_parser('show-config', help='Show current debug configuration')
    
    # Analysis commands
    analyze_parser = subparsers.add_parser('analyze', help='Analyze trace file')
    analyze_parser.add_argument('file', help='Path to trace file (.jsonl)')
    
    detail_parser = subparsers.add_parser('detail', help='Show detailed trace events')
    detail_parser.add_argument('file', help='Path to trace file (.jsonl)')
    detail_parser.add_argument('--trace-id', help='Specific trace ID to show')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    try:
        if args.command == 'run-case-1':
            print("🚀 Running Case 1: Simple Agent")
            result = await run_case_1()
            print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
            if result.success:
                print(f"✅ Test completed successfully!")
                # Try to show the actual response from the trace
                if result.output_file and Path(result.output_file).exists():
                    try:
                        with open(result.output_file, 'r') as f:
                            for line in f:
                                event = json.loads(line)
                                if (event.get('component') == 'test_case' and 
                                    event.get('operation') == 'agent_response' and
                                    event.get('data', {}).get('response')):
                                    actual_response = event['data']['response']
                                    print(f"📤 Agent Response: '{actual_response}'")
                                    break
                    except Exception:
                        pass
            if result.output_file:
                print(f"Trace file: {result.output_file}")
        
        elif args.command == 'run-case-2':
            print("🚀 Running Case 2: Agent with Memory")
            result = await run_case_2()
            print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
            if result.output_file:
                print(f"Trace file: {result.output_file}")
        
        elif args.command == 'run-case-3':
            print("🚀 Running Case 3: BigQuery Tool")
            result = await run_case_3()
            print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
            if result.success:
                print(f"✅ BigQuery tool test completed!")
                
                # Show individual scenario trace files
                from glob import glob
                scenario_files = glob("debug_traces/case_3_bigquery_*.jsonl")
                # Exclude main tool file and summary file
                scenario_files = [f for f in scenario_files if not f.endswith("_tool.jsonl") and not f.endswith("_summary.jsonl")]
                
                if scenario_files:
                    print(f"\n📁 Individual scenario trace files:")
                    for trace_file in sorted(scenario_files):
                        scenario_name = trace_file.replace("debug_traces/case_3_bigquery_", "").replace(".jsonl", "")
                        print(f"   📊 {scenario_name}: {trace_file}")
                    print(f"   📄 setup: {result.output_file}")
                
                # Show summary of tool test results from main trace
                if result.output_file and Path(result.output_file).exists():
                    try:
                        with open(result.output_file, 'r') as f:
                            for line in f:
                                event = json.loads(line)
                                if (event.get('component') == 'test_case' and 
                                    event.get('operation') == 'tool_test_summary'):
                                    summary_data = event.get('data', {})
                                    total = summary_data.get('total_tests', 0)
                                    successful = summary_data.get('successful_tests', 0)
                                    print(f"📊 Overall: {successful}/{total} tests passed")
                                    break
                    except Exception:
                        pass
            # Main trace file info already shown above in the scenario list
        
        elif args.command == 'run-case-4':
            print("🚀 Running Case 4: Agent with Tools")
            result = await run_case_4()
            print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
            if result.output_file:
                print(f"Trace file: {result.output_file}")
        
        elif args.command == 'init-config':
            print("🔧 Creating sample debug configuration...")
            config_path = create_sample_debug_config()
            print(f"✅ Sample configuration created: {config_path}")
            print()
            print("📝 Next steps:")
            print("   1. Edit the configuration file with your API keys and settings")
            print("   2. Run 'validate-config' to check your configuration")
            print("   3. Start debugging with 'run-case-1'")
        
        elif args.command == 'validate-config':
            print("🔍 Validating debug configuration...")
            is_valid, errors = validate_debug_config()
            if is_valid:
                print("✅ Configuration is valid!")
                config = get_debug_config()
                print(f"   • OpenAI Model: {config.openai.model}")
                print(f"   • Output Directory: {config.output_dir}")
                if config.google_cloud.project_id:
                    print(f"   • GCP Project: {config.google_cloud.project_id}")
                if config.bigquery.dataset_id:
                    print(f"   • BigQuery Dataset: {config.bigquery.dataset_id}")
            else:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"   • {error}")
                print()
                print("💡 Run 'init-config' to create a sample configuration file")
        
        elif args.command == 'show-config':
            print("📋 Current debug configuration:")
            try:
                config = get_debug_config()
                print(f"   • OpenAI Model: {config.openai.model}")
                print(f"   • OpenAI API Key: {'✅ Set' if config.openai.api_key else '❌ Not set'}")
                print(f"   • Output Directory: {config.output_dir}")
                print(f"   • Log Level: {config.log_level}")
                print()
                print("🌥️  Google Cloud Configuration:")
                print(f"   • Project ID: {config.google_cloud.project_id or '❌ Not set'}")
                if config.google_cloud.credentials_path:
                    print(f"   • Credentials: ✅ Service account file")
                else:
                    print(f"   • Credentials: 🔐 Using gcloud auth (Application Default Credentials)")
                print()
                print("📊 BigQuery Configuration:")
                print(f"   • Dataset: {config.bigquery.dataset_id}")
                print(f"   • Table: {config.bigquery.table_name}")
                print(f"   • Embedding Model: {config.bigquery.embedding_model}")
                print(f"   • Max Results: {config.bigquery.max_results}")
            except Exception as e:
                print(f"❌ Error loading configuration: {e}")
                print("💡 Run 'init-config' to create a configuration file")
        
        elif args.command == 'run-all-basic':
            print("🚀 Running all basic test cases")
            results = await run_all_basic_cases()
            passed = sum(1 for r in results if r.success)
            print(f"\n📊 Summary: {passed}/{len(results)} tests passed")
        
        elif args.command == 'analyze':
            print(f"📊 Analyzing trace file: {args.file}")
            stats = analyze_trace_file(args.file)
            print_trace_analysis(stats)
        
        elif args.command == 'detail':
            print(f"📋 Detailed view of trace file: {args.file}")
            if args.trace_id:
                print(f"Filtering by trace ID: {args.trace_id}")
            print_detailed_trace(args.file, args.trace_id)
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
