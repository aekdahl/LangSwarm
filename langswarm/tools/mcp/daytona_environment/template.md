# Daytona Environment MCP Tool

## Description

Intelligent development environment management with natural language workspace configuration using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "daytona_environment",
    "arguments": {
      "intent": "Set up a Python development environment for a machine learning project with GPU support",
      "context": "data science, model training, cloud resources"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "daytona_environment.create_workspace",
    "arguments": {"name": "ml-project", "template": "python-gpu", "resources": {"gpu": true}}
  }
}
```

**When to use:** Development environment setup, workspace management, resource provisioning, team collaboration

**Intent examples:**
- "Create a Node.js environment for our React frontend team"
- "Set up a secure workspace for the security audit project"
- "Provision a high-memory environment for data processing"

**Available methods:** create_workspace, manage_resources, configure_environment, share_workspace, monitor_usage

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

Development environment management with intelligent intent processing via flattened MCP protocol.
