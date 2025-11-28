
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_wrapper")

try:
    import langfuse
    print(f"📦 Langfuse version: {langfuse.version.__version__}")
except ImportError:
    print("❌ Langfuse not installed")
    sys.exit(1)

def test_wrapper():
    print("\n🔍 Inspecting Original Langfuse Class:")
    OriginalLangfuse = langfuse.Langfuse
    print(f"   Type: {type(OriginalLangfuse)}")
    print(f"   Has 'trace' method: {hasattr(OriginalLangfuse, 'trace')}")
    
    # Create an instance of original to check instance attributes
    try:
        # We need dummy credentials
        instance = OriginalLangfuse(public_key="pk-dummy", secret_key="sk-dummy", host="https://dummy.com")
        print(f"   Instance has 'trace': {hasattr(instance, 'trace')}")
    except Exception as e:
        print(f"   ❌ Failed to instantiate original: {e}")

    print("\n🛠️  Applying Monkeypatch...")
    
    class LangfuseWrapper(OriginalLangfuse):
        def __init__(self, **kwargs):
            print("   Wrapper __init__ called")
            # Strip unsupported arguments
            if 'sdk_integration' in kwargs:
                print(f"   Removing sdk_integration: {kwargs['sdk_integration']}")
                kwargs.pop('sdk_integration')
            super().__init__(**kwargs)
            
    # Replace
    langfuse.Langfuse = LangfuseWrapper
    
    print("\n🔍 Inspecting Wrapper Class:")
    print(f"   Type: {type(langfuse.Langfuse)}")
    print(f"   Has 'trace' method: {hasattr(langfuse.Langfuse, 'trace')}")
    
    print("\n🧪 Testing Wrapper Instantiation & Trace:")
    try:
        # Simulate LiteLLM call with the problematic argument
        wrapper_instance = langfuse.Langfuse(
            public_key="pk-dummy", 
            secret_key="sk-dummy", 
            host="https://dummy.com",
            sdk_integration="litellm" 
        )
        print(f"   Wrapper Instance created: {wrapper_instance}")
        print(f"   Wrapper Instance has 'trace': {hasattr(wrapper_instance, 'trace')}")
        
        if hasattr(wrapper_instance, 'trace'):
            print("   ✅ trace method exists!")
        else:
            print("   ❌ trace method MISSING!")
            # Inspect dir
            print(f"   Dir(instance): {dir(wrapper_instance)}")
            
    except Exception as e:
        print(f"   ❌ Failed to instantiate wrapper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wrapper()
