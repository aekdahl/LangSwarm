"""
Memory Enhancement Managers for AgentMem v0.2.0

Provides mem0-inspired enhancements:
- Memory Relations/Graph: Connect related memories
- Temporal Decay with Reinforcement: Spaced repetition algorithm
- Auto-Categorization: LLM-powered memory classification
- Memory Deduplication: Merge similar memories
"""

import asyncio
import logging
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

from .agent_memory_types import EnhancedMemoryRecord as MemoryRecord, RelationType, MemoryRelation
from .errors import AgentMemError

logger = logging.getLogger(__name__)


class MemoryRelationManager:
    """
    Manage relationships between memories to build knowledge graphs
    
    Features:
    - Add/remove relations between memories
    - Find related memories
    - Get memory graph (traversal with depth)
    - Relationship strength scoring
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._relation_cache: Dict[str, List[MemoryRelation]] = {}
    
    async def add_relation(
        self, 
        source_id: str, 
        target_id: str, 
        relation_type: RelationType,
        strength: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryRelation:
        """
        Create a relationship between two memories
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            relation_type: Type of relationship
            strength: Relationship strength (0-1)
            metadata: Additional metadata
            
        Returns:
            The created MemoryRelation
        """
        relation = MemoryRelation(
            target_memory_id=target_id,
            relation_type=relation_type,
            strength=max(0.0, min(1.0, strength)),  # Clamp to [0, 1]
            metadata=metadata or {}
        )
        
        try:
            cursor = self._conn.cursor()
            cursor.execute('''
                INSERT INTO memory_relations 
                (relation_id, source_memory_id, target_memory_id, relation_type, strength, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                relation.relation_id,
                source_id,
                target_id,
                relation_type.value,
                strength,
                str(metadata or {}),
                relation.created_at.isoformat()
            ))
            self._conn.commit()
            
            # Update cache
            if source_id in self._relation_cache:
                self._relation_cache[source_id].append(relation)
            
            logger.debug(f"Added relation: {source_id} --[{relation_type.value}]--> {target_id}")
            return relation
            
        except Exception as e:
            logger.error(f"Failed to add relation: {e}")
            raise AgentMemError(f"Failed to add memory relation", details={"error": str(e)})
    
    async def find_related(
        self, 
        memory_id: str, 
        relation_type: Optional[RelationType] = None,
        min_strength: float = 0.0
    ) -> List[Tuple[str, MemoryRelation]]:
        """
        Find all memories related to the given memory
        
        Args:
            memory_id: Memory ID to find relations for
            relation_type: Optional filter by relation type
            min_strength: Minimum relationship strength
            
        Returns:
            List of (target_memory_id, relation) tuples
        """
        try:
            cursor = self._conn.cursor()
            
            # Build query with filters
            query = '''
                SELECT target_memory_id, relation_id, relation_type, strength, metadata, created_at
                FROM memory_relations
                WHERE source_memory_id = ? AND strength >= ?
            '''
            params = [memory_id, min_strength]
            
            if relation_type:
                query += " AND relation_type = ?"
                params.append(relation_type.value)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            related = []
            for row in results:
                relation = MemoryRelation(
                    relation_id=row[1],
                    target_memory_id=row[0],
                    relation_type=RelationType(row[2]),
                    strength=row[3],
                    metadata=eval(row[4]) if row[4] else {},
                    created_at=datetime.fromisoformat(row[5])
                )
                related.append((row[0], relation))
            
            logger.debug(f"Found {len(related)} related memories for {memory_id}")
            return related
            
        except Exception as e:
            logger.error(f"Failed to find related memories: {e}")
            return []
    
    async def get_memory_graph(
        self, 
        memory_id: str, 
        depth: int = 2,
        visited: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a graph of related memories up to specified depth
        
        Args:
            memory_id: Root memory ID
            depth: Maximum traversal depth
            visited: Set of already visited memory IDs (for recursion)
            
        Returns:
            Dict representing the memory graph
        """
        if depth <= 0:
            return {}
        
        if visited is None:
            visited = set()
        
        if memory_id in visited:
            return {}
        
        visited.add(memory_id)
        
        # Get direct relations
        relations = await self.find_related(memory_id)
        
        graph = {
            "memory_id": memory_id,
            "relations": []
        }
        
        # Recursively build graph
        for target_id, relation in relations:
            relation_data = {
                "target_id": target_id,
                "relation_type": relation.relation_type.value,
                "strength": relation.strength,
                "subgraph": await self.get_memory_graph(target_id, depth - 1, visited)
            }
            graph["relations"].append(relation_data)
        
        return graph
    
    async def remove_relation(self, relation_id: str) -> bool:
        """Remove a specific relation"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memory_relations WHERE relation_id = ?", (relation_id,))
            self._conn.commit()
            
            # Clear cache
            self._relation_cache.clear()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to remove relation: {e}")
            return False


class TemporalDecayManager:
    """
    Spaced repetition for memories - frequently accessed memories stay stronger
    
    Features:
    - Boost importance on access (spaced repetition)
    - Apply time-based decay to unused memories
    - Smart decay rates based on access patterns
    """
    
    def __init__(self, base_decay_rate: float = 0.1, boost_factor: float = 1.1):
        self.base_decay_rate = base_decay_rate
        self.boost_factor = boost_factor
    
    async def update_importance_on_access(self, memory: MemoryRecord) -> None:
        """
        Boost importance when memory is accessed (spaced repetition reinforcement)
        
        Args:
            memory: Memory record to update
        """
        # Update access tracking
        memory.update_access()
        
        # Boost importance (spaced repetition)
        memory.boost_importance(self.boost_factor)
        
        logger.debug(f"Boosted memory {memory.memory_id} to importance {memory.importance_score:.3f}")
    
    async def apply_decay(
        self, 
        memories: List[MemoryRecord], 
        current_time: Optional[datetime] = None
    ) -> List[MemoryRecord]:
        """
        Apply time-based decay to memories not recently accessed
        
        Decay formula:
        - Decay rate decreases with access frequency
        - More accessed memories decay slower
        - Exponential decay based on time since last access
        
        Args:
            memories: List of memories to apply decay to
            current_time: Current time (defaults to now)
            
        Returns:
            Updated list of memories
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        for memory in memories:
            # Calculate time since last access
            time_delta = current_time - memory.last_accessed
            days_since_access = time_delta.total_seconds() / 86400  # Convert to days
            
            # Adaptive decay rate based on access frequency
            # More frequently accessed memories decay slower
            access_factor = 1.0 / (1.0 + memory.access_count * 0.1)
            effective_decay = self.base_decay_rate * access_factor
            
            # Exponential decay over time
            decay_amount = effective_decay * (1 - 0.9 ** days_since_access)
            
            # Apply decay
            memory.decay_importance(decay_amount)
            
            logger.debug(
                f"Applied decay to {memory.memory_id}: "
                f"days={days_since_access:.1f}, decay={decay_amount:.3f}, "
                f"new_importance={memory.importance_score:.3f}"
            )
        
        return memories


class MemoryCategorizer:
    """
    Automatically categorize memories using pattern matching
    
    Features:
    - Extract categories from content
    - Pattern-based categorization
    - Confidence scoring
    """
    
    def __init__(self):
        # Define category patterns (can be extended)
        self.category_patterns = {
            "programming": [
                r"\b(python|javascript|java|code|programming|function|class|variable)\b",
                r"\b(api|endpoint|backend|frontend|database)\b"
            ],
            "data": [
                r"\b(data|dataset|analysis|statistics|dataframe|csv)\b",
                r"\b(machine learning|ml|ai|model|training)\b"
            ],
            "business": [
                r"\b(meeting|deadline|project|client|customer|stakeholder)\b",
                r"\b(revenue|profit|sales|marketing|strategy)\b"
            ],
            "personal": [
                r"\b(preference|like|dislike|favorite|interested|hobby)\b",
                r"\b(personal|family|friend|weekend)\b"
            ],
            "technical": [
                r"\b(server|deploy|infrastructure|configuration|setup)\b",
                r"\b(bug|issue|error|debug|fix)\b"
            ],
            "question": [
                r"^\s*(what|how|why|when|where|who|can you|could you|please)\b",
                r"\?\s*$"
            ]
        }
    
    async def categorize_memory(self, memory: MemoryRecord) -> List[str]:
        """
        Extract categories from memory content using pattern matching
        
        Args:
            memory: Memory record to categorize
            
        Returns:
            List of category names
        """
        content_lower = memory.content.lower()
        categories = []
        confidence_scores = {}
        
        for category, patterns in self.category_patterns.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    match_count += 1
            
            if match_count > 0:
                categories.append(category)
                confidence_scores[category] = min(1.0, match_count * 0.3)
        
        # Store confidence if categorized
        if categories:
            memory.auto_categorized = True
            memory.categorization_confidence = sum(confidence_scores.values()) / len(categories)
        
        logger.debug(f"Categorized memory {memory.memory_id}: {categories}")
        return categories
    
    async def bulk_categorize(self, memories: List[MemoryRecord]) -> None:
        """
        Categorize multiple memories efficiently
        
        Args:
            memories: List of memories to categorize
        """
        for memory in memories:
            if not memory.auto_categorized:
                categories = await self.categorize_memory(memory)
                memory.categories.extend(categories)
        
        logger.info(f"Bulk categorized {len(memories)} memories")


class MemoryDeduplicator:
    """
    Find and merge duplicate/similar memories
    
    Features:
    - Detect similar memories based on content
    - Merge duplicates keeping best metadata
    - Create relation links to merged memories
    """
    
    def __init__(self, conn: sqlite3.Connection, similarity_threshold: float = 0.95):
        self._conn = conn
        self.similarity_threshold = similarity_threshold
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (Jaccard similarity on words)
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Simple word-based Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def find_duplicates(
        self, 
        memory: MemoryRecord,
        threshold: Optional[float] = None
    ) -> List[MemoryRecord]:
        """
        Find memories highly similar to the given memory
        
        Args:
            memory: Memory to find duplicates for
            threshold: Similarity threshold (default: instance threshold)
            
        Returns:
            List of similar memory records
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        try:
            cursor = self._conn.cursor()
            
            # Get all memories of same type and user
            cursor.execute('''
                SELECT memory_id, memory_type, content, importance_score, 
                       tags, categories, created_at, user_id
                FROM memory_records
                WHERE user_id = ? AND memory_type = ? AND memory_id != ?
            ''', (memory.user_id, memory.memory_type.value, memory.memory_id))
            
            candidates = cursor.fetchall()
            duplicates = []
            
            for row in candidates:
                candidate_content = row[2]
                similarity = self._calculate_text_similarity(memory.content, candidate_content)
                
                if similarity >= threshold:
                    # This is a duplicate
                    duplicate = MemoryRecord(
                        memory_id=row[0],
                        memory_type=memory.memory_type,
                        content=candidate_content,
                        importance_score=row[3],
                        tags=eval(row[4]) if row[4] else [],
                        categories=eval(row[5]) if row[5] else [],
                        created_at=datetime.fromisoformat(row[6]),
                        user_id=row[7]
                    )
                    duplicates.append(duplicate)
                    logger.debug(
                        f"Found duplicate: {duplicate.memory_id} "
                        f"(similarity: {similarity:.3f})"
                    )
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            return []
    
    async def merge_memories(
        self, 
        memories: List[MemoryRecord],
        relation_manager: Optional[MemoryRelationManager] = None
    ) -> MemoryRecord:
        """
        Merge similar memories, keeping highest importance
        
        Strategy:
        - Keep memory with highest importance as primary
        - Combine content from all memories
        - Merge tags and categories
        - Create relations to indicate merging
        
        Args:
            memories: List of memories to merge
            relation_manager: Optional relation manager for creating links
            
        Returns:
            The merged memory record
        """
        if not memories:
            raise AgentMemError("No memories provided for merging")
        
        if len(memories) == 1:
            return memories[0]
        
        # Sort by importance (highest first)
        sorted_memories = sorted(memories, key=lambda m: m.importance_score, reverse=True)
        primary = sorted_memories[0]
        
        # Combine content (deduplicate similar sentences)
        combined_content_parts = [primary.content]
        for memory in sorted_memories[1:]:
            if memory.content not in combined_content_parts:
                combined_content_parts.append(memory.content)
        
        primary.content = " | ".join(combined_content_parts)
        
        # Merge tags and categories (deduplicate)
        all_tags = set(primary.tags)
        all_categories = set(primary.categories)
        
        for memory in sorted_memories[1:]:
            all_tags.update(memory.tags)
            all_categories.update(memory.categories)
        
        primary.tags = list(all_tags)
        primary.categories = list(all_categories)
        
        # Boost importance (merged memories are more valuable)
        primary.importance_score = min(1.0, primary.importance_score * 1.2)
        
        # Add provenance
        primary.source = "merged"
        primary.derivation_method = "deduplication"
        
        # Create relations if manager provided
        if relation_manager:
            for memory in sorted_memories[1:]:
                await relation_manager.add_relation(
                    source_id=primary.memory_id,
                    target_id=memory.memory_id,
                    relation_type=RelationType.SUPERSEDES,
                    strength=0.9,
                    metadata={"reason": "deduplication_merge"}
                )
        
        logger.info(f"Merged {len(memories)} memories into {primary.memory_id}")
        return primary


__all__ = [
    "MemoryRelationManager",
    "TemporalDecayManager",
    "MemoryCategorizer",
    "MemoryDeduplicator"
]



