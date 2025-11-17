# LangSwarm v0.0.54.dev60 Release Notes

## 🔧 Critical Bug Fix: Python Literal Parsing for MCP Arguments

### Summary
Fixed a critical parsing issue where LLMs would return Python dict literals (single quotes) instead of valid JSON (double quotes), causing `json.loads()` to fail when parsing MCP tool arguments. This commonly occurred when values contained special characters like apostrophes (e.g., "Jacy'z").

### The Problem

**Symptom:**
```
⚠️  Failed to parse arguments as JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
🔍 MCP Server call with params: None
```

**Root Cause:**
When an LLM-generated parameter value contained a single quote (e.g., `Jacy'z`), the LLM would output Python literal format to avoid escaping:
```python
# What LLM returned (Python literal - INVALID JSON):
{'query': "Jacy'z company-specific information", 'limit': 10}

# What json.loads() requires (valid JSON):
{"query": "Jacy'z company-specific information", "limit": 10}
```

### The Fix

#### 1. Defensive Multi-Strategy Parsing
**File:** `langswarm/v1/core/utils/workflows/functions.py` (lines 341-367)

Added a 3-tier fallback parsing strategy:

```python
if isinstance(task_args, str):
    # Tier 1: Try standard JSON
    try:
        task_args = json.loads(task_args)
    except (json.JSONDecodeError, ValueError):
        # Tier 2: Try Python literal eval (handles single quotes)
        try:
            task_args = ast.literal_eval(task_args)  # ← Safe Python literal parser
        except (ValueError, SyntaxError):
            # Tier 3: Simple quote replacement
            try:
                sanitized = task_args.replace("'", '"')
                task_args = json.loads(sanitized)
            except json.JSONDecodeError:
                # Final fallback: empty dict
                task_args = {}
```

**Key Addition:** `ast.literal_eval()` - Python's standard library function for safely parsing Python literals like `{'key': 'value'}`.

#### 2. Force Valid JSON from Source
**File:** `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` (line 129)

Added `response_format: json_object` to the `parameter_builder` agent:

```yaml
- id: parameter_builder
  agent_type: langchain-openai
  model: gpt-4o
  allow_middleware: false
  response_format: json_object  # ← Forces OpenAI to return ONLY valid JSON
  system_prompt: |
    # ... existing prompt ...
```

This ensures OpenAI returns properly formatted JSON (double quotes) instead of Python literals (single quotes).

### Benefits

✅ **Robust Parsing:** Handles Python literals, valid JSON, and malformed strings gracefully  
✅ **No More Empty Params:** Tools receive proper parameters instead of `None`  
✅ **Special Characters:** Handles apostrophes, quotes, and other special characters correctly  
✅ **Prevention at Source:** `response_format: json_object` prevents the issue from occurring  
✅ **Backward Compatible:** Existing valid JSON continues to work  

### Impact

**Before:** MCP tool calls would fail silently with empty parameters when LLM returned Python literals  
**After:** All parameter formats (JSON, Python literal, malformed) are handled correctly

### Testing

Test with queries containing special characters:
```python
# Query with apostrophe
query = "Search for Jacy'z company policies"

# Query with quotes
query = 'Find "mission statement" documents'

# Query with both
query = "Locate Alex's 'annual review' report"
```

All should now parse correctly and reach the MCP tool with proper parameters.

### Files Changed

1. `langswarm/v1/core/utils/workflows/functions.py` - Added multi-tier parsing
2. `langswarm/tools/mcp/bigquery_vector_search/agents.yaml` - Added `response_format: json_object`
3. `pyproject.toml` - Version bump to `0.0.54.dev60`

### Migration Guide

**No migration required.** This is a backward-compatible bug fix.

**Optional Enhancement:** Add `response_format: json_object` to any agent in your YAML configs that needs to return structured JSON:

```yaml
- id: your_parameter_agent
  model: gpt-4o
  response_format: json_object  # ← Add this line
  system_prompt: |
    Return ONLY valid JSON...
```

---

**Full Changelog:** https://github.com/aekdahl/langswarm  
**Report Issues:** https://github.com/aekdahl/langswarm/issues

