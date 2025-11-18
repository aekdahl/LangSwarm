# LangSwarm v0.0.54.dev64 Release Notes

## 🛡️ Critical Fix: Prevent Hallucinated Tool Calls from Internal Agents

### Summary
Fixed a critical issue where internal agents (with `allow_middleware: false`) would hallucinate MCP tool calls in their responses, causing workflows to loop endlessly or trigger unintended tool executions. Implemented system-wide MCP stripping when returning to user.

### The Problem

**Symptom:**
Internal formatting agents would return responses like:
```json
{
  "response": "Here's the information...",
  "mcp": {
    "tool": "dataset_service",
    "intent": "resolve dataset access issue"
  }
}
```

Even though they had `allow_middleware: false` and were explicitly instructed not to call tools.

**Root Cause:**
1. All V1 agents receive auto-injected JSON format instructions that teach both patterns:
   - `{"response": "..."}` (conversation only)
   - `{"response": "...", "mcp": {...}}` (with tool calls)
2. Internal agents see MCP blocks in conversation context from previous workflow steps
3. They mimic this format even when they shouldn't have tool access
4. The workflow executor would interpret these hallucinated `mcp` blocks as real tool calls, causing:
   - Endless loops (trying to execute non-existent tools)
   - Unintended tool executions
   - Workflow state corruption

### The Fixes

#### 1. Enhanced Agent Instructions (BigQuery Tool)
**File:** `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` (lines 185-231)

Updated `search_response_formatter` agent with explicit "Conversation only" instructions:

```yaml
- id: search_response_formatter
  system_prompt: |
    ⚠️ CRITICAL OUTPUT FORMAT ⚠️
    You are a FORMATTING agent ONLY. You do NOT have access to tools.
    Use the "Conversation only" response pattern:
    
    {
      "response": "Your formatted answer here..."
    }
    
    Do NOT include the "mcp" field. Do NOT call any tools.
    REMEMBER: Return ONLY {"response": "..."} with NO "mcp" field.
```

Key additions:
- Visual attention grabber (`⚠️`)
- References the exact pattern name ("Conversation only") from auto-injected instructions
- Explicit example showing NO mcp field
- Multiple emphatic reminders

#### 2. System-Wide MCP Stripping
**File:** `langswarm/v1/core/config.py` (lines 3855-3880)

Added automatic MCP block removal when returning to user in `_handle_output`:

```python
if target == "user":
    # Strip hallucinated MCP tool calls from responses before returning to user
    cleaned_output = output
    
    # Handle dict outputs with mcp field
    if isinstance(output, dict) and 'mcp' in output:
        print(f"⚠️  Stripping hallucinated 'mcp' block from response before returning to user")
        if 'response' in output:
            cleaned_output = output['response']
        else:
            cleaned_output = {k: v for k, v in output.items() if k != 'mcp'}
    
    # Handle string outputs that might contain JSON with mcp field
    elif isinstance(output, str):
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict) and 'mcp' in parsed:
                print(f"⚠️  Detected and stripping 'mcp' block from JSON string response")
                cleaned_output = parsed.get('response', parsed)
        except (json.JSONDecodeError, ValueError):
            pass  # Not JSON, keep as-is
    
    # Return cleaned output to user
    self.context["user_output"] = cleaned_output
```

This ensures:
- ✅ All responses to user are sanitized
- ✅ Hallucinated `mcp` blocks are automatically removed
- ✅ Works for both dict and JSON string outputs
- ✅ Preserves the actual response content
- ✅ Prevents endless loops and unintended tool executions

#### 3. Additional Fixes

**Uncommented `response_format: json_object`** (line 129):
- Forces `parameter_builder` agent to return valid JSON
- Prevents Python literal format issues

**Fixed template syntax** (line 71 in `workflows.yaml`):
- Changed from `${context.step_outputs.get('enhance_query', '')}` (not supported)
- To `${context.step_outputs.enhance_query}` (direct reference)

**Added debug logging** (`functions.py` line 343):
- Shows raw argument string before parsing attempts
- Helps diagnose JSON/Python literal parsing issues

### Benefits

✅ **Prevents Endless Loops:** Hallucinated tool calls no longer trigger workflow continuation  
✅ **System-Wide Protection:** All workflows automatically strip MCP from user-directed outputs  
✅ **Backward Compatible:** Legitimate tool calls in non-user steps work normally  
✅ **Clear Agent Instructions:** Internal agents know exactly which response format to use  
✅ **Defensive Coding:** Handles both dict and JSON string outputs  
✅ **Better Debugging:** Added logging to track when MCP blocks are stripped  

### Impact

**Before:**
- Internal agents would hallucinate tool calls
- Workflows would loop endlessly trying to execute fake tools
- User responses contained confusing MCP blocks
- Tool execution could be triggered unintentionally

**After:**
- Internal agents receive explicit "Conversation only" instructions
- All MCP blocks are automatically stripped before returning to user
- Clean, tool-free responses delivered to users
- Workflows complete normally without loops

### Testing

Test with workflows that have internal formatting agents:

```python
# Run a workflow with a formatting step that returns to user
result = executor.run_workflow('workflow_with_formatter', user_input="test query")

# Result should be clean text or {"response": "..."}
# NO "mcp" field should appear
assert 'mcp' not in result if isinstance(result, dict) else True
```

### Files Changed

1. `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` - Enhanced `search_response_formatter` instructions
2. `langswarm/v1/core/config.py` - Added MCP stripping in `_handle_output` (lines 3855-3880)
3. `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` - Uncommented `response_format: json_object` for `parameter_builder`
4. `langswarm/tools/mcp/bigquery_vector_search/workflows.yaml` - Fixed template syntax for `enhance_query`
5. `langswarm/v1/core/utils/workflows/functions.py` - Added debug logging for argument parsing
6. `pyproject.toml` - Version bump to `0.0.54.dev64`

### Migration Guide

**No migration required.** This is a backward-compatible bug fix.

**For your own workflows:**
If you have internal agents that shouldn't call tools, add this to their system prompts:

```yaml
system_prompt: |
  ⚠️ CRITICAL OUTPUT FORMAT ⚠️
  Use the "Conversation only" response pattern:
  
  {
    "response": "Your content here..."
  }
  
  Do NOT include the "mcp" field. Do NOT call any tools.
```

### Related Issues

- Fixes endless loop when internal agents hallucinate tool calls
- Resolves unintended tool executions from formatting agents
- Prevents workflow state corruption from fake MCP blocks

---

**Full Changelog:** https://github.com/aekdahl/langswarm  
**Report Issues:** https://github.com/aekdahl/langswarm/issues

