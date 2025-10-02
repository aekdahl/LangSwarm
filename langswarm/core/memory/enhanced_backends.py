"""
Enhanced Memory Backends with Optional Dependencies

Demonstrates how to handle optional memory backends gracefully with helpful error messages.
"""

from typing import Dict, List, Any, Optional, Type
import logging
from abc import ABC, abstractmethod

from langswarm.core.utils.optional_imports import optional_import, requires, OptionalImportError
from langswarm.core.errors import ConfigurationError, ErrorContext

logger = logging.getLogger(__name__)


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        """Store data with the given key."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by key."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar content."""
        pass


class SQLiteBackend(MemoryBackend):
    """SQLite memory backend - always available (no optional dependencies)."""
    
    def __init__(self, db_path: str = "langswarm_memory.db"):
        import sqlite3
        import aiosqlite
        
        self.db_path = db_path
        logger.info(f"Initialized SQLite memory backend: {db_path}")
    
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        # Implementation here
        pass
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation here
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Implementation here
        pass


@requires('redis', 'aioredis')
class RedisBackend(MemoryBackend):
    """Redis memory backend - requires redis and aioredis packages."""
    
    def __init__(self, url: str = "redis://localhost:6379"):
        redis = optional_import('redis', 'Redis memory backend')
        aioredis = optional_import('aioredis', 'Redis memory backend')
        
        self.url = url
        self.redis = None
        logger.info(f"Initialized Redis memory backend: {url}")
    
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        # Implementation using redis
        pass
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation using redis
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Implementation using redis search
        pass


@requires('chromadb')
class ChromaDBBackend(MemoryBackend):
    """ChromaDB vector store backend - requires chromadb package."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        chromadb = optional_import('chromadb', 'ChromaDB vector store')
        
        self.persist_directory = persist_directory
        self.client = None
        logger.info(f"Initialized ChromaDB backend: {persist_directory}")
    
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        # Implementation using chromadb
        pass
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation using chromadb
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Implementation using chromadb vector search
        pass


@requires('qdrant_client')
class QdrantBackend(MemoryBackend):
    """Qdrant vector store backend - requires qdrant-client package."""
    
    def __init__(self, url: str = "http://localhost:6333"):
        qdrant_client = optional_import('qdrant_client', 'Qdrant vector store')
        
        self.url = url
        self.client = None
        logger.info(f"Initialized Qdrant backend: {url}")
    
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        # Implementation using qdrant
        pass
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation using qdrant
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Implementation using qdrant vector search
        pass


@requires('google.cloud.bigquery')
class BigQueryBackend(MemoryBackend):
    """BigQuery memory backend - requires Google Cloud BigQuery."""
    
    def __init__(self, project_id: str, dataset_id: str = "langswarm_memory"):
        bigquery = optional_import('google.cloud.bigquery', 'BigQuery memory backend')
        
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = None
        logger.info(f"Initialized BigQuery backend: {project_id}.{dataset_id}")
    
    async def store(self, key: str, data: Dict[str, Any]) -> None:
        # Implementation using BigQuery
        pass
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation using BigQuery
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Implementation using BigQuery vector search
        pass


class MemoryBackendRegistry:
    """Registry for memory backends with dependency checking."""
    
    def __init__(self):
        self._backends: Dict[str, Type[MemoryBackend]] = {
            'sqlite': SQLiteBackend,  # Always available
        }
        
        # Register optional backends
        self._optional_backends = {
            'redis': (RedisBackend, ['redis', 'aioredis']),
            'chromadb': (ChromaDBBackend, ['chromadb']),
            'qdrant': (QdrantBackend, ['qdrant_client']),
            'bigquery': (BigQueryBackend, ['google.cloud.bigquery']),
        }
        
        self._register_optional_backends()
    
    def _register_optional_backends(self):
        """Register backends that have their dependencies available."""
        for backend_name, (backend_class, requirements) in self._optional_backends.items():
            if all(optional_import(req) for req in requirements):
                self._backends[backend_name] = backend_class
                logger.debug(f"Registered memory backend: {backend_name}")
            else:
                missing = [req for req in requirements if not optional_import(req)]
                logger.debug(f"Memory backend {backend_name} not available (missing: {missing})")
    
    def get_backend(self, backend_name: str) -> Type[MemoryBackend]:
        """
        Get a memory backend class by name.
        
        Args:
            backend_name: Name of the backend (e.g., 'redis', 'chromadb')
            
        Returns:
            Backend class
            
        Raises:
            ConfigurationError: If backend is not available
        """
        if backend_name in self._backends:
            return self._backends[backend_name]
        
        # Check if it's a known backend with missing dependencies
        if backend_name in self._optional_backends:
            backend_class, requirements = self._optional_backends[backend_name]
            missing_deps = [req for req in requirements if not optional_import(req)]
            
            # Create helpful error message
            install_suggestions = {
                'redis': "pip install langswarm[redis]",
                'chromadb': "pip install langswarm[chromadb]", 
                'qdrant': "pip install langswarm[qdrant]",
                'bigquery': "pip install langswarm[bigquery]"
            }
            
            install_cmd = install_suggestions.get(backend_name, f"pip install {' '.join(missing_deps)}")
            
            raise ConfigurationError(
                f"Memory backend '{backend_name}' requires missing dependencies: {missing_deps}",
                context=ErrorContext(
                    component="MemoryBackendRegistry",
                    operation="get_backend",
                    metadata={
                        "backend": backend_name,
                        "missing_dependencies": missing_deps
                    }
                ),
                suggestion=(
                    f"Install the required dependencies:\n{install_cmd}\n\n"
                    f"Or use the default SQLite backend which requires no additional dependencies:\n"
                    f"memory:\n  backend: sqlite"
                )
            )
        
        # Unknown backend
        available_backends = list(self._backends.keys())
        raise ConfigurationError(
            f"Unknown memory backend: '{backend_name}'",
            context=ErrorContext(
                component="MemoryBackendRegistry",
                operation="get_backend",
                metadata={
                    "backend": backend_name,
                    "available_backends": available_backends
                }
            ),
            suggestion=(
                f"Available backends: {', '.join(available_backends)}\n\n"
                f"For more backends, install additional dependencies:\n"
                f"pip install langswarm[memory]"
            )
        )
    
    def list_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        return list(self._backends.keys())
    
    def get_backend_status_summary(self) -> str:
        """Get a formatted summary of backend availability."""
        available = list(self._backends.keys())
        unavailable = []
        
        for backend_name, (_, requirements) in self._optional_backends.items():
            if backend_name not in available:
                missing = [req for req in requirements if not optional_import(req)]
                unavailable.append((backend_name, missing))
        
        summary = f"💾 Memory Backend Status:\n\n"
        summary += f"✅ Available ({len(available)}): {', '.join(available)}\n"
        
        if unavailable:
            summary += f"❌ Unavailable ({len(unavailable)}):\n"
            for backend_name, missing in unavailable:
                summary += f"   • {backend_name}: missing {', '.join(missing)}\n"
            
            summary += f"\nInstall all backends: pip install langswarm[memory]"
        
        return summary


# Global backend registry
memory_backend_registry = MemoryBackendRegistry()


def get_memory_backend(backend_name: str) -> Type[MemoryBackend]:
    """Convenience function to get a memory backend."""
    return memory_backend_registry.get_backend(backend_name)


def list_available_backends() -> List[str]:
    """Convenience function to list available backends."""
    return memory_backend_registry.list_available_backends()


def get_memory_status() -> str:
    """Convenience function to get memory backend status."""
    return memory_backend_registry.get_backend_status_summary()