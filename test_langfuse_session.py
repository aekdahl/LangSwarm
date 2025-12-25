#!/usr/bin/env python3
"""Test script to verify session_id is being passed to Langfuse."""

import asyncio
import logging

# Enable debug logging for the LiteLLM provider
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("langswarm.core.agents.providers.litellm").setLevel(logging.DEBUG)

async def test_session_id():
    from langswarm.core.agents import AgentBuilder
    
    print("=" * 60)
    print("Testing Langfuse Session ID Propagation")
    print("=" * 60)
    
    # Create agent
    agent = await AgentBuilder() \
        .openai() \
        .model("gpt-4o-mini") \
        .name("test-agent") \
        .build()
    
    print(f"\nAgent created: {agent.name}")
    print(f"Agent ID: {agent.agent_id}")
    
    # Make a chat call
    print("\n--- Making first chat call ---")
    response = await agent.chat("Hello, just testing session tracking.")
    print(f"Response: {response.content[:100] if response.content else 'No content'}...")
    
    # Check the current session
    if agent._current_session:
        print(f"\nCurrent session ID: {agent._current_session.session_id}")
    else:
        print("\n⚠️ No current session found!")
    
    # Make another call with the same session
    print("\n--- Making second chat call (same session) ---")
    response2 = await agent.chat("What did I just say?")
    print(f"Response: {response2.content[:100] if response2.content else 'No content'}...")
    
    if agent._current_session:
        print(f"\nFinal session ID: {agent._current_session.session_id}")
    
    print("\n" + "=" * 60)
    print("Check DEBUG logs above for 'Langfuse session_id set:' messages")
    print("If sessions are working, you should see the UUID in that log")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_session_id())
