"""
Agent Memory & Context Management System for LangSwarm V2

This module provides sophisticated memory and context handling capabilities for V2 agents,
including persistent conversation memory, context compression, long-term memory with retrieval,
context-aware personalization, and memory analytics.
"""

from .interfaces import (
    # Core interfaces
    IAgentMemory,
    IContextManager,
    IMemoryRetrieval,
    IPersonalizationEngine,
    IMemoryAnalytics,
    
    # Data structures
    MemoryRecord,
    ConversationContext,
    PersonalizationProfile,
    MemoryInsight,
    ContextCompressionResult,
    
    # Enums
    MemoryType,
    ContextScope,
    CompressionStrategy,
    RetrievalStrategy,
    PersonalizationLevel,
    
    # Factory function
    create_agent_memory
)

from .implementations import (
    AgentMemoryManager,
    ContextManager,
    MemoryRetrievalEngine,
    PersonalizationEngine,
    MemoryAnalytics
)

__all__ = [
    # Interfaces
    "IAgentMemory",
    "IContextManager", 
    "IMemoryRetrieval",
    "IPersonalizationEngine",
    "IMemoryAnalytics",
    
    # Data structures
    "MemoryRecord",
    "ConversationContext",
    "PersonalizationProfile",
    "MemoryInsight",
    "ContextCompressionResult",
    
    # Enums
    "MemoryType",
    "ContextScope",
    "CompressionStrategy",
    "RetrievalStrategy",
    "PersonalizationLevel",
    
    # Implementations
    "AgentMemoryManager",
    "ContextManager",
    "MemoryRetrievalEngine",
    "PersonalizationEngine",
    "MemoryAnalytics",
    
    # Factory
    "create_agent_memory"
]