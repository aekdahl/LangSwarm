# Workflow Executor MCP Tool

A powerful MCP tool that enables dynamic workflow orchestration with support for both pre-written and agent-generated workflow configurations.

## Methods

### execute_workflow
Execute a pre-written LangSwarm workflow configuration.

**Parameters:**
- `workflow_name` (string, required): Name of the workflow to execute
- `input_data` (object, required): Input data for the workflow
- `execution_mode` (string, optional): Execution mode - "sync", "async", or "isolated" (default: "sync")
- `config_override` (object, optional): Configuration overrides to apply
- `timeout` (integer, optional): Timeout in seconds (default: 300)

**Returns:**
- `execution_id` (string): Unique execution identifier
- `status` (string): Execution status
- `result` (object, optional): Execution result for sync mode
- `message` (string): Status message

### generate_workflow
Generate a complete workflow configuration from natural language description.

**Parameters:**
- `workflow_description` (string, required): Natural language description of desired workflow
- `workflow_name` (string, optional): Name for the generated workflow
- `agents_config` (object, optional): Custom agents configuration
- `tools_config` (object, optional): Custom tools configuration
- `complexity` (string, optional): Workflow complexity - "simple", "medium", or "complex" (default: "medium")

**Returns:**
- `workflow_name` (string): Generated workflow name
- `workflow_config` (object): Complete workflow configuration
- `validation_status` (string): Configuration validation status
- `message` (string): Generation status message

### execute_generated_workflow
Generate and execute a workflow in one step from natural language description.

**Parameters:**
- `workflow_description` (string, required): Natural language workflow description
- `input_data` (object, required): Input data for execution
- `execution_mode` (string, optional): Execution mode (default: "sync")
- `complexity` (string, optional): Workflow complexity (default: "medium")
- `timeout` (integer, optional): Timeout in seconds (default: 300)

**Returns:**
- `execution_id` (string): Unique execution identifier
- `workflow_name` (string): Generated workflow name
- `workflow_config` (object): Generated configuration
- `status` (string): Execution status
- `result` (object, optional): Execution result for sync mode
- `message` (string): Combined generation and execution message

### check_execution_status
Check the status of a workflow execution.

**Parameters:**
- `execution_id` (string, required): Execution ID to check

**Returns:**
- `execution_id` (string): Execution identifier
- `status` (string): Current execution status
- `result` (object, optional): Result if completed
- `progress` (string, optional): Progress information
- `message` (string): Status message

### cancel_execution
Cancel a running workflow execution.

**Parameters:**
- `execution_id` (string, required): Execution ID to cancel

**Returns:**
- `execution_id` (string): Execution identifier
- `status` (string): Cancellation status
- `message` (string): Cancellation message

### list_workflows
List available workflows in the current or specified directory.

**Parameters:**
- `config_path` (string, optional): Path to search for workflows
- `pattern` (string, optional): File pattern to search (default: "*.yaml")

**Returns:**
- `available_workflows` (array): List of available workflow configurations
- `total_count` (integer): Total number of workflows found
- `message` (string): Search status message

## Intent-Based Examples

### Execute Pre-Written Workflow
```json
{
  "response": "I'll execute the document analysis workflow with your data",
  "mcp": {
    "tool": "workflow_executor",
    "method": "execute_workflow",
    "params": {
      "workflow_name": "document_analysis",
      "input_data": {"file_path": "/documents/report.pdf"},
      "execution_mode": "sync"
    }
  }
}
```

### Generate Custom Workflow
```json
{
  "response": "I'll create a workflow that analyzes code repositories and generates summary reports",
  "mcp": {
    "tool": "workflow_executor", 
    "method": "generate_workflow",
    "params": {
      "workflow_description": "Analyze a code repository, extract key metrics, identify patterns, and generate a comprehensive summary report",
      "complexity": "medium"
    }
  }
}
```

### One-Step Generation and Execution
```json
{
  "response": "I'll create and run a research workflow to analyze your topic",
  "mcp": {
    "tool": "workflow_executor",
    "method": "execute_generated_workflow", 
    "params": {
      "workflow_description": "Research a topic by gathering information from multiple sources, analyzing content, and creating a structured report",
      "input_data": {"topic": "artificial intelligence ethics", "depth": "comprehensive"},
      "execution_mode": "async",
      "complexity": "complex"
    }
  }
}
```

### Monitor Async Execution
```json
{
  "response": "I'll check the status of your running workflow",
  "mcp": {
    "tool": "workflow_executor",
    "method": "check_execution_status",
    "params": {
      "execution_id": "abc-123-def-456"
    }
  }
}
```

### List Available Workflows
```json
{
  "response": "I'll show you all available workflows in the current project",
  "mcp": {
    "tool": "workflow_executor",
    "method": "list_workflows",
    "params": {
      "config_path": ".",
      "pattern": "*.yaml"
    }
  }
}
```

## Execution Modes

### Sync Mode
- Executes workflow in the same process
- Blocks until completion
- Returns immediate results
- Best for: Quick workflows (< 30 seconds)

### Async Mode  
- Executes workflow in background thread
- Returns execution_id immediately
- Check status with check_execution_status
- Best for: Long-running workflows, parallel processing

### Isolated Mode
- Executes workflow in separate process
- Complete isolation and fault tolerance
- Independent resource allocation
- Best for: Sensitive data, resource-intensive operations

## Workflow Generation

### Complexity Levels

**Simple Workflows:**
- 1-2 agents maximum
- 2-3 workflow steps
- Basic tools: filesystem, tasklist
- Linear execution flow

**Medium Workflows:**
- 3-4 agents maximum
- 4-6 workflow steps
- Standard tool suite
- Some parallel processing

**Complex Workflows:**
- 5-8 agents maximum
- 6-12 workflow steps
- Full tool ecosystem
- Advanced orchestration patterns

### Generated Agent Types
- **analyzer**: Data and content analysis
- **summarizer**: Content summarization
- **researcher**: Information gathering
- **reporter**: Report generation
- **processor**: Data processing
- **coordinator**: Workflow management
- **validator**: Quality assurance
- **creator**: Content creation
- **generator**: Output generation

## Configuration Structure

Generated workflows follow LangSwarm standards:

```yaml
version: "1.0"
project_name: "dynamic_workflow_name"
memory: "production"

agents:
  - id: agent_name
    agent_type: openai
    model: gpt-4o
    system_prompt: "Role-specific prompt"
    tools: [filesystem, tasklist, ...]

workflows:
  workflow_name:
    steps:
      - agent: agent_name
        input: "${user_input}"
        output: {to: user}
```

## Error Handling

The tool provides comprehensive error handling:
- Configuration validation errors
- Execution timeout handling
- Resource availability checks
- Process isolation failures
- Network connectivity issues

## Performance Considerations

- Use appropriate execution modes for workload
- Consider timeout settings for complex workflows
- Monitor resource usage in isolated mode
- Leverage async mode for parallel operations
- Use configuration overrides for optimization

## Limitations

- Generated workflows are template-based
- Complex orchestration patterns may need manual refinement
- Isolated mode requires sufficient system resources
- Some advanced LangSwarm features may not be auto-generated
- Network latency can affect isolated mode performance