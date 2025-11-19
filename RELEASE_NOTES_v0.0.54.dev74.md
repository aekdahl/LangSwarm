# Release Notes - LangSwarm v0.0.54.dev74

**Release Date:** November 19, 2024  
**Type:** Critical Bug Fix  
**Depends On:** v0.0.54.dev73 (ToolRegistry singleton)

---

## 🔥 Critical Fix

### Provider Tool Schema Access Error

**Issue:** V2 agent creation with tools failed with error:
```
OpenAI API error: Failed to build tool definitions: 'MCPToolAdapter' object has no attribute 'get'
```

**Root Cause:**
After the singleton fix in dev73, `registry.get_tool(tool_name)` now correctly returns an `IToolInterface` object (e.g., `MCPToolAdapter`), but all provider implementations (`OpenAIProvider`, `AnthropicProvider`, etc.) were treating it as a dictionary, calling `.get()` on it.

**Code Problem:**
```python
# In all providers (_get_tool_mcp_schema method)
def _get_tool_mcp_schema(self, tool_info: Dict[str, Any]):
    tool_instance = tool_info.get('tool_instance')  # ❌ tool_info is not a dict!
    metadata = tool_info.get('metadata', {})        # ❌ Causes AttributeError
```

**Solution:**
Updated all provider implementations to handle `IToolInterface` objects correctly:

```python
def _get_tool_mcp_schema(self, tool: Any):
    """Get standard MCP schema from V2 tool (IToolInterface object)"""
    if hasattr(tool, 'list_tools'):
        tools_list = tool.list_tools()
        if tools_list:
            return tools_list[0]
    
    if hasattr(tool, 'metadata'):
        metadata = tool.metadata
        return {
            "name": getattr(metadata, 'name', 'unknown'),
            "description": getattr(metadata, 'description', ''),
            "input_schema": getattr(metadata, 'input_schema', {...})
        }
```

---

## 📝 Files Modified

### Providers Fixed:
1. **`langswarm/core/agents/providers/openai.py`**
   - ✅ Fixed `_get_tool_mcp_schema()` to accept `IToolInterface` object
   - ✅ Added proper attribute access instead of dictionary access
   - ✅ Added fallback for tools without `list_tools()` method

2. **`langswarm/core/agents/providers/anthropic.py`**
   - ✅ Same fixes as OpenAI provider

3. **`langswarm/core/agents/providers/cohere.py`**
   - ✅ Same fixes as OpenAI provider

4. **`langswarm/core/agents/providers/gemini.py`**
   - ✅ Same fixes as OpenAI provider

5. **`langswarm/core/agents/providers/mistral.py`**
   - ✅ Fixed (slightly different original implementation)

6. **`pyproject.toml`**
   - ✅ Version bumped: `0.0.54.dev73` → `0.0.54.dev74`

---

## ✅ What Now Works

### Complete V2 Agent Creation Flow

```python
from langswarm.core.agents import create_openai_agent
from langswarm.tools import ToolRegistry

# Step 1: Populate registry (singleton)
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()  # Finds tools

# Step 2: Create agent with tools - NOW WORKS! ✅
agent = await create_openai_agent(
    name="assistant",
    model="gpt-4o-mini",
    system_prompt="You are helpful",
    tools=['bigquery_vector_search']  # Tool found and schema extracted!
)

# Step 3: Use agent
result = await agent.chat("What is Jacy'z?", session_id="demo_123")
print(result.content)  # ✅ Works!
```

---

## 🔍 Technical Details

### The Issue Chain

1. **dev72 and earlier:** Each `ToolRegistry()` call created new empty instance
2. **dev73 (yesterday):** Fixed with singleton pattern - registry shared correctly
3. **dev74 (today):** Fixed providers to handle the tool objects correctly

### Why It Failed in dev73

The singleton fix made `registry.get_tool()` work correctly, but exposed a second bug:

```python
# What get_tool() returns
tool = registry.get_tool('bigquery_vector_search')
# tool is: MCPToolAdapter object (has .metadata, .list_tools())

# What providers expected
# They expected: {"tool_instance": ..., "metadata": {...}}

# What happened
tool_info.get('tool_instance')  # AttributeError: MCPToolAdapter has no .get()
```

### The Fix

Changed from dictionary access to object attribute access:

**Before:**
```python
tool_instance = tool_info.get('tool_instance')
metadata = tool_info.get('metadata', {})
name = metadata.get('name', 'unknown')
```

**After:**
```python
# tool is the tool object directly
if hasattr(tool, 'metadata'):
    metadata = tool.metadata
    name = getattr(metadata, 'name', 'unknown')
```

---

## 🧪 Testing

Verified with actual agent creation:

```python
registry = ToolRegistry()
count = registry.auto_populate_with_mcp_tools()
print(f"Registered {count} tools")  # 13 tools

agent = await create_openai_agent(
    name="test",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)
# ✅ No errors! Agent created successfully

result = await agent.chat("Hello", session_id="test")
# ✅ Works!
```

---

## 📦 Upgrade Path

**Required for all V2 users:**

```bash
pip install --upgrade langswarm==0.0.54.dev74
```

**No code changes needed** - this is a transparent bug fix.

---

## ⚠️ Important Notes

### Dependency Chain

- **dev74 requires dev73** - The singleton pattern from dev73 is required
- **Do not skip dev73** - Going straight from dev72 to dev74 won't work

### Both Fixes Needed

To successfully use V2 agents with tools, you need:
1. ✅ **dev73** - ToolRegistry singleton (fixes registry visibility)
2. ✅ **dev74** - Provider schema access (fixes tool schema extraction)

---

## 🐛 Known Issues (None)

All V2 tool integration issues are now resolved.

---

## 👥 Credits

**Reported by:** User experiencing V2 agent creation errors in production  
**Root cause identified by:** Error analysis of production logs  
**Fixed by:** Core team

---

## 📚 Related Documentation

- [V2 Agent Creation Guide](docs/v2/agents.md)
- [Tool Registry Documentation](docs/v2/tools/registry.md)
- [V1 to V2 Migration Guide](docs/migration/v1-to-v2.md)
- [Release Notes v0.0.54.dev73](RELEASE_NOTES_v0.0.54.dev73.md) - Singleton fix

