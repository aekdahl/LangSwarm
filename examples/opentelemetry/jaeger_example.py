#!/usr/bin/env python3
"""
LangSwarm OpenTelemetry + Jaeger Integration Example

This example demonstrates how to configure LangSwarm to export traces
to Jaeger for distributed tracing visualization.

Prerequisites:
1. Install LangSwarm with OpenTelemetry support:
   pip install langswarm[opentelemetry]

2. Start Jaeger (using Docker):
   docker run -d --name jaeger \
     -p 16686:16686 \
     -p 14268:14268 \
     -p 4317:4317 \
     jaegertracing/all-in-one:latest

3. View traces at: http://localhost:16686
"""

import asyncio
import logging
from datetime import datetime

from langswarm.core.observability import (
    ObservabilityProvider,
    ObservabilityConfig,
    LogLevel
)

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function"""
    
    # Configure observability with Jaeger integration
    config = ObservabilityConfig(
        # Basic observability settings
        enabled=True,
        log_level=LogLevel.INFO,
        tracing_enabled=True,
        metrics_enabled=True,
        
        # OpenTelemetry + Jaeger configuration
        opentelemetry_enabled=True,
        opentelemetry_service_name="langswarm-jaeger-example",
        opentelemetry_service_version="1.0.0",
        
        # Jaeger endpoint (adjust if Jaeger is running elsewhere)
        opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
        
        # Optional: Also enable OTLP for Jaeger's OTLP receiver
        # opentelemetry_otlp_endpoint="http://localhost:4317",
    )
    
    # Initialize observability provider
    provider = ObservabilityProvider(config)
    await provider.start()
    
    logger.info("🚀 Starting LangSwarm with Jaeger tracing")
    logger.info("📊 View traces at: http://localhost:16686")
    
    try:
        # Simulate some LangSwarm operations with tracing
        await simulate_agent_operations(provider)
        await simulate_workflow_execution(provider)
        await simulate_tool_usage(provider)
        
    finally:
        # Ensure all traces are flushed to Jaeger
        await provider.flush()
        await provider.stop()
        logger.info("✅ Example completed - check Jaeger UI for traces!")


async def simulate_agent_operations(provider):
    """Simulate agent operations that will be traced"""
    
    # Use the tracer to create spans
    with provider.tracer.start_span("agent.chat_request") as span:
        span.add_tag("agent_type", "conversational")
        span.add_tag("user_id", "user_123")
        
        provider.logger.info("Processing chat request", 
                           component="agent",
                           operation="chat")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Nested operation
        with provider.tracer.start_span("agent.generate_response") as nested_span:
            nested_span.add_tag("model", "gpt-4")
            nested_span.add_tag("tokens", 150)
            
            provider.logger.info("Generating response",
                               component="agent", 
                               operation="generate")
            
            # Simulate LLM call
            await asyncio.sleep(0.5)
            
            # Record metrics
            provider.metrics.increment_counter("agent.requests.total", 
                                             agent_type="conversational")
            provider.metrics.record_histogram("agent.response_time", 0.6,
                                            model="gpt-4")
        
        span.add_tag("response_length", 256)
        provider.logger.info("Chat request completed",
                           component="agent",
                           operation="complete")


async def simulate_workflow_execution(provider):
    """Simulate workflow execution with multiple steps"""
    
    with provider.tracer.start_span("workflow.execute") as span:
        span.add_tag("workflow_id", "workflow_456")
        span.add_tag("workflow_type", "data_processing")
        
        provider.logger.info("Starting workflow execution",
                           component="workflow",
                           operation="execute")
        
        # Simulate workflow steps
        steps = ["validate_input", "process_data", "generate_output"]
        
        for i, step in enumerate(steps):
            with provider.tracer.start_span(f"workflow.step.{step}") as step_span:
                step_span.add_tag("step_number", i + 1)
                step_span.add_tag("step_name", step)
                
                provider.logger.info(f"Executing step: {step}",
                                   component="workflow",
                                   operation="step")
                
                # Simulate step processing
                await asyncio.sleep(0.2)
                
                # Record step metrics
                provider.metrics.increment_counter("workflow.steps.completed",
                                                 step=step)
        
        provider.logger.info("Workflow execution completed",
                           component="workflow", 
                           operation="complete")


async def simulate_tool_usage(provider):
    """Simulate tool usage operations"""
    
    tools = ["web_search", "calculator", "file_reader"]
    
    for tool in tools:
        with provider.tracer.start_span(f"tool.{tool}.execute") as span:
            span.add_tag("tool_name", tool)
            span.add_tag("tool_version", "1.0")
            
            provider.logger.info(f"Executing tool: {tool}",
                               component="tool",
                               operation="execute")
            
            try:
                # Simulate tool execution
                if tool == "web_search":
                    span.add_tag("query", "OpenTelemetry best practices")
                    await asyncio.sleep(0.3)
                    span.add_tag("results_count", 10)
                    
                elif tool == "calculator":
                    span.add_tag("expression", "2 + 2")
                    await asyncio.sleep(0.1)
                    span.add_tag("result", 4)
                    
                elif tool == "file_reader":
                    span.add_tag("file_path", "/tmp/example.txt")
                    await asyncio.sleep(0.2)
                    span.add_tag("file_size", 1024)
                
                # Record success metrics
                provider.metrics.increment_counter("tool.executions.total",
                                                 tool=tool, status="success")
                
                provider.logger.info(f"Tool {tool} completed successfully",
                                   component="tool",
                                   operation="complete")
                
            except Exception as e:
                # Handle errors (simulate occasional failures)
                span.add_tag("error", True)
                span.add_tag("error_message", str(e))
                
                provider.metrics.increment_counter("tool.executions.total",
                                                 tool=tool, status="error")
                
                provider.logger.error(f"Tool {tool} failed: {e}",
                                    component="tool",
                                    operation="error")


if __name__ == "__main__":
    print("🔍 LangSwarm + Jaeger Tracing Example")
    print("=" * 50)
    print("This example will:")
    print("1. Configure LangSwarm with Jaeger tracing")
    print("2. Simulate various operations (agent, workflow, tools)")
    print("3. Export traces to Jaeger")
    print()
    print("📊 View traces at: http://localhost:16686")
    print("🐳 Make sure Jaeger is running (see docstring for Docker command)")
    print()
    
    asyncio.run(main())
