"""
Navigation Decision Tracking and Analytics

This module tracks all navigation decisions made by agents, providing
analytics, optimization insights, and decision history for workflows.
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class NavigationDecision:
    """Represents a single navigation decision made by an agent"""
    decision_id: str
    workflow_id: str
    step_id: str
    agent_id: str
    chosen_step: str
    available_steps: List[str]
    reasoning: str
    confidence: float
    context_hash: str
    timestamp: datetime
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationAnalytics:
    """Analytics data for navigation decisions"""
    total_decisions: int
    avg_confidence: float
    most_common_paths: List[Dict[str, Any]]
    decision_patterns: Dict[str, Any]
    performance_metrics: Dict[str, float]
    optimization_suggestions: List[str]


class NavigationTracker:
    """
    Tracks and analyzes navigation decisions for optimization and insights.
    
    Features:
    - Decision history storage
    - Performance analytics
    - Pattern recognition
    - Optimization suggestions
    - A/B testing support
    """
    
    def __init__(self, db_path: str = "navigation_decisions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database for tracking decisions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS navigation_decisions (
                    decision_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    chosen_step TEXT NOT NULL,
                    available_steps TEXT NOT NULL,
                    reasoning TEXT,
                    confidence REAL,
                    context_hash TEXT,
                    timestamp TEXT NOT NULL,
                    execution_time_ms REAL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_id 
                ON navigation_decisions(workflow_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON navigation_decisions(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id 
                ON navigation_decisions(agent_id)
            """)
    
    def track_decision(self, decision: NavigationDecision) -> None:
        """Track a navigation decision"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO navigation_decisions 
                    (decision_id, workflow_id, step_id, agent_id, chosen_step, 
                     available_steps, reasoning, confidence, context_hash, 
                     timestamp, execution_time_ms, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision.decision_id,
                    decision.workflow_id,
                    decision.step_id,
                    decision.agent_id,
                    decision.chosen_step,
                    json.dumps(decision.available_steps),
                    decision.reasoning,
                    decision.confidence,
                    decision.context_hash,
                    decision.timestamp.isoformat(),
                    decision.execution_time_ms,
                    json.dumps(decision.metadata)
                ))
                
            logger.info(f"Tracked navigation decision: {decision.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to track navigation decision: {e}")
    
    def get_decisions(self, 
                     workflow_id: Optional[str] = None,
                     agent_id: Optional[str] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     limit: int = 1000) -> List[NavigationDecision]:
        """Retrieve navigation decisions with optional filtering"""
        
        query = "SELECT * FROM navigation_decisions WHERE 1=1"
        params = []
        
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
            
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
            
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
            
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        decisions = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                
                for row in cursor:
                    decision = NavigationDecision(
                        decision_id=row['decision_id'],
                        workflow_id=row['workflow_id'],
                        step_id=row['step_id'],
                        agent_id=row['agent_id'],
                        chosen_step=row['chosen_step'],
                        available_steps=json.loads(row['available_steps']),
                        reasoning=row['reasoning'],
                        confidence=row['confidence'],
                        context_hash=row['context_hash'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        execution_time_ms=row['execution_time_ms'],
                        metadata=json.loads(row['metadata'] or '{}')
                    )
                    decisions.append(decision)
                    
        except Exception as e:
            logger.error(f"Failed to retrieve navigation decisions: {e}")
            
        return decisions
    
    def get_analytics(self, 
                     workflow_id: Optional[str] = None,
                     days: int = 30) -> NavigationAnalytics:
        """Generate analytics for navigation decisions"""
        
        start_time = datetime.now() - timedelta(days=days)
        decisions = self.get_decisions(
            workflow_id=workflow_id,
            start_time=start_time,
            limit=10000
        )
        
        if not decisions:
            return NavigationAnalytics(
                total_decisions=0,
                avg_confidence=0.0,
                most_common_paths=[],
                decision_patterns={},
                performance_metrics={},
                optimization_suggestions=[]
            )
        
        # Calculate analytics
        total_decisions = len(decisions)
        avg_confidence = sum(d.confidence for d in decisions) / total_decisions
        
        # Find most common paths
        path_counts = {}
        for decision in decisions:
            path = f"{decision.step_id} -> {decision.chosen_step}"
            path_counts[path] = path_counts.get(path, 0) + 1
        
        most_common_paths = [
            {"path": path, "count": count, "percentage": (count / total_decisions) * 100}
            for path, count in sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Decision patterns
        step_patterns = {}
        for decision in decisions:
            step = decision.step_id
            if step not in step_patterns:
                step_patterns[step] = {
                    "total_decisions": 0,
                    "avg_confidence": 0.0,
                    "most_chosen": {},
                    "avg_execution_time": 0.0
                }
            
            pattern = step_patterns[step]
            pattern["total_decisions"] += 1
            pattern["avg_confidence"] = (
                (pattern["avg_confidence"] * (pattern["total_decisions"] - 1) + decision.confidence) 
                / pattern["total_decisions"]
            )
            pattern["avg_execution_time"] = (
                (pattern["avg_execution_time"] * (pattern["total_decisions"] - 1) + decision.execution_time_ms) 
                / pattern["total_decisions"]
            )
            
            chosen = decision.chosen_step
            pattern["most_chosen"][chosen] = pattern["most_chosen"].get(chosen, 0) + 1
        
        # Performance metrics
        performance_metrics = {
            "avg_execution_time_ms": sum(d.execution_time_ms for d in decisions) / total_decisions,
            "min_execution_time_ms": min(d.execution_time_ms for d in decisions),
            "max_execution_time_ms": max(d.execution_time_ms for d in decisions),
            "low_confidence_decisions": len([d for d in decisions if d.confidence < 0.5]),
            "high_confidence_decisions": len([d for d in decisions if d.confidence >= 0.8])
        }
        
        # Generate optimization suggestions
        optimization_suggestions = []
        
        if avg_confidence < 0.6:
            optimization_suggestions.append(
                "Consider improving step descriptions or context to increase agent confidence"
            )
        
        if performance_metrics["avg_execution_time_ms"] > 1000:
            optimization_suggestions.append(
                "Navigation decisions are taking longer than expected - consider optimizing step evaluation"
            )
        
        if performance_metrics["low_confidence_decisions"] > total_decisions * 0.3:
            optimization_suggestions.append(
                "High number of low-confidence decisions - review step conditions and context"
            )
        
        # Check for potential infinite loops
        repeated_paths = [p for p in most_common_paths if p["percentage"] > 50]
        if repeated_paths:
            optimization_suggestions.append(
                "Potential loop detected - review workflow logic to prevent infinite cycles"
            )
        
        return NavigationAnalytics(
            total_decisions=total_decisions,
            avg_confidence=avg_confidence,
            most_common_paths=most_common_paths,
            decision_patterns=step_patterns,
            performance_metrics=performance_metrics,
            optimization_suggestions=optimization_suggestions
        )
    
    def get_decision_history(self, workflow_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get decision history for a specific workflow"""
        decisions = self.get_decisions(workflow_id=workflow_id, limit=limit)
        
        return [
            {
                "timestamp": d.timestamp.isoformat(),
                "step_id": d.step_id,
                "chosen_step": d.chosen_step,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "execution_time_ms": d.execution_time_ms
            }
            for d in decisions
        ]
    
    def export_analytics(self, filepath: str, workflow_id: Optional[str] = None):
        """Export analytics to JSON file"""
        analytics = self.get_analytics(workflow_id=workflow_id)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "analytics": asdict(analytics)
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Analytics exported to {filepath}")
    
    def clear_old_decisions(self, days: int = 90):
        """Clear old navigation decisions to manage database size"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM navigation_decisions WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                deleted_count = cursor.rowcount
                
            logger.info(f"Cleared {deleted_count} old navigation decisions")
            
        except Exception as e:
            logger.error(f"Failed to clear old decisions: {e}") 