# no_mcp Tool Configuration Guide

This guide clarifies the different ways to configure tools in LangSwarm workflows and when to use each approach.

## Overview

LangSwarm supports two main approaches for configuring tools with agents:

1. **Direct Tools Configuration** - Tools are configured directly on the agent
2. **no_mcp Wrapper Configuration** - Tools are configured inline within workflow steps

Both approaches are fully supported and provide similar functionality, but have different use cases.

## Configuration Formats

### 1. Direct Tools Configuration (Recommended)

**When to use**: Default approach for most use cases.

```yaml
agents:
  - id: my_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are a helpful assistant."
    tools:
      - tool_id_1
      - tool_id_2

workflows:
  main_workflow:
    - id: agent_step
      agent: my_agent
      input: "User message"
      output:
        to: user
```

**Advantages**:
- Cleaner configuration
- Tools are reusable across workflow steps
- Better performance (tools are initialized once)
- Easier to maintain

### 2. no_mcp Wrapper Configuration

**When to use**: When you need step-specific tool access or dynamic tool assignment.

```yaml
agents:
  - id: my_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are a helpful assistant."

workflows:
  main_workflow:
    - id: agent_step
      agent: my_agent
      input: "User message"
      no_mcp:
        tools:
          - tool_id_1
          - tool_id_2
      output:
        to: user
```

**Advantages**:
- Step-specific tool access
- Dynamic tool assignment per workflow step
- Fine-grained control over tool availability

## Use Case Examples

### Example 1: Consistent Tool Access (Use Direct Configuration)

If an agent always needs the same tools across all workflow steps:

```yaml
tools:
  - id: time_tracker
    type: function
    metadata:
      function: track_time
      description: "Track time entries"

agents:
  - id: timebot_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You help track time."
    tools:  # ✅ Direct configuration
      - time_tracker

workflows:
  time_tracking:
    - id: log_time
      agent: timebot_agent
      input: ${user_input}
```

### Example 2: Step-Specific Tool Access (Use no_mcp)

If different workflow steps need different tools:

```yaml
tools:
  - id: calculator
    type: function
    metadata:
      function: calculate
      description: "Perform calculations"
  
  - id: email_sender
    type: function
    metadata:
      function: send_email
      description: "Send emails"

agents:
  - id: assistant_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are a versatile assistant."

workflows:
  multi_step_workflow:
    - id: calculation_step
      agent: assistant_agent
      input: "Calculate 15 * 23"
      no_mcp:  # ✅ Step-specific tools
        tools:
          - calculator
    
    - id: email_step
      agent: assistant_agent
      input: "Send result via email"
      no_mcp:  # ✅ Different tools for this step
        tools:
          - email_sender
```

## Tool Configuration Options

Both configuration methods support the same tool options:

### Basic Tool Reference
```yaml
tools:
  - tool_id
```

### Tool with Options
```yaml
tools:
  - name: tool_id
    repeatable: true
    retry_limit: 5
```

## Migration Between Formats

### Converting from no_mcp to Direct Configuration

**Before (no_mcp)**:
```yaml
workflows:
  example:
    - id: step1
      agent: my_agent
      no_mcp:
        tools:
          - tool_a
          - tool_b
```

**After (Direct)**:
```yaml
agents:
  - id: my_agent
    tools:
      - tool_a
      - tool_b

workflows:
  example:
    - id: step1
      agent: my_agent
```

### Converting from Direct to no_mcp Configuration

**Before (Direct)**:
```yaml
agents:
  - id: my_agent
    tools:
      - tool_a
      - tool_b
```

**After (no_mcp)**:
```yaml
agents:
  - id: my_agent
    # Remove tools from agent

workflows:
  example:
    - id: step1
      agent: my_agent
      no_mcp:
        tools:
          - tool_a
          - tool_b
```

## Best Practices

1. **Default to Direct Configuration**: Use direct tools configuration unless you specifically need step-level control.

2. **Consistent Tool Access**: If an agent always needs the same tools, use direct configuration.

3. **Dynamic Tool Access**: Use no_mcp when different workflow steps need different tools.

4. **Performance Considerations**: Direct configuration has better performance for frequently used tools.

5. **Maintainability**: Direct configuration is easier to maintain for large projects.

## Common Issues and Solutions

### Issue: UnboundLocalError with no_mcp

**Error**: `UnboundLocalError: local variable 'user_response' referenced before assignment`

**Solution**: This was a bug in LangSwarm v0.0.51 that has been fixed. Update to the latest version.

### Issue: Tool Not Found

**Error**: `Unknown tool selected by agent: tool_name`

**Solutions**:
1. Ensure the tool is defined in the `tools` section
2. Check tool ID spelling
3. Verify tool metadata is correctly configured

### Issue: Agent Response Format

**Problem**: Agent doesn't call tools correctly

**Solutions**:
1. Ensure proper system prompt configuration
2. Check tool descriptions are clear
3. Verify tool parameter schemas

## Configuration Schema Reference

### Direct Tools Configuration
```yaml
agents:
  - id: string              # Required: Agent identifier
    tools:                  # Optional: List of tools
      - string              # Tool ID reference
      - name: string        # Tool ID with options
        repeatable: boolean # Optional: Allow repeated calls
        retry_limit: integer # Optional: Max retry attempts
```

### no_mcp Configuration
```yaml
workflows:
  workflow_name:
    - id: string            # Required: Step identifier
      agent: string         # Required: Agent ID
      no_mcp:               # Optional: Inline tool configuration
        tools:              # Required: List of tools
          - string          # Tool ID reference
          - name: string    # Tool ID with options
            repeatable: boolean
            retry_limit: integer
```

## Summary

Both direct tools configuration and no_mcp wrapper are fully supported in LangSwarm. Choose the approach that best fits your use case:

- **Direct Configuration**: For consistent, reusable tool access
- **no_mcp Configuration**: For step-specific, dynamic tool access

Both formats provide the same functionality and performance, so the choice is primarily about organization and use case requirements. 