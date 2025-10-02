"""
LangSwarm V2 Session Base Implementation

Core session implementation that provides a clean, provider-aligned session
management system focusing on simplicity and native provider capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from .interfaces import (
    ISession, ISessionManager, ISessionStorage, IProviderSession,
    ISessionLifecycleHook, ISessionMiddleware,
    SessionStatus, MessageRole, SessionBackend,
    SessionMessage, SessionContext, SessionMetrics,
    SessionError, SessionNotFoundError, ProviderSessionError
)
from langswarm.core.errors import handle_error


logger = logging.getLogger(__name__)


class BaseSession(ISession):
    """
    Base session implementation aligned with provider patterns.
    
    Provides a clean interface that leverages provider-native session
    capabilities while maintaining a unified abstraction.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        context: SessionContext,
        storage: Optional[ISessionStorage] = None,
        provider_session: Optional[IProviderSession] = None
    ):
        """
        Initialize session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            context: Session context
            storage: Storage backend
            provider_session: Provider-specific session handler
        """
        self._session_id = session_id
        self._user_id = user_id
        self._context = context
        self._storage = storage
        self._provider_session = provider_session
        
        # Session state
        self._status = SessionStatus.ACTIVE
        self._messages: List[SessionMessage] = []
        self._metrics = SessionMetrics()
        
        # Middleware and hooks
        self._middleware: List[ISessionMiddleware] = []
        self._lifecycle_hooks: List[ISessionLifecycleHook] = []
        
        self._logger = logging.getLogger(f"session.{session_id}")
        self._logger.debug(f"Session initialized: {session_id} for user {user_id}")
    
    @property
    def session_id(self) -> str:
        """Get session ID"""
        return self._session_id
    
    @property
    def user_id(self) -> str:
        """Get user ID"""
        return self._user_id
    
    @property
    def status(self) -> SessionStatus:
        """Get session status"""
        return self._status
    
    @property
    def context(self) -> SessionContext:
        """Get session context"""
        return self._context
    
    @property
    def metrics(self) -> SessionMetrics:
        """Get session metrics"""
        return self._metrics
    
    async def send_message(
        self,
        content: str,
        role: MessageRole = MessageRole.USER,
        **kwargs
    ) -> SessionMessage:
        """
        Send a message in this session.
        
        Args:
            content: Message content
            role: Message role
            **kwargs: Additional message parameters
            
        Returns:
            SessionMessage with response
        """
        try:
            # Create outgoing message
            message = SessionMessage(
                id=f"msg_{uuid4().hex[:8]}",
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=kwargs
            )
            
            # Process through middleware
            for middleware in self._middleware:
                message = await middleware.process_outgoing_message(self, message)
            
            # Send through provider or add to local messages
            if self._provider_session and self._context.backend == SessionBackend.PROVIDER_NATIVE:
                response_message = await self._send_via_provider(message)
            else:
                response_message = await self._send_local(message)
            
            # Update metrics
            self._metrics.message_count += 1
            self._metrics.last_activity = datetime.utcnow()
            if message.token_count:
                self._metrics.total_tokens += message.token_count
            
            # Call lifecycle hooks
            for hook in self._lifecycle_hooks:
                await hook.on_message_sent(self, message)
                if response_message != message:
                    await hook.on_message_received(self, response_message)
            
            # Save to storage if enabled
            if self._storage and self._context.persist_messages:
                await self._storage.save_session(self._session_id, self._messages, self._context)
            
            return response_message
            
        except Exception as e:
            self._logger.error(f"Failed to send message: {e}")
            handle_error(e, "session_send_message")
            raise ProviderSessionError(f"Failed to send message: {e}") from e
    
    async def get_messages(self, limit: Optional[int] = None) -> List[SessionMessage]:
        """
        Get messages from this session.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of session messages
        """
        try:
            # Get from provider if using native session
            if self._provider_session and self._context.backend == SessionBackend.PROVIDER_NATIVE:
                messages = await self._provider_session.get_messages(
                    self._context.provider_session_id,
                    limit=limit
                )
                # Update local cache
                self._messages = messages
                return messages
            
            # Return local messages
            if limit:
                return self._messages[-limit:]
            return self._messages.copy()
            
        except Exception as e:
            self._logger.error(f"Failed to get messages: {e}")
            handle_error(e, "session_get_messages")
            return self._messages.copy()  # Fallback to local cache
    
    async def add_system_message(self, content: str) -> SessionMessage:
        """
        Add a system message.
        
        Args:
            content: System message content
            
        Returns:
            Created system message
        """
        return await self.send_message(content, MessageRole.SYSTEM)
    
    async def clear_messages(self) -> bool:
        """
        Clear session messages.
        
        Returns:
            True if successful
        """
        try:
            # Clear provider session if using native
            if self._provider_session and self._context.backend == SessionBackend.PROVIDER_NATIVE:
                # Most providers don't support clearing, so we archive and create new
                await self.archive()
                return True
            
            # Clear local messages
            self._messages.clear()
            self._metrics.message_count = 0
            
            # Save cleared state
            if self._storage and self._context.persist_messages:
                await self._storage.save_session(self._session_id, self._messages, self._context)
            
            self._logger.debug(f"Cleared messages for session {self._session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to clear messages: {e}")
            handle_error(e, "session_clear_messages")
            return False
    
    async def update_context(self, **kwargs) -> bool:
        """
        Update session context.
        
        Args:
            **kwargs: Context updates
            
        Returns:
            True if successful
        """
        try:
            # Update context fields
            for key, value in kwargs.items():
                if hasattr(self._context, key):
                    setattr(self._context, key, value)
                else:
                    self._context.provider_context[key] = value
            
            # Save updated context
            if self._storage:
                await self._storage.save_session(self._session_id, self._messages, self._context)
            
            self._logger.debug(f"Updated context for session {self._session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to update context: {e}")
            handle_error(e, "session_update_context")
            return False
    
    async def archive(self) -> bool:
        """
        Archive this session.
        
        Returns:
            True if successful
        """
        try:
            self._status = SessionStatus.ARCHIVED
            
            # Archive provider session if using native
            if self._provider_session and self._context.backend == SessionBackend.PROVIDER_NATIVE:
                # Provider sessions typically handle archiving automatically
                pass
            
            # Save archived state
            if self._storage:
                await self._storage.save_session(self._session_id, self._messages, self._context)
            
            # Call lifecycle hooks
            for hook in self._lifecycle_hooks:
                await hook.on_session_archived(self)
            
            self._logger.info(f"Archived session {self._session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to archive session: {e}")
            handle_error(e, "session_archive")
            return False
    
    async def _send_via_provider(self, message: SessionMessage) -> SessionMessage:
        """Send message via provider session"""
        if not self._provider_session or not self._context.provider_session_id:
            raise ProviderSessionError("Provider session not available")
        
        response = await self._provider_session.send_message(
            self._context.provider_session_id,
            message.content,
            message.role
        )
        
        # Add both user message and response to local cache
        self._messages.append(message)
        self._messages.append(response)
        
        # Trim messages if over limit
        if len(self._messages) > self._context.max_messages:
            excess = len(self._messages) - self._context.max_messages
            self._messages = self._messages[excess:]
        
        return response
    
    async def _send_local(self, message: SessionMessage) -> SessionMessage:
        """Send message locally (without provider session)"""
        # Add user message
        self._messages.append(message)
        
        # For local sessions, we don't generate responses
        # The response would come from the agent/LLM call separately
        return message
    
    def add_middleware(self, middleware: ISessionMiddleware):
        """Add session middleware"""
        self._middleware.append(middleware)
    
    def add_lifecycle_hook(self, hook: ISessionLifecycleHook):
        """Add lifecycle hook"""
        self._lifecycle_hooks.append(hook)


class SessionManager(ISessionManager):
    """
    Unified session manager with provider alignment.
    
    Manages sessions across different providers while leveraging native
    capabilities where available.
    """
    
    def __init__(
        self,
        storage: Optional[ISessionStorage] = None,
        provider_sessions: Optional[Dict[str, IProviderSession]] = None
    ):
        """
        Initialize session manager.
        
        Args:
            storage: Default storage backend
            provider_sessions: Provider session handlers
        """
        self._storage = storage
        self._provider_sessions = provider_sessions or {}
        self._active_sessions: Dict[str, BaseSession] = {}
        
        # Global middleware and hooks
        self._global_middleware: List[ISessionMiddleware] = []
        self._global_hooks: List[ISessionLifecycleHook] = []
        
        self._logger = logging.getLogger("session_manager")
        self._logger.info("Session manager initialized")
    
    async def create_session(
        self,
        user_id: str,
        provider: str,
        model: str,
        backend: SessionBackend = SessionBackend.PROVIDER_NATIVE,
        session_id: Optional[str] = None,
        **kwargs
    ) -> BaseSession:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            provider: LLM provider
            model: Model name
            backend: Session backend type
            session_id: Optional session ID
            **kwargs: Additional session configuration
            
        Returns:
            Created session
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{user_id}_{uuid4().hex[:8]}"
            
            # Create session context
            context = SessionContext(
                session_id=session_id,
                user_id=user_id,
                provider=provider,
                model=model,
                backend=backend,
                **kwargs
            )
            
            # Get provider session handler
            provider_session = self._provider_sessions.get(provider)
            
            # Create provider session if using native backend
            if backend == SessionBackend.PROVIDER_NATIVE and provider_session:
                try:
                    provider_session_id = await provider_session.create_provider_session(
                        user_id, **kwargs
                    )
                    context.provider_session_id = provider_session_id
                    self._logger.debug(f"Created provider session: {provider_session_id}")
                except Exception as e:
                    self._logger.warning(f"Failed to create provider session, falling back to local: {e}")
                    context.backend = SessionBackend.LOCAL_MEMORY
                    provider_session = None
            
            # Create session instance
            session = BaseSession(
                session_id=session_id,
                user_id=user_id,
                context=context,
                storage=self._storage,
                provider_session=provider_session
            )
            
            # Add global middleware and hooks
            for middleware in self._global_middleware:
                session.add_middleware(middleware)
            for hook in self._global_hooks:
                session.add_lifecycle_hook(hook)
            
            # Store in active sessions
            self._active_sessions[session_id] = session
            
            # Call lifecycle hooks
            for hook in self._global_hooks:
                await hook.on_session_created(session)
            
            self._logger.info(f"Created session {session_id} for user {user_id} using {backend.value}")
            return session
            
        except Exception as e:
            self._logger.error(f"Failed to create session: {e}")
            handle_error(e, "session_create")
            raise SessionError(f"Failed to create session: {e}") from e
    
    async def get_session(self, session_id: str) -> Optional[BaseSession]:
        """
        Get existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if found, None otherwise
        """
        try:
            # Check active sessions first
            if session_id in self._active_sessions:
                return self._active_sessions[session_id]
            
            # Load from storage
            if self._storage:
                session_data = await self._storage.load_session(session_id)
                if session_data:
                    messages, context = session_data
                    
                    # Get provider session handler
                    provider_session = self._provider_sessions.get(context.provider)
                    
                    # Recreate session
                    session = BaseSession(
                        session_id=session_id,
                        user_id=context.user_id,
                        context=context,
                        storage=self._storage,
                        provider_session=provider_session
                    )
                    
                    # Restore messages
                    session._messages = messages
                    
                    # Add global middleware and hooks
                    for middleware in self._global_middleware:
                        session.add_middleware(middleware)
                    for hook in self._global_hooks:
                        session.add_lifecycle_hook(hook)
                    
                    # Add to active sessions if still active
                    if session.status == SessionStatus.ACTIVE:
                        self._active_sessions[session_id] = session
                    
                    self._logger.debug(f"Loaded session {session_id} from storage")
                    return session
            
            return None
            
        except Exception as e:
            self._logger.error(f"Failed to get session {session_id}: {e}")
            handle_error(e, "session_get")
            return None
    
    async def list_user_sessions(self, user_id: str, limit: int = 100) -> List[BaseSession]:
        """
        List sessions for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions
            
        Returns:
            List of user sessions
        """
        try:
            sessions = []
            
            # Get from storage
            if self._storage:
                contexts = await self._storage.list_sessions(user_id=user_id, limit=limit)
                for context in contexts:
                    session = await self.get_session(context.session_id)
                    if session:
                        sessions.append(session)
            
            return sessions
            
        except Exception as e:
            self._logger.error(f"Failed to list sessions for user {user_id}: {e}")
            handle_error(e, "session_list_user")
            return []
    
    async def archive_session(self, session_id: str) -> bool:
        """
        Archive a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            success = await session.archive()
            
            # Remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to archive session {session_id}: {e}")
            handle_error(e, "session_archive")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            session = await self.get_session(session_id)
            
            # Remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            
            # Delete from storage
            if self._storage:
                await self._storage.delete_session(session_id)
            
            # Delete provider session if exists
            if session and session._provider_session and session.context.provider_session_id:
                await session._provider_session.delete_provider_session(
                    session.context.provider_session_id
                )
            
            # Call lifecycle hooks
            if session:
                for hook in self._global_hooks:
                    await hook.on_session_deleted(session)
            
            self._logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to delete session {session_id}: {e}")
            handle_error(e, "session_delete")
            return False
    
    def add_provider_session(self, provider: str, provider_session: IProviderSession):
        """Add provider session handler"""
        self._provider_sessions[provider] = provider_session
    
    def add_global_middleware(self, middleware: ISessionMiddleware):
        """Add global middleware"""
        self._global_middleware.append(middleware)
    
    def add_global_hook(self, hook: ISessionLifecycleHook):
        """Add global lifecycle hook"""
        self._global_hooks.append(hook)
    
    async def cleanup_inactive_sessions(self, max_inactive_hours: int = 24) -> int:
        """Clean up inactive sessions"""
        try:
            cleaned = 0
            cutoff = datetime.utcnow().timestamp() - (max_inactive_hours * 3600)
            
            # Check active sessions
            to_remove = []
            for session_id, session in self._active_sessions.items():
                if session.metrics.last_activity and session.metrics.last_activity.timestamp() < cutoff:
                    to_remove.append(session_id)
            
            # Remove inactive sessions
            for session_id in to_remove:
                await self.archive_session(session_id)
                cleaned += 1
            
            self._logger.info(f"Cleaned up {cleaned} inactive sessions")
            return cleaned
            
        except Exception as e:
            self._logger.error(f"Failed to cleanup sessions: {e}")
            handle_error(e, "session_cleanup")
            return 0
