import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langswarm.core.agents.builder import AgentBuilder
from langswarm.core.agents.interfaces import ProviderType

async def test_provider_method():
    """Test the .provider() method to reproduce the spawning issue"""
    print("🧪 Testing .provider() method...")
    
    # Set a mock API key for testing
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    
    try:
        # Test 1: Using .provider() directly
        print("\n1. Testing builder.provider(ProviderType.OPENAI)...")
        builder = AgentBuilder()
        builder.provider(ProviderType.OPENAI)
        builder.model("gpt-4o")
        
        config = builder.build_config()
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model}")
        print(f"   API Key: {config.api_key}")
        
        if not config.api_key:
            print("   ❌ API Key is None! This will cause provider initialization to fail.")
        else:
            print("   ✅ API Key is set")
            
        # Test 2: Using .openai() method (for comparison)
        print("\n2. Testing builder.openai() (for comparison)...")
        builder2 = AgentBuilder()
        builder2.openai()
        builder2.model("gpt-4o")
        
        config2 = builder2.build_config()
        print(f"   Provider: {config2.provider}")
        print(f"   Model: {config2.model}")
        print(f"   API Key: {config2.api_key}")
        
        if config2.api_key:
            print("   ✅ API Key is set by .openai()")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_provider_method())
