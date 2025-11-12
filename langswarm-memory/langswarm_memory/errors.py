"""
Error handling for AgentMem

Provides clear, actionable error messages for memory-related issues.
"""

from typing import Optional, Dict, Any


class AgentMemError(Exception):
    """Base error for agentmem operations"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, suggestion: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion
    
    def __str__(self):
        result = self.message
        if self.details:
            result += f"\nDetails: {self.details}"
        if self.suggestion:
            result += f"\n\nSuggestion:\n{self.suggestion}"
        return result


class MemoryBackendError(AgentMemError):
    """Raised when backend operations fail"""
    
    def __init__(self, backend: str, operation: str, error: Optional[Exception] = None, suggestion: Optional[str] = None):
        self.backend = backend
        self.operation = operation
        self.original_error = error
        
        message = f"Backend '{backend}' failed during '{operation}'"
        if error:
            message += f": {str(error)}"
        
        details = {
            "backend": backend,
            "operation": operation,
            "error_type": type(error).__name__ if error else None
        }
        
        super().__init__(message, details=details, suggestion=suggestion)


class MemoryConfigurationError(AgentMemError):
    """Raised when configuration is invalid"""
    
    def __init__(self, issue: str, component: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None):
        self.issue = issue
        self.component = component
        self.config_data = config_data
        
        message = f"Invalid configuration: {issue}"
        if component:
            message = f"Invalid configuration for {component}: {issue}"
        
        details = {
            "issue": issue,
            "component": component,
            "has_config": config_data is not None
        }
        
        super().__init__(message, details=details)


class EmbeddingError(AgentMemError):
    """Raised when embedding operations fail"""
    
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
        if error:
            message += f": {str(error)}"
        
        details = {
            "operation": operation,
            "provider": provider,
            "error_type": type(error).__name__ if error else None,
            "has_text": text_preview is not None
        }
        
        suggestion = self._build_suggestion()
        super().__init__(message, details=details, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for embedding errors."""
        suggestions = [f"Fix {self.provider} embedding issue:"]
        
        provider_suggestions = {
            "openai": [
                "• Verify OPENAI_API_KEY is set correctly",
                "• Check API quota and rate limits",
                "• Ensure model 'text-embedding-ada-002' is accessible"
            ],
            "sentence_transformers": [
                "• Install sentence-transformers: pip install sentence-transformers",
                "• Check model compatibility",
                "• Verify model loading"
            ]
        }
        
        if self.provider in provider_suggestions:
            suggestions.extend([""])
            suggestions.extend(provider_suggestions[self.provider])
        
        return "\n".join(suggestions)


class VectorSearchError(AgentMemError):
    """Raised when vector search operations fail"""
    
    def __init__(
        self,
        operation: str,
        backend: str,
        query: Optional[str] = None,
        error: Optional[Exception] = None
    ):
        self.operation = operation
        self.backend = backend
        self.query = query
        self.original_error = error
        
        message = f"Vector search {operation} failed with {backend} backend"
        if error:
            message += f": {str(error)}"
        
        details = {
            "operation": operation,
            "backend": backend,
            "has_query": query is not None,
            "error_type": type(error).__name__ if error else None
        }
        
        super().__init__(message, details=details)


class MemoryStorageError(AgentMemError):
    """Raised when memory storage operations fail"""
    
    def __init__(
        self,
        operation: str,
        backend: str,
        error: Optional[Exception] = None,
        data_type: Optional[str] = None
    ):
        self.operation = operation
        self.backend = backend
        self.original_error = error
        self.data_type = data_type
        
        message = f"Memory storage {operation} failed with {backend} backend"
        if data_type:
            message += f" (data: {data_type})"
        if error:
            message += f": {str(error)}"
        
        details = {
            "operation": operation,
            "backend": backend,
            "data_type": data_type,
            "error_type": type(error).__name__ if error else None
        }
        
        super().__init__(message, details=details)



