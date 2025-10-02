#!/usr/bin/env python3
"""
LangSwarm Issues Diagnostic Tool
================================

This script helps diagnose common LangSwarm issues:
1. Agent 'main_workflow' not found errors
2. BigQuery session update warnings
3. Tool functionality problems
4. HuggingFace tokenizer issues
"""

import os
import sys
import json
from typing import Dict, Any, List

def check_hf_tokenizer():
    """Check HuggingFace tokenizer status"""
    print("🔍 Checking HuggingFace Tokenizer Status...")
    
    disable_hf = os.getenv('LANGSWARM_DISABLE_HF_TOKENIZER', '').lower() == 'true'
    if disable_hf:
        print("✅ HuggingFace tokenizer is DISABLED (good for avoiding rate limits)")
        return True
    else:
        print("⚠️ HuggingFace tokenizer is ENABLED (may cause rate limiting)")
        print("   💡 To disable: export LANGSWARM_DISABLE_HF_TOKENIZER=true")
        return False

def check_workflow_config(config_path: str = None):
    """Check for workflow configuration issues"""
    print("\n🔍 Checking Workflow Configuration...")
    
    if not config_path:
        # Look for common config files
        possible_configs = [
            "langswarm.yaml", 
            "config.yaml", 
            "langswarm_config.yaml",
            "config/langswarm.yaml"
        ]
        
        config_path = None
        for path in possible_configs:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            print("❌ No configuration file found")
            print("   💡 Looking for: langswarm.yaml, config.yaml, etc.")
            return False
    
    print(f"📁 Found config: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for common issues
        issues = []
        
        # Check workflows structure
        if 'workflows' in config:
            workflows = config['workflows']
            
            # Issue 1: workflows as a list instead of dict
            if isinstance(workflows, list):
                issues.append("❌ 'workflows' should be a dict, not a list")
                issues.append("   💡 Use: workflows: {main_workflow: [...]} not workflows: [...]")
                
                # Check for specific "main_workflow" in list (causing the error)
                if "main_workflow" in workflows:
                    issues.append("🚨 CRITICAL: 'main_workflow' found as list item!")
                    issues.append("   💡 This causes 'Agent main_workflow not found' error")
                    issues.append("   💡 Change from: workflows: [main_workflow]")
                    issues.append("   💡 To: workflows: {main_workflow: [{id: 'workflow_name', steps: [...]}]}")
            
            # Issue 2: main_workflow as string instead of list
            elif isinstance(workflows, dict) and 'main_workflow' in workflows:
                main_wf = workflows['main_workflow']
                if isinstance(main_wf, str):
                    issues.append(f"❌ main_workflow is a string: '{main_wf}'")
                    issues.append("   💡 This causes 'Agent not found' errors")
                    issues.append("   💡 main_workflow should be a list of workflow definitions")
                elif isinstance(main_wf, list) and len(main_wf) > 0:
                    first_wf = main_wf[0]
                    if isinstance(first_wf, dict) and 'id' in first_wf:
                        print(f"✅ main_workflow structure looks correct (ID: {first_wf['id']})")
                    else:
                        issues.append("❌ main_workflow list items missing 'id' field")
        
        # Check agents structure
        if 'agents' in config:
            agents = config['agents']
            if isinstance(agents, list):
                agent_ids = [agent.get('id', 'unnamed') for agent in agents if isinstance(agent, dict)]
                print(f"✅ Found {len(agent_ids)} agents: {agent_ids}")
            else:
                issues.append("❌ 'agents' should be a list")
        
        # Check tools structure
        if 'tools' in config:
            tools = config['tools']
            if isinstance(tools, list):
                issues.append("❌ 'tools' should be a dict, not a list")
                issues.append("   💡 Use: tools: {tool_id: {...}} not tools: [...]")
            elif isinstance(tools, dict):
                print(f"✅ Found {len(tools)} tools: {list(tools.keys())}")
        
        if issues:
            print("⚠️ Configuration Issues Found:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("✅ Configuration structure looks good")
            return True
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def check_bigquery_usage():
    """Check for BigQuery session management issues"""
    print("\n🔍 Checking BigQuery Usage...")
    
    try:
        from langswarm.core.session.storage import SessionStorageFactory, BIGQUERY_AVAILABLE
        
        if BIGQUERY_AVAILABLE:
            print("✅ BigQuery storage is available")
            print("💡 Use append-only pattern to avoid streaming buffer warnings")
            print("   Example: storage = SessionStorageFactory.create_storage('bigquery', ...)")
        else:
            print("⚠️ BigQuery storage not available (missing google-cloud-bigquery)")
            
    except Exception as e:
        print(f"❌ Error checking BigQuery: {e}")

def check_tool_functionality():
    """Check if tools are working correctly"""
    print("\n🔍 Checking Tool Functionality...")
    
    try:
        # Test core utilities
        from langswarm.core.utils.utilities import Utils
        utils = Utils()
        print("✅ Core utilities working")
        
        # Test tool registry
        from langswarm.synapse.registry.tools import ToolRegistry
        registry = ToolRegistry()
        print("✅ Tool registry working")
        
        # Test MCP tools availability
        from langswarm.core.config import LangSwarmConfigLoader
        loader = LangSwarmConfigLoader()
        
        # Check if SQL tool is available
        if hasattr(loader, 'tool_classes') and 'mcpsql_database' in loader.tool_classes:
            print("✅ SQL database tool is available")
        else:
            print("⚠️ SQL database tool may not be registered")
            
        return True
        
    except Exception as e:
        print(f"❌ Tool functionality error: {e}")
        return False

def provide_solutions():
    """Provide solutions for common issues"""
    print("\n🛠️ Common Solutions:")
    print()
    
    print("1️⃣ For 'Agent main_workflow not found' errors:")
    print("   ✅ Check your workflows structure in langswarm.yaml:")
    print("   workflows:")
    print("     main_workflow:")
    print("       - id: your_actual_workflow_id")
    print("         steps: [...]")
    print()
    
    print("2️⃣ For HuggingFace rate limiting:")
    print("   ✅ export LANGSWARM_DISABLE_HF_TOKENIZER=true")
    print("   ✅ or run: ./disable_hf_tokenizer.sh")
    print()
    
    print("3️⃣ For BigQuery streaming buffer warnings:")
    print("   ✅ Use append-only session storage:")
    print("   from langswarm.core.session.storage import SessionStorageFactory")
    print("   storage = SessionStorageFactory.create_storage('bigquery', ...)")
    print()
    
    print("4️⃣ For tools not working:")
    print("   ✅ HuggingFace tokenizer disable does NOT affect tools")
    print("   ✅ Check your agent configuration has proper tools list")
    print("   ✅ Verify tool registry is properly initialized")

def main():
    """Run comprehensive diagnostics"""
    print("🔧 LangSwarm Issues Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    hf_ok = check_hf_tokenizer()
    config_ok = check_workflow_config()
    check_bigquery_usage()
    tools_ok = check_tool_functionality()
    
    print("\n📊 Summary:")
    print(f"   HuggingFace: {'✅' if hf_ok else '⚠️'}")
    print(f"   Configuration: {'✅' if config_ok else '❌'}")
    print(f"   Tools: {'✅' if tools_ok else '❌'}")
    
    provide_solutions()
    
    if not config_ok:
        print("\n🚨 PRIORITY: Fix configuration issues first!")

if __name__ == "__main__":
    main()
