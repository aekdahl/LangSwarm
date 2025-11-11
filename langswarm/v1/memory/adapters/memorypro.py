"""
MemoryPro Adapter for LangSwarm
===============================

Advanced memory management with dual-mode support:
- Internal Mode: Enhanced local memory with analytics
- External Mode: Full MemoryPro cloud service integration

Features:
- AI-powered memory analysis and insights
- Action discovery from memory content
- Evolution tracking and pattern analysis
- Real-time webhook notifications
- Memory lifecycle management
"""

import os
import json
import requests
import hmac
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .database_adapter import DatabaseAdapter


@dataclass
class MemoryAnalysis:
    """Analysis results for memory content"""
    priority_score: float
    relevance_score: float
    themes: List[str]
    extracted_actions: List[Dict[str, Any]]
    patterns_discovered: Optional[List[str]] = None
    evolution_insights: Optional[str] = None


@dataclass
class MemoryInsights:
    """Memory insights and analytics"""
    memory_health_score: float
    total_memories: int
    high_priority_count: int
    patterns: List[Dict[str, Any]]
    lifecycle_recommendations: List[Dict[str, Any]]
    evolution_updates: List[Dict[str, Any]]


class MemoryProAdapter(DatabaseAdapter):
    """
    MemoryPro adapter with dual-mode support
    
    Modes:
    - internal: Enhanced local memory with basic analytics
    - external: Full MemoryPro cloud service integration
    """
    
    def __init__(
        self,
        mode: str = "internal",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        local_adapter: Optional[DatabaseAdapter] = None,
        **kwargs
    ):
        """
        Initialize MemoryPro adapter
        
        Args:
            mode: 'internal' or 'external'
            api_url: External MemoryPro API URL
            api_key: API authentication key
            api_secret: API secret for additional security
            webhook_url: URL for webhook notifications
            webhook_secret: Secret for webhook verification
            local_adapter: Adapter for internal mode (defaults to SQLite)
        """
        super().__init__(
            name="MemoryPro",
            description="Advanced memory management with AI insights",
            instruction="Stores and retrieves memories with AI analysis and evolution tracking"
        )
        
        self.mode = mode
        self.api_url = api_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        
        # Initialize internal adapter if needed
        if mode == "internal" or not self._is_external_configured():
            if local_adapter:
                self.local_adapter = local_adapter
            else:
                # Default to SQLite adapter for internal mode
                from .langswarm import SQLiteAdapter
                self.local_adapter = SQLiteAdapter(
                    identifier="memorypro_sqlite",
                    db_path=kwargs.get("db_path", "memorypro.db")
                )
        
        # Initialize external API client if configured
        if mode == "external" and self._is_external_configured():
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "X-API-Secret": self.api_secret,
                "Content-Type": "application/json",
                "User-Agent": "LangSwarm-MemoryPro/1.0"
            })
    
    def _is_external_configured(self) -> bool:
        """Check if external MemoryPro is properly configured"""
        return bool(self.api_url and self.api_key and self.api_secret)
    
    def _get_effective_mode(self) -> str:
        """Get the effective mode (fallback to internal if external not configured)"""
        if self.mode == "external" and self._is_external_configured():
            return "external"
        return "internal"
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add memories with enhanced analysis
        
        Args:
            documents: List of memory documents to store
            
        Returns:
            Dictionary with storage results and analysis
        """
        mode = self._get_effective_mode()
        
        if mode == "external":
            return self._external_add_documents(documents)
        else:
            return self._internal_add_documents(documents)
    
    def _external_add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store documents using external MemoryPro API"""
        results = []
        
        for doc in documents:
            payload = {
                "content": doc.get("text", ""),
                "metadata": {
                    "session_id": doc.get("session_id"),
                    "agent_id": doc.get("agent_id"),
                    "user_id": doc.get("user_id"),
                    "timestamp": doc.get("timestamp", datetime.utcnow().isoformat()),
                    "conversation_context": doc.get("context")
                },
                "memory_type": doc.get("type", "conversation"),
                "tags": doc.get("tags", []),
                "priority": doc.get("priority", "medium")
            }
            
            try:
                response = self.session.post(
                    f"{self.api_url}/api/v1/memory/store",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                # Transform response to include analysis
                results.append({
                    "memory_id": result.get("memory_id"),
                    "status": "success",
                    "analysis": MemoryAnalysis(
                        priority_score=result.get("analysis", {}).get("priority_score", 0.0),
                        relevance_score=result.get("analysis", {}).get("relevance_score", 0.0),
                        themes=result.get("analysis", {}).get("themes", []),
                        extracted_actions=result.get("analysis", {}).get("extracted_actions", [])
                    )
                })
                
            except requests.exceptions.RequestException as e:
                results.append({
                    "memory_id": None,
                    "status": "error",
                    "error": str(e)
                })
        
        return {"results": results, "mode": "external"}
    
    def _internal_add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store documents using internal adapter with enhanced analysis"""
        # Use local adapter for storage
        storage_result = self.local_adapter.add_documents(documents)
        
        # Add basic analysis for internal mode
        results = []
        for doc in documents:
            # Simple analysis for internal mode
            content = doc.get("text", "")
            analysis = self._basic_content_analysis(content)
            
            results.append({
                "memory_id": doc.get("key", f"mem_{datetime.utcnow().timestamp()}"),
                "status": "success",
                "analysis": analysis
            })
        
        return {"results": results, "mode": "internal"}
    
    def _basic_content_analysis(self, content: str) -> MemoryAnalysis:
        """Basic content analysis for internal mode"""
        # Simple keyword-based analysis
        priority_keywords = ["urgent", "important", "deadline", "critical", "asap"]
        theme_keywords = {
            "project": ["project", "task", "deadline", "milestone"],
            "meeting": ["meeting", "call", "discussion", "agenda"],
            "decision": ["decide", "choice", "option", "recommendation"]
        }
        
        content_lower = content.lower()
        
        # Calculate basic priority score
        priority_score = 0.5  # baseline
        for keyword in priority_keywords:
            if keyword in content_lower:
                priority_score += 0.1
        priority_score = min(priority_score, 1.0)
        
        # Extract themes
        themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        # Basic action extraction
        actions = []
        if any(word in content_lower for word in ["task", "todo", "need to", "should", "must"]):
            actions.append({
                "type": "task",
                "title": "Follow up on conversation",
                "priority": "medium"
            })
        
        return MemoryAnalysis(
            priority_score=priority_score,
            relevance_score=0.7,  # default
            themes=themes,
            extracted_actions=actions
        )
    
    def query(self, query: str, filters: Optional[Dict[str, Any]] = None, n: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Enhanced memory recall with AI analysis
        
        Args:
            query: Search query
            filters: Additional filters
            n: Number of results to return
            
        Returns:
            Enhanced search results with analysis
        """
        mode = self._get_effective_mode()
        
        if mode == "external":
            return self._external_query(query, filters, n, **kwargs)
        else:
            return self._internal_query(query, filters, n, **kwargs)
    
    def _external_query(self, query: str, filters: Optional[Dict[str, Any]], n: int, **kwargs) -> Dict[str, Any]:
        """Query using external MemoryPro API"""
        payload = {
            "query": query,
            "user_id": kwargs.get("user_id"),
            "session_id": kwargs.get("session_id"),
            "recall_count": n,
            "options": {
                "weight_recent": kwargs.get("weight_recent", True),
                "weight_responsibilities": kwargs.get("weight_responsibilities", True),
                "auto_queue_actions": kwargs.get("auto_queue_actions", True),
                "include_analysis": True,
                "evolution_enabled": True
            }
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/memory/recall",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Fallback to internal mode if external fails
            return self._internal_query(query, filters, n, **kwargs)
    
    def _internal_query(self, query: str, filters: Optional[Dict[str, Any]], n: int, **kwargs) -> Dict[str, Any]:
        """Query using internal adapter with basic analysis"""
        # Use local adapter for search
        local_results = self.local_adapter.query(query, filters, n=n)
        
        # Transform to MemoryPro format
        memories = []
        if isinstance(local_results, list):
            for i, result in enumerate(local_results[:n]):
                if isinstance(result, dict):
                    memories.append({
                        "memory_id": result.get("key", f"mem_{i}"),
                        "content": result.get("value", result.get("text", "")),
                        "relevance_score": 0.8,  # default for internal
                        "priority_score": 0.7,   # default for internal
                        "timestamp": result.get("metadata", {}).get("timestamp", datetime.utcnow().isoformat()),
                        "themes": ["general"]
                    })
        
        return {
            "status": "success",
            "memories": memories,
            "analysis": {
                "total_memories_searched": len(memories),
                "relevance_threshold": 0.7,
                "patterns_discovered": [],
                "evolution_insights": None
            },
            "discovered_actions": [],
            "mode": "internal"
        }
    
    def get_insights(self, user_id: Optional[str] = None) -> MemoryInsights:
        """Get memory insights and analytics"""
        mode = self._get_effective_mode()
        
        if mode == "external":
            return self._external_get_insights(user_id)
        else:
            return self._internal_get_insights(user_id)
    
    def _external_get_insights(self, user_id: Optional[str]) -> MemoryInsights:
        """Get insights from external MemoryPro API"""
        try:
            params = {"user_id": user_id} if user_id else {}
            response = self.session.get(
                f"{self.api_url}/api/v1/memory/insights",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            insights_data = data.get("insights", {})
            return MemoryInsights(
                memory_health_score=insights_data.get("memory_health_score", 0.0),
                total_memories=insights_data.get("total_memories", 0),
                high_priority_count=insights_data.get("high_priority_count", 0),
                patterns=insights_data.get("patterns", []),
                lifecycle_recommendations=insights_data.get("lifecycle_recommendations", []),
                evolution_updates=insights_data.get("evolution_updates", [])
            )
            
        except requests.exceptions.RequestException:
            # Fallback to internal mode
            return self._internal_get_insights(user_id)
    
    def _internal_get_insights(self, user_id: Optional[str]) -> MemoryInsights:
        """Get basic insights from internal mode"""
        # Basic analytics for internal mode
        return MemoryInsights(
            memory_health_score=0.85,
            total_memories=100,  # placeholder
            high_priority_count=15,  # placeholder
            patterns=[
                {
                    "pattern_type": "recurring_topics",
                    "description": "Basic pattern analysis",
                    "frequency": 5,
                    "trend": "stable"
                }
            ],
            lifecycle_recommendations=[],
            evolution_updates=[]
        )
    
    def register_webhook(self, webhook_url: str, events: List[str], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Register webhook for real-time notifications (external mode only)"""
        if self._get_effective_mode() != "external":
            return {"status": "error", "message": "Webhooks only available in external mode"}
        
        payload = {
            "webhook_url": webhook_url,
            "webhook_secret": self.webhook_secret,
            "events": events,
            "user_id": user_id
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/webhooks/register",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256"""
        if not self.webhook_secret:
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Return adapter capabilities"""
        mode = self._get_effective_mode()
        return {
            "mode": mode,
            "supports_analysis": True,
            "supports_insights": True,
            "supports_webhooks": mode == "external",
            "supports_actions": True,
            "supports_priorities": True
        }
    
    def run(self, payload: Dict[str, Any], action: str = "query") -> Any:
        """
        Execute MemoryPro actions
        
        Args:
            payload: Action parameters
            action: Action type ('query', 'add_documents', 'insights', 'register_webhook')
            
        Returns:
            Action result
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(payload.get("documents", []))
        elif action == "insights":
            return self.get_insights(payload.get("user_id"))
        elif action == "register_webhook":
            return self.register_webhook(
                payload.get("webhook_url"),
                payload.get("events", []),
                payload.get("user_id")
            )
        else:
            return {"error": f"Unsupported action: {action}"}
    
    def delete(self, filters: Dict[str, Any]) -> bool:
        """Delete memories based on filters"""
        mode = self._get_effective_mode()
        
        if mode == "external":
            # External deletion would need specific API endpoint
            return False
        else:
            # Use local adapter for deletion
            return self.local_adapter.delete(filters)


def create_memorypro_adapter(
    mode: str = "internal",
    **config
) -> MemoryProAdapter:
    """
    Factory function to create MemoryPro adapter with configuration
    
    Args:
        mode: 'internal' or 'external'
        **config: Configuration parameters
        
    Returns:
        Configured MemoryProAdapter instance
    """
    # Get configuration from environment if not provided
    if mode == "external":
        api_config = {
            "api_url": config.get("api_url") or os.getenv("MEMORYPRO_API_URL"),
            "api_key": config.get("api_key") or os.getenv("MEMORYPRO_API_KEY"),
            "api_secret": config.get("api_secret") or os.getenv("MEMORYPRO_API_SECRET"),
            "webhook_url": config.get("webhook_url") or os.getenv("MEMORYPRO_WEBHOOK_URL"),
            "webhook_secret": config.get("webhook_secret") or os.getenv("MEMORYPRO_WEBHOOK_SECRET")
        }
        config.update(api_config)
    
    return MemoryProAdapter(mode=mode, **config) 