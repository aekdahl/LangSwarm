from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from langswarm_memory.agent_memory_types import EnhancedMemoryRecord

class PriorityTier(str, Enum):
    CRITICAL = "critical"  # Never fades
    HIGH = "high"         # Slow fade
    NORMAL = "normal"     # Normal fade
    LOW = "low"          # Fast fade

@dataclass
class ProMemoryRecord(EnhancedMemoryRecord):
    """
    Pro extension of memory record with advanced lifecycle management.
    """
    priority_tier: PriorityTier = PriorityTier.NORMAL
    fading_rate: float = 0.1  # Default decay rate
    is_protected: bool = False # If true, never deleted by cleanup
    
    def calculate_current_importance(self) -> float:
        """Calculate importance based on tier and decay"""
        if self.priority_tier == PriorityTier.CRITICAL or self.is_protected:
            return 1.0
            
        base_score = self.importance_score
        
        # Recency boost
        now = datetime.now(timezone.utc)
        hours_since_access = (now - self.last_accessed).total_seconds() / 3600
        
        # Simple decay formula: score * (1 - rate)^hours
        # This is a simplification
        decay_factor = (1.0 - self.fading_rate) ** (hours_since_access / 24.0) # Daily decay
        
        return max(0.0, min(1.0, base_score * decay_factor))
