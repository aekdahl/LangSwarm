
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.providers.litellm import LiteLLMProvider
from langswarm.core.agents.base import AgentSession, AgentConfiguration, AgentMessage
from langswarm.core.agents.interfaces import ProviderType

@pytest.mark.asyncio
async def test_duplicate_message_prevention():
    # Setup
    provider = LiteLLMProvider()
    config = AgentConfiguration(
        provider=ProviderType.LITELLM,
        model="gpt-4",
        max_tokens=4096
    )
    session = AgentSession()
    
    # Case 1: Message ALREADY in session (Standard Chat Flow)
    # BaseAgent adds message to session before calling send_message
    user_msg = AgentMessage(role="user", content="Hello world")
    await session.add_message(user_msg)
    
    # Build messages
    messages = await provider._build_messages(session, user_msg, config)
    
    print(f"\nCase 1 (Chat): Session has {len(session.messages)} msgs. Result has {len(messages)} msgs.")
    for i, m in enumerate(messages):
        print(f"  {i}: {m['role']} - {m['content']}")
        
    # Expectation: Should NOT duplicate. 
    # Current buggy behavior: Duplicates (len=2)
    # Desired behavior: No duplicate (len=1)
    
    # Case 2: Message NOT in session (Continuation/Loop Flow)
    # BaseAgent creates empty continuation message but DOES NOT add to session
    continuation_msg = AgentMessage(role="user", content="")
    
    messages_cont = await provider._build_messages(session, continuation_msg, config)
    
    print(f"\nCase 2 (Loop): Session has {len(session.messages)} msgs. Result has {len(messages_cont)} msgs.")
    for i, m in enumerate(messages_cont):
        print(f"  {i}: {m['role']} - {m['content']}")

    # Expectation: Should append. (len=2: "Hello world", "")
    
    return messages, messages_cont

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    m1, m2 = loop.run_until_complete(test_duplicate_message_prevention())
    
    # Assertions for VERIFICATION (asserting the BUG is FIXED)
    # If fixed, m1 has 1 message (no duplicate)
    if len(m1) == 1:
        print("\n✅ VERIFICATION SUCCESSFUL: No duplicates found!")
    else:
        print(f"\n❌ VERIFICATION FAILED: Found {len(m1)} messages (expected 1).")
