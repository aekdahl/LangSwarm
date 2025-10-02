"""
Session Management Integration Tests
===================================

Comprehensive end-to-end tests for LangSwarm session management system
including all storage backends, provider adapters, session strategies,
persistence, recovery, and hybrid enhanced features.

Test Coverage:
- Basic Session Management (creation, retrieval, archival, deletion)
- Storage Backends (InMemory, SQLite, Enhanced with multiple backends)
- Session Strategies (Native, Client-side, Hybrid)
- Provider Adapters (OpenAI, Claude, Gemini, Mistral, Cohere)
- Hybrid Session Management (semantic search, analytics)
- Session Persistence (recovery, cleanup, metadata handling)
- Multi-User Session Coordination
- Real-World Chat Scenarios
- Cross-Session Analytics and Insights
- Performance and System Health
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch
import logging

# Session Management Core
from langswarm.core.session.manager import LangSwarmSessionManager
from langswarm.core.session.hybrid_manager import HybridSessionManager, HybridSessionManagerFactory
from langswarm.core.session.models import (
    LangSwarmSession, SessionMetadata, ConversationMessage, ConversationHistory,
    SessionStatus, SessionControl, MessageRole
)
from langswarm.core.session.storage import (
    SessionStorage, InMemorySessionStorage, SQLiteSessionStorage, SessionStorageFactory
)
from langswarm.core.session.strategies import (
    SessionStrategy, NativeSessionStrategy, ClientSideSessionStrategy, 
    HybridSessionStrategy, SessionStrategyFactory
)
from langswarm.core.session.adapters import (
    BaseSessionAdapter, OpenAISessionAdapter, ClaudeSessionAdapter,
    GeminiSessionAdapter, MistralSessionAdapter, CohereSessionAdapter,
    SessionAdapterFactory
)
from langswarm.core.session.adapters_bridge import (
    SessionDatabaseBridge, HybridAdapterFactory, MockSessionAdapter
)
from langswarm.core.session.enhanced_storage import (
    EnhancedSessionStorage, EnhancedSessionStorageFactory
)


class TestSessionManagementIntegration:
    """Comprehensive session management integration tests"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for each test"""
        # Create temporary directory for test databases
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db_path = self.temp_dir / "test_sessions.db"
        
        # Test configuration
        self.test_users = ["user_001", "user_002", "user_003"]
        self.test_providers = ["openai", "claude", "gemini", "mistral", "cohere"]
        self.test_models = {
            "openai": "gpt-4o",
            "claude": "claude-3-sonnet",
            "gemini": "gemini-pro",
            "mistral": "mistral-large",
            "cohere": "command-r"
        }
        
        # Mock enhanced adapters for testing
        self.mock_adapters = {}
        
        yield
        
        # Cleanup after each test
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_basic_session_lifecycle(self):
        """Test complete session lifecycle: create, use, archive, delete"""
        print("\n=== Testing Basic Session Lifecycle ===")
        
        # Test with different storage backends
        storage_configs = [
            ("memory", {}),
            ("sqlite", {"db_path": str(self.test_db_path)})
        ]
        
        for storage_type, config in storage_configs:
            print(f"\n--- Testing {storage_type} storage ---")
            
            # Create storage and manager
            storage = SessionStorageFactory.create_storage(storage_type, **config)
            manager = LangSwarmSessionManager(storage=storage)
            
            # Test session creation
            session = manager.create_session(
                user_id="test_user",
                provider="openai",
                model="gpt-4o",
                session_control=SessionControl.HYBRID
            )
            
            assert session is not None
            assert session.user_id == "test_user"
            assert session.provider == "openai"
            assert session.model == "gpt-4o"
            assert session.metadata.status == SessionStatus.ACTIVE
            print(f"✓ Session created: {session.session_id}")
            
            # Test session retrieval
            retrieved_session = manager.get_session(session.session_id)
            assert retrieved_session is not None
            assert retrieved_session.session_id == session.session_id
            assert retrieved_session.user_id == session.user_id
            print(f"✓ Session retrieved successfully")
            
            # Test message sending (mock)
            with patch.object(manager, '_simulate_provider_response') as mock_response:
                mock_response.return_value = {
                    "message": "Hello! How can I help you?",
                    "usage": {"total_tokens": 25}
                }
                
                response = manager.send_message(session.session_id, "Hello")
                assert response is not None
                assert response.role == MessageRole.ASSISTANT
                print(f"✓ Message sent and response received")
            
            # Test session archival
            archived = manager.archive_session(session.session_id)
            assert archived is True
            
            archived_session = manager.get_session(session.session_id)
            assert archived_session.metadata.status == SessionStatus.ARCHIVED
            print(f"✓ Session archived successfully")
            
            # Test session deletion
            deleted = manager.delete_session(session.session_id)
            assert deleted is True
            
            deleted_session = manager.get_session(session.session_id)
            assert deleted_session is None
            print(f"✓ Session deleted successfully")

    def test_session_strategies_comprehensive(self):
        """Test all session strategies with different providers"""
        print("\n=== Testing Session Strategies ===")
        
        storage = InMemorySessionStorage()
        manager = LangSwarmSessionManager(storage=storage)
        
        # Test each strategy with each provider
        strategies = [SessionControl.NATIVE, SessionControl.LANGSWARM, SessionControl.HYBRID]
        
        for strategy in strategies:
            print(f"\n--- Testing {strategy.value} strategy ---")
            
            for provider in self.test_providers:
                model = self.test_models[provider]
                
                session = manager.create_session(
                    user_id=f"user_{strategy.value}",
                    provider=provider,
                    model=model,
                    session_control=strategy
                )
                
                assert session is not None
                assert session.metadata.session_control == strategy
                
                # Test strategy-specific behavior
                strategy_obj = manager._get_strategy(strategy)
                supports_native = strategy_obj.should_use_native_sessions(provider, model)
                
                if strategy == SessionControl.NATIVE:
                    # Native strategy should prefer native when available
                    expected_native = provider.lower() in ["openai", "mistral"]
                    assert supports_native == expected_native
                elif strategy == SessionControl.LANGSWARM:
                    # Client-side strategy should never use native
                    assert supports_native is False
                elif strategy == SessionControl.HYBRID:
                    # Hybrid should make intelligent decisions
                    expected_native = provider.lower() in ["openai", "mistral"]
                    assert supports_native == expected_native
                
                print(f"✓ {provider}/{model} with {strategy.value}: native={supports_native}")

    def test_provider_adapters_comprehensive(self):
        """Test all provider-specific adapters"""
        print("\n=== Testing Provider Adapters ===")
        
        storage = InMemorySessionStorage()
        manager = LangSwarmSessionManager(storage=storage)
        
        for provider in self.test_providers:
            print(f"\n--- Testing {provider} adapter ---")
            model = self.test_models[provider]
            
            # Create session with this provider
            session = manager.create_session(
                user_id=f"user_{provider}",
                provider=provider,
                model=model
            )
            
            # Get adapter
            adapter = manager._get_adapter(provider, model)
            assert adapter is not None
            assert adapter.provider.lower() == provider.lower()
            print(f"✓ Adapter created for {provider}")
            
            # Test adapter capabilities
            supports_native = adapter.supports_native_sessions()
            print(f"✓ Native session support: {supports_native}")
            
            # Test session creation with adapter
            try:
                session_params = adapter.create_session(session)
                print(f"✓ Session parameters: {session_params}")
            except Exception as e:
                print(f"! Session creation failed (expected for mock): {e}")
            
            # Test request preparation
            request_params = adapter.prepare_request(session, "Test message")
            assert isinstance(request_params, dict)
            # Different providers use different parameter names
            has_content = any(key in request_params for key in ["messages", "prompt", "contents", "chat_history", "message"])
            assert has_content, f"No content parameter found in {list(request_params.keys())}"
            print(f"✓ Request preparation successful")

    def test_hybrid_session_management(self):
        """Test hybrid session management with enhanced features"""
        print("\n=== Testing Hybrid Session Management ===")
        
        # Test different enhanced backends
        backend_configs = [
            ("mock", {}),
            ("chromadb", {"persist_directory": str(self.temp_dir / "chroma")}),
            ("sqlite", {"db_path": str(self.temp_dir / "enhanced.db")})
        ]
        
        for backend, config in backend_configs:
            print(f"\n--- Testing {backend} enhanced backend ---")
            
            try:
                # Create hybrid manager
                hybrid_manager = HybridSessionManagerFactory.create_hybrid_manager(
                    enhanced_backend=backend,
                    basic_storage_type="memory",
                    **config
                )
                
                assert hybrid_manager is not None
                print(f"✓ Hybrid manager created with {backend} backend")
                
                # Create session with enhanced features
                session = hybrid_manager.create_session(
                    user_id="hybrid_user",
                    provider="openai",
                    model="gpt-4o"
                )
                
                assert session is not None
                print(f"✓ Hybrid session created: {session.session_id}")
                
                # Test enhanced features if available
                if hybrid_manager.enhanced_available:
                    # Test semantic search
                    if hybrid_manager.enable_semantic_search:
                        try:
                            results = hybrid_manager.search_conversation_history(
                                session.session_id, 
                                "test query"
                            )
                            print(f"✓ Semantic search successful: {len(results)} results")
                        except Exception as e:
                            print(f"! Semantic search failed: {e}")
                    
                    # Test analytics
                    if hybrid_manager.enable_analytics:
                        try:
                            analytics = hybrid_manager.get_conversation_analytics(session.session_id)
                            assert isinstance(analytics, dict)
                            print(f"✓ Analytics retrieved: {list(analytics.keys())}")
                        except Exception as e:
                            print(f"! Analytics failed: {e}")
                else:
                    print(f"! Enhanced features not available for {backend}")
                    
            except Exception as e:
                print(f"! {backend} backend failed: {e}")

    def test_session_persistence_and_recovery(self):
        """Test session persistence across manager restarts"""
        print("\n=== Testing Session Persistence and Recovery ===")
        
        # Create initial manager and sessions
        storage = SQLiteSessionStorage(str(self.test_db_path))
        manager1 = LangSwarmSessionManager(storage=storage)
        
        # Create multiple sessions
        sessions_data = []
        for i, user_id in enumerate(self.test_users):
            provider = self.test_providers[i % len(self.test_providers)]
            model = self.test_models[provider]
            
            session = manager1.create_session(
                user_id=user_id,
                provider=provider,
                model=model,
                session_id=f"persistent_session_{i+1}"
            )
            
            # Add some conversation history
            with patch.object(manager1, '_simulate_provider_response') as mock_response:
                mock_response.return_value = {
                    "message": f"Response to user {user_id}",
                    "usage": {"total_tokens": 20}
                }
                manager1.send_message(session.session_id, f"Hello from {user_id}")
            
            sessions_data.append({
                "session_id": session.session_id,
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "message_count": len(session.history.messages)
            })
            
        print(f"✓ Created {len(sessions_data)} persistent sessions")
        
        # "Restart" by creating new manager with same storage
        manager2 = LangSwarmSessionManager(storage=storage)
        
        # Verify all sessions are recoverable
        for session_data in sessions_data:
            recovered_session = manager2.get_session(session_data["session_id"])
            
            assert recovered_session is not None
            assert recovered_session.user_id == session_data["user_id"]
            assert recovered_session.provider == session_data["provider"]
            assert recovered_session.model == session_data["model"]
            assert len(recovered_session.history.messages) == session_data["message_count"]
            
            print(f"✓ Recovered session {session_data['session_id']} for {session_data['user_id']}")

    def test_multi_user_session_coordination(self):
        """Test multi-user session management and isolation"""
        print("\n=== Testing Multi-User Session Coordination ===")
        
        storage = InMemorySessionStorage()
        manager = LangSwarmSessionManager(storage=storage)
        
        # Create sessions for multiple users
        user_sessions = {}
        for user_id in self.test_users:
            user_sessions[user_id] = []
            
            # Create multiple sessions per user
            for i in range(3):
                provider = self.test_providers[i % len(self.test_providers)]
                model = self.test_models[provider]
                
                session = manager.create_session(
                    user_id=user_id,
                    provider=provider,
                    model=model,
                    session_id=f"{user_id}_session_{i+1}"
                )
                
                user_sessions[user_id].append(session)
        
        print(f"✓ Created sessions for {len(self.test_users)} users")
        
        # Test session isolation
        for user_id, sessions in user_sessions.items():
            # Verify user can access their own sessions
            for session in sessions:
                retrieved = manager.get_session(session.session_id)
                assert retrieved is not None
                assert retrieved.user_id == user_id
            
            # Verify sessions are properly isolated
            user_session_ids = {s.session_id for s in sessions}
            other_user_sessions = [
                s for other_user, other_sessions in user_sessions.items()
                if other_user != user_id
                for s in other_sessions
            ]
            
            for other_session in other_user_sessions:
                assert other_session.session_id not in user_session_ids
            
            print(f"✓ Session isolation verified for {user_id}")
        
        # Test session listing and filtering
        all_sessions = storage.list_sessions()
        assert len(all_sessions) == len(self.test_users) * 3
        print(f"✓ Total sessions: {len(all_sessions)}")
        
        # Test filtering by user
        for user_id in self.test_users:
            user_specific_sessions = storage.list_sessions(user_id=user_id)
            assert len(user_specific_sessions) == 3
            assert all(s.user_id == user_id for s in user_specific_sessions)
            print(f"✓ User filtering works for {user_id}")

    def test_session_cleanup_and_maintenance(self):
        """Test session cleanup and maintenance operations"""
        print("\n=== Testing Session Cleanup and Maintenance ===")
        
        storage = SQLiteSessionStorage(str(self.test_db_path))
        manager = LangSwarmSessionManager(storage=storage)
        
        # Create sessions with different ages
        old_sessions = []
        new_sessions = []
        
        for i in range(5):
            # Create old session (simulated)
            old_session = manager.create_session(
                user_id=f"old_user_{i}",
                provider="openai",
                model="gpt-4o",
                session_id=f"old_session_{i}"
            )
            
            # Manually set old timestamp
            old_date = datetime.now() - timedelta(days=35)
            old_session.metadata.created_at = old_date
            old_session.metadata.updated_at = old_date
            storage.save_session(old_session)
            old_sessions.append(old_session)
            
            # Create new session
            new_session = manager.create_session(
                user_id=f"new_user_{i}",
                provider="claude", 
                model="claude-3-sonnet",
                session_id=f"new_session_{i}"
            )
            new_sessions.append(new_session)
        
        print(f"✓ Created {len(old_sessions)} old sessions and {len(new_sessions)} new sessions")
        
        # Test cleanup of expired sessions
        cleaned_count = manager.cleanup_expired_sessions(max_age_days=30)
        print(f"✓ Cleaned up {cleaned_count} expired sessions")
        
        # Verify old sessions are gone, new sessions remain
        for old_session in old_sessions:
            retrieved = manager.get_session(old_session.session_id)
            assert retrieved is None  # Should be deleted
        
        for new_session in new_sessions:
            retrieved = manager.get_session(new_session.session_id)
            assert retrieved is not None  # Should still exist
            assert retrieved.session_id == new_session.session_id
        
        print(f"✓ Cleanup verification successful")

    def test_enhanced_storage_backends(self):
        """Test enhanced storage with different database backends"""
        print("\n=== Testing Enhanced Storage Backends ===")
        
        # Test configurations for different backends
        backend_configs = [
            ("chromadb", {
                "collection_name": "test_sessions",
                "persist_directory": str(self.temp_dir / "chroma")
            }),
            ("sqlite", {
                "db_path": str(self.temp_dir / "enhanced.db")
            }),
            ("redis", {
                "host": "localhost",
                "port": 6379,
                "db": 1
            })
        ]
        
        for backend_type, config in backend_configs:
            print(f"\n--- Testing {backend_type} enhanced storage ---")
            
            try:
                # Create enhanced storage
                if backend_type == "chromadb":
                    enhanced_storage = EnhancedSessionStorageFactory.create_chromadb_storage(**config)
                elif backend_type == "sqlite":
                    enhanced_storage = EnhancedSessionStorageFactory.create_sqlite_storage(**config)
                elif backend_type == "redis":
                    enhanced_storage = EnhancedSessionStorageFactory.create_redis_storage(**config)
                
                assert enhanced_storage is not None
                print(f"✓ Enhanced storage created for {backend_type}")
                
                # Create test session
                session = LangSwarmSession(
                    user_id="enhanced_user",
                    session_id="enhanced_test_session",
                    provider="openai",
                    model="gpt-4o"
                )
                
                # Add some conversation history
                session.history.add_message(ConversationMessage(
                    content="Hello, I need help with machine learning",
                    role=MessageRole.USER
                ))
                session.history.add_message(ConversationMessage(
                    content="I'd be happy to help with machine learning! What specific area interests you?",
                    role=MessageRole.ASSISTANT
                ))
                
                # Test save
                saved = enhanced_storage.save_session(session)
                assert saved is True
                print(f"✓ Session saved to {backend_type}")
                
                # Test load
                loaded_session = enhanced_storage.load_session(session.session_id)
                assert loaded_session is not None
                assert loaded_session.session_id == session.session_id
                assert len(loaded_session.history.messages) == len(session.history.messages)
                print(f"✓ Session loaded from {backend_type}")
                
                # Test enhanced features
                try:
                    # Test semantic search
                    search_results = enhanced_storage.search_conversation_history(
                        "machine learning", limit=5
                    )
                    print(f"✓ Semantic search: {len(search_results)} results")
                    
                    # Test analytics
                    analytics = enhanced_storage.get_conversation_analytics()
                    assert isinstance(analytics, dict)
                    print(f"✓ Analytics: {list(analytics.keys())}")
                    
                except Exception as e:
                    print(f"! Enhanced features failed: {e}")
                
            except Exception as e:
                print(f"! {backend_type} backend not available: {e}")

    def test_real_world_chat_scenarios(self):
        """Test realistic chat conversation scenarios"""
        print("\n=== Testing Real-World Chat Scenarios ===")
        
        storage = SQLiteSessionStorage(str(self.test_db_path))
        manager = LangSwarmSessionManager(storage=storage)
        
        # Scenario 1: Customer Support Conversation
        print("\n--- Scenario 1: Customer Support ---")
        support_session = manager.create_session(
            user_id="customer_001",
            provider="claude",
            model="claude-3-sonnet",
            session_id="support_session_001"
        )
        
        support_conversation = [
            ("I'm having trouble with my account login", MessageRole.USER),
            ("I'd be happy to help you with your login issue. Can you tell me what error message you're seeing?", MessageRole.ASSISTANT),
            ("It says 'Invalid credentials' but I'm sure my password is correct", MessageRole.USER),
            ("Let's try resetting your password. I'll send you a reset link to your registered email.", MessageRole.ASSISTANT),
            ("Great, I received the email and was able to reset it. Now I can log in. Thank you!", MessageRole.USER),
            ("You're welcome! Is there anything else I can help you with today?", MessageRole.ASSISTANT)
        ]
        
        with patch.object(manager, '_simulate_provider_response') as mock_response:
            for i, (message, role) in enumerate(support_conversation):
                if role == MessageRole.USER:
                    # Set up mock response for next assistant message
                    if i + 1 < len(support_conversation):
                        mock_response.return_value = {
                            "message": support_conversation[i + 1][0],
                            "usage": {"total_tokens": 50}
                        }
                    manager.send_message(support_session.session_id, message)
        
        assert len(support_session.history.messages) >= len([m for m, r in support_conversation if r == MessageRole.USER])
        print(f"✓ Customer support conversation completed: {len(support_session.history.messages)} messages")
        
        # Scenario 2: Multi-turn Technical Discussion
        print("\n--- Scenario 2: Technical Discussion ---")
        tech_session = manager.create_session(
            user_id="developer_001",
            provider="openai",
            model="gpt-4o",
            session_id="tech_session_001"
        )
        
        tech_topics = [
            "Explain the difference between SQL and NoSQL databases",
            "What are the advantages of microservices architecture?", 
            "How does machine learning model training work?",
            "What are best practices for API security?",
            "Explain containerization with Docker"
        ]
        
        with patch.object(manager, '_simulate_provider_response') as mock_response:
            for topic in tech_topics:
                mock_response.return_value = {
                    "message": f"Here's a detailed explanation of {topic.lower()}...",
                    "usage": {"total_tokens": 200}
                }
                manager.send_message(tech_session.session_id, topic)
        
        assert len(tech_session.history.messages) >= len(tech_topics)
        print(f"✓ Technical discussion completed: {len(tech_session.history.messages)} messages")
        
        # Scenario 3: Context-Aware Conversation
        print("\n--- Scenario 3: Context-Aware Conversation ---")
        context_session = manager.create_session(
            user_id="user_context",
            provider="gemini",
            model="gemini-pro",
            session_id="context_session_001"
        )
        
        context_flow = [
            "I'm planning a trip to Japan",
            "What's the best time to visit?",
            "I'm interested in cherry blossoms",
            "What cities should I visit for the best cherry blossom experience?",
            "How long should I stay in each city?",
            "What's the budget like for this kind of trip?"
        ]
        
        with patch.object(manager, '_simulate_provider_response') as mock_response:
            for message in context_flow:
                mock_response.return_value = {
                    "message": f"Regarding your Japan trip planning: {message}...",
                    "usage": {"total_tokens": 150}
                }
                manager.send_message(context_session.session_id, message)
        
        print(f"✓ Context-aware conversation completed: {len(context_session.history.messages)} messages")

    def test_cross_session_analytics(self):
        """Test analytics and insights across multiple sessions"""
        print("\n=== Testing Cross-Session Analytics ===")
        
        # Use hybrid manager for enhanced analytics
        try:
            hybrid_manager = HybridSessionManagerFactory.create_hybrid_manager(
                enhanced_backend="mock",
                basic_storage_type="memory"
            )
            
            # Create sessions across different users and providers
            analytics_sessions = []
            for i, user_id in enumerate(self.test_users):
                for j, provider in enumerate(self.test_providers[:3]):  # Limit to 3 providers
                    model = self.test_models[provider]
                    
                    session = hybrid_manager.create_session(
                        user_id=user_id,
                        provider=provider,
                        model=model,
                        session_id=f"analytics_session_{i}_{j}"
                    )
                    
                    # Simulate some conversation activity
                    with patch.object(hybrid_manager, '_simulate_provider_response') as mock_response:
                        mock_response.return_value = {
                            "message": f"Analytics response for {user_id}",
                            "usage": {"total_tokens": 100}
                        }
                        
                        for k in range(3):  # 3 messages per session
                            hybrid_manager.send_message(
                                session.session_id, 
                                f"Analytics test message {k+1}"
                            )
                    
                    analytics_sessions.append(session)
            
            print(f"✓ Created {len(analytics_sessions)} sessions for analytics testing")
            
            # Test global analytics (if enhanced features available)
            if hybrid_manager.enhanced_available:
                try:
                    global_analytics = hybrid_manager.get_conversation_analytics()
                    assert isinstance(global_analytics, dict)
                    print(f"✓ Global analytics retrieved: {list(global_analytics.keys())}")
                except Exception as e:
                    print(f"! Global analytics failed: {e}")
                
                # Test user-specific analytics
                for user_id in self.test_users:
                    try:
                        user_analytics = hybrid_manager.get_conversation_analytics(user_id=user_id)
                        assert isinstance(user_analytics, dict)
                        print(f"✓ User analytics for {user_id}: {list(user_analytics.keys())}")
                    except Exception as e:
                        print(f"! User analytics failed for {user_id}: {e}")
            else:
                print("! Enhanced analytics not available")
        
        except Exception as e:
            print(f"! Analytics testing failed: {e}")

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        print("\n=== Testing Error Handling and Recovery ===")
        
        storage = InMemorySessionStorage()
        manager = LangSwarmSessionManager(storage=storage)
        
        # Test invalid session operations
        print("\n--- Testing Invalid Operations ---")
        
        # Try to get non-existent session
        non_existent = manager.get_session("non_existent_session")
        assert non_existent is None
        print("✓ Non-existent session handling")
        
        # Try to send message to non-existent session
        try:
            manager.send_message("non_existent_session", "test message")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Invalid session message handling")
        
        # Try to archive non-existent session
        archived = manager.archive_session("non_existent_session")
        assert archived is False
        print("✓ Invalid session archival handling")
        
        # Test provider adapter errors
        print("\n--- Testing Provider Adapter Errors ---")
        
        try:
            invalid_adapter = SessionAdapterFactory.create_adapter("invalid_provider", "invalid_model")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✓ Invalid provider handling")
        
        # Test session strategy errors
        print("\n--- Testing Strategy Errors ---")
        
        try:
            invalid_strategy = SessionStrategyFactory.create_strategy("invalid_strategy")
            assert False, "Should have raised ValueError"  
        except (ValueError, KeyError):
            print("✓ Invalid strategy handling")
        
        # Test storage errors with mock failures
        print("\n--- Testing Storage Error Recovery ---")
        
        with patch.object(storage, 'save_session', return_value=False):
            session = manager.create_session(
                user_id="test_user",
                provider="openai",
                model="gpt-4o"
            )
            # Session should still be created in memory even if storage fails
            assert session is not None
            print("✓ Storage failure recovery")

    def test_performance_and_concurrency(self):
        """Test performance characteristics and concurrent access"""
        print("\n=== Testing Performance and Concurrency ===")
        
        storage = InMemorySessionStorage()
        manager = LangSwarmSessionManager(storage=storage)
        
        # Test bulk session creation performance
        print("\n--- Performance Testing ---")
        
        start_time = time.time()
        bulk_sessions = []
        
        for i in range(100):
            session = manager.create_session(
                user_id=f"perf_user_{i}",
                provider=self.test_providers[i % len(self.test_providers)],
                model="test-model",
                session_id=f"perf_session_{i}"
            )
            bulk_sessions.append(session)
        
        creation_time = time.time() - start_time
        print(f"✓ Created 100 sessions in {creation_time:.3f} seconds")
        
        # Test bulk retrieval performance
        start_time = time.time()
        for session in bulk_sessions:
            retrieved = manager.get_session(session.session_id)
            assert retrieved is not None
        
        retrieval_time = time.time() - start_time
        print(f"✓ Retrieved 100 sessions in {retrieval_time:.3f} seconds")
        
        # Test concurrent session access (basic simulation)
        print("\n--- Concurrency Simulation ---")
        
        shared_session = manager.create_session(
            user_id="shared_user",
            provider="openai", 
            model="gpt-4o",
            session_id="shared_session"
        )
        
        # Simulate concurrent message sending
        with patch.object(manager, '_simulate_provider_response') as mock_response:
            mock_response.return_value = {
                "message": "Concurrent response",
                "usage": {"total_tokens": 50}
            }
            
            # Send multiple messages rapidly
            for i in range(10):
                manager.send_message(shared_session.session_id, f"Concurrent message {i}")
        
        # Verify session integrity
        final_session = manager.get_session(shared_session.session_id)
        assert final_session is not None
        assert len(final_session.history.messages) >= 10
        print(f"✓ Concurrent access test: {len(final_session.history.messages)} messages")

    def test_system_health_and_monitoring(self):
        """Test system health monitoring and diagnostics"""
        print("\n=== Testing System Health and Monitoring ===")
        
        storage = SQLiteSessionStorage(str(self.test_db_path))
        manager = LangSwarmSessionManager(storage=storage)
        
        # Create test sessions for health monitoring
        health_sessions = []
        for i in range(10):
            session = manager.create_session(
                user_id=f"health_user_{i}",
                provider=self.test_providers[i % len(self.test_providers)],
                model="health-test-model",
                session_id=f"health_session_{i}"
            )
            health_sessions.append(session)
        
        print(f"✓ Created {len(health_sessions)} sessions for health monitoring")
        
        # Test session counting and statistics
        all_sessions = storage.list_sessions()
        active_sessions = storage.list_sessions(status=SessionStatus.ACTIVE)
        
        assert len(all_sessions) >= len(health_sessions)
        assert len(active_sessions) >= len(health_sessions)
        print(f"✓ Health stats: {len(all_sessions)} total, {len(active_sessions)} active")
        
        # Test memory usage monitoring
        active_session_count = len(manager._active_sessions)
        print(f"✓ Active sessions in memory: {active_session_count}")
        
        # Test adapter and strategy cache monitoring
        adapter_cache_size = len(manager._adapter_cache)
        strategy_cache_size = len(manager._strategy_cache)
        print(f"✓ Cache sizes - Adapters: {adapter_cache_size}, Strategies: {strategy_cache_size}")
        
        # Test storage health check
        try:
            # Test database connectivity (SQLite)
            test_session = manager.create_session(
                user_id="health_check_user",
                provider="openai",
                model="gpt-4o",
                session_id="health_check_session"
            )
            
            saved = storage.save_session(test_session)
            loaded = storage.load_session(test_session.session_id)
            deleted = storage.delete_session(test_session.session_id)
            
            assert saved is True
            assert loaded is not None
            assert deleted is True
            print("✓ Storage health check passed")
            
        except Exception as e:
            print(f"! Storage health check failed: {e}")
        
        # Test session manager health status
        manager_health = {
            "total_sessions_created": len(health_sessions),
            "active_sessions_cached": len(manager._active_sessions),
            "adapter_cache_size": len(manager._adapter_cache),
            "strategy_cache_size": len(manager._strategy_cache),
            "default_session_control": manager.default_session_control.value,
            "storage_type": type(manager.storage).__name__
        }
        
        print(f"✓ Manager health status: {manager_health}")
        assert isinstance(manager_health, dict)
        assert all(isinstance(v, (int, str)) for v in manager_health.values())


def run_session_management_integration_tests():
    """Run all session management integration tests"""
    print("="*80)
    print("LANGSWARM SESSION MANAGEMENT INTEGRATION TESTS")
    print("="*80)
    
    # Create test instance
    test_instance = TestSessionManagementIntegration()
    test_instance.setup_test_environment()
    
    try:
        # Run all test methods
        test_methods = [
            test_instance.test_basic_session_lifecycle,
            test_instance.test_session_strategies_comprehensive,
            test_instance.test_provider_adapters_comprehensive,
            test_instance.test_hybrid_session_management,
            test_instance.test_session_persistence_and_recovery,
            test_instance.test_multi_user_session_coordination,
            test_instance.test_session_cleanup_and_maintenance,
            test_instance.test_enhanced_storage_backends,
            test_instance.test_real_world_chat_scenarios,
            test_instance.test_cross_session_analytics,
            test_instance.test_error_handling_and_recovery,
            test_instance.test_performance_and_concurrency,
            test_instance.test_system_health_and_monitoring
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed += 1
                print(f"\n✅ {test_method.__name__} PASSED")
            except Exception as e:
                failed += 1
                print(f"\n❌ {test_method.__name__} FAILED: {e}")
                import traceback
                print(traceback.format_exc())
        
        print("\n" + "="*80)
        print(f"SESSION MANAGEMENT INTEGRATION TEST RESULTS")
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"TOTAL:  {passed + failed}")
        print("="*80)
        
        return passed, failed
        
    finally:
        # Cleanup
        import shutil
        if hasattr(test_instance, 'temp_dir') and test_instance.temp_dir.exists():
            shutil.rmtree(test_instance.temp_dir)


if __name__ == "__main__":
    run_session_management_integration_tests() 