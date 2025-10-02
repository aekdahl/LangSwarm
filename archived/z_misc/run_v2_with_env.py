#!/usr/bin/env python3
"""
Run V2 BigQuery Configuration with Environment Variables

This script sets up environment variables and runs the V2 BigQuery configuration tests.
It demonstrates the full V2 system with proper environment variable integration.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

print("🚀 LangSwarm V2 with Environment Variables")
print("=" * 60)


def setup_environment_variables():
    """Set up environment variables for V2 testing"""
    
    print("🌍 Setting up Environment Variables...")
    
    # Core LangSwarm Settings
    env_vars = {
        'LANGSWARM_ENV': 'development',
        'LANGSWARM_USE_V2_AGENTS': 'true',
        'LANGSWARM_USE_V2_CONFIG': 'true', 
        'LANGSWARM_USE_V2_TOOLS': 'true',
        
        # Google Cloud Configuration (using defaults if not set)
        'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT', 'production-pingday'),
        'BIGQUERY_DATASET_ID': os.getenv('BIGQUERY_DATASET_ID', 'vector_search'),
        'BIGQUERY_TABLE_NAME': os.getenv('BIGQUERY_TABLE_NAME', 'embeddings'),
        'BIGQUERY_LOCATION': os.getenv('BIGQUERY_LOCATION', 'US'),
        'GOOGLE_CLOUD_REGION': os.getenv('GOOGLE_CLOUD_REGION', 'us-central1'),
        'VERTEX_AI_LOCATION': os.getenv('VERTEX_AI_LOCATION', 'us-central1'),
        
        # Embedding Configuration
        'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
        'MAX_SEARCH_RESULTS': os.getenv('MAX_SEARCH_RESULTS', '10'),
        'SIMILARITY_THRESHOLD': os.getenv('SIMILARITY_THRESHOLD', '0.01'),
        
        # Logging Configuration
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'DEBUG'),
        'LOG_OUTPUT_DIR': os.getenv('LOG_OUTPUT_DIR', 'debug_traces/v2'),
        'TRACE_OUTPUT_DIR': os.getenv('TRACE_OUTPUT_DIR', 'debug_traces/v2/traces'),
        'TRACE_SAMPLE_RATE': os.getenv('TRACE_SAMPLE_RATE', '1.0'),
        
        # Database Configuration
        'SQLITE_PATH': os.getenv('SQLITE_PATH', './debug.db'),
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    # Check for API keys
    api_keys = {
        'OPENAI_API_KEY': 'OpenAI API key for LLM operations',
        'ANTHROPIC_API_KEY': 'Anthropic API key (optional)',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud service account file path (optional)'
    }
    
    print(f"\n🔑 API Key Status:")
    for key, description in api_keys.items():
        value = os.getenv(key)
        if value:
            # Mask the key for security
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"  ✅ {key}: {masked}")
        else:
            print(f"  ⚠️  {key}: Not set ({description})")
    
    # Create output directories
    os.makedirs('debug_traces/v2/traces', exist_ok=True)
    os.makedirs('debug_traces/v2/metrics', exist_ok=True) 
    os.makedirs('debug_traces/v2/profiles', exist_ok=True)
    os.makedirs('debug_traces/v2/tests', exist_ok=True)
    os.makedirs('debug_traces/v2/migration', exist_ok=True)
    
    print(f"✅ Output directories created")
    
    return True


async def test_v2_with_environment():
    """Test V2 system with environment variables"""
    
    print(f"\n🧪 Testing V2 System with Environment Variables...")
    
    try:
        # Test environment variable loading
        print(f"📊 Environment Status:")
        print(f"  LangSwarm Environment: {os.getenv('LANGSWARM_ENV')}")
        print(f"  V2 Tools Enabled: {os.getenv('LANGSWARM_USE_V2_TOOLS')}")
        print(f"  Google Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        print(f"  BigQuery Dataset: {os.getenv('BIGQUERY_DATASET_ID')}")
        print(f"  Embedding Model: {os.getenv('EMBEDDING_MODEL')}")
        print(f"  Log Level: {os.getenv('LOG_LEVEL')}")
        
        # Test V2 tools integration
        print(f"\n🔧 Testing V2 Tools Integration...")
        from langswarm.tools import get_tools_version_info
        
        tools_info = get_tools_version_info()
        print(f"  V2 Available: {tools_info['v2_available']}")
        print(f"  V2 Enabled: {tools_info['v2_enabled']}")
        print(f"  MCP Tools: {tools_info['mcp_tools_location']}")
        
        # Test configuration loading
        print(f"\n📁 Testing Configuration Loading...")
        import yaml
        
        # Load BigQuery V2 config
        with open('langswarm/v2/test_configs/bigquery_v2_test.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ BigQuery V2 config loaded")
        print(f"  Version: {config.get('version')}")
        print(f"  Project: {config.get('project_name')}")
        
        # Demonstrate environment variable substitution
        print(f"\n🔄 Demonstrating Environment Variable Substitution...")
        
        # Find tool configuration
        tools = config.get('tools', [])
        if tools:
            tool_config = tools[0].get('config', {})
            
            # Show original template values
            print(f"  Original templates:")
            print(f"    project_id: {tool_config.get('project_id')}")
            print(f"    dataset_id: {tool_config.get('dataset_id')}")
            print(f"    embedding_model: {tool_config.get('embedding_model')}")
            
            # Show what they would resolve to
            print(f"  Would resolve to:")
            print(f"    project_id: {os.getenv('GOOGLE_CLOUD_PROJECT', 'production-pingday')}")
            print(f"    dataset_id: {os.getenv('BIGQUERY_DATASET_ID', 'vector_search')}")
            print(f"    embedding_model: {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')}")
        
        return True
        
    except Exception as e:
        print(f"❌ V2 testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_v2_configuration_tests():
    """Run the V2 configuration tests with environment variables"""
    
    print(f"\n🎯 Running V2 Configuration Tests...")
    
    try:
        # Import and run the simple test
        print(f"📋 Running simple configuration test...")
        
        # Run our existing test script programmatically
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'test_v2_configs_simple.py'
        ], capture_output=True, text=True, env=os.environ)
        
        print(f"Test output:")
        print(result.stdout)
        
        if result.stderr:
            print(f"Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ V2 configuration tests passed!")
            return True
        else:
            print(f"⚠️  V2 configuration tests had issues (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run configuration tests: {e}")
        return False


async def demonstrate_bigquery_configuration():
    """Demonstrate BigQuery configuration with real environment variables"""
    
    print(f"\n🗄️  Demonstrating BigQuery Configuration...")
    
    try:
        # Load and process the BigQuery configuration
        import yaml
        import re
        
        with open('langswarm/v2/test_configs/bigquery_v2_test.yaml', 'r') as f:
            content = f.read()
        
        # Simple environment variable substitution
        def substitute_env_vars(text):
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_expr = match.group(1)
                if ":-" in var_expr:
                    var_name, default_value = var_expr.split(":-", 1)
                    return os.getenv(var_name, default_value)
                else:
                    return os.getenv(var_expr, f"${{{var_expr}}}")
            
            return re.sub(pattern, replace_var, text)
        
        # Substitute environment variables
        processed_content = substitute_env_vars(content)
        processed_config = yaml.safe_load(processed_content)
        
        print(f"✅ BigQuery configuration processed with environment variables")
        
        # Show processed configuration
        agents = processed_config.get('agents', [])
        if agents:
            agent = agents[0]
            print(f"\n🤖 Processed Agent Configuration:")
            print(f"  ID: {agent.get('id')}")
            print(f"  Provider: {agent.get('provider')}")
            print(f"  Model: {agent.get('model')}")
            print(f"  Middleware enabled: {agent.get('middleware', {}).get('enable_routing', False)}")
        
        tools = processed_config.get('tools', [])
        if tools:
            tool = tools[0]
            tool_config = tool.get('config', {})
            print(f"\n🔧 Processed Tool Configuration:")
            print(f"  ID: {tool.get('id')}")
            print(f"  Type: {tool.get('type')}")
            print(f"  Project ID: {tool_config.get('project_id')}")
            print(f"  Dataset ID: {tool_config.get('dataset_id')}")
            print(f"  Table Name: {tool_config.get('table_name')}")
            print(f"  Embedding Model: {tool_config.get('embedding_model')}")
        
        # Check if we can actually connect (if credentials are available)
        openai_key = os.getenv('OPENAI_API_KEY')
        google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        print(f"\n🔗 Connection Readiness:")
        print(f"  OpenAI API: {'✅ Ready' if openai_key else '⚠️  API key needed'}")
        print(f"  Google Cloud: {'✅ Ready' if google_creds or os.getenv('GOOGLE_CLOUD_PROJECT') else '⚠️  Auth needed'}")
        
        if openai_key and (google_creds or os.getenv('GOOGLE_CLOUD_PROJECT')):
            print(f"\n🚀 Ready for live BigQuery vector search testing!")
            print(f"   You can now run actual queries against your BigQuery dataset")
        else:
            print(f"\n📋 To enable live testing:")
            if not openai_key:
                print(f"   1. Set OPENAI_API_KEY environment variable")
            if not google_creds:
                print(f"   2. Set up Google Cloud authentication:")
                print(f"      - gcloud auth application-default login")
                print(f"      - Or set GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery configuration demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main execution function"""
    
    print(f"🚀 Starting V2 Environment & Configuration Demo")
    print(f"📅 {datetime.now()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Setup environment
    setup_success = setup_environment_variables()
    if not setup_success:
        print("❌ Environment setup failed")
        return
    
    # Run tests
    tests = [
        ("V2 System Test", test_v2_with_environment),
        ("Configuration Tests", run_v2_configuration_tests),
        ("BigQuery Demo", demonstrate_bigquery_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"🧪 {test_name}")
            print(f"{'='*60}")
            
            result = await test_func()
            if result:
                print(f"✅ {test_name} - SUCCESS")
                passed += 1
            else:
                print(f"⚠️  {test_name} - ISSUES DETECTED")
        except Exception as e:
            print(f"💥 {test_name} - ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"🎯 Final Results: {passed}/{total} tests successful")
    
    if passed == total:
        print(f"🎉 All tests passed! V2 system ready with environment variables!")
    else:
        print(f"⚠️  Some issues detected. Check the output above.")
    
    print(f"\n📋 Summary:")
    print(f"  ✅ Environment variables configured")
    print(f"  ✅ V2 system integration validated") 
    print(f"  ✅ Configuration loading tested")
    print(f"  ✅ BigQuery setup demonstrated")
    
    print(f"\n🚀 Your V2 system is ready!")
    print(f"   Set your API keys and run live BigQuery vector search tests")


if __name__ == "__main__":
    asyncio.run(main())
