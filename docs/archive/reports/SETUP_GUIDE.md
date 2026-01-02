# 🚀 LangSwarm Setup Guide - Code-First Configuration

This guide covers everything you need to know to set up and use LangSwarm with pure Python code. No YAML files required.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Creating Agents](#creating-agents)
4. [Memory & Sessions](#memory--sessions)
5. [Tools](#tools)
6. [Workflows](#workflows)
7. [Advanced Configuration](#advanced-configuration)

---

## Installation

```bash
# Basic installation (includes OpenAI by default)
pip install langswarm

# With optional extras
pip install langswarm[bigquery]       # For BigQuery Vector Search
pip install langswarm[daytona]        # For Daytona sandbox environments
pip install langswarm[opentelemetry]  # For observability/tracing

# Full installation with all extras
pip install langswarm[all]
```

> **Note:** Core AI providers (OpenAI, Anthropic, etc.) are included in the base installation.

### Environment Variables

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

---

## Quick Start

### 30-Second Example

```python
import asyncio
from langswarm import create_agent

async def main():
    # Create an agent
    agent = create_agent(
        model="gpt-4",
        system_prompt="You are a helpful assistant"
    )
    
    # Chat with it
    response = await agent.chat("Hello! What can you help me with?")
    print(response)

asyncio.run(main())
```

---

## Creating Agents

### Method 1: Simple API (Recommended for Beginners)

```python
from langswarm import create_agent

# Minimal agent
agent = create_agent(model="gpt-3.5-turbo")

# Agent with options
agent = create_agent(
    model="gpt-4",
    system_prompt="You are a coding expert",
    memory=True,              # Enable conversation memory
    tools=["filesystem"],     # Add tools
    stream=False,             # Disable streaming
    track_costs=True          # Track token usage
)
```

### Method 2: Builder Pattern (Recommended for Advanced Use)

```python
from langswarm.core.agents import AgentBuilder

# Fluent builder pattern
agent = await (
    AgentBuilder()
    .name("my-assistant")
    .openai()                              # Use OpenAI provider
    .model("gpt-4")
    .system_prompt("You are a helpful assistant")
    .memory_enabled(True, max_messages=100)
    .temperature(0.7)
    .max_tokens(4096)
    .build()
)

# With tools
agent = await (
    AgentBuilder()
    .name("code-assistant")
    .openai()
    .model("gpt-4")
    .tools(["filesystem", "web_search"])
    .max_tool_iterations(5)
    .build()
)
```

### Supported Providers

```python
from langswarm.core.agents import AgentBuilder

# OpenAI
agent = await AgentBuilder().openai().model("gpt-4").build()

# Anthropic
agent = await AgentBuilder().anthropic().model("claude-3-5-sonnet-20241022").build()

# Google Gemini
agent = await AgentBuilder().gemini().model("gemini-pro").build()

# Mistral
agent = await AgentBuilder().mistral().model("mistral-large").build()

# Cohere
agent = await AgentBuilder().cohere().model("command-r-plus").build()

# Local models (Ollama)
agent = await AgentBuilder().local("http://localhost:11434", "llama2:7b").build()
```

---

## Memory & Sessions

LangSwarm supports multiple memory backends:

**Core Backends (always available):**
1. **In-Memory** - Fast, ephemeral (lost when app closes)
2. **SQLite** - Persistent local storage (survives restarts)
3. **Redis** - Distributed persistent storage (multi-instance/production)

**Optional Backends (install separately):**
- **BigQuery** - Cloud-scale persistent storage on GCP (`pip install langswarm-memory[bigquery]`)
- **PostgreSQL** - Enterprise-grade relational storage (`pip install langswarm-memory[postgres]`)
- **MongoDB** - Document-based persistent storage (`pip install langswarm-memory[mongodb]`)
- **Elasticsearch** - Search-optimized storage (`pip install langswarm-memory[elasticsearch]`)

### In-Memory Only

```python
# Simple in-memory conversation history
agent = create_agent(model="gpt-4", memory=True)

# Conversations are remembered within the session
await agent.chat("My name is Alice")
await agent.chat("What's my name?")  # Agent remembers "Alice"
```

### Persistent Memory with MemoryManager

```python
from langswarm import create_agent
from langswarm.core.memory import create_memory_manager

# Create a persistent memory backend
manager = create_memory_manager("sqlite", db_path="conversations.db")
await manager.backend.connect()

# Create agent with persistent memory
agent = create_agent(
    model="gpt-4",
    memory_manager=manager,
    system_prompt="You are a helpful assistant"
)

# Chat with session persistence
response = await agent.chat("Hello!", session_id="user-123")

# Later, resume the same conversation
response = await agent.chat("What did I say earlier?", session_id="user-123")
```

### Memory Backends

```python
from langswarm.core.memory import create_memory_manager

# SQLite (persistent, local) - Recommended for single-instance apps
manager = create_memory_manager("sqlite", db_path="memory.db")

# Redis (persistent, distributed) - Recommended for multi-instance/production
manager = create_memory_manager("redis", host="localhost", port=6379)

# In-Memory (fast, ephemeral) - For testing/development only
manager = create_memory_manager("memory")

# Don't forget to connect!
await manager.backend.connect()
```

### Using Memory with Builder Pattern

```python
from langswarm.core.agents import AgentBuilder
from langswarm.core.memory import create_memory_manager

# Create memory manager
manager = create_memory_manager("sqlite", db_path="agent_memory.db")
await manager.backend.connect()

# Build agent with memory manager
agent = await (
    AgentBuilder()
    .name("persistent-assistant")
    .openai()
    .model("gpt-4")
    .memory_manager(manager)  # Attach memory manager
    .build()
)
```

---

## Tools

### Enabling Built-in Tools

```python
from langswarm.core.agents import AgentBuilder

agent = await (
    AgentBuilder()
    .openai()
    .model("gpt-4")
    .tools(["filesystem", "web_search"])
    .build()
)

# Agent can now read/write files and search the web
response = await agent.chat("Read the contents of README.md")
```

### Available Built-in Tools

LangSwarm includes both core built-in tools and MCP-compatible tools:

#### Core Built-in Tools

These ship with LangSwarm and require no additional setup:

| Tool Name | Description |
|-----------|-------------|
| `SystemStatusTool` | System health monitoring and status checks |
| `TextProcessorTool` | Text manipulation and processing utilities |
| `WebRequestTool` | HTTP requests and web API interactions |
| `FileOperationsTool` | File read/write/list operations |
| `ToolInspectorTool` | Introspect available tools and their capabilities |

#### MCP-Compatible Tools

These follow the Model Context Protocol and provide extended capabilities:

| Tool Name | Description |
|-----------|-------------|
| `filesystem` | Enhanced file and directory operations |
| `codebase_indexer` | Index and search codebases semantically |
| `sql_database` | Query SQL databases |
| `bigquery_vector_search` | Vector similarity search with BigQuery |
| `tasklist` | Manage task lists and todos |
| `workflow_executor` | Execute predefined workflows |
| `dynamic_forms` | Generate and process dynamic forms |
| `mcpgithubtool` | GitHub repository operations |
| `message_queue_publisher` | Publish to message queues (Pub/Sub, SQS) |
| `message_queue_consumer` | Consume from message queues |
| `gcp_environment` | Google Cloud Platform operations |
| `daytona_environment` | Secure cloud sandbox environments (Daytona) |
| `realtime_voice` | Real-time voice processing |
| `remote` | Connect to remote MCP servers |

### Tool Configuration

```python
agent = await (
    AgentBuilder()
    .openai()
    .model("gpt-4")
    .tools(["filesystem"])
    .tool_configs({
        "filesystem": {
            "allowed_paths": ["/home/user/projects"],
            "read_only": False
        }
    })
    .build()
)
```

### Custom Tools

```python
from langswarm.tools.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Does something useful"
        )
    
    async def run(self, params: dict) -> str:
        # Your tool logic here
        return f"Result: {params}"

# Register and use
from langswarm.tools.registry import ToolRegistry
registry = ToolRegistry()
registry.register_tool(MyCustomTool())
```

---

## Workflows

Workflows allow multiple agents to work together in sequence or parallel.

### Simple Sequential Workflow

```python
from langswarm import create_agent
from langswarm.core.agents import register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

# Create specialized agents
researcher = create_agent(
    model="gpt-4",
    system_prompt="You are a research specialist. Gather information."
)

writer = create_agent(
    model="gpt-4",
    system_prompt="You are a writer. Create engaging content."
)

# Register agents for workflow use
register_agent(researcher, "researcher")
register_agent(writer, "writer")

# Create workflow: researcher -> writer
workflow = create_simple_workflow(
    workflow_id="content-pipeline",
    name="Research and Write",
    agent_chain=["researcher", "writer"]
)

# Execute workflow
engine = get_workflow_engine()
result = await engine.execute_workflow(
    workflow,
    {"input": "Write about AI safety"}
)

print(result.result)  # Final output from writer
```

### Workflow with Shared Memory

All agents in a workflow can share the same memory:

```python
from langswarm.core.memory import create_memory_manager
from langswarm.core.workflows import get_workflow_engine

# Create shared memory
manager = create_memory_manager("sqlite", db_path="workflow_memory.db")
await manager.backend.connect()

# Execute workflow with shared memory
engine = get_workflow_engine()
result = await engine.execute_workflow(
    workflow,
    {"input": "Research quantum computing"},
    memory_manager=manager  # All agents share this memory
)
```

### Parallel Execution

```python
from langswarm.core.workflows import ExecutionMode

# Execute steps in parallel where possible
result = await engine.execute_workflow(
    workflow,
    {"input": "Analyze this data"},
    execution_mode=ExecutionMode.PARALLEL
)
```

---

## Advanced Configuration

### Streaming Responses

```python
# Simple API
agent = create_agent(model="gpt-4", stream=True)

async for chunk in agent.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)

# Builder pattern
agent = await (
    AgentBuilder()
    .openai()
    .model("gpt-4")
    .streaming(True)
    .build()
)

async for chunk in agent.stream_chat("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### Temperature and Sampling

```python
agent = await (
    AgentBuilder()
    .openai()
    .model("gpt-4")
    .temperature(0.7)       # Creativity (0.0 - 2.0)
    .top_p(0.9)             # Nucleus sampling
    .frequency_penalty(0.5) # Reduce repetition
    .presence_penalty(0.5)  # Encourage new topics
    .build()
)
```

### Timeouts and Retries

LangSwarm includes built-in retry logic with exponential backoff for transient failures.

```python
from langswarm.core.agents.base import AgentConfiguration

# Configure via AgentConfiguration
config = AgentConfiguration(
    provider=ProviderType.OPENAI,
    model="gpt-4",
    timeout=60,           # Request timeout in seconds
    retry_attempts=3,     # Number of retry attempts (default: 3)
    retry_delay=1.0       # Initial delay between retries in seconds (default: 1.0)
)

# Or use builder with timeout
agent = await (
    AgentBuilder()
    .openai()
    .model("gpt-4")
    .timeout(60)  # 60 second timeout
    .build()
)
```

**Retry behavior:**
- Retries are automatic for transient errors (rate limits, network issues)
- Uses exponential backoff: `retry_delay * (2 ** attempt)`
- Does not retry on authentication or validation errors

### Cost Tracking

```python
agent = create_agent(model="gpt-4", track_costs=True)

await agent.chat("Hello!")
await agent.chat("How are you?")

stats = agent.get_usage_stats()
print(f"Total tokens: {stats['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
```

---

## Complete Example

Here's a full example combining multiple features:

```python
import asyncio
from langswarm import create_agent
from langswarm.core.agents import AgentBuilder, register_agent
from langswarm.core.memory import create_memory_manager
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

async def main():
    # 1. Set up persistent memory
    memory = create_memory_manager("sqlite", db_path="app_memory.db")
    await memory.backend.connect()
    
    # 2. Create specialized agents
    researcher = await (
        AgentBuilder()
        .name("researcher")
        .openai()
        .model("gpt-4")
        .system_prompt("You research topics thoroughly and provide detailed findings.")
        .memory_manager(memory)
        .tools(["web_search"])
        .build()
    )
    
    writer = await (
        AgentBuilder()
        .name("writer")
        .openai()
        .model("gpt-4")
        .system_prompt("You write clear, engaging content based on research.")
        .memory_manager(memory)
        .build()
    )
    
    # 3. Register agents
    register_agent(researcher, "researcher")
    register_agent(writer, "writer")
    
    # 4. Create workflow
    workflow = create_simple_workflow(
        workflow_id="content-creation",
        name="Research & Write",
        agent_chain=["researcher", "writer"]
    )
    
    # 5. Execute workflow
    engine = get_workflow_engine()
    result = await engine.execute_workflow(
        workflow,
        {"input": "Write a blog post about sustainable energy"},
        memory_manager=memory
    )
    
    print("=== Final Output ===")
    print(result.result)
    
    # 6. Check execution details
    print(f"\nStatus: {result.status}")
    print(f"Execution time: {result.execution_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

- Check out the [examples/simple/](../../examples/simple/) directory for more working examples
- Explore the [templates/](../../templates/) directory for ready-to-use configurations
- Read the [Multi-Agent Orchestration Guide](../MULTI_AGENT_ORCHESTRATION_GUIDE.md) for advanced patterns

---

## Troubleshooting

### API Key Not Found

```
ValueError: OpenAI API key is required
```

**Solution:** Set your API key as an environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

### Tool Not Found

```
ValueError: Requested tools not found in registry: ['my_tool']
```

**Solution:** Ensure the tool is registered before building the agent:
```python
from langswarm.tools.registry import ToolRegistry
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()  # Load built-in tools
```

### Memory Session Not Persisting

**Solution:** Make sure you:
1. Connect the memory backend: `await manager.backend.connect()`
2. Use the same `session_id` across calls
3. Pass the `memory_manager` to the agent

---

**Happy coding with LangSwarm!** 🎉

