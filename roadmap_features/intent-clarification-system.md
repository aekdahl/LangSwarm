# Intent-Based Tool Clarification System

## Overview

LangSwarm provides sophisticated clarification mechanisms for intent-based tool calls that can work within workflows or bubble up through the workflow hierarchy to parent workflows or the original calling agent.

## Architecture

### 1. Modular System Prompt Templates ✅

The system prompt now uses **modular template fragments** that are conditionally included based on agent configuration:

```
langswarm/core/templates/
├── system_prompt_template.md      # Main template
└── fragments/
    ├── clarification.md           # Basic clarification instructions
    ├── retry.md                   # Retry behavior instructions  
    ├── intent_workflow.md         # Intent-based tool calling
    └── cross_workflow_clarification.md  # Cross-workflow clarification
```

**When fragments are included:**
- **clarification.md**: If agent has intent-based tools OR retry capabilities
- **retry.md**: If agent has retry capabilities configured
- **intent_workflow.md**: If agent has intent-based tools  
- **cross_workflow_clarification.md**: If agent has tools that can invoke workflows

### 2. Cross-Workflow Clarification ✅

Enhanced clarification system with **scope-based routing**:

## How It Works

### Local Clarification (Default)
```json
{
  "response": "I need more information to help you.",
  "tool": "clarify",
  "args": {"prompt": "Which configuration file do you want me to read?"}
}
```

### Parent Workflow Clarification
```json
{
  "response": "I need input from the main workflow calling this tool.",
  "tool": "clarify", 
  "args": {
    "prompt": "Which environment are you deploying to?",
    "scope": "parent_workflow",
    "context": "Found configs for staging, prod, and dev environments"
  }
}
```

### Root User Clarification
```json
{
  "response": "I need clarification from the original user.",
  "tool": "clarify",
  "args": {
    "prompt": "Do you want me to delete these files permanently?", 
    "scope": "root_user",
    "context": "Found 50 temporary files that could be deleted"
  }
}
```

## Clarification Flow Examples

### Example 1: Tool Workflow Needs User Input

```yaml
# filesystem tool workflow
workflows:
  main_workflow:
    steps:
    - id: analyze_intent
      agent: file_agent
      input: "{{user_input}}"
      output:
        to: execute_action
        
    - id: execute_action  
      agent: file_agent
      input: "{{step_outputs.analyze_intent}}"
```

**Agent Response:**
```json
{
  "response": "I found multiple config files but need to know which environment you're targeting.",
  "tool": "clarify",
  "args": {
    "prompt": "Which environment? (staging/production/development)",
    "scope": "parent_workflow", 
    "context": "Found: config-staging.yml, config-prod.yml, config-dev.yml"
  }
}
```

### Example 2: Nested Workflow Stack

```
User Request → Main Agent → Tool Workflow → Sub-Tool → Clarification
                   ↑                                        ↓
              Clarification Response ←←←←←←←←←←←←←←←←←←←←←
```

## Implementation Benefits

### ✅ **Existing Retry Integration**
- Works seamlessly with current `retry: 2-3` workflow configurations
- Clarifications count as retry attempts with additional context

### ✅ **Multi-Step Conversations** 
- Workflows maintain conversation context across clarification cycles
- Previous outputs preserved during clarification requests

### ✅ **Automatic Resumption**
- Workflows automatically resume after clarification with additional context
- No manual intervention required

## Configuration Examples

### Agent with Clarification Capabilities
```yaml
agents:
  - id: filesystem_agent
    model: gpt-4o
    tools: ["filesystem"]
    config:
      retry_enabled: true
```

**Generated System Prompt includes:**
- Base response format instructions
- Clarification capabilities fragment (because has intent-based tools)
- Retry & error recovery fragment (because retry_enabled: true)
- Intent-based tool workflows fragment (because has filesystem tool)
- Cross-workflow clarification fragment (because has tools)

### MCP Tool with Intent Support
```yaml
tools:
  filesystem:
    type: mcp_filesystem
    settings:
      pattern: "intent"  # Supports intent-based calls
      
workflows:
  filesystem_main:
    steps:
    - id: understand_intent
      agent: intent_parser
      retry: 3  # Retry with clarification
```

## API Integration

### Starting Intent-Based Tool Call
```python
# User calls tool with intent
agent_response = agent.chat("read the configuration file")

# Agent uses intent-based tool call
{
  "response": "I'll find and read the configuration file for you.",
  "mcp": {
    "tool": "filesystem",
    "intent": "read configuration file", 
    "context": "user wants to analyze current settings"
  }
}
```

### Clarification Request Flow
```python
# Tool workflow needs clarification
clarification_request = {
  "tool": "clarify",
  "args": {
    "prompt": "Which config file? Found: app.yml, db.yml, api.yml", 
    "scope": "parent_workflow",
    "context": "Multiple configuration files found in /config directory"
  }
}

# System automatically:
# 1. Routes clarification to parent workflow
# 2. Preserves workflow state 
# 3. Waits for clarification response
# 4. Resumes with additional context
```

## Advanced Features

### Progressive Clarification
```json
{
  "response": "I need more specific information to help you effectively.",
  "tool": "clarify", 
  "args": {
    "prompt": "You mentioned 'configuration file' - which specific file? Options: nginx.conf (web server), app.yaml (application), database.env (database settings)",
    "scope": "local",
    "context": "Found 3 different types of config files with different purposes"
  }
}
```

### Contextual Clarification  
```json
{
  "response": "I found the files but need permission confirmation for this destructive operation.",
  "tool": "clarify",
  "args": {
    "prompt": "Delete 847 log files (2.3GB total)? Type 'confirm' to proceed.",
    "scope": "root_user",
    "context": "Cleanup operation - found log files older than 30 days"
  }
}
```

## Summary

The LangSwarm clarification system provides:

1. **✅ Modular System Prompts**: Template fragments conditionally included based on agent capabilities
2. **✅ Cross-Workflow Communication**: Clarifications can bubble up through workflow hierarchy  
3. **✅ Automatic Integration**: Works with existing retry mechanisms and workflow patterns
4. **✅ Context Preservation**: Maintains conversation state across clarification cycles
5. **✅ Progressive Refinement**: Supports iterative clarification until sufficient information is gathered

**Ready to use!** The system is already integrated and will automatically enhance agents that have intent-based tools or retry capabilities configured. 