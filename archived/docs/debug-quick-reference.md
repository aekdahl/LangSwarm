# LangSwarm Debug Tracing - Quick Reference

## 🚀 TL;DR

```python
# Emergency production debugging (34% performance hit)
from langswarm.core.debug import enable_debug_tracing
enable_debug_tracing("emergency.jsonl")

# Your LangSwarm code - now traced
agent.chat("debug this issue")  # ← Automatically logged

# Disable when done
from langswarm.core.debug import disable_debug_tracing
disable_debug_tracing()
```

## ✅ Default State: DISABLED

**Debug tracing is OFF by default** - your production apps are safe!

- ✅ **Zero performance impact** when disabled
- ✅ **No file I/O** when disabled  
- ✅ **Safe to deploy** with debug code

## 📊 Performance Impact

| State | Overhead | Use Case |
|-------|----------|----------|
| **Disabled (default)** | `0.000023ms` per call | ✅ **Production safe** |
| **Enabled** | `34%` performance hit | ⚠️ **Emergency only** |

## 🔧 Quick Commands

```bash
# Run ready-made debug cases
python -m langswarm.core.debug.cli run-case-1    # Simple agent
python -m langswarm.core.debug.cli run-case-3    # BigQuery tool

# Setup configuration  
python -m langswarm.core.debug.cli init-config   # Create config
python -m langswarm.core.debug.cli show-config   # Check status

# Analyze traces
python -m langswarm.core.debug.cli detail my_trace.jsonl
```

## 🏭 Production Pattern

```python
import os
from langswarm.core.debug import enable_debug_tracing

# Safe for production deployment
if os.getenv('DEBUG_MODE') == 'true':
    enable_debug_tracing("app_debug.jsonl")
    
# Your app runs normally:
# - debug=false: virtually no overhead  
# - debug=true: comprehensive tracing
```

## 📋 Environment Variables

```bash
# Enable emergency debugging
export LANGSWARM_DEBUG=true
export OPENAI_API_KEY=your-key

# BigQuery debugging (optional)
export GOOGLE_CLOUD_PROJECT=your-project
gcloud auth application-default login
```

## 🔍 What Gets Traced

When debug is **enabled**, every operation is logged:

- **🤖 Agent calls**: `agent.chat()` with timing and responses
- **🛠️ Tool calls**: MCP tool execution and parameters  
- **⚙️ Config loading**: Component initialization and setup
- **📋 Workflows**: Step-by-step execution flow

## 📁 Trace Output Example

```json
{
  "trace_id": "abc123",
  "component": "agent", 
  "operation": "chat",
  "message": "Agent responded to user query",
  "data": {
    "query": "Hello world",
    "response": "Hi there!",
    "execution_time_ms": 1250
  },
  "source_file": "agent.py",
  "source_line": 123
}
```

## 🚨 Emergency Debugging Steps

1. **Enable debug** on affected instance:
   ```python
   enable_debug_tracing("emergency.jsonl")
   ```

2. **Reproduce issue** (operations now traced)

3. **Analyze traces**:
   ```bash
   python -m langswarm.core.debug.cli detail emergency.jsonl
   ```

4. **Disable debug**:
   ```python
   disable_debug_tracing()
   ```

5. **Monitor file size** during debug session

## ⚡ Key Benefits

- **🔍 Complete visibility** into agent execution
- **📊 Performance metrics** for every operation
- **🐛 Error isolation** with exact source locations
- **🔗 Hierarchical tracing** shows operation relationships
- **🚀 Production-safe** when disabled (default)

## 📖 Full Documentation

See [debug-tracing-system.md](debug-tracing-system.md) for complete guide.

---

**Remember: Debug is DISABLED by default - your production is safe! ✅**
