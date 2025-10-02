# Codebase Indexer MCP Tool

## Description

Code analysis and indexing tool with natural language project understanding using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "codebase_indexer",
    "arguments": {
      "intent": "Analyze this Python project and create documentation for the API endpoints",
      "context": "code documentation, API analysis"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "codebase_indexer.index_project",
    "arguments": {"path": "/path/to/project", "language": "python"}
  }
}
```

**When to use:** Code analysis, project indexing, documentation generation, code search

**Intent examples:**
- "Find all the database models in this Django project"
- "Generate API documentation for this FastAPI service"
- "Show me the test coverage for the authentication module"

**Available methods:** index_project, analyze_code, generate_docs, search_code, get_metrics

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

Code analysis and indexing with intelligent intent processing via flattened MCP protocol.
