"""
LangSwarm V2 Native ChromaDB Vector Store

Direct ChromaDB API integration without LangChain dependencies.
Provides better performance and control compared to LangChain abstractions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .interfaces import (
    IVectorStore, VectorDocument, VectorQuery, VectorResult, 
    VectorStoreConfig, VectorStoreError, ConnectionError, QueryError
)


logger = logging.getLogger(__name__)


class NativeChromaStore(IVectorStore):
    """
    Native ChromaDB vector store implementation.
    
    Direct integration with ChromaDB API that replaces LangChain's
    Chroma wrapper with better performance and control.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize ChromaDB store.
        
        Args:
            config: Vector store configuration with ChromaDB parameters
        """
        self.config = config
        self.client = None
        self.collection = None
        self._connected = False
        
        # Extract ChromaDB-specific config
        self.host = config.connection_params.get("host", "localhost")
        self.port = config.connection_params.get("port", 8000)
        self.collection_name = config.connection_params.get("collection_name", "langswarm_default")
        self.persist_directory = config.connection_params.get("persist_directory")
        
        logger.debug(f"Initialized ChromaDB store for collection: {self.collection_name}")
    
    async def connect(self) -> bool:
        """Connect to ChromaDB"""
        try:
            # Import ChromaDB (optional dependency)
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ConnectionError("ChromaDB not installed. Install with: pip install chromadb")
            
            # Initialize ChromaDB client
            if self.persist_directory:
                # Persistent client
                self.client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                # HTTP client or in-memory
                if self.host == "localhost" and not self.persist_directory:
                    # In-memory client for testing
                    self.client = chromadb.EphemeralClient()
                else:
                    # HTTP client
                    self.client = chromadb.HttpClient(
                        host=self.host,
                        port=self.port
                    )
            
            logger.info(f"Connected to ChromaDB")
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise ConnectionError(f"Failed to connect to ChromaDB: {e}") from e
    
    async def disconnect(self) -> bool:
        """Disconnect from ChromaDB"""
        try:
            self.client = None
            self.collection = None
            self._connected = False
            logger.debug("Disconnected from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from ChromaDB: {e}")
            return False
    
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create ChromaDB collection"""
        try:
            if not self._connected:
                await self.connect()
            
            # Map metric to ChromaDB distance function
            distance_map = {
                "cosine": "cosine",
                "euclidean": "l2", 
                "dotproduct": "ip"
            }
            distance_function = distance_map.get(metric, "cosine")
            
            # Create collection
            self.client.create_collection(
                name=name,
                metadata={"hnsw:space": distance_function}
            )
            
            logger.info(f"Created ChromaDB collection: {name} (dimension: {dimension}, metric: {metric})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ChromaDB collection {name}: {e}")
            return False
    
    async def delete_index(self, name: str) -> bool:
        """Delete ChromaDB collection"""
        try:
            if not self._connected:
                await self.connect()
            
            self.client.delete_collection(name=name)
            
            # Clear current collection if it was deleted
            if name == self.collection_name:
                self.collection = None
            
            logger.info(f"Deleted ChromaDB collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete ChromaDB collection {name}: {e}")
            return False
    
    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents in ChromaDB"""
        try:
            if not await self._ensure_collection():
                return False
            
            # Prepare data for ChromaDB
            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            metadatas = []
            documents_text = []
            
            for doc in documents:
                # ChromaDB expects string values in metadata
                metadata = {}
                for key, value in doc.metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
                    else:
                        metadata[key] = str(value)
                
                metadata["timestamp"] = doc.timestamp.isoformat() if doc.timestamp else None
                metadatas.append(metadata)
                documents_text.append(doc.content)
            
            # Upsert to ChromaDB
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text
            )
            
            logger.debug(f"Upserted {len(documents)} documents to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert documents to ChromaDB: {e}")
            return False
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query ChromaDB for similar vectors"""
        try:
            if not await self._ensure_collection():
                return []
            
            # Build query parameters
            query_params = {
                "query_embeddings": [query.embedding],
                "n_results": query.top_k,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add where filter if provided
            if query.filters:
                # ChromaDB uses where clause for metadata filtering
                query_params["where"] = query.filters
            
            # Execute query
            results = self.collection.query(**query_params)
            
            # Convert results
            vector_results = []
            if results["ids"] and results["ids"][0]:  # ChromaDB returns nested lists
                ids = results["ids"][0]
                documents = results["documents"][0] if results["documents"] else []
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                for i, doc_id in enumerate(ids):
                    # Convert distance to similarity score (ChromaDB returns distances)
                    distance = distances[i] if i < len(distances) else 1.0
                    score = 1.0 - distance  # Simple conversion, adjust based on metric
                    
                    # Filter by minimum score if specified
                    if query.min_score and score < query.min_score:
                        continue
                    
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    content = documents[i] if i < len(documents) and query.include_content else ""
                    
                    # Remove timestamp from metadata if it exists
                    metadata.pop("timestamp", None)
                    
                    result = VectorResult(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                        score=score
                    )
                    vector_results.append(result)
            
            logger.debug(f"ChromaDB query returned {len(vector_results)} results")
            return vector_results
            
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            raise QueryError(f"Failed to query ChromaDB: {e}") from e
    
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID from ChromaDB"""
        try:
            if not await self._ensure_collection():
                return None
            
            # Get document
            result = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not result["ids"] or doc_id not in result["ids"]:
                return None
            
            idx = result["ids"].index(doc_id)
            content = result["documents"][idx] if result["documents"] else ""
            metadata = result["metadatas"][idx] if result["metadatas"] else {}
            embedding = result["embeddings"][idx] if result["embeddings"] else []
            
            # Extract timestamp from metadata
            timestamp_str = metadata.pop("timestamp", None)
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            
            document = VectorDocument(
                id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                timestamp=timestamp
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from ChromaDB: {e}")
            return None
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs from ChromaDB"""
        try:
            if not await self._ensure_collection():
                return False
            
            # Delete documents
            self.collection.delete(ids=doc_ids)
            
            logger.debug(f"Deleted {len(doc_ids)} documents from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {e}")
            return False
    
    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs from ChromaDB"""
        try:
            if not await self._ensure_collection():
                return []
            
            # Get documents with optional filtering
            query_params = {"limit": limit}
            if filters:
                query_params["where"] = filters
            
            result = self.collection.get(**query_params)
            
            doc_ids = result["ids"] if result["ids"] else []
            
            logger.debug(f"Listed {len(doc_ids)} documents from ChromaDB")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to list documents from ChromaDB: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics"""
        try:
            if not await self._ensure_collection():
                return {}
            
            # Get collection count
            count = self.collection.count()
            
            return {
                "total_vectors": count,
                "store_type": "chromadb",
                "collection_name": self.collection_name,
                "host": self.host,
                "port": self.port,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check ChromaDB connection health"""
        try:
            if not self._connected:
                return False
            
            # Try a simple operation
            self.client.list_collections()
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    async def _ensure_collection(self) -> bool:
        """Ensure collection exists and is accessible"""
        try:
            if not self._connected:
                await self.connect()
            
            if not self.collection:
                try:
                    # Try to get existing collection
                    self.collection = self.client.get_collection(name=self.collection_name)
                except Exception:
                    # Collection doesn't exist, create it
                    dimension = self.config.embedding_dimension
                    if dimension <= 0:
                        raise ValueError("Invalid embedding dimension for collection creation")
                    
                    success = await self.create_index(
                        self.collection_name, 
                        dimension, 
                        self.config.metric
                    )
                    if not success:
                        return False
                    
                    self.collection = self.client.get_collection(name=self.collection_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure ChromaDB collection: {e}")
            return False
