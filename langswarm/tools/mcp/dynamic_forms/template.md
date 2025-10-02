# Dynamic Forms MCP Tool

## Description

Intelligent form generation with natural language specification using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "dynamic_forms",
    "arguments": {
      "intent": "Create a customer feedback form for our mobile app with rating and comments",
      "context": "user experience, app improvement"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "dynamic_forms.create_form",
    "arguments": {"fields": [{"name": "rating", "type": "number"}]}
  }
}
```

**When to use:** User input collection, surveys, registration forms, data gathering interfaces

**Intent examples:**
- "Build a sign-up form for enterprise customers"
- "Create a bug report form with file upload"
- "Make a simple contact form with validation"

**Available methods:** create_form, validate_form, process_submission, generate_fields

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

Dynamic form generation with intelligent intent processing via flattened MCP protocol.
