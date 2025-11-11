"""
LangSwarm Debug and Tracing System

Comprehensive, production-safe debugging and tracing for LangSwarm applications.

🔒 PRODUCTION SAFETY:
- Debug tracing is DISABLED by default (negligible overhead)
- 0.000023ms per operation when disabled
- 34% performance impact when enabled (emergency use only)

📚 DOCUMENTATION:
- Quick Reference: docs/debug-quick-reference.md
- Complete Guide: docs/debug-tracing-system.md  
- Configuration: docs/debug-configuration.md

🚀 QUICK START:

Emergency Production Debugging:
```python
from langswarm.v1.core.debug import enable_debug_tracing, disable_debug_tracing

# Enable (34% performance hit - emergency only!)
enable_debug_tracing("emergency.jsonl")

# Your LangSwarm code - now automatically traced
agent = MyAgent()
response = agent.chat("debug this issue")  # ← Logged with full context

# Disable when done
disable_debug_tracing()
```

Safe Production Pattern:
```python
import os
from langswarm.v1.core.debug import enable_debug_tracing

# Safe for production deployment
if os.getenv('LANGSWARM_DEBUG') == 'true':
    enable_debug_tracing("app_debug.jsonl")

# Your app runs normally (traced if debug enabled, ignored if disabled)
```

Ready-Made Debug Cases:
```bash
# CLI commands for instant debugging
python -m langswarm.core.debug.cli run-case-1  # Simple agent
python -m langswarm.core.debug.cli run-case-3  # BigQuery tool
python -m langswarm.core.debug.cli show-config # Check setup
```

Custom Tracing:
```python
from langswarm.v1.core.debug import get_debug_tracer

tracer = get_debug_tracer()
if tracer and tracer.enabled:
    with tracer.trace_operation("my_component", "my_operation", "Doing work"):
        # Your code - gets START/END events with timing
        do_work()
```

COMPONENTS TRACED:
- 🤖 Agent calls (chat, memory, sessions)
- 🛠️ Tool execution (MCP, parameters, responses)  
- ⚙️ Config loading (agents, tools, initialization)
- 📋 Workflows (step execution, routing, errors)

TRACE OUTPUT:
- 📁 Real-time JSON logs to local files
- 🔗 Hierarchical trace_id/span_id relationships
- 📊 Performance metrics and timing data
- 🐛 Error isolation with source locations
- 📈 Rich contextual data for analysis

See docs/debug-tracing-system.md for complete documentation.
"""

from .tracer import (
    initialize_debug_tracer,
    get_debug_tracer,
    trace_event,
    trace_operation,
    traced,
    DebugTracer,
    TraceEvent
)

from .integration import (
    enable_debug_tracing,
    disable_debug_tracing,
    TracingMixin
)

from .critical_failures import (
    initialize_failure_handler,
    handle_critical_failure,
    is_critical_error,
    get_failure_handler,
    CriticalFailureHandler,
    FailureType,
    FailureInfo
)

from .debug_cases import (
    run_case_1,
    run_case_2, 
    run_case_3,
    run_case_4,
    run_all_basic_cases,
    TestCaseRunner,
    Case1SimpleAgent,
    Case2AgentWithMemory,
    Case3BigQueryTool,
    Case4AgentWithTools
)

from .config import (
    get_debug_config,
    validate_debug_config,
    create_sample_debug_config,
    set_debug_environment_variables,
    DebugConfig,
    DebugConfigManager
)

__all__ = [
    # Core tracing
    'initialize_debug_tracer',
    'get_debug_tracer',
    'trace_event',
    'trace_operation', 
    'traced',
    'DebugTracer',
    'TraceEvent',
    
    # Integration
    'enable_debug_tracing',
    'disable_debug_tracing',
    'TracingMixin',
    
    # Critical failure handling
    'initialize_failure_handler',
    'handle_critical_failure',
    'is_critical_error',
    'get_failure_handler',
    'CriticalFailureHandler',
    'FailureType',
    'FailureInfo',
    
    # Debug cases
    'run_case_1',
    'run_case_2',
    'run_case_3',
    'run_case_4',
    'run_all_basic_cases',
    'TestCaseRunner',
    'Case1SimpleAgent',
    'Case2AgentWithMemory',
    'Case3BigQueryTool',
    'Case4AgentWithTools',
    
    # Configuration
    'get_debug_config',
    'validate_debug_config', 
    'create_sample_debug_config',
    'set_debug_environment_variables',
    'DebugConfig',
    'DebugConfigManager'
]
