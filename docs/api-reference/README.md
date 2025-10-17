# LangSwarm API Reference

Complete API documentation for LangSwarm's multi-agent orchestration framework.

*Generated on 2025-10-06 13:34:13*

## Quick Start

LangSwarm's core value is **multi-agent orchestration**. Here's the essential workflow:

```python
from langswarm import create_openai_agent, register_agent, create_simple_workflow, get_workflow_engine

# 1. Create specialized agents
researcher = await create_openai_agent('researcher', system_prompt='Research specialist')
summarizer = await create_openai_agent('summarizer', system_prompt='Summary specialist')

# 2. Register for orchestration
register_agent(researcher)
register_agent(summarizer)

# 3. Create workflow
workflow = create_simple_workflow('task', 'Research Task', ['researcher', 'summarizer'])

# 4. Execute orchestration
engine = get_workflow_engine()
result = await engine.execute_workflow(workflow, {'input': 'AI safety research'})
```

## API Modules

### [core.agents](langswarm_core_agents.md)

LangSwarm V2 Agent System

- **Functions:** 0
- **Classes:** 0

### [core.workflows](langswarm_core_workflows.md)

LangSwarm V2 Workflow System

- **Functions:** 6
- **Classes:** 0

### [core.session](langswarm_core_session.md)

LangSwarm V2 Session Management

- **Functions:** 9
- **Classes:** 3

### [simple_api](langswarm_simple_api.md)

Simple API for LangSwarm examples.

- **Functions:** 4
- **Classes:** 3

### [core.orchestration_errors](langswarm_core_orchestration_errors.md)

Orchestration-specific error handling for LangSwarm.

- **Functions:** 5
- **Classes:** 6

## Key Concepts

### 🤖 Agents
Specialized AI entities with specific roles and capabilities. Each agent has a unique ID and system prompt.

### 📋 Workflows
Orchestration blueprints defining how agents collaborate. Specify sequence and data flow between agents.

### 🔄 Data Flow
Automatic data passing between agents. Each agent receives output from the previous agent.

### 🏭 Execution Engine
Orchestration runtime that executes workflows, manages agent coordination and error handling.

## Type System

LangSwarm uses comprehensive type hints for better development experience:

- `BaseAgent`: Core agent implementation
- `IWorkflow`: Workflow interface
- `WorkflowResult`: Execution result with status and data
- `WorkflowStatus`: Enum for tracking execution state

## Error Handling

Comprehensive error system with actionable suggestions:

- `AgentNotFoundError`: When workflow references unregistered agent
- `WorkflowExecutionError`: When workflow execution fails
- `AgentExecutionError`: When individual agent fails
- `DataPassingError`: When data cannot be passed between steps

See the [orchestration_errors](langswarm_core_orchestration_errors.md) module for details.
