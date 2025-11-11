# LangSwarm V1 (with Automatic Fixes)

This directory contains LangSwarm V1 with automatic compatibility patches applied on import.

## What's Fixed

When you import `langswarm.v1`, two critical bugs are automatically fixed:

### 1. LangChain API Compatibility ✅
- **Problem**: `'ChatOpenAI' object has no attribute 'run'`
- **Solution**: Uses modern `.invoke()` API with fallback to legacy `.run()`
- **Works with**: LangChain 0.1.0 through 0.3.x+

### 2. UTF-8 Encoding Corruption ✅
- **Problem**: Swedish characters corrupted: `"sme4rta"` instead of `"smärta"`
- **Solution**: Proper UTF-8 decoding + auto-repair of hex patterns
- **Works with**: All international characters (Swedish, German, French, Spanish, etc.)

## Usage

```python
# Simple! Just change import path from archived.v1 to langswarm.v1
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Patches are applied automatically - no extra setup needed!
loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Now works with modern LangChain and Swedish characters!
result = executor.run_workflow('main_workflow', {'user_input': 'Vad är naprapati?'})
# Output: "Naprapati är en terapi för smärta..." ✅
```

## Migration from Archived V1

### Before (broken):
```python
from archived.v1.core.config import LangSwarmConfigLoader  # ❌ Bugs present
```

### After (fixed):
```python
from langswarm.v1.core.config import LangSwarmConfigLoader  # ✅ Auto-fixed!
```

That's it! Just update the import path.

## What Happens on Import

When you import any `langswarm.v1` module:

1. **Patches check** - Verifies if patches already applied
2. **If not applied** - Automatically patches `AgentWrapper` methods
3. **Logs** - Shows confirmation: "✅ V1 ready - LangChain compatibility + UTF-8 fixes applied"
4. **Done** - Your V1 code works perfectly

## Technical Details

### Patched Methods

1. **`AgentWrapper._call_agent()`**
   - Checks for `.invoke()` method first (modern LangChain)
   - Falls back to `.run()` if available (legacy LangChain)
   - Raises clear error if neither exists

2. **`AgentWrapper._parse_response()`**
   - Properly decodes bytes objects as UTF-8
   - Detects hex corruption patterns (e4, f6, e5, etc.)
   - Auto-repairs corrupted text

### Patch Application

- **Automatic**: Applied on first `langswarm.v1` import
- **Idempotent**: Safe to import multiple times
- **Non-invasive**: Original V1 code unchanged
- **Runtime**: Patches applied in memory, not to files

## Disabling Auto-Patch (Advanced)

If you need to disable automatic patching (not recommended):

```python
# Set before importing
import langswarm.v1._patches
langswarm.v1._patches._PATCHES_APPLIED = True  # Skip auto-patch

from langswarm.v1.core.config import LangSwarmConfigLoader
```

## Upgrading to V2

V2 is the recommended version with modern architecture. To migrate:

```python
# V1 (current)
from langswarm.v1.core.config import LangSwarmConfigLoader

# V2 (recommended)
from langswarm.core.planning import Coordinator, TaskBrief
```

See main README for V2 migration guide.

## Support

- **V1 Status**: Maintained with bug fixes only
- **V2 Status**: Active development, recommended for new projects
- **Issues**: Report at GitHub Issues with `[V1]` prefix

---

**Version**: 0.0.54.dev46  
**Status**: ✅ Production Ready with Automatic Fixes  
**Compatibility**: LangChain 0.1.0+, Python 3.8+

