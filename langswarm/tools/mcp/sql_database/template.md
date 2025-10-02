# Sql Database MCP Tool

## Description

Intelligent SQL interface with natural language query understanding using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "sql_database",
    "arguments": {
      "intent": "Show me customers from Stockholm who signed up in the last quarter",
      "context": "customer analysis, geographic segmentation"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "sql_database.execute_query",
    "arguments": {"query": "SELECT * FROM table WHERE condition"}
  }
}
```

**When to use:** Data analysis, reporting, customer insights, business intelligence queries

**Intent examples:**
- "Find our top performing products this month"
- "Show users who haven't logged in recently"
- "Get revenue breakdown by region"

**Available methods:** execute_query, list_tables, describe_table, analyze_data

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

SQL database interface with intelligent natural language query processing via flattened MCP.
