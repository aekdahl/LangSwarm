"""
LangSwarm V2 Session Management

Modern, provider-aligned session management system that replaces the complex
V1 session system with a clean, efficient implementation leveraging native
LLM provider capabilities.

Key Features:
- Provider-native session support (OpenAI threads, Anthropic conversations)
- Simple, unified API across all providers
- Efficient storage backends (in-memory, SQLite)
- Session lifecycle management
- Message persistence and retrieval
- Metrics and analytics

Usage:
    from langswarm.core.session import SessionManager, create_session_manager
    
    # Create session manager
    manager = create_session_manager(storage="sqlite")
    
    # Create session
    session = await manager.create_session("user123", "openai", "gpt-4o")
    
    # Send message
    response = await session.send_message("Hello!")
    
    # Get conversation history
    messages = await session.get_messages()
"""

from typing import Optional, Dict, Any

# Core interfaces
from .interfaces import (
    # Main interfaces
    ISession, ISessionManager, ISessionStorage, IProviderSession,
    ISessionLifecycleHook, ISessionMiddleware,
    
    # Data structures
    SessionMessage, SessionContext, SessionMetrics,
    
    # Enums
    SessionStatus, MessageRole, SessionBackend,
    
    # Exceptions
    SessionError, SessionNotFoundError, ProviderSessionError, SessionStorageError
)

# Base implementations
from .base import (
    BaseSession, SessionManager
)

# Storage backends
from .storage import (
    InMemorySessionStorage, SQLiteSessionStorage,
    StorageFactory, get_default_storage, set_default_storage
)

# Provider sessions
from .providers import (
    OpenAIProviderSession, AnthropicProviderSession, InMemorySessionStore,
    ProviderSessionFactory
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core interfaces
    'ISession',
    'ISessionManager', 
    'ISessionStorage',
    'IProviderSession',
    'ISessionLifecycleHook',
    'ISessionMiddleware',
    
    # Data structures
    'SessionMessage',
    'SessionContext',
    'SessionMetrics',
    
    # Enums
    'SessionStatus',
    'MessageRole',
    'SessionBackend',
    
    # Exceptions
    'SessionError',
    'SessionNotFoundError',
    'ProviderSessionError',
    'SessionStorageError',
    
    # Base implementations
    'BaseSession',
    'SessionManager',
    
    # Storage backends
    'InMemorySessionStorage',
    'SQLiteSessionStorage',
    'StorageFactory',
    'get_default_storage',
    'set_default_storage',
    
    # Provider sessions
    'OpenAIProviderSession',
    'AnthropicProviderSession', 
    'InMemorySessionStore',
    'ProviderSessionFactory',
    
    # Convenience functions
    'create_session_manager',
    'create_simple_session',
    'create_provider_session'
]

# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> Optional[SessionManager]:
    """Get the global session manager instance"""
    return _global_session_manager


def set_session_manager(manager: SessionManager):
    """Set the global session manager instance"""
    global _global_session_manager
    _global_session_manager = manager


def create_session_manager(
    storage: str = "sqlite",
    storage_config: Optional[Dict[str, Any]] = None,
    providers: Optional[Dict[str, str]] = None
) -> SessionManager:
    """
    Create a session manager with specified configuration.
    
    Args:
        storage: Storage backend type ("memory", "sqlite")
        storage_config: Storage-specific configuration
        providers: Provider API keys {"openai": "sk-...", "anthropic": "sk-..."}
        
    Returns:
        Configured session manager
    """
    # Create storage backend
    storage_config = storage_config or {}
    storage_backend = StorageFactory.create_storage(storage, **storage_config)
    
    # Create provider sessions
    provider_sessions = {}
    if providers:
        for provider, api_key in providers.items():
            try:
                provider_session = ProviderSessionFactory.create_provider_session(
                    provider, api_key
                )
                provider_sessions[provider] = provider_session
            except Exception as e:
                # Log error but continue without this provider
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to create {provider} provider session: {e}")
    
    # Create session manager
    manager = SessionManager(
        storage=storage_backend,
        provider_sessions=provider_sessions
    )
    
    return manager


async def create_simple_session(
    user_id: str,
    provider: str = "mock",
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    storage: str = "memory"
) -> BaseSession:
    """
    Create a simple session for quick testing.
    
    Args:
        user_id: User identifier
        provider: LLM provider
        model: Model name
        api_key: Provider API key
        storage: Storage backend
        
    Returns:
        Created session
    """
    # Create simple manager
    providers = {provider: api_key} if api_key else {}
    manager = create_session_manager(storage=storage, providers=providers)
    
    # Create session
    session = await manager.create_session(
        user_id=user_id,
        provider=provider,
        model=model,
        backend=SessionBackend.PROVIDER_NATIVE if api_key else SessionBackend.LOCAL_MEMORY
    )
    
    return session


def create_provider_session(
    provider: str,
    api_key: str,
    **kwargs
) -> IProviderSession:
    """
    Create a provider session instance.
    
    Args:
        provider: Provider name
        api_key: Provider API key
        **kwargs: Provider-specific configuration
        
    Returns:
        Provider session instance
    """
    return ProviderSessionFactory.create_provider_session(provider, api_key, **kwargs)


# Session middleware and hooks
class LoggingMiddleware(ISessionMiddleware):
    """Simple logging middleware for sessions"""
    
    def __init__(self, logger_name: str = "session_middleware"):
        import logging
        self.logger = logging.getLogger(logger_name)
    
    async def process_outgoing_message(self, session: ISession, message: SessionMessage) -> SessionMessage:
        """Log outgoing messages"""
        self.logger.debug(f"Outgoing message in session {session.session_id}: {message.role.value}")
        return message
    
    async def process_incoming_message(self, session: ISession, message: SessionMessage) -> SessionMessage:
        """Log incoming messages"""
        self.logger.debug(f"Incoming message in session {session.session_id}: {message.role.value}")
        return message


class MetricsHook(ISessionLifecycleHook):
    """Simple metrics collection hook"""
    
    def __init__(self):
        self.session_counts = {
            "created": 0,
            "archived": 0,
            "deleted": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
    
    async def on_session_created(self, session: ISession) -> None:
        """Track session creation"""
        self.session_counts["created"] += 1
    
    async def on_message_sent(self, session: ISession, message: SessionMessage) -> None:
        """Track message sending"""
        self.session_counts["messages_sent"] += 1
    
    async def on_message_received(self, session: ISession, message: SessionMessage) -> None:
        """Track message receiving"""
        self.session_counts["messages_received"] += 1
    
    async def on_session_archived(self, session: ISession) -> None:
        """Track session archiving"""
        self.session_counts["archived"] += 1
    
    async def on_session_deleted(self, session: ISession) -> None:
        """Track session deletion"""
        self.session_counts["deleted"] += 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get collected metrics"""
        return self.session_counts.copy()


# Auto-configuration for common use cases
def configure_development_sessions() -> SessionManager:
    """Configure session manager for development"""
    manager = create_session_manager(
        storage="memory",
        providers={}  # Use mock providers by default
    )
    
    # Add development middleware and hooks
    manager.add_global_middleware(LoggingMiddleware())
    manager.add_global_hook(MetricsHook())
    
    return manager


def configure_production_sessions(
    storage_config: Optional[Dict[str, Any]] = None,
    providers: Optional[Dict[str, str]] = None
) -> SessionManager:
    """Configure session manager for production"""
    storage_config = storage_config or {"db_path": "/var/lib/langswarm/sessions.db"}
    providers = providers or {}
    
    manager = create_session_manager(
        storage="sqlite",
        storage_config=storage_config,
        providers=providers
    )
    
    # Add production middleware and hooks
    manager.add_global_hook(MetricsHook())
    
    return manager


# Initialize with development settings by default
def initialize_default_session_manager():
    """Initialize default session manager"""
    if not get_session_manager():
        manager = configure_development_sessions()
        set_session_manager(manager)


# Session context manager for convenience
class SessionContext:
    """Context manager for session operations"""
    
    def __init__(self, session: ISession):
        self.session = session
    
    async def __aenter__(self):
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Auto-save or cleanup if needed
        pass


def session_context(session: ISession) -> SessionContext:
    """Create session context manager"""
    return SessionContext(session)
