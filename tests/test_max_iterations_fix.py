
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from langswarm.core.agents.base import BaseAgent, AgentConfiguration, AgentResponse, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_max_iterations_fix():
    print("🧪 Testing max_tool_iterations fix...")
    
    # Mock configuration
    config = MagicMock(spec=AgentConfiguration)
    config.provider = ProviderType.OPENAI
    config.model = "gpt-4o"
    config.max_tool_iterations = 2
    config.tools_enabled = True
    config.streaming_enabled = False
    config.max_memory_messages = 10
    
    # Mock provider
    provider = MagicMock()
    
    # Create agent
    agent = BaseAgent("test_agent", config, provider)
    
    # Mock internal methods
    agent._get_or_create_session = AsyncMock()
    session = MagicMock()
    session.session_id = "test_session"
    session.add_message = AsyncMock()
    agent._get_or_create_session.return_value = session
    
    agent._persist_to_memory = AsyncMock()
    agent._update_statistics = MagicMock()
    agent._auto_record_metric = MagicMock()
    agent._auto_log = MagicMock()
    agent._auto_trace = MagicMock()
    
    # Mock _execute_tool_calls to verify it's called
    agent._execute_tool_calls = AsyncMock()
    
    # Setup provider responses to simulate a loop that hits the limit
    # Response 1: Tool call (iteration 0)
    msg1 = AgentMessage(role="assistant", content="", tool_calls=[{"id": "call_1", "function": {"name": "tool1", "arguments": "{}"}}])
    resp1 = AgentResponse(content="", message=msg1, success=True)
    
    # Response 2: Tool call (iteration 1)
    msg2 = AgentMessage(role="assistant", content="", tool_calls=[{"id": "call_2", "function": {"name": "tool2", "arguments": "{}"}}])
    resp2 = AgentResponse(content="", message=msg2, success=True)
    
    # Response 3: Tool call (iteration 2 - LIMIT REACHED)
    msg3 = AgentMessage(role="assistant", content="", tool_calls=[{"id": "call_3", "function": {"name": "tool3", "arguments": "{}"}}])
    resp3 = AgentResponse(content="", message=msg3, success=True)
    
    # Configure provider to return these responses in sequence
    # 1. Initial call
    # 2. Continuation after tool 1
    # 3. Continuation after tool 2
    provider.send_message = AsyncMock(side_effect=[resp1, resp2, resp3])
    
    # Run chat
    print("   Running chat loop...")
    await agent.chat("Start")
    
    # Verification
    # We expect _execute_tool_calls to be called 3 times:
    # 1. For resp1 (iteration 0)
    # 2. For resp2 (iteration 1)
    # 3. For resp3 (iteration 2 - LIMIT REACHED) -> THIS IS THE FIX
    
    call_count = agent._execute_tool_calls.call_count
    print(f"   _execute_tool_calls called {call_count} times")
    
    if call_count == 3:
        print("✅ Fix verified: Pending tools executed when limit reached")
    else:
        print(f"❌ Fix failed: Expected 3 calls, got {call_count}")

    # Verify session.add_message was NOT called for the final response (since _execute_tool_calls handles it)
    # session.add_message is called:
    # 1. User message
    # 2. _execute_tool_calls calls it internally (we mocked it, so it won't)
    # 3. Final response (if handled by chat)
    
    # Since we mocked _execute_tool_calls, it didn't add messages.
    # We just want to ensure `chat` didn't add the final message manually.
    # We can check if `session.add_message` was called with `msg3`.
    
    # Filter calls to add_message with msg3
    msg3_calls = [call for call in session.add_message.mock_calls if msg3 in call.args]
    if len(msg3_calls) == 0:
        print("✅ Fix verified: Final response not double-added to session")
    else:
        print("❌ Fix failed: Final response added to session manually (double add risk)")

async def main():
    await test_max_iterations_fix()

if __name__ == "__main__":
    asyncio.run(main())
