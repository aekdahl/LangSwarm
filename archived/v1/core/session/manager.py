"""
LangSwarm Session Manager
=========================

Main session management class that coordinates all session functionality
including native thread IDs, provider adapters, and intelligent session strategies.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import uuid4

from .models import (
    LangSwarmSession, 
    SessionMetadata, 
    ConversationMessage, 
    MessageRole,
    SessionControl,
    SessionStatus
)
from .strategies import SessionStrategy, SessionStrategyFactory
from .adapters import BaseSessionAdapter, SessionAdapterFactory
from .storage import SessionStorage, get_session_storage


logger = logging.getLogger(__name__)


class LangSwarmSessionManager:
    """
    Main session manager for unified conversation management
    
    Coordinates session strategies, provider adapters, and storage to provide
    seamless session management across all LLM providers with native ID support.
    """
    
    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        default_session_control: SessionControl = SessionControl.HYBRID
    ):
        """
        Initialize the session manager
        
        Args:
            storage: Session storage backend (uses default if None)
            default_session_control: Default session control strategy
        """
        self.storage = storage or get_session_storage()
        self.default_session_control = default_session_control
        
        # Cache for session strategies and adapters
        self._strategy_cache: Dict[SessionControl, SessionStrategy] = {}
        self._adapter_cache: Dict[Tuple[str, str], BaseSessionAdapter] = {}
        
        # Active sessions in memory for quick access
        self._active_sessions: Dict[str, LangSwarmSession] = {}
        
        logger.info("LangSwarm Session Manager initialized")
    
    def create_session(
        self,
        user_id: str,
        provider: str = "openai",
        model: str = "gpt-4o",
        session_id: Optional[str] = None,
        session_control: Optional[SessionControl] = None,
        **kwargs
    ) -> LangSwarmSession:
        """
        Create a new session
        
        Args:
            user_id: Unique user identifier
            provider: LLM provider name
            model: Model name
            session_id: Optional custom session ID
            session_control: Session control strategy
            **kwargs: Additional session configuration
        
        Returns:
            LangSwarmSession: The created session
        """
        # Use default session control if not specified
        if session_control is None:
            session_control = SessionStrategyFactory.get_recommended_strategy(provider, model)
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = f"session_{uuid4().hex[:8]}"
        
        # Create session
        session = LangSwarmSession(
            user_id=user_id,
            session_id=session_id,
            provider=provider,
            model=model,
            session_control=session_control,
            **kwargs
        )
        
        # Get strategy and adapter
        strategy = self._get_strategy(session_control)
        adapter = self._get_adapter(provider, model)
        
        # Set references
        session._strategy = strategy
        session._adapter = adapter
        session._manager = self
        
        # Initialize provider-specific session if needed
        if strategy.should_use_native_sessions(provider, model):
            try:
                session_params = adapter.create_session(session)
                logger.info(f"Created native session for {provider}/{model}: {session_params}")
            except Exception as e:
                logger.warning(f"Failed to create native session, falling back to client-side: {e}")
                session.metadata.session_control = SessionControl.LANGSWARM
                session._strategy = self._get_strategy(SessionControl.LANGSWARM)
        
        # Save to storage
        self.storage.save_session(session)
        
        # Add to active sessions
        self._active_sessions[session_id] = session
        
        logger.info(f"Created session {session_id} for user {user_id} ({provider}/{model})")
        return session
    
    def get_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """
        Get an existing session
        
        Args:
            session_id: Session identifier
        
        Returns:
            LangSwarmSession or None if not found
        """
        # Check active sessions first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Load from storage
        session = self.storage.load_session(session_id)
        if session:
            # Restore strategy and adapter references
            strategy = self._get_strategy(session.metadata.session_control)
            adapter = self._get_adapter(session.provider, session.model)
            
            session._strategy = strategy
            session._adapter = adapter
            session._manager = self
            
            # Only add to active sessions if the session is actually active
            if session.metadata.status == SessionStatus.ACTIVE:
                self._active_sessions[session_id] = session
            
            logger.debug(f"Loaded session {session_id} from storage")
        
        return session
    
    def add_message_to_session(
        self,
        session_id: str,
        content: str,
        role: MessageRole,
        **kwargs
    ) -> Optional[ConversationMessage]:
        """
        Add a message to session (for compatibility with hybrid session manager)
        
        Args:
            session_id: Session identifier
            content: Message content
            role: Message role
            **kwargs: Additional message parameters
        
        Returns:
            ConversationMessage or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Add message to session
        message = session.add_message(content, role, **kwargs)
        
        # Save updated session
        self.storage.save_session(session)
        
        return message
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[SessionMetadata]:
        """
        List sessions with optional filtering
        
        Args:
            user_id: Filter by user ID
            status: Filter by session status
            limit: Maximum number of sessions to return
        
        Returns:
            List of session metadata
        """
        return self.storage.list_sessions(user_id, status, limit)
    
    def send_message(
        self,
        session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> ConversationMessage:
        """
        Send a message in a session
        
        Args:
            session_id: Session identifier
            message: Message content
            role: Message role (default: USER)
        
        Returns:
            ConversationMessage: The response message
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Add user message to session
        user_message = session.add_message(message, role)
        
        # Get strategy and adapter
        strategy = session._strategy
        adapter = session._adapter
        
        # Prepare request using adapter
        request_params = adapter.prepare_request(session, message)
        
        # Here you would make the actual API call to the provider
        # For now, we'll simulate a response
        mock_response = self._simulate_provider_response(session, request_params)
        
        # Process response using adapter
        assistant_message = adapter.process_response(session, mock_response)
        
        # Add assistant message to session
        session.history.add_message(assistant_message)
        
        # Update session metadata from response
        adapter.update_session_from_response(session, mock_response)
        
        # Save session
        self.storage.save_session(session)
        
        logger.info(f"Processed message in session {session_id}")
        return assistant_message
    
    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: Success status
        """
        session = self.get_session(session_id)
        if session:
            session.archive()
            success = self.storage.save_session(session)
            
            # Remove from active sessions after archival
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            
            logger.info(f"Archived session {session_id}")
            return success
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: Success status
        """
        success = self.storage.delete_session(session_id)
        
        # Remove from active sessions
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        if success:
            logger.info(f"Deleted session {session_id}")
        
        return success
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """
        Clean up expired sessions
        
        Args:
            max_age_days: Maximum age in days before session is considered expired
        
        Returns:
            int: Number of sessions cleaned up
        """
        count = self.storage.cleanup_expired_sessions(max_age_days)
        
        # Remove any expired sessions from active cache
        expired_sessions = []
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        
        for session_id, session in self._active_sessions.items():
            if session.metadata.updated_at.timestamp() < cutoff:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._active_sessions[session_id]
        
        logger.info(f"Cleaned up {count} expired sessions")
        return count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get session management statistics
        
        Returns:
            Dictionary with statistics
        """
        active_sessions = len(self._active_sessions)
        
        # Get provider distribution
        provider_stats = {}
        strategy_stats = {}
        
        for session in self._active_sessions.values():
            provider = session.provider
            strategy = session.metadata.session_control.value
            
            provider_stats[provider] = provider_stats.get(provider, 0) + 1
            strategy_stats[strategy] = strategy_stats.get(strategy, 0) + 1
        
        return {
            "active_sessions": active_sessions,
            "provider_distribution": provider_stats,
            "strategy_distribution": strategy_stats,
            "supported_providers": SessionAdapterFactory.get_supported_providers(),
            "cache_sizes": {
                "strategies": len(self._strategy_cache),
                "adapters": len(self._adapter_cache)
            }
        }
    
    def analyze_provider_capabilities(self, provider: str) -> Dict[str, Any]:
        """
        Analyze provider session management capabilities
        
        Args:
            provider: Provider name
        
        Returns:
            Dictionary with capability analysis
        """
        return SessionStrategyFactory.analyze_provider_capabilities(provider)
    
    def _get_strategy(self, control: SessionControl) -> SessionStrategy:
        """Get or create a session strategy"""
        if control not in self._strategy_cache:
            self._strategy_cache[control] = SessionStrategyFactory.create_strategy(control)
        return self._strategy_cache[control]
    
    def _get_adapter(self, provider: str, model: str) -> BaseSessionAdapter:
        """Get or create a session adapter"""
        key = (provider.lower(), model)
        if key not in self._adapter_cache:
            self._adapter_cache[key] = SessionAdapterFactory.create_adapter(provider, model)
        return self._adapter_cache[key]
    
    def _simulate_provider_response(self, session: LangSwarmSession, request_params: Dict[str, Any]) -> Any:
        """
        Simulate provider response for demonstration
        
        In real implementation, this would make actual API calls to providers.
        """
        class MockResponse:
            def __init__(self, provider: str):
                self.id = f"mock_{uuid4().hex[:8]}"
                self.provider = provider
                
                if provider == "openai":
                    self.choices = [MockChoice()]
                    self.usage = MockUsage()
                elif provider == "claude":
                    self.content = [MockContent()]
                    self.usage = MockUsage()
                elif provider == "gemini":
                    self.candidates = [MockCandidate()]
                elif provider == "mistral":
                    self.choices = [MockChoice()]
                    self.usage = MockUsage()
                elif provider == "cohere":
                    self.text = "This is a mock response from Cohere."
                    self.generation_id = self.id
        
        class MockChoice:
            def __init__(self):
                self.message = MockMessage()
        
        class MockMessage:
            def __init__(self):
                self.content = "This is a mock response from the assistant."
                self.tool_calls = None
        
        class MockContent:
            def __init__(self):
                self.text = "This is a mock response from Claude."
        
        class MockCandidate:
            def __init__(self):
                self.content = MockGeminiContent()
        
        class MockGeminiContent:
            def __init__(self):
                self.parts = [MockGeminiPart()]
        
        class MockGeminiPart:
            def __init__(self):
                self.text = "This is a mock response from Gemini."
        
        class MockUsage:
            def __init__(self):
                self.total_tokens = 50
                self.input_tokens = 20
                self.output_tokens = 30
        
        return MockResponse(session.provider)


# Global session manager instance
_default_manager: Optional[LangSwarmSessionManager] = None


def get_session_manager() -> LangSwarmSessionManager:
    """Get the global session manager instance"""
    global _default_manager
    if _default_manager is None:
        _default_manager = LangSwarmSessionManager()
    return _default_manager


def set_session_manager(manager: LangSwarmSessionManager) -> None:
    """Set the global session manager instance"""
    global _default_manager
    _default_manager = manager 