"""
LangSwarm V2 Native Redis Vector Store

Redis-based vector storage using Redis Stack (RediSearch + Vector Similarity).
High-performance, in-memory vector database.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import numpy as np

# Redis import
try:
    import redis
    import redis.asyncio as redis_async
    from redis.exceptions import ResponseError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis_async = Any
    ResponseError = Exception

from .interfaces import (
    IVectorStore, VectorDocument, VectorQuery, VectorResult, 
    VectorStoreConfig, VectorStoreError, ConnectionError, QueryError
)

logger = logging.getLogger(__name__)


class NativeRedisVectorStore(IVectorStore):
    """
    Native Redis vector store implementation.
    
    Uses Redis Stack's vector search capabilities.
    Requires Redis Stack or Redis 6.x+ with RediSearch module.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize Redis vector store.
        
        Args:
            config: Vector store configuration
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis is not available. Install with: pip install redis")
            
        self.config = config
        self.url = config.connection_params.get("url", "redis://localhost:6379")
        self.index_name = config.connection_params.get("index_name", "idx:vectors")
        # Prefix for keys. If index_name is idx:vectors, keys might be vectors:uuid
        self.key_prefix = config.connection_params.get("key_prefix", "vectors:")
        
        self._client: Optional[redis_async.Redis] = None
        self._connected = False
        
        logger.debug(f"Initialized Redis vector store: {self.url}")
    
    async def connect(self) -> bool:
        """Connect to Redis and check index"""
        try:
            self._client = redis_async.from_url(
                self.url,
                decode_responses=False # Keep binary for vector data? No, redis-py handles bytes usually.
                # Actually for RediSearch we usually want decode_responses=True for metadata, 
                # but vector fields need binary packing.
                # It's safer to use decode_responses=False (default) and decode strings manually.
            )
            
            # Ping
            await self._client.ping()
            
            # Check/Create index
            await self._ensure_index()
            
            self._connected = True
            logger.info(f"Connected to Redis vector store: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e
    
    async def _ensure_index(self):
        """Ensure the search index exists"""
        try:
            await self._client.ft(self.index_name).info()
        except ResponseError:
            # Index does not exist, create it
            logger.info(f"Creating Redis index: {self.index_name}")
            await self._create_index(self.index_name, self.config.embedding_dimension)
            
    async def _create_index(self, name: str, dimension: int):
        """Create RediSearch index"""
        from redis.commands.search.field import TextField, VectorField, TagField
        from redis.commands.search.indexDefinition import IndexDefinition, IndexType
        
        # Define schema
        # We store: content (text), metadata (json/text), embedding (vector)
        
        # Metric mapping
        metric = "COSINE"
        if self.config.metric == "euclidean":
            metric = "L2"
        elif self.config.metric == "dotproduct":
            metric = "IP"
            
        schema = (
            TagField("id"), # For exact match filtering
            TextField("content"),
            TextField("metadata"), # We'll store metadata as a JSON string for simple retrieval, 
                                 # OR we can flattened it. 
                                 # For simple filtering we might need TagFields for specific metadata keys.
                                 # For now, simplistic approach: metadata blob + generated tags if needed?
                                 # Let's stick to simple blob for storage, but maybe extract key fields if configured.
                                 # The SQLite impl uses JSON extract, Redis needs explicit fields for filtering.
                                 # For parity, we might assume NO deep filtering or just ID filtering for now.
            VectorField(
                "embedding",
                "FLAT", # or HNSW
                {
                    "TYPE": "FLOAT32",
                    "DIM": dimension,
                    "DISTANCE_METRIC": metric
                }
            )
        )
        
        # Index definition
        definition = IndexDefinition(
            prefix=[self.key_prefix],
            index_type=IndexType.HASH
        )
        
        await self._client.ft(name).create_index(
            fields=schema,
            definition=definition
        )
        
    async def disconnect(self) -> bool:
        """Disconnect"""
        try:
            if self._client:
                await self._client.close()
                self._client = None
            self._connected = False
            return True
        except Exception:
            return False

    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Manually create an index (advanced usage)"""
        # In Redis, creating an 'index' usually means a FT index.
        # This matches our internal helper.
        try:
            if not self._connected:
                await self.connect()
            await self._create_index(name, dimension)
            return True
        except Exception as e:
            logger.error(f"Failed to create Redis index {name}: {e}")
            return False

    async def delete_index(self, name: str) -> bool:
        """Delete index"""
        try:
            if not self._connected:
                await self.connect()
            await self._client.ft(name).dropindex(delete_documents=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {name}: {e}")
            return False

    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Upsert documents"""
        try:
            if not self._connected:
                await self.connect()
            
            pipeline = self._client.pipeline(transaction=False)
            
            for doc in documents:
                key = f"{self.key_prefix}{doc.id}"
                
                # Redis requires bytes for vector
                vector_bytes = np.array(doc.embedding, dtype=np.float32).tobytes()
                
                mapping = {
                    "id": doc.id,
                    "content": doc.content,
                    "embedding": vector_bytes,
                    "metadata": json.dumps(doc.metadata) if doc.metadata else "{}",
                    "timestamp": doc.timestamp.isoformat() if doc.timestamp else datetime.utcnow().isoformat()
                }
                
                # Add metadata fields as separate tags if needed for filtering?
                # For now, we rely on the blob.
                
                pipeline.hset(key, mapping=mapping)
            
            await pipeline.execute()
            logger.debug(f"Upserted {len(documents)} to Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert Redis: {e}")
            return False

    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query similar vectors"""
        try:
            if not self._connected:
                await self.connect()
            
            from redis.commands.search.query import Query
            
            # Prepare vector
            query_vector = np.array(query.embedding, dtype=np.float32).tobytes()
            
            # Base query: Search all (*) matched by vector
            # Syntax: "*=>[KNN top_k @embedding $blob AS score]"
            
            # Filter construction
            # Redis filters are part of the pre-filter query string passed to Q
            # e.g. "@id:{123} => [KNN...]"
            filter_str = "*"
            if query.filters:
                # Basic ID filtering support or Tag filtering if we tracked it
                if "id" in query.filters:
                    # Escape special chars if needed
                    val = query.filters["id"]
                    filter_str = f"@id:{{{val}}}"
            
            q = Query(f"{filter_str}=>[KNN {query.top_k} @embedding $blob AS score]")\
                .sort_by("score")\
                .return_fields("id", "content", "metadata", "score")\
                .dialect(2)
            
            params = {"blob": query_vector}
            
            res = await self._client.ft(self.index_name).search(q, query_params=params)
            
            results = []
            for doc in res.docs:
                # Redis returns distance as score (lower is better for dist, higher for similarity?)
                # Wait, KNN score depends on metric.
                # For COSINE, it's 1 - cosine_similarity (distance). 
                # So similarity = 1 - score.
                # Unless we used IP (Inner Product), then it's 1 - IP? Redis docs say:
                # "Cosine distance is defined as 1 - cosine_similarity"
                
                score_val = float(doc.score)
                similarity = 1.0 - score_val if self.config.metric == "cosine" else score_val
                # If Euclidean (L2), score is L2 squared distance? No just L2 distance.
                # To normalize L2 to 0-1 similarity is hard without bounds.
                # We'll stick to 1-score for cosine as the primary use case.
                
                if query.min_score and similarity < query.min_score:
                    continue
                    
                # Decode fields (if using decode_responses=False)
                # doc.* fields are bytes.
                
                content = doc.content
                if isinstance(content, bytes):
                     content = content.decode('utf-8')
                     
                metadata_str = doc.metadata
                if isinstance(metadata_str, bytes):
                    metadata_str = metadata_str.decode('utf-8')
                
                doc_id = doc.id
                if isinstance(doc_id, bytes):
                    doc_id = doc_id.decode('utf-8')

                results.append(VectorResult(
                    id=doc_id,
                    content=content,
                    metadata=json.loads(metadata_str),
                    score=similarity
                ))
            
            return results

        except Exception as e:
            logger.error(f"Redis query failed: {e}")
            raise QueryError(f"Redis query failed: {e}") from e

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document"""
        try:
            if not self._connected:
                await self.connect()
                
            key = f"{self.key_prefix}{doc_id}"
            data = await self._client.hgetall(key)
            
            if not data:
                return None
                
            # Decode
            content = data[b'content'].decode('utf-8')
            metadata = json.loads(data[b'metadata'].decode('utf-8'))
            timestamp = datetime.fromisoformat(data[b'timestamp'].decode('utf-8'))
            
            # Vector
            embedding_bytes = data[b'embedding']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
            
            doc_id = data[b'id'].decode('utf-8')
            
            return VectorDocument(
                id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to get doc {doc_id}: {e}")
            return None

    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents"""
        try:
            if not self._connected:
                await self.connect()
            
            keys = [f"{self.key_prefix}{did}" for did in doc_ids]
            await self._client.delete(*keys)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete docs: {e}")
            return False

    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List docs"""
        # Without a search query, listing all IDs efficiently in Redis is tricky with FT.SEARCH using *
        try:
            if not self._connected:
                await self.connect()
            
            # Simple SCAN if no filters? OR FT.SEARCH "*"
            # FT.SEARCH is better.
            
            from redis.commands.search.query import Query
            q = Query("*").limit(0, limit).return_fields("id")
            
            res = await self._client.ft(self.index_name).search(q)
            
            ids = []
            for doc in res.docs:
                d_id = doc.id
                if isinstance(d_id, bytes):
                    d_id = d_id.decode('utf-8')
                ids.append(d_id)
            return ids
            
        except Exception as e:
            logger.error(f"List docs failed: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get stats"""
        try:
            if not self._connected:
                await self.connect()
                
            info = await self._client.ft(self.index_name).info()
            
            # Parse useful bits
            # num_docs, etc.
            # info is a dict (if decode_responses=True) or list/dict mixed.
            # redis-py usually returns dict for info()
            
            return {
                "total_vectors": int(info.get("num_docs", 0)),
                "index_name": self.index_name,
                "store_type": "redis", 
                "memory_used": info.get("index_total_size_mb", 0) # approximation
            }
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {"error": str(e)}

    async def health_check(self) -> bool:
        try:
            if not self._connected:
                return False
            await self._client.ping()
            return True
        except Exception:
            return False
