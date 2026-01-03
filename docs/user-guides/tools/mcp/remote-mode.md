---
title: "Remote Tools (MCP)"
description: "Connect to remote MCP servers via SSE"
---

# ☁️ Remote Tools (MCP)

LangSwarm supports connecting to remote MCP servers over HTTP/HTTPS using the standard **Server-Sent Events (SSE)** transport. This allows you to securely access tools hosted on cloud services, internal microservices, or third-party APIs.

## 🚀 Quick Connect

Connect to any remote MCP server using its SSE endpoint URL.

```python
from langswarm.core.agents import AgentBuilder

agent = await (AgentBuilder("cloud_agent")
    .openai()
    .model("gpt-4o")
    
    # Connect via URL (SSE Transport)
    .add_mcp_server(
        name="weather_service",
        url="https://api.weather-service.com/mcp/sse",
        headers={"X-API-Key": "your-api-key"}
    )
    .build())

await agent.chat("What is the weather in Tokyo?")
```

## 🔒 Authentication

Pass custom headers for authentication (Bearer tokens, API keys).

```python
agent = await (AgentBuilder("enterprise_agent")
    .add_mcp_server(
        name="internal_db",
        url="https://internal-api.corp.com/mcp",
        headers={
            "Authorization": "Bearer eyJhbGciOi...",
            "X-Tenant-ID": "tenant-123"
        }
    )
    .build())
```

## 🌐 Transport Protocols

LangSwarm automatically detects and handles the standard MCP handshake:

1.  **SSE Connection**: Connects to the main SSE endpoint for real-time events.
2.  **POST Endpoint**: Uses the associated POST endpoint (discovery via SSE) for sending client requests.

You only need to provide the initial SSE URL.

## ⚠️ Security Best Practices

When connecting to remote servers:

1.  **HTTPS Only**: Always use `https://` for remote connections to protect data in transit.
2.  **Secret Management**: Never hardcode API keys. Use `os.getenv()`:
    ```python
    .add_mcp_server(
        name="secure_service",
        url=os.getenv("MCP_URL"),
        headers={"Authorization": f"Bearer {os.getenv('MCP_TOKEN')}"}
    )
    ```
3.  **Trust**: Only connect to trusted MCP servers. Agents grant these servers ability to execute code or access data depending on the tools they expose.

## 🔧 Debugging Remote Connections

If connection fails:

1.  Check if the server is reachable (`curl -v https://...`).
2.  Ensure it supports the **Model Context Protocol** version 1.0+.
3.  Enable debug mode to see the handshake logs:

```python
import logging
logging.getLogger("langswarm.mcp.client").setLevel(logging.DEBUG)
```