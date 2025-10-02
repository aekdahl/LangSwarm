# LangSwarm V1 to V2 Tool Migration Guide

**Complete guide for migrating from V1's fragmented tool system to V2's unified MCP architecture**

## 🎯 Overview

LangSwarm V2 unifies 4 different tool types (MCP, Synapse, Retrievers, Plugins) into a single, consistent MCP-based architecture. This guide helps you migrate your tools and tool usage from V1 to V2.

**Migration Benefits:**
- **Single Interface**: All tools use the same MCP-based pattern
- **Auto-Discovery**: Automatic tool registration and detection
- **Better Performance**: Async execution with optimization
- **Consistent Development**: Same patterns for all tool types
- **Backward Compatibility**: V1 tools continue working during migration

---

## 🔄 Migration Strategy

### **Phase 1: Compatibility (No Changes Required)**
V2 maintains full backward compatibility - your existing tools and configurations continue working unchanged.

```python
# Your existing V1 tool usage works without changes
from langswarm import SomeV1Tool

tool = SomeV1Tool()
result = tool.run(input_data)  # Still works in V2
```

### **Phase 2: Enhanced Usage (Optional)**
Gradually adopt V2 patterns for better performance and features.

```python
# Enhanced V2 usage with async execution
from langswarm.tools import get_tool

tool = get_tool("some_tool")  # Auto-discovery
result = await tool.execute(input_data)  # Async execution
```

### **Phase 3: Full V2 Migration (Recommended)**
Migrate to V2 unified architecture for optimal experience.

```python
from langswarm.tools import UnifiedTool

class MyV2Tool(UnifiedTool):
    async def execute(self, input_data: dict, context = None) -> dict:
        # V2 unified interface
        return {"success": True, "result": "data"}
```

---

## 📊 Tool Type Migration Mapping

### **V1 Tool Types → V2 Unified System**

| V1 Tool Type | V1 Interface | V2 Migration Path | Complexity |
|--------------|--------------|-------------------|------------|
| **MCP Tools** | `BaseMCPTool` | ✅ Direct (minimal changes) | Low |
| **Synapse Tools** | `BaseTool` | 🔄 Convert to MCP | Medium |
| **Retrievers** | `BaseRetriever` | 🔄 Convert to MCP Memory Tools | Medium |
| **Plugins** | `BasePlugin` | 🔄 Convert to MCP Utility Tools | Medium |

### **Migration Complexity Assessment**

#### **Low Complexity: MCP Tools (35+ tools)**
- **Existing Pattern**: Already follows MCP standards
- **Changes Required**: Minimal (mainly async support)
- **Timeline**: 1-2 days per tool
- **Risk**: Very Low

#### **Medium Complexity: Synapse Tools**
- **Existing Pattern**: Custom tool interface
- **Changes Required**: Convert to MCP pattern, async execution
- **Timeline**: 2-3 days per tool
- **Risk**: Low (well-isolated functionality)

#### **Medium Complexity: Retrievers**
- **Existing Pattern**: RAG-focused interface
- **Changes Required**: Convert to MCP memory/search tools
- **Timeline**: 2-3 days per tool
- **Risk**: Medium (memory system integration)

#### **Medium Complexity: Plugins**
- **Existing Pattern**: Workflow utility interface
- **Changes Required**: Convert to MCP utility tools
- **Timeline**: 2-3 days per tool
- **Risk**: Low (utility functions are self-contained)

---

## 🛠️ Detailed Migration Steps

### **MCP Tools → Enhanced MCP Tools**

#### **Current V1 MCP Tool**
```python
from langswarm.synapse.tools.base import BaseTool

class FileSystemMCPTool(BaseTool):
    _bypass_pydantic = True
    
    def __init__(self, tool_id: str = "filesystem", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
    
    def run(self, input_data: dict) -> dict:
        try:
            operation = input_data.get("operation")
            if operation == "read_file":
                return self._read_file(input_data)
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _read_file(self, input_data: dict):
        path = input_data.get("path")
        with open(path, 'r') as f:
            content = f.read()
        return {"success": True, "content": content}
```

#### **V2 Enhanced MCP Tool**
```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ToolError, ErrorContext

class FileSystemTool(UnifiedTool):
    """V2 enhanced MCP tool with async execution and error integration"""
    
    metadata = {
        "name": "Filesystem Tool",
        "description": "File operations with V2 enhancements",
        "version": "2.0.0",
        "capabilities": ["file_read", "file_write", "directory_list"]
    }
    
    def __init__(self, tool_id: str = "filesystem", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
    
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        """V2 unified async execution method"""
        try:
            # Input validation with V2 error system
            self._validate_input(input_data)
            
            operation = input_data.get("operation")
            if operation == "read_file":
                result = await self._read_file_async(input_data)
            else:
                raise ToolError(
                    message=f"Unknown operation: {operation}",
                    suggestion="Use 'read_file', 'write_file', or 'list_directory'",
                    context=context
                )
            
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
        """Enhanced input validation"""
        if "operation" not in input_data:
            raise ToolError("Missing required parameter: operation")
    
    async def _read_file_async(self, input_data: dict):
        """Async file reading with enhanced error handling"""
        import aiofiles
        
        path = input_data.get("path")
        if not path:
            raise ToolError("Missing required parameter: path")
        
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
            return {"content": content, "size": len(content)}
        except FileNotFoundError:
            raise ToolError(
                message=f"File not found: {path}",
                suggestion="Check that the file path is correct and the file exists"
            )
```

**Migration Changes:**
- ✅ `run()` → `execute()` (async)
- ✅ Enhanced error handling with V2 error system
- ✅ Added metadata for auto-discovery
- ✅ Async file operations for better performance
- ✅ Structured response format

### **Synapse Tools → MCP Tools**

#### **Current V1 Synapse Tool**
```python
from langswarm.synapse.tools.base import BaseTool

class DataProcessorTool(BaseTool):
    def process_data(self, data: str, operation: str) -> dict:
        if operation == "uppercase":
            return {"result": data.upper()}
        elif operation == "lowercase":
            return {"result": data.lower()}
        else:
            return {"error": "Unknown operation"}
    
    def analyze_data(self, data: str) -> dict:
        return {
            "length": len(data),
            "word_count": len(data.split()),
            "uppercase_count": sum(1 for c in data if c.isupper())
        }
```

#### **V2 MCP Tool (Converted)**
```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ToolError

class DataProcessorTool(UnifiedTool):
    """Converted Synapse tool to V2 MCP format"""
    
    metadata = {
        "name": "Data Processor",
        "description": "Text data processing and analysis",
        "version": "2.0.0",
        "capabilities": ["text_processing", "text_analysis"],
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["process", "analyze"]},
                "data": {"type": "string"},
                "sub_operation": {"type": "string", "enum": ["uppercase", "lowercase"]}
            },
            "required": ["operation", "data"]
        }
    }
    
    async def execute(self, input_data: dict, context = None) -> dict:
        try:
            operation = input_data.get("operation")
            data = input_data.get("data")
            
            if not data:
                raise ToolError("Missing required parameter: data")
            
            if operation == "process":
                result = await self._process_data(data, input_data.get("sub_operation", "uppercase"))
            elif operation == "analyze":
                result = await self._analyze_data(data)
            else:
                raise ToolError(f"Unknown operation: {operation}")
            
            return {
                "success": True,
                "result": result,
                "metadata": {"tool_id": self.tool_id}
            }
            
        except Exception as e:
            return self._handle_error(e, context)
    
    async def _process_data(self, data: str, sub_operation: str) -> dict:
        """Converted from original process_data method"""
        if sub_operation == "uppercase":
            return {"processed_data": data.upper(), "operation": "uppercase"}
        elif sub_operation == "lowercase":
            return {"processed_data": data.lower(), "operation": "lowercase"}
        else:
            raise ToolError(f"Unknown sub-operation: {sub_operation}")
    
    async def _analyze_data(self, data: str) -> dict:
        """Converted from original analyze_data method"""
        return {
            "analysis": {
                "length": len(data),
                "word_count": len(data.split()),
                "uppercase_count": sum(1 for c in data if c.isupper()),
                "lowercase_count": sum(1 for c in data if c.islower())
            }
        }
```

**Migration Changes:**
- ✅ Combined multiple methods into single `execute()` method
- ✅ Added operation routing via input parameters
- ✅ Enhanced with V2 error handling and metadata
- ✅ Structured input/output schemas
- ✅ Async execution support

### **Retrievers → MCP Memory Tools**

#### **Current V1 Retriever**
```python
from langswarm.memory.base import BaseRetriever

class CustomRetriever(BaseRetriever):
    def __init__(self, embedding_model="text-embedding-3-small"):
        self.embedding_model = embedding_model
        self.documents = []
    
    def add_documents(self, documents: list):
        self.documents.extend(documents)
    
    def retrieve(self, query: str, top_k: int = 5) -> list:
        # Simple similarity search (placeholder)
        scores = []
        for i, doc in enumerate(self.documents):
            score = self._calculate_similarity(query, doc)
            scores.append((score, i, doc))
        
        scores.sort(reverse=True)
        return [{"document": doc, "score": score} for score, i, doc in scores[:top_k]]
    
    def _calculate_similarity(self, query: str, document: str) -> float:
        # Placeholder similarity calculation
        return len(set(query.lower().split()) & set(document.lower().split()))
```

#### **V2 MCP Memory Tool (Converted)**
```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ToolError

class MemorySearchTool(UnifiedTool):
    """Converted retriever to V2 MCP memory tool"""
    
    metadata = {
        "name": "Memory Search Tool",
        "description": "Semantic search through stored documents and conversations",
        "version": "2.0.0",
        "capabilities": ["memory_search", "document_storage", "similarity_search"],
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["search", "add_documents", "list_documents"]},
                "query": {"type": "string"},
                "documents": {"type": "array", "items": {"type": "string"}},
                "top_k": {"type": "integer", "default": 5}
            }
        }
    }
    
    def __init__(self, tool_id: str = "memory_search", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        self.documents = []
    
    async def execute(self, input_data: dict, context = None) -> dict:
        try:
            operation = input_data.get("operation")
            
            if operation == "search":
                result = await self._search_documents(input_data)
            elif operation == "add_documents":
                result = await self._add_documents(input_data)
            elif operation == "list_documents":
                result = await self._list_documents()
            else:
                raise ToolError(f"Unknown operation: {operation}")
            
            return {
                "success": True,
                "result": result,
                "metadata": {"tool_id": self.tool_id, "document_count": len(self.documents)}
            }
            
        except Exception as e:
            return self._handle_error(e, context)
    
    async def _search_documents(self, input_data: dict) -> dict:
        """Converted from original retrieve method"""
        query = input_data.get("query")
        top_k = input_data.get("top_k", 5)
        
        if not query:
            raise ToolError("Missing required parameter: query")
        
        # Enhanced similarity search with async processing
        scores = []
        for i, doc in enumerate(self.documents):
            score = await self._calculate_similarity_async(query, doc)
            scores.append({"score": score, "index": i, "document": doc})
        
        scores.sort(key=lambda x: x["score"], reverse=True)
        results = scores[:top_k]
        
        return {
            "query": query,
            "results": results,
            "total_searched": len(self.documents),
            "returned": len(results)
        }
    
    async def _add_documents(self, input_data: dict) -> dict:
        """Enhanced document addition"""
        documents = input_data.get("documents", [])
        if not documents:
            raise ToolError("Missing required parameter: documents")
        
        self.documents.extend(documents)
        return {
            "added_count": len(documents),
            "total_documents": len(self.documents)
        }
    
    async def _list_documents(self) -> dict:
        """List all stored documents"""
        return {
            "documents": self.documents,
            "count": len(self.documents)
        }
    
    async def _calculate_similarity_async(self, query: str, document: str) -> float:
        """Async similarity calculation"""
        # Enhanced similarity calculation
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        intersection = query_words & doc_words
        union = query_words | doc_words
        return len(intersection) / len(union) if union else 0.0
```

**Migration Changes:**
- ✅ `retrieve()` → `execute()` with operation routing
- ✅ Added document management operations
- ✅ Enhanced with metadata and structured responses
- ✅ Async processing for better performance
- ✅ V2 error handling integration

### **Plugins → MCP Utility Tools**

#### **Current V1 Plugin**
```python
from langswarm.cortex.base import BasePlugin

class UtilityPlugin(BasePlugin):
    def format_json(self, data: dict) -> str:
        import json
        return json.dumps(data, indent=2)
    
    def parse_csv(self, csv_content: str) -> list:
        import csv
        import io
        reader = csv.DictReader(io.StringIO(csv_content))
        return list(reader)
    
    def generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

#### **V2 MCP Utility Tool (Converted)**
```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ToolError

class UtilityTool(UnifiedTool):
    """Converted plugin to V2 MCP utility tool"""
    
    metadata = {
        "name": "Utility Tool",
        "description": "General utility functions for data processing",
        "version": "2.0.0",
        "capabilities": ["json_formatting", "csv_parsing", "uuid_generation"],
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["format_json", "parse_csv", "generate_uuid"]},
                "data": {"type": "object"},
                "csv_content": {"type": "string"}
            }
        }
    }
    
    async def execute(self, input_data: dict, context = None) -> dict:
        try:
            operation = input_data.get("operation")
            
            if operation == "format_json":
                result = await self._format_json(input_data)
            elif operation == "parse_csv":
                result = await self._parse_csv(input_data)
            elif operation == "generate_uuid":
                result = await self._generate_uuid()
            else:
                raise ToolError(f"Unknown operation: {operation}")
            
            return {
                "success": True,
                "result": result,
                "metadata": {"tool_id": self.tool_id, "operation": operation}
            }
            
        except Exception as e:
            return self._handle_error(e, context)
    
    async def _format_json(self, input_data: dict) -> dict:
        """Converted from format_json method"""
        import json
        
        data = input_data.get("data")
        if data is None:
            raise ToolError("Missing required parameter: data")
        
        formatted = json.dumps(data, indent=2)
        return {
            "formatted_json": formatted,
            "original_type": type(data).__name__
        }
    
    async def _parse_csv(self, input_data: dict) -> dict:
        """Converted from parse_csv method"""
        import csv
        import io
        
        csv_content = input_data.get("csv_content")
        if not csv_content:
            raise ToolError("Missing required parameter: csv_content")
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            parsed_data = list(reader)
            return {
                "parsed_data": parsed_data,
                "row_count": len(parsed_data),
                "columns": list(parsed_data[0].keys()) if parsed_data else []
            }
        except Exception as e:
            raise ToolError(f"CSV parsing failed: {str(e)}")
    
    async def _generate_uuid(self) -> dict:
        """Converted from generate_uuid method"""
        import uuid
        
        new_uuid = str(uuid.uuid4())
        return {
            "uuid": new_uuid,
            "version": 4,
            "format": "string"
        }
```

**Migration Changes:**
- ✅ Combined multiple methods into single `execute()` method
- ✅ Added operation routing via input parameters
- ✅ Enhanced with structured responses and metadata
- ✅ Better error handling with V2 system
- ✅ Async support for future scalability

---

## 🔄 Compatibility Adapters

During migration, V2 provides automatic compatibility adapters:

### **Automatic V1 Tool Wrapping**

```python
from langswarm.tools.adapters import auto_wrap_v1_tool

# Automatically wrap any V1 tool for V2 usage
v1_synapse_tool = OldSynapseTool()
v2_wrapped_tool = auto_wrap_v1_tool(v1_synapse_tool)

# Now works with V2 interface
result = await v2_wrapped_tool.execute({
    "operation": "legacy_method",
    "params": {"data": "input"}
})
```

### **Batch Tool Migration**

```python
from langswarm.tools.migration import migrate_v1_tools

# Migrate all V1 tools in a project
migration_result = migrate_v1_tools(
    source_dir="./legacy_tools",
    target_dir="./v2_tools",
    dry_run=True  # Analyze first
)

print(f"Found {len(migration_result.tools)} tools to migrate")
for tool in migration_result.tools:
    print(f"  {tool.name}: {tool.type} → MCP ({tool.complexity})")
```

---

## 🧪 Testing Migration

### **Migration Testing Strategy**

```python
import pytest
from langswarm.tools.testing import MigrationTestCase

class TestToolMigration(MigrationTestCase):
    """Test V1 to V2 tool migration"""
    
    async def test_mcp_tool_migration(self):
        """Test MCP tool enhancement"""
        # V1 tool
        v1_tool = FileSystemMCPTool()
        v1_result = v1_tool.run({"operation": "read_file", "path": "test.txt"})
        
        # V2 migrated tool
        v2_tool = FileSystemTool()
        v2_result = await v2_tool.execute({"operation": "read_file", "path": "test.txt"})
        
        # Verify compatibility
        assert v1_result["content"] == v2_result["result"]["content"]
        
        # Verify V2 enhancements
        assert "metadata" in v2_result
        assert v2_result["success"] is True
    
    async def test_synapse_tool_conversion(self):
        """Test Synapse tool conversion"""
        # V1 Synapse tool
        v1_tool = DataProcessorTool()
        v1_result = v1_tool.process_data("Hello World", "uppercase")
        
        # V2 converted tool
        v2_tool = DataProcessorTool()  # V2 version
        v2_result = await v2_tool.execute({
            "operation": "process",
            "data": "Hello World",
            "sub_operation": "uppercase"
        })
        
        # Verify functional compatibility
        assert v1_result["result"] == v2_result["result"]["processed_data"]
```

### **Compatibility Validation**

```python
from langswarm.tools.migration import validate_migration

# Validate that migration preserves functionality
validation_result = validate_migration(
    v1_tool=old_tool,
    v2_tool=new_tool,
    test_cases=[
        {"input": {"operation": "test1"}, "expected_output": "result1"},
        {"input": {"operation": "test2"}, "expected_output": "result2"}
    ]
)

if validation_result.passed:
    print("✅ Migration validation passed")
else:
    print("❌ Migration issues found:")
    for issue in validation_result.issues:
        print(f"  {issue}")
```

---

## 📋 Migration Checklist

### **For Each Tool Type**

#### **MCP Tools**
- [ ] Update to async `execute()` method
- [ ] Add V2 error handling integration
- [ ] Include metadata for auto-discovery
- [ ] Update tests for V2 patterns
- [ ] Verify backward compatibility

#### **Synapse Tools**
- [ ] Convert to MCP interface pattern
- [ ] Combine methods into operation routing
- [ ] Add async execution support
- [ ] Update error handling to V2 system
- [ ] Create compatibility adapter if needed

#### **Retrievers**
- [ ] Convert to MCP memory/search tool
- [ ] Add operation routing (search, add, list)
- [ ] Enhance with V2 error handling
- [ ] Update to async processing
- [ ] Test with memory system integration

#### **Plugins**
- [ ] Convert to MCP utility tool pattern
- [ ] Add operation routing for multiple methods
- [ ] Update to async execution
- [ ] Integrate V2 error system
- [ ] Verify utility functionality preserved

### **General Migration Steps**
- [ ] **Assess Tool Type**: Identify current tool pattern
- [ ] **Choose Migration Path**: Direct, conversion, or adapter
- [ ] **Create V2 Version**: Implement unified interface
- [ ] **Test Compatibility**: Ensure functionality preserved
- [ ] **Update Configuration**: Use V2 configuration patterns
- [ ] **Update Documentation**: Document V2 usage patterns
- [ ] **Deploy Gradually**: Migrate in phases

---

## 🎯 Success Metrics

### **Migration Completeness**
- [ ] **All Tool Types Supported**: MCP, Synapse, Retrievers, Plugins
- [ ] **100% Functional Compatibility**: All existing functionality preserved
- [ ] **Unified Interface**: All tools use same execution pattern
- [ ] **Auto-Discovery**: Tools automatically registered and discoverable
- [ ] **Enhanced Performance**: Async execution and optimization

### **Developer Experience**
- [ ] **Single Learning Curve**: One tool development pattern
- [ ] **Consistent Testing**: Same testing patterns for all tools
- [ ] **Unified Documentation**: Single documentation structure
- [ ] **Better Debugging**: V2 error system integration

### **User Experience**
- [ ] **No Breaking Changes**: Existing code continues working
- [ ] **Improved Performance**: Async execution and caching
- [ ] **Better Error Messages**: V2 error system benefits
- [ ] **Simplified Configuration**: Unified tool configuration

---

**The V2 tool migration provides a clear path from V1's fragmented tool landscape to a unified, consistent, and powerful tool system while maintaining 100% backward compatibility.**
