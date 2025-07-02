# Quick Test Guide - Enhanced MCP Patterns

This guide helps developers quickly test the enhanced MCP patterns implementation.

## 🚀 Quick Start Testing

### 1. **Run Manual Test** (30 seconds)
```bash
python3 test_enhanced_mcp_manual.py
```
**Expected Output:**
```
🚀 Enhanced MCP Patterns - Basic Test
✅ Status: 201
✅ Result: {"content": "test content"}
✅ MCP URL: local://filesystem
✅ SUCCESS
```

### 2. **Run Unit Tests** (1 minute)
```bash
# Enhanced pattern tests
/Users/alexanderekdahl/Library/Python/3.9/bin/pytest tests/core/wrappers/test_enhanced_mcp_patterns.py -v

# Legacy compatibility tests
/Users/alexanderekdahl/Library/Python/3.9/bin/pytest tests/core/wrappers/test_middleware.py -v
```

### 3. **Full Wrapper Test Suite** (2 minutes)
```bash
/Users/alexanderekdahl/Library/Python/3.9/bin/pytest tests/core/wrappers/ -v
```

## ✅ Success Indicators

### ✅ All Tests Should Pass
- **Enhanced MCP Tests**: 4/4 passed
- **Legacy Middleware Tests**: 3/3 passed
- **Manual Test**: SUCCESS message

### ✅ Key Features Working
1. **MCP Input Detection**: `{"mcp": {...}}` patterns recognized
2. **Local Mode**: `local://filesystem` URLs generated
3. **Direct Pattern**: Method calls routed correctly
4. **Intent Pattern**: Workflow routing functional
5. **Error Handling**: Validation messages clear

## 🔧 Test What Matters

### Critical Test Cases
1. **Direct Pattern Local Mode** ✅
   ```python
   agent_input = {
       "mcp": {
           "tool": "filesystem",
           "method": "read_file", 
           "params": {"path": "/tmp/test.txt"}
       }
   }
   ```

2. **Intent Pattern Local Mode** ✅
   ```python
   agent_input = {
       "mcp": {
           "tool": "local_analytics",
           "intent": "analyze sales trends",
           "context": "Q4 data"
       }
   }
   ```

3. **Error Handling** ✅
   ```python
   # Missing tool field
   agent_input = {"mcp": {"method": "read_file"}}
   # Should return 400 error
   ```

4. **Legacy Compatibility** ✅
   ```python
   # Non-MCP tools should still work
   agent_input = {
       "summarizer": {
           "method": "summarize",
           "params": {"text": "hello"}
       }
   }
   ```

## 🚨 Red Flags

### ❌ Test Failures to Investigate
- Any enhanced MCP pattern test fails
- Legacy middleware tests break
- Manual test shows ERROR instead of SUCCESS
- Missing MCP URL in test output

### ❌ Ignore These (Known Issues)
- LangSmith logging test failure (unrelated)
- Integration test agent factory issues (config format)

## ⚡ Performance Validation

### Check Local Mode Performance
Look for these indicators in test output:
- ✅ `MCP URL: local://filesystem` (not `stdio://`)
- ✅ `[LOG] Agent test-agent: Using direct MCP: filesystem.read_file`
- ✅ `MCP Direct output: {...}` (successful call)

## 🎯 Minimum Viable Testing

**If you only have 30 seconds:**
```bash
python3 test_enhanced_mcp_manual.py
```
Should see `✅ SUCCESS` - that means core functionality works.

**If you have 2 minutes:**
```bash
python3 test_enhanced_mcp_manual.py && \
/Users/alexanderekdahl/Library/Python/3.9/bin/pytest tests/core/wrappers/test_enhanced_mcp_patterns.py tests/core/wrappers/test_middleware.py -v
```
Should see all tests passing.

## 🔍 Debug Test Failures

### Common Issues & Fixes

1. **Import Errors**
   ```bash
   # Add project to Python path
   export PYTHONPATH=$PYTHONPATH:/path/to/LangSwarm
   ```

2. **Pytest Not Found**
   ```bash
   pip3 install pytest
   # or use full path
   /Users/alexanderekdahl/Library/Python/3.9/bin/pytest
   ```

3. **Module Import Issues**
   ```bash
   # Run from project root
   cd /path/to/LangSwarm
   python3 test_enhanced_mcp_manual.py
   ```

## 📊 Expected Test Results

### ✅ Successful Test Run
```
Manual Test: ✅ SUCCESS
Enhanced MCP Tests: ✅ 4/4 passed  
Legacy Tests: ✅ 3/3 passed
Wrapper Suite: ✅ 31/32 passed (1 LangSmith failure OK)
```

### ❌ Failed Test Run
If you see test failures in enhanced MCP or middleware tests, the implementation needs fixing before publication.

---

**Ready for Publication**: When all critical tests pass ✅ 