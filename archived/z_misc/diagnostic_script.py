#!/usr/bin/env python3
"""
LangSwarm BigQuery Diagnostic Script
Helps identify environmental and configuration issues
"""

import os
import sys
import json
import asyncio
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_environment():
    print_section("Environment Variables")
    
    env_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_CLOUD_PROJECT', 
        'GOOGLE_APPLICATION_CREDENTIALS',
        'PYTHONPATH'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                print(f"✅ {var}: {'*' * 20}...{value[-4:] if len(value) > 4 else '****'}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

def check_python_environment():
    print_section("Python Environment")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")

def check_langswarm_installation():
    print_section("LangSwarm Installation")
    
    try:
        import langswarm
        print(f"✅ LangSwarm imported successfully")
        
        # Check version
        try:
            from langswarm import __version__
            print(f"📦 Version: {__version__}")
        except ImportError:
            print("⚠️  Version not available")
        
        # Check installation path
        print(f"📍 Installation path: {langswarm.__file__}")
        
    except ImportError as e:
        print(f"❌ LangSwarm import failed: {e}")
        return False
    
    return True

def check_dependencies():
    print_section("Dependencies")
    
    required_deps = [
        'openai',
        'google.cloud.bigquery',
        'yaml',
        'pydantic',
        'asyncio'
    ]
    
    for dep in required_deps:
        try:
            if dep == 'google.cloud.bigquery':
                import google.cloud.bigquery
                print(f"✅ {dep}: Available")
            elif dep == 'asyncio':
                import asyncio
                print(f"✅ {dep}: Available")
            else:
                __import__(dep)
                print(f"✅ {dep}: Available")
        except ImportError as e:
            print(f"❌ {dep}: Missing - {e}")

def check_bigquery_tool():
    print_section("BigQuery Tool Import")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import (
            similarity_search, 
            SimilaritySearchInput,
            BigQueryVectorSearchMCPTool
        )
        print("✅ BigQuery tool imports successful")
        return True
    except ImportError as e:
        print(f"❌ BigQuery tool import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bigquery_direct():
    print_section("Direct BigQuery Test")
    
    if not check_bigquery_tool():
        return False
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search, SimilaritySearchInput
        
        print("🧪 Testing direct BigQuery similarity search...")
        
        search_input = SimilaritySearchInput(
            query='test query',
            limit=1,
            similarity_threshold=0.01
        )
        
        result = await similarity_search(search_input)
        print(f"✅ Direct BigQuery test successful!")
        print(f"   Results returned: {len(result.results)}")
        return True
        
    except Exception as e:
        print(f"❌ Direct BigQuery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_loading():
    print_section("Configuration Loading")
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Try to find a config file
        config_paths = [
            'langswarm/core/debug/test_configs/bigquery_debug.yaml',
            'config.yaml',
            'langswarm.yaml'
        ]
        
        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if not config_file:
            print("⚠️  No config file found, testing with default")
            return True
        
        print(f"📄 Using config file: {config_file}")
        
        loader = LangSwarmConfigLoader(config_file)
        workflows, agents, brokers, tools, metadata = loader.load()
        
        print(f"✅ Config loaded successfully")
        print(f"   Tools: {[getattr(tool, 'identifier', 'unknown') for tool in tools]}")
        print(f"   Agents: {list(agents.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 LangSwarm BigQuery Diagnostic Script")
    print("This script will help identify why BigQuery search isn't working")
    
    # Run all checks
    check_environment()
    check_python_environment()
    
    if not check_langswarm_installation():
        print("\n❌ LangSwarm installation failed - cannot continue")
        return
    
    check_dependencies()
    check_config_loading()
    
    # Run async tests
    print_section("Async Tests")
    try:
        asyncio.run(test_bigquery_direct())
    except Exception as e:
        print(f"❌ Async test execution failed: {e}")
    
    print_section("Summary")
    print("✅ Diagnostic script completed")
    print("📋 Please share the output above to help debug the issue")

if __name__ == "__main__":
    main()
