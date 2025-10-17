"""
Memory System Error Handling for LangSwarm

Provides clear, actionable error messages for memory-related issues
including embedding failures, vector search problems, and storage issues.
"""

from typing import List, Optional, Dict, Any, Union
from langswarm.core.errors import LangSwarmError, ErrorContext


class MemoryError(LangSwarmError):
    """Base class for all memory-related errors."""
    pass


class EmbeddingError(MemoryError):
    """Raised when text embedding operations fail."""
    
    def __init__(
        self,
        operation: str,
        provider: str,
        error: Optional[Exception] = None,
        text_preview: Optional[str] = None
    ):
        self.operation = operation
        self.provider = provider
        self.original_error = error
        self.text_preview = text_preview
        
        message = f"Embedding {operation} failed with {provider} provider"
        if text_preview:
            preview = text_preview[:50] + "..." if len(text_preview) > 50 else text_preview
            message += f" (text: '{preview}')"
        
        context = ErrorContext(
            component="EmbeddingProvider",
            operation=operation,
            metadata={
                "provider": provider,
                "error_type": type(error).__name__ if error else None,
                "has_text": text_preview is not None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for embedding errors."""
        suggestions = [f"Fix {self.provider} embedding issue:"]
        
        provider_suggestions = {
            "openai": [
                "• Verify OPENAI_API_KEY is set correctly",
                "• Check API quota and rate limits",
                "• Ensure model 'text-embedding-ada-002' is accessible",
                "• Monitor text length (max ~8000 tokens)"
            ],
            "huggingface": [
                "• Install transformers: pip install transformers",
                "• Check model download and cache",
                "• Verify model name is correct",
                "• Monitor GPU/CPU memory usage"
            ],
            "sentence_transformers": [
                "• Install sentence-transformers: pip install sentence-transformers",
                "• Check model compatibility",
                "• Verify CUDA availability if using GPU",
                "• Monitor model loading time"
            ],
            "cohere": [
                "• Verify COHERE_API_KEY is set",
                "• Check text length limits",
                "• Monitor API rate limits",
                "• Ensure model availability"
            ]
        }
        
        if self.provider in provider_suggestions:
            suggestions.extend([""])
            suggestions.extend(provider_suggestions[self.provider])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "api" in error_str or "key" in error_str:
                suggestions.extend([
                    "",
                    "API key issue detected:",
                    "• Check if API key is set as environment variable",
                    "• Verify key has correct permissions",
                    "• Test key with provider's CLI tools"
                ])
            elif "quota" in error_str or "limit" in error_str:
                suggestions.extend([
                    "",
                    "Rate/quota limit detected:",
                    "• Check your API usage dashboard",
                    "• Implement exponential backoff",
                    "• Consider upgrading your plan",
                    "• Batch smaller requests"
                ])
            elif "model" in error_str:
                suggestions.extend([
                    "",
                    "Model issue detected:",
                    "• Verify model name spelling",
                    "• Check if model is still available",
                    "• Try alternative embedding models",
                    "• Check model compatibility"
                ])
            elif "network" in error_str or "connection" in error_str:
                suggestions.extend([
                    "",
                    "Network issue detected:",
                    "• Check internet connectivity",
                    "• Verify proxy settings",
                    "• Try different DNS servers",
                    "• Check firewall settings"
                ])
        
        suggestions.extend([
            "",
            "For development, use local embeddings:",
            "```yaml",
            "memory:",
            "  embedding:",
            "    provider: sentence_transformers",
            "    model: all-MiniLM-L6-v2",
            "```"
        ])
        
        return "\n".join(suggestions)


class VectorSearchError(MemoryError):
    """Raised when vector search operations fail."""
    
    def __init__(
        self,
        operation: str,
        backend: str,
        query: Optional[str] = None,
        error: Optional[Exception] = None,
        collection: Optional[str] = None
    ):
        self.operation = operation
        self.backend = backend
        self.query = query
        self.original_error = error
        self.collection = collection
        
        message = f"Vector search {operation} failed with {backend} backend"
        if collection:
            message += f" (collection: {collection})"
        
        context = ErrorContext(
            component="VectorSearch",
            operation=operation,
            metadata={
                "backend": backend,
                "collection": collection,
                "has_query": query is not None,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for vector search errors."""
        suggestions = [f"Fix {self.backend} vector search issue:"]
        
        backend_suggestions = {
            "chromadb": [
                "• Verify ChromaDB installation and version",
                "• Check if collection exists and is accessible",
                "• Verify embedding dimensions match",
                "• Check ChromaDB server status if using client/server"
            ],
            "qdrant": [
                "• Verify Qdrant server connection",
                "• Check collection configuration and schema",
                "• Ensure vector dimensions are consistent",
                "• Monitor Qdrant server logs and resources"
            ],
            "redis": [
                "• Verify Redis server with search module",
                "• Check if index exists and is valid",
                "• Verify vector field configuration",
                "• Monitor Redis memory usage"
            ],
            "bigquery": [
                "• Check Google Cloud authentication",
                "• Verify BigQuery ML and vector search permissions",
                "• Ensure table schema supports vector search",
                "• Check query quotas and billing"
            ],
            "elasticsearch": [
                "• Verify Elasticsearch cluster health",
                "• Check index mapping for vector fields",
                "• Ensure sufficient cluster resources",
                "• Verify search plugin compatibility"
            ]
        }
        
        if self.backend in backend_suggestions:
            suggestions.extend([""])
            suggestions.extend(backend_suggestions[self.backend])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "connection" in error_str:
                suggestions.extend([
                    "",
                    "Connection issue detected:",
                    "• Check if vector database server is running",
                    "• Verify connection parameters (host, port, credentials)",
                    "• Test basic connectivity outside of LangSwarm",
                    "• Check network and firewall settings"
                ])
            elif "index" in error_str:
                suggestions.extend([
                    "",
                    "Index issue detected:",
                    "• Rebuild the vector index",
                    "• Check index configuration and mapping",
                    "• Verify sufficient storage space",
                    "• Monitor indexing performance"
                ])
            elif "dimension" in error_str:
                suggestions.extend([
                    "",
                    "Vector dimension mismatch detected:",
                    "• Check embedding model output dimensions",
                    "• Verify index was created with correct dimensions",
                    "• Ensure all vectors have same dimensionality",
                    "• Consider re-embedding with consistent model"
                ])
            elif "permission" in error_str or "auth" in error_str:
                suggestions.extend([
                    "",
                    "Permission/authentication issue detected:",
                    "• Check database credentials and permissions",
                    "• Verify API keys or tokens are valid",
                    "• Ensure user has read/write access to collections",
                    "• Check role-based access controls"
                ])
        
        if self.query:
            query_preview = self.query[:100] + "..." if len(self.query) > 100 else self.query
            suggestions.extend([
                "",
                f"Query: {query_preview}",
                "• Check query format and syntax",
                "• Verify query vector has correct dimensions",
                "• Test with simpler queries first"
            ])
        
        suggestions.extend([
            "",
            "For development, use simple in-memory search:",
            "```yaml",
            "memory:",
            "  backend: memory  # No external dependencies",
            "  search:",
            "    type: simple_similarity",
            "```"
        ])
        
        return "\n".join(suggestions)


class MemoryStorageError(MemoryError):
    """Raised when memory storage operations fail."""
    
    def __init__(
        self,
        operation: str,
        backend: str,
        error: Optional[Exception] = None,
        data_type: Optional[str] = None,
        size_info: Optional[str] = None
    ):
        self.operation = operation
        self.backend = backend
        self.original_error = error
        self.data_type = data_type
        self.size_info = size_info
        
        message = f"Memory storage {operation} failed with {backend} backend"
        if data_type:
            message += f" (data: {data_type})"
        
        context = ErrorContext(
            component="MemoryStorage",
            operation=operation,
            metadata={
                "backend": backend,
                "data_type": data_type,
                "size_info": size_info,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for storage errors."""
        suggestions = [f"Fix {self.backend} memory storage issue:"]
        
        storage_troubleshooting = {
            "sqlite": [
                "• Check file permissions and disk space",
                "• Verify SQLite database integrity",
                "• Consider using WAL mode for better concurrency",
                "• Monitor database file growth"
            ],
            "redis": [
                "• Check Redis server memory limits",
                "• Verify Redis persistence configuration",
                "• Monitor Redis memory usage and eviction",
                "• Check for Redis cluster issues if applicable"
            ],
            "bigquery": [
                "• Verify Google Cloud project quotas",
                "• Check BigQuery dataset permissions",
                "• Monitor BigQuery job execution",
                "• Consider partitioning for large datasets"
            ],
            "gcs": [
                "• Check Google Cloud Storage permissions",
                "• Verify bucket exists and is accessible",
                "• Monitor storage quotas and billing",
                "• Check object versioning settings"
            ]
        }
        
        if self.backend in storage_troubleshooting:
            suggestions.extend([""])
            suggestions.extend(storage_troubleshooting[self.backend])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "disk" in error_str or "space" in error_str:
                suggestions.extend([
                    "",
                    "Disk space issue detected:",
                    "• Free up disk space",
                    "• Move to larger storage volume",
                    "• Implement data cleanup policies",
                    "• Monitor storage usage trends"
                ])
            elif "memory" in error_str:
                suggestions.extend([
                    "",
                    "Memory issue detected:",
                    "• Increase available system memory",
                    "• Reduce batch sizes",
                    "• Implement data streaming",
                    "• Consider memory-efficient backends"
                ])
            elif "serialization" in error_str:
                suggestions.extend([
                    "",
                    "Data serialization issue detected:",
                    "• Check data format compatibility",
                    "• Verify data types are serializable",
                    "• Consider alternative serialization formats",
                    "• Remove circular references in data"
                ])
        
        if self.size_info:
            suggestions.extend([
                "",
                f"Data size: {self.size_info}",
                "• Consider data compression",
                "• Implement chunking for large data",
                "• Use streaming for processing"
            ])
        
        suggestions.extend([
            "",
            "For development, use lightweight storage:",
            "```yaml",
            "memory:",
            "  backend: memory    # In-memory only",
            "  max_size: 100MB    # Limit memory usage",
            "```"
        ])
        
        return "\n".join(suggestions)


class MemoryConfigurationError(MemoryError):
    """Raised when memory configuration is invalid."""
    
    def __init__(
        self,
        config_issue: str,
        component: str,
        config_data: Optional[Dict[str, Any]] = None
    ):
        self.config_issue = config_issue
        self.component = component
        self.config_data = config_data
        
        message = f"Invalid memory configuration for {component}: {config_issue}"
        
        context = ErrorContext(
            component="MemoryConfiguration",
            operation="validate_config",
            metadata={
                "component": component,
                "issue": config_issue,
                "has_config": config_data is not None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for configuration errors."""
        suggestions = [f"Fix memory configuration for {self.component}:"]
        
        component_configs = {
            "embedding": [
                "```yaml",
                "memory:",
                "  embedding:",
                "    provider: openai  # or sentence_transformers, huggingface",
                "    model: text-embedding-ada-002",
                "    batch_size: 100",
                "    timeout: 30",
                "```"
            ],
            "vector_search": [
                "```yaml",
                "memory:",
                "  vector_search:",
                "    backend: chromadb  # or qdrant, redis, bigquery",
                "    collection: my_collection",
                "    distance_metric: cosine",
                "    index_params:",
                "      ef_construction: 200",
                "```"
            ],
            "storage": [
                "```yaml",
                "memory:",
                "  storage:",
                "    backend: sqlite  # or redis, bigquery, gcs",
                "    connection:",
                "      database: memory.db",
                "      timeout: 30",
                "```"
            ]
        }
        
        if self.component in component_configs:
            suggestions.extend(["", f"Example {self.component} configuration:"])
            suggestions.extend(component_configs[self.component])
        
        # Common configuration issues
        if "backend" in self.config_issue.lower():
            suggestions.extend([
                "",
                "Valid backends by component:",
                "• Embedding: openai, sentence_transformers, huggingface, cohere",
                "• Vector Search: chromadb, qdrant, redis, bigquery, elasticsearch",
                "• Storage: memory, sqlite, redis, bigquery, gcs"
            ])
        
        if "connection" in self.config_issue.lower():
            suggestions.extend([
                "",
                "Connection configuration examples:",
                "• Redis: {host: localhost, port: 6379, password: '...'}",
                "• BigQuery: {project: my-project, dataset: my_dataset}",
                "• Qdrant: {host: localhost, port: 6333, api_key: '...'}"
            ])
        
        suggestions.extend([
            "",
            "For quick setup, use defaults:",
            "```yaml",
            "memory:",
            "  backend: sqlite  # Simple, works out of the box",
            "```"
        ])
        
        return "\n".join(suggestions)


# Convenience functions for creating common memory errors
def embedding_failed(
    operation: str, 
    provider: str, 
    error: Optional[Exception] = None
) -> EmbeddingError:
    """Create an EmbeddingError with context."""
    return EmbeddingError(operation, provider, error)


def search_failed(
    operation: str, 
    backend: str, 
    error: Optional[Exception] = None
) -> VectorSearchError:
    """Create a VectorSearchError with context."""
    return VectorSearchError(operation, backend, error=error)


def storage_failed(
    operation: str, 
    backend: str, 
    error: Optional[Exception] = None
) -> MemoryStorageError:
    """Create a MemoryStorageError with context."""
    return MemoryStorageError(operation, backend, error)


def config_invalid(
    issue: str, 
    component: str, 
    config: Optional[Dict[str, Any]] = None
) -> MemoryConfigurationError:
    """Create a MemoryConfigurationError with context."""
    return MemoryConfigurationError(issue, component, config)