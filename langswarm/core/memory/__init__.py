"""
LangSwarm V2 Memory System

Unified, simplified memory management that aligns with major LLM providers
and provides a clean, consistent interface across all memory backends.

This module provides:
- Clean interfaces aligned with LLM provider patterns
- Multiple backend support (SQLite, Redis, In-Memory)
- Automatic backend selection and configuration
- Session-based conversation management
- Message history with token management
- Conversation summarization
- Memory usage analytics
- Migration support from V1 memory systems

Quick Start:
    # Development setup
    manager = create_memory_manager("development")
    
    # Production setup
    manager = create_memory_manager("production")
    
    # Custom configuration
    manager = create_memory_manager({
        "backend": "redis",
        "settings": {"url": "redis://localhost:6379"}
    })
    
    # Create a session
    session = await manager.create_session(user_id="user123")
    
    # Add messages
    await session.add_message(Message(
        role=MessageRole.USER,
        content="Hello, how are you?"
    ))
    
    # Get conversation history
    messages = await session.get_messages()
"""

from typing import List

# Core interfaces and types
from .interfaces import (
    # Enums
    MessageRole,
    SessionStatus,
    MemoryBackendType,
    
    # Data classes
    Message,
    ConversationSummary,
    SessionMetadata,
    MemoryUsage,
    
    # Interfaces
    IMemorySession,
    IMemoryBackend,
    IMemoryManager,
    IMemoryProvider,
    IMemoryMigrator,
    
    # Type aliases
    MemoryConfig,
    MemoryEvent,
    SearchQuery,
    SearchResult,
    MessageList,
    SessionList,
    MemoryCallback,
    ProgressCallback
)

# Base implementations
from .base import (
    BaseMemorySession,
    BaseMemoryBackend,
    MemoryManager,
    get_memory_manager,
    set_memory_manager,
    create_session,
    get_session
)

# Backend implementations
from .backends import (
    InMemoryBackend,
    SQLiteBackend,
    RedisBackend,
    InMemorySession,
    SQLiteSession,
    RedisSession
)

# Factory and configuration
from .factory import (
    MemoryConfiguration,
    MemoryFactory,
    create_memory_manager,
    create_memory_backend,
    setup_global_memory,
    get_global_memory_manager,
    teardown_global_memory,
    # Exception classes
    MemoryBackendError,
    MemoryConfigurationError
)

# Public API exports
__all__ = [
    # Enums
    "MessageRole",
    "SessionStatus", 
    "MemoryBackendType",
    
    # Data classes
    "Message",
    "ConversationSummary",
    "SessionMetadata",
    "MemoryUsage",
    
    # Interfaces
    "IMemorySession",
    "IMemoryBackend",
    "IMemoryManager",
    "IMemoryProvider",
    "IMemoryMigrator",
    
    # Base implementations
    "BaseMemorySession",
    "BaseMemoryBackend",
    "MemoryManager",
    
    # Backend implementations
    "InMemoryBackend",
    "SQLiteBackend",
    "RedisBackend",
    "InMemorySession",
    "SQLiteSession",
    "RedisSession",
    
    # Configuration and factory
    "MemoryConfiguration",
    "MemoryFactory",
    
    # Factory functions
    "create_memory_manager",
    "create_memory_backend",
    "setup_global_memory",
    "get_global_memory_manager",
    "teardown_global_memory",
    
    # Exception classes
    "MemoryBackendError",
    "MemoryConfigurationError",
    
    # Manager functions
    "get_memory_manager",
    "set_memory_manager",
    "create_session",
    "get_session",
    
    # Type aliases
    "MemoryConfig",
    "MemoryEvent",
    "SearchQuery",
    "SearchResult",
    "MessageList",
    "SessionList",
    "MemoryCallback",
    "ProgressCallback"
]

# Package metadata
__version__ = "2.0.0"
__author__ = "LangSwarm Team"
__description__ = "Unified memory management for LangSwarm V2"

# Global memory manager instance for convenience
_memory_manager = None

def initialize_memory(config=None):
    """
    Initialize the memory system with the given configuration.
    
    Args:
        config: Memory configuration (bool, str, dict, or MemoryConfiguration)
                Defaults to "development" if not provided
    
    Returns:
        bool: True if initialization was successful
    
    Examples:
        # Auto-select development setup
        initialize_memory()
        
        # Explicit configuration
        initialize_memory("production")
        
        # Custom configuration
        initialize_memory({
            "backend": "redis",
            "settings": {"url": "redis://localhost:6379"}
        })
    """
    global _memory_manager
    
    # Default to development if no config provided
    if config is None:
        config = "development"
    
    # Setup global memory manager
    success = setup_global_memory(config)
    if success:
        _memory_manager = get_global_memory_manager()
    
    return success

def get_memory():
    """
    Get the current memory manager instance.
    
    Returns:
        IMemoryManager or None: The memory manager instance
    """
    global _memory_manager
    if not _memory_manager:
        _memory_manager = get_global_memory_manager()
    return _memory_manager

def shutdown_memory():
    """Shutdown the memory system"""
    global _memory_manager
    teardown_global_memory()
    _memory_manager = None

# Convenience factory functions for common patterns

def create_development_memory():
    """Create a memory manager optimized for development"""
    return create_memory_manager("development")

def create_production_memory():
    """Create a memory manager optimized for production"""
    return create_memory_manager("production")

def create_testing_memory():
    """Create a memory manager optimized for testing"""
    return create_memory_manager("testing")

def create_redis_memory(url: str = "redis://localhost:6379", **kwargs):
    """
    Create a Redis-based memory manager.
    
    Args:
        url: Redis connection URL
        **kwargs: Additional Redis configuration
    """
    config = {
        "backend": "redis",
        "settings": {"url": url, **kwargs}
    }
    return create_memory_manager(config)

def create_sqlite_memory(db_path: str = "langswarm_memory.db", **kwargs):
    """
    Create a SQLite-based memory manager.
    
    Args:
        db_path: Path to SQLite database file
        **kwargs: Additional SQLite configuration
    """
    config = {
        "backend": "sqlite", 
        "settings": {"db_path": db_path, **kwargs}
    }
    return create_memory_manager(config)

def create_inmemory_memory():
    """Create an in-memory manager (for testing/development)"""
    return create_memory_manager({
        "backend": "in_memory",
        "settings": {}
    })

# Provider-specific message format helpers

def create_openai_message(role: str, content: str, **kwargs) -> Message:
    """Create a message in OpenAI format"""
    return Message(
        role=MessageRole(role),
        content=content,
        function_call=kwargs.get("function_call"),
        tool_calls=kwargs.get("tool_calls"),
        **{k: v for k, v in kwargs.items() if k not in ["function_call", "tool_calls"]}
    )

def create_anthropic_message(role: str, content: str, **kwargs) -> Message:
    """Create a message in Anthropic format"""
    # Anthropic uses "user" and "assistant" roles
    if role == "human":
        role = "user"
    elif role == "ai":
        role = "assistant"
    
    return Message(
        role=MessageRole(role),
        content=content,
        **kwargs
    )

def messages_to_openai_format(messages: List[Message]) -> List[dict]:
    """Convert messages to OpenAI API format"""
    return [msg.to_openai_format() for msg in messages]

def messages_to_anthropic_format(messages: List[Message]) -> List[dict]:
    """Convert messages to Anthropic API format"""
    return [msg.to_anthropic_format() for msg in messages]

# Async context manager for memory sessions

class MemorySessionContext:
    """
    Async context manager for memory sessions.
    
    Usage:
        async with MemorySessionContext("user123") as session:
            await session.add_message(Message(...))
            messages = await session.get_messages()
    """
    
    def __init__(self, session_id: str = None, user_id: str = None, **kwargs):
        self.session_id = session_id
        self.user_id = user_id
        self.kwargs = kwargs
        self.session = None
        self.manager = None
    
    async def __aenter__(self):
        self.manager = get_memory()
        if not self.manager:
            raise RuntimeError("Memory system not initialized. Call initialize_memory() first.")
        
        if self.session_id:
            self.session = await self.manager.get_or_create_session(
                self.session_id, self.user_id, **self.kwargs
            )
        else:
            self.session = await self.manager.create_session(
                user_id=self.user_id, **self.kwargs
            )
        
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and hasattr(self.session, 'close'):
            await self.session.close()

# Export context manager
__all__.append("MemorySessionContext")
