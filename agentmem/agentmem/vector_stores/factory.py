"""
LangSwarm V2 Vector Store Factory

Factory for creating native vector store implementations that replace
LangChain/LlamaIndex dependencies with direct API integrations.
"""

import logging
from typing import Dict, Any, Optional, Type, List

from .interfaces import IVectorStore, VectorStoreConfig
from .pinecone_native import NativePineconeStore
from .qdrant_native import NativeQdrantStore
from .chroma_native import NativeChromaStore
from .sqlite_native import NativeSQLiteStore


logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised when vector store creation or operation fails"""
    def __init__(self, message: str, store_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.store_type = store_type
        self.details = details or {}


class VectorStoreFactory:
    """
    Factory for creating native vector store implementations.
    
    Replaces LangChain/LlamaIndex vector store factories with direct
    API integrations for better performance and control.
    """
    
    # Registry of available vector stores
    _stores: Dict[str, Type[IVectorStore]] = {
        "pinecone": NativePineconeStore,
        "qdrant": NativeQdrantStore,
        "chroma": NativeChromaStore,
        "chromadb": NativeChromaStore,
        "sqlite": NativeSQLiteStore,
        "local": NativeSQLiteStore
    }
    
    @classmethod
    def create_store(
        cls,
        store_type: str,
        embedding_dimension: int,
        connection_params: Dict[str, Any],
        **kwargs
    ) -> IVectorStore:
        """
        Create a vector store instance.
        
        Args:
            store_type: Type of vector store (pinecone, qdrant, chroma, sqlite)
            embedding_dimension: Dimension of embeddings
            connection_params: Store-specific connection parameters
            **kwargs: Additional configuration options
            
        Returns:
            Vector store instance
            
        Raises:
            ValueError: If store type is not supported
        """
        store_type_lower = store_type.lower()
        
        if store_type_lower not in cls._stores:
            available = ", ".join(cls._stores.keys())
            raise ValueError(f"Unsupported vector store type: {store_type}. Available: {available}")
        
        # Create configuration
        config = VectorStoreConfig(
            store_type=store_type_lower,
            connection_params=connection_params,
            embedding_dimension=embedding_dimension,
            **kwargs
        )
        
        # Create store instance
        store_class = cls._stores[store_type_lower]
        store = store_class(config)
        
        logger.info(f"Created {store_type} vector store with dimension {embedding_dimension}")
        return store
    
    @classmethod
    def create_pinecone_store(
        cls,
        api_key: str,
        environment: str,
        index_name: str,
        embedding_dimension: int,
        namespace: Optional[str] = None,
        metric: str = "cosine"
    ) -> NativePineconeStore:
        """
        Create Pinecone vector store with specific configuration.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Pinecone index name
            embedding_dimension: Dimension of embeddings
            namespace: Optional namespace
            metric: Distance metric (cosine, euclidean, dotproduct)
            
        Returns:
            Configured Pinecone store
        """
        connection_params = {
            "api_key": api_key,
            "environment": environment,
            "index_name": index_name
        }
        
        return cls.create_store(
            store_type="pinecone",
            embedding_dimension=embedding_dimension,
            connection_params=connection_params,
            namespace=namespace,
            metric=metric
        )
    
    @classmethod
    def create_qdrant_store(
        cls,
        url: str,
        collection_name: str,
        embedding_dimension: int,
        api_key: Optional[str] = None,
        prefer_grpc: bool = False,
        metric: str = "cosine"
    ) -> NativeQdrantStore:
        """
        Create Qdrant vector store with specific configuration.
        
        Args:
            url: Qdrant server URL
            collection_name: Qdrant collection name
            embedding_dimension: Dimension of embeddings
            api_key: Optional API key
            prefer_grpc: Whether to prefer gRPC connection
            metric: Distance metric (cosine, euclidean, dotproduct)
            
        Returns:
            Configured Qdrant store
        """
        connection_params = {
            "url": url,
            "collection_name": collection_name,
            "api_key": api_key,
            "prefer_grpc": prefer_grpc
        }
        
        return cls.create_store(
            store_type="qdrant",
            embedding_dimension=embedding_dimension,
            connection_params=connection_params,
            metric=metric
        )
    
    @classmethod
    def create_chroma_store(
        cls,
        collection_name: str,
        embedding_dimension: int,
        host: str = "localhost",
        port: int = 8000,
        persist_directory: Optional[str] = None,
        metric: str = "cosine"
    ) -> NativeChromaStore:
        """
        Create ChromaDB vector store with specific configuration.
        
        Args:
            collection_name: ChromaDB collection name
            embedding_dimension: Dimension of embeddings
            host: ChromaDB server host
            port: ChromaDB server port
            persist_directory: Optional directory for persistence
            metric: Distance metric (cosine, euclidean, dotproduct)
            
        Returns:
            Configured ChromaDB store
        """
        connection_params = {
            "collection_name": collection_name,
            "host": host,
            "port": port,
            "persist_directory": persist_directory
        }
        
        return cls.create_store(
            store_type="chroma",
            embedding_dimension=embedding_dimension,
            connection_params=connection_params,
            metric=metric
        )
    
    @classmethod
    def create_sqlite_store(
        cls,
        db_path: str,
        embedding_dimension: int,
        table_name: str = "vectors",
        metric: str = "cosine"
    ) -> NativeSQLiteStore:
        """
        Create SQLite vector store with specific configuration.
        
        Args:
            db_path: Path to SQLite database file
            embedding_dimension: Dimension of embeddings
            table_name: Name of the vectors table
            metric: Distance metric (cosine, euclidean, dotproduct)
            
        Returns:
            Configured SQLite store
        """
        connection_params = {
            "db_path": db_path,
            "table_name": table_name
        }
        
        return cls.create_store(
            store_type="sqlite",
            embedding_dimension=embedding_dimension,
            connection_params=connection_params,
            metric=metric
        )
    
    @classmethod
    def register_store(cls, store_type: str, store_class: Type[IVectorStore]):
        """
        Register a custom vector store implementation.
        
        Args:
            store_type: Name of the store type
            store_class: Store implementation class
        """
        cls._stores[store_type.lower()] = store_class
        logger.info(f"Registered custom vector store: {store_type}")
    
    @classmethod
    def list_available_stores(cls) -> List[str]:
        """Get list of available vector store types"""
        return list(cls._stores.keys())
    
    @classmethod
    def get_store_requirements(cls, store_type: str) -> Dict[str, Any]:
        """
        Get requirements for a specific store type.
        
        Args:
            store_type: Type of vector store
            
        Returns:
            Dictionary with requirements information
        """
        requirements = {
            "pinecone": {
                "pip_package": "pinecone-client",
                "required_params": ["api_key", "environment", "index_name"],
                "optional_params": ["namespace"],
                "description": "Pinecone vector database - cloud-hosted"
            },
            "qdrant": {
                "pip_package": "qdrant-client",
                "required_params": ["url", "collection_name"],
                "optional_params": ["api_key", "prefer_grpc"],
                "description": "Qdrant vector database - self-hosted or cloud"
            },
            "chroma": {
                "pip_package": "chromadb",
                "required_params": ["collection_name"],
                "optional_params": ["host", "port", "persist_directory"],
                "description": "ChromaDB vector database - local or server"
            },
            "sqlite": {
                "pip_package": "numpy",
                "required_params": ["db_path"],
                "optional_params": ["table_name"],
                "description": "SQLite-based vector storage - local file-based"
            }
        }
        
        return requirements.get(store_type.lower(), {})


# Convenience functions for common configurations
def create_development_store(embedding_dimension: int) -> NativeSQLiteStore:
    """Create SQLite store for development"""
    return VectorStoreFactory.create_sqlite_store(
        db_path="langswarm_dev_vectors.db",
        embedding_dimension=embedding_dimension
    )


def create_production_store(
    store_type: str,
    embedding_dimension: int,
    config: Dict[str, Any]
) -> IVectorStore:
    """Create production vector store"""
    return VectorStoreFactory.create_store(
        store_type=store_type,
        embedding_dimension=embedding_dimension,
        connection_params=config
    )


def create_auto_store(
    embedding_dimension: int,
    config: Optional[Dict[str, Any]] = None
) -> IVectorStore:
    """
    Create vector store with automatic selection based on available dependencies.
    
    Args:
        embedding_dimension: Dimension of embeddings
        config: Optional configuration
        
    Returns:
        Best available vector store
        
    Raises:
        VectorStoreError: If no suitable vector store can be created
    """
    config = config or {}
    
    # Try stores in order of preference
    store_preferences = [
        ("pinecone", lambda: config.get("pinecone", {}).get("api_key")),
        ("qdrant", lambda: config.get("qdrant", {}).get("url")),
        ("chroma", lambda: True),  # ChromaDB can work in-memory
        ("sqlite", lambda: True)   # SQLite always available
    ]
    
    attempted_stores = []
    errors = []
    
    for store_type, check_available in store_preferences:
        attempted_stores.append(store_type)
        
        if not check_available():
            errors.append(f"{store_type}: Configuration not available")
            continue
            
        try:
            store_config = config.get(store_type, {})
            
            if store_type == "pinecone":
                logger.info(f"Creating Pinecone vector store with dimension {embedding_dimension}")
                return VectorStoreFactory.create_pinecone_store(
                    api_key=store_config["api_key"],
                    environment=store_config.get("environment", "us-east-1-aws"),
                    index_name=store_config.get("index_name", "langswarm-default"),
                    embedding_dimension=embedding_dimension
                )
            elif store_type == "qdrant":
                logger.info(f"Creating Qdrant vector store with dimension {embedding_dimension}")
                return VectorStoreFactory.create_qdrant_store(
                    url=store_config.get("url", "http://localhost:6333"),
                    collection_name=store_config.get("collection_name", "langswarm_default"),
                    embedding_dimension=embedding_dimension
                )
            elif store_type == "chroma":
                logger.info(f"Creating ChromaDB vector store with dimension {embedding_dimension}")
                return VectorStoreFactory.create_chroma_store(
                    collection_name=store_config.get("collection_name", "langswarm_default"),
                    embedding_dimension=embedding_dimension,
                    persist_directory=store_config.get("persist_directory")
                )
            else:  # sqlite
                logger.info(f"Creating SQLite vector store with dimension {embedding_dimension}")
                return VectorStoreFactory.create_sqlite_store(
                    db_path=store_config.get("db_path", "langswarm_vectors.db"),
                    embedding_dimension=embedding_dimension
                )
                    
        except Exception as e:
            error_msg = f"{store_type}: {e}"
            errors.append(error_msg)
            logger.error(f"Failed to create {store_type} vector store: {e}")
    
    # If we get here, all stores failed
    raise VectorStoreError(
        f"Failed to create any vector store. Attempted: {attempted_stores}. "
        f"Errors: {'; '.join(errors)}. "
        f"Check your configuration and ensure at least one vector store service is available."
    )
