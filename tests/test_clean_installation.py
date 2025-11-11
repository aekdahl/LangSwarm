#!/usr/bin/env python3
"""
Test script demonstrating LangSwarm's clean installation approach.

This shows how helpful error messages guide users to install exactly what they need.
"""

import sys

def test_openai_provider():
    """Test using OpenAI provider with helpful error if not installed."""
    print("\n1️⃣ Testing OpenAI Provider...")
    try:
        from langswarm.core.agents import create_agent
        agent = create_agent(provider="openai", model="gpt-4")
        print("✅ OpenAI provider available!")
    except Exception as e:
        print(f"Error: {e}")

def test_redis_memory():
    """Test using Redis memory with helpful error if not installed."""
    print("\n2️⃣ Testing Redis Memory Backend...")
    try:
        from langswarm.core.memory import create_memory_backend
        memory = create_memory_backend("redis")
        print("✅ Redis backend available!")
    except Exception as e:
        print(f"Error: {e}")

def test_fastapi_web():
    """Test using FastAPI with helpful error if not installed."""
    print("\n3️⃣ Testing FastAPI Web Framework...")
    try:
        from langswarm.ui.api import create_api_app
        app = create_api_app()
        print("✅ FastAPI available!")
    except Exception as e:
        print(f"Error: {e}")

def test_discord_platform():
    """Test using Discord with helpful error if not installed."""
    print("\n4️⃣ Testing Discord Platform...")
    try:
        from langswarm.ui.discord_gateway import DiscordGateway
        gateway = DiscordGateway()
        print("✅ Discord integration available!")
    except Exception as e:
        print(f"Error: {e}")

def check_minimal_core():
    """Verify core functionality works without optional dependencies."""
    print("\n✅ Testing Core Functionality (always available)...")
    try:
        # These should always work
        from langswarm.core.config import load_config
        from langswarm.core.workflows import WorkflowEngine
        from langswarm.core.session import SessionManager
        
        print("✅ Configuration system: Available")
        print("✅ Workflow engine: Available")
        print("✅ Session management: Available")
        print("✅ Core framework: Fully functional!")
        
        return True
    except Exception as e:
        print(f"❌ Core framework error: {e}")
        return False

def show_installation_summary():
    """Show summary of what's available."""
    print("\n" + "="*60)
    print("📊 LangSwarm Installation Summary")
    print("="*60)
    
    from langswarm.core.utils.optional_imports import optional_imports
    
    # Check what's available
    features = optional_imports.get_available_features()
    
    available = [name for name, is_available in features.items() if is_available]
    missing = [name for name, is_available in features.items() if not is_available]
    
    if available:
        print(f"\n✅ Available Features ({len(available)}):")
        for feature in available:
            print(f"   • {feature}")
    
    if missing:
        print(f"\n❌ Missing Features ({len(missing)}):")
        for feature in missing:
            info = optional_imports.dependency_groups[feature]
            packages = info['packages']
            if len(packages) == 1:
                install_cmd = f"pip install {packages[0]}"
            else:
                install_cmd = f"pip install {' '.join(packages)}"
            print(f"   • {feature}: {install_cmd}")
    
    print("\n💡 Install everything: pip install langswarm[full]")
    print("="*60)

def main():
    print("🧪 LangSwarm Clean Installation Test")
    print("====================================")
    print("This demonstrates how LangSwarm guides you to install")
    print("only the dependencies you need, when you need them.")
    
    # First check core is working
    if not check_minimal_core():
        print("\n❌ Core framework not working properly!")
        sys.exit(1)
    
    # Test optional features
    test_openai_provider()
    test_redis_memory()
    test_fastapi_web()
    test_discord_platform()
    
    # Show summary
    show_installation_summary()
    
    print("\n✨ Test complete!")
    print("\nWith LangSwarm's clean approach:")
    print("• Install only what you need: pip install langswarm openai redis")
    print("• Or get everything: pip install langswarm[full]")
    print("• Clear errors guide you when dependencies are missing")

if __name__ == "__main__":
    main()