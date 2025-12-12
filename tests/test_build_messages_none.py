"""Unit test for _build_messages with None message (tool continuation)"""
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Mock litellm before importing langswarm
mock_litellm = MagicMock()
mock_litellm.success_callback = []
mock_litellm.failure_callback = []
sys.modules["litellm"] = mock_litellm
sys.modules["litellm.utils"] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langswarm.core.agents.providers.litellm import LiteLLMProvider
from langswarm.core.agents.base import AgentSession, AgentMessage, AgentConfiguration
from langswarm.core.agents.interfaces import ProviderType

async def test_build_messages_with_none():
    print("Testing _build_messages with None message (tool continuation)...")
    
    # Create provider
    provider = LiteLLMProvider()
    
    # Create session with tool results
    session = AgentSession()
    
    # Add conversation history
    await session.add_message(AgentMessage(role="user", content="What's the weather?"))
    await session.add_message(AgentMessage(
        role="assistant", 
        content="",
        tool_calls=[{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{}"}}]
    ))
    await session.add_message(AgentMessage(
        role="tool",
        content='{"temp": 72, "condition": "sunny"}',
        tool_call_id="call_123"
    ))
    
    # Create mock config
    config = MagicMock()
    config.system_prompt = "You are helpful."
    config.tools_enabled = False
    config.available_tools = []
    config.max_tokens = None
    
    # Test with None message (tool continuation)
    messages = await provider._build_messages(session, None, config)
    
    print(f"Messages built: {len(messages)}")
    for i, msg in enumerate(messages):
        role = msg.get('role')
        content = msg.get('content', '')[:50]
        print(f"  {i}: role={role}, content={content}...")
    
    # Verify no extra user message was added
    last_msg = messages[-1]
    if last_msg['role'] == 'tool':
        print("✅ Last message is 'tool' - no spurious user message added!")
        return True
    else:
        print(f"❌ Last message has role '{last_msg['role']}' - expected 'tool'")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_build_messages_with_none())
    sys.exit(0 if result else 1)
