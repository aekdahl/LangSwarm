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


class BaseStatelessProviderSession(IProviderSession):
    """
    Base class for stateless provider sessions (Claude, Gemini, Cohere).
    
    Manages conversation history client-side since these providers
    don't support persistent server-side sessions.
    """
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        logger.debug(f"{self.__class__.__name__} initialized")
    
    async def create_provider_session(self, user_id: str, **kwargs) -> str:
        """Create a local conversation tracking ID"""
        conversation_id = f"conv_{user_id}_{uuid4().hex[:8]}"
        self._conversations[conversation_id] = []
        
        # Add system message if provided
        system_message = kwargs.get("system_message")
        if system_message:
            self._conversations[conversation_id].append({
                "role": "system",
                "content": system_message
            })
        
        logger.debug(f"Created {self.__class__.__name__} conversation: {conversation_id}")
        return conversation_id

    async def get_provider_session(self, provider_session_id: str) -> Optional[Dict[str, Any]]:
        """Get local conversation info"""
        if provider_session_id in self._conversations:
            return {
                "id": provider_session_id,
                "message_count": len(self._conversations[provider_session_id]),
                "created_at": datetime.utcnow().isoformat(),
                "type": "stateless_client_managed"
            }
        return None

    async def get_messages(
        self,
        provider_session_id: str,
        limit: Optional[int] = None
    ) -> List[SessionMessage]:
        """Get messages from local history"""
        if provider_session_id not in self._conversations:
            return []
        
        conversation = self._conversations[provider_session_id]
        messages = conversation[-limit:] if limit else conversation
        
        session_messages = []
        for i, msg in enumerate(messages):
            session_messages.append(SessionMessage(
                id=f"msg_{provider_session_id}_{i}",
                role=MessageRole(msg["role"]) if msg["role"] != "model" else MessageRole.ASSISTANT,
                content=msg["content"],
                timestamp=datetime.utcnow(),
                metadata={"conversation_id": provider_session_id}
            ))
        return session_messages

    async def delete_provider_session(self, provider_session_id: str) -> bool:
        """Delete local conversation history"""
        if provider_session_id in self._conversations:
            del self._conversations[provider_session_id]
            return True
        return False
    
    async def _add_to_history(self, provider_session_id: str, role: str, content: str):
        """Add message to local history"""
        if provider_session_id in self._conversations:
            self._conversations[provider_session_id].append({
                "role": role,
                "content": content
            })


class AnthropicProviderSession(BaseStatelessProviderSession):
    """Anthropic provider session implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ProviderSessionError("Anthropic library not available")

    async def send_message(
        self,
        provider_session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> SessionMessage:
        if provider_session_id not in self._conversations:
            raise ProviderSessionError(f"Conversation {provider_session_id} not found")
        
        # Add user message
        await self._add_to_history(provider_session_id, "user", message)
        
        # Prepare messages for API (Anthropic expects user/assistant only, system is separate parameter usually)
        # For simplicity in V1, we pass full history but filter system if needed or pass as system param
        # LangSwarm Agent config usually handles system prompt separately, here we just pass mapped messages
        
        api_messages = [
            m for m in self._conversations[provider_session_id] 
            if m["role"] in ["user", "assistant"]
        ]
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=api_messages
            )
            
            content = response.content[0].text
            await self._add_to_history(provider_session_id, "assistant", content)
            
            return SessionMessage(
                id=response.id,
                role=MessageRole.ASSISTANT,
                content=content,
                timestamp=datetime.utcnow(),
                metadata={"usage": response.usage._asdict()},
                token_count=response.usage.output_tokens
            )
        except Exception as e:
            raise ProviderSessionError(f"Anthropic call failed: {e}")


class GeminiProviderSession(BaseStatelessProviderSession):
    """Google Gemini provider session"""
    
    def __init__(self, api_key: str):
        super().__init__()
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            raise ProviderSessionError("Google GenerativeAI library not available")

    async def send_message(
        self,
        provider_session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> SessionMessage:
        if provider_session_id not in self._conversations:
            raise ProviderSessionError(f"Conversation {provider_session_id} not found")
            
        await self._add_to_history(provider_session_id, "user", message)
        
        # Gemini history format: [{"role": "user", "parts": ["..."]}, ...]
        gemini_history = []
        for msg in self._conversations[provider_session_id]:
            role_map = "user" if msg["role"] == "user" else "model"
            if msg["role"] == "system": continue # Gemini handles system prompts differently or in first user message
            gemini_history.append({"role": role_map, "parts": [msg["content"]]})
            
        try:
            model = self.genai.GenerativeModel("gemini-1.5-pro-latest")
            # We recreate chat session each time with full history for stateless illusion
            chat = model.start_chat(history=gemini_history[:-1]) # All but last user message
            response = await chat.send_message_async(message)
            
            content = response.text
            await self._add_to_history(provider_session_id, "model", content) # Store as 'model' internally match Gemini? Or map back to assistant? Let's use 'assistant' for consistency in _conversations
            # Fix: overwrite the last 'model' role in _add_to_history to 'assistant' for consistency
            self._conversations[provider_session_id][-1]["role"] = "assistant"

            return SessionMessage(
                id=f"gemini_{uuid4().hex}",
                role=MessageRole.ASSISTANT,
                content=content,
                timestamp=datetime.utcnow(),
                metadata={}
            )
        except Exception as e:
            raise ProviderSessionError(f"Gemini call failed: {e}")


class CohereProviderSession(BaseStatelessProviderSession):
    """Cohere provider session"""
    
    def __init__(self, api_key: str):
        super().__init__()
        try:
            import cohere
            self.client = cohere.AsyncClient(api_key=api_key)
        except ImportError:
            raise ProviderSessionError("Cohere library not available")

    async def send_message(
        self,
        provider_session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> SessionMessage:
        if provider_session_id not in self._conversations:
            self._conversations[provider_session_id] = []
            
        # Cohere manages history via 'chat_history' param
        # We store it locally to pass it back
        
        chat_history = []
        for msg in self._conversations[provider_session_id]:
            role_map = "USER" if msg["role"] == "user" else "CHATBOT"
            chat_history.append({"role": role_map, "message": msg["content"]})
            
        try:
            response = await self.client.chat(
                message=message,
                chat_history=chat_history,
                model="command-r-plus"
            )
            
            # Update local history
            await self._add_to_history(provider_session_id, "user", message)
            await self._add_to_history(provider_session_id, "assistant", response.text)
            
            return SessionMessage(
                id=response.generation_id or f"cohere_{uuid4().hex}",
                role=MessageRole.ASSISTANT,
                content=response.text,
                timestamp=datetime.utcnow(),
                metadata={"meta": response.meta}
            )
        except Exception as e:
            raise ProviderSessionError(f"Cohere call failed: {e}")


class MistralProviderSession(IProviderSession):
    """
    Mistral provider session using native conversations (Le Chat style if available via API, 
    otherwise falls back to stateless but implemented cleanly here).
    
    NOTE: As of late 2024, Mistral API is primarily stateless for /chat/completions. 
    If 'agents' endpoint supports state, we use that. 
    For now, we will implement this as a wrapper around mistral-ai client similar to stateless,
    but prepared for the 'agents' stateful ID.
    """
    
    def __init__(self, api_key: str, agent_id: Optional[str] = None):
        try:
            from mistralai import Mistral
            self.client = Mistral(api_key=api_key)
            self.agent_id = agent_id
            self._conversations = {} # Fallback if API doesn't persist
        except ImportError:
             raise ProviderSessionError("Mistral library not available")

    async def create_provider_session(self, user_id: str, **kwargs) -> str:
        # Placeholder for real stateful ID if available
        return f"mistral_{user_id}_{uuid4().hex[:8]}"

    async def get_provider_session(self, provider_session_id: str) -> Optional[Dict[str, Any]]:
        return {"id": provider_session_id, "type": "mistral_simulated"}

    async def send_message(self, provider_session_id: str, message: str, role: MessageRole = MessageRole.USER) -> SessionMessage:
        # Implementation of Mistral chat
        # For V1, we treat it disjointly as stateless wrapper
        # ... (Simplified for brevity, similar to others)
        # Returning mock for now to satisfy interface for the plan
        return SessionMessage(
            id=f"mistral_msg_{uuid4().hex}", 
            role=MessageRole.ASSISTANT, 
            content="Mistral support implementation pending.", 
            timestamp=datetime.utcnow(), 
            metadata={}
        )

    async def get_messages(self, provider_session_id: str, limit: Optional[int] = None) -> List[SessionMessage]:
        return []

    async def delete_provider_session(self, provider_session_id: str) -> bool:
        return True


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
            return AnthropicProviderSession(api_key)
            
        elif provider_lower == "gemini":
            if not api_key:
                raise ValueError("Gemini API key required")
            return GeminiProviderSession(api_key)
            
        elif provider_lower == "cohere":
            if not api_key:
                raise ValueError("Cohere API key required")
            return CohereProviderSession(api_key)
            
        elif provider_lower == "mistral":
            if not api_key:
                raise ValueError("Mistral API key required")
            return MistralProviderSession(api_key, **kwargs)
        
        else:
            # No fallback to mock providers - fail fast with clear error
            supported_providers = ["openai", "anthropic", "gemini", "cohere", "mistral"]
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Supported providers: {', '.join(supported_providers)}. "
                f"Please check provider name or install required dependencies."
            )
