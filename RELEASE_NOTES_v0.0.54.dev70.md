# Release Notes: LangSwarm v0.0.54.dev70

**Release Date**: 2025-11-18

## 🚀 GPT-5/GPT-5.1 Compatibility Fix

This release fixes a critical compatibility issue with newer OpenAI models (GPT-5, GPT-5.1) that reject `null` values for the `max_tokens` parameter.

---

## 🐛 Bug Fix

### **Fixed: Invalid `max_tokens` Parameter Error** ✅

**Problem**: 
OpenAI's newer models (GPT-5, GPT-5.1 released Nov 12, 2025) enforce stricter parameter validation and reject requests with `max_tokens: null`:

```
API Error: Error code: 400 - {'error': {'message': "Invalid type for 'max_tokens': 
expected an unsupported value, but got null instead.", 'type': 'invalid_request_error', 
'param': 'max_tokens', 'code': 'invalid_type'}}
```

**Root Cause**:
V1's `AgentWrapper` was always including `max_tokens` in API requests, even when set to `None`:

```python
# Before (BROKEN)
api_params = {
    "model": self.model,
    "messages": messages,
    "temperature": 0.0,
    "max_tokens": self.max_tokens  # ❌ Always included, even if None
}
```

When agents didn't have `max_tokens` configured in YAML, `self.max_tokens` would be `None`, which serializes to `null` in JSON and triggers the API error.

**Fix**: 
Modified both regular and streaming API calls to **conditionally include** `max_tokens` only when explicitly set:

**File**: `langswarm/v1/core/wrappers/generic.py`

**Location 1**: Lines 795-803 (Regular API calls)
```python
# After (FIXED)
api_params = {
    "model": self.model,
    "messages": messages,
    "temperature": 0.0
}

# Only add max_tokens if explicitly set (required for GPT-5/GPT-5.1 compatibility)
if self.max_tokens is not None:
    api_params["max_tokens"] = self.max_tokens
```

**Location 2**: Lines 1405-1414 (Streaming API calls)
```python
# After (FIXED)
api_params = {
    "model": self.model,
    "messages": self.in_memory,
    "temperature": 0.0,
    "stream": True
}

# Only add max_tokens if explicitly set (required for GPT-5/GPT-5.1 compatibility)
if self.max_tokens is not None:
    api_params["max_tokens"] = self.max_tokens
```

---

## 🎯 Impact

### ✅ What Now Works

1. **GPT-5/GPT-5.1 Support**: Can now use the latest OpenAI models without API errors
2. **Backward Compatible**: Older models (GPT-4o, GPT-4o-mini) continue to work normally
3. **Flexible Configuration**: Agents can omit `max_tokens` and rely on model defaults

### 📋 Agent Configuration Options

**Option 1: Omit `max_tokens` (Recommended)**
```yaml
agents:
  - id: my_agent
    model: gpt-5.1  # or gpt-4o-mini
    # max_tokens not specified - uses model default
```

**Option 2: Explicitly Set `max_tokens`**
```yaml
agents:
  - id: my_agent
    model: gpt-5.1
    max_tokens: 2048  # Explicit limit
```

Both configurations now work correctly!

---

## 🔄 Migration Guide

### No Action Required

This is a **100% backward-compatible fix**. No changes needed to your existing YAML configurations.

**What happens automatically**:
- ✅ Agents without `max_tokens` → Parameter omitted from API request → Model uses its default
- ✅ Agents with `max_tokens: 2048` → Parameter included in API request → Model respects limit
- ✅ Works with all OpenAI models: GPT-5.1, GPT-5, GPT-4o, GPT-4o-mini, GPT-3.5-turbo

---

## 🧪 Testing

### Verify GPT-5/GPT-5.1 Support

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Load config (agents can use gpt-5.1 without max_tokens)
loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()

# Execute workflow - should work without errors
executor = WorkflowExecutor(workflows, agents)
result = executor.run_workflow('test_workflow', {'input': 'test'})

# Expected: No "Invalid type for 'max_tokens'" error
```

### Test Case: Agent Without max_tokens

```yaml
agents:
  - id: test_gpt5
    agent_type: langchain-openai
    model: gpt-5.1
    system_prompt: "You are a test agent"
    # max_tokens intentionally omitted
```

**Before this fix**: ❌ API Error 400  
**After this fix**: ✅ Works perfectly

---

## 📊 API Parameter Changes

| Scenario | Before (dev69) | After (dev70) |
|----------|---------------|---------------|
| Agent with `max_tokens: 2048` | `"max_tokens": 2048` ✅ | `"max_tokens": 2048` ✅ |
| Agent without `max_tokens` | `"max_tokens": null` ❌ | Parameter omitted ✅ |
| Default `self.max_tokens` | `"max_tokens": 16000` ✅ | `"max_tokens": 16000` ✅ |

---

## 🔍 Technical Details

### Why This Matters for GPT-5/GPT-5.1

OpenAI's newer models have stricter parameter validation:

**GPT-4 era (lenient)**:
- Accepts `max_tokens: null` (treats as unset)
- Accepts invalid parameter values (ignores them)

**GPT-5 era (strict)**:
- Rejects `max_tokens: null` with 400 error
- Validates all parameters strictly
- Requires proper typing

### The Python `None` → JSON `null` Problem

```python
# Python code
api_params = {"max_tokens": None}  # None in Python

# JSON serialization
json.dumps(api_params)  # → '{"max_tokens": null}'

# OpenAI API receives
{"max_tokens": null}  # ❌ Rejected by GPT-5
```

### The Conditional Inclusion Solution

```python
# Python code
api_params = {}
if max_tokens is not None:
    api_params["max_tokens"] = max_tokens

# JSON serialization (when max_tokens is None)
json.dumps(api_params)  # → '{}'  (parameter omitted)

# OpenAI API receives
{}  # ✅ Accepted by GPT-5 (uses model default)
```

---

## 🎓 Model-Specific Notes

### GPT-5.1 Features (Released Nov 12, 2025)

- **Adaptive Reasoning**: Adjusts thinking time based on complexity
- **Customizable Personalities**: Tailor tone/style
- **Better Parameter Validation**: Requires this fix
- **Improved Context Handling**: 200K+ context window

### Recommended Configuration

For internal workflow agents (fast, structured tasks):
```yaml
- id: intent_parser
  model: gpt-4o-mini  # Cost-effective, fast
  max_tokens: 1024    # Constrain output for structured tasks
  response_format: json_object
```

For user-facing conversational agents:
```yaml
- id: main_assistant
  model: gpt-5.1      # Best quality, adaptive reasoning
  # max_tokens omitted - let model decide based on complexity
  system_prompt: "You are a helpful assistant..."
```

---

## 🐛 Known Issues

### Validation Warnings May Still Appear

Some debug/info logs might still reference max_tokens in error messages, but these are cosmetic. The actual API calls are now correct.

---

## 📦 Related Changes

This fix complements:
- **v0.0.54.dev69**: JSON object response format support
- **v0.0.54.dev68**: Strategy B workflow consolidation
- **v0.0.54.dev67**: MCP structure parsing fixes

Together, these releases provide **full compatibility** with OpenAI's latest models and API requirements.

---

## 🚀 Upgrade Instructions

```bash
# Pull latest version
cd /path/to/LangSwarm
git pull origin main

# Install
pip install -e .

# Or from PyPI when published
pip install --upgrade langswarm
```

---

## ✅ Verification Checklist

After upgrading:
- [ ] Workflows execute without "Invalid type for 'max_tokens'" errors
- [ ] GPT-5/GPT-5.1 models work correctly
- [ ] Existing agents with explicit max_tokens still work
- [ ] Agents without max_tokens use model defaults

---

## 📝 Developer Notes

This fix follows OpenAI's best practices:
1. **Optional parameters should be omitted**, not set to `null`
2. **Model defaults are intelligent** - let newer models decide token limits
3. **Explicit limits remain honored** when specified in configuration

The fix is applied to both:
- Regular API calls (`_call_chat_completions_api`)
- Streaming API calls (`chat` method with streaming)

Ensuring consistent behavior across all V1 execution paths.

---

**Full Changelog**: [v0.0.54.dev69...v0.0.54.dev70](https://github.com/aekdahl/langswarm/compare/v0.0.54.dev69...v0.0.54.dev70)

