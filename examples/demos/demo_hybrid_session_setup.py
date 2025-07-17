"""
Demo: Hybrid Session Management Setup
====================================

This demo shows how Option 1 (Hybrid) would work with agent.chat() integration.

Key Points:
1. agent.chat() remains the primary interface (no breaking changes)
2. Basic session functionality works immediately 
3. Enhanced features activate when enhanced backend is available
4. Graceful fallback when enhanced features fail
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSwarm imports
from langswarm.core.factory.agents import AgentWrapperFactory
from langswarm.core.session.hybrid_manager import HybridSessionManager, HybridSessionManagerFactory

def demo_basic_agent_chat():
    """
    Demo 1: Basic agent.chat() with session management
    This is what users get today - no setup changes needed
    """
    print("🔧 Demo 1: Basic Agent Chat with Sessions")
    print("=" * 50)
    
    # Create agent (exactly as users do today)
    agent = AgentWrapperFactory.create_agent(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key-here"
    )
    
    # Chat with automatic session management (NEW - but transparent)
    print("\n💬 Starting conversation...")
    
    # First message - creates session automatically
    response1 = agent.chat(
        "Hello! I'm working on a Python project.",
        user_id="user123",
        start_new_session=True  # Optional: explicitly start new session
    )
    
    print(f"🤖 Agent: {response1}")
    print(f"📝 Session ID: {agent.current_session_id}")
    
    # Continue conversation - uses same session
    response2 = agent.chat(
        "Can you help me with database design?",
        user_id="user123"
    )
    
    print(f"🤖 Agent: {response2}")
    print(f"📝 Same Session: {agent.current_session_id}")
    
    # Get session history
    history = agent.get_session_history()
    print(f"\n📊 Session has {len(history.messages)} messages")
    
    print("\n✅ Basic session management working!")
    print("   - No setup changes needed")
    print("   - Sessions created automatically")
    print("   - History preserved across calls")
    
    return agent

def demo_hybrid_setup():
    """
    Demo 2: Hybrid setup with enhanced features
    This shows how to enable enhanced capabilities
    """
    print("\n🚀 Demo 2: Hybrid Setup with Enhanced Features")
    print("=" * 50)
    
    # Option 1: Simple hybrid setup
    print("\n🔧 Setup Option 1: Simple Hybrid")
    hybrid_manager = HybridSessionManagerFactory.create_hybrid_manager(
        enhanced_backend="chromadb",  # Enable semantic search
        basic_storage_type="sqlite"   # Keep reliable basic storage
    )
    
    # Create agent with hybrid manager
    agent = AgentWrapperFactory.create_agent(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key-here",
        session_manager=hybrid_manager  # Use hybrid manager
    )
    
    print("✅ Hybrid manager created:")
    print(f"   - Basic storage: SQLite (reliable)")
    print(f"   - Enhanced backend: ChromaDB (semantic search)")
    print(f"   - Fallback: Automatic if enhanced fails")
    
    # Option 2: Advanced hybrid setup
    print("\n🔧 Setup Option 2: Advanced Hybrid")
    advanced_hybrid = HybridSessionManagerFactory.create_hybrid_manager(
        enhanced_backend="chromadb",
        basic_storage_type="sqlite",
        enable_semantic_search=True,
        enable_analytics=True,
        chromadb_config={
            "host": "localhost",
            "port": 8000,
            "collection_name": "langswarm_conversations"
        }
    )
    
    agent_advanced = AgentWrapperFactory.create_agent(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key-here",
        session_manager=advanced_hybrid
    )
    
    print("✅ Advanced hybrid manager created with:")
    print("   - Semantic search enabled")
    print("   - Analytics enabled")
    print("   - Custom ChromaDB config")
    
    return agent, agent_advanced

def demo_agent_chat_with_hybrid(agent):
    """
    Demo 3: Using agent.chat() with hybrid features
    Shows new capabilities available through same interface
    """
    print("\n💬 Demo 3: Agent Chat with Hybrid Features")
    print("=" * 50)
    
    # Regular chat (works exactly as before)
    response = agent.chat(
        "I need help with machine learning model deployment",
        user_id="user456",
        start_new_session=True
    )
    
    print(f"🤖 Agent: {response}")
    session_id = agent.current_session_id
    
    # Continue conversation
    agent.chat(
        "Specifically, I'm working with TensorFlow models",
        user_id="user456"
    )
    
    agent.chat(
        "And I need to deploy to AWS",
        user_id="user456"
    )
    
    # NEW: Enhanced features (if available)
    print("\n🔍 Enhanced Features Available:")
    
    # 1. Semantic search across all conversations
    try:
        similar_conversations = agent.session_manager.search_conversation_history(
            query="machine learning deployment AWS",
            user_id="user456",
            limit=3
        )
        
        print(f"   ✅ Found {len(similar_conversations)} similar conversations")
        for conv in similar_conversations:
            print(f"      - {conv.get('content', '')[:50]}...")
            
    except Exception as e:
        print(f"   ⚠️ Semantic search not available: {e}")
    
    # 2. Conversation analytics
    try:
        analytics = agent.session_manager.get_conversation_analytics(
            user_id="user456",
            time_range_days=30
        )
        
        print(f"   ✅ Analytics: {analytics.get('total_messages', 0)} messages")
        print(f"      - {analytics.get('unique_sessions', 0)} sessions")
        print(f"      - Top topics: {list(analytics.get('top_topics', {}).keys())[:3]}")
        
    except Exception as e:
        print(f"   ⚠️ Analytics not available: {e}")
    
    # 3. Similar conversation discovery
    try:
        similar = agent.session_manager.find_similar_conversations(
            session_id=session_id,
            limit=3
        )
        
        print(f"   ✅ Found {len(similar)} similar sessions")
        for sim in similar:
            print(f"      - Session {sim.get('session_id', '')}: {sim.get('sample_content', '')[:30]}...")
            
    except Exception as e:
        print(f"   ⚠️ Similar conversations not available: {e}")
    
    print("\n✅ Hybrid features demonstrated!")
    print("   - Same agent.chat() interface")
    print("   - Enhanced capabilities when available")
    print("   - Graceful fallback when not")

def demo_migration_path():
    """
    Demo 4: Migration path for existing users
    Shows how existing code keeps working
    """
    print("\n🔄 Demo 4: Migration Path")
    print("=" * 50)
    
    print("📋 Existing User Code (KEEPS WORKING):")
    print("""
    # This code works exactly as before
    agent = AgentWrapperFactory.create_agent(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key"
    )
    
    response = agent.chat("Hello")  # Sessions created automatically
    """)
    
    print("\n📋 Enhanced User Code (OPTIONAL UPGRADE):")
    print("""
    # Users can optionally upgrade to hybrid
    hybrid_manager = HybridSessionManagerFactory.create_hybrid_manager(
        enhanced_backend="chromadb"
    )
    
    agent = AgentWrapperFactory.create_agent(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key",
        session_manager=hybrid_manager  # Only change needed
    )
    
    response = agent.chat("Hello")  # Same interface, enhanced features
    """)
    
    print("\n✅ Migration Benefits:")
    print("   - Zero breaking changes")
    print("   - Existing code works immediately")
    print("   - Users upgrade when ready")
    print("   - Enhanced features opt-in")

def demo_backend_options():
    """
    Demo 5: Different backend options
    Shows flexibility in choosing enhanced backends
    """
    print("\n🔧 Demo 5: Backend Options")
    print("=" * 50)
    
    backends = [
        ("chromadb", "Vector search, semantic similarity"),
        ("sqlite", "Local storage, full-text search"),
        ("redis", "High-performance caching, real-time analytics"),
        ("elasticsearch", "Advanced search, text analytics"),
        ("qdrant", "High-performance vector database"),
        ("bigquery", "Enterprise-scale analytics")
    ]
    
    for backend, description in backends:
        print(f"\n🔧 {backend.upper()} Backend:")
        print(f"   - {description}")
        print(f"   - Setup: enhanced_backend='{backend}'")
        
        # Show config example
        if backend == "chromadb":
            print("   - Config: chromadb_config={'host': 'localhost', 'port': 8000}")
        elif backend == "redis":
            print("   - Config: redis_config={'host': 'localhost', 'port': 6379}")
        elif backend == "elasticsearch":
            print("   - Config: elasticsearch_config={'host': 'localhost', 'port': 9200}")
    
    print("\n✅ Backend Selection:")
    print("   - Choose based on your needs")
    print("   - Start simple (SQLite)")
    print("   - Scale up (ChromaDB, Redis)")
    print("   - Enterprise (BigQuery, Elasticsearch)")

def main():
    """Main demo showing hybrid session management"""
    print("🚀 LangSwarm Hybrid Session Management Demo")
    print("=" * 70)
    
    # Demo 1: Basic functionality (what users get today)
    agent = demo_basic_agent_chat()
    
    # Demo 2: Hybrid setup options
    agent_hybrid, agent_advanced = demo_hybrid_setup()
    
    # Demo 3: Enhanced features through same interface
    demo_agent_chat_with_hybrid(agent_hybrid)
    
    # Demo 4: Migration path
    demo_migration_path()
    
    # Demo 5: Backend options
    demo_backend_options()
    
    print("\n🎯 SUMMARY: Hybrid Session Management")
    print("=" * 70)
    print("✅ Uses existing agent.chat() interface")
    print("✅ No breaking changes for existing users")
    print("✅ Sessions created automatically")
    print("✅ Enhanced features opt-in")
    print("✅ Graceful fallback when enhanced features fail")
    print("✅ Multiple backend options")
    print("✅ Easy migration path")
    
    print("\n🔧 Setup is simple:")
    print("   1. Basic: No changes needed (sessions work automatically)")
    print("   2. Enhanced: Add session_manager=hybrid_manager to agent creation")
    print("   3. Advanced: Configure enhanced backend of choice")

if __name__ == "__main__":
    main() 