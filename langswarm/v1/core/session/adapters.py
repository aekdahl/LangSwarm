"""
Provider-Specific Session Adapters
===================================

Handles provider-specific session management, including native thread IDs
and conversation management features unique to each provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .models import LangSwarmSession, ConversationMessage, MessageRole


class BaseSessionAdapter(ABC):
    """Base class for provider-specific session adapters"""
    
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
    
    @abstractmethod
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create a new session with the provider"""
        pass
    
    @abstractmethod
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare API request parameters for this provider"""
        pass
    
    @abstractmethod
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process provider response and extract session info"""
        pass
    
    @abstractmethod
    def supports_native_sessions(self) -> bool:
        """Check if this provider supports native session management"""
        pass
    
    def update_session_from_response(self, session: LangSwarmSession, response: Any) -> None:
        """Update session metadata from provider response (override if needed)"""
        pass


class OpenAISessionAdapter(BaseSessionAdapter):
    """OpenAI session adapter with Assistants API support"""
    
    def __init__(self, model: str):
        super().__init__("openai", model)
    
    def supports_native_sessions(self) -> bool:
        """OpenAI supports native sessions via Assistants API"""
        return True
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create OpenAI thread/assistant session"""
        params = {
            "model": self.model,
            "messages": session.get_messages_for_api()
        }
        
        # Use Assistants API if available
        if session.metadata.session_control.value in ["native", "hybrid"]:
            # Create thread for conversation management
            thread_params = {
                "metadata": {
                    "langswarm_session_id": session.session_id,
                    "user_id": session.user_id
                }
            }
            params["thread"] = thread_params
        
        return params
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare OpenAI request with thread support"""
        params = {
            "model": self.model,
            "messages": session.get_messages_for_api()
        }
        
        # Add thread_id if using native sessions
        if session.metadata.provider_thread_id:
            params["thread_id"] = session.metadata.provider_thread_id
        
        # Add the new message
        params["messages"].append({
            "role": "user",
            "content": message
        })
        
        return params
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process OpenAI response and extract thread information"""
        # Extract message content
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            tool_calls = getattr(response.choices[0].message, 'tool_calls', None)
        else:
            content = str(response)
            tool_calls = None
        
        # Create conversation message
        message = ConversationMessage(
            id=f"openai_{response.id if hasattr(response, 'id') else 'unknown'}",
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=[tc.model_dump() for tc in tool_calls] if tool_calls else None,
            provider_message_id=response.id if hasattr(response, 'id') else None
        )
        
        return message
    
    def update_session_from_response(self, session: LangSwarmSession, response: Any) -> None:
        """Update session with OpenAI thread information"""
        # Extract thread_id if present
        if hasattr(response, 'thread_id'):
            session.metadata.provider_thread_id = response.thread_id
        
        # Update token usage if available
        if hasattr(response, 'usage'):
            session.metadata.total_tokens += response.usage.total_tokens


class ClaudeSessionAdapter(BaseSessionAdapter):
    """Claude session adapter (stateless with message IDs)"""
    
    def __init__(self, model: str):
        super().__init__("claude", model)
    
    def supports_native_sessions(self) -> bool:
        """Claude is stateless but provides message IDs"""
        return False
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create Claude session (client-side only)"""
        return {
            "model": self.model,
            "messages": session.get_messages_for_api(),
            "max_tokens": 4096
        }
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare Claude request"""
        messages = session.get_messages_for_api()
        messages.append({
            "role": "user",
            "content": message
        })
        
        return {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096
        }
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process Claude response"""
        # Extract content
        if hasattr(response, 'content') and response.content:
            content = response.content[0].text if response.content else ""
        else:
            content = str(response)
        
        # Create message with Claude message ID
        message = ConversationMessage(
            id=f"claude_{response.id if hasattr(response, 'id') else 'unknown'}",
            role=MessageRole.ASSISTANT,
            content=content,
            provider_message_id=response.id if hasattr(response, 'id') else None
        )
        
        return message
    
    def update_session_from_response(self, session: LangSwarmSession, response: Any) -> None:
        """Update session with Claude response info"""
        # Update token usage if available
        if hasattr(response, 'usage'):
            session.metadata.total_tokens += response.usage.output_tokens + response.usage.input_tokens


class GeminiSessionAdapter(BaseSessionAdapter):
    """Gemini session adapter (stateless, client-side management)"""
    
    def __init__(self, model: str):
        super().__init__("gemini", model)
    
    def supports_native_sessions(self) -> bool:
        """Gemini doesn't support native sessions"""
        return False
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create Gemini session (client-side only)"""
        # Convert messages to Gemini format
        contents = []
        for msg in session.get_messages_for_api():
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        return {
            "model": self.model,
            "contents": contents
        }
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare Gemini request"""
        contents = []
        
        # Convert existing messages
        for msg in session.get_messages_for_api():
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        # Add new message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        return {
            "model": self.model,
            "contents": contents
        }
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process Gemini response"""
        # Extract content from Gemini response
        if hasattr(response, 'candidates') and response.candidates:
            content = response.candidates[0].content.parts[0].text
        else:
            content = str(response)
        
        message = ConversationMessage(
            id=f"gemini_{datetime.now().isoformat()}",
            role=MessageRole.ASSISTANT,
            content=content
        )
        
        return message


class MistralSessionAdapter(BaseSessionAdapter):
    """Mistral session adapter with native conversation support"""
    
    def __init__(self, model: str):
        super().__init__("mistral", model)
    
    def supports_native_sessions(self) -> bool:
        """Mistral supports native conversation management"""
        return True
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create Mistral session with agent/conversation support"""
        params = {
            "model": self.model,
            "messages": session.get_messages_for_api()
        }
        
        # Use native conversation management if available
        if session.metadata.session_control.value in ["native", "hybrid"]:
            if session.metadata.provider_agent_id:
                params["agent_id"] = session.metadata.provider_agent_id
            if session.metadata.provider_conversation_id:
                params["conversation_id"] = session.metadata.provider_conversation_id
        
        return params
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare Mistral request with conversation support"""
        params = {
            "model": self.model,
            "messages": session.get_messages_for_api()
        }
        
        # Add conversation parameters
        if session.metadata.provider_agent_id:
            params["agent_id"] = session.metadata.provider_agent_id
        if session.metadata.provider_conversation_id:
            params["conversation_id"] = session.metadata.provider_conversation_id
        
        # Add new message
        params["messages"].append({
            "role": "user",
            "content": message
        })
        
        return params
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process Mistral response"""
        # Extract content
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
        else:
            content = str(response)
        
        message = ConversationMessage(
            id=f"mistral_{response.id if hasattr(response, 'id') else 'unknown'}",
            role=MessageRole.ASSISTANT,
            content=content,
            provider_message_id=response.id if hasattr(response, 'id') else None
        )
        
        return message
    
    def update_session_from_response(self, session: LangSwarmSession, response: Any) -> None:
        """Update session with Mistral conversation info"""
        # Extract conversation metadata if present
        if hasattr(response, 'conversation_id'):
            session.metadata.provider_conversation_id = response.conversation_id
        if hasattr(response, 'agent_id'):
            session.metadata.provider_agent_id = response.agent_id
        
        # Update token usage
        if hasattr(response, 'usage'):
            session.metadata.total_tokens += response.usage.total_tokens


class CohereSessionAdapter(BaseSessionAdapter):
    """Cohere session adapter (stateless with response IDs)"""
    
    def __init__(self, model: str):
        super().__init__("cohere", model)
    
    def supports_native_sessions(self) -> bool:
        """Cohere is stateless"""
        return False
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create Cohere session (client-side only)"""
        # Cohere uses chat history format
        chat_history = []
        current_messages = session.get_messages_for_api()
        
        for i in range(0, len(current_messages) - 1, 2):
            if i + 1 < len(current_messages):
                user_msg = current_messages[i]
                bot_msg = current_messages[i + 1]
                
                chat_history.append({
                    "role": "USER",
                    "message": user_msg["content"]
                })
                chat_history.append({
                    "role": "CHATBOT",
                    "message": bot_msg["content"]
                })
        
        return {
            "model": self.model,
            "chat_history": chat_history
        }
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare Cohere request"""
        session_params = self.create_session(session)
        
        return {
            "model": self.model,
            "message": message,
            "chat_history": session_params["chat_history"]
        }
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process Cohere response"""
        # Extract content
        if hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
        
        message = ConversationMessage(
            id=f"cohere_{response.generation_id if hasattr(response, 'generation_id') else 'unknown'}",
            role=MessageRole.ASSISTANT,
            content=content,
            provider_message_id=response.generation_id if hasattr(response, 'generation_id') else None
        )
        
        return message


class TestSessionAdapter(BaseSessionAdapter):
    """Test session adapter for unit testing"""
    
    def __init__(self, model: str):
        super().__init__("test", model)
    
    def supports_native_sessions(self) -> bool:
        """Test adapter supports native sessions for testing"""
        return True
    
    def create_session(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Create test session"""
        return {
            "model": self.model,
            "messages": session.get_messages_for_api(),
            "test_session": True
        }
    
    def prepare_request(self, session: LangSwarmSession, message: str) -> Dict[str, Any]:
        """Prepare test request"""
        params = {
            "model": self.model,
            "messages": session.get_messages_for_api()
        }
        
        params["messages"].append({
            "role": "user",
            "content": message
        })
        
        return params
    
    def process_response(self, session: LangSwarmSession, response: Any) -> ConversationMessage:
        """Process test response"""
        from datetime import datetime
        
        # Mock response for testing
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = "Test response"
        
        return ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            message_id=f"test_msg_{session.history.message_count + 1}",
            session_id=session.session_id
        )


class SessionAdapterFactory:
    """Factory for creating provider-specific session adapters"""
    
    _adapters = {
        "openai": OpenAISessionAdapter,
        "gpt": OpenAISessionAdapter,  # Alias for OpenAI
        "claude": ClaudeSessionAdapter,
        "gemini": GeminiSessionAdapter,
        "mistral": MistralSessionAdapter,
        "cohere": CohereSessionAdapter,
        "test": TestSessionAdapter,   # For testing
        "none": TestSessionAdapter,   # Another alias for testing
    }
    
    @classmethod
    def create_adapter(cls, provider: str, model: str) -> BaseSessionAdapter:
        """Create a session adapter for the specified provider"""
        provider_lower = provider.lower()
        adapter_class = cls._adapters.get(provider_lower)
        
        if not adapter_class:
            raise ValueError(f"No session adapter available for provider: {provider}")
        
        return adapter_class(model)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported providers"""
        return list(cls._adapters.keys())
    
    @classmethod
    def supports_provider(cls, provider: str) -> bool:
        """Check if provider is supported"""
        return provider.lower() in cls._adapters 