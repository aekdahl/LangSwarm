"""
Enhanced Agent Memory Data Structures for AgentMem v0.2.0

Provides enhanced memory types with:
- Memory relations/graph support
- Provenance tracking
- Confidence scoring
- Auto-categorization
- Temporal decay with reinforcement
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional


class MemoryType(Enum):
    """Types of memory storage"""
    WORKING = "working"           # Current conversation context
    EPISODIC = "episodic"        # Specific conversation episodes
    SEMANTIC = "semantic"        # Knowledge and facts
    PROCEDURAL = "procedural"    # Learned patterns and procedures
    EMOTIONAL = "emotional"      # Emotional context and patterns
    PREFERENCE = "preference"    # User preferences and patterns


class RelationType(Enum):
    """Types of relationships between memories"""
    RELATES_TO = "relates_to"        # General relationship
    CONTRADICTS = "contradicts"      # Memories contradict each other
    EXTENDS = "extends"              # One extends the other
    SUPPORTS = "supports"            # One supports the other
    SUPERSEDES = "supersedes"        # Newer memory replaces older
    DERIVED_FROM = "derived_from"    # Memory derived from another


@dataclass
class MemoryRelation:
    """Relationship between memories"""
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_memory_id: str = ""
    relation_type: RelationType = RelationType.RELATES_TO
    strength: float = 0.5  # 0-1, confidence in the relationship
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "relation_id": self.relation_id,
            "target_memory_id": self.target_memory_id,
            "relation_type": self.relation_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRelation':
        """Create from dictionary"""
        return cls(
            relation_id=data["relation_id"],
            target_memory_id=data["target_memory_id"],
            relation_type=RelationType(data["relation_type"]),
            strength=data["strength"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class EnhancedMemoryRecord:
    """
    Enhanced memory record with relations, provenance, and quality metrics
    
    This extends the base memory concept with:
    - Graph-based relationships to other memories
    - Provenance tracking (where did this memory come from?)
    - Quality metrics (confidence, verification)
    - Auto-categorization support
    - Temporal access tracking for spaced repetition
    """
    # Core identification
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.WORKING
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Temporal information
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
    
    # NEW: Graph-based relationships
    relations: List[MemoryRelation] = field(default_factory=list)
    
    # NEW: Provenance tracking
    source: str = "conversation"  # "conversation", "document", "inference", "external", "system"
    parent_memory_id: Optional[str] = None  # If derived from another memory
    derivation_method: Optional[str] = None  # "summarization", "inference", "extraction", etc.
    
    # NEW: Quality metrics
    confidence: float = 1.0  # 0-1, confidence in the memory accuracy
    verified: bool = False  # Has this memory been verified?
    verification_source: Optional[str] = None  # Where was it verified?
    verification_date: Optional[datetime] = None
    
    # NEW: Auto-categorization
    auto_categorized: bool = False  # Was this auto-categorized?
    categorization_confidence: float = 0.0  # Confidence in auto-categorization
    
    def update_access(self) -> None:
        """Update access statistics and temporal information"""
        now = datetime.now(timezone.utc)
        self.accessed_at = now
        self.last_accessed = now
        self.access_count += 1
        self.updated_at = now
    
    def is_expired(self) -> bool:
        """Check if memory record is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def add_relation(self, target_id: str, relation_type: RelationType, 
                    strength: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> MemoryRelation:
        """Add a relationship to another memory"""
        relation = MemoryRelation(
            target_memory_id=target_id,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )
        self.relations.append(relation)
        self.updated_at = datetime.now(timezone.utc)
        return relation
    
    def get_relations(self, relation_type: Optional[RelationType] = None) -> List[MemoryRelation]:
        """Get relations, optionally filtered by type"""
        if relation_type:
            return [r for r in self.relations if r.relation_type == relation_type]
        return self.relations
    
    def verify(self, source: str) -> None:
        """Mark memory as verified"""
        self.verified = True
        self.verification_source = source
        self.verification_date = datetime.now(timezone.utc)
        self.confidence = min(1.0, self.confidence + 0.2)  # Boost confidence
        self.updated_at = datetime.now(timezone.utc)
    
    def decay_importance(self, decay_rate: float) -> None:
        """Apply decay to importance score"""
        self.importance_score = max(0.0, self.importance_score - decay_rate)
        self.updated_at = datetime.now(timezone.utc)
    
    def boost_importance(self, boost_factor: float = 1.1) -> None:
        """Boost importance (spaced repetition reinforcement)"""
        self.importance_score = min(1.0, self.importance_score * boost_factor)
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "message_id": self.message_id,
            "importance_score": self.importance_score,
            "relevance_scores": self.relevance_scores,
            "access_count": self.access_count,
            "embedding": self.embedding,
            "tags": self.tags,
            "categories": self.categories,
            "relations": [r.to_dict() for r in self.relations],
            "source": self.source,
            "parent_memory_id": self.parent_memory_id,
            "derivation_method": self.derivation_method,
            "confidence": self.confidence,
            "verified": self.verified,
            "verification_source": self.verification_source,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None,
            "auto_categorized": self.auto_categorized,
            "categorization_confidence": self.categorization_confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedMemoryRecord':
        """Create from dictionary"""
        relations = [MemoryRelation.from_dict(r) for r in data.get("relations", [])]
        
        return cls(
            memory_id=data["memory_id"],
            memory_type=MemoryType(data["memory_type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            accessed_at=datetime.fromisoformat(data["accessed_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            agent_id=data.get("agent_id"),
            message_id=data.get("message_id"),
            importance_score=data.get("importance_score", 0.5),
            relevance_scores=data.get("relevance_scores", {}),
            access_count=data.get("access_count", 0),
            embedding=data.get("embedding"),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            relations=relations,
            source=data.get("source", "conversation"),
            parent_memory_id=data.get("parent_memory_id"),
            derivation_method=data.get("derivation_method"),
            confidence=data.get("confidence", 1.0),
            verified=data.get("verified", False),
            verification_source=data.get("verification_source"),
            verification_date=datetime.fromisoformat(data["verification_date"]) if data.get("verification_date") else None,
            auto_categorized=data.get("auto_categorized", False),
            categorization_confidence=data.get("categorization_confidence", 0.0)
        )


__all__ = [
    "MemoryType",
    "RelationType",
    "MemoryRelation",
    "EnhancedMemoryRecord"
]



