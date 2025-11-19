# Release Notes - LangSwarm v0.0.54.dev75

**Release Date:** November 19, 2024  
**Type:** Critical Bug Fix  
**Depends On:** v0.0.54.dev74 (Provider tool schema access)

---

## 🔥 Critical Fix

### OpenAI Tool Name Validation Error

**Issue:** V2 agent creation with tools failed with OpenAI API error:
```
Error code: 400 - {'error': {'message': "Invalid 'tools[0].function.name': string does not match pattern. Expected a string that matches the pattern '^[a-zA-Z0-9_-]+$'."}}
```

**Root Cause:**
Tool names from the tool's MCP schema (e.g., "BigQuery Vector Search") contained spaces and other characters not allowed by OpenAI's pattern `^[a-zA-Z0-9_-]+$`. Only alphanumeric characters, underscores, and hyphens are valid.

**What Was Happening:**
```python
# Tool registry key (valid)
tool_name = "bigquery_vector_search"  # ✅ Matches pattern

# But we were using the tool's display name from schema
schema_name = "BigQuery Vector Search"  # ❌ Has spaces, rejected by OpenAI
```

**Solution:**
Use the **registry key** (which is guaranteed to be valid) as the function name instead of the tool's display name from its schema.

---

## 📝 Changes Made

### All Provider Implementations Updated:

1. **`langswarm/core/agents/providers/openai.py`**
   - ✅ Pass `tool_name` (registry key) to conversion method
   - ✅ Use registry key as function name instead of schema name
   
2. **`langswarm/core/agents/providers/anthropic.py`**
   - ✅ Same fix for Claude compatibility
   
3. **`langswarm/core/agents/providers/cohere.py`**
   - ✅ Same fix for Cohere compatibility
   
4. **`langswarm/core/agents/providers/gemini.py`**
   - ✅ Same fix for Gemini compatibility
   
5. **`langswarm/core/agents/providers/mistral.py`**
   - ✅ Same fix for Mistral compatibility

6. **`pyproject.toml`**
   - ✅ Version bumped: `0.0.54.dev74` → `0.0.54.dev75`

---

## 🔍 Technical Details

### Before (Broken):

```python
def _build_tool_definitions(self, tool_names: List[str]):
    for tool_name in tool_names:
        tool = registry.get_tool(tool_name)
        mcp_schema = self._get_tool_mcp_schema(tool)
        # mcp_schema contains: {"name": "BigQuery Vector Search", ...}
        openai_tool = self._convert_mcp_to_openai_format(mcp_schema)
        # ❌ Uses "BigQuery Vector Search" - INVALID for OpenAI

def _convert_mcp_to_openai_format(self, mcp_schema):
    return {
        "type": "function",
        "function": {
            "name": mcp_schema.get("name"),  # ❌ "BigQuery Vector Search"
            ...
        }
    }
```

### After (Fixed):

```python
def _build_tool_definitions(self, tool_names: List[str]):
    for tool_name in tool_names:  # tool_name = "bigquery_vector_search"
        tool = registry.get_tool(tool_name)
        mcp_schema = self._get_tool_mcp_schema(tool)
        # Pass registry key to ensure valid name
        openai_tool = self._convert_mcp_to_openai_format(mcp_schema, tool_name)
        # ✅ Uses "bigquery_vector_search" - VALID!

def _convert_mcp_to_openai_format(self, mcp_schema, tool_name=None):
    # Use registry key (guaranteed valid) if provided
    function_name = tool_name if tool_name else mcp_schema.get("name")
    
    return {
        "type": "function",
        "function": {
            "name": function_name,  # ✅ "bigquery_vector_search"
            ...
        }
    }
```

---

## ✅ What Now Works

### Complete V2 Agent Creation with Tools

```python
from langswarm.core.agents import create_openai_agent
from langswarm.tools import ToolRegistry

# Populate registry
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()

# Create agent with tools - NOW WORKS! ✅
agent = await create_openai_agent(
    name="assistant",
    model="gpt-4o-mini",
    system_prompt="You are helpful",
    tools=['bigquery_vector_search']  # ✅ Valid name sent to OpenAI!
)

# Use agent
result = await agent.chat("What is Jacy'z?", session_id="demo")
# ✅ No API errors! Tool calls work!
```

---

## 🎯 Registry Keys vs Display Names

### Registry Keys (Tool IDs):
- **Format:** `^[a-zA-Z0-9_-]+$` (lowercase with underscores)
- **Examples:** 
  - `bigquery_vector_search` ✅
  - `sql_database` ✅
  - `filesystem` ✅
  - `realtime_voice` ✅
- **Usage:** Internal tool identification, API calls

### Display Names (from tool schema):
- **Format:** Human-readable with spaces and capitals
- **Examples:**
  - "BigQuery Vector Search" 
  - "SQL Database"
  - "File System"
  - "Realtime Voice"
- **Usage:** Documentation, UI display only

**The Fix:** Always use registry keys for LLM API calls, not display names.

---

## 📦 Upgrade Path

**Required for all V2 users:**

```bash
pip install --upgrade langswarm==0.0.54.dev75
```

**No code changes needed** - this is a transparent bug fix.

---

## ⚠️ Dependency Chain

To use V2 agents with tools successfully, you need all three fixes:

1. ✅ **dev73** - ToolRegistry singleton (registry visibility)
2. ✅ **dev74** - Provider schema access (handle IToolInterface objects)
3. ✅ **dev75** - Tool name validation (use registry keys, not display names)

**Do not skip any of these versions!**

---

## 🧪 Testing

Verified with actual agent creation and tool calls:

```python
# Test 1: Agent creation
registry = ToolRegistry()
count = registry.auto_populate_with_mcp_tools()
print(f"Registered {count} tools")

agent = await create_openai_agent(
    name="test",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search', 'sql_database', 'filesystem']
)
# ✅ No OpenAI API errors!

# Test 2: Tool calling
result = await agent.chat("Search for Jacy'z in the knowledge base")
# ✅ Tool calls work correctly!
```

---

## 🐛 Known Issues (None)

All V2 tool integration issues are now resolved. The complete fix chain (dev73 → dev74 → dev75) enables full V2 agent functionality with MCP tools.

---

## 👥 Credits

**Reported by:** User experiencing OpenAI API validation errors in production  
**Root cause identified by:** OpenAI API error analysis  
**Fixed by:** Core team

---

## 📚 Related Documentation

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [V2 Agent Creation Guide](docs/v2/agents.md)
- [Tool Registry Documentation](docs/v2/tools/registry.md)
- [Release Notes v0.0.54.dev73](RELEASE_NOTES_v0.0.54.dev73.md) - Singleton fix
- [Release Notes v0.0.54.dev74](RELEASE_NOTES_v0.0.54.dev74.md) - Schema access fix

