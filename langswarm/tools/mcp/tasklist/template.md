# Tasklist MCP Tool

## Description

Smart task management with natural language task creation using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "tasklist",
    "arguments": {
      "intent": "Add a high-priority task to review and update our security documentation by Friday",
      "context": "security audit, compliance deadline"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "tasklist.add_task",
    "arguments": {"title": "Task name", "priority": "high"}
  }
}
```

**When to use:** Project management, productivity tracking, deadline management, team coordination

**Intent examples:**
- "Show me overdue tasks for the development team"
- "Create a checklist for onboarding new employees"
- "Mark the API documentation task as completed"

**Available methods:** add_task, update_task, list_tasks, complete_task, set_priorities

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

Task management with intelligent intent processing via flattened MCP protocol.
