"""
LangSwarm V2 Vector Store Interfaces

Clean, provider-agnostic interfaces for vector storage operations that replace
LangChain/LlamaIndex abstractions with LangSwarm-native implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class VectorDocument:
    """Document with vector embedding and metadata"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class VectorQuery:
    """Vector query with filters and options"""
    embedding: List[float]
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    include_content: bool = True
    min_score: Optional[float] = None


@dataclass
class VectorResult:
    """Vector search result"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    embedding: Optional[List[float]] = None


@dataclass
class VectorStoreConfig:
    """Vector store configuration"""
    store_type: str
    connection_params: Dict[str, Any]
    embedding_dimension: int
    index_params: Optional[Dict[str, Any]] = None
    
    # Common parameters
    namespace: Optional[str] = None
    metric: str = "cosine"  # cosine, euclidean, dotproduct
    
    def __post_init__(self):
        if self.index_params is None:
            self.index_params = {}


class IVectorStore(ABC):
    """
    Interface for vector storage operations.
    
    Provides a clean, unified interface for all vector storage backends
    without the complexity of LangChain/LlamaIndex abstractions.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the vector store"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the vector store"""
        pass
    
    @abstractmethod
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create a vector index"""
        pass
    
    @abstractmethod
    async def delete_index(self, name: str) -> bool:
        """Delete a vector index"""
        pass
    
    @abstractmethod
    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents"""
        pass
    
    @abstractmethod
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query vectors by similarity"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID"""
        pass
    
    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        pass
    
    @abstractmethod
    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if store is healthy"""
        pass


class IEmbeddingProvider(ABC):
    """Interface for embedding generation"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass


class VectorStoreError(Exception):
    """Base vector store error"""
    pass


class ConnectionError(VectorStoreError):
    """Vector store connection error"""
    pass


class IndexError(VectorStoreError):
    """Vector store index error"""
    pass


class QueryError(VectorStoreError):
    """Vector store query error"""
    pass
