"""
LangSwarm V2 Native Qdrant Vector Store

Direct Qdrant API integration without LangChain dependencies.
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


class NativeQdrantStore(IVectorStore):
    """
    Native Qdrant vector store implementation.
    
    Direct integration with Qdrant API that replaces LangChain's
    Qdrant wrapper with better performance and control.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize Qdrant store.
        
        Args:
            config: Vector store configuration with Qdrant parameters
        """
        self.config = config
        self.client = None
        self._connected = False
        
        # Extract Qdrant-specific config
        self.url = config.connection_params.get("url", "http://localhost:6333")
        self.api_key = config.connection_params.get("api_key")
        self.collection_name = config.connection_params.get("collection_name", "langswarm_default")
        self.prefer_grpc = config.connection_params.get("prefer_grpc", False)
        
        logger.debug(f"Initialized Qdrant store for collection: {self.collection_name}")
    
    async def connect(self) -> bool:
        """Connect to Qdrant"""
        try:
            # Import Qdrant (optional dependency)
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams, CollectionStatus
            except ImportError:
                raise ConnectionError("Qdrant client not installed. Install with: pip install qdrant-client")
            
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                prefer_grpc=self.prefer_grpc
            )
            
            # Test connection
            info = self.client.get_collections()
            logger.info(f"Connected to Qdrant at {self.url}")
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise ConnectionError(f"Failed to connect to Qdrant: {e}") from e
    
    async def disconnect(self) -> bool:
        """Disconnect from Qdrant"""
        try:
            if self.client:
                self.client.close()
            self.client = None
            self._connected = False
            logger.debug("Disconnected from Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Qdrant: {e}")
            return False
    
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create Qdrant collection"""
        try:
            if not self._connected:
                await self.connect()
            
            # Import Qdrant models
            from qdrant_client.models import Distance, VectorParams
            
            # Map metric to Qdrant distance
            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "dotproduct": Distance.DOT
            }
            distance = distance_map.get(metric, Distance.COSINE)
            
            # Create collection
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=distance
                )
            )
            
            logger.info(f"Created Qdrant collection: {name} (dimension: {dimension}, metric: {metric})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection {name}: {e}")
            return False
    
    async def delete_index(self, name: str) -> bool:
        """Delete Qdrant collection"""
        try:
            if not self._connected:
                await self.connect()
            
            self.client.delete_collection(collection_name=name)
            
            logger.info(f"Deleted Qdrant collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Qdrant collection {name}: {e}")
            return False
    
    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents in Qdrant"""
        try:
            if not await self._ensure_collection():
                return False
            
            # Import Qdrant models
            from qdrant_client.models import PointStruct
            
            # Convert documents to Qdrant points
            points = []
            for doc in documents:
                payload = {
                    **doc.metadata,
                    "content": doc.content,
                    "timestamp": doc.timestamp.isoformat() if doc.timestamp else None
                }
                
                point = PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.debug(f"Upserted {len(documents)} documents to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert documents to Qdrant: {e}")
            return False
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query Qdrant for similar vectors"""
        try:
            if not await self._ensure_collection():
                return []
            
            # Import Qdrant models
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build query filter
            query_filter = None
            if query.filters:
                conditions = []
                for field, value in query.filters.items():
                    if isinstance(value, dict):
                        # Handle complex filter conditions
                        for op, val in value.items():
                            if op == "eq":
                                conditions.append(FieldCondition(key=field, match=MatchValue(value=val)))
                            # Add more operators as needed
                    else:
                        # Simple equality filter
                        conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Execute search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query.embedding,
                query_filter=query_filter,
                limit=query.top_k,
                with_payload=query.include_metadata,
                with_vectors=False  # Don't return embeddings by default
            )
            
            # Convert results
            results = []
            for hit in search_result:
                # Filter by minimum score if specified
                if query.min_score and hit.score < query.min_score:
                    continue
                
                payload = hit.payload or {}
                content = payload.pop("content", "") if query.include_content else ""
                
                result = VectorResult(
                    id=str(hit.id),
                    content=content,
                    metadata=payload,
                    score=hit.score,
                    embedding=hit.vector if hasattr(hit, 'vector') and hit.vector else None
                )
                results.append(result)
            
            logger.debug(f"Qdrant query returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query Qdrant: {e}")
            raise QueryError(f"Failed to query Qdrant: {e}") from e
    
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID from Qdrant"""
        try:
            if not await self._ensure_collection():
                return None
            
            # Retrieve point
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
                with_payload=True,
                with_vectors=True
            )
            
            if not result:
                return None
            
            point = result[0]
            payload = point.payload or {}
            
            # Extract content and timestamp from payload
            content = payload.pop("content", "")
            timestamp_str = payload.pop("timestamp", None)
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            
            document = VectorDocument(
                id=str(point.id),
                content=content,
                embedding=point.vector,
                metadata=payload,
                timestamp=timestamp
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from Qdrant: {e}")
            return None
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs from Qdrant"""
        try:
            if not await self._ensure_collection():
                return False
            
            # Delete points
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=doc_ids
            )
            
            logger.debug(f"Deleted {len(doc_ids)} documents from Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from Qdrant: {e}")
            return False
    
    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs from Qdrant"""
        try:
            if not await self._ensure_collection():
                return []
            
            # Import Qdrant models
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build filter if provided
            query_filter = None
            if filters:
                conditions = []
                for field, value in filters.items():
                    conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Scroll through points to get IDs
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=False,
                with_vectors=False
            )
            
            # Extract IDs
            doc_ids = [str(point.id) for point in result[0]]
            
            logger.debug(f"Listed {len(doc_ids)} documents from Qdrant")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to list documents from Qdrant: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant collection statistics"""
        try:
            if not await self._ensure_collection():
                return {}
            
            # Get collection info
            info = self.client.get_collection(collection_name=self.collection_name)
            
            return {
                "total_vectors": info.points_count,
                "indexed_vectors": info.indexed_vectors_count,
                "vector_dimension": info.config.params.vectors.size,
                "distance_metric": info.config.params.vectors.distance.name,
                "status": info.status.name,
                "store_type": "qdrant",
                "collection_name": self.collection_name,
                "url": self.url
            }
            
        except Exception as e:
            logger.error(f"Failed to get Qdrant stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Qdrant connection health"""
        try:
            if not self._connected:
                return False
            
            # Try a simple operation
            self.client.get_collections()
            return True
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    async def _ensure_collection(self) -> bool:
        """Ensure collection exists and is accessible"""
        try:
            if not self._connected:
                await self.connect()
            
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
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
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")
            return False
