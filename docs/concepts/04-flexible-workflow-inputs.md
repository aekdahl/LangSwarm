# 04 - Flexible Workflow Input Variables

**Status**: ✅ **IMPLEMENTED**  
**Date**: 2024  
**Priority**: High  

## Summary

Enhanced MCP tool workflows to accept both `user_input` and `user_query` variables for maximum backwards compatibility and flexible intent-based tool calling.

## Problem Solved

Previously, workflows were inconsistent about input variable names:
- Some expected `user_input` (new intent-based system)
- Others expected `user_query` (legacy format)
- This caused `'user_query'` errors when intent-based tools were called

## Solution Implemented

### 1. ✅ **Flexible Input Acceptance**

Workflows now accept both variable names in their inputs:

```yaml
workflows:
  main_workflow:
    - id: use_filesystem_tool
      inputs:
        - user_input    # New format
        - user_query    # Legacy format
      steps:
        - id: normalize_input
          agent: input_normalizer
          input: 
            user_input: ${user_input}
            user_query: ${user_query}
          output_key: normalized_input
```

### 2. ✅ **Input Normalization Agent**

Added `input_normalizer` agent that intelligently chooses the right input:

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

### 3. ✅ **Updated Workflow Steps**

All workflow steps now use the normalized input:

```yaml
steps:
  - id: choose_function
    agent: tool_decider
    input: ${normalized_input}    # Uses normalized input
    output_key: selected_function

  - id: extract_path
    agent: path_extractor
    input: ${normalized_input}    # Uses normalized input
    output_key: extracted_path
```

## Implementation Details

### **Files Modified**:

1. **`langswarm/mcp/tools/filesystem/workflows.yaml`**:
   - Added `user_query` to inputs
   - Added `normalize_input` step
   - Updated all steps to use `${normalized_input}`

2. **`langswarm/mcp/tools/filesystem/agents.yaml`**:
   - Added `input_normalizer` agent

3. **`langswarm/mcp/tools/mcpgithubtool/workflows.yaml`**:
   - Added `user_query` to inputs
   - Added `normalize_input` step
   - Updated references to use normalized input

4. **`langswarm/mcp/tools/mcpgithubtool/agents.yaml`**:
   - Added `input_normalizer` agent

### **Logic Flow**:

```
Intent-Based Call
       ↓
kwargs: {user_input: "explore project structure"}
       ↓
Workflow Inputs: [user_input, user_query]
       ↓
Input Normalizer Agent
       ↓
Chooses user_input (since it's provided)
       ↓
All subsequent steps use normalized_input
       ↓
✅ Success!
```

## Benefits

### ✅ **Backwards Compatibility**
- Legacy workflows using `user_query` still work
- New workflows using `user_input` work
- No breaking changes to existing systems

### ✅ **Intent-Based Tool Calling**
- Resolves the original `'user_query'` error
- Intent-based clarification system works seamlessly
- Cross-workflow clarification handles variable resolution

### ✅ **Flexible Integration**
- Any system can pass either variable name
- Automatic preference for `user_input` when both provided
- Graceful fallback when neither is provided

## Usage Examples

### **Example 1: New Format (user_input)**
```python
executor.run_workflow("main_workflow", user_input="List directory contents")
```

### **Example 2: Legacy Format (user_query)**
```python
executor.run_workflow("main_workflow", user_query="Read config file")
```

### **Example 3: Both Provided (prefers user_input)**
```python
executor.run_workflow(
    "main_workflow", 
    user_input="Primary request",     # This will be used
    user_query="Secondary request"    # This will be ignored
)
```

### **Example 4: Intent-Based Call (now works!)**
```json
{
  "response": "Let me explore the project structure.",
  "mcp": {
    "tool": "filesystem",
    "intent": "explore project structure",
    "context": "need to understand codebase organization"
  }
}
```

## Testing

Created `demos/demo_flexible_workflow_inputs.py` with comprehensive tests:
- ✅ Test with `user_input` only
- ✅ Test with `user_query` only  
- ✅ Test with both variables (priority handling)
- ✅ Test intent-based call resolution
- ✅ Input normalization logic validation

## Future Enhancements

1. **Auto-Detection**: Could detect variable names automatically in workflows
2. **Custom Mappings**: Allow custom input variable mappings per tool
3. **Validation**: Add validation for input format consistency
4. **Template Generation**: Auto-generate input normalization for new tools

## Impact

🎯 **Direct Impact**: Resolves the `'user_query'` error in intent-based tool calls
🔄 **Backwards Compatibility**: 100% maintained for existing workflows  
🚀 **Enhanced Flexibility**: Supports all input variable naming conventions
📈 **Improved UX**: Seamless intent-based tool clarification system

**Result**: Intent-based tool calling now works reliably across all MCP tools with zero breaking changes. 