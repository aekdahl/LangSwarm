"""
LangSwarm V2 Context Interceptor

Manages request context enrichment and workflow context handling.
"""

import logging
from typing import Callable

from ..interfaces import IRequestContext, IResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class ContextInterceptor(BaseInterceptor):
    """
    Interceptor that enriches request context with additional information.
    """
    
    def __init__(self, priority: int = 150):
        super().__init__(name="context", priority=priority)
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Enrich context and call next interceptor.
        """
        # Enrich context with additional metadata
        enriched_context = context.with_metadata(
            context_interceptor="context",
            enriched_timestamp=context.timestamp.isoformat()
        )
        
        return await next_interceptor(enriched_context)
