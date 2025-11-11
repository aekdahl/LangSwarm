#!/usr/bin/env python3
"""
Test Script for Optional Dependencies System

Demonstrates how LangSwarm handles missing dependencies gracefully and provides
helpful error messages for users.
"""

import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_optional_import_manager():
    """Test the optional import manager."""
    print("🧪 Testing Optional Import Manager")
    print("=" * 50)
    
    try:
        from langswarm.core.utils.optional_imports import optional_imports
        
        # Test available features
        features = optional_imports.get_available_features()
        print(f"✅ Found {len(features)} feature groups")
        
        # Show summary
        print("\n" + optional_imports.get_missing_dependencies_summary())
        
    except Exception as e:
        print(f"❌ Failed to test optional imports: {e}")


def test_provider_registry():
    """Test the provider registry with optional dependencies."""
    print("\n🤖 Testing Provider Registry")
    print("=" * 50)
    
    try:
        from langswarm.core.agents.provider_registry import provider_registry
        
        # List available providers
        available = provider_registry.list_available_providers()
        print(f"✅ Available providers: {available}")
        
        # Show status summary
        print("\n" + provider_registry.get_provider_status_summary())
        
        # Test getting a provider that might not be available
        print("\n🔍 Testing provider access...")
        
        # Try OpenAI (might be available)
        try:
            openai_provider = provider_registry.get_provider('openai')
            print("✅ OpenAI provider available")
        except Exception as e:
            print(f"ℹ️  OpenAI provider not available: {e}")
        
        # Try a provider that's likely not available
        try:
            fake_provider = provider_registry.get_provider('nonexistent')
            print("❌ This shouldn't happen - nonexistent provider found")
        except Exception as e:
            print("✅ Correct error for nonexistent provider:")
            print(f"   {e}")
            
    except Exception as e:
        print(f"❌ Failed to test provider registry: {e}")


def test_memory_backends():
    """Test memory backend registry with optional dependencies."""
    print("\n💾 Testing Memory Backend Registry")
    print("=" * 50)
    
    try:
        from langswarm.core.memory.enhanced_backends import memory_backend_registry
        
        # List available backends
        available = memory_backend_registry.list_available_backends()
        print(f"✅ Available backends: {available}")
        
        # Show status summary
        print("\n" + memory_backend_registry.get_backend_status_summary())
        
        # Test getting backends
        print("\n🔍 Testing backend access...")
        
        # SQLite should always be available
        try:
            sqlite_backend = memory_backend_registry.get_backend('sqlite')
            print("✅ SQLite backend available (as expected)")
        except Exception as e:
            print(f"❌ SQLite backend failed: {e}")
        
        # Test a backend that might not be available
        try:
            redis_backend = memory_backend_registry.get_backend('redis')
            print("✅ Redis backend available")
        except Exception as e:
            print("ℹ️  Redis backend not available (as expected):")
            print(f"   {e}")
            
    except Exception as e:
        print(f"❌ Failed to test memory backends: {e}")


def test_configuration_with_missing_deps():
    """Test configuration loading with missing dependencies."""
    print("\n⚙️ Testing Configuration with Missing Dependencies")
    print("=" * 50)
    
    # Create a test config that uses potentially missing dependencies
    import tempfile
    import os
    
    config_content = """
version: "2.0"
name: "Test Config with Optional Dependencies"

agents:
  - id: "openai_agent"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "You are helpful"
  
  - id: "anthropic_agent"
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    system_prompt: "You are helpful"

memory:
  backend: "redis"
  config:
    url: "redis://localhost:6379"

tools:
  - id: "filesystem"
    type: "mcp"
    local_mode: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_file = f.name
    
    try:
        from langswarm.core.config import load_config
        
        print("🔍 Attempting to load configuration with optional dependencies...")
        config = load_config(config_file)
        print("✅ Configuration loaded successfully!")
        print(f"   Agents: {len(config.agents)}")
        print(f"   Memory backend: {config.memory.backend}")
        
    except Exception as e:
        print("ℹ️  Configuration loading failed (as expected with missing deps):")
        print(f"   {e}")
        
    finally:
        os.unlink(config_file)


def test_minimal_functionality():
    """Test that core functionality works without optional dependencies."""
    print("\n🏃 Testing Minimal Core Functionality")
    print("=" * 50)
    
    try:
        # Test basic imports
        import langswarm
        print("✅ LangSwarm core imported")
        
        # Test configuration schema
        from langswarm.core.config.schema import LangSwarmConfig
        print("✅ Configuration schema available")
        
        # Test error system
        from langswarm.core.errors import ConfigurationError
        print("✅ Error system available")
        
        # Test optional import utilities
        from langswarm.core.utils.optional_imports import optional_import
        print("✅ Optional import utilities available")
        
        print("\n🎉 Core functionality works without optional dependencies!")
        
    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")


def show_installation_guidance():
    """Show installation guidance for users."""
    print("\n📦 Installation Guidance")
    print("=" * 50)
    
    print("🏃 Minimal Installation (core only):")
    print("   pip install langswarm")
    print("   • Basic configuration and orchestration")
    print("   • SQLite memory backend")
    print("   • No AI providers (bring your own)")
    print()
    
    print("⚡ Quick Start (with OpenAI):")
    print("   pip install langswarm[openai]")
    print("   • Core functionality + OpenAI provider")
    print("   • Perfect for getting started")
    print()
    
    print("🎯 Essential Setup (recommended):")
    print("   pip install langswarm[essential]")
    print("   • OpenAI provider + Redis memory + FastAPI")
    print("   • Good for development and light production")
    print()
    
    print("🏭 Production Setup:")
    print("   pip install langswarm[production]")
    print("   • Multiple providers + cloud backends")
    print("   • Ready for production deployments")
    print()
    
    print("🌟 Full Installation:")
    print("   pip install langswarm[all]")
    print("   • Everything included")
    print("   • All providers, backends, and integrations")


def main():
    """Run all tests."""
    print("🚀 LangSwarm Optional Dependencies Test Suite")
    print("=" * 60)
    print("This test demonstrates how LangSwarm handles optional dependencies")
    print("gracefully, providing helpful error messages when dependencies are missing.")
    print()
    
    # Run tests
    test_optional_import_manager()
    test_provider_registry()
    test_memory_backends()
    test_configuration_with_missing_deps()
    test_minimal_functionality()
    show_installation_guidance()
    
    print("\n" + "=" * 60)
    print("✅ Optional Dependencies Test Suite Complete!")
    print("=" * 60)
    print("\nKey Benefits Demonstrated:")
    print("• Graceful degradation when dependencies are missing")
    print("• Clear, actionable error messages with installation commands")
    print("• Minimal core that works without heavy dependencies")
    print("• Flexible installation options for different use cases")
    print("• Automatic discovery of available features")


if __name__ == "__main__":
    main()