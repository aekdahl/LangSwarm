"""
LangSwarm V2 Middleware Interfaces

Defines the core interfaces for the middleware pipeline system.
These interfaces ensure type safety and clear contracts between components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from enum import Enum


class RequestType(Enum):
    """Types of requests that can be processed by the middleware"""
    TOOL_CALL = "tool_call"
    PLUGIN_CALL = "plugin_call"
    RAG_QUERY = "rag_query"
    WORKFLOW_STEP = "workflow_step"
    AGENT_RESPONSE = "agent_response"


class ResponseStatus(Enum):
    """Standard response status codes for middleware operations"""
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TIMEOUT = 408
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503


class IRequestContext(ABC):
    """
    Interface for request context objects that flow through the pipeline.
    Immutable objects containing all information needed for request processing.
    """
    
    @property
    @abstractmethod
    def request_id(self) -> str:
        """Unique identifier for this request"""
        pass
    
    @property
    @abstractmethod
    def request_type(self) -> RequestType:
        """Type of request being processed"""
        pass
    
    @property
    @abstractmethod
    def action_id(self) -> str:
        """ID of the action/tool/plugin being requested"""
        pass
    
    @property
    @abstractmethod
    def method(self) -> str:
        """Method being called on the action"""
        pass
    
    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """Parameters for the action call"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata for the request"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """When the request was created"""
        pass
    
    @property
    @abstractmethod
    def user_id(self) -> Optional[str]:
        """User ID if available"""
        pass
    
    @property
    @abstractmethod
    def session_id(self) -> Optional[str]:
        """Session ID if available"""
        pass
    
    @abstractmethod
    def with_metadata(self, **metadata) -> 'IRequestContext':
        """Create new context with additional metadata"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        pass


class IResponseContext(ABC):
    """
    Interface for response context objects returned from the pipeline.
    Contains the results of request processing along with metadata.
    """
    
    @property
    @abstractmethod
    def request_id(self) -> str:
        """ID of the original request"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> ResponseStatus:
        """Status of the response"""
        pass
    
    @property
    @abstractmethod
    def result(self) -> Any:
        """Result data from processing"""
        pass
    
    @property
    @abstractmethod
    def error(self) -> Optional[Exception]:
        """Error if processing failed"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Response metadata including timing, handler info, etc."""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """When the response was created"""
        pass
    
    @property
    @abstractmethod
    def processing_time(self) -> float:
        """Time taken to process the request (in seconds)"""
        pass
    
    @abstractmethod
    def is_success(self) -> bool:
        """Check if the response indicates success"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization"""
        pass


class IMiddlewareInterceptor(ABC):
    """
    Interface for middleware interceptors that process requests in the pipeline.
    Each interceptor should have a single responsibility.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this interceptor"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority for ordering interceptors (lower numbers execute first)"""
        pass
    
    @abstractmethod
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Process the request and optionally call the next interceptor.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor in the chain
            
        Returns:
            Response context with results
        """
        pass
    
    @abstractmethod
    def can_handle(self, context: IRequestContext) -> bool:
        """
        Check if this interceptor can handle the given request type.
        
        Args:
            context: The request context
            
        Returns:
            True if this interceptor should process the request
        """
        pass
    
    def on_error(self, context: IRequestContext, error: Exception) -> IResponseContext:
        """
        Handle errors that occur during processing.
        Default implementation creates error response.
        
        Args:
            context: The request context
            error: The error that occurred
            
        Returns:
            Error response context
        """
        from .context import ResponseContext
        return ResponseContext(
            request_id=context.request_id,
            status=ResponseStatus.INTERNAL_ERROR,
            result=None,
            error=error,
            metadata={"interceptor": self.name, "error_type": type(error).__name__}
        )


class IMiddlewarePipeline(ABC):
    """
    Interface for the middleware pipeline that orchestrates interceptor execution.
    """
    
    @abstractmethod
    def add_interceptor(self, interceptor: IMiddlewareInterceptor) -> 'IMiddlewarePipeline':
        """
        Add an interceptor to the pipeline.
        
        Args:
            interceptor: The interceptor to add
            
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def remove_interceptor(self, name: str) -> 'IMiddlewarePipeline':
        """
        Remove an interceptor from the pipeline by name.
        
        Args:
            name: Name of the interceptor to remove
            
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    async def process(self, context: IRequestContext) -> IResponseContext:
        """
        Process a request through the middleware pipeline.
        
        Args:
            context: The request context
            
        Returns:
            Response context with results
        """
        pass
    
    @abstractmethod
    def get_interceptors(self) -> List[IMiddlewareInterceptor]:
        """
        Get all interceptors in the pipeline in execution order.
        
        Returns:
            List of interceptors ordered by priority
        """
        pass
    
    @property
    @abstractmethod
    def interceptor_count(self) -> int:
        """Number of interceptors in the pipeline"""
        pass


class IMiddlewareRegistry(ABC):
    """
    Interface for registries that provide handlers for different action types.
    This abstracts the various registries (tools, plugins, RAGs) behind a common interface.
    """
    
    @abstractmethod
    def get_handler(self, action_id: str) -> Optional[Any]:
        """
        Get a handler for the given action ID.
        
        Args:
            action_id: ID of the action to get handler for
            
        Returns:
            Handler object or None if not found
        """
        pass
    
    @abstractmethod
    def has_handler(self, action_id: str) -> bool:
        """
        Check if a handler exists for the given action ID.
        
        Args:
            action_id: ID of the action to check
            
        Returns:
            True if handler exists
        """
        pass
    
    @abstractmethod
    def list_handlers(self) -> List[str]:
        """
        List all available handler IDs.
        
        Returns:
            List of handler IDs
        """
        pass
    
    @property
    @abstractmethod
    def registry_type(self) -> str:
        """Type of registry (tool, plugin, rag, etc.)"""
        pass


class IMiddlewareConfiguration(ABC):
    """
    Interface for middleware configuration that controls pipeline behavior.
    """
    
    @property
    @abstractmethod
    def timeout_seconds(self) -> float:
        """Timeout for middleware operations in seconds"""
        pass
    
    @property
    @abstractmethod
    def max_retries(self) -> int:
        """Maximum number of retries for failed operations"""
        pass
    
    @property
    @abstractmethod
    def enable_tracing(self) -> bool:
        """Whether to enable distributed tracing"""
        pass
    
    @property
    @abstractmethod
    def enable_metrics(self) -> bool:
        """Whether to enable metrics collection"""
        pass
    
    @property
    @abstractmethod
    def error_handling_strategy(self) -> str:
        """Strategy for handling errors (fail_fast, continue, retry)"""
        pass
