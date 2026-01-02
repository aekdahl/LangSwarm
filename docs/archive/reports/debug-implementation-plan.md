# V2 Debug Tracing Implementation Plan

## Current State Analysis

### What We Have Now
- Basic BigQuery tool execution logging
- Raw tool output display
- Environment variable validation
- Simple success/failure reporting

### What's Missing
- **Agent interaction tracing**: No visibility into agent decision-making
- **Middleware pipeline visibility**: No insight into request routing
- **Tool call correlation**: Can't see full request → tool → response flow
- **Performance metrics**: No timing breakdown by component
- **Structured trace format**: Output is human-readable but not machine-parseable

## Implementation Phases

### Phase 1: **Core Trace Infrastructure** (Week 1)

#### 1.1 Create Basic Trace Context
```python
# File: langswarm/v2/observability/trace_context.py
@dataclass
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def create_child_span(self, name: str) -> 'TraceContext':
        """Create child span for nested operations"""
        
    def log_event(self, level: str, event: str, data: Dict[str, Any]):
        """Log trace event"""
```

#### 1.2 Create Trace Event Logger
```python
# File: langswarm/v2/observability/trace_logger.py
class TraceLogger:
    def __init__(self, output_format: str = "console", level: str = "standard"):
        self.format = output_format
        self.level = level
        
    def log_user_query(self, trace_context: TraceContext, query: str):
        """Log initial user query"""
        
    def log_agent_invocation(self, trace_context: TraceContext, agent_config: Dict):
        """Log agent being invoked"""
        
    def log_tool_execution(self, trace_context: TraceContext, tool_name: str, params: Dict):
        """Log tool execution start"""
        
    def log_tool_result(self, trace_context: TraceContext, result: ExecutionResult):
        """Log tool execution completion"""
        
    def log_final_response(self, trace_context: TraceContext, response: str):
        """Log final response to user"""
```

#### 1.3 Update Debug Script Integration
```python
# File: debug/test_bigquery_simple.py - Enhanced Version
async def test_bigquery_with_tracing():
    """Test BigQuery with comprehensive tracing"""
    
    # Initialize trace context
    trace_context = TraceContext(
        trace_id=str(uuid.uuid4()),
        span_id="main_span",
        user_id="debug_user",
        session_id="debug_session"
    )
    
    # Initialize trace logger
    tracer = TraceLogger(output_format="console", level="detailed")
    
    # Log user query
    query = "vad är pingday"
    tracer.log_user_query(trace_context, query)
    
    # Test tool execution with tracing
    tool_span = trace_context.create_child_span("tool_execution")
    tracer.log_tool_execution(tool_span, "bigquery_vector_search", {"query": query})
    
    # Execute tool
    result = await execute_bigquery_tool(query)
    
    # Log result
    tracer.log_tool_result(tool_span, result)
    
    # Log final response
    tracer.log_final_response(trace_context, "Search completed with 3 results")
```

### Phase 2: **Agent Integration** (Week 2)

#### 2.1 Integrate with AgentBuilder
```python
# File: langswarm/v2/core/agents/base.py - Enhanced
class BaseAgent:
    async def chat(self, message: str, trace_context: Optional[TraceContext] = None) -> AgentResponse:
        if not trace_context:
            trace_context = TraceContext.create_new()
            
        agent_span = trace_context.create_child_span("agent_processing")
        
        tracer.log_agent_invocation(agent_span, {
            "agent_name": self.name,
            "provider": self.provider.type,
            "model": self.configuration.model,
            "tools_available": self.configuration.available_tools
        })
        
        # Process message through middleware
        response = await self.process_through_middleware(message, agent_span)
        
        tracer.log_agent_response(agent_span, response)
        return response
```

#### 2.2 Middleware Pipeline Tracing
```python
# File: langswarm/v2/core/middleware/base.py - Enhanced
class MiddlewareInterceptor:
    async def intercept(self, request: MiddlewareRequest, trace_context: TraceContext) -> MiddlewareResponse:
        middleware_span = trace_context.create_child_span(f"middleware_{self.name}")
        
        tracer.log_middleware_start(middleware_span, {
            "interceptor": self.name,
            "request_type": request.type,
            "input_size": len(str(request.data))
        })
        
        response = await self._process(request)
        
        tracer.log_middleware_complete(middleware_span, {
            "action_taken": response.action,
            "processing_time_ms": middleware_span.duration_ms
        })
        
        return response
```

### Phase 3: **Tool Execution Tracing** (Week 3)

#### 3.1 Enhanced Tool Executor
```python
# File: langswarm/v2/tools/execution.py - Enhanced
class ToolExecutor:
    async def execute(self, tool: IToolInterface, method: str, parameters: Dict, 
                     context: Optional[ExecutionContext] = None,
                     trace_context: Optional[TraceContext] = None) -> ExecutionResult:
        
        if not trace_context:
            trace_context = TraceContext.create_new()
            
        tool_span = trace_context.create_child_span("tool_execution")
        
        # Log tool execution start
        tracer.log_tool_start(tool_span, {
            "tool_name": tool.metadata.name,
            "tool_type": tool.metadata.type,
            "method": method,
            "parameters": parameters,
            "context": context.to_dict() if context else None
        })
        
        start_time = time.time()
        
        try:
            result = await self._execute_with_retry(tool, method, parameters, context)
            execution_time = (time.time() - start_time) * 1000
            
            tracer.log_tool_success(tool_span, {
                "result_summary": self._summarize_result(result),
                "execution_time_ms": execution_time,
                "success": result.success
            })
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            tracer.log_tool_error(tool_span, {
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_ms": execution_time
            })
            
            raise
```

### Phase 4: **Output Formatting & Analysis** (Week 4)

#### 4.1 Structured Output Formats
```python
# File: langswarm/v2/observability/formatters.py
class TraceFormatter:
    @staticmethod
    def console_output(events: List[TraceEvent]) -> str:
        """Human-readable console output with colors and hierarchy"""
        
    @staticmethod
    def jsonl_output(events: List[TraceEvent]) -> str:
        """JSONL format for log analysis tools"""
        
    @staticmethod
    def performance_summary(events: List[TraceEvent]) -> Dict[str, Any]:
        """Performance breakdown by component"""
```

#### 4.2 Enhanced Debug Script Output
```bash
# Expected enhanced output:
🎯 BigQuery Vector Search - V2 Agent Test (Trace: abc-123-def)
==================================================
📋 [10:50:15.123] USER_QUERY | "vad är pingday"
📋 [10:50:15.125] AGENT_START | search_agent (openai/gpt-4o) | tools: [bigquery_vector_search]
📋 [10:50:15.130] MIDDLEWARE | routing_interceptor → tool_execution_pipeline
📋 [10:50:15.135] TOOL_START | bigquery_vector_search.similarity_search
    ├─ Parameters: {"query": "vad är pingday", "limit": 3}
    ├─ Context: {user: debug_user, session: debug_session}
📋 [10:50:15.890] TOOL_COMPLETE | SUCCESS | 3 results | 755ms
    ├─ Top result: similarity=0.5667 "Helsingborgs eget stadsnät..."
    ├─ BigQuery job: 3a52e394-fb07 (cached)
📋 [10:50:16.100] AGENT_RESPONSE | Generated response from tool results | 210ms
📋 [10:50:16.120] FINAL_RESPONSE | "I found information about Pingday..."

⏱️  Performance Summary:
    ├─ Total time: 995ms
    ├─ Tool execution: 755ms (75.9%)
    ├─ Agent processing: 210ms (21.1%)  
    ├─ Middleware: 30ms (3.0%)
    
💰 Cost Breakdown:
    ├─ LLM costs: $0.00234
    ├─ Tool costs: $0.00012
    ├─ Total: $0.00246
```

## Integration with Current Debug System

### Immediate Updates Needed

#### 1. Update `debug/test_bigquery_simple.py`
```python
# Add tracing imports
from langswarm.observability import TraceContext, TraceLogger

# Enhance test functions with tracing
async def test_bigquery_with_agent_tracing():
    """Enhanced version with full trace visibility"""
    
    # Create trace context
    trace = TraceContext.create_new("debug_user", "debug_session")
    tracer = TraceLogger(level="detailed", output="console")
    
    # Log user query
    tracer.log_user_query(trace, "Search for Pingday information")
    
    # Test agent creation with tracing
    agent_span = trace.create_child_span("agent_creation")
    # ... existing agent creation code ...
    
    # Test tool execution with tracing  
    tool_span = trace.create_child_span("tool_test")
    # ... existing tool execution code ...
    
    # Performance summary
    tracer.log_performance_summary(trace)
```

#### 2. Update Makefile
```makefile
# Add trace level options
debug-bigquery-trace: check-bigquery-env
	@echo "🔍 BigQuery V2 Debug - Detailed Tracing"
	cd $(DEBUG_ROOT) && python test_bigquery_simple.py --trace-level detailed

debug-bigquery-performance: check-bigquery-env  
	@echo "⏱️ BigQuery V2 Debug - Performance Analysis"
	cd $(DEBUG_ROOT) && python test_bigquery_simple.py --trace-level performance
```

## Implementation Priority

### High Priority (Immediate)
1. **TraceContext and TraceLogger classes**
2. **Basic console output formatting**
3. **Integration with current debug script**
4. **Tool execution tracing**

### Medium Priority (Next Sprint)
1. **Agent interaction tracing**
2. **Middleware pipeline visibility**
3. **Performance metrics collection**
4. **JSONL output format**

### Lower Priority (Future)
1. **Real-time streaming**
2. **Web-based trace viewer**
3. **Distributed tracing**
4. **Alert integration**

This plan provides a clear roadmap for implementing comprehensive debug tracing while building incrementally on the working system we have now.

