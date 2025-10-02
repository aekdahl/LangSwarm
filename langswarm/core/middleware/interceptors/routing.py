"""
LangSwarm V2 Routing Interceptor

Handles routing requests to appropriate handlers (tools, plugins, RAGs).
Replaces the legacy _route_action method with modern, testable logic.
"""

import logging
from typing import Callable, Optional, Any, Dict, List

from langswarm.core.errors import handle_error, ToolError, ErrorContext

from ..interfaces import IRequestContext, IResponseContext, RequestType, ResponseStatus
from ..context import ResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class RegistryAdapter:
    """
    Adapter for legacy registries to provide consistent interface.
    Handles both dict-like and object-like registries.
    """
    
    def __init__(self, registry: Any, registry_type: str, getter_method: str):
        """
        Initialize registry adapter.
        
        Args:
            registry: The registry object (dict or object with getter method)
            registry_type: Type of registry (tool, plugin, rag)
            getter_method: Method name to get handlers (e.g., 'get_tool')
        """
        self.registry = registry
        self.registry_type = registry_type
        self.getter_method = getter_method
    
    def get_handler(self, action_id: str) -> Optional[Any]:
        """
        Get handler for the given action ID.
        
        Args:
            action_id: ID of the action to get handler for
            
        Returns:
            Handler object or None if not found
        """
        if not self.registry:
            return None
        
        try:
            if isinstance(self.registry, dict):
                return self.registry.get(action_id)
            else:
                getter = getattr(self.registry, self.getter_method, None)
                if callable(getter):
                    return getter(action_id)
                else:
                    # Fallback to direct attribute access
                    return getattr(self.registry, action_id, None)
        except Exception as e:
            logger.warning(f"Error accessing {self.registry_type} registry: {e}")
            return None
    
    def has_handler(self, action_id: str) -> bool:
        """
        Check if handler exists for the given action ID.
        
        Args:
            action_id: ID of the action to check
            
        Returns:
            True if handler exists
        """
        return self.get_handler(action_id) is not None
    
    def list_handlers(self) -> List[str]:
        """
        List all available handler IDs.
        
        Returns:
            List of handler IDs
        """
        if not self.registry:
            return []
        
        try:
            if isinstance(self.registry, dict):
                return list(self.registry.keys())
            else:
                # Try to get list method
                list_method = getattr(self.registry, f'list_{self.registry_type}s', None)
                if callable(list_method):
                    return list_method()
                
                # Fallback to tools attribute if available
                tools_attr = getattr(self.registry, 'tools', None)
                if isinstance(tools_attr, list):
                    return [getattr(tool, 'id', str(tool)) for tool in tools_attr]
                
                return []
        except Exception as e:
            logger.warning(f"Error listing {self.registry_type} handlers: {e}")
            return []


class RoutingInterceptor(BaseInterceptor):
    """
    Interceptor that routes requests to appropriate handlers.
    
    Handles the routing logic previously implemented in MiddlewareMixin._route_action,
    but with better error handling, observability, and testability.
    """
    
    def __init__(
        self, 
        priority: int = 100,
        rag_registry: Any = None,
        tool_registry: Any = None,
        plugin_registry: Any = None
    ):
        """
        Initialize routing interceptor.
        
        Args:
            priority: Priority for interceptor ordering
            rag_registry: RAG registry for memory/retrieval operations
            tool_registry: Tool registry for tool operations
            plugin_registry: Plugin registry for plugin operations
        """
        super().__init__(name="routing", priority=priority)
        
        # Initialize registry adapters
        self._rag_adapter = RegistryAdapter(rag_registry, "rag", "get_rag") if rag_registry else None
        self._tool_adapter = RegistryAdapter(tool_registry, "tool", "get_tool") if tool_registry else None
        self._plugin_adapter = RegistryAdapter(plugin_registry, "plugin", "get_plugin") if plugin_registry else None
        
        # Registry search order (RAG -> Tool -> Plugin)
        self._adapters = [
            adapter for adapter in [self._rag_adapter, self._tool_adapter, self._plugin_adapter]
            if adapter is not None
        ]
        
        logger.debug(f"Routing interceptor initialized with {len(self._adapters)} registries")
    
    def set_registries(
        self, 
        rag_registry: Any = None, 
        tool_registry: Any = None, 
        plugin_registry: Any = None
    ) -> None:
        """
        Update the registries used for routing.
        
        Args:
            rag_registry: RAG registry
            tool_registry: Tool registry  
            plugin_registry: Plugin registry
        """
        if rag_registry is not None:
            self._rag_adapter = RegistryAdapter(rag_registry, "rag", "get_rag")
        if tool_registry is not None:
            self._tool_adapter = RegistryAdapter(tool_registry, "tool", "get_tool")
        if plugin_registry is not None:
            self._plugin_adapter = RegistryAdapter(plugin_registry, "plugin", "get_plugin")
        
        # Update adapters list
        self._adapters = [
            adapter for adapter in [self._rag_adapter, self._tool_adapter, self._plugin_adapter]
            if adapter is not None
        ]
        
        logger.debug(f"Routing interceptor registries updated, {len(self._adapters)} registries available")
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Route the request to find an appropriate handler and call next interceptor.
        
        Args:
            context: The request context
            next_interceptor: Function to call the next interceptor
            
        Returns:
            Response context with routing information
        """
        action_id = context.action_id
        
        logger.debug(f"Routing request for action: {action_id}")
        
        # Try to find handler in registries
        handler, registry_type = self._find_handler(action_id)
        
        if handler is None:
            logger.warning(f"No handler found for action: {action_id}")
            return ResponseContext.not_found(
                context.request_id,
                action_id,
                available_handlers=self._get_available_handlers(),
                registries_searched=[adapter.registry_type for adapter in self._adapters]
            )
        
        logger.debug(f"Found handler for {action_id} in {registry_type} registry")
        
        # Add routing information to context
        enhanced_context = context.with_metadata(
            handler=handler,
            handler_type=registry_type,
            routing_interceptor="routing"
        )
        
        # Call next interceptor with enhanced context
        return await next_interceptor(enhanced_context)
    
    def _find_handler(self, action_id: str) -> tuple[Optional[Any], Optional[str]]:
        """
        Find handler for the given action ID across all registries.
        
        Args:
            action_id: ID of the action to find handler for
            
        Returns:
            Tuple of (handler, registry_type) or (None, None) if not found
        """
        for adapter in self._adapters:
            try:
                handler = adapter.get_handler(action_id)
                if handler is not None:
                    return handler, adapter.registry_type
            except Exception as e:
                logger.warning(f"Error searching {adapter.registry_type} registry: {e}")
                # Continue searching other registries
                continue
        
        return None, None
    
    def _get_available_handlers(self) -> Dict[str, List[str]]:
        """
        Get list of all available handlers across all registries.
        
        Returns:
            Dictionary mapping registry type to list of handler IDs
        """
        available = {}
        
        for adapter in self._adapters:
            try:
                handlers = adapter.list_handlers()
                available[adapter.registry_type] = handlers
            except Exception as e:
                logger.warning(f"Error listing {adapter.registry_type} handlers: {e}")
                available[adapter.registry_type] = []
        
        return available
    
    def can_handle(self, context: IRequestContext) -> bool:
        """
        Check if this interceptor should handle the request.
        
        The routing interceptor should handle all request types as it's responsible
        for finding the appropriate handler.
        
        Args:
            context: The request context
            
        Returns:
            True (routing interceptor handles all requests)
        """
        return self.enabled and len(self._adapters) > 0
    
    def get_handler_for_action(self, action_id: str) -> Optional[Any]:
        """
        Public method to get handler for action (useful for testing).
        
        Args:
            action_id: ID of the action
            
        Returns:
            Handler object or None if not found
        """
        handler, _ = self._find_handler(action_id)
        return handler
    
    def has_handler_for_action(self, action_id: str) -> bool:
        """
        Check if any registry has a handler for the action.
        
        Args:
            action_id: ID of the action
            
        Returns:
            True if handler exists
        """
        return self.get_handler_for_action(action_id) is not None
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about available registries.
        
        Returns:
            Dictionary with registry information
        """
        info = {
            'total_registries': len(self._adapters),
            'registries': {}
        }
        
        for adapter in self._adapters:
            try:
                handlers = adapter.list_handlers()
                info['registries'][adapter.registry_type] = {
                    'handler_count': len(handlers),
                    'handlers': handlers[:10],  # Show first 10 for brevity
                    'has_more': len(handlers) > 10
                }
            except Exception as e:
                info['registries'][adapter.registry_type] = {
                    'error': str(e),
                    'handler_count': 0
                }
        
        return info
