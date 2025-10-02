# LangSwarm V2 Unified Tool System

**Single, consistent interface for all LangSwarm tools - MCP, Synapse, Retrievers, and Plugins unified**

## 🎯 Overview

LangSwarm V2 introduces a unified tool system that consolidates 4 different tool types (MCP, Synapse, Retrievers, Plugins) into a single, consistent MCP-based architecture. This eliminates complexity, improves developer experience, and provides consistent behavior across all tools.

**Key Benefits:**
- **Single Interface**: All tools use the same MCP-based interface
- **Auto-Discovery**: Automatic tool registration and dependency resolution
- **Unified Configuration**: Consistent configuration across all tool types
- **Enhanced Performance**: Async execution with V2 middleware integration
- **Backward Compatibility**: Existing tools continue working during migration

---

## 🔄 Tool System Evolution

### **Before V2: Fragmented Tool Types**

```
❌ 4 Different Tool Types:
├── MCP Tools (35+ tools)
│   ├── Interface: BaseMCPTool
│   ├── Registry: Manual registration
│   └── Execution: .run() method
├── Synapse Tools
│   ├── Interface: BaseTool
│   ├── Registry: Synapse registry
│   └── Execution: Direct methods
├── Retrievers (RAG)
│   ├── Interface: BaseRetriever
│   ├── Registry: RAG registry
│   └── Execution: .retrieve() method
└── Plugins
    ├── Interface: BasePlugin
    ├── Registry: Plugin registry
    └── Execution: .execute() method
```

**Problems:**
- ❌ Inconsistent interfaces and development patterns
- ❌ Different registration and discovery mechanisms
- ❌ Fragmented configuration and documentation
- ❌ Complex LLM integration with 4 different concepts

### **After V2: Unified MCP Architecture**

```
✅ Single Unified System:
langswarm/v2/tools/
├── Unified Interface: Enhanced MCP
├── Auto-Discovery Registry
├── Consistent Async Execution
├── V2 Error System Integration
├── V2 Middleware Integration
└── Backward Compatibility Adapters
```

**Benefits:**
- ✅ Single interface for all tools
- ✅ Consistent development patterns
- ✅ Unified auto-discovery system
- ✅ Simplified LLM integration
- ✅ Enhanced performance and reliability

---

## 🏗️ V2 Tool Architecture

### **Unified Tool Interface**

```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ErrorContext

class MyTool(UnifiedTool):
    """All tools inherit from UnifiedTool (enhanced MCP)"""
    
    def __init__(self, tool_id: str = "my_tool", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
    
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        """Unified async execution method for all tools"""
        try:
            # Your tool logic here
            result = await self._process_input(input_data)
            
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "tool_id": self.tool_id,
                    "execution_time": self.get_execution_time()
                }
            }
        except Exception as e:
            # V2 error handling integration
            return self.handle_error(e, context)
    
    async def _process_input(self, input_data: dict):
        """Tool-specific processing logic"""
        pass
```

### **Auto-Discovery Registry**

```python
from langswarm.tools import ToolRegistry

# Tools automatically register themselves
registry = ToolRegistry()

# Auto-discovery based on:
# 1. Installed packages
# 2. Environment capabilities
# 3. Configuration preferences
# 4. Dependency availability

discovered_tools = registry.discover_tools()
print(f"Found {len(discovered_tools)} available tools")

# Get tool by ID
tool = registry.get_tool("filesystem")
result = await tool.execute({"operation": "read_file", "path": "config.yaml"})
```

### **Unified Configuration**

```yaml
# Single, consistent configuration for all tools
tools:
  filesystem:
    type: "mcp"  # All tools are now MCP-based
    enabled: true
    config:
      base_path: "/safe/directory"
      read_only: false
  
  bigquery_search:
    type: "mcp"
    enabled: true
    config:
      project_id: "my-project"
      dataset: "search_data"
  
  # Legacy tools automatically converted
  custom_retriever:
    type: "mcp"  # Converted from retriever
    enabled: true
    legacy_type: "retriever"  # Tracks original type
    config:
      embedding_model: "text-embedding-3-small"
```

---

## 🔄 Migration from Legacy Tool Types

### **MCP Tools → Enhanced MCP**
**Status**: ✅ Direct migration (minimal changes)

```python
# V1 MCP Tool (minimal changes needed)
class FileSystemTool(BaseMCPTool):
    def run(self, input_data: dict) -> dict:
        return {"result": "file content"}

# V2 Enhanced MCP Tool
class FileSystemTool(UnifiedTool):
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        return {"result": "file content"}
```

### **Synapse Tools → MCP Tools**
**Status**: 🔄 Conversion in progress

```python
# V1 Synapse Tool
class SynapseTool(BaseTool):
    def process(self, data):
        return self.custom_method(data)

# V2 Unified Tool (converted)
class ConvertedSynapseTool(UnifiedTool):
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        result = await self._convert_synapse_logic(input_data)
        return {"success": True, "result": result}
    
    async def _convert_synapse_logic(self, data):
        # Converted from original Synapse logic
        return self.custom_method(data)
```

### **Retrievers → MCP Memory Tools**
**Status**: 🔄 Conversion in progress

```python
# V1 Retriever
class CustomRetriever(BaseRetriever):
    def retrieve(self, query: str, top_k: int = 5):
        return self.search_embeddings(query, top_k)

# V2 Memory Tool (converted)
class MemorySearchTool(UnifiedTool):
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        query = input_data.get("query")
        top_k = input_data.get("top_k", 5)
        
        results = await self._search_embeddings(query, top_k)
        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "count": len(results)
            }
        }
```

### **Plugins → MCP Utility Tools**
**Status**: 🔄 Conversion in progress

```python
# V1 Plugin
class UtilityPlugin(BasePlugin):
    def execute(self, operation: str, params: dict):
        return getattr(self, operation)(params)

# V2 Utility Tool (converted)
class UtilityTool(UnifiedTool):
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        operation = input_data.get("operation")
        params = input_data.get("params", {})
        
        if hasattr(self, f"_{operation}"):
            result = await getattr(self, f"_{operation}")(params)
            return {"success": True, "result": result}
        else:
            raise ValueError(f"Unknown operation: {operation}")
```

---

## 🔧 Compatibility Adapters

V2 provides compatibility adapters to ensure legacy tools continue working during migration:

### **Synapse Tool Adapter**

```python
from langswarm.tools.adapters import SynapseToolAdapter

# Automatically wraps V1 Synapse tools
class LegacySynapseTool(BaseTool):
    def process(self, data):
        return "legacy result"

# V2 automatically creates adapter
adapted_tool = SynapseToolAdapter(LegacySynapseTool())

# Works with V2 interface
result = await adapted_tool.execute({"data": "input"})
```

### **Retriever Adapter**

```python
from langswarm.tools.adapters import RetrieverAdapter

# Automatically wraps V1 retrievers
legacy_retriever = CustomRetriever()
adapted_tool = RetrieverAdapter(legacy_retriever)

# V2 interface
result = await adapted_tool.execute({
    "query": "search query",
    "top_k": 5
})
```

### **Plugin Adapter**

```python
from langswarm.tools.adapters import PluginAdapter

# Automatically wraps V1 plugins
legacy_plugin = UtilityPlugin()
adapted_tool = PluginAdapter(legacy_plugin)

# V2 interface
result = await adapted_tool.execute({
    "operation": "process_data",
    "params": {"data": "input"}
})
```

---

## 📊 Tool Discovery and Registration

### **Automatic Tool Discovery**

```python
from langswarm.tools import ToolRegistry

registry = ToolRegistry()

# Discover tools from multiple sources
discovered = registry.discover_tools(sources=[
    "installed_packages",    # pip-installed tool packages
    "local_directory",      # ./tools/ directory
    "environment",          # Environment-based tools (Docker, etc.)
    "configuration"         # Explicitly configured tools
])

# Discovery results
print(f"Found tools:")
for tool in discovered:
    print(f"  {tool.id}: {tool.type} ({tool.source})")
```

### **Tool Dependencies**

```python
# Tools can declare dependencies
class DatabaseTool(UnifiedTool):
    dependencies = ["postgresql", "redis"]  # External dependencies
    tool_dependencies = ["filesystem"]      # Other LangSwarm tools
    
    async def execute(self, input_data: dict, context: ErrorContext = None):
        # Automatically checked before execution
        filesystem_tool = self.get_dependency("filesystem")
        config = await filesystem_tool.execute({"operation": "read_config"})
        # ... use config for database operations
```

### **Tool Metadata**

```python
class MyTool(UnifiedTool):
    """Tools include rich metadata for discovery and LLM integration"""
    
    metadata = {
        "name": "My Custom Tool",
        "description": "Performs custom operations",
        "version": "1.0.0",
        "author": "Developer Name",
        "capabilities": [
            "data_processing",
            "file_operations",
            "api_integration"
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["process", "analyze"]},
                "data": {"type": "string"}
            },
            "required": ["operation", "data"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
    }
```

---

## 🎯 LLM Integration

### **Unified Tool Interface for LLM**

The V2 system presents a single, consistent interface to LLMs:

```json
{
  "response": "I'll help you with that file operation.",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "config.yaml"}
  }
}
```

**All tools use the same pattern:**
- `tool`: The tool identifier
- `method`: The operation to perform
- `params`: The parameters for the operation

### **System Prompt Integration**

```markdown
## Available Tools

You have access to a unified tool system with consistent interfaces:

### Tool Execution Pattern
Always use this format for tool calls:
{
  "response": "I'll [action description]",
  "mcp": {
    "tool": "tool_name",
    "method": "operation_name",
    "params": {"param1": "value1"}
  }
}

### Available Tools:
- **filesystem**: File operations (read, write, list, delete)
- **bigquery_search**: Vector similarity search in BigQuery
- **github**: Repository operations (issues, PRs, code search)
- **memory_search**: Semantic search through conversation history
- **workflow_executor**: Execute complex multi-step workflows

Each tool provides consistent async execution with comprehensive error handling.
```

---

## 🚀 Performance Improvements

### **Async Execution**

```python
# V1: Synchronous execution
result1 = tool1.run(data1)
result2 = tool2.run(data2)
result3 = tool3.run(data3)

# V2: Concurrent async execution
import asyncio

async def execute_tools():
    results = await asyncio.gather(
        tool1.execute(data1),
        tool2.execute(data2),
        tool3.execute(data3)
    )
    return results
```

### **Tool Caching**

```python
from langswarm.tools import ToolRegistry

# Tools automatically cached for performance
registry = ToolRegistry(cache_tools=True)

# First call: tool instantiated and cached
tool = registry.get_tool("filesystem")

# Subsequent calls: returned from cache
cached_tool = registry.get_tool("filesystem")  # Same instance
```

### **Lazy Loading**

```python
# Tools loaded on-demand rather than at startup
registry = ToolRegistry(lazy_loading=True)

# Tool only loaded when first accessed
tool = registry.get_tool("bigquery_search")  # Loads tool now
```

---

## 🔧 Development Experience

### **Tool Development Template**

```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ErrorContext, ToolError

class NewTool(UnifiedTool):
    """Template for creating new V2 tools"""
    
    metadata = {
        "name": "New Tool",
        "description": "Description of what this tool does",
        "version": "1.0.0",
        "capabilities": ["capability1", "capability2"]
    }
    
    def __init__(self, tool_id: str = "new_tool", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
        # Tool-specific initialization
    
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        """Main execution method"""
        try:
            # Validate input
            self._validate_input(input_data)
            
            # Execute operation
            result = await self._perform_operation(input_data)
            
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "tool_id": self.tool_id,
                    "execution_time": self.get_execution_time()
                }
            }
            
        except Exception as e:
            return self._handle_error(e, context)
    
    def _validate_input(self, input_data: dict):
        """Validate input parameters"""
        required_fields = ["operation"]
        for field in required_fields:
            if field not in input_data:
                raise ToolError(f"Missing required field: {field}")
    
    async def _perform_operation(self, input_data: dict):
        """Perform the actual tool operation"""
        operation = input_data["operation"]
        
        if operation == "example":
            return await self._example_operation(input_data)
        else:
            raise ToolError(f"Unknown operation: {operation}")
    
    async def _example_operation(self, input_data: dict):
        """Example operation implementation"""
        return {"message": "Operation completed successfully"}
```

### **Tool Testing**

```python
import pytest
from langswarm.tools.testing import ToolTestCase

class TestNewTool(ToolTestCase):
    """Test framework for V2 tools"""
    
    async def test_tool_execution(self):
        tool = NewTool()
        
        result = await tool.execute({
            "operation": "example",
            "data": "test data"
        })
        
        assert result["success"] is True
        assert "result" in result
        assert result["metadata"]["tool_id"] == "new_tool"
    
    async def test_error_handling(self):
        tool = NewTool()
        
        result = await tool.execute({})  # Missing required fields
        
        assert result["success"] is False
        assert "error" in result
```

---

## 📚 Migration Guide

### **For Tool Developers**

1. **Assess Current Tools**: Identify which tool type you're using
2. **Choose Migration Path**: 
   - MCP tools: Minimal changes needed
   - Other types: Convert to MCP pattern
3. **Use Compatibility Adapters**: For gradual migration
4. **Test Thoroughly**: Ensure functionality preserved
5. **Update Documentation**: Use V2 documentation standards

### **For Users**

1. **No Immediate Changes**: Existing configurations continue working
2. **Optional Enhancement**: Gradually adopt V2 configuration patterns
3. **Tool Discovery**: Enable auto-discovery for better experience
4. **Monitor Migration**: Track tool conversion progress

---

## 🎯 Success Metrics

### **Unified Architecture Achievements**
- **4 → 1**: Tool types reduced from 4 to 1 (MCP-based)
- **Consistent Interface**: All tools use same execution pattern
- **Auto-Discovery**: Automatic tool registration and dependency resolution
- **Backward Compatibility**: 100% compatibility with existing tools
- **Performance**: Async execution with caching and lazy loading

### **Developer Experience Improvements**
- **Single Learning Curve**: One tool development pattern to learn
- **Consistent Testing**: Same testing patterns for all tools
- **Unified Documentation**: Single documentation structure
- **Enhanced Debugging**: V2 error system and middleware integration

### **User Experience Benefits**
- **Simplified Configuration**: Single tool configuration format
- **Consistent Behavior**: All tools behave consistently
- **Better Error Messages**: V2 error system integration
- **Improved Performance**: Async execution and optimization

---

**The LangSwarm V2 Unified Tool System simplifies tool development, improves performance, and provides a consistent experience while maintaining full backward compatibility with existing tools.**
