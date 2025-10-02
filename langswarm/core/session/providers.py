"""
LangSwarm V2 Provider Session Implementations

Provider-specific session implementations that leverage native capabilities
like OpenAI threads, Anthropic conversations, etc.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import uuid4

from .interfaces import (
    IProviderSession, SessionMessage, MessageRole,
    ProviderSessionError
)
from langswarm.core.errors import handle_error


logger = logging.getLogger(__name__)


class OpenAIProviderSession(IProviderSession):
    """
    OpenAI provider session using native threads API.
    
    Leverages OpenAI's thread and assistant capabilities for native
    session management with built-in message persistence.
    """
    
    def __init__(self, api_key: str, assistant_id: Optional[str] = None):
        """
        Initialize OpenAI provider session.
        
        Args:
            api_key: OpenAI API key
            assistant_id: Optional assistant ID for thread conversations
        """
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
            self.assistant_id = assistant_id
            
            logger.debug("OpenAI provider session initialized")
            
        except ImportError:
            raise ProviderSessionError("OpenAI library not available. Install with: pip install openai")
    
    async def create_provider_session(self, user_id: str, **kwargs) -> str:
        """
        Create OpenAI thread for session management.
        
        Args:
            user_id: User identifier
            **kwargs: Additional thread parameters
            
        Returns:
            Thread ID
        """
        try:
            # Create thread with metadata
            thread = await self.client.beta.threads.create(
                metadata={
                    "user_id": user_id,
                    "created_by": "langswarm_v2",
                    "session_type": "conversation",
                    **kwargs.get("metadata", {})
                }
            )
            
            logger.debug(f"Created OpenAI thread: {thread.id} for user {user_id}")
            return thread.id
            
        except Exception as e:
            logger.error(f"Failed to create OpenAI thread: {e}")
            handle_error(e, "openai_create_session")
            raise ProviderSessionError(f"Failed to create OpenAI thread: {e}") from e
    
    async def get_provider_session(self, provider_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenAI thread information.
        
        Args:
            provider_session_id: Thread ID
            
        Returns:
            Thread information
        """
        try:
            thread = await self.client.beta.threads.retrieve(provider_session_id)
            
            return {
                "id": thread.id,
                "created_at": thread.created_at,
                "metadata": thread.metadata,
                "object": thread.object
            }
            
        except Exception as e:
            logger.error(f"Failed to get OpenAI thread {provider_session_id}: {e}")
            handle_error(e, "openai_get_session")
            return None
    
    async def send_message(
        self,
        provider_session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> SessionMessage:
        """
        Send message through OpenAI thread.
        
        Args:
            provider_session_id: Thread ID
            message: Message content
            role: Message role
            
        Returns:
            Response message
        """
        try:
            # Add message to thread
            thread_message = await self.client.beta.threads.messages.create(
                thread_id=provider_session_id,
                role=role.value,
                content=message
            )
            
            # If we have an assistant, run it to get response
            if self.assistant_id and role == MessageRole.USER:
                run = await self.client.beta.threads.runs.create(
                    thread_id=provider_session_id,
                    assistant_id=self.assistant_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(0.5)
                    run = await self.client.beta.threads.runs.retrieve(
                        thread_id=provider_session_id,
                        run_id=run.id
                    )
                
                if run.status == "completed":
                    # Get the latest assistant message
                    messages = await self.client.beta.threads.messages.list(
                        thread_id=provider_session_id,
                        limit=1
                    )
                    
                    if messages.data:
                        assistant_message = messages.data[0]
                        content = assistant_message.content[0].text.value if assistant_message.content else ""
                        
                        return SessionMessage(
                            id=assistant_message.id,
                            role=MessageRole.ASSISTANT,
                            content=content,
                            timestamp=datetime.fromtimestamp(assistant_message.created_at),
                            metadata={"thread_id": provider_session_id, "run_id": run.id},
                            provider_message_id=assistant_message.id
                        )
                
                elif run.status == "failed":
                    logger.error(f"OpenAI run failed: {run.last_error}")
                    raise ProviderSessionError(f"OpenAI run failed: {run.last_error}")
            
            # Return user message if no assistant or system message
            return SessionMessage(
                id=thread_message.id,
                role=role,
                content=message,
                timestamp=datetime.fromtimestamp(thread_message.created_at),
                metadata={"thread_id": provider_session_id},
                provider_message_id=thread_message.id
            )
            
        except Exception as e:
            logger.error(f"Failed to send message via OpenAI: {e}")
            handle_error(e, "openai_send_message")
            raise ProviderSessionError(f"Failed to send message via OpenAI: {e}") from e
    
    async def get_messages(
        self,
        provider_session_id: str,
        limit: Optional[int] = None
    ) -> List[SessionMessage]:
        """
        Get messages from OpenAI thread.
        
        Args:
            provider_session_id: Thread ID
            limit: Maximum messages to retrieve
            
        Returns:
            List of messages
        """
        try:
            messages = await self.client.beta.threads.messages.list(
                thread_id=provider_session_id,
                limit=limit or 100
            )
            
            session_messages = []
            for msg in reversed(messages.data):  # Reverse to get chronological order
                content = ""
                if msg.content:
                    if hasattr(msg.content[0], 'text'):
                        content = msg.content[0].text.value
                    else:
                        content = str(msg.content[0])
                
                session_message = SessionMessage(
                    id=msg.id,
                    role=MessageRole(msg.role),
                    content=content,
                    timestamp=datetime.fromtimestamp(msg.created_at),
                    metadata={"thread_id": provider_session_id},
                    provider_message_id=msg.id
                )
                session_messages.append(session_message)
            
            return session_messages
            
        except Exception as e:
            logger.error(f"Failed to get messages from OpenAI thread {provider_session_id}: {e}")
            handle_error(e, "openai_get_messages")
            return []
    
    async def delete_provider_session(self, provider_session_id: str) -> bool:
        """
        Delete OpenAI thread.
        
        Args:
            provider_session_id: Thread ID
            
        Returns:
            True if successful
        """
        try:
            await self.client.beta.threads.delete(provider_session_id)
            logger.debug(f"Deleted OpenAI thread: {provider_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete OpenAI thread {provider_session_id}: {e}")
            handle_error(e, "openai_delete_session")
            return False


class AnthropicProviderSession(IProviderSession):
    """
    Anthropic provider session with conversation management.
    
    Since Anthropic doesn't have native threads, we simulate sessions
    by maintaining conversation context.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Anthropic provider session.
        
        Args:
            api_key: Anthropic API key
        """
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
            self._conversations: Dict[str, List[Dict[str, Any]]] = {}
            
            logger.debug("Anthropic provider session initialized")
            
        except ImportError:
            raise ProviderSessionError("Anthropic library not available. Install with: pip install anthropic")
    
    async def create_provider_session(self, user_id: str, **kwargs) -> str:
        """
        Create conversation session for Anthropic.
        
        Args:
            user_id: User identifier
            **kwargs: Additional parameters
            
        Returns:
            Conversation ID
        """
        try:
            conversation_id = f"conv_{user_id}_{uuid4().hex[:8]}"
            self._conversations[conversation_id] = []
            
            # Add system message if provided
            system_message = kwargs.get("system_message")
            if system_message:
                self._conversations[conversation_id].append({
                    "role": "system",
                    "content": system_message
                })
            
            logger.debug(f"Created Anthropic conversation: {conversation_id} for user {user_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to create Anthropic conversation: {e}")
            handle_error(e, "anthropic_create_session")
            raise ProviderSessionError(f"Failed to create Anthropic conversation: {e}") from e
    
    async def get_provider_session(self, provider_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Anthropic conversation information.
        
        Args:
            provider_session_id: Conversation ID
            
        Returns:
            Conversation information
        """
        if provider_session_id in self._conversations:
            return {
                "id": provider_session_id,
                "message_count": len(self._conversations[provider_session_id]),
                "created_at": datetime.utcnow().isoformat()
            }
        return None
    
    async def send_message(
        self,
        provider_session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> SessionMessage:
        """
        Send message through Anthropic conversation.
        
        Args:
            provider_session_id: Conversation ID
            message: Message content
            role: Message role
            
        Returns:
            Response message
        """
        try:
            if provider_session_id not in self._conversations:
                raise ProviderSessionError(f"Conversation {provider_session_id} not found")
            
            conversation = self._conversations[provider_session_id]
            
            # Add user message to conversation
            if role == MessageRole.USER:
                conversation.append({"role": "user", "content": message})
                
                # Get response from Claude
                response = await self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=conversation
                )
                
                # Add assistant response to conversation
                assistant_content = response.content[0].text if response.content else ""
                conversation.append({"role": "assistant", "content": assistant_content})
                
                return SessionMessage(
                    id=f"msg_{uuid4().hex[:8]}",
                    role=MessageRole.ASSISTANT,
                    content=assistant_content,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "conversation_id": provider_session_id,
                        "model": "claude-3-5-sonnet-20241022",
                        "usage": response.usage._asdict() if response.usage else None
                    },
                    token_count=response.usage.output_tokens if response.usage else None
                )
            
            else:
                # For system or other messages, just add to conversation
                conversation.append({"role": role.value, "content": message})
                
                return SessionMessage(
                    id=f"msg_{uuid4().hex[:8]}",
                    role=role,
                    content=message,
                    timestamp=datetime.utcnow(),
                    metadata={"conversation_id": provider_session_id}
                )
            
        except Exception as e:
            logger.error(f"Failed to send message via Anthropic: {e}")
            handle_error(e, "anthropic_send_message")
            raise ProviderSessionError(f"Failed to send message via Anthropic: {e}") from e
    
    async def get_messages(
        self,
        provider_session_id: str,
        limit: Optional[int] = None
    ) -> List[SessionMessage]:
        """
        Get messages from Anthropic conversation.
        
        Args:
            provider_session_id: Conversation ID
            limit: Maximum messages to retrieve
            
        Returns:
            List of messages
        """
        try:
            if provider_session_id not in self._conversations:
                return []
            
            conversation = self._conversations[provider_session_id]
            messages = conversation[-limit:] if limit else conversation
            
            session_messages = []
            for i, msg in enumerate(messages):
                session_message = SessionMessage(
                    id=f"msg_{provider_session_id}_{i}",
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=datetime.utcnow(),  # We don't track individual timestamps
                    metadata={"conversation_id": provider_session_id}
                )
                session_messages.append(session_message)
            
            return session_messages
            
        except Exception as e:
            logger.error(f"Failed to get messages from Anthropic conversation {provider_session_id}: {e}")
            handle_error(e, "anthropic_get_messages")
            return []
    
    async def delete_provider_session(self, provider_session_id: str) -> bool:
        """
        Delete Anthropic conversation.
        
        Args:
            provider_session_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            if provider_session_id in self._conversations:
                del self._conversations[provider_session_id]
                logger.debug(f"Deleted Anthropic conversation: {provider_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Anthropic conversation {provider_session_id}: {e}")
            handle_error(e, "anthropic_delete_session")
            return False


class InMemorySessionStore:
    """
    In-memory conversation tracking and session lifecycle management.
    
    Provides core session management functionality without mock response generation.
    Useful for testing, development, and applications that need in-memory session tracking.
    """
    
    def __init__(self):
        """Initialize in-memory session store."""
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._messages: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.debug("In-memory session store initialized")
    
    async def create_session(self, user_id: str, session_type: str = "conversation", **kwargs) -> str:
        """Create a new session"""
        session_id = f"session_{user_id}_{uuid4().hex[:8]}"
        
        self._sessions[session_id] = {
            "user_id": user_id,
            "session_type": session_type,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            **kwargs
        }
        self._messages[session_id] = []
        
        logger.debug(f"Created in-memory session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self._sessions.get(session_id)
    
    async def add_message(
        self,
        session_id: str,
        message: str,
        role: str,
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a message to session"""
        if session_id not in self._sessions:
            logger.error(f"Session {session_id} not found")
            return False
        
        # Update last activity
        self._sessions[session_id]["last_activity"] = datetime.utcnow()
        
        # Add message
        message_data = {
            "id": message_id or f"msg_{uuid4().hex[:8]}",
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        self._messages[session_id].append(message_data)
        
        logger.debug(f"Added message to session {session_id}")
        return True
    
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from session"""
        if session_id not in self._messages:
            return []
        
        messages = self._messages[session_id]
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and all its messages"""
        session_deleted = self._sessions.pop(session_id, None) is not None
        messages_deleted = self._messages.pop(session_id, None) is not None
        
        if session_deleted or messages_deleted:
            logger.debug(f"Deleted in-memory session: {session_id}")
            return True
        return False
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max_age_hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = []
        
        for session_id, session_data in self._sessions.items():
            if session_data.get("last_activity", session_data["created_at"]) < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self._sessions)
    
    def get_message_count(self, session_id: Optional[str] = None) -> int:
        """Get message count for a session or total message count"""
        if session_id:
            return len(self._messages.get(session_id, []))
        return sum(len(messages) for messages in self._messages.values())


class ProviderSessionFactory:
    """Factory for creating provider sessions"""
    
    @staticmethod
    def create_provider_session(
        provider: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> IProviderSession:
        """
        Create provider session.
        
        Args:
            provider: Provider name
            api_key: API key for the provider
            **kwargs: Provider-specific configuration
            
        Returns:
            Provider session instance
        """
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required")
            return OpenAIProviderSession(api_key, **kwargs)
        
        elif provider_lower == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key required")
            return AnthropicProviderSession(api_key, **kwargs)
        
        else:
            # No fallback to mock providers - fail fast with clear error
            supported_providers = ["openai", "anthropic"]
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Supported providers: {', '.join(supported_providers)}. "
                f"Please check provider name or install required dependencies."
            )
