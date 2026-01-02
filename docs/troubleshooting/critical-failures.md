# Critical Failure Handling in LangSwarm Debug System

## Overview

The LangSwarm Debug System now includes comprehensive critical failure detection and handling that **immediately halts execution** when critical issues are detected, preventing cascading failures and providing clear diagnostic information.

## What Constitutes a Critical Failure

Critical failures are issues that will prevent successful execution and should halt the system immediately:

### 🚨 **API Key Issues**
- Missing API keys (OpenAI, Anthropic, etc.)
- Invalid/expired API keys
- Authentication failures

### 🚨 **Model Initialization Failures**
- Model not found or unavailable
- Model initialization errors
- Unsupported model configurations

### 🚨 **Network/Connectivity Issues**
- Connection timeouts to API endpoints
- DNS resolution failures
- SSL certificate errors

### 🚨 **Configuration Errors**
- Missing required parameters
- Invalid configuration formats
- Configuration validation failures

## How It Works

### **1. Automatic Detection**
The system analyzes error messages and exceptions using pattern matching:

```python
from langswarm.core.debug import is_critical_error, handle_critical_failure

# Check if an error is critical
if is_critical_error("API key for openai not found"):
    print("This will halt execution!")

# Handle failure with automatic detection
should_continue = handle_critical_failure(
    error_message="API key missing", 
    exception=ValueError("API key required"),
    component="openai_agent"
)
# Returns False for critical failures, True for recoverable ones
```

### **2. Early Termination**
When a critical failure is detected:

- ✋ **Execution halts immediately**
- 🚨 **Clear diagnostic message is displayed**
- 💡 **Actionable solution is provided**
- 📝 **Failure is logged with full context**
- 🛑 **Subsequent operations are prevented**

### **3. Clear Error Messages**
Critical failures display prominent, actionable error messages:

```
🚨 CRITICAL FAILURE DETECTED 🚨
Component: openai_agent
Category: api_key
Error: API key for openai not found. Set OPENAI_API_KEY or pass the key explicitly.
💡 Solution: Set the required API key as an environment variable (e.g., OPENAI_API_KEY) or pass it explicitly in the configuration.

⛔ Execution halted due to critical failure.
Please fix the issue above before proceeding.
```

## Implementation in Test Cases

### **Test Suite Early Termination**
When running multiple test cases, the first critical failure stops execution:

```python
# This will stop at the first critical failure
results = await run_all_basic_cases()

# Output:
# ❌ FAIL case_1_simple_agent 🚨 CRITICAL
# 🚨 Critical failure detected in test case 1/3
# 🛑 Stopping test execution to prevent cascading failures.
```

### **Individual Test Case Handling**
Each test case checks for critical failures during setup and execution:

```python
async def setup(self) -> bool:
    try:
        # Try to initialize agent
        loader._initialize_agents()
        agent = loader.agents.get("simple_test_agent")
        
        # Check for critical failure (missing API key)
        if isinstance(agent, dict) and agent.get("status") == "pending_api_key":
            error_msg = agent.get("error", "API key required")
            should_continue = handle_critical_failure(error_msg, ValueError(error_msg), "openai_agent")
            if not should_continue:
                return False  # Critical failure, halt execution
                
    except Exception as e:
        should_continue = handle_critical_failure(str(e), e, "openai_agent")
        if not should_continue:
            return False  # Critical failure, halt execution
```

## Integration with Existing Code

### **1. Automatic Integration**
The debug system automatically detects critical failures in:
- Agent initialization (`AgentWrapper`)
- Workflow execution (`WorkflowExecutor`)
- Tool calls (`MiddlewareMixin`)

### **2. Manual Integration**
Add critical failure detection to your own code:

```python
from langswarm.core.debug import handle_critical_failure

def my_business_logic():
    try:
        # Your code here
        result = call_external_api()
    except Exception as e:
        # Check if this is a critical failure
        should_continue = handle_critical_failure(str(e), e, "my_component")
        if not should_continue:
            raise  # Re-raise to halt execution
        
        # Handle recoverable error
        return fallback_result()
```

### **3. Custom Failure Patterns**
You can extend the critical failure detection:

```python
from langswarm.core.debug.critical_failures import CriticalFailureDetector

detector = CriticalFailureDetector()

# Add custom patterns
detector.CRITICAL_PATTERNS["database"] = [
    r"database.*connection.*failed",
    r"schema.*not.*found"
]

detector.SUGGESTIONS["database"] = "Check database connectivity and schema configuration."
```

## Examples and Testing

### **Run Examples**
```bash
# See critical failure detection in action
python critical_failure_example.py

# Test with CLI (will show critical failure handling)
python -m langswarm.core.debug.cli run-case-1
```

### **Expected Behavior**
1. **With missing API key**: Critical failure detected, execution halted
2. **With valid API key**: Normal execution continues
3. **In test suites**: First critical failure stops remaining tests

### **Sample Output**
```bash
🚨 CRITICAL FAILURE DETECTED 🚨
Component: openai_agent
Category: api_key
Error: API key for openai not found. Set OPENAI_API_KEY or pass the key explicitly.
💡 Solution: Set the required API key as an environment variable (e.g., OPENAI_API_KEY) or pass it explicitly in the configuration.

⛔ Execution halted due to critical failure.
Please fix the issue above before proceeding.
```

## Benefits

### **🚫 Prevents Cascading Failures**
- Stops at the root cause instead of generating dozens of confusing downstream errors
- Saves time by not running tests that are guaranteed to fail

### **🎯 Clear Diagnostics**
- Immediate identification of the actual problem
- Actionable solutions provided with each error
- Structured logging for analysis

### **⚡ Fast Feedback**
- No waiting for long test suites to complete when there's a fundamental issue
- Quick identification of setup problems

### **🧹 Clean Error Messages**
- No more hunting through pages of stack traces
- Clear distinction between critical and recoverable issues

## Configuration

### **Enable Critical Failure Detection**
Critical failure detection is automatically enabled when you enable debug tracing:

```python
from langswarm.core.debug import enable_debug_tracing

# This enables both tracing AND critical failure detection
enable_debug_tracing("my_debug.jsonl")
```

### **Customize Behavior**
```python
from langswarm.core.debug import initialize_failure_handler

# Initialize with custom settings
failure_handler = initialize_failure_handler(tracer)

# Check for failures manually
if failure_handler.has_critical_failures():
    summary = failure_handler.get_failure_summary()
    print(f"Critical failures detected: {summary['count']}")
```

## Best Practices

### **1. Set API Keys Early**
Ensure all required API keys are configured before running tests:
```bash
export OPENAI_API_KEY="your-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### **2. Use Test Cases for Validation**
Run the basic test cases first to validate your setup:
```bash
python -m langswarm.core.debug.cli run-all-basic
```

### **3. Handle Critical Failures in Production**
Add critical failure detection to production code for better error handling:
```python
if not handle_critical_failure(error_msg, exception, "production_component"):
    # Log critical failure and gracefully shutdown
    logger.critical("Critical failure detected, shutting down")
    sys.exit(1)
```

### **4. Monitor for Patterns**
Use the structured logs to identify common critical failure patterns:
```bash
python -m langswarm.core.debug.cli analyze debug_traces/case_1_simple_agent.jsonl
```

## Summary

The critical failure handling system ensures that:

✅ **Critical issues are caught immediately**  
✅ **Clear, actionable error messages are provided**  
✅ **Execution stops before cascading failures**  
✅ **Root causes are quickly identified**  
✅ **Time is saved on debugging**  
✅ **Production systems fail gracefully**  

This creates a much better debugging experience and prevents the frustration of chasing downstream errors when the real issue is a simple configuration problem.
