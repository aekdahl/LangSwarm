---
title: "Agentic Selection"
description: "How agents reason about and select MCP tools"
---

# 🧠 Agentic Tool Selection

Modern LLMs (like GPT-4o, Claude 3.5 Sonnet) are capable of sophisticated reasoning. Instead of manually mapping user inputs to tool parameters, LangSwarm allows agents to **autonomously select** the correct MCP tool and populate its arguments based on semantic understanding.

## 🎯 How it Works

1.  **Discovery**: The Agent inspects the `description` and `schema` of all connected MCP tools.
2.  **Reasoning**: It analyzes the user's request (e.g., "Find high-margin customers").
3.  **Selection**: It chooses the tool that best fits the goal (e.g., `database.query`) and generates the necessary SQL/parameters.

## ✍️ Writing Good Tool Descriptions

The key to accurate tool selection is writing clear, descriptive prompts for your tools within the MCP Server.

### Bad Description
```python
@mcp.tool()
def query(sql: str) -> str:
    """Runs a query.""" 
    # vague! agent doesn't know what tables exist
    ...
```

### Good Description
```python
@mcp.tool()
def query_customers_db(sql: str) -> str:
    """
    Executes a read-only SQL query against the 'customers' database.
    Available tables:
    - users (id, name, email, signup_date)
    - orders (id, user_id, amount, margin, status)
    
    Use this to answer questions about customer spending and margins.
    """
    ...
```

With the "Good" description, an agent asked to "Find high-margin customers" will know exactly how to construct the query `SELECT * FROM orders WHERE margin > ...`.

## 🧩 Hints & Reasoning

Sometimes an agent needs guidance. You can inject reasoning hints into the **System Prompt** without changing the tools themselves.

```python
agent = await (AgentBuilder("analyst")
    .system_prompt("""
        You are a Data Analyst.
        
        STRATEGY:
        1. When searching for files, always use 'grep' before 'read_file'.
        2. When querying databases, limit results to 10 rows first.
    """)
    .add_mcp_server(...) 
    .build())
```

## 🔄 Replaces "Intent-Based" Calling

Older systems required agents to emit a vague "Intent" (e.g., `{"intent": "find users"}`) which was then mapped by code to a specific function.

With LangSwarm + MCP, this is obsolete. The Agent **directly calls** the correct tool with the correct parameters, reducing latency and complexity.
