"""
LangSwarm Memory - Enterprise-grade conversational memory for AI agents

A standalone memory management system that provides session-based conversation
handling, multiple storage backends, and LLM provider integration.

Quick Start:
    from langswarm_memory import create_memory_manager, Message, MessageRole
    
    # Create memory manager
    manager = create_memory_manager("sqlite", db_path="memory.db")
    
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

__version__ = "0.1.0"
__author__ = "Alexander Ekdahl"
__license__ = "Apache-2.0"

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
)

# Error classes
from .errors import (
    LangSwarmMemoryError,
    MemoryBackendError,
    MemoryConfigurationError,
    EmbeddingError,
    VectorSearchError,
    MemoryStorageError,
)

__all__ = [
    # Version
    "__version__",
    
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
    "create_memory_manager",
    "create_memory_backend",
    
    # Error classes
    "LangSwarmMemoryError",
    "MemoryBackendError",
    "MemoryConfigurationError",
    "EmbeddingError",
    "VectorSearchError",
    "MemoryStorageError",
    
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



