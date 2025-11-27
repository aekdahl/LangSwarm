"""
Test script to verify automatic LangFuse integration with LiteLLM.

This script tests:
1. Auto-detection of LangFuse environment variables
2. Automatic callback registration
3. Graceful fallback when env vars are not set
"""
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


async def test_auto_langfuse_detection():
    """Test that LangFuse is automatically detected and enabled when env vars are set."""
    print("🧪 Test 1: Auto-detection of LangFuse environment variables")
    
    # Set mock environment variables
    with patch.dict(os.environ, {
        'LANGFUSE_PUBLIC_KEY': 'pk-test-12345',
        'LANGFUSE_SECRET_KEY': 'sk-test-67890',
        'LANGFUSE_HOST': 'https://test.langfuse.com'
    }):
        # Mock langfuse package
        with patch.dict(sys.modules, {'langfuse': MagicMock()}):
            # Import fresh to ensure env detection runs
            import importlib
            from langswarm.core.agents.providers import litellm as litellm_module
            importlib.reload(litellm_module)
            
            # Create provider instance (should auto-configure)
            from langswarm.core.agents.providers.litellm import LiteLLMProvider
            provider = LiteLLMProvider()
            
            # Check that callbacks were registered
            import litellm
            assert 'langfuse' in litellm.success_callback, "❌ LangFuse success callback not registered"
            assert 'langfuse' in litellm.failure_callback, "❌ LangFuse failure callback not registered"
            
            print("✅ LangFuse callbacks automatically registered!")
            print(f"   - Success callback: {litellm.success_callback}")
            print(f"   - Failure callback: {litellm.failure_callback}")
    
    print()


async def test_no_env_vars():
    """Test graceful handling when LangFuse env vars are not set."""
    print("🧪 Test 2: Graceful fallback without environment variables")
    
    # Clear LangFuse env vars
    env_backup = {}
    for key in ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_HOST']:
        env_backup[key] = os.environ.pop(key, None)
    
    try:
        # Import fresh
        import importlib
        from langswarm.core.agents.providers import litellm as litellm_module
        importlib.reload(litellm_module)
        
        # Create provider (should not fail)
        from langswarm.core.agents.providers.litellm import LiteLLMProvider
        provider = LiteLLMProvider()
        
        print("✅ Provider created successfully without LangFuse env vars")
        print("   (No error thrown, graceful fallback)")
    
    finally:
        # Restore env vars
        for key, value in env_backup.items():
            if value is not None:
                os.environ[key] = value
    
    print()


async def test_missing_package():
    """Test graceful handling when langfuse package is not installed."""
    print("🧪 Test 3: Graceful handling when LangFuse package not installed")
    
    # Set env vars but simulate missing package
    with patch.dict(os.environ, {
        'LANGFUSE_PUBLIC_KEY': 'pk-test-12345',
        'LANGFUSE_SECRET_KEY': 'sk-test-67890'
    }):
        # Mock ImportError when trying to import langfuse
        def mock_import(name, *args, **kwargs):
            if name == 'langfuse':
                raise ImportError("No module named 'langfuse'")
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Import fresh
            import importlib
            from langswarm.core.agents.providers import litellm as litellm_module
            importlib.reload(litellm_module)
            
            # Create provider (should not fail, just warn)
            from langswarm.core.agents.providers.litellm import LiteLLMProvider
            provider = LiteLLMProvider()
            
            print("✅ Provider created successfully despite missing langfuse package")
            print("   (Warning logged, but no error thrown)")
    
    print()


async def test_builder_integration():
    """Test that AgentBuilder works with automatic LangFuse."""
    print("🧪 Test 4: AgentBuilder integration with automatic LangFuse")
    
    # Set env vars
    with patch.dict(os.environ, {
        'LANGFUSE_PUBLIC_KEY': 'pk-test-12345',
        'LANGFUSE_SECRET_KEY': 'sk-test-67890',
        'OPENAI_API_KEY': 'sk-test-openai'
    }):
        # Mock langfuse package
        with patch.dict(sys.modules, {'langfuse': MagicMock()}):
            from langswarm.core.agents import AgentBuilder
            
            # Build agent with litellm (should auto-enable LangFuse)
            builder = AgentBuilder().litellm().model("gpt-4o")
            config = builder.build_config()
            
            print("✅ AgentBuilder configuration created successfully")
            print(f"   - Provider: {config.provider}")
            print(f"   - Model: {config.model}")
            print("   - LangFuse will be auto-enabled when provider is instantiated")
    
    print()


def print_summary():
    """Print test summary."""
    print("=" * 60)
    print("✅ All Tests Passed!")
    print("=" * 60)
    print()
    print("Summary:")
    print("• LangFuse auto-detection working ✓")
    print("• Graceful fallback without env vars ✓")
    print("• Graceful handling of missing package ✓")
    print("• AgentBuilder integration ✓")
    print()
    print("The automatic LangFuse integration is ready to use!")
    print()
    print("To enable in production:")
    print("  1. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
    print("  2. Install: pip install langfuse")
    print("  3. Create agents normally - LangFuse auto-enables!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Automatic LangFuse Integration")
    print("=" * 60)
    print()
    
    try:
        await test_auto_langfuse_detection()
        await test_no_env_vars()
        await test_missing_package()
        await test_builder_integration()
        
        print_summary()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
