# Release Notes: LangSwarm v0.0.54.dev56

**Release Date**: November 15, 2025  
**Type**: Critical Bug Fix

---

## Critical Bug Fix: Endless Loop in V1 Tool Execution

### Summary
This release fixes a critical bug in LangSwarm V1 that caused tool calls to loop indefinitely (100+ times) instead of respecting the configured retry limit of 3 attempts.

### Problem Description
Users reported that certain tool calls, particularly `bigquery_vector_search`, would get stuck in endless loops, consuming excessive API credits and causing workflows to hang. The issue was caused by two compounding problems:

1. **Unconditional "Repeatable" Tool Retries**: The repeatable tool logic in `config.py` (lines 3357-3368 sync, 3548-3559 async) would unconditionally retry tool executions regardless of success or failure, as long as the retry counter was below the limit.

2. **Nested JSON Parsing Retries**: When an agent returned malformed JSON (e.g., containing ternary operators like `"${var}" ? "${var}" : "default"`), the `safe_json_loads` method would call `to_json`, which in turn called `agent.chat()` directly, creating nested retry loops that bypassed workflow-level retry tracking.

### Root Cause
The compound effect of these two issues created exponential retry loops:
- Repeatable tool retries: 3×
- JSON parsing retries via `to_json`: 3×
- Multiple JSON sanitization attempts
- **Total**: 3 × 3 × N = 100+ calls

### What Was Fixed

#### 1. Fixed Repeatable Tool Logic (`langswarm/v1/core/config.py`)
**Locations**: Lines 3357-3385 (sync), Lines 3565-3593 (async)

**Changes**:
- Added success condition checks before retrying
- Only retries if result indicates actual failure:
  - Empty or None results
  - String results containing error indicators ("error", "failed", "exception", "traceback")
  - Dict results with error status
- Added informative logging for retry attempts and decisions
- Logs successful completions to prevent confusion

**Example logging output**:
```
✅ Tool 'bigquery_vector_search' succeeded, skipping retry
🔄 Retrying tool 'data_fetch' (attempt 2/3): empty or None result
⚠️ Tool 'api_call' retry limit reached (3)
```

#### 2. Added Retry Depth Limits (`langswarm/v1/core/utils/subutilities/formatting.py`)

##### `safe_json_loads` method (Line 231)
**Changes**:
- Added `_retry_depth` parameter (internal use only, defaults to 0)
- Hard limit of `MAX_RETRY_DEPTH = 2` to prevent infinite loops
- Passes incremented depth to `to_json()` and recursive calls
- Returns None when depth limit reached with clear error message

##### `to_json` method (Line 406)
**Changes**:
- Added `_retry_depth` parameter (internal use only, defaults to 0)
- Checks if `_retry_depth >= 2`, returns `(False, data)` immediately
- Prevents nested agent retries when already in a retry context
- Added comprehensive docstring explaining the depth tracking

**Example logging output**:
```
❌ Maximum JSON parse retry depth (2) reached. Returning None to prevent infinite loop.
❌ to_json() called at retry depth 2. Aborting to prevent infinite loop.
```

### Impact on Users

#### Immediate Benefits
- Tool calls now respect the configured `retry_limit` (default: 3)
- No more runaway API costs from endless loops
- Workflows complete or fail gracefully instead of hanging
- Clear logging shows retry decisions and reasons

#### Behavioral Changes
- **Successful tool calls**: No longer retry unnecessarily, improving performance
- **Failed tool calls**: Retry only on actual failures, with clear logging
- **Malformed JSON responses**: Limited to 2 depth levels of retry attempts before failing gracefully

#### Migration Notes
- **No action required**: This is a transparent bug fix
- **Config compatibility**: All existing workflow configurations work unchanged
- **API compatibility**: No breaking changes to public APIs

### Testing Recommendations
After upgrading to v0.0.54.dev56, test workflows that:
1. Use tools marked as "repeatable" in their configuration
2. Make external API calls that may return malformed JSON
3. Have retry logic configured
4. Previously experienced hanging or excessive retries

### Files Changed
- `langswarm/v1/core/config.py`: Fixed unconditional retry logic (2 locations)
- `langswarm/v1/core/utils/subutilities/formatting.py`: Added depth limits to prevent nested loops (2 methods)
- `pyproject.toml`: Version bump to 0.0.54.dev56

### Acknowledgments
Thanks to the user who reported this critical issue with detailed logs showing 100+ retry attempts, enabling us to identify and fix the compound loop problem.

---

## Upgrade Instructions

### Using Poetry
```bash
poetry update langswarm
```

### Using Pip
```bash
pip install --upgrade langswarm
```

### From Source
```bash
git pull origin main
pip install -e .
```

---

## Support
If you encounter any issues with this release, please:
1. Check the [V1/V2 Import Guide](V1_V2_IMPORT_GUIDE.md) for compatibility information
2. Review the [GitHub Issues](https://github.com/aekdahl/langswarm/issues)
3. Open a new issue with detailed logs if the problem persists

---

**Previous Version**: v0.0.54.dev55  
**Next Version**: TBD

