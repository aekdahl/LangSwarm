"""
LangSwarm V2 Native Pinecone Vector Store

Direct Pinecone API integration without LangChain dependencies.
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


class NativePineconeStore(IVectorStore):
    """
    Native Pinecone vector store implementation.
    
    Direct integration with Pinecone API that replaces LangChain's
    Pinecone wrapper with better performance and control.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize Pinecone store.
        
        Args:
            config: Vector store configuration with Pinecone parameters
        """
        self.config = config
        self.client = None
        self.index = None
        self._connected = False
        
        # Extract Pinecone-specific config
        self.api_key = config.connection_params.get("api_key")
        self.environment = config.connection_params.get("environment")
        self.index_name = config.connection_params.get("index_name", "langswarm-default")
        self.namespace = config.namespace or ""
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        
        logger.debug(f"Initialized Pinecone store for index: {self.index_name}")
    
    async def connect(self) -> bool:
        """Connect to Pinecone"""
        try:
            # Import Pinecone (optional dependency)
            try:
                import pinecone
                from pinecone import Pinecone
            except ImportError:
                raise ConnectionError("Pinecone library not installed. Install with: pip install pinecone-client")
            
            # Initialize Pinecone client
            self.client = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            try:
                index_description = self.client.describe_index(self.index_name)
                self.index = self.client.Index(self.index_name)
                logger.info(f"Connected to existing Pinecone index: {self.index_name}")
            except Exception as e:
                logger.warning(f"Index {self.index_name} not found: {e}")
                # Index will be created when needed
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            raise ConnectionError(f"Failed to connect to Pinecone: {e}") from e
    
    async def disconnect(self) -> bool:
        """Disconnect from Pinecone"""
        try:
            self.client = None
            self.index = None
            self._connected = False
            logger.debug("Disconnected from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Pinecone: {e}")
            return False
    
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create Pinecone index"""
        try:
            if not self._connected:
                await self.connect()
            
            # Create index with specified parameters
            self.client.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
            )
            
            # Wait for index to be ready
            import time
            while not self.client.describe_index(name).status.ready:
                await asyncio.sleep(1)
            
            # Update current index if it's the one we're using
            if name == self.index_name:
                self.index = self.client.Index(name)
            
            logger.info(f"Created Pinecone index: {name} (dimension: {dimension}, metric: {metric})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Pinecone index {name}: {e}")
            return False
    
    async def delete_index(self, name: str) -> bool:
        """Delete Pinecone index"""
        try:
            if not self._connected:
                await self.connect()
            
            self.client.delete_index(name)
            
            # Clear current index if it was deleted
            if name == self.index_name:
                self.index = None
            
            logger.info(f"Deleted Pinecone index: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Pinecone index {name}: {e}")
            return False
    
    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents in Pinecone"""
        try:
            if not self.index:
                if not await self._ensure_index():
                    return False
            
            # Convert documents to Pinecone format
            vectors = []
            for doc in documents:
                vector_data = {
                    "id": doc.id,
                    "values": doc.embedding,
                    "metadata": {
                        **doc.metadata,
                        "content": doc.content,
                        "timestamp": doc.timestamp.isoformat() if doc.timestamp else None
                    }
                }
                vectors.append(vector_data)
            
            # Upsert in batches (Pinecone limit: 100 vectors per request)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=self.namespace)
            
            logger.debug(f"Upserted {len(documents)} documents to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert documents to Pinecone: {e}")
            return False
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query Pinecone for similar vectors"""
        try:
            if not self.index:
                if not await self._ensure_index():
                    return []
            
            # Build query parameters
            query_params = {
                "vector": query.embedding,
                "top_k": query.top_k,
                "namespace": self.namespace,
                "include_metadata": query.include_metadata,
                "include_values": False  # Don't return embeddings by default
            }
            
            # Add filters if provided
            if query.filters:
                query_params["filter"] = query.filters
            
            # Execute query
            response = self.index.query(**query_params)
            
            # Convert results
            results = []
            for match in response.matches:
                # Filter by minimum score if specified
                if query.min_score and match.score < query.min_score:
                    continue
                
                metadata = match.metadata or {}
                content = metadata.pop("content", "") if query.include_content else ""
                
                result = VectorResult(
                    id=match.id,
                    content=content,
                    metadata=metadata,
                    score=match.score,
                    embedding=match.values if query_params.get("include_values") else None
                )
                results.append(result)
            
            logger.debug(f"Pinecone query returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query Pinecone: {e}")
            raise QueryError(f"Failed to query Pinecone: {e}") from e
    
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID from Pinecone"""
        try:
            if not self.index:
                if not await self._ensure_index():
                    return None
            
            # Fetch document
            response = self.index.fetch(ids=[doc_id], namespace=self.namespace)
            
            if doc_id not in response.vectors:
                return None
            
            vector_data = response.vectors[doc_id]
            metadata = vector_data.metadata or {}
            
            # Extract content and timestamp from metadata
            content = metadata.pop("content", "")
            timestamp_str = metadata.pop("timestamp", None)
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            
            document = VectorDocument(
                id=doc_id,
                content=content,
                embedding=vector_data.values,
                metadata=metadata,
                timestamp=timestamp
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from Pinecone: {e}")
            return None
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs from Pinecone"""
        try:
            if not self.index:
                if not await self._ensure_index():
                    return False
            
            # Delete in batches
            batch_size = 1000  # Pinecone delete limit
            for i in range(0, len(doc_ids), batch_size):
                batch = doc_ids[i:i + batch_size]
                self.index.delete(ids=batch, namespace=self.namespace)
            
            logger.debug(f"Deleted {len(doc_ids)} documents from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from Pinecone: {e}")
            return False
    
    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs (limited functionality in Pinecone)"""
        try:
            # Pinecone doesn't have a direct list operation
            # We'll use a dummy query to get recent documents
            if not self.index:
                if not await self._ensure_index():
                    return []
            
            # Create a zero vector for dummy query
            dimension = self.config.embedding_dimension
            dummy_vector = [0.0] * dimension
            
            # Query with filters if provided
            query_params = {
                "vector": dummy_vector,
                "top_k": min(limit, 10000),  # Pinecone max
                "namespace": self.namespace,
                "include_metadata": False
            }
            
            if filters:
                query_params["filter"] = filters
            
            response = self.index.query(**query_params)
            
            # Extract IDs
            doc_ids = [match.id for match in response.matches]
            
            logger.debug(f"Listed {len(doc_ids)} documents from Pinecone")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to list documents from Pinecone: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            if not self.index:
                if not await self._ensure_index():
                    return {}
            
            # Get index stats
            stats = self.index.describe_index_stats()
            
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {},
                "store_type": "pinecone",
                "index_name": self.index_name,
                "namespace": self.namespace
            }
            
        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Pinecone connection health"""
        try:
            if not self._connected:
                return False
            
            if not self.index:
                return await self._ensure_index()
            
            # Try a simple operation
            await self.get_stats()
            return True
            
        except Exception as e:
            logger.error(f"Pinecone health check failed: {e}")
            return False
    
    async def _ensure_index(self) -> bool:
        """Ensure index exists and is accessible"""
        try:
            if not self._connected:
                await self.connect()
            
            if not self.index:
                # Try to get existing index
                try:
                    self.index = self.client.Index(self.index_name)
                    # Test access
                    self.index.describe_index_stats()
                except Exception:
                    # Index doesn't exist, create it
                    dimension = self.config.embedding_dimension
                    if dimension <= 0:
                        raise ValueError("Invalid embedding dimension for index creation")
                    
                    success = await self.create_index(
                        self.index_name, 
                        dimension, 
                        self.config.metric
                    )
                    if not success:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure Pinecone index: {e}")
            return False
