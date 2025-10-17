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
def create_agent(model: str, **kwargs) -> langswarm.simple_api.Agent
```

Create a simple agent.

Args:
    model: AI model name (e.g., "gpt-3.5-turbo", "gpt-4")
    **kwargs: Additional agent options
    
Returns:
    Agent instance

**Parameters:**

- `model`: `str`
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
async def chat(self, message: str) -> str
```

Send a message and get a response.

**Parameters:**

- `message`: `str`

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

