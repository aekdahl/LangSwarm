"""
Tests for Priority 5: Native Thread IDs & Session Management
============================================================

Comprehensive test suite for LangSwarm session management system
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import sqlite3

from langswarm.core.session.models import (
    LangSwarmSession,
    SessionMetadata,
    ConversationMessage,
    ConversationHistory,
    MessageRole,
    SessionControl,
    SessionStatus
)
from langswarm.core.session.strategies import (
    SessionStrategy,
    NativeSessionStrategy,
    ClientSideSessionStrategy,
    HybridSessionStrategy,
    SessionStrategyFactory
)
from langswarm.core.session.adapters import (
    BaseSessionAdapter,
    OpenAISessionAdapter,
    ClaudeSessionAdapter,
    GeminiSessionAdapter,
    MistralSessionAdapter,
    CohereSessionAdapter,
    SessionAdapterFactory
)
from langswarm.core.session.storage import (
    SessionStorage,
    InMemorySessionStorage,
    SQLiteSessionStorage,
    SessionStorageFactory
)
from langswarm.core.session.manager import LangSwarmSessionManager


class TestSessionModels:
    """Test session data models"""
    
    def test_conversation_message_creation(self):
        """Test ConversationMessage creation and serialization"""
        message = ConversationMessage(
            id="msg_123",
            role=MessageRole.USER,
            content="Hello, world!"
        )
        
        assert message.id == "msg_123"
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert isinstance(message.timestamp, datetime)
        
        # Test serialization
        data = message.to_dict()
        assert data["id"] == "msg_123"
        assert data["role"] == "user"
        assert data["content"] == "Hello, world!"
        
        # Test deserialization
        restored = ConversationMessage.from_dict(data)
        assert restored.id == message.id
        assert restored.role == message.role
        assert restored.content == message.content
    
    def test_session_metadata_creation(self):
        """Test SessionMetadata creation and serialization"""
        metadata = SessionMetadata(
            user_id="user_123",
            session_id="session_456",
            provider="openai",
            model="gpt-4o",
            session_control=SessionControl.HYBRID
        )
        
        assert metadata.user_id == "user_123"
        assert metadata.session_id == "session_456"
        assert metadata.provider == "openai"
        assert metadata.model == "gpt-4o"
        assert metadata.session_control == SessionControl.HYBRID
        assert metadata.status == SessionStatus.ACTIVE
        
        # Test serialization
        data = metadata.to_dict()
        restored = SessionMetadata.from_dict(data)
        assert restored.user_id == metadata.user_id
        assert restored.session_control == metadata.session_control
    
    def test_conversation_history(self):
        """Test ConversationHistory functionality"""
        history = ConversationHistory(session_id="session_123")
        
        # Add messages
        msg1 = ConversationMessage("msg1", MessageRole.USER, "Hello")
        msg2 = ConversationMessage("msg2", MessageRole.ASSISTANT, "Hi there!")
        
        history.add_message(msg1)
        history.add_message(msg2)
        
        assert len(history.messages) == 2
        assert history.messages[0].content == "Hello"
        assert history.messages[1].content == "Hi there!"
        
        # Test recent messages
        recent = history.get_recent_messages(1)
        assert len(recent) == 1
        assert recent[0].content == "Hi there!"
        
        # Test truncation
        history.truncate_to_limit(1)
        assert len(history.messages) == 1
        assert history.truncated_at is not None
    
    def test_langswarm_session(self):
        """Test LangSwarmSession functionality"""
        session = LangSwarmSession(
            user_id="user_123",
            provider="openai",
            model="gpt-4o"
        )
        
        assert session.user_id == "user_123"
        assert session.provider == "openai"
        assert session.model == "gpt-4o"
        assert session.is_active
        
        # Add message
        message = session.add_message("Hello", MessageRole.USER)
        assert message.content == "Hello"
        assert session.message_count == 1
        
        # Get messages for API
        api_messages = session.get_messages_for_api()
        assert len(api_messages) == 1
        assert api_messages[0]["role"] == "user"
        assert api_messages[0]["content"] == "Hello"
        
        # Test serialization
        data = session.to_dict()
        restored = LangSwarmSession.from_dict(data)
        assert restored.user_id == session.user_id
        assert restored.session_id == session.session_id
        assert len(restored.history.messages) == 1


class TestSessionStrategies:
    """Test session management strategies"""
    
    def test_native_session_strategy(self):
        """Test NativeSessionStrategy"""
        strategy = NativeSessionStrategy()
        
        # Test native session support detection
        assert strategy.supports_threading("openai")
        assert strategy.supports_threading("mistral")
        assert not strategy.supports_threading("claude")
        assert not strategy.supports_threading("gemini")
        
        # Test should use native sessions
        assert strategy.should_use_native_sessions("openai", "gpt-4o")
        assert not strategy.should_use_native_sessions("claude", "claude-3")
    
    def test_client_side_session_strategy(self):
        """Test ClientSideSessionStrategy"""
        strategy = ClientSideSessionStrategy()
        
        # Client-side supports all providers
        assert strategy.supports_threading("openai")
        assert strategy.supports_threading("claude")
        assert strategy.supports_threading("gemini")
        
        # Never uses native sessions
        assert not strategy.should_use_native_sessions("openai", "gpt-4o")
        assert not strategy.should_use_native_sessions("mistral", "mistral-large")
    
    def test_hybrid_session_strategy(self):
        """Test HybridSessionStrategy"""
        strategy = HybridSessionStrategy()
        
        # All providers supported
        assert strategy.supports_threading("openai")
        assert strategy.supports_threading("claude")
        
        # Intelligent decisions based on provider
        assert strategy.should_use_native_sessions("openai", "gpt-4o")
        assert not strategy.should_use_native_sessions("claude", "claude-3")
        
        # Test optimal strategy detection
        assert strategy.get_optimal_strategy("openai", "gpt-4o") == "native"
        assert strategy.get_optimal_strategy("claude", "claude-3") == "client"
    
    def test_session_strategy_factory(self):
        """Test SessionStrategyFactory"""
        # Test strategy creation
        native = SessionStrategyFactory.create_strategy(SessionControl.NATIVE)
        assert isinstance(native, NativeSessionStrategy)
        
        client = SessionStrategyFactory.create_strategy(SessionControl.LANGSWARM)
        assert isinstance(client, ClientSideSessionStrategy)
        
        hybrid = SessionStrategyFactory.create_strategy(SessionControl.HYBRID)
        assert isinstance(hybrid, HybridSessionStrategy)
        
        # Test recommendations
        openai_rec = SessionStrategyFactory.get_recommended_strategy("openai", "gpt-4o")
        assert openai_rec == SessionControl.HYBRID
        
        claude_rec = SessionStrategyFactory.get_recommended_strategy("claude", "claude-3")
        assert claude_rec == SessionControl.LANGSWARM
        
        # Test capability analysis
        capabilities = SessionStrategyFactory.analyze_provider_capabilities("openai")
        assert capabilities["native_threading"] is True
        assert "assistants_api" in capabilities["features"]


class TestSessionAdapters:
    """Test provider-specific session adapters"""
    
    def test_openai_session_adapter(self):
        """Test OpenAISessionAdapter"""
        adapter = OpenAISessionAdapter("gpt-4o")
        
        assert adapter.provider == "openai"
        assert adapter.model == "gpt-4o"
        assert adapter.supports_native_sessions()
        
        # Test session creation
        session = LangSwarmSession("user_123", provider="openai", model="gpt-4o")
        session_params = adapter.create_session(session)
        
        assert session_params["model"] == "gpt-4o"
        assert "messages" in session_params
    
    def test_claude_session_adapter(self):
        """Test ClaudeSessionAdapter"""
        adapter = ClaudeSessionAdapter("claude-3-sonnet")
        
        assert adapter.provider == "claude"
        assert adapter.model == "claude-3-sonnet"
        assert not adapter.supports_native_sessions()
        
        # Test request preparation
        session = LangSwarmSession("user_123", provider="claude", model="claude-3-sonnet")
        request = adapter.prepare_request(session, "Hello")
        
        assert request["model"] == "claude-3-sonnet"
        assert request["max_tokens"] == 4096
        assert len(request["messages"]) == 1
        assert request["messages"][0]["content"] == "Hello"
    
    def test_gemini_session_adapter(self):
        """Test GeminiSessionAdapter"""
        adapter = GeminiSessionAdapter("gemini-pro")
        
        assert adapter.provider == "gemini"
        assert not adapter.supports_native_sessions()
        
        # Test Gemini-specific message format
        session = LangSwarmSession("user_123", provider="gemini", model="gemini-pro")
        session.add_message("Hello", MessageRole.USER)
        
        request = adapter.prepare_request(session, "How are you?")
        
        assert "contents" in request
        assert len(request["contents"]) == 2  # Previous message + new message
        assert request["contents"][0]["role"] == "user"
        assert request["contents"][0]["parts"][0]["text"] == "Hello"
    
    def test_mistral_session_adapter(self):
        """Test MistralSessionAdapter"""
        adapter = MistralSessionAdapter("mistral-large")
        
        assert adapter.provider == "mistral"
        assert adapter.supports_native_sessions()
        
        # Test with native conversation management
        session = LangSwarmSession("user_123", provider="mistral", model="mistral-large")
        session.metadata.provider_agent_id = "agent_123"
        session.metadata.provider_conversation_id = "conv_456"
        
        request = adapter.prepare_request(session, "Hello")
        
        assert request["agent_id"] == "agent_123"
        assert request["conversation_id"] == "conv_456"
    
    def test_cohere_session_adapter(self):
        """Test CohereSessionAdapter"""
        adapter = CohereSessionAdapter("command-r")
        
        assert adapter.provider == "cohere"
        assert not adapter.supports_native_sessions()
        
        # Test Cohere chat history format
        session = LangSwarmSession("user_123", provider="cohere", model="command-r")
        session.add_message("Hello", MessageRole.USER)
        session.add_message("Hi there!", MessageRole.ASSISTANT)
        
        request = adapter.prepare_request(session, "How are you?")
        
        assert request["message"] == "How are you?"
        assert "chat_history" in request
        assert len(request["chat_history"]) == 2
        assert request["chat_history"][0]["role"] == "USER"
        assert request["chat_history"][1]["role"] == "CHATBOT"
    
    def test_session_adapter_factory(self):
        """Test SessionAdapterFactory"""
        # Test adapter creation
        openai_adapter = SessionAdapterFactory.create_adapter("openai", "gpt-4o")
        assert isinstance(openai_adapter, OpenAISessionAdapter)
        
        claude_adapter = SessionAdapterFactory.create_adapter("claude", "claude-3")
        assert isinstance(claude_adapter, ClaudeSessionAdapter)
        
        # Test supported providers
        providers = SessionAdapterFactory.get_supported_providers()
        assert "openai" in providers
        assert "claude" in providers
        assert "gemini" in providers
        assert "mistral" in providers
        assert "cohere" in providers
        
        # Test provider support check
        assert SessionAdapterFactory.supports_provider("openai")
        assert SessionAdapterFactory.supports_provider("CLAUDE")  # Case insensitive
        assert not SessionAdapterFactory.supports_provider("unknown")


class TestSessionStorage:
    """Test session storage backends"""
    
    def test_in_memory_storage(self):
        """Test InMemorySessionStorage"""
        storage = InMemorySessionStorage()
        
        # Create test session
        session = LangSwarmSession("user_123", provider="openai", model="gpt-4o")
        session.add_message("Hello", MessageRole.USER)
        
        # Test save and load
        assert storage.save_session(session)
        loaded = storage.load_session(session.session_id)
        
        assert loaded is not None
        assert loaded.user_id == "user_123"
        assert loaded.provider == "openai"
        assert len(loaded.history.messages) == 1
        
        # Test list sessions
        sessions = storage.list_sessions(user_id="user_123")
        assert len(sessions) == 1
        assert sessions[0].user_id == "user_123"
        
        # Test delete
        assert storage.delete_session(session.session_id)
        assert storage.load_session(session.session_id) is None
    
    def test_sqlite_storage(self):
        """Test SQLiteSessionStorage"""
        # Use temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            storage = SQLiteSessionStorage(db_path)
            
            # Create test session
            session = LangSwarmSession("user_456", provider="claude", model="claude-3")
            session.add_message("Test message", MessageRole.USER)
            
            # Test save and load
            assert storage.save_session(session)
            loaded = storage.load_session(session.session_id)
            
            assert loaded is not None
            assert loaded.user_id == "user_456"
            assert loaded.provider == "claude"
            assert len(loaded.history.messages) == 1
            
            # Test metadata update
            metadata_update = {"tags": ["test"], "custom_metadata": {"key": "value"}}
            assert storage.update_session_metadata(session.session_id, metadata_update)
            
            updated = storage.load_session(session.session_id)
            assert "test" in updated.metadata.tags
            assert updated.metadata.custom_metadata["key"] == "value"
            
            # Test cleanup
            # Make session old
            old_time = datetime.now() - timedelta(days=31)
            storage.update_session_metadata(session.session_id, {"updated_at": old_time})
            
            cleaned = storage.cleanup_expired_sessions(max_age_days=30)
            assert cleaned == 1
            
        finally:
            # Clean up temp file
            Path(db_path).unlink(missing_ok=True)
    
    def test_session_storage_factory(self):
        """Test SessionStorageFactory"""
        # Test memory storage creation
        memory_storage = SessionStorageFactory.create_storage("memory")
        assert isinstance(memory_storage, InMemorySessionStorage)
        
        # Test SQLite storage creation
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            sqlite_storage = SessionStorageFactory.create_storage("sqlite", db_path=db_path)
            assert isinstance(sqlite_storage, SQLiteSessionStorage)
        finally:
            Path(db_path).unlink(missing_ok=True)
        
        # Test invalid storage type
        with pytest.raises(ValueError):
            SessionStorageFactory.create_storage("invalid")


class TestSessionManager:
    """Test the main LangSwarmSessionManager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.storage = InMemorySessionStorage()
        self.manager = LangSwarmSessionManager(storage=self.storage)
    
    def test_session_creation(self):
        """Test session creation"""
        session = self.manager.create_session(
            user_id="user_123",
            provider="openai",
            model="gpt-4o"
        )
        
        assert session.user_id == "user_123"
        assert session.provider == "openai"
        assert session.model == "gpt-4o"
        assert session._manager == self.manager
        assert session._strategy is not None
        assert session._adapter is not None
        
        # Verify session was saved
        loaded = self.manager.get_session(session.session_id)
        assert loaded is not None
        assert loaded.user_id == "user_123"
    
    def test_session_retrieval(self):
        """Test session retrieval"""
        # Create session
        session = self.manager.create_session("user_456", provider="claude", model="claude-3")
        session_id = session.session_id
        
        # Clear active sessions cache to test storage retrieval
        self.manager._active_sessions.clear()
        
        # Retrieve session
        loaded = self.manager.get_session(session_id)
        assert loaded is not None
        assert loaded.user_id == "user_456"
        assert loaded._strategy is not None
        assert loaded._adapter is not None
        
        # Should be back in active sessions
        assert session_id in self.manager._active_sessions
    
    def test_send_message(self):
        """Test sending messages"""
        # Create session
        session = self.manager.create_session("user_789", provider="openai", model="gpt-4o")
        
        # Send message
        response = self.manager.send_message(session.session_id, "Hello, AI!")
        
        assert response.role == MessageRole.ASSISTANT
        assert response.content is not None
        
        # Verify message was added to session
        updated_session = self.manager.get_session(session.session_id)
        assert len(updated_session.history.messages) == 2  # User + assistant message
        assert updated_session.history.messages[0].content == "Hello, AI!"
        assert updated_session.history.messages[0].role == MessageRole.USER
    
    def test_session_archival(self):
        """Test session archival"""
        session = self.manager.create_session("user_archive", provider="gemini", model="gemini-pro")
        session_id = session.session_id
        
        # Archive session
        assert self.manager.archive_session(session_id)
        
        # Verify session is archived
        archived = self.manager.get_session(session_id)
        assert archived.metadata.status == SessionStatus.ARCHIVED
        
        # Should be removed from active sessions
        assert session_id not in self.manager._active_sessions
    
    def test_session_deletion(self):
        """Test session deletion"""
        session = self.manager.create_session("user_delete", provider="mistral", model="mistral-large")
        session_id = session.session_id
        
        # Delete session
        assert self.manager.delete_session(session_id)
        
        # Verify session is deleted
        assert self.manager.get_session(session_id) is None
        assert session_id not in self.manager._active_sessions
    
    def test_session_listing(self):
        """Test session listing"""
        # Create multiple sessions
        session1 = self.manager.create_session("user_list_1", provider="openai", model="gpt-4o")
        session2 = self.manager.create_session("user_list_1", provider="claude", model="claude-3")
        session3 = self.manager.create_session("user_list_2", provider="gemini", model="gemini-pro")
        
        # List all sessions
        all_sessions = self.manager.list_sessions()
        assert len(all_sessions) == 3
        
        # List by user
        user1_sessions = self.manager.list_sessions(user_id="user_list_1")
        assert len(user1_sessions) == 2
        
        user2_sessions = self.manager.list_sessions(user_id="user_list_2")
        assert len(user2_sessions) == 1
        
        # List by status
        active_sessions = self.manager.list_sessions(status=SessionStatus.ACTIVE)
        assert len(active_sessions) == 3
    
    def test_session_statistics(self):
        """Test session statistics"""
        # Create sessions with different providers
        self.manager.create_session("user_stats_1", provider="openai", model="gpt-4o")
        self.manager.create_session("user_stats_2", provider="openai", model="gpt-4-turbo")
        self.manager.create_session("user_stats_3", provider="claude", model="claude-3")
        
        stats = self.manager.get_session_statistics()
        
        assert stats["active_sessions"] == 3
        assert stats["provider_distribution"]["openai"] == 2
        assert stats["provider_distribution"]["claude"] == 1
        assert "openai" in stats["supported_providers"]
        assert "strategies" in stats["cache_sizes"]
        assert "adapters" in stats["cache_sizes"]
    
    def test_provider_capabilities_analysis(self):
        """Test provider capabilities analysis"""
        openai_caps = self.manager.analyze_provider_capabilities("openai")
        assert openai_caps["native_threading"] is True
        assert openai_caps["stateful_conversations"] is True
        assert "assistants_api" in openai_caps["features"]
        
        claude_caps = self.manager.analyze_provider_capabilities("claude")
        assert claude_caps["native_threading"] is False
        assert claude_caps["stateful_conversations"] is False
        assert "message_ids" in claude_caps["features"]
    
    def test_cleanup_expired_sessions(self):
        """Test expired session cleanup"""
        # Create session
        session = self.manager.create_session("user_cleanup", provider="cohere", model="command-r")
        
        # Make session old by updating storage directly
        old_time = datetime.now() - timedelta(days=31)
        self.storage.update_session_metadata(
            session.session_id, 
            {"updated_at": old_time}
        )
        
        # Cleanup
        cleaned_count = self.manager.cleanup_expired_sessions(max_age_days=30)
        assert cleaned_count == 1
        
        # Session should be gone
        assert self.manager.get_session(session.session_id) is None
    
    def test_error_handling(self):
        """Test error handling"""
        # Test sending message to non-existent session
        with pytest.raises(ValueError, match="Session .* not found"):
            self.manager.send_message("non_existent", "Hello")
        
        # Test archiving non-existent session
        assert not self.manager.archive_session("non_existent")
        
        # Test deleting non-existent session
        assert not self.manager.delete_session("non_existent")


class TestIntegration:
    """Integration tests for the complete session management system"""
    
    def test_multi_provider_session_workflow(self):
        """Test complete workflow with multiple providers"""
        manager = LangSwarmSessionManager(storage=InMemorySessionStorage())
        
        # Create sessions for different providers
        providers_models = [
            ("openai", "gpt-4o"),
            ("claude", "claude-3-sonnet"),
            ("gemini", "gemini-pro"),
            ("mistral", "mistral-large"),
            ("cohere", "command-r")
        ]
        
        sessions = []
        for provider, model in providers_models:
            session = manager.create_session(
                user_id=f"user_{provider}",
                provider=provider,
                model=model
            )
            sessions.append(session)
            
            # Send a message
            response = manager.send_message(session.session_id, f"Hello from {provider}!")
            assert response.role == MessageRole.ASSISTANT
            assert response.content is not None
        
        # Verify all sessions work
        stats = manager.get_session_statistics()
        assert stats["active_sessions"] == 5
        assert len(stats["provider_distribution"]) == 5
        
        # Test different session controls
        for session in sessions:
            assert session._strategy is not None
            assert session._adapter is not None
            assert session._adapter.provider == session.provider
    
    def test_session_persistence_workflow(self):
        """Test session persistence across manager instances"""
        # Use temporary SQLite database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create manager and session
            storage1 = SQLiteSessionStorage(db_path)
            manager1 = LangSwarmSessionManager(storage=storage1)
            
            session = manager1.create_session("persistent_user", provider="openai", model="gpt-4o")
            session_id = session.session_id
            
            manager1.send_message(session_id, "First message")
            manager1.send_message(session_id, "Second message")
            
            # Create new manager instance with same storage
            storage2 = SQLiteSessionStorage(db_path)
            manager2 = LangSwarmSessionManager(storage=storage2)
            
            # Load session from new manager
            loaded_session = manager2.get_session(session_id)
            assert loaded_session is not None
            assert loaded_session.user_id == "persistent_user"
            assert len(loaded_session.history.messages) == 4  # 2 user + 2 assistant
            
            # Continue conversation
            response = manager2.send_message(session_id, "Third message")
            assert response.role == MessageRole.ASSISTANT
            
            # Verify persistence
            final_session = manager2.get_session(session_id)
            assert len(final_session.history.messages) == 6  # 3 user + 3 assistant
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    def test_session_control_strategy_switching(self):
        """Test switching between session control strategies"""
        manager = LangSwarmSessionManager(storage=InMemorySessionStorage())
        
        # Create session with different strategies
        native_session = manager.create_session(
            "user_native",
            provider="openai",
            model="gpt-4o",
            session_control=SessionControl.NATIVE
        )
        
        client_session = manager.create_session(
            "user_client",
            provider="openai", 
            model="gpt-4o",
            session_control=SessionControl.LANGSWARM
        )
        
        hybrid_session = manager.create_session(
            "user_hybrid",
            provider="openai",
            model="gpt-4o",
            session_control=SessionControl.HYBRID
        )
        
        # Verify strategy assignment
        assert isinstance(native_session._strategy, 
                         (type(SessionStrategyFactory.create_strategy(SessionControl.NATIVE))))
        assert isinstance(client_session._strategy,
                         (type(SessionStrategyFactory.create_strategy(SessionControl.LANGSWARM))))
        assert isinstance(hybrid_session._strategy,
                         (type(SessionStrategyFactory.create_strategy(SessionControl.HYBRID))))
        
        # Test behavior differences
        assert native_session._strategy.should_use_native_sessions("openai", "gpt-4o")
        assert not client_session._strategy.should_use_native_sessions("openai", "gpt-4o")
        
        # Hybrid should choose intelligently
        hybrid_strategy = hybrid_session._strategy
        assert hybrid_strategy.should_use_native_sessions("openai", "gpt-4o")  # Native for OpenAI
        assert not hybrid_strategy.should_use_native_sessions("claude", "claude-3")  # Client for Claude


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 