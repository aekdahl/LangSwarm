# Debug & Tracing Quick Start

**Get LangSwarm debug tracing running in emergency situations or development**

---

## 🚨 Emergency Production Debugging

When you have a critical issue in production and need immediate insight:

### **Step 1: Enable Emergency Tracing**
```python
from langswarm.core.debug import enable_debug_tracing

# ⚠️ Warning: 34% performance impact - emergency use only!
enable_debug_tracing("emergency.jsonl")
```

### **Step 2: Reproduce the Issue**
Run your failing LangSwarm code - it will now be automatically traced:

```python
# Your existing code - no changes needed
agent = MyAgent()
response = agent.chat("the failing request")  # ← Now traced
```

### **Step 3: Disable Tracing Immediately**
```python
from langswarm.core.debug import disable_debug_tracing
disable_debug_tracing()  # ← Critical: Stop performance impact
```

### **Step 4: Analyze the Emergency Trace**
```bash
python -m langswarm.core.debug.cli analyze emergency.jsonl
```

---

## 🔧 Development Environment Setup

For regular development debugging:

### **Step 1: Initialize Configuration**
```bash
cd your-langswarm-project
python -m langswarm.core.debug.cli init-config
```

This creates `langswarm/core/debug/debug_config.yaml` with sample settings.

### **Step 2: Add Your API Keys**
Edit the configuration file:

```yaml
# debug_config.yaml
openai:
  api_key: sk-your-actual-openai-api-key-here
  model: gpt-4o-mini

google_cloud:
  project_id: your-actual-gcp-project-id
  # No credentials_path needed if using `gcloud auth`

output_dir: debug_traces
log_level: INFO
```

### **Step 3: Validate Configuration**
```bash
python -m langswarm.core.debug.cli validate-config
```

### **Step 4: Test with Debug Cases**
```bash
# Run a simple test to verify everything works
python -m langswarm.core.debug.cli run-case-1
```

---

## 💻 Adding Tracing to Your Code

### **Pattern 1: Environment-Controlled (Recommended)**
```python
import os
from langswarm.core.debug import enable_debug_tracing

# Safe for production - only enables when explicitly requested
if os.getenv('LANGSWARM_DEBUG') == 'true':
    enable_debug_tracing("app_debug.jsonl")

# Your LangSwarm code runs normally:
# - LANGSWARM_DEBUG=false: no tracing, no performance impact
# - LANGSWARM_DEBUG=true: full tracing enabled
agent = MyAgent()
response = agent.chat("user request")
```

**Usage:**
```bash
# Development: Enable tracing
export LANGSWARM_DEBUG=true
python your_app.py

# Production: No tracing (default)
python your_app.py
```

### **Pattern 2: Explicit Control**
```python
from langswarm.core.debug import enable_debug_tracing, disable_debug_tracing

# Explicit control for specific scenarios
def debug_this_workflow():
    enable_debug_tracing("workflow_debug.jsonl")
    
    try:
        # Run the workflow you want to debug
        result = complex_workflow()
        return result
    finally:
        # Always disable to restore performance
        disable_debug_tracing()
```

### **Pattern 3: Custom Tracing**
```python
from langswarm.core.debug import get_debug_tracer

tracer = get_debug_tracer()
if tracer and tracer.enabled:
    with tracer.trace_operation("my_component", "my_operation", "Processing data"):
        # Your custom code - gets START/END events with timing
        result = process_data()
        tracer.log_info("my_component", "my_operation", f"Processed {len(result)} items")
```

---

## 🧪 Pre-Built Debug Cases

LangSwarm includes ready-made debug scenarios for testing different components:

### **Case 1: Simple Agent**
Tests basic agent functionality:
```bash
python -m langswarm.core.debug.cli run-case-1
```
**Trace file:** `debug_traces/case_1_simple_agent.jsonl`

### **Case 2: Agent with Memory**
Tests agent memory integration:
```bash
python -m langswarm.core.debug.cli run-case-2
```
**Trace file:** `debug_traces/case_2_agent_memory.jsonl`

### **Case 3: BigQuery Tool**
Tests BigQuery vector search tool with multiple scenarios:
```bash
python -m langswarm.core.debug.cli run-case-3
```
**Trace files:**
- `debug_traces/case_3_bigquery_similarity_search.jsonl`
- `debug_traces/case_3_bigquery_list_datasets.jsonl`
- `debug_traces/case_3_bigquery_error_handling.jsonl`

### **Case 4: Complex Workflow**
Tests multi-step workflow execution:
```bash
python -m langswarm.core.debug.cli run-case-4
```
**Trace file:** `debug_traces/case_4_complex_workflow.jsonl`

### **Run All Basic Cases**
```bash
python -m langswarm.core.debug.cli run-all-basic
```

---

## 📊 Quick Trace Analysis

### **Basic Analysis**
```bash
# Analyze a specific trace file
python -m langswarm.core.debug.cli analyze debug_traces/case_1_simple_agent.jsonl
```

**Output:**
```
📊 Trace Analysis: debug_traces/case_1_simple_agent.jsonl
   Total events: 45
   Unique traces: 1
   Duration: 2.34 seconds
   
🎯 Top Operations:
   agent.chat: 1 call, 2.1s total
   tool.execute: 3 calls, 0.8s total
   config.load: 1 call, 0.2s total

⚠️  Errors: 0
✅ Success: All operations completed successfully
```

### **Directory Summary**
```bash
# Analyze all traces in a directory
python -m langswarm.core.debug.cli summary debug_traces/
```

### **Watch for New Traces**
```bash
# Monitor for new trace files
python -m langswarm.core.debug.cli watch debug_traces/
```

---

## 🔍 Understanding Trace Output

### **Trace Event Structure**
Each line in the trace file is a JSON event:

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "parent_span_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "event_type": "START",
  "component": "agent",
  "operation": "chat",
  "level": "INFO",
  "message": "Starting agent chat operation",
  "data": {
    "user_input": "Hello world",
    "agent_id": "my_agent",
    "model": "gpt-4o"
  },
  "source_file": "agent_wrapper.py",
  "source_line": 123,
  "source_function": "chat"
}
```

### **Key Fields**
- **trace_id**: Groups related operations
- **span_id**: Unique identifier for this operation
- **parent_span_id**: Links to parent operation (hierarchical)
- **event_type**: START, END, INFO, ERROR, TOOL_CALL, etc.
- **component**: agent, tool, workflow, config, etc.
- **operation**: chat, execute, load, etc.
- **data**: Rich contextual information

### **Following Operation Flow**
1. **Find START event** for main operation
2. **Follow child spans** using parent_span_id relationships
3. **Check END event** for completion status and timing
4. **Review ERROR events** for failure details

---

## ⚡ Performance Tips

### **Minimize Performance Impact**
```python
# ✅ Good: Check if tracing is enabled before expensive operations
tracer = get_debug_tracer()
if tracer and tracer.enabled:
    # Only do expensive trace operations if actually tracing
    with tracer.trace_operation("component", "operation", "message"):
        do_work()

# ❌ Avoid: Always doing expensive operations
with tracer.trace_operation("component", "operation", expensive_operation()):  # Always runs
    do_work()
```

### **Use Appropriate Trace Levels**
```python
# For high-frequency operations, use DEBUG level
tracer.log_debug("component", "operation", "Frequent operation")

# For important milestones, use INFO level
tracer.log_info("component", "operation", "Important milestone")

# For problems, use ERROR level
tracer.log_error("component", "operation", "Something failed")
```

---

## 🎯 Next Steps

1. **[Set Up Configuration](../configuration/setup.md)** - Complete configuration guide
2. **[Learn the CLI Tools](../cli-tools/reference.md)** - All available commands
3. **[Understand Trace Analysis](../analysis/trace-analysis.md)** - Deep dive into analysis
4. **[Explore Test Cases](../test-cases/)** - Pre-built debugging scenarios

---

**You're now ready to use LangSwarm's debug tracing system for both emergency production debugging and regular development work!**
