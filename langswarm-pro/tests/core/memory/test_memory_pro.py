import pytest
from datetime import datetime, timedelta, timezone
from langswarm_pro.core.memory.models import ProMemoryRecord, PriorityTier
from langswarm_pro.core.memory.algorithms import MemoryPrioritizer, MemoryFader

class TestMemoryPro:
    def test_pro_memory_record_creation(self):
        record = ProMemoryRecord(
            content="test",
            priority_tier=PriorityTier.HIGH,
            fading_rate=0.05
        )
        assert record.importance_score == 0.5 # default
        assert record.priority_tier == PriorityTier.HIGH
        assert record.fading_rate == 0.05
    
    def test_importance_calculation_fresh(self):
        record = ProMemoryRecord(content="fresh", importance_score=0.8)
        # Just created, should have high score
        score = record.calculate_current_importance()
        # Should be close to base score as time diff is near 0
        assert score > 0.79

    def test_importance_calculation_decay(self):
        # Simulate old access
        old_time = datetime.now(timezone.utc) - timedelta(hours=24)
        record = ProMemoryRecord(
            content="old", 
            importance_score=1.0, 
            fading_rate=0.5,
            priority_tier=PriorityTier.NORMAL
        )
        record.last_accessed = old_time
        
        score = record.calculate_current_importance()
        # Expect roughly 50% decay over 24h
        # 1.0 * (1 - 0.5)^(24/24) = 0.5
        assert 0.45 < score < 0.55

    def test_critical_no_decay(self):
        old_time = datetime.now(timezone.utc) - timedelta(days=100)
        record = ProMemoryRecord(
            content="critical", 
            importance_score=1.0, 
            priority_tier=PriorityTier.CRITICAL
        )
        record.last_accessed = old_time
        
        score = record.calculate_current_importance()
        assert score == 1.0

    def test_prioritizer_ranking(self):
        # Create records with different effective scores
        high = ProMemoryRecord(content="high", importance_score=1.0) # default decay low
        low = ProMemoryRecord(content="low", importance_score=0.1)
        
        memories = [low, high]
        ranked = MemoryPrioritizer.rank_memories(memories)
        
        assert ranked[0].content == "high"
        assert ranked[1].content == "low"

    def test_fader_identification(self):
        fresh = ProMemoryRecord(content="keep", importance_score=1.0)
        faded = ProMemoryRecord(content="fade", importance_score=0.1) # below threshold 0.2
        
        fader = MemoryFader(threshold=0.2)
        candidates = fader.identify_fading_memories([fresh, faded])
        
        assert len(candidates) == 1
        assert candidates[0].content == "fade"
