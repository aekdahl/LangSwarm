import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.openai import OpenAIProvider
from langswarm.core.agents.base import AgentConfiguration, AgentSession, AgentMessage, BaseAgent
from langswarm.core.agents.interfaces import ProviderType, IAgentResponse

# Mock classes
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

# Mock tool
class MockTool:
    def __init__(self):
        self.name = "mock_tool"
        self.description = "A mock tool"
    
    async def execute(self, **kwargs):
        print("  🔨 MockTool.execute called!")
        return "Tool executed successfully"

async def mock_openai_stream_with_tool():
    print("  📡 Stream 1: Sending tool call chunk...")
    # 1. Tool call chunk
    tool_call = MagicMock()
    tool_call.index = 0
    tool_call.id = "call_123"
    tool_call.type = "function"
    tool_call.function.name = "mock_tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None, tool_calls=[tool_call]))])
    
    # 2. Finish chunk (tool_calls)
    print("  📡 Stream 1: Sending finish chunk (tool_calls)...")
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None), finish_reason="tool_calls")])

async def mock_openai_stream_final_response():
    print("  📡 Stream 2: Sending final response chunks...")
    # 1. Content chunk 1
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content="Final "))])
    
    # 2. Content chunk 2
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content="response"))])
    
    # 3. Finish chunk
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None), finish_reason="stop")])

async def run_reproduction():
    print("🚀 Starting dev102 bug reproduction script...")
    
    # Mock openai module
    import sys
    sys.modules['openai'] = MagicMock()
    
    # Patch module-level openai in provider
    with unittest.mock.patch('langswarm.core.agents.providers.openai.AsyncOpenAI', MagicMock()):
        # Create agent with mocked provider
        config = AgentConfiguration(
            provider=ProviderType.OPENAI,
            model="gpt-4",
            api_key="mock-key",
            streaming_enabled=True,
            tools_enabled=True,
            available_tools=["mock_tool"]
        )
        
        provider = OpenAIProvider()
        # Mock tool definitions to bypass registry lookup
        provider._build_tool_definitions = MagicMock(return_value=[{
            "type": "function",
            "function": {
                "name": "mock_tool",
                "description": "A mock tool",
                "parameters": {"type": "object", "properties": {}}
            }
        }])
        
        # Mock client
        mock_client = AsyncMock()
        # First call returns tool call stream, second call returns final response stream
        mock_client.chat.completions.create.side_effect = [
            mock_openai_stream_with_tool(),
            mock_openai_stream_final_response()
        ]
        provider._get_client = MagicMock(return_value=mock_client)
        
        agent = BaseAgent("test_agent", config, provider)
        
        # Register mock tool
        agent._tools["mock_tool"] = MockTool()
        
        session = await agent.create_session()
        message = "Use the mock tool"
        
        print("\n📡 Calling agent.stream_chat()...")
        chunks = []
        chunk_count = 0
        async for chunk in agent.stream_chat(message, session.session_id):
            chunk_count += 1
            print(f"  📦 Chunk #{chunk_count}: success={chunk.success}, content='{chunk.content}', finish_reason='{chunk.metadata.get('finish_reason')}'")
            
            if chunk.success and chunk.content:
                chunks.append(chunk.content)
            elif chunk.metadata.get('stream_complete'):
                print("  ✅ Stream complete signal received")
            elif chunk.message and chunk.message.tool_calls:
                print(f"  🛠️ Tool call detected in chunk: {len(chunk.message.tool_calls)}")
        
        full_response = "".join(chunks)
        print(f"\nFull response: '{full_response}'")
        
        if "Final response" in full_response:
            print("✅ Verification PASSED: Received final response after tool execution.")
        else:
            print("❌ Verification FAILED: Did not receive final response after tool execution.")

if __name__ == "__main__":
    import unittest
    asyncio.run(run_reproduction())
