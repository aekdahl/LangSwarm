#!/usr/bin/env python3
"""
LangSwarm Interactive Workflow Runner
=====================================

An interactive command-line tool that lets users:
1. Browse and select available workflows
2. Enter custom queries/inputs
3. Execute workflows with real-time feedback
4. Debug and trace workflow execution
5. Generate new workflows using AI

Usage:
    python scripts/interactive_workflow_runner.py
    python scripts/interactive_workflow_runner.py --debug
    python scripts/interactive_workflow_runner.py --create
    python scripts/interactive_workflow_runner.py --list-only
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import glob
from datetime import datetime

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def load_environment_variables():
    """Load environment variables from .env file if available"""
    env_file = project_root / ".env"
    
    if env_file.exists():
        if DOTENV_AVAILABLE:
            load_dotenv(env_file)
            print(f"{Colors.GREEN}✅ Loaded environment variables from .env file{Colors.NC}")
            
            # Check if OPENAI_API_KEY is now available
            if os.getenv('OPENAI_API_KEY'):
                api_key = os.getenv('OPENAI_API_KEY')
                masked_key = f"...{api_key[-8:]}" if len(api_key) > 8 else "***"
                print(f"{Colors.CYAN}🔑 OPENAI_API_KEY found: {masked_key}{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}⚠️  OPENAI_API_KEY not found in .env file{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠️  .env file found but python-dotenv not installed{Colors.NC}")
            print(f"{Colors.CYAN}💡 Install with: pip install python-dotenv{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠️  No .env file found at {env_file}{Colors.NC}")
        
        # Check if OPENAI_API_KEY is already in environment
        if os.getenv('OPENAI_API_KEY'):
            api_key = os.getenv('OPENAI_API_KEY')
            masked_key = f"...{api_key[-8:]}" if len(api_key) > 8 else "***"
            print(f"{Colors.CYAN}🔑 OPENAI_API_KEY found in environment: {masked_key}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ OPENAI_API_KEY not found in environment{Colors.NC}")
            print(f"{Colors.CYAN}💡 Either create a .env file or set the environment variable{Colors.NC}")

# Load environment variables early
load_environment_variables()

try:
    from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
    from langswarm.core.debug import enable_debug_tracing
    from langswarm.mcp.tools.workflow_executor.main import WorkflowGenerator, execute_generated_workflow
except ImportError as e:
    print(f"❌ Error importing LangSwarm modules: {e}")
    print("💡 Make sure you've installed LangSwarm: pip install -e .")
    sys.exit(1)


class WorkflowDiscovery:
    """Discovers and catalogs available workflows"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.workflows = {}
        self.discover_workflows()
    
    def discover_workflows(self):
        """Discover all available workflows in the debug test configs directory"""
        print(f"{Colors.CYAN}🔍 Discovering workflows in debug test configs...{Colors.NC}")
        
        # Search only in the debug test configs directory
        debug_configs_dir = self.project_root / "langswarm/core/debug/test_configs"
        search_patterns = [
            "*.yaml",
            "*.yml"
        ]
        
        workflow_files = []
        for pattern in search_patterns:
            matches = glob.glob(str(debug_configs_dir / pattern), recursive=False)
            workflow_files.extend(matches)
        
        # Parse each file for workflows
        for file_path in workflow_files:
            try:
                self._parse_workflow_file(file_path)
            except Exception as e:
                # Silently skip files that can't be parsed as workflows
                continue
        
        print(f"{Colors.GREEN}✅ Found {len(self.workflows)} workflows{Colors.NC}")
    
    def _parse_workflow_file(self, file_path: str):
        """Parse a YAML file for workflow definitions"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, dict):
                return
            
            # Check if this file contains workflows
            if 'workflows' in data:
                workflows_data = data['workflows']
                
                # Handle different workflow formats
                if isinstance(workflows_data, dict):
                    # Format: workflows: { workflow_id: {...} }
                    for workflow_id, workflow_config in workflows_data.items():
                        self._add_workflow(file_path, workflow_id, workflow_config, data)
                elif isinstance(workflows_data, list):
                    # Format: workflows: [{ id: workflow_id, ... }]
                    for workflow_config in workflows_data:
                        if isinstance(workflow_config, dict) and 'id' in workflow_config:
                            workflow_id = workflow_config['id']
                            self._add_workflow(file_path, workflow_id, workflow_config, data)
                            
        except Exception as e:
            # Skip files that can't be parsed
            pass
    
    def _add_workflow(self, file_path: str, workflow_id: str, workflow_config: Any, full_config: dict):
        """Add a discovered workflow to the catalog"""
        # Create a unique key for the workflow
        file_name = Path(file_path).stem
        unique_key = f"{file_name}::{workflow_id}"
        
        # Extract description
        description = ""
        if isinstance(workflow_config, dict):
            description = workflow_config.get('description', '')
            if 'name' in workflow_config:
                description = workflow_config['name']
        
        # Determine workflow type based on structure
        workflow_type = self._determine_workflow_type(workflow_config)
        
        self.workflows[unique_key] = {
            'id': workflow_id,
            'file_path': file_path,
            'description': description,
            'type': workflow_type,
            'config': workflow_config,
            'full_config': full_config
        }
    
    def _determine_workflow_type(self, workflow_config: Any) -> str:
        """Determine the type of workflow based on its structure"""
        if not isinstance(workflow_config, dict):
            return "unknown"
        
        if 'steps' in workflow_config:
            steps = workflow_config['steps']
            if isinstance(steps, list) and len(steps) > 0:
                # Check what kind of steps it has
                first_step = steps[0]
                if isinstance(first_step, dict):
                    if 'agent' in first_step:
                        return "agent-based"
                    elif 'function' in first_step:
                        return "function-based"
                    elif 'tool' in first_step:
                        return "tool-based"
        
        return "workflow"
    
    def get_workflows_by_category(self) -> Dict[str, List[Dict]]:
        """Group workflows by category/type"""
        categories = {
            'Agent-Based Workflows': [],
            'Tool-Based Workflows': [],
            'Function-Based Workflows': [],
            'BigQuery Workflows': [],
            'Filesystem Workflows': [],
            'Memory Workflows': [],
            'Other Workflows': []
        }
        
        for key, workflow in self.workflows.items():
            # Categorize based on file path and content
            file_path = workflow['file_path'].lower()
            workflow_type = workflow['type']
            
            if 'bigquery' in file_path or 'bigquery' in workflow['id'].lower():
                categories['BigQuery Workflows'].append((key, workflow))
            elif 'filesystem' in file_path or 'filesystem' in workflow['id'].lower():
                categories['Filesystem Workflows'].append((key, workflow))
            elif 'memory' in file_path or 'memory' in workflow['id'].lower():
                categories['Memory Workflows'].append((key, workflow))
            elif workflow_type == 'agent-based':
                categories['Agent-Based Workflows'].append((key, workflow))
            elif workflow_type == 'tool-based':
                categories['Tool-Based Workflows'].append((key, workflow))
            elif workflow_type == 'function-based':
                categories['Function-Based Workflows'].append((key, workflow))
            else:
                categories['Other Workflows'].append((key, workflow))
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


class InteractiveWorkflowRunner:
    """Main interactive workflow runner class"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.project_root = Path(__file__).parent.parent
        self.discovery = WorkflowDiscovery(self.project_root)
        
        if debug_mode:
            # Enable debug tracing
            trace_file = f"debug_traces/interactive_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            enable_debug_tracing(trace_file)
            print(f"{Colors.YELLOW}🐛 Debug mode enabled. Traces will be saved to: {trace_file}{Colors.NC}")
    
    def run(self):
        """Main interactive loop"""
        self.print_welcome()
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == '1':
                    self.select_and_run_workflow()
                elif choice == '2':
                    self.create_workflow()
                elif choice == '3':
                    self.list_workflows()
                elif choice == '4':
                    self.run_preset_workflow()
                elif choice == '5':
                    self.show_workflow_details()
                elif choice == 'q':
                    print(f"\n{Colors.CYAN}👋 Thank you for using LangSwarm!{Colors.NC}")
                    break
                else:
                    print(f"{Colors.RED}❌ Invalid choice. Please try again.{Colors.NC}")
                    
            except KeyboardInterrupt:
                print(f"\n\n{Colors.CYAN}👋 Goodbye!{Colors.NC}")
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
                if self.debug_mode:
                    import traceback
                    traceback.print_exc()
    
    def print_welcome(self):
        """Print welcome message"""
        print(f"""
{Colors.CYAN}🚀 LangSwarm Interactive Workflow Runner{Colors.NC}
{'='*50}

Welcome! This tool helps you discover, select, and run LangSwarm workflows.
Found {Colors.GREEN}{len(self.discovery.workflows)}{Colors.NC} available workflows.

""")
    
    def show_main_menu(self) -> str:
        """Show main menu and get user choice"""
        print(f"{Colors.BOLD}Main Menu:{Colors.NC}")
        print(f"  {Colors.GREEN}1{Colors.NC} - 🎯 Select and run a workflow")
        print(f"  {Colors.GREEN}2{Colors.NC} - ✨ Create a new workflow (AI-powered)")
        print(f"  {Colors.GREEN}3{Colors.NC} - 📋 List all available workflows")
        print(f"  {Colors.GREEN}4{Colors.NC} - ⚡ Run a preset workflow")
        print(f"  {Colors.GREEN}5{Colors.NC} - 🔍 View workflow details")
        print(f"  {Colors.YELLOW}q{Colors.NC} - 🚪 Quit")
        print()
        
        return input(f"{Colors.CYAN}Choose an option (1-5, q): {Colors.NC}").strip().lower()
    
    def list_workflows(self):
        """List all available workflows by category"""
        print(f"\n{Colors.CYAN}📋 Available Workflows{Colors.NC}")
        print("="*50)
        
        categories = self.discovery.get_workflows_by_category()
        
        for category, workflows in categories.items():
            if workflows:
                print(f"\n{Colors.YELLOW}{category}:{Colors.NC}")
                for i, (key, workflow) in enumerate(workflows, 1):
                    file_name = Path(workflow['file_path']).name
                    desc = workflow['description'][:60] + "..." if len(workflow['description']) > 60 else workflow['description']
                    print(f"  {Colors.GREEN}{i:2d}.{Colors.NC} {workflow['id']} {Colors.MAGENTA}({file_name}){Colors.NC}")
                    if desc:
                        print(f"      {Colors.WHITE}{desc}{Colors.NC}")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")
    
    def select_and_run_workflow(self):
        """Interactive workflow selection and execution"""
        print(f"\n{Colors.CYAN}🎯 Select a Workflow to Run{Colors.NC}")
        print("="*40)
        
        # Group workflows by category
        categories = self.discovery.get_workflows_by_category()
        
        # Create a flat list for selection
        workflow_list = []
        for category, workflows in categories.items():
            if workflows:
                workflow_list.extend(workflows)
        
        if not workflow_list:
            print(f"{Colors.RED}❌ No workflows found!{Colors.NC}")
            return
        
        # Display workflows with numbers
        print()
        for i, (key, workflow) in enumerate(workflow_list, 1):
            file_name = Path(workflow['file_path']).name
            desc = workflow['description'][:60] + "..." if len(workflow['description']) > 60 else workflow['description']
            print(f"{Colors.GREEN}{i:2d}.{Colors.NC} {workflow['id']} {Colors.MAGENTA}({file_name}){Colors.NC}")
            if desc:
                print(f"    {Colors.WHITE}{desc}{Colors.NC}")
        
        print()
        
        # Get user selection
        try:
            choice = input(f"{Colors.CYAN}Select workflow number (1-{len(workflow_list)}): {Colors.NC}").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(workflow_list):
                selected_key, selected_workflow = workflow_list[choice_idx]
                self.run_selected_workflow(selected_workflow)
            else:
                print(f"{Colors.RED}❌ Invalid selection!{Colors.NC}")
                
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid number!{Colors.NC}")
    
    def run_selected_workflow(self, workflow: Dict):
        """Run the selected workflow with user input"""
        print(f"\n{Colors.CYAN}🚀 Running Workflow: {workflow['id']}{Colors.NC}")
        print("="*50)
        
        if workflow['description']:
            print(f"{Colors.WHITE}Description: {workflow['description']}{Colors.NC}")
        
        print(f"{Colors.MAGENTA}File: {workflow['file_path']}{Colors.NC}")
        print()
        
        # Get user input/query
        print(f"{Colors.YELLOW}Enter your query or input for this workflow:{Colors.NC}")
        print(f"{Colors.WHITE}(This will be passed as the user_input to the workflow){Colors.NC}")
        user_query = input(f"{Colors.CYAN}Your query: {Colors.NC}").strip()
        
        if not user_query:
            print(f"{Colors.RED}❌ No input provided!{Colors.NC}")
            return
        
        print(f"\n{Colors.YELLOW}🔄 Executing workflow...{Colors.NC}")
        
        try:
            # Load and execute the workflow
            config_path = workflow['file_path']
            
            # Use LangSwarm's config loader
            loader = LangSwarmConfigLoader(config_path)
            workflows, agents, brokers, tools, metadata = loader.load()
            
            # Create workflow executor
            executor = WorkflowExecutor(workflows, agents, tools=tools)
            
            # Execute the specific workflow
            result = executor.run_workflow(
                workflow_id=workflow['id'],
                user_input=user_query
            )
            
            print(f"\n{Colors.GREEN}✅ Workflow completed successfully!{Colors.NC}")
            print(f"{Colors.CYAN}Result:{Colors.NC}")
            print(f"{Colors.WHITE}{result}{Colors.NC}")
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ Error executing workflow: {e}{Colors.NC}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")
    
    def create_workflow(self):
        """AI-powered workflow creation"""
        print(f"\n{Colors.CYAN}✨ AI-Powered Workflow Creator{Colors.NC}")
        print("="*40)
        
        print(f"{Colors.WHITE}Describe the workflow you want to create.{Colors.NC}")
        print(f"{Colors.WHITE}Example: 'Analyze a text file and generate a summary report'{Colors.NC}")
        print()
        
        description = input(f"{Colors.CYAN}Workflow description: {Colors.NC}").strip()
        
        if not description:
            print(f"{Colors.RED}❌ No description provided!{Colors.NC}")
            return
        
        # Get workflow name
        workflow_name = input(f"{Colors.CYAN}Workflow name (optional): {Colors.NC}").strip()
        if not workflow_name:
            workflow_name = f"generated_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n{Colors.YELLOW}🔄 Generating workflow...{Colors.NC}")
        
        try:
            # Use the workflow generator
            generator = WorkflowGenerator()
            result = generator.generate_workflow(
                workflow_description=description,
                workflow_name=workflow_name,
                complexity="medium"
            )
            
            print(f"\n{Colors.GREEN}✅ Workflow generated successfully!{Colors.NC}")
            print(f"{Colors.CYAN}Generated workflow: {result['workflow_name']}{Colors.NC}")
            
            # Ask if user wants to save and run the workflow
            save_choice = input(f"\n{Colors.CYAN}Save and run this workflow? (y/n): {Colors.NC}").strip().lower()
            
            if save_choice == 'y':
                # Save workflow to file
                output_file = f"generated_workflows/{workflow_name}.yaml"
                os.makedirs("generated_workflows", exist_ok=True)
                
                with open(output_file, 'w') as f:
                    yaml.dump(result['workflow_config'], f, default_flow_style=False, indent=2)
                
                print(f"{Colors.GREEN}💾 Workflow saved to: {output_file}{Colors.NC}")
                
                # Get input for execution
                user_input = input(f"{Colors.CYAN}Enter input for workflow execution: {Colors.NC}").strip()
                
                if user_input:
                    print(f"\n{Colors.YELLOW}🚀 Executing generated workflow...{Colors.NC}")
                    
                    exec_result = execute_generated_workflow(
                        workflow_description=description,
                        input_data={"user_input": user_input},
                        execution_mode="sync"
                    )
                    
                    print(f"\n{Colors.GREEN}✅ Generated workflow executed!{Colors.NC}")
                    print(f"{Colors.CYAN}Result:{Colors.NC}")
                    print(f"{Colors.WHITE}{exec_result.get('result', 'No result returned')}{Colors.NC}")
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ Error creating workflow: {e}{Colors.NC}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")
    
    def run_preset_workflow(self):
        """Run preset workflows for common use cases"""
        print(f"\n{Colors.CYAN}⚡ Preset Workflows{Colors.NC}")
        print("="*30)
        
        presets = {
            '1': ('BigQuery Analysis', 'bigquery'),
            '2': ('Filesystem Operations', 'filesystem'), 
            '3': ('Memory Demo', 'memory'),
            '4': ('Workflow Executor', 'workflow_executor')
        }
        
        print()
        for key, (name, _) in presets.items():
            print(f"{Colors.GREEN}{key}.{Colors.NC} {name}")
        
        choice = input(f"\n{Colors.CYAN}Select preset (1-{len(presets)}): {Colors.NC}").strip()
        
        if choice in presets:
            preset_name, preset_type = presets[choice]
            print(f"\n{Colors.YELLOW}🔄 Running {preset_name} preset...{Colors.NC}")
            
            # Find workflows matching the preset type
            matching_workflows = []
            for key, workflow in self.discovery.workflows.items():
                if preset_type.lower() in workflow['file_path'].lower() or preset_type.lower() in workflow['id'].lower():
                    matching_workflows.append((key, workflow))
            
            if matching_workflows:
                # Use the first matching workflow
                _, workflow = matching_workflows[0]
                user_query = input(f"{Colors.CYAN}Enter your query for {preset_name}: {Colors.NC}").strip()
                if user_query:
                    self.run_selected_workflow(workflow)
            else:
                print(f"{Colors.RED}❌ No {preset_name} workflows found!{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Invalid preset selection!{Colors.NC}")
    
    def show_workflow_details(self):
        """Show detailed information about a workflow"""
        print(f"\n{Colors.CYAN}🔍 Workflow Details{Colors.NC}")
        print("="*30)
        
        # Show abbreviated workflow list
        workflow_list = list(self.discovery.workflows.items())
        
        print()
        for i, (key, workflow) in enumerate(workflow_list[:10], 1):  # Show first 10
            print(f"{Colors.GREEN}{i:2d}.{Colors.NC} {workflow['id']}")
        
        if len(workflow_list) > 10:
            print(f"    ... and {len(workflow_list) - 10} more")
        
        try:
            choice = input(f"\n{Colors.CYAN}Select workflow number (1-{min(10, len(workflow_list))}): {Colors.NC}").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(workflow_list):
                _, workflow = workflow_list[choice_idx]
                self.display_workflow_details(workflow)
            else:
                print(f"{Colors.RED}❌ Invalid selection!{Colors.NC}")
                
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid number!{Colors.NC}")
    
    def display_workflow_details(self, workflow: Dict):
        """Display detailed workflow information"""
        print(f"\n{Colors.CYAN}📋 Workflow Details{Colors.NC}")
        print("="*50)
        
        print(f"{Colors.YELLOW}ID:{Colors.NC} {workflow['id']}")
        print(f"{Colors.YELLOW}File:{Colors.NC} {workflow['file_path']}")
        print(f"{Colors.YELLOW}Type:{Colors.NC} {workflow['type']}")
        
        if workflow['description']:
            print(f"{Colors.YELLOW}Description:{Colors.NC} {workflow['description']}")
        
        # Show workflow structure
        config = workflow.get('config', {})
        if isinstance(config, dict) and 'steps' in config:
            steps = config['steps']
            print(f"\n{Colors.YELLOW}Steps ({len(steps)}):{Colors.NC}")
            for i, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    step_id = step.get('id', f'step_{i}')
                    step_type = 'agent' if 'agent' in step else 'function' if 'function' in step else 'unknown'
                    print(f"  {Colors.GREEN}{i}.{Colors.NC} {step_id} ({step_type})")
        
        # Show agents if available
        full_config = workflow.get('full_config', {})
        if 'agents' in full_config:
            agents = full_config['agents']
            if agents:
                print(f"\n{Colors.YELLOW}Agents:{Colors.NC}")
                if isinstance(agents, list):
                    for agent in agents:
                        if isinstance(agent, dict) and 'id' in agent:
                            print(f"  • {agent['id']}")
                elif isinstance(agents, dict):
                    for agent_id in agents.keys():
                        print(f"  • {agent_id}")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LangSwarm Interactive Workflow Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode with tracing'
    )
    
    parser.add_argument(
        '--list-only', '-l',
        action='store_true',
        help='List workflows and exit'
    )
    
    parser.add_argument(
        '--create', '-c',
        action='store_true',
        help='Go directly to workflow creation'
    )
    
    parser.add_argument(
        '--preset', '-p',
        type=str,
        help='Run a specific preset workflow type'
    )
    
    args = parser.parse_args()
    
    try:
        runner = InteractiveWorkflowRunner(debug_mode=args.debug)
        
        if args.list_only:
            runner.list_workflows()
        elif args.create:
            runner.create_workflow()
        elif args.preset:
            # Handle preset workflow selection
            print(f"{Colors.CYAN}🎯 Running {args.preset} preset workflow{Colors.NC}")
            # Implementation for preset workflows would go here
        else:
            runner.run()
            
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Fatal error: {e}{Colors.NC}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
