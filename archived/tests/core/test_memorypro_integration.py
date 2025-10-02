"""
Comprehensive tests for MemoryPro integration
============================================

Tests all MemoryPro features including:
- MemoryPro adapter (internal and external modes)
- API routes and endpoints
- Webhook handling
- Action discovery and queuing
"""

import json
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Test the memory adapter
def test_memorypro_adapter_internal_mode():
    """Test MemoryPro adapter in internal mode"""
    from langswarm.memory.adapters.memorypro import MemoryProAdapter
    
    adapter = MemoryProAdapter(mode="internal")
    
    # Test document addition
    documents = [{
        "text": "We need to schedule a meeting with the team next week",
        "metadata": {"user_id": "test_user", "session_id": "test_session"},
        "key": "test_doc_1"
    }]
    
    result = adapter.add_documents(documents)
    
    assert result["mode"] == "internal"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    assert result["results"][0]["analysis"].priority_score > 0


def test_memorypro_adapter_external_mode():
    """Test MemoryPro adapter in external mode with mocked API"""
    from langswarm.memory.adapters.memorypro import MemoryProAdapter
    
    with patch('requests.Session') as mock_session:
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "success",
            "memory_id": "mem_123",
            "analysis": {
                "priority_score": 0.8,
                "relevance_score": 0.9,
                "themes": ["project management"],
                "extracted_actions": [{"type": "task", "title": "Schedule meeting"}]
            }
        }
        mock_session.return_value.post.return_value = mock_response
        
        adapter = MemoryProAdapter(
            mode="external",
            api_url="https://api.memorypro.com",
            api_key="test_key",
            api_secret="test_secret"
        )
        
        documents = [{
            "text": "We need to schedule a meeting with the team next week",
            "metadata": {"user_id": "test_user", "session_id": "test_session"},
            "key": "test_doc_1"
        }]
        
        result = adapter.add_documents(documents)
        
        assert result["mode"] == "external"
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "success"
        assert result["results"][0]["memory_id"] == "mem_123"


def test_memorypro_adapter_query():
    """Test memory query functionality"""
    from langswarm.memory.adapters.memorypro import MemoryProAdapter
    
    adapter = MemoryProAdapter(mode="internal")
    
    # Add some test documents first
    documents = [
        {
            "text": "Project deadline is next Friday",
            "metadata": {"user_id": "test_user"},
            "key": "doc_1"
        },
        {
            "text": "Team meeting scheduled for Monday",
            "metadata": {"user_id": "test_user"},
            "key": "doc_2"
        }
    ]
    adapter.add_documents(documents)
    
    # Query for memories
    result = adapter.query("deadline", user_id="test_user")
    
    assert result["status"] == "success"
    assert "memories" in result
    assert "analysis" in result


def test_memorypro_adapter_insights():
    """Test memory insights functionality"""
    from langswarm.memory.adapters.memorypro import MemoryProAdapter
    
    adapter = MemoryProAdapter(mode="internal")
    insights = adapter.get_insights("test_user")
    
    assert insights.memory_health_score > 0
    assert insights.total_memories >= 0
    assert isinstance(insights.patterns, list)


def test_memorypro_configuration():
    """Test MemoryPro configuration integration"""
    from langswarm.core.config import MemoryConfig
    
    # Test internal mode configuration
    config = MemoryConfig(
        memorypro_enabled=True,
        memorypro_mode="internal"
    )
    
    assert not config.is_external_memorypro()
    
    # Test external mode configuration
    config = MemoryConfig(
        memorypro_enabled=True,
        memorypro_mode="external",
        memorypro_api_url="https://api.memorypro.com",
        memorypro_api_key="test_key",
        memorypro_api_secret="test_secret"
    )
    
    assert config.is_external_memorypro()
    
    memorypro_config = config.get_memorypro_config()
    assert memorypro_config["enabled"] == True
    assert memorypro_config["mode"] == "external"
    assert memorypro_config["api_url"] == "https://api.memorypro.com"


# Test webhook functionality
def test_webhook_signature_verification():
    """Test webhook signature verification"""
    from langswarm.core.webhooks.memorypro_webhooks import MemoryProWebhookHandler
    
    handler = MemoryProWebhookHandler(webhook_secret="test_secret")
    
    # Test valid signature
    payload = b'{"test": "data"}'
    import hmac
    import hashlib
    expected_signature = hmac.new(
        b"test_secret",
        payload,
        hashlib.sha256
    ).hexdigest()
    
    assert handler.verify_signature(payload, f"sha256={expected_signature}")
    assert handler.verify_signature(payload, expected_signature)
    
    # Test invalid signature
    assert not handler.verify_signature(payload, "invalid_signature")


@pytest.mark.asyncio
async def test_webhook_event_handling():
    """Test webhook event handling"""
    from langswarm.core.webhooks.memorypro_webhooks import MemoryProWebhookHandler, WebhookEvent, WebhookEventType
    
    handler = MemoryProWebhookHandler()
    
    # Test action discovery event
    event = WebhookEvent(
        event_type=WebhookEventType.ACTION_DISCOVERIES,
        user_id="test_user",
        timestamp=datetime.utcnow(),
        data={
            "actions": [
                {
                    "type": "task",
                    "title": "Review project proposal",
                    "priority": "high"
                }
            ]
        }
    )
    
    # Process event
    await handler._handle_action_discoveries(event)
    
    # Check that action was queued
    pending_actions = handler.get_pending_actions("test_user")
    assert len(pending_actions) == 1


# Test action discovery
def test_action_discovery_basic():
    """Test basic action discovery functionality"""
    from langswarm.core.actions.action_discovery import ActionDiscoveryEngine
    
    engine = ActionDiscoveryEngine()
    
    # Test task discovery
    content = "We need to schedule a meeting with the team next week and review the project proposal."
    actions = engine.discover_actions(content, user_id="test_user")
    
    assert len(actions) > 0
    
    # Check for task action
    task_actions = [a for a in actions if a.type == "task"]
    assert len(task_actions) > 0
    
    # Check action properties
    action = task_actions[0]
    assert action.user_id == "test_user"
    assert action.title is not None
    assert len(action.title) > 0


def test_action_discovery_priority():
    """Test action priority detection"""
    from langswarm.core.actions.action_discovery import ActionDiscoveryEngine
    from langswarm.core.actions.action_queue import ActionPriority
    
    engine = ActionDiscoveryEngine()
    
    # Test urgent priority
    content = "We need to fix this critical bug immediately!"
    actions = engine.discover_actions(content)
    
    if actions:
        # Should detect high/urgent priority
        assert any(a.priority in [ActionPriority.HIGH, ActionPriority.URGENT] for a in actions)
    
    # Test low priority
    content = "We should eventually look into optimizing the database."
    actions = engine.discover_actions(content)
    
    if actions:
        # Should detect low priority
        assert any(a.priority == ActionPriority.LOW for a in actions)


def test_action_discovery_time_extraction():
    """Test due date extraction from content"""
    from langswarm.core.actions.action_discovery import ActionDiscoveryEngine
    
    engine = ActionDiscoveryEngine()
    
    content = "We need to finish this project by tomorrow."
    actions = engine.discover_actions(content)
    
    if actions:
        action = actions[0]
        assert action.due_date is not None
        # Should be approximately tomorrow
        expected_date = datetime.utcnow() + timedelta(days=1)
        time_diff = abs((action.due_date - expected_date).total_seconds())
        assert time_diff < 3600  # Within 1 hour


def test_action_discovery_deduplication():
    """Test action deduplication"""
    from langswarm.core.actions.action_discovery import ActionDiscoveryEngine
    
    engine = ActionDiscoveryEngine()
    
    # Content with similar actions
    content = "We need to schedule a meeting. We should schedule a meeting with the team."
    actions = engine.discover_actions(content)
    
    # Should deduplicate similar actions
    meeting_actions = [a for a in actions if "meeting" in a.title.lower()]
    assert len(meeting_actions) <= 1  # Should be deduplicated


# Test action queue
def test_action_queue_basic():
    """Test basic action queue functionality"""
    from langswarm.core.actions.action_queue import ActionQueue, ActionItem, ActionStatus, ActionPriority
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        queue = ActionQueue(db_path=temp_db.name)
        
        # Create test action
        action = ActionItem(
            id="test_action_1",
            type="task",
            title="Test Action",
            description="This is a test action",
            priority=ActionPriority.HIGH,
            user_id="test_user"
        )
        
        # Add action to queue
        assert queue.add_action(action) == True
        
        # Retrieve pending actions
        pending_actions = queue.get_pending_actions("test_user")
        assert len(pending_actions) == 1
        assert pending_actions[0].title == "Test Action"
        
        # Update action status
        assert queue.update_action_status("test_action_1", ActionStatus.COMPLETED) == True
        
        # Check updated status
        completed_actions = queue.get_actions(status=ActionStatus.COMPLETED, user_id="test_user")
        assert len(completed_actions) == 1
        assert completed_actions[0].status == ActionStatus.COMPLETED


def test_action_queue_filtering():
    """Test action queue filtering"""
    from langswarm.core.actions.action_queue import ActionQueue, ActionItem, ActionStatus, ActionPriority
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        queue = ActionQueue(db_path=temp_db.name)
        
        # Add multiple actions
        actions = [
            ActionItem(
                id="action_1",
                type="task",
                title="High Priority Task",
                priority=ActionPriority.HIGH,
                user_id="user1"
            ),
            ActionItem(
                id="action_2",
                type="reminder",
                title="Low Priority Reminder",
                priority=ActionPriority.LOW,
                user_id="user1"
            ),
            ActionItem(
                id="action_3",
                type="task",
                title="User2 Task",
                priority=ActionPriority.MEDIUM,
                user_id="user2"
            )
        ]
        
        for action in actions:
            queue.add_action(action)
        
        # Test filtering by priority
        high_priority_actions = queue.get_actions(priority=ActionPriority.HIGH)
        assert len(high_priority_actions) == 1
        assert high_priority_actions[0].title == "High Priority Task"
        
        # Test filtering by user
        user1_actions = queue.get_actions(user_id="user1")
        assert len(user1_actions) == 2
        
        user2_actions = queue.get_actions(user_id="user2")
        assert len(user2_actions) == 1


def test_action_queue_overdue():
    """Test overdue action detection"""
    from langswarm.core.actions.action_queue import ActionQueue, ActionItem, ActionPriority
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        queue = ActionQueue(db_path=temp_db.name)
        
        # Create overdue action
        overdue_action = ActionItem(
            id="overdue_action",
            type="task",
            title="Overdue Task",
            priority=ActionPriority.HIGH,
            user_id="test_user",
            due_date=datetime.utcnow() - timedelta(days=1)  # Yesterday
        )
        
        # Create future action
        future_action = ActionItem(
            id="future_action",
            type="task",
            title="Future Task",
            priority=ActionPriority.MEDIUM,
            user_id="test_user",
            due_date=datetime.utcnow() + timedelta(days=1)  # Tomorrow
        )
        
        queue.add_action(overdue_action)
        queue.add_action(future_action)
        
        # Get overdue actions
        overdue_actions = queue.get_overdue_actions("test_user")
        assert len(overdue_actions) == 1
        assert overdue_actions[0].title == "Overdue Task"


# Integration test
@pytest.mark.asyncio
async def test_memorypro_full_integration():
    """Test full MemoryPro integration workflow"""
    from langswarm.memory.adapters.memorypro import MemoryProAdapter
    from langswarm.core.actions.action_discovery import discover_actions_from_content
    from langswarm.core.actions.action_queue import get_action_queue
    from langswarm.core.webhooks.memorypro_webhooks import MemoryProWebhookHandler
    
    # 1. Store memory with action-rich content
    adapter = MemoryProAdapter(mode="internal")
    
    content = "We need to schedule a meeting with the client by Friday to discuss the project requirements. Also, we should review the technical specifications urgently."
    
    documents = [{
        "text": content,
        "metadata": {"user_id": "integration_test_user", "session_id": "test_session"},
        "key": "integration_test_doc"
    }]
    
    memory_result = adapter.add_documents(documents)
    assert memory_result["mode"] == "internal"
    assert memory_result["results"][0]["status"] == "success"
    
    # 2. Discover actions from the content
    actions = discover_actions_from_content(
        content,
        user_id="integration_test_user",
        memory_id="integration_test_doc"
    )
    
    assert len(actions) > 0
    
    # 3. Add actions to queue
    action_queue = get_action_queue()
    for action in actions:
        assert action_queue.add_action(action) == True
    
    # 4. Verify actions in queue
    pending_actions = action_queue.get_pending_actions("integration_test_user")
    assert len(pending_actions) >= len(actions)
    
    # 5. Test webhook integration
    webhook_handler = MemoryProWebhookHandler()
    
    # Simulate webhook payload for action discoveries
    webhook_payload = {
        "event_type": "action_discoveries",
        "user_id": "integration_test_user",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "actions": [
                {
                    "type": "meeting",
                    "title": "Client meeting",
                    "priority": "high"
                }
            ]
        }
    }
    
    payload_bytes = json.dumps(webhook_payload).encode()
    result = await webhook_handler.handle_webhook(payload_bytes, "")  # No signature for test
    
    assert result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 