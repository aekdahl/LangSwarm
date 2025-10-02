# Bigquery Vector Search MCP Tool

## Description

Advanced semantic search tool with natural language intent processing for knowledge base exploration.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

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

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "bigquery_vector_search.similarity_search",
    "arguments": {"query": "search terms", "limit": 5}
  }
}
```

**When to use:** Knowledge base search, document retrieval, policy lookup, information discovery

**Intent examples:**
- "What's our stance on data privacy?"
- "Find documentation about API rate limits" 
- "Show me onboarding procedures for new employees"

**Available methods:** similarity_search, get_content, list_datasets, get_embedding

### Standard MCP Protocol Methods

This tool supports standard MCP protocol for discovery and introspection:

**Discovery Methods:**
- `list_tools()` - Discover all available tools in the system
- `call_tool(name, arguments)` - Execute with flattened name format or intent
- `list_prompts()` - Find available agent prompts for workflows  
- `list_resources()` - See available files (template.md, agents.yaml, etc.)

**Execution Methods:**
- `call_tool(name, arguments)` - Supports both `tool.method` and intent formats
- `get_prompt(name, arguments)` - Get formatted prompts with variables
- `read_resource(uri)` - Access specific resource content

**Example Protocol Discovery:**
```json
{
  "method": "list_tools",
  "params": {}
}
```

**Pro tip:** Use intent-based calls for intelligent processing, or flattened direct calls (`tool.method`) for precise control.

## Brief

Semantic search with intelligent intent processing using flattened MCP protocol.
