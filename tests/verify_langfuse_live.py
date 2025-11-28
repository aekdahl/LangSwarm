
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set USER PROVIDED credentials
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-2c12a9d2-30ec-4044-a453-32e3bb0efb62"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-8f8dd993-babe-4203-b108-9cd5523308b0"
os.environ["LANGFUSE_BASE_URL"] = "https://cloud.langfuse.com"

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langswarm.core.agents.builder import AgentBuilder
from langswarm.core.agents.base import AgentMessage
from langswarm.core.agents.interfaces import ProviderType

async def verify_live():
    print("🚀 Starting Live Langfuse Verification...")
    
    try:
        # Build agent (this triggers auto-configuration)
        print("   Building agent...")
        agent = await AgentBuilder()\
            .litellm()\
            .model("gpt-3.5-turbo")\
            .system_prompt("You are a test agent.")\
            .build()
            
        print("✅ Agent built successfully.")
        
        # Check internal state
        import litellm
        print(f"   LiteLLM Success Callbacks: {litellm.success_callback}")
        
        if "langfuse" in litellm.success_callback:
            print("✅ Langfuse registered in callbacks.")
        else:
            print("❌ Langfuse NOT registered!")
            return

        # We can't easily make a real LLM call without an OpenAI key.
        # But we can check if the Langfuse SDK initialized correctly.
        import langfuse
        print(f"   Langfuse SDK version: {langfuse.version.__version__}")
        
        # If we have an OpenAI key in env, we could try a real call.
        if os.getenv("OPENAI_API_KEY"):
            print("   OpenAI Key found. Attempting real generation...")
            response = await agent.chat("Hello, this is a test for Langfuse.")
            print(f"   Response: {response.content}")
            print("✅ Chat completed. Check Langfuse dashboard.")
        else:
            print("⚠️  No OPENAI_API_KEY found. Skipping real chat generation.")
            print("   (Langfuse requires a real generation to show data, but setup looks correct)")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_live())
