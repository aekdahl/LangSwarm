"""
LangSwarm V2 Execution Interceptor

Handles the actual execution of handlers (tools, plugins, RAGs).
Replaces the legacy _execute_with_timeout method with modern async execution,
proper timeout handling, and comprehensive error management.
"""

import asyncio
import json
import logging
import time
from typing import Callable, Any, Dict, Optional

from langswarm.core.errors import handle_error, ToolError, ErrorContext

from ..interfaces import IRequestContext, IResponseContext, ResponseStatus
from ..context import ResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class ExecutionInterceptor(BaseInterceptor):
    """
    Interceptor that executes the handler found by the routing interceptor.
    
    Provides timeout handling, async execution, result processing,
    and comprehensive error management.
    """
    
    def __init__(
        self, 
        priority: int = 500,
        default_timeout: float = 30.0,
        enable_async: bool = True
    ):
        """
        Initialize execution interceptor.
        
        Args:
            priority: Priority for interceptor ordering
            default_timeout: Default timeout for handler execution
            enable_async: Whether to enable async execution
        """
        super().__init__(
            name="execution", 
            priority=priority, 
            timeout_seconds=default_timeout
        )
        self._default_timeout = default_timeout
        self._enable_async = enable_async
        
        # Execution statistics
        self._execution_count = 0
        self._timeout_count = 0
        self._success_count = 0
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Execute the handler and return the result.
        
        Args:
            context: The request context (should contain handler from routing)
            next_interceptor: Function to call next interceptor (not used in execution)
            
        Returns:
            Response context with execution results
        """
        # Get handler from context metadata (set by routing interceptor)
        handler = context.metadata.get('handler')
        handler_type = context.metadata.get('handler_type', 'unknown')
        
        if handler is None:
            logger.error(f"No handler found in context for {context.action_id}")
            return ResponseContext.error(
                context.request_id,
                ToolError(
                    f"No handler available for action: {context.action_id}",
                    context=ErrorContext("execution", "handler_lookup"),
                    suggestion="Ensure the routing interceptor runs before execution"
                ),
                ResponseStatus.INTERNAL_ERROR,
                execution_error="no_handler"
            )
        
        self._execution_count += 1
        
        logger.debug(f"Executing {handler_type} handler for {context.action_id}.{context.method}")
        
        try:
            # Execute the handler with timeout
            result = await self._execute_handler(handler, context)
            
            self._success_count += 1
            
            # Create successful response
            return ResponseContext.created(  # Use 201 to match legacy behavior
                context.request_id,
                result,
                handler_type=handler_type,
                handler_name=getattr(handler, '__name__', str(handler)),
                execution_interceptor="execution"
            )
            
        except asyncio.TimeoutError as e:
            self._timeout_count += 1
            logger.warning(f"Handler execution timeout for {context.action_id}: {self._default_timeout}s")
            
            return ResponseContext.error(
                context.request_id,
                ToolError(
                    f"Handler execution timeout after {self._default_timeout}s",
                    context=ErrorContext("execution", "timeout"),
                    suggestion="Check handler performance or increase timeout"
                ),
                ResponseStatus.TIMEOUT,
                execution_error="timeout",
                timeout_seconds=self._default_timeout
            )
            
        except Exception as e:
            logger.error(f"Handler execution error for {context.action_id}: {e}")
            
            # Use V2 error handling
            should_continue = handle_error(e, f"execution_{handler_type}")
            
            return ResponseContext.error(
                context.request_id,
                e,
                ResponseStatus.INTERNAL_ERROR,
                execution_error="handler_exception",
                handler_type=handler_type
            )
    
    async def _execute_handler(self, handler: Any, context: IRequestContext) -> Any:
        """
        Execute the handler with the given context.
        
        Args:
            handler: The handler to execute
            context: The request context
            
        Returns:
            Result from handler execution
        """
        method = context.method
        params = context.params
        
        logger.debug(f"Executing handler method: {method} with params: {params}")
        
        # Try different execution patterns based on handler type
        result = None
        
        try:
            # Pattern 1: Direct method call (handler.method_name())
            if hasattr(handler, method):
                handler_method = getattr(handler, method)
                if callable(handler_method):
                    if self._enable_async:
                        result = await asyncio.wait_for(
                            self._call_handler_method(handler_method, params),
                            timeout=self._default_timeout
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None, 
                                lambda: handler_method(**params) if params else handler_method()
                            ),
                            timeout=self._default_timeout
                        )
                    return self._process_result(result)
            
            # Pattern 2: Run method with method name (handler.run(method, params))
            if hasattr(handler, 'run'):
                run_method = getattr(handler, 'run')
                if callable(run_method):
                    if self._enable_async:
                        result = await asyncio.wait_for(
                            self._call_run_method(run_method, method, params),
                            timeout=self._default_timeout
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None, 
                                lambda: run_method(method, params)
                            ),
                            timeout=self._default_timeout
                        )
                    return self._process_result(result)
            
            # Pattern 3: Call handler directly (handler(method, params))
            if callable(handler):
                if self._enable_async:
                    result = await asyncio.wait_for(
                        self._call_handler_directly(handler, method, params),
                        timeout=self._default_timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: handler(method, params)
                        ),
                        timeout=self._default_timeout
                    )
                return self._process_result(result)
            
            # No suitable execution pattern found
            raise ToolError(
                f"Handler does not support method '{method}' or common execution patterns",
                context=ErrorContext("execution", "method_lookup"),
                suggestion=f"Ensure handler implements '{method}' method or 'run' method"
            )
            
        except asyncio.TimeoutError:
            raise  # Re-raise timeout errors
        except Exception as e:
            # Wrap in execution error with context
            raise ToolError(
                f"Handler execution failed: {str(e)}",
                context=ErrorContext("execution", "handler_call"),
                suggestion="Check handler implementation and parameters",
                cause=e
            )
    
    async def _call_handler_method(self, handler_method: Callable, params: Dict[str, Any]) -> Any:
        """
        Call handler method with parameters.
        
        Args:
            handler_method: The method to call
            params: Parameters to pass
            
        Returns:
            Result from method call
        """
        if asyncio.iscoroutinefunction(handler_method):
            if params:
                return await handler_method(**params)
            else:
                return await handler_method()
        else:
            # Sync method, run in executor
            if params:
                return await asyncio.get_event_loop().run_in_executor(
                    None, lambda: handler_method(**params)
                )
            else:
                return await asyncio.get_event_loop().run_in_executor(
                    None, handler_method
                )
    
    async def _call_run_method(self, run_method: Callable, method: str, params: Dict[str, Any]) -> Any:
        """
        Call handler's run method.
        
        Args:
            run_method: The run method to call
            method: Method name to pass
            params: Parameters to pass
            
        Returns:
            Result from run method
        """
        if asyncio.iscoroutinefunction(run_method):
            return await run_method(method, params)
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: run_method(method, params)
            )
    
    async def _call_handler_directly(self, handler: Callable, method: str, params: Dict[str, Any]) -> Any:
        """
        Call handler directly.
        
        Args:
            handler: The handler to call
            method: Method name to pass
            params: Parameters to pass
            
        Returns:
            Result from handler call
        """
        if asyncio.iscoroutinefunction(handler):
            return await handler(method, params)
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: handler(method, params)
            )
    
    def _process_result(self, result: Any) -> Any:
        """
        Process the result from handler execution.
        
        Args:
            result: Raw result from handler
            
        Returns:
            Processed result
        """
        if result is None:
            return None
        
        # If result is already JSON string, return as-is
        if isinstance(result, str):
            try:
                # Try to parse as JSON to validate
                json.loads(result)
                return result
            except json.JSONDecodeError:
                # Not valid JSON, return as string
                return result
        
        # If result is dict or list, convert to JSON
        if isinstance(result, (dict, list)):
            try:
                return json.dumps(result, indent=2)
            except (TypeError, ValueError):
                # Can't serialize, convert to string
                return str(result)
        
        # For other types, convert to string
        return str(result)
    
    def can_handle(self, context: IRequestContext) -> bool:
        """
        Check if this interceptor should handle the request.
        
        Execution interceptor should only run if a handler was found by routing.
        
        Args:
            context: The request context
            
        Returns:
            True if handler is available in context
        """
        return (self.enabled and 
                context.metadata.get('handler') is not None)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        base_stats = self.get_statistics()
        
        success_rate = self._success_count / self._execution_count if self._execution_count > 0 else 0.0
        timeout_rate = self._timeout_count / self._execution_count if self._execution_count > 0 else 0.0
        
        base_stats.update({
            'execution_count': self._execution_count,
            'success_count': self._success_count,
            'timeout_count': self._timeout_count,
            'success_rate': success_rate,
            'timeout_rate': timeout_rate,
            'default_timeout': self._default_timeout,
            'async_enabled': self._enable_async
        })
        
        return base_stats
    
    def reset_statistics(self) -> None:
        """Reset execution statistics"""
        super().reset_statistics()
        self._execution_count = 0
        self._timeout_count = 0
        self._success_count = 0
