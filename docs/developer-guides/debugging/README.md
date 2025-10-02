# LangSwarm Debug & Tracing System

**Comprehensive, production-safe debugging and tracing for LangSwarm applications**

## 🎯 Overview

The LangSwarm Debug & Tracing System provides structured, hierarchical logging and tracing capabilities designed to be **production-safe when disabled** and **powerful when enabled**. It's built for debugging complex multi-agent workflows, tool executions, and system interactions.

---

## 🔒 Production Safety First

### **Default State: DISABLED ✅**
- Debug tracing is **OFF by default**
- **Zero performance impact** until explicitly enabled  
- **No file I/O or memory allocation** when disabled
- Safe to deploy with tracing code in production

### **Performance Characteristics**
| State | Overhead | Use Case |
|-------|----------|----------|
| **Disabled (default)** | `0.000023ms` per operation | ✅ **Production safe** |
| **Enabled** | `34%` performance hit | ⚠️ **Emergency debugging only** |

---

## 🚀 Quick Start

### **Emergency Production Debugging**
```python
from langswarm.core.debug import enable_debug_tracing

# Enable (34% performance hit - emergency only!)
enable_debug_tracing("emergency.jsonl")

# Your LangSwarm code - now automatically traced
agent = MyAgent()
response = agent.chat("debug this issue")  # ← Logged with full context

# Disable when done
from langswarm.core.debug import disable_debug_tracing
disable_debug_tracing()
```

### **Production-Safe Pattern**
```python
import os
from langswarm.core.debug import enable_debug_tracing

# Safe for production deployment
if os.getenv('LANGSWARM_DEBUG') == 'true':
    enable_debug_tracing("app_debug.jsonl")

# Your app runs normally (traced if debug enabled, ignored if disabled)
```

### **Ready-Made Debug Cases**
```bash
# CLI commands for instant debugging
python -m langswarm.core.debug.cli run-case-1  # Simple agent
python -m langswarm.core.debug.cli run-case-3  # BigQuery tool
python -m langswarm.core.debug.cli show-config # Check setup
```

---

## 🎯 Key Features

### **Hierarchical Tracing**
- Nested operations with trace_id/span_id/parent_span_id relationships
- Complete execution flow tracking across components
- Easy correlation of related operations

### **Structured JSON Logs**
- Machine-readable events with rich metadata
- Performance metrics and timing data
- Error isolation with source locations
- Rich contextual data for analysis

### **Comprehensive Coverage**
When enabled, traces all core components:
- 🤖 **Agent calls** (chat, memory, sessions)
- 🛠️ **Tool execution** (MCP, parameters, responses)  
- ⚙️ **Config loading** (agents, tools, initialization)
- 📋 **Workflows** (step execution, routing, errors)
- 🔗 **Middleware** (request/response processing)

### **File-Based Output**
- Real-time logging to local files
- Configurable output paths and formats
- Separate trace files for different scenarios
- JSON Lines format for easy parsing

### **CLI Tools**
- Built-in commands for running debug cases
- Trace analysis and visualization
- Configuration management
- Health checks and validation

---

## 📚 Documentation Structure

### 🚀 [Quick Start](quick-start/)
Get debug tracing running immediately for emergency situations.

- **[Emergency Debugging](quick-start/emergency.md)** - Critical production issues
- **[Basic Setup](quick-start/basic-setup.md)** - Development environment
- **[Common Patterns](quick-start/patterns.md)** - Typical usage scenarios

### ⚙️ [Configuration](configuration/)
Complete configuration management for debug tracing.

- **[Setup Guide](configuration/setup.md)** - Initial configuration
- **[Config File Reference](configuration/config-reference.md)** - All options explained
- **[Environment Variables](configuration/environment.md)** - Environment overrides
- **[Security Best Practices](configuration/security.md)** - Safe credential handling

### 🔍 [Tracing System](tracing-system/)
Deep dive into the tracing architecture and capabilities.

- **[Architecture Overview](tracing-system/architecture.md)** - System design
- **[Trace Event Format](tracing-system/event-format.md)** - JSON structure
- **[Hierarchical Spans](tracing-system/hierarchical-spans.md)** - Nested operations
- **[Component Integration](tracing-system/integration.md)** - How components are traced
- **[Performance Impact](tracing-system/performance.md)** - Overhead analysis

### 🛠️ [CLI Tools](cli-tools/)
Command-line tools for debugging and analysis.

- **[CLI Reference](cli-tools/reference.md)** - All available commands
- **[Debug Cases](cli-tools/debug-cases.md)** - Pre-built test scenarios
- **[Trace Analysis](cli-tools/analysis.md)** - Analyzing trace files
- **[Configuration Commands](cli-tools/configuration.md)** - Config management

### 🧪 [Test Cases](test-cases/)
Pre-built debug scenarios for testing different components.

- **[Case 1: Simple Agent](test-cases/simple-agent.md)** - Basic agent debugging
- **[Case 2: Agent with Memory](test-cases/agent-memory.md)** - Memory system tracing
- **[Case 3: BigQuery Tool](test-cases/bigquery-tool.md)** - Tool execution tracing
- **[Case 4: Complex Workflow](test-cases/complex-workflow.md)** - Multi-step workflows
- **[Custom Test Cases](test-cases/custom-cases.md)** - Building your own scenarios

### 📊 [Analysis](analysis/)
Analyzing and understanding trace data.

- **[Trace Analysis Guide](analysis/trace-analysis.md)** - Understanding trace files
- **[Performance Analysis](analysis/performance.md)** - Finding bottlenecks
- **[Error Investigation](analysis/error-investigation.md)** - Debugging failures
- **[Visualization Tools](analysis/visualization.md)** - Visual trace analysis

---

## 🔧 Core Components

### **DebugTracer**
Main tracing class that handles structured logging and hierarchical spans.

```python
from langswarm.core.debug import get_debug_tracer

tracer = get_debug_tracer()
if tracer and tracer.enabled:
    with tracer.trace_operation("my_component", "my_operation", "Doing work"):
        # Your code - gets START/END events with timing
        do_work()
```

### **Integration Layer**
Monkey-patching system that automatically traces existing components without code changes.

```python
from langswarm.core.debug import enable_debug_tracing

# Automatically enables tracing for:
# - AgentWrapper.chat()
# - WorkflowExecutor.run_workflow()
# - LangSwarmConfigLoader.load()
# - All MCP tool calls
enable_debug_tracing("auto_trace.jsonl")
```

### **CLI Interface**
Command-line tools for debug operations and analysis.

```bash
# Run debug cases
python -m langswarm.core.debug.cli run-case-1
python -m langswarm.core.debug.cli run-all-basic

# Manage configuration
python -m langswarm.core.debug.cli init-config
python -m langswarm.core.debug.cli validate-config

# Analyze traces
python -m langswarm.core.debug.cli analyze trace_file.jsonl
python -m langswarm.core.debug.cli summary debug_traces/
```

### **Test Cases**
Pre-built scenarios for testing different LangSwarm components.

```python
from langswarm.core.debug.debug_cases import run_case_1, run_case_3

# Simple agent test
result = await run_case_1()

# BigQuery tool test with multiple scenarios
result = await run_case_3()
```

---

## 📋 Common Use Cases

### **Production Emergency Debugging**
When something breaks in production and you need immediate insight:

1. **Enable Emergency Tracing**
   ```python
   enable_debug_tracing("emergency.jsonl")
   ```

2. **Reproduce the Issue**
   - Run the failing operation
   - Let tracing capture all details

3. **Analyze Traces**
   ```bash
   python -m langswarm.core.debug.cli analyze emergency.jsonl
   ```

4. **Disable Tracing**
   ```python
   disable_debug_tracing()
   ```

### **Development Debugging**
During development when building new features:

1. **Set Up Development Config**
   ```bash
   python -m langswarm.core.debug.cli init-config
   # Edit debug_config.yaml with your API keys
   ```

2. **Enable Automatic Tracing**
   ```python
   import os
   if os.getenv('DEV_MODE') == 'true':
       enable_debug_tracing("dev_debug.jsonl")
   ```

3. **Run Debug Cases**
   ```bash
   python -m langswarm.core.debug.cli run-case-1  # Test basic functionality
   ```

### **Component Integration Testing**
When integrating new tools or agents:

1. **Create Custom Test Case**
   ```python
   from langswarm.core.debug.debug_cases import DebugCase
   
   class MyComponentTest(DebugCase):
       async def execute(self):
           # Your test logic here
           pass
   ```

2. **Run with Tracing**
   ```python
   enable_debug_tracing("integration_test.jsonl")
   result = await MyComponentTest().run()
   ```

3. **Analyze Results**
   ```bash
   python -m langswarm.core.debug.cli analyze integration_test.jsonl
   ```

---

## 🎯 Best Practices

### **Production Usage**
- ✅ Always use environment variable guards
- ✅ Enable only for specific issues
- ✅ Disable immediately after debugging
- ❌ Never leave enabled in production
- ❌ Don't trace sensitive data

### **Development Usage**
- ✅ Use configuration files for API keys
- ✅ Create separate trace files for different tests
- ✅ Analyze traces regularly during development
- ✅ Use pre-built debug cases to verify functionality

### **Security Considerations**
- 🔒 Never commit API keys to version control
- 🔒 Use restricted service accounts for Google Cloud
- 🔒 Store credentials outside project directories
- 🔒 Rotate credentials regularly

---

## 🚀 Getting Started

1. **[Set Up Configuration](configuration/setup.md)** - Initialize debug config
2. **[Run Your First Debug Case](quick-start/basic-setup.md)** - Test the system
3. **[Enable Tracing in Your Code](quick-start/patterns.md)** - Add to your application
4. **[Analyze Your First Trace](analysis/trace-analysis.md)** - Understand the output

---

**The LangSwarm Debug & Tracing System provides the visibility you need to understand, debug, and optimize complex multi-agent workflows while maintaining production safety and performance.**
