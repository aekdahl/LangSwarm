# Release Notes - LangSwarm v0.0.54.dev76

**Release Date:** November 19, 2024  
**Type:** Critical Bug Fix  
**Depends On:** v0.0.54.dev75 (Tool name validation)

---

## 🔥 Critical Fix

### AgentUsage Attribute Name Mismatch

**Issue:** V2 agent execution failed with error:
```
Error: 'AgentUsage' object has no attribute 'input_tokens'
```

**Root Cause:**
The `AgentUsage` class uses `prompt_tokens` and `completion_tokens` as attribute names, but code in `BaseAgent` was trying to access `input_tokens` and `output_tokens` (which don't exist).

**Code Inconsistency:**
```python
# AgentUsage class definition (correct)
@dataclass
class AgentUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    ...

# But BaseAgent code was using (incorrect)
response.usage.input_tokens  # ❌ AttributeError!
response.usage.output_tokens  # ❌ AttributeError!
```

**Solution:**
Fixed all references in `BaseAgent` to use the correct attribute names from the `AgentUsage` class.

---

## 📝 Changes Made

### Files Fixed:

1. **`langswarm/core/agents/base.py`**
   - ✅ Line 568: Changed `response.usage.input_tokens` → `response.usage.prompt_tokens`
   - ✅ Line 569: Changed `response.usage.output_tokens` → `response.usage.completion_tokens`
   - ✅ Line 598: Changed `response.usage.input_tokens` → `response.usage.prompt_tokens`
   - ✅ Line 600: Changed `response.usage.output_tokens` → `response.usage.completion_tokens`

2. **`pyproject.toml`**
   - ✅ Version bumped: `0.0.54.dev75` → `0.0.54.dev76`

---

## 🔍 Technical Details

### The Naming Convention

The `AgentUsage` dataclass follows the **OpenAI naming convention**:
- `prompt_tokens` - Tokens in the input/prompt
- `completion_tokens` - Tokens in the output/completion
- `total_tokens` - Sum of both

This is consistent with:
- OpenAI API response format
- Industry standard terminology
- Most LLM provider APIs

### Where the Confusion Came From

Some LLM providers (like Anthropic) use different names:
- Anthropic: `input_tokens` and `output_tokens`
- OpenAI: `prompt_tokens` and `completion_tokens`

The providers correctly map to the `AgentUsage` standard:
```python
# Anthropic provider (correct mapping)
usage = AgentUsage(
    prompt_tokens=response.usage.input_tokens,      # Maps input → prompt
    completion_tokens=response.usage.output_tokens,  # Maps output → completion
    ...
)
```

But `BaseAgent` was incorrectly trying to access the Anthropic-style names.

---

## ✅ What Now Works

### Complete Agent Execution with Usage Tracking

```python
from langswarm.core.agents import create_openai_agent
from langswarm.tools import ToolRegistry

# Create agent
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()

agent = await create_openai_agent(
    name="assistant",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)

# Execute with usage tracking - NOW WORKS! ✅
result = await agent.chat("What is Jacy'z?", session_id="demo")

# Access usage information
if result.usage:
    print(f"Prompt tokens: {result.usage.prompt_tokens}")
    print(f"Completion tokens: {result.usage.completion_tokens}")
    print(f"Total tokens: {result.usage.total_tokens}")
    print(f"Cost estimate: ${result.usage.cost_estimate:.4f}")
# ✅ No AttributeError!
```

---

## 📦 Upgrade Path

**Required for all V2 users:**

```bash
pip install --upgrade langswarm==0.0.54.dev76
```

**No code changes needed** - this is a transparent bug fix.

---

## ⚠️ Complete V2 Fix Chain

To use V2 agents successfully, you need all these fixes:

1. ✅ **dev73** - ToolRegistry singleton (registry visibility)
2. ✅ **dev74** - Provider schema access (handle IToolInterface objects)
3. ✅ **dev75** - Tool name validation (use registry keys, not display names)
4. ✅ **dev76** - AgentUsage attributes (use prompt_tokens/completion_tokens)

**All four versions required!**

---

## 🧪 Testing

Verified with actual agent execution and usage tracking:

```python
agent = await create_openai_agent(
    name="test",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)

result = await agent.chat("Test message")

# Verify usage attributes work
assert hasattr(result.usage, 'prompt_tokens')
assert hasattr(result.usage, 'completion_tokens')
assert hasattr(result.usage, 'total_tokens')
assert result.usage.prompt_tokens >= 0
assert result.usage.completion_tokens >= 0
# ✅ All assertions pass!
```

---

## 🐛 Known Issues (None)

All V2 agent execution and usage tracking issues are now resolved.

---

## 👥 Credits

**Reported by:** User experiencing AttributeError in production  
**Root cause identified by:** Stack trace analysis  
**Fixed by:** Core team

---

## 📚 Related Documentation

- [AgentUsage API Reference](docs/v2/agents/usage.md)
- [Cost Tracking Guide](docs/v2/agents/cost-tracking.md)
- [V2 Agent Creation Guide](docs/v2/agents.md)
- [Release Notes v0.0.54.dev73](RELEASE_NOTES_v0.0.54.dev73.md) - Singleton fix
- [Release Notes v0.0.54.dev74](RELEASE_NOTES_v0.0.54.dev74.md) - Schema access fix
- [Release Notes v0.0.54.dev75](RELEASE_NOTES_v0.0.54.dev75.md) - Tool name validation

