"""
Action Discovery Engine
======================

Analyzes memory content to discover actionable items like tasks, reminders,
follow-ups, and other actions using NLP and pattern matching
"""

import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .action_queue import ActionItem, ActionPriority, ActionStatus


@dataclass
class ActionPattern:
    """Pattern for discovering actions in text"""
    pattern: str
    action_type: str
    priority: ActionPriority
    keywords: List[str]
    negative_keywords: List[str] = None


class ActionDiscoveryEngine:
    """
    Engine for discovering actions from memory content
    """
    
    def __init__(self):
        """Initialize action discovery engine"""
        self.patterns = self._load_action_patterns()
        self.priority_keywords = self._load_priority_keywords()
        self.time_patterns = self._load_time_patterns()
    
    def _load_action_patterns(self) -> List[ActionPattern]:
        """Load predefined action patterns"""
        return [
            # Task patterns
            ActionPattern(
                pattern=r"(?:need to|should|must|have to|todo|task)\s+(.+?)(?:\.|$|,)",
                action_type="task",
                priority=ActionPriority.MEDIUM,
                keywords=["need to", "should", "must", "have to", "todo", "task"],
                negative_keywords=["don't need", "shouldn't", "mustn't"]
            ),
            
            # Reminder patterns
            ActionPattern(
                pattern=r"(?:remind|remember|don't forget)\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\.|$|,)",
                action_type="reminder",
                priority=ActionPriority.MEDIUM,
                keywords=["remind", "remember", "don't forget"],
                negative_keywords=["reminded", "remembered"]
            ),
            
            # Follow-up patterns
            ActionPattern(
                pattern=r"(?:follow up|check back|circle back|get back)\s+(?:on\s+|with\s+)?(.+?)(?:\.|$|,)",
                action_type="follow_up",
                priority=ActionPriority.MEDIUM,
                keywords=["follow up", "check back", "circle back", "get back"]
            ),
            
            # Meeting patterns
            ActionPattern(
                pattern=r"(?:schedule|book|arrange|plan)\s+(?:a\s+)?(?:meeting|call|discussion)\s+(?:with\s+)?(.+?)(?:\.|$|,)",
                action_type="meeting",
                priority=ActionPriority.MEDIUM,
                keywords=["schedule", "book", "arrange", "plan meeting", "plan call"]
            ),
            
            # Research patterns
            ActionPattern(
                pattern=r"(?:research|look into|investigate|find out)\s+(?:about\s+)?(.+?)(?:\.|$|,)",
                action_type="research",
                priority=ActionPriority.LOW,
                keywords=["research", "look into", "investigate", "find out"]
            ),
            
            # Decision patterns
            ActionPattern(
                pattern=r"(?:decide|choose|determine|figure out)\s+(?:on\s+|about\s+)?(.+?)(?:\.|$|,)",
                action_type="decision",
                priority=ActionPriority.HIGH,
                keywords=["decide", "choose", "determine", "figure out"]
            ),
            
            # Review patterns
            ActionPattern(
                pattern=r"(?:review|check|examine|analyze)\s+(.+?)(?:\.|$|,)",
                action_type="review",
                priority=ActionPriority.MEDIUM,
                keywords=["review", "check", "examine", "analyze"]
            )
        ]
    
    def _load_priority_keywords(self) -> Dict[ActionPriority, List[str]]:
        """Load keywords that indicate action priority"""
        return {
            ActionPriority.URGENT: [
                "urgent", "asap", "immediately", "critical", "emergency",
                "now", "today", "deadline", "due", "overdue"
            ],
            ActionPriority.HIGH: [
                "important", "high priority", "priority", "soon", "quickly",
                "this week", "by friday", "by tomorrow"
            ],
            ActionPriority.MEDIUM: [
                "medium priority", "normal", "regular", "when possible",
                "next week", "sometime"
            ],
            ActionPriority.LOW: [
                "low priority", "eventually", "someday", "when convenient",
                "nice to have", "optional", "if time permits"
            ]
        }
    
    def _load_time_patterns(self) -> List[Dict[str, Any]]:
        """Load time-based patterns for due dates"""
        return [
            {"pattern": r"by\s+(tomorrow|today)", "days": 1},
            {"pattern": r"by\s+(?:the\s+end\s+of\s+)?(?:this\s+)?week", "days": 7},
            {"pattern": r"by\s+(?:the\s+end\s+of\s+)?(?:next\s+)?week", "days": 14},
            {"pattern": r"by\s+(?:the\s+end\s+of\s+)?(?:this\s+)?month", "days": 30},
            {"pattern": r"in\s+(\d+)\s+days?", "capture_days": True},
            {"pattern": r"in\s+(\d+)\s+weeks?", "capture_weeks": True},
        ]
    
    def discover_actions(
        self,
        content: str,
        user_id: Optional[str] = None,
        memory_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ActionItem]:
        """
        Discover actions from content
        
        Args:
            content: Text content to analyze
            user_id: User ID for the actions
            memory_id: Memory ID that generated the actions
            context: Additional context information
            
        Returns:
            List of discovered ActionItem objects
        """
        if not content or not content.strip():
            return []
        
        discovered_actions = []
        content_lower = content.lower()
        
        for pattern in self.patterns:
            # Check if any negative keywords are present
            if pattern.negative_keywords and any(nk in content_lower for nk in pattern.negative_keywords):
                continue
            
            # Check if any positive keywords are present
            if not any(keyword in content_lower for keyword in pattern.keywords):
                continue
            
            # Find matches using regex
            matches = re.finditer(pattern.pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Extract action description
                action_description = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                if len(action_description) < 3:  # Skip very short matches
                    continue
                
                # Determine priority
                priority = self._determine_priority(content, pattern.priority)
                
                # Extract due date if present
                due_date = self._extract_due_date(content)
                
                # Create action item
                action = ActionItem(
                    id=f"action_{uuid.uuid4().hex[:8]}",
                    type=pattern.action_type,
                    title=self._clean_action_title(action_description),
                    description=f"Discovered from: {content[:100]}...",
                    priority=priority,
                    status=ActionStatus.PENDING,
                    user_id=user_id,
                    memory_id=memory_id,
                    due_date=due_date,
                    metadata={
                        "source": "memory_content",
                        "discovery_pattern": pattern.pattern,
                        "context": context or {}
                    }
                )
                
                discovered_actions.append(action)
        
        # Remove duplicates based on similar titles
        return self._deduplicate_actions(discovered_actions)
    
    def _determine_priority(self, content: str, default_priority: ActionPriority) -> ActionPriority:
        """Determine action priority based on content analysis"""
        content_lower = content.lower()
        
        # Check for explicit priority keywords
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return priority
        
        # Context-based priority adjustment
        if any(word in content_lower for word in ["deadline", "due", "urgent", "critical"]):
            return ActionPriority.HIGH
        
        if any(word in content_lower for word in ["eventually", "someday", "maybe"]):
            return ActionPriority.LOW
        
        return default_priority
    
    def _extract_due_date(self, content: str) -> Optional[datetime]:
        """Extract due date from content"""
        content_lower = content.lower()
        
        for time_pattern in self.time_patterns:
            pattern = time_pattern["pattern"]
            match = re.search(pattern, content_lower)
            
            if match:
                if "days" in time_pattern:
                    days = time_pattern["days"]
                elif "capture_days" in time_pattern and time_pattern["capture_days"]:
                    days = int(match.group(1))
                elif "capture_weeks" in time_pattern and time_pattern["capture_weeks"]:
                    days = int(match.group(1)) * 7
                else:
                    continue
                
                return datetime.utcnow() + timedelta(days=days)
        
        return None
    
    def _clean_action_title(self, title: str) -> str:
        """Clean and format action title"""
        # Remove common prefixes
        title = re.sub(r"^(to\s+|that\s+|we\s+)", "", title, flags=re.IGNORECASE)
        
        # Capitalize first letter
        title = title[0].upper() + title[1:] if title else ""
        
        # Remove trailing punctuation
        title = title.rstrip(".,;:")
        
        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title
    
    def _deduplicate_actions(self, actions: List[ActionItem]) -> List[ActionItem]:
        """Remove duplicate actions based on similar titles"""
        if not actions:
            return actions
        
        unique_actions = []
        seen_titles = set()
        
        for action in actions:
            # Normalize title for comparison
            normalized_title = action.title.lower().strip()
            
            # Simple similarity check
            is_duplicate = False
            for seen_title in seen_titles:
                if self._are_titles_similar(normalized_title, seen_title):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_actions.append(action)
                seen_titles.add(normalized_title)
        
        return unique_actions
    
    def _are_titles_similar(self, title1: str, title2: str, threshold: float = 0.4) -> bool:
        """Check if two titles are similar using simple word overlap"""
        words1 = set(word.lower() for word in title1.split() if len(word) > 2)
        words2 = set(word.lower() for word in title2.split() if len(word) > 2)
        
        if not words1 or not words2:
            return len(title1) > 0 and len(title2) > 0 and title1.lower() == title2.lower()
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def analyze_content_patterns(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for patterns and insights
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with pattern analysis results
        """
        content_lower = content.lower()
        
        analysis = {
            "action_indicators": 0,
            "priority_indicators": [],
            "time_indicators": [],
            "sentiment": "neutral",
            "complexity": "medium",
            "confidence": 0.5
        }
        
        # Count action indicators
        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword in content_lower:
                    analysis["action_indicators"] += 1
        
        # Identify priority indicators
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    analysis["priority_indicators"].append(priority.value)
        
        # Identify time indicators
        for time_pattern in self.time_patterns:
            if re.search(time_pattern["pattern"], content_lower):
                analysis["time_indicators"].append(time_pattern["pattern"])
        
        # Simple sentiment analysis
        positive_words = ["good", "great", "excellent", "positive", "happy", "excited"]
        negative_words = ["bad", "terrible", "negative", "sad", "worried", "concerned"]
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            analysis["sentiment"] = "positive"
        elif negative_count > positive_count:
            analysis["sentiment"] = "negative"
        
        # Determine complexity
        word_count = len(content.split())
        if word_count < 20:
            analysis["complexity"] = "low"
        elif word_count > 100:
            analysis["complexity"] = "high"
        
        # Calculate confidence
        confidence_factors = [
            analysis["action_indicators"] > 0,
            len(analysis["priority_indicators"]) > 0,
            len(analysis["time_indicators"]) > 0,
            word_count > 10
        ]
        
        analysis["confidence"] = sum(confidence_factors) / len(confidence_factors)
        
        return analysis


# Global action discovery engine instance
_discovery_engine = None


def get_action_discovery_engine() -> ActionDiscoveryEngine:
    """
    Get or create the global action discovery engine
    
    Returns:
        ActionDiscoveryEngine instance
    """
    global _discovery_engine
    
    if _discovery_engine is None:
        _discovery_engine = ActionDiscoveryEngine()
    
    return _discovery_engine


def discover_actions_from_content(
    content: str,
    user_id: Optional[str] = None,
    memory_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> List[ActionItem]:
    """
    Convenience function to discover actions from content
    
    Args:
        content: Text content to analyze
        user_id: User ID for the actions
        memory_id: Memory ID that generated the actions
        context: Additional context information
        
    Returns:
        List of discovered ActionItem objects
    """
    engine = get_action_discovery_engine()
    return engine.discover_actions(content, user_id, memory_id, context) 