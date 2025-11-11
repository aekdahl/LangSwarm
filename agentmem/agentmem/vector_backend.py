"""
AgentMem Vector-Enabled Memory Backend

Memory backend that integrates native vector stores.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict

from .interfaces import (
    IMemorySession, IMemoryBackend, 
    Message, MessageRole, SessionMetadata, SessionStatus,
    ConversationSummary, MemoryUsage, MemoryBackendType
)
from .base import BaseMemoryBackend
from .vector_stores import (
    IVectorStore, VectorDocument, VectorQuery, VectorStoreFactory,
    IEmbeddingProvider
)


logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider:
    """
    Native OpenAI embedding provider that replaces LangChain embeddings.
    
    Direct API integration without LangChain dependencies.
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library required. Install with: pip install openai")
        
        self.model = model
        self._dimension = self._get_model_dimension(model)
        
        logger.debug(f"Initialized OpenAI embedding provider: {model}")
    
    def _get_model_dimension(self, model: str) -> int:
        """Get embedding dimension for model"""
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(model, 1536)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


class VectorMemoryBackend(BaseMemoryBackend):
    """
    Vector-enabled memory backend using native vector stores.
    
    Replaces LangChain/LlamaIndex memory adapters with V2 native
    implementations for better performance and control.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize vector memory backend.
        
        Args:
            config: Backend configuration including vector store and embedding settings
        """
        super().__init__(config)
        
        # Extract configuration
        self.vector_config = config.get("vector_store", {})
        self.embedding_config = config.get("embedding", {})
        self.enable_semantic_search = config.get("enable_semantic_search", True)
        
        # Initialize components
        self.vector_store: Optional[IVectorStore] = None
        self.embedding_provider: Optional[OpenAIEmbeddingProvider] = None
        
        # Session storage (non-vector data)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized vector memory backend")
    
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.EXTERNAL_DB  # Vector stores are external
    
    async def connect(self) -> bool:
        """Connect to vector store and embedding provider"""
        # Initialize embedding provider
        if self.enable_semantic_search and self.embedding_config:
            provider_type = self.embedding_config.get("provider", "openai")
            
            if provider_type == "openai":
                api_key = self.embedding_config.get("api_key")
                model = self.embedding_config.get("model", "text-embedding-3-small")
                
                if not api_key:
                    raise ValueError(
                        "OpenAI API key is required for vector memory backend with semantic search. "
                        "Provide 'api_key' in embedding configuration or disable semantic search."
                    )
                
                try:
                    self.embedding_provider = OpenAIEmbeddingProvider(api_key, model)
                    logger.info(f"Connected to OpenAI embedding provider: {model}")
                except Exception as e:
                    raise ConnectionError(f"Failed to initialize OpenAI embedding provider: {e}") from e
            else:
                raise ValueError(f"Unsupported embedding provider: {provider_type}. Supported: 'openai'")
        
        # Initialize vector store
        if self.enable_semantic_search and self.vector_config and self.embedding_provider:
            store_type = self.vector_config.get("store_type", "sqlite")
            embedding_dimension = self.embedding_provider.get_dimension()
            connection_params = self.vector_config.get("connection_params", {})
            
            try:
                self.vector_store = VectorStoreFactory.create_store(
                    store_type=store_type,
                    embedding_dimension=embedding_dimension,
                    connection_params=connection_params
                )
                
                # Connect to vector store
                await self.vector_store.connect()
                logger.info(f"Connected to {store_type} vector store")
            except Exception as e:
                raise ConnectionError(
                    f"Failed to initialize {store_type} vector store: {e}. "
                    f"Check configuration and ensure the vector store service is accessible."
                ) from e
        elif self.enable_semantic_search:
            if not self.vector_config:
                raise ValueError("Vector store configuration is required when semantic search is enabled")
            if not self.embedding_provider:
                raise ValueError("Embedding provider is required when semantic search is enabled")
        
        self._connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect from vector store and embedding provider"""
        try:
            if self.vector_store:
                await self.vector_store.disconnect()
            
            self.vector_store = None
            self.embedding_provider = None
            self._connected = False
            
            logger.info("Disconnected from vector memory backend")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from vector memory backend: {e}")
            return False
    
    async def save_session(self, session_id: str, messages: List[Message], 
                          metadata: SessionMetadata) -> bool:
        """Save session with optional vector indexing"""
        try:
            # Save session metadata and messages
            session_data = {
                "session_id": session_id,
                "messages": [asdict(msg) for msg in messages],
                "metadata": asdict(metadata),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self._sessions[session_id] = session_data
            
            # Index messages in vector store if enabled
            if self.enable_semantic_search and self.vector_store and self.embedding_provider:
                await self._index_messages(session_id, messages)
            
            logger.debug(f"Saved session {session_id} with {len(messages)} messages")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False
    
    async def load_session(self, session_id: str) -> Optional[tuple[List[Message], SessionMetadata]]:
        """Load session data"""
        try:
            if session_id not in self._sessions:
                return None
            
            session_data = self._sessions[session_id]
            
            # Reconstruct messages
            messages = []
            for msg_data in session_data["messages"]:
                msg_data["timestamp"] = datetime.fromisoformat(msg_data["timestamp"])
                messages.append(Message(**msg_data))
            
            # Reconstruct metadata
            metadata_data = session_data["metadata"]
            metadata_data["created_at"] = datetime.fromisoformat(metadata_data["created_at"])
            if metadata_data.get("last_accessed"):
                metadata_data["last_accessed"] = datetime.fromisoformat(metadata_data["last_accessed"])
            
            metadata = SessionMetadata(**metadata_data)
            
            return messages, metadata
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and its vector data"""
        try:
            # Remove from session storage
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            # Remove from vector store
            if self.vector_store:
                # Get message IDs to delete
                doc_ids = await self.vector_store.list_documents(
                    filters={"session_id": session_id}
                )
                
                if doc_ids:
                    await self.vector_store.delete_documents(doc_ids)
            
            logger.debug(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(self, user_id: Optional[str] = None, 
                           status: Optional[SessionStatus] = None,
                           limit: int = 100) -> List[SessionMetadata]:
        """List sessions with optional filtering"""
        try:
            sessions = []
            count = 0
            
            for session_data in self._sessions.values():
                if count >= limit:
                    break
                
                metadata_data = session_data["metadata"]
                
                # Filter by user_id
                if user_id and metadata_data.get("user_id") != user_id:
                    continue
                
                # Filter by status
                if status and SessionStatus(metadata_data.get("status")) != status:
                    continue
                
                # Reconstruct metadata
                metadata_data["created_at"] = datetime.fromisoformat(metadata_data["created_at"])
                if metadata_data.get("last_accessed"):
                    metadata_data["last_accessed"] = datetime.fromisoformat(metadata_data["last_accessed"])
                
                metadata = SessionMetadata(**metadata_data)
                sessions.append(metadata)
                count += 1
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    async def search_messages(self, query: str, session_id: Optional[str] = None,
                             limit: int = 10) -> List[Message]:
        """
        Semantic search through messages using vector similarity.
        
        This replaces LangChain/LlamaIndex semantic search with native implementation.
        """
        try:
            if not (self.enable_semantic_search and self.vector_store and self.embedding_provider):
                logger.warning("Semantic search not enabled, falling back to text search")
                return await self._text_search_messages(query, session_id, limit)
            
            # Generate query embedding
            query_embedding = await self.embedding_provider.embed_text(query)
            
            # Build vector query
            filters = {"session_id": session_id} if session_id else None
            vector_query = VectorQuery(
                embedding=query_embedding,
                top_k=limit,
                filters=filters,
                include_metadata=True,
                include_content=True
            )
            
            # Execute vector search
            results = await self.vector_store.query(vector_query)
            
            # Convert results back to messages
            messages = []
            for result in results:
                try:
                    message_data = json.loads(result.metadata.get("message_data", "{}"))
                    message_data["timestamp"] = datetime.fromisoformat(message_data["timestamp"])
                    
                    message = Message(**message_data)
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning(f"Failed to reconstruct message from vector result: {e}")
                    continue
            
            logger.debug(f"Vector search for '{query}' returned {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []
    
    async def _index_messages(self, session_id: str, messages: List[Message]):
        """Index messages in vector store for semantic search"""
        try:
            if not (self.vector_store and self.embedding_provider):
                return
            
            # Create vector documents for messages
            documents = []
            texts_to_embed = []
            
            for message in messages:
                if message.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                    texts_to_embed.append(message.content)
            
            if not texts_to_embed:
                return
            
            # Generate embeddings in batch
            embeddings = await self.embedding_provider.embed_batch(texts_to_embed)
            
            # Create vector documents
            embedding_idx = 0
            for message in messages:
                if message.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                    doc_id = f"{session_id}_{message.id}"
                    
                    document = VectorDocument(
                        id=doc_id,
                        content=message.content,
                        embedding=embeddings[embedding_idx],
                        metadata={
                            "session_id": session_id,
                            "message_id": message.id,
                            "role": message.role.value,
                            "timestamp": message.timestamp.isoformat(),
                            "message_data": json.dumps(asdict(message), default=str)
                        }
                    )
                    
                    documents.append(document)
                    embedding_idx += 1
            
            # Index documents
            if documents:
                await self.vector_store.upsert_documents(documents)
                logger.debug(f"Indexed {len(documents)} messages for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to index messages: {e}")
    
    async def _text_search_messages(self, query: str, session_id: Optional[str], 
                                   limit: int) -> List[Message]:
        """Fallback text search when vector search is not available"""
        try:
            messages = []
            query_lower = query.lower()
            count = 0
            
            for session_data in self._sessions.values():
                if count >= limit:
                    break
                
                # Filter by session if specified
                if session_id and session_data["session_id"] != session_id:
                    continue
                
                # Search through messages
                for msg_data in session_data["messages"]:
                    if count >= limit:
                        break
                    
                    if query_lower in msg_data["content"].lower():
                        msg_data["timestamp"] = datetime.fromisoformat(msg_data["timestamp"])
                        messages.append(Message(**msg_data))
                        count += 1
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to perform text search: {e}")
            return []
    
    async def get_usage_stats(self) -> MemoryUsage:
        """Get memory usage statistics"""
        try:
            total_sessions = len(self._sessions)
            total_messages = sum(len(session["messages"]) for session in self._sessions.values())
            
            # Get vector store stats if available
            vector_stats = {}
            if self.vector_store:
                vector_stats = await self.vector_store.get_stats()
            
            usage = MemoryUsage(
                total_sessions=total_sessions,
                total_messages=total_messages,
                memory_usage_mb=0.0,  # In-memory tracking not implemented
                storage_size_mb=vector_stats.get("database_size_mb", 0.0),
                backend_type=self.backend_type
            )
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return MemoryUsage(
                total_sessions=0,
                total_messages=0,
                memory_usage_mb=0.0,
                storage_size_mb=0.0,
                backend_type=self.backend_type
            )
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions"""
        try:
            cutoff_date = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)
            cleaned_count = 0
            
            sessions_to_delete = []
            for session_id, session_data in self._sessions.items():
                created_at = datetime.fromisoformat(session_data["metadata"]["created_at"])
                if created_at.timestamp() < cutoff_date:
                    sessions_to_delete.append(session_id)
            
            # Delete old sessions
            for session_id in sessions_to_delete:
                await self.delete_session(session_id)
                cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
