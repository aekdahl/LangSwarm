# Message Queue Consumer MCP Tool

## Description

Message queue consumer with natural language event processing using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "message_queue_consumer",
    "arguments": {
      "intent": "Process all pending notification messages and send them to users",
      "context": "notification system, message processing"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "message_queue_consumer.consume_messages",
    "arguments": {"queue": "notifications", "batch_size": 10}
  }
}
```

**When to use:** Message processing, event handling, queue management, system integration

**Intent examples:**
- "Handle all urgent alerts from the monitoring system"
- "Process customer feedback messages from the support queue"
- "Consume and route messages from the payment processing system"

**Available methods:** consume_messages, process_events, handle_queue, manage_subscriptions, get_metrics

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

Message queue consumer with intelligent intent processing via flattened MCP protocol.
