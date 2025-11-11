# V1 Import Note

## Current Status

LangSwarm V1 has been moved to `langswarm.v1` but still has some legacy absolute imports that assume the old structure.

## Known Issue

V1 code contains imports like:
- `from langswarm.memory.adapters...` 
- `from langswarm.core.session...`

These were correct in the old structure but now point to wrong locations since V1 is at `langswarm.v1`.

## Workaround

For now, the recommended approach is to:

1. **Keep V1 in archived/** if you're actively using it
2. **Use the standalone monkey patch** (`langswarm_v1_monkey_patch.py`) to fix the bugs
3. **Migrate to V2** for new projects

## Future Fix

To properly integrate V1 into the main package, we need to:
- Fix all absolute imports in V1 to be relative
- Or create compatibility shims
- Or refactor V1 to remove dependencies on old structure

This is a non-trivial refactoring task beyond the scope of the current bug fixes.

## Recommendation

**For v0.0.54.dev46, let's publish with just V2 + standalone monkey patch.**

V1 users can:
```bash
pip install langswarm==0.0.54.dev46
pip install langswarm-v1-compat  # Separate package for V1 fixes
```

Or for now, keep using `archived/v1` with the monkey patch applied manually.

