# Intent-Based MCP Extension Proposal

## 🎯 Strategic Direction: Extend Standard MCP for Intent-Based Calling

Instead of having a custom LangSwarm format, we can define intent-based calling as a **standard MCP protocol extension** that preserves our USP while ensuring full interoperability.

## 📋 Current vs Proposed

### **Current LangSwarm Format (Non-Standard)**
```json
{
  "tool": "bigquery_vector_search",
  "intent": "Find information about our refund policy", 
  "context": "customer support, policy documentation"
}
```

### **Proposed: Intent as MCP Extension (Standard + USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "bigquery_vector_search",
    "arguments": {
      "intent": "Find information about our refund policy",
      "context": "customer support, policy documentation"
    }
  }
}
```

### **Traditional Direct Calling (Also Standard)**
```json
{
  "method": "call_tool", 
  "params": {
    "name": "bigquery_vector_search",
    "arguments": {
      "method": "similarity_search",
      "params": {
        "query": "refund policy",
        "limit": 5,
        "similarity_threshold": 0.7
      }
    }
  }
}
```

## ✅ Benefits of This Approach

### **1. Full MCP Compliance**
- Works with any standard MCP client (Claude Desktop, VS Code, etc.)
- Can be discovered via `list_tools()`
- Follows standard JSON-RPC 2.0 envelope
- Integrates with existing MCP ecosystems

### **2. Preserves LangSwarm USP**
- Intent-based calling is still our unique differentiator
- Natural language processing capabilities maintained
- Intelligent parameter inference and method selection
- Context-aware execution remains

### **3. Best of Both Worlds**
- **Intent-based**: For intelligent, natural language interactions
- **Direct calling**: For precise, optimized execution
- **Discovery**: Standard protocol methods work
- **Interoperability**: Compatible with all MCP tools

### **4. Tool Schema Definition**
Tools can advertise both capabilities in their schema:

```json
{
  "name": "bigquery_vector_search",
  "description": "Semantic search with intent processing",
  "inputSchema": {
    "oneOf": [
      {
        "type": "object",
        "properties": {
          "intent": {"type": "string", "description": "Natural language intent"},
          "context": {"type": "string", "description": "Additional context"}
        },
        "required": ["intent"]
      },
      {
        "type": "object", 
        "properties": {
          "method": {"type": "string", "enum": ["similarity_search", "get_content"]},
          "params": {"type": "object"}
        },
        "required": ["method", "params"]
      }
    ]
  }
}
```

## 🔧 Implementation Strategy

### **Phase 1: Update Tool Definitions**
- Modify tool schemas to accept both intent and direct calling
- Update `call_tool` implementations to handle both formats
- Maintain backward compatibility

### **Phase 2: Update Templates**
- Show both formats in template.md files
- Promote intent-based as "intelligent mode"
- Document standard MCP compliance

### **Phase 3: Update Agent Integration**
- Modify agent tool calling to use standard MCP envelope
- Keep intent-based parameter passing
- Update tool injection logic

## 📝 Template Example

```markdown
## Instructions

🎯 **LangSwarm's Intelligent Intent Processing**

This tool supports both intelligent intent-based calling and direct method execution within the standard MCP protocol.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "bigquery_vector_search",
    "arguments": {
      "intent": "Find information about our refund policy for enterprise customers",
      "context": "customer support, policy documentation"
    }
  }
}
```

**Alternative: Direct Method Calling**
```json
{
  "method": "call_tool", 
  "params": {
    "name": "bigquery_vector_search",
    "arguments": {
      "method": "similarity_search",
      "params": {
        "query": "enterprise refund policy",
        "limit": 5,
        "similarity_threshold": 0.7
      }
    }
  }
}
```

**Intent Processing Advantages:**
- Automatic method selection based on natural language
- Intelligent parameter inference and optimization  
- Context-aware execution and result formatting
- Natural language understanding and interpretation
```

## 🎯 Competitive Positioning

### **LangSwarm's Unique Value:**
1. **Intent Understanding**: Natural language → optimal execution
2. **Context Awareness**: Semantic understanding of user needs
3. **Intelligent Automation**: Parameter optimization and method selection
4. **User Experience**: Natural conversation vs technical specifications

### **Standard MCP Compliance:**
1. **Interoperability**: Works with any MCP client
2. **Discovery**: Tools can be found and introspected
3. **Ecosystem**: Integrates with existing MCP tools
4. **Standards**: Follows established protocols

## 🚀 Recommendation

**Adopt this hybrid approach** to:
- ✅ Maintain competitive advantage (intent-based intelligence)
- ✅ Ensure broad compatibility (standard MCP protocol)  
- ✅ Enable ecosystem growth (works with all MCP clients)
- ✅ Future-proof architecture (follows industry standards)

This gives us the best of both worlds: **intelligent natural language processing** wrapped in **standard protocol compliance**.
