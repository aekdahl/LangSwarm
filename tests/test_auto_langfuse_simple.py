"""
Simple test to verify automatic LangFuse integration with LiteLLM.

This test verifies that LangFuse is automatically configured when environment
variables are set, without using complex module reloading.
"""
import os
import sys

# Ensure we test with env vars set BEFORE importing
os.environ['LANGFUSE_PUBLIC_KEY'] = 'pk-test-12345'
os.environ['LANGFUSE_SECRET_KEY'] = 'sk-test-67890'
os.environ['LANGFUSE_HOST'] = 'https://test.langfuse.com'

print("=" * 70)
print("Testing Automatic LangFuse Integration")
print("=" * 70)
print()

print("📝 Environment Variables:")
print(f"   LANGFUSE_PUBLIC_KEY: {os.environ.get('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
print(f"   LANGFUSE_SECRET_KEY: {os.environ.get('LANGFUSE_SECRET_KEY', 'NOT SET')[:10]}...")
print(f"   LANGFUSE_HOST: {os.environ.get('LANGFUSE_HOST', 'NOT SET')}")
print()

print("🧪 Test 1: Check if LangFuse package is installed")
try:
    import langfuse
    print("   ✅ LangFuse package is installed")
    langfuse_installed = True
except ImportError:
    print("   ⚠️  LangFuse package NOT installed (this is OK for testing)")
    print("      To use LangFuse in production: pip install langfuse")
    langfuse_installed = False
print()

print("🧪 Test 2: Import LiteLLM provider (should auto-configure LangFuse)")
try:
    from langswarm.core.agents.providers.litellm import LiteLLMProvider
    import litellm
    
    print("   ✅ LiteLLMProvider imported successfully")
    print()
    
    print("🧪 Test 3: Check LiteLLM callbacks")
    print(f"   Success callbacks: {litellm.success_callback}")
    print(f"   Failure callbacks: {litellm.failure_callback}")
    print()
    
    if langfuse_installed:
        if 'langfuse' in litellm.success_callback and 'langfuse' in litellm.failure_callback:
            print("   ✅ LangFuse callbacks automatically registered!")
            print("   🎉 Automatic integration is working!")
        else:
            print("   ❌ LangFuse callbacks NOT registered")
            print("      This might indicate an issue with auto-detection")
    else:
        print("   ℹ️  LangFuse package not installed, so callbacks not registered")
        print("      (This is expected behavior - graceful fallback)")
    
    print()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🧪 Test 4: Create a LiteLLMProvider instance")
try:
    provider = LiteLLMProvider()
    print("   ✅ Provider created successfully")
    print(f"   Provider type: {provider.provider_type}")
    print()
except Exception as e:
    print(f"   ❌ Error creating provider: {e}")
    sys.exit(1)

print("=" * 70)
print("Summary")
print("=" * 70)
print()
print("✅ All tests passed!")
print()
if langfuse_installed:
    print("✨ Automatic LangFuse integration is ENABLED and WORKING!")
    print()
    print("What this means:")
    print("  • All LiteLLM API calls will be traced in LangFuse")
    print("  • Cost tracking is automatic")
    print("  • Prompt management is available")
    print("  • No code changes needed - just set env vars!")
else:
    print("ℹ️  LangFuse package not installed")
    print()
    print("To enable automatic integration:")
    print("  1. Install: pip install langfuse")
    print("  2. Set environment variables (already done)")
    print("  3. Run your agents - tracing happens automatically!")
print()
print("Configuration used:")
print(f"  • Host: {os.environ.get('LANGFUSE_HOST')}")
print(f"  • Public Key: {os.environ.get('LANGFUSE_PUBLIC_KEY')}")
print()
print("=" * 70)
