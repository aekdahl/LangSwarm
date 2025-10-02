#!/usr/bin/env python3
"""
LangSwarm Debug & Test System
============================

A comprehensive system for testing and debugging LangSwarm with real data and real scenarios.
This system focuses on end-to-end testing with actual API calls and real configurations.

Features:
- Real API key management and validation
- Interactive credential setup
- Real BigQuery testing with actual data
- V2 system validation with live services
- Configuration testing with real environments
- Debug tracing for actual workflow execution

Usage:
    python scripts/langswarm_debug.py --help
    python scripts/langswarm_debug.py setup
    python scripts/langswarm_debug.py test bigquery --query "your search query"
    python scripts/langswarm_debug.py validate config
    python scripts/langswarm_debug.py debug workflow --id your_workflow
"""

import argparse
import asyncio
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

class CredentialManager:
    """Manages API keys and credentials for real testing"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.env_file = project_root / '.env'
        self.credentials_template = project_root / 'scripts' / 'credentials_template.env'
        
    def check_and_setup_credentials(self) -> bool:
        """Check for credentials and guide user through setup if missing"""
        
        print(f"{Colors.CYAN}🔐 Checking Credentials for Real Testing{Colors.NC}")
        print("=" * 50)
        
        # Check if .env file exists
        if not self.env_file.exists():
            print(f"{Colors.YELLOW}⚠️  No .env file found{Colors.NC}")
            return self.guide_credential_setup()
        
        # Load existing .env and check for required credentials
        missing_creds = self.check_required_credentials()
        
        if missing_creds:
            print(f"{Colors.YELLOW}⚠️  Missing required credentials: {', '.join(missing_creds)}{Colors.NC}")
            return self.prompt_for_missing_credentials(missing_creds)
        
        print(f"{Colors.GREEN}✅ All required credentials found{Colors.NC}")
        return True
    
    def check_required_credentials(self) -> List[str]:
        """Check which required credentials are missing"""
        
        required_creds = {
            'OPENAI_API_KEY': 'OpenAI API key for LLM operations',
            'GOOGLE_CLOUD_PROJECT': 'Google Cloud Project ID for BigQuery',
        }
        
        # Load environment variables from .env file
        self.load_env_file()
        
        missing = []
        for key, description in required_creds.items():
            value = os.getenv(key)
            if not value or value.startswith('your_') or value.startswith('sk-xxx'):
                missing.append(key)
            else:
                # Mask the key for display
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"   ✅ {key}: {masked}")
        
        return missing
    
    def load_env_file(self):
        """Load environment variables from .env file"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def guide_credential_setup(self) -> bool:
        """Guide user through initial credential setup"""
        
        print(f"\n{Colors.CYAN}📝 Setting up credentials for real testing{Colors.NC}")
        print(f"{Colors.WHITE}This system requires real API keys for testing actual functionality.{Colors.NC}")
        print()
        
        # Create credentials template if it doesn't exist
        self.create_credentials_template()
        
        print(f"I've created a credentials template at: {Colors.YELLOW}{self.credentials_template}{Colors.NC}")
        print()
        print(f"{Colors.CYAN}Please follow these steps:{Colors.NC}")
        print(f"1. Copy the template to .env: cp {self.credentials_template} .env")
        print(f"2. Edit .env and add your real API keys")
        print(f"3. Run this script again")
        print()
        
        # Ask if they want to proceed with interactive setup
        response = input(f"{Colors.CYAN}Would you like to set up credentials interactively now? (y/n): {Colors.NC}").strip().lower()
        
        if response == 'y':
            return self.interactive_credential_setup()
        else:
            print(f"{Colors.YELLOW}Please set up credentials manually and run again.{Colors.NC}")
            return False
    
    def interactive_credential_setup(self) -> bool:
        """Interactive credential setup"""
        
        print(f"\n{Colors.CYAN}🔧 Interactive Credential Setup{Colors.NC}")
        print("=" * 40)
        
        credentials = {}
        
        # OpenAI API Key
        print(f"\n{Colors.YELLOW}OpenAI API Key{Colors.NC}")
        print("Required for: LLM operations, embeddings, chat completions")
        print("Get yours at: https://platform.openai.com/api-keys")
        openai_key = input(f"{Colors.CYAN}Enter your OpenAI API key (sk-...): {Colors.NC}").strip()
        
        if openai_key and openai_key.startswith('sk-'):
            credentials['OPENAI_API_KEY'] = openai_key
            print(f"{Colors.GREEN}✅ OpenAI API key added{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Invalid OpenAI API key format{Colors.NC}")
        
        # Google Cloud Project ID
        print(f"\n{Colors.YELLOW}Google Cloud Project ID{Colors.NC}")
        print("Required for: BigQuery vector search, Google Cloud services")
        print("Find yours at: https://console.cloud.google.com/")
        project_id = input(f"{Colors.CYAN}Enter your Google Cloud Project ID: {Colors.NC}").strip()
        
        if project_id:
            credentials['GOOGLE_CLOUD_PROJECT'] = project_id
            print(f"{Colors.GREEN}✅ Google Cloud Project ID added{Colors.NC}")
        
        # BigQuery Dataset (optional)
        print(f"\n{Colors.YELLOW}BigQuery Dataset ID (optional){Colors.NC}")
        print("Default: vector_search")
        dataset_id = input(f"{Colors.CYAN}Enter BigQuery Dataset ID [vector_search]: {Colors.NC}").strip()
        if dataset_id:
            credentials['BIGQUERY_DATASET_ID'] = dataset_id
        else:
            credentials['BIGQUERY_DATASET_ID'] = 'vector_search'
        
        # Save credentials
        if credentials:
            self.save_credentials(credentials)
            print(f"\n{Colors.GREEN}✅ Credentials saved to .env{Colors.NC}")
            return True
        else:
            print(f"\n{Colors.RED}❌ No valid credentials provided{Colors.NC}")
            return False
    
    def save_credentials(self, credentials: Dict[str, str]):
        """Save credentials to .env file"""
        
        # Load existing .env content if it exists
        existing_content = []
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                existing_content = f.readlines()
        
        # Remove existing entries for the credentials we're updating
        filtered_content = []
        for line in existing_content:
            if not any(line.startswith(f"{key}=") for key in credentials.keys()):
                filtered_content.append(line)
        
        # Add new credentials
        with open(self.env_file, 'w') as f:
            f.writelines(filtered_content)
            f.write("\n# Credentials added by LangSwarm debug system\n")
            for key, value in credentials.items():
                f.write(f"{key}={value}\n")
    
    def create_credentials_template(self):
        """Create a credentials template file"""
        
        template_content = """# LangSwarm Credentials Template
# Copy this file to .env and fill in your real API keys and credentials

# ============================================================================
# REQUIRED CREDENTIALS
# ============================================================================

# OpenAI API Key (Required)
# Get yours at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud Project ID (Required for BigQuery)
# Find yours at: https://console.cloud.google.com/
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id

# ============================================================================
# OPTIONAL CREDENTIALS
# ============================================================================

# Anthropic API Key (Optional - for Claude models)
# Get yours at: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Cloud Service Account (Optional - for authentication)
# Download from: https://console.cloud.google.com/iam-admin/serviceaccounts
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json

# ============================================================================
# CONFIGURATION SETTINGS
# ============================================================================

# BigQuery Configuration
BIGQUERY_DATASET_ID=vector_search
BIGQUERY_TABLE_NAME=embeddings
BIGQUERY_LOCATION=US

# Environment Settings
LANGSWARM_ENV=development
LANGSWARM_USE_V2_AGENTS=true
LANGSWARM_USE_V2_CONFIG=true
LANGSWARM_USE_V2_TOOLS=true

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_OUTPUT_DIR=debug_traces

# ============================================================================
# SECURITY NOTE
# ============================================================================
# Never commit the .env file with real credentials to version control!
# Add .env to your .gitignore file.
"""
        
        with open(self.credentials_template, 'w') as f:
            f.write(template_content)
    
    def prompt_for_missing_credentials(self, missing_creds: List[str]) -> bool:
        """Prompt user to add missing credentials"""
        
        print(f"\n{Colors.CYAN}Missing Credentials{Colors.NC}")
        print("=" * 30)
        
        for cred in missing_creds:
            print(f"❌ {cred}")
        
        print(f"\n{Colors.CYAN}Options:{Colors.NC}")
        print(f"1. Add credentials interactively now")
        print(f"2. Edit .env file manually")
        print(f"3. Exit and set up later")
        
        choice = input(f"\n{Colors.CYAN}Choose an option (1-3): {Colors.NC}").strip()
        
        if choice == '1':
            return self.add_missing_credentials_interactively(missing_creds)
        elif choice == '2':
            print(f"\n{Colors.YELLOW}Please edit {self.env_file} and add the missing credentials.{Colors.NC}")
            print(f"Run this script again when ready.")
            return False
        else:
            print(f"{Colors.YELLOW}Exiting. Please set up credentials and try again.{Colors.NC}")
            return False
    
    def add_missing_credentials_interactively(self, missing_creds: List[str]) -> bool:
        """Add missing credentials interactively"""
        
        credentials = {}
        
        for cred in missing_creds:
            if cred == 'OPENAI_API_KEY':
                print(f"\n{Colors.YELLOW}OpenAI API Key{Colors.NC}")
                print("Get yours at: https://platform.openai.com/api-keys")
                value = input(f"{Colors.CYAN}Enter your OpenAI API key (sk-...): {Colors.NC}").strip()
                if value and value.startswith('sk-'):
                    credentials[cred] = value
                    
            elif cred == 'GOOGLE_CLOUD_PROJECT':
                print(f"\n{Colors.YELLOW}Google Cloud Project ID{Colors.NC}")
                print("Find yours at: https://console.cloud.google.com/")
                value = input(f"{Colors.CYAN}Enter your Google Cloud Project ID: {Colors.NC}").strip()
                if value:
                    credentials[cred] = value
        
        if credentials:
            self.save_credentials(credentials)
            print(f"\n{Colors.GREEN}✅ Credentials added{Colors.NC}")
            return True
        else:
            print(f"\n{Colors.RED}❌ No valid credentials provided{Colors.NC}")
            return False
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate that credentials work with actual services"""
        
        print(f"\n{Colors.CYAN}🔍 Validating Credentials{Colors.NC}")
        print("=" * 30)
        
        results = {}
        
        # Validate OpenAI API Key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            print(f"Testing OpenAI API key...")
            results['openai'] = self.test_openai_key(openai_key)
        
        # Validate Google Cloud access
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if project_id:
            print(f"Testing Google Cloud access...")
            results['google_cloud'] = self.test_google_cloud_access(project_id)
        
        return results
    
    def test_openai_key(self, api_key: str) -> bool:
        """Test OpenAI API key with a simple request"""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            print(f"   ✅ OpenAI API key valid")
            return True
            
        except Exception as e:
            print(f"   ❌ OpenAI API key invalid: {str(e)[:100]}...")
            return False
    
    def test_google_cloud_access(self, project_id: str) -> bool:
        """Test Google Cloud access"""
        try:
            from google.cloud import bigquery
            
            client = bigquery.Client(project=project_id)
            
            # Test by listing datasets (this requires basic access)
            datasets = list(client.list_datasets(max_results=1))
            
            print(f"   ✅ Google Cloud access valid")
            return True
            
        except Exception as e:
            print(f"   ❌ Google Cloud access invalid: {str(e)[:100]}...")
            print(f"   💡 Try: gcloud auth application-default login")
            return False

class RealDataTester:
    """Tests LangSwarm with real data and real API calls"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    async def test_bigquery_real(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Test real BigQuery vector search"""
        
        print(f"{Colors.CYAN}🗄️  Testing Real BigQuery Vector Search{Colors.NC}")
        print("=" * 40)
        
        print(f"Query: '{query}'")
        print(f"Max Results: {max_results}")
        print(f"Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        print(f"Dataset: {os.getenv('BIGQUERY_DATASET_ID', 'vector_search')}")
        print(f"Table: {os.getenv('BIGQUERY_TABLE_NAME', 'embeddings')}")
        
        try:
            # Test actual BigQuery connection
            from google.cloud import bigquery
            
            client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
            
            # Check if dataset exists
            dataset_id = os.getenv('BIGQUERY_DATASET_ID', 'vector_search')
            table_name = os.getenv('BIGQUERY_TABLE_NAME', 'embeddings')
            
            dataset_ref = client.dataset(dataset_id)
            table_ref = dataset_ref.table(table_name)
            
            # Check table exists
            try:
                table = client.get_table(table_ref)
                print(f"✅ Table found: {table.num_rows} rows")
            except Exception as e:
                print(f"❌ Table not found: {e}")
                return self.create_bigquery_setup_guide()
            
            # If we have a real MCP tool, use it
            try:
                result = await self.execute_bigquery_search(query, max_results)
                return result
            except Exception as e:
                print(f"⚠️  MCP tool not available, testing basic query: {e}")
                return await self.test_basic_bigquery_query(client, table_ref, query)
                
        except Exception as e:
            print(f"❌ BigQuery test failed: {e}")
            return {"error": str(e), "suggestions": self.get_bigquery_troubleshooting()}
    
    async def execute_bigquery_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Execute BigQuery search using MCP tool"""
        
        # Try to use the actual MCP BigQuery tool
        try:
            from langswarm.tools.mcp.bigquery_vector_search import main as bigquery_tool
            
            # Execute the search
            result = await bigquery_tool.similarity_search(
                query=query,
                max_results=max_results
            )
            
            print(f"✅ BigQuery vector search completed")
            print(f"Found: {len(result.get('results', []))} results")
            
            return result
            
        except ImportError:
            raise Exception("BigQuery MCP tool not available")
        except Exception as e:
            raise Exception(f"BigQuery search failed: {e}")
    
    async def test_basic_bigquery_query(self, client, table_ref, query: str) -> Dict[str, Any]:
        """Test basic BigQuery connectivity with a simple query"""
        
        try:
            # Simple query to test connectivity
            query_job = client.query(f"""
                SELECT *
                FROM `{table_ref.dataset_id}.{table_ref.table_id}`
                LIMIT 5
            """)
            
            results = list(query_job.result())
            
            print(f"✅ Basic BigQuery query successful")
            print(f"Sample rows: {len(results)}")
            
            return {
                "status": "basic_query_success",
                "sample_rows": len(results),
                "table_info": {
                    "project": table_ref.project,
                    "dataset": table_ref.dataset_id,
                    "table": table_ref.table_id
                }
            }
            
        except Exception as e:
            raise Exception(f"Basic query failed: {e}")
    
    def create_bigquery_setup_guide(self) -> Dict[str, Any]:
        """Create setup guide for BigQuery"""
        
        return {
            "status": "setup_required",
            "message": "BigQuery table not found",
            "setup_steps": [
                "1. Create a BigQuery dataset",
                "2. Create a table for vector embeddings",
                "3. Upload your document embeddings",
                "4. Configure BIGQUERY_DATASET_ID and BIGQUERY_TABLE_NAME",
                "5. Run the test again"
            ],
            "sql_example": """
            CREATE TABLE `your-project.vector_search.embeddings` (
                id STRING,
                text STRING,
                embedding ARRAY<FLOAT64>,
                metadata JSON
            )
            """
        }
    
    def get_bigquery_troubleshooting(self) -> List[str]:
        """Get BigQuery troubleshooting suggestions"""
        
        return [
            "Check Google Cloud authentication: gcloud auth application-default login",
            "Verify project ID is correct",
            "Ensure BigQuery API is enabled in your project",
            "Check dataset and table exist",
            "Verify service account has BigQuery permissions"
        ]
    
    async def test_v2_system_real(self) -> Dict[str, bool]:
        """Test V2 system with real components"""
        
        print(f"{Colors.CYAN}🧪 Testing V2 System (Real Components){Colors.NC}")
        print("=" * 40)
        
        results = {}
        
        # Test V2 tool discovery with real tools
        try:
            from langswarm.tools import auto_discover_tools, get_global_registry
            
            discovered = auto_discover_tools()
            registry = get_global_registry()
            
            print(f"✅ V2 Tools: {discovered} discovered")
            results['v2_tools'] = True
            
        except Exception as e:
            print(f"❌ V2 Tools failed: {e}")
            results['v2_tools'] = False
        
        # Test V2 agent creation with real providers
        try:
            from langswarm.core import get_version_info
            
            version_info = get_version_info()
            v2_available = version_info.get('v2_available', False)
            
            print(f"✅ V2 Available: {v2_available}")
            results['v2_available'] = v2_available
            
        except Exception as e:
            print(f"❌ V2 Version check failed: {e}")
            results['v2_available'] = False
        
        # Test configuration loading
        try:
            import yaml
            
            config_path = self.project_root / "langswarm/v2/test_configs/bigquery_v2_test.yaml"
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            print(f"✅ V2 Config: {config.get('project_name', 'Unknown')}")
            results['v2_config'] = True
            
        except Exception as e:
            print(f"❌ V2 Config failed: {e}")
            results['v2_config'] = False
        
        return results

class WorkflowDebugger:
    """Debug real workflow execution"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    async def debug_workflow(self, workflow_id: str, user_input: str) -> Dict[str, Any]:
        """Debug a real workflow execution with tracing"""
        
        print(f"{Colors.CYAN}🔧 Debugging Workflow: {workflow_id}{Colors.NC}")
        print("=" * 40)
        
        # Enable debug tracing
        trace_file = f"debug_traces/workflow_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        try:
            from langswarm.core.debug import enable_debug_tracing
            enable_debug_tracing(trace_file)
            print(f"📝 Debug tracing enabled: {trace_file}")
        except ImportError:
            print(f"⚠️  Debug tracing not available")
        
        try:
            # Load workflow configuration
            config_files = [
                self.project_root / "langswarm/v2/test_configs/bigquery_v2_test.yaml",
                self.project_root / "langswarm/core/debug/test_configs/bigquery_debug.yaml"
            ]
            
            workflow_config = None
            for config_file in config_files:
                if config_file.exists():
                    import yaml
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Check if this config has our workflow
                    workflows = config.get('workflows', [])
                    for workflow in workflows:
                        if isinstance(workflow, dict) and workflow.get('id') == workflow_id:
                            workflow_config = config
                            break
                    
                    if workflow_config:
                        break
            
            if not workflow_config:
                return {"error": f"Workflow '{workflow_id}' not found"}
            
            # Execute workflow with real components
            print(f"🚀 Executing workflow with input: '{user_input}'")
            
            # Use actual LangSwarm execution
            from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
            
            loader = LangSwarmConfigLoader(config_file)
            workflows, agents, brokers, tools, metadata = loader.load()
            
            executor = WorkflowExecutor(workflows, agents, tools=tools)
            
            result = executor.run_workflow(
                workflow_id=workflow_id,
                user_input=user_input
            )
            
            print(f"✅ Workflow completed")
            print(f"Result: {result}")
            
            return {
                "workflow_id": workflow_id,
                "input": user_input,
                "result": result,
                "trace_file": trace_file,
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return {
                "workflow_id": workflow_id,
                "input": user_input,
                "error": str(e),
                "trace_file": trace_file,
                "status": "failed"
            }

class DebugCLI:
    """Main CLI for the debug system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.credential_manager = CredentialManager(self.project_root)
        self.real_tester = RealDataTester(self.project_root)
        self.workflow_debugger = WorkflowDebugger(self.project_root)
    
    def run(self, args) -> int:
        """Run the debug system"""
        
        print(f"{Colors.BOLD}🚀 LangSwarm Debug & Test System{Colors.NC}")
        print(f"{Colors.CYAN}📅 {datetime.now()}{Colors.NC}")
        print(f"{Colors.CYAN}📁 Project: {self.project_root}{Colors.NC}")
        print("=" * 60)
        
        try:
            if args.command == 'setup':
                return self.handle_setup()
            elif args.command == 'test':
                return asyncio.run(self.handle_test(args))
            elif args.command == 'validate':
                return self.handle_validate(args)
            elif args.command == 'debug':
                return asyncio.run(self.handle_debug(args))
            else:
                print(f"{Colors.RED}❌ Unknown command: {args.command}{Colors.NC}")
                return 1
                
        except KeyboardInterrupt:
            print(f"\n{Colors.CYAN}👋 Interrupted by user{Colors.NC}")
            return 130
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def handle_setup(self) -> int:
        """Handle credential and environment setup"""
        
        success = self.credential_manager.check_and_setup_credentials()
        
        if success:
            # Load credentials and validate
            self.credential_manager.load_env_file()
            validation_results = self.credential_manager.validate_credentials()
            
            print(f"\n{Colors.CYAN}📊 Validation Results:{Colors.NC}")
            for service, valid in validation_results.items():
                status = f"{Colors.GREEN}✅{Colors.NC}" if valid else f"{Colors.RED}❌{Colors.NC}"
                print(f"   {status} {service}")
            
            if all(validation_results.values()):
                print(f"\n{Colors.GREEN}🎉 Setup complete! All credentials validated.{Colors.NC}")
                return 0
            else:
                print(f"\n{Colors.YELLOW}⚠️  Setup complete but some credentials need attention.{Colors.NC}")
                return 1
        else:
            print(f"\n{Colors.RED}❌ Setup failed. Please fix credentials and try again.{Colors.NC}")
            return 1
    
    async def handle_test(self, args) -> int:
        """Handle testing commands"""
        
        # Ensure credentials are set up
        if not self.credential_manager.check_and_setup_credentials():
            return 1
        
        self.credential_manager.load_env_file()
        
        if args.test_type == 'bigquery':
            query = args.query or "LangSwarm AI agent workflows"
            max_results = args.max_results or 5
            
            result = await self.real_tester.test_bigquery_real(query, max_results)
            
            if 'error' in result:
                print(f"\n{Colors.RED}❌ BigQuery test failed{Colors.NC}")
                print(f"Error: {result['error']}")
                if 'suggestions' in result:
                    print(f"\n{Colors.CYAN}Suggestions:{Colors.NC}")
                    for suggestion in result['suggestions']:
                        print(f"  • {suggestion}")
                return 1
            else:
                print(f"\n{Colors.GREEN}✅ BigQuery test successful{Colors.NC}")
                return 0
        
        elif args.test_type == 'v2':
            results = await self.real_tester.test_v2_system_real()
            
            total = len(results)
            passed = sum(results.values())
            
            print(f"\n{Colors.CYAN}📊 V2 Test Results:{Colors.NC}")
            print(f"Passed: {passed}/{total}")
            
            return 0 if passed == total else 1
        
        return 0
    
    def handle_validate(self, args) -> int:
        """Handle validation commands"""
        
        if args.validate_type == 'credentials':
            self.credential_manager.load_env_file()
            results = self.credential_manager.validate_credentials()
            
            if all(results.values()):
                print(f"\n{Colors.GREEN}✅ All credentials valid{Colors.NC}")
                return 0
            else:
                print(f"\n{Colors.RED}❌ Some credentials invalid{Colors.NC}")
                return 1
        
        elif args.validate_type == 'config':
            # Validate configurations with real environment variables
            print(f"{Colors.CYAN}📋 Validating Configurations with Real Environment{Colors.NC}")
            
            self.credential_manager.load_env_file()
            
            # Test environment variable substitution
            test_vars = {
                'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
                'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT'),
                'BIGQUERY_DATASET_ID': os.getenv('BIGQUERY_DATASET_ID', 'vector_search'),
            }
            
            print(f"Environment variables:")
            for key, value in test_vars.items():
                if value:
                    masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                    print(f"   ✅ {key}: {masked}")
                else:
                    print(f"   ❌ {key}: Not set")
            
            return 0
        
        return 0
    
    async def handle_debug(self, args) -> int:
        """Handle debug commands"""
        
        if args.debug_type == 'workflow':
            workflow_id = args.workflow_id or 'bigquery_v2_debug_workflow'
            user_input = args.input or 'Test query for debugging'
            
            result = await self.workflow_debugger.debug_workflow(workflow_id, user_input)
            
            if result.get('status') == 'success':
                print(f"\n{Colors.GREEN}✅ Workflow debug successful{Colors.NC}")
                print(f"Trace file: {result.get('trace_file')}")
                return 0
            else:
                print(f"\n{Colors.RED}❌ Workflow debug failed{Colors.NC}")
                print(f"Error: {result.get('error')}")
                return 1
        
        return 0

def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser"""
    
    parser = argparse.ArgumentParser(
        description="LangSwarm Debug & Test System - Real data testing and debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up credentials and environment
  python scripts/langswarm_debug.py setup
  
  # Test BigQuery with real data
  python scripts/langswarm_debug.py test bigquery --query "AI workflows"
  
  # Test V2 system components
  python scripts/langswarm_debug.py test v2
  
  # Validate credentials
  python scripts/langswarm_debug.py validate credentials
  
  # Debug a workflow with real execution
  python scripts/langswarm_debug.py debug workflow --workflow-id bigquery_debug_workflow --input "test query"
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up credentials and environment')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run real tests')
    test_parser.add_argument('test_type', choices=['bigquery', 'v2'], help='Test type')
    test_parser.add_argument('--query', type=str, help='Search query for BigQuery test')
    test_parser.add_argument('--max-results', type=int, help='Maximum results for BigQuery test')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate components')
    validate_parser.add_argument('validate_type', choices=['credentials', 'config'], help='Validation type')
    
    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug workflows and components')
    debug_parser.add_argument('debug_type', choices=['workflow'], help='Debug type')
    debug_parser.add_argument('--workflow-id', type=str, help='Workflow ID to debug')
    debug_parser.add_argument('--input', type=str, help='Input for workflow')
    
    return parser

def main():
    """Main entry point"""
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = DebugCLI()
    return cli.run(args)

if __name__ == '__main__':
    sys.exit(main())
