"""
LangSwarm Memory Integration - Now using AgentMem

This module maintains backwards compatibility by re-exporting from the agentmem package.
LangSwarm's memory system has been extracted as a standalone package that can be used
by any AI agent framework.

For more information about AgentMem, see: https://github.com/aekdahl/agentmem
"""

# Re-export everything from agentmem for backwards compatibility
# Note: During development, agentmem is a namespace package, so we import from agentmem.agentmem
# When published to PyPI, this will work as: from agentmem import ...
try:
    from agentmem import (
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
        
        # Base implementations
        BaseMemorySession,
        BaseMemoryBackend,
        MemoryManager,
        
        # Backend implementations
        InMemoryBackend,
        SQLiteBackend,
        RedisBackend,
        
        # Factory functions
        create_memory_manager,
        create_memory_backend,
        MemoryConfiguration,
        MemoryFactory,
        
        # Error classes
        AgentMemError as MemoryError,  # Map to old name
        MemoryBackendError,
        MemoryConfigurationError,
        
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
except ImportError:
    # During development with editable install, use nested import
    from agentmem.agentmem import (
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
        
        # Base implementations
        BaseMemorySession,
        BaseMemoryBackend,
        MemoryManager,
        
        # Backend implementations
        InMemoryBackend,
        SQLiteBackend,
        RedisBackend,
        
        # Factory functions
        create_memory_manager,
        create_memory_backend,
        MemoryConfiguration,
        MemoryFactory,
        
        # Error classes
        AgentMemError as MemoryError,  # Map to old name
        MemoryBackendError,
        MemoryConfigurationError,
        
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
    
    # Factory functions
    "create_memory_manager",
    "create_memory_backend",
    "MemoryConfiguration",
    "MemoryFactory",
    
    # Error classes
    "MemoryError",
    "MemoryBackendError",
    "MemoryConfigurationError",
    
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

# Convenience functions to maintain compatibility
def initialize_memory(config=None):
    """
    Initialize memory system (compatibility wrapper)
    
    Args:
        config: Memory configuration (string or dict)
        
    Returns:
        Memory manager instance
    """
    if config is None:
        config = "development"
    
    if isinstance(config, str):
        # Simple string config
        manager = create_memory_manager(config)
    else:
        # Dict config
        manager = create_memory_manager(**config)
    
    return manager


def get_memory():
    """Get global memory manager (for backwards compatibility)"""
    # Note: AgentMem doesn't have a global singleton by default
    # This is a stub for compatibility
    return None


# Alias for common usage patterns
MemorySessionContext = None  # Placeholder - not yet implemented in agentmem


__version__ = "2.0.0"  # LangSwarm V2 with AgentMem integration
__agentmem_version__ = "0.1.0"
