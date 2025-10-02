"""
LangSwarm V2 Session Storage Backends

Simple, efficient storage backends for session persistence with focus on
performance and reliability.
"""

import json
import sqlite3
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor

from .interfaces import (
    ISessionStorage, SessionMessage, SessionContext, SessionMetrics,
    SessionStatus, MessageRole, SessionStorageError
)
from langswarm.core.errors import handle_error


logger = logging.getLogger(__name__)


class InMemorySessionStorage(ISessionStorage):
    """
    In-memory session storage for development and testing.
    
    Fast, simple storage that doesn't persist between restarts.
    """
    
    def __init__(self):
        """Initialize in-memory storage"""
        self._sessions: Dict[str, tuple[List[SessionMessage], SessionContext]] = {}
        self._metrics: Dict[str, SessionMetrics] = {}
        self._lock = asyncio.Lock()
        
        logger.debug("Initialized in-memory session storage")
    
    async def save_session(
        self,
        session_id: str,
        messages: List[SessionMessage],
        context: SessionContext
    ) -> bool:
        """Save session to memory"""
        try:
            async with self._lock:
                self._sessions[session_id] = (messages.copy(), context)
                
                # Update metrics
                if session_id not in self._metrics:
                    self._metrics[session_id] = SessionMetrics()
                
                metrics = self._metrics[session_id]
                metrics.message_count = len(messages)
                metrics.last_activity = datetime.utcnow()
                
                # Calculate token count if available
                total_tokens = sum(msg.token_count or 0 for msg in messages)
                if total_tokens > 0:
                    metrics.total_tokens = total_tokens
            
            logger.debug(f"Saved session {session_id} to memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            handle_error(e, "memory_storage_save")
            return False
    
    async def load_session(
        self,
        session_id: str
    ) -> Optional[tuple[List[SessionMessage], SessionContext]]:
        """Load session from memory"""
        try:
            async with self._lock:
                return self._sessions.get(session_id)
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            handle_error(e, "memory_storage_load")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from memory"""
        try:
            async with self._lock:
                self._sessions.pop(session_id, None)
                self._metrics.pop(session_id, None)
            
            logger.debug(f"Deleted session {session_id} from memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            handle_error(e, "memory_storage_delete")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[SessionContext]:
        """List sessions from memory"""
        try:
            async with self._lock:
                contexts = []
                for session_id, (messages, context) in self._sessions.items():
                    # Filter by user ID
                    if user_id and context.user_id != user_id:
                        continue
                    
                    # Filter by status (assume ACTIVE for in-memory)
                    if status and status != SessionStatus.ACTIVE:
                        continue
                    
                    contexts.append(context)
                    
                    if len(contexts) >= limit:
                        break
                
                return contexts
                
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            handle_error(e, "memory_storage_list")
            return []
    
    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get session metrics from memory"""
        try:
            async with self._lock:
                return self._metrics.get(session_id)
                
        except Exception as e:
            logger.error(f"Failed to get metrics for session {session_id}: {e}")
            handle_error(e, "memory_storage_metrics")
            return None


class SQLiteSessionStorage(ISessionStorage):
    """
    SQLite session storage for persistent local storage.
    
    Efficient, reliable storage with support for concurrent access.
    """
    
    def __init__(self, db_path: str = "langswarm_sessions.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread pool for database operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="session_db")
        
        # Initialize database
        asyncio.create_task(self._init_database())
        
        logger.info(f"Initialized SQLite session storage: {db_path}")
    
    async def _init_database(self):
        """Initialize database schema"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._create_tables
            )
            logger.debug("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            handle_error(e, "sqlite_storage_init")
    
    def _create_tables(self):
        """Create database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT,
                    provider_message_id TEXT,
                    token_count INTEGER,
                    finish_reason TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    session_duration REAL DEFAULT 0.0,
                    last_activity TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON session_messages (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON session_messages (timestamp)")
            
            conn.commit()
    
    async def save_session(
        self,
        session_id: str,
        messages: List[SessionMessage],
        context: SessionContext
    ) -> bool:
        """Save session to SQLite"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._save_session_sync, session_id, messages, context
            )
            
            logger.debug(f"Saved session {session_id} to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            handle_error(e, "sqlite_storage_save")
            return False
    
    def _save_session_sync(
        self,
        session_id: str,
        messages: List[SessionMessage],
        context: SessionContext
    ):
        """Synchronous session save"""
        with sqlite3.connect(self.db_path) as conn:
            # Save session context
            context_data = json.dumps({
                'session_id': context.session_id,
                'user_id': context.user_id,
                'provider': context.provider,
                'model': context.model,
                'backend': context.backend.value,
                'max_messages': context.max_messages,
                'auto_archive': context.auto_archive,
                'persist_messages': context.persist_messages,
                'provider_session_id': context.provider_session_id,
                'provider_context': context.provider_context
            })
            
            conn.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, provider, model, backend, context_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, context.user_id, context.provider, context.model,
                context.backend.value, context_data, datetime.utcnow()
            ))
            
            # Clear existing messages
            conn.execute("DELETE FROM session_messages WHERE session_id = ?", (session_id,))
            
            # Save messages
            for msg in messages:
                conn.execute("""
                    INSERT INTO session_messages 
                    (session_id, message_id, role, content, timestamp, metadata, 
                     provider_message_id, token_count, finish_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, msg.id, msg.role.value, msg.content, msg.timestamp,
                    json.dumps(msg.metadata), msg.provider_message_id,
                    msg.token_count, msg.finish_reason
                ))
            
            # Update metrics
            total_tokens = sum(msg.token_count or 0 for msg in messages)
            conn.execute("""
                INSERT OR REPLACE INTO session_metrics 
                (session_id, message_count, total_tokens, last_activity)
                VALUES (?, ?, ?, ?)
            """, (session_id, len(messages), total_tokens, datetime.utcnow()))
            
            conn.commit()
    
    async def load_session(
        self,
        session_id: str
    ) -> Optional[tuple[List[SessionMessage], SessionContext]]:
        """Load session from SQLite"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._load_session_sync, session_id
            )
            
            if result:
                logger.debug(f"Loaded session {session_id} from SQLite")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            handle_error(e, "sqlite_storage_load")
            return None
    
    def _load_session_sync(
        self,
        session_id: str
    ) -> Optional[tuple[List[SessionMessage], SessionContext]]:
        """Synchronous session load"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Load session context
            session_row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            
            if not session_row:
                return None
            
            # Parse context data
            context_data = json.loads(session_row['context_data'])
            context = SessionContext(
                session_id=context_data['session_id'],
                user_id=context_data['user_id'],
                provider=context_data['provider'],
                model=context_data['model'],
                backend=context_data['backend'],
                max_messages=context_data.get('max_messages', 100),
                auto_archive=context_data.get('auto_archive', True),
                persist_messages=context_data.get('persist_messages', True),
                provider_session_id=context_data.get('provider_session_id'),
                provider_context=context_data.get('provider_context', {})
            )
            
            # Load messages
            message_rows = conn.execute("""
                SELECT * FROM session_messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,)).fetchall()
            
            messages = []
            for row in message_rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                message = SessionMessage(
                    id=row['message_id'],
                    role=MessageRole(row['role']),
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=metadata,
                    provider_message_id=row['provider_message_id'],
                    token_count=row['token_count'],
                    finish_reason=row['finish_reason']
                )
                messages.append(message)
            
            return messages, context
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from SQLite"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._delete_session_sync, session_id
            )
            
            logger.debug(f"Deleted session {session_id} from SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            handle_error(e, "sqlite_storage_delete")
            return False
    
    def _delete_session_sync(self, session_id: str):
        """Synchronous session delete"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[SessionContext]:
        """List sessions from SQLite"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._list_sessions_sync, user_id, status, limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            handle_error(e, "sqlite_storage_list")
            return []
    
    def _list_sessions_sync(
        self,
        user_id: Optional[str],
        status: Optional[SessionStatus],
        limit: int
    ) -> List[SessionContext]:
        """Synchronous session list"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM sessions"
            params = []
            
            if user_id:
                query += " WHERE user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            contexts = []
            for row in rows:
                context_data = json.loads(row['context_data'])
                context = SessionContext(
                    session_id=context_data['session_id'],
                    user_id=context_data['user_id'],
                    provider=context_data['provider'],
                    model=context_data['model'],
                    backend=context_data['backend'],
                    max_messages=context_data.get('max_messages', 100),
                    auto_archive=context_data.get('auto_archive', True),
                    persist_messages=context_data.get('persist_messages', True),
                    provider_session_id=context_data.get('provider_session_id'),
                    provider_context=context_data.get('provider_context', {})
                )
                contexts.append(context)
            
            return contexts
    
    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get session metrics from SQLite"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._get_metrics_sync, session_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get metrics for session {session_id}: {e}")
            handle_error(e, "sqlite_storage_metrics")
            return None
    
    def _get_metrics_sync(self, session_id: str) -> Optional[SessionMetrics]:
        """Synchronous metrics get"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            row = conn.execute(
                "SELECT * FROM session_metrics WHERE session_id = ?", (session_id,)
            ).fetchone()
            
            if not row:
                return None
            
            return SessionMetrics(
                message_count=row['message_count'],
                total_tokens=row['total_tokens'],
                session_duration=row['session_duration'],
                last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                created_at=datetime.fromisoformat(row['created_at'])
            )
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._cleanup_old_sessions_sync, max_age_days
            )
            
            logger.info(f"Cleaned up {result} old sessions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            handle_error(e, "sqlite_storage_cleanup")
            return 0
    
    def _cleanup_old_sessions_sync(self, max_age_days: int) -> int:
        """Synchronous old session cleanup"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE updated_at < ?", (cutoff_date,)
            )
            count = cursor.rowcount
            conn.commit()
            
            return count


class StorageFactory:
    """Factory for creating session storage backends"""
    
    @staticmethod
    def create_storage(storage_type: str, **kwargs) -> ISessionStorage:
        """
        Create session storage backend.
        
        Args:
            storage_type: Storage type (memory, sqlite)
            **kwargs: Storage-specific configuration
            
        Returns:
            Session storage instance
        """
        if storage_type.lower() in ["memory", "in_memory"]:
            return InMemorySessionStorage()
        
        elif storage_type.lower() in ["sqlite", "local"]:
            db_path = kwargs.get("db_path", "langswarm_sessions.db")
            return SQLiteSessionStorage(db_path)
        
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")


# Global storage instance
_default_storage: Optional[ISessionStorage] = None


def get_default_storage() -> ISessionStorage:
    """Get default session storage"""
    global _default_storage
    if _default_storage is None:
        _default_storage = SQLiteSessionStorage()
    return _default_storage


def set_default_storage(storage: ISessionStorage):
    """Set default session storage"""
    global _default_storage
    _default_storage = storage
