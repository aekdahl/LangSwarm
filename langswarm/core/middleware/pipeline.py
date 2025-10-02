"""
LangSwarm V2 Middleware Pipeline

Modern pipeline implementation with composable interceptors.
Provides async execution, error handling, and comprehensive observability.
"""

import asyncio
import time
from typing import List, Dict, Optional, Callable, Any
import logging

from langswarm.core.errors import handle_error, ErrorContext, MiddlewareError

from .interfaces import (
    IMiddlewarePipeline, 
    IMiddlewareInterceptor, 
    IRequestContext, 
    IResponseContext,
    ResponseStatus
)
from .context import ResponseContext

logger = logging.getLogger(__name__)


class Pipeline(IMiddlewarePipeline):
    """
    Modern middleware pipeline with composable interceptors.
    
    Executes interceptors in priority order, providing async support,
    error handling, and comprehensive observability.
    """
    
    def __init__(self, interceptors: Optional[List[IMiddlewareInterceptor]] = None):
        """
        Initialize pipeline with optional interceptors.
        
        Args:
            interceptors: List of interceptors to add to pipeline
        """
        self._interceptors: List[IMiddlewareInterceptor] = []
        self._interceptor_map: Dict[str, IMiddlewareInterceptor] = {}
        
        if interceptors:
            for interceptor in interceptors:
                self.add_interceptor(interceptor)
    
    def add_interceptor(self, interceptor: IMiddlewareInterceptor) -> 'Pipeline':
        """
        Add an interceptor to the pipeline.
        
        Args:
            interceptor: The interceptor to add
            
        Returns:
            Self for method chaining
        """
        if interceptor.name in self._interceptor_map:
            logger.warning(f"Replacing existing interceptor: {interceptor.name}")
            self.remove_interceptor(interceptor.name)
        
        self._interceptors.append(interceptor)
        self._interceptor_map[interceptor.name] = interceptor
        
        # Sort by priority (lower numbers execute first)
        self._interceptors.sort(key=lambda i: i.priority)
        
        logger.debug(f"Added interceptor: {interceptor.name} (priority: {interceptor.priority})")
        return self
    
    def remove_interceptor(self, name: str) -> 'Pipeline':
        """
        Remove an interceptor from the pipeline by name.
        
        Args:
            name: Name of the interceptor to remove
            
        Returns:
            Self for method chaining
        """
        if name in self._interceptor_map:
            interceptor = self._interceptor_map[name]
            self._interceptors.remove(interceptor)
            del self._interceptor_map[name]
            logger.debug(f"Removed interceptor: {name}")
        else:
            logger.warning(f"Interceptor not found for removal: {name}")
        
        return self
    
    async def process(self, context: IRequestContext) -> IResponseContext:
        """
        Process a request through the middleware pipeline.
        
        Args:
            context: The request context
            
        Returns:
            Response context with results
        """
        start_time = time.time()
        
        try:
            # Filter interceptors that can handle this request
            applicable_interceptors = [
                interceptor for interceptor in self._interceptors
                if interceptor.can_handle(context)
            ]
            
            if not applicable_interceptors:
                logger.warning(f"No interceptors can handle request: {context.action_id}")
                return ResponseContext.not_found(
                    context.request_id,
                    context.action_id,
                    processing_time=time.time() - start_time,
                    pipeline_interceptors=0
                )
            
            # Create the interceptor chain
            chain = self._create_interceptor_chain(applicable_interceptors, context)
            
            # Execute the chain
            response = await chain(context)
            
            # Update processing time
            processing_time = time.time() - start_time
            response = response.with_metadata(
                pipeline_processing_time=processing_time,
                pipeline_interceptors=len(applicable_interceptors),
                interceptor_chain=[i.name for i in applicable_interceptors]
            )
            
            logger.debug(
                f"Pipeline processed request {context.request_id} in {processing_time:.3f}s "
                f"through {len(applicable_interceptors)} interceptors"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Use V2 error handling
            should_continue = handle_error(e, "middleware_pipeline")
            
            logger.error(f"Pipeline error for request {context.request_id}: {e}")
            
            return ResponseContext.error(
                context.request_id,
                e,
                ResponseStatus.INTERNAL_ERROR,
                processing_time=processing_time,
                pipeline_error=True,
                error_location="pipeline"
            )
    
    def _create_interceptor_chain(
        self, 
        interceptors: List[IMiddlewareInterceptor], 
        context: IRequestContext
    ) -> Callable:
        """
        Create the interceptor execution chain.
        
        Args:
            interceptors: List of interceptors to chain
            context: Request context
            
        Returns:
            Async callable that executes the chain
        """
        if not interceptors:
            # No interceptors, return empty success response
            async def empty_chain(ctx):
                return ResponseContext.success(
                    ctx.request_id,
                    None,
                    no_interceptors=True
                )
            return empty_chain
        
        # Build chain from end to beginning
        def build_chain(index: int) -> Callable:
            if index >= len(interceptors):
                # End of chain, return success
                async def end_chain(ctx):
                    return ResponseContext.success(
                        ctx.request_id,
                        None,
                        end_of_chain=True
                    )
                return end_chain
            
            interceptor = interceptors[index]
            next_chain = build_chain(index + 1)
            
            async def interceptor_chain(ctx):
                try:
                    return await interceptor.intercept(ctx, next_chain)
                except Exception as e:
                    logger.error(f"Error in interceptor {interceptor.name}: {e}")
                    return interceptor.on_error(ctx, e)
            
            return interceptor_chain
        
        return build_chain(0)
    
    def get_interceptors(self) -> List[IMiddlewareInterceptor]:
        """
        Get all interceptors in the pipeline in execution order.
        
        Returns:
            List of interceptors ordered by priority
        """
        return list(self._interceptors)
    
    @property
    def interceptor_count(self) -> int:
        """Number of interceptors in the pipeline"""
        return len(self._interceptors)
    
    def get_interceptor(self, name: str) -> Optional[IMiddlewareInterceptor]:
        """
        Get an interceptor by name.
        
        Args:
            name: Name of the interceptor
            
        Returns:
            Interceptor or None if not found
        """
        return self._interceptor_map.get(name)
    
    def has_interceptor(self, name: str) -> bool:
        """
        Check if an interceptor exists in the pipeline.
        
        Args:
            name: Name of the interceptor
            
        Returns:
            True if interceptor exists
        """
        return name in self._interceptor_map
    
    def clear(self) -> 'Pipeline':
        """
        Clear all interceptors from the pipeline.
        
        Returns:
            Self for method chaining
        """
        self._interceptors.clear()
        self._interceptor_map.clear()
        logger.debug("Pipeline cleared")
        return self
    
    def clone(self) -> 'Pipeline':
        """
        Create a copy of this pipeline with the same interceptors.
        
        Returns:
            New pipeline instance with same interceptors
        """
        return Pipeline(list(self._interceptors))


class PipelineBuilder:
    """
    Builder for creating middleware pipelines with fluent interface.
    """
    
    def __init__(self):
        """Initialize pipeline builder"""
        self._interceptors: List[IMiddlewareInterceptor] = []
        self._config: Dict[str, Any] = {}
    
    def add_interceptor(self, interceptor: IMiddlewareInterceptor) -> 'PipelineBuilder':
        """
        Add an interceptor to the pipeline being built.
        
        Args:
            interceptor: The interceptor to add
            
        Returns:
            Self for method chaining
        """
        self._interceptors.append(interceptor)
        return self
    
    def add_routing(self, priority: int = 100) -> 'PipelineBuilder':
        """
        Add routing interceptor.
        
        Args:
            priority: Priority for the interceptor
            
        Returns:
            Self for method chaining
        """
        from .interceptors import RoutingInterceptor
        self._interceptors.append(RoutingInterceptor(priority=priority))
        return self
    
    def add_validation(self, priority: int = 200) -> 'PipelineBuilder':
        """
        Add validation interceptor.
        
        Args:
            priority: Priority for the interceptor
            
        Returns:
            Self for method chaining
        """
        from .interceptors import ValidationInterceptor
        self._interceptors.append(ValidationInterceptor(priority=priority))
        return self
    
    def add_execution(self, priority: int = 500) -> 'PipelineBuilder':
        """
        Add execution interceptor.
        
        Args:
            priority: Priority for the interceptor
            
        Returns:
            Self for method chaining
        """
        from .interceptors import ExecutionInterceptor
        self._interceptors.append(ExecutionInterceptor(priority=priority))
        return self
    
    def add_observability(self, priority: int = 50) -> 'PipelineBuilder':
        """
        Add observability interceptor.
        
        Args:
            priority: Priority for the interceptor
            
        Returns:
            Self for method chaining
        """
        from .interceptors import ObservabilityInterceptor
        self._interceptors.append(ObservabilityInterceptor(priority=priority))
        return self
    
    def add_error_handling(self, priority: int = 10) -> 'PipelineBuilder':
        """
        Add error handling interceptor.
        
        Args:
            priority: Priority for the interceptor
            
        Returns:
            Self for method chaining
        """
        from .interceptors import ErrorInterceptor
        self._interceptors.append(ErrorInterceptor(priority=priority))
        return self
    
    def with_config(self, **config) -> 'PipelineBuilder':
        """
        Add configuration options.
        
        Args:
            **config: Configuration key-value pairs
            
        Returns:
            Self for method chaining
        """
        self._config.update(config)
        return self
    
    def build(self) -> Pipeline:
        """
        Build the pipeline with configured interceptors.
        
        Returns:
            Configured pipeline instance
        """
        pipeline = Pipeline(self._interceptors)
        
        # Apply configuration if any
        if self._config:
            logger.debug(f"Built pipeline with config: {self._config}")
        
        return pipeline
    
    @classmethod
    def create_default(cls) -> Pipeline:
        """
        Create a default pipeline with standard interceptors.
        
        Returns:
            Pipeline with default interceptors
        """
        return (cls()
                .add_error_handling(10)
                .add_observability(50)
                .add_routing(100)
                .add_validation(200)
                .add_execution(500)
                .build())
    
    @classmethod
    def create_minimal(cls) -> Pipeline:
        """
        Create a minimal pipeline with only essential interceptors.
        
        Returns:
            Pipeline with minimal interceptors
        """
        return (cls()
                .add_routing(100)
                .add_execution(500)
                .build())


# Convenience function for creating pipelines
def create_pipeline(*interceptors: IMiddlewareInterceptor) -> Pipeline:
    """
    Create a pipeline with the given interceptors.
    
    Args:
        *interceptors: Interceptors to add to the pipeline
        
    Returns:
        Pipeline with the interceptors
    """
    return Pipeline(list(interceptors))


# Convenience function for creating default pipeline
def create_default_pipeline() -> Pipeline:
    """
    Create a default pipeline with standard interceptors.
    
    Returns:
        Pipeline with default interceptors
    """
    return PipelineBuilder.create_default()
