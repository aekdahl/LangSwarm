"""
LangSwarm Session Management
===========================

Unified session management system for LangSwarm agents with support for:
- Native thread IDs where available
- Multi-provider session coordination
- Session persistence and recovery
- Hybrid session management with enhanced capabilities

Basic Usage:
    # Basic session management (automatic)
    agent = AgentWrapperFactory.create_agent(provider="openai", model="gpt-4")
    response = agent.chat("Hello")  # Session created automatically
    
    # Hybrid session management (enhanced features)
    agent = AgentWrapperFactory.create_agent(
        provider="openai", 
        model="gpt-4",
        enable_hybrid_sessions=True,
        enhanced_backend="chromadb"
    )
    response = agent.chat("Hello")  # Enhanced session with semantic search
    
    # Search conversation history
    results = agent.search_conversation_history("machine learning")
    
    # Get analytics
    analytics = agent.get_conversation_analytics()
"""

# Core session management
from .models import (
    LangSwarmSession,
    SessionMetadata,
    ConversationMessage,
    ConversationHistory,
    SessionStatus,
    SessionControl,
    MessageRole
)

from .storage import (
    SessionStorage,
    InMemorySessionStorage,
    SQLiteSessionStorage,
    SessionStorageFactory
)

from .strategies import (
    SessionStrategy,
    NativeSessionStrategy,
    ClientSideSessionStrategy,
    HybridSessionStrategy,
    SessionStrategyFactory
)

from .adapters import (
    BaseSessionAdapter,
    OpenAISessionAdapter,
    ClaudeSessionAdapter,
    GeminiSessionAdapter,
    MistralSessionAdapter,
    CohereSessionAdapter,
    SessionAdapterFactory
)

from .manager import (
    LangSwarmSessionManager
)

# Enhanced hybrid session management
from .hybrid_manager import (
    HybridSessionManager,
    HybridSessionManagerFactory
)

from .adapters_bridge import (
    SessionDatabaseBridge,
    HybridAdapterFactory,
    MockSessionAdapter
)

# Version and metadata
__version__ = "1.0.0"
__all__ = [
    # Core models
    "LangSwarmSession",
    "SessionMetadata", 
    "ConversationMessage",
    "ConversationHistory",
    "SessionStatus",
    "SessionControl",
    "MessageRole",
    
    # Storage
    "SessionStorage",
    "InMemorySessionStorage",
    "SQLiteSessionStorage", 
    "SessionStorageFactory",
    
    # Strategies
    "SessionStrategy",
    "NativeSessionStrategy",
    "ClientSideSessionStrategy",
    "HybridSessionStrategy",
    "SessionStrategyFactory",
    
    # Adapters
    "BaseSessionAdapter",
    "OpenAISessionAdapter",
    "ClaudeSessionAdapter",
    "GeminiSessionAdapter",
    "MistralSessionAdapter",
    "CohereSessionAdapter",
    "SessionAdapterFactory",
    
    # Basic manager
    "LangSwarmSessionManager",
    
    # Hybrid management
    "HybridSessionManager",
    "HybridSessionManagerFactory",
    
    # Adapter bridges
    "SessionDatabaseBridge",
    "HybridAdapterFactory",
    "MockSessionAdapter",
] 