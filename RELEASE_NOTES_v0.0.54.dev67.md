# LangSwarm v0.0.54.dev67 Release Notes

## 🐛 Critical Bug Fixes: MCP Structure Parsing & Error Handler Hallucinations

### Summary
Fixed two critical issues: 
1. **`error_handler` agent hallucinating MCP tool calls** - Applied the same emphatic instructions that fixed `search_response_formatter` 
2. **MCP structure not being recognized** - Tool was parsing user agent responses incorrectly, causing "Failed to parse arguments as JSON" errors

### The Problems

#### Problem 1: `error_handler` Hallucinating Tool Calls

**Symptom:**
```json
{
  "response": "It seems like the operation failed...",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "list_datasets",
    "params": {}
  }
}
```

The `error_handler` agent (with `allow_middleware: false`) was returning MCP tool call structures even though:
- It has no tool access
- It's an internal agent meant only for formatting error messages
- Instructions said "Do NOT include tool calls"

**Root Cause:** The instructions weren't emphatic enough. The agent saw MCP structures in conversation history and mimicked the format.

#### Problem 2: MCP Structure Not Recognized

**Symptom:**
```
User agent returns:
{'response': "I need to perform a similarity search...", 
 'mcp': {'tool': 'bigquery_vector_search', 'method': 'similarity_search', 
         'params': {'query': '...', 'limit': 10}}}

Tool receives:
🔍 Raw task_args string (length=106): "I need to perform a similarity search..."
⚠️ Failed to parse arguments as JSON
⚠️ All parsing attempts failed, treating as empty dict
🔍 MCP Server call with params: None
```

**Root Cause:** The BigQuery tool's `run_async` method didn't recognize the MCP structure format. It treated the entire response as "ambiguous input", passing the `response` text to the intent workflow instead of extracting `mcp.params`.

### The Fixes

#### Fix 1: Enhanced `error_handler` Instructions

**File:** `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` (lines 255-293)

Applied the same emphatic "Conversation only" pattern that successfully fixed `search_response_formatter`:

```yaml
- id: error_handler
  model: gpt-4o-mini
  allow_middleware: false
  system_prompt: |
    ⚠️ CRITICAL OUTPUT FORMAT ⚠️
    You are an ERROR HANDLER agent ONLY. You do NOT have access to tools.
    Use the "Conversation only" response pattern:
    
    {
      "response": "Your error guidance here..."
    }
    
    Do NOT include the "mcp" field. Do NOT call any tools. Do NOT suggest tool calls.
    
    REMEMBER: Return ONLY {"response": "..."} with NO "mcp" field.
    You cannot and should not call tools - you are explaining errors, not fixing them.
```

**Key additions:**
- ⚠️ Visual attention grabber
- Explicit "Conversation only" pattern reference
- Multiple emphatic reminders
- Clear example showing correct format
- Specific instruction: "You cannot and should not call tools"

#### Fix 2: MCP Structure Parsing

**File:** `langswarm/tools/mcp/bigquery_vector_search/main.py` (lines 677-689)

Added MCP structure detection **before** other input format checks:

```python
# Structured input
# Check for MCP structure first (from user-facing agents)
if "mcp" in input_data and isinstance(input_data["mcp"], dict):
    mcp_data = input_data["mcp"]
    if "method" in mcp_data and "params" in mcp_data:
        method = mcp_data["method"]
        params = mcp_data["params"]
        print(f"🔍 Extracted from MCP structure: method={method}, params={params}")
    else:
        # MCP structure but incomplete, treat as ambiguous
        return await self._handle_intent_call({
            "intent": input_data.get("response", "Process this request"),
            "context": f"incomplete MCP structure: {mcp_data}",
        })
elif "method" in input_data and "params" in input_data:
    # ... existing direct format handling ...
```

**How it works:**
1. **Checks for MCP wrapper** - Detects `{"response": "...", "mcp": {...}}`
2. **Extracts method and params** - Gets `mcp.method` and `mcp.params`
3. **Routes to correct handler** - Uses extracted values instead of whole structure
4. **Graceful fallback** - If MCP structure is incomplete, uses intent workflow

#### Bonus Fix: `response_format` Enabled

**File:** `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` (line 129)

Uncommented the `response_format: json_object` for `parameter_builder` agent:

```yaml
- id: parameter_builder
  model: gpt-4o-mini
  response_format: json_object  # Force valid JSON output (no markdown, no Python literals)
```

This ensures the agent returns **only valid JSON**, eliminating Python literal format issues.

### Benefits

✅ **No More Error Handler Hallucinations:** Error messages are clean, tool-call-free responses  
✅ **MCP Structure Properly Parsed:** User agents can return MCP calls that get executed correctly  
✅ **No More "Failed to parse arguments":** Parameters are extracted from the correct location  
✅ **Better Debugging:** Added logging shows exactly what's being extracted  
✅ **Consistent JSON:** `response_format: json_object` prevents format ambiguity  
✅ **Backward Compatible:** Existing direct method calls still work  

### Impact

**Before:**
- Error handler returned confusing MCP tool calls alongside error messages
- User agent MCP responses caused "Failed to parse arguments as JSON" errors
- Tool received None as params, causing searches to fail
- Workflows would retry with empty parameters endlessly

**After:**
- Error handler returns clean, helpful error messages only
- User agent MCP responses are properly parsed and executed
- Tool receives correct params from `mcp.params`
- Searches execute successfully with proper parameters

### Example Flow (After Fix)

```
User Agent returns:
{
  "response": "I'll search for Jacy'z information",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {"query": "Jacy'z hotel resort", "limit": 10}
  }
}
                    ↓
BigQuery Tool detects MCP structure:
🔍 Extracted from MCP structure: method=similarity_search, 
    params={'query': 'Jacy'z hotel resort', 'limit': 10}
                    ↓
Tool executes similarity_search with correct params:
✅ BigQuery search successful, 10 results found
                    ↓
Results formatted and returned to user:
"Here's what I found about Jacy'z Hotel & Resort..."
```

### Testing

Test MCP structure parsing:

```python
# User agent returns MCP structure
result = tool.run_async({
    "response": "Searching for information",
    "mcp": {
        "tool": "bigquery_vector_search",
        "method": "similarity_search",
        "params": {"query": "test query", "limit": 5}
    }
})

# Should execute similarity_search with params={'query': 'test query', 'limit': 5}
# Should NOT treat response text as arguments
```

Test error handler:

```python
# Trigger an error in the workflow
result = executor.run_workflow('bigquery_search_workflow', user_input="invalid method")

# Check that error_handler response has NO 'mcp' field
assert 'mcp' not in result
assert 'response' in result
```

### Files Changed

1. `langswarm/tools/mcp/bigquery_vector_search/agents.yaml`:
   - Lines 255-293: Enhanced `error_handler` with emphatic instructions
   - Line 129: Uncommented `response_format: json_object` for `parameter_builder`
2. `langswarm/tools/mcp/bigquery_vector_search/main.py`:
   - Lines 677-689: Added MCP structure detection and parsing
3. `pyproject.toml` - Version bump to `0.0.54.dev67`

### Related Issues

- Fixes `error_handler` hallucinating tool calls (same as `search_response_formatter` in dev64)
- Fixes "Failed to parse arguments as JSON" when user agents use MCP format
- Fixes workflows failing with None params when MCP structure is present
- Enables user-facing agents to properly call internal MCP tools

### Migration Guide

**No migration required.** These are bug fixes that make the system work as intended.

**However**, if you have custom agents that return MCP structures, they will now be properly recognized and executed. Ensure your MCP structures follow this format:

```json
{
  "response": "Optional explanation for user",
  "mcp": {
    "tool": "tool_name",
    "method": "method_name",
    "params": {"param1": "value1"}
  }
}
```

---

**Full Changelog:** https://github.com/aekdahl/langswarm  
**Report Issues:** https://github.com/aekdahl/langswarm/issues

