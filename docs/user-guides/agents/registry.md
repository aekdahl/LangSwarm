---
title: "Agent Registry & Hierarchy"
description: "Manage complex multi-agent systems with the centralized registry"
---

# 🏛️ Agent Registry

For complex applications with many agents, LangSwarm provides a **Global Agent Registry**. This allows you to centralize agent management, define hierarchical relationships, and persist agent configurations.

## 🚀 Quick Start

Register agents to access them globally across your application.

```python
from langswarm.core.agents import AgentBuilder, register_agent, get_agent

# 1. Create and Register
await (AgentBuilder("researcher")
    .openai()
    .model("gpt-4o")
    .register())  # .register() automatically adds to global registry

# 2. Retrieve anywhere in your app
agent = get_agent("researcher")
await agent.chat("Find the latest news")
```

## 🌳 Hierarchy (Supervisors & Workers)

You can organize agents into a tree structure. This is useful for "Supervisor-Worker" patterns or organizational modeling.

```python
from langswarm.core.agents import register_agent, get_agent_children

# 1. Create Hierarchy
# Root Agent (Supervisor)
manager = await AgentBuilder("manager").system_prompt("You coordinate the team.").build()
register_agent(manager)

# Child Agents (Workers)
coder = await AgentBuilder("coder").system_prompt("Write python code.").build()
tester = await AgentBuilder("tester").system_prompt("Write tests.").build()

# Register as children of 'manager'
register_agent(coder, parent_id="manager")
register_agent(tester, parent_id="manager")

# 2. Inspect Hierarchy
children = get_agent_children("manager")
# Returns [coder_agent, tester_agent]
```

## 💾 Persistence

Save and load your entire agent fleet configuration. This is crucial for applications that allow users to dynamic create/customize agents.

### File Storage
Save the registry to a simple JSON/YAML file.

```python
from langswarm.core.agents import save_registry, load_registry

# Save all registered agents to disk
save_registry("my_swarm_config.json")

# ... later, on app startup ...

# Restore all agents
await load_registry("my_swarm_config.json")
```

### Database Storage
Export the registry state to store in your own database (Postgres, MongoDB, etc).

```python
from langswarm.core.agents import export_registry, import_registry

# Export as list of dictionaries
agent_configs = export_registry()
# db.agents.insert_many(agent_configs)

# Import back into registry
# configs = db.agents.find({})
await import_registry(configs)
```

## 🏥 Health & Monitoring

Monitor the status of your swarm.

```python
from langswarm.core.agents import agent_health_check, list_agent_info

# Check health of all registered agents (connectivity, etc)
report = await agent_health_check()
print(f"Healthy: {report.healthy_count}, Errors: {report.errors}")

# List all agents with metadata
for info in list_agent_info():
    print(f"{info.id}: {info.provider} ({info.status})")
```

## API Reference

| Function | Description |
| :--- | :--- |
| `register_agent(agent, parent_id=None)` | Register an existing agent instance. |
| `get_agent(id)` | Retrieve an agent instance by ID. |
| `list_agents()` | List all registered agent IDs. |
| `get_agent_hierarchy()` | Return the full tree structure of agents. |
| `save_registry(path)` | Save registry configuration to a file. |
| `load_registry(path)` | Load registry configuration from a file. |
