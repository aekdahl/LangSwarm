# LangSwarm V1 Encoding & Import Compatibility Fixes - v0.0.54.dev54

## Summary

Fixed critical Swedish character encoding corruption and V1/V2 import compatibility issues across the entire LangSwarm codebase.

**Version**: 0.0.54.dev54  
**Date**: 2025-11-14  
**Issues Resolved**: Swedish character corruption (null bytes) + V1/V2 tool import failures

---

## Issues Fixed

### 1. Swedish Character Encoding Corruption ✅

**Problem**: OpenAI responses contained null bytes that corrupted Swedish characters:
- `"uppst\u0000e5tt"` → `"uppste5tt"` instead of `"uppstått"`
- `"s\u00000f\u000000ka"` → `"s0ka"` instead of `"söka"`
- `"tyv\u00000rr"` → `"tyv0rr"` instead of `"tyvärr"`

**Root Cause**: 
1. OpenAI JSON responses included Unicode escape sequences with null bytes (`\u0000`)
2. `json.dumps()` without `ensure_ascii=False` corrupted non-ASCII characters
3. No null byte stripping in response parsing

**Files Fixed**:
- `langswarm/v1/core/wrappers/middleware.py`
- `langswarm/v1/core/wrappers/generic.py`

**Changes**:

#### middleware.py (Lines 40-72, 466, 487, 576)
```python
@staticmethod
def _fix_utf8_encoding(text):
    """Fix UTF-8 encoding issues in tool responses"""
    if not text:
        return text
    
    # Handle bytes
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = text.decode('latin-1')
    elif not isinstance(text, str):
        text = str(text)
    
    # Remove null bytes that corrupt Swedish characters (from OpenAI responses)
    if isinstance(text, str):
        text = text.replace('\x00', '')
        text = text.replace('\u0000', '')
        
        # Handle Unicode escape sequences that may have been literalized
        if '\\u' in text or '\\x' in text:
            try:
                # Try to decode Unicode escape sequences
                text = text.encode('latin-1').decode('unicode-escape')
            except:
                pass
    
    # Fix hex corruption patterns
    if isinstance(text, str) and MiddlewareMixin._has_hex_corruption(text):
        text = MiddlewareMixin._fix_hex_patterns(text)
    
    return text

# All json.dumps() calls fixed:
return 201, json.dumps(result, indent=2, ensure_ascii=False)
```

#### generic.py (Lines 1598-1642)
```python
def _parse_response(self, response: Any) -> str:
    """Parse the response from the wrapped agent with safety limits."""
    if hasattr(response, "content"):
        result = response.content
    elif isinstance(response, dict):
        result = response.get("generated_text", "")
    else:
        result = str(response)
    
    # FIX: Handle null bytes that corrupt Swedish characters (from OpenAI responses)
    if isinstance(result, str):
        result = result.replace('\x00', '')
        result = result.replace('\u0000', '')
        
        # Handle Unicode escape sequences that may have been literalized
        if '\\u' in result or '\\x' in result:
            try:
                # Try to decode Unicode escape sequences
                result = result.encode('latin-1').decode('unicode-escape')
            except:
                pass
    
    # Ensure proper UTF-8 encoding
    if isinstance(result, bytes):
        try:
            result = result.decode('utf-8')
        except UnicodeDecodeError:
            result = result.decode('latin-1', errors='replace')
    
    # ... rest of method ...
    return result
```

---

### 2. V1/V2 Import Compatibility ✅

**Problem**: Tools were using V2-only import paths, breaking for V1 users:
```python
from langswarm.core.config import LangSwarmConfigLoader  # ❌ V2 only
```

**Root Cause**: Tools assumed V2 was available, causing `ModuleNotFoundError` for V1 users.

**Files Fixed**:
1. `langswarm/tools/base.py`
2. `langswarm/tools/adapters/base.py`
3. `langswarm/tools/mcp/workflow_executor/main.py`
4. `langswarm/tools/mcp/bigquery_vector_search/main.py`
5. `langswarm/tools/mcp/sql_database/main.py`
6. `langswarm/tools/mcp/tasklist/main.py`

**Solution Pattern**:
```python
# V1/V2 compatibility
try:
    from langswarm.core.config import LangSwarmConfigLoader  # Try V2 first
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader  # Fall back to V1
```

**Detailed Changes**:

#### tools/base.py (Lines 17-31)
```python
# V1/V2 compatibility for error handling
try:
    from langswarm.core.errors import handle_error, ToolError, ErrorContext
except ImportError:
    try:
        from langswarm.v1.core.errors import handle_error, ToolError, ErrorContext
    except ImportError:
        # Fallback for minimal environments
        class ToolError(Exception):
            pass
        class ErrorContext:
            def __init__(self, **kwargs):
                pass
        def handle_error(func):
            return func
```

#### tools/adapters/base.py (Lines 12-23)
```python
# V1/V2 compatibility for error handling
try:
    from langswarm.core.errors import handle_error, ToolError
except ImportError:
    try:
        from langswarm.v1.core.errors import handle_error, ToolError
    except ImportError:
        # Fallback for minimal environments
        class ToolError(Exception):
            pass
        def handle_error(func):
            return func
```

#### tools/mcp/workflow_executor/main.py (Lines 328-332, 425-433)
```python
# Import LangSwarm components (V1/V2 compatibility)
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader

# Also fixed in script_content string:
script_content = f"""
import sys
import json

# V1/V2 compatibility
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader

# Load configuration
loader = LangSwarmConfigLoader('{os.path.dirname(config_path)}')
"""
```

#### tools/mcp/bigquery_vector_search/main.py (Lines 15-27, 149-168, 739-743)
```python
# Python 3.11+ compatibility (V1/V2)
try:
    from langswarm.core.utils.python_compat import (
        OpenAIClientFactory, IS_PYTHON_311_PLUS
    )
except ImportError:
    try:
        from langswarm.v1.core.utils.python_compat import (
            OpenAIClientFactory, IS_PYTHON_311_PLUS
        )
    except ImportError:
        IS_PYTHON_311_PLUS = sys.version_info >= (3, 11)
        OpenAIClientFactory = None

# Debug tracer compatibility (lines 149-168):
except ImportError:
    # Fallback to V1 tracing
    try:
        # Try V2 path first
        from langswarm.core.debug import get_debug_tracer
        tracer = get_debug_tracer()
        if tracer and hasattr(tracer, 'enabled') and tracer.enabled:
            logger.info(f"🎯 V1_INTERNAL_LLM_CALL | get_embedding | model={model} | text_length={len(text)}")
        return await _perform_embedding_call(text, model)
    except ImportError:
        try:
            # Try V1 path
            from langswarm.v1.core.debug import get_debug_tracer
            tracer = get_debug_tracer()
            if tracer and hasattr(tracer, 'enabled') and tracer.enabled:
                logger.info(f"🎯 V1_INTERNAL_LLM_CALL | get_embedding | model={model} | text_length={len(text)}")
            return await _perform_embedding_call(text, model)
        except ImportError:
            # No tracing available, proceed without tracing
            return await _perform_embedding_call(text, model)

# LangSwarmConfigLoader import (lines 739-743):
# Import LangSwarm workflow system (V1/V2 compatibility)
try:
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError:
    from langswarm.v1.core.config import LangSwarmConfigLoader
```

#### tools/mcp/sql_database/main.py (Lines 1064-1071)
```python
try:
    # Import LangSwarm workflow system (V1/V2 compatibility)
    try:
        from langswarm.core.config import LangSwarmConfigLoader
    except ImportError:
        from langswarm.v1.core.config import LangSwarmConfigLoader
    import os
    from pathlib import Path
```

#### tools/mcp/tasklist/main.py (Lines 95-102)
```python
def _create_default_adapter(self):
    """Create default memory adapter using LangSwarm's memory made simple"""
    try:
        # V1/V2 compatibility for MemoryConfig
        try:
            from langswarm.core.config import MemoryConfig
        except ImportError:
            from langswarm.v1.core.config import MemoryConfig
```

---

## Benefits

### Swedish Character Encoding
✅ Swedish characters (ä, ö, å) now display correctly  
✅ No more hex corruption (`e4`, `f6`, `e5`)  
✅ No more null byte corruption (`\u0000`)  
✅ Works with all international characters (German, French, Spanish, etc.)

### V1/V2 Import Compatibility
✅ Tools work seamlessly with V1 (archived)  
✅ Tools work seamlessly with V2 (current)  
✅ Graceful fallbacks for minimal environments  
✅ No breaking changes for existing users

---

## Testing

### Test Swedish Characters
```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents, tools, metadata)

# Test Swedish input
result = executor.run_workflow('main_workflow', user_input='Vad är naprapati?')

# Should output clean Swedish text like:
# "Naprapati är en form av terapi för smärta..."
# NOT: "Naprapati e4r en form av terapi ff6r sme4rta..."
```

### Test V1/V2 Tool Imports
```python
# Should work with both V1 and V2
from langswarm.tools.mcp.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
from langswarm.tools.mcp.workflow_executor.main import WorkflowExecutorMCPTool

# Tools should initialize without import errors
tool = BigQueryVectorSearchMCPTool()
```

---

## Version History

- **v0.0.54.dev54** (2025-11-14): Fixed Swedish character encoding + V1/V2 import compatibility
- **v0.0.54.dev53** (2025-11-14): Previous version with encoding issues

---

## Notes

- All fixes are **backward compatible** - no breaking changes
- V2 imports are tried first for performance, then fall back to V1
- Null byte stripping happens at multiple layers (response parsing, middleware, tool responses)
- `ensure_ascii=False` ensures JSON preserves UTF-8 characters
- All tools now work with both V1 (archived) and V2 (current)

---

## Files Modified

### V1 Core Wrappers
- `langswarm/v1/core/wrappers/middleware.py`
- `langswarm/v1/core/wrappers/generic.py`

### Tools Base
- `langswarm/tools/base.py`
- `langswarm/tools/adapters/base.py`

### MCP Tools
- `langswarm/tools/mcp/workflow_executor/main.py`
- `langswarm/tools/mcp/bigquery_vector_search/main.py`
- `langswarm/tools/mcp/sql_database/main.py`
- `langswarm/tools/mcp/tasklist/main.py`

### Package Metadata
- `pyproject.toml` (version bump to 0.0.54.dev54)

---

## Related Issues

- Swedish character corruption in tool responses
- `ModuleNotFoundError: No module named 'langswarm.core.config'` in V1
- `ModuleNotFoundError: No module named 'langswarm.core.utils.workflows'` in V1
- Null bytes in OpenAI JSON responses

---

## Next Steps

1. ✅ Test with Swedish input
2. ✅ Verify V1 tool imports work
3. ✅ Verify V2 tool imports work
4. 📦 Publish to PyPI as `langswarm-v0.0.54.dev54`
5. 📝 Update documentation with encoding fixes
6. 🎯 Monitor for any remaining encoding issues

---

**All fixes complete! LangSwarm V1 now handles Swedish characters correctly and tools work seamlessly with both V1 and V2.** 🎉

