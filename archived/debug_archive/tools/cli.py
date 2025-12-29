#!/usr/bin/env python3
"""
Debug Tools CLI

A comprehensive CLI for testing debug tools using LangSwarm workflows
with full tracing and observability integration.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Look for .env file in debug directory (parent of tools)
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"🔧 Loaded environment variables from {env_file}")
    else:
        # Fallback to current directory
        load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables only")

# Import LangSwarm components
from langswarm.core.config import load_config
from langswarm.core.workflows import get_workflow_engine
from langswarm.core.agents import AgentBuilder
from langswarm.core.observability import ObservabilityProvider
from langswarm.tools.registry import ToolRegistry
from langswarm.tools.base import ToolResult

# Import debug tools
from debug.tools.bigquery_vector_search.tool import create_bigquery_search_tool
from debug.tools.sql_database.tool import create_sql_database_tool
from debug.tools.query_selector import select_query_interactive
from debug.tools.tracer import initialize_debug_tracer, get_debug_tracer

# Color codes for better output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'


class DebugTracer:
    """Simple debug tracer for tool testing"""
    
    def __init__(self, output_file: Optional[str] = None):
        self.output_file = output_file
        self.enabled = output_file is not None
        self.traces = []
        
        if self.enabled:
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    def trace_event(self, event_type: str, component: str, operation: str, 
                   message: str, data: Optional[Dict[str, Any]] = None):
        """Record a trace event"""
        if not self.enabled:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "component": component,
            "operation": operation,
            "message": message,
            "data": data or {}
        }
        
        self.traces.append(event)
        
        # Write to file immediately for real-time tracing
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(json.dumps(event) + '\n')
            except Exception as e:
                print(f"Warning: Failed to write trace: {e}")
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all recorded traces"""
        return self.traces.copy()


class DebugToolsCLI:
    """Main CLI for debug tools testing"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = Path(__file__).parent / "debug_tools_config.yaml"
        self.tracer = None
        self.logger = logging.getLogger(__name__)
        
        # Setup directories
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup required directories (traces are handled separately)"""
        # Note: Traces are stored in debug/traces/ (parent directory)
        # No local directories needed since we focus on traces only
        pass
    
    def _setup_logging(self, debug: bool = False):
        """Setup minimal logging (focusing on traces instead)"""
        # Minimal logging setup - we focus on traces now
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        return None
    
    def _setup_tracing(self, enable_tracing: bool = True) -> Optional[str]:
        """Setup tracing configuration using comprehensive tracer"""
        if not enable_tracing:
            return None
        
        # Store traces in debug/traces/ directory (parent of tools)
        trace_file = Path(__file__).parent.parent / "traces" / f"tool_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the comprehensive debug tracer
        self.tracer = initialize_debug_tracer(enabled=True, output_file=str(trace_file))
        
        return str(trace_file)
    
    async def test_single_tool(self, tool_name: str, query: str = None, method: str = "search", interactive: bool = True) -> Dict[str, Any]:
        """Test a single tool with a query"""
        
        # Interactive query selection if no query provided
        selected_option = None
        if query is None and interactive:
            query, selected_option = select_query_interactive(tool_name, auto_mode=False)
            if not query:
                return {
                    "success": False,
                    "tool": tool_name,
                    "method": method,
                    "query": "",
                    "error": "No query selected",
                    "cancelled": True
                }
            
            # Show selected query info
            if selected_option:
                print(f"{Colors.CYAN}📋 Using pre-written query: {selected_option.name}{Colors.NC}")
                print(f"{Colors.BLUE}Description: {selected_option.description}{Colors.NC}")
            else:
                print(f"{Colors.CYAN}📝 Using custom query{Colors.NC}")
        
        print(f"{Colors.CYAN}🔧 Testing {tool_name} with query: '{query}'{Colors.NC}")
        print("=" * 60)
        
        if self.tracer:
            self.tracer.log_event("START", "cli", "test_single_tool", 
                                 f"Testing {tool_name}", "INFO", {
                                     "tool": tool_name, 
                                     "query": query,
                                     "method": method,
                                     "interactive": interactive,
                                     "query_source": "pre-written" if selected_option else "custom" if query else "none",
                                     "selected_query_name": selected_option.name if selected_option else None,
                                     "selected_query_category": selected_option.category if selected_option else None
                                 })
        
        try:
            # Trace tool creation
            if self.tracer:
                self.tracer.log_event("INFO", "cli", "create_tool", 
                                     f"Creating {tool_name} tool instance", "INFO", {
                                         "tool": tool_name
                                     })
            
            # Create tool instance
            if tool_name == "bigquery":
                config = {
                    "project_id": os.getenv('GOOGLE_CLOUD_PROJECT'),
                    "debug_mode": True,
                    "trace_queries": True
                }
                tool = create_bigquery_search_tool(config)
            elif tool_name == "sql":
                config = {
                    "db_type": "sqlite",
                    "database_path": str(Path(__file__).parent / "test_database.db"),
                    "debug_mode": True,
                    "trace_queries": True
                }
                tool = create_sql_database_tool(config)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Trace tool execution start
            if self.tracer:
                self.tracer.log_event("INFO", "cli", "execute_tool", 
                                     f"Executing {tool_name}.{method}", "INFO", {
                                         "tool": tool_name,
                                         "method": method,
                                         "query": query,
                                         "config": config
                                     })
            
            # Execute tool using the correct async methods
            if method == "search" and tool_name == "bigquery":
                result = await tool.search(query)
            elif method == "search" and tool_name == "sql":
                # SQL tool uses execute_query method
                sql_result = await tool.execute_query(query)
                result = ToolResult(
                    success=True,
                    data=sql_result.results,
                    metadata=sql_result.metadata
                )
            elif method == "query" and tool_name == "sql":
                sql_result = await tool.execute_query(query)
                result = ToolResult(
                    success=True,
                    data=sql_result.results,
                    metadata=sql_result.metadata
                )
            elif method == "health_check":
                result = await tool.execute("health_check", {})
            elif method == "list_datasets" and tool_name == "bigquery":
                result = await tool.list_datasets()
            else:
                # Default based on tool type
                if tool_name == "bigquery":
                    result = await tool.search(query)
                elif tool_name == "sql":
                    sql_result = await tool.execute_query(query)
                    result = ToolResult(
                        success=True,
                        data=sql_result.results,
                        metadata=sql_result.metadata
                    )
                else:
                    raise ValueError(f"Unknown method {method} for tool {tool_name}")
            
            # Trace tool execution result
            if self.tracer:
                self.tracer.log_event("SUCCESS", "cli", "test_single_tool",
                                     f"Tool {tool_name} executed successfully", "INFO",
                                     {
                                         "result_success": result.success,
                                         "result_data_type": type(result.data).__name__,
                                         "result_metadata": result.metadata,
                                         "execution_time": result.metadata.get("execution_time_ms") if result.metadata else None
                                     })
            
            return {
                "success": True,
                "tool": tool_name,
                "method": method,
                "query": query,
                "result": result.data,
                "metadata": result.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Tool test failed: {e}")
            
            if self.tracer:
                self.tracer.log_event("ERROR", "cli", "test_single_tool",
                                     f"Tool {tool_name} failed: {e}", "ERROR",
                                     {
                                         "error": str(e), 
                                         "error_type": type(e).__name__,
                                         "tool": tool_name,
                                         "method": method,
                                         "query": query,
                                         "stack_trace": str(e.__traceback__) if hasattr(e, '__traceback__') else None
                                     })
            
            return {
                "success": False,
                "tool": tool_name,
                "method": method,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_workflow(self, workflow_id: str, user_input: str) -> Dict[str, Any]:
        """Test a complete workflow"""
        
        print(f"{Colors.CYAN}🔄 Testing workflow: {workflow_id}{Colors.NC}")
        print(f"{Colors.CYAN}📝 Input: {user_input}{Colors.NC}")
        print("=" * 60)
        
        if self.tracer:
            self.tracer.trace_event("START", "cli", "test_workflow",
                                   f"Testing workflow {workflow_id}",
                                   {"workflow_id": workflow_id, "input": user_input})
        
        try:
            # Load configuration
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            config = load_config(str(self.config_path))
            
            # Get workflow engine
            engine = get_workflow_engine()
            
            # Execute workflow
            result = await engine.execute_workflow(
                workflow_id=workflow_id,
                input_data={"user_input": user_input, "query": user_input}
            )
            
            if self.tracer:
                self.tracer.trace_event("SUCCESS", "cli", "test_workflow",
                                       f"Workflow {workflow_id} completed",
                                       {"execution_time": result.execution_time if hasattr(result, 'execution_time') else None})
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "input": user_input,
                "result": result.output if hasattr(result, 'output') else str(result),
                "execution_time": result.execution_time if hasattr(result, 'execution_time') else None
            }
            
        except Exception as e:
            self.logger.error(f"Workflow test failed: {e}")
            
            if self.tracer:
                self.tracer.trace_event("ERROR", "cli", "test_workflow",
                                       f"Workflow {workflow_id} failed: {e}",
                                       {"error": str(e), "error_type": type(e).__name__})
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "input": user_input,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all debug tools"""
        
        print(f"{Colors.CYAN}🏥 Running health checks for all tools{Colors.NC}")
        print("=" * 60)
        
        results = {}
        
        # Test BigQuery tool
        try:
            bigquery_result = await self.test_single_tool("bigquery", "", "health_check")
            results["bigquery"] = bigquery_result
        except Exception as e:
            results["bigquery"] = {"success": False, "error": str(e)}
        
        # Test SQL tool
        try:
            sql_result = await self.test_single_tool("sql", "", "health_check")
            results["sql"] = sql_result
        except Exception as e:
            results["sql"] = {"success": False, "error": str(e)}
        
        # Overall health
        overall_healthy = all(result.get("success", False) for result in results.values())
        
        return {
            "overall_healthy": overall_healthy,
            "tools": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print results in a formatted way"""
        
        print(f"\n{Colors.BOLD}📊 RESULTS{Colors.NC}")
        print("=" * 60)
        
        if results.get("success", False):
            print(f"{Colors.GREEN}✅ Success{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Failed{Colors.NC}")
        
        # Print main result data
        if "result" in results:
            result_data = results["result"]
            if isinstance(result_data, dict):
                if "results" in result_data and isinstance(result_data["results"], list):
                    print(f"\n{Colors.CYAN}📋 Query Results ({len(result_data['results'])} rows):{Colors.NC}")
                    for i, row in enumerate(result_data["results"][:5]):  # Show first 5 rows
                        print(f"  {i+1}. {json.dumps(row, indent=2)}")
                    if len(result_data["results"]) > 5:
                        print(f"  ... and {len(result_data['results']) - 5} more rows")
                
                if "metadata" in result_data:
                    print(f"\n{Colors.YELLOW}📊 Metadata:{Colors.NC}")
                    print(json.dumps(result_data["metadata"], indent=2))
            else:
                print(f"\n{Colors.CYAN}📋 Result:{Colors.NC}")
                print(json.dumps(result_data, indent=2))
        
        # Print error if any
        if "error" in results:
            print(f"\n{Colors.RED}❌ Error: {results['error']}{Colors.NC}")
        
        # Print execution info
        if "execution_time" in results:
            print(f"\n{Colors.MAGENTA}⏱️  Execution Time: {results['execution_time']:.2f}ms{Colors.NC}")
        
        print("\n" + "=" * 60)
    
    async def run(self, args) -> int:
        """Run the CLI"""
        
        print(f"{Colors.BOLD}🚀 LangSwarm Debug Tools CLI{Colors.NC}")
        print(f"{Colors.CYAN}📅 {datetime.now()}{Colors.NC}")
        print(f"{Colors.CYAN}📁 Project: {self.project_root}{Colors.NC}")
        print("=" * 60)
        
        # Setup minimal logging and comprehensive tracing
        self._setup_logging(args.debug)
        trace_file = self._setup_tracing(args.trace)
        
        if trace_file:
            print(f"{Colors.YELLOW}🔍 Tracing enabled: {trace_file}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}📝 Running without tracing{Colors.NC}")
        
        try:
            if args.command == 'test-tool':
                # Use interactive mode if no query provided
                interactive = not hasattr(args, 'query') or args.query is None
                query = getattr(args, 'query', None)
                result = await self.test_single_tool(args.tool, query, args.method, interactive=interactive)
                
                # Don't treat cancellation as failure
                if result.get("cancelled"):
                    print(f"{Colors.CYAN}👋 Tool test cancelled{Colors.NC}")
                    return 0
                
                self.print_results(result)
                return 0 if result["success"] else 1
            
            elif args.command == 'test-workflow':
                result = await self.test_workflow(args.workflow, args.query)
                self.print_results(result)
                return 0 if result["success"] else 1
            
            elif args.command == 'health-check':
                result = await self.health_check_all()
                self.print_results(result)
                return 0 if result["overall_healthy"] else 1
            
            elif args.command == 'interactive':
                return await self.interactive_mode()
            
            else:
                print(f"{Colors.RED}❌ Unknown command: {args.command}{Colors.NC}")
                return 1
                
        except KeyboardInterrupt:
            print(f"\n{Colors.CYAN}👋 Interrupted by user{Colors.NC}")
            return 130
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1
        finally:
            # Print trace summary if tracing was enabled
            if self.tracer and trace_file:
                event_count = len(self.tracer.events) if self.tracer and hasattr(self.tracer, 'events') else 0
                print(f"\n{Colors.CYAN}📊 Trace Summary: {event_count} events recorded in {trace_file}{Colors.NC}")
    
    async def interactive_mode(self) -> int:
        """Run in interactive mode"""
        
        print(f"{Colors.BOLD}🎮 Interactive Mode{Colors.NC}")
        print("Type 'help' for commands, 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input(f"{Colors.CYAN}> {Colors.NC}").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"{Colors.CYAN}👋 Goodbye!{Colors.NC}")
                    break
                
                elif user_input.lower() == 'help':
                    self._print_interactive_help()
                
                elif user_input.startswith('bigquery '):
                    query = user_input[9:].strip()
                    if not query:
                        # Interactive query selection
                        result = await self.test_single_tool("bigquery", None, "search", interactive=True)
                    else:
                        result = await self.test_single_tool("bigquery", query, "search", interactive=False)
                    self.print_results(result)
                
                elif user_input.startswith('sql '):
                    query = user_input[4:].strip()
                    if not query:
                        # Interactive query selection
                        result = await self.test_single_tool("sql", None, "query", interactive=True)
                    else:
                        result = await self.test_single_tool("sql", query, "query", interactive=False)
                    self.print_results(result)
                
                elif user_input == 'bigquery':
                    # Interactive query selection
                    result = await self.test_single_tool("bigquery", None, "search", interactive=True)
                    self.print_results(result)
                
                elif user_input == 'sql':
                    # Interactive query selection
                    result = await self.test_single_tool("sql", None, "query", interactive=True)
                    self.print_results(result)
                
                elif user_input == 'health':
                    result = await self.health_check_all()
                    self.print_results(result)
                
                elif user_input.startswith('workflow '):
                    parts = user_input.split(' ', 2)
                    if len(parts) >= 3:
                        workflow_id = parts[1]
                        query = parts[2]
                        result = await self.test_workflow(workflow_id, query)
                        self.print_results(result)
                    else:
                        print(f"{Colors.RED}Usage: workflow <workflow_id> <query>{Colors.NC}")
                
                elif user_input:
                    print(f"{Colors.RED}Unknown command. Type 'help' for available commands.{Colors.NC}")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.NC}")
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        
        return 0
    
    def _print_interactive_help(self):
        """Print help for interactive mode"""
        
        print(f"\n{Colors.BOLD}Available Commands:{Colors.NC}")
        print(f"{Colors.CYAN}bigquery{Colors.NC}             - Interactive BigQuery query selection")
        print(f"{Colors.CYAN}bigquery <query>{Colors.NC}     - Test BigQuery with specific query")
        print(f"{Colors.CYAN}sql{Colors.NC}                  - Interactive SQL query selection")
        print(f"{Colors.CYAN}sql <query>{Colors.NC}          - Test SQL with specific query")
        print(f"{Colors.CYAN}workflow <id> <query>{Colors.NC} - Test workflow execution")
        print(f"{Colors.CYAN}health{Colors.NC}               - Check health of all tools")
        print(f"{Colors.CYAN}help{Colors.NC}                 - Show this help")
        print(f"{Colors.CYAN}quit{Colors.NC}                 - Exit interactive mode")
        print()
        print(f"{Colors.YELLOW}💡 Tips:{Colors.NC}")
        print(f"  • Use '{Colors.GREEN}bigquery{Colors.NC}' or '{Colors.GREEN}sql{Colors.NC}' without a query for interactive selection")
        print(f"  • Interactive mode offers pre-written queries and custom input")
        print(f"  • Pre-written queries include examples, tests, and error cases")
        print()


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="LangSwarm Debug Tools CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test BigQuery vector search
  python debug/tools/cli.py test-tool --tool bigquery --query "What is LangSwarm?"
  
  # Test SQL database query
  python debug/tools/cli.py test-tool --tool sql --query "SELECT * FROM employees LIMIT 5"
  
  # Test workflow
  python debug/tools/cli.py test-workflow --workflow single_tool_test --query "Find information about AI"
  
  # Health check all tools
  python debug/tools/cli.py health-check
  
  # Interactive mode
  python debug/tools/cli.py interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test tool command
    test_tool_parser = subparsers.add_parser('test-tool', help='Test a single tool')
    test_tool_parser.add_argument('--tool', '-t', required=True, choices=['bigquery', 'sql'], help='Tool to test')
    test_tool_parser.add_argument('--query', '-q', help='Query to execute (optional - will prompt if not provided)')
    test_tool_parser.add_argument('--method', '-m', default='search', help='Tool method to call')
    
    # Test workflow command
    test_workflow_parser = subparsers.add_parser('test-workflow', help='Test a workflow')
    test_workflow_parser.add_argument('--workflow', '-w', required=True, help='Workflow ID to test')
    test_workflow_parser.add_argument('--query', '-q', required=True, help='Input query for workflow')
    
    # Health check command
    subparsers.add_parser('health-check', help='Check health of all tools')
    
    # Interactive mode command
    subparsers.add_parser('interactive', help='Run in interactive mode')
    
    # Global options
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--trace', '-tr', action='store_true', default=True, help='Enable tracing (default: True)')
    parser.add_argument('--no-trace', action='store_true', help='Disable tracing')
    
    args = parser.parse_args()
    
    # Handle trace flags
    if args.no_trace:
        args.trace = False
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run CLI
    cli = DebugToolsCLI()
    return asyncio.run(cli.run(args))


if __name__ == "__main__":
    sys.exit(main())
