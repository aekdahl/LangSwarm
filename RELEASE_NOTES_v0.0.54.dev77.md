# Release Notes - LangSwarm v0.0.54.dev77

**Release Date:** November 19, 2024  
**Type:** Critical Bug Fix  
**Depends On:** v0.0.54.dev76 (AgentUsage attribute names)

---

## 🔥 Critical Fix

### Empty Response Content - Message Object Not Being Passed

**Issue:** V2 agents returning empty responses. Users saw:
```
✅ Extracted from result.message.content: 0 chars
🤖 V2 Response: 0 chars -
```

Even though OpenAI API returned `200 OK` and the agent generated content.

**Root Cause:**
All providers (OpenAI, Anthropic, Gemini) were creating detailed `AgentMessage` objects with tool calls and metadata, but then **not passing them** to `AgentResponse.success_response()`. This caused `success_response()` to create a NEW basic message without the original content and metadata.

**What Was Happening:**
```python
# Provider creates detailed message
agent_message = AgentMessage(
    role="assistant",
    content="Here is information about Jacy'z...",  # ✅ Has content
    tool_calls=[...],
    metadata={...}
)

# But then doesn't use it!
return AgentResponse.success_response(
    content="...",
    # ❌ No message parameter - creates new basic message
    usage=usage
)

# Result: AgentResponse has TWO messages:
# - response.content: "Here is information..."  ✅ Has content
# - response.message.content: ""  ❌ Empty basic message!
```

**Solution:**
Modified `AgentResponse.success_response()` to accept an optional `message` parameter, and updated all providers to pass their detailed message objects.

---

## 📝 Changes Made

### Core Response Class:

1. **`langswarm/core/agents/base.py`**
   - ✅ Added optional `message` parameter to `success_response()`
   - ✅ Uses provided message if given, creates new one if not (backward compatible)

### All Provider Implementations Fixed:

2. **`langswarm/core/agents/providers/openai.py`**
   - ✅ Non-streaming response: Pass `agent_message` to `success_response()`
   - ✅ Streaming chunks: Pass `chunk_message` to `success_response()`
   - ✅ Final stream message: Pass `final_message` to `success_response()`

3. **`langswarm/core/agents/providers/anthropic.py`**
   - ✅ Pass `agent_message` with tool calls and metadata

4. **`langswarm/core/agents/providers/gemini.py`**
   - ✅ Pass `agent_message` with safety ratings and metadata

5. **`pyproject.toml`**
   - ✅ Version bumped: `0.0.54.dev76` → `0.0.54.dev77`

---

## 🔍 Technical Details

### The Problem in Detail

Providers were creating TWO messages:
1. **Detailed message** (agent_message) - had tool_calls, metadata, etc.
2. **Basic message** (created by success_response) - just role + content

The `AgentResponse` object has:
- `response.content` - works correctly ✅
- `response.message` - was the basic message ❌

User code extracting `result.message.content` got the empty basic message instead of the detailed one!

### The Fix

**Before (Broken):**
```python
# OpenAI provider
agent_message = AgentMessage(
    role="assistant",
    content=message.content or "",
    tool_calls=getattr(message, 'tool_calls', None),
    metadata={...}
)

return AgentResponse.success_response(
    content=message.content or "",
    # ❌ agent_message created but not used!
    usage=usage
)

# Inside success_response():
def success_response(cls, content, usage=None, **metadata):
    message = AgentMessage(role="assistant", content=content)  # ❌ Creates NEW message
    return cls(content=content, message=message, usage=usage)
```

**After (Fixed):**
```python
# OpenAI provider
agent_message = AgentMessage(
    role="assistant",
    content=message.content or "",
    tool_calls=getattr(message, 'tool_calls', None),
    metadata={...}
)

return AgentResponse.success_response(
    content=message.content or "",
    message=agent_message,  # ✅ Pass the detailed message!
    usage=usage
)

# Inside success_response():
def success_response(cls, content, message=None, usage=None, **metadata):
    if message is None:
        message = AgentMessage(role="assistant", content=content)  # Fallback
    return cls(content=content, message=message, usage=usage)  # ✅ Uses provided message
```

---

## ✅ What Now Works

### Complete Agent Response with Proper Message Objects

```python
from langswarm.core.agents import create_openai_agent

agent = await create_openai_agent(
    name="assistant",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)

result = await agent.chat("Vad vet du om Jacy'z?", session_id="demo")

# Both ways now work! ✅
print(result.content)          # "Jacy'z är ett hotell..."
print(result.message.content)  # "Jacy'z är ett hotell..."

# Message object has full details
print(result.message.metadata)     # {"model": "gpt-4o-mini", ...}
print(result.message.tool_calls)   # [...] if tools were called
```

---

## 📦 Upgrade Path

**Required for all V2 users:**

```bash
pip install --upgrade langswarm==0.0.54.dev77
```

**No code changes needed** - this is a transparent bug fix that maintains backward compatibility.

---

## ⚠️ Complete V2 Fix Chain

To use V2 agents successfully, you need all these fixes:

1. ✅ **dev73** - ToolRegistry singleton (registry visibility)
2. ✅ **dev74** - Provider schema access (handle IToolInterface objects)
3. ✅ **dev75** - Tool name validation (use registry keys, not display names)
4. ✅ **dev76** - AgentUsage attributes (use prompt_tokens/completion_tokens)
5. ✅ **dev77** - AgentMessage passing (preserve tool calls and metadata)

**All five versions required for full V2 functionality!**

---

## 🧪 Testing

Verified with actual agent execution and response extraction:

```python
agent = await create_openai_agent(
    name="test",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)

result = await agent.chat("Vad vet du om Jacy'z?")

# Verify both content access methods work
assert result.content != ""
assert result.message.content != ""
assert result.content == result.message.content
assert result.message.role == "assistant"

# Verify metadata is preserved
assert "model" in result.message.metadata
assert result.message.metadata["provider"] == "openai"

# Verify tool calls are preserved if present
if result.message.tool_calls:
    assert isinstance(result.message.tool_calls, list)
    
# ✅ All assertions pass!
```

---

## 🐛 Known Issues (None)

All V2 agent response issues are now resolved. The complete fix chain (dev73 → dev74 → dev75 → dev76 → dev77) enables full V2 functionality.

---

## 👥 Credits

**Reported by:** User experiencing empty responses in production  
**Root cause identified by:** Log analysis showing 0 char extraction  
**Fixed by:** Core team

---

## 📚 Related Documentation

- [AgentResponse API Reference](docs/v2/agents/response.md)
- [AgentMessage Structure](docs/v2/agents/messages.md)
- [V2 Agent Creation Guide](docs/v2/agents.md)
- [Release Notes v0.0.54.dev73](RELEASE_NOTES_v0.0.54.dev73.md) - Singleton fix
- [Release Notes v0.0.54.dev74](RELEASE_NOTES_v0.0.54.dev74.md) - Schema access fix
- [Release Notes v0.0.54.dev75](RELEASE_NOTES_v0.0.54.dev75.md) - Tool name validation
- [Release Notes v0.0.54.dev76](RELEASE_NOTES_v0.0.54.dev76.md) - AgentUsage attributes

