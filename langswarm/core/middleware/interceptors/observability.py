"""
LangSwarm V2 Observability Interceptor

Provides tracing, metrics, and logging for the middleware pipeline.
"""

import logging
import time
from typing import Callable

from ..interfaces import IRequestContext, IResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class ObservabilityInterceptor(BaseInterceptor):
    """
    Interceptor that adds observability to the middleware pipeline.
    """
    
    def __init__(self, priority: int = 50):
        super().__init__(name="observability", priority=priority)
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Add observability around next interceptor.
        """
        start_time = time.time()
        
        logger.info(f"Processing request {context.request_id} for {context.action_id}.{context.method}")
        
        try:
            response = await next_interceptor(context)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Request {context.request_id} completed in {processing_time:.3f}s "
                f"with status {response.status.value}"
            )
            
            return response.with_metadata(
                observability_processing_time=processing_time,
                observability_interceptor="observability"
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Request {context.request_id} failed after {processing_time:.3f}s: {e}"
            )
            raise
