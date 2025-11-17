# Release Notes: LangSwarm v0.0.54.dev58

**Release Date**: November 17, 2025  
**Type**: Critical Bug Fix - Template Resolution

---

## 🐛 Critical Bug Fix: Template Resolution Type Safety

### Summary
This release fixes a critical bug in LangSwarm V1's template resolution system that caused the infamous "string indices must be integers" error when workflows tried to access properties on non-dict step outputs.

### Problem Description
Users reported cryptic errors when workflows tried to access nested properties in templates like `${context.step_outputs.classify_intent.type}`, especially when the step output was a simple string instead of a structured dict. This caused:

1. **Cryptic error messages**: "string indices must be integers"
2. **Parameter validation failures**: Tools received None or invalid params
3. **Workflow failures**: Steps couldn't resolve dependencies
4. **Difficult debugging**: Error didn't indicate the root cause

**Example Error**:
```
⚠️ Failed to resolve: ${context.step_outputs.classify_intent.type} — string indices must be integers
🚨 PARAMETER VALIDATION FAILED in bigquery_vector_search.similarity_search: query Field required
```

### Root Cause
The `_safe_resolve` method in `langswarm/v1/core/config.py` (line 4117) was **NOT** performing type checking before accessing values:

```python
# OLD CODE (BUGGY):
def _safe_resolve(self, path_parts, context):
    current = context
    for part in path_parts:
        current = current[part]  # ❌ No type check!
    return current
```

When a step output was a string like `"search"` and the template tried to access `.type` on it, Python tried `string_value["type"]` which gives "string indices must be integers".

---

## 🔧 What Was Fixed

### 1. Type-Safe Resolution in `_safe_resolve` (Line 4117)

**Changes**:
- Added `isinstance()` checks before all property accesses
- Handles dicts, lists, and non-containers separately
- Raises clear, actionable `TypeError` when accessing properties on non-containers

**New Code**:
```python
def _safe_resolve(self, path_parts, context):
    current = context
    for part in path_parts:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                raise KeyError(f"Key '{part}' not found. Available keys: {list(current.keys())[:10]}")
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            # ✅ This is the key fix!
            raise TypeError(
                f"Cannot access property '{part}' on {type(current).__name__} value. "
                f"Current value: {repr(current)[:100]}. "
                f"Hint: The step output may be a simple value instead of a dict. "
                f"Ensure the step returns structured data if you need to access properties."
            )
    return current
```

### 2. Improved Error Handling in `_resolve_input` (Lines 4091-4102, 4105-4109)

**Changes**:
- Single variable references that fail now return `None` instead of raising exceptions
- Inline template substitutions that fail are marked as `<UNRESOLVED:...>` for debugging
- Both approaches prevent invalid data from being passed to tools

**Before**:
```python
# Failed resolution would return f"<error:{expr}>" which breaks tool validation
```

**After**:
```python
# Single variable reference failure
return None  # Prevents invalid params to tools

# Inline substitution failure
value = value.replace(f"${{{match}}}", f"<UNRESOLVED:{match}>")  # Clear debugging
```

### 3. Detailed Error Messages with Context

**Now shows**:
- The full path where resolution failed
- The type of value encountered
- The actual value (truncated)
- Available keys (for dicts)
- Actionable hints for fixing the workflow

**Example new error message**:
```
Cannot access property 'type' on str value at 'step_outputs.classify_intent.type'.
Current value: 'search'.
Hint: The step output may be a simple value instead of a dict.
Ensure the step returns structured data if you need to access properties.
```

---

## ✅ Testing Results

All test cases passed:

| Test | Result |
|------|--------|
| Accessing property on string value | ✅ Correctly raises TypeError |
| Accessing property on dict value | ✅ Works correctly |
| Accessing non-existent key | ✅ Shows available keys |
| Single variable with failed resolution | ✅ Returns None |
| Valid template resolution | ✅ Works correctly |
| Inline template substitution | ✅ Works correctly |
| Failed inline substitution | ✅ Marked as UNRESOLVED |

---

## 🎯 Impact on Users

### Before This Fix
```python
# Workflow YAML
- id: search_step
  input: "${context.step_outputs.classify_intent.type}"
  # classify_intent returns: "search"

# Result:
# ⚠️ Failed to resolve: ... — string indices must be integers
# 🚨 PARAMETER VALIDATION FAILED: query Field required
# Tool receives None or invalid params
```

### After This Fix
```python
# Same workflow YAML

# Result:
# ⚠️ Failed to resolve single variable ${...}: Cannot access property 'type' on str value
# at 'step_outputs.classify_intent.type'. Current value: 'search'.
# Hint: The step output may be a simple value instead of a dict.
# Ensure the step returns structured data if you need to access properties.
# 
# Tool receives None (cleaner failure)
```

### Recommended Workflow Fix
```yaml
# Ensure classify_intent returns structured data:
- id: classify_intent
  agent: classifier
  output:
    to: search_step
    format: json  # Returns {"type": "search", "confidence": 0.9}

# Now this works:
- id: search_step
  input: "${context.step_outputs.classify_intent.type}"  # ✅ Gets "search"
```

---

## 📋 Files Modified

- `langswarm/v1/core/config.py`:
  - Line 4117-4172: Complete rewrite of `_safe_resolve` with type checking
  - Line 4091-4102: Improved error handling for single variable references
  - Line 4105-4110: Improved error handling for inline substitutions
- `pyproject.toml`: Version bump to 0.0.54.dev58
- `test_template_resolution.py`: New comprehensive test suite

---

## 🔄 Migration Guide

### No Code Changes Required
This is a transparent bug fix. Existing workflows work unchanged.

### Recommended: Fix Workflow Structure
If you encounter the new error messages, fix your workflows to return structured data:

**Before** (causes error):
```yaml
- id: classify
  agent: my_classifier
  # Returns: "search" (plain string)

- id: next_step
  input: "${context.step_outputs.classify.type}"  # ❌ Fails!
```

**After** (works correctly):
```yaml
- id: classify
  agent: my_classifier
  # Ensure agent returns: {"type": "search", "confidence": 0.9}

- id: next_step
  input: "${context.step_outputs.classify.type}"  # ✅ Works!
```

---

## 🆚 Related Fixes

This fix complements:
- **v0.0.54.dev56**: Fixed endless retry loops
- **v0.0.54.dev57**: Added emergency stop mechanisms

Together, these three releases provide comprehensive protection against:
1. Endless loops consuming credits (dev56)
2. Runaway costs (dev57)
3. Template resolution errors breaking workflows (dev58)

---

## 🧪 Testing Recommendations

Test your workflows with:

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Test template resolution
loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, _, _, _ = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Run workflow and check for new error messages
try:
    result = executor.run_workflow('test_workflow', input)
except Exception as e:
    # New error messages will guide you to fix workflow structure
    print(e)
```

---

## 📊 Error Message Comparison

### Before (dev57)
```
⚠️ Failed to resolve: ${context.step_outputs.classify_intent.type} — string indices must be integers
```

### After (dev58)
```
⚠️ Failed to resolve single variable ${context.step_outputs.classify_intent.type}:
Cannot access property 'type' on str value at 'step_outputs.classify_intent.type'.
Current value: 'search'.
Hint: The step output may be a simple value instead of a dict.
Ensure the step returns structured data if you need to access properties.
```

---

## 🔗 Related Issues

- Fixes: Template resolution type safety
- Addresses: "string indices must be integers" errors
- Prevents: Invalid data being passed to tools
- Improves: Debugging experience with clear error messages

---

## Upgrade Instructions

### Using Poetry
```bash
poetry update langswarm
```

### Using Pip
```bash
pip install --upgrade langswarm
```

### From Source
```bash
git pull origin main
pip install -e .
```

---

## Support

If you encounter template resolution issues:
1. Check the new error messages - they include hints for fixing
2. Ensure step outputs are structured (dicts/objects) when accessing properties
3. Use `print(context['step_outputs'])` to debug step output structure
4. Open a [GitHub Issue](https://github.com/aekdahl/langswarm/issues) with workflow YAML

---

**Previous Version**: v0.0.54.dev57  
**Next Version**: TBD

---

## Acknowledgments

Thanks to the user who reported the "string indices must be integers" error and helped trace it to the `_safe_resolve` method. Your detailed logs made this fix possible!

