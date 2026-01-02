# V2 Automatic Tool Injection

LangSwarm V2 provides **automatic tool injection** for agents, eliminating the need for manual tool configuration. When tools are specified in AgentBuilder or YAML workflows, they are automatically injected into the agent's system prompt with proper definitions and calling instructions.

## Key Features

- ✅ **Zero Manual Configuration**: Just specify tool names, injection happens automatically
- ✅ **Safety First**: Only V2 registry tools are injected (external tools ignored)
- ✅ **YAML Integration**: Works seamlessly with workflow YAML files
- ✅ **Provider Agnostic**: Works with all V2 agent providers (OpenAI, Anthropic, etc.)
- ✅ **Error Resilient**: Tool injection failures don't break agent creation

## AgentBuilder Usage

### Basic Tool Injection
```python
from langswarm.core.agents import AgentBuilder, AgentProvider

# Automatic tool injection
agent = await AgentBuilder()
    .provider(AgentProvider.OPENAI)
    .model("gpt-4o")
    .system_prompt("You are a helpful assistant.")
    .tools(["bigquery_vector_search", "file_operations"])  # 🎯 AUTO-INJECTION!
    .build()

# Tools are now automatically injected into system prompt!
print(f"Tools enabled: {agent.configuration.tools_enabled}")
print(f"Available tools: {agent.configuration.available_tools}")
```

### What Happens Automatically
1. **Tool Discovery**: V2 registry is checked for each tool name
2. **Metadata Extraction**: Tool descriptions, parameters, and methods are extracted
3. **System Prompt Enhancement**: Tool definitions and calling format are added
4. **Configuration Update**: Agent configuration is updated with tool information
5. **Safety Filtering**: Only V2 registry tools are included (external tools ignored)

### Synchronous Alternative
```python
# If you need synchronous build (without automatic injection)
agent = AgentBuilder()
    .tools(["bigquery_vector_search"])
    .build_sync()  # No auto-injection
```

## YAML Workflow Integration

### Agent Tool Configuration
```yaml
# workflow.yaml
agents:
  search_assistant:
    provider: openai
    model: gpt-4o-mini
    system_prompt: |
      You are a helpful search assistant.
    tools:  # 🎯 AUTOMATIC injection happens here!
      - bigquery_vector_search
      - file_operations
      - web_search  # External tool (safely ignored)
    
  simple_agent:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    # No tools specified - no injection
```

### Workflow Usage Discovery
```yaml
workflows:
  example_workflow:
    steps:
      - id: search_step
        function: langswarm.core.utils.workflows.functions.mcp_call
        args:
          mcp_url: "local://bigquery_vector_search"  # Auto-discovered
          payload: {...}
      
      - id: agent_step
        agent: search_assistant  # Will auto-get bigquery_vector_search tool
        input: "Search for information about ${user_query}"
```

### Loading Workflows with Auto-Injection
```python
from langswarm.core.workflows import load_yaml_workflows

# Automatic tool injection during workflow loading
workflows = await load_yaml_workflows("path/to/workflow.yaml")

# All agents with tools specified will have them auto-injected
```

## System Prompt Enhancement

When tools are automatically injected, the agent's system prompt is enhanced with:

### Tool Definitions
```
## Available Tools

### bigquery_vector_search
**Description:** Search for similar content in BigQuery vector database
**Methods:** similarity_search, get_content, list_datasets
**Parameters:** {
  "type": "object",
  "properties": {
    "query": {"type": "string", "description": "Search query"},
    "limit": {"type": "number", "description": "Max results"}
  },
  "required": ["query"]
}
```

### Tool Call Format
```
## Tool Call Format

To use a tool, respond with:
```json
{
  "tool_call": {
    "name": "tool_name",
    "method": "method_name", 
    "parameters": {
      "param1": "value1"
    }
  }
}
```
```

## Implementation Details

### Tool Integration Process
1. **Registry Check**: `tool_registry.get_tool(tool_name)`
2. **Metadata Extraction**: Tool description, methods, parameters
3. **Prompt Building**: Structured tool documentation generation
4. **System Prompt Injection**: Append to existing system prompt
5. **Configuration Update**: Mark tools as enabled

### Safety Mechanisms
```python
async def _filter_available_tools(self, tool_names: List[str]) -> List[str]:
    """Filter to only include V2 registry tools (excludes external)"""
    available_tools = []
    for tool_name in tool_names:
        tool = await self.tool_registry.get_tool(tool_name)
        if tool:  # Only V2 registry tools
            available_tools.append(tool_name)
    return available_tools
```

### Error Handling
- Tool injection failures don't break agent creation
- Missing tools are logged as warnings
- External tools are safely ignored
- Graceful degradation if registry unavailable

## Migration from Manual Injection

### Before (Manual)
```python
# Old way - manual injection required
from langswarm.core.agents.tool_integration import AgentToolIntegrator

agent = AgentBuilder().build()
integrator = AgentToolIntegrator()
await integrator.inject_tools_into_agent(agent, ["bigquery_vector_search"])
```

### After (Automatic)
```python
# New way - automatic injection
agent = await AgentBuilder()
    .tools(["bigquery_vector_search"])  # 🎯 That's it!
    .build()
```

## Best Practices

### 1. Use Descriptive Tool Names
```python
# Good - clear tool names
.tools(["bigquery_vector_search", "document_processor", "web_scraper"])

# Avoid - generic names
.tools(["search", "process", "scrape"])
```

### 2. Specify Relevant Tools Only
```python
# Good - only tools the agent needs
.tools(["bigquery_vector_search"])

# Avoid - kitchen sink approach
.tools(["tool1", "tool2", "tool3", "tool4", "tool5"])
```

### 3. Handle External Tools Gracefully
```yaml
agents:
  my_agent:
    tools:
      - bigquery_vector_search  # V2 registry tool (will inject)
      - external_api_tool       # External tool (safely ignored)
      - custom_tool            # Custom tool (ignored if not in registry)
```

### 4. Test Tool Integration
```python
# Verify tools were injected
agent = await AgentBuilder().tools(["bigquery_vector_search"]).build()

assert agent.configuration.tools_enabled == True
assert "bigquery_vector_search" in agent.configuration.available_tools
assert "bigquery_vector_search" in agent.configuration.system_prompt
```

## Troubleshooting

### Tool Not Found
```
⚠️ Tool 'my_tool' not found in V2 registry (may be external)
```
**Solution**: Ensure tool is registered in V2 registry or check tool name spelling.

### No Tools Injected
```python
# Check if tools were filtered out
integrator = AgentToolIntegrator()
available = await integrator._filter_available_tools(["my_tool"])
print(f"Available tools: {available}")
```

### System Prompt Not Updated
```python
# Verify automatic injection occurred
print(f"System prompt: {agent.configuration.system_prompt}")
print(f"Tools enabled: {agent.configuration.tools_enabled}")
```

## Advanced Usage

### Custom Tool Integration
```python
from langswarm.core.agents.tool_integration import AgentToolIntegrator

# Manual integration for special cases
integrator = AgentToolIntegrator()
await integrator.inject_tools_into_agent(agent, ["custom_tool"])
```

### Workflow Pre-processing
```python
from langswarm.core.agents.tool_integration import auto_inject_tools_from_yaml

# Pre-process YAML before loading
with open("workflow.yaml") as f:
    yaml_content = yaml.safe_load(f)

# Apply automatic tool injection
enhanced_content = await auto_inject_tools_from_yaml(yaml_content)
```

## See Also

- [V2 Agent System Overview](../agents/overview.md)
- [V2 Tool System](../tools/overview.md) 
- [YAML Workflow Migration](../workflows/yaml-migration.md)
- [Agent Provider Configuration](../agents/providers.md)

