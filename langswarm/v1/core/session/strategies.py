"""
Session Management Strategies
=============================

Defines strategies for intelligent session management across providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

from .models import SessionControl, LangSwarmSession


class SessionStrategy(ABC):
    """Base class for session management strategies"""
    
    @abstractmethod
    def should_use_native_sessions(self, provider: str, model: str, **kwargs) -> bool:
        """Determine if native sessions should be used for this provider/model"""
        pass
    
    @abstractmethod
    def get_session_parameters(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Get provider-specific session parameters"""
        pass
    
    @abstractmethod
    def supports_threading(self, provider: str) -> bool:
        """Check if provider supports threading/conversation management"""
        pass


class NativeSessionStrategy(SessionStrategy):
    """Strategy that prefers native provider session management"""
    
    def should_use_native_sessions(self, provider: str, model: str, **kwargs) -> bool:
        """Always prefer native sessions when available"""
        return self.supports_threading(provider)
    
    def get_session_parameters(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Get native session parameters for the provider"""
        provider = session.provider.lower()
        params = {}
        
        if provider == "openai":
            if session.metadata.provider_thread_id:
                params["thread_id"] = session.metadata.provider_thread_id
        elif provider == "mistral":
            if session.metadata.provider_agent_id:
                params["agent_id"] = session.metadata.provider_agent_id
            if session.metadata.provider_conversation_id:
                params["conversation_id"] = session.metadata.provider_conversation_id
        
        return params
    
    def supports_threading(self, provider: str) -> bool:
        """Check native threading support by provider"""
        native_support = {
            "openai": True,      # Assistants API with threads
            "mistral": True,     # Native conversation management
            "claude": False,     # Stateless API
            "gemini": False,     # No native session management
            "cohere": False      # Stateless API
        }
        return native_support.get(provider.lower(), False)


class ClientSideSessionStrategy(SessionStrategy):
    """Strategy that uses client-side session management"""
    
    def should_use_native_sessions(self, provider: str, model: str, **kwargs) -> bool:
        """Never use native sessions, always client-side"""
        return False
    
    def get_session_parameters(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Get client-side session parameters"""
        return {
            "messages": session.get_messages_for_api(),
            "session_id": session.session_id,
            "user_id": session.user_id
        }
    
    def supports_threading(self, provider: str) -> bool:
        """Client-side supports threading for all providers"""
        return True


class HybridSessionStrategy(SessionStrategy):
    """Intelligent strategy that chooses optimal approach per provider"""
    
    def __init__(self):
        self.native_strategy = NativeSessionStrategy()
        self.client_strategy = ClientSideSessionStrategy()
        
        # Provider-specific preferences
        self.provider_preferences = {
            "openai": "native",      # Use Assistants API threads when possible
            "mistral": "native",     # Use native conversation management
            "claude": "client",      # Stateless, better with client management
            "gemini": "client",      # No native sessions available
            "cohere": "client"       # Stateless API
        }
    
    def should_use_native_sessions(self, provider: str, model: str, **kwargs) -> bool:
        """Choose based on provider capabilities and preferences"""
        provider_lower = provider.lower()
        preference = self.provider_preferences.get(provider_lower, "client")
        
        if preference == "native":
            return self.native_strategy.supports_threading(provider)
        else:
            return False
    
    def get_session_parameters(self, session: LangSwarmSession) -> Dict[str, Any]:
        """Get parameters based on chosen strategy"""
        if self.should_use_native_sessions(session.provider, session.model):
            return self.native_strategy.get_session_parameters(session)
        else:
            return self.client_strategy.get_session_parameters(session)
    
    def supports_threading(self, provider: str) -> bool:
        """Hybrid supports threading for all providers"""
        return True
    
    def get_optimal_strategy(self, provider: str, model: str) -> str:
        """Get the optimal strategy name for a provider/model"""
        if self.should_use_native_sessions(provider, model):
            return "native"
        else:
            return "client"


class SessionStrategyFactory:
    """Factory for creating session strategies"""
    
    _strategies = {
        SessionControl.NATIVE: NativeSessionStrategy,
        SessionControl.LANGSWARM: ClientSideSessionStrategy,
        SessionControl.HYBRID: HybridSessionStrategy
    }
    
    @classmethod
    def create_strategy(cls, control: SessionControl) -> SessionStrategy:
        """Create a session strategy instance"""
        strategy_class = cls._strategies.get(control)
        if not strategy_class:
            raise ValueError(f"Unknown session control: {control}")
        
        return strategy_class()
    
    @classmethod
    def get_recommended_strategy(cls, provider: str, model: str) -> SessionControl:
        """Get recommended session control for provider/model"""
        provider_lower = provider.lower()
        
        # Recommendations based on provider capabilities
        if provider_lower in ["openai", "mistral"]:
            return SessionControl.HYBRID  # Can benefit from native features
        else:
            return SessionControl.LANGSWARM  # Better with client-side management
    
    @classmethod
    def analyze_provider_capabilities(cls, provider: str) -> Dict[str, Any]:
        """Analyze provider session management capabilities"""
        provider_lower = provider.lower()
        
        capabilities = {
            "openai": {
                "native_threading": True,
                "stateful_conversations": True,
                "message_ids": True,
                "thread_branching": True,
                "recommended_strategy": "hybrid",
                "features": ["assistants_api", "thread_management", "message_persistence"]
            },
            "mistral": {
                "native_threading": True,
                "stateful_conversations": True,
                "message_ids": False,
                "thread_branching": True,
                "recommended_strategy": "hybrid",
                "features": ["agent_conversations", "conversation_branching"]
            },
            "claude": {
                "native_threading": False,
                "stateful_conversations": False,
                "message_ids": True,
                "thread_branching": False,
                "recommended_strategy": "client",
                "features": ["message_ids", "stateless_api"]
            },
            "gemini": {
                "native_threading": False,
                "stateful_conversations": False,
                "message_ids": False,
                "thread_branching": False,
                "recommended_strategy": "client",
                "features": ["stateless_api"]
            },
            "cohere": {
                "native_threading": False,
                "stateful_conversations": False,
                "message_ids": True,
                "thread_branching": False,
                "recommended_strategy": "client",
                "features": ["response_ids", "stateless_api"]
            }
        }
        
        return capabilities.get(provider_lower, {
            "native_threading": False,
            "stateful_conversations": False,
            "message_ids": False,
            "thread_branching": False,
            "recommended_strategy": "client",
            "features": ["unknown_provider"]
        }) 