"""
Hybrid Session Manager
======================

Combines basic session storage (for metadata/core functionality) with 
_langswarm adapters (for semantic search and analytics) to provide
best of both worlds without breaking existing functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from .manager import LangSwarmSessionManager
from .storage import SessionStorage
from .models import LangSwarmSession, ConversationMessage, MessageRole
from langswarm.memory.adapters.database_adapter import DatabaseAdapter


logger = logging.getLogger(__name__)


class HybridSessionManager(LangSwarmSessionManager):
    """
    Hybrid session manager that extends basic functionality with enhanced capabilities
    
    Architecture:
    - Basic Storage: Session metadata, core functionality (existing behavior)
    - Enhanced Storage: Semantic search, analytics, cross-session insights
    """
    
    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        enhanced_adapter: Optional[DatabaseAdapter] = None,
        enable_semantic_search: bool = True,
        enable_analytics: bool = True,
        **kwargs
    ):
        """
        Initialize hybrid session manager
        
        Args:
            storage: Basic session storage (existing functionality)
            enhanced_adapter: _langswarm adapter for enhanced features
            enable_semantic_search: Enable semantic search capabilities
            enable_analytics: Enable analytics and insights
        """
        # Initialize base session manager with existing functionality
        super().__init__(storage=storage, **kwargs)
        
        # Enhanced capabilities
        self.enhanced_adapter = enhanced_adapter
        self.enable_semantic_search = enable_semantic_search
        self.enable_analytics = enable_analytics
        
        # Track if enhanced features are available
        self.enhanced_available = enhanced_adapter is not None
        
        if self.enhanced_available:
            logger.info("Hybrid session manager initialized with enhanced capabilities")
        else:
            logger.info("Hybrid session manager initialized in basic mode")
    
    def create_session(self, *args, **kwargs) -> LangSwarmSession:
        """Create session with hybrid storage"""
        # Use base functionality for session creation
        session = super().create_session(*args, **kwargs)
        
        # Initialize enhanced storage for this session
        if self.enhanced_available:
            try:
                self._init_enhanced_session(session)
            except Exception as e:
                logger.warning(f"Enhanced session initialization failed: {e}")
        
        return session
    
    def add_message_to_session(
        self, 
        session_id: str, 
        content: str, 
        role: MessageRole,
        **kwargs
    ) -> Optional[ConversationMessage]:
        """Add message with hybrid storage (called from AgentWrapper)"""
        # Get session
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Add to basic storage (existing functionality)
        message = session.add_message(content, role, **kwargs)
        
        # Save to basic storage
        self.storage.save_session(session)
        
        # Add to enhanced storage for semantic search
        if self.enhanced_available and self.enable_semantic_search:
            try:
                self._add_to_enhanced_storage(session, message)
            except Exception as e:
                logger.warning(f"Enhanced storage failed: {e}")
        
        return message
    
    def search_conversation_history(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        🔥 NEW: Semantic search across conversation history
        """
        if not self.enhanced_available or not self.enable_semantic_search:
            logger.warning("Semantic search not available - enhanced adapter required")
            return []
        
        try:
            # Build filters for enhanced search
            filters = {"conditions": [{"field": "type", "operator": "==", "value": "message"}]}
            
            if user_id:
                filters["conditions"].append(
                    {"field": "user_id", "operator": "==", "value": user_id}
                )
            
            if session_id:
                filters["conditions"].append(
                    {"field": "session_id", "operator": "==", "value": session_id}
                )
            
            # Perform semantic search
            results = self.enhanced_adapter.query(
                query=query,
                filters=filters,
                k=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                try:
                    metadata = result.get("metadata", {})
                    formatted_results.append({
                        "content": result.get("text", ""),
                        "session_id": metadata.get("session_id"),
                        "role": metadata.get("role"),
                        "timestamp": metadata.get("timestamp"),
                        "user_id": metadata.get("user_id"),
                        "provider": metadata.get("provider"),
                        "model": metadata.get("model"),
                        "relevance_score": result.get("score")
                    })
                except Exception as e:
                    logger.warning(f"Error formatting search result: {e}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def get_conversation_analytics(
        self,
        user_id: Optional[str] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        🔥 NEW: Advanced conversation analytics
        """
        if not self.enhanced_available or not self.enable_analytics:
            logger.warning("Analytics not available - enhanced adapter required")
            return {}
        
        try:
            from datetime import timedelta
            
            cutoff = datetime.now() - timedelta(days=time_range_days)
            
            # Build filters
            filters = {
                "conditions": [
                    {"field": "type", "operator": "==", "value": "message"},
                    {"field": "timestamp", "operator": ">=", "value": cutoff.isoformat()}
                ]
            }
            
            if user_id:
                filters["conditions"].append(
                    {"field": "user_id", "operator": "==", "value": user_id}
                )
            
            # Get analytics data
            results = self.enhanced_adapter.query(
                query="conversation analytics",
                filters=filters,
                k=10000  # Get all messages in range
            )
            
            # Analyze results
            total_messages = len(results)
            providers = {}
            roles = {}
            sessions = set()
            topics = {}
            
            for result in results:
                try:
                    metadata = result.get("metadata", {})
                    provider = metadata.get("provider", "unknown")
                    role = metadata.get("role", "unknown")
                    session_id = metadata.get("session_id")
                    content = result.get("text", "")
                    
                    providers[provider] = providers.get(provider, 0) + 1
                    roles[role] = roles.get(role, 0) + 1
                    
                    if session_id:
                        sessions.add(session_id)
                    
                    # Simple topic extraction (could be enhanced)
                    words = content.lower().split()
                    for word in words:
                        if len(word) > 4:  # Filter short words
                            topics[word] = topics.get(word, 0) + 1
                            
                except Exception as e:
                    logger.warning(f"Error processing analytics result: {e}")
            
            # Get top topics
            top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "time_range_days": time_range_days,
                "total_messages": total_messages,
                "unique_sessions": len(sessions),
                "provider_distribution": providers,
                "role_distribution": roles,
                "top_topics": dict(top_topics),
                "average_messages_per_session": total_messages / len(sessions) if sessions else 0,
                "enhanced_features_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {"error": str(e)}
    
    def find_similar_conversations(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        🔥 NEW: Find conversations similar to current session
        """
        if not self.enhanced_available:
            return []
        
        try:
            # Get current session content
            session = self.get_session(session_id)
            if not session:
                return []
            
            # Create query from recent messages
            recent_messages = session.get_messages(limit=3)
            query_content = " ".join([msg.content for msg in recent_messages])
            
            # Search for similar conversations (excluding current session)
            filters = {
                "conditions": [
                    {"field": "type", "operator": "==", "value": "message"},
                    {"field": "session_id", "operator": "!=", "value": session_id}
                ]
            }
            
            results = self.enhanced_adapter.query(
                query=query_content,
                filters=filters,
                k=limit * 3  # Get more to deduplicate by session
            )
            
            # Group by session and get top similar sessions
            session_scores = {}
            for result in results:
                result_session = result.get("metadata", {}).get("session_id")
                if result_session and result_session != session_id:
                    score = result.get("score", 0)
                    if result_session not in session_scores or score > session_scores[result_session]["score"]:
                        session_scores[result_session] = {
                            "session_id": result_session,
                            "score": score,
                            "sample_content": result.get("text", "")[:100],
                            "user_id": result.get("metadata", {}).get("user_id"),
                            "provider": result.get("metadata", {}).get("provider")
                        }
            
            # Return top similar sessions
            similar_sessions = sorted(
                session_scores.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )[:limit]
            
            return similar_sessions
            
        except Exception as e:
            logger.error(f"Similar conversation search failed: {e}")
            return []
    
    def _init_enhanced_session(self, session: LangSwarmSession) -> None:
        """Initialize enhanced storage for a session"""
        try:
            # Add session metadata document for enhanced storage
            session_doc = {
                "key": f"session:{session.session_id}",
                "text": f"Session {session.session_id} for user {session.user_id}",
                "metadata": {
                    "type": "session",
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "provider": session.provider,
                    "model": session.model,
                    "created_at": session.metadata.created_at.isoformat()
                }
            }
            
            self.enhanced_adapter.add_documents([session_doc])
            
        except Exception as e:
            logger.warning(f"Enhanced session initialization failed: {e}")
    
    def _add_to_enhanced_storage(
        self, 
        session: LangSwarmSession, 
        message: ConversationMessage
    ) -> None:
        """Add message to enhanced storage for semantic search"""
        try:
            message_doc = {
                "key": f"message:{message.id}",
                "text": message.content,
                "metadata": {
                    "type": "message",
                    "session_id": session.session_id,
                    "message_id": message.id,
                    "role": message.role.value,
                    "timestamp": message.timestamp.isoformat(),
                    "user_id": session.user_id,
                    "provider": session.provider,
                    "model": session.model
                }
            }
            
            self.enhanced_adapter.add_documents([message_doc])
            
        except Exception as e:
            logger.warning(f"Enhanced storage for message failed: {e}")


class HybridSessionManagerFactory:
    """Factory for creating hybrid session managers with different enhanced backends"""
    
    @classmethod
    def create_hybrid_manager(
        cls,
        enhanced_backend: str = "chromadb",
        basic_storage_type: str = "sqlite",
        **kwargs
    ) -> HybridSessionManager:
        """
        Create hybrid session manager with specified backends
        
        Args:
            enhanced_backend: Backend for enhanced features (chromadb, sqlite, redis, etc.)
            basic_storage_type: Backend for basic storage (sqlite, memory)
        """
        from .storage import SessionStorageFactory
        
        # Create basic storage (existing functionality)
        basic_storage = SessionStorageFactory.create_storage(basic_storage_type, **kwargs)
        
        # Create enhanced adapter
        enhanced_adapter = None
        try:
            if enhanced_backend == "chromadb":
                enhanced_adapter = cls._create_chromadb_adapter(**kwargs)
            elif enhanced_backend == "sqlite":
                enhanced_adapter = cls._create_sqlite_adapter(**kwargs)
            elif enhanced_backend == "redis":
                enhanced_adapter = cls._create_redis_adapter(**kwargs)
            elif enhanced_backend == "qdrant":
                enhanced_adapter = cls._create_qdrant_adapter(**kwargs)
            elif enhanced_backend == "elasticsearch":
                enhanced_adapter = cls._create_elasticsearch_adapter(**kwargs)
            elif enhanced_backend == "bigquery":
                enhanced_adapter = cls._create_bigquery_adapter(**kwargs)
            elif enhanced_backend == "gcs":
                enhanced_adapter = cls._create_gcs_adapter(**kwargs)
            elif enhanced_backend == "mock":
                enhanced_adapter = cls._create_mock_adapter(**kwargs)
            else:
                logger.warning(f"Unknown enhanced backend: {enhanced_backend}")
            
        except Exception as e:
            logger.warning(f"Enhanced backend {enhanced_backend} failed to initialize: {e}")
            logger.info("Falling back to basic session management")
        
        return HybridSessionManager(
            storage=basic_storage,
            enhanced_adapter=enhanced_adapter,
            **kwargs
        )
    
    @classmethod
    def _create_chromadb_adapter(cls, **kwargs):
        """Create ChromaDB adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_chromadb_adapter(**kwargs)
    
    @classmethod  
    def _create_sqlite_adapter(cls, **kwargs):
        """Create SQLite adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_sqlite_adapter(**kwargs)
    
    @classmethod
    def _create_redis_adapter(cls, **kwargs):
        """Create Redis adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_redis_adapter(**kwargs)
    
    @classmethod
    def _create_qdrant_adapter(cls, **kwargs):
        """Create Qdrant adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_qdrant_adapter(**kwargs)
    
    @classmethod
    def _create_elasticsearch_adapter(cls, **kwargs):
        """Create Elasticsearch adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_elasticsearch_adapter(**kwargs)
    
    @classmethod
    def _create_bigquery_adapter(cls, **kwargs):
        """Create BigQuery adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_bigquery_adapter(**kwargs)
    
    @classmethod
    def _create_gcs_adapter(cls, **kwargs):
        """Create GCS adapter for enhanced features"""
        from .adapters_bridge import HybridAdapterFactory
        return HybridAdapterFactory.create_gcs_adapter(**kwargs)
    
    @classmethod
    def _create_mock_adapter(cls, **kwargs):
        """Create Mock adapter for testing"""
        from .adapters_bridge import MockSessionAdapter
        return MockSessionAdapter(**kwargs) 