"""
Tool Inspector Tool - V2 Built-in Tool

Provides introspection capabilities for examining other tools in the system.
Useful for debugging, documentation, and system exploration.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List

from langswarm.tools.base import BaseTool, ToolResult, create_tool_metadata, create_method_schema
from langswarm.tools.interfaces import ToolType, ToolCapability


class ToolInspectorTool(BaseTool):
    """
    Built-in tool for tool introspection and system exploration.
    
    Provides capabilities to:
    - List available tools
    - Get tool metadata and schemas
    - Inspect tool capabilities
    - Generate tool documentation
    - Test tool availability
    """
    
    def __init__(self):
        metadata = create_tool_metadata(
            tool_id="builtin_tool_inspector",
            name="tool_inspector",
            description="Tool introspection and system exploration",
            version="2.0.0",
            tool_type=ToolType.BUILTIN,
            capabilities=[ToolCapability.INTROSPECTION, ToolCapability.DIAGNOSTIC, ToolCapability.DOCUMENTATION]
        )
        
        # Add methods
        metadata.add_method(create_method_schema(
            name="list_tools",
            description="List all available tools in the system",
            parameters={
                "include_metadata": {"type": "boolean", "required": False, "default": False,
                                   "description": "Include detailed metadata for each tool"}
            },
            returns="List of available tools with optional metadata"
        ))
        
        metadata.add_method(create_method_schema(
            name="inspect_tool",
            description="Get detailed information about a specific tool",
            parameters={
                "tool_name": {"type": "string", "required": True, "description": "Name of tool to inspect"}
            },
            returns="Detailed tool information including schema, methods, and capabilities"
        ))
        
        metadata.add_method(create_method_schema(
            name="list_capabilities",
            description="List all tool capabilities available in the system",
            parameters={},
            returns="List of tool capabilities with descriptions"
        ))
        
        metadata.add_method(create_method_schema(
            name="tools_by_capability",
            description="Find tools that have specific capabilities",
            parameters={
                "capability": {"type": "string", "required": True, "description": "Capability to search for"}
            },
            returns="List of tools with the specified capability"
        ))
        
        metadata.add_method(create_method_schema(
            name="generate_docs",
            description="Generate documentation for tools",
            parameters={
                "tool_names": {"type": "array", "items": {"type": "string"}, "required": False,
                             "description": "Specific tools to document (all if not specified)"},
                "format": {"type": "string", "required": False, "default": "markdown",
                         "description": "Documentation format: markdown, json, yaml"}
            },
            returns="Generated documentation"
        ))
        
        metadata.add_method(create_method_schema(
            name="test_tool",
            description="Test if a tool is available and responsive",
            parameters={
                "tool_name": {"type": "string", "required": True, "description": "Name of tool to test"}
            },
            returns="Tool availability and health status"
        ))
        
        super().__init__(metadata)
    
    async def list_tools(self, include_metadata: bool = False) -> List[Dict[str, Any]]:
        """List all available tools in the system"""
        tools = []
        
        try:
            from langswarm.tools import ServiceRegistry
            service_registry = ServiceRegistry()
            
            # Get all registries
            registries = service_registry._registries
            
            for registry_name, registry in registries.items():
                tool_list = registry.list_tools()
                for tool_name in tool_list:
                    tool_info = {
                        "name": tool_name,
                        "registry": registry_name
                    }
                    
                    if include_metadata:
                        try:
                            tool = registry.get_tool(tool_name)
                            if tool and hasattr(tool, 'metadata'):
                                tool_info.update({
                                    "description": tool.metadata.description,
                                    "version": tool.metadata.version,
                                    "type": tool.metadata.tool_type.value if hasattr(tool.metadata.tool_type, 'value') else str(tool.metadata.tool_type),
                                    "capabilities": [cap.value if hasattr(cap, 'value') else str(cap) for cap in tool.metadata.capabilities],
                                    "methods": list(tool.metadata.methods.keys()) if hasattr(tool.metadata, 'methods') else []
                                })
                        except Exception as e:
                            tool_info["metadata_error"] = str(e)
                    
                    tools.append(tool_info)
        except Exception as e:
            # Fallback: look for built-in tools
            tools.append({
                "name": "system_status",
                "registry": "builtin",
                "type": "builtin",
                "error": f"Service registry not available: {e}"
            })
        
        return tools
    
    async def inspect_tool(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool"""
        try:
            from langswarm.tools import ServiceRegistry
            service_registry = ServiceRegistry()
            
            # Find the tool across all registries
            tool = None
            registry_name = None
            
            for reg_name, registry in service_registry._registries.items():
                try:
                    tool = registry.get_tool(tool_name)
                    if tool:
                        registry_name = reg_name
                        break
                except:
                    continue
            
            if not tool:
                return {"error": f"Tool '{tool_name}' not found in any registry"}
            
            # Extract detailed information
            info = {
                "name": tool_name,
                "registry": registry_name,
                "found": True
            }
            
            if hasattr(tool, 'metadata'):
                metadata = tool.metadata
                info.update({
                    "description": metadata.description,
                    "version": metadata.version,
                    "type": metadata.tool_type.value if hasattr(metadata.tool_type, 'value') else str(metadata.tool_type),
                    "capabilities": [cap.value if hasattr(cap, 'value') else str(cap) for cap in metadata.capabilities],
                    "tags": list(metadata.tags) if hasattr(metadata, 'tags') else []
                })
                
                # Methods information
                if hasattr(metadata, 'methods'):
                    methods = {}
                    for method_name, method_schema in metadata.methods.items():
                        methods[method_name] = {
                            "description": method_schema.description,
                            "parameters": method_schema.parameters,
                            "returns": method_schema.returns
                        }
                    info["methods"] = methods
            
            # Check if tool has execution interface
            if hasattr(tool, 'execution'):
                info["execution_available"] = True
                try:
                    stats = tool.execution.get_statistics()
                    info["execution_stats"] = stats
                except:
                    info["execution_stats"] = "unavailable"
            
            return info
            
        except Exception as e:
            return {"error": f"Failed to inspect tool '{tool_name}': {e}"}
    
    async def list_capabilities(self) -> List[Dict[str, str]]:
        """List all tool capabilities available in the system"""
        try:
            from langswarm.tools.interfaces import ToolCapability
            capabilities = []
            
            for capability in ToolCapability:
                capabilities.append({
                    "name": capability.value,
                    "description": self._get_capability_description(capability.value)
                })
            
            return capabilities
        except Exception as e:
            return [{"error": f"Failed to list capabilities: {e}"}]
    
    def _get_capability_description(self, capability: str) -> str:
        """Get description for a capability"""
        descriptions = {
            "file_system": "File and directory operations",
            "network": "Network and HTTP operations", 
            "data_processing": "Data transformation and analysis",
            "ai_integration": "AI model and service integration",
            "database": "Database connectivity and operations",
            "api_integration": "External API integrations",
            "monitoring": "System monitoring and observability",
            "security": "Security and authentication operations",
            "workflow": "Workflow and automation capabilities",
            "communication": "Messaging and communication tools",
            "diagnostic": "System diagnostics and debugging",
            "introspection": "System introspection and reflection",
            "text_processing": "Text analysis and manipulation",
            "formatting": "Data formatting and presentation",
            "encoding": "Data encoding and decoding",
            "documentation": "Documentation generation and management",
            "data_access": "Data reading and writing operations"
        }
        return descriptions.get(capability, "No description available")
    
    async def tools_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find tools that have specific capabilities"""
        tools = await self.list_tools(include_metadata=True)
        matching_tools = []
        
        for tool in tools:
            tool_capabilities = tool.get("capabilities", [])
            if capability in tool_capabilities:
                matching_tools.append(tool)
        
        return matching_tools
    
    async def generate_docs(self, tool_names: Optional[List[str]] = None, format: str = "markdown") -> str:
        """Generate documentation for tools"""
        if tool_names:
            tools_to_doc = []
            for tool_name in tool_names:
                tool_info = await self.inspect_tool(tool_name)
                if "error" not in tool_info:
                    tools_to_doc.append(tool_info)
        else:
            tools_to_doc = await self.list_tools(include_metadata=True)
        
        if format == "json":
            return json.dumps(tools_to_doc, indent=2)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(tools_to_doc, default_flow_style=False)
            except ImportError:
                return "YAML format requires PyYAML library"
        else:  # markdown
            return self._generate_markdown_docs(tools_to_doc)
    
    def _generate_markdown_docs(self, tools: List[Dict[str, Any]]) -> str:
        """Generate markdown documentation"""
        docs = ["# LangSwarm V2 Tools Documentation", ""]
        
        for tool in tools:
            docs.append(f"## {tool.get('name', 'Unknown Tool')}")
            docs.append("")
            
            if "description" in tool:
                docs.append(f"**Description**: {tool['description']}")
                docs.append("")
            
            if "version" in tool:
                docs.append(f"**Version**: {tool['version']}")
            if "type" in tool:
                docs.append(f"**Type**: {tool['type']}")
            if "registry" in tool:
                docs.append(f"**Registry**: {tool['registry']}")
            docs.append("")
            
            if "capabilities" in tool:
                docs.append("**Capabilities**:")
                for cap in tool["capabilities"]:
                    docs.append(f"- {cap}")
                docs.append("")
            
            if "methods" in tool:
                docs.append("**Methods**:")
                for method_name, method_info in tool["methods"].items():
                    docs.append(f"### {method_name}")
                    docs.append(f"{method_info.get('description', 'No description')}")
                    docs.append("")
                    
                    if method_info.get("parameters"):
                        docs.append("**Parameters**:")
                        for param_name, param_info in method_info["parameters"].items():
                            param_type = param_info.get("type", "unknown")
                            required = " (required)" if param_info.get("required") else ""
                            docs.append(f"- `{param_name}` ({param_type}){required}: {param_info.get('description', 'No description')}")
                        docs.append("")
                    
                    if method_info.get("returns"):
                        docs.append(f"**Returns**: {method_info['returns']}")
                        docs.append("")
            
            docs.append("---")
            docs.append("")
        
        return "\n".join(docs)
    
    async def test_tool(self, tool_name: str) -> Dict[str, Any]:
        """Test if a tool is available and responsive"""
        try:
            from langswarm.tools import ServiceRegistry
            service_registry = ServiceRegistry()
            
            # Find the tool
            tool = None
            registry_name = None
            
            for reg_name, registry in service_registry._registries.items():
                try:
                    tool = registry.get_tool(tool_name)
                    if tool:
                        registry_name = reg_name
                        break
                except:
                    continue
            
            if not tool:
                return {
                    "tool_name": tool_name,
                    "available": False,
                    "error": "Tool not found in any registry"
                }
            
            # Test basic functionality
            result = {
                "tool_name": tool_name,
                "available": True,
                "registry": registry_name,
                "has_metadata": hasattr(tool, 'metadata'),
                "has_execution": hasattr(tool, 'execution'),
                "has_run_method": hasattr(tool, 'run')
            }
            
            # Test execution if available
            if hasattr(tool, 'execution'):
                try:
                    stats = tool.execution.get_statistics()
                    result["execution_stats"] = stats
                    result["execution_responsive"] = True
                except Exception as e:
                    result["execution_responsive"] = False
                    result["execution_error"] = str(e)
            
            return result
            
        except Exception as e:
            return {
                "tool_name": tool_name,
                "available": False,
                "error": f"Failed to test tool: {e}"
            }
    
    def run(self, input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        MCP-compatible run method
        """
        if input_data is None:
            input_data = kwargs
        
        method = input_data.get('method', 'list_tools')
        method_args = {k: v for k, v in input_data.items() if k != 'method'}
        
        if method == 'list_tools':
            return asyncio.run(self.list_tools(**method_args))
        elif method == 'inspect_tool':
            return asyncio.run(self.inspect_tool(**method_args))
        elif method == 'list_capabilities':
            return asyncio.run(self.list_capabilities(**method_args))
        elif method == 'tools_by_capability':
            return asyncio.run(self.tools_by_capability(**method_args))
        elif method == 'generate_docs':
            return asyncio.run(self.generate_docs(**method_args))
        elif method == 'test_tool':
            return asyncio.run(self.test_tool(**method_args))
        else:
            raise ValueError(f"Unknown method: {method}")
