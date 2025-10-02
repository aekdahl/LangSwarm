# Workflow Executor MCP Tool

## Description

Workflow automation and orchestration tool with natural language process management using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "workflow_executor",
    "arguments": {
      "intent": "Run the data processing pipeline for today's customer analytics",
      "context": "daily batch processing, analytics workflow"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "workflow_executor.execute_workflow",
    "arguments": {"workflow_id": "data-processing-pipeline", "inputs": {"source": "database"}}
  }
}
```

**When to use:** Workflow automation, process orchestration, business logic execution, pipeline management

**Intent examples:**
- "Start the monthly report generation workflow"
- "Process all pending customer onboarding tasks"
- "Run the backup and cleanup procedures for the weekend"

**Available methods:** execute_workflow, schedule_workflow, monitor_execution, manage_pipelines, get_status

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

Workflow automation with intelligent intent processing via flattened MCP protocol.
