"""
MemoryPro Webhook Handler
=========================

Handles webhook events from MemoryPro external service including:
- Memory insights notifications
- Lifecycle recommendations
- Evolution updates
- Action discoveries
"""

import json
import hmac
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class WebhookEventType(Enum):
    """Types of webhook events from MemoryPro"""
    MEMORY_INSIGHTS = "memory_insights"
    LIFECYCLE_RECOMMENDATIONS = "lifecycle_recommendations"
    EVOLUTION_UPDATES = "evolution_updates"
    ACTION_DISCOVERIES = "action_discoveries"


@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    event_type: WebhookEventType
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'WebhookEvent':
        """Create WebhookEvent from webhook payload"""
        return cls(
            event_type=WebhookEventType(payload.get("event_type")),
            user_id=payload.get("user_id"),
            timestamp=datetime.fromisoformat(payload.get("timestamp").replace("Z", "+00:00")),
            data=payload.get("data", {})
        )


class MemoryProWebhookHandler:
    """
    Handles MemoryPro webhook events and routes them to appropriate handlers
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            webhook_secret: Secret for webhook signature verification
        """
        self.webhook_secret = webhook_secret
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {
            event_type: [] for event_type in WebhookEventType
        }
        
        # Default action queue for discovered actions
        self.action_queue: List[Dict[str, Any]] = []
        
        # Setup default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default event handlers"""
        self.register_handler(WebhookEventType.ACTION_DISCOVERIES, self._handle_action_discoveries)
        self.register_handler(WebhookEventType.MEMORY_INSIGHTS, self._handle_memory_insights)
        self.register_handler(WebhookEventType.LIFECYCLE_RECOMMENDATIONS, self._handle_lifecycle_recommendations)
        self.register_handler(WebhookEventType.EVOLUTION_UPDATES, self._handle_evolution_updates)
    
    def register_handler(self, event_type: WebhookEventType, handler: Callable):
        """
        Register an event handler for a specific webhook event type
        
        Args:
            event_type: Type of webhook event
            handler: Function to handle the event (async or sync)
        """
        self.event_handlers[event_type].append(handler)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature using HMAC-SHA256
        
        Args:
            payload: Raw request body
            signature: Signature from X-MemoryPro-Signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle incoming webhook
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            Response dictionary
        """
        # Verify signature
        if not self.verify_signature(payload, signature):
            return {"error": "Invalid signature", "status": 401}
        
        # Parse payload
        try:
            data = json.loads(payload.decode())
            event = WebhookEvent.from_payload(data)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            return {"error": f"Invalid payload: {e}", "status": 400}
        
        # Route to handlers
        try:
            await self._route_event(event)
            return {"status": "success", "event_type": event.event_type.value}
        except Exception as e:
            return {"error": f"Handler error: {e}", "status": 500}
    
    async def _route_event(self, event: WebhookEvent):
        """Route event to registered handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Handler error for {event.event_type}: {e}")
    
    # Default event handlers
    async def _handle_memory_insights(self, event: WebhookEvent):
        """Handle memory insights webhook event"""
        insights = event.data.get("insights", {})
        
        print(f"📊 Memory insights for user {event.user_id}:")
        print(f"   Health Score: {insights.get('memory_health_score', 'N/A')}")
        print(f"   Total Memories: {insights.get('total_memories', 'N/A')}")
        print(f"   High Priority: {insights.get('high_priority_count', 'N/A')}")
        
        # Process new patterns
        for pattern in insights.get("new_patterns", []):
            print(f"   New Pattern: {pattern.get('description', 'Unknown')}")
        
        # Store insights for later retrieval
        self._store_user_insights(event.user_id, insights)
    
    async def _handle_lifecycle_recommendations(self, event: WebhookEvent):
        """Handle lifecycle recommendations webhook event"""
        recommendations = event.data.get("recommendations", [])
        
        print(f"🔄 Lifecycle recommendations for user {event.user_id}:")
        
        for rec in recommendations:
            action = rec.get("action")
            memory_ids = rec.get("memory_ids", [])
            reason = rec.get("reason", "No reason provided")
            
            print(f"   Action: {action} ({len(memory_ids)} memories) - {reason}")
            
            # Queue lifecycle action
            self._queue_lifecycle_action(event.user_id, rec)
    
    async def _handle_evolution_updates(self, event: WebhookEvent):
        """Handle evolution updates webhook event"""
        updates = event.data.get("updates", [])
        
        print(f"🧬 Evolution updates for user {event.user_id}:")
        
        for update in updates:
            insight = update.get("insight")
            confidence = update.get("confidence", 0.0)
            recommendation = update.get("recommendation")
            
            print(f"   Insight: {insight} (confidence: {confidence:.2f})")
            print(f"   Recommendation: {recommendation}")
            
            # Update user preferences
            self._update_user_preferences(event.user_id, update)
    
    async def _handle_action_discoveries(self, event: WebhookEvent):
        """Handle action discoveries webhook event"""
        actions = event.data.get("actions", [])
        
        print(f"🎯 Action discoveries for user {event.user_id}:")
        
        for action in actions:
            action_type = action.get("type", "unknown")
            title = action.get("title", "Untitled")
            priority = action.get("priority", "medium")
            
            print(f"   {action_type.upper()}: {title} (priority: {priority})")
            
            # Queue discovered action
            self._queue_discovered_action(event.user_id, action)
    
    def _store_user_insights(self, user_id: str, insights: Dict[str, Any]):
        """Store user insights for later retrieval"""
        # In a real implementation, this would store to a database
        print(f"Stored insights for user {user_id}")
    
    def _queue_lifecycle_action(self, user_id: str, recommendation: Dict[str, Any]):
        """Queue a lifecycle action for processing"""
        action = {
            "type": "lifecycle",
            "user_id": user_id,
            "recommendation": recommendation,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        self.action_queue.append(action)
        print(f"Queued lifecycle action for user {user_id}")
    
    def _update_user_preferences(self, user_id: str, update: Dict[str, Any]):
        """Update user preferences based on evolution insights"""
        # In a real implementation, this would update user profile
        print(f"Updated preferences for user {user_id}: {update.get('insight')}")
    
    def _queue_discovered_action(self, user_id: str, action: Dict[str, Any]):
        """Queue a discovered action for processing"""
        queued_action = {
            "type": "discovered",
            "user_id": user_id,
            "action": action,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        self.action_queue.append(queued_action)
        print(f"Queued discovered action for user {user_id}: {action.get('title')}")
    
    def get_pending_actions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pending actions from the queue
        
        Args:
            user_id: Filter by user ID (optional)
            
        Returns:
            List of pending actions
        """
        if user_id:
            return [action for action in self.action_queue 
                   if action.get("user_id") == user_id and action.get("status") == "pending"]
        else:
            return [action for action in self.action_queue if action.get("status") == "pending"]
    
    def mark_action_completed(self, action_index: int):
        """Mark an action as completed"""
        if 0 <= action_index < len(self.action_queue):
            self.action_queue[action_index]["status"] = "completed"
            self.action_queue[action_index]["completed_at"] = datetime.utcnow().isoformat()
    
    def clear_completed_actions(self):
        """Remove completed actions from the queue"""
        self.action_queue = [action for action in self.action_queue 
                           if action.get("status") != "completed"]


# Global webhook handler instance
_webhook_handler = None


def get_memorypro_webhook_handler(webhook_secret: Optional[str] = None) -> MemoryProWebhookHandler:
    """
    Get or create the global MemoryPro webhook handler
    
    Args:
        webhook_secret: Webhook secret for signature verification
        
    Returns:
        MemoryProWebhookHandler instance
    """
    global _webhook_handler
    
    if _webhook_handler is None:
        _webhook_handler = MemoryProWebhookHandler(webhook_secret)
    
    return _webhook_handler


def create_webhook_handler(webhook_secret: Optional[str] = None) -> MemoryProWebhookHandler:
    """
    Create a new MemoryPro webhook handler
    
    Args:
        webhook_secret: Webhook secret for signature verification
        
    Returns:
        MemoryProWebhookHandler instance
    """
    return MemoryProWebhookHandler(webhook_secret) 