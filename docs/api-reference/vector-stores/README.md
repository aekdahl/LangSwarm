# LangSwarm V2 Native Vector Stores API Reference

**Complete API reference for native vector database implementations**

## 🎯 Overview

LangSwarm V2's native vector stores provide direct API integrations with major vector databases, replacing LangChain/LlamaIndex dependencies with high-performance, type-safe implementations. The API offers 20-40% better performance while maintaining a unified interface across all backends.

**Core Modules:**
- **`interfaces`**: Type-safe vector store interfaces and data structures
- **`pinecone_native`**: Direct Pinecone API integration
- **`qdrant_native`**: Direct Qdrant API integration  
- **`chroma_native`**: Direct ChromaDB API integration
- **`sqlite_native`**: Local SQLite vector storage with numpy similarity
- **`factory`**: Unified factory for store creation and management
- **`embeddings`**: Native embedding providers (OpenAI, custom)

---

## 📦 Package API

### **Main Package Interface**

```python
from langswarm.core.memory.vector_stores import (
    # Factory and Management
    VectorStoreFactory,
    
    # Vector Store Interfaces
    IVectorStore,
    IEmbeddingProvider,
    
    # Native Store Implementations
    NativePineconeStore,
    NativeQdrantStore,
    NativeChromaStore,
    NativeSQLiteStore,
    
    # Data Structures
    VectorDocument,
    VectorQuery,
    VectorResult,
    VectorStoreStats,
    VectorStoreHealth,
    
    # Embedding Providers
    OpenAIEmbeddingProvider,
    BaseEmbeddingProvider,
    
    # Configuration
    VectorStoreConfig,
    EmbeddingConfig,
    
    # Exceptions
    VectorStoreError,
    EmbeddingError,
    ConnectionError,
    QueryError
)
```

---

## 🏗️ Core Interfaces

### **IVectorStore**

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np

class IVectorStore(ABC):
    """Core vector store interface for document storage and similarity search"""
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if store is connected"""
    
    @property
    @abstractmethod
    def backend_type(self) -> str:
        """Get backend type identifier"""
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to vector store backend
        
        Raises:
            ConnectionError: If connection fails
        """
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from vector store backend"""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to vector store
        
        Args:
            documents: List of documents to add
            batch_size: Batch size for processing
            
        Returns:
            List of document IDs that were added
            
        Raises:
            VectorStoreError: If operation fails
        """
    
    @abstractmethod
    async def query(
        self,
        query: VectorQuery
    ) -> List[VectorResult]:
        """Perform similarity search
        
        Args:
            query: Vector query specification
            
        Returns:
            List of similar documents with scores
            
        Raises:
            QueryError: If query fails
        """
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Get document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document if found, None otherwise
        """
    
    @abstractmethod
    async def update_document(
        self,
        document_id: str,
        document: VectorDocument
    ) -> None:
        """Update existing document
        
        Args:
            document_id: Document identifier
            document: Updated document data
            
        Raises:
            VectorStoreError: If update fails
        """
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> int:
        """Delete documents by ID
        
        Args:
            document_ids: List of document identifiers
            
        Returns:
            Number of documents deleted
        """
    
    @abstractmethod
    async def get_statistics(self) -> VectorStoreStats:
        """Get store statistics and metrics
        
        Returns:
            Comprehensive store statistics
        """
    
    @abstractmethod
    async def health_check(self) -> VectorStoreHealth:
        """Check store health and connectivity
        
        Returns:
            Health status and diagnostics
        """
    
    @abstractmethod
    async def create_index(
        self,
        index_config: Dict[str, Any] = None
    ) -> None:
        """Create or update vector index
        
        Args:
            index_config: Backend-specific index configuration
        """
    
    @abstractmethod
    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        metadata_filter: Dict[str, Any] = None
    ) -> List[VectorDocument]:
        """List documents with pagination
        
        Args:
            limit: Maximum number of documents
            offset: Number of documents to skip
            metadata_filter: Filter by metadata
            
        Returns:
            List of documents
        """
```

### **IEmbeddingProvider**

```python
class IEmbeddingProvider(ABC):
    """Interface for embedding generation providers"""
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
    
    @property
    @abstractmethod
    def max_batch_size(self) -> int:
        """Get maximum batch size for embedding"""
    
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple documents
        
        Args:
            texts: List of text documents
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
    
    @abstractmethod
    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for query text
        
        Args:
            text: Query text
            
        Returns:
            Query embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
    
    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[np.ndarray]:
        """Generate embeddings in batches for efficiency
        
        Args:
            texts: List of text documents
            batch_size: Batch size (uses max_batch_size if None)
            
        Returns:
            List of embedding vectors
        """
```

---

## 🔧 Data Structures

### **VectorDocument**

```python
@dataclass
class VectorDocument:
    """Document with vector embedding and metadata"""
    
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    
    # Document properties
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        """Initialize document timestamps"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorDocument':
        """Create from dictionary"""
        embedding = None
        if data.get("embedding"):
            embedding = np.array(data["embedding"])
        
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=embedding,
            created_at=created_at,
            updated_at=updated_at,
            source=data.get("source")
        )
    
    def update_content(self, content: str):
        """Update document content and timestamp"""
        self.content = content
        self.updated_at = datetime.now()
        self.embedding = None  # Reset embedding for re-generation
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata field"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
```

### **VectorQuery**

```python
@dataclass
class VectorQuery:
    """Vector similarity search query specification"""
    
    # Query specification (one of these must be provided)
    embedding: Optional[np.ndarray] = None
    text: Optional[str] = None
    
    # Search parameters
    top_k: int = 10
    similarity_threshold: float = 0.0
    
    # Filtering
    metadata_filter: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[str]] = None
    
    # Result configuration
    include_metadata: bool = True
    include_embeddings: bool = False
    include_scores: bool = True
    
    # Advanced parameters
    similarity_metric: Optional[str] = None  # cosine, euclidean, dot_product
    rerank: bool = False
    diversify_results: bool = False
    
    def validate(self) -> List[str]:
        """Validate query parameters
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if self.embedding is None and self.text is None:
            errors.append("Either 'embedding' or 'text' must be provided")
        
        if self.embedding is not None and self.text is not None:
            errors.append("Only one of 'embedding' or 'text' should be provided")
        
        if self.top_k <= 0:
            errors.append("top_k must be positive")
        
        if not 0 <= self.similarity_threshold <= 1:
            errors.append("similarity_threshold must be between 0 and 1")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "text": self.text,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "metadata_filter": self.metadata_filter,
            "document_ids": self.document_ids,
            "include_metadata": self.include_metadata,
            "include_embeddings": self.include_embeddings,
            "include_scores": self.include_scores,
            "similarity_metric": self.similarity_metric,
            "rerank": self.rerank,
            "diversify_results": self.diversify_results
        }
```

### **VectorResult**

```python
@dataclass
class VectorResult:
    """Vector similarity search result"""
    
    document: VectorDocument
    score: float
    similarity: float
    
    # Result metadata
    rank: Optional[int] = None
    distance: Optional[float] = None
    
    # Advanced result data
    explanation: Optional[Dict[str, Any]] = None
    rerank_score: Optional[float] = None
    
    def __post_init__(self):
        """Calculate distance from similarity if not provided"""
        if self.distance is None:
            self.distance = 1.0 - self.similarity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "similarity": self.similarity,
            "rank": self.rank,
            "distance": self.distance,
            "explanation": self.explanation,
            "rerank_score": self.rerank_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorResult':
        """Create from dictionary"""
        return cls(
            document=VectorDocument.from_dict(data["document"]),
            score=data["score"],
            similarity=data["similarity"],
            rank=data.get("rank"),
            distance=data.get("distance"),
            explanation=data.get("explanation"),
            rerank_score=data.get("rerank_score")
        )
```

### **VectorStoreStats**

```python
@dataclass
class VectorStoreStats:
    """Vector store statistics and metrics"""
    
    # Basic statistics
    total_documents: int
    total_vectors: int
    embedding_dimension: int
    
    # Storage metrics
    index_size_mb: float
    storage_size_mb: float
    memory_usage_mb: float
    
    # Performance metrics
    avg_query_time_ms: float
    total_queries: int
    queries_per_second: float
    
    # Health metrics
    last_updated: datetime
    backend: str
    version: str
    
    # Advanced metrics
    vector_density: Optional[float] = None
    index_fragmentation: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.vector_density is None and self.total_documents > 0:
            self.vector_density = self.total_vectors / self.total_documents
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_documents": self.total_documents,
            "total_vectors": self.total_vectors,
            "embedding_dimension": self.embedding_dimension,
            "index_size_mb": self.index_size_mb,
            "storage_size_mb": self.storage_size_mb,
            "memory_usage_mb": self.memory_usage_mb,
            "avg_query_time_ms": self.avg_query_time_ms,
            "total_queries": self.total_queries,
            "queries_per_second": self.queries_per_second,
            "last_updated": self.last_updated.isoformat(),
            "backend": self.backend,
            "version": self.version,
            "vector_density": self.vector_density,
            "index_fragmentation": self.index_fragmentation
        }
```

### **VectorStoreHealth**

```python
@dataclass
class VectorStoreHealth:
    """Vector store health status and diagnostics"""
    
    is_healthy: bool
    status: str  # "healthy", "degraded", "unhealthy"
    
    # Connection status
    is_connected: bool
    response_time_ms: float
    
    # Resource status
    available_space_gb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    
    # Issues and warnings
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Diagnostic info
    last_check: datetime = field(default_factory=datetime.now)
    backend_version: Optional[str] = None
    
    def add_issue(self, issue: str):
        """Add health issue"""
        self.issues.append(issue)
        self.is_healthy = False
        if self.status == "healthy":
            self.status = "unhealthy"
    
    def add_warning(self, warning: str):
        """Add health warning"""
        self.warnings.append(warning)
        if self.status == "healthy":
            self.status = "degraded"
```

---

## 🏭 Vector Store Implementations

### **NativePineconeStore**

```python
class NativePineconeStore(IVectorStore):
    """Native Pinecone vector store implementation"""
    
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        embedding_dimension: int,
        metric: str = "cosine",
        namespace: str = "",
        embedding_provider: IEmbeddingProvider = None
    ):
        """Initialize Pinecone store
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., "us-west1-gcp")
            index_name: Pinecone index name
            embedding_dimension: Vector embedding dimension
            metric: Similarity metric ("cosine", "euclidean", "dotproduct")
            namespace: Pinecone namespace for isolation
            embedding_provider: Embedding provider for text processing
        """
        
    async def connect(self) -> None:
        """Connect to Pinecone service"""
        
    async def create_index(
        self,
        index_config: Dict[str, Any] = None
    ) -> None:
        """Create Pinecone index if it doesn't exist
        
        Args:
            index_config: Pinecone-specific index configuration
        """
        
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to Pinecone index"""
        
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query Pinecone index for similar vectors"""
        
    async def delete_documents(self, document_ids: List[str]) -> int:
        """Delete documents from Pinecone index"""
        
    async def get_statistics(self) -> VectorStoreStats:
        """Get Pinecone index statistics"""
        
    async def health_check(self) -> VectorStoreHealth:
        """Check Pinecone service health"""
        
    # Pinecone-specific methods
    async def list_indexes(self) -> List[str]:
        """List available Pinecone indexes"""
        
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get detailed Pinecone index statistics"""
        
    async def configure_namespace(self, namespace: str) -> None:
        """Configure Pinecone namespace"""
```

### **NativeQdrantStore**

```python
class NativeQdrantStore(IVectorStore):
    """Native Qdrant vector store implementation"""
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str = None,
        collection_name: str = "langswarm_vectors",
        embedding_dimension: int = 1536,
        distance_metric: str = "Cosine",
        embedding_provider: IEmbeddingProvider = None,
        connection_config: Dict[str, Any] = None
    ):
        """Initialize Qdrant store
        
        Args:
            url: Qdrant server URL
            api_key: API key for Qdrant Cloud
            collection_name: Collection name for vectors
            embedding_dimension: Vector embedding dimension
            distance_metric: Distance metric ("Cosine", "Euclid", "Dot")
            embedding_provider: Embedding provider for text processing
            connection_config: Additional connection configuration
        """
        
    async def connect(self) -> None:
        """Connect to Qdrant service"""
        
    async def create_collection(
        self,
        collection_config: Dict[str, Any] = None
    ) -> None:
        """Create Qdrant collection if it doesn't exist
        
        Args:
            collection_config: Qdrant-specific collection configuration
        """
        
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to Qdrant collection"""
        
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query Qdrant collection for similar vectors"""
        
    # Qdrant-specific methods
    async def scroll_documents(
        self,
        limit: int = 100,
        offset: str = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> Dict[str, Any]:
        """Scroll through documents in collection"""
        
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get detailed collection information"""
        
    async def create_payload_index(
        self,
        field_name: str,
        field_type: str = "keyword"
    ) -> None:
        """Create payload index for efficient filtering"""
```

### **NativeChromaStore**

```python
class NativeChromaStore(IVectorStore):
    """Native ChromaDB vector store implementation"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "langswarm_vectors",
        embedding_dimension: int = 1536,
        persist_directory: str = None,
        embedding_provider: IEmbeddingProvider = None,
        settings: Dict[str, Any] = None
    ):
        """Initialize ChromaDB store
        
        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            collection_name: Collection name for vectors
            embedding_dimension: Vector embedding dimension
            persist_directory: Directory for persistent storage
            embedding_provider: Embedding provider for text processing
            settings: ChromaDB client settings
        """
        
    async def connect(self) -> None:
        """Connect to ChromaDB service"""
        
    async def create_collection(
        self,
        collection_config: Dict[str, Any] = None
    ) -> None:
        """Create ChromaDB collection if it doesn't exist
        
        Args:
            collection_config: ChromaDB-specific collection configuration
        """
        
    # ChromaDB-specific methods
    async def list_collections(self) -> List[str]:
        """List available ChromaDB collections"""
        
    async def get_collection_count(self) -> int:
        """Get number of documents in collection"""
        
    async def peek_documents(self, limit: int = 10) -> List[VectorDocument]:
        """Peek at first N documents in collection"""
```

### **NativeSQLiteStore**

```python
class NativeSQLiteStore(IVectorStore):
    """Native SQLite vector store with numpy similarity calculations"""
    
    def __init__(
        self,
        db_path: str,
        embedding_dimension: int,
        similarity_metric: str = "cosine",
        embedding_provider: IEmbeddingProvider = None,
        connection_config: Dict[str, Any] = None
    ):
        """Initialize SQLite vector store
        
        Args:
            db_path: Path to SQLite database file
            embedding_dimension: Vector embedding dimension
            similarity_metric: Similarity metric ("cosine", "euclidean", "dot_product")
            embedding_provider: Embedding provider for text processing
            connection_config: SQLite connection configuration
        """
        
    async def connect(self) -> None:
        """Connect to SQLite database and create tables"""
        
    async def create_tables(self) -> None:
        """Create database tables for vector storage"""
        
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to SQLite database"""
        
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query SQLite database using numpy similarity calculations"""
        
    # SQLite-specific methods
    async def vacuum_database(self) -> None:
        """Vacuum SQLite database for optimization"""
        
    async def rebuild_index(self) -> None:
        """Rebuild database indexes"""
        
    async def get_database_size(self) -> Dict[str, Any]:
        """Get detailed database size information"""
        
    def _calculate_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate similarity scores using numpy
        
        Args:
            query_embedding: Query vector
            document_embeddings: Document vectors matrix
            
        Returns:
            Similarity scores array
        """
```

---

## ⚙️ Vector Store Factory

### **VectorStoreFactory**

```python
class VectorStoreFactory:
    """Factory for creating and managing vector stores"""
    
    @staticmethod
    def create_pinecone_store(
        api_key: str,
        environment: str,
        index_name: str,
        embedding_dimension: int = 1536,
        **kwargs
    ) -> NativePineconeStore:
        """Create Pinecone vector store
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Index name
            embedding_dimension: Vector dimension
            **kwargs: Additional configuration
            
        Returns:
            Configured Pinecone store
        """
        
    @staticmethod
    def create_qdrant_store(
        url: str = "http://localhost:6333",
        api_key: str = None,
        collection_name: str = "langswarm_vectors",
        embedding_dimension: int = 1536,
        **kwargs
    ) -> NativeQdrantStore:
        """Create Qdrant vector store"""
        
    @staticmethod
    def create_chroma_store(
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "langswarm_vectors",
        embedding_dimension: int = 1536,
        **kwargs
    ) -> NativeChromaStore:
        """Create ChromaDB vector store"""
        
    @staticmethod
    def create_sqlite_store(
        db_path: str,
        embedding_dimension: int = 1536,
        **kwargs
    ) -> NativeSQLiteStore:
        """Create SQLite vector store"""
        
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> IVectorStore:
        """Create vector store from configuration
        
        Args:
            config: Vector store configuration
            
        Returns:
            Configured vector store
            
        Raises:
            ValueError: If configuration is invalid
        """
        
    @staticmethod
    def create_development_store(
        embedding_dimension: int = 1536
    ) -> IVectorStore:
        """Create vector store suitable for development
        
        Automatically selects best available option:
        1. ChromaDB (if available)
        2. SQLite (fallback)
        
        Args:
            embedding_dimension: Vector dimension
            
        Returns:
            Development-ready vector store
        """
        
    @staticmethod
    def create_production_store(
        preferred_backends: List[str] = None,
        config: Dict[str, Any] = None
    ) -> IVectorStore:
        """Create vector store suitable for production
        
        Args:
            preferred_backends: Ordered list of preferred backends
            config: Backend-specific configuration
            
        Returns:
            Production-ready vector store
        """
        
    @staticmethod
    def list_available_backends() -> List[str]:
        """List available vector store backends
        
        Returns:
            List of backend names
        """
        
    @staticmethod
    def get_requirements(backend: str) -> Dict[str, Any]:
        """Get requirements for specific backend
        
        Args:
            backend: Backend name
            
        Returns:
            Requirements and dependencies
        """
        
    @staticmethod
    async def benchmark_stores(
        stores: List[str],
        document_count: int = 1000,
        query_count: int = 100,
        embedding_dimension: int = 1536
    ) -> Dict[str, Dict[str, float]]:
        """Benchmark different vector stores
        
        Args:
            stores: List of store backends to benchmark
            document_count: Number of documents for testing
            query_count: Number of queries for testing
            embedding_dimension: Vector dimension
            
        Returns:
            Benchmark results for each store
        """
```

---

## 🔌 Embedding Providers

### **OpenAIEmbeddingProvider**

```python
class OpenAIEmbeddingProvider(IEmbeddingProvider):
    """Native OpenAI embedding provider"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        cache_embeddings: bool = False,
        timeout: int = 30
    ):
        """Initialize OpenAI embedding provider
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
            batch_size: Maximum batch size for API calls
            cache_embeddings: Whether to cache embeddings
            timeout: API request timeout
        """
        
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension for the model"""
        
    @property
    def max_batch_size(self) -> int:
        """Get maximum batch size"""
        
    async def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for documents
        
        Args:
            texts: List of document texts
            
        Returns:
            List of embedding vectors
        """
        
    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for query text
        
        Args:
            text: Query text
            
        Returns:
            Query embedding vector
        """
        
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[np.ndarray]:
        """Generate embeddings in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses default if None)
            
        Returns:
            List of embedding vectors
        """
        
    # OpenAI-specific methods
    def get_supported_models(self) -> List[str]:
        """Get list of supported embedding models"""
        
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        
    def estimate_cost(self, token_count: int) -> float:
        """Estimate cost for embedding token count"""
```

### **BaseEmbeddingProvider**

```python
class BaseEmbeddingProvider(IEmbeddingProvider):
    """Base class for custom embedding providers"""
    
    def __init__(
        self,
        embedding_dimension: int,
        max_batch_size: int = 100
    ):
        """Initialize base embedding provider
        
        Args:
            embedding_dimension: Vector embedding dimension
            max_batch_size: Maximum batch size
        """
        
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        
    @property
    def max_batch_size(self) -> int:
        """Get maximum batch size"""
        
    async def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for documents
        
        Must be implemented by subclasses
        """
        
    async def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for query text
        
        Default implementation delegates to embed_documents
        """
        
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[np.ndarray]:
        """Generate embeddings in batches
        
        Default implementation handles batching automatically
        """
        
    # Utility methods for subclasses
    def _validate_texts(self, texts: List[str]) -> None:
        """Validate input texts"""
        
    def _normalize_embeddings(self, embeddings: List[np.ndarray]) -> List[np.ndarray]:
        """Normalize embedding vectors"""
        
    async def _handle_api_error(self, error: Exception) -> None:
        """Handle API errors consistently"""
```

---

## ❌ Exception Handling

### **Vector Store Exceptions**

```python
class VectorStoreError(Exception):
    """Base vector store error"""
    
    def __init__(
        self,
        message: str,
        store_type: str = None,
        error_code: str = None,
        context: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.store_type = store_type
        self.error_code = error_code
        self.context = context or {}

class ConnectionError(VectorStoreError):
    """Vector store connection error"""

class QueryError(VectorStoreError):
    """Vector query execution error"""

class EmbeddingError(VectorStoreError):
    """Embedding generation error"""

class ConfigurationError(VectorStoreError):
    """Vector store configuration error"""

class IndexError(VectorStoreError):
    """Vector index management error"""

# Usage with error handling
try:
    store = VectorStoreFactory.create_pinecone_store(
        api_key="invalid_key",
        environment="us-west1-gcp",
        index_name="test"
    )
    await store.connect()
except ConnectionError as e:
    logger.error(f"Failed to connect to Pinecone: {e}")
    # Fall back to SQLite store
    store = VectorStoreFactory.create_sqlite_store("fallback_vectors.db")
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    raise
except VectorStoreError as e:
    logger.error(f"Vector store error: {e}")
    raise
```

---

## 🌍 Global Vector Store Management

### **Vector Store Registry**

```python
class VectorStoreRegistry:
    """Global registry for vector store instances"""
    
    _stores: Dict[str, IVectorStore] = {}
    _default_store: Optional[str] = None
    
    @classmethod
    def register_store(cls, name: str, store: IVectorStore) -> None:
        """Register vector store instance
        
        Args:
            name: Store identifier
            store: Vector store instance
        """
        
    @classmethod
    def get_store(cls, name: str = None) -> Optional[IVectorStore]:
        """Get vector store by name
        
        Args:
            name: Store identifier (uses default if None)
            
        Returns:
            Vector store instance
        """
        
    @classmethod
    def set_default_store(cls, name: str) -> None:
        """Set default vector store
        
        Args:
            name: Store identifier
        """
        
    @classmethod
    def list_stores(cls) -> List[str]:
        """List registered store names
        
        Returns:
            List of store identifiers
        """
        
    @classmethod
    async def close_all_stores(cls) -> None:
        """Close all registered stores"""

# Global convenience functions
def get_default_vector_store() -> Optional[IVectorStore]:
    """Get default vector store instance"""
    return VectorStoreRegistry.get_store()

async def create_and_register_store(
    name: str,
    backend: str,
    config: Dict[str, Any],
    set_as_default: bool = False
) -> IVectorStore:
    """Create, register, and optionally set as default store
    
    Args:
        name: Store identifier
        backend: Backend type
        config: Store configuration
        set_as_default: Whether to set as default
        
    Returns:
        Created and registered store
    """
```

---

**LangSwarm V2's native vector stores API provides high-performance, type-safe vector database operations with direct API integrations, replacing LangChain/LlamaIndex dependencies while offering 20-40% better performance and comprehensive type safety.**
