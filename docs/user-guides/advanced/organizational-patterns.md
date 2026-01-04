# 🏗️ Organizational Patterns

LangSwarm is designed to support complex organizations of agents, not just single chat bots. This guide explains how to structure systems with Managers, Specialists, and Workers.

## 1. The Core Model

To build a scalable agency, you need two types of agents:

### 🏢 Persistent Agents (Managers)
*   **Role**: Coordinate work, maintain state, oversee domains.
*   **Lifespan**: Matches the application lifecycle.
*   **Memory**: Uses persistent storage (Redis/Postgres).

```python
manager = await (AgentBuilder()
    .name("eng_manager")
    .memory_manager(redis_memory)  # Persist across restarts
    .build())
```

### 👷 Ephemeral Agents (Workers)
*   **Role**: Perform a single unit of work (research, code generation).
*   **Lifespan**: Created on-demand, destroyed after task.
*   **Memory**: In-memory (RAM), lost after execution.

```python
worker = await (AgentBuilder()
    .name(f"worker_{uuid.uuid4()}") # Unique ID
    .system_prompt("You are a specialized researcher.")
    .build())
```

## 2. The "Spawn" Pattern

A powerful pattern is to give a Manager a tool that allows them to spawn their own sub-agents. This enables **Dynamic Delegation**.

### The Spawning Tool
```python
@tool
async def spawn_researcher(topic: str) -> str:
    """Spawns a temporary agent to research a topic."""
    agent = await (AgentBuilder()
        .model("gpt-3.5-turbo") # Cheaper model for sub-tasks
        .system_prompt("Summarize key findings.")
        .build())
    
    # Execute and return result
    response = await agent.chat(f"Research: {topic}")
    return response.content
```

### The Manager
```python
# The manager decides WHEN to spawn a researcher
manager = await (AgentBuilder()
    .system_prompt("Delegate research tasks using 'spawn_researcher'.")
    .add_tool(spawn_researcher)
    .build())
```

## 3. Programmatic Workflows

For structured processes, use the **Workflow Builders** to chain agents together with type safety.

### Linear Chains (Pipeline)
Best for: Review processes, content generation pipelines.

```python
from langswarm.core.workflows.builder import LinearWorkflowBuilder

workflow = (LinearWorkflowBuilder()
    .start("pipeline", "Blog Post Pipeline")
    .then_agent("draft", "writer_agent", input_data="${user_input}")
    .then_agent("critique", "critic_agent", input_data="${draft.output}")
    .then_agent("refine", "editor_agent", input_data="${critique.output}")
    .build())
```

### Complex Orchestration (DAGs)
Best for: Parallel processing, map-reduce operations.

```python
from langswarm.core.workflows.builder import WorkflowBuilder

workflow = (WorkflowBuilder()
    .start("analysis", "Parallel Analysis")
    .add_agent_step("extract", "extractor")
    # Run these two in parallel
    .add_agent_step("security_scan", "sec_bot", dependencies=["extract"])
    .add_agent_step("perf_scan", "perf_bot", dependencies=["extract"])
    # Wait for both
    .add_agent_step("report", "reporter", 
                   dependencies=["security_scan", "perf_scan"])
    .set_execution_mode("parallel")
    .build())
```

## Summary

| use Case | Pattern |
| :--- | :--- |
| **Simple Task** | Single Agent |
| **Complex Goal** | Manager + Dynamic Spawning |
| **Strict Process** | Linear Workflow |
| **High Throughput** | Parallel Workflow |
