# Core Workflows API

**Module:** `langswarm.core.workflows`

## Overview

LangSwarm V2 Workflow System

Modern, simplified workflow orchestration system for LangSwarm V2.
Provides clean interfaces, fluent builder pattern, and comprehensive
execution engine while maintaining full backward compatibility.

Key Features:
- Clean, type-safe interfaces
- Fluent workflow builder API  
- Multiple execution modes (sync, async, streaming, parallel)
- Integration with V2 middleware and error handling
- YAML compatibility layer
- Comprehensive monitoring and debugging

## Table of Contents

### Functions
- [execute_workflow](#execute_workflow)
- [execute_workflow_stream](#execute_workflow_stream)
- [get_workflow](#get_workflow)
- [list_executions](#list_executions)
- [list_workflows](#list_workflows)
- [register_workflow](#register_workflow)

## Functions

### execute_workflow

```python
async def execute_workflow(workflow_id: str, input_data: Dict[str, Any], execution_mode: langswarm.core.workflows.interfaces.ExecutionMode = <ExecutionMode.SYNC: 'sync'>) -> langswarm.core.workflows.interfaces.WorkflowResult
```

Execute a registered workflow by ID

**Parameters:**

- `workflow_id`: `str`
- `input_data`: `Dict`
- `execution_mode`: `ExecutionMode = <ExecutionMode.SYNC: 'sync'>`

**Returns:**

`WorkflowResult`


### execute_workflow_stream

```python
def execute_workflow_stream(workflow_id: str, input_data: Dict[str, Any])
```

Execute a workflow with streaming results

**Parameters:**

- `workflow_id`: `str`
- `input_data`: `Dict`


### get_workflow

```python
async def get_workflow(workflow_id: str) -> langswarm.core.workflows.interfaces.IWorkflow
```

Get a workflow from the global registry

**Parameters:**

- `workflow_id`: `str`

**Returns:**

`IWorkflow`


### list_executions

```python
async def list_executions(workflow_id: str = None, status: langswarm.core.workflows.interfaces.WorkflowStatus = None, limit: int = 100) -> List[langswarm.core.workflows.interfaces.IWorkflowExecution]
```

List workflow executions

**Parameters:**

- `workflow_id`: `str = None`
- `status`: `WorkflowStatus = None`
- `limit`: `int = 100`

**Returns:**

`List`


### list_workflows

```python
async def list_workflows() -> List[langswarm.core.workflows.interfaces.IWorkflow]
```

List all registered workflows

**Returns:**

`List`


### register_workflow

```python
async def register_workflow(workflow: langswarm.core.workflows.interfaces.IWorkflow) -> bool
```

Register a workflow in the global registry

**Parameters:**

- `workflow`: `IWorkflow`

**Returns:**

`bool`

