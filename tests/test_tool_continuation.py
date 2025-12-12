"""Quick verification that tool continuation with None message works"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langswarm.core.agents.builder import AgentBuilder

async def test_tool_continuation():
    print("Testing tool continuation with None message...")
    
    try:
        # Build agent with a simple tool
        agent = await (AgentBuilder()
            .litellm()
            .model("gpt-4o-mini")
            .system_prompt("You are a helpful assistant. Use the weather tool when asked about weather.")
            .tools(["weather"])  # Assuming weather tool exists
            .build())
        
        # This should trigger a tool call
        response = await agent.chat("What's the weather in Paris?")
        
        print(f"Response: {response.content[:200]}...")
        print(f"Success: {response.success}")
        
        if response.success:
            print("✅ Tool continuation works!")
        else:
            print(f"❌ Error: {response.error}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_continuation())
