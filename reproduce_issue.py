import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.openai import OpenAIProvider
from langswarm.core.agents.interfaces import ProviderType, AgentMessage
from langswarm.core.agents.base import AgentConfiguration, AgentSession

# Mock classes to simulate OpenAI streaming response
class MockDelta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

class MockChoice:
    def __init__(self, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason

class MockChunk:
    def __init__(self, choices):
        self.choices = choices

async def mock_openai_stream():
    # Chunk 1: "Thinking..." content
    yield MockChunk([MockChoice(MockDelta(content="Thinking..."))])
    
    # Chunk 2: Start tool call (index 0, id, type, function name part 1)
    yield MockChunk([MockChoice(MockDelta(tool_calls=[
        MagicMock(index=0, id="call_123", type="function", function=MagicMock(name="calculator", arguments=""))
    ]))])
    
    # Chunk 3: Tool call arguments part 1
    yield MockChunk([MockChoice(MockDelta(tool_calls=[
        MagicMock(index=0, function=MagicMock(arguments='{"op": "add"'))
    ]))])
    
    # Chunk 4: Tool call arguments part 2
    yield MockChunk([MockChoice(MockDelta(tool_calls=[
        MagicMock(index=0, function=MagicMock(arguments=', "a": 1, "b": 2}'))
    ]))])
    
    # Chunk 5: Finish
    yield MockChunk([MockChoice(MockDelta(content=None), finish_reason="tool_calls")])

async def run_reproduction():
    print("🚀 Starting reproduction script...")
    
    # Setup provider
    provider = OpenAIProvider()
    # Mock the client creation to return our mock stream
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_openai_stream()
    provider._get_client = MagicMock(return_value=mock_client)
    
    # Mock tool definitions to avoid registry lookup
    provider._build_tool_definitions = MagicMock(return_value=[
        {"type": "function", "function": {"name": "calculator", "description": "Calculate things"}}
    ])
    
    # Setup config and session
    config = AgentConfiguration(
        provider=ProviderType.OPENAI,
        model="gpt-4o",
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
            # Check if it's a valid object or a delta
            if hasattr(tc, 'function') and hasattr(tc.function, 'arguments'):
                print(f"    Name: {tc.function.name}")
                print(f"    Arguments: {tc.function.arguments}")
                try:
                    args = json.loads(tc.function.arguments)
                    print(f"    ✅ Arguments are valid JSON: {args}")
                except:
                    print(f"    ❌ Arguments are NOT valid JSON")
            else:
                print(f"    ❌ Tool call object structure is unexpected: {type(tc)}")
    else:
        print("❌ No tool calls found in final response!")

if __name__ == "__main__":
    asyncio.run(run_reproduction())
