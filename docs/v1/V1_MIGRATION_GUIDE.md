# LangSwarm V1 Migration Guide

## v0.0.54.dev46: V1 with Automatic Fixes

As of v0.0.54.dev46, LangSwarm V1 is available at `langswarm.v1` with automatic bug fixes.

## What Changed

### V1 Location Moved
- **Old**: `archived/v1/` (broken with modern LangChain)
- **New**: `langswarm/v1/` (auto-fixed on import)

### Two Critical Bugs Fixed
1. ✅ **LangChain API**: Works with LangChain 0.3.x+ (no more `.run()` errors)
2. ✅ **UTF-8 Encoding**: Swedish characters work correctly (no more hex corruption)

## Migration Steps

### 1. Update Your Imports

Simply change `archived.v1` to `langswarm.v1`:

```python
# OLD (v0.0.54.dev44 and earlier)
from archived.v1.core.config import LangSwarmConfigLoader

# NEW (v0.0.54.dev46+)
from langswarm.v1.core.config import LangSwarmConfigLoader
```

### 2. That's It!

No other changes needed. Your V1 code now:
- ✅ Works with modern LangChain (0.3.x+)
- ✅ Handles Swedish characters correctly
- ✅ Supports all international UTF-8 text

## Example Migration

### Before (Broken)

```python
# config.py
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
from archived.v1.core.registry.agents import AgentRegistry

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# ❌ Error: 'ChatOpenAI' object has no attribute 'run'
# ❌ Swedish text corrupted: "sme4rta" instead of "smärta"
result = executor.run_workflow('main_workflow', {'user_input': 'Vad är naprapati?'})
```

### After (Fixed)

```python
# config.py
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
from langswarm.v1.core.registry.agents import AgentRegistry

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# ✅ Works perfectly
# ✅ Swedish text correct: "smärta"
result = executor.run_workflow('main_workflow', {'user_input': 'Vad är naprapati?'})
print(result)  # "Naprapati är en terapi för smärta..."
```

## Search & Replace Guide

Use these regex patterns to update your imports:

### Pattern 1: Direct imports
```
Find:    from archived\.v1\.
Replace: from langswarm.v1.
```

### Pattern 2: Import blocks
```
Find:    import archived\.v1\.
Replace: import langswarm.v1.
```

### Examples

```python
# OLD → NEW
from archived.v1.core.config import *
from langswarm.v1.core.config import *

from archived.v1.core.wrappers.generic import AgentWrapper
from langswarm.v1.core.wrappers.generic import AgentWrapper

from archived.v1.core.registry.agents import AgentRegistry
from langswarm.v1.core.registry.agents import AgentRegistry

import archived.v1.core.utils as utils
import langswarm.v1.core.utils as utils
```

## What Happens on First Import

When you first import any `langswarm.v1` module:

1. **Auto-patch runs** (takes <1ms)
2. **Logs confirmation**: "✅ V1 ready - LangChain compatibility + UTF-8 fixes applied"
3. **Your code continues** with fixes applied

## Compatibility

### Supported
- ✅ LangChain 0.1.0 through 0.3.x+
- ✅ Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ All V1 features and APIs
- ✅ All international characters (UTF-8)

### Not Changed
- ✅ V1 API is identical
- ✅ Configuration files unchanged
- ✅ Workflow definitions unchanged
- ✅ Tool integrations unchanged

## Testing Your Migration

### Quick Test

```python
# test_v1_migration.py
from langswarm.v1.core.config import LangSwarmConfigLoader

print("✅ V1 import successful")

# Test with your config
loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()

print(f"✅ Loaded {len(workflows)} workflows")
print(f"✅ Loaded {len(agents)} agents")
print("✅ V1 migration complete!")
```

### Test Swedish Characters

```python
# test_utf8.py
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Test Swedish input
result = executor.run_workflow('test', {'input': 'Vad är smärta?'})

# Check for corruption
if 'e4' in result or 'f6' in result:
    print("❌ UTF-8 corruption detected")
else:
    print("✅ UTF-8 encoding works correctly")
```

## FAQ

### Q: Do I need to uninstall anything?
**A**: No! Just update your imports from `archived.v1` to `langswarm.v1`.

### Q: Will my old code break?
**A**: No. The API is identical, only the import path changes.

### Q: Can I use both V1 and V2?
**A**: Yes! V1 is at `langswarm.v1.*`, V2 is at `langswarm.core.*`

### Q: Do I need to install anything extra?
**A**: No. Just upgrade to `langswarm>=0.0.54.dev46`

### Q: What if I can't update yet?
**A**: Use the standalone `langswarm-v1-compat` package (see separate docs)

### Q: Should I migrate to V2?
**A**: V2 is recommended for new projects. V1 remains supported with bug fixes.

## V2 Migration (Optional)

If you want to migrate to V2 (recommended for new features):

### V1 (current)
```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)
result = executor.run_workflow('main', {'input': '...'})
```

### V2 (new)
```python
from langswarm.core.planning import Coordinator, TaskBrief

brief = TaskBrief(
    objective="Your task",
    inputs={"data": "..."},
    constraints={"cost_usd": 5.0}
)

coordinator = Coordinator()
result = await coordinator.execute_task(brief)
```

See main README for full V2 guide.

## Troubleshooting

### "ModuleNotFoundError: No module named 'langswarm.v1'"

Upgrade LangSwarm:
```bash
pip install --upgrade langswarm>=0.0.54.dev46
```

### "Still getting .run() errors"

Clear Python cache:
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### "Swedish characters still corrupted"

Check you're using the new import:
```python
# ❌ OLD - still broken
from archived.v1.core.config import *

# ✅ NEW - fixed
from langswarm.v1.core.config import *
```

## Support

- **GitHub Issues**: Tag with `[V1]` prefix
- **Documentation**: See `/langswarm/v1/README.md`
- **V2 Docs**: See main README.md

---

**Version**: 0.0.54.dev46  
**Status**: ✅ Ready for Production  
**Migration Time**: ~5 minutes (search & replace imports)

