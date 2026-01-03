---
title: "Response Modes"
description: "Control how agents communicate and use tools"
---

# 🗣️ Response Modes

Control how your agents deliver responses, especially when they are using tools.

## 🔄 Modes Overview

LangSwarm supports different response strategies to fit your user interface needs.

| Mode | Description | Best For |
|------|-------------|----------|
| `streaming` | **Default**. Streams text token-by-token. Tool status is emitted as events. | Chat interfaces, CLIs |
| `integrated` | Waits for tool execution to finish, then delivers a single final answer. | APIs, Reports, Batch jobs |
| `json` | Forces the output to be strictly valid JSON. | Data extraction, Pipelines |

## 🌊 Streaming Mode (Default)

Streaming provides the best perceived latency. Users see the thought process and tool execution in real-time.

```python
agent = await AgentBuilder("bot").openai().model("gpt-4o").build()

# Stream the response
async for chunk in agent.chat_stream("Check the weather in Tokyo"):
    print(chunk, end="", flush=True)
```

**What happens:**
1.  Agent says: *"Checking weather..."* (Streamed)
2.  **Tool Event**: `weather_tool.check("Tokyo")` (Emitted)
3.  Agent says: *"It's currently 22°C and sunny in Tokyo."* (Streamed)

## 📦 Integrated Mode

Use this when you need a clean, final answer without the intermediate noise of tool execution. The agent "thinks" internally and only returns the result.

```python
agent = await (AgentBuilder("api_bot")
    .openai()
    .model("gpt-4o")
    .response_mode("integrated") # output is fully formed before returning
    .build())

response = await agent.chat("Summarize the latest 3 emails")
# Returns only the final summary string, after all tools have run.
print(response)
```

## 🧱 JSON Mode (Structured Output)

Force the agent to output strict JSON. Crucial for reliable data pipelines.

```python
agent = await (AgentBuilder("parser")
    .openai()
    .model("gpt-4o")
    .response_format("json_object") # Enforce JSON
    .system_prompt("You are a data extractor. Output JSON only.")
    .build())

response = await agent.chat(
    "Extract user info: John Doe, 30, Engineer",
    response_model={ # Optional: Pydantic schema validation
        "name": "str",
        "age": "int",
        "role": "str"
    }
)

print(response)
# {
#   "name": "John Doe",
#   "age": 30,
#   "role": "Engineer"
# }
```

## ⚙️ Configuration

Configure response behavior directly in the builder:

```python
agent = await (AgentBuilder("custom")
    .openai()
    .streaming(True)                # Enable/Disable streaming
    .response_mode("integrated")    # Set specific mode
    .build())
```