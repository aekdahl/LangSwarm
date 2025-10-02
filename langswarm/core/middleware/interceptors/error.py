"""
LangSwarm V2 Error Interceptor

Handles error processing and recovery in the middleware pipeline.
"""

import logging
from typing import Callable

from langswarm.core.errors import handle_error

from ..interfaces import IRequestContext, IResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class ErrorInterceptor(BaseInterceptor):
    """
    Interceptor that handles errors and provides recovery mechanisms.
    """
    
    def __init__(self, priority: int = 10):
        super().__init__(name="error", priority=priority)
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Wrap next interceptor with error handling.
        """
        try:
            return await next_interceptor(context)
        except Exception as e:
            logger.error(f"Error in middleware pipeline: {e}")
            handle_error(e, "middleware_pipeline")
            return self.on_error(context, e)
