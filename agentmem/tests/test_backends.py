"""
Test suite for AgentMem backends (InMemory, SQLite, Redis)
"""

import pytest
import asyncio
from datetime import datetime, timezone
from agentmem import (
    InMemoryBackend,
    SQLiteBackend,
    Message,
    MessageRole,
    SessionMetadata,
    SessionStatus,
)


@pytest.mark.asyncio
async def test_inmemory_backend_basic():
    """Test basic InMemory backend operations"""
    backend = InMemoryBackend()
    await backend.connect()
    
    assert backend.is_connected
    assert backend.backend_type.value == "in_memory"
    
    # Create session
    metadata = SessionMetadata(session_id="test_session", user_id="user1")
    session = await backend.create_session(metadata)
    
    assert session.session_id == "test_session"
    assert session.metadata.user_id == "user1"
    
    # Add message
    message = Message(role=MessageRole.USER, content="Hello")
    await session.add_message(message)
    
    # Get messages
    messages = await session.get_messages()
    assert len(messages) == 1
    assert messages[0].content == "Hello"
    assert messages[0].role == MessageRole.USER
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_inmemory_multiple_messages():
    """Test adding and retrieving multiple messages"""
    backend = InMemoryBackend()
    await backend.connect()
    
    metadata = SessionMetadata(session_id="test_multi", user_id="user1")
    session = await backend.create_session(metadata)
    
    # Add multiple messages
    messages_to_add = [
        Message(role=MessageRole.USER, content="Message 1"),
        Message(role=MessageRole.ASSISTANT, content="Response 1"),
        Message(role=MessageRole.USER, content="Message 2"),
        Message(role=MessageRole.ASSISTANT, content="Response 2"),
    ]
    
    for msg in messages_to_add:
        await session.add_message(msg)
    
    # Retrieve all
    messages = await session.get_messages()
    assert len(messages) == 4
    
    # Test limit
    limited = await session.get_messages(limit=2)
    assert len(limited) == 2
    assert limited[0].content == "Message 2"  # Most recent
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_sqlite_backend_basic():
    """Test basic SQLite backend operations"""
    backend = SQLiteBackend(db_path=":memory:")  # In-memory SQLite
    await backend.connect()
    
    assert backend.is_connected
    assert backend.backend_type.value == "sqlite"
    
    # Create session
    metadata = SessionMetadata(session_id="sqlite_test", user_id="user1")
    session = await backend.create_session(metadata)
    
    # Add messages
    await session.add_message(Message(role=MessageRole.USER, content="Test message"))
    
    # Retrieve
    messages = await session.get_messages()
    assert len(messages) == 1
    assert messages[0].content == "Test message"
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_sqlite_persistence():
    """Test that SQLite persists data across connections"""
    import tempfile
    import os
    
    # Create temp database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        # First connection: Create and populate
        backend1 = SQLiteBackend(db_path=db_path)
        await backend1.connect()
        
        metadata = SessionMetadata(session_id="persist_test", user_id="user1")
        session1 = await backend1.create_session(metadata)
        await session1.add_message(Message(role=MessageRole.USER, content="Persisted message"))
        
        await backend1.disconnect()
        
        # Second connection: Retrieve
        backend2 = SQLiteBackend(db_path=db_path)
        await backend2.connect()
        
        session2 = await backend2.get_session("persist_test")
        assert session2 is not None
        
        messages = await session2.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Persisted message"
        
        await backend2.disconnect()
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_session_metadata_updates():
    """Test updating session metadata"""
    backend = InMemoryBackend()
    await backend.connect()
    
    metadata = SessionMetadata(
        session_id="meta_test",
        user_id="user1",
        status=SessionStatus.ACTIVE
    )
    session = await backend.create_session(metadata)
    
    # Update metadata
    await session.update_metadata(status=SessionStatus.PAUSED)
    
    # Verify update
    updated_meta = session.metadata
    assert updated_meta.status == SessionStatus.PAUSED
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_list_sessions():
    """Test listing sessions with filters"""
    backend = InMemoryBackend()
    await backend.connect()
    
    # Create multiple sessions
    for i in range(3):
        metadata = SessionMetadata(session_id=f"session_{i}", user_id="user1")
        await backend.create_session(metadata)
    
    # List all sessions
    sessions = await backend.list_sessions()
    assert len(sessions) >= 3
    
    # List by user
    user_sessions = await backend.list_sessions(user_id="user1")
    assert len(user_sessions) >= 3
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_delete_session():
    """Test deleting a session"""
    backend = InMemoryBackend()
    await backend.connect()
    
    metadata = SessionMetadata(session_id="delete_test", user_id="user1")
    session = await backend.create_session(metadata)
    await session.add_message(Message(role=MessageRole.USER, content="Test"))
    
    # Delete session
    result = await backend.delete_session("delete_test")
    assert result is True
    
    # Verify deletion
    deleted_session = await backend.get_session("delete_test")
    assert deleted_session is None
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_message_filtering():
    """Test message filtering options"""
    backend = InMemoryBackend()
    await backend.connect()
    
    metadata = SessionMetadata(session_id="filter_test", user_id="user1")
    session = await backend.create_session(metadata)
    
    # Add messages with different roles
    await session.add_message(Message(role=MessageRole.SYSTEM, content="System message"))
    await session.add_message(Message(role=MessageRole.USER, content="User message"))
    await session.add_message(Message(role=MessageRole.ASSISTANT, content="Assistant message"))
    
    # Get all messages
    all_messages = await session.get_messages()
    assert len(all_messages) == 3
    
    # Exclude system messages
    non_system = await session.get_messages(include_system=False)
    assert len(non_system) == 2
    assert all(msg.role != MessageRole.SYSTEM for msg in non_system)
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_usage_stats():
    """Test backend usage statistics"""
    backend = InMemoryBackend()
    await backend.connect()
    
    # Create sessions and messages
    for i in range(2):
        metadata = SessionMetadata(session_id=f"stats_session_{i}", user_id="user1")
        session = await backend.create_session(metadata)
        await session.add_message(Message(role=MessageRole.USER, content=f"Message {i}"))
    
    # Get stats
    stats = await backend.get_usage_stats()
    assert stats.session_count >= 2
    assert stats.message_count >= 2
    
    await backend.disconnect()


@pytest.mark.asyncio
async def test_health_check():
    """Test backend health check"""
    backend = InMemoryBackend()
    await backend.connect()
    
    health = await backend.health_check()
    assert health["status"] == "healthy"
    assert health["connected"] is True
    assert "backend_type" in health
    
    await backend.disconnect()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])



