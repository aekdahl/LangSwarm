# V1 Tool Response UTF-8 Encoding Fix

## Version
Should be included in v0.0.54.dev50 or v0.0.54.dev51

## Issue
Swedish characters (and all international text) corrupted when LLM uses tools:
- "anve4nde" instead of "använde"
- "ff6r" instead of "för"
- "sf6ka" instead of "söka"

## Fix Applied
Added UTF-8 decoding and hex pattern correction to `langswarm/v1/core/wrappers/middleware.py`:

1. **Three static helper methods** (lines 40-83):
   - `_fix_utf8_encoding(text)` - Main fix method
   - `_has_hex_corruption(text)` - Detects corruption patterns
   - `_fix_hex_patterns(text)` - Fixes hex codes (e4→ä, f6→ö, etc.)

2. **Individual tool response fix** (line 567):
   - Applied after tool execution in `_route_action()`

3. **Concatenated response fix** (line 474):
   - Applied before concatenation in `to_middleware()`

## Testing
```python
from langswarm.v1.core.wrappers.middleware import MiddlewareMixin

# Test case
corrupted = "Jag anve4nde ett verktyg ff6r att sf6ka"
fixed = MiddlewareMixin._fix_utf8_encoding(corrupted)

# Expected: "Jag använde ett verktyg för att söka"
```

## Impact
- **Scope**: V1 only (V2 doesn't have MiddlewareMixin)
- **Breaking Changes**: None
- **Performance**: Negligible
- **Coverage**: All tool responses (MCP, legacy, plugins, RAGs)

## Files Modified
- `langswarm/v1/core/wrappers/middleware.py` (~50 lines added)

## Related
Complements existing `_parse_response` UTF-8 fix for complete coverage of all V1 response paths.

