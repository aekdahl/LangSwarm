---
title: "Local Tools (MCP)"
description: "Run tools locally via stdio"
---

# 🔧 Local Tools (MCP)

LangSwarm supports the **Model Context Protocol (MCP)**, allowing agents to connect to tools running locally on your machine via standard input/output (`stdio`). This enables zero-latency access to your filesystem, databases, or custom scripts without exposing them to the internet.

## 🚀 Quick Start

Use `uvx` (from the `uv` package manager) to instantly run standard MCP servers.

```python
from langswarm.core.agents import AgentBuilder

agent = await (AgentBuilder("sysadmin")
    .openai()
    .model("gpt-4o")
    
    # 1. Connect to Local Filesystem Server
    .add_mcp_server(
        name="filesystem",
        command="uvx",
        args=["-q", "mcp-server-filesystem", "/Users/alex/Desktop"]
    )
    
    # 2. Connect to Local SQLite
    .add_mcp_server(
        name="sqlite",
        command="uvx",
        args=["-q", "mcp-server-sqlite", "--db-path", "./test.db"]
    )
    .build())

await agent.chat("List files in the Desktop folder")
```

## 📦 Running Custom Python Tools

You can run your own Python scripts as MCP servers easily.

### 1. Create a Tool Script
Create a file `my_tool.py` that uses the `mcp` library:

```python
# my_tool.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my_tool")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

### 2. Connect Agent
Connect your agent to run this script directly.

```python
agent = await (AgentBuilder("math_agent")
    .add_mcp_server(
        name="my_math_tool",
        command="python", # Or "uv", "python3"
        args=["my_tool.py"]
    )
    .build())

await agent.chat("What is 5 + 10?")
```

## 🛠️ Configuration Directory

For persistent setups, you can define servers in `~/.langswarm/mcp_settings.json`.

```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    }
  }
}
```

Then load them automatically:

```python
agent = await (AgentBuilder("developer")
    .load_mcp_settings() # Loads from default JSON location
    .build())
```

## 🧩 Environment Variables

Pass environment variables to your local servers (e.g. for API keys).

```python
agent = await (AgentBuilder("cloud_agent")
    .add_mcp_server(
        name="aws_tools",
        command="uvx",
        args=["mcp-server-aws"],
        env={"AWS_PROFILE": "dev-profile"}
    )
    .build())
```

## 🔍 Debugging

If a tool isn't working, check the stdio logs.

```python
# Enable debug logging for MCP transport
import logging
logging.getLogger("langswarm.mcp").setLevel(logging.DEBUG)
```