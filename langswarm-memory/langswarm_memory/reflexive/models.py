"""
Data models for Reflexive Memory system.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid

@dataclass
class Lesson:
    """
    A learned rule or instruction derived from past feedback.
    Aligned with the "Reflexive Onion" architecture.
    """
    rule_content: str
    trigger_scenario_text: str  # The input text used to generate the vector
    scope: str = "global"       # 'global', 'role', 'session'
    target_role: Optional[str] = None # e.g. 'lawyer', 'cs', 'sales' or None if global
    source_incident: str = ""   # The original query/failure that caused this rule
    
    vector: Optional[List[float]] = None
    lesson_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hit_count: int = 0
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "lesson_id": self.lesson_id,
            "rule_content": self.rule_content,
            "trigger_scenario_text": self.trigger_scenario_text,
            "scope": self.scope,
            "target_role": self.target_role,
            "source_incident": self.source_incident,
            "created_at": self.created_at.isoformat(),
            "hit_count": self.hit_count,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lesson':
        """Create from dictionary"""
        return cls(
            lesson_id=data.get("lesson_id"),
            rule_content=data.get("rule_content"),
            trigger_scenario_text=data.get("trigger_scenario_text"),
            scope=data.get("scope", "global"),
            target_role=data.get("target_role"),
            source_incident=data.get("source_incident") or data.get("feedback_source", ""), # Backwards compat
            created_at=datetime.fromisoformat(data.get("created_at")),
            hit_count=data.get("hit_count", 0),
            confidence_score=data.get("confidence_score", 1.0),
            metadata=data.get("metadata", {})
        )
