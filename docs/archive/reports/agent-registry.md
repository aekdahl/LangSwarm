# Agent Registry Guide

The Agent Registry provides centralized management for multi-agent systems with hierarchy support and persistence.

## Quick Start

```python
from langswarm.core.agents import (
    AgentBuilder,
    register_agent,
    get_agent,
    list_agents,
    save_registry,
    load_registry,
    export_registry,
    import_registry,
    get_agent_hierarchy
)
```

## Creating and Registering Agents

```python
# Create agents programmatically
supervisor = await AgentBuilder() \
    .openai() \
    .model("gpt-4o") \
    .name("supervisor") \
    .system_prompt("You coordinate a team of specialists.") \
    .build()

researcher = await AgentBuilder() \
    .anthropic() \
    .model("claude-sonnet-4-20250514") \
    .name("researcher") \
    .build()

writer = await AgentBuilder() \
    .openai() \
    .model("gpt-4o") \
    .name("writer") \
    .build()

# Register with hierarchy
register_agent(supervisor)  # Root agent
register_agent(researcher, parent_id="supervisor")  # Child of supervisor
register_agent(writer, parent_id="supervisor")  # Child of supervisor
```

## Using Registered Agents

```python
# Get agent by ID
agent = get_agent("supervisor")
response = await agent.chat("Hello!")

# List all agent IDs
agents = list_agents()  # ["supervisor", "researcher", "writer"]

# Get hierarchy tree
hierarchy = get_agent_hierarchy()
# {
#   "agents": [{
#     "id": "supervisor",
#     "name": "supervisor", 
#     "children": [
#       {"id": "researcher", ...},
#       {"id": "writer", ...}
#     ]
#   }],
#   "total_agents": 3
# }
```

## Persistence

### Option 1: File-based (YAML/JSON)

```python
# Save to file
save_registry("agents.yaml")

# Load on startup
await load_registry("agents.yaml")
```

### Option 2: Database (Firestore, MongoDB, Redis, etc.)

```python
# Export as list of dicts
configs = export_registry()

# Save to Firestore
for config in configs:
    db.collection('agents').document(config['id']).set(config)

# Load from Firestore
configs = [doc.to_dict() for doc in db.collection('agents').stream()]
await import_registry(configs)
```

## Hierarchy Functions

| Function | Description |
|----------|-------------|
| `get_agent_children(id)` | Get child agents |
| `get_agent_parent(id)` | Get parent agent |
| `get_root_agents()` | Get agents with no parent |
| `get_agent_hierarchy()` | Get full tree structure |

## Notes

- **API keys** are NOT saved - agents use environment variables when restored
- **Parent must exist** before registering children
- Registry is a **singleton** - same instance across your application
