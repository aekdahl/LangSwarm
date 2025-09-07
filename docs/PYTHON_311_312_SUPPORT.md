# Python 3.11 & 3.12 Support Guide

LangSwarm v0.0.54.dev12+ now fully supports Python 3.11 and 3.12! This guide explains the changes and how to migrate.

## ✅ **What's Fixed**

### **Cloud Run Issue**
The main issue you encountered was **Python version incompatibility**:
- **Problem**: Cloud Run used Python 3.11, local dev used Python 3.9
- **Symptoms**: Tool hanging, `has_tools: false`, missing debug logs
- **Solution**: Enhanced async compatibility utilities

### **Python 3.11+ Changes**
Python 3.11 introduced stricter requirements for:
- AsyncIO event loop management
- Async context manager lifecycle  
- Import system behavior
- Error handling in `asyncio.gather()`

## 🐍 **Supported Python Versions**

| Version | Status | Recommended |
|---------|--------|-------------|
| 3.9     | ✅ Fully Supported | ✅ Production Ready |
| 3.10    | ✅ Fully Supported | ✅ Production Ready |
| 3.11    | ✅ Fully Supported | ✅ **Latest Stable** |
| 3.12    | ✅ Fully Supported | ✅ **Latest** |

**Minimum Version**: Python 3.9 (3.8 reached end-of-life)

## 🚀 **Migration Guide**

### **Cloud Run Deployment**

**Before (Python 3.9 only):**
```dockerfile
FROM python:3.9-slim
```

**After (Choose any supported version):**
```dockerfile
FROM python:3.11-slim
# OR
FROM python:3.12-slim
```

### **Local Development**

**Install any supported Python version:**
```bash
# Using pyenv
pyenv install 3.11.7
pyenv local 3.11.7

# Or using conda
conda create -n langswarm python=3.11
conda activate langswarm
```

### **Docker Compose**

**Update your docker-compose.yml:**
```yaml
services:
  langswarm:
    build:
      context: .
      dockerfile: Dockerfile
    image: python:3.11-slim  # or 3.12-slim
```

## 🔧 **Technical Details**

### **Compatibility Utilities**

LangSwarm includes new compatibility utilities in `langswarm.core.utils.python_compat`:

```python
from langswarm.core.utils.python_compat import (
    EventLoopManager,      # Smart event loop handling
    OpenAIClientFactory,   # Cross-version OpenAI clients  
    AsyncContextManager,   # Proper async context management
    IS_PYTHON_311_PLUS     # Version detection
)
```

### **Automatic Detection**

The BigQuery tool and other components automatically detect Python version and use appropriate patterns:

```python
# Python 3.11+ gets enhanced async patterns
if IS_PYTHON_311_PLUS:
    logger.info("Using Python 3.11+ compatibility mode")
    # Enhanced event loop management
    # Proper async context cleanup
    # Stricter error handling
```

### **Event Loop Management**

**Python 3.9/3.10:**
```python
# Old pattern (still works)
loop = asyncio.get_event_loop()
result = loop.run_until_complete(coro)
```

**Python 3.11+:**
```python
# New pattern (automatic in LangSwarm)
result = EventLoopManager.run_async_in_sync_context(coro)
```

## 🧪 **Testing**

### **Verify Compatibility**

Run the compatibility test (included in repository):
```bash
python test_python_version_compatibility.py
```

### **Expected Output**
```
🐍 PYTHON 3.11.7 COMPATIBILITY REPORT
==================================================
Overall Status: ✅ COMPATIBLE

Test Results:
  basic_imports: ✅ PASS
  version_detection: ✅ PASS  
  event_loop_sync: ✅ PASS
  async_context: ✅ PASS
  bigquery_tool: ✅ PASS
  agent_integration: ✅ PASS
```

### **CI/CD Testing**

The GitHub Actions workflow automatically tests all supported Python versions:
- Python 3.9 (baseline compatibility)
- Python 3.11 (current stable)  
- Python 3.12 (latest)

## 🎯 **Best Practices**

### **Production Deployment**

1. **Choose your Python version**:
   - **Python 3.11**: Most stable, well-tested
   - **Python 3.12**: Latest features, cutting edge

2. **Update Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "main.py"]
   ```

3. **Verify dependencies**:
   ```bash
   poetry install --with bigquery
   poetry run python -c "import langswarm; print('✅ LangSwarm ready')"
   ```

### **Development**

1. **Use virtual environments**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install poetry
   poetry install
   ```

2. **Test across versions** (if needed):
   ```bash
   python3.9 test_python_version_compatibility.py
   python3.11 test_python_version_compatibility.py  
   python3.12 test_python_version_compatibility.py
   ```

## 🔍 **Troubleshooting**

### **Common Issues**

**Issue**: `asyncio.run() cannot be called from a running event loop`
**Solution**: ✅ Fixed automatically with compatibility utilities

**Issue**: `'AsyncOpenAI' object has no attribute 'aclose'`  
**Solution**: ✅ Fixed with enhanced context management

**Issue**: Tool execution hangs in containers
**Solution**: ✅ Fixed with simplified execution patterns

### **Debug Information**

Enable debug logging to see Python version detection:
```python
import logging
logging.basicConfig(level=logging.INFO)

# You'll see:
# INFO:langswarm.mcp.tools.bigquery_vector_search.main:BigQuery tool running on Python 3.11+
```

### **Version Check**

Verify your Python version in production:
```python
from langswarm.core.utils.python_compat import get_python_version_info
print(get_python_version_info())
```

## 📋 **Summary**

✅ **Python 3.11 & 3.12 are now fully supported**  
✅ **Cloud Run deployment issues resolved**  
✅ **BigQuery tool execution fixed**  
✅ **Backward compatibility maintained**  
✅ **Comprehensive testing included**  

Your Cloud Run deployment should now work perfectly with Python 3.11! 🎉
