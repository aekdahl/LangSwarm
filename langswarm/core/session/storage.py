"""
Session Storage System
======================

Handles persistence and retrieval of sessions and conversation history
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import LangSwarmSession, ConversationHistory, SessionMetadata, SessionStatus


class SessionStorage(ABC):
    """Abstract base class for session storage backends"""
    
    @abstractmethod
    def save_session(self, session: LangSwarmSession) -> bool:
        """Save a session"""
        pass
    
    @abstractmethod
    def load_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """Load a session by ID"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass
    
    @abstractmethod
    def list_sessions(self, user_id: Optional[str] = None, 
                     status: Optional[SessionStatus] = None,
                     limit: int = 100) -> List[SessionMetadata]:
        """List sessions with optional filtering"""
        pass
    
    @abstractmethod
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata"""
        pass
    
    @abstractmethod
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions and return count deleted"""
        pass


class InMemorySessionStorage(SessionStorage):
    """In-memory session storage for testing and development"""
    
    def __init__(self):
        self._sessions: Dict[str, LangSwarmSession] = {}
    
    def save_session(self, session: LangSwarmSession) -> bool:
        """Save session to memory"""
        try:
            self._sessions[session.session_id] = session
            return True
        except Exception:
            return False
    
    def load_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """Load session from memory"""
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self, user_id: Optional[str] = None, 
                     status: Optional[SessionStatus] = None,
                     limit: int = 100) -> List[SessionMetadata]:
        """List sessions with filtering"""
        sessions = list(self._sessions.values())
        
        # Filter by user_id
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        # Filter by status
        if status:
            sessions = [s for s in sessions if s.metadata.status == status]
        
        # Sort by updated_at desc and limit
        sessions.sort(key=lambda s: s.metadata.updated_at, reverse=True)
        sessions = sessions[:limit]
        
        return [s.metadata for s in sessions]
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata"""
        session = self._sessions.get(session_id)
        if session:
            for key, value in metadata.items():
                if hasattr(session.metadata, key):
                    setattr(session.metadata, key, value)
            
            # Only update timestamp if not explicitly set
            if "updated_at" not in metadata:
                session.metadata.updated_at = datetime.now()
            return True
        return False
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        expired_sessions = [
            sid for sid, session in self._sessions.items()
            if session.metadata.updated_at < cutoff
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        return len(expired_sessions)


class SQLiteSessionStorage(SessionStorage):
    """SQLite-based session storage for production use"""
    
    def __init__(self, db_path: str = "langswarm_sessions.db"):
        """
        Initialize SQLite session storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    session_control TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_activity TEXT,
                    metadata TEXT NOT NULL,
                    history TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON sessions(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at ON sessions(updated_at)
            """)
    
    def save_session(self, session: LangSwarmSession) -> bool:
        """Save session to SQLite"""
        try:
            session_data = session.to_dict()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions (
                        session_id, user_id, provider, model, status, session_control,
                        created_at, updated_at, last_activity, metadata, history
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.user_id,
                    session.provider,
                    session.model,
                    session.metadata.status.value,
                    session.metadata.session_control.value,
                    session.metadata.created_at.isoformat(),
                    session.metadata.updated_at.isoformat(),
                    session.metadata.last_activity.isoformat() if session.metadata.last_activity else None,
                    json.dumps(session_data["metadata"]),
                    json.dumps(session_data["history"])
                ))
            return True
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """Load session from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT metadata, history FROM sessions WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    session_data = {
                        "metadata": json.loads(row["metadata"]),
                        "history": json.loads(row["history"])
                    }
                    return LangSwarmSession.from_dict(session_data)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE session_id = ?
                """, (session_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self, user_id: Optional[str] = None, 
                     status: Optional[SessionStatus] = None,
                     limit: int = 100) -> List[SessionMetadata]:
        """List sessions with filtering"""
        try:
            query = "SELECT metadata FROM sessions WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                
                sessions = []
                for row in cursor.fetchall():
                    metadata_dict = json.loads(row["metadata"])
                    sessions.append(SessionMetadata.from_dict(metadata_dict))
                
                return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata"""
        try:
            session = self.load_session(session_id)
            if session:
                for key, value in metadata.items():
                    if hasattr(session.metadata, key):
                        # Handle datetime conversion for testing
                        if key == "updated_at" and isinstance(value, datetime):
                            setattr(session.metadata, key, value)
                        else:
                            setattr(session.metadata, key, value)
                
                # Only update timestamp if not explicitly set
                if "updated_at" not in metadata:
                    session.metadata.updated_at = datetime.now()
                
                return self.save_session(session)
            return False
        except Exception as e:
            print(f"Error updating session metadata {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions"""
        try:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE updated_at < ?
                """, (cutoff.isoformat(),))
                return cursor.rowcount
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
            return 0


class SessionStorageFactory:
    """Factory for creating session storage instances"""
    
    @classmethod
    def create_storage(cls, storage_type: str = "sqlite", **kwargs) -> SessionStorage:
        """
        Create a session storage instance
        
        Args:
            storage_type: Type of storage ("memory", "sqlite")
            **kwargs: Storage-specific configuration
        """
        if storage_type == "memory":
            return InMemorySessionStorage()
        elif storage_type == "sqlite":
            db_path = kwargs.get("db_path", "langswarm_sessions.db")
            return SQLiteSessionStorage(db_path)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    @classmethod
    def get_default_storage(cls) -> SessionStorage:
        """Get default session storage (SQLite)"""
        return cls.create_storage("sqlite")


# Global session storage instance
_default_storage: Optional[SessionStorage] = None


def get_session_storage() -> SessionStorage:
    """Get the global session storage instance"""
    global _default_storage
    if _default_storage is None:
        _default_storage = SessionStorageFactory.get_default_storage()
    return _default_storage


def set_session_storage(storage: SessionStorage) -> None:
    """Set the global session storage instance"""
    global _default_storage
    _default_storage = storage 