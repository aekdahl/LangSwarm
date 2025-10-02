"""
Standard MCP Protocol Interface

This module defines the standard MCP protocol methods that all MCP tools should implement
for compatibility with standard MCP clients and tooling.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from enum import Enum
import json
import os
import yaml


class ToolInfo(BaseModel):
    """Information about an available tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None


class PromptInfo(BaseModel):
    """Information about an available prompt"""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = []


class ResourceInfo(BaseModel):
    """Information about an available resource"""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = None


class ToolResult(BaseModel):
    """Result from a tool execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PromptResult(BaseModel):
    """Result from a prompt request"""
    name: str
    description: str
    content: str
    arguments_used: Dict[str, Any] = {}


class ResourceContent(BaseModel):
    """Content from a resource"""
    uri: str
    content: str
    mime_type: Optional[str] = None
    size: Optional[int] = None


class StandardMCPProtocol(ABC):
    """Abstract interface for standard MCP protocol methods"""
    
    @abstractmethod
    async def list_tools(self) -> List[ToolInfo]:
        """List all available tools with their schemas"""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a specific tool with given arguments"""
        pass
    
    @abstractmethod
    async def list_prompts(self) -> List[PromptInfo]:
        """List all available prompts"""
        pass
    
    @abstractmethod
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> PromptResult:
        """Get a formatted prompt with substituted variables"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[ResourceInfo]:
        """List all available resources (files, URIs, etc.)"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> ResourceContent:
        """Read content from a specific resource"""
        pass


class MCPProtocolMixin:
    """
    Mixin class that provides standard MCP protocol methods for any MCP tool.
    
    This class should be mixed into existing MCP tool classes to add protocol compliance
    without breaking existing functionality.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tool_directory = self._get_tool_directory()
        self._cached_prompts = None
        self._cached_resources = None
    
    def _get_tool_directory(self) -> str:
        """Get the directory containing this tool's files"""
        # Try to infer from the class module
        import inspect
        module = inspect.getmodule(self.__class__)
        if module and hasattr(module, '__file__'):
            return os.path.dirname(module.__file__)
        return os.getcwd()
    
    # ===============================
    # TOOL MANAGEMENT METHODS
    # ===============================
    
    async def list_tools(self) -> List[ToolInfo]:
        """List all available tools with their schemas"""
        tools = []
        
        # Get tools from the class methods
        tool_methods = self._discover_tool_methods()
        
        for method_name, method_info in tool_methods.items():
            tools.append(ToolInfo(
                name=method_name,
                description=method_info.get('description', f'{method_name} operation'),
                input_schema=method_info.get('input_schema', {"type": "object", "properties": {}}),
                output_schema=method_info.get('output_schema')
            ))
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a specific tool with given arguments.
        
        Supports:
        1. Intent-based calling (LangSwarm USP): {"intent": "...", "context": "..."}
        2. Flattened method calling: name="tool.method", arguments={...}
        3. Direct method calling: {"method": "...", "params": {...}}
        """
        try:
            # Handle flattened method calling (LLM-friendly): tool.method
            if "." in name:
                return await self._handle_flattened_method_call(name, arguments)
            
            # Check if this is intent-based calling (LangSwarm USP)
            elif "intent" in arguments:
                return await self._handle_intent_based_call(name, arguments)
            
            # Check if this is direct method calling
            elif "method" in arguments and "params" in arguments:
                return await self._handle_direct_method_call(name, arguments)
            
            # Try direct method call on the tool
            elif hasattr(self, name) and callable(getattr(self, name)):
                method = getattr(self, name)
                result = await self._execute_method(method, arguments)
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={"tool_name": name, "method": "direct_call", "call_type": "direct_tool_method"}
                )
            
            # Fall back to run method with method specification
            elif hasattr(self, 'run'):
                # Try different input formats for run method
                input_formats = [
                    {"method": name, "params": arguments},  # Structured format
                    {name: arguments},  # Method as key format
                    arguments  # Direct arguments
                ]
                
                for input_data in input_formats:
                    try:
                        result = await self._execute_method(self.run, input_data)
                        break
                    except TypeError as e:
                        if "unexpected keyword argument" in str(e):
                            continue
                        else:
                            raise
                else:
                    # If all formats failed, raise the last error
                    raise TypeError(f"Could not call run method for tool '{name}'")
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={"tool_name": name, "method": "run_method", "call_type": "fallback"}
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Tool '{name}' not found",
                    metadata={"tool_name": name, "available_methods": list(self._discover_tool_methods().keys())}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool_name": name, "error_type": type(e).__name__}
            )
    
    async def _handle_intent_based_call(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Handle intent-based calling using REAL agent workflows (LangSwarm USP)"""
        intent = arguments.get("intent", "")
        context = arguments.get("context", "")
        
        # Check if tool has agent workflow capability
        if hasattr(self, '_handle_intent_call') and callable(getattr(self, '_handle_intent_call')):
            try:
                # Use the tool's sophisticated agent workflow system
                result = await self._handle_intent_call({
                    "intent": intent,
                    "context": context
                })
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": name, 
                        "method": "_handle_intent_call", 
                        "call_type": "intent_via_agent_workflow",
                        "intent": intent[:100] + "..." if len(intent) > 100 else intent
                    }
                )
            except Exception as e:
                # Fall through to run_async method
                pass
        
        # Fallback: Use run_async method with intent parameters
        if hasattr(self, 'run_async'):
            try:
                result = await self.run_async({
                    "intent": intent,
                    "context": context
                })
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": name, 
                        "method": "run_async", 
                        "call_type": "intent_via_run_async_fallback",
                        "intent": intent[:100] + "..." if len(intent) > 100 else intent
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Intent-based call failed: {str(e)}",
                    metadata={"tool_name": name, "call_type": "intent_based", "error": str(e)}
                )
        
        return ToolResult(
            success=False,
            error=f"Tool '{name}' does not support intent-based calling",
            metadata={"tool_name": name, "call_type": "intent_based"}
        )
    
    async def _handle_direct_method_call(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Handle direct method calling with method and params"""
        method_name = arguments.get("method", "")
        params = arguments.get("params", {})
        
        # Try to call the specific method directly
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            try:
                method = getattr(self, method_name)
                result = await self._execute_method(method, **params)
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": name, 
                        "method": method_name, 
                        "call_type": "direct_method"
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Direct method call failed: {str(e)}",
                    metadata={"tool_name": name, "method": method_name, "call_type": "direct_method"}
                )
        
        # Fallback: Use run_async method with method specification
        if hasattr(self, 'run_async'):
            try:
                result = await self.run_async({
                    "method": method_name,
                    "params": params
                })
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": name, 
                        "method": method_name, 
                        "call_type": "direct_via_run_async"
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Direct method call via run failed: {str(e)}",
                    metadata={"tool_name": name, "method": method_name, "call_type": "direct_via_run"}
                )
        
        return ToolResult(
            success=False,
            error=f"Method '{method_name}' not found on tool '{name}'",
            metadata={"tool_name": name, "method": method_name, "call_type": "direct_method"}
        )
    
    async def _handle_flattened_method_call(self, flattened_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Handle flattened method calling (LLM-friendly): tool.method"""
        if "." not in flattened_name:
            return ToolResult(
                success=False,
                error=f"Invalid flattened name format: '{flattened_name}' (expected: tool.method)",
                metadata={"flattened_name": flattened_name, "call_type": "flattened_method"}
            )
        
        # Parse tool.method format
        parts = flattened_name.split(".", 1)
        tool_name = parts[0]
        method_name = parts[1]
        
        # Verify this is the correct tool
        if hasattr(self, 'identifier') and self.identifier != tool_name:
            return ToolResult(
                success=False,
                error=f"Tool mismatch: expected '{self.identifier}', got '{tool_name}'",
                metadata={"expected_tool": getattr(self, 'identifier', 'unknown'), "requested_tool": tool_name, "call_type": "flattened_method"}
            )
        
        # Try to call the specific method directly
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            try:
                method = getattr(self, method_name)
                result = await self._execute_method(method, **arguments)
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": tool_name, 
                        "method": method_name, 
                        "call_type": "flattened_direct",
                        "flattened_name": flattened_name
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Flattened method call failed: {str(e)}",
                    metadata={"tool_name": tool_name, "method": method_name, "call_type": "flattened_direct", "flattened_name": flattened_name}
                )
        
        # Fallback: Use run_async method with method specification
        if hasattr(self, 'run_async'):
            try:
                result = await self.run_async({
                    "method": method_name,
                    "params": arguments
                })
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": tool_name, 
                        "method": method_name, 
                        "call_type": "flattened_via_run_async",
                        "flattened_name": flattened_name
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Flattened method call via run_async failed: {str(e)}",
                    metadata={"tool_name": tool_name, "method": method_name, "call_type": "flattened_via_run_async", "flattened_name": flattened_name}
                )
        
        return ToolResult(
            success=False,
            error=f"Method '{method_name}' not found on tool '{tool_name}' and no run_async fallback",
            metadata={"tool_name": tool_name, "method": method_name, "call_type": "flattened_method", "flattened_name": flattened_name}
        )
    
    def _discover_tool_methods(self) -> Dict[str, Dict[str, Any]]:
        """Discover available tool methods from the class"""
        methods = {}
        
        # Check if we have a tasks registry (from BaseMCPToolServer)
        if hasattr(self, '_tasks') and self._tasks:
            for task_name, task_info in self._tasks.items():
                methods[task_name] = {
                    'description': task_info.get('description', ''),
                    'input_schema': self._get_input_schema_from_model(task_info.get('input_model')),
                    'output_schema': self._get_output_schema_from_model(task_info.get('output_model'))
                }
        
        # Also check for common method patterns
        common_methods = ['similarity_search', 'list_datasets', 'get_content', 'execute_query', 'get_database_info']
        for method_name in common_methods:
            if hasattr(self, method_name) and method_name not in methods:
                methods[method_name] = {
                    'description': f'{method_name.replace("_", " ").title()} operation',
                    'input_schema': {"type": "object", "properties": {}}
                }
        
        # If no methods found, provide run method
        if not methods and hasattr(self, 'run'):
            methods['run'] = {
                'description': 'Main tool execution method',
                'input_schema': {"type": "object", "properties": {}}
            }
        
        return methods
    
    def _get_input_schema_from_model(self, model_class) -> Dict[str, Any]:
        """Extract JSON schema from Pydantic model"""
        if model_class and hasattr(model_class, 'model_json_schema'):
            return model_class.model_json_schema()
        return {"type": "object", "properties": {}}
    
    def _get_output_schema_from_model(self, model_class) -> Optional[Dict[str, Any]]:
        """Extract JSON schema from Pydantic model"""
        if model_class and hasattr(model_class, 'model_json_schema'):
            return model_class.model_json_schema()
        return None
    
    async def _execute_method(self, method, arguments):
        """Execute method handling both sync and async"""
        import asyncio
        import inspect
        
        if inspect.iscoroutinefunction(method):
            if isinstance(arguments, dict):
                return await method(**arguments)
            else:
                return await method(arguments)
        else:
            if isinstance(arguments, dict):
                return method(**arguments)
            else:
                return method(arguments)
    
    # ===============================
    # PROMPT MANAGEMENT METHODS
    # ===============================
    
    async def list_prompts(self) -> List[PromptInfo]:
        """List all available prompts from agents.yaml"""
        if self._cached_prompts is None:
            self._cached_prompts = self._load_prompts()
        
        prompts = []
        for prompt_name, prompt_data in self._cached_prompts.items():
            prompts.append(PromptInfo(
                name=prompt_name,
                description=prompt_data.get('description', f'Agent prompt for {prompt_name}'),
                arguments=prompt_data.get('arguments', [])
            ))
        
        return prompts
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> PromptResult:
        """Get a formatted prompt with substituted variables"""
        if self._cached_prompts is None:
            self._cached_prompts = self._load_prompts()
        
        if name not in self._cached_prompts:
            raise ValueError(f"Prompt '{name}' not found. Available prompts: {list(self._cached_prompts.keys())}")
        
        prompt_data = self._cached_prompts[name]
        content = prompt_data.get('system_prompt', '')
        
        # Simple template substitution
        if arguments:
            for key, value in arguments.items():
                content = content.replace(f'{{{key}}}', str(value))
                content = content.replace(f'${{{key}}}', str(value))
        
        return PromptResult(
            name=name,
            description=prompt_data.get('description', f'Agent prompt for {name}'),
            content=content,
            arguments_used=arguments or {}
        )
    
    def _load_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Load prompts from agents.yaml"""
        agents_file = os.path.join(self._tool_directory, "agents.yaml")
        if not os.path.exists(agents_file):
            return {}
        
        try:
            with open(agents_file, 'r') as f:
                agents_data = yaml.safe_load(f)
            
            prompts = {}
            for agent in agents_data.get('agents', []):
                agent_id = agent.get('id', 'unknown')
                prompts[agent_id] = {
                    'description': f"Agent prompt for {agent_id}",
                    'system_prompt': agent.get('system_prompt', ''),
                    'arguments': []  # Could be extracted from prompt template
                }
            
            return prompts
        except Exception as e:
            print(f"Warning: Could not load prompts from {agents_file}: {e}")
            return {}
    
    # ===============================
    # RESOURCE MANAGEMENT METHODS
    # ===============================
    
    async def list_resources(self) -> List[ResourceInfo]:
        """List all available resources (files, URIs, etc.)"""
        if self._cached_resources is None:
            self._cached_resources = self._discover_resources()
        
        return self._cached_resources
    
    async def read_resource(self, uri: str) -> ResourceContent:
        """Read content from a specific resource"""
        if uri.startswith("file://"):
            file_path = uri[7:]  # Remove file:// prefix
            if not os.path.isabs(file_path):
                file_path = os.path.join(self._tool_directory, file_path)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Resource not found: {uri}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return ResourceContent(
                uri=uri,
                content=content,
                mime_type=self._get_mime_type(file_path),
                size=len(content)
            )
        
        else:
            raise ValueError(f"Unsupported URI scheme: {uri}")
    
    def _discover_resources(self) -> List[ResourceInfo]:
        """Discover resources in the tool directory"""
        resources = []
        
        # Standard tool files
        standard_files = {
            'template.md': 'Tool instructions for LLM',
            'agents.yaml': 'Agent configurations',
            'workflows.yaml': 'Workflow definitions',
            'readme.md': 'Human-readable documentation'
        }
        
        for filename, description in standard_files.items():
            file_path = os.path.join(self._tool_directory, filename)
            if os.path.exists(file_path):
                resources.append(ResourceInfo(
                    uri=f"file://{filename}",
                    name=filename.replace('.', '_'),
                    description=description,
                    mime_type=self._get_mime_type(file_path)
                ))
        
        return resources
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for a file"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.md': 'text/markdown',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.py': 'text/x-python'
        }
        return mime_types.get(ext, 'text/plain')


class StandardMCPToolServer(MCPProtocolMixin):
    """
    A complete MCP tool server that implements the standard protocol.
    
    This can be used as a base class for new tools or mixed into existing tools.
    """
    
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description
        super().__init__(**kwargs)
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get information about this MCP server"""
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "protocol_version": "2024-11-05"
        }
