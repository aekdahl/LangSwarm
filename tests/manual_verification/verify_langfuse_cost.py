
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langswarm.core.agents.builder import AgentBuilder
import litellm

async def verify_langfuse_cost():
    print("🧪 Verifying LangFuse Cost Tracking...")
    
    # Mock langfuse module to pass installation check
    with patch.dict(sys.modules, {"langfuse": MagicMock()}):
        
        # Mock LangFuse callbacks on the imported litellm module
        # We use a real list so we can check if items are appended
        litellm.success_callback = []
        litellm.failure_callback = []
        
        # Configure agent with LangFuse
        builder = AgentBuilder().litellm().model("gpt-4o").observability(
            provider="langfuse",
            public_key="pk-test",
            secret_key="sk-test",
            host="https://test.langfuse.com"
        )
        agent = await builder.build()
        
        # Mock LiteLLM response with usage
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70
        mock_response.model = "gpt-4o"
        
        # Mock cost calculation
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
             patch("litellm.completion_cost", return_value=0.002) as mock_cost:
            
            mock_acompletion.return_value = mock_response
            
            # Send message
            response = await agent.chat("Hello")
            
            # Verify cost was calculated
            assert response.usage.cost_estimate == 0.002
            print("✅ Cost calculated correctly in AgentResponse")
            
            # Verify LangFuse callback is registered
            # Verify LangFuse callback is registered
            assert "langfuse" in litellm.success_callback
            print("✅ LangFuse callback registered")
            
            # Note: We can't easily verify that LiteLLM *actually* called LangFuse 
            # without mocking the internal LangFuse logger inside LiteLLM, 
            # but knowing the callback is there and usage is present is strong evidence.
            
    print("\n🎉 LangFuse Cost Verification Passed!")

if __name__ == "__main__":
    asyncio.run(verify_langfuse_cost())
