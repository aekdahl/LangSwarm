# LangSwarm V2 Tool System Documentation

## Overview

The LangSwarm V2 Tool System is a revolutionary, LLM-agnostic platform that provides seamless tool integration across multiple AI providers. It automatically adapts existing MCP tools to work with any LLM provider while maintaining their native capabilities and performance.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangSwarm V2 Tool System                    │
│                     (LLM-Agnostic)                             │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
         ┌──────────▼──────────┐   │   ┌──────────▼──────────┐
         │   MCP Tool Adapter  │   │   │   V2 Tool Registry  │
         │                     │   │   │                     │
         │ • Auto-discovery    │   │   │ • 13+ Adapted Tools │
         │ • V2 Interface      │   │   │ • Schema Management │
         │ • Metadata Bridge   │   │   │ • Health Monitoring │
         └─────────────────────┘   │   └─────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ OpenAI  │              │Anthropic│              │ Gemini  │
    │Provider │              │Provider │              │Provider │
    │         │              │         │              │         │
    │MCP→     │              │MCP→     │              │MCP→     │
    │OpenAI   │              │Claude   │              │Gemini   │
    │Format   │              │Format   │              │Format   │
    └─────────┘              └─────────┘              └─────────┘
```

### Key Principles

1. **LLM Agnostic**: Each provider handles tools in their native format
2. **Zero Breaking Changes**: Existing MCP tools work without modification  
3. **Auto-Discovery**: Automatic detection and registration of tools
4. **Provider-Specific Optimization**: Native format conversion for each LLM
5. **Extensible**: Easy to add new providers and tools

## Quick Start

### Basic Usage

```python
from langswarm.v2.core.agents.builder import AgentBuilder
from langswarm.v2.core.agents.interfaces import ProviderType

# Create an agent with tools (any provider)
agent = await AgentBuilder('my_agent') \
    .provider(ProviderType.OPENAI) \
    .model('gpt-4o') \
    .tools(['bigquery_vector_search', 'sql_database']) \
    .build()

# Tools are automatically adapted and integrated
print(f"Available tools: {agent.get_available_tools()}")
```

### YAML Workflow Usage

```yaml
# workflows.yaml
workflows:
  data_analysis:
    steps:
      - id: query_database
        function: langswarm.core.utils.workflows.functions.mcp_call
        args:
          mcp_url: "local://sql_database"
          payload:
            name: "execute_query"
            arguments:
              query: "SELECT * FROM users LIMIT 10"
```

## Supported Providers

### OpenAI
- **Models**: GPT-4o, GPT-4, GPT-3.5-turbo, etc.
- **Tool Format**: OpenAI Function Calling
- **Features**: Streaming, vision, function calls

### Anthropic  
- **Models**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Tool Format**: Anthropic Tool Use
- **Features**: Streaming, vision, tool calls

### Google Gemini
- **Models**: Gemini Pro, Gemini Pro Vision, Gemini Ultra
- **Tool Format**: Gemini Function Declarations
- **Features**: Multimodal, safety settings, function calls

### Cohere
- **Models**: Command R+, Command R, Command
- **Tool Format**: Cohere Tool Calling
- **Features**: RAG, embeddings, tool calls

### Mistral
- **Models**: Mistral Large, Mistral Medium, Mistral Small
- **Tool Format**: Mistral Function Calling
- **Features**: Streaming, function calls

### Hugging Face
- **Models**: Any compatible HF model
- **Tool Format**: Custom schema format
- **Features**: Local/remote models, custom implementations

## Available Tools

The system automatically discovers and adapts all MCP tools:

1. **bigquery_vector_search** - Vector similarity search in BigQuery
2. **sql_database** - SQL database operations
3. **codebase_indexer** - Code analysis and indexing
4. **filesystem** - File system operations
5. **dynamic_forms** - Dynamic form generation
6. **message_queue_publisher** - Message queue publishing
7. **message_queue_consumer** - Message queue consumption
8. **tasklist** - Task management
9. **workflow_executor** - Workflow execution
10. **realtime_voice** - Voice processing
11. **gcp_environment** - Google Cloud Platform integration
12. **daytona_environment** - Daytona development environment
13. **remote** - Remote system operations

## Tool Development

### Creating New Tools

```python
from langswarm.v2.tools.base import BaseTool
from langswarm.v2.tools.interfaces import ToolType, ToolCapability

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            tool_id="my_custom_tool",
            name="My Custom Tool",
            description="Custom tool for specific operations",
            tool_type=ToolType.UTILITY,
            capabilities=[ToolCapability.READ, ToolCapability.WRITE]
        )
    
    async def execute_operation(self, data: str) -> Dict[str, Any]:
        """Execute custom operation"""
        # Implementation here
        return {"result": "success", "data": data}
```

### Adapting Existing Tools

For existing MCP tools, no changes are required. The adapter automatically:

1. Discovers methods and capabilities
2. Creates V2-compatible metadata
3. Provides execution interface
4. Handles lifecycle management

## Advanced Configuration

### Custom Tool Registration

```python
from langswarm.v2.tools.registry import ToolRegistry
from langswarm.v2.tools.adapters.mcp_adapter import create_mcp_adapter

# Manual tool registration
registry = ToolRegistry()
tool_instance = MyMCPTool(identifier="my_tool")
adapter = create_mcp_adapter(tool_instance, "my_tool")
registry.register(adapter)
```

### Provider-Specific Settings

```python
# OpenAI with custom settings
agent = await AgentBuilder('openai_agent') \
    .provider(ProviderType.OPENAI) \
    .model('gpt-4o') \
    .temperature(0.7) \
    .max_tokens(4096) \
    .tools(['bigquery_vector_search']) \
    .build()

# Anthropic with safety settings
agent = await AgentBuilder('claude_agent') \
    .provider(ProviderType.ANTHROPIC) \
    .model('claude-3-5-sonnet-20241022') \
    .tools(['sql_database']) \
    .build()
```

## Monitoring and Analytics

### Registry Statistics

```python
from langswarm.v2.tools.registry import ToolRegistry

registry = ToolRegistry()
stats = registry.get_statistics()
print(f"Total tools: {stats['total_tools']}")
print(f"Tool types: {stats['tool_types']}")
```

### Tool Health Checks

```python
# Check individual tool health
tool = registry.get_tool("bigquery_vector_search")
health = tool.health_check()
print(f"Tool status: {health['status']}")

# System-wide health check
from langswarm.v2.tools.registry import _global_service_registry
health = _global_service_registry.health_check()
```

## Error Handling

### Tool Failures

The system uses a "fail-fast" approach with comprehensive error reporting:

```python
try:
    result = await tool.execution.execute("method_name", parameters)
    if not result.success:
        print(f"Tool error: {result.error}")
except ToolError as e:
    print(f"Tool execution failed: {e}")
    print(f"Suggestion: {e.suggestion}")
```

### Provider Failures

Each provider handles errors gracefully:

```python
try:
    response = await agent.chat("Hello")
except Exception as e:
    # Provider-specific error handling
    print(f"Agent error: {e}")
```

## Migration Guide

### From V1 to V2

1. **Update imports**:
   ```python
   # Old
   from langswarm.core.agents import Agent
   
   # New  
   from langswarm.v2.core.agents.builder import AgentBuilder
   ```

2. **Use AgentBuilder**:
   ```python
   # Old
   agent = Agent(provider="openai", model="gpt-4")
   
   # New
   agent = await AgentBuilder('agent') \
       .provider(ProviderType.OPENAI) \
       .model('gpt-4o') \
       .build()
   ```

3. **Tool integration is automatic** - no manual setup required

### Backward Compatibility

- All existing MCP tools work without changes
- YAML workflows continue to work
- Legacy agent configurations are supported through adapters

## Best Practices

### Performance

1. **Tool Selection**: Only include necessary tools to reduce overhead
2. **Provider Choice**: Choose the optimal provider for your use case
3. **Caching**: Use tool result caching for expensive operations
4. **Batch Operations**: Group related tool calls when possible

### Security

1. **API Keys**: Store API keys securely using environment variables
2. **Tool Permissions**: Limit tool capabilities based on use case
3. **Input Validation**: Always validate tool inputs
4. **Monitoring**: Monitor tool usage and errors

### Scalability

1. **Registry Management**: Use separate registries for different environments
2. **Resource Limits**: Set appropriate timeouts and limits
3. **Load Balancing**: Distribute tool calls across multiple instances
4. **Health Monitoring**: Implement comprehensive health checks

## Troubleshooting

### Common Issues

1. **Tool Not Found**: Ensure tool is properly registered in registry
2. **Provider Error**: Check API keys and model availability
3. **Schema Mismatch**: Verify tool parameter formats
4. **Performance Issues**: Monitor tool execution times

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("langswarm.v2").setLevel(logging.DEBUG)

# Registry debug information
registry = ToolRegistry()
print(f"Registered tools: {list(registry._tools.keys())}")
```

## API Reference

### Core Classes

- `AgentBuilder`: Fluent API for creating agents
- `ToolRegistry`: Central tool management
- `MCPToolAdapter`: MCP tool adaptation
- `IToolInterface`: Tool interface specification
- `ToolMetadata`: Tool metadata management

### Provider Classes

- `OpenAIProvider`: OpenAI integration
- `AnthropicProvider`: Anthropic integration  
- `GeminiProvider`: Google Gemini integration
- `CohereProvider`: Cohere integration
- `MistralProvider`: Mistral integration
- `HuggingFaceProvider`: Hugging Face integration

## Examples

### Multi-Provider Tool Usage

```python
# Same tools, different providers
providers = [
    (ProviderType.OPENAI, "gpt-4o"),
    (ProviderType.ANTHROPIC, "claude-3-5-sonnet-20241022"),
    (ProviderType.GEMINI, "gemini-pro")
]

agents = []
for provider_type, model in providers:
    agent = await AgentBuilder(f'{provider_type.value}_agent') \
        .provider(provider_type) \
        .model(model) \
        .tools(['bigquery_vector_search']) \
        .build()
    agents.append(agent)

# All agents can use the same tools with provider-optimized formats
```

### Tool Composition

```python
# Combine multiple tools for complex workflows
agent = await AgentBuilder('data_analyst') \
    .provider(ProviderType.OPENAI) \
    .model('gpt-4o') \
    .tools([
        'bigquery_vector_search',  # Data retrieval
        'sql_database',            # Data processing  
        'codebase_indexer',        # Code analysis
        'filesystem'               # File operations
    ]) \
    .build()
```

## Conclusion

The LangSwarm V2 Tool System represents a breakthrough in LLM tool integration, providing:

- **Universal Compatibility**: Works with any LLM provider
- **Zero Migration Cost**: Existing tools work without changes
- **Optimal Performance**: Native format optimization for each provider
- **Enterprise Ready**: Comprehensive monitoring and error handling
- **Future Proof**: Extensible architecture for new providers and tools

For support and contributions, visit our [GitHub repository](https://github.com/langswarm/langswarm).
