---
title: "Tool Registry"
description: "Global tool management and automatic injection"
---

# 🧰 Tool Registry

The **Global Tool Registry** simplifies tool management by allowing you to register tools once and use them anywhere by name. This enables "Automatic Tool Injection" in agents.

## 🚀 Quick Start

Register a tool globally, then refer to it by string ID in your agents.

```python
from langswarm.tools import ToolRegistry
from langswarm.core.agents import AgentBuilder

# 1. Get the registry
registry = ToolRegistry()

# 2. Register a tool (e.g., a custom or MCP tool)
# Assuming 'fs_tool' is an initialized tool instance with id="filesystem"
registry.register(fs_tool)

# 3. Use in AgentBuilder by name string
agent = await (AgentBuilder("assistant")
    .tools(["filesystem"])  # ⚡ Automatic Injection!
    .build())
```

## 🔍 Automatic Discovery

LangSwarm automatically discovers and registers standard tools on startup, including:
-   **MCP Tools**: Standard tools found in `langswarm.tools.mcp`.
-   **Built-in Tools**: Common utilities provided by the framework.

This means standard tools like `filesystem` or `git` (if properly installed via MCP) are often available out-of-the-box without manual registration.

## 💉 Automatic Injection

When you pass strings to `.tools()`, `AgentBuilder` looks them up in the registry.

```python
# Pass a list of tool IDs
agent = await AgentBuilder() \
    .model("gpt-4o") \
    .tools(["web_search", "calculator", "filesystem"]) \
    .build()

# The builder automatically:
# 1. Finds tools in the registry
# 2. Injects their schemas into the Agent's System Prompt (or Provider config)
# 3. Wires up execution handling
```

## 🧰 Standard Tool Ecosystem

LangSwarm comes with a suite of production-ready MCP tools. You can register these by name:

| Tool ID | Description |
| :--- | :--- |
| `mcpfilesystem` | CRUD operations with GCS/S3 support |
| `mcpgithubtool` | Manage repos, issues, and PRs |
| `mcpcodebase_indexer` | Semantic code analysis and graph |
| `mcptasklist` | Persistent task tracking (Redis/SQL) |
| `mcpmessage_queue_publisher` | Publish to Redis/PubSub |
| `mcpmessage_queue_consumer` | Consume distributed tasks |
| `mcpworkflow_executor` | Run dynamic workflows |
| `mcpforms` | dynamic user input forms |
| `mcpremote` | Connect to external MCP servers |

**Example:**
```python
builder.tools([
    "mcpfilesystem", 
    "mcpgithubtool"
])
```

## 📦 Managing Custom Tools

You can register your own custom tools to make them available to all agents.

```python
from langswarm.tools import BaseTool, ToolRegistry

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "Does custom things")
    
    async def run(self, params):
        return "Done"

# Register globally
ToolRegistry().register(MyCustomTool())

# Now any agent can use it
agent = await AgentBuilder().tools(["my_tool"]).build()
```

## API Reference

| Function | Description |
| :--- | :--- |
| `ToolRegistry()` | Get the global singleton registry instance. |
| `registry.register(tool)` | Register a tool instance. Throws error if ID exists. |
| `registry.get_tool(id)` | Get a tool instance by ID. Returns `None` if missing. |
| `registry.list_tools()` | List all registered tools. |
| `registry.auto_populate_with_mcp_tools()` | Trigger auto-discovery of local MCP tools. |
