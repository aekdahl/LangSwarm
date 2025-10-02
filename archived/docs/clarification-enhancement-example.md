# Intent-Based Tool Clarification Guide

## Current System Overview

LangSwarm already includes sophisticated clarification mechanisms for intent-based tool calls. Here's how it works:

## 1. Built-in Clarification Flow

### Agent Clarification Response
When an agent needs more information, it returns:
```json
{
  "response": "I need more information to help you with that.",
  "tool": "clarify",
  "args": {"prompt": "Which specific configuration file do you want me to read?"}
}
```

### Workflow Processing
The workflow system automatically handles clarification by:
1. **Detecting** clarification requests (`tool: "clarify"`)
2. **Returning** the clarification question to the user
3. **Resuming** the workflow when user provides more context
4. **Retrying** with enhanced context (up to configured retry limits)

## 2. Multi-Step Conversation Example

### User Intent
```json
{
  "mcp": {
    "tool": "filesystem",
    "intent": "read configuration file",
    "context": "analyze configuration settings for troubleshooting"
  }
}
```

### Workflow Clarification Steps

**Step 1: Path Extraction Agent**
- Input: "read configuration file" 
- If unclear → returns clarification request

**Step 2: Tool Selection Agent**  
- Input: User intent + clarified path
- Selects appropriate filesystem method

**Step 3: Execution with Retry**
- Uses `retry: 2` configuration
- If tool call fails, retries with additional context

## 3. Enhanced Clarification Implementation

### Enhanced Agent Prompts
```yaml
agents:
  - id: enhanced_path_extractor
    agent_type: langchain-openai
    model: gpt-4
    system_prompt: |
      You are a path extraction agent with clarification capabilities.
      
      If the user's request contains a clear file/directory path, extract and return it.
      If the path is ambiguous or missing, ask for clarification using this format:
      
      {
        "response": "I need more specific information.",
        "tool": "clarify", 
        "args": {"prompt": "Which configuration file? Please specify the full path or filename (e.g., /etc/nginx.conf, config.yaml, .env)"}
      }
      
      Examples of clear paths:
      - "docs/README.md" → return "docs/README.md"
      - "config file in root" → ASK FOR CLARIFICATION
      - "the nginx config" → ASK FOR CLARIFICATION
```

### Enhanced Workflow with Context Memory
```yaml
workflows:
  enhanced_filesystem_workflow:
    - id: understand_intent
      inputs: [user_query, conversation_history]
      steps:
        - id: analyze_request
          agent: context_analyzer
          input: 
            query: ${user_query}
            history: ${conversation_history}
          output_key: analysis
          
        - id: extract_details
          agent: enhanced_path_extractor  
          input:
            query: ${user_query}
            previous_context: ${analysis}
          output_key: file_details
          retry: 3  # Allow multiple clarification rounds
          
        - id: validate_and_execute
          agent: execution_validator
          input:
            details: ${file_details}
            original_intent: ${user_query}
          output_key: validation_result
          
        - id: execute_tool
          function: mcp_call
          condition: ${validation_result.ready}
          args:
            tool_id: ${validation_result.tool}
            input: ${validation_result.params}
          retry: 2
          output_key: tool_result
          
        - id: handle_clarification
          agent: clarification_handler
          condition: ${validation_result.needs_clarification}
          input: ${validation_result.clarification_prompt}
          output:
            to: user
```

## 4. Advanced Clarification Patterns

### Context-Aware Clarification
```python
# In your custom agent system prompt:
ENHANCED_CLARIFICATION_PROMPT = """
When asking for clarification, be specific and helpful:

❌ Bad: "I need more information"
✅ Good: "I found 3 config files: nginx.conf, app.yaml, database.env. Which one do you want me to read?"

❌ Bad: "Path unclear" 
✅ Good: "You mentioned 'config in root directory'. I see these config files in the root: .env, config.json, settings.yaml. Which one?"

Always provide context about what you found and offer specific options when possible.
"""
```

### Progressive Clarification
```yaml
# Example workflow that gets progressively more specific
- id: progressive_clarification
  steps:
    - id: broad_search
      function: find_candidate_files
      args:
        query: ${user_intent}
        search_paths: ["/etc", "/config", "./"]
      output_key: candidates
      
    - id: narrow_down
      agent: file_selector
      input:
        candidates: ${candidates}
        user_intent: ${user_intent}
      condition: ${len(candidates) > 1}
      output_key: selection_request
      
    - id: final_selection
      agent: path_resolver  
      input: ${selection_request}
      retry: 2
      output_key: final_path
```

## 5. Testing Enhanced Clarification

### Example Test Case
```python
# Intent-based call that will trigger clarification
intent_call = {
    "mcp": {
        "tool": "filesystem",
        "intent": "read the config",  # Deliberately vague
        "context": "need to check database settings"
    }
}

# Expected clarification flow:
# 1. Agent finds multiple config files
# 2. Returns: "I found database.yaml, db.env, and config.json. Which contains your database settings?"
# 3. User responds: "database.yaml"
# 4. Agent proceeds with reading database.yaml
```

## 6. Best Practices

### Tool Design
- **Make agents context-aware**: Use conversation history
- **Provide options**: When unclear, offer specific choices  
- **Be progressive**: Start broad, get more specific
- **Set appropriate retry limits**: Balance user experience with system resources

### Workflow Configuration
```yaml
# Recommended retry patterns
- id: clarification_step
  retry: 3  # Allow multiple clarification rounds
  rollback_to: previous_step  # If clarification fails
  rollback_limit: 1
```

### Error Handling
```yaml
- id: fallback_handler
  condition: ${retries_exhausted}
  agent: fallback_agent
  input: "Unable to understand request after clarification attempts"
  output:
    to: user
```

## 7. Integration with Existing Retries

The clarification system works seamlessly with the existing retry mechanism:

1. **Normal Retry**: Technical failures, network issues
2. **Clarification Retry**: Incomplete or ambiguous information
3. **Combined Flow**: Clarification → Technical retry → Success

This creates a robust system that handles both technical and communication challenges in intent-based tool calling. 