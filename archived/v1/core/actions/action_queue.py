"""
Action Queue System
===================

Manages discovered actions from MemoryPro and other sources with priority 
queuing, persistence, and integration with Google Cloud Pub/Sub
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class ActionStatus(Enum):
    """Action status types"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionPriority(Enum):
    """Action priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ActionItem:
    """Individual action item"""
    id: str
    type: str  # task, reminder, follow_up, lifecycle, etc.
    title: str
    description: Optional[str] = None
    priority: ActionPriority = ActionPriority.MEDIUM
    status: ActionStatus = ActionStatus.PENDING
    user_id: Optional[str] = None
    memory_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    due_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        # Convert datetime to ISO string
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        data["due_date"] = self.due_date.isoformat() if self.due_date else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        """Create ActionItem from dictionary"""
        # Convert string enums back to enum objects
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = ActionPriority(data["priority"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ActionStatus(data["status"])
        
        # Convert ISO strings back to datetime
        for field in ["created_at", "updated_at", "due_date"]:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)


class ActionQueue:
    """
    Action queue with SQLite persistence and optional Google Cloud Pub/Sub integration
    """
    
    def __init__(
        self,
        db_path: str = "actions.db",
        pubsub_enabled: bool = False,
        pubsub_project: Optional[str] = None,
        pubsub_topic: Optional[str] = None
    ):
        """
        Initialize action queue
        
        Args:
            db_path: Path to SQLite database file
            pubsub_enabled: Enable Google Cloud Pub/Sub integration
            pubsub_project: GCP project ID
            pubsub_topic: Pub/Sub topic name
        """
        self.db_path = db_path
        self.pubsub_enabled = pubsub_enabled
        self.pubsub_project = pubsub_project
        self.pubsub_topic = pubsub_topic
        
        # Initialize database
        self._init_database()
        
        # Initialize Pub/Sub if enabled
        if self.pubsub_enabled and self.pubsub_project and self.pubsub_topic:
            self._init_pubsub()
    
    def _init_database(self):
        """Initialize SQLite database for action persistence"""
        # Create database directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    user_id TEXT,
                    memory_id TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    due_date TEXT
                )
            """)
            
            # Create indices for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON actions(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON actions(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON actions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_due_date ON actions(due_date)")
            
            conn.commit()
    
    def _init_pubsub(self):
        """Initialize Google Cloud Pub/Sub client"""
        try:
            from google.cloud import pubsub_v1
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.pubsub_project, self.pubsub_topic)
            print(f"✅ Pub/Sub initialized: {self.topic_path}")
        except ImportError:
            print("⚠️ Google Cloud Pub/Sub not available. Install with: pip install google-cloud-pubsub")
            self.pubsub_enabled = False
        except Exception as e:
            print(f"⚠️ Failed to initialize Pub/Sub: {e}")
            self.pubsub_enabled = False
    
    def add_action(self, action: ActionItem) -> bool:
        """
        Add action to queue
        
        Args:
            action: ActionItem to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = action.to_dict()
                conn.execute("""
                    INSERT INTO actions (
                        id, type, title, description, priority, status,
                        user_id, memory_id, metadata, created_at, updated_at, due_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["id"], data["type"], data["title"], data["description"],
                    data["priority"], data["status"], data["user_id"], data["memory_id"],
                    json.dumps(data["metadata"]), data["created_at"], data["updated_at"],
                    data["due_date"]
                ))
                conn.commit()
            
            # Publish to Pub/Sub if enabled
            if self.pubsub_enabled:
                self._publish_action_event("action_added", action)
            
            return True
            
        except Exception as e:
            print(f"Failed to add action: {e}")
            return False
    
    def get_actions(
        self,
        status: Optional[ActionStatus] = None,
        priority: Optional[ActionPriority] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ActionItem]:
        """
        Get actions from queue with filtering
        
        Args:
            status: Filter by status
            priority: Filter by priority
            user_id: Filter by user ID
            limit: Maximum number of actions to return
            
        Returns:
            List of ActionItem objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM actions WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status.value)
                
                if priority:
                    query += " AND priority = ?"
                    params.append(priority.value)
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                actions = []
                for row in rows:
                    data = dict(row)
                    # Parse JSON metadata
                    if data["metadata"]:
                        data["metadata"] = json.loads(data["metadata"])
                    else:
                        data["metadata"] = {}
                    
                    actions.append(ActionItem.from_dict(data))
                
                return actions
                
        except Exception as e:
            print(f"Failed to get actions: {e}")
            return []
    
    def update_action_status(self, action_id: str, status: ActionStatus) -> bool:
        """
        Update action status
        
        Args:
            action_id: Action ID to update
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE actions 
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (status.value, datetime.utcnow().isoformat(), action_id))
                
                if conn.total_changes > 0:
                    conn.commit()
                    
                    # Publish status update to Pub/Sub if enabled
                    if self.pubsub_enabled:
                        self._publish_status_update(action_id, status)
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Failed to update action status: {e}")
            return False
    
    def delete_action(self, action_id: str) -> bool:
        """
        Delete action from queue
        
        Args:
            action_id: Action ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM actions WHERE id = ?", (action_id,))
                
                if conn.total_changes > 0:
                    conn.commit()
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Failed to delete action: {e}")
            return False
    
    def get_pending_actions(self, user_id: Optional[str] = None) -> List[ActionItem]:
        """Get all pending actions"""
        return self.get_actions(status=ActionStatus.PENDING, user_id=user_id)
    
    def get_overdue_actions(self, user_id: Optional[str] = None) -> List[ActionItem]:
        """Get overdue actions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT * FROM actions 
                    WHERE status = 'pending' 
                    AND due_date IS NOT NULL 
                    AND due_date < ?
                """
                params = [datetime.utcnow().isoformat()]
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                query += " ORDER BY due_date ASC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                actions = []
                for row in rows:
                    data = dict(row)
                    if data["metadata"]:
                        data["metadata"] = json.loads(data["metadata"])
                    else:
                        data["metadata"] = {}
                    
                    actions.append(ActionItem.from_dict(data))
                
                return actions
                
        except Exception as e:
            print(f"Failed to get overdue actions: {e}")
            return []
    
    def _publish_action_event(self, event_type: str, action: ActionItem):
        """Publish action event to Pub/Sub"""
        if not self.pubsub_enabled:
            return
        
        try:
            message_data = {
                "event_type": event_type,
                "action": action.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = json.dumps(message_data).encode()
            future = self.publisher.publish(self.topic_path, message)
            print(f"Published action event: {future.result()}")
            
        except Exception as e:
            print(f"Failed to publish action event: {e}")
    
    def _publish_status_update(self, action_id: str, status: ActionStatus):
        """Publish action status update to Pub/Sub"""
        if not self.pubsub_enabled:
            return
        
        try:
            message_data = {
                "event_type": "action_status_update",
                "action_id": action_id,
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = json.dumps(message_data).encode()
            future = self.publisher.publish(self.topic_path, message)
            print(f"Published status update: {future.result()}")
            
        except Exception as e:
            print(f"Failed to publish status update: {e}")
    
    def clear_completed_actions(self, days_old: int = 7) -> int:
        """
        Clear completed actions older than specified days
        
        Args:
            days_old: Number of days old to consider for deletion
            
        Returns:
            Number of actions deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM actions 
                    WHERE status = 'completed' 
                    AND updated_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            print(f"Failed to clear completed actions: {e}")
            return 0


# Global action queue instance
_action_queue = None


def get_action_queue() -> ActionQueue:
    """
    Get or create the global action queue
    
    Returns:
        ActionQueue instance
    """
    global _action_queue
    
    if _action_queue is None:
        # Configure from environment variables
        pubsub_enabled = os.getenv("LANGSWARM_PUBSUB_ENABLED", "false").lower() == "true"
        pubsub_project = os.getenv("LANGSWARM_PUBSUB_PROJECT")
        pubsub_topic = os.getenv("LANGSWARM_PUBSUB_TOPIC", "langswarm-actions")
        
        _action_queue = ActionQueue(
            db_path=os.getenv("LANGSWARM_ACTIONS_DB", "actions.db"),
            pubsub_enabled=pubsub_enabled,
            pubsub_project=pubsub_project,
            pubsub_topic=pubsub_topic
        )
    
    return _action_queue 