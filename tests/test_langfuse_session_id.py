
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langswarm.core.agents.providers.litellm import LiteLLMProvider
from langswarm.core.agents.base import AgentSession, AgentConfiguration, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

@pytest.mark.asyncio
async def test_session_id_propagation():
    # Setup
    with patch('langswarm.core.agents.providers.litellm.litellm') as mock_litellm:
        # Mock acompletion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="response", tool_calls=None), finish_reason="stop")]
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        
        provider = LiteLLMProvider()
        config = AgentConfiguration(
            provider=ProviderType.LITELLM,
            model="gpt-4"
        )
        session = AgentSession(session_id="test-session-123")
        message = AgentMessage(role="user", content="Hello")
        
        # Act
        await provider.send_message(message, session, config)
        
        # Assert
        # Check if acompletion was called with metadata={'session_id': 'test-session-123'}
        call_kwargs = mock_litellm.acompletion.call_args.kwargs
        print(f"\nCall kwargs: {call_kwargs}")
        
        if "metadata" in call_kwargs and call_kwargs["metadata"].get("session_id") == "test-session-123":
            print("✅ SUCCESS: session_id found in metadata")
            return True
        else:
            print("❌ FAILURE: session_id NOT found in metadata")
            return False

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_session_id_propagation())
    if not success:
        exit(1)
