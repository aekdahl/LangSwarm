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
      
      Use direct calls:
      {
        "mcp": {
          "tool": "remote_service",
          "method": "process_data",
          "params": {"data": "...", "format": "json"}
        }
      }
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
| `pattern` | string | `"direct"` | Tool usage pattern (`direct` or `intent`) |

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

### Custom Headers

```yaml
tools:
  - id: custom_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    headers:
      X-Client-ID: "${CLIENT_ID}"
      X-API-Version: "v1"
      Custom-Header: "value"
```

## Environment Variables

Use environment variables for sensitive information:

```bash
# Authentication
export SERVICE_API_KEY="your-api-key"
export JWT_TOKEN="your-jwt-token"
export CLIENT_ID="your-client-id"

# Dynamic URLs
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

## Usage Patterns

### Direct Pattern

Direct method calls with explicit parameters:

```yaml
# Tool configuration
tools:
  - id: data_processor
    type: mcpremote
    pattern: "direct"
    mcp_url: "https://data-api.com/mcp"
```

```json
// Agent usage
{
  "mcp": {
    "tool": "data_processor",
    "method": "analyze_data",
    "params": {
      "dataset": "sales_2024.csv",
      "analysis_type": "trend"
    }
  }
}
```

### Intent Pattern

Natural language intent with agent workflow:

```yaml
# Tool configuration
tools:
  - id: smart_processor
    type: mcpremote
    pattern: "intent"
    main_workflow: "processing_workflow"
    mcp_url: "https://smart-api.com/mcp"
```

```json
// Agent usage
{
  "mcp": {
    "tool": "smart_processor",
    "intent": "analyze customer behavior patterns",
    "context": "e-commerce data from last quarter"
  }
}
```

## Error Handling

LangSwarm provides comprehensive error handling for remote MCP tools:

### HTTP Status Codes

- **401 Unauthorized**: Authentication failed
- **400 Bad Request**: Invalid request or parameters
- **500+ Server Error**: Remote server issues (retryable)

### Network Errors

- **Timeout**: Request exceeded timeout period
- **Connection Error**: Unable to connect to server
- **Invalid JSON**: Server returned non-JSON response

### Example Error Response

```json
{
  "error": {
    "message": "Authentication failed - check API key or JWT token",
    "code": 401,
    "url": "https://api.service.com/mcp",
    "retryable": false
  }
}
```

## Advanced Configuration

### Multi-Environment Setup

```yaml
tools:
  - id: service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    
    # Environment-specific overrides
    environment_overrides:
      development:
        mcp_url: "https://dev-api.service.com/mcp"
        timeout: 60  # Longer timeout for dev
      staging:
        mcp_url: "https://staging-api.service.com/mcp"
      production:
        mcp_url: "https://api.service.com/mcp"
        retry_count: 5  # More retries in prod
```

### Custom Retry Logic

```yaml
tools:
  - id: reliable_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    retry_count: 5
    timeout: 45
    
    # Custom retry configuration
    retry_strategy:
      exponential_backoff: true
      max_delay: 30
      retryable_codes: [500, 502, 503, 504]
```

### Connection Pooling

```yaml
tools:
  - id: high_volume_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    
    # Connection settings
    connection:
      pool_size: 10
      keep_alive: true
      connection_timeout: 10
```

## Tool Discovery and Schema

Remote MCP tools automatically discover available methods and schemas:

### Initialization Flow

1. **Initialize**: Send `{"method": "initialize"}` to establish connection
2. **Discover Tools**: Send `{"method": "tools/list"}` to get available tools
3. **Cache Schemas**: Store tool schemas for validation and help

### Manual Schema Discovery

```python
# Get available tools
tools = agent.tool_registry.get_tool("remote_service")
available_tools = tools.get_available_tools()

# Get specific tool schema
schema = tools.get_tool_schema("analyze_data")
```

## Troubleshooting

### Common Issues

#### Connection Refused
```
Error: Connection error: [Errno 61] Connection refused
```
**Solution**: Verify the MCP server URL and ensure the server is running.

#### Authentication Failed
```
Error: Authentication failed - check API key or JWT token
```
**Solution**: 
- Verify API key/token is correct
- Check environment variables are set
- Ensure headers are properly configured

#### Tool Not Found
```
Error: Tool 'process_data' not available
```
**Solution**:
- Check tool exists on remote server via `tools/list`
- Verify tool name spelling
- Ensure remote server is properly initialized

#### Timeout Errors
```
Error: Request timeout - server did not respond within timeout period
```
**Solution**:
- Increase `timeout` value
- Check network connectivity
- Verify remote server performance

### Debugging Commands

```bash
# Test remote MCP connection
curl -X POST https://your-mcp-server.com/api \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"method":"initialize","id":"test-1"}'

# List available tools
curl -X POST https://your-mcp-server.com/api \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"method":"tools/list","id":"test-2"}'
```

### Log Analysis

Enable debug logging:

```python
import logging
logging.getLogger("langswarm.mcp").setLevel(logging.DEBUG)
```

## Performance Optimization

### Best Practices

1. **Connection Reuse**: Configure connection pooling for high-volume applications
2. **Timeout Tuning**: Adjust timeouts based on expected response times
3. **Retry Strategy**: Use exponential backoff for temporary failures
4. **Caching**: Cache tool schemas to reduce initialization overhead
5. **Parallel Requests**: Use async patterns for concurrent tool calls

### Monitoring

```yaml
tools:
  - id: monitored_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    
    # Monitoring configuration
    monitoring:
      enable_metrics: true
      log_requests: true
      alert_on_failures: true
      health_check_interval: 60
```

## Security Considerations

### Authentication Best Practices

1. **Environment Variables**: Store sensitive tokens in environment variables
2. **Token Rotation**: Implement regular API key rotation
3. **Least Privilege**: Use tokens with minimal required permissions
4. **HTTPS Only**: Always use HTTPS for remote MCP connections
5. **Header Security**: Avoid logging sensitive headers

### Network Security

```yaml
tools:
  - id: secure_service
    type: mcpremote
    mcp_url: "https://api.service.com/mcp"
    
    # Security configuration
    security:
      verify_ssl: true
      allowed_hosts: ["api.service.com"]
      max_redirects: 0
      disable_warnings: false
```

## Examples

### Complete Configuration Examples

See the following files for complete examples:
- `examples/remote_mcp_tool_example.yaml` - General remote MCP configuration
- `examples/user_mcp_configuration.yaml` - User MCP (Agent Server) specific setup with NEW expanded capabilities
- `examples/enterprise_mcp_setup.yaml` - Enterprise-grade configuration

### User MCP Server Update (Latest)

The User MCP server has been significantly expanded with new capabilities:

**New Features Added:**
- **Subtasks**: Create, list, update, delete, promote subtasks
- **Subprojects**: Organize projects hierarchically  
- **Task Messages/Logs**: Full conversation and logging system
- **Backlog Management**: Create, reorder, convert backlog items
- **Document System**: Create docs with group organization
- **Milestones**: Track project milestones with items
- **File Management**: List and delete attachments (read-only)

**Important Requirements:**
- **Authentication**: Prefer `Authorization: Bearer JWT` over `x-api-key`
- **Scoping**: Always provide teamId/projectId/subprojectId/taskId for performance
- **Dates**: Use ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
- **Safety**: Ask confirmation before delete_* operations
- **Rate Limits**: Max ~3 req/s, 10s timeout recommended
- **Response Format**: Check error first, then read `result.content[0].text`

### Integration Examples

- **Data Processing**: Connect to remote analytics services
- **Document Processing**: Integrate with cloud document APIs  
- **ML Services**: Access remote machine learning endpoints
- **Enterprise APIs**: Connect to internal company services

## API Reference

### RemoteMCPTool Methods

- `call_remote_tool(tool_name, arguments)` - Call specific remote tool
- `get_available_tools()` - Get list of available tools
- `get_tool_schema(tool_name)` - Get schema for specific tool
- `check_connection()` - Test connection to remote server

### Configuration Schema

For detailed configuration schema, see:
- JSON Schema: `schemas/remote_mcp_tool.json`
- TypeScript Types: `types/remote_mcp_tool.ts`
- Python Types: `langswarm.mcp.tools.remote.types`

## Contributing

To add support for new remote MCP servers or protocols:

1. Extend `RemoteMCPTool` class
2. Add custom authentication handlers
3. Implement protocol-specific features
4. Submit pull request with tests and documentation

## Support

- **Documentation**: [LangSwarm MCP Docs](https://docs.langswarm.com/mcp)
- **Issues**: [GitHub Issues](https://github.com/langswarm/langswarm/issues)
- **Community**: [Discord Server](https://discord.gg/langswarm)
- **Examples**: [LangSwarm Examples](https://github.com/langswarm/examples)