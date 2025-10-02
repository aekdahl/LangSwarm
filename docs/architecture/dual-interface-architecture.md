# Dual Interface Architecture for MCP Tools

## Overview

LangSwarm MCP tools implement a **dual interface architecture** that provides both efficient direct calls and intelligent workflow-based processing, optimizing for different use cases.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 MCP Tool (e.g. BigQuery Vector Search)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 template.md ────► Complete user documentation & guidelines  │
│                                                                 │
│  🔧 Core Functions ─► Pure business logic functions             │
│     ├── similarity_search(query, limit, threshold)             │
│     ├── list_datasets(pattern)                                 │
│     └── get_content(document_id)                               │
│                                                                 │
│  🎯 Dual Interface:                                             │
│     ├── DIRECT: Method + Params (fast, precise)                │
│     └── WORKFLOW: Natural language (smart, flexible)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Interface Types

### 🚀 Direct Method Calls

**When to Use:**
- Agent knows the exact operation needed
- Parameters are clear and specific  
- Optimizing for speed and token efficiency
- Making precise, targeted requests

**Format:**
```json
{
  "tool": "bigquery_vector_search",
  "method": "similarity_search", 
  "params": {
    "query": "enterprise pricing policies",
    "limit": 5,
    "similarity_threshold": 0.7
  }
}
```

**Benefits:**
- ⚡ **Ultra-low latency**: Direct execution, no workflow overhead
- 💰 **Cost efficient**: No additional agent calls for processing
- 🎯 **Precise control**: Agent specifies exact parameters
- 🔧 **Predictable**: Deterministic input/output behavior

### 🧠 Workflow-Based Calls

**When to Use:**
- Request needs interpretation or enhancement
- Natural language input requires processing
- Complex multi-step operations needed
- Ambiguous intent requiring classification

**Format:**
```json
{
  "tool": "bigquery_vector_search",
  "workflow": "main_workflow",
  "input": "I need to find information about customer refund processes"
}
```

**Benefits:**
- 🤖 **Smart interpretation**: AI agents analyze and enhance requests
- 🔄 **Complex routing**: Can chain multiple operations intelligently
- 📊 **Context enhancement**: Automatically improves queries
- 🧩 **Multi-step**: Handles complex workflows seamlessly

## Implementation Pattern

### Smart Routing Logic

```python
class MCPTool(BaseTool):
    def run(self, input_data=None, **kwargs):
        """Auto-route between direct and workflow interfaces"""
        
        # Direct method call - efficiency path
        if self._is_direct_call(input_data):
            return self._execute_direct_method(input_data)
        
        # Workflow call - intelligence path
        elif self._is_workflow_call(input_data):
            return self._execute_workflow(input_data)
        
        # Auto-detect based on structure
        else:
            return self._auto_route(input_data)
    
    def _is_direct_call(self, data):
        """Detect direct method calls"""
        return (isinstance(data, dict) and 
                "method" in data and 
                "params" in data)
    
    def _is_workflow_call(self, data):
        """Detect workflow calls"""
        return (isinstance(data, dict) and 
                ("workflow" in data or 
                 self._is_natural_language(data.get("input", ""))))
```

### Method Registration

```python
# Each tool registers both interfaces
AVAILABLE_METHODS = {
    # Direct methods
    "similarity_search": similarity_search,
    "list_datasets": list_datasets, 
    "get_content": get_content,
    
    # Workflow entry point
    "main_workflow": execute_workflow
}
```

## Performance Characteristics

| Interface Type | Latency | Token Cost | Flexibility | Use Case |
|----------------|---------|------------|-------------|----------|
| Direct Method  | ~100ms  | Low        | Medium      | Known operations |
| Workflow-Based | ~500ms  | Medium     | High        | Complex/ambiguous |

## Example Usage Patterns

### Pattern 1: Direct Call (Optimal for Clarity)
```
User: "Search for refund policies"
Agent Analysis: Clear semantic search request
Agent Decision: Use direct method call

Request:
{
  "tool": "bigquery_vector_search",
  "method": "similarity_search",
  "params": {"query": "refund policies", "limit": 5}
}

Result: ⚡ Fast execution, precise results
```

### Pattern 2: Workflow Call (Optimal for Complexity)
```
User: "Help me understand what options unhappy customers have"
Agent Analysis: Ambiguous, needs interpretation  
Agent Decision: Use workflow system

Request:
{
  "tool": "bigquery_vector_search", 
  "workflow": "main_workflow",
  "input": "what options unhappy customers have"
}

Workflow Process:
1. Intent classification: "customer_support_options"
2. Query enhancement: "customer service options complaint resolution refund exchange"
3. Semantic search: similarity_search()
4. Result formatting: Structured response

Result: 🧠 Intelligent processing, comprehensive results
```

## Design Principles

### 1. **Efficiency First**
- Direct calls for 80% of common use cases
- Zero overhead when agent knows what to do
- Minimal token usage for straightforward requests

### 2. **Intelligence When Needed**  
- Workflow system for complex interpretation
- AI agents enhance ambiguous requests
- Multi-step processing for sophisticated operations

### 3. **Backwards Compatibility**
- All existing direct method calls continue to work
- Legacy workflow calls remain supported
- Gradual migration path for existing implementations

### 4. **Clear Documentation**
- template.md explains when to use each interface
- Examples for both approaches
- Performance characteristics clearly documented

## Migration Strategy

### For Existing Direct Calls
```python
# ✅ Continue working unchanged
tool_call = {
    "tool": "bigquery_vector_search",
    "method": "similarity_search", 
    "params": {"query": "search terms"}
}
```

### For New Workflow-Based Calls  
```python
# ✅ New capability 
tool_call = {
    "tool": "bigquery_vector_search",
    "workflow": "main_workflow",
    "input": "natural language request"
}
```

### For Tool Developers
1. Keep all existing direct methods
2. Ensure template.md documents both interfaces
3. Implement workflow routing if complex processing needed
4. Remove any deprecated `handle_intent` fallbacks

## Benefits of Dual Interface

### For Users
- **Flexibility**: Choose the right interface for each use case
- **Performance**: Get optimal speed when possible
- **Intelligence**: Access AI enhancement when needed

### For Developers  
- **Efficiency**: Direct calls for simple operations
- **Power**: Workflow system for complex logic
- **Maintainability**: Clean separation of concerns

### For the System
- **Scalability**: Efficient resource utilization
- **Extensibility**: Easy to add new capabilities
- **Debuggability**: Clear execution paths for both interfaces

This dual interface architecture provides the **best of both worlds**: the efficiency of direct method calls when you know what you want, and the intelligence of workflow-based processing when you need interpretation and enhancement.
