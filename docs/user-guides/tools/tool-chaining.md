---
title: "Tool Chaining"
description: "Sequential tool execution patterns"
---

# 🔗 Tool Chaining

Tool chaining allows complex tasks to be broken down into sequence of operations. LangSwarm supports two patterns for chaining: **Natural Chaining** (Agentic) and **Explicit Chaining** (Workflow).

## 🧠 Natural Chaining (Agentic)

Modern agents automatically chain tools based on their reasoning loop (ReAct). You don't need to configure this; simply give the agent the tools it needs.

### How it works
1.  **Thought**: "I need to check the logs, but I don't know the log file path."
2.  **Action 1**: Call `filesystem.list_files("/var/log")`.
3.  **Observation**: "Found error.log, access.log".
4.  **Action 2**: Call `filesystem.read_file("/var/log/error.log")`.
5.  **Final Answer**: "I found the error in error.log..."

### Setup
Just provide multiple tools to the agent.

```python
agent = await (AgentBuilder("debugger")
    .add_mcp_server(name="fs", command="uvx", args=["mcp-server-filesystem", "."])
    .add_mcp_server(name="git", command="uvx", args=["mcp-server-git", "."])
    .build())

# Agent naturally chains: List Files -> Read File -> Git Blame
await agent.chat("Find who introduced the bug in the auth module.")
```

## 📋 Explicit Chaining (Workflow)

For deterministic processes, you can chain agents/tools explicitly in a Workflow. This is useful when you want to enforce a specific pipeline steps.

### Using WorkflowBuilder

Use `WorkflowBuilder` to pass outputs from one step as inputs to the next.

```python
from langswarm.core.workflows import WorkflowBuilder

workflow = (WorkflowBuilder("research_pipeline")
    # Step 1: Search for topic
    .add_step(
        id="search",
        agent="researcher",
        task="Find top 3 articles about: ${input}"
    )
    
    # Step 2: Summarize (Input is Step 1's output)
    .add_step(
        id="summarize",
        agent="writer",
        task="Summarize these articles: ${search.output}"
    )
    .build())

# Run the chain
result = await workflow.run("Quantum Computing")
```

## ⚡ Comparison

| Feature | Natural Chaining | Explicit Chaining |
| :--- | :--- | :--- |
| **Driver** | Agent (LLM Reasoning) | Workflow Engine (Code) |
| **Flexibility** | High (Adaptable) | Low (Deterministic) |
| **Use Case** | Exploration, Debugging | ETL, Reports, Batch Jobs |
| **Setup** | Zero Config | Requires Definition |

Most users should start with **Natural Chaining**. Use Explicit Chaining only when you need strict process control.
