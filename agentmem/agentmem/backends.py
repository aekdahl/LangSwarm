"""
Memory Backend Implementations for AgentMem

Concrete implementations of memory backends for different storage systems.
Provides SQLite, Redis, and in-memory backends with unified interface.
"""

import json
import logging
import sqlite3
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from .interfaces import (
    IMemorySession, IMemoryBackend, 
    Message, MessageRole, SessionMetadata, SessionStatus,
    ConversationSummary, MemoryUsage, MemoryBackendType,
    MemoryConfig
)
from .base import BaseMemorySession, BaseMemoryBackend

# Optional Redis support
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class InMemoryBackend(BaseMemoryBackend):
    """
    In-memory backend for development and testing.
    Fast but non-persistent memory storage.
    """
    
    def __init__(self, config: MemoryConfig = None):
        super().__init__(config or {})
        self._data: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.IN_MEMORY
    
    async def connect(self) -> bool:
        """Connect to in-memory storage"""
        self._connected = True
        self._logger.info("Connected to in-memory backend")
        return True
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new in-memory session"""
        session = InMemorySession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        # Initialize session data
        self._data[metadata.session_id] = {
            "metadata": metadata,
            "messages": [],
            "summary": None
        }
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from memory"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Check if we have data for this session
        if session_id in self._data:
            session_data = self._data[session_id]
            session = InMemorySession(session_data["metadata"], self)
            
            # Restore messages
            for msg_data in session_data["messages"]:
                message = Message.from_dict(msg_data)
                session._messages.append(message)
            
            # Restore summary
            if session_data["summary"]:
                session._summary = ConversationSummary(**session_data["summary"])
            
            self._sessions[session_id] = session
            return session
        
        return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from memory"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        if session_id in self._data:
            del self._data[session_id]
        
        return True
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get raw session data (for internal use)"""
        return self._data.get(session_id)
    
    def update_session_data(self, session_id: str, data: Dict[str, Any]):
        """Update raw session data (for internal use)"""
        if session_id in self._data:
            self._data[session_id].update(data)


class InMemorySession(BaseMemorySession):
    """In-memory session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to in-memory storage"""
        if isinstance(self._backend, InMemoryBackend):
            session_data = self._backend.get_session_data(self.session_id)
            if session_data:
                session_data["messages"].append(message.to_dict())
    
    async def _persist_changes(self):
        """Persist changes to in-memory storage"""
        if isinstance(self._backend, InMemoryBackend):
            session_data = {
                "metadata": self._metadata,
                "messages": [msg.to_dict() for msg in self._messages],
                "summary": self._summary.__dict__ if self._summary else None
            }
            self._backend.update_session_data(self.session_id, session_data)
        
        self._is_dirty = False


class SQLiteBackend(BaseMemoryBackend):
    """
    SQLite backend for persistent local storage.
    Ideal for development and single-instance deployments.
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self._db_path = config.get("db_path", "langswarm_memory.db")
        self._connection: Optional[sqlite3.Connection] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.SQLITE
    
    async def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            # Ensure directory exists
            if self._db_path != ":memory:":
                Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            self._connected = True
            self._logger.info(f"Connected to SQLite backend: {self._db_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to SQLite backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from SQLite database"""
        try:
            if self._connection:
                self._connection.close()
                self._connection = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from SQLite backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from SQLite backend: {e}")
            return False
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self._connection.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                agent_id TEXT,
                workflow_id TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                max_messages INTEGER DEFAULT 100,
                max_tokens INTEGER,
                auto_summarize BOOLEAN DEFAULT TRUE,
                summary_threshold INTEGER DEFAULT 50,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                tags TEXT,
                properties TEXT
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                token_count INTEGER,
                metadata TEXT,
                function_call TEXT,
                tool_calls TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Summaries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                summary_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                message_count INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                key_topics TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)")
        
        self._connection.commit()
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new SQLite session"""
        cursor = self._connection.cursor()
        
        # Insert session metadata
        cursor.execute("""
            INSERT INTO sessions (
                session_id, user_id, agent_id, workflow_id, status,
                max_messages, max_tokens, auto_summarize, summary_threshold,
                created_at, updated_at, expires_at, tags, properties
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.session_id,
            metadata.user_id,
            metadata.agent_id,
            metadata.workflow_id,
            metadata.status.value,
            metadata.max_messages,
            metadata.max_tokens,
            metadata.auto_summarize,
            metadata.summary_threshold,
            metadata.created_at.isoformat(),
            metadata.updated_at.isoformat(),
            metadata.expires_at.isoformat() if metadata.expires_at else None,
            json.dumps(metadata.tags),
            json.dumps(metadata.properties)
        ))
        
        self._connection.commit()
        
        session = SQLiteSession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from SQLite"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Create metadata from row
        metadata = SessionMetadata(
            session_id=row["session_id"],
            user_id=row["user_id"],
            agent_id=row["agent_id"],
            workflow_id=row["workflow_id"],
            status=SessionStatus(row["status"]),
            max_messages=row["max_messages"],
            max_tokens=row["max_tokens"],
            auto_summarize=bool(row["auto_summarize"]),
            summary_threshold=row["summary_threshold"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            tags=json.loads(row["tags"]) if row["tags"] else [],
            properties=json.loads(row["properties"]) if row["properties"] else {}
        )
        
        session = SQLiteSession(metadata, self)
        
        # Load messages
        cursor.execute("""
            SELECT * FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        for msg_row in cursor.fetchall():
            message = Message(
                role=MessageRole(msg_row["role"]),
                content=msg_row["content"],
                timestamp=datetime.fromisoformat(msg_row["timestamp"]),
                message_id=msg_row["message_id"],
                metadata=json.loads(msg_row["metadata"]) if msg_row["metadata"] else {},
                token_count=msg_row["token_count"],
                function_call=json.loads(msg_row["function_call"]) if msg_row["function_call"] else None,
                tool_calls=json.loads(msg_row["tool_calls"]) if msg_row["tool_calls"] else None
            )
            session._messages.append(message)
        
        # Load summary
        cursor.execute("SELECT * FROM summaries WHERE session_id = ? ORDER BY created_at DESC LIMIT 1", (session_id,))
        summary_row = cursor.fetchone()
        
        if summary_row:
            session._summary = ConversationSummary(
                summary_id=summary_row["summary_id"],
                summary=summary_row["summary"],
                message_count=summary_row["message_count"],
                start_time=datetime.fromisoformat(summary_row["start_time"]),
                end_time=datetime.fromisoformat(summary_row["end_time"]),
                key_topics=json.loads(summary_row["key_topics"]) if summary_row["key_topics"] else [],
                created_at=datetime.fromisoformat(summary_row["created_at"])
            )
        
        self._sessions[session_id] = session
        return session
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions from SQLite"""
        cursor = self._connection.cursor()
        
        query = "SELECT * FROM sessions"
        params = []
        conditions = []
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        sessions = []
        for row in cursor.fetchall():
            metadata = SessionMetadata(
                session_id=row["session_id"],
                user_id=row["user_id"],
                agent_id=row["agent_id"],
                workflow_id=row["workflow_id"],
                status=SessionStatus(row["status"]),
                max_messages=row["max_messages"],
                max_tokens=row["max_tokens"],
                auto_summarize=bool(row["auto_summarize"]),
                summary_threshold=row["summary_threshold"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                tags=json.loads(row["tags"]) if row["tags"] else [],
                properties=json.loads(row["properties"]) if row["properties"] else {}
            )
            sessions.append(metadata)
        
        return sessions
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from SQLite"""
        try:
            cursor = self._connection.cursor()
            
            # Delete in order due to foreign key constraints
            cursor.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            
            self._connection.commit()
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection (for internal use)"""
        return self._connection


class SQLiteSession(BaseMemorySession):
    """SQLite session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to SQLite"""
        if isinstance(self._backend, SQLiteBackend):
            connection = self._backend.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO messages (
                    message_id, session_id, role, content, timestamp,
                    token_count, metadata, function_call, tool_calls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.message_id,
                self.session_id,
                message.role.value,
                message.content,
                message.timestamp.isoformat(),
                message.token_count,
                json.dumps(message.metadata) if message.metadata else None,
                json.dumps(message.function_call) if message.function_call else None,
                json.dumps(message.tool_calls) if message.tool_calls else None
            ))
            
            connection.commit()
    
    async def _persist_changes(self):
        """Persist changes to SQLite"""
        if isinstance(self._backend, SQLiteBackend):
            connection = self._backend.get_connection()
            cursor = connection.cursor()
            
            # Update session metadata
            cursor.execute("""
                UPDATE sessions SET
                    status = ?, updated_at = ?, max_messages = ?,
                    max_tokens = ?, auto_summarize = ?, summary_threshold = ?,
                    tags = ?, properties = ?
                WHERE session_id = ?
            """, (
                self._metadata.status.value,
                self._metadata.updated_at.isoformat(),
                self._metadata.max_messages,
                self._metadata.max_tokens,
                self._metadata.auto_summarize,
                self._metadata.summary_threshold,
                json.dumps(self._metadata.tags),
                json.dumps(self._metadata.properties),
                self.session_id
            ))
            
            # Persist summary if exists
            if self._summary:
                cursor.execute("""
                    INSERT OR REPLACE INTO summaries (
                        summary_id, session_id, summary, message_count,
                        start_time, end_time, key_topics, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self._summary.summary_id,
                    self.session_id,
                    self._summary.summary,
                    self._summary.message_count,
                    self._summary.start_time.isoformat(),
                    self._summary.end_time.isoformat(),
                    json.dumps(self._summary.key_topics),
                    self._summary.created_at.isoformat()
                ))
            
            connection.commit()
        
        self._is_dirty = False


class RedisBackend(BaseMemoryBackend):
    """
    Redis backend for fast, distributed memory storage.
    Ideal for production deployments with multiple instances.
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install with: pip install redis")
        
        self._redis_url = config.get("url", "redis://localhost:6379")
        self._db = config.get("db", 0)
        self._key_prefix = config.get("key_prefix", "langswarm:memory:")
        self._ttl = config.get("ttl", 86400)  # 24 hours default
        self._redis: Optional[redis.Redis] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.REDIS
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self._redis = redis.from_url(
                self._redis_url,
                db=self._db,
                decode_responses=True
            )
            
            # Test connection
            await self._redis.ping()
            
            self._connected = True
            self._logger.info(f"Connected to Redis backend: {self._redis_url}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to Redis backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Redis"""
        try:
            if self._redis:
                await self._redis.close()
                self._redis = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from Redis backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from Redis backend: {e}")
            return False
    
    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self._key_prefix}session:{session_id}"
    
    def _messages_key(self, session_id: str) -> str:
        """Get Redis key for messages"""
        return f"{self._key_prefix}messages:{session_id}"
    
    def _summary_key(self, session_id: str) -> str:
        """Get Redis key for summary"""
        return f"{self._key_prefix}summary:{session_id}"
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new Redis session"""
        session_data = {
            "session_id": metadata.session_id,
            "user_id": metadata.user_id or "",
            "agent_id": metadata.agent_id or "",
            "workflow_id": metadata.workflow_id or "",
            "status": metadata.status.value,
            "max_messages": str(metadata.max_messages),
            "max_tokens": str(metadata.max_tokens or ""),
            "auto_summarize": str(metadata.auto_summarize),
            "summary_threshold": str(metadata.summary_threshold),
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else "",
            "tags": json.dumps(metadata.tags),
            "properties": json.dumps(metadata.properties)
        }
        
        # Store session metadata
        session_key = self._session_key(metadata.session_id)
        await self._redis.hset(session_key, mapping=session_data)
        await self._redis.expire(session_key, self._ttl)
        
        session = RedisSession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from Redis"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        session_key = self._session_key(session_id)
        session_data = await self._redis.hgetall(session_key)
        
        if not session_data:
            return None
        
        # Create metadata from Redis data
        metadata = SessionMetadata(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"] or None,
            agent_id=session_data["agent_id"] or None,
            workflow_id=session_data["workflow_id"] or None,
            status=SessionStatus(session_data["status"]),
            max_messages=int(session_data["max_messages"]),
            max_tokens=int(session_data["max_tokens"]) if session_data["max_tokens"] else None,
            auto_summarize=session_data["auto_summarize"].lower() == "true",
            summary_threshold=int(session_data["summary_threshold"]),
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            expires_at=datetime.fromisoformat(session_data["expires_at"]) if session_data["expires_at"] else None,
            tags=json.loads(session_data["tags"]),
            properties=json.loads(session_data["properties"])
        )
        
        session = RedisSession(metadata, self)
        
        # Load messages
        messages_key = self._messages_key(session_id)
        message_ids = await self._redis.lrange(messages_key, 0, -1)
        
        for message_id in message_ids:
            message_data = await self._redis.hgetall(f"{self._key_prefix}message:{message_id}")
            if message_data:
                message = Message(
                    role=MessageRole(message_data["role"]),
                    content=message_data["content"],
                    timestamp=datetime.fromisoformat(message_data["timestamp"]),
                    message_id=message_data["message_id"],
                    metadata=json.loads(message_data["metadata"]) if message_data.get("metadata") else {},
                    token_count=int(message_data["token_count"]) if message_data.get("token_count") else None,
                    function_call=json.loads(message_data["function_call"]) if message_data.get("function_call") else None,
                    tool_calls=json.loads(message_data["tool_calls"]) if message_data.get("tool_calls") else None
                )
                session._messages.append(message)
        
        # Load summary
        summary_key = self._summary_key(session_id)
        summary_data = await self._redis.hgetall(summary_key)
        
        if summary_data:
            session._summary = ConversationSummary(
                summary_id=summary_data["summary_id"],
                summary=summary_data["summary"],
                message_count=int(summary_data["message_count"]),
                start_time=datetime.fromisoformat(summary_data["start_time"]),
                end_time=datetime.fromisoformat(summary_data["end_time"]),
                key_topics=json.loads(summary_data["key_topics"]),
                created_at=datetime.fromisoformat(summary_data["created_at"])
            )
        
        self._sessions[session_id] = session
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            # Delete all session-related keys
            session_key = self._session_key(session_id)
            messages_key = self._messages_key(session_id)
            summary_key = self._summary_key(session_id)
            
            # Get message IDs to delete individual message keys
            message_ids = await self._redis.lrange(messages_key, 0, -1)
            
            # Delete all keys
            keys_to_delete = [session_key, messages_key, summary_key]
            for message_id in message_ids:
                keys_to_delete.append(f"{self._key_prefix}message:{message_id}")
            
            await self._redis.delete(*keys_to_delete)
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def get_redis(self) -> redis.Redis:
        """Get Redis connection (for internal use)"""
        return self._redis
    
    def get_key_prefix(self) -> str:
        """Get Redis key prefix (for internal use)"""
        return self._key_prefix
    
    def get_ttl(self) -> int:
        """Get Redis TTL (for internal use)"""
        return self._ttl


class RedisSession(BaseMemorySession):
    """Redis session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to Redis"""
        if isinstance(self._backend, RedisBackend):
            redis_client = self._backend.get_redis()
            key_prefix = self._backend.get_key_prefix()
            ttl = self._backend.get_ttl()
            
            # Store message data
            message_key = f"{key_prefix}message:{message.message_id}"
            message_data = {
                "message_id": message.message_id,
                "session_id": self.session_id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "token_count": str(message.token_count or ""),
                "metadata": json.dumps(message.metadata) if message.metadata else "",
                "function_call": json.dumps(message.function_call) if message.function_call else "",
                "tool_calls": json.dumps(message.tool_calls) if message.tool_calls else ""
            }
            
            await redis_client.hset(message_key, mapping=message_data)
            await redis_client.expire(message_key, ttl)
            
            # Add message ID to session's message list
            messages_key = self._backend._messages_key(self.session_id)
            await redis_client.rpush(messages_key, message.message_id)
            await redis_client.expire(messages_key, ttl)
    
    async def _persist_changes(self):
        """Persist changes to Redis"""
        if isinstance(self._backend, RedisSession):
            redis_client = self._backend.get_redis()
            ttl = self._backend.get_ttl()
            
            # Update session metadata
            session_key = self._backend._session_key(self.session_id)
            session_data = {
                "status": self._metadata.status.value,
                "updated_at": self._metadata.updated_at.isoformat(),
                "max_messages": str(self._metadata.max_messages),
                "max_tokens": str(self._metadata.max_tokens or ""),
                "auto_summarize": str(self._metadata.auto_summarize),
                "summary_threshold": str(self._metadata.summary_threshold),
                "tags": json.dumps(self._metadata.tags),
                "properties": json.dumps(self._metadata.properties)
            }
            
            await redis_client.hset(session_key, mapping=session_data)
            await redis_client.expire(session_key, ttl)
            
            # Persist summary if exists
            if self._summary:
                summary_key = self._backend._summary_key(self.session_id)
                summary_data = {
                    "summary_id": self._summary.summary_id,
                    "session_id": self.session_id,
                    "summary": self._summary.summary,
                    "message_count": str(self._summary.message_count),
                    "start_time": self._summary.start_time.isoformat(),
                    "end_time": self._summary.end_time.isoformat(),
                    "key_topics": json.dumps(self._summary.key_topics),
                    "created_at": self._summary.created_at.isoformat()
                }
                
                await redis_client.hset(summary_key, mapping=summary_data)
                await redis_client.expire(summary_key, ttl)
        
        self._is_dirty = False
