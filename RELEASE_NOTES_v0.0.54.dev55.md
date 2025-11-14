# Release Notes - LangSwarm v0.0.54.dev55

## V1/V2 Import Compatibility Layer

**Release Date**: 2025-11-14  
**Version**: 0.0.54.dev55

---

## Overview

This release introduces a comprehensive V1/V2 import compatibility layer that eliminates import errors when using V1 workflows with shared tools and utilities.

---

## Key Features

### 1. Compatibility Shims ✅

Created intelligent routing modules at `langswarm/core/utils/*` that automatically route imports to V2 (primary) or V1 (fallback):

- `langswarm/core/utils/__init__.py` - General utils routing
- `langswarm/core/utils/workflows/__init__.py` - Workflow utils routing
- `langswarm/core/utils/workflows/intelligence.py` - WorkflowIntelligence routing
- `langswarm/core/utils/subutilities/__init__.py` - Sub-utilities routing
- `langswarm/core/utils/subutilities/formatting.py` - Formatting utilities routing

### 2. Seamless Import Pattern

Users can now use a single import path that works with both V1 and V2:

```python
# This now works regardless of whether you're using V1 or V2:
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
from langswarm.core.utils.subutilities.formatting import Formatting
```

The compatibility layer automatically:
1. Tries V2 first (if available)
2. Falls back to V1 (if V2 not available)
3. Provides graceful handling for minimal environments

### 3. V2 Remains Primary

The system maintains V2 as the primary version:
- All imports try V2 first
- V1 is only used as a fallback
- No performance impact for V2 users
- Full backward compatibility for V1 users

---

## Fixed Issues

### Import Error: `No module named 'langswarm.core.utils.workflows'`

**Status**: ✅ Fixed

**Before**:
```python
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
# ❌ ModuleNotFoundError in V1 environment
```

**After**:
```python
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
# ✅ Works in both V1 and V2 environments
```

### V1 Workflows with Shared Tools

**Status**: ✅ Fixed

V1 workflows can now use shared tools from `langswarm/tools/` without import errors. Tools that use V2-style imports now gracefully fall back to V1 when needed.

---

## New Files

### Compatibility Shims (5 files)
- `langswarm/core/utils/__init__.py`
- `langswarm/core/utils/workflows/__init__.py`
- `langswarm/core/utils/workflows/intelligence.py`
- `langswarm/core/utils/subutilities/__init__.py`
- `langswarm/core/utils/subutilities/formatting.py`

### Documentation (1 file)
- `V1_V2_IMPORT_GUIDE.md` - Comprehensive import compatibility guide

### Tests (1 file)
- `tests/test_v1_v2_import_compatibility.py` - Automated compatibility tests

---

## Deleted Files

- `langswarm/v1/core/config.py.backup` - Removed old backup with broken imports

---

## Benefits

### For V1 Users
- ✅ No more import errors when using workflows
- ✅ Seamless access to shared tools
- ✅ Compatibility shims handle routing automatically
- ✅ No code changes needed

### For V2 Users
- ✅ No impact on V2 functionality
- ✅ V2 remains primary (tried first)
- ✅ No performance overhead
- ✅ Full V2 API available

### For Developers
- ✅ Clear import patterns documented
- ✅ Automated tests verify compatibility
- ✅ Easy to add new compatibility shims
- ✅ Gradual migration path from V1 to V2

---

## Testing

### Automated Tests

Run compatibility tests:
```bash
pytest tests/test_v1_v2_import_compatibility.py -v
```

### Manual Testing

Test V1 imports:
```python
from langswarm.v1.core.config import LangSwarmConfigLoader
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
# Should work without errors
```

Test V2 imports (if V2 available):
```python
from langswarm.core.agents import BaseAgent
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
# Should work without errors
```

---

## Migration Guide

### No Changes Needed

Existing code continues to work:
- V1 code using V1 imports: ✅ Works
- V2 code using V2 imports: ✅ Works
- Mixed code using compatibility imports: ✅ Works

### Optional: Use Compatibility Imports

If you want to write code that works with both V1 and V2, use the compatibility imports:

```python
# Instead of choosing V1 or V2:
from langswarm.v1.core.utils.workflows.intelligence import WorkflowIntelligence  # V1 only
from langswarm.core.v2.utils.workflows.intelligence import WorkflowIntelligence  # V2 only

# Use compatibility import:
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence  # Works with both
```

---

## Documentation

### New Documentation
- `V1_V2_IMPORT_GUIDE.md` - Comprehensive guide to import patterns
  - Import path reference
  - Compatibility shim locations
  - Best practices
  - Troubleshooting guide
  - Real-world examples

### Updated Documentation
- `README.md` - Added V1/V2 compatibility note
- `pyproject.toml` - Version bump to 0.0.54.dev55

---

## Breaking Changes

**None** - This release is fully backward compatible.

---

## Known Issues

None at this time.

---

## Upgrade Instructions

1. Update to version 0.0.54.dev55:
   ```bash
   pip install --upgrade langswarm==0.0.54.dev55
   ```

2. No code changes required - compatibility is automatic

3. (Optional) Update imports to use compatibility layer:
   ```python
   from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
   ```

---

## Technical Details

### Compatibility Layer Architecture

```
User Import Request
    ↓
langswarm.core.utils.workflows.intelligence
    ↓
    ├── Try: langswarm.core.v2.utils.workflows.intelligence (V2)
    │   └── Success: Use V2 implementation ✅
    └── Except ImportError:
        └── Try: langswarm.v1.core.utils.workflows.intelligence (V1)
            └── Success: Use V1 implementation ✅
```

### Import Priority

1. **V2 (Primary)**: Always tried first
2. **V1 (Fallback)**: Used if V2 not available
3. **Graceful Degradation**: Handle missing dependencies

---

## Related Changes

This release builds on previous fixes:
- v0.0.54.dev54 - Swedish character encoding + Tool import compatibility
- v0.0.54.dev53 - Initial V1 integration

---

## Contributors

- Alexander Ekdahl (@aekdahl)

---

## Next Steps

- Monitor for any remaining import issues
- Add more compatibility shims as needed
- Continue V2 development
- Maintain V1 support via compatibility layer

---

For detailed import documentation, see `V1_V2_IMPORT_GUIDE.md`

For issues or questions, please open an issue on GitHub: https://github.com/aekdahl/langswarm

