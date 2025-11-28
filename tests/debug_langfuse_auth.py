
import os
import sys
import logging

# Configure logging to see our debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_langfuse")

# Mock environment variables BEFORE importing langswarm
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-mock-123"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-mock-456"
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import litellm
    print(f"📦 LiteLLM version: {getattr(litellm, '__version__', 'unknown')}")
except ImportError:
    print("❌ LiteLLM not installed")
    sys.exit(1)

try:
    import langfuse
    print(f"📦 Langfuse version: {getattr(langfuse, '__version__', 'unknown')}")
except ImportError:
    print("❌ Langfuse not installed")
    # We continue to see if the provider handles this gracefully or if this is the issue
    
from langswarm.core.agents.providers.litellm import LiteLLMProvider

def debug_langfuse_setup():
    print("\n🔍 Initializing LiteLLMProvider...")
    provider = LiteLLMProvider()
    
    print("\n👀 Checking LiteLLM Callbacks:")
    print(f"   Success Callbacks: {litellm.success_callback}")
    print(f"   Failure Callbacks: {litellm.failure_callback}")
    
    if "langfuse" in litellm.success_callback:
        print("\n✅ Langfuse is REGISTERED in success_callback")
    else:
        print("\n❌ Langfuse is NOT registered in success_callback")

    if "langfuse" in litellm.failure_callback:
        print("✅ Langfuse is REGISTERED in failure_callback")
    else:
        print("❌ Langfuse is NOT registered in failure_callback")

if __name__ == "__main__":
    debug_langfuse_setup()
