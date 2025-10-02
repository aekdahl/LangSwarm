#!/usr/bin/env python3
"""
Demo: Integrated Session Management with LangSwarm AgentWrapper

This demo shows how the PRIORITY 5 session management system works seamlessly
with the existing LangSwarm chat() method, using real agents instead of mocked responses.

The session management is now fully integrated into the AgentWrapper class:
- Automatic session creation and management
- Session persistence across conversations
- Resume capability for interrupted sessions
- Multi-provider session support
- Real agent responses with conversation history

Usage:
    python demo_integrated_session_management.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the LangSwarm module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langswarm.core.wrappers.generic import AgentWrapper
from langswarm.core.session.models import SessionControl

# Try to import OpenAI for real agent testing
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. Using mock agent for demo.")

def create_demo_agent():
    """Create a demo agent for testing"""
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        # Real OpenAI agent
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return AgentWrapper(
            name="OpenAI_Assistant",
            agent=client,
            model="gpt-3.5-turbo",
            session_storage_config={"type": "sqlite", "path": "demo_sessions.db"}
        )
    else:
        # Mock agent for demonstration - make it callable like a HuggingFace agent
        class MockCallableAgent:
            def __init__(self):
                self.conversation_count = 0
                self.model = "mock-model"
                self.task = "text-generation"  # HuggingFace-like attributes
                
            def __call__(self, context):
                self.conversation_count += 1
                if isinstance(context, list):
                    context = " ".join([msg.get("content", str(msg)) for msg in context])
                return f"Demo response #{self.conversation_count}: I received your message '{context}'"
        
        return AgentWrapper(
            name="Demo_Agent",
            agent=MockCallableAgent(),
            model="openai-mock",  # Use openai prefix for adapter compatibility
            session_storage_config={"type": "memory"}
        )

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def print_chat_message(role, content, session_id=None):
    """Print a formatted chat message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    session_info = f" [Session: {session_id}]" if session_id else ""
    print(f"[{timestamp}]{session_info} {role.title()}: {content}")

def demo_basic_session_chat():
    """Demo basic session-enabled chat"""
    print_header("Demo 1: Basic Session-Enabled Chat")
    
    agent = create_demo_agent()
    
    print("Creating agent with integrated session management...")
    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Session Manager: {type(agent.session_manager).__name__}")
    
    print_section("Starting conversation with automatic session creation")
    
    # First message - automatically creates session
    response1 = agent.chat("Hello, this is my first message!")
    print_chat_message("User", "Hello, this is my first message!", agent.current_session_id)
    print_chat_message("Agent", response1, agent.current_session_id)
    
    # Second message - continues in same session
    response2 = agent.chat("Do you remember my first message?")
    print_chat_message("User", "Do you remember my first message?", agent.current_session_id)
    print_chat_message("Agent", response2, agent.current_session_id)
    
    # Show session history
    print_section("Session History")
    history = agent.get_session_history()
    print(f"Session ID: {agent.current_session_id}")
    print(f"Total messages: {len(history)}")
    for i, msg in enumerate(history):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
    
    return agent

def demo_explicit_session_management():
    """Demo explicit session creation and management"""
    print_header("Demo 2: Explicit Session Management")
    
    agent = create_demo_agent()
    
    print_section("Creating named session")
    
    # Start a named session
    session_id = agent.start_session("customer_support_session", 
                                   metadata={"customer_id": "12345", "topic": "billing"})
    print(f"Started session: {session_id}")
    
    # Chat in the named session
    response1 = agent.chat("I have a billing question", session_id=session_id)
    print_chat_message("User", "I have a billing question", session_id)
    print_chat_message("Agent", response1, session_id)
    
    response2 = agent.chat("Can you help me understand my charges?", session_id=session_id)
    print_chat_message("User", "Can you help me understand my charges?", session_id)
    print_chat_message("Agent", response2, session_id)
    
    # End the session
    agent.end_session(session_id)
    print(f"Ended session: {session_id}")
    
    return agent

def demo_session_resumption():
    """Demo session resumption capabilities"""
    print_header("Demo 3: Session Resumption")
    
    # First agent instance
    agent1 = create_demo_agent()
    
    print_section("First conversation instance")
    
    # Create session and have conversation
    session_id = agent1.start_session("resumable_session")
    print(f"Started session: {session_id}")
    
    response1 = agent1.chat("My name is Alice and I love programming")
    print_chat_message("User", "My name is Alice and I love programming", session_id)
    print_chat_message("Agent", response1, session_id)
    
    response2 = agent1.chat("What's my favorite hobby?")
    print_chat_message("User", "What's my favorite hobby?", session_id)
    print_chat_message("Agent", response2, session_id)
    
    # Show session info before ending
    print(f"Session has {len(agent1.get_session_history())} messages")
    
    # End the first agent (simulating app restart)
    agent1.end_session()
    del agent1
    
    print_section("Second conversation instance (resuming)")
    
    # Second agent instance - resume session
    agent2 = create_demo_agent()
    resumed = agent2.resume_session(session_id)
    print(f"Resume successful: {resumed}")
    
    if resumed:
        print(f"Resumed session: {session_id}")
        print(f"Loaded {len(agent2.get_session_history())} messages from history")
        
        # Continue conversation
        response3 = agent2.chat("Do you remember my name?")
        print_chat_message("User", "Do you remember my name?", session_id)
        print_chat_message("Agent", response3, session_id)
        
        response4 = agent2.chat("What did we talk about before?")
        print_chat_message("User", "What did we talk about before?", session_id)
        print_chat_message("Agent", response4, session_id)
    
    return agent2

def demo_multi_session_management():
    """Demo managing multiple sessions simultaneously"""
    print_header("Demo 4: Multi-Session Management")
    
    agent = create_demo_agent()
    
    print_section("Creating multiple sessions")
    
    # Create first session
    session1 = agent.start_session("work_session", metadata={"context": "work"})
    response1 = agent.chat("I need help with a Python project", session_id=session1)
    print_chat_message("User", "I need help with a Python project", session1)
    print_chat_message("Agent", response1, session1)
    
    # Create second session
    session2 = agent.start_session("personal_session", metadata={"context": "personal"})
    response2 = agent.chat("I'm planning a vacation", session_id=session2)
    print_chat_message("User", "I'm planning a vacation", session2)
    print_chat_message("Agent", response2, session2)
    
    # Switch back to first session
    response3 = agent.chat("Can you help me debug this code?", session_id=session1)
    print_chat_message("User", "Can you help me debug this code?", session1)
    print_chat_message("Agent", response3, session1)
    
    # Switch to second session
    response4 = agent.chat("What's the weather like in Paris?", session_id=session2)
    print_chat_message("User", "What's the weather like in Paris?", session2)
    print_chat_message("Agent", response4, session2)
    
    print_section("Session Summary")
    print(f"Work session ({session1}): {len(agent.get_session_history(session1))} messages")
    print(f"Personal session ({session2}): {len(agent.get_session_history(session2))} messages")
    
    return agent

def demo_session_with_streaming():
    """Demo session management with streaming responses"""
    print_header("Demo 5: Session Management with Streaming")
    
    agent = create_demo_agent()
    
    print_section("Streaming chat with session management")
    
    # Start session and stream response
    session_id = agent.start_session("streaming_session")
    print(f"Started streaming session: {session_id}")
    
    query = "Tell me a story about a robot learning to code"
    print_chat_message("User", query, session_id)
    
    # Note: This will fall back to regular chat for non-streaming agents
    try:
        print("Agent (streaming): ", end="", flush=True)
        for chunk in agent.chat_stream(query, session_id=session_id):
            content = chunk.get("content", "")
            print(content, end="", flush=True)
            if chunk.get("is_complete"):
                print("\n")
                break
    except Exception as e:
        print(f"Streaming not available, falling back to regular chat: {e}")
        response = agent.chat(query, session_id=session_id)
        print_chat_message("Agent", response, session_id)
    
    return agent

def demo_real_world_scenario():
    """Demo a real-world customer service scenario"""
    print_header("Demo 6: Real-World Customer Service Scenario")
    
    agent = create_demo_agent()
    
    print_section("Customer service conversation")
    
    # Customer starts conversation
    session_id = agent.start_session("customer_service_001", 
                                   metadata={
                                       "customer_id": "CUST789",
                                       "issue_type": "account_access",
                                       "priority": "high"
                                   })
    
    conversation_flow = [
        "Hello, I'm having trouble accessing my account",
        "I keep getting an error when I try to log in",
        "The error says 'Invalid credentials' but I'm sure my password is correct",
        "I tried resetting my password but didn't receive the email",
        "Yes, I checked my spam folder",
        "My email is john.doe@example.com",
        "That worked! I can access my account now. Thank you!"
    ]
    
    agent_responses = []
    for user_message in conversation_flow:
        response = agent.chat(user_message, session_id=session_id)
        print_chat_message("Customer", user_message, session_id)
        print_chat_message("Agent", response, session_id)
        agent_responses.append(response)
    
    print_section("Session Summary")
    history = agent.get_session_history(session_id)
    print(f"Session ID: {session_id}")
    print(f"Total exchanges: {len(history) // 2}")
    print(f"Issue resolved: {'Yes' if 'thank you' in conversation_flow[-1].lower() else 'No'}")
    
    return agent

def main():
    """Run all demos"""
    print_header("LangSwarm Integrated Session Management Demo")
    print("This demo shows how session management is seamlessly integrated")
    print("with the LangSwarm AgentWrapper chat() method.")
    print("\nFeatures demonstrated:")
    print("✓ Automatic session creation")
    print("✓ Session persistence and resumption")
    print("✓ Multi-session management")
    print("✓ Real agent integration")
    print("✓ Streaming support")
    print("✓ Real-world scenarios")
    
    try:
        # Run all demos
        demo_basic_session_chat()
        demo_explicit_session_management()
        demo_session_resumption()
        demo_multi_session_management()
        demo_session_with_streaming()
        demo_real_world_scenario()
        
        print_header("Demo Complete!")
        print("The session management system is now fully integrated")
        print("with the LangSwarm AgentWrapper chat() method.")
        print("\nKey integration points:")
        print("• AgentWrapper.__init__() - Initializes session manager")
        print("• AgentWrapper.chat() - Supports session parameters")
        print("• AgentWrapper.chat_stream() - Supports session parameters")
        print("• AgentWrapper._store_conversation() - Stores in sessions")
        print("• AgentWrapper._call_agent() - Uses session context")
        print("\nSession management is now production-ready!")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 