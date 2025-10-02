# MCP Tool Template System

This document describes the template system used for MCP tools in LangSwarm.

## Template Components

Each MCP tool consists of several key files that work together:

### Required Files
- `main.py` - The core tool implementation
- `agents.yaml` - Agent configurations for the tool workflow
- `workflows.yaml` - Workflow definitions and step orchestration  
- `template.md` - Tool instructions and examples for the LLM

### Optional Files
- `tools.yaml` - Tool-specific configurations (deprecated in favor of inline configs)
- `README.md` - Human-readable documentation

## Template Usage

### For LLM Use
The `template.md` files are specifically designed for LLM consumption and contain:
- Tool capabilities and limitations
- Usage examples and patterns
- Parameter specifications
- Response format expectations

### For Human Use  
The `README.md` files provide human-readable documentation including:
- Setup instructions
- Configuration options
- Integration examples
- Troubleshooting guides

## Template Loading

The template system automatically loads appropriate templates based on:
1. Tool-specific template.md files (highest priority)
2. Fallback to template variables if no tool-specific template exists
3. Dynamic template composition for complex workflows

## Best Practices

### Workflow Design
- Use descriptive step IDs and agent names
- Include retry mechanisms for critical steps
- Design for both success and failure paths
- Implement proper output routing

### Agent Configuration
- Use appropriate models for different complexity levels
- Design clear, specific system prompts
- Include examples in prompts where helpful
- Consider token limits and costs

### Template Content
- Focus on LLM-consumable instructions
- Include concrete examples
- Specify exact output formats
- Avoid human-specific explanations

## Flexible Input Pattern (Recommended)

For tools that accept general user input, implement the **flexible input pattern** for maximum compatibility:

### Workflow Configuration
```yaml
workflows:
  main_workflow:
    - id: use_tool
      inputs:
        - user_input    # New format (preferred)
        - user_query    # Legacy format (backwards compatibility)
      steps:
        - id: normalize_input
          agent: input_normalizer
          input: 
            user_input: ${user_input}
            user_query: ${user_query}
          output_key: normalized_input
        
        - id: main_processing
          agent: tool_processor
          input: ${normalized_input}  # Use normalized input
          output:
            to: user
```

### Input Normalizer Agent
```yaml
- id: input_normalizer
  agent_type: langchain-openai
  model: gpt-4
  system_prompt: |
    You are an input normalizer that handles multiple input variable formats.
    You will receive both user_input and user_query variables. One or both may be provided:
    - If user_input is provided and user_query is empty/null, use user_input
    - If user_query is provided and user_input is empty/null, use user_query  
    - If both are provided, prefer user_input
    - If neither is provided, return "No input provided"
    
    Simply return the chosen input value exactly as provided, without any additional formatting or explanation.
```

### Benefits
- ✅ Backwards compatibility with legacy systems
- ✅ Support for both intent-based and direct tool calling
- ✅ Consistent input handling across all tools
- ✅ Future-proof against variable naming changes

### When to Use
Use the flexible input pattern for tools that:
- Accept general natural language user requests
- Are called via intent-based workflows
- Need backwards compatibility with existing systems
- May be integrated with multiple calling systems

### When NOT to Use
Skip the flexible input pattern for tools that:
- Use only specific structured parameters (like dynamic_forms)
- Have complex multi-parameter inputs
- Are internal-only tools with fixed interfaces
- Have performance requirements that can't support normalization overhead

## Template Evolution

The template system continues to evolve with new patterns and best practices. Key recent additions:

### Clarification System Integration
Templates now support modular prompt fragments for:
- Basic clarification requests
- Retry behavior instructions
- Intent-based workflow patterns  
- Cross-workflow clarification routing

### Input Normalization
Standardized input normalization patterns ensure compatibility across different calling systems and variable naming conventions.

This ensures all MCP tools follow consistent patterns while maintaining flexibility for specific use cases. 