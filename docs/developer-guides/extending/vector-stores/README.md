# Extending LangSwarm V2 Native Vector Stores

**Complete guide for extending and customizing the native vector store system**

## 🎯 Overview

LangSwarm V2's native vector store system is designed for extensibility, allowing developers to add custom vector databases, embedding providers, similarity metrics, and advanced search capabilities while maintaining compatibility with the unified interface and V2 memory system.

**Extension Capabilities:**
- **Custom Vector Stores**: Add support for new vector databases
- **Custom Embedding Providers**: Integrate new embedding models and APIs
- **Custom Similarity Metrics**: Implement specialized distance calculations
- **Custom Search Logic**: Add advanced search and filtering capabilities
- **Custom Storage Backends**: Create specialized storage implementations
- **Integration Patterns**: Integrate with external systems and pipelines

---

## 💾 Custom Vector Store Implementation

### **Implementing IVectorStore Interface**

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio
import numpy as np
from datetime import datetime

from langswarm.core.memory.vector_stores.interfaces import (
    IVectorStore,
    VectorDocument,
    VectorQuery,
    VectorResult,
    VectorStoreStats,
    VectorStoreHealth
)

class CustomVectorStore(IVectorStore):
    """Custom vector store implementation"""
    
    def __init__(
        self,
        connection_string: str,
        collection_name: str = "vectors",
        embedding_dimension: int = 1536,
        similarity_metric: str = "cosine",
        config: Dict[str, Any] = None
    ):
        """Initialize custom vector store
        
        Args:
            connection_string: Database connection string
            collection_name: Collection/table name for vectors
            embedding_dimension: Vector embedding dimension
            similarity_metric: Similarity metric to use
            config: Additional configuration options
        """
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.similarity_metric = similarity_metric
        self.config = config or {}
        
        # Connection state
        self._client = None
        self._connected = False
        
        # Performance tracking
        self._query_count = 0
        self._total_query_time = 0.0
    
    @property
    def is_connected(self) -> bool:
        """Check if store is connected"""
        return self._connected
    
    @property
    def backend_type(self) -> str:
        """Get backend type identifier"""
        return "custom_vector_store"
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self._embedding_dimension
    
    async def connect(self) -> None:
        """Connect to vector store backend"""
        try:
            # Initialize your custom client
            self._client = await self._create_client()
            
            # Test connection
            await self._test_connection()
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            self._connected = True
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to custom vector store: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from vector store backend"""
        if self._client and hasattr(self._client, 'close'):
            await self._client.close()
        
        self._connected = False
        self._client = None
    
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to vector store"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        added_ids = []
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Prepare batch for insertion
                batch_data = await self._prepare_batch_for_insertion(batch)
                
                # Insert batch
                batch_ids = await self._insert_batch(batch_data)
                added_ids.extend(batch_ids)
                
            except Exception as e:
                raise VectorStoreError(f"Failed to add document batch: {e}")
        
        return added_ids
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Perform similarity search"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate query
            errors = query.validate()
            if errors:
                raise QueryError(f"Invalid query: {', '.join(errors)}")
            
            # Prepare query for execution
            prepared_query = await self._prepare_query(query)
            
            # Execute search
            raw_results = await self._execute_search(prepared_query)
            
            # Process results
            results = await self._process_search_results(raw_results, query)
            
            # Update performance metrics
            query_time = asyncio.get_event_loop().time() - start_time
            self._query_count += 1
            self._total_query_time += query_time
            
            return results
            
        except Exception as e:
            raise QueryError(f"Query execution failed: {e}")
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Get document by ID"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        try:
            raw_doc = await self._get_document_by_id(document_id)
            
            if raw_doc:
                return self._convert_to_vector_document(raw_doc)
            
            return None
            
        except Exception as e:
            raise VectorStoreError(f"Failed to get document {document_id}: {e}")
    
    async def update_document(
        self,
        document_id: str,
        document: VectorDocument
    ) -> None:
        """Update existing document"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        try:
            # Prepare document for update
            update_data = await self._prepare_document_for_update(document)
            
            # Execute update
            await self._update_document_by_id(document_id, update_data)
            
        except Exception as e:
            raise VectorStoreError(f"Failed to update document {document_id}: {e}")
    
    async def delete_documents(self, document_ids: List[str]) -> int:
        """Delete documents by ID"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        try:
            deleted_count = await self._delete_documents_by_ids(document_ids)
            return deleted_count
            
        except Exception as e:
            raise VectorStoreError(f"Failed to delete documents: {e}")
    
    async def get_statistics(self) -> VectorStoreStats:
        """Get store statistics and metrics"""
        if not self._connected:
            raise VectorStoreError("Store not connected")
        
        try:
            # Gather basic statistics
            total_docs = await self._count_documents()
            storage_size = await self._calculate_storage_size()
            
            # Calculate performance metrics
            avg_query_time = (
                self._total_query_time / self._query_count
                if self._query_count > 0 else 0.0
            ) * 1000  # Convert to milliseconds
            
            return VectorStoreStats(
                total_documents=total_docs,
                total_vectors=total_docs,  # Assuming 1:1 ratio
                embedding_dimension=self.embedding_dimension,
                index_size_mb=storage_size,
                storage_size_mb=storage_size,
                memory_usage_mb=await self._get_memory_usage(),
                avg_query_time_ms=avg_query_time,
                total_queries=self._query_count,
                queries_per_second=self._calculate_qps(),
                last_updated=datetime.now(),
                backend=self.backend_type,
                version=await self._get_backend_version()
            )
            
        except Exception as e:
            raise VectorStoreError(f"Failed to get statistics: {e}")
    
    async def health_check(self) -> VectorStoreHealth:
        """Check store health and connectivity"""
        health = VectorStoreHealth(
            is_healthy=True,
            status="healthy",
            is_connected=self._connected,
            response_time_ms=0.0
        )
        
        try:
            # Test connection response time
            start_time = asyncio.get_event_loop().time()
            await self._ping_backend()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            health.response_time_ms = response_time
            
            # Check resource usage
            health.available_space_gb = await self._get_available_space()
            health.memory_usage_percent = await self._get_memory_usage_percent()
            
            # Validate health thresholds
            if response_time > 5000:  # 5 seconds
                health.add_warning("High response time detected")
            
            if health.memory_usage_percent and health.memory_usage_percent > 90:
                health.add_issue("High memory usage")
            
            if health.available_space_gb and health.available_space_gb < 1:
                health.add_issue("Low available storage space")
            
        except Exception as e:
            health.add_issue(f"Health check failed: {e}")
        
        return health
    
    # Implementation-specific helper methods
    
    async def _create_client(self):
        """Create and configure custom client"""
        # Implement client creation based on your backend
        from your_custom_vector_db import AsyncClient
        
        client = AsyncClient(
            connection_string=self.connection_string,
            timeout=self.config.get("timeout", 30),
            pool_size=self.config.get("pool_size", 10)
        )
        
        return client
    
    async def _test_connection(self):
        """Test backend connection"""
        await self._client.ping()
    
    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        exists = await self._client.collection_exists(self.collection_name)
        
        if not exists:
            await self._client.create_collection(
                name=self.collection_name,
                dimension=self.embedding_dimension,
                metric=self.similarity_metric,
                **self.config.get("collection_config", {})
            )
    
    async def _prepare_batch_for_insertion(
        self,
        documents: List[VectorDocument]
    ) -> List[Dict[str, Any]]:
        """Prepare document batch for insertion"""
        batch_data = []
        
        for doc in documents:
            # Ensure document has embedding
            if doc.embedding is None:
                if hasattr(self, 'embedding_provider'):
                    doc.embedding = await self.embedding_provider.embed_query(doc.content)
                else:
                    raise VectorStoreError(f"Document {doc.id} missing embedding")
            
            # Convert to backend format
            doc_data = {
                "id": doc.id,
                "content": doc.content,
                "embedding": doc.embedding.tolist(),
                "metadata": doc.metadata,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            
            batch_data.append(doc_data)
        
        return batch_data
    
    async def _insert_batch(self, batch_data: List[Dict[str, Any]]) -> List[str]:
        """Insert document batch"""
        result = await self._client.insert_documents(
            collection=self.collection_name,
            documents=batch_data
        )
        
        return result.get("inserted_ids", [])
    
    async def _prepare_query(self, query: VectorQuery) -> Dict[str, Any]:
        """Prepare query for execution"""
        prepared = {
            "collection": self.collection_name,
            "top_k": query.top_k,
            "similarity_threshold": query.similarity_threshold,
            "include_metadata": query.include_metadata,
            "include_embeddings": query.include_embeddings
        }
        
        # Handle embedding vs text query
        if query.embedding is not None:
            prepared["embedding"] = query.embedding.tolist()
        elif query.text is not None:
            if hasattr(self, 'embedding_provider'):
                embedding = await self.embedding_provider.embed_query(query.text)
                prepared["embedding"] = embedding.tolist()
            else:
                raise QueryError("No embedding provider available for text query")
        
        # Add metadata filtering
        if query.metadata_filter:
            prepared["filter"] = self._convert_metadata_filter(query.metadata_filter)
        
        # Add document ID filtering
        if query.document_ids:
            prepared["document_ids"] = query.document_ids
        
        return prepared
    
    async def _execute_search(self, prepared_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute similarity search"""
        results = await self._client.search(
            **prepared_query
        )
        
        return results.get("matches", [])
    
    async def _process_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: VectorQuery
    ) -> List[VectorResult]:
        """Process raw search results into VectorResult objects"""
        results = []
        
        for i, raw_result in enumerate(raw_results):
            # Extract document data
            doc_data = raw_result.get("document", {})
            
            # Create VectorDocument
            document = VectorDocument(
                id=doc_data["id"],
                content=doc_data["content"],
                metadata=doc_data.get("metadata", {}),
                embedding=np.array(doc_data["embedding"]) if doc_data.get("embedding") else None,
                created_at=datetime.fromisoformat(doc_data["created_at"]) if doc_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(doc_data["updated_at"]) if doc_data.get("updated_at") else None
            )
            
            # Create VectorResult
            result = VectorResult(
                document=document,
                score=raw_result.get("score", 0.0),
                similarity=raw_result.get("similarity", 0.0),
                rank=i + 1,
                distance=raw_result.get("distance")
            )
            
            results.append(result)
        
        return results
    
    def _convert_metadata_filter(self, metadata_filter: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata filter to backend-specific format"""
        # Convert LangSwarm filter format to your backend's format
        # This is highly backend-specific
        
        backend_filter = {}
        
        for key, value in metadata_filter.items():
            if isinstance(value, dict):
                # Handle operators like {"$in": ["value1", "value2"]}
                for operator, operand in value.items():
                    if operator == "$in":
                        backend_filter[key] = {"in": operand}
                    elif operator == "$gte":
                        backend_filter[key] = {"gte": operand}
                    elif operator == "$lte":
                        backend_filter[key] = {"lte": operand}
                    # Add more operators as needed
            else:
                # Direct equality
                backend_filter[key] = {"eq": value}
        
        return backend_filter
    
    # Additional helper methods for statistics and health
    
    async def _count_documents(self) -> int:
        """Count total documents in collection"""
        result = await self._client.count_documents(self.collection_name)
        return result.get("count", 0)
    
    async def _calculate_storage_size(self) -> float:
        """Calculate storage size in MB"""
        stats = await self._client.collection_stats(self.collection_name)
        return stats.get("size_mb", 0.0)
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        stats = await self._client.memory_stats()
        return stats.get("used_mb", 0.0)
    
    async def _ping_backend(self) -> None:
        """Ping backend for health check"""
        await self._client.ping()
    
    async def _get_available_space(self) -> float:
        """Get available storage space in GB"""
        stats = await self._client.storage_stats()
        return stats.get("available_gb", 0.0)
    
    async def _get_memory_usage_percent(self) -> float:
        """Get memory usage percentage"""
        stats = await self._client.memory_stats()
        return stats.get("usage_percent", 0.0)
    
    def _calculate_qps(self) -> float:
        """Calculate queries per second"""
        if self._total_query_time > 0:
            return self._query_count / self._total_query_time
        return 0.0
    
    async def _get_backend_version(self) -> str:
        """Get backend version"""
        info = await self._client.server_info()
        return info.get("version", "unknown")

# Register custom vector store
from langswarm.core.memory.vector_stores import VectorStoreFactory

VectorStoreFactory.register_custom_store(
    "custom",
    CustomVectorStore,
    requirements=["your-custom-vector-db>=1.0.0"]
)

# Usage
store = VectorStoreFactory.create_from_config({
    "backend": "custom",
    "connection_string": "custom://localhost:9000",
    "collection_name": "my_vectors",
    "embedding_dimension": 1536
})

await store.connect()
```

---

## 🔌 Custom Embedding Providers

### **Implementing IEmbeddingProvider Interface**

```python
from langswarm.core.memory.vector_stores.interfaces import IEmbeddingProvider
import numpy as np
import asyncio
import aiohttp
from typing import List, Dict, Any

class HuggingFaceEmbeddingProvider(IEmbeddingProvider):
    """Custom Hugging Face embedding provider"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        api_key: str = None,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        cache_embeddings: bool = False
    ):
        """Initialize Hugging Face embedding provider
        
        Args:
            model_name: Hugging Face model name
            api_key: Hugging Face API key (if using Inference API)
            batch_size: Batch size for processing
            normalize_embeddings: Whether to normalize embeddings
            cache_embeddings: Whether to cache embeddings
        """
        self.model_name = model_name
        self.api_key = api_key
        self._batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.cache_embeddings = cache_embeddings
        
        # Model configuration
        self._model_config = self._get_model_config(model_name)
        
        # Caching
        self._embedding_cache = {} if cache_embeddings else None
        
        # HTTP session for API calls
        self._session = None
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self._model_config["dimension"]
    
    @property
    def max_batch_size(self) -> int:
        """Get maximum batch size"""
        return self._batch_size
    
    async def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple documents"""
        if not texts:
            return []
        
        # Check cache first
        if self.cache_embeddings:
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    cached_embeddings.append((i, self._embedding_cache[cache_key]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = await self._generate_embeddings(uncached_texts)
                
                # Cache new embeddings
                for text, embedding in zip(uncached_texts, new_embeddings):
                    cache_key = self._get_cache_key(text)
                    self._embedding_cache[cache_key] = embedding
                
                # Combine cached and new embeddings
                all_embeddings = [None] * len(texts)
                
                # Place cached embeddings
                for idx, embedding in cached_embeddings:
                    all_embeddings[idx] = embedding
                
                # Place new embeddings
                for i, embedding in enumerate(new_embeddings):
                    original_idx = uncached_indices[i]
                    all_embeddings[original_idx] = embedding
                
                return all_embeddings
            else:
                # All embeddings were cached
                return [embedding for _, embedding in sorted(cached_embeddings)]
        else:
            # No caching, generate all embeddings
            return await self._generate_embeddings(texts)
    
    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for query text"""
        embeddings = await self.embed_documents([text])
        return embeddings[0]
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[np.ndarray]:
        """Generate embeddings in batches"""
        if batch_size is None:
            batch_size = self.max_batch_size
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Hugging Face model"""
        if self.api_key:
            # Use Hugging Face Inference API
            return await self._generate_embeddings_api(texts)
        else:
            # Use local transformers library
            return await self._generate_embeddings_local(texts)
    
    async def _generate_embeddings_api(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Hugging Face Inference API"""
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self._session.post(
                api_url,
                headers=headers,
                json={"inputs": texts}
            ) as response:
                
                if response.status == 200:
                    embeddings_data = await response.json()
                    embeddings = [np.array(emb) for emb in embeddings_data]
                    
                    if self.normalize_embeddings:
                        embeddings = [self._normalize_embedding(emb) for emb in embeddings]
                    
                    return embeddings
                else:
                    error_text = await response.text()
                    raise EmbeddingError(f"Hugging Face API error: {error_text}")
                    
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")
    
    async def _generate_embeddings_local(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using local transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load model (this should be cached after first load)
            if not hasattr(self, '_local_model'):
                self._local_model = SentenceTransformer(self.model_name)
            
            # Generate embeddings in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._local_model.encode,
                texts,
                {"normalize_embeddings": self.normalize_embeddings}
            )
            
            return [np.array(emb) for emb in embeddings]
            
        except ImportError:
            raise EmbeddingError(
                "sentence-transformers library required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise EmbeddingError(f"Local embedding generation failed: {e}")
    
    def _get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get model configuration"""
        # Model configurations for common models
        model_configs = {
            "sentence-transformers/all-MiniLM-L6-v2": {"dimension": 384},
            "sentence-transformers/all-mpnet-base-v2": {"dimension": 768},
            "sentence-transformers/all-MiniLM-L12-v2": {"dimension": 384},
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {"dimension": 384},
            "intfloat/e5-large-v2": {"dimension": 1024},
            "intfloat/e5-base-v2": {"dimension": 768},
            "intfloat/e5-small-v2": {"dimension": 384}
        }
        
        return model_configs.get(model_name, {"dimension": 768})  # Default dimension
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding vector"""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    async def close(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()

class OpenSourceEmbeddingProvider(IEmbeddingProvider):
    """Local open-source embedding provider"""
    
    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        batch_size: int = 64
    ):
        """Initialize open-source embedding provider
        
        Args:
            model_path: Path to local model or model name
            device: Device to run model on ("cpu", "cuda", "mps")
            batch_size: Batch size for processing
        """
        self.model_path = model_path
        self.device = device
        self._batch_size = batch_size
        
        # Model will be loaded lazily
        self._model = None
        self._tokenizer = None
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        self._ensure_model_loaded()
        return self._model.config.hidden_size
    
    @property
    def max_batch_size(self) -> int:
        """Get maximum batch size"""
        return self._batch_size
    
    def _ensure_model_loaded(self):
        """Ensure model and tokenizer are loaded"""
        if self._model is None:
            try:
                from transformers import AutoModel, AutoTokenizer
                import torch
                
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self._model = AutoModel.from_pretrained(self.model_path)
                self._model.to(self.device)
                self._model.eval()
                
            except ImportError:
                raise EmbeddingError(
                    "transformers and torch libraries required. "
                    "Install with: pip install transformers torch"
                )
    
    async def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for documents"""
        self._ensure_model_loaded()
        
        # Run model inference in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self._generate_embeddings_sync,
            texts
        )
        
        return embeddings
    
    def _generate_embeddings_sync(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings synchronously"""
        import torch
        
        # Tokenize texts
        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        
        # Move to device
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self._model(**encoded)
            
            # Use mean pooling
            embeddings = self._mean_pooling(outputs.last_hidden_state, encoded['attention_mask'])
            
            # Normalize embeddings
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        # Convert to numpy
        return [emb.cpu().numpy() for emb in embeddings]
    
    def _mean_pooling(self, token_embeddings, attention_mask):
        """Apply mean pooling to token embeddings"""
        import torch
        
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return sum_embeddings / sum_mask
    
    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for query text"""
        embeddings = await self.embed_documents([text])
        return embeddings[0]

# Register custom embedding providers
from langswarm.core.memory.vector_stores.embeddings import EmbeddingProviderFactory

EmbeddingProviderFactory.register_provider(
    "huggingface",
    HuggingFaceEmbeddingProvider
)

EmbeddingProviderFactory.register_provider(
    "opensource", 
    OpenSourceEmbeddingProvider
)

# Usage
embedding_provider = HuggingFaceEmbeddingProvider(
    model_name="sentence-transformers/all-mpnet-base-v2",
    batch_size=32,
    normalize_embeddings=True,
    cache_embeddings=True
)

store = VectorStoreFactory.create_sqlite_store(
    db_path="custom_embeddings.db",
    embedding_provider=embedding_provider
)
```

---

## 🎯 Custom Similarity Metrics

### **Implementing Custom Distance Functions**

```python
import numpy as np
from typing import Callable, Dict, Any
from langswarm.core.memory.vector_stores.interfaces import SimilarityMetric

class CustomSimilarityMetrics:
    """Collection of custom similarity metrics"""
    
    @staticmethod
    def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Manhattan distance"""
        return np.sum(np.abs(a - b))
    
    @staticmethod
    def chebyshev_distance(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Chebyshev distance"""
        return np.max(np.abs(a - b))
    
    @staticmethod
    def jaccard_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Jaccard similarity (for binary vectors)"""
        intersection = np.sum(np.minimum(a, b))
        union = np.sum(np.maximum(a, b))
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def pearson_correlation(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Pearson correlation coefficient"""
        return np.corrcoef(a, b)[0, 1]
    
    @staticmethod
    def kl_divergence(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Kullback-Leibler divergence"""
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        a_safe = a + epsilon
        b_safe = b + epsilon
        
        # Normalize to probability distributions
        a_norm = a_safe / np.sum(a_safe)
        b_norm = b_safe / np.sum(b_safe)
        
        return np.sum(a_norm * np.log(a_norm / b_norm))
    
    @staticmethod
    def weighted_cosine_similarity(
        a: np.ndarray,
        b: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """Calculate weighted cosine similarity"""
        weighted_a = a * weights
        weighted_b = b * weights
        
        dot_product = np.dot(weighted_a, weighted_b)
        norm_a = np.linalg.norm(weighted_a)
        norm_b = np.linalg.norm(weighted_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

class AdaptiveSimilarityMetric:
    """Adaptive similarity metric that combines multiple metrics"""
    
    def __init__(
        self,
        primary_metric: str = "cosine",
        secondary_metrics: Dict[str, float] = None,
        adaptation_threshold: float = 0.5
    ):
        """Initialize adaptive similarity metric
        
        Args:
            primary_metric: Primary similarity metric
            secondary_metrics: Secondary metrics with weights
            adaptation_threshold: Threshold for metric adaptation
        """
        self.primary_metric = primary_metric
        self.secondary_metrics = secondary_metrics or {}
        self.adaptation_threshold = adaptation_threshold
        
        # Metric functions mapping
        self.metric_functions = {
            "cosine": self._cosine_similarity,
            "euclidean": self._euclidean_similarity,
            "manhattan": CustomSimilarityMetrics.manhattan_distance,
            "chebyshev": CustomSimilarityMetrics.chebyshev_distance,
            "jaccard": CustomSimilarityMetrics.jaccard_similarity,
            "pearson": CustomSimilarityMetrics.pearson_correlation,
            "kl_divergence": CustomSimilarityMetrics.kl_divergence
        }
    
    def calculate_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
        metadata: Dict[str, Any] = None
    ) -> np.ndarray:
        """Calculate adaptive similarity scores"""
        
        # Calculate primary similarity
        primary_scores = self._calculate_metric(
            self.primary_metric,
            query_embedding,
            document_embeddings
        )
        
        # If no secondary metrics, return primary scores
        if not self.secondary_metrics:
            return primary_scores
        
        # Calculate secondary metrics
        secondary_scores = {}
        for metric, weight in self.secondary_metrics.items():
            scores = self._calculate_metric(metric, query_embedding, document_embeddings)
            secondary_scores[metric] = scores * weight
        
        # Combine scores based on adaptation logic
        final_scores = self._adaptive_combination(
            primary_scores,
            secondary_scores,
            metadata
        )
        
        return final_scores
    
    def _calculate_metric(
        self,
        metric_name: str,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate specific similarity metric"""
        metric_func = self.metric_functions.get(metric_name)
        if not metric_func:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        scores = []
        for doc_embedding in document_embeddings:
            score = metric_func(query_embedding, doc_embedding)
            scores.append(score)
        
        return np.array(scores)
    
    def _adaptive_combination(
        self,
        primary_scores: np.ndarray,
        secondary_scores: Dict[str, np.ndarray],
        metadata: Dict[str, Any] = None
    ) -> np.ndarray:
        """Adaptively combine similarity scores"""
        
        # Start with primary scores
        final_scores = primary_scores.copy()
        
        # Identify low-confidence primary scores
        low_confidence_mask = primary_scores < self.adaptation_threshold
        
        if np.any(low_confidence_mask):
            # For low-confidence scores, blend with secondary metrics
            for metric, scores in secondary_scores.items():
                final_scores[low_confidence_mask] = (
                    final_scores[low_confidence_mask] * 0.6 +
                    scores[low_confidence_mask] * 0.4
                )
        
        # Apply metadata-based adjustments if available
        if metadata:
            final_scores = self._apply_metadata_adjustments(final_scores, metadata)
        
        return final_scores
    
    def _apply_metadata_adjustments(
        self,
        scores: np.ndarray,
        metadata: Dict[str, Any]
    ) -> np.ndarray:
        """Apply metadata-based score adjustments"""
        
        # Example: boost scores for documents from preferred sources
        preferred_sources = metadata.get("preferred_sources", [])
        if preferred_sources:
            # This would require document metadata in the calculation
            # Implementation depends on how metadata is passed
            pass
        
        return scores
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    @staticmethod
    def _euclidean_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate Euclidean similarity (inverse of distance)"""
        distance = np.linalg.norm(a - b)
        return 1.0 / (1.0 + distance)

# Integration with custom vector store
class CustomVectorStoreWithMetrics(CustomVectorStore):
    """Vector store with custom similarity metrics"""
    
    def __init__(self, *args, **kwargs):
        similarity_metric = kwargs.pop("similarity_metric", "cosine")
        super().__init__(*args, **kwargs)
        
        # Initialize custom similarity metric
        if isinstance(similarity_metric, str):
            self.similarity_calculator = AdaptiveSimilarityMetric(primary_metric=similarity_metric)
        else:
            self.similarity_calculator = similarity_metric
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Enhanced query with custom similarity metrics"""
        
        # Get all potential matches (broader search)
        broad_query = VectorQuery(
            embedding=query.embedding,
            text=query.text,
            top_k=query.top_k * 3,  # Get more candidates
            similarity_threshold=0.0,  # No threshold filtering
            metadata_filter=query.metadata_filter,
            include_metadata=True,
            include_embeddings=True
        )
        
        # Execute broad search using parent implementation
        broad_results = await super().query(broad_query)
        
        if not broad_results:
            return []
        
        # Extract embeddings and recalculate similarities
        query_embedding = query.embedding
        if query_embedding is None and query.text:
            query_embedding = await self.embedding_provider.embed_query(query.text)
        
        document_embeddings = np.array([
            result.document.embedding for result in broad_results
        ])
        
        # Calculate custom similarities
        custom_similarities = self.similarity_calculator.calculate_similarity(
            query_embedding,
            document_embeddings,
            metadata={"query_metadata": query.metadata_filter}
        )
        
        # Update results with new similarities
        for i, result in enumerate(broad_results):
            result.similarity = custom_similarities[i]
            result.score = custom_similarities[i]  # Update score to match
        
        # Re-sort by new similarities
        broad_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Apply threshold filtering
        filtered_results = [
            result for result in broad_results
            if result.similarity >= query.similarity_threshold
        ]
        
        # Return top_k results
        return filtered_results[:query.top_k]

# Usage
custom_store = CustomVectorStoreWithMetrics(
    connection_string="custom://localhost:9000",
    similarity_metric=AdaptiveSimilarityMetric(
        primary_metric="cosine",
        secondary_metrics={
            "pearson": 0.3,
            "euclidean": 0.2
        },
        adaptation_threshold=0.6
    )
)
```

---

## 🔍 Advanced Search and Filtering

### **Custom Search Logic Implementation**

```python
from typing import List, Dict, Any, Optional, Callable
import numpy as np
from datetime import datetime, timedelta

class AdvancedSearchEngine:
    """Advanced search engine with custom logic"""
    
    def __init__(self, vector_store: IVectorStore):
        self.vector_store = vector_store
        self.search_strategies = {}
        self.result_processors = {}
        
        # Register default strategies
        self._register_default_strategies()
    
    def register_search_strategy(
        self,
        name: str,
        strategy: Callable[[VectorQuery], List[VectorResult]]
    ):
        """Register custom search strategy"""
        self.search_strategies[name] = strategy
    
    def register_result_processor(
        self,
        name: str,
        processor: Callable[[List[VectorResult], Dict[str, Any]], List[VectorResult]]
    ):
        """Register custom result processor"""
        self.result_processors[name] = processor
    
    async def advanced_search(
        self,
        query: VectorQuery,
        strategy: str = "hybrid",
        processors: List[str] = None,
        strategy_config: Dict[str, Any] = None
    ) -> List[VectorResult]:
        """Perform advanced search with custom strategies"""
        
        # Execute search strategy
        if strategy not in self.search_strategies:
            raise ValueError(f"Unknown search strategy: {strategy}")
        
        strategy_func = self.search_strategies[strategy]
        results = await strategy_func(query, strategy_config or {})
        
        # Apply result processors
        if processors:
            for processor_name in processors:
                if processor_name in self.result_processors:
                    processor_func = self.result_processors[processor_name]
                    results = processor_func(results, strategy_config or {})
        
        return results
    
    def _register_default_strategies(self):
        """Register default search strategies"""
        
        # Hybrid search strategy
        async def hybrid_search(query: VectorQuery, config: Dict[str, Any]) -> List[VectorResult]:
            """Combine semantic and keyword search"""
            
            # Semantic search
            semantic_results = await self.vector_store.query(query)
            
            # Keyword search (if content is available)
            keyword_results = await self._keyword_search(query, config)
            
            # Combine and re-rank results
            combined_results = self._combine_search_results(
                semantic_results,
                keyword_results,
                config.get("semantic_weight", 0.7),
                config.get("keyword_weight", 0.3)
            )
            
            return combined_results
        
        # Multi-vector search strategy
        async def multi_vector_search(query: VectorQuery, config: Dict[str, Any]) -> List[VectorResult]:
            """Search using multiple query representations"""
            
            all_results = []
            
            # Original query
            original_results = await self.vector_store.query(query)
            all_results.extend(original_results)
            
            # Expanded queries
            expanded_queries = await self._expand_query(query, config)
            for expanded_query in expanded_queries:
                expanded_results = await self.vector_store.query(expanded_query)
                all_results.extend(expanded_results)
            
            # Deduplicate and re-rank
            deduplicated_results = self._deduplicate_results(all_results)
            
            return deduplicated_results[:query.top_k]
        
        # Temporal search strategy
        async def temporal_search(query: VectorQuery, config: Dict[str, Any]) -> List[VectorResult]:
            """Search with temporal relevance weighting"""
            
            # Base search
            base_results = await self.vector_store.query(query)
            
            # Apply temporal weighting
            temporal_results = self._apply_temporal_weighting(
                base_results,
                config.get("time_decay_factor", 0.1),
                config.get("reference_time", datetime.now())
            )
            
            # Re-sort by adjusted scores
            temporal_results.sort(key=lambda x: x.score, reverse=True)
            
            return temporal_results
        
        # Register strategies
        self.search_strategies["hybrid"] = hybrid_search
        self.search_strategies["multi_vector"] = multi_vector_search
        self.search_strategies["temporal"] = temporal_search
        
        # Register default processors
        self.result_processors["diversity"] = self._diversify_results
        self.result_processors["personalization"] = self._personalize_results
        self.result_processors["quality_filter"] = self._filter_by_quality
    
    async def _keyword_search(
        self,
        query: VectorQuery,
        config: Dict[str, Any]
    ) -> List[VectorResult]:
        """Perform keyword-based search"""
        
        if not query.text:
            return []
        
        # Extract keywords
        keywords = self._extract_keywords(query.text)
        
        # Search for documents containing keywords
        keyword_results = []
        
        # This would require full-text search capabilities
        # Implementation depends on your backend
        
        return keyword_results
    
    def _combine_search_results(
        self,
        semantic_results: List[VectorResult],
        keyword_results: List[VectorResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[VectorResult]:
        """Combine semantic and keyword search results"""
        
        # Create document ID to result mapping
        semantic_map = {result.document.id: result for result in semantic_results}
        keyword_map = {result.document.id: result for result in keyword_results}
        
        # Combine scores
        all_doc_ids = set(semantic_map.keys()) | set(keyword_map.keys())
        combined_results = []
        
        for doc_id in all_doc_ids:
            semantic_result = semantic_map.get(doc_id)
            keyword_result = keyword_map.get(doc_id)
            
            # Calculate combined score
            combined_score = 0.0
            
            if semantic_result:
                combined_score += semantic_result.score * semantic_weight
                base_result = semantic_result
            
            if keyword_result:
                combined_score += keyword_result.score * keyword_weight
                if not semantic_result:
                    base_result = keyword_result
            
            # Create combined result
            combined_result = VectorResult(
                document=base_result.document,
                score=combined_score,
                similarity=base_result.similarity if semantic_result else 0.0
            )
            
            combined_results.append(combined_result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results
    
    async def _expand_query(
        self,
        query: VectorQuery,
        config: Dict[str, Any]
    ) -> List[VectorQuery]:
        """Expand query with synonyms and related terms"""
        
        if not query.text:
            return []
        
        expanded_queries = []
        
        # Synonym expansion
        synonyms = await self._get_synonyms(query.text)
        for synonym in synonyms:
            expanded_query = VectorQuery(
                text=synonym,
                top_k=query.top_k,
                similarity_threshold=query.similarity_threshold * 0.9,  # Lower threshold
                metadata_filter=query.metadata_filter
            )
            expanded_queries.append(expanded_query)
        
        # Related terms expansion
        related_terms = await self._get_related_terms(query.text)
        for term in related_terms:
            expanded_query = VectorQuery(
                text=term,
                top_k=query.top_k // 2,  # Fewer results per expansion
                similarity_threshold=query.similarity_threshold * 0.8,
                metadata_filter=query.metadata_filter
            )
            expanded_queries.append(expanded_query)
        
        return expanded_queries[:config.get("max_expansions", 3)]
    
    def _deduplicate_results(self, results: List[VectorResult]) -> List[VectorResult]:
        """Remove duplicate results and combine scores"""
        
        doc_to_results = {}
        
        for result in results:
            doc_id = result.document.id
            if doc_id not in doc_to_results:
                doc_to_results[doc_id] = []
            doc_to_results[doc_id].append(result)
        
        # Combine duplicate results
        deduplicated = []
        for doc_id, doc_results in doc_to_results.items():
            if len(doc_results) == 1:
                deduplicated.append(doc_results[0])
            else:
                # Combine scores (use maximum)
                best_result = max(doc_results, key=lambda x: x.score)
                deduplicated.append(best_result)
        
        return deduplicated
    
    def _apply_temporal_weighting(
        self,
        results: List[VectorResult],
        time_decay_factor: float,
        reference_time: datetime
    ) -> List[VectorResult]:
        """Apply temporal decay to search results"""
        
        for result in results:
            # Get document timestamp
            doc_time = result.document.created_at or result.document.updated_at
            
            if doc_time:
                # Calculate time difference in days
                time_diff = (reference_time - doc_time).total_seconds() / 86400
                
                # Apply exponential decay
                time_weight = np.exp(-time_decay_factor * time_diff)
                
                # Adjust score
                result.score = result.score * time_weight
        
        return results
    
    def _diversify_results(
        self,
        results: List[VectorResult],
        config: Dict[str, Any]
    ) -> List[VectorResult]:
        """Diversify search results to avoid redundancy"""
        
        diversity_threshold = config.get("diversity_threshold", 0.8)
        max_results = config.get("max_diverse_results", len(results))
        
        if not results:
            return results
        
        diverse_results = [results[0]]  # Always include top result
        
        for result in results[1:]:
            # Check diversity against selected results
            is_diverse = True
            
            for selected_result in diverse_results:
                similarity = self._calculate_document_similarity(
                    result.document,
                    selected_result.document
                )
                
                if similarity > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_results.append(result)
                
                if len(diverse_results) >= max_results:
                    break
        
        return diverse_results
    
    def _personalize_results(
        self,
        results: List[VectorResult],
        config: Dict[str, Any]
    ) -> List[VectorResult]:
        """Personalize results based on user preferences"""
        
        user_preferences = config.get("user_preferences", {})
        
        if not user_preferences:
            return results
        
        # Apply preference-based boosting
        for result in results:
            boost_factor = 1.0
            
            # Category preferences
            doc_category = result.document.metadata.get("category")
            if doc_category and doc_category in user_preferences.get("preferred_categories", []):
                boost_factor *= 1.2
            
            # Source preferences
            doc_source = result.document.metadata.get("source")
            if doc_source and doc_source in user_preferences.get("preferred_sources", []):
                boost_factor *= 1.1
            
            # Apply boost
            result.score *= boost_factor
        
        # Re-sort by adjusted scores
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _filter_by_quality(
        self,
        results: List[VectorResult],
        config: Dict[str, Any]
    ) -> List[VectorResult]:
        """Filter results by quality metrics"""
        
        min_quality_score = config.get("min_quality_score", 0.5)
        
        filtered_results = []
        
        for result in results:
            quality_score = self._calculate_quality_score(result.document)
            
            if quality_score >= min_quality_score:
                filtered_results.append(result)
        
        return filtered_results
    
    def _calculate_document_similarity(
        self,
        doc1: VectorDocument,
        doc2: VectorDocument
    ) -> float:
        """Calculate similarity between two documents"""
        
        if doc1.embedding is not None and doc2.embedding is not None:
            # Use embedding similarity
            dot_product = np.dot(doc1.embedding, doc2.embedding)
            norm1 = np.linalg.norm(doc1.embedding)
            norm2 = np.linalg.norm(doc2.embedding)
            
            if norm1 > 0 and norm2 > 0:
                return dot_product / (norm1 * norm2)
        
        # Fallback to content similarity (simple)
        return len(set(doc1.content.split()) & set(doc2.content.split())) / len(set(doc1.content.split()) | set(doc2.content.split()))
    
    def _calculate_quality_score(self, document: VectorDocument) -> float:
        """Calculate document quality score"""
        
        quality_score = 1.0
        
        # Content length factor
        content_length = len(document.content)
        if content_length < 50:
            quality_score *= 0.5
        elif content_length > 1000:
            quality_score *= 1.2
        
        # Metadata completeness
        if document.metadata:
            quality_score *= 1.1
        
        # Source quality (if available)
        source = document.metadata.get("source", "")
        if "wikipedia" in source.lower():
            quality_score *= 1.2
        elif "blog" in source.lower():
            quality_score *= 0.9
        
        return min(quality_score, 1.0)
    
    # Utility methods
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP libraries)
        import re
        
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        words = re.findall(r'\w+', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Top 10 keywords
    
    async def _get_synonyms(self, text: str) -> List[str]:
        """Get synonyms for query expansion"""
        # This would integrate with a thesaurus API or WordNet
        # Placeholder implementation
        return []
    
    async def _get_related_terms(self, text: str) -> List[str]:
        """Get related terms for query expansion"""
        # This would use word embeddings or knowledge graphs
        # Placeholder implementation
        return []

# Usage
advanced_search = AdvancedSearchEngine(vector_store)

# Hybrid search
results = await advanced_search.advanced_search(
    query=VectorQuery(text="machine learning algorithms", top_k=10),
    strategy="hybrid",
    processors=["diversity", "personalization"],
    strategy_config={
        "semantic_weight": 0.7,
        "keyword_weight": 0.3,
        "diversity_threshold": 0.8,
        "user_preferences": {
            "preferred_categories": ["AI", "Technology"],
            "preferred_sources": ["academic", "documentation"]
        }
    }
)
```

---

## 📚 Extension Best Practices

### **Vector Store Extension Guidelines**
- **Interface Compliance**: Always implement the complete IVectorStore interface
- **Async Operations**: Use async/await for all operations to maintain compatibility
- **Error Handling**: Provide clear, informative error messages with context
- **Type Safety**: Use proper type annotations and validate inputs
- **Performance**: Optimize for your specific use case and backend

### **Embedding Provider Guidelines**
- **Batch Processing**: Implement efficient batch processing for large datasets
- **Caching**: Consider implementing embedding caching for repeated queries
- **Normalization**: Normalize embeddings when appropriate for consistency
- **Error Recovery**: Handle API failures gracefully with retries and fallbacks
- **Resource Management**: Properly manage API quotas and rate limits

### **Similarity Metric Guidelines**
- **Mathematical Correctness**: Ensure similarity calculations are mathematically sound
- **Performance**: Optimize for vector operations using numpy/scipy
- **Flexibility**: Allow configuration of metric parameters
- **Validation**: Validate input vectors and handle edge cases
- **Documentation**: Clearly document when and why to use specific metrics

### **Search Engine Guidelines**
- **Strategy Modularity**: Keep search strategies modular and composable
- **Result Quality**: Focus on result relevance and quality
- **Performance**: Monitor search performance and optimize bottlenecks
- **Configurability**: Make search behavior configurable for different use cases
- **Testing**: Thoroughly test search quality with diverse query sets

---

**LangSwarm V2's native vector store system provides comprehensive extension capabilities, allowing developers to customize every aspect of vector storage and search while maintaining compatibility with the unified interface and high performance standards.**
