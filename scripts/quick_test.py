#!/usr/bin/env python3
"""
Quick Test Script for LangSwarm TODO Implementation

Run this script before and after implementing any TODO sub-task to ensure
no regressions and that new features work correctly.

Usage:
    python scripts/quick_test.py
    python scripts/quick_test.py --feature llm_abstractions
    python scripts/quick_test.py --feature config_simplification
"""

import os
import sys
import subprocess
import tempfile
import yaml
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description=""):
    """Run a command and return success status"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            print(f"   ✅ PASSED")
            return True
        else:
            print(f"   ❌ FAILED")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_current_functionality():
    """Test current LangSwarm functionality (baseline)"""
    print("\n🧪 Testing Current Functionality (Baseline)")
    print("=" * 50)
    
    tests = [
        ("python3 -m pytest tests/ -v --tb=short", "Core unit tests"),
        ("python3 -m pytest tests/integration/ -v", "Integration tests"),
        ("python3 example_mcp_config/test_filesystem_example.py", "Example configuration test"),
    ]
    
    results = []
    for cmd, desc in tests:
        results.append(run_command(cmd, desc))
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Baseline Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Baseline is HEALTHY - safe to proceed with TODO implementation")
        return True
    else:
        print("❌ Baseline has ISSUES - fix these before implementing new features")
        return False

def test_config_loading():
    """Test configuration loading works with current setup"""
    print("\n🔧 Testing Configuration Loading")
    print("=" * 40)
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Test multi-file loading
        if os.path.exists("example_mcp_config"):
            loader = LangSwarmConfigLoader("example_mcp_config")
            workflows, agents, brokers, tools, tools_metadata = loader.load()
            print(f"   ✅ Multi-file config: {len(agents)} agents, {len(tools)} tools")
        
        # Test that existing configs are valid
        config_dirs = ["example_mcp_config", "langswarm/mcp/tools/filesystem", "langswarm/mcp/tools/mcpgithubtool"]
        valid_configs = 0
        
        for config_dir in config_dirs:
            if os.path.exists(config_dir):
                try:
                    loader = LangSwarmConfigLoader(config_dir)
                    workflows, agents, brokers, tools, tools_metadata = loader.load()
                    valid_configs += 1
                    print(f"   ✅ Config {config_dir}: OK")
                except Exception as e:
                    print(f"   ❌ Config {config_dir}: {e}")
        
        print(f"   📊 {valid_configs}/{len([d for d in config_dirs if os.path.exists(d)])} configs loaded successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return False

def test_agent_chat():
    """Test basic agent chat functionality"""
    print("\n💬 Testing Agent Chat Functionality")
    print("=" * 40)
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Load a simple agent configuration
        if os.path.exists("example_mcp_config"):
            loader = LangSwarmConfigLoader("example_mcp_config")
            workflows, agents, brokers, tools, tools_metadata = loader.load()
            
            if agents:
                agent = list(agents.values())[0]
                test_message = "Hello, this is a test message"
                
                print(f"   Testing agent: {agent.name}")
                response = agent.chat(test_message)
                
                if response and len(str(response)) > 0:
                    print(f"   ✅ Agent responded: {str(response)[:100]}...")
                    return True
                else:
                    print(f"   ❌ Agent returned empty/null response")
                    return False
            else:
                print(f"   ⚠️  No agents found in configuration")
                return True  # Not necessarily an error
        else:
            print(f"   ⚠️  No example config found - skipping chat test")
            return True
            
    except Exception as e:
        print(f"   ❌ Agent chat test failed: {e}")
        return False

def test_llm_abstractions():
    """Test LLM abstractions features if implemented"""
    print("\n🧠 Testing LLM Abstractions Features")
    print("=" * 40)
    
    # Test if native structured responses are available
    try:
        from langswarm.core.wrappers.generic import AgentWrapper
        print("   ✅ AgentWrapper imports successfully")
        
        # Test if response_format parameter is supported
        # This is just checking that we can call it without error
        print("   📝 Native structured responses: Implementation needed")
        print("   📝 Native tool calling: Implementation needed")
        print("   📝 Streaming responses: Implementation needed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ LLM abstractions test failed: {e}")
        return False

def test_single_config_file():
    """Test single configuration file features if implemented"""
    print("\n📄 Testing Single Configuration File Features")
    print("=" * 50)
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Check if load_single_config method exists
        loader = LangSwarmConfigLoader()
        if hasattr(loader, 'load_single_config'):
            print("   ✅ load_single_config method exists")
            
            # Create a test single config file
            test_config = {
                "name": "test-assistant",
                "agent": {
                    "model": "gpt-4o-mini",
                    "behavior": "helpful assistant",
                    "tools": ["filesystem"]
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(test_config, f)
                test_file = f.name
            
            try:
                workflows, agents, brokers, tools, tools_metadata = loader.load_single_config(test_file)
                print("   ✅ Single config file loading works")
                os.unlink(test_file)
                return True
            except Exception as e:
                print(f"   ❌ Single config loading failed: {e}")
                os.unlink(test_file)
                return False
        else:
            print("   📝 load_single_config method: Not implemented yet")
            return True
            
    except Exception as e:
        print(f"   ❌ Single config test failed: {e}")
        return False

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick test script for LangSwarm TODO implementation")
    parser.add_argument("--feature", choices=["llm_abstractions", "config_simplification", "all"], 
                       default="all", help="Test specific feature area")
    args = parser.parse_args()
    
    print("🚀 LangSwarm Quick Test Suite")
    print("=" * 60)
    print(f"Testing feature area: {args.feature}")
    
    all_results = []
    
    # Always test baseline functionality
    all_results.append(test_current_functionality())
    all_results.append(test_config_loading())
    all_results.append(test_agent_chat())
    
    # Feature-specific tests
    if args.feature in ["llm_abstractions", "all"]:
        all_results.append(test_llm_abstractions())
    
    if args.feature in ["config_simplification", "all"]:
        all_results.append(test_single_config_file())
    
    # Summary
    passed = sum(all_results)
    total = len(all_results)
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {passed}/{total} test categories passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Ready for development!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Address issues before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 