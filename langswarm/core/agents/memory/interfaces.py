"""
Agent Memory & Context Management Interfaces for LangSwarm V2

Sophisticated interfaces for agent memory and context handling that provide:
- Persistent conversation memory across sessions
- Context compression and summarization
- Long-term memory with retrieval capabilities  
- Context-aware personalization and adaptation
- Memory analytics and usage optimization
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union, AsyncIterator, Tuple, Callable

# Import agent interfaces
from ..interfaces import AgentMessage, IAgentSession


class MemoryType(Enum):
    """Types of memory storage"""
    WORKING = "working"           # Current conversation context
    EPISODIC = "episodic"        # Specific conversation episodes
    SEMANTIC = "semantic"        # Knowledge and facts
    PROCEDURAL = "procedural"    # Learned patterns and procedures
    EMOTIONAL = "emotional"      # Emotional context and patterns
    PREFERENCE = "preference"    # User preferences and patterns


class ContextScope(Enum):
    """Scope of context management"""
    SESSION = "session"          # Single conversation session
    USER = "user"               # All sessions for a user
    AGENT = "agent"             # All sessions for an agent
    GLOBAL = "global"           # System-wide context


class CompressionStrategy(Enum):
    """Context compression strategies"""
    SUMMARIZATION = "summarization"     # Summarize older messages
    EXTRACTION = "extraction"           # Extract key information
    CLUSTERING = "clustering"           # Group similar messages
    HIERARCHICAL = "hierarchical"       # Multi-level compression
    SEMANTIC = "semantic"              # Semantic similarity compression


class RetrievalStrategy(Enum):
    """Memory retrieval strategies"""
    RECENCY = "recency"                # Most recent first
    RELEVANCE = "relevance"            # Most relevant to query
    IMPORTANCE = "importance"          # Based on importance scores
    HYBRID = "hybrid"                  # Combination of strategies
    PERSONALIZED = "personalized"     # Based on user patterns


class PersonalizationLevel(Enum):
    """Levels of personalization"""
    NONE = "none"                      # No personalization
    BASIC = "basic"                    # Basic preference tracking
    ADAPTIVE = "adaptive"              # Learning from interactions
    PREDICTIVE = "predictive"          # Predicting user needs
    INTELLIGENT = "intelligent"       # AI-driven personalization


@dataclass
class MemoryRecord:
    """A record stored in agent memory"""
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.WORKING
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Temporal information
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    # Association information
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    message_id: Optional[str] = None
    
    # Importance and relevance
    importance_score: float = 0.5
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    access_count: int = 0
    
    # Vector embedding for semantic search
    embedding: Optional[List[float]] = None
    
    # Tags and categories
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    def update_access(self) -> None:
        """Update access statistics"""
        self.accessed_at = datetime.now(timezone.utc)
        self.access_count += 1
        
    def is_expired(self) -> bool:
        """Check if memory record is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass 
class ConversationContext:
    """Context for a conversation"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Context content
    messages: List[AgentMessage] = field(default_factory=list)
    summary: Optional[str] = None
    key_topics: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    
    # Context metrics
    token_count: int = 0
    message_count: int = 0
    compression_ratio: float = 1.0
    
    # Temporal information
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context state
    is_compressed: bool = False
    compression_strategy: Optional[CompressionStrategy] = None
    
    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the context"""
        self.messages.append(message)
        self.message_count = len(self.messages)
        self.updated_at = datetime.now(timezone.utc)
        
    def calculate_token_count(self) -> int:
        """Calculate approximate token count"""
        # Simple approximation: ~4 characters per token
        total_chars = sum(len(msg.content) for msg in self.messages)
        self.token_count = total_chars // 4
        return self.token_count


@dataclass
class PersonalizationProfile:
    """User personalization profile"""
    user_id: str
    agent_id: Optional[str] = None
    
    # Preferences
    communication_style: Dict[str, Any] = field(default_factory=dict)
    topic_interests: Dict[str, float] = field(default_factory=dict)
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Learning data
    response_preferences: Dict[str, float] = field(default_factory=dict)
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    behavioral_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Personalization settings
    personalization_level: PersonalizationLevel = PersonalizationLevel.BASIC
    privacy_settings: Dict[str, bool] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction: Optional[datetime] = None
    
    def update_interaction(self) -> None:
        """Update interaction timestamp"""
        self.last_interaction = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class MemoryInsight:
    """Insights derived from memory analysis"""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: str = ""
    title: str = ""
    description: str = ""
    
    # Insight data
    data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    relevance_score: float = 0.0
    
    # Source information
    source_records: List[str] = field(default_factory=list)
    time_range: Optional[Tuple[datetime, datetime]] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    agent_id: Optional[str] = None


@dataclass
class ContextCompressionResult:
    """Result of context compression operation"""
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    strategy_used: CompressionStrategy
    
    # Compressed content
    compressed_messages: List[AgentMessage] = field(default_factory=list)
    summary: Optional[str] = None
    preserved_entities: Dict[str, Any] = field(default_factory=dict)
    
    # Quality metrics
    information_loss: float = 0.0
    semantic_similarity: float = 1.0
    
    # Metadata
    compressed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IAgentMemory(ABC):
    """Interface for agent memory management"""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Get the agent ID this memory belongs to"""
        pass
    
    @abstractmethod
    async def store_memory(self, record: MemoryRecord) -> bool:
        """Store a memory record"""
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self,
        query: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        strategy: RetrievalStrategy = RetrievalStrategy.RELEVANCE
    ) -> List[MemoryRecord]:
        """Retrieve memory records based on criteria"""
        pass
    
    @abstractmethod
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory record"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record"""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, float]]:
        """Search memories with relevance scores"""
        pass
    
    @abstractmethod
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        pass
    
    @abstractmethod
    async def cleanup_expired_memories(self) -> int:
        """Clean up expired memories"""
        pass


class IContextManager(ABC):
    """Interface for conversation context management"""
    
    @abstractmethod
    async def create_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ConversationContext:
        """Create a new conversation context"""
        pass
    
    @abstractmethod
    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get existing conversation context"""
        pass
    
    @abstractmethod
    async def update_context(
        self,
        session_id: str,
        message: AgentMessage
    ) -> ConversationContext:
        """Update context with new message"""
        pass
    
    @abstractmethod
    async def compress_context(
        self,
        session_id: str,
        target_token_count: int,
        strategy: CompressionStrategy = CompressionStrategy.SUMMARIZATION
    ) -> ContextCompressionResult:
        """Compress context to fit token limit"""
        pass
    
    @abstractmethod
    async def get_relevant_context(
        self,
        session_id: str,
        query: str,
        max_tokens: Optional[int] = None
    ) -> List[AgentMessage]:
        """Get contextually relevant messages"""
        pass
    
    @abstractmethod
    async def summarize_context(self, session_id: str) -> str:
        """Create a summary of the conversation context"""
        pass
    
    @abstractmethod
    async def extract_entities(self, session_id: str) -> Dict[str, Any]:
        """Extract entities from conversation context"""
        pass


class IMemoryRetrieval(ABC):
    """Interface for memory retrieval operations"""
    
    @abstractmethod
    async def retrieve_by_similarity(
        self,
        query_embedding: List[float],
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[MemoryRecord, float]]:
        """Retrieve memories by semantic similarity"""
        pass
    
    @abstractmethod
    async def retrieve_by_keywords(
        self,
        keywords: List[str],
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """Retrieve memories by keyword matching"""
        pass
    
    @abstractmethod
    async def retrieve_temporal(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 50
    ) -> List[MemoryRecord]:
        """Retrieve memories within time range"""
        pass
    
    @abstractmethod
    async def retrieve_for_user(
        self,
        user_id: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 50
    ) -> List[MemoryRecord]:
        """Retrieve all memories for a user"""
        pass
    
    @abstractmethod
    async def retrieve_patterns(
        self,
        pattern_type: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[MemoryRecord]:
        """Retrieve memories matching behavioral patterns"""
        pass


class IPersonalizationEngine(ABC):
    """Interface for personalization and adaptation"""
    
    @abstractmethod
    async def get_profile(
        self,
        user_id: str,
        agent_id: Optional[str] = None
    ) -> Optional[PersonalizationProfile]:
        """Get user personalization profile"""
        pass
    
    @abstractmethod
    async def update_profile(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> PersonalizationProfile:
        """Update profile based on interaction"""
        pass
    
    @abstractmethod
    async def get_personalized_context(
        self,
        user_id: str,
        base_context: List[AgentMessage],
        agent_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get personalized context for user"""
        pass
    
    @abstractmethod
    async def suggest_response_style(
        self,
        user_id: str,
        context: List[AgentMessage],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest response style based on user preferences"""
        pass
    
    @abstractmethod
    async def predict_user_intent(
        self,
        user_id: str,
        current_message: str,
        context: List[AgentMessage],
        agent_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Predict user intent based on patterns"""
        pass
    
    @abstractmethod
    async def adapt_to_feedback(
        self,
        user_id: str,
        feedback: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> bool:
        """Adapt personalization based on user feedback"""
        pass


class IMemoryAnalytics(ABC):
    """Interface for memory analytics and insights"""
    
    @abstractmethod
    async def analyze_memory_usage(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Analyze memory usage patterns"""
        pass
    
    @abstractmethod
    async def generate_insights(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        insight_types: Optional[List[str]] = None
    ) -> List[MemoryInsight]:
        """Generate insights from memory data"""
        pass
    
    @abstractmethod
    async def get_conversation_analytics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get analytics for a specific conversation"""
        pass
    
    @abstractmethod
    async def get_user_analytics(
        self,
        user_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get analytics for a user across sessions"""
        pass
    
    @abstractmethod
    async def optimize_memory_usage(
        self,
        target_reduction: float = 0.2
    ) -> Dict[str, Any]:
        """Optimize memory usage by removing low-value memories"""
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get memory system performance metrics"""
        pass


# Factory function type
def create_agent_memory(
    agent_id: str,
    memory_backend_config: Dict[str, Any],
    personalization_level: PersonalizationLevel = PersonalizationLevel.BASIC
) -> Tuple[IAgentMemory, IContextManager, IMemoryRetrieval, IPersonalizationEngine, IMemoryAnalytics]:
    """
    Factory function to create a complete agent memory system
    
    Returns tuple of (memory, context_manager, retrieval, personalization, analytics)
    """
    from .implementations import (
        AgentMemoryManager,
        ContextManager,
        MemoryRetrievalEngine, 
        PersonalizationEngine,
        MemoryAnalytics
    )
    
    # Create core components
    memory = AgentMemoryManager(agent_id, memory_backend_config)
    context_manager = ContextManager(memory)
    retrieval = MemoryRetrievalEngine(memory)
    personalization = PersonalizationEngine(memory, personalization_level)
    analytics = MemoryAnalytics(memory)
    
    return memory, context_manager, retrieval, personalization, analytics


# Type aliases for convenience
MemoryQuery = Union[str, Dict[str, Any]]
MemoryFilter = Dict[str, Any]
AnalyticsResult = Dict[str, Any]
PersonalizationData = Dict[str, Any]