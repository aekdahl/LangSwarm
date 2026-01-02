# V2 Debug Tracing Specification

## Overview

The V2 debug tracing system should provide comprehensive visibility into the complete agent interaction flow, from initial user query to final response. This document outlines the required tracing capabilities for debugging, development, and production monitoring.

## Core Tracing Requirements

### 1. **User Interaction Tracing**
```json
{
  "trace_id": "uuid-v4",
  "timestamp": "2025-09-27T10:50:15.123Z",
  "level": "USER_INTERACTION",
  "event": "query_received",
  "data": {
    "user_id": "user_123",
    "session_id": "session_456",
    "query": "Search for information about Pingday",
    "context": {
      "conversation_history": [...],
      "user_preferences": {...}
    }
  }
}
```

### 2. **Agent Processing Tracing**
```json
{
  "trace_id": "uuid-v4",
  "parent_span_id": "span_001",
  "span_id": "span_002",
  "timestamp": "2025-09-27T10:50:15.125Z",
  "level": "AGENT_PROCESSING", 
  "event": "agent_invoked",
  "data": {
    "agent_name": "search_agent",
    "agent_provider": "openai",
    "agent_model": "gpt-4o",
    "system_prompt": "You are a helpful search assistant...",
    "tools_available": ["bigquery_vector_search"],
    "configuration": {
      "temperature": 0.7,
      "max_tokens": 1500,
      "tools_enabled": true
    }
  }
}
```

### 3. **Middleware Interception Tracing**
```json
{
  "trace_id": "uuid-v4",
  "span_id": "span_003",
  "timestamp": "2025-09-27T10:50:15.130Z",
  "level": "MIDDLEWARE",
  "event": "interceptor_triggered",
  "data": {
    "interceptor_type": "routing",
    "interceptor_name": "RoutingInterceptor",
    "action": "route_to_tool_executor",
    "input": {
      "request_type": "tool_call",
      "tool_name": "bigquery_vector_search"
    },
    "output": {
      "route_decision": "tool_execution_pipeline",
      "execution_context": {...}
    },
    "processing_time_ms": 2.5
  }
}
```

### 4. **Tool Execution Tracing**
```json
{
  "trace_id": "uuid-v4",
  "span_id": "span_004",
  "timestamp": "2025-09-27T10:50:15.135Z",
  "level": "TOOL_EXECUTION",
  "event": "tool_called",
  "data": {
    "tool_name": "bigquery_vector_search",
    "tool_method": "similarity_search",
    "tool_type": "mcp",
    "parameters": {
      "query": "Pingday",
      "limit": 5,
      "similarity_threshold": 0.01
    },
    "execution_context": {
      "user_id": "user_123",
      "session_id": "session_456",
      "workflow_id": "workflow_789"
    }
  }
}
```

### 5. **Tool Result Tracing**
```json
{
  "trace_id": "uuid-v4",
  "span_id": "span_004",
  "timestamp": "2025-09-27T10:50:15.890Z",
  "level": "TOOL_EXECUTION",
  "event": "tool_completed",
  "data": {
    "tool_name": "bigquery_vector_search",
    "success": true,
    "execution_time_ms": 755,
    "result_summary": {
      "results_count": 3,
      "max_similarity": 0.5667,
      "data_size_bytes": 1234
    },
    "full_result": {
      "success": true,
      "data": {
        "results": [
          {
            "similarity": 0.5667,
            "content": "Helsingborgs eget stadsnät...",
            "document_id": "d7de6e72..."
          }
        ]
      }
    },
    "performance_metrics": {
      "bigquery_job_id": "3a52e394-fb07-45d3-9ed1-e54266c7292a",
      "bytes_processed": 431988,
      "cache_hit": true
    }
  }
}
```

### 6. **Agent Response Generation Tracing**
```json
{
  "trace_id": "uuid-v4",
  "span_id": "span_005",
  "timestamp": "2025-09-27T10:50:16.100Z",
  "level": "AGENT_PROCESSING",
  "event": "response_generated",
  "data": {
    "agent_name": "search_agent",
    "tool_results_processed": [
      {
        "tool": "bigquery_vector_search",
        "results_count": 3,
        "integration_status": "success"
      }
    ],
    "llm_request": {
      "model": "gpt-4o",
      "messages": [
        {
          "role": "system",
          "content": "You are a helpful search assistant..."
        },
        {
          "role": "user", 
          "content": "Search for information about Pingday"
        },
        {
          "role": "function",
          "name": "bigquery_vector_search",
          "content": "Found 3 results about Pingday..."
        }
      ],
      "temperature": 0.7
    },
    "llm_response": {
      "content": "I found information about Pingday...",
      "usage": {
        "prompt_tokens": 450,
        "completion_tokens": 120,
        "total_tokens": 570
      },
      "processing_time_ms": 210
    }
  }
}
```

### 7. **Final Response Tracing**
```json
{
  "trace_id": "uuid-v4",
  "span_id": "span_006",
  "timestamp": "2025-09-27T10:50:16.120Z",
  "level": "USER_INTERACTION",
  "event": "response_delivered",
  "data": {
    "user_id": "user_123",
    "session_id": "session_456",
    "final_response": {
      "content": "I found information about Pingday. Based on the search results, Pingday appears to be related to Helsingborg's city network...",
      "metadata": {
        "tools_used": ["bigquery_vector_search"],
        "sources": ["d7de6e72..."],
        "confidence": 0.85
      }
    },
    "total_processing_time_ms": 995,
    "cost_breakdown": {
      "llm_cost_usd": 0.00234,
      "tool_cost_usd": 0.00012,
      "total_cost_usd": 0.00246
    }
  }
}
```

## Debug Trace Levels

### Level 1: **Summary** (Production Default)
- User query received
- Tools executed (name + success/failure)
- Final response delivered
- Total processing time
- Cost breakdown

### Level 2: **Standard** (Development Default)
- All Level 1 events
- Agent invocation details
- Middleware routing decisions
- Tool parameter validation
- Performance metrics

### Level 3: **Detailed** (Debug/Troubleshooting)
- All Level 2 events
- Complete LLM request/response payloads
- Full tool result data
- Middleware interception details
- Memory usage tracking

### Level 4: **Verbose** (Deep Debugging)
- All Level 3 events
- Step-by-step middleware pipeline execution
- Registry lookups and tool discovery
- Configuration resolution details
- Error stack traces and recovery attempts

## Implementation Features

### 1. **Trace Correlation**
```python
class TraceContext:
    trace_id: str
    parent_span_id: Optional[str]
    span_id: str
    user_id: str
    session_id: str
    workflow_id: Optional[str]
    
    def create_child_span(self) -> 'TraceContext':
        """Create child span for nested operations"""
        
    def add_metadata(self, key: str, value: Any) -> None:
        """Add contextual metadata to trace"""
```

### 2. **Structured Trace Output**
```python
class TraceOutput:
    def json_lines(self) -> str:
        """JSONL format for log analysis"""
        
    def human_readable(self) -> str:
        """Pretty-printed format for debugging"""
        
    def performance_summary(self) -> Dict[str, Any]:
        """Performance metrics summary"""
```

### 3. **Trace Filtering and Search**
```python
class TraceFilter:
    def by_user(self, user_id: str) -> List[TraceEvent]:
        """Filter traces by user"""
        
    def by_time_range(self, start: datetime, end: datetime) -> List[TraceEvent]:
        """Filter traces by time range"""
        
    def by_tool(self, tool_name: str) -> List[TraceEvent]:
        """Filter traces by tool usage"""
        
    def by_error(self) -> List[TraceEvent]:
        """Filter traces with errors"""
```

### 4. **Real-time Trace Streaming**
```python
class TraceStreamer:
    def stream_to_console(self, level: TraceLevel = TraceLevel.STANDARD):
        """Stream traces to console in real-time"""
        
    def stream_to_file(self, filepath: str, format: str = "jsonl"):
        """Stream traces to file"""
        
    def stream_to_websocket(self, ws_endpoint: str):
        """Stream traces to WebSocket for real-time monitoring"""
```

## Debug Scenarios

### Scenario 1: **Agent Tool Call Flow**
**Use Case**: Debug why agent is not calling expected tools
**Required Traces**:
- Agent system prompt with tool definitions
- LLM tool calling decision process
- Tool parameter validation
- Tool execution success/failure
- Response integration

### Scenario 2: **Performance Analysis**
**Use Case**: Optimize slow agent responses
**Required Traces**:
- Time breakdown by component (LLM, tools, middleware)
- Tool execution performance metrics
- Memory usage patterns
- Cost analysis

### Scenario 3: **Error Debugging**
**Use Case**: Diagnose tool execution failures
**Required Traces**:
- Error propagation through middleware
- Retry attempts and backoff strategies
- Fallback mechanism activation
- Error context and stack traces

### Scenario 4: **Workflow Analysis**
**Use Case**: Debug complex multi-step workflows
**Required Traces**:
- Workflow step execution order
- Data flow between steps
- Conditional logic evaluation
- Parallel execution coordination

## Configuration

### Environment Variables
```bash
# Trace level configuration
LANGSWARM_TRACE_LEVEL=STANDARD  # SUMMARY|STANDARD|DETAILED|VERBOSE

# Output configuration
LANGSWARM_TRACE_OUTPUT=console  # console|file|both
LANGSWARM_TRACE_FILE=debug/traces/langswarm_%Y%m%d_%H%M%S.jsonl

# Filtering configuration
LANGSWARM_TRACE_INCLUDE_TOOLS=bigquery_vector_search,web_search
LANGSWARM_TRACE_EXCLUDE_USERS=system,internal
```

### Programmatic Configuration
```python
from langswarm.observability import configure_tracing

configure_tracing(
    level=TraceLevel.DETAILED,
    outputs=[ConsoleOutput(), FileOutput("traces.jsonl")],
    filters=[ExcludeUserFilter("system")],
    correlation_id_header="X-Correlation-ID"
)
```

## Integration Points

### 1. **Agent Integration**
```python
class BaseAgent:
    async def chat(self, message: str, trace_context: TraceContext) -> AgentResponse:
        with trace_context.create_span("agent_processing") as span:
            span.log("agent_invoked", {"message": message})
            # ... processing ...
            span.log("response_generated", {"response": response})
            return response
```

### 2. **Tool Integration**
```python
class ToolExecutor:
    async def execute(self, tool: IToolInterface, method: str, parameters: Dict) -> ExecutionResult:
        with TraceContext.current().create_span("tool_execution") as span:
            span.log("tool_called", {
                "tool": tool.metadata.name,
                "method": method,
                "parameters": parameters
            })
            # ... execution ...
            span.log("tool_completed", {"result": result})
            return result
```

### 3. **Middleware Integration**
```python
class MiddlewareInterceptor:
    async def intercept(self, request: MiddlewareRequest) -> MiddlewareResponse:
        with TraceContext.current().create_span("middleware_intercept") as span:
            span.log("interceptor_triggered", {"type": self.type})
            # ... processing ...
            span.log("interceptor_completed", {"action": action})
            return response
```

## Future Enhancements

### Phase 1: **Basic Implementation**
- [ ] Core tracing infrastructure
- [ ] Agent and tool integration
- [ ] Console and file output
- [ ] Basic filtering

### Phase 2: **Advanced Features**
- [ ] Real-time streaming
- [ ] Performance analytics
- [ ] Cost tracking
- [ ] Error correlation

### Phase 3: **Production Features**
- [ ] Distributed tracing
- [ ] Sampling strategies
- [ ] Retention policies
- [ ] Alert integration

### Phase 4: **Monitoring Dashboard**
- [ ] Web-based trace viewer
- [ ] Performance dashboards
- [ ] Real-time monitoring
- [ ] Automated anomaly detection

## Example Debug Session

```bash
# Start debug session with detailed tracing
langswarm debug --trace-level detailed --query "Search for Pingday information"

# Output:
[10:50:15.123] USER_INTERACTION | query_received | user_123 | "Search for Pingday information"
[10:50:15.125] AGENT_PROCESSING | agent_invoked | search_agent (openai/gpt-4o)
[10:50:15.130] MIDDLEWARE | routing_interceptor | route_to_tool_executor
[10:50:15.135] TOOL_EXECUTION | tool_called | bigquery_vector_search.similarity_search
[10:50:15.890] TOOL_EXECUTION | tool_completed | success | 3 results | 755ms
[10:50:16.100] AGENT_PROCESSING | response_generated | 570 tokens | 210ms  
[10:50:16.120] USER_INTERACTION | response_delivered | 995ms total | $0.00246

# Filter traces by tool
langswarm trace filter --tool bigquery_vector_search --last 1h

# Performance analysis
langswarm trace analyze --performance --group-by tool
```

This specification provides a comprehensive framework for implementing debug tracing that will give complete visibility into the V2 agent interaction flow.

