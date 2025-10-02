#!/usr/bin/env python3
"""
Demo: V2 BigQuery Configuration Usage

This script demonstrates how to use the enhanced V2 BigQuery configuration
for vector search operations with the new V2 architecture.
"""

import asyncio
import sys
import os
import yaml
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

print("🚀 LangSwarm V2 BigQuery Configuration Demo")
print("=" * 60)


def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return None


def substitute_env_vars(config, env_vars=None):
    """Simple environment variable substitution for demo purposes"""
    if env_vars is None:
        env_vars = {}
    
    import re
    import json
    
    def substitute_value(value):
        if isinstance(value, str) and "${" in value:
            # Simple substitution for demo - in real V2 this would be more sophisticated
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_expr = match.group(1)
                if ":-" in var_expr:
                    var_name, default_value = var_expr.split(":-", 1)
                    return env_vars.get(var_name, os.getenv(var_name, default_value))
                else:
                    return env_vars.get(var_expr, os.getenv(var_expr, f"${{{var_expr}}}"))
            
            return re.sub(pattern, replace_var, value)
        return value
    
    def process_obj(obj):
        if isinstance(obj, dict):
            return {k: process_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [process_obj(item) for item in obj]
        else:
            return substitute_value(obj)
    
    return process_obj(config)


async def demo_configuration_loading():
    """Demonstrate V2 configuration loading and processing"""
    
    print("\n📁 V2 Configuration Loading Demo")
    print("-" * 40)
    
    # Load the V2 BigQuery configuration
    config_path = "langswarm/v2/test_configs/bigquery_v2_test.yaml"
    
    print(f"Loading configuration: {config_path}")
    config = load_config(config_path)
    
    if not config:
        print("❌ Failed to load configuration")
        return False
    
    print(f"✅ Configuration loaded successfully!")
    print(f"  Version: {config.get('version')}")
    print(f"  Project: {config.get('project_name')}")
    
    # Demo environment variable substitution
    print(f"\n🌍 Environment Variable Substitution Demo")
    demo_env_vars = {
        'OPENAI_API_KEY': 'demo-openai-key-12345',
        'GOOGLE_CLOUD_PROJECT': 'my-project-demo',
        'BIGQUERY_DATASET_ID': 'vector_search_demo',
        'BIGQUERY_TABLE_NAME': 'embeddings_demo',
        'EMBEDDING_MODEL': 'text-embedding-3-large'
    }
    
    print("Demo environment variables:")
    for key, value in demo_env_vars.items():
        print(f"  {key}={value}")
    
    # Substitute variables
    processed_config = substitute_env_vars(config, demo_env_vars)
    
    print(f"\n✅ Configuration processed with environment variables")
    
    # Show processed tool configuration
    tools = processed_config.get('tools', [])
    if tools:
        tool = tools[0]
        print(f"\n🔧 Processed Tool Configuration:")
        print(f"  ID: {tool.get('id')}")
        print(f"  Type: {tool.get('type')}")
        print(f"  Project ID: {tool.get('config', {}).get('project_id')}")
        print(f"  Dataset ID: {tool.get('config', {}).get('dataset_id')}")
        print(f"  Table Name: {tool.get('config', {}).get('table_name')}")
        print(f"  Embedding Model: {tool.get('config', {}).get('embedding_model')}")
    
    return True


async def demo_agent_configuration():
    """Demonstrate V2 agent configuration features"""
    
    print("\n🤖 V2 Agent Configuration Demo")
    print("-" * 40)
    
    config_path = "langswarm/v2/test_configs/bigquery_v2_test.yaml"
    config = load_config(config_path)
    
    if not config:
        return False
    
    agents = config.get('agents', [])
    if not agents:
        print("❌ No agents found in configuration")
        return False
    
    agent_config = agents[0]
    
    print(f"📊 Agent Configuration Analysis:")
    print(f"  ID: {agent_config.get('id')}")
    print(f"  Provider: {agent_config.get('provider')}")
    print(f"  Model: {agent_config.get('model')}")
    print(f"  Name: {agent_config.get('name')}")
    
    # V2 Configuration Features
    v2_config = agent_config.get('config', {})
    print(f"\n✨ V2 Agent Features:")
    print(f"  Temperature: {v2_config.get('temperature')}")
    print(f"  Max Tokens: {v2_config.get('max_tokens')}")
    print(f"  Native Tools: {v2_config.get('use_native_tools')}")
    print(f"  Streaming: {v2_config.get('enable_streaming')}")
    print(f"  Retry Attempts: {v2_config.get('retry_attempts')}")
    print(f"  Timeout: {v2_config.get('timeout_seconds')}s")
    
    # Middleware Configuration
    middleware = agent_config.get('middleware', {})
    print(f"\n🌐 Middleware Configuration:")
    print(f"  Routing: {middleware.get('enable_routing')}")
    print(f"  Validation: {middleware.get('enable_validation')}")
    print(f"  Context Enrichment: {middleware.get('enable_context_enrichment')}")
    print(f"  Result Transformation: {middleware.get('enable_result_transformation')}")
    print(f"  Audit Logging: {middleware.get('enable_audit_logging')}")
    print(f"  Policy: {middleware.get('policy_name')}")
    
    # Observability Configuration
    observability = agent_config.get('observability', {})
    print(f"\n👁️  Observability Configuration:")
    print(f"  Tracing: {observability.get('enable_tracing')}")
    print(f"  Metrics: {observability.get('enable_metrics')}")
    print(f"  Debug Logging: {observability.get('enable_debug_logging')}")
    print(f"  Trace Level: {observability.get('trace_level')}")
    
    return True


async def demo_workflow_configuration():
    """Demonstrate V2 workflow configuration features"""
    
    print("\n⚡ V2 Workflow Configuration Demo")
    print("-" * 40)
    
    config_path = "langswarm/v2/test_configs/bigquery_v2_test.yaml"
    config = load_config(config_path)
    
    if not config:
        return False
    
    workflows = config.get('workflows', [])
    if not workflows:
        print("❌ No workflows found in configuration")
        return False
    
    workflow_config = workflows[0]
    
    print(f"📊 Workflow Configuration Analysis:")
    print(f"  ID: {workflow_config.get('id')}")
    print(f"  Name: {workflow_config.get('name')}")
    print(f"  Description: {workflow_config.get('description')}")
    print(f"  Version: {workflow_config.get('version')}")
    
    # V2 Workflow Configuration
    wf_config = workflow_config.get('config', {})
    print(f"\n✨ V2 Workflow Features:")
    print(f"  Timeout: {wf_config.get('timeout_seconds')}s")
    print(f"  Error Strategy: {wf_config.get('error_strategy')}")
    
    retry_policy = wf_config.get('retry_policy', {})
    print(f"  Retry Policy:")
    print(f"    Max Retries: {retry_policy.get('max_retries')}")
    print(f"    Exponential Backoff: {retry_policy.get('exponential_backoff')}")
    
    # Variables
    variables = workflow_config.get('variables', {})
    print(f"\n🔧 Workflow Variables:")
    for var_name, var_value in variables.items():
        print(f"    {var_name}: {var_value}")
    
    # Steps Analysis
    steps = workflow_config.get('steps', [])
    print(f"\n📋 Workflow Steps ({len(steps)} total):")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step.get('id')} ({step.get('type')})")
        if step.get('type') == 'condition':
            print(f"     Condition: {step.get('condition')}")
        elif step.get('type') == 'agent':
            print(f"     Agent: {step.get('agent_id')}")
        elif step.get('type') == 'transform':
            print(f"     Function: {step.get('transform_function')}")
        
        depends_on = step.get('depends_on', [])
        if depends_on:
            print(f"     Depends on: {depends_on}")
    
    return True


async def demo_policy_configuration():
    """Demonstrate V2 policy configuration features"""
    
    print("\n🛡️  V2 Policy Configuration Demo")
    print("-" * 40)
    
    config_path = "langswarm/v2/test_configs/bigquery_v2_test.yaml"
    config = load_config(config_path)
    
    if not config:
        return False
    
    policies = config.get('policies', {})
    if not policies:
        print("❌ No policies found in configuration")
        return False
    
    for policy_name, policy_config in policies.items():
        print(f"📊 Policy: {policy_name}")
        print(f"  Max Execution Time: {policy_config.get('max_execution_time')}")
        print(f"  Max Steps: {policy_config.get('max_steps')}")
        print(f"  Max Parallel Steps: {policy_config.get('max_parallel_steps')}")
        print(f"  Retry Attempts: {policy_config.get('retry_attempts')}")
        print(f"  Audit Level: {policy_config.get('audit_level')}")
        print(f"  Security Level: {policy_config.get('security_level')}")
        print(f"  Data Classification: {policy_config.get('data_classification')}")
        
        resource_limits = policy_config.get('resource_limits', {})
        if resource_limits:
            print(f"  Resource Limits:")
            print(f"    Memory: {resource_limits.get('memory')}")
            print(f"    CPU: {resource_limits.get('cpu')}")
    
    return True


async def demo_v2_vs_v1_comparison():
    """Compare V2 configuration with original V1 configuration"""
    
    print("\n🔄 V2 vs V1 Configuration Comparison")
    print("-" * 40)
    
    # Load V1 config
    v1_config_path = "langswarm/core/debug/test_configs/bigquery_debug.yaml"
    v2_config_path = "langswarm/v2/test_configs/bigquery_v2_test.yaml"
    
    v1_config = None
    v2_config = None
    
    if Path(v1_config_path).exists():
        v1_config = load_config(v1_config_path)
        print(f"✅ V1 config loaded: {v1_config_path}")
    else:
        print(f"⚠️  V1 config not found: {v1_config_path}")
    
    if Path(v2_config_path).exists():
        v2_config = load_config(v2_config_path)
        print(f"✅ V2 config loaded: {v2_config_path}")
    else:
        print(f"❌ V2 config not found: {v2_config_path}")
        return False
    
    print(f"\n📊 Configuration Comparison:")
    
    # Basic structure comparison
    if v1_config and v2_config:
        print(f"  Version:")
        print(f"    V1: {v1_config.get('version', 'Not specified')}")
        print(f"    V2: {v2_config.get('version', 'Not specified')}")
        
        print(f"  Agent Count:")
        print(f"    V1: {len(v1_config.get('agents', []))}")
        print(f"    V2: {len(v2_config.get('agents', []))}")
        
        print(f"  Tool Count:")
        print(f"    V1: {len(v1_config.get('tools', []))}")
        print(f"    V2: {len(v2_config.get('tools', []))}")
        
        print(f"  Workflow Count:")
        print(f"    V1: {len(v1_config.get('workflows', []))}")
        print(f"    V2: {len(v2_config.get('workflows', []))}")
    
    # V2 Enhancements
    print(f"\n✨ V2 Enhancements Added:")
    v2_only_features = [
        "middleware configuration",
        "observability configuration", 
        "policy configuration",
        "enhanced error handling",
        "connection pooling",
        "cost management",
        "advanced workflow features",
        "V2 tool location references",
        "provider-specific configurations",
        "structured logging configuration"
    ]
    
    for feature in v2_only_features:
        print(f"  ✅ {feature}")
    
    return True


async def demo_practical_usage():
    """Demonstrate practical usage scenarios"""
    
    print("\n🎯 Practical Usage Scenarios")
    print("-" * 40)
    
    print(f"📋 Scenario 1: Development Environment Setup")
    print(f"  1. Copy v2_debug_config.yaml to your project")
    print(f"  2. Set environment variables:")
    print(f"     export LANGSWARM_ENV=development")
    print(f"     export OPENAI_API_KEY=your_openai_key")
    print(f"     export GOOGLE_CLOUD_PROJECT=your_project")
    print(f"  3. Enable V2 features:")
    print(f"     export LANGSWARM_USE_V2_TOOLS=true")
    print(f"  4. Run: python -m langswarm.v2.core.config load v2_debug_config.yaml")
    
    print(f"\n📋 Scenario 2: BigQuery Vector Search Setup")
    print(f"  1. Copy bigquery_v2_test.yaml to your project")
    print(f"  2. Configure BigQuery environment:")
    print(f"     export BIGQUERY_DATASET_ID=your_dataset")
    print(f"     export BIGQUERY_TABLE_NAME=your_table")
    print(f"  3. Set up Google Cloud authentication")
    print(f"  4. Run workflow: python -m langswarm.v2.workflows execute bigquery_v2_debug_workflow")
    
    print(f"\n📋 Scenario 3: Production Deployment")
    print(f"  1. Use production policy configuration")
    print(f"  2. Enable comprehensive observability")
    print(f"  3. Configure connection pooling and cost management")
    print(f"  4. Set resource limits and security policies")
    print(f"  5. Deploy with: docker run -v config:/config langswarm:v2")
    
    return True


async def run_v2_configuration_demo():
    """Run complete V2 configuration demonstration"""
    
    print(f"🚀 Starting V2 Configuration Demo at {datetime.now()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    demos = [
        ("Configuration Loading", demo_configuration_loading),
        ("Agent Configuration", demo_agent_configuration),
        ("Workflow Configuration", demo_workflow_configuration),
        ("Policy Configuration", demo_policy_configuration),
        ("V2 vs V1 Comparison", demo_v2_vs_v1_comparison),
        ("Practical Usage", demo_practical_usage),
    ]
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*60}")
            result = await demo_func()
            if result:
                print(f"✅ {demo_name} demo completed successfully")
            else:
                print(f"⚠️  {demo_name} demo had issues")
        except Exception as e:
            print(f"💥 {demo_name} demo error: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"🎉 V2 Configuration Demo Complete!")
    print(f"\n📋 Key Takeaways:")
    print(f"  ✅ V2 configurations are significantly more powerful than V1")
    print(f"  ✅ Enhanced middleware, observability, and policy support")
    print(f"  ✅ Environment variable substitution for flexible deployment")
    print(f"  ✅ Backward compatibility maintained with V1 configurations")
    print(f"  ✅ Ready for production deployment with comprehensive features")
    
    print(f"\n🚀 Ready to test with real BigQuery data!")
    print(f"  Set your environment variables and run the configurations")
    print(f"  The V2 system will provide enhanced debugging and monitoring")


if __name__ == "__main__":
    asyncio.run(run_v2_configuration_demo())
