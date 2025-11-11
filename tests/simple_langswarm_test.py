#!/usr/bin/env python3
"""
Simple LangSwarm Test - Identifying Issues for LLM Usage
========================================================

This script tests the basic functionality of LangSwarm to identify
why LLMs might have difficulty using it.
"""

import os
import sys
import asyncio
from typing import Optional

def test_basic_imports():
    """Test basic imports to identify missing dependencies."""
    print("🔍 Testing basic imports...")
    
    results = {}
    
    # Core LangSwarm
    try:
        import langswarm
        results['langswarm'] = "✅ Available"
    except ImportError as e:
        results['langswarm'] = f"❌ Failed: {e}"
    
    # Agent creation functions
    try:
        from langswarm.core.agents import create_openai_agent, AgentBuilder
        results['agent_creation'] = "✅ Available"
    except ImportError as e:
        results['agent_creation'] = f"❌ Failed: {e}"
    
    # Configuration system
    try:
        from langswarm.core.config import load_config, LangSwarmConfig
        results['config_system'] = "✅ Available"
    except ImportError as e:
        results['config_system'] = f"❌ Failed: {e}"
    
    # Provider dependencies
    providers = {
        'openai': 'openai',
        'anthropic': 'anthropic',
        'google_ai': 'google.generativeai',
        'cohere': 'cohere',
        'mistral': 'mistralai'
    }
    
    for name, module in providers.items():
        try:
            __import__(module)
            results[f'provider_{name}'] = "✅ Available"
        except ImportError:
            results[f'provider_{name}'] = "❌ Missing"
    
    # Print results
    for component, status in results.items():
        print(f"  {component}: {status}")
    
    return results

async def test_simple_agent_creation():
    """Test creating a simple agent with minimal configuration."""
    print("\n🤖 Testing simple agent creation...")
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY environment variable found")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        from langswarm.core.agents import create_openai_agent
        
        # Try to create agent
        agent = create_openai_agent(
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            api_key=api_key
        )
        
        print("✅ Agent created successfully")
        
        # Try a simple chat
        try:
            response = await agent.chat("Hello! Just say 'Hi' back.")
            print(f"✅ Chat successful: {response.content[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading with the example config."""
    print("\n📋 Testing configuration loading...")
    
    try:
        from langswarm.core.config import load_config
        
        # Try to load the example config
        config_path = "example_config.yaml"
        if not os.path.exists(config_path):
            print(f"❌ Example config not found: {config_path}")
            return False
        
        config = load_config(config_path)
        print(f"✅ Configuration loaded successfully")
        print(f"   - {len(config.agents)} agents defined")
        print(f"   - {len(config.workflows)} workflows defined")
        print(f"   - Memory backend: {config.memory.backend}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_builder_pattern():
    """Test the builder pattern for agent creation."""
    print("\n🏗️ Testing builder pattern...")
    
    try:
        from langswarm.core.agents import AgentBuilder
        
        # Test builder without actually creating agent (no API key needed)
        builder = AgentBuilder()
        
        # Test method chaining
        builder = (builder
                  .openai("fake-key-for-testing")  # This will fail later but tests the pattern
                  .model("gpt-3.5-turbo")
                  .system_prompt("You are a test agent")
                  .temperature(0.7))
        
        print("✅ Builder pattern works (method chaining successful)")
        return True
        
    except Exception as e:
        print(f"❌ Builder pattern failed: {e}")
        return False

def analyze_complexity_issues():
    """Analyze potential complexity issues that might confuse LLMs."""
    print("\n🔍 Analyzing complexity issues...")
    
    issues = []
    
    # Check number of import paths
    try:
        from langswarm.core import agents, config, workflows, memory, middleware
        import_paths = [
            "langswarm.core.agents",
            "langswarm.core.config", 
            "langswarm.core.workflows",
            "langswarm.core.memory",
            "langswarm.core.middleware"
        ]
        print(f"✅ Core modules accessible: {len(import_paths)} main paths")
    except ImportError as e:
        issues.append(f"Core module import issues: {e}")
    
    # Check for circular dependencies or complex imports
    try:
        from langswarm.core.agents import create_openai_agent
        from langswarm.core.config import load_config
        # These should be the main entry points
        print("✅ Main entry points accessible")
    except ImportError as e:
        issues.append(f"Entry point import issues: {e}")
    
    # Check configuration complexity
    try:
        with open("example_config.yaml", "r") as f:
            config_content = f.read()
            lines = len(config_content.split('\n'))
            print(f"📊 Example config: {lines} lines")
            if lines > 50:
                issues.append(f"Configuration file is quite long ({lines} lines)")
    except FileNotFoundError:
        issues.append("No example configuration file found")
    
    # Check for optional dependencies
    optional_deps = [
        'cv2', 'PIL', 'pytesseract', 'PyPDF2', 'docx', 
        'speech_recognition', 'pydub', 'redis', 'psycopg2',
        'chromadb', 'qdrant_client'
    ]
    
    missing_optional = []
    for dep in optional_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_optional.append(dep)
    
    if missing_optional:
        print(f"⚠️  Optional dependencies missing: {len(missing_optional)}")
        print(f"   Missing: {', '.join(missing_optional[:5])}{'...' if len(missing_optional) > 5 else ''}")
    
    return issues

async def main():
    """Run all tests and provide analysis."""
    print("🚀 LangSwarm Usability Analysis for LLMs")
    print("=" * 50)
    
    # Run tests
    import_results = test_basic_imports()
    config_success = test_config_loading()
    builder_success = test_builder_pattern()
    agent_success = await test_simple_agent_creation()
    complexity_issues = analyze_complexity_issues()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 50)
    
    # Count successes
    successes = sum([
        'langswarm' in str(import_results.get('langswarm', '')),
        config_success,
        builder_success,
        agent_success
    ])
    
    print(f"✅ Basic functionality: {successes}/4 tests passed")
    
    # Identify main issues
    main_issues = []
    
    if not config_success:
        main_issues.append("Configuration loading problems")
    
    if not agent_success:
        main_issues.append("Agent creation/chat problems")
    
    if not builder_success:
        main_issues.append("Builder pattern problems")
    
    # Provider availability
    available_providers = [k for k, v in import_results.items() 
                          if k.startswith('provider_') and '✅' in v]
    
    print(f"🔌 Available providers: {len(available_providers)}")
    for provider in available_providers:
        print(f"   - {provider.replace('provider_', '')}")
    
    if complexity_issues:
        print(f"\n⚠️  Complexity issues identified:")
        for issue in complexity_issues:
            print(f"   - {issue}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR LLM USAGE:")
    print("1. Ensure OpenAI API key is set: export OPENAI_API_KEY='your-key'")
    print("2. Use simple entry points: create_openai_agent() or AgentBuilder()")
    print("3. Start with minimal config - avoid complex YAML files initially")
    print("4. Install missing provider dependencies as needed")
    
    if len(available_providers) == 1:
        print("5. Consider installing additional providers (anthropic, google-generativeai)")
    
    return successes >= 3  # Success if most tests pass

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
