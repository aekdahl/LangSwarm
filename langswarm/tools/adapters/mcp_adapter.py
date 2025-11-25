"""
MCP Tool V2 Adapter

Bridges existing MCP tools to the V2 IToolInterface without requiring
changes to the original tool implementations. This allows gradual migration
and maintains backward compatibility.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from ..interfaces import (
    IToolInterface, IToolMetadata, IToolExecution, 
    ToolType, ToolCapability
)
from ..base import ToolMetadata, ToolExecution

logger = logging.getLogger(__name__)


class MCPToolAdapter(IToolInterface):
    """
    Adapter that wraps existing MCP tools to make them V2 compatible.
    
    This adapter:
    - Auto-discovers tool methods and capabilities
    - Creates V2 metadata from MCP tool properties
    - Provides V2 execution interface
    - Handles async/sync method calls
    - Manages tool lifecycle
    """
    
    def __init__(self, mcp_tool: Any, tool_id: Optional[str] = None):
        self._mcp_tool = mcp_tool
        self._tool_id = tool_id or getattr(mcp_tool, 'identifier', type(mcp_tool).__name__.lower())
        self._metadata = None
        self._execution = None
        self._initialized = False
        self._logger = logging.getLogger(f"mcp_adapter.{self._tool_id}")
        
        # Auto-discover tool properties
        self._discover_tool_properties()
    
    def _discover_tool_properties(self):
        """Auto-discover tool properties and capabilities"""
        try:
            # Get tool name and description
            name = getattr(self._mcp_tool, 'name', self._tool_id)
            description = getattr(self._mcp_tool, 'description', '')
            
            # Try to get instruction from MCP tool
            instruction = getattr(self._mcp_tool, 'instruction', None)
            
            # If no instruction but we have description, use description as instruction
            if not instruction and description:
                instruction = description
            
            # Try to get description from template.md if available
            if not description:
                description = self._load_description_from_template()
            
            # Auto-discover methods
            discovered_methods = self._discover_methods()
            
            # Create ToolSchema for each discovered method
            from ..base import ToolSchema
            method_schemas = {}
            
            # Standard MCP protocol methods to skip
            mcp_protocol_methods = [
                'call_tool', 'list_tools', 'list_prompts', 'get_prompt',
                'list_resources', 'read_resource', 'run_async', 'run', 
                'initialize', 'cleanup', 'health_check'
            ]
            
            for method_name in discovered_methods:
                if method_name in mcp_protocol_methods:
                    # Skip MCP protocol methods and infrastructure methods
                    continue
                
                # Try to get method for signature inspection
                method = getattr(self._mcp_tool, method_name, None)
                if method and callable(method):
                    # Try to inspect method signature for parameters
                    import inspect
                    try:
                        sig = inspect.signature(method)
                        parameters = {}
                        required = []
                        
                        for param_name, param in sig.parameters.items():
                            if param_name in ['self', 'cls']:
                                continue
                            
                            param_info = {
                                "type": "string",  # Default to string
                                "description": f"Parameter: {param_name}"
                            }
                            
                            if param.default == param.empty:
                                required.append(param_name)
                            else:
                                param_info["default"] = str(param.default)
                            
                            parameters[param_name] = param_info
                        
                        # Create schema for the method
                        method_schemas[method_name] = ToolSchema(
                            name=method_name,
                            description=f"Execute {method_name} on {name}",
                            parameters=parameters,
                            returns={"type": "any", "description": "Method result"},
                            required=required
                        )
                        
                    except Exception as e:
                        self._logger.debug(f"Could not inspect method {method_name}: {e}")
                        # Create basic schema without parameters
                        method_schemas[method_name] = ToolSchema(
                            name=method_name,
                            description=f"Execute {method_name} on {name}",
                            parameters={},
                            returns={"type": "any"},
                            required=[]
                        )
            
            # Auto-discover capabilities
            capabilities = self._discover_capabilities()
            
            # Determine tool type
            tool_type = self._determine_tool_type()
            
            # Create V2 metadata with populated methods
            self._metadata = ToolMetadata(
                id=self._tool_id,
                name=name,
                description=description,
                instruction=instruction,
                version="1.0.0",
                tool_type=tool_type,
                capabilities=capabilities,
                methods=method_schemas,  # Now properly populated!
                tags=["mcp", "adapted"]
            )
            
            # Create V2 execution interface
            self._execution = ToolExecution(self._mcp_tool)
            
            self._logger.info(f"✅ Adapted MCP tool '{name}' with {len(discovered_methods)} discovered, {len(method_schemas)} registered methods and {len(capabilities)} capabilities")
            
        except Exception as e:
            self._logger.error(f"❌ Failed to discover tool properties: {e}")
            # Create minimal metadata as fallback
            self._metadata = ToolMetadata(
                id=self._tool_id,
                name=self._tool_id,
                description="MCP tool (adapted)",
                version="1.0.0",
                tool_type=ToolType.MCP,
                capabilities=[ToolCapability.EXECUTE],
                methods={},
                tags=["mcp", "adapted", "minimal"]
            )
            self._execution = ToolExecution(self._mcp_tool)
    
    def _load_description_from_template(self) -> str:
        """Load description from template.md file if available"""
        try:
            # Try to find template.md in the tool's directory
            tool_module = self._mcp_tool.__class__.__module__
            if tool_module:
                module_path = Path(tool_module.replace('.', '/'))
                # Look for template.md in the same directory as main.py
                template_path = module_path.parent / 'template.md'
                
                # Try different possible paths
                possible_paths = [
                    template_path,
                    Path(str(template_path).replace('langswarm/', '/Users/alexanderekdahl/Docker/LangSwarm/langswarm/')),
                ]
                
                for path in possible_paths:
                    if path.exists():
                        content = path.read_text()
                        # Extract description section
                        lines = content.split('\n')
                        in_description = False
                        description_lines = []
                        
                        for line in lines:
                            if line.strip().startswith('## Description'):
                                in_description = True
                                continue
                            elif line.strip().startswith('##') and in_description:
                                break
                            elif in_description:
                                description_lines.append(line)
                        
                        if description_lines:
                            return '\n'.join(description_lines).strip()
            
        except Exception as e:
            self._logger.debug(f"Could not load template description: {e}")
        
        return ""
    
    def _discover_methods(self) -> List[str]:
        """Auto-discover available methods on the MCP tool"""
        methods = []
        
        # Standard MCP protocol methods
        standard_methods = [
            'call_tool', 'list_tools', 'list_prompts', 'get_prompt',
            'list_resources', 'read_resource', 'run_async'
        ]
        
        for method_name in standard_methods:
            if hasattr(self._mcp_tool, method_name):
                methods.append(method_name)
        
        # Tool-specific methods - ONLY from the tool's own class, not inherited
        # This prevents discovering dozens of inherited methods from BaseTool/object
        tool_class = self._mcp_tool.__class__
        for attr_name in dir(tool_class):
            if (not attr_name.startswith('_') and 
                attr_name in tool_class.__dict__ and  # Only methods defined on this class
                callable(getattr(self._mcp_tool, attr_name, None)) and
                attr_name not in standard_methods and
                attr_name not in ['initialize', 'cleanup', 'health_check']):
                methods.append(attr_name)
        
        return methods
    
    def _discover_capabilities(self) -> List[ToolCapability]:
        """Auto-discover tool capabilities based on available methods"""
        capabilities = [ToolCapability.EXECUTE]
        
        # Check for async support
        if hasattr(self._mcp_tool, 'run_async') or any(
            asyncio.iscoroutinefunction(getattr(self._mcp_tool, method, None))
            for method in self._discover_methods()
        ):
            capabilities.append(ToolCapability.ASYNC)
        
        # Check for streaming support
        if any('stream' in method.lower() for method in self._discover_methods()):
            capabilities.append(ToolCapability.STREAM)
        
        # Check for batch support
        if any('batch' in method.lower() for method in self._discover_methods()):
            capabilities.append(ToolCapability.BATCH)
        
        # Determine specific capabilities based on tool type
        tool_name = self._tool_id.lower()
        if 'database' in tool_name or 'sql' in tool_name:
            capabilities.extend([ToolCapability.READ, ToolCapability.WRITE, ToolCapability.DATABASE])
        elif 'file' in tool_name or 'filesystem' in tool_name:
            capabilities.extend([ToolCapability.READ, ToolCapability.WRITE, ToolCapability.FILE_SYSTEM])
        elif 'network' in tool_name or 'http' in tool_name or 'api' in tool_name:
            capabilities.extend([ToolCapability.NETWORK, ToolCapability.API_INTEGRATION])
        elif 'bigquery' in tool_name or 'vector' in tool_name:
            capabilities.extend([ToolCapability.READ, ToolCapability.DATABASE, ToolCapability.AI_INTEGRATION])
        
        return list(set(capabilities))  # Remove duplicates
    
    def _determine_tool_type(self) -> ToolType:
        """Determine the tool type based on the tool name and capabilities"""
        tool_name = self._tool_id.lower()
        
        if 'database' in tool_name or 'sql' in tool_name or 'bigquery' in tool_name:
            return ToolType.DATABASE
        elif 'file' in tool_name or 'filesystem' in tool_name:
            return ToolType.FILESYSTEM
        elif 'network' in tool_name or 'http' in tool_name:
            return ToolType.NETWORK
        elif 'workflow' in tool_name:
            return ToolType.WORKFLOW
        elif 'memory' in tool_name or 'vector' in tool_name:
            return ToolType.MEMORY
        else:
            return ToolType.MCP
    
    # IToolInterface implementation
    @property
    def metadata(self) -> IToolMetadata:
        """Tool metadata"""
        return self._metadata
    
    @property
    def execution(self) -> IToolExecution:
        """Tool execution interface"""
        return self._execution
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the adapted MCP tool"""
        try:
            # Try to initialize the underlying MCP tool if it has an initialize method
            if hasattr(self._mcp_tool, 'initialize'):
                if asyncio.iscoroutinefunction(self._mcp_tool.initialize):
                    await self._mcp_tool.initialize(config)
                else:
                    self._mcp_tool.initialize(config)
            
            self._initialized = True
            self._logger.info(f"✅ Initialized adapted MCP tool '{self._tool_id}'")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Failed to initialize adapted MCP tool '{self._tool_id}': {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup the adapted MCP tool"""
        try:
            # Try to cleanup the underlying MCP tool if it has a cleanup method
            if hasattr(self._mcp_tool, 'cleanup'):
                if asyncio.iscoroutinefunction(self._mcp_tool.cleanup):
                    await self._mcp_tool.cleanup()
                else:
                    self._mcp_tool.cleanup()
            
            self._initialized = False
            self._logger.info(f"✅ Cleaned up adapted MCP tool '{self._tool_id}'")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Failed to cleanup adapted MCP tool '{self._tool_id}': {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check health status of the adapted MCP tool"""
        try:
            # Try to get health status from the underlying MCP tool
            if hasattr(self._mcp_tool, 'health_check'):
                mcp_health = self._mcp_tool.health_check()
                if isinstance(mcp_health, dict):
                    return {
                        "status": "healthy",
                        "tool_id": self._tool_id,
                        "initialized": self._initialized,
                        "adapter_version": "1.0.0",
                        "mcp_tool_health": mcp_health
                    }
            
            # Default health check
            return {
                "status": "healthy" if self._initialized else "not_initialized",
                "tool_id": self._tool_id,
                "initialized": self._initialized,
                "adapter_version": "1.0.0",
                "methods_count": len(self._metadata.methods),
                "capabilities_count": len(self._metadata.capabilities)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "tool_id": self._tool_id,
                "initialized": self._initialized,
                "adapter_version": "1.0.0",
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema in V2 format"""
        return {
            "id": self._metadata.id,
            "name": self._metadata.name,
            "description": self._metadata.description,
            "version": self._metadata.version,
            "type": self._metadata.tool_type.value,
            "capabilities": [cap.value for cap in self._metadata.capabilities],
            "methods": self._metadata.methods,
            "tags": self._metadata.tags,
            "adapter": "mcp_v2_adapter",
            "input_schema": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": self._metadata.methods,
                        "description": "Method to call on the tool"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the method call",
                        "additionalProperties": True
                    }
                },
                "required": ["method"]
            }
        }


def create_mcp_adapter(mcp_tool: Any, tool_id: Optional[str] = None) -> MCPToolAdapter:
    """
    Factory function to create an MCP tool adapter.
    
    Args:
        mcp_tool: The existing MCP tool instance
        tool_id: Optional custom tool ID
        
    Returns:
        MCPToolAdapter instance
    """
    return MCPToolAdapter(mcp_tool, tool_id)


def auto_adapt_mcp_tools(tools_directory: str) -> List[MCPToolAdapter]:
    """
    Auto-discover and adapt all MCP tools in a directory.
    
    Args:
        tools_directory: Path to the MCP tools directory
        
    Returns:
        List of adapted MCP tools
    """
    adapted_tools = []
    tools_path = Path(tools_directory)
    
    if not tools_path.exists():
        logger.warning(f"MCP tools directory not found: {tools_directory}")
        return adapted_tools
    
    # Look for main.py files in subdirectories
    for tool_dir in tools_path.iterdir():
        if tool_dir.is_dir():
            main_file = tool_dir / 'main.py'
            if main_file.exists():
                try:
                    # Import the tool module
                    module_name = f"langswarm.tools.mcp.{tool_dir.name}.main"
                    module = __import__(module_name, fromlist=[''])
                    
                    # Look for MCP tool classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            attr_name.endswith('MCPTool') and
                            attr_name != 'MCPTool'):
                            
                            try:
                                # Create tool instance
                                tool_instance = attr(identifier=tool_dir.name)
                                
                                # Create adapter
                                adapter = create_mcp_adapter(tool_instance, tool_dir.name)
                                adapted_tools.append(adapter)
                                
                                logger.info(f"✅ Auto-adapted MCP tool: {tool_dir.name}")
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Could not adapt MCP tool {tool_dir.name}: {e}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Could not import MCP tool from {tool_dir}: {e}")
    
    logger.info(f"🎉 Auto-adapted {len(adapted_tools)} MCP tools")
    return adapted_tools
