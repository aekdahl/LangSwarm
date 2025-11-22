import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.openai import OpenAIProvider
from langswarm.core.agents.base import AgentConfiguration, AgentSession, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

# Mock classes for OpenAI events
class MockDelta:
    def __init__(self, content=None, tool_calls=None, refusal=None):
        self.content = content
        self.tool_calls = tool_calls
        self.refusal = refusal

class MockChoice:
    def __init__(self, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason

class MockChunk:
    def __init__(self, choices):
        self.choices = choices

async def mock_openai_stream():
    # 1. Role chunk (no content)
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None))])
    
    # 2. Refusal chunk
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None, refusal="I cannot do that."))])
    
    # 3. Finish chunk
    yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None), finish_reason="stop")])

async def run_reproduction():
    print("🚀 Starting OpenAI content reproduction script...")
    
    # Mock openai module
    import sys
    sys.modules['openai'] = MagicMock()
    
    # Patch module-level openai in provider
    with unittest.mock.patch('langswarm.core.agents.providers.openai.AsyncOpenAI', MagicMock()):
        provider = OpenAIProvider()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_openai_stream()
        provider._get_client = MagicMock(return_value=mock_client)
        
        # Setup config
        config = AgentConfiguration(
            provider=ProviderType.OPENAI,
            model="gpt-4",
            api_key="mock-key",
            streaming_enabled=True
        )
        session = AgentSession()
        message = AgentMessage(role="user", content="Say hello")
        
        print("\n📡 Processing stream...")
        chunk_count = 0
        async for chunk in provider.stream_message(message, session, config):
            if chunk.success and chunk.content:
                chunk_count += 1
                print(f"  Chunk #{chunk_count}: '{chunk.content}'")
            elif chunk.metadata.get('stream_complete'):
                print("  ✅ Stream complete signal received")
            else:
                print(f"  ⚠️ Empty/Unsuccessful chunk: success={chunk.success}, content='{chunk.content}'")
                
        print(f"\nTotal chunks received: {chunk_count}")
        if chunk_count == 1:
            print("✅ Verification PASSED: Received exactly 1 content chunk (refusal).")
        else:
            print(f"❌ Verification FAILED: Expected 1 chunk, got {chunk_count}.")

if __name__ == "__main__":
    import unittest
    asyncio.run(run_reproduction())
