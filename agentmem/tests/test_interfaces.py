"""
Test suite for AgentMem interfaces and data classes
"""

import pytest
from datetime import datetime, timezone, timedelta
from agentmem import (
    Message,
    MessageRole,
    SessionMetadata,
    SessionStatus,
    ConversationSummary,
    MemoryUsage,
)


def test_message_creation():
    """Test creating Message objects"""
    msg = Message(
        role=MessageRole.USER,
        content="Test message"
    )
    
    assert msg.role == MessageRole.USER
    assert msg.content == "Test message"
    assert isinstance(msg.timestamp, datetime)
    assert isinstance(msg.message_id, str)
    assert len(msg.message_id) > 0


def test_message_to_dict():
    """Test Message serialization to dict"""
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="Response",
        metadata={"key": "value"}
    )
    
    data = msg.to_dict()
    assert data["role"] == "assistant"
    assert data["content"] == "Response"
    assert "timestamp" in data
    assert "message_id" in data
    assert data["metadata"] == {"key": "value"}


def test_message_from_dict():
    """Test Message deserialization from dict"""
    data = {
        "role": "user",
        "content": "Hello",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_id": "test-id-123",
        "metadata": {"test": True}
    }
    
    msg = Message.from_dict(data)
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello"
    assert msg.message_id == "test-id-123"
    assert msg.metadata == {"test": True}


def test_message_openai_format():
    """Test conversion to OpenAI format"""
    msg = Message(
        role=MessageRole.USER,
        content="Hello AI"
    )
    
    openai_msg = msg.to_openai_format()
    assert openai_msg["role"] == "user"
    assert openai_msg["content"] == "Hello AI"
    assert "timestamp" not in openai_msg  # OpenAI doesn't use timestamp


def test_message_anthropic_format():
    """Test conversion to Anthropic format"""
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="Hello human"
    )
    
    anthropic_msg = msg.to_anthropic_format()
    assert anthropic_msg["role"] == "assistant"
    assert anthropic_msg["content"] == "Hello human"


def test_session_metadata_creation():
    """Test creating SessionMetadata objects"""
    metadata = SessionMetadata(
        session_id="test-session-123",
        user_id="user-456",
        agent_id="agent-789"
    )
    
    assert metadata.session_id == "test-session-123"
    assert metadata.user_id == "user-456"
    assert metadata.agent_id == "agent-789"
    assert metadata.status == SessionStatus.ACTIVE
    assert isinstance(metadata.created_at, datetime)


def test_session_metadata_expiration():
    """Test session expiration check"""
    # Not expired
    metadata1 = SessionMetadata(
        session_id="session1",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    assert not metadata1.is_expired()
    
    # Expired
    metadata2 = SessionMetadata(
        session_id="session2",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    assert metadata2.is_expired()
    
    # No expiration set
    metadata3 = SessionMetadata(session_id="session3")
    assert not metadata3.is_expired()


def test_session_metadata_timestamp_update():
    """Test updating session timestamp"""
    metadata = SessionMetadata(session_id="test")
    original_updated_at = metadata.updated_at
    
    # Wait a tiny bit
    import time
    time.sleep(0.01)
    
    metadata.update_timestamp()
    assert metadata.updated_at > original_updated_at


def test_conversation_summary_creation():
    """Test creating ConversationSummary objects"""
    summary = ConversationSummary(
        summary="This was a helpful conversation about Python",
        message_count=10,
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        key_topics=["python", "programming", "help"]
    )
    
    assert summary.summary.startswith("This was a helpful")
    assert summary.message_count == 10
    assert len(summary.key_topics) == 3
    assert isinstance(summary.summary_id, str)
    assert isinstance(summary.created_at, datetime)


def test_memory_usage_creation():
    """Test creating MemoryUsage objects"""
    usage = MemoryUsage(
        session_count=5,
        message_count=50,
        total_tokens=1000,
        storage_size_bytes=1024,
        active_sessions=3
    )
    
    assert usage.session_count == 5
    assert usage.message_count == 50
    assert usage.total_tokens == 1000
    assert usage.storage_size_bytes == 1024
    assert usage.active_sessions == 3


def test_message_roles():
    """Test all message roles"""
    roles = [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.SYSTEM,
        MessageRole.FUNCTION,
        MessageRole.TOOL
    ]
    
    for role in roles:
        msg = Message(role=role, content="Test")
        assert msg.role == role


def test_session_statuses():
    """Test all session statuses"""
    statuses = [
        SessionStatus.ACTIVE,
        SessionStatus.PAUSED,
        SessionStatus.COMPLETED,
        SessionStatus.ARCHIVED,
        SessionStatus.EXPIRED
    ]
    
    for status in statuses:
        metadata = SessionMetadata(session_id="test", status=status)
        assert metadata.status == status


def test_message_with_function_call():
    """Test message with function call metadata"""
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        function_call={"name": "get_weather", "arguments": '{"location": "Paris"}'}
    )
    
    assert msg.function_call is not None
    assert msg.function_call["name"] == "get_weather"
    
    # Check OpenAI format includes function_call
    openai_msg = msg.to_openai_format()
    assert "function_call" in openai_msg


def test_message_with_tool_calls():
    """Test message with tool calls metadata"""
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        tool_calls=[
            {"id": "call_1", "function": {"name": "search", "arguments": '{"query": "AI"}'}}
        ]
    )
    
    assert msg.tool_calls is not None
    assert len(msg.tool_calls) == 1
    
    # Check OpenAI format includes tool_calls
    openai_msg = msg.to_openai_format()
    assert "tool_calls" in openai_msg


def test_session_metadata_with_tags():
    """Test session metadata with tags and properties"""
    metadata = SessionMetadata(
        session_id="test",
        tags=["support", "billing", "urgent"],
        properties={"department": "sales", "priority": "high"}
    )
    
    assert len(metadata.tags) == 3
    assert "support" in metadata.tags
    assert metadata.properties["department"] == "sales"
    assert metadata.properties["priority"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



