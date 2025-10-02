# Mcpgithubtool MCP Tool

## Description

Intelligent GitHub integration with natural language repository management using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "mcpgithubtool",
    "arguments": {
      "intent": "Create a bug report issue for the login problem with authentication errors",
      "context": "user reports, authentication system, priority bug"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "mcpgithubtool.create_issue",
    "arguments": {"title": "Login authentication error", "body": "Users unable to login", "labels": ["bug", "priority"]}
  }
}
```

**When to use:** GitHub repository management, issue tracking, pull request automation, code collaboration

**Intent examples:**
- "Review and merge all approved pull requests for the release"
- "Create a milestone for the next sprint with all planned features"
- "Generate a release summary from all closed issues this month"

**Available methods:** create_issue, manage_pr, handle_repository, track_milestones, generate_reports

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

GitHub integration with intelligent intent processing via flattened MCP protocol.
