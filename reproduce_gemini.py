import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.gemini import GeminiProvider
from langswarm.core.agents.base import AgentConfiguration, AgentSession, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

# Mock classes for Gemini objects
class MockFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class MockPart:
    def __init__(self, text=None, function_call=None):
        self.text = text
        self.function_call = function_call

class MockChunk:
    def __init__(self, text=None, parts=None):
        self.text = text
        self.parts = parts if parts else []

async def mock_gemini_stream():
    # 1. Text chunk
    yield MockChunk(
        text="Sure, I can calculate that.",
        parts=[MockPart(text="Sure, I can calculate that.")]
    )
    
    # 2. Function call chunk
    yield MockChunk(
        text=None,
        parts=[MockPart(function_call=MockFunctionCall(
            name="calculator",
            args={"op": "add", "a": 1, "b": 2}
        ))]
    )

async def run_reproduction():
    print("🚀 Starting Gemini reproduction script...")
    
    # Mock google.generativeai module
    import sys
    sys.modules['google'] = MagicMock()
    sys.modules['google.generativeai'] = MagicMock()
    sys.modules['google.generativeai.types'] = MagicMock()
    
    # Patch module-level genai in provider
    with unittest.mock.patch('langswarm.core.agents.providers.gemini.genai', MagicMock()):
        provider = GeminiProvider()
        
        # Mock model
        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_gemini_stream())
        provider._get_model = MagicMock(return_value=mock_model)
        
        # Mock tool definitions
        provider._build_tool_definitions = MagicMock(return_value=[])
        
        # Setup config
        config = AgentConfiguration(
            provider=ProviderType.GEMINI,
            model="gemini-pro",
            api_key="mock-key",
            streaming_enabled=True,
            tools_enabled=True,
            available_tools=["calculator"]
        )
        session = AgentSession()
        message = AgentMessage(role="user", content="Calculate 1+2")
        
        print("\n📡 Processing stream...")
        last_response = None
        # We need to mock asyncio.to_thread because stream_message uses it to call generate_content
        # But here we want to return our async generator directly.
        # However, generate_content is usually synchronous returning an iterable, 
        # OR if stream=True it returns a generation object which is iterable.
        # In provider: response_stream = await asyncio.to_thread(model.generate_content, ..., stream=True)
        # So we need to mock asyncio.to_thread to return our async generator? 
        # No, asyncio.to_thread runs a sync function in a thread.
        # Our mock_gemini_stream is async generator.
        # Let's just mock stream_message to call _process_gemini_stream directly with our mock stream
        # Or better, mock asyncio.to_thread to return the stream.
        
        # Actually, the provider code:
        # response_stream = await asyncio.to_thread(model.generate_content, prompt, stream=True)
        # async for chunk in self._process_gemini_stream(response_stream, ...):
        
        # If we mock asyncio.to_thread to return mock_gemini_stream(), 
        # then _process_gemini_stream will iterate over it.
        # But mock_gemini_stream() is an async generator.
        # _process_gemini_stream iterates with `for chunk in stream:` (synchronous iteration?)
        # Wait, Gemini stream is synchronous iterator usually?
        # "async for chunk in self._process_gemini_stream(response_stream...)"
        # Inside _process_gemini_stream: "for chunk in stream:"
        # So stream must be a sync iterator or iterable.
        
        # Let's change mock_gemini_stream to be a sync generator or list
        def mock_sync_stream():
            yield MockChunk(
                text="Sure, I can calculate that.",
                parts=[MockPart(text="Sure, I can calculate that.")]
            )
            yield MockChunk(
                text=None,
                parts=[MockPart(function_call=MockFunctionCall(
                    name="calculator",
                    args={"op": "add", "a": 1, "b": 2}
                ))]
            )
            
        with unittest.mock.patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_sync_stream()
            
            async for response in provider.stream_message(message, session, config):
                last_response = response
                if response.content:
                    print(f"  Content chunk: {response.content}")
            
            print("\n🔍 Inspecting final response...")
            if last_response and last_response.message and last_response.message.tool_calls:
                print(f"  Tool calls found: {len(last_response.message.tool_calls)}")
                for i, tc in enumerate(last_response.message.tool_calls):
                    print(f"  Tool Call #{i+1}: {tc}")
                    if tc['name'] == "calculator" and tc['arguments'] == {"op": "add", "a": 1, "b": 2}:
                         print(f"    ✅ Tool call matches expected")
                    else:
                         print(f"    ❌ Tool call mismatch")
            else:
                print("❌ No tool calls found in final response!")

if __name__ == "__main__":
    asyncio.run(run_reproduction())
