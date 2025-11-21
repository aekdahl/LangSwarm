import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.anthropic import AnthropicProvider
from langswarm.core.agents.base import AgentConfiguration, AgentSession, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

# Mock classes for Anthropic events
class MockDelta:
    def __init__(self, type, text=None, partial_json=None):
        self.type = type
        self.text = text
        self.partial_json = partial_json

class MockContentBlock:
    def __init__(self, type, id=None, name=None, input=None):
        self.type = type
        self.id = id
        self.name = name
        self.input = input

class MockEvent:
    def __init__(self, type, delta=None, content_block=None):
        self.type = type
        self.delta = delta
        self.content_block = content_block

async def mock_anthropic_stream():
    # 1. Text content delta
    yield MockEvent(
        type="content_block_delta",
        delta=MockDelta(type="text_delta", text="Thinking...")
    )
    
    # 2. Tool use start
    yield MockEvent(
        type="content_block_start",
        content_block=MockContentBlock(
            type="tool_use",
            id="toolu_123",
            name="calculator"
        )
    )
    
    # 3. JSON delta part 1
    yield MockEvent(
        type="content_block_delta",
        delta=MockDelta(type="input_json_delta", partial_json='{"op": "add"')
    )
    
    # 4. JSON delta part 2
    yield MockEvent(
        type="content_block_delta",
        delta=MockDelta(type="input_json_delta", partial_json=', "a": 1, "b": 2}')
    )
    
    # 5. Tool use stop
    yield MockEvent(type="content_block_stop")
    
    # 6. Message stop
    yield MockEvent(type="message_stop")

async def run_reproduction():
    print("🚀 Starting Anthropic reproduction script...")
    
    # Mock anthropic module presence
    import sys
    sys.modules['anthropic'] = MagicMock()
    
    # Setup provider
    # We need to patch the module-level 'anthropic' variable in the provider file
    # or just instantiate it after mocking sys.modules if it checks on init
    
    # Re-import to pick up mocked module if needed, or just patch the class
    with unittest.mock.patch('langswarm.core.agents.providers.anthropic.anthropic', MagicMock()):
        provider = AnthropicProvider()
        # Mock client
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_anthropic_stream()
        provider._get_client = MagicMock(return_value=mock_client)
        
        # Mock tool definitions
        provider._build_tool_definitions = MagicMock(return_value=[])
        
        # Setup config
        config = AgentConfiguration(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-opus-20240229",
            api_key="mock-key",
            streaming_enabled=True,
            tools_enabled=True,
            available_tools=["calculator"]
        )
        session = AgentSession()
        message = AgentMessage(role="user", content="Calculate 1+2")
        
        print("\n📡 Processing stream...")
        last_response = None
        async for response in provider.stream_message(message, session, config):
            last_response = response
            if response.content:
                print(f"  Content chunk: {response.content}")
                
        print("\n🔍 Inspecting final response...")
        if last_response and last_response.message and last_response.message.tool_calls:
            print(f"  Tool calls found: {len(last_response.message.tool_calls)}")
            for i, tc in enumerate(last_response.message.tool_calls):
                print(f"  Tool Call #{i+1}: {tc}")
                if isinstance(tc, dict) and "input" in tc:
                    print(f"    Name: {tc['name']}")
                    print(f"    Input: {tc['input']}")
                    if tc['input'] == {"op": "add", "a": 1, "b": 2}:
                        print(f"    ✅ Input is correctly parsed JSON")
                    else:
                        print(f"    ❌ Input mismatch")
                else:
                    print(f"    ❌ Tool call structure is unexpected")
        else:
            print("❌ No tool calls found in final response!")

if __name__ == "__main__":
    asyncio.run(run_reproduction())
