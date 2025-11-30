# Building an Agent Organization with LangSwarm

LangSwarm allows you to create complex organizations of agents, ranging from persistent managers to temporary task-specific sub-agents. This guide explains how to structure and deploy these agents programmatically.

## 1. The Organizational Model

An effective agent organization typically consists of:

*   **Managers (Persistent)**: Long-running agents that oversee domains (e.g., "Engineering Manager"). They maintain state, have long-term memory, and coordinate others.
*   **Specialists (Persistent)**: Dedicated agents with specific tools (e.g., "Database Admin") that are always available.
*   **Sub-Agents (Temporary)**: Ephemeral agents spawned to handle a single task (e.g., "Research this specific topic") and then terminate.

## 2. Agent Lifecycle Management

Managing the difference between persistent and temporary agents is key to a scalable system.

### A. Persistent Agents (Services)
These agents are intended to run indefinitely, often as part of your application startup.

**Characteristics:**
*   **Identity**: Have a fixed `agent_id` and `name`.
*   **Memory**: Use `langswarm-memory` (Redis/Postgres) to persist state across restarts.
*   **Availability**: Always addressable by other agents.

**Implementation:**
```python
# In your application startup (e.g., main.py)
from langswarm.core.agents.builder import AgentBuilder
from langswarm.memory import create_memory_manager

# 1. Setup Persistent Memory
memory = create_memory_manager("redis", url="redis://localhost:6379")

# 2. Create Persistent Manager
engineering_manager = await (AgentBuilder()
    .litellm()
    .model("gpt-4o")
    .name("engineering_manager")
    .memory_manager(memory)  # Persist sessions
    .tools(["workflow_executor", "tasklist"])
    .build())

# 3. Register in a Global Registry (Your App Logic)
agent_registry = {
    "engineering_manager": engineering_manager
}
```

### B. Temporary Agents (Ephemerals)
These agents are created on-the-fly to perform a specific unit of work and are discarded afterwards.

**Characteristics:**
*   **Identity**: Generated UUIDs or temporary names.
*   **Memory**: In-memory only (RAM). Lost when the task finishes.
*   **Lifecycle**: Created -> Executed -> Garbage Collected.

**Implementation:**
```python
async def spawn_researcher(topic: str):
    # Create a disposable agent
    researcher = await (AgentBuilder()
        .litellm()
        .model("gpt-3.5-turbo")
        .name(f"researcher_{uuid.uuid4()}")
        .system_prompt(f"Research this topic: {topic}")
        .tools(["web_search"])
        .build())
    
    # Execute task
    result = await researcher.chat("Start research")
    
    # Agent goes out of scope and is cleaned up
    return result.content
```

## 3. Spawning Sub-Agents & Workflows

Managers can delegate tasks by spawning sub-agents. Instead of static configuration files, you can generate these programmatically.

### A. Dynamic Delegation (The "Spawn" Pattern)

Give your manager a tool that can call a Python function to create sub-agents.

**The Tool:**
```python
@tool
async def spawn_sub_agent(role: str, task: str) -> str:
    """Spawns a temporary agent to handle a specific task."""
    agent = await (AgentBuilder()
        .litellm()
        .model("gpt-4o")
        .system_prompt(f"You are a {role}.")
        .tools(["filesystem"]) # Give appropriate tools
        .build())
        
    response = await agent.chat(task)
    return response.content
```

**The Manager:**
```python
manager = await (AgentBuilder()
    .litellm()
    .model("gpt-4o")
    .system_prompt("You are a manager. Use 'spawn_sub_agent' to delegate tasks.")
    .add_tool(spawn_sub_agent) # Add the custom tool
    .build())

# Usage
# Manager: "I need someone to summarize this file."
# Action: Calls spawn_sub_agent(role="Summarizer", task="Summarize file.txt")
```

### B. Programmatic Workflows

You can define workflows using the fluent `WorkflowBuilder` API, which provides type safety and ease of use.

```python
from langswarm.core.workflows.builder import WorkflowBuilder, LinearWorkflowBuilder

# 1. Linear Workflow (Chain of Responsibility)
# Research -> Write -> Review
workflow = (LinearWorkflowBuilder()
    .start("research_pipeline", "Research Pipeline")
    .then_agent("research", "researcher", input_data="${user_input}")
    .then_agent("write", "writer", input_data="${research.output}")
    .then_agent("review", "reviewer", input_data="${write.output}")
    .build())

# 2. Complex Workflow (Parallel Execution)
# Extract -> (Analyze A + Analyze B) -> Synthesize
workflow = (WorkflowBuilder()
    .start("analysis_pipeline", "Complex Analysis")
    .add_agent_step("extract", "extractor", input_data="${user_input}")
    # Parallel steps depend on extraction
    .add_agent_step("analyze_a", "analyzer_a", 
                   input_data=lambda ctx: ctx.get_step_output("extract"),
                   dependencies=["extract"])
    .add_agent_step("analyze_b", "analyzer_b", 
                   input_data=lambda ctx: ctx.get_step_output("extract"),
                   dependencies=["extract"])
    # Synthesis depends on both analyzers
    .add_agent_step("synthesize", "synthesizer",
                   input_data=lambda ctx: {
                       "a": ctx.get_step_output("analyze_a"),
                       "b": ctx.get_step_output("analyze_b")
                   },
                   dependencies=["analyze_a", "analyze_b"])
    .set_execution_mode("parallel")
    .build())

# Execute using the workflow engine
from langswarm.core.workflows.engine import WorkflowEngine
engine = WorkflowEngine()
result = await engine.execute_workflow(workflow, {"user_input": "AI trends"})
```

## 4. Architectural Patterns

### The "Hub and Spoke"
*   **Hub**: A persistent "Dispatcher" agent.
*   **Spokes**: Temporary agents spawned for each request.
*   **Flow**: User -> Dispatcher -> Spawns Agent -> Agent Replies -> Dispatcher -> User.

### The "Department"
*   **Head**: Persistent Manager (e.g., CTO).
*   **Leads**: Persistent Sub-Managers (e.g., Frontend Lead, Backend Lead).
*   **Workers**: Temporary agents spawned by Leads for specific tickets.

## Summary

| Feature | Persistent Agents | Temporary Agents |
| :--- | :--- | :--- |
| **Use Case** | Managers, Domain Experts, Routers | Single Tasks, Parallel Jobs, Research |
| **Creation** | At App Startup | On-Demand (Runtime) |
| **Memory** | Persistent (Redis/DB) | Ephemeral (RAM) |
| **Cost** | Higher (Always running/loaded) | Lower (Only runs when needed) |
