# 🎭 LangSwarm Multi-Agent Orchestration Guide

## Overview

LangSwarm's **core value proposition** is multi-agent orchestration - the ability to coordinate multiple specialized AI agents to work together on complex tasks. This guide explains how to leverage this powerful capability.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Creating Agents](#creating-agents)
4. [Registering Agents](#registering-agents)
5. [Building Workflows](#building-workflows)
6. [Executing Workflows](#executing-workflows)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Advanced Patterns](#advanced-patterns)
10. [API Reference](#api-reference)

## Quick Start

Here's a complete example of multi-agent orchestration in 10 lines:

```python
from langswarm import create_openai_agent, register_agent, create_simple_workflow, get_workflow_engine

# Create specialized agents
researcher = await create_openai_agent("researcher", system_prompt="Research specialist")
summarizer = await create_openai_agent("summarizer", system_prompt="Summary specialist")

# Register for orchestration
register_agent(researcher)
register_agent(summarizer)

# Create workflow
workflow = create_simple_workflow("task", "Research Task", ["researcher", "summarizer"])

# Execute orchestration
engine = get_workflow_engine()
result = await engine.execute_workflow(workflow, {"input": "AI safety research"})
```

## Core Concepts

### 🤖 Agents
- **Specialized AI entities** with specific roles and capabilities
- Each agent has a unique ID and system prompt
- Agents can use different models and providers

### 📋 Workflows  
- **Orchestration blueprints** defining how agents collaborate
- Specify the sequence and data flow between agents
- Can be linear, parallel, or conditional

### 🔄 Data Flow
- **Automatic data passing** between agents
- Each agent receives output from the previous agent
- Results accumulate through the workflow

### 🏭 Execution Engine
- **Orchestration runtime** that executes workflows
- Manages agent coordination and error handling
- Provides execution tracking and monitoring

## Creating Agents

### Async Creation (Recommended)

```python
from langswarm import create_openai_agent

# Full async creation with tool injection
agent = await create_openai_agent(
    name="researcher",
    model="gpt-3.5-turbo",
    system_prompt="You are a research specialist. Provide detailed analysis.",
    temperature=0.7,
    tools=["web_search", "calculator"]  # Optional tools
)
```

### Sync Creation

```python
from langswarm import create_openai_agent_sync

# Synchronous creation (no automatic tool injection)
agent = create_openai_agent_sync(
    name="analyzer",
    model="gpt-4",
    system_prompt="You are a data analyst.",
    temperature=0.3
)
```

### Using AgentBuilder

```python
from langswarm import AgentBuilder

# Fine-grained control with builder pattern
agent = (AgentBuilder("expert")
         .openai()  # or .anthropic(), .google(), etc.
         .model("gpt-4")
         .system_prompt("You are a domain expert.")
         .temperature(0.5)
         .max_tokens(2000)
         .build_sync())
```

### Provider-Specific Agents

```python
# OpenAI
openai_agent = await create_openai_agent("gpt-expert", model="gpt-4")

# Anthropic  
anthropic_agent = await create_anthropic_agent("claude-expert", model="claude-3-sonnet")

# Google
google_agent = await create_google_agent("gemini-expert", model="gemini-pro")

# Cohere
cohere_agent = await create_cohere_agent("command-expert", model="command")

# Mistral
mistral_agent = await create_mistral_agent("mistral-expert", model="mistral-medium")
```

## Registering Agents

Agents must be registered before they can be used in workflows:

```python
from langswarm import register_agent, get_agent, list_agents

# Register an agent
success = register_agent(my_agent)
print(f"Registration successful: {success}")

# Register with metadata
register_agent(my_agent, metadata={
    "capabilities": ["research", "analysis"],
    "domain": "scientific_papers"
})

# Retrieve registered agents
agent = get_agent("researcher")  # By ID
agents = list_agents()  # List all IDs
```

## Building Workflows

### Simple Linear Workflow

```python
from langswarm import create_simple_workflow

# Agents execute in sequence: A → B → C
workflow = create_simple_workflow(
    workflow_id="research_pipeline",
    name="Research and Analysis Pipeline",
    agent_chain=["researcher", "analyzer", "summarizer"]
)
```

### Workflow with Input Data

```python
# Provide initial input structure
workflow = create_simple_workflow(
    workflow_id="custom_pipeline",
    name="Custom Pipeline",
    agent_chain=["agent1", "agent2"],
    input_data={
        "query": "${input}",
        "context": "Academic research",
        "max_length": 1000
    }
)
```

### Using WorkflowBuilder (Advanced)

```python
from langswarm import WorkflowBuilder, AgentStep

builder = WorkflowBuilder("complex_workflow")

# Add steps manually
builder.add_step(AgentStep("research_step", "researcher"))
builder.add_step(AgentStep("analyze_step", "analyzer"))
builder.add_step(AgentStep("summarize_step", "summarizer"))

workflow = builder.build()
```

## Executing Workflows

### Synchronous Execution

```python
from langswarm import get_workflow_engine

engine = get_workflow_engine()

# Execute and wait for result
result = await engine.execute_workflow(
    workflow=my_workflow,
    input_data={"input": "Research quantum computing applications"}
)

# Access results
print(f"Status: {result.status}")
print(f"Final output: {result.result}")
print(f"Execution time: {result.execution_time}s")

# Check individual step results
for step_id, step_result in result.step_results.items():
    print(f"{step_id}: {step_result.status}")
```

### Asynchronous Execution

```python
from langswarm import ExecutionMode

# Start workflow asynchronously
execution = await engine.execute_workflow(
    workflow=my_workflow,
    input_data={"input": "Complex analysis task"},
    execution_mode=ExecutionMode.ASYNC
)

# Monitor progress
while execution.get_status() == WorkflowStatus.RUNNING:
    print(f"Progress: {execution.get_progress()}%")
    await asyncio.sleep(1)

# Get final result
result = execution.get_result()
```

### Streaming Execution

```python
# Stream results as steps complete
async for step_result in engine.execute_workflow_stream(
    workflow=my_workflow,
    input_data={"input": "Stream this analysis"}
):
    if isinstance(step_result, StepResult):
        print(f"Step {step_result.step_id} completed")
    else:  # WorkflowResult
        print(f"Workflow completed: {step_result.status}")
```

## Error Handling

LangSwarm provides comprehensive error handling for orchestration:

### Agent Not Found

```python
try:
    workflow = create_simple_workflow("test", "Test", ["missing_agent"])
except AgentNotFoundError as e:
    print(e)  # Clear error message
    print(e.suggestion)  # Helpful fix suggestions
```

Output:
```
Agent 'missing_agent' not found in registry

Make sure to register agent 'missing_agent' before using it in workflows:

  from langswarm import create_openai_agent, register_agent
  
  # Create the agent
  missing_agent = await create_openai_agent(
      name='missing_agent',
      model='gpt-3.5-turbo',
      system_prompt='Your agent instructions'
  )
  
  # Register it for orchestration
  register_agent(missing_agent)

Currently registered agents:
  • researcher
  • summarizer
```

### Workflow Execution Errors

```python
try:
    result = await engine.execute_workflow(workflow, input_data)
except WorkflowExecutionError as e:
    print(f"Workflow failed: {e}")
    print(f"Failed at step: {e.step_id}")
    print(f"Suggestion: {e.suggestion}")
```

### Agent Execution Errors

```python
try:
    result = await agent.execute("process this")
except AgentExecutionError as e:
    print(f"Agent {e.agent_id} failed: {e}")
    print(f"Input data type: {type(e.input_data)}")
    print(f"Fix: {e.suggestion}")
```

## Best Practices

### 1. Design Specialized Agents

```python
# ✅ Good: Specific, focused roles
researcher = await create_openai_agent(
    name="paper_researcher",
    system_prompt="You are a scientific paper research specialist. Find and analyze peer-reviewed papers on the given topic."
)

# ❌ Avoid: Generic, unfocused agents
generic = await create_openai_agent(
    name="helper",
    system_prompt="You are a helpful assistant."
)
```

### 2. Clear Data Contracts

```python
# ✅ Good: Clear expectations for data format
analyzer = await create_openai_agent(
    name="data_analyzer",
    system_prompt="""You are a data analyst. 
    
    Input format: {"papers": [...], "query": "..."}
    Output format: {"insights": [...], "summary": "...", "confidence": 0.0-1.0}
    """
)
```

### 3. Error Recovery

```python
# Implement retry logic for critical workflows
async def execute_with_retry(workflow, input_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await engine.execute_workflow(workflow, input_data)
        except WorkflowExecutionError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Workflow Validation

```python
# Validate workflow before execution
def validate_workflow(workflow):
    """Ensure all agents are registered before execution."""
    for step in workflow.steps:
        if hasattr(step, 'agent_id'):
            if not get_agent(step.agent_id):
                raise AgentNotFoundError(step.agent_id, list_agents())
```

### 5. Monitoring and Logging

```python
import logging

# Enable debug logging for orchestration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('langswarm.orchestration')

# Add workflow metadata for tracking
result = await engine.execute_workflow(
    workflow=workflow,
    input_data=input_data,
    context_variables={
        "request_id": "req-123",
        "user_id": "user-456",
        "environment": "production"
    }
)
```

## Advanced Patterns

### Multi-Provider Orchestration

```python
# Mix agents from different providers
openai_researcher = await create_openai_agent("openai_researcher", model="gpt-4")
anthropic_analyzer = await create_anthropic_agent("claude_analyzer", model="claude-3-sonnet")
google_summarizer = await create_google_agent("gemini_summarizer", model="gemini-pro")

register_agent(openai_researcher)
register_agent(anthropic_analyzer)
register_agent(google_summarizer)

# Create cross-provider workflow
workflow = create_simple_workflow(
    "multi_provider",
    "Multi-Provider Analysis",
    ["openai_researcher", "claude_analyzer", "gemini_summarizer"]
)
```

### Conditional Workflows (Future)

```python
# Coming soon: Conditional execution based on results
workflow = (WorkflowBuilder("conditional_flow")
    .add_agent_step("research", "researcher")
    .add_condition_step("quality_check", lambda ctx: ctx.confidence > 0.8)
    .add_agent_step("deep_analysis", "analyzer", condition="quality_check")
    .add_agent_step("quick_summary", "summarizer", condition="!quality_check")
    .build())
```

### Parallel Execution (Future)

```python
# Coming soon: Parallel agent execution
workflow = create_parallel_workflow(
    "parallel_analysis",
    "Parallel Analysis",
    agents=["analyst1", "analyst2", "analyst3"],
    aggregator="result_combiner"
)
```

## API Reference

### Agent Creation

```python
async def create_openai_agent(
    name: str = "openai-agent",
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs: Any
) -> BaseAgent:
    """Create an OpenAI agent with smart defaults."""
```

### Agent Registration

```python
def register_agent(
    agent: IAgent, 
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Register an agent in the global registry for orchestration."""

def get_agent(agent_id: str) -> Optional[IAgent]:
    """Get a registered agent by ID from the global registry."""

def list_agents() -> List[str]:
    """List all registered agent IDs available for orchestration."""
```

### Workflow Creation

```python
def create_simple_workflow(
    workflow_id: str,
    name: str,
    agent_chain: List[str],
    input_data: Optional[Dict[str, Any]] = None
) -> IWorkflow:
    """Create a simple linear workflow for multi-agent orchestration."""
```

### Workflow Execution

```python
async def execute_workflow(
    self,
    workflow: IWorkflow,
    input_data: Dict[str, Any],
    execution_mode: ExecutionMode = ExecutionMode.SYNC,
    context_variables: Optional[Dict[str, Any]] = None
) -> Union[WorkflowResult, IWorkflowExecution]:
    """Execute a multi-agent workflow with automatic orchestration."""
```

## Conclusion

Multi-agent orchestration is the heart of LangSwarm. By combining specialized agents into workflows, you can tackle complex tasks that would be difficult for a single agent to handle. The orchestration system handles all the complexity of agent coordination, data passing, and error recovery, allowing you to focus on designing effective agent collaborations.

Start simple with two agents, then scale up to complex multi-agent systems as your needs grow. That's the power of LangSwarm orchestration.