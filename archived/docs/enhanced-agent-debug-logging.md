# Enhanced Agent Debug Logging

This document describes the enhanced debug logging system for agent configurations in LangSwarm, which provides comprehensive visibility into agent settings and configurations during debug tracing.

## Overview

The enhanced agent debug logging system captures detailed configuration information when agents are retrieved during workflow execution, providing significantly more insight for debugging and troubleshooting purposes.

## What's Changed

### Before Enhancement (Old Format)

The original logging captured minimal information:

```json
{
  "agent_name": "bigquery_test_agent",
  "agent_type": "AgentWrapper", 
  "agent_id_attr": null,
  "agent_id_attr_alt": null,
  "has_name_attr": true,
  "name_value": "bigquery_test_agent",
  "agent_repr": "<langswarm.core.wrappers.generic.AgentWrapper object at 0x11700d0d0>"
}
```

### After Enhancement (New Format)

The enhanced logging captures comprehensive configuration details:

```json
{
  "agent_name": "bigquery_test_agent",
  "agent_type": "AgentWrapper",
  "agent_class": "langswarm.core.wrappers.generic.AgentWrapper",
  "model": "gpt-4o",
  "agent_repr": "<langswarm.core.wrappers.generic.AgentWrapper object at 0x11700d0d0>",
  "model_details": {
    "name": "gpt-4o",
    "limit": 128000,
    "ppm": 0,
    "ppm_out": 0,
    "supports_structured_output": true,
    "supports_function_calling": true,
    "supports_streaming": true,
    "streaming_type": "sse",
    "supports_structured_streaming": true
  },
  "memory_info": {
    "has_memory": false,
    "is_conversational": false,
    "memory_adapter": "<class 'NoneType'>",
    "memory_size": 1
  },
  "tool_info": {
    "has_tool_registry": true,
    "tools_count": 1,
    "tool_names": ["bigquery_search - BigQuery vector search..."]
  },
  "session_info": {
    "session_manager": "<class 'langswarm.core.session.manager.LangSwarmSessionManager'>",
    "current_session_id": null,
    "response_mode": "integrated",
    "streaming_enabled": false
  },
  "agent_settings": {
    "timeout": 60,
    "max_response_length": 50000,
    "max_tokens": null,
    "use_native_tool_calling": null,
    "context_limit": 128000
  },
  "extension_info": {
    "has_plugin_registry": true,
    "has_rag_registry": true,
    "has_broker": false
  },
  "system_prompt_info": {
    "has_system_prompt": true,
    "system_prompt_length": 9459,
    "system_prompt_full": "\\nYou are a BigQuery vector search agent. You must call the bigquery_search tool with the EXACT method requested...\\n\\n[COMPLETE SYSTEM PROMPT CONTENT HERE]"
  }
}
```

## Enhanced Information Categories

The enhanced logging now captures:

### 1. Model Configuration Details
- Model name and capabilities
- Token limits and context windows  
- Support for structured output, function calling, streaming
- Pricing information (PPM rates)

### 2. Memory Configuration
- Memory status and type
- Conversational mode settings
- Memory adapter configuration
- Current memory size

### 3. Tool Registry Information
- Tool availability status
- Number of registered tools
- Tool names and descriptions (truncated)
- Tool configuration errors (if any)

### 4. Session Management
- Session manager type
- Current session ID
- Response mode (integrated/streaming)
- Streaming enablement status

### 5. Agent-Specific Settings
- Timeout configurations
- Response length limits
- Token limits
- Tool calling preferences
- Context limits

### 6. Extension Configuration
- Plugin registry availability
- RAG (Retrieval Augmented Generation) registry status
- Message broker configuration

### 7. System Prompt Information
- System prompt availability
- Prompt length
- Complete prompt content (full text for debugging dynamic content injection)

## Implementation Details

### Safe Serialization

The enhanced logging uses a safe serialization system that:

- Prevents circular reference issues
- Limits recursion depth (max 3 levels)
- Truncates long strings to prevent log bloat
- Handles complex object types gracefully
- Provides fallback data on serialization errors

### Performance Considerations

- Serialization is only performed when debug tracing is enabled
- String truncation prevents excessive log file growth
- Fallback to basic data if serialization fails
- Lazy evaluation - only captures data when needed

## Usage

### Enabling Enhanced Logging

Enhanced logging is automatically enabled when you enable debug tracing:

```python
from langswarm.core.debug.integration import enable_debug_tracing

# Enable debug tracing - enhanced logging is included
enable_debug_tracing("debug_traces/my_session.jsonl")
```

### Viewing Enhanced Logs

The enhanced agent information appears in debug traces during workflow execution:

```json
{
  "trace_id": "...",
  "event_type": "INFO",
  "component": "workflow", 
  "operation": "agent_retrieved",
  "message": "Successfully retrieved agent bigquery_test_agent",
  "data": {
    // Enhanced agent configuration data here
  }
}
```

### Analyzing Logs

Use the enhanced information to debug:

- **Configuration Issues**: Check model_details and agent_settings
- **Tool Problems**: Review tool_info for tool counts and names
- **Memory Issues**: Examine memory_info for configuration problems
- **Performance**: Check timeout, limits, and streaming settings
- **System Prompt**: Verify system_prompt_info for prompt issues

## Integration Points

### Files Modified

1. **`langswarm/core/debug/integration.py`**
   - Added `serialize_agent_config()` function
   - Added `_safe_serialize()` helper function
   - Safe serialization with circular reference protection

2. **`langswarm/core/config.py`**
   - Updated agent retrieval logging in `_execute_step_inner_sync()`
   - Fallback to basic logging if enhanced serialization fails
   - Import protection for backward compatibility

### Backward Compatibility

The enhancement maintains full backward compatibility:

- If the enhanced serialization function is not available, falls back to original format
- No breaking changes to existing debug trace structure
- Optional enhancement that doesn't affect core functionality

## Benefits

### For Developers
- **Comprehensive Debugging**: See complete agent configuration at runtime
- **Configuration Validation**: Verify settings are applied correctly
- **Tool Troubleshooting**: Understand tool registry issues
- **Performance Analysis**: Identify configuration bottlenecks

### For Operations
- **Production Debugging**: Detailed configuration visibility in production
- **Issue Diagnosis**: Faster root cause identification
- **Configuration Auditing**: Track agent configuration changes
- **Monitoring**: Better observability into agent behavior

## Example Use Cases

### 1. Tool Configuration Issues
```json
"tool_info": {
  "has_tool_registry": true,
  "tools_count": 0,
  "tool_names": [],
  "tool_error": "Failed to initialize tools"
}
```

### 2. Memory Configuration Problems
```json
"memory_info": {
  "has_memory": false,
  "is_conversational": true,
  "memory_adapter": "<class 'NoneType'>",
  "memory_size": 0
}
```

### 3. Model Capability Verification
```json
"model_details": {
  "name": "gpt-4o",
  "supports_function_calling": true,
  "supports_structured_output": true,
  "limit": 128000
}
```

## Testing

The enhancement includes comprehensive testing:

- **`test_enhanced_agent_logging.py`**: Basic functionality test
- **`demo_enhanced_agent_logging.py`**: Comparison demo showing old vs new format
- **Integration tests**: Verify fallback behavior and error handling

## Performance Impact

- **Minimal overhead**: Only active during debug tracing
- **6x more detailed**: Provides 6x more information than previous format
- **Safe limits**: String truncation prevents excessive memory usage
- **Graceful degradation**: Falls back to basic format on errors
