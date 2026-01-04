# Remote MCP Tools Guide

A comprehensive guide for connecting LangSwarm to remote MCP servers via HTTP/HTTPS.

## Overview

LangSwarm supports connecting to remote MCP (Model-Compatible Protocol) servers through HTTP/HTTPS endpoints. This enables integration with:

- External MCP services and APIs
- Third-party tool providers
- Cloud-hosted MCP servers
- Enterprise MCP services

## Quick Start

### Basic Remote MCP Tool Configuration

Configuration is handled automatically via the `ToolRegistry` and `RemoteMCPTool`. You can define them in your `tools.yaml` or instantiate programmatically.

```yaml
# tools.yaml
tools:
  - id: remote_service
    type: mcpremote
    description: "Remote MCP service for data processing"
    mcp_url: "https://your-mcp-server.com/api"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    timeout: 30
    retry_count: 3
```

### Agent Configuration

```yaml
# agents.yaml
agents:
  - id: data_agent
    agent_type: openai
    model: gpt-4o
    system_prompt: |
      You can use remote MCP tools for external operations.
      
      Available tools:
      - remote_service: External data processing
    tools:
      - remote_service
```

## Configuration Reference

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique tool identifier |
| `type` | string | Must be `mcpremote` |
| `mcp_url` | string | HTTP/HTTPS URL of the remote MCP server |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | string | Auto-generated | Tool description |
| `headers` | object | `{}` | HTTP headers for authentication |
| `timeout` | integer | `30` | Request timeout in seconds |
| `retry_count` | integer | `3` | Number of retry attempts |
| `auto_initialize` | boolean | `true` | Auto-connect on startup |

## Authentication

### API Key Authentication

```yaml
tools:
  - id: secure_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    headers:
      x-api-key: "${SERVICE_API_KEY}"
```

### Bearer Token Authentication

```yaml
tools:
  - id: jwt_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    headers:
      Authorization: "Bearer ${JWT_TOKEN}"
```

## Environment Variables

Use environment variables for sensitive information. LangSwarm supports explicit variable expansion `${VAR_NAME}` in your YAML configurations.

```bash
# Authentication
export SERVICE_API_KEY="your-api-key"
export MCP_SERVER_URL="https://prod-api.service.com/mcp"
```

Then reference in configuration:

```yaml
tools:
  - id: env_service
    type: mcpremote
    mcp_url: "${MCP_SERVER_URL}"
    headers:
      x-api-key: "${SERVICE_API_KEY}"
```
