# LangSwarm V1/V2 Import Compatibility Guide

## Overview

LangSwarm supports both V1 (archived) and V2 (current) versions with a comprehensive compatibility layer that ensures seamless imports regardless of which version is being used.

**Key Principle**: V2 is the primary version. All imports try V2 first, then fall back to V1 if V2 is not available.

---

## Import Paths

### V2 Paths (Primary)

V2 uses the `langswarm.core.*` namespace:

```python
from langswarm.core.agents import BaseAgent
from langswarm.core.workflows import WorkflowBuilder
from langswarm.core.config import LangSwarmConfigLoader  # V2 version
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
from langswarm.core.utils.subutilities.formatting import Formatting
```

### V1 Paths (Legacy)

V1 uses the `langswarm.v1.core.*` namespace:

```python
from langswarm.v1.core.config import LangSwarmConfigLoader  # V1 version
from langswarm.v1.core.wrappers.generic import AgentWrapper
from langswarm.v1.core.utils.workflows.intelligence import WorkflowIntelligence
from langswarm.v1.core.utils.subutilities.formatting import Formatting
```

---

## Compatibility Shims

The following compatibility shims exist at `langswarm.core.*` to route imports:

### 1. Workflow Intelligence

**Location**: `langswarm/core/utils/workflows/intelligence.py`

```python
# This import works for both V1 and V2 users:
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence

# Internally routes to:
# - langswarm.core.v2.utils.workflows.intelligence (if V2 available)
# - langswarm.v1.core.utils.workflows.intelligence (if only V1 available)
```

### 2. Formatting Utilities

**Location**: `langswarm/core/utils/subutilities/formatting.py`

```python
# This import works for both V1 and V2 users:
from langswarm.core.utils.subutilities.formatting import Formatting

# Internally routes to:
# - langswarm.core.v2.utils.subutilities.formatting (if V2 available)
# - langswarm.v1.core.utils.subutilities.formatting (if only V1 available)
```

### 3. Core Utils

**Location**: `langswarm/core/utils/__init__.py`

```python
# This import works for both V1 and V2 users:
from langswarm.core.utils import *

# Internally routes to:
# - langswarm.core.v2.utils (if V2 available)
# - langswarm.v1.core.utils (if only V1 available)
```

---

## Tools and Shared Components

Tools in `langswarm/tools/` use V2-first imports with V1 fallbacks:

```python
# Pattern used in all tools:
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader
```

This ensures tools work with both V1 and V2.

---

## Best Practices

### For V2 Users (Recommended)

Use V2 imports directly:

```python
from langswarm.core.agents import BaseAgent
from langswarm.core.workflows import execute_workflow
from langswarm.core.config import LangSwarmConfigLoader
```

### For V1 Users (Legacy Support)

Use V1 imports directly for guaranteed compatibility:

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
from langswarm.v1.core.wrappers.generic import AgentWrapper
```

### For Library Developers

Use compatibility imports when you need to support both V1 and V2:

```python
# Option 1: Use compatibility shims (for utils only)
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
from langswarm.core.utils.subutilities.formatting import Formatting

# Option 2: Use try/except for other imports
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'langswarm.core.utils.workflows'`

**Cause**: V1 code trying to import from V2 path without compatibility shim.

**Solution**: Use the compatibility shim at `langswarm/core/utils/workflows/intelligence.py`:

```python
# Instead of importing from a non-existent V2 path:
from langswarm.core.v2.utils.workflows import WorkflowIntelligence  # ❌

# Use the compatibility shim:
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence  # ✅
```

### Error: `ModuleNotFoundError: No module named 'langswarm.core.config'`

**Cause**: V1-only environment trying to use V2 imports.

**Solution**: Use V1 imports explicitly:

```python
# Instead of:
from langswarm.core.config import LangSwarmConfigLoader  # ❌ (V2 only)

# Use:
from langswarm.v1.core.config import LangSwarmConfigLoader  # ✅ (V1)
```

### Error: Import works locally but fails in production

**Cause**: Production may have only V1 or only V2 installed.

**Solution**: Use compatibility patterns with try/except:

```python
try:
    from langswarm.core.config import LangSwarmConfigLoader  # Try V2
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader  # Fall back to V1
```

---

## Compatibility Layer Architecture

```
User Code
    ↓
langswarm.core.utils.workflows.intelligence
    ↓
    ├── Try V2: langswarm.core.v2.utils.workflows.intelligence ✅ (if available)
    └── Fall back to V1: langswarm.v1.core.utils.workflows.intelligence ✅ (if V2 not available)
```

---

## Checking Your Environment

### Determine if V2 is Available

```python
try:
    from langswarm.core.agents import BaseAgent
    print("✅ V2 is available")
except ImportError:
    print("❌ V2 is not available - using V1")
```

### Determine if V1 is Available

```python
try:
    from langswarm.v1.core.config import LangSwarmConfigLoader
    print("✅ V1 is available")
except ImportError:
    print("❌ V1 is not available")
```

---

## Migration Path

### From V1 to V2

1. **Update imports** from `langswarm.v1.*` to `langswarm.core.*`
2. **Update agent creation** from `AgentWrapper` to `BaseAgent`
3. **Update workflow execution** from `WorkflowExecutor` to `execute_workflow()`
4. **Test thoroughly** - V2 has different APIs

### From V2 to V1 (Rare)

1. **Update imports** from `langswarm.core.*` to `langswarm.v1.core.*`
2. **Update agent creation** from `BaseAgent` to `AgentWrapper`
3. **Add compatibility patches** for Swedish character encoding (if needed)

---

## Examples

### V2 Example (Modern)

```python
from langswarm.core.workflows import execute_workflow

async def main():
    result = await execute_workflow(
        workflow_id="main_workflow",
        input_data={"user_input": "Hello"}
    )
    print(result)
```

### V1 Example (Legacy)

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents, tools, metadata)

result = executor.run_workflow("main_workflow", user_input="Hello")
print(result)
```

### Compatible Tool Example

```python
# This works with both V1 and V2:
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader

def execute_with_langswarm(workflow_name, user_input):
    loader = LangSwarmConfigLoader('config.yaml')
    # ... rest of code works with both versions
```

---

## Summary

- **V2 is primary**: Always try V2 imports first
- **V1 is supported**: Comprehensive fallbacks ensure V1 continues to work
- **Compatibility shims**: Located at `langswarm/core/utils/*` for seamless routing
- **Tools are compatible**: All tools in `langswarm/tools/` work with both V1 and V2
- **No code changes needed**: Existing V1 and V2 code continues to work

---

## Version Information

- **LangSwarm Version**: 0.0.54.dev55
- **V1 Status**: Archived, fully supported via compatibility layer
- **V2 Status**: Current, primary version
- **Compatibility Layer**: Introduced in dev55

---

## Related Documentation

- `V1_ENCODING_AND_IMPORTS_FIX_SUMMARY.md` - Swedish character encoding fixes
- `langswarm/v1/README.md` - V1 usage guide
- `langswarm/tools/README.md` - Tool development guide

---

For issues or questions, please open an issue on GitHub: https://github.com/aekdahl/langswarm

