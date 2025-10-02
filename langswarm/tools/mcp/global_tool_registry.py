#!/usr/bin/env python3
"""
Global Tool Registry - System-wide list_tools() Implementation

This implements a global registry that can list all available MCP tools
in the system, following the MCP standard where list_tools() should return
ALL tools, not just methods of a single tool.
"""

import os
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ToolInfo:
    """Information about a tool"""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], module_path: str = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.module_path = module_path

class GlobalMCPToolRegistry:
    """
    Global registry for all MCP tools in the system.
    
    Implements the MCP standard where list_tools() returns ALL available tools,
    not just methods of a single tool.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._loaded = False
    
    def _discover_mcp_tools(self) -> Dict[str, ToolInfo]:
        """Discover all MCP tools in the system"""
        tools = {}
        
        # Get the MCP tools directory
        mcp_tools_dir = Path(__file__).parent
        
        for tool_dir in mcp_tools_dir.iterdir():
            if tool_dir.is_dir() and not tool_dir.name.startswith(('_', '.')):
                tool_name = tool_dir.name
                main_file = tool_dir / "main.py"
                template_file = tool_dir / "template.md"
                
                if main_file.exists():
                    try:
                        # Try to load tool metadata
                        description = self._extract_description(template_file)
                        input_schema = self._generate_input_schema(tool_name)
                        
                        tools[tool_name] = ToolInfo(
                            name=tool_name,
                            description=description,
                            input_schema=input_schema,
                            module_path=str(main_file)
                        )
                        
                        logger.debug(f"Discovered tool: {tool_name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to load tool {tool_name}: {e}")
        
        return tools
    
    def _extract_description(self, template_file: Path) -> str:
        """Extract description from template.md file"""
        if not template_file.exists():
            return "MCP tool with intelligent intent processing"
        
        try:
            content = template_file.read_text()
            lines = content.split('\n')
            
            # Look for description section
            in_description = False
            description_lines = []
            
            for line in lines:
                if line.strip() == "## Description":
                    in_description = True
                    continue
                elif line.startswith("## ") and in_description:
                    break
                elif in_description and line.strip():
                    description_lines.append(line.strip())
            
            if description_lines:
                return ' '.join(description_lines)
            else:
                # Fallback: use first non-empty line after title
                for line in lines[2:]:  # Skip title and empty line
                    if line.strip():
                        return line.strip()
                        
        except Exception as e:
            logger.warning(f"Failed to extract description from {template_file}: {e}")
        
        return f"MCP tool: {template_file.parent.name}"
    
    def _generate_input_schema(self, tool_name: str) -> Dict[str, Any]:
        """Generate input schema for a tool"""
        return {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "Natural language description of what you want to accomplish (LangSwarm USP)"
                },
                "context": {
                    "type": "string", 
                    "description": "Additional context to help interpret the intent"
                },
                "method": {
                    "type": "string",
                    "description": "Specific method to call (for direct method calling)"
                },
                "params": {
                    "type": "object",
                    "description": "Parameters for the specific method"
                }
            },
            "oneOf": [
                {
                    "required": ["intent"],
                    "description": "Intent-based calling (recommended)"
                },
                {
                    "required": ["method", "params"],
                    "description": "Direct method calling"
                }
            ],
            "description": f"Supports both intent-based calling and direct method calling. For flattened calls, use name='{tool_name}.method_name'"
        }
    
    def load_tools(self) -> None:
        """Load all available tools"""
        if self._loaded:
            return
        
        logger.info("Loading global MCP tool registry...")
        self._tools = self._discover_mcp_tools()
        self._loaded = True
        logger.info(f"Loaded {len(self._tools)} MCP tools")
    
    def list_tools(self) -> List[ToolInfo]:
        """
        List all available tools in the system.
        
        This implements the MCP standard where list_tools() returns ALL tools,
        not just methods of a single tool.
        """
        if not self._loaded:
            self.load_tools()
        
        return list(self._tools.values())
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool"""
        if not self._loaded:
            self.load_tools()
        
        return self._tools.get(name)
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        if not self._loaded:
            self.load_tools()
        
        return list(self._tools.keys())
    
    def create_tool_instance(self, tool_name: str, **kwargs):
        """Create an instance of a specific tool"""
        if not self._loaded:
            self.load_tools()
        
        tool_info = self._tools.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            # Import the tool module
            module_path = tool_info.module_path
            spec = importlib.util.spec_from_file_location(f"{tool_name}_main", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the tool class (should end with MCPTool)
            tool_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('MCPTool') and 
                    attr_name != 'BaseMCPTool'):
                    tool_class = attr
                    break
            
            if not tool_class:
                raise ValueError(f"No MCP tool class found in {module_path}")
            
            # Create instance
            return tool_class(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to create tool instance for {tool_name}: {e}")
            raise

# Global registry instance
global_registry = GlobalMCPToolRegistry()

# Convenience functions
def list_all_tools() -> List[ToolInfo]:
    """List all available MCP tools in the system"""
    return global_registry.list_tools()

def get_tool_info(name: str) -> Optional[ToolInfo]:
    """Get information about a specific tool"""
    return global_registry.get_tool(name)

def get_all_tool_names() -> List[str]:
    """Get list of all tool names"""
    return global_registry.get_tool_names()

def create_tool(tool_name: str, **kwargs):
    """Create an instance of a specific tool"""
    return global_registry.create_tool_instance(tool_name, **kwargs)

# MCP Protocol Interface for Global Registry
class GlobalMCPProtocolInterface:
    """
    Global MCP protocol interface that can list and call any tool in the system.
    
    This implements the true MCP standard where a server can expose multiple tools.
    """
    
    def __init__(self):
        self.registry = global_registry
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools (MCP standard)"""
        tools = self.registry.list_tools()
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in tools
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call any tool in the system (MCP standard).
        
        Supports:
        1. Flattened method calling: name="tool.method"
        2. Intent-based calling: arguments={"intent": "...", "context": "..."}
        3. Direct method calling: arguments={"method": "...", "params": {...}}
        """
        try:
            # Handle flattened method calling: tool.method
            if "." in name:
                tool_name, method_name = name.split(".", 1)
                tool_instance = self.registry.create_tool_instance(tool_name, identifier=tool_name)
                
                # Call the flattened method
                result = await tool_instance.call_tool(name, arguments)
                
                return {
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "metadata": result.metadata
                }
            
            # Handle regular tool calling
            else:
                tool_instance = self.registry.create_tool_instance(name, identifier=name)
                
                # Call the tool
                result = await tool_instance.call_tool(name, arguments)
                
                return {
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "metadata": result.metadata
                }
                
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {"error_type": type(e).__name__, "global_call": True}
            }

# Global protocol interface instance
global_protocol = GlobalMCPProtocolInterface()
