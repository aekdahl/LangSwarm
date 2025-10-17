# Core Orchestration_Errors API

**Module:** `langswarm.core.orchestration_errors`

## Overview

Orchestration-specific error handling for LangSwarm.

Provides clear, actionable error messages for common orchestration issues
to help developers quickly identify and resolve problems.

## Table of Contents

### Functions
- [agent_failed](#agent_failed)
- [agent_not_found](#agent_not_found)
- [data_passing_failed](#data_passing_failed)
- [validation_failed](#validation_failed)
- [workflow_failed](#workflow_failed)

### Classes
- [AgentExecutionError](#agentexecutionerror)
- [AgentNotFoundError](#agentnotfounderror)
- [DataPassingError](#datapassingerror)
- [OrchestrationError](#orchestrationerror)
- [WorkflowExecutionError](#workflowexecutionerror)
- [WorkflowValidationError](#workflowvalidationerror)

## Functions

### agent_failed

```python
def agent_failed(agent_id: str, step_id: str, error: Optional[Exception] = None) -> langswarm.core.orchestration_errors.AgentExecutionError
```

Create an AgentExecutionError with context.

**Parameters:**

- `agent_id`: `str`
- `step_id`: `str`
- `error`: `Optional = None`

**Returns:**

`AgentExecutionError`


### agent_not_found

```python
def agent_not_found(agent_id: str, available_agents: Optional[List[str]] = None) -> langswarm.core.orchestration_errors.AgentNotFoundError
```

Create an AgentNotFoundError with context.

**Parameters:**

- `agent_id`: `str`
- `available_agents`: `Optional = None`

**Returns:**

`AgentNotFoundError`


### data_passing_failed

```python
def data_passing_failed(from_step: str, to_step: str, reason: str) -> langswarm.core.orchestration_errors.DataPassingError
```

Create a DataPassingError with context.

**Parameters:**

- `from_step`: `str`
- `to_step`: `str`
- `reason`: `str`

**Returns:**

`DataPassingError`


### validation_failed

```python
def validation_failed(workflow_id: str, errors: List[str]) -> langswarm.core.orchestration_errors.WorkflowValidationError
```

Create a WorkflowValidationError with context.

**Parameters:**

- `workflow_id`: `str`
- `errors`: `List`

**Returns:**

`WorkflowValidationError`


### workflow_failed

```python
def workflow_failed(workflow_id: str, step_id: Optional[str] = None, error: Optional[Exception] = None) -> langswarm.core.orchestration_errors.WorkflowExecutionError
```

Create a WorkflowExecutionError with context.

**Parameters:**

- `workflow_id`: `str`
- `step_id`: `Optional = None`
- `error`: `Optional = None`

**Returns:**

`WorkflowExecutionError`


## Classes

### AgentExecutionError

```python
class AgentExecutionError(OrchestrationError)
```

Raised when an agent fails during workflow execution.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`


### AgentNotFoundError

```python
class AgentNotFoundError(OrchestrationError)
```

Raised when a workflow references an agent that isn't registered.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`


### DataPassingError

```python
class DataPassingError(OrchestrationError)
```

Raised when data cannot be passed between workflow steps.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`


### OrchestrationError

```python
class OrchestrationError(LangSwarmError)
```

Base class for all orchestration-related errors.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`


### WorkflowExecutionError

```python
class WorkflowExecutionError(OrchestrationError)
```

Raised when workflow execution fails.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`


### WorkflowValidationError

```python
class WorkflowValidationError(OrchestrationError)
```

Raised when workflow configuration is invalid.

**Methods:**

#### get_debug_info

```python
def get_debug_info(self) -> Dict[str, Any]
```

Get comprehensive debug information

**Parameters:**


**Returns:**

`Dict`

#### is_critical

```python
def is_critical(self) -> bool
```

Check if this is a critical error requiring system halt

**Parameters:**


**Returns:**

`bool`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert error to dictionary for logging/serialization

**Parameters:**


**Returns:**

`Dict`

