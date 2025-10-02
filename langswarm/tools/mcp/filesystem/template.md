# Filesystem MCP Tool

## Description

Smart file system operations with natural language intent understanding using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "filesystem",
    "arguments": {
      "intent": "Find all Python files in the project that were modified today",
      "context": "code review, recent changes"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "filesystem.list_directory",
    "arguments": {"path": "/project", "pattern": "*.py"}
  }
}
```

**When to use:** File management, code exploration, content search, directory operations

**Intent examples:**
- "Show me the latest log files from the server"
- "Find configuration files that need updating"
- "List all documents created this week"

**Available methods:** read_file, write_file, list_directory, search_files, manage_permissions

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

File system operations with intelligent intent processing via flattened MCP protocol.
