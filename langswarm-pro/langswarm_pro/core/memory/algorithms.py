from typing import List
from datetime import datetime, timezone
from .models import ProMemoryRecord, PriorityTier

class MemoryPrioritizer:
    @staticmethod
    def rank_memories(memories: List[ProMemoryRecord]) -> List[ProMemoryRecord]:
        """Rank memories by current calculated importance"""
        return sorted(
            memories, 
            key=lambda m: m.calculate_current_importance(), 
            reverse=True
        )

class MemoryFader:
    def __init__(self, threshold: float = 0.2):
        self.threshold = threshold

    def identify_fading_memories(self, memories: List[ProMemoryRecord]) -> List[ProMemoryRecord]:
        """Identify memories that have faded below threshold"""
        candidates = []
        for mem in memories:
            if mem.is_protected:
                continue
                
            current_score = mem.calculate_current_importance()
            if current_score < self.threshold:
                candidates.append(mem)
        return candidates
