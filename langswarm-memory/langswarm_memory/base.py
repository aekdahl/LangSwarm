"""
Base Memory Implementations for AgentMem

Provides base classes and core functionality for the unified memory system.
Includes session management, conversation handling, and provider integration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import asdict

from .interfaces import (
    IMemorySession, IMemoryBackend, IMemoryManager,
    Message, MessageRole, SessionMetadata, SessionStatus,
    ConversationSummary, MemoryUsage, MemoryBackendType,
    MemoryConfig, MemoryEvent, ProgressCallback
)


class BaseMemorySession(IMemorySession):
    """
    Base implementation of memory session with common functionality.
    
    Provides core session management, message handling, and conversation
    summarization that can be extended by specific backend implementations.
    """
    
    def __init__(self, metadata: SessionMetadata, backend: IMemoryBackend):
        self._metadata = metadata
        self._backend = backend
        self._messages: List[Message] = []
        self._summary: Optional[ConversationSummary] = None
        self._is_dirty = False
        self._logger = logging.getLogger(__name__)
    
    @property
    def session_id(self) -> str:
        return self._metadata.session_id
    
    @property
    def metadata(self) -> SessionMetadata:
        return self._metadata
    
    async def add_message(self, message: Message) -> bool:
        """Add a message to the session"""
        try:
            # Update metadata timestamp
            self._metadata.update_timestamp()
            
            # Add message to internal list
            self._messages.append(message)
            self._is_dirty = True
            
            # Check if we need to create a summary
            if (self._metadata.auto_summarize and 
                len(self._messages) >= self._metadata.summary_threshold and 
                not self._summary):
                await self.create_summary()
            
            # Check message limit
            if len(self._messages) > self._metadata.max_messages:
                await self._trim_messages()
            
            # Persist message if backend supports it
            await self._persist_message(message)
            
            self._logger.debug(f"Added message to session {self.session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to add message to session {self.session_id}: {e}")
            return False
    
    async def get_messages(
        self,
        limit: Optional[int] = None,
        include_system: bool = True,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from the session"""
        messages = self._messages.copy()
        
        # Filter by role
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        # Filter by timestamp
        if since:
            messages = [m for m in messages if m.timestamp >= since]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    async def get_recent_context(self, max_tokens: Optional[int] = None) -> List[Message]:
        """Get recent messages that fit within token limit"""
        if not max_tokens:
            # Return recent messages without token limit
            return await self.get_messages(limit=10)
        
        messages = []
        total_tokens = 0
        
        # Work backwards from most recent messages
        for message in reversed(self._messages):
            message_tokens = message.token_count or len(message.content.split())
            
            if total_tokens + message_tokens <= max_tokens:
                messages.insert(0, message)
                total_tokens += message_tokens
            else:
                break
        
        return messages
    
    async def clear_messages(self, keep_system: bool = True) -> bool:
        """Clear messages from session"""
        try:
            if keep_system:
                # Keep only system messages
                self._messages = [m for m in self._messages if m.role == MessageRole.SYSTEM]
            else:
                self._messages = []
            
            self._is_dirty = True
            self._metadata.update_timestamp()
            
            # Clear summary if all messages are cleared
            if not keep_system:
                self._summary = None
            
            await self._persist_changes()
            
            self._logger.debug(f"Cleared messages from session {self.session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to clear messages from session {self.session_id}: {e}")
            return False
    
    async def get_summary(self) -> Optional[ConversationSummary]:
        """Get conversation summary if available"""
        return self._summary
    
    async def create_summary(self, force: bool = False) -> Optional[ConversationSummary]:
        """Create conversation summary"""
        if not force and self._summary:
            return self._summary
        
        if len(self._messages) < 5:  # Need minimum messages for summary
            return None
        
        try:
            # Simple summary creation (in production, use LLM)
            user_messages = [m for m in self._messages if m.role == MessageRole.USER]
            assistant_messages = [m for m in self._messages if m.role == MessageRole.ASSISTANT]
            
            if not user_messages or not assistant_messages:
                return None
            
            summary_text = f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses."
            
            # Extract topics (simple keyword extraction)
            all_content = " ".join([m.content for m in self._messages])
            words = all_content.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only longer words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top 5 most frequent words as topics
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            key_topics = [word for word, _ in top_words]
            
            self._summary = ConversationSummary(
                summary=summary_text,
                message_count=len(self._messages),
                start_time=self._messages[0].timestamp,
                end_time=self._messages[-1].timestamp,
                key_topics=key_topics
            )
            
            self._is_dirty = True
            await self._persist_changes()
            
            self._logger.debug(f"Created summary for session {self.session_id}")
            return self._summary
            
        except Exception as e:
            self._logger.error(f"Failed to create summary for session {self.session_id}: {e}")
            return None
    
    async def update_metadata(self, **kwargs) -> bool:
        """Update session metadata"""
        try:
            for key, value in kwargs.items():
                if hasattr(self._metadata, key):
                    setattr(self._metadata, key, value)
            
            self._metadata.update_timestamp()
            self._is_dirty = True
            
            await self._persist_changes()
            
            self._logger.debug(f"Updated metadata for session {self.session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to update metadata for session {self.session_id}: {e}")
            return False
    
    async def close(self) -> bool:
        """Close the session"""
        try:
            # Update status and persist final state
            self._metadata.status = SessionStatus.COMPLETED
            self._metadata.update_timestamp()
            
            await self._persist_changes()
            
            self._logger.debug(f"Closed session {self.session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to close session {self.session_id}: {e}")
            return False
    
    async def _trim_messages(self):
        """Trim messages to stay within limits"""
        if len(self._messages) <= self._metadata.max_messages:
            return
        
        # Keep system messages and recent messages
        system_messages = [m for m in self._messages if m.role == MessageRole.SYSTEM]
        other_messages = [m for m in self._messages if m.role != MessageRole.SYSTEM]
        
        # Keep recent messages up to limit
        keep_count = self._metadata.max_messages - len(system_messages)
        if keep_count > 0:
            other_messages = other_messages[-keep_count:]
        else:
            other_messages = []
        
        self._messages = system_messages + other_messages
        self._is_dirty = True
    
    async def _persist_message(self, message: Message):
        """Persist individual message (override in backend implementations)"""
        pass
    
    async def _persist_changes(self):
        """Persist session changes (override in backend implementations)"""
        if self._is_dirty:
            self._is_dirty = False


class BaseMemoryBackend(IMemoryBackend):
    """
    Base implementation of memory backend with common functionality.
    
    Provides core backend operations that can be extended by specific
    backend implementations (SQLite, Redis, etc.).
    """
    
    def __init__(self, config: MemoryConfig):
        self._config = config
        self._connected = False
        self._sessions: Dict[str, IMemorySession] = {}
        self._logger = logging.getLogger(__name__)
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.IN_MEMORY  # Override in subclasses
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def connect(self) -> bool:
        """Connect to the memory backend"""
        try:
            # Base implementation - just mark as connected
            self._connected = True
            self._logger.info(f"Connected to {self.backend_type.value} memory backend")
            return True
        except Exception as e:
            self._logger.error(f"Failed to connect to memory backend: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the memory backend"""
        try:
            # Persist any pending changes
            for session in self._sessions.values():
                if hasattr(session, '_persist_changes'):
                    await session._persist_changes()
            
            self._connected = False
            self._sessions.clear()
            
            self._logger.info(f"Disconnected from {self.backend_type.value} memory backend")
            return True
        except Exception as e:
            self._logger.error(f"Failed to disconnect from memory backend: {e}")
            return False
    
    async def create_session(self, metadata: SessionMetadata) -> IMemorySession:
        """Create a new memory session"""
        if not self._connected:
            await self.connect()
        
        session = BaseMemorySession(metadata, self)
        self._sessions[metadata.session_id] = session
        
        self._logger.debug(f"Created session {metadata.session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get an existing memory session"""
        return self._sessions.get(session_id)
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List sessions with filtering"""
        sessions = []
        
        for session in self._sessions.values():
            metadata = session.metadata
            
            # Apply filters
            if user_id and metadata.user_id != user_id:
                continue
            if status and metadata.status != status:
                continue
            
            sessions.append(metadata)
        
        # Sort by created_at descending
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return sessions[offset:offset + limit]
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its data"""
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            self._logger.debug(f"Deleted session {session_id}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_sessions = []
        current_time = datetime.now(timezone.utc)
        
        for session_id, session in self._sessions.items():
            metadata = session.metadata
            if metadata.expires_at and current_time > metadata.expires_at:
                expired_sessions.append(session_id)
        
        # Delete expired sessions
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        self._logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)
    
    async def get_usage_stats(self) -> MemoryUsage:
        """Get memory usage statistics"""
        total_messages = 0
        total_tokens = 0
        active_sessions = 0
        
        for session in self._sessions.values():
            messages = await session.get_messages()
            total_messages += len(messages)
            
            for message in messages:
                if message.token_count:
                    total_tokens += message.token_count
            
            if session.metadata.status == SessionStatus.ACTIVE:
                active_sessions += 1
        
        return MemoryUsage(
            session_count=len(self._sessions),
            message_count=total_messages,
            total_tokens=total_tokens,
            active_sessions=active_sessions,
            last_cleanup=datetime.now(timezone.utc)
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Get backend health status"""
        return {
            "status": "healthy" if self._connected else "disconnected",
            "backend_type": self.backend_type.value,
            "session_count": len(self._sessions),
            "connected": self._connected,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class MemoryManager(IMemoryManager):
    """
    Unified memory manager that provides a consistent interface across
    all memory backends and handles session lifecycle management.
    """
    
    def __init__(self, backend: IMemoryBackend):
        self._backend = backend
        self._logger = logging.getLogger(__name__)
        self._session_cache: Dict[str, IMemorySession] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @property
    def backend(self) -> IMemoryBackend:
        return self._backend
    
    async def start(self):
        """Start the memory manager"""
        if not self._backend.is_connected:
            await self._backend.connect()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self._logger.info("Memory manager started")
    
    async def stop(self):
        """Stop the memory manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self._backend.disconnect()
        self._session_cache.clear()
        
        self._logger.info("Memory manager stopped")
    
    async def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> IMemorySession:
        """Create a new memory session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = SessionMetadata(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            **kwargs
        )
        
        # Create session through backend
        session = await self._backend.create_session(metadata)
        
        # Cache the session
        self._session_cache[session_id] = session
        
        self._logger.debug(f"Created session {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[IMemorySession]:
        """Get or restore a memory session"""
        # Check cache first
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        
        # Try to get from backend
        session = await self._backend.get_session(session_id)
        if session:
            self._session_cache[session_id] = session
        
        return session
    
    async def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> IMemorySession:
        """Get existing session or create new one"""
        session = await self.get_session(session_id)
        
        if not session:
            session = await self.create_session(
                session_id=session_id,
                user_id=user_id,
                agent_id=agent_id,
                **kwargs
            )
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        # Remove from cache
        if session_id in self._session_cache:
            del self._session_cache[session_id]
        
        # Delete from backend
        return await self._backend.delete_session(session_id)
    
    async def list_user_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: int = 50
    ) -> List[SessionMetadata]:
        """List sessions for a user"""
        return await self._backend.list_sessions(
            user_id=user_id,
            status=status,
            limit=limit
        )
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        # Clean up expired sessions from cache
        expired_session_ids = []
        for session_id, session in self._session_cache.items():
            if session.metadata.is_expired():
                expired_session_ids.append(session_id)
        
        for session_id in expired_session_ids:
            del self._session_cache[session_id]
        
        # Clean up from backend
        return await self._backend.cleanup_expired_sessions()
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system memory statistics"""
        usage = await self._backend.get_usage_stats()
        health = await self._backend.health_check()
        
        return {
            "usage": asdict(usage),
            "health": health,
            "cached_sessions": len(self._session_cache),
            "backend_type": self._backend.backend_type.value
        }
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> Optional[MemoryManager]:
    """Get the global memory manager instance"""
    return _memory_manager


def set_memory_manager(manager: MemoryManager):
    """Set the global memory manager instance"""
    global _memory_manager
    _memory_manager = manager


# Convenience functions
async def create_session(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    **kwargs
) -> Optional[IMemorySession]:
    """Create a memory session using the global manager"""
    manager = get_memory_manager()
    if manager:
        return await manager.create_session(session_id, user_id, agent_id, **kwargs)
    return None


async def get_session(session_id: str) -> Optional[IMemorySession]:
    """Get a memory session using the global manager"""
    manager = get_memory_manager()
    if manager:
        return await manager.get_session(session_id)
    return None
