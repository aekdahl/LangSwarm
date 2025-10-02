# LangSwarm Debug and Tracing System

## 🔍 Overview

The LangSwarm Debug and Tracing System provides comprehensive, structured logging and tracing capabilities for debugging and monitoring LangSwarm applications. It's designed to be **production-safe when disabled** and **powerful when enabled**.

## ✅ Key Features

- **🎯 Hierarchical Tracing**: Nested operations with trace_id/span_id/parent_span_id relationships
- **📊 Structured JSON Logs**: Machine-readable events with rich metadata
- **🚀 Production-Safe**: Negligible overhead when disabled (default state)
- **🛠️ Comprehensive Coverage**: Traces agents, tools, workflows, and config loading
- **📁 File-Based Output**: Real-time logging to local files
- **🔧 CLI Tools**: Built-in commands for running debug cases and analyzing traces
- **⚡ Performance Optimized**: Early returns and minimal allocations when disabled

## 🔒 Production Safety

### **Default State: DISABLED ✅**
- Debug tracing is **disabled by default**
- **Zero performance impact** until explicitly enabled
- **No file I/O or memory allocation** when disabled
- Safe to deploy with tracing code in production

### **Performance Characteristics**
- **When disabled**: `0.000023ms` overhead per operation (negligible)
- **When enabled**: `34%` performance impact (emergency debugging only)

## 🚀 Quick Start

### **Basic Usage**

```python
from langswarm.core.debug import enable_debug_tracing, run_case_1

# Enable debug tracing (applies monkey patches and starts logging)
enable_debug_tracing("my_debug.jsonl")

# Your LangSwarm code - now automatically traced
agent = SomeAgent()
response = agent.chat("Hello world")  # ← Automatically traced

# Run pre-built debug cases
result = await run_case_1()
print(f"Debug case completed: {result.success}")
```

### **Production-Safe Pattern**

```python
import os
from langswarm.core.debug import enable_debug_tracing

# Safe for production - only enable when needed
if os.getenv('LANGSWARM_DEBUG') == 'true':
    enable_debug_tracing("production_debug.jsonl")
    print("🔍 Debug tracing enabled")

# Your application runs normally
# - If debug=false: virtually no overhead
# - If debug=true: comprehensive tracing
```

## 📋 CLI Commands

### **Ready-Made Debug Cases**

```bash
# Run individual debug cases
python -m langswarm.core.debug.cli run-case-1  # Simple agent
python -m langswarm.core.debug.cli run-case-2  # Agent with memory
python -m langswarm.core.debug.cli run-case-3  # BigQuery tool
python -m langswarm.core.debug.cli run-case-4  # Agent with tools

# Run all basic cases
python -m langswarm.core.debug.cli run-all-basic
```

### **Configuration Management**

```bash
# Initialize debug configuration
python -m langswarm.core.debug.cli init-config

# Validate current configuration
python -m langswarm.core.debug.cli validate-config

# Show current configuration status
python -m langswarm.core.debug.cli show-config
```

### **Trace Analysis**

```bash
# Analyze trace files
python -m langswarm.core.debug.cli analyze debug_traces/my_trace.jsonl

# Detailed trace view
python -m langswarm.core.debug.cli detail debug_traces/my_trace.jsonl
```

## ⚙️ Configuration

### **Configuration File**

Create `langswarm/core/debug/debug_config.yaml`:

```yaml
# OpenAI Configuration (Required)
openai:
  api_key: your-openai-api-key
  model: gpt-4o

# Google Cloud (Required for BigQuery debugging)
google_cloud:
  project_id: your-gcp-project
  # credentials_path: null  # Uses gcloud auth if not set

# BigQuery Configuration
bigquery:
  dataset_id: vector_search
  table_name: embeddings
  embedding_model: text-embedding-3-small

# Output Settings
output_dir: debug_traces
log_level: INFO
```

### **Environment Variables**

Environment variables override config file settings:

```bash
export OPENAI_API_KEY="your-api-key"
export GOOGLE_CLOUD_PROJECT="your-project"
export LANGSWARM_DEBUG="true"
```

## 🏗️ Architecture

### **Components Traced**

1. **🤖 Agent Wrapper** (`AgentWrapper.chat()`, `._call_agent()`)
   - Query processing
   - Memory management
   - Response generation
   - Session handling

2. **🛠️ Config Loader** (`LangSwarmConfigLoader.load()`)
   - Configuration file loading
   - Agent initialization
   - Tool initialization
   - Component setup

3. **⚙️ Workflow Executor** (`._execute_step_inner_sync()`)
   - Workflow step execution
   - Step type detection
   - Error handling

4. **🔧 Middleware** (`MiddlewareMixin.to_middleware()`)
   - Tool call execution
   - MCP communication
   - Parameter validation

### **Trace Structure**

Each trace event contains:

```json
{
  "trace_id": "abc123...",           // Groups related operations
  "span_id": "def456...",            // Identifies this operation
  "parent_span_id": "ghi789...",     // Creates hierarchy
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "START|END|INFO|ERROR",
  "component": "agent|tool|config|workflow",
  "operation": "chat|load|call|execute",
  "level": "DEBUG|INFO|WARN|ERROR",
  "message": "Human readable description",
  "data": {                          // Rich contextual data
    "query": "user input",
    "response_length": 150,
    "execution_time_ms": 1250
  },
  "duration_ms": 1250,              // For START/END events
  "source_file": "agent.py",        // Code location
  "source_line": 123,
  "source_function": "chat"
}
```

## 💻 Advanced Usage

### **Custom Tracing**

```python
from langswarm.core.debug import get_debug_tracer

tracer = get_debug_tracer()
if tracer and tracer.enabled:
    # Manual event logging
    tracer.log_event(
        "INFO", "my_component", "my_operation",
        "Something happened",
        data={"key": "value"}
    )
    
    # Context manager for operations
    with tracer.trace_operation("my_component", "complex_op", "Doing complex work"):
        # Your code here - automatically gets START/END events
        do_complex_work()
```

### **Custom Debug Cases**

```python
from langswarm.core.debug.debug_cases import DebugCase

class MyCustomCase(DebugCase):
    def __init__(self):
        super().__init__("my_case", "Tests my custom functionality")
        
    async def setup(self) -> bool:
        # Initialize your test
        return True
        
    async def execute(self) -> Dict[str, Any]:
        # Run your test
        return {"result": "success"}

# Run it
case = MyCustomCase()
result = await case.run("debug_traces")
```

## 📊 Trace Analysis

### **Grouping Events**

```bash
# All events from same scenario
jq 'select(.trace_id == "abc123...")' debug_traces/*.jsonl

# All agent operations
jq 'select(.component == "agent")' debug_traces/*.jsonl

# Performance analysis
jq 'select(.duration_ms != null) | {operation, duration_ms}' debug_traces/*.jsonl
```

### **Performance Debugging**

```python
import json

# Load and analyze trace
with open('debug_traces/my_trace.jsonl') as f:
    events = [json.loads(line) for line in f]

# Find slow operations
slow_ops = [e for e in events if e.get('duration_ms', 0) > 1000]
print(f"Found {len(slow_ops)} operations > 1s")

# Analyze agent response times
agent_times = [e['duration_ms'] for e in events 
               if e.get('component') == 'agent' and e.get('duration_ms')]
avg_time = sum(agent_times) / len(agent_times)
print(f"Average agent response: {avg_time:.2f}ms")
```

## 🚨 Troubleshooting

### **Common Issues**

**1. API Key Errors**
```bash
# Check configuration
python -m langswarm.core.debug.cli validate-config

# Set environment variable
export OPENAI_API_KEY="your-key"
```

**2. BigQuery Tool Issues**
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Verify project access
gcloud config set project your-project-id
```

**3. Performance Issues**
```bash
# Check if debug is accidentally enabled
python -c "from langswarm.core.debug import get_debug_tracer; t=get_debug_tracer(); print(f'Debug enabled: {t.enabled if t else False}')"

# Disable debug tracing
python -c "from langswarm.core.debug import disable_debug_tracing; disable_debug_tracing()"
```

### **Debug Cases Not Working**

```bash
# Initialize configuration first
python -m langswarm.core.debug.cli init-config

# Validate setup
python -m langswarm.core.debug.cli validate-config

# Check specific case
python -m langswarm.core.debug.cli run-case-1
```

## 🔧 Production Deployment

### **Recommended Setup**

```python
import os
from langswarm.core.debug import enable_debug_tracing

class ProductionApp:
    def __init__(self):
        # Safe: Apply monkey patches (negligible overhead when disabled)
        if os.getenv('LANGSWARM_DEBUG_ENABLED', 'false').lower() == 'true':
            output_file = os.getenv('LANGSWARM_DEBUG_FILE', 'app_debug.jsonl')
            enable_debug_tracing(output_file)
            print(f"🔍 Debug tracing enabled: {output_file}")
        
    def process_request(self, user_input):
        # This will be traced if debug is enabled, ignored if disabled
        agent = self.get_agent()
        return agent.chat(user_input)
```

### **Environment Variables**

```bash
# Production (default) - debug disabled
# No environment variables needed

# Emergency debugging - enable for specific instances
export LANGSWARM_DEBUG_ENABLED=true
export LANGSWARM_DEBUG_FILE=/tmp/emergency_debug.jsonl

# Monitor file size and disable when done
```

### **Monitoring**

```bash
# Check debug status
curl http://localhost:8080/debug/status

# File size monitoring
watch -n 1 'ls -lh /tmp/emergency_debug.jsonl 2>/dev/null || echo "No debug file"'

# Disable after collecting data
unset LANGSWARM_DEBUG_ENABLED
# Restart service or call disable_debug_tracing()
```

## 📈 Performance Guidelines

### **✅ Safe for Production**
- **Default state**: Debug disabled
- **Monkey patches applied**: Negligible overhead
- **Early returns**: 0.000023ms per operation

### **⚠️ Emergency Use Only**
- **Debug enabled**: 34% performance impact
- **File I/O**: ~3KB per operation
- **Memory growth**: Events accumulate

### **Best Practices**
1. **Enable debug** only for troubleshooting
2. **Monitor disk space** when debug is enabled
3. **Set time limits** for debug sessions
4. **Use dedicated log volumes** for debug output
5. **Scale horizontally** if needed during debug

## 🔗 Related Documentation

- [Debug Configuration Guide](debug-configuration.md)
- [Debug Cases Guide](debug-cases.md)
- [Performance Analysis](debug-performance.md)
- [CLI Reference](debug-cli.md)

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Run debug cases to verify setup
3. Review trace files for error patterns
4. Check configuration with `validate-config`

---

*Last updated: September 2024*