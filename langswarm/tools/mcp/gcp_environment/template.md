# Gcp Environment MCP Tool

## Description

Google Cloud Platform environment management with natural language infrastructure operations using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "gcp_environment",
    "arguments": {
      "intent": "Deploy a scalable web service to GCP with auto-scaling and load balancing",
      "context": "production deployment, high availability"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "gcp_environment.deploy_service",
    "arguments": {"service_name": "my-app", "region": "us-central1"}
  }
}
```

**When to use:** GCP resource management, service deployment, infrastructure operations, cloud monitoring

**Intent examples:**
- "Set up a production environment for our e-commerce platform"
- "Scale down the development resources to save costs"
- "Monitor the health of our microservices cluster"

**Available methods:** deploy_service, manage_resources, configure_infrastructure, monitor_services, scale_resources

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

GCP environment management with intelligent intent processing via flattened MCP protocol.
