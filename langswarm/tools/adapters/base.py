"""
LangSwarm V2 Base Tool Adapter

Base adapter class for wrapping legacy tools to provide V2 interface compatibility.
"""

import asyncio
import inspect
from typing import Any, Dict, List, Optional
import logging

# V1/V2 compatibility for error handling
try:
    from langswarm.core.errors import handle_error, ToolError
except ImportError:
    try:
        from langswarm.v1.core.errors import handle_error, ToolError
    except ImportError:
        # Fallback for minimal environments
        class ToolError(Exception):
            pass
        def handle_error(func):
            return func

from ..interfaces import IToolInterface, IToolAdapter, ToolType, ToolCapability
from ..base import BaseTool, ToolMetadata, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class LegacyToolAdapter(BaseTool):
    """
    Base adapter for wrapping legacy tools to provide V2 interface.
    
    This adapter wraps any legacy tool and provides the standard V2 interface,
    allowing seamless integration with the V2 tool system.
    """
    
    def __init__(
        self,
        legacy_tool: Any,
        tool_id: str = None,
        name: str = None,
        description: str = None,
        tool_type: ToolType = ToolType.MCP,
        capabilities: List[ToolCapability] = None,
        **kwargs
    ):
        # Extract metadata from legacy tool
        extracted_id = tool_id or self._extract_id(legacy_tool)
        extracted_name = name or self._extract_name(legacy_tool)
        extracted_description = description or self._extract_description(legacy_tool)
        
        # Initialize V2 tool
        super().__init__(
            tool_id=extracted_id,
            name=extracted_name,
            description=extracted_description,
            tool_type=tool_type,
            capabilities=capabilities or [ToolCapability.READ, ToolCapability.EXECUTE],
            tags=["legacy", "adapted"],
            **kwargs
        )
        
        # Store legacy tool
        self._legacy_tool = legacy_tool
        self._adapter_type = "legacy"
        
        # Analyze legacy tool methods
        self._analyze_legacy_methods()
        
        self._logger.info(f"Adapted legacy tool: {extracted_id} ({type(legacy_tool).__name__})")
    
    def _extract_id(self, tool: Any) -> str:
        """Extract tool ID from legacy tool"""
        # Try common ID attributes
        for attr in ['id', 'identifier', 'tool_id', 'name']:
            if hasattr(tool, attr):
                value = getattr(tool, attr)
                if value and isinstance(value, str):
                    return value.lower().replace(' ', '_')
        
        # Fallback to class name
        return tool.__class__.__name__.lower()
    
    def _extract_name(self, tool: Any) -> str:
        """Extract tool name from legacy tool"""
        # Try common name attributes
        for attr in ['name', 'tool_name', 'title']:
            if hasattr(tool, attr):
                value = getattr(tool, attr)
                if value and isinstance(value, str):
                    return value
        
        # Fallback to class name
        return tool.__class__.__name__
    
    def _extract_description(self, tool: Any) -> str:
        """Extract tool description from legacy tool"""
        # Try common description attributes
        for attr in ['description', 'brief', 'doc', '__doc__']:
            if hasattr(tool, attr):
                value = getattr(tool, attr)
                if value and isinstance(value, str):
                    return value.strip()
        
        # Fallback to generic description
        return f"Legacy tool: {tool.__class__.__name__}"
    
    def _analyze_legacy_methods(self):
        """Analyze legacy tool methods and add to metadata"""
        # Common method patterns
        methods_to_check = ['run', 'execute', 'call', 'use']
        
        # Check for direct methods
        for method_name in methods_to_check:
            if hasattr(self._legacy_tool, method_name):
                method = getattr(self._legacy_tool, method_name)
                if callable(method):
                    self._add_method_from_callable(method_name, method)
        
        # Check for action-based methods (common in Synapse tools)
        if hasattr(self._legacy_tool, 'run'):
            self._analyze_action_methods()
    
    def _add_method_from_callable(self, name: str, method: callable):
        """Add method schema from callable"""
        try:
            sig = inspect.signature(method)
            parameters = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'cls']:
                    continue
                
                param_info = {
                    "type": "any",
                    "description": f"Parameter: {param_name}"
                }
                
                if param.default == param.empty:
                    required.append(param_name)
                else:
                    param_info["default"] = param.default
                
                parameters[param_name] = param_info
            
            schema = ToolSchema(
                name=name,
                description=f"Legacy method: {name}",
                parameters=parameters,
                returns={"type": "any", "description": "Method result"},
                required=required
            )
            
            self._metadata.add_method(schema)
            
        except Exception as e:
            self._logger.warning(f"Failed to analyze method {name}: {e}")
    
    def _analyze_action_methods(self):
        """Analyze action-based methods (for tools with action parameter)"""
        # This is common in Synapse tools where actions are passed to run()
        if hasattr(self._legacy_tool, 'instruction'):
            instruction = getattr(self._legacy_tool, 'instruction')
            # Parse instruction text to find available actions
            # This is a simplified parser - can be enhanced
            if 'actions:' in instruction.lower():
                # Try to extract action names from instruction
                lines = instruction.split('\n')
                for line in lines:
                    if 'action:' in line.lower() or '- ' in line:
                        # Simple action extraction
                        action_name = line.strip().replace('-', '').replace('action:', '').strip()
                        if action_name and action_name.isalnum():
                            self._add_action_method(action_name)
    
    def _add_action_method(self, action_name: str):
        """Add an action-based method"""
        schema = ToolSchema(
            name=action_name,
            description=f"Legacy action: {action_name}",
            parameters={
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "default": action_name
                },
                "payload": {
                    "type": "object",
                    "description": "Action parameters"
                }
            },
            returns={"type": "any", "description": "Action result"},
            required=[]
        )
        
        self._metadata.add_method(schema)
    
    async def _initialize_impl(self):
        """Initialize the adapted legacy tool"""
        # Check if legacy tool has initialization method
        for init_method in ['initialize', 'init', 'setup']:
            if hasattr(self._legacy_tool, init_method):
                method = getattr(self._legacy_tool, init_method)
                if callable(method):
                    try:
                        if asyncio.iscoroutinefunction(method):
                            await method()
                        else:
                            method()
                        self._logger.debug(f"Called legacy tool {init_method}")
                        break
                    except Exception as e:
                        self._logger.warning(f"Legacy tool {init_method} failed: {e}")
    
    async def _cleanup_impl(self):
        """Cleanup the adapted legacy tool"""
        # Check if legacy tool has cleanup method
        for cleanup_method in ['cleanup', 'close', 'shutdown']:
            if hasattr(self._legacy_tool, cleanup_method):
                method = getattr(self._legacy_tool, cleanup_method)
                if callable(method):
                    try:
                        if asyncio.iscoroutinefunction(method):
                            await method()
                        else:
                            method()
                        self._logger.debug(f"Called legacy tool {cleanup_method}")
                        break
                    except Exception as e:
                        self._logger.warning(f"Legacy tool {cleanup_method} failed: {e}")
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Run the legacy tool with compatibility handling.
        
        This method provides the main interface to the legacy tool,
        handling different calling conventions and parameter patterns.
        """
        try:
            # Pattern 1: Try direct run method
            if hasattr(self._legacy_tool, 'run'):
                run_method = getattr(self._legacy_tool, 'run')
                return self._call_legacy_method(run_method, input_data, **kwargs)
            
            # Pattern 2: Try use method (LangChain compatibility)
            if hasattr(self._legacy_tool, 'use'):
                use_method = getattr(self._legacy_tool, 'use')
                return self._call_legacy_method(use_method, input_data, **kwargs)
            
            # Pattern 3: Try execute method
            if hasattr(self._legacy_tool, 'execute'):
                execute_method = getattr(self._legacy_tool, 'execute')
                return self._call_legacy_method(execute_method, input_data, **kwargs)
            
            # Pattern 4: Try calling the tool directly
            if callable(self._legacy_tool):
                return self._call_legacy_method(self._legacy_tool, input_data, **kwargs)
            
            # No suitable method found
            raise ToolError(
                f"Legacy tool {self.metadata.id} has no callable interface",
                suggestion="Ensure the tool implements 'run', 'use', 'execute', or is callable"
            )
            
        except Exception as e:
            self._logger.error(f"Legacy tool execution failed: {e}")
            handle_error(e, f"adapter_{self.metadata.id}")
            raise
    
    def _call_legacy_method(self, method: callable, input_data: Any, **kwargs) -> Any:
        """Call a legacy method with appropriate parameter handling"""
        try:
            sig = inspect.signature(method)
            params = sig.parameters
            
            # Handle different parameter patterns
            if 'input_data' in params:
                return method(input_data=input_data, **kwargs)
            elif 'payload' in params:
                return method(payload=kwargs or input_data)
            elif 'data' in params:
                return method(data=input_data, **kwargs)
            elif len(params) == 1 and list(params.keys())[0] != 'self':
                # Single parameter method
                param_name = list(params.keys())[0]
                return method(**{param_name: input_data or kwargs})
            elif len(params) == 0 or (len(params) == 1 and 'self' in params):
                # No parameter method
                return method()
            else:
                # Multiple parameters, try kwargs
                return method(**kwargs)
                
        except TypeError as e:
            # Parameter mismatch, try simpler approach
            self._logger.warning(f"Parameter mismatch for {method}, trying simple call: {e}")
            if input_data is not None:
                return method(input_data)
            else:
                return method()
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check including legacy tool status"""
        base_health = super().health_check()
        
        base_health.update({
            "adapter_type": self._adapter_type,
            "legacy_tool_type": type(self._legacy_tool).__name__,
            "legacy_tool_methods": [
                name for name in dir(self._legacy_tool)
                if callable(getattr(self._legacy_tool, name)) and not name.startswith('_')
            ]
        })
        
        # Check if legacy tool has health check
        if hasattr(self._legacy_tool, 'health_check'):
            try:
                legacy_health = self._legacy_tool.health_check()
                base_health["legacy_health"] = legacy_health
            except Exception as e:
                base_health["legacy_health"] = {"error": str(e)}
        
        return base_health
    
    @property
    def legacy_tool(self) -> Any:
        """Access to the underlying legacy tool"""
        return self._legacy_tool


class AdapterFactory:
    """Factory for creating appropriate adapters for different tool types"""
    
    @staticmethod
    def create_adapter(tool: Any, **kwargs) -> Optional[LegacyToolAdapter]:
        """
        Create appropriate adapter for a given tool.
        
        Args:
            tool: Legacy tool to adapt
            **kwargs: Additional configuration
            
        Returns:
            Appropriate adapter or None if tool cannot be adapted
        """
        # Import adapters here to avoid circular imports
        from .synapse import SynapseToolAdapter
        from .rag import RAGToolAdapter
        from .plugin import PluginToolAdapter
        from .mcp import MCPToolAdapter
        
        # Determine tool type and create appropriate adapter
        tool_type_name = type(tool).__name__
        
        # Check for Synapse tools
        if 'synapse' in tool.__class__.__module__.lower() or hasattr(tool, 'consensus'):
            return SynapseToolAdapter(tool, **kwargs)
        
        # Check for RAG/memory tools
        if (hasattr(tool, 'query') and hasattr(tool, 'add_documents')) or \
           'memory' in tool.__class__.__module__.lower() or \
           'rag' in tool_type_name.lower():
            return RAGToolAdapter(tool, **kwargs)
        
        # Check for MCP tools
        if 'mcp' in tool.__class__.__module__.lower() or 'MCP' in tool_type_name:
            return MCPToolAdapter(tool, **kwargs)
        
        # Check for plugin tools
        if 'plugin' in tool.__class__.__module__.lower() or 'Plugin' in tool_type_name:
            return PluginToolAdapter(tool, **kwargs)
        
        # Default to base legacy adapter
        return LegacyToolAdapter(tool, **kwargs)
