# Emergency Stop Guide: Preventing Runaway Costs in LangSwarm V1

## 🚨 Quick Start: Protect Your Wallet NOW

If you're running LangSwarm workflows and worried about runaway costs, add this to the top of your script:

```python
from langswarm.v1.safety_limits import quick_protect

# One line to protect against runaway costs
limits = quick_protect(budget=5.00)  # $5 hard limit

# Apply to all workflows
result = executor.run_workflow('workflow_id', user_input, **limits)
```

**What this does:**
- Sets $5 hard budget limit
- 60 second timeout
- Max 20 API calls
- Stops after 3 consecutive errors
- **Automatically aborts** if any limit is exceeded

---

## 💰 Why You Need This

### The Problem
Without safety limits, a single bug can cause:
- **Endless retry loops**: 100+ API calls instead of 3
- **Runaway costs**: $50-$500 in minutes
- **Hanging workflows**: Hours of execution
- **No easy abort**: Ctrl+C doesn't always work cleanly

### The Solution (v0.0.54.dev57)
**7 Layers of Protection:**
1. ✅ Retry limits (fixed in dev56)
2. ✅ JSON parsing depth limits (fixed in dev56)
3. ✅ Budget caps (existing feature)
4. ✅ **Execution timeout** (NEW)
5. ✅ **API call limits** (NEW)
6. ✅ **Circuit breaker** (NEW)
7. ✅ **Graceful Ctrl+C** (NEW)

---

## 🛡️ Emergency Stop Methods

### Method 1: Press Ctrl+C (Instant Stop)
**When**: Workflow is running and you want to stop it NOW

```bash
# While workflow is running, press:
Ctrl + C
```

**What happens:**
```
🛑 Received shutdown signal. Aborting workflow to prevent further costs...
KeyboardInterrupt: 🛑 Manual abort via Ctrl+C to prevent runaway costs
```

**Result**: Workflow stops at next step boundary, no further API calls

---

### Method 2: Budget Limits (Auto-Stop)
**When**: You want automatic cost protection

```python
from langswarm.v1.safety_limits import set_budget_limits

# Set BEFORE running workflows
set_budget_limits(
    total_budget=10.00,           # Stop at $10
    agent_limits={'gpt4': 5.00}   # Stop GPT-4 at $5
)

# Now any workflow will auto-abort if budget exceeded
result = executor.run_workflow('workflow_id', input)
```

**Auto-abort message:**
```
RuntimeError: Total budget exceeded. Execution blocked.
```

---

### Method 3: Timeout Limits (Auto-Stop)
**When**: You want time-based protection

```python
# Stop after 60 seconds
result = executor.run_workflow(
    'workflow_id', 
    user_input,
    max_execution_time_sec=60
)
```

**Auto-abort message:**
```
TimeoutError: ⏱️ Workflow execution exceeded maximum time limit (60s). 
Elapsed: 62.3s. Emergency abort to prevent runaway costs.
```

---

### Method 4: API Call Limits (Auto-Stop)
**When**: You want to limit API usage

```python
# Stop after 20 API calls
result = executor.run_workflow(
    'workflow_id', 
    user_input,
    max_api_calls=20
)
```

**Auto-abort message:**
```
RuntimeError: 🚨 Emergency abort: Maximum API calls (20) exceeded.
Current count: 21. This prevents runaway loops from consuming credits.
```

---

### Method 5: Circuit Breaker (Auto-Stop)
**When**: Workflow has consecutive errors

```python
# Stop after 5 consecutive errors
result = executor.run_workflow(
    'workflow_id', 
    user_input,
    max_consecutive_errors=5
)
```

**Auto-abort message:**
```
RuntimeError: 🔴 Circuit breaker triggered: 5 consecutive errors.
Emergency abort to prevent runaway costs.
```

---

## 🎯 Recommended Settings by Use Case

### Development/Testing
```python
from langswarm.v1.safety_limits import set_conservative_limits

limits = set_conservative_limits()
# - $5 budget
# - 60s timeout
# - 20 API calls
# - 3 consecutive errors
```

### Production (Low-Risk)
```python
limits = {
    'max_execution_time_sec': 120,    # 2 minutes
    'max_api_calls': 50,
    'max_consecutive_errors': 5
}
set_budget_limits(total_budget=20.00)
```

### Production (High-Volume)
```python
from langswarm.v1.safety_limits import set_production_limits

limits = set_production_limits()
# - $50 budget
# - 5min timeout
# - 200 API calls
# - 10 consecutive errors
```

### Long-Running Workflows
```python
limits = {
    'max_execution_time_sec': 600,    # 10 minutes
    'max_api_calls': 500,
    'max_consecutive_errors': 15
}
set_budget_limits(total_budget=100.00)
```

---

## 📊 Monitoring Costs

### Check Current Spending
```python
from langswarm.v1.safety_limits import print_cost_report

print_cost_report()
```

**Output:**
```
📊 Cost Report
==================================================
Total Spent: $2.3450
Budget Limit: $10.00
Remaining: $7.6550 (76.6%)

Per-Agent Costs:
  - gpt4: $1.8200 / $5.00
  - gpt3: $0.5250
==================================================
```

### Get Programmatic Access
```python
from langswarm.v1.safety_limits import get_current_limits

limits = get_current_limits()
print(f"Spent: ${limits['budget']['total_spent']:.2f}")
print(f"Remaining: ${limits['budget']['total_budget_limit'] - limits['budget']['total_spent']:.2f}")
```

---

## 🚦 Complete Protection Example

```python
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
from langswarm.v1.safety_limits import quick_protect, print_cost_report

# 1. Set up protection FIRST
limits = quick_protect(budget=5.00)

# 2. Load workflow
loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# 3. Run with ALL protections enabled
try:
    result = executor.run_workflow('main_workflow', user_input, **limits)
    print("✅ Success!")
    
except TimeoutError as e:
    print(f"⏱️ TIMEOUT: {e}")
    print("Workflow took too long - auto-aborted")
    
except RuntimeError as e:
    if "API calls" in str(e):
        print(f"📞 TOO MANY CALLS: {e}")
        print("Possible endless loop detected - auto-aborted")
    elif "budget" in str(e).lower():
        print(f"💰 BUDGET EXCEEDED: {e}")
        print("Cost limit reached - auto-aborted")
    elif "Circuit breaker" in str(e):
        print(f"🔴 TOO MANY ERRORS: {e}")
        print("Error loop detected - auto-aborted")
    else:
        print(f"❌ ERROR: {e}")
    
except KeyboardInterrupt as e:
    print(f"🛑 MANUAL ABORT: {e}")
    print("You pressed Ctrl+C - workflow stopped")
    
finally:
    # ALWAYS show cost report
    print("\n" + "="*50)
    print_cost_report()
    print("="*50)
```

---

## ⚡ Quick Reference

| Method | How to Trigger | When Checked | Auto-Abort |
|--------|---------------|--------------|------------|
| **Ctrl+C** | Press Ctrl+C | Every step | ✅ |
| **Timeout** | `max_execution_time_sec=60` | Every step | ✅ |
| **API Limits** | `max_api_calls=20` | Every step | ✅ |
| **Circuit Breaker** | `max_consecutive_errors=5` | Every step | ✅ |
| **Budget** | `set_budget_limits(total_budget=10)` | Every API call | ✅ |

---

## 🔥 Emergency Scenarios

### Scenario 1: Workflow Won't Stop
**Problem**: Workflow keeps looping, ignoring retries

**Solution**:
```python
# Press Ctrl+C immediately
# Then add stricter limits:
limits = {
    'max_execution_time_sec': 30,
    'max_api_calls': 10,
    'max_consecutive_errors': 2
}
```

### Scenario 2: Costs Spiraling
**Problem**: Spending $1/minute unexpectedly

**Solution**:
```python
# Set immediate budget cap
from langswarm.v1.safety_limits import set_budget_limits
set_budget_limits(total_budget=5.00)

# All future workflows will stop at $5
```

### Scenario 3: Unknown How Much Spent
**Problem**: Can't see current costs

**Solution**:
```python
from langswarm.v1.safety_limits import print_cost_report
print_cost_report()
```

### Scenario 4: Testing New Workflow
**Problem**: Don't know if it will loop

**Solution**:
```python
# Use ultra-conservative limits for first run
limits = {
    'max_execution_time_sec': 30,
    'max_api_calls': 5,
    'max_consecutive_errors': 2
}
set_budget_limits(total_budget=1.00)
```

---

## 📱 Integration Examples

### FastAPI Endpoint
```python
from fastapi import FastAPI, HTTPException
from langswarm.v1.safety_limits import quick_protect

app = FastAPI()

@app.post("/run-workflow")
async def run_workflow(request: dict):
    limits = quick_protect(budget=2.00)  # $2 per request
    
    try:
        result = executor.run_workflow(
            'api_workflow', 
            request['input'],
            **limits
        )
        return {"status": "success", "result": result}
    except (TimeoutError, RuntimeError, KeyboardInterrupt) as e:
        raise HTTPException(status_code=429, detail=f"Safety limit: {str(e)}")
```

### Celery Task
```python
from celery import Celery
from langswarm.v1.safety_limits import set_workflow_limits

app = Celery('tasks')

@app.task(time_limit=120)  # Celery timeout
def process_workflow(input_data):
    # Additional LangSwarm protection
    limits = set_workflow_limits(
        max_execution_time_sec=100,
        max_api_calls=30
    )
    
    return executor.run_workflow('task_workflow', input_data, **limits)
```

---

## 🎓 Best Practices

1. **Always use `quick_protect()` during development**
2. **Set budget limits BEFORE any workflow execution**
3. **Monitor costs with `print_cost_report()` after each run**
4. **Use conservative limits for untested workflows**
5. **Increase limits gradually based on actual usage**
6. **Keep Ctrl+C as final emergency stop**
7. **Log all safety aborts for debugging**

---

## 🔗 Related Documentation

- [RELEASE_NOTES_v0.0.54.dev57.md](RELEASE_NOTES_v0.0.54.dev57.md) - Full release notes
- [RELEASE_NOTES_v0.0.54.dev56.md](RELEASE_NOTES_v0.0.54.dev56.md) - Retry loop fixes
- `langswarm/v1/safety_limits.py` - Source code with examples

---

## 🆘 Support

If safety mechanisms don't work:
1. Check you're using v0.0.54.dev57 or later
2. Verify limits are passed to `run_workflow()`
3. Check logs for specific error messages
4. Open a [GitHub Issue](https://github.com/aekdahl/langswarm/issues)

---

**Your wallet will thank you!** 💰🛡️

