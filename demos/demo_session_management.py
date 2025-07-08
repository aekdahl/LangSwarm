#!/usr/bin/env python3
"""
Demo: Priority 5 - Native Thread IDs & Session Management
==========================================================

Comprehensive demonstration of LangSwarm's session management system
with native thread ID support, provider adapters, and intelligent strategies.

Features Demonstrated:
- Unified session management across all providers
- Native thread/session ID support where available
- Intelligent session strategy selection
- Multi-provider session coordination  
- Session persistence and recovery
- Conversation history management
"""

import json
import time
from datetime import datetime, timedelta
from langswarm.core.session import (
    LangSwarmSessionManager,
    LangSwarmSession,
    SessionControl,
    SessionStatus,
    MessageRole,
    SessionStrategyFactory,
    SessionAdapterFactory,
    InMemorySessionStorage,
    SQLiteSessionStorage
)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def demo_provider_capabilities():
    """Demonstrate provider capability analysis"""
    print_header("PRIORITY 5: NATIVE THREAD IDS & SESSION MANAGEMENT")
    print("Unified session management with native ID support across all providers")
    
    print_section("Provider Capability Analysis")
    
    providers = ["openai", "claude", "gemini", "mistral", "cohere"]
    
    for provider in providers:
        capabilities = SessionStrategyFactory.analyze_provider_capabilities(provider)
        
        print(f"\n📋 {provider.upper()}")
        print(f"   Native Threading: {'✅' if capabilities['native_threading'] else '❌'}")
        print(f"   Stateful Conversations: {'✅' if capabilities['stateful_conversations'] else '❌'}")
        print(f"   Message IDs: {'✅' if capabilities['message_ids'] else '❌'}")
        print(f"   Thread Branching: {'✅' if capabilities['thread_branching'] else '❌'}")
        print(f"   Recommended Strategy: {capabilities['recommended_strategy']}")
        print(f"   Features: {', '.join(capabilities['features'])}")


def demo_session_strategies():
    """Demonstrate different session management strategies"""
    print_section("Session Management Strategies")
    
    # Test different strategies
    strategies = {
        "Native": SessionControl.NATIVE,
        "Client-Side": SessionControl.LANGSWARM,
        "Hybrid (Intelligent)": SessionControl.HYBRID
    }
    
    for name, control in strategies.items():
        strategy = SessionStrategyFactory.create_strategy(control)
        
        print(f"\n🎯 {name} Strategy")
        print(f"   OpenAI (GPT-4): {'Uses Native' if strategy.should_use_native_sessions('openai', 'gpt-4o') else 'Uses Client-Side'}")
        print(f"   Claude: {'Uses Native' if strategy.should_use_native_sessions('claude', 'claude-3') else 'Uses Client-Side'}")
        print(f"   Gemini: {'Uses Native' if strategy.should_use_native_sessions('gemini', 'gemini-pro') else 'Uses Client-Side'}")
        print(f"   Mistral: {'Uses Native' if strategy.should_use_native_sessions('mistral', 'mistral-large') else 'Uses Client-Side'}")


def demo_session_creation_and_management():
    """Demonstrate session creation and management"""
    print_section("Session Creation & Management")
    
    # Create session manager
    manager = LangSwarmSessionManager(storage=InMemorySessionStorage())
    
    # Create sessions for different providers
    sessions = []
    provider_configs = [
        ("openai", "gpt-4o", SessionControl.HYBRID),
        ("claude", "claude-3-sonnet", SessionControl.LANGSWARM),
        ("gemini", "gemini-pro", SessionControl.LANGSWARM),
        ("mistral", "mistral-large", SessionControl.NATIVE),
        ("cohere", "command-r", SessionControl.LANGSWARM)
    ]
    
    print("\n🚀 Creating Multi-Provider Sessions")
    
    for provider, model, control in provider_configs:
        session = manager.create_session(
            user_id=f"user_{provider}",
            provider=provider,
            model=model,
            session_control=control
        )
        sessions.append(session)
        
        print(f"   ✅ {provider.upper()}: {session.session_id}")
        print(f"      Model: {model}")
        print(f"      Strategy: {control.value}")
        print(f"      Native Support: {'✅' if session._adapter.supports_native_sessions() else '❌'}")
    
    return manager, sessions


def demo_conversation_flow(manager, sessions):
    """Demonstrate conversation flow across providers"""
    print_section("Multi-Provider Conversation Flow")
    
    # Test conversations with each provider
    conversations = [
        ("openai", "Hello! Can you explain quantum computing briefly?"),
        ("claude", "What are the key principles of machine learning?"),
        ("gemini", "How do neural networks work?"),
        ("mistral", "Explain the concept of artificial intelligence."),
        ("cohere", "What is the future of AI technology?")
    ]
    
    for provider, message in conversations:
        # Find session for this provider
        session = next(s for s in sessions if s.provider == provider)
        
        print(f"\n💬 Conversation with {provider.upper()}")
        print(f"   User: {message}")
        
        try:
            # Send message
            response = manager.send_message(session.session_id, message)
            print(f"   Assistant: {response.content[:100]}...")
            print(f"   Message ID: {response.id}")
            if response.provider_message_id:
                print(f"   Provider ID: {response.provider_message_id}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")


def demo_session_persistence():
    """Demonstrate session persistence with SQLite"""
    print_section("Session Persistence & Recovery")
    
    # Create SQLite storage
    storage = SQLiteSessionStorage("demo_sessions.db")
    manager = LangSwarmSessionManager(storage=storage)
    
    print("\n💾 Creating Persistent Session")
    
    # Create session
    session = manager.create_session(
        user_id="persistent_user",
        provider="openai",
        model="gpt-4o",
        session_control=SessionControl.HYBRID
    )
    
    print(f"   Session ID: {session.session_id}")
    
    # Add some conversation history
    manager.send_message(session.session_id, "What is LangSwarm?")
    manager.send_message(session.session_id, "How does session management work?")
    
    print(f"   Messages: {session.message_count}")
    
    # Simulate application restart by creating new manager
    print("\n🔄 Simulating Application Restart")
    new_storage = SQLiteSessionStorage("demo_sessions.db")
    new_manager = LangSwarmSessionManager(storage=new_storage)
    
    # Recover session
    recovered_session = new_manager.get_session(session.session_id)
    
    if recovered_session:
        print(f"   ✅ Session Recovered: {recovered_session.session_id}")
        print(f"   User: {recovered_session.user_id}")
        print(f"   Messages: {len(recovered_session.history.messages)}")
        print(f"   Last Activity: {recovered_session.metadata.last_activity}")
        
        # Continue conversation
        response = new_manager.send_message(session.session_id, "Continue our discussion.")
        print(f"   Continued conversation: {response.content[:50]}...")
    else:
        print("   ❌ Session recovery failed")
    
    return new_manager


def demo_session_statistics_and_management(manager):
    """Demonstrate session statistics and management features"""
    print_section("Session Statistics & Management")
    
    # Get statistics
    stats = manager.get_session_statistics()
    
    print("\n📊 Session Statistics")
    print(f"   Active Sessions: {stats['active_sessions']}")
    print(f"   Supported Providers: {len(stats['supported_providers'])}")
    
    if stats['provider_distribution']:
        print("   Provider Distribution:")
        for provider, count in stats['provider_distribution'].items():
            print(f"      {provider}: {count}")
    
    if stats['strategy_distribution']:
        print("   Strategy Distribution:")
        for strategy, count in stats['strategy_distribution'].items():
            print(f"      {strategy}: {count}")
    
    print(f"   Cache Sizes:")
    print(f"      Strategies: {stats['cache_sizes']['strategies']}")
    print(f"      Adapters: {stats['cache_sizes']['adapters']}")
    
    # List sessions
    print("\n📋 Session Management")
    sessions = manager.list_sessions()
    
    for session_meta in sessions[:3]:  # Show first 3
        print(f"   Session: {session_meta.session_id}")
        print(f"      User: {session_meta.user_id}")
        print(f"      Provider: {session_meta.provider}/{session_meta.model}")
        print(f"      Status: {session_meta.status.value}")
        print(f"      Messages: {session_meta.message_count}")
        print(f"      Updated: {session_meta.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


def demo_session_adapters():
    """Demonstrate provider-specific session adapters"""
    print_section("Provider-Specific Session Adapters")
    
    # Test each adapter
    adapters_info = [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-sonnet"),
        ("gemini", "gemini-pro"),
        ("mistral", "mistral-large"),
        ("cohere", "command-r")
    ]
    
    for provider, model in adapters_info:
        adapter = SessionAdapterFactory.create_adapter(provider, model)
        
        print(f"\n🔧 {provider.upper()} Adapter")
        print(f"   Model: {model}")
        print(f"   Native Sessions: {'✅' if adapter.supports_native_sessions() else '❌'}")
        print(f"   Provider: {adapter.provider}")
        
        # Create test session
        session = LangSwarmSession(
            user_id="test_user",
            provider=provider,
            model=model
        )
        
        # Test session creation parameters
        try:
            session_params = adapter.create_session(session)
            print(f"   Session Parameters: {len(session_params)} keys")
            if "model" in session_params:
                print(f"      Model: {session_params['model']}")
            if "messages" in session_params:
                print(f"      Messages Format: Standard")
            if "contents" in session_params:
                print(f"      Messages Format: Gemini-specific")
            if "chat_history" in session_params:
                print(f"      Messages Format: Cohere-specific")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def demo_advanced_features():
    """Demonstrate advanced session management features"""
    print_section("Advanced Features")
    
    manager = LangSwarmSessionManager(storage=InMemorySessionStorage())
    
    # Create session with custom metadata
    print("\n🏷️  Custom Session Metadata")
    session = manager.create_session(
        user_id="advanced_user",
        provider="openai",
        model="gpt-4o",
        tags=["demo", "advanced"],
        custom_metadata={"project": "session_demo", "version": "1.0"}
    )
    
    print(f"   Session ID: {session.session_id}")
    print(f"   Tags: {session.metadata.tags}")
    print(f"   Custom Metadata: {session.metadata.custom_metadata}")
    
    # Test session archival
    print("\n📦 Session Archival")
    archive_success = manager.archive_session(session.session_id)
    print(f"   Archive Success: {'✅' if archive_success else '❌'}")
    
    archived_session = manager.get_session(session.session_id)
    if archived_session:
        print(f"   Status: {archived_session.metadata.status.value}")
        
        # Reactivate
        archived_session.reactivate()
        manager.storage.save_session(archived_session)
        print(f"   Reactivated: {archived_session.metadata.status.value}")
    
    # Test context management
    print("\n📏 Context Management")
    
    # Add many messages to test truncation
    for i in range(10):
        manager.send_message(session.session_id, f"Test message {i+1}")
    
    print(f"   Total Messages: {session.message_count}")
    
    # Test context limit
    session.history.truncate_to_limit(5)
    print(f"   After Truncation: {len(session.history.messages)}")
    print(f"   Truncated At: {session.history.truncated_at}")


def demo_error_handling():
    """Demonstrate error handling and edge cases"""
    print_section("Error Handling & Edge Cases")
    
    manager = LangSwarmSessionManager(storage=InMemorySessionStorage())
    
    print("\n🚨 Error Handling Tests")
    
    # Test non-existent session
    try:
        manager.send_message("non_existent", "Hello")
        print("   ❌ Should have failed for non-existent session")
    except ValueError as e:
        print(f"   ✅ Correctly handled non-existent session: {str(e)[:50]}...")
    
    # Test invalid provider
    try:
        SessionAdapterFactory.create_adapter("invalid_provider", "model")
        print("   ❌ Should have failed for invalid provider")
    except ValueError as e:
        print(f"   ✅ Correctly handled invalid provider: {str(e)[:50]}...")
    
    # Test session cleanup
    print("\n🧹 Session Cleanup")
    
    # Create test session
    test_session = manager.create_session("cleanup_user", provider="openai", model="gpt-4o")
    
    # Simulate old session by updating timestamp
    old_time = datetime.now() - timedelta(days=31)
    manager.storage.update_session_metadata(test_session.session_id, {"updated_at": old_time})
    
    # Cleanup
    cleaned = manager.cleanup_expired_sessions(max_age_days=30)
    print(f"   Cleaned Sessions: {cleaned}")


def demo_real_world_scenario():
    """Demonstrate a real-world multi-provider scenario"""
    print_section("Real-World Scenario: Multi-Provider Chat Application")
    
    manager = LangSwarmSessionManager(storage=SQLiteSessionStorage("chat_app.db"))
    
    print("\n🌐 Multi-Provider Chat Application Simulation")
    
    # User preferences for different tasks
    user_sessions = {
        "coding": manager.create_session("developer_user", "openai", "gpt-4o"),
        "creative": manager.create_session("developer_user", "claude", "claude-3-sonnet"),
        "research": manager.create_session("developer_user", "gemini", "gemini-pro"),
        "analysis": manager.create_session("developer_user", "mistral", "mistral-large")
    }
    
    # Simulate task-specific conversations
    tasks = {
        "coding": "Help me write a Python function to sort a list",
        "creative": "Write a creative story about space exploration",
        "research": "What are the latest developments in quantum computing?",
        "analysis": "Analyze the pros and cons of remote work"
    }
    
    for task_type, message in tasks.items():
        session = user_sessions[task_type]
        print(f"\n📝 {task_type.upper()} Task")
        print(f"   Provider: {session.provider}")
        print(f"   Session: {session.session_id}")
        print(f"   Query: {message}")
        
        response = manager.send_message(session.session_id, message)
        print(f"   Response Length: {len(response.content)} chars")
        print(f"   Native Session: {'✅' if session._adapter.supports_native_sessions() else '❌'}")
    
    # Show final statistics
    print(f"\n📊 Final Statistics")
    final_stats = manager.get_session_statistics()
    print(f"   Total Active Sessions: {final_stats['active_sessions']}")
    print(f"   Provider Usage: {final_stats['provider_distribution']}")


def main():
    """Run the complete Priority 5 session management demo"""
    try:
        # Core demonstrations
        demo_provider_capabilities()
        demo_session_strategies()
        
        # Session management
        manager, sessions = demo_session_creation_and_management()
        demo_conversation_flow(manager, sessions)
        
        # Persistence and recovery
        persistent_manager = demo_session_persistence()
        demo_session_statistics_and_management(persistent_manager)
        
        # Technical details
        demo_session_adapters()
        demo_advanced_features()
        demo_error_handling()
        
        # Real-world scenario
        demo_real_world_scenario()
        
        print_header("PRIORITY 5 DEMONSTRATION COMPLETE")
        print("\n🎉 Session Management System Features Demonstrated:")
        print("   ✅ Native thread ID support for OpenAI & Mistral")
        print("   ✅ Intelligent session strategy selection")
        print("   ✅ Multi-provider session coordination")
        print("   ✅ Session persistence with SQLite")
        print("   ✅ Conversation history management")
        print("   ✅ Provider-specific adapters")
        print("   ✅ Session archival and cleanup")
        print("   ✅ Error handling and edge cases")
        print("   ✅ Real-world application scenarios")
        
        print("\n🔧 Integration Benefits:")
        print("   • Unified API across all LLM providers")
        print("   • Automatic native session optimization")
        print("   • Seamless session persistence")
        print("   • Intelligent conversation management")
        print("   • Production-ready session storage")
        
        print("\n📚 Next Steps:")
        print("   • Integrate with existing LangSwarm agents")
        print("   • Add session management to generic.py wrapper")
        print("   • Implement session-aware tool calling")
        print("   • Add session analytics and monitoring")
        
    except Exception as e:
        print(f"\n❌ Demo Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up demo databases
        import os
        for db_file in ["demo_sessions.db", "chat_app.db"]:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"   🧹 Cleaned up {db_file}")


if __name__ == "__main__":
    main() 