# Release Notes - LangSwarm v0.0.54.dev73

**Release Date:** November 19, 2024  
**Type:** Critical Bug Fix

---

## 🔥 Critical Fix

### ToolRegistry Singleton Pattern

**Issue:** V2's `ToolRegistry` was creating a new empty instance every time it was instantiated, causing tool registration failures where tools registered in one instance were not visible to other parts of the application (agent builders, providers).

**Root Cause:**
- `AgentBuilder._auto_inject_tools()` created: `registry = ToolRegistry()`
- `OpenAIProvider._build_tool_definitions()` created: `registry = ToolRegistry()`
- `AnthropicProvider._build_tool_definitions()` created: `registry = ToolRegistry()`
- Each call created a NEW empty instance instead of sharing the same registry

**Symptoms:**
```python
# User code
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()  # Registers 13 tools

agent = create_openai_agent(tools=['bigquery_vector_search'])
# Error: "Available tools: []" - agent sees empty registry!
```

**Solution:**
Implemented singleton pattern for `ToolRegistry`:
- Added `__new__` method to always return the same instance
- Added `_initialized` flag to prevent re-initialization
- All parts of the application now share the same registry instance

**Impact:**
- ✅ **V2 agent creation with tools now works correctly**
- ✅ **Tool registration is consistent across the application**
- ✅ **Fixes "Requested tools not found in registry" errors**

---

## 🛠️ Additional Improvements

### Package-Relative Tool Discovery

**Issue:** `auto_populate_with_mcp_tools()` used hardcoded absolute path:
```python
mcp_tools_directory = "/Users/alexanderekdahl/Docker/LangSwarm/langswarm/v2/tools/mcp"
```

This failed in production containers where the path doesn't exist.

**Solution:**
```python
import langswarm.tools.mcp
mcp_tools_directory = str(Path(langswarm.tools.mcp.__file__).parent)
```

**Impact:**
- ✅ **Works in both development and production environments**
- ✅ **Auto-discovers tools from installed package location**
- ✅ **No hardcoded paths**

---

## 📝 Migration Notes

### For Users Migrating from V1 to V2

**Before (dev72 - BROKEN):**
```python
from langswarm.core.agents import create_openai_agent
from langswarm.tools import ToolRegistry

# This didn't work - each ToolRegistry() call created new instance
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()

agent = await create_openai_agent(
    name="assistant",
    tools=['bigquery_vector_search']  # ❌ Error: tools not found
)
```

**After (dev73 - FIXED):**
```python
from langswarm.core.agents import create_openai_agent
from langswarm.tools import ToolRegistry

# Now works - singleton pattern ensures same instance everywhere
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()  # Registers tools

agent = await create_openai_agent(
    name="assistant",
    tools=['bigquery_vector_search']  # ✅ Works! Agent sees registered tools
)
```

---

## 🔍 Technical Details

### Singleton Implementation

```python
class ToolRegistry(IToolRegistry):
    _instance = None
    _initialized = False
    
    def __new__(cls, name: str = "default"):
        """Singleton pattern - always return the same instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "default"):
        """Initialize only once, even if called multiple times"""
        if self._initialized:
            return  # Skip re-initialization
        
        # Initialize registry state
        self.name = name
        self._tools: Dict[str, IToolInterface] = {}
        # ... rest of initialization ...
        
        self._initialized = True
```

### Path Resolution

```python
def auto_populate_with_mcp_tools(self, mcp_tools_directory: str = None) -> int:
    if mcp_tools_directory is None:
        # Use package-relative path that works everywhere
        import langswarm.tools.mcp
        mcp_tools_directory = str(Path(langswarm.tools.mcp.__file__).parent)
```

---

## 🧪 Testing

Verified fixes with:

1. **Tool Registration Test:**
```python
registry1 = ToolRegistry()
registry1.auto_populate_with_mcp_tools()
print(f"Registry 1 tools: {len(registry1._tools)}")  # 13 tools

registry2 = ToolRegistry()
print(f"Registry 2 tools: {len(registry2._tools)}")  # 13 tools (same instance!)
assert registry1 is registry2  # ✅ Same object
```

2. **Agent Creation Test:**
```python
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()

agent = await create_openai_agent(
    name="test",
    model="gpt-4o-mini",
    tools=['bigquery_vector_search']
)
# ✅ No errors - tools found!
```

---

## 📦 Files Changed

- `langswarm/tools/registry.py` - Singleton pattern + package-relative paths
- `pyproject.toml` - Version bump to 0.0.54.dev73

---

## 🚀 Upgrade Path

**Recommended for all V2 users:**

```bash
pip install --upgrade langswarm==0.0.54.dev73
```

**No code changes required** - the singleton fix is transparent to existing code.

---

## 🐛 Known Issues (None)

All critical V2 tool registry issues are resolved in this release.

---

## 👥 Credits

**Reported by:** User experiencing V2 migration issues  
**Root cause identified by:** LangSwarm team analysis  
**Fixed by:** Core team

---

## 📚 Related Documentation

- [V2 Agent Creation Guide](docs/v2/agents.md)
- [Tool Registry Documentation](docs/v2/tools/registry.md)
- [V1 to V2 Migration Guide](docs/migration/v1-to-v2.md)

