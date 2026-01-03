---
title: "Agents vs Workflows"
description: "Choosing between single agents and multi-agent swarms"
---

# ⚔️ Agents vs Workflows

When to use a single `Agent` and when to orchestrate a `Workflow`.

| Feature | 🤖 Single Agent | 🐝 Swarm Workflow |
| :--- | :--- | :--- |
| **Best For** | Chatbots, Simple Tasks, specific tools | Complex pipelines, Research, Reporting |
| **Control** | Autonomous (Agent decides) | Orchestrated (You define the flow) |
| **Complexity** | Low (1 Agent) | High (Multiple Agents + Logic) |
| **Output** | Single Message stream | Final Artifact (Report, Code, etc.) |

## 🤖 Single Agent

Use a direct agent when you need a **conversational interface** or a **single specialized worker**. The agent autonomously decides which tools to call to answer the user.

**Use Case:** Customer Support Bot

```python
# The agent decides: Search KB -> Read Info -> Reply
agent = await AgentBuilder("support").tools(["kb_search"]).build()

response = await agent.chat("How do I reset my password?")
```

**Pros:**
- ✅ Simple to set up
- ✅ Natural conversation flow
- ✅ Great for "General Purpose" tasks

## 🐝 Swarm Workflow

Use a workflow when you need a **deterministic process** involving multiple specialists. You define the chain of command.

**Use Case:** Financial Analysis Pipeline

```python
# Step 1: Reader extracts data
reader = await AgentBuilder("reader").build()

# Step 2: Analyst processes it
analyst = await AgentBuilder("analyst").build()

# Orchestration: Reader -> Analyst
workflow = create_workflow("analysis", agent_chain=["reader", "analyst"])

# The output of Reader flows directly into Analyst
result = await workflow.run(input_message="AAPL Earnings Report...")
```

**Pros:**
- ✅ Result quality is higher (specialists > generalists)
- ✅ Process is repeatable and auditable
- ✅ Better for complex, multi-step reasoning

## 🚀 When to Switch?

Start with a **Single Agent**. Switch to a **Workflow** when:

1.  **Context Limited**: The system prompt is getting too long/complex for one agent.
2.  **Hallucination**: The agent gets confused by trying to do too many different things (e.g., trying to be a Lawyer AND a Coder).
3.  **Process Control**: You need to enforce a specific sequence (e.g., "Research MUST happen before Writing").

## 🧩 Hybrid Approach

You can mix them! A "Manager Agent" can have a tool that triggers a "Workflow".

```python
# A Chatbot that can trigger a research workflow
agent = await (AgentBuilder("manager")
    .tools(["trigger_research_workflow"]) 
    .build())

# User: "Research the history of Rome"
# Agent -> Calls tool -> triggers Swarm -> Returns report
```
