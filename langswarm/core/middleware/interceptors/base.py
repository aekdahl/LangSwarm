"""
LangSwarm V2 Base Interceptor

Base class for all middleware interceptors providing common functionality,
error handling, and integration with the V2 systems.
"""

import time
import logging
from abc import abstractmethod
from typing import Callable, Dict, Any, Optional

from langswarm.core.errors import handle_error, MiddlewareError, ErrorContext

from ..interfaces import (
    IMiddlewareInterceptor, 
    IRequestContext, 
    IResponseContext,
    RequestType,
    ResponseStatus
)
from ..context import ResponseContext

logger = logging.getLogger(__name__)


class BaseInterceptor(IMiddlewareInterceptor):
    """
    Base class for all middleware interceptors.
    
    Provides common functionality including timing, error handling,
    and integration with the V2 error system.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True,
        timeout_seconds: float = 30.0
    ):
        """
        Initialize base interceptor.
        
        Args:
            name: Name of the interceptor (defaults to class name)
            priority: Priority for ordering (lower numbers execute first)
            enabled: Whether the interceptor is enabled
            timeout_seconds: Timeout for interceptor execution
        """
        self._name = name or self.__class__.__name__
        self._priority = priority
        self._enabled = enabled
        self._timeout_seconds = timeout_seconds
        
        # Statistics
        self._request_count = 0
        self._error_count = 0
        self._total_time = 0.0
    
    @property
    def name(self) -> str:
        """Name of this interceptor"""
        return self._name
    
    @property
    def priority(self) -> int:
        """Priority for ordering interceptors (lower numbers execute first)"""
        return self._priority
    
    @property
    def enabled(self) -> bool:
        """Whether this interceptor is enabled"""
        return self._enabled
    
    @property
    def timeout_seconds(self) -> float:
        """Timeout for interceptor execution"""
        return self._timeout_seconds
    
    def enable(self) -> None:
        """Enable this interceptor"""
        self._enabled = True
        logger.debug(f"Interceptor {self.name} enabled")
    
    def disable(self) -> None:
        """Disable this interceptor"""
        self._enabled = False
        logger.debug(f"Interceptor {self.name} disabled")
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Process the request and optionally call the next interceptor.
        
        This method provides timing, error handling, and statistics collection
        around the actual interceptor logic.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor in the chain
            
        Returns:
            Response context with results
        """
        if not self._enabled:
            logger.debug(f"Interceptor {self.name} is disabled, skipping")
            return await next_interceptor(context)
        
        start_time = time.time()
        self._request_count += 1
        
        try:
            logger.debug(f"Interceptor {self.name} processing request {context.request_id}")
            
            # Call the actual interceptor logic
            response = await self._process(context, next_interceptor)
            
            # Update timing statistics
            processing_time = time.time() - start_time
            self._total_time += processing_time
            
            # Add interceptor metadata to response
            response = response.with_metadata(
                **{f"{self.name}_processing_time": processing_time}
            )
            
            logger.debug(
                f"Interceptor {self.name} completed request {context.request_id} "
                f"in {processing_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._error_count += 1
            
            logger.error(f"Interceptor {self.name} error: {e}")
            
            # Use V2 error handling
            should_continue = handle_error(e, f"middleware_{self.name}")
            
            # Return error response
            error_response = self.on_error(context, e)
            return error_response.with_metadata(
                **{f"{self.name}_processing_time": processing_time,
                   f"{self.name}_error": True}
            )
    
    @abstractmethod
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Actual interceptor logic to be implemented by subclasses.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor in the chain
            
        Returns:
            Response context with results
        """
        pass
    
    def can_handle(self, context: IRequestContext) -> bool:
        """
        Base implementation checks if interceptor is enabled.
        Subclasses can override for more specific logic.
        
        Args:
            context: The request context
            
        Returns:
            True if this interceptor should process the request
        """
        return self._enabled
    
    def on_error(self, context: IRequestContext, error: Exception) -> IResponseContext:
        """
        Handle errors that occur during processing.
        
        Creates a structured error response using the V2 error system.
        
        Args:
            context: The request context
            error: The error that occurred
            
        Returns:
            Error response context
        """
        # Determine appropriate status code based on error type
        if isinstance(error, TimeoutError):
            status = ResponseStatus.TIMEOUT
        elif isinstance(error, PermissionError):
            status = ResponseStatus.FORBIDDEN
        elif isinstance(error, ValueError):
            status = ResponseStatus.BAD_REQUEST
        else:
            status = ResponseStatus.INTERNAL_ERROR
        
        # Create middleware error with context
        middleware_error = MiddlewareError(
            f"Error in {self.name}: {str(error)}",
            context=ErrorContext(
                component=f"middleware_{self.name}",
                operation="intercept",
                metadata={
                    "request_id": context.request_id,
                    "action_id": context.action_id,
                    "method": context.method
                }
            ),
            suggestion=f"Check {self.name} configuration and request parameters",
            cause=error
        )
        
        return ResponseContext.error(
            context.request_id,
            middleware_error,
            status,
            interceptor=self.name,
            error_type=type(error).__name__
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get interceptor statistics.
        
        Returns:
            Dictionary with interceptor statistics
        """
        avg_time = self._total_time / self._request_count if self._request_count > 0 else 0.0
        error_rate = self._error_count / self._request_count if self._request_count > 0 else 0.0
        
        return {
            'name': self.name,
            'priority': self.priority,
            'enabled': self.enabled,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'total_time': self._total_time,
            'average_time': avg_time,
            'error_rate': error_rate
        }
    
    def reset_statistics(self) -> None:
        """Reset interceptor statistics"""
        self._request_count = 0
        self._error_count = 0
        self._total_time = 0.0
        logger.debug(f"Statistics reset for interceptor {self.name}")
    
    def __str__(self) -> str:
        """String representation of the interceptor"""
        return f"{self.name}(priority={self.priority}, enabled={self.enabled})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the interceptor"""
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"priority={self.priority}, "
                f"enabled={self.enabled}, "
                f"requests={self._request_count}, "
                f"errors={self._error_count})")


class PassthroughInterceptor(BaseInterceptor):
    """
    Simple passthrough interceptor that just calls the next interceptor.
    Useful for testing and as a base for simple interceptors.
    """
    
    def __init__(self, name: str = "passthrough", priority: int = 999):
        """
        Initialize passthrough interceptor.
        
        Args:
            name: Name of the interceptor
            priority: Priority (defaults to 999 to run last)
        """
        super().__init__(name=name, priority=priority)
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Just call the next interceptor.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor
            
        Returns:
            Response from next interceptor
        """
        return await next_interceptor(context)


class TerminatingInterceptor(BaseInterceptor):
    """
    Interceptor that terminates the chain and returns a response.
    Useful for testing and implementing endpoints.
    """
    
    def __init__(
        self, 
        response: Any = None, 
        name: str = "terminating", 
        priority: int = 1000
    ):
        """
        Initialize terminating interceptor.
        
        Args:
            response: Response to return
            name: Name of the interceptor
            priority: Priority (defaults to 1000 to run last)
        """
        super().__init__(name=name, priority=priority)
        self._response = response
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Return the configured response without calling next interceptor.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor (ignored)
            
        Returns:
            Configured response
        """
        return ResponseContext.success(
            context.request_id,
            self._response,
            terminating_interceptor=self.name
        )
