# Simple_Api API

**Module:** `langswarm.simple_api`

## Overview

Simple API for LangSwarm examples.

This provides a clean, beginner-friendly interface for the most common use cases.

## Table of Contents

### Functions
- [create_agent](#create_agent)
- [create_workflow](#create_workflow)
- [load_config](#load_config)
- [require_package](#require_package)

### Classes
- [Agent](#agent)
- [Config](#config)
- [Workflow](#workflow)

## Functions

### create_agent

```python
def create_agent(model: str, memory_manager: Optional[ForwardRef('IMemoryManager')] = None, **kwargs) -> langswarm.simple_api.Agent
```

Create a simple agent.

Args:
    model: AI model name (e.g., "gpt-3.5-turbo", "gpt-4")
    memory_manager: Optional external memory manager for persistent sessions.
        When provided, conversations are automatically persisted and can be
        restored across agent restarts.
    **kwargs: Additional agent options:
        - provider: Provider name (auto-detected from model if not specified)
        - system_prompt: System instructions for the agent
        - memory: Enable in-memory conversation history (default: False)
        - tools: List of tool names to enable
        - stream: Enable streaming responses (default: False)
        - track_costs: Track token usage and costs (default: False)
    
Returns:
    Agent instance
    
Example:
    # Simple agent
    agent = create_agent(model="gpt-4")
    
    # Agent with persistent memory
    from langswarm.core.memory import create_memory_manager
    manager = create_memory_manager("sqlite", db_path="memory.db")
    await manager.backend.connect()
    
    agent = create_agent(
        model="gpt-4",
        memory_manager=manager,
        system_prompt="You are a helpful assistant"
    )
    
    # Chat with session persistence
    response = await agent.chat("Hello!", session_id="user-123")

**Parameters:**

- `model`: `str`
- `memory_manager`: `Optional = None`
- `kwargs`: `Any`

**Returns:**

`Agent`


### create_workflow

```python
def create_workflow(definition: str, agents: List[Dict[str, Any]]) -> langswarm.simple_api.Workflow
```

Create a simple workflow.

Args:
    definition: Workflow definition string
    agents: List of agent configurations
    
Returns:
    Workflow instance

**Parameters:**

- `definition`: `str`
- `agents`: `List`

**Returns:**

`Workflow`


### load_config

```python
def load_config(filepath: str) -> langswarm.simple_api.Config
```

Load configuration from YAML file.

Args:
    filepath: Path to YAML configuration file
    
Returns:
    Config instance

**Parameters:**

- `filepath`: `str`

**Returns:**

`Config`


### require_package

```python
def require_package(package_name: str, feature_desc: str)
```

Simple package requirement checker.

**Parameters:**

- `package_name`: `str`
- `feature_desc`: `str`


## Classes

### Agent

```python
class Agent
```

Simple agent wrapper for examples.

**Methods:**

#### chat

```python
async def chat(self, message: str, session_id: Optional[str] = None) -> str
```

Send a message and get a response.

Args:
    message: The user message to send
    session_id: Optional session ID for external memory persistence
    
Returns:
    The assistant's response

**Parameters:**

- `message`: `str`
- `session_id`: `Optional = None`

**Returns:**

`str`

#### chat_stream

```python
def chat_stream(self, message: str) -> AsyncGenerator[str, NoneType]
```

Stream a response as it's generated.

**Parameters:**

- `message`: `str`

**Returns:**

`AsyncGenerator`

#### get_usage_stats

```python
def get_usage_stats(self) -> Dict[str, Any]
```

Get usage statistics.

**Parameters:**


**Returns:**

`Dict`


### Config

```python
class Config
```

Simple configuration wrapper.

**Methods:**

#### get_agent

```python
def get_agent(self, agent_id: str) -> langswarm.simple_api.Agent
```

Get an agent by ID.

**Parameters:**

- `agent_id`: `str`

**Returns:**

`Agent`


### Workflow

```python
class Workflow
```

Simple workflow wrapper.

**Methods:**

#### run

```python
async def run(self, input_message: str) -> str
```

Run the workflow with input.

**Parameters:**

- `input_message`: `str`

**Returns:**

`str`

