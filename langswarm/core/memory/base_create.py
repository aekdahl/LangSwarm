"""
Base memory backend creation with helpful dependency errors.
"""

from typing import Optional, Dict, Any
from langswarm.core.utils.optional_imports import optional_imports, OptionalImportError


def create_memory_backend(backend: str, **kwargs) -> Any:
    """
    Create a memory backend with the specified type.
    
    Provides helpful error messages if the backend's package is not installed.
    """
    backend = backend.lower()
    
    # Map backends to their implementations
    backend_map = {
        'sqlite': ([], 'SQLite (built-in)'),  # No dependencies needed
        'redis': (['redis', 'aioredis'], 'Redis memory backend'),
        'chromadb': (['chromadb'], 'ChromaDB vector store'),
        'qdrant': (['qdrant_client'], 'Qdrant vector database'),
        'pinecone': (['pinecone'], 'Pinecone vector database'),
        'bigquery': (['google.cloud.bigquery'], 'Google BigQuery'),
        'postgres': (['psycopg2', 'asyncpg'], 'PostgreSQL database'),
    }
    
    if backend not in backend_map:
        available = list(backend_map.keys())
        raise ValueError(
            f"Unknown memory backend: '{backend}'\n"
            f"Available backends: {', '.join(available)}"
        )
    
    packages, feature_desc = backend_map[backend]
    
    # SQLite doesn't need any dependencies
    if backend == 'sqlite':
        return "SQLite memory backend (built-in)"
    
    # Try to import required packages
    missing_packages = []
    for package_name in packages:
        if not optional_imports.is_available(package_name):
            missing_packages.append(package_name)
    
    if missing_packages:
        # Create helpful error message
        install_cmd = f"pip install {' '.join(missing_packages)}"
        
        error_msg = (
            f"❌ {feature_desc} requires missing dependencies: {missing_packages}\n\n"
            f"📦 To use {backend} backend, install:\n"
            f"   {install_cmd}\n\n"
            f"💡 Alternatives:\n"
            f"   • Use SQLite (no installation needed): backend='sqlite'\n"
            f"   • Install all backends: pip install langswarm[full]\n"
        )
        
        # Add backend-specific setup hints
        if backend == 'redis':
            error_msg += f"\n🔧 Also ensure Redis server is running:\n"
            error_msg += f"   • Docker: docker run -p 6379:6379 redis\n"
            error_msg += f"   • Local: redis-server"
        elif backend == 'postgres':
            error_msg += f"\n🔧 Also ensure PostgreSQL is running"
        elif backend == 'bigquery':
            error_msg += f"\n🔧 Also configure Google Cloud credentials"
            
        raise ImportError(error_msg)
    
    # Here we would create the actual backend
    # This is just a demo to show the error handling
    return f"Memory backend created with {backend}"