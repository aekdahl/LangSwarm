"""
Enhanced Session Storage System
===============================

Leverages existing _langswarm memory adapters to provide advanced session storage
capabilities including semantic search, vector storage, and cloud backends.
"""

import json
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .storage import SessionStorage
from .models import LangSwarmSession, SessionMetadata, SessionStatus, ConversationMessage, MessageRole
from langswarm.memory.adapters.database_adapter import DatabaseAdapter


class EnhancedSessionStorage(SessionStorage):
    """
    Enhanced session storage that leverages _langswarm database adapters
    for advanced capabilities like semantic search of conversation history
    """
    
    def __init__(
        self,
        adapter: DatabaseAdapter,
        session_collection: str = "sessions",
        history_collection: str = "conversation_history"
    ):
        """
        Initialize enhanced session storage
        
        Args:
            adapter: Database adapter from _langswarm memory adapters
            session_collection: Collection name for session metadata
            history_collection: Collection name for conversation history
        """
        self.adapter = adapter
        self.session_collection = session_collection
        self.history_collection = history_collection
    
    def save_session(self, session: LangSwarmSession) -> bool:
        """Save session with enhanced storage capabilities"""
        try:
            # Save session metadata
            session_doc = {
                "key": f"session:{session.session_id}",
                "text": f"Session {session.session_id} for user {session.user_id}",
                "metadata": {
                    "type": "session",
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "provider": session.provider,
                    "model": session.model,
                    "status": session.metadata.status.value,
                    "created_at": session.metadata.created_at.isoformat(),
                    "updated_at": session.metadata.updated_at.isoformat(),
                    "message_count": session.message_count,
                    "session_data": json.dumps(session.to_dict())
                }
            }
            
            # Save conversation messages grouped as conversation pairs for BigQuery compatibility
            conversation_docs = []
            
            # Group messages into conversation pairs (user + assistant)
            conversation_pairs = self._group_messages_into_pairs(session.history.messages)
            
            for pair in conversation_pairs:
                if pair["user_message"] and pair["assistant_message"]:
                    # Create conversation pair document with user_input and agent_response
                    conversation_docs.append({
                        "key": f"conversation:{pair['user_message'].id}_{pair['assistant_message'].id}",
                        "text": f"{pair['user_message'].content} -> {pair['assistant_message'].content}",
                        "metadata": {
                            "type": "conversation",
                            "session_id": session.session_id,
                            "user_message_id": pair["user_message"].id,
                            "assistant_message_id": pair["assistant_message"].id,
                            "user_timestamp": pair["user_message"].timestamp.isoformat(),
                            "assistant_timestamp": pair["assistant_message"].timestamp.isoformat(),
                            "user_id": session.user_id,
                            "provider": session.provider,
                            "model": session.model
                        },
                        # These fields are crucial for BigQuery compatibility
                        "user_input": pair["user_message"].content,
                        "agent_response": pair["assistant_message"].content
                    })
                
                # Also save individual messages for completeness (optional)
                elif pair["user_message"]:
                    # Orphaned user message (no assistant response yet)
                    conversation_docs.append({
                        "key": f"message:{pair['user_message'].id}",
                        "text": pair["user_message"].content,
                        "metadata": {
                            "type": "message",
                            "session_id": session.session_id,
                            "message_id": pair["user_message"].id,
                            "role": pair["user_message"].role.value,
                            "timestamp": pair["user_message"].timestamp.isoformat(),
                            "user_id": session.user_id,
                            "provider": session.provider,
                            "model": session.model
                        },
                        "user_input": pair["user_message"].content,
                        "agent_response": None  # No response yet
                    })
            
            # Store in database adapter
            all_docs = [session_doc] + conversation_docs
            self.adapter.add_documents(all_docs)
            
            return True
        except Exception as e:
            print(f"Error saving enhanced session {session.session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """Load session with enhanced retrieval"""
        try:
            # Query for session metadata
            results = self.adapter.query(
                query=f"session:{session_id}",
                filters={
                    "conditions": [
                        {"field": "type", "operator": "==", "value": "session"},
                        {"field": "session_id", "operator": "==", "value": session_id}
                    ]
                },
                k=1
            )
            
            if results:
                session_data = json.loads(results[0]["metadata"]["session_data"])
                return LangSwarmSession.from_dict(session_data)
                
        except Exception as e:
            print(f"Error loading enhanced session {session_id}: {e}")
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and all related messages"""
        try:
            # Get all documents for this session
            results = self.adapter.query(
                query=session_id,
                filters={
                    "conditions": [
                        {"field": "session_id", "operator": "==", "value": session_id}
                    ]
                },
                k=1000  # Get all related documents
            )
            
            # Delete all documents
            doc_ids = [doc["id"] for doc in results]
            self.adapter.delete(doc_ids)
            
            return len(doc_ids) > 0
        except Exception as e:
            print(f"Error deleting enhanced session {session_id}: {e}")
            return False
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[SessionMetadata]:
        """List sessions with enhanced filtering"""
        try:
            filters = {
                "conditions": [
                    {"field": "type", "operator": "==", "value": "session"}
                ]
            }
            
            if user_id:
                filters["conditions"].append(
                    {"field": "user_id", "operator": "==", "value": user_id}
                )
            
            if status:
                filters["conditions"].append(
                    {"field": "status", "operator": "==", "value": status.value}
                )
            
            results = self.adapter.query(
                query="session metadata",
                filters=filters,
                k=limit
            )
            
            sessions = []
            for result in results:
                session_data = json.loads(result["metadata"]["session_data"])
                sessions.append(SessionMetadata.from_dict(session_data["metadata"]))
            
            return sessions
        except Exception as e:
            print(f"Error listing enhanced sessions: {e}")
            return []
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata"""
        session = self.load_session(session_id)
        if session:
            for key, value in metadata.items():
                if hasattr(session.metadata, key):
                    setattr(session.metadata, key, value)
            
            if "updated_at" not in metadata:
                session.metadata.updated_at = datetime.now()
            
            return self.save_session(session)
        return False
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions"""
        try:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            # Find expired sessions
            results = self.adapter.query(
                query="expired sessions",
                filters={
                    "conditions": [
                        {"field": "type", "operator": "==", "value": "session"},
                        {"field": "updated_at", "operator": "<=", "value": cutoff.isoformat()}
                    ]
                },
                k=1000
            )
            
            # Delete expired sessions
            deleted_count = 0
            for result in results:
                session_id = result["metadata"]["session_id"]
                if self.delete_session(session_id):
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up enhanced sessions: {e}")
            return 0
    
    def search_conversation_history(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        🔥 NEW CAPABILITY: Semantic search across conversation history
        """
        try:
            filters = {
                "conditions": [
                    {"field": "type", "operator": "==", "value": "message"}
                ]
            }
            
            if user_id:
                filters["conditions"].append(
                    {"field": "user_id", "operator": "==", "value": user_id}
                )
            
            if session_id:
                filters["conditions"].append(
                    {"field": "session_id", "operator": "==", "value": session_id}
                )
            
            results = self.adapter.query(
                query=query,
                filters=filters,
                k=limit
            )
            
            return [
                {
                    "content": result["text"],
                    "session_id": result["metadata"]["session_id"],
                    "role": result["metadata"]["role"],
                    "timestamp": result["metadata"]["timestamp"],
                    "relevance_score": result.get("relevance_score"),
                    "context": {
                        "user_id": result["metadata"]["user_id"],
                        "provider": result["metadata"]["provider"],
                        "model": result["metadata"]["model"]
                    }
                }
                for result in results
            ]
        except Exception as e:
            print(f"Error searching conversation history: {e}")
            return []
    
    def get_conversation_analytics(
        self,
        user_id: Optional[str] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        🔥 NEW CAPABILITY: Advanced conversation analytics
        """
        try:
            cutoff = datetime.now() - timedelta(days=time_range_days)
            
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
            
            results = self.adapter.query(
                query="conversation analytics",
                filters=filters,
                k=10000  # Get all messages in range
            )
            
            # Analyze results
            total_messages = len(results)
            providers = {}
            roles = {}
            sessions = set()
            
            for result in results:
                metadata = result["metadata"]
                provider = metadata["provider"]
                role = metadata["role"]
                session_id = metadata["session_id"]
                
                providers[provider] = providers.get(provider, 0) + 1
                roles[role] = roles.get(role, 0) + 1
                sessions.add(session_id)
            
            return {
                "time_range_days": time_range_days,
                "total_messages": total_messages,
                "unique_sessions": len(sessions),
                "provider_distribution": providers,
                "role_distribution": roles,
                "average_messages_per_session": total_messages / len(sessions) if sessions else 0
            }
        except Exception as e:
            print(f"Error getting conversation analytics: {e}")
            return {}
    
    def _group_messages_into_pairs(self, messages):
        """
        Group conversation messages into user/assistant pairs for BigQuery compatibility.
        
        Returns list of pairs: [{"user_message": msg1, "assistant_message": msg2}, ...]
        """
        from langswarm.core.session.models import MessageRole
        
        pairs = []
        current_user_message = None
        
        for message in messages:
            if message.role == MessageRole.USER:
                # Save previous user message if it didn't get a response
                if current_user_message:
                    pairs.append({
                        "user_message": current_user_message,
                        "assistant_message": None
                    })
                
                # Start new conversation pair
                current_user_message = message
                
            elif message.role == MessageRole.ASSISTANT:
                if current_user_message:
                    # Complete the conversation pair
                    pairs.append({
                        "user_message": current_user_message,
                        "assistant_message": message
                    })
                    current_user_message = None
                else:
                    # Orphaned assistant message (no user message)
                    pairs.append({
                        "user_message": None,
                        "assistant_message": message
                    })
            
            # Skip SYSTEM messages for now as they're not part of user/assistant conversations
        
        # Handle final user message without response
        if current_user_message:
            pairs.append({
                "user_message": current_user_message,
                "assistant_message": None
            })
        
        return pairs


class EnhancedSessionStorageFactory:
    """Factory for creating enhanced session storage with different adapters"""
    
    @classmethod
    def create_chromadb_storage(
        cls,
        collection_name: str = "langswarm_sessions",
        persist_directory: Optional[str] = None
    ) -> EnhancedSessionStorage:
        """Create ChromaDB-based enhanced session storage"""
        from langswarm.memory.adapters._langswarm.chromadb.main import ChromaDBAdapter
        
        adapter = ChromaDBAdapter(
            identifier="session_storage",
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        return EnhancedSessionStorage(adapter)
    
    @classmethod
    def create_sqlite_storage(
        cls,
        db_path: str = "enhanced_sessions.db"
    ) -> EnhancedSessionStorage:
        """Create enhanced SQLite-based session storage"""
        from langswarm.memory.adapters._langswarm.sqlite.main import SQLiteAdapter
        
        adapter = SQLiteAdapter(
            identifier="session_storage",
            db_path=db_path
        )
        
        return EnhancedSessionStorage(adapter)
    
    @classmethod
    def create_redis_storage(
        cls,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0
    ) -> EnhancedSessionStorage:
        """Create Redis-based enhanced session storage"""
        from langswarm.memory.adapters._langswarm.redis.main import RedisAdapter
        
        adapter = RedisAdapter(
            identifier="session_storage",
            host=host,
            port=port,
            db=db
        )
        
        return EnhancedSessionStorage(adapter)
    
    @classmethod  
    def create_qdrant_storage(
        cls,
        url: str = "http://localhost:6333",
        collection_name: str = "langswarm_sessions"
    ) -> EnhancedSessionStorage:
        """Create Qdrant-based enhanced session storage"""
        from langswarm.memory.adapters._langswarm.qdrant.main import QdrantAdapter
        
        adapter = QdrantAdapter(
            identifier="session_storage",
            url=url,
            collection_name=collection_name
        )
        
        return EnhancedSessionStorage(adapter) 