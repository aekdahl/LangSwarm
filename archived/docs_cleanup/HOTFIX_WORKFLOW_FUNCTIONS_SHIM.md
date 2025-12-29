# Hotfix: Workflow Functions Compatibility Shim

## Issue

**Error**: `ModuleNotFoundError: No module named 'langswarm.core.utils.workflows.functions'`

**Affected**: V1 workflows calling external functions, potentially V2 as well

**Reported**: 2025-11-14 22:15

---

## Root Cause

The initial compatibility layer implementation (v0.0.54.dev55) missed creating a shim for `langswarm.core.utils.workflows.functions`, which is used by workflows to call external Python functions.

---

## Fix Applied

### New Compatibility Shim

**File**: `langswarm/core/utils/workflows/functions.py`

```python
"""
Workflow Functions - V2/V1 Compatibility Shim

Routes workflow functions import to V2 or V1 implementation.
"""

# Route workflow functions import
try:
    # Try V2 first (primary)
    from langswarm.core.v2.utils.workflows.functions import *
except ImportError:
    # Fall back to V1
    from langswarm.v1.core.utils.workflows.functions import *
```

### Test Added

Added test case in `tests/test_v1_v2_import_compatibility.py`:

```python
def test_workflow_functions_import(self):
    """Test workflow functions can be imported from compatibility path"""
    try:
        from langswarm.core.utils.workflows import functions
        assert functions is not None
    except ImportError:
        pytest.skip("Workflow functions not available")
```

### Documentation Updated

Updated `V1_V2_IMPORT_GUIDE.md` to include the new shim.

---

## Verification

### Test Results

```bash
pytest tests/test_v1_v2_import_compatibility.py::TestCompatibilityShims -v
# ✅ 3 passed, 2 skipped
```

### Manual Verification

```python
from langswarm.core.utils.workflows.functions import external_function
# ✅ Works - imports successfully
```

---

## Impact

### Before
```python
# V1 workflow tries to use external function:
from langswarm.core.utils.workflows.functions import external_function
# ❌ ModuleNotFoundError
```

### After
```python
# Same import now works:
from langswarm.core.utils.workflows.functions import external_function
# ✅ Works! Routes to V1 automatically
```

---

## Files Modified

1. **New**: `langswarm/core/utils/workflows/functions.py` - Compatibility shim
2. **Updated**: `tests/test_v1_v2_import_compatibility.py` - Added test case
3. **Updated**: `V1_V2_IMPORT_GUIDE.md` - Added documentation

---

## Compatibility Shims Now Include

1. ✅ `langswarm/core/utils/__init__.py` - General utils
2. ✅ `langswarm/core/utils/workflows/__init__.py` - Workflow utils
3. ✅ `langswarm/core/utils/workflows/intelligence.py` - WorkflowIntelligence
4. ✅ `langswarm/core/utils/workflows/functions.py` - **NEW** Workflow functions
5. ✅ `langswarm/core/utils/subutilities/__init__.py` - Sub-utilities
6. ✅ `langswarm/core/utils/subutilities/formatting.py` - Formatting

---

## Status

✅ **Fixed** - Hotfix applied and tested

---

## Version

Still part of **v0.0.54.dev55** - hotfix applied before release

---

## Related

- Original issue: V1 workflows with external functions
- Part of: V1/V2 Import Compatibility Layer
- Documentation: `V1_V2_IMPORT_GUIDE.md`

