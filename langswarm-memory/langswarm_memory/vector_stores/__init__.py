"""
LangSwarm V2 Native Vector Store Implementations

Native vector store implementations that replace LangChain/LlamaIndex dependencies
with direct API integrations for better performance and control.
"""

from .interfaces import IVectorStore, VectorStoreConfig, VectorDocument, VectorQuery, VectorResult, IEmbeddingProvider
from .pinecone_native import NativePineconeStore
from .qdrant_native import NativeQdrantStore
from .chroma_native import NativeChromaStore
from .sqlite_native import NativeSQLiteStore
from .factory import VectorStoreFactory, create_development_store, create_auto_store

__all__ = [
    # Interfaces
    'IVectorStore',
    'VectorStoreConfig', 
    'VectorDocument',
    'VectorQuery',
    'VectorResult',
    'IEmbeddingProvider',
    
    # Native implementations
    'NativePineconeStore',
    'NativeQdrantStore', 
    'NativeChromaStore',
    'NativeSQLiteStore',
    
    # Factory
    'VectorStoreFactory',
    'create_development_store',
    'create_auto_store'
]
