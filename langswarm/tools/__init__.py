"""
LangSwarm V2 Unified Tool System

Modern tool system that unifies MCP, Synapse, Retrievers, and Plugins into 
a single, consistent MCP-based architecture with:

- Enhanced MCP standard compliance
- V2 error system integration  
- Async execution with V2 middleware compatibility
- Auto-discovery service registry
- Type-safe interfaces with rich metadata
- Backward compatibility with all existing tool types

Usage:
    from langswarm.tools import Tool, ToolRegistry, create_tool
    
    # Create a tool
    tool = create_tool("my_tool", "filesystem", config={"path": "/tmp"})
    
    # Register and use tools
    registry = ToolRegistry()
    registry.register(tool)
    
    result = await tool.execute("read_file", {"path": "test.txt"})
"""

from .interfaces import (
    IToolInterface,
    IToolMetadata,
    IToolRegistry,
    IToolExecution,
    ToolSchema,
    ToolType,
    ToolCapability
)

from .base import (
    BaseTool,
    ToolMetadata,
    ToolResult,
    ToolError as V2ToolError
)

from .registry import (
    ToolRegistry,
    ServiceRegistry,
    auto_discover_tools
)

from .execution import (
    ToolExecutor,
    ExecutionContext,
    ExecutionResult
)

from .adapters import (
    SynapseToolAdapter,
    RAGToolAdapter,
    PluginToolAdapter,
    LegacyToolAdapter,
    AdapterFactory
)

__all__ = [
    # Interfaces
    'IToolInterface',
    'IToolMetadata', 
    'IToolRegistry',
    'IToolExecution',
    'ToolSchema',
    'ToolType',
    'ToolCapability',
    
    # Base Implementation
    'BaseTool',
    'ToolMetadata',
    'ToolResult',
    'V2ToolError',
    
    # Registry
    'ToolRegistry',
    'ServiceRegistry',
    'auto_discover_tools',
    
    # Execution
    'ToolExecutor',
    'ExecutionContext',
    'ExecutionResult',
    
    # Compatibility
    'SynapseToolAdapter',
    'RAGToolAdapter', 
    'PluginToolAdapter',
    'LegacyToolAdapter',
    'AdapterFactory'
]
