
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langswarm.core.agents.builder import AgentBuilder
from langswarm.core.agents.interfaces import ProviderType

async def verify_litellm_integration():
    print("🧪 Verifying LiteLLM Integration...")
    
    # 1. Test Builder Configuration
    print("\n1. Testing Builder Configuration...")
    builder = AgentBuilder().litellm().model("gpt-4o")
    agent = await builder.build()
    
    assert agent.configuration.provider == ProviderType.LITELLM
    assert agent.configuration.model == "gpt-4o"
    print("✅ Builder configured correctly")
    
    # 2. Test Observability Configuration
    print("\n2. Testing Observability Configuration...")
    with patch("litellm.success_callback", []) as success_cb, \
         patch("litellm.failure_callback", []) as failure_cb:
        
        builder = AgentBuilder().litellm().observability(
            provider="langfuse",
            public_key="pk-test",
            secret_key="sk-test",
            host="https://test.langfuse.com"
        )
        
        # Check if callbacks were added
        import litellm
        assert "langfuse" in litellm.success_callback
        assert "langfuse" in litellm.failure_callback
        assert os.environ["LANGFUSE_PUBLIC_KEY"] == "pk-test"
        assert os.environ["LANGFUSE_SECRET_KEY"] == "sk-test"
        assert os.environ["LANGFUSE_HOST"] == "https://test.langfuse.com"
        print("✅ Observability configured correctly")
        
    # 3. Test Failover Configuration
    print("\n3. Testing Failover Configuration...")
    builder = AgentBuilder().litellm().failover(["claude-3-opus", "gemini-pro"])
    # Access private config to verify
    assert builder._provider_config["fallbacks"] == ["claude-3-opus", "gemini-pro"]
    print("✅ Failover configured correctly")
    
    # 4. Test Message Sending (Mocked)
    print("\n4. Testing Message Sending (Mocked)...")
    
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello from LiteLLM!"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    
    from unittest.mock import AsyncMock
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_response
        
        agent = await AgentBuilder().litellm().model("gpt-4o").build()
        response = await agent.chat("Hello")
        
        print(f"Response content: {response.content}")
        print(f"Response success: {response.success}")
        if not response.success:
            print(f"Response error: {response.error}")
        assert response.content == "Hello from LiteLLM!"
        assert response.usage.total_tokens == 15
        assert response.metadata["provider"] == "litellm"
        
        # Verify call args
        call_args = mock_acompletion.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert len(call_args["messages"]) > 0
        print("✅ Message sending works")

    print("\n🎉 All LiteLLM verification tests passed!")

if __name__ == "__main__":
    asyncio.run(verify_litellm_integration())
