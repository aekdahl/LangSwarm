"""
Memory Backend Implementations for langswarm-memory

Concrete implementations of memory backends for different storage systems.
Provides SQLite, Redis, BigQuery, PostgreSQL, MongoDB, Elasticsearch backends.
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

# Optional BigQuery support
try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    BIGQUERY_AVAILABLE = True
except ImportError:
    bigquery = None
    NotFound = None
    BIGQUERY_AVAILABLE = False

# Optional PostgreSQL support
try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    asyncpg = None
    POSTGRES_AVAILABLE = False

# Optional MongoDB support
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
except ImportError:
    AsyncIOMotorClient = None
    MONGODB_AVAILABLE = False

# Optional Elasticsearch support
try:
    from elasticsearch import AsyncElasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    AsyncElasticsearch = None
    ELASTICSEARCH_AVAILABLE = False


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


# =============================================================================
# PostgreSQL Backend
# =============================================================================

class PostgresBackend(BaseMemoryBackend):
    """
    PostgreSQL backend for enterprise-grade persistent memory storage.
    Ideal for production deployments requiring ACID compliance.
    
    Config options:
        - host: PostgreSQL host (default: "localhost")
        - port: PostgreSQL port (default: 5432)
        - database: Database name (required)
        - user: Database user (required)
        - password: Database password (required)
        - min_connections: Minimum pool connections (default: 5)
        - max_connections: Maximum pool connections (default: 20)
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        if not POSTGRES_AVAILABLE:
            raise ImportError("asyncpg is not available. Install with: pip install asyncpg")
        
        self._host = config.get("host", "localhost")
        self._port = config.get("port", 5432)
        self._database = config.get("database")
        self._user = config.get("user")
        self._password = config.get("password")
        self._min_connections = config.get("min_connections", 5)
        self._max_connections = config.get("max_connections", 20)
        
        if not self._database:
            raise ValueError("database is required for PostgreSQL backend")
        if not self._user:
            raise ValueError("user is required for PostgreSQL backend")
        
        self._pool: Any = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.POSTGRES
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL and ensure tables exist"""
        try:
            self._pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password,
                min_size=self._min_connections,
                max_size=self._max_connections,
            )
            
            # Create tables
            await self._create_tables()
            
            self._connected = True
            self._logger.info(f"Connected to PostgreSQL backend: {self._host}:{self._port}/{self._database}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to PostgreSQL backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL"""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from PostgreSQL backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from PostgreSQL backend: {e}")
            return False
    
    async def _create_tables(self):
        """Create required tables if they don't exist"""
        async with self._pool.acquire() as conn:
            # Sessions table
            await conn.execute("""
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
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    expires_at TIMESTAMPTZ,
                    tags JSONB DEFAULT '[]',
                    properties JSONB DEFAULT '{}'
                )
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    token_count INTEGER,
                    metadata JSONB,
                    function_call JSONB,
                    tool_calls JSONB
                )
            """)
            
            # Summaries table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    summary_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    summary TEXT NOT NULL,
                    message_count INTEGER NOT NULL,
                    start_time TIMESTAMPTZ NOT NULL,
                    end_time TIMESTAMPTZ NOT NULL,
                    key_topics JSONB,
                    created_at TIMESTAMPTZ NOT NULL
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_summaries_session_id ON summaries(session_id)")
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new PostgreSQL session"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO sessions (
                    session_id, user_id, agent_id, workflow_id, status,
                    max_messages, max_tokens, auto_summarize, summary_threshold,
                    created_at, updated_at, expires_at, tags, properties
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
                metadata.session_id,
                metadata.user_id,
                metadata.agent_id,
                metadata.workflow_id,
                metadata.status.value,
                metadata.max_messages,
                metadata.max_tokens,
                metadata.auto_summarize,
                metadata.summary_threshold,
                metadata.created_at,
                metadata.updated_at,
                metadata.expires_at,
                json.dumps(metadata.tags),
                json.dumps(metadata.properties),
            )
        
        session = PostgresSession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from PostgreSQL"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE session_id = $1",
                session_id
            )
            
            if not row:
                return None
            
            metadata = SessionMetadata(
                session_id=row["session_id"],
                user_id=row["user_id"],
                agent_id=row["agent_id"],
                workflow_id=row["workflow_id"],
                status=SessionStatus(row["status"]),
                max_messages=row["max_messages"] or 100,
                max_tokens=row["max_tokens"],
                auto_summarize=row["auto_summarize"] if row["auto_summarize"] is not None else True,
                summary_threshold=row["summary_threshold"] or 50,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
                tags=row["tags"] if row["tags"] else [],
                properties=row["properties"] if row["properties"] else {},
            )
            
            session = PostgresSession(metadata, self)
            
            # Load messages
            messages = await conn.fetch(
                "SELECT * FROM messages WHERE session_id = $1 ORDER BY timestamp ASC",
                session_id
            )
            
            for msg_row in messages:
                message = Message(
                    role=MessageRole(msg_row["role"]),
                    content=msg_row["content"],
                    timestamp=msg_row["timestamp"],
                    message_id=msg_row["message_id"],
                    metadata=msg_row["metadata"] if msg_row["metadata"] else {},
                    token_count=msg_row["token_count"],
                    function_call=msg_row["function_call"],
                    tool_calls=msg_row["tool_calls"],
                )
                session._messages.append(message)
            
            # Load latest summary
            summary_row = await conn.fetchrow(
                "SELECT * FROM summaries WHERE session_id = $1 ORDER BY created_at DESC LIMIT 1",
                session_id
            )
            
            if summary_row:
                session._summary = ConversationSummary(
                    summary_id=summary_row["summary_id"],
                    summary=summary_row["summary"],
                    message_count=summary_row["message_count"],
                    start_time=summary_row["start_time"],
                    end_time=summary_row["end_time"],
                    key_topics=summary_row["key_topics"] if summary_row["key_topics"] else [],
                    created_at=summary_row["created_at"],
                )
            
            self._sessions[session_id] = session
            return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from PostgreSQL"""
        try:
            async with self._pool.acquire() as conn:
                # CASCADE will handle messages and summaries
                await conn.execute("DELETE FROM sessions WHERE session_id = $1", session_id)
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions from PostgreSQL"""
        conditions = []
        params = []
        param_idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        params.extend([limit, offset])
        
        query = f"""
            SELECT * FROM sessions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        sessions = []
        for row in rows:
            metadata = SessionMetadata(
                session_id=row["session_id"],
                user_id=row["user_id"],
                agent_id=row["agent_id"],
                workflow_id=row["workflow_id"],
                status=SessionStatus(row["status"]),
                max_messages=row["max_messages"] or 100,
                max_tokens=row["max_tokens"],
                auto_summarize=row["auto_summarize"] if row["auto_summarize"] is not None else True,
                summary_threshold=row["summary_threshold"] or 50,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
                tags=row["tags"] if row["tags"] else [],
                properties=row["properties"] if row["properties"] else {},
            )
            sessions.append(metadata)
        
        return sessions
    
    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connection health"""
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            return {
                "status": "healthy",
                "connected": True,
                "backend": "postgres",
                "host": self._host,
                "database": self._database,
                "pool_size": self._pool.get_size(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "backend": "postgres",
                "error": str(e),
            }
    
    def get_pool(self) -> Any:
        """Get connection pool (for internal use)"""
        return self._pool


class PostgresSession(BaseMemorySession):
    """PostgreSQL session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to PostgreSQL"""
        if isinstance(self._backend, PostgresBackend):
            pool = self._backend.get_pool()
            
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO messages (
                        message_id, session_id, role, content, timestamp,
                        token_count, metadata, function_call, tool_calls
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    message.message_id,
                    self.session_id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    message.token_count,
                    json.dumps(message.metadata) if message.metadata else None,
                    json.dumps(message.function_call) if message.function_call else None,
                    json.dumps(message.tool_calls) if message.tool_calls else None,
                )
    
    async def _persist_changes(self):
        """Persist session changes to PostgreSQL"""
        if isinstance(self._backend, PostgresBackend):
            pool = self._backend.get_pool()
            
            async with pool.acquire() as conn:
                # Update session metadata
                await conn.execute("""
                    UPDATE sessions SET
                        status = $2,
                        updated_at = $3,
                        max_messages = $4,
                        max_tokens = $5,
                        auto_summarize = $6,
                        summary_threshold = $7,
                        tags = $8,
                        properties = $9
                    WHERE session_id = $1
                """,
                    self.session_id,
                    self._metadata.status.value,
                    self._metadata.updated_at,
                    self._metadata.max_messages,
                    self._metadata.max_tokens,
                    self._metadata.auto_summarize,
                    self._metadata.summary_threshold,
                    json.dumps(self._metadata.tags),
                    json.dumps(self._metadata.properties),
                )
                
                # Persist summary if exists
                if self._summary:
                    await conn.execute("""
                        INSERT INTO summaries (
                            summary_id, session_id, summary, message_count,
                            start_time, end_time, key_topics, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (summary_id) DO UPDATE SET
                            summary = EXCLUDED.summary,
                            message_count = EXCLUDED.message_count,
                            end_time = EXCLUDED.end_time,
                            key_topics = EXCLUDED.key_topics
                    """,
                        self._summary.summary_id,
                        self.session_id,
                        self._summary.summary,
                        self._summary.message_count,
                        self._summary.start_time,
                        self._summary.end_time,
                        json.dumps(self._summary.key_topics),
                        self._summary.created_at,
                    )
        
        self._is_dirty = False


# =============================================================================
# BigQuery Backend
# =============================================================================

class BigQueryBackend(BaseMemoryBackend):
    """
    BigQuery backend for cloud-scale persistent memory storage.
    Ideal for large-scale deployments on Google Cloud Platform.
    
    Config options:
        - project_id: GCP project ID (required)
        - dataset_id: BigQuery dataset ID (default: "langswarm_memory")
        - location: Dataset location (default: "US")
        - credentials_path: Path to service account JSON (optional, uses default if not set)
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        if not BIGQUERY_AVAILABLE:
            raise ImportError("BigQuery is not available. Install with: pip install google-cloud-bigquery")
        
        self._project_id = config.get("project_id")
        if not self._project_id:
            raise ValueError("project_id is required for BigQuery backend")
        
        self._dataset_id = config.get("dataset_id", "langswarm_memory")
        self._location = config.get("location", "US")
        self._credentials_path = config.get("credentials_path")
        
        # Retention settings (default 180 days)
        self._retention_days = config.get("retention_days", 180)
        self._retention_ms = self._retention_days * 24 * 60 * 60 * 1000 if self._retention_days else None
        
        self._client: Optional[bigquery.Client] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.BIGQUERY
    
    async def connect(self) -> bool:
        """Connect to BigQuery and ensure tables exist"""
        try:
            # Create client
            if self._credentials_path:
                self._client = bigquery.Client.from_service_account_json(
                    self._credentials_path,
                    project=self._project_id
                )
            else:
                self._client = bigquery.Client(project=self._project_id)
            
            # Create dataset if not exists
            await self._ensure_dataset()
            
            # Create tables if not exist
            await self._create_tables()
            
            self._connected = True
            self._logger.info(f"Connected to BigQuery backend: {self._project_id}.{self._dataset_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to BigQuery backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from BigQuery"""
        try:
            if self._client:
                self._client.close()
                self._client = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from BigQuery backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from BigQuery backend: {e}")
            return False
    
    async def _ensure_dataset(self):
        """Ensure dataset exists"""
        dataset_ref = bigquery.DatasetReference(self._project_id, self._dataset_id)
        
        try:
            self._client.get_dataset(dataset_ref)
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self._location
            self._client.create_dataset(dataset)
            self._logger.info(f"Created BigQuery dataset: {self._dataset_id}")
    
    async def _create_tables(self):
        """Create required tables if they don't exist"""
        # Sessions table schema
        sessions_schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING"),
            bigquery.SchemaField("agent_id", "STRING"),
            bigquery.SchemaField("workflow_id", "STRING"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("max_messages", "INTEGER"),
            bigquery.SchemaField("max_tokens", "INTEGER"),
            bigquery.SchemaField("auto_summarize", "BOOLEAN"),
            bigquery.SchemaField("summary_threshold", "INTEGER"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("expires_at", "TIMESTAMP"),
            bigquery.SchemaField("tags", "JSON"),
            bigquery.SchemaField("properties", "JSON"),
        ]
        
        # Messages table schema
        messages_schema = [
            bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("token_count", "INTEGER"),
            bigquery.SchemaField("metadata", "JSON"),
            bigquery.SchemaField("function_call", "JSON"),
            bigquery.SchemaField("tool_calls", "JSON"),
        ]
        
        # Summaries table schema
        summaries_schema = [
            bigquery.SchemaField("summary_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("summary", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message_count", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("key_topics", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        tables = [
            ("sessions", sessions_schema, "created_at"),
            ("messages", messages_schema, "timestamp"),
            ("summaries", summaries_schema, "created_at"),
        ]
        
        for table_name, schema, partition_field in tables:
            table_ref = f"{self._project_id}.{self._dataset_id}.{table_name}"
            try:
                table = self._client.get_table(table_ref)
                
                # Check if retention needs to be updated for existing partitioned tables
                if table.time_partitioning and self._retention_ms:
                    if table.time_partitioning.expiration_ms != self._retention_ms:
                        self._logger.info(f"Updating retention for table {table_name} to {self._retention_days} days")
                        table.time_partitioning.expiration_ms = self._retention_ms
                        self._client.update_table(table, ["time_partitioning"])
                elif not table.time_partitioning and self._retention_ms:
                    self._logger.warning(
                        f"⚠️ Cannot apply retention to existing non-partitioned table '{table_name}'. "
                        "To enable retention, you must migrate this table to a partitioned table."
                    )
                    
            except NotFound:
                table = bigquery.Table(table_ref, schema=schema)
                
                # Configure partitioning if retention is enabled
                if self._retention_ms:
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field=partition_field,
                        expiration_ms=self._retention_ms
                    )
                
                self._client.create_table(table)
                self._logger.info(f"Created BigQuery table: {table_name} (retention: {self._retention_days} days)")
    
    def _full_table_name(self, table: str) -> str:
        """Get fully qualified table name"""
        return f"`{self._project_id}.{self._dataset_id}.{table}`"
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new BigQuery session"""
        # Insert session into BigQuery
        table_ref = f"{self._project_id}.{self._dataset_id}.sessions"
        
        rows_to_insert = [{
            "session_id": metadata.session_id,
            "user_id": metadata.user_id,
            "agent_id": metadata.agent_id,
            "workflow_id": metadata.workflow_id,
            "status": metadata.status.value,
            "max_messages": metadata.max_messages,
            "max_tokens": metadata.max_tokens,
            "auto_summarize": metadata.auto_summarize,
            "summary_threshold": metadata.summary_threshold,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
            "tags": json.dumps(metadata.tags),
            "properties": json.dumps(metadata.properties),
        }]
        
        errors = self._client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            self._logger.error(f"Failed to insert session: {errors}")
            raise RuntimeError(f"BigQuery insert failed: {errors}")
        
        session = BigQuerySession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from BigQuery"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Query session from BigQuery
        query = f"""
            SELECT * FROM {self._full_table_name('sessions')}
            WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        query_job = self._client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return None
        
        row = results[0]
        
        # Create metadata from BigQuery row
        metadata = SessionMetadata(
            session_id=row.session_id,
            user_id=row.user_id,
            agent_id=row.agent_id,
            workflow_id=row.workflow_id,
            status=SessionStatus(row.status),
            max_messages=row.max_messages or 100,
            max_tokens=row.max_tokens,
            auto_summarize=row.auto_summarize if row.auto_summarize is not None else True,
            summary_threshold=row.summary_threshold or 50,
            created_at=row.created_at,
            updated_at=row.updated_at,
            expires_at=row.expires_at,
            tags=json.loads(row.tags) if row.tags else [],
            properties=json.loads(row.properties) if row.properties else {},
        )
        
        session = BigQuerySession(metadata, self)
        
        # Load messages
        messages_query = f"""
            SELECT * FROM {self._full_table_name('messages')}
            WHERE session_id = @session_id
            ORDER BY timestamp ASC
        """
        
        messages_job = self._client.query(messages_query, job_config=job_config)
        
        for msg_row in messages_job.result():
            message = Message(
                role=MessageRole(msg_row.role),
                content=msg_row.content,
                timestamp=msg_row.timestamp,
                message_id=msg_row.message_id,
                metadata=json.loads(msg_row.metadata) if msg_row.metadata else {},
                token_count=msg_row.token_count,
                function_call=json.loads(msg_row.function_call) if msg_row.function_call else None,
                tool_calls=json.loads(msg_row.tool_calls) if msg_row.tool_calls else None,
            )
            session._messages.append(message)
        
        # Load summary
        summary_query = f"""
            SELECT * FROM {self._full_table_name('summaries')}
            WHERE session_id = @session_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        summary_job = self._client.query(summary_query, job_config=job_config)
        summary_results = list(summary_job.result())
        
        if summary_results:
            sum_row = summary_results[0]
            session._summary = ConversationSummary(
                summary_id=sum_row.summary_id,
                summary=sum_row.summary,
                message_count=sum_row.message_count,
                start_time=sum_row.start_time,
                end_time=sum_row.end_time,
                key_topics=json.loads(sum_row.key_topics) if sum_row.key_topics else [],
                created_at=sum_row.created_at,
            )
        
        self._sessions[session_id] = session
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from BigQuery"""
        try:
            # Delete messages
            delete_messages = f"""
                DELETE FROM {self._full_table_name('messages')}
                WHERE session_id = @session_id
            """
            
            # Delete summaries
            delete_summaries = f"""
                DELETE FROM {self._full_table_name('summaries')}
                WHERE session_id = @session_id
            """
            
            # Delete session
            delete_session = f"""
                DELETE FROM {self._full_table_name('sessions')}
                WHERE session_id = @session_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            )
            
            for query in [delete_messages, delete_summaries, delete_session]:
                self._client.query(query, job_config=job_config).result()
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions from BigQuery"""
        conditions = []
        params = []
        
        if user_id:
            conditions.append("user_id = @user_id")
            params.append(bigquery.ScalarQueryParameter("user_id", "STRING", user_id))
        
        if status:
            conditions.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status.value))
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM {self._full_table_name('sessions')}
            {where_clause}
            ORDER BY created_at DESC
            LIMIT @limit OFFSET @offset
        """
        
        params.extend([
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ])
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        query_job = self._client.query(query, job_config=job_config)
        
        sessions = []
        for row in query_job.result():
            metadata = SessionMetadata(
                session_id=row.session_id,
                user_id=row.user_id,
                agent_id=row.agent_id,
                workflow_id=row.workflow_id,
                status=SessionStatus(row.status),
                max_messages=row.max_messages or 100,
                max_tokens=row.max_tokens,
                auto_summarize=row.auto_summarize if row.auto_summarize is not None else True,
                summary_threshold=row.summary_threshold or 50,
                created_at=row.created_at,
                updated_at=row.updated_at,
                expires_at=row.expires_at,
                tags=json.loads(row.tags) if row.tags else [],
                properties=json.loads(row.properties) if row.properties else {},
            )
            sessions.append(metadata)
        
        return sessions
    
    async def health_check(self) -> Dict[str, Any]:
        """Check BigQuery connection health"""
        try:
            # Simple query to test connection
            query = "SELECT 1"
            self._client.query(query).result()
            
            return {
                "status": "healthy",
                "connected": True,
                "backend": "bigquery",
                "project_id": self._project_id,
                "dataset_id": self._dataset_id,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "backend": "bigquery",
                "error": str(e),
            }
    
    def get_client(self) -> bigquery.Client:
        """Get BigQuery client (for internal use)"""
        return self._client


class BigQuerySession(BaseMemorySession):
    """BigQuery session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to BigQuery"""
        if isinstance(self._backend, BigQueryBackend):
            client = self._backend.get_client()
            table_ref = f"{self._backend._project_id}.{self._backend._dataset_id}.messages"
            
            rows_to_insert = [{
                "message_id": message.message_id,
                "session_id": self.session_id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "token_count": message.token_count,
                "metadata": json.dumps(message.metadata) if message.metadata else None,
                "function_call": json.dumps(message.function_call) if message.function_call else None,
                "tool_calls": json.dumps(message.tool_calls) if message.tool_calls else None,
            }]
            
            errors = client.insert_rows_json(table_ref, rows_to_insert)
            if errors:
                self._backend._logger.error(f"Failed to insert message: {errors}")
    
    async def _persist_changes(self):
        """Persist session changes to BigQuery"""
        if isinstance(self._backend, BigQueryBackend):
            client = self._backend.get_client()
            
            # Update session metadata using MERGE (BigQuery doesn't support UPDATE directly with streaming buffer)
            update_query = f"""
                UPDATE {self._backend._full_table_name('sessions')}
                SET 
                    status = @status,
                    updated_at = @updated_at,
                    max_messages = @max_messages,
                    max_tokens = @max_tokens,
                    auto_summarize = @auto_summarize,
                    summary_threshold = @summary_threshold,
                    tags = @tags,
                    properties = @properties
                WHERE session_id = @session_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", self.session_id),
                    bigquery.ScalarQueryParameter("status", "STRING", self._metadata.status.value),
                    bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", self._metadata.updated_at.isoformat()),
                    bigquery.ScalarQueryParameter("max_messages", "INT64", self._metadata.max_messages),
                    bigquery.ScalarQueryParameter("max_tokens", "INT64", self._metadata.max_tokens),
                    bigquery.ScalarQueryParameter("auto_summarize", "BOOL", self._metadata.auto_summarize),
                    bigquery.ScalarQueryParameter("summary_threshold", "INT64", self._metadata.summary_threshold),
                    bigquery.ScalarQueryParameter("tags", "STRING", json.dumps(self._metadata.tags)),
                    bigquery.ScalarQueryParameter("properties", "STRING", json.dumps(self._metadata.properties)),
                ]
            )
            
            client.query(update_query, job_config=job_config).result()
            
            # Persist summary if exists
            if self._summary:
                summary_table = f"{self._backend._project_id}.{self._backend._dataset_id}.summaries"
                
                rows_to_insert = [{
                    "summary_id": self._summary.summary_id,
                    "session_id": self.session_id,
                    "summary": self._summary.summary,
                    "message_count": self._summary.message_count,
                    "start_time": self._summary.start_time.isoformat(),
                    "end_time": self._summary.end_time.isoformat(),
                    "key_topics": json.dumps(self._summary.key_topics),
                    "created_at": self._summary.created_at.isoformat(),
                }]
                
                client.insert_rows_json(summary_table, rows_to_insert)
        
        self._is_dirty = False


# =============================================================================
# MongoDB Backend
# =============================================================================

class MongoDBBackend(BaseMemoryBackend):
    """
    MongoDB backend for flexible document-based memory storage.
    Ideal for deployments requiring schema flexibility and horizontal scaling.
    
    Config options:
        - uri: MongoDB connection URI (default: "mongodb://localhost:27017")
        - database: Database name (default: "langswarm_memory")
        - collection_prefix: Prefix for collections (default: "")
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        if not MONGODB_AVAILABLE:
            raise ImportError("motor is not available. Install with: pip install motor")
        
        self._uri = config.get("uri", "mongodb://localhost:27017")
        self._database_name = config.get("database", "langswarm_memory")
        self._collection_prefix = config.get("collection_prefix", "")
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.MONGODB
    
    def _collection_name(self, name: str) -> str:
        """Get prefixed collection name"""
        return f"{self._collection_prefix}{name}" if self._collection_prefix else name
    
    async def connect(self) -> bool:
        """Connect to MongoDB and ensure indexes exist"""
        try:
            self._client = AsyncIOMotorClient(self._uri)
            self._db = self._client[self._database_name]
            
            # Test connection
            await self._client.admin.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            self._connected = True
            self._logger.info(f"Connected to MongoDB backend: {self._uri}/{self._database_name}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to MongoDB backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MongoDB"""
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._db = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from MongoDB backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from MongoDB backend: {e}")
            return False
    
    async def _create_indexes(self):
        """Create required indexes"""
        sessions_col = self._db[self._collection_name("sessions")]
        messages_col = self._db[self._collection_name("messages")]
        summaries_col = self._db[self._collection_name("summaries")]
        
        # Sessions indexes
        await sessions_col.create_index("session_id", unique=True)
        await sessions_col.create_index("user_id")
        await sessions_col.create_index("status")
        await sessions_col.create_index("created_at")
        
        # Messages indexes
        await messages_col.create_index("message_id", unique=True)
        await messages_col.create_index("session_id")
        await messages_col.create_index([("session_id", 1), ("timestamp", 1)])
        
        # Summaries indexes
        await summaries_col.create_index("summary_id", unique=True)
        await summaries_col.create_index("session_id")
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new MongoDB session"""
        sessions_col = self._db[self._collection_name("sessions")]
        
        doc = {
            "session_id": metadata.session_id,
            "user_id": metadata.user_id,
            "agent_id": metadata.agent_id,
            "workflow_id": metadata.workflow_id,
            "status": metadata.status.value,
            "max_messages": metadata.max_messages,
            "max_tokens": metadata.max_tokens,
            "auto_summarize": metadata.auto_summarize,
            "summary_threshold": metadata.summary_threshold,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at,
            "expires_at": metadata.expires_at,
            "tags": metadata.tags,
            "properties": metadata.properties,
        }
        
        await sessions_col.insert_one(doc)
        
        session = MongoDBSession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from MongoDB"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        sessions_col = self._db[self._collection_name("sessions")]
        messages_col = self._db[self._collection_name("messages")]
        summaries_col = self._db[self._collection_name("summaries")]
        
        doc = await sessions_col.find_one({"session_id": session_id})
        
        if not doc:
            return None
        
        metadata = SessionMetadata(
            session_id=doc["session_id"],
            user_id=doc.get("user_id"),
            agent_id=doc.get("agent_id"),
            workflow_id=doc.get("workflow_id"),
            status=SessionStatus(doc["status"]),
            max_messages=doc.get("max_messages", 100),
            max_tokens=doc.get("max_tokens"),
            auto_summarize=doc.get("auto_summarize", True),
            summary_threshold=doc.get("summary_threshold", 50),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            expires_at=doc.get("expires_at"),
            tags=doc.get("tags", []),
            properties=doc.get("properties", {}),
        )
        
        session = MongoDBSession(metadata, self)
        
        # Load messages
        cursor = messages_col.find({"session_id": session_id}).sort("timestamp", 1)
        async for msg_doc in cursor:
            message = Message(
                role=MessageRole(msg_doc["role"]),
                content=msg_doc["content"],
                timestamp=msg_doc["timestamp"],
                message_id=msg_doc["message_id"],
                metadata=msg_doc.get("metadata", {}),
                token_count=msg_doc.get("token_count"),
                function_call=msg_doc.get("function_call"),
                tool_calls=msg_doc.get("tool_calls"),
            )
            session._messages.append(message)
        
        # Load latest summary
        summary_doc = await summaries_col.find_one(
            {"session_id": session_id},
            sort=[("created_at", -1)]
        )
        
        if summary_doc:
            session._summary = ConversationSummary(
                summary_id=summary_doc["summary_id"],
                summary=summary_doc["summary"],
                message_count=summary_doc["message_count"],
                start_time=summary_doc["start_time"],
                end_time=summary_doc["end_time"],
                key_topics=summary_doc.get("key_topics", []),
                created_at=summary_doc["created_at"],
            )
        
        self._sessions[session_id] = session
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from MongoDB"""
        try:
            sessions_col = self._db[self._collection_name("sessions")]
            messages_col = self._db[self._collection_name("messages")]
            summaries_col = self._db[self._collection_name("summaries")]
            
            # Delete all related documents
            await messages_col.delete_many({"session_id": session_id})
            await summaries_col.delete_many({"session_id": session_id})
            await sessions_col.delete_one({"session_id": session_id})
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions from MongoDB"""
        sessions_col = self._db[self._collection_name("sessions")]
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status.value
        
        cursor = sessions_col.find(query).sort("created_at", -1).skip(offset).limit(limit)
        
        sessions = []
        async for doc in cursor:
            metadata = SessionMetadata(
                session_id=doc["session_id"],
                user_id=doc.get("user_id"),
                agent_id=doc.get("agent_id"),
                workflow_id=doc.get("workflow_id"),
                status=SessionStatus(doc["status"]),
                max_messages=doc.get("max_messages", 100),
                max_tokens=doc.get("max_tokens"),
                auto_summarize=doc.get("auto_summarize", True),
                summary_threshold=doc.get("summary_threshold", 50),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                expires_at=doc.get("expires_at"),
                tags=doc.get("tags", []),
                properties=doc.get("properties", {}),
            )
            sessions.append(metadata)
        
        return sessions
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            await self._client.admin.command('ping')
            
            return {
                "status": "healthy",
                "connected": True,
                "backend": "mongodb",
                "uri": self._uri,
                "database": self._database_name,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "backend": "mongodb",
                "error": str(e),
            }
    
    def get_db(self):
        """Get database instance (for internal use)"""
        return self._db
    
    def get_collection_name(self, name: str) -> str:
        """Get collection name (for internal use)"""
        return self._collection_name(name)


class MongoDBSession(BaseMemorySession):
    """MongoDB session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to MongoDB"""
        if isinstance(self._backend, MongoDBBackend):
            db = self._backend.get_db()
            messages_col = db[self._backend.get_collection_name("messages")]
            
            doc = {
                "message_id": message.message_id,
                "session_id": self.session_id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp,
                "token_count": message.token_count,
                "metadata": message.metadata,
                "function_call": message.function_call,
                "tool_calls": message.tool_calls,
            }
            
            await messages_col.insert_one(doc)
    
    async def _persist_changes(self):
        """Persist session changes to MongoDB"""
        if isinstance(self._backend, MongoDBBackend):
            db = self._backend.get_db()
            sessions_col = db[self._backend.get_collection_name("sessions")]
            summaries_col = db[self._backend.get_collection_name("summaries")]
            
            # Update session metadata
            await sessions_col.update_one(
                {"session_id": self.session_id},
                {"$set": {
                    "status": self._metadata.status.value,
                    "updated_at": self._metadata.updated_at,
                    "max_messages": self._metadata.max_messages,
                    "max_tokens": self._metadata.max_tokens,
                    "auto_summarize": self._metadata.auto_summarize,
                    "summary_threshold": self._metadata.summary_threshold,
                    "tags": self._metadata.tags,
                    "properties": self._metadata.properties,
                }}
            )
            
            # Persist summary if exists
            if self._summary:
                await summaries_col.update_one(
                    {"summary_id": self._summary.summary_id},
                    {"$set": {
                        "session_id": self.session_id,
                        "summary": self._summary.summary,
                        "message_count": self._summary.message_count,
                        "start_time": self._summary.start_time,
                        "end_time": self._summary.end_time,
                        "key_topics": self._summary.key_topics,
                        "created_at": self._summary.created_at,
                    }},
                    upsert=True
                )
        
        self._is_dirty = False


# =============================================================================
# Elasticsearch Backend
# =============================================================================

class ElasticsearchBackend(BaseMemoryBackend):
    """
    Elasticsearch backend for search-optimized memory storage.
    Ideal for deployments requiring full-text search and analytics.
    
    Config options:
        - hosts: List of Elasticsearch hosts (default: ["http://localhost:9200"])
        - index_prefix: Prefix for indices (default: "langswarm_memory")
        - api_key: API key for authentication (optional)
        - username: Username for basic auth (optional)
        - password: Password for basic auth (optional)
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("elasticsearch is not available. Install with: pip install elasticsearch[async]")
        
        self._hosts = config.get("hosts", ["http://localhost:9200"])
        self._index_prefix = config.get("index_prefix", "langswarm_memory")
        self._api_key = config.get("api_key")
        self._username = config.get("username")
        self._password = config.get("password")
        
        self._client: Optional[AsyncElasticsearch] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.ELASTICSEARCH
    
    def _index_name(self, name: str) -> str:
        """Get prefixed index name"""
        return f"{self._index_prefix}_{name}"
    
    async def connect(self) -> bool:
        """Connect to Elasticsearch and ensure indices exist"""
        try:
            # Build connection kwargs
            kwargs = {"hosts": self._hosts}
            
            if self._api_key:
                kwargs["api_key"] = self._api_key
            elif self._username and self._password:
                kwargs["basic_auth"] = (self._username, self._password)
            
            self._client = AsyncElasticsearch(**kwargs)
            
            # Test connection
            await self._client.info()
            
            # Create indices
            await self._create_indices()
            
            self._connected = True
            self._logger.info(f"Connected to Elasticsearch backend: {self._hosts}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to Elasticsearch backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Elasticsearch"""
        try:
            if self._client:
                await self._client.close()
                self._client = None
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info("Disconnected from Elasticsearch backend")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to disconnect from Elasticsearch backend: {e}")
            return False
    
    async def _create_indices(self):
        """Create required indices if they don't exist"""
        # Sessions index mapping
        sessions_mapping = {
            "mappings": {
                "properties": {
                    "session_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "agent_id": {"type": "keyword"},
                    "workflow_id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "max_messages": {"type": "integer"},
                    "max_tokens": {"type": "integer"},
                    "auto_summarize": {"type": "boolean"},
                    "summary_threshold": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "expires_at": {"type": "date"},
                    "tags": {"type": "keyword"},
                    "properties": {"type": "object", "enabled": False},
                }
            }
        }
        
        # Messages index mapping
        messages_mapping = {
            "mappings": {
                "properties": {
                    "message_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "role": {"type": "keyword"},
                    "content": {"type": "text"},
                    "timestamp": {"type": "date"},
                    "token_count": {"type": "integer"},
                    "metadata": {"type": "object", "enabled": False},
                    "function_call": {"type": "object", "enabled": False},
                    "tool_calls": {"type": "object", "enabled": False},
                }
            }
        }
        
        # Summaries index mapping
        summaries_mapping = {
            "mappings": {
                "properties": {
                    "summary_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "message_count": {"type": "integer"},
                    "start_time": {"type": "date"},
                    "end_time": {"type": "date"},
                    "key_topics": {"type": "keyword"},
                    "created_at": {"type": "date"},
                }
            }
        }
        
        indices = [
            (self._index_name("sessions"), sessions_mapping),
            (self._index_name("messages"), messages_mapping),
            (self._index_name("summaries"), summaries_mapping),
        ]
        
        for index_name, mapping in indices:
            if not await self._client.indices.exists(index=index_name):
                await self._client.indices.create(index=index_name, body=mapping)
                self._logger.info(f"Created Elasticsearch index: {index_name}")
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new Elasticsearch session"""
        doc = {
            "session_id": metadata.session_id,
            "user_id": metadata.user_id,
            "agent_id": metadata.agent_id,
            "workflow_id": metadata.workflow_id,
            "status": metadata.status.value,
            "max_messages": metadata.max_messages,
            "max_tokens": metadata.max_tokens,
            "auto_summarize": metadata.auto_summarize,
            "summary_threshold": metadata.summary_threshold,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
            "tags": metadata.tags,
            "properties": metadata.properties,
        }
        
        await self._client.index(
            index=self._index_name("sessions"),
            id=metadata.session_id,
            document=doc,
            refresh=True
        )
        
        session = ElasticsearchSession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get session from Elasticsearch"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        try:
            result = await self._client.get(
                index=self._index_name("sessions"),
                id=session_id
            )
            doc = result["_source"]
        except Exception:
            return None
        
        metadata = SessionMetadata(
            session_id=doc["session_id"],
            user_id=doc.get("user_id"),
            agent_id=doc.get("agent_id"),
            workflow_id=doc.get("workflow_id"),
            status=SessionStatus(doc["status"]),
            max_messages=doc.get("max_messages", 100),
            max_tokens=doc.get("max_tokens"),
            auto_summarize=doc.get("auto_summarize", True),
            summary_threshold=doc.get("summary_threshold", 50),
            created_at=datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00")) if doc.get("expires_at") else None,
            tags=doc.get("tags", []),
            properties=doc.get("properties", {}),
        )
        
        session = ElasticsearchSession(metadata, self)
        
        # Load messages
        messages_result = await self._client.search(
            index=self._index_name("messages"),
            query={"term": {"session_id": session_id}},
            sort=[{"timestamp": "asc"}],
            size=10000
        )
        
        for hit in messages_result["hits"]["hits"]:
            msg_doc = hit["_source"]
            message = Message(
                role=MessageRole(msg_doc["role"]),
                content=msg_doc["content"],
                timestamp=datetime.fromisoformat(msg_doc["timestamp"].replace("Z", "+00:00")),
                message_id=msg_doc["message_id"],
                metadata=msg_doc.get("metadata", {}),
                token_count=msg_doc.get("token_count"),
                function_call=msg_doc.get("function_call"),
                tool_calls=msg_doc.get("tool_calls"),
            )
            session._messages.append(message)
        
        # Load latest summary
        summaries_result = await self._client.search(
            index=self._index_name("summaries"),
            query={"term": {"session_id": session_id}},
            sort=[{"created_at": "desc"}],
            size=1
        )
        
        if summaries_result["hits"]["hits"]:
            sum_doc = summaries_result["hits"]["hits"][0]["_source"]
            session._summary = ConversationSummary(
                summary_id=sum_doc["summary_id"],
                summary=sum_doc["summary"],
                message_count=sum_doc["message_count"],
                start_time=datetime.fromisoformat(sum_doc["start_time"].replace("Z", "+00:00")),
                end_time=datetime.fromisoformat(sum_doc["end_time"].replace("Z", "+00:00")),
                key_topics=sum_doc.get("key_topics", []),
                created_at=datetime.fromisoformat(sum_doc["created_at"].replace("Z", "+00:00")),
            )
        
        self._sessions[session_id] = session
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Elasticsearch"""
        try:
            # Delete messages
            await self._client.delete_by_query(
                index=self._index_name("messages"),
                query={"term": {"session_id": session_id}},
                refresh=True
            )
            
            # Delete summaries
            await self._client.delete_by_query(
                index=self._index_name("summaries"),
                query={"term": {"session_id": session_id}},
                refresh=True
            )
            
            # Delete session
            await self._client.delete(
                index=self._index_name("sessions"),
                id=session_id,
                refresh=True
            )
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions from Elasticsearch"""
        must_clauses = []
        
        if user_id:
            must_clauses.append({"term": {"user_id": user_id}})
        if status:
            must_clauses.append({"term": {"status": status.value}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        
        result = await self._client.search(
            index=self._index_name("sessions"),
            query=query,
            sort=[{"created_at": "desc"}],
            from_=offset,
            size=limit
        )
        
        sessions = []
        for hit in result["hits"]["hits"]:
            doc = hit["_source"]
            metadata = SessionMetadata(
                session_id=doc["session_id"],
                user_id=doc.get("user_id"),
                agent_id=doc.get("agent_id"),
                workflow_id=doc.get("workflow_id"),
                status=SessionStatus(doc["status"]),
                max_messages=doc.get("max_messages", 100),
                max_tokens=doc.get("max_tokens"),
                auto_summarize=doc.get("auto_summarize", True),
                summary_threshold=doc.get("summary_threshold", 50),
                created_at=datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")),
                expires_at=datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00")) if doc.get("expires_at") else None,
                tags=doc.get("tags", []),
                properties=doc.get("properties", {}),
            )
            sessions.append(metadata)
        
        return sessions
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch connection health"""
        try:
            info = await self._client.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "backend": "elasticsearch",
                "hosts": self._hosts,
                "cluster_name": info.get("cluster_name"),
                "version": info.get("version", {}).get("number"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "backend": "elasticsearch",
                "error": str(e),
            }
    
    def get_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client (for internal use)"""
        return self._client
    
    def get_index_name(self, name: str) -> str:
        """Get index name (for internal use)"""
        return self._index_name(name)


class ElasticsearchSession(BaseMemorySession):
    """Elasticsearch session implementation"""
    
    async def _persist_message(self, message: Message):
        """Persist message to Elasticsearch"""
        if isinstance(self._backend, ElasticsearchBackend):
            client = self._backend.get_client()
            
            doc = {
                "message_id": message.message_id,
                "session_id": self.session_id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "token_count": message.token_count,
                "metadata": message.metadata,
                "function_call": message.function_call,
                "tool_calls": message.tool_calls,
            }
            
            await client.index(
                index=self._backend.get_index_name("messages"),
                id=message.message_id,
                document=doc,
                refresh=True
            )
    
    async def _persist_changes(self):
        """Persist session changes to Elasticsearch"""
        if isinstance(self._backend, ElasticsearchBackend):
            client = self._backend.get_client()
            
            # Update session metadata
            doc = {
                "status": self._metadata.status.value,
                "updated_at": self._metadata.updated_at.isoformat(),
                "max_messages": self._metadata.max_messages,
                "max_tokens": self._metadata.max_tokens,
                "auto_summarize": self._metadata.auto_summarize,
                "summary_threshold": self._metadata.summary_threshold,
                "tags": self._metadata.tags,
                "properties": self._metadata.properties,
            }
            
            await client.update(
                index=self._backend.get_index_name("sessions"),
                id=self.session_id,
                doc=doc,
                refresh=True
            )
            
            # Persist summary if exists
            if self._summary:
                summary_doc = {
                    "summary_id": self._summary.summary_id,
                    "session_id": self.session_id,
                    "summary": self._summary.summary,
                    "message_count": self._summary.message_count,
                    "start_time": self._summary.start_time.isoformat(),
                    "end_time": self._summary.end_time.isoformat(),
                    "key_topics": self._summary.key_topics,
                    "created_at": self._summary.created_at.isoformat(),
                }
                
                await client.index(
                    index=self._backend.get_index_name("summaries"),
                    id=self._summary.summary_id,
                    document=summary_doc,
                    refresh=True
                )
        
        self._is_dirty = False


# PostgreSQL (asyncpg) Backend with PGVector support
# -----------------------------------------------------------------------------

class PostgresBackend(BaseMemoryBackend):
    """
    PostgreSQL backend using asyncpg.
    Supports both relational storage and vector embeddings (via pgvector).
    """

    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self._dsn = config.get("dsn") or config.get("url")
        if not self._dsn:
            # Construct DSN from parts
            user = config.get("user", "postgres")
            password = config.get("password", "")
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            database = config.get("database", "langswarm")
            self._dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        self._pool: Optional[asyncpg.Pool] = None
        self._min_size = config.get("min_size", 10)
        self._max_size = config.get("max_size", 10)
        self._schema = config.get("schema", "public")
        self._table_prefix = config.get("table_prefix", "")
        self._enable_vector = config.get("enable_vector", False)
        self._embedding_dimension = config.get("embedding_dimension", 1536)
        self._logger = logging.getLogger(__name__)

        # Embedding provider for semantic search (if enabled)
        self.embedding_provider = None
        if self._enable_vector:
            embedding_config = config.get("embedding", {})
            if embedding_config:
                 # Lazy load to avoid circular import issues or heavy loads
                 from .vector_backend import OpenAIEmbeddingProvider
                 provider_type = embedding_config.get("provider", "openai")
                 if provider_type == "openai":
                     self.embedding_provider = OpenAIEmbeddingProvider(
                         api_key=embedding_config.get("api_key"),
                         model=embedding_config.get("model", "text-embedding-3-small")
                     )
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.POSTGRES

    async def connect(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size
            )
            
            # Initialize schema
            await self._create_tables()

            self._connected = True
            self._logger.info(f"Connected to Postgres backend")
            return True
        except Exception as e:
            self._logger.error(f"Failed to connect to Postgres backend: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL"""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
            self._connected = False
            self._sessions.clear()
            self._logger.info("Disconnected from Postgres backend")
            return True
        except Exception as e:
            self._logger.error(f"Failed to disconnect: {e}")
            return False

    async def _create_tables(self):
        """Create tables and extensions"""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            # Enable vector extension if needed
            if self._enable_vector:
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                except Exception as e:
                    self._logger.warning(f"Could not create vector extension: {e}. Vector search may fail.")

            # Sessions table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._schema}.{self._table_prefix}sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    agent_id TEXT,
                    workflow_id TEXT,
                    status TEXT NOT NULL,
                    max_messages INTEGER,
                    max_tokens INTEGER,
                    auto_summarize BOOLEAN,
                    summary_threshold INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    tags JSONB,
                    properties JSONB
                )
            """)

            # Messages table
            vector_col_def = ""
            if self._enable_vector:
                vector_col_def = f", embedding vector({self._embedding_dimension})"

            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._schema}.{self._table_prefix}messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES {self._schema}.{self._table_prefix}sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    token_count INTEGER,
                    metadata JSONB,
                    function_call JSONB,
                    tool_calls JSONB
                    {vector_col_def}
                )
            """)

            # Summaries table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._schema}.{self._table_prefix}summaries (
                    summary_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES {self._schema}.{self._table_prefix}sessions(session_id) ON DELETE CASCADE,
                    summary TEXT NOT NULL,
                    message_count INTEGER,
                    start_time TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    key_topics JSONB,
                    created_at TIMESTAMP WITH TIME ZONE
                )
            """)
            
            # Indexes
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_sessions_user ON {self._schema}.{self._table_prefix}sessions(user_id)")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_messages_session ON {self._schema}.{self._table_prefix}messages(session_id)")
             # Add HNSW index for vector search if enabled
            if self._enable_vector:
                 await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_messages_embedding ON {self._schema}.{self._table_prefix}messages 
                    USING hnsw (embedding vector_cosine_ops)
                 """)


    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self._schema}.{self._table_prefix}sessions (
                    session_id, user_id, agent_id, workflow_id, status,
                    max_messages, max_tokens, auto_summarize, summary_threshold,
                    created_at, updated_at, expires_at, tags, properties
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, 
                metadata.session_id,
                metadata.user_id,
                metadata.agent_id,
                metadata.workflow_id,
                metadata.status.value,
                metadata.max_messages,
                metadata.max_tokens,
                metadata.auto_summarize,
                metadata.summary_threshold,
                metadata.created_at,
                metadata.updated_at,
                metadata.expires_at,
                json.dumps(metadata.tags),
                json.dumps(metadata.properties)
            )

        session = PostgresSession(metadata, self)
        self._sessions[metadata.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        if session_id in self._sessions:
            return self._sessions[session_id]

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self._schema}.{self._table_prefix}sessions WHERE session_id = $1", 
                session_id
            )
            
            if not row:
                return None
            
            metadata = SessionMetadata(
                session_id=row["session_id"],
                user_id=row["user_id"],
                agent_id=row["agent_id"],
                workflow_id=row["workflow_id"],
                status=SessionStatus(row["status"]),
                max_messages=row["max_messages"],
                max_tokens=row["max_tokens"],
                auto_summarize=row["auto_summarize"],
                summary_threshold=row["summary_threshold"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
                properties=json.loads(row["properties"]) if row["properties"] else {}
            )

            session = PostgresSession(metadata, self)
            
            # Load messages
            msg_rows = await conn.fetch(
                f"SELECT * FROM {self._schema}.{self._table_prefix}messages WHERE session_id = $1 ORDER BY timestamp ASC",
                session_id
            )
            
            for r in msg_rows:
                msg = Message(
                    role=MessageRole(r["role"]),
                    content=r["content"],
                    timestamp=r["timestamp"],
                    message_id=r["message_id"],
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                    token_count=r["token_count"],
                    function_call=json.loads(r["function_call"]) if r["function_call"] else None,
                    tool_calls=json.loads(r["tool_calls"]) if r["tool_calls"] else None
                )
                session._messages.append(msg)
            
            # Load summary
            sum_row = await conn.fetchrow(
                f"SELECT * FROM {self._schema}.{self._table_prefix}summaries WHERE session_id = $1",
                session_id
            )
            if sum_row:
                 session._summary = ConversationSummary(
                    summary_id=sum_row["summary_id"],
                    summary=sum_row["summary"],
                    message_count=sum_row["message_count"],
                    start_time=sum_row["start_time"],
                    end_time=sum_row["end_time"],
                    key_topics=json.loads(sum_row["key_topics"]) if sum_row["key_topics"] else [],
                    created_at=sum_row["created_at"]
                )
            
            self._sessions[session_id] = session
            return session

    async def list_sessions(self, user_id=None, status=None, limit=100, offset=0) -> List[SessionMetadata]:
        conditions = []
        args = []
        idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${idx}")
            args.append(user_id)
            idx += 1
        if status:
            conditions.append(f"status = ${idx}")
            args.append(status.value)
            idx += 1
            
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        args.append(limit)
        args.append(offset)
        
        query = f"""
            SELECT * FROM {self._schema}.{self._table_prefix}sessions 
            {where} 
            ORDER BY created_at DESC 
            LIMIT ${idx} OFFSET ${idx+1}
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [
                SessionMetadata(
                    session_id=r["session_id"],
                    user_id=r["user_id"],
                    agent_id=r["agent_id"],
                    workflow_id=r["workflow_id"],
                    status=SessionStatus(r["status"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    max_messages=r["max_messages"]
                ) for r in rows
            ]

    async def delete_session(self, session_id: str) -> bool:
        async with self._pool.acquire() as conn:
            # Cascade delete should handle messages/summaries
            await conn.execute(f"DELETE FROM {self._schema}.{self._table_prefix}sessions WHERE session_id = $1", session_id)
            if session_id in self._sessions:
                del self._sessions[session_id]
            return True

    async def search_messages(self, query: str, session_id: Optional[str] = None, limit: int = 10) -> List[Message]:
        """Vector semantic search using pgvector"""
        if not (self._enable_vector and self.embedding_provider):
            self._logger.warning("Vector search disabled or not configured. Falling back to text search.")
             # Simple TEXT ILIKE fallback could be implemented here
            return []

        # Generate embedding
        embedding = await self.embedding_provider.embed_text(query)
        embedding_str = str(embedding) # pgvector expects array literal or direct string representation usually handled by driver, or simply list of floats

        filter_clause = ""
        args = [embedding_str, limit]
        if session_id:
            filter_clause = f"AND session_id = $3"
            args.append(session_id)

        # Use cosine distance (<=>) operator
        sql = f"""
            SELECT * FROM {self._schema}.{self._table_prefix}messages
            WHERE embedding IS NOT NULL {filter_clause}
            ORDER BY embedding <=> $1
            LIMIT $2
        """
        
        async with self._pool.acquire() as conn:
            # Note: asyncpg-pgvector handling usually requires registering a specific codec
            # For simplicity assuming standard array handling or string literal if driver doesn't support it automatically
            # Usually strict asyncpg requires: await conn.set_type_codec(...)
            # We assume user has configured environment or we try to pass list of floats directly
            
            try:
                # Try passing raw list, asyncpg might handle if vector type matches
                # If not, we might need manual string formatting '[1.0, 0.5, ...]'
                # Let's try explicit string format as safe fallback
                vec_literal = f"[{','.join(map(str, embedding))}]"
                
                # Replace arg 1 with literal to avoid codec issues in this implementation without registering type
                # (A proper implementation would register the codec on connect)
                # But let's use the parameterized list first, as modern asyncpg + vector setup might work
                
                rows = await conn.fetch(sql, vec_literal, limit, *([session_id] if session_id else []))
            except Exception as e:
                self._logger.error(f"Vector search query failed: {e}")
                return []

            return [
                Message(
                    role=MessageRole(r["role"]),
                    content=r["content"],
                    timestamp=r["timestamp"],
                    message_id=r["message_id"],
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                ) for r in rows
            ]

    
class PostgresSession(BaseMemorySession):
    async def _persist_message(self, message: Message):
        if isinstance(self._backend, PostgresBackend) and self._backend._pool:
             # Calculate embedding if enabled
            embedding_val = None
            if self._backend._enable_vector and self._backend.embedding_provider:
                try:
                    embedding_list = await self._backend.embedding_provider.embed_text(message.content)
                    embedding_val = f"[{','.join(map(str, embedding_list))}]"
                except Exception as e:
                    logging.error(f"Failed to generate embedding: {e}")

            query = f"""
                INSERT INTO {self._backend._schema}.{self._backend._table_prefix}messages (
                    message_id, session_id, role, content, timestamp,
                    token_count, metadata, function_call, tool_calls
                    {", embedding" if embedding_val else ""}
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9
                    {", $10" if embedding_val else ""}
                )
            """
            
            args = [
                message.message_id,
                self.session_id,
                message.role.value,
                message.content,
                message.timestamp,
                message.token_count,
                json.dumps(message.metadata) if message.metadata else None,
                json.dumps(message.function_call) if message.function_call else None,
                json.dumps(message.tool_calls) if message.tool_calls else None
            ]
            if embedding_val:
                args.append(embedding_val)

            async with self._backend._pool.acquire() as conn:
                await conn.execute(query, *args)

    async def _persist_changes(self):
        if isinstance(self._backend, PostgresBackend) and self._backend._pool:
             async with self._backend._pool.acquire() as conn:
                 await conn.execute(f"""
                    UPDATE {self._backend._schema}.{self._backend._table_prefix}sessions
                    SET status=$1, updated_at=$2, max_messages=$3, max_tokens=$4,
                        auto_summarize=$5, summary_threshold=$6, tags=$7, properties=$8
                    WHERE session_id=$9
                 """,
                    self._metadata.status.value,
                    self._metadata.updated_at,
                    self._metadata.max_messages,
                    self._metadata.max_tokens,
                    self._metadata.auto_summarize,
                    self._metadata.summary_threshold,
                    json.dumps(self._metadata.tags),
                    json.dumps(self._metadata.properties),
                    self.session_id
                 )
                 
                 if self._summary:
                     await conn.execute(f"""
                        INSERT INTO {self._backend._schema}.{self._backend._table_prefix}summaries
                        (summary_id, session_id, summary, message_count, start_time, end_time, key_topics, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (summary_id) DO NOTHING
                     """,
                        self._summary.summary_id,
                        self.session_id,
                        self._summary.summary,
                        self._summary.message_count,
                        self._summary.start_time,
                        self._summary.end_time,
                        json.dumps(self._summary.key_topics),
                        self._summary.created_at
                     )
        self._is_dirty = False
