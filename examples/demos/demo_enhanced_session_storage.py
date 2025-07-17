#!/usr/bin/env python3
"""
Demo: Enhanced Session Storage with _langswarm Adapters

This demo shows how to leverage the existing _langswarm memory adapters
for advanced session storage capabilities including:

1. Semantic search across conversation history
2. Vector-based session storage 
3. Advanced analytics and insights
4. Multiple backend support (ChromaDB, SQLite, Redis, etc.)

Usage:
    python demo_enhanced_session_storage.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add the LangSwarm module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*50}")
    print(f"  {title}")
    print(f"{'-'*50}")

def demo_enhanced_storage_capabilities():
    """Demo the enhanced storage capabilities"""
    print_header("Enhanced Session Storage with _langswarm Adapters")
    
    try:
        from langswarm.core.session.enhanced_storage import EnhancedSessionStorageFactory
        from langswarm.core.session.models import LangSwarmSession, MessageRole
        from langswarm.core.wrappers.generic import AgentWrapper
        
        print("✅ Enhanced session storage imports successful!")
        
        # Mock agent for testing
        class MockAgent:
            def __init__(self):
                self.conversation_count = 0
                self.model = "mock-model"
                self.task = "text-generation"
                
            def __call__(self, context):
                self.conversation_count += 1
                return f"Enhanced storage response #{self.conversation_count}"
        
        print_section("Creating Enhanced Storage with Different Backends")
        
        # Create different enhanced storage backends
        storage_backends = {}
        
        try:
            # SQLite enhanced storage (most likely to work)
            storage_backends["sqlite"] = EnhancedSessionStorageFactory.create_sqlite_storage(
                db_path="enhanced_demo_sessions.db"
            )
            print("✅ Enhanced SQLite storage created")
        except Exception as e:
            print(f"❌ Enhanced SQLite storage failed: {e}")
        
        try:
            # ChromaDB enhanced storage
            storage_backends["chromadb"] = EnhancedSessionStorageFactory.create_chromadb_storage(
                collection_name="demo_sessions",
                persist_directory="./demo_chroma_sessions"
            )
            print("✅ Enhanced ChromaDB storage created")
        except Exception as e:
            print(f"❌ Enhanced ChromaDB storage failed: {e}")
        
        if not storage_backends:
            print("❌ No enhanced storage backends available")
            return
        
        # Use the first available backend
        storage_name, enhanced_storage = list(storage_backends.items())[0]
        print(f"\n🔥 Using {storage_name.upper()} enhanced storage for demo")
        
        print_section("Creating Sessions with Rich Conversation Data")
        
        # Create multiple sessions with rich conversation data
        sessions = []
        conversation_topics = [
            {
                "user_id": "alice",
                "provider": "openai", 
                "conversations": [
                    "I need help with Python programming",
                    "Can you explain machine learning concepts?",
                    "What are the best practices for data structures?",
                    "How do I optimize my neural network?"
                ]
            },
            {
                "user_id": "bob",
                "provider": "claude",
                "conversations": [
                    "I'm planning a vacation to Japan",
                    "What's the best time to visit Tokyo?", 
                    "Can you recommend some restaurants?",
                    "How do I navigate the train system?"
                ]
            },
            {
                "user_id": "alice", 
                "provider": "openai",
                "conversations": [
                    "I want to learn about quantum computing",
                    "How do quantum bits work?",
                    "What are quantum algorithms?",
                    "Can you explain quantum entanglement?"
                ]
            }
        ]
        
        # Create and populate sessions
        for topic in conversation_topics:
            session = LangSwarmSession(
                user_id=topic["user_id"],
                provider=topic["provider"],
                model="gpt-4"
            )
            
            # Add conversation messages
            for i, message in enumerate(topic["conversations"]):
                # Add user message
                session.add_message(message, MessageRole.USER)
                # Add assistant response
                response = f"Here's information about {message.lower()}..."
                session.add_message(response, MessageRole.ASSISTANT)
            
            # Save to enhanced storage
            success = enhanced_storage.save_session(session)
            if success:
                sessions.append(session)
                print(f"✅ Saved session {session.session_id} for {topic['user_id']}")
            else:
                print(f"❌ Failed to save session for {topic['user_id']}")
        
        print(f"\n📊 Total sessions created: {len(sessions)}")
        
        print_section("🔥 NEW CAPABILITY: Semantic Search Across All Conversations")
        
        # Demonstrate semantic search capabilities
        search_queries = [
            "programming and coding",
            "travel and vacation", 
            "quantum physics",
            "machine learning algorithms",
            "Tokyo restaurants"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Searching for: '{query}'")
            results = enhanced_storage.search_conversation_history(
                query=query,
                limit=3
            )
            
            for i, result in enumerate(results[:2], 1):  # Show top 2 results
                print(f"  {i}. [{result['role']}] {result['content'][:80]}...")
                print(f"     Session: {result['session_id'][:12]}... | User: {result['context']['user_id']}")
        
        print_section("🔥 NEW CAPABILITY: Advanced Conversation Analytics")
        
        # Demonstrate analytics capabilities
        analytics = enhanced_storage.get_conversation_analytics(time_range_days=30)
        
        print(f"📈 Conversation Analytics (Last {analytics.get('time_range_days', 30)} days):")
        print(f"   • Total Messages: {analytics.get('total_messages', 0)}")
        print(f"   • Unique Sessions: {analytics.get('unique_sessions', 0)}")
        print(f"   • Avg Messages/Session: {analytics.get('average_messages_per_session', 0):.1f}")
        
        if analytics.get('provider_distribution'):
            print(f"   • Provider Distribution:")
            for provider, count in analytics['provider_distribution'].items():
                print(f"     - {provider}: {count} messages")
        
        if analytics.get('role_distribution'):
            print(f"   • Role Distribution:")
            for role, count in analytics['role_distribution'].items():
                print(f"     - {role}: {count} messages")
        
        print_section("🔥 NEW CAPABILITY: User-Specific Search")
        
        # Demonstrate user-specific search
        user_results = enhanced_storage.search_conversation_history(
            query="learning and education",
            user_id="alice",
            limit=5
        )
        
        print(f"🔍 Alice's conversations about learning:")
        for result in user_results[:3]:
            print(f"   • [{result['role']}] {result['content'][:60]}...")
        
        print_section("🔥 NEW CAPABILITY: Session-Specific Search")
        
        # Demonstrate session-specific search
        if sessions:
            session_results = enhanced_storage.search_conversation_history(
                query="algorithms and computing",
                session_id=sessions[0].session_id,
                limit=3
            )
            
            print(f"🔍 Session-specific search results:")
            for result in session_results:
                print(f"   • [{result['role']}] {result['content'][:60]}...")
        
        print_section("Comparison: Basic vs Enhanced Storage")
        
        print("📊 BASIC SESSION STORAGE:")
        print("   ✅ Session persistence")
        print("   ✅ Conversation history")
        print("   ✅ Session metadata")
        print("   ❌ No semantic search")
        print("   ❌ No analytics")
        print("   ❌ Limited querying")
        
        print("\n🔥 ENHANCED SESSION STORAGE:")
        print("   ✅ All basic features")
        print("   🔥 Semantic search across conversations") 
        print("   🔥 Vector-based storage and retrieval")
        print("   🔥 Advanced conversation analytics")
        print("   🔥 Cross-session insights")
        print("   🔥 Multiple backend support")
        print("   🔥 Scalable for enterprise use")
        
        print_section("Available Enhanced Backends")
        
        backends = [
            ("ChromaDB", "Vector database with semantic search"),
            ("SQLite", "Enhanced SQLite with vector capabilities"),
            ("Redis", "High-performance caching and search"),
            ("Qdrant", "Advanced vector search engine"),
            ("Elasticsearch", "Full-text search and analytics"),
            ("BigQuery", "Enterprise-scale data analytics"),
            ("GCS", "Cloud storage with advanced features")
        ]
        
        for name, description in backends:
            print(f"   🔥 {name}: {description}")
        
        print_header("Enhanced Storage Demo Complete!")
        print("🚀 Ready to integrate enhanced session storage with _langswarm adapters!")
        print("\nNext steps:")
        print("1. Choose your preferred backend (ChromaDB recommended)")
        print("2. Update AgentWrapper to use enhanced storage")
        print("3. Enable semantic search and analytics features")
        print("4. Scale to enterprise-level conversation management")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required dependencies are installed")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

def demo_integration_example():
    """Show how to integrate enhanced storage with AgentWrapper"""
    print_header("Integration Example: AgentWrapper + Enhanced Storage")
    
    print("""
🔧 INTEGRATION APPROACH:

1. Update AgentWrapper initialization:
   ```python
   from langswarm.core.session.enhanced_storage import EnhancedSessionStorageFactory
   
   # Create enhanced storage
   enhanced_storage = EnhancedSessionStorageFactory.create_chromadb_storage()
   
   # Initialize session manager with enhanced storage
   agent = AgentWrapper(
       name="Assistant",
       agent=openai_client,
       model="gpt-4",
       enhanced_session_storage=enhanced_storage
   )
   ```

2. Add new AgentWrapper methods:
   ```python
   # Semantic search across user's conversation history
   results = agent.search_conversation_history("machine learning")
   
   # Get conversation analytics
   analytics = agent.get_conversation_analytics()
   
   # Find similar conversations
   similar = agent.find_similar_conversations(current_session_id)
   ```

3. Enhanced session management:
   ```python
   # Create session with enhanced capabilities
   session_id = agent.start_enhanced_session(
       user_id="alice",
       context_tags=["programming", "AI", "learning"]
   )
   
   # Chat with automatic semantic indexing
   response = agent.chat("Explain neural networks", session_id=session_id)
   
   # Search across all user's conversations
   history = agent.search_user_conversations("neural networks", user_id="alice")
   ```

🎯 BENEFITS:
   • Semantic search across ALL conversations
   • Advanced analytics and insights  
   • Scalable vector storage
   • Cross-session intelligence
   • Enterprise-ready backends
   • Backward compatibility maintained
""")

def main():
    """Run the enhanced storage demo"""
    demo_enhanced_storage_capabilities()
    demo_integration_example()

if __name__ == "__main__":
    main() 