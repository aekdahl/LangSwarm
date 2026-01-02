# LangSwarm Debugging & Tracing Guide

## 🚀 Quick Start (Emergency Debugging)

**Debug tracing is DISABLED by default**. To enable it for emergency debugging:

```python
from langswarm.core.debug import enable_debug_tracing, disable_debug_tracing

# 1. Enable tracing (34% performance impact)
enable_debug_tracing("emergency_trace.jsonl")

# 2. Run your code (it will be automatically traced)
agent.chat("debug this issue")

# 3. Disable when done
disable_debug_tracing()
```

### CLI Quick Commands

```bash
# Initialize configuration
python -m langswarm.core.debug.cli init-config

# Run a test case
python -m langswarm.core.debug.cli run-case-1

# Analyze a trace file
python -m langswarm.core.debug.cli detail emergency_trace.jsonl
```

---

## 🔍 Overview

The LangSwarm Debug and Tracing System provides comprehensive, structured logging and tracing capabilities. It is designed to be **production-safe**, meaning it has zero performance overhead when disabled.

**Key Features:**
- **Hierarchical Tracing**: Nested operations (Agents -> Workflows -> Tools).
- **Structured JSON**: Machine-readable logs (`.jsonl`).
- **Production Safe**: Negligible overhead when disabled (`0.000023ms`/call).

---

## ⚙️ Configuration

### 1. Configuration File
The system looks for `debug_config.yaml` in the current directory or `~/.langswarm/`.

```yaml
# OpenAI (Required)
openai:
  api_key: sk-your-key
  model: gpt-4o

# Google Cloud (For BigQuery Tools)
google_cloud:
  project_id: your-project-id

# Output Settings
output_dir: debug_traces
log_level: INFO
```

### 2. Environment Variables
Environment variables override configuration files:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API Key |
| `LANGSWARM_DEBUG` | Set to `true` to enable tracing globally |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID |

---

## 🏭 Production Pattern

To safely instrument production applications:

```python
import os
from langswarm.core.debug import enable_debug_tracing

# Only enable if env var is set
if os.getenv('LANGSWARM_DEBUG') == 'true':
    # Log to a volume or temp path
    enable_debug_tracing("/var/log/langswarm/debug.jsonl")
    print("🔍 Debug tracing enabled")

# Your application code runs normally
```

---

## 📊 Trace Analysis

Traces are saved as JSON Lines (`.jsonl`). Each line is a JSON object representing an event (Start, End, Info, Error).

### Example Event
```json
{
  "trace_id": "abc123",
  "component": "agent", 
  "operation": "chat",
  "event_type": "END",
  "duration_ms": 1250,
  "data": {
    "response": "Hello world"
  }
}
```

### Analyzing with CLI
```bash
# Get a summary of the trace
python -m langswarm.core.debug.cli summary trace.jsonl

# View detailed hierarchy
python -m langswarm.core.debug.cli detail trace.jsonl
```

### Analyzing with `jq`
```bash
# Find all errors
jq 'select(.level == "ERROR")' trace.jsonl

# Operations taking > 1s
jq 'select(.duration_ms > 1000)' trace.jsonl
```

---

## 🏗️ Architecture & Internals

When enabled, the tracers monkey-patch key components:

1.  **AgentWrapper**: Traces `chat()` calls.
2.  **WorkflowExecutor**: Traces workflow steps.
3.  **Middleware**: Traces tool execution and parameter validation.

Because these patches are only applied when `enable_debug_tracing()` is called, the system remains lightweight by default.

---

## ❓ Troubleshooting

-   **Files not appearing?** Check `output_dir` permissions or if `disable_debug_tracing()` was called early.
-   **Performance slow?** Ensure you are NOT running with debug enabled in high-throughput production (overhead is ~34%).
-   **Config not found?** Run `python -m langswarm.core.debug.cli validate-config` to check paths.
