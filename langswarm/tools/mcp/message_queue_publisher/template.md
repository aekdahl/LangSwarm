# Message Queue Publisher MCP Tool

## Description

Smart message publishing with natural language event specification using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "message_queue_publisher",
    "arguments": {
      "intent": "Send urgent notification to all admin users about system maintenance tonight",
      "context": "system alerts, maintenance window, admin communication"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "message_queue_publisher.publish_message",
    "arguments": {"queue": "admin-alerts", "message": "System maintenance scheduled", "priority": "urgent"}
  }
}
```

**When to use:** Message publishing, event broadcasting, notification delivery, system communication

**Intent examples:**
- "Notify all users about the new feature release"
- "Send payment confirmation to customer after successful transaction"
- "Broadcast system status update to all monitoring dashboards"

**Available methods:** publish_message, broadcast_event, send_notification, manage_topics, get_delivery_status

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

Message publishing with intelligent intent processing via flattened MCP protocol.
