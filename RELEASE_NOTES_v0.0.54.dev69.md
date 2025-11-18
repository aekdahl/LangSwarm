# Release Notes: LangSwarm v0.0.54.dev69

**Release Date**: 2025-11-18

## 🎯 Critical Fixes: JSON Object Response Format Support

This release fixes a critical workflow execution issue where agents configured with `response_format: json_object` were having their JSON responses stored as strings instead of dictionaries, breaking template resolution and property access.

---

## 🐛 Bug Fixes

### 1. **JSON Object Responses Stored as Dicts** ✅

**Problem**: Agents with `response_format: json_object` returned valid JSON, but the V1 workflow executor was:
- Storing responses as JSON strings instead of parsed dicts
- Failing validation because internal agents don't have a `response` wrapper field
- Breaking template expressions like `${context.step_outputs.parse_and_extract.operation}`

**Symptoms**:
```
⚠️ Failed to resolve: ${context.step_outputs.parse_and_extract.operation}
Cannot access property 'operation' on str value at 'step_outputs.parse_and_extract.operation'
Current value: '{'operation': 'similarity_search', 'query': "...", ...}'
```

**Fix**: Modified `WorkflowExecutor` to automatically detect and parse JSON responses:

**File**: `langswarm/v1/core/config.py` (lines 3312-3324, 3755-3767)

```python
# After agent.chat() is called
if hasattr(agent, 'response_format') and agent.response_format == 'json_object':
    try:
        import json
        if isinstance(output, str):
            parsed_output = json.loads(output)
            if isinstance(parsed_output, dict):
                output = parsed_output
                print(f"✅ Parsed json_object response from agent '{step['agent']}' into dict")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️  Failed to parse json_object response from agent '{step['agent']}': {e}")
        # Keep output as string if parsing fails
```

**Impact**:
- ✅ Step outputs are now proper dicts, not stringified JSON
- ✅ Template expressions like `.operation`, `.query` work correctly
- ✅ Internal workflow agents can return pure JSON without `response` wrapper
- ✅ Compatible with consolidated workflow agents (e.g., `intent_and_param_extractor`, `query_enhancer_and_finalizer`)

**Applied to**: Both sync (`_execute_step_inner_sync`) and async (`_execute_step_inner_async`) execution paths

---

### 2. **Fixed Workflow YAML References** ✅

**Problem**: BigQuery tool workflow was referencing removed steps from pre-consolidation architecture:
- `${context.step_outputs.normalize_input}` (removed in Strategy B)
- `${context.step_outputs.clean_intent}` (removed in Strategy B)

**Fix**: Updated workflow to use correct consolidated step references:

**File**: `langswarm/tools/mcp/bigquery_vector_search/workflows.yaml` (lines 45-65)

**Before**:
```yaml
- id: format_response
  input: |
    Operation: ${context.step_outputs.clean_intent}  # ❌ Doesn't exist
    Original request: ${context.step_outputs.normalize_input}  # ❌ Doesn't exist
```

**After**:
```yaml
- id: format_response
  input: |
    Operation: ${context.step_outputs.parse_and_extract.operation}  # ✅ Correct
    Original request: ${user_query}  # ✅ Use workflow input
```

**Impact**:
- ✅ Error formatting now receives correct operation type
- ✅ Response formatting gets the original user query
- ✅ No more `<UNRESOLVED:...>` warnings in logs

---

## 📋 Changes Summary

| Component | Change | Impact |
|-----------|--------|--------|
| `WorkflowExecutor` (sync) | Auto-parse `json_object` responses | Step outputs are dicts |
| `WorkflowExecutor` (async) | Auto-parse `json_object` responses | Step outputs are dicts |
| BigQuery workflow | Fix step references | Correct error/response formatting |

---

## 🔄 Migration Guide

### No Breaking Changes

This release is **100% backward compatible**. All fixes are internal improvements that:
- Don't change public APIs
- Don't modify YAML schema
- Auto-detect and apply when `response_format: json_object` is present

### What You Get Automatically

If you're using agents with `response_format: json_object`:
```yaml
agents:
  - id: my_internal_agent
    model: gpt-4o-mini
    response_format: json_object  # Now fully supported!
    system_prompt: |
      Return pure JSON like: {"operation": "search", "query": "..."}
```

**Before this release**: Response stored as string `'{"operation": "search"}'`
**After this release**: Response stored as dict `{"operation": "search"}`

---

## 🎯 Testing Recommendations

### Test Case 1: Internal Workflow Agents
```yaml
# Test that consolidated agents return proper dicts
workflows:
  test_workflow:
    steps:
      - id: parse
        agent: intent_and_param_extractor  # response_format: json_object
        input: "User query: search for Jacy'z"
      
      - id: use_output
        function: some_function
        args:
          operation: ${context.step_outputs.parse.operation}  # Should work!
          query: ${context.step_outputs.parse.query}  # Should work!
```

**Expected**: No `Cannot access property 'operation' on str value` errors

### Test Case 2: MCP Tool Calls
```python
# Should now pass correct method name to MCP server
payload:
  name: ${context.step_outputs.parse_and_extract.operation}  # Now resolves correctly
  arguments: ${context.step_outputs.enhance_and_finalize}  # Now a dict, not string
```

**Expected**: MCP tools receive correct method names instead of `None`

---

## 🔍 Debug Output

When this fix is active, you'll see these confirmation messages:
```
✅ Parsed json_object response from agent 'intent_and_param_extractor' into dict
✅ Parsed json_object response from agent 'query_enhancer_and_finalizer' into dict
```

If parsing fails (malformed JSON), you'll see:
```
⚠️  Failed to parse json_object response from agent 'my_agent': Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

---

## 📊 Performance Impact

**Minimal**: JSON parsing happens once per agent step, only for agents with `response_format: json_object`.

**Typical overhead**: < 1ms per step

---

## 🚀 Related Improvements

This fix complements:
- **v0.0.54.dev68**: Strategy B (2-step consolidation) for BigQuery tool
- **v0.0.54.dev67**: MCP structure parsing and system-wide MCP stripping
- **v0.0.54.dev65**: Fundamental workflow execution bug fix

Together, these releases create a **robust, low-latency internal workflow system** for MCP tools.

---

## 📝 Known Issues & Limitations

### 1. Validation Warnings Still Appear
The warning `Invalid structured response from gpt-4o-mini: Missing required 'response' field` will still appear in logs because validation happens in `AgentWrapper.chat()` before the workflow executor parses the response.

**Impact**: Cosmetic only - the fix still works

**Future improvement**: Add `response_format` awareness to validation logic

### 2. Only Applies to Workflow Steps
This fix only applies to agent steps in workflows. Direct `.chat()` calls outside workflows are unaffected.

---

## 🎓 Developer Notes

### Why JSON Strings Were a Problem

V1's workflow engine uses template resolution like:
```python
${context.step_outputs.my_step.property}
```

This requires `my_step` to be a **dict**, not a string. When agents returned JSON strings:
1. String gets stored in `step_outputs['my_step']`
2. Template tries to access `.property` on a string
3. Python throws `TypeError: string indices must be integers`
4. Workflow executor catches it and returns `None`
5. Downstream steps receive `None` instead of the value

### The Fix Strategy

1. **Detect**: Check if agent has `response_format == 'json_object'`
2. **Parse**: Use `json.loads()` to convert string to dict
3. **Validate**: Ensure result is a dict before replacing
4. **Store**: Dict goes into `step_outputs`, making property access work
5. **Fallback**: If parsing fails, keep as string (backward compatible)

---

## 🔗 Related Issues

- Fixes template resolution errors in BigQuery vector search tool
- Resolves `Cannot access property 'operation' on str value` errors
- Enables pure JSON agents without `response` wrapper requirement

---

## 📦 Upgrade Instructions

```bash
# Pull latest version
cd /path/to/LangSwarm
git pull origin main

# Install (if using locally)
pip install -e .

# Or install from PyPI when published
pip install --upgrade langswarm
```

---

## ✅ Verification

After upgrading, verify the fix works:

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Load config with response_format: json_object agents
loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()

# Execute workflow
executor = WorkflowExecutor(workflows, agents)
result = executor.run_workflow('bigquery_search_workflow', {
    'user_input': 'search for company info',
    'user_query': 'Jacy\'z'
})

# Check debug output
# Should see: ✅ Parsed json_object response from agent '...' into dict
# Should NOT see: Cannot access property 'operation' on str value
```

---

**Full Changelog**: [v0.0.54.dev68...v0.0.54.dev69](https://github.com/aekdahl/langswarm/compare/v0.0.54.dev68...v0.0.54.dev69)

