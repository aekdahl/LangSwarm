#!/usr/bin/env python3
"""
LangSwarm OpenTelemetry + Prometheus Integration Example

This example demonstrates how to configure LangSwarm to export metrics
to Prometheus for monitoring and alerting.

Prerequisites:
1. Install LangSwarm with OpenTelemetry support:
   pip install langswarm[opentelemetry]

2. Start Prometheus (using Docker):
   docker run -d --name prometheus \
     -p 9090:9090 \
     -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
     prom/prometheus

3. Create prometheus.yml with this content:
   global:
     scrape_interval: 15s
   scrape_configs:
     - job_name: 'langswarm'
       static_configs:
         - targets: ['host.docker.internal:8000']

4. View metrics at: http://localhost:9090
"""

import asyncio
import logging
import random
from datetime import datetime

from langswarm.core.observability import (
    ObservabilityProvider,
    ObservabilityConfig,
    LogLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function"""
    
    # Configure observability with Prometheus integration
    config = ObservabilityConfig(
        # Basic observability settings
        enabled=True,
        log_level=LogLevel.INFO,
        tracing_enabled=True,
        metrics_enabled=True,
        
        # OpenTelemetry + Prometheus configuration
        opentelemetry_enabled=True,
        opentelemetry_service_name="langswarm-prometheus-example",
        opentelemetry_service_version="1.0.0",
        
        # Prometheus metrics endpoint
        opentelemetry_prometheus_enabled=True,
        opentelemetry_prometheus_port=8000,
        opentelemetry_prometheus_host="0.0.0.0",
    )
    
    # Initialize observability provider
    provider = ObservabilityProvider(config)
    await provider.start()
    
    logger.info("🚀 Starting LangSwarm with Prometheus metrics")
    logger.info("📊 Metrics available at: http://localhost:8000/metrics")
    logger.info("📈 View in Prometheus at: http://localhost:9090")
    
    try:
        # Generate metrics continuously
        logger.info("🔄 Generating metrics... (Press Ctrl+C to stop)")
        
        # Run for a while to generate interesting metrics
        for i in range(100):
            await generate_agent_metrics(provider, i)
            await generate_workflow_metrics(provider, i)
            await generate_tool_metrics(provider, i)
            await generate_system_metrics(provider, i)
            
            # Wait between iterations
            await asyncio.sleep(2)
            
            if i % 10 == 0:
                logger.info(f"📊 Generated {i * 4} metric batches...")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Stopping metric generation...")
    
    finally:
        # Keep the server running briefly to allow final scraping
        logger.info("🔄 Keeping metrics endpoint alive for final scraping...")
        await asyncio.sleep(5)
        
        await provider.flush()
        await provider.stop()
        logger.info("✅ Example completed!")


async def generate_agent_metrics(provider, iteration):
    """Generate agent-related metrics"""
    
    # Simulate different agent types and their performance
    agent_types = ["conversational", "analytical", "creative", "technical"]
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "llama-2"]
    
    for agent_type in agent_types:
        model = random.choice(models)
        
        # Request count (counter)
        provider.metrics.increment_counter(
            "langswarm_agent_requests_total",
            agent_type=agent_type,
            model=model,
            status="success" if random.random() > 0.1 else "error"
        )
        
        # Response time (histogram)
        response_time = random.uniform(0.5, 3.0)  # 0.5-3 seconds
        provider.metrics.record_histogram(
            "langswarm_agent_response_time_seconds",
            response_time,
            agent_type=agent_type,
            model=model
        )
        
        # Token usage (histogram)
        tokens = random.randint(50, 2000)
        provider.metrics.record_histogram(
            "langswarm_agent_tokens_used",
            tokens,
            agent_type=agent_type,
            model=model,
            operation="completion"
        )
        
        # Cost tracking (histogram)
        cost = tokens * 0.00002  # Rough cost calculation
        provider.metrics.record_histogram(
            "langswarm_agent_cost_usd",
            cost,
            agent_type=agent_type,
            model=model
        )
    
    # Active agents (gauge)
    active_agents = random.randint(5, 20)
    provider.metrics.set_gauge(
        "langswarm_active_agents",
        active_agents
    )


async def generate_workflow_metrics(provider, iteration):
    """Generate workflow-related metrics"""
    
    workflow_types = ["data_processing", "content_generation", "analysis", "automation"]
    
    for workflow_type in workflow_types:
        # Workflow executions (counter)
        provider.metrics.increment_counter(
            "langswarm_workflow_executions_total",
            workflow_type=workflow_type,
            status="completed" if random.random() > 0.05 else "failed"
        )
        
        # Workflow duration (histogram)
        duration = random.uniform(10, 300)  # 10 seconds to 5 minutes
        provider.metrics.record_histogram(
            "langswarm_workflow_duration_seconds",
            duration,
            workflow_type=workflow_type
        )
        
        # Steps per workflow (histogram)
        steps = random.randint(3, 15)
        provider.metrics.record_histogram(
            "langswarm_workflow_steps_count",
            steps,
            workflow_type=workflow_type
        )
    
    # Active workflows (gauge)
    active_workflows = random.randint(2, 10)
    provider.metrics.set_gauge(
        "langswarm_active_workflows",
        active_workflows
    )


async def generate_tool_metrics(provider, iteration):
    """Generate tool usage metrics"""
    
    tools = [
        "web_search", "calculator", "file_reader", "database_query",
        "image_generator", "code_executor", "email_sender", "api_caller"
    ]
    
    for tool in tools:
        # Tool usage (counter)
        success_rate = 0.95 if tool != "api_caller" else 0.85  # API calls fail more
        status = "success" if random.random() < success_rate else "error"
        
        provider.metrics.increment_counter(
            "langswarm_tool_executions_total",
            tool=tool,
            status=status
        )
        
        # Tool execution time (histogram)
        if tool == "web_search":
            exec_time = random.uniform(1.0, 5.0)
        elif tool == "database_query":
            exec_time = random.uniform(0.1, 2.0)
        elif tool == "image_generator":
            exec_time = random.uniform(5.0, 30.0)
        else:
            exec_time = random.uniform(0.1, 1.0)
        
        provider.metrics.record_histogram(
            "langswarm_tool_execution_time_seconds",
            exec_time,
            tool=tool
        )
        
        # Tool result size (histogram) - in bytes
        result_size = random.randint(100, 10000)
        provider.metrics.record_histogram(
            "langswarm_tool_result_size_bytes",
            result_size,
            tool=tool
        )
    
    # Tool cache hit rate (gauge)
    cache_hit_rate = random.uniform(0.6, 0.9)
    provider.metrics.set_gauge(
        "langswarm_tool_cache_hit_rate",
        cache_hit_rate
    )


async def generate_system_metrics(provider, iteration):
    """Generate system-level metrics"""
    
    # Memory usage (gauge) - in MB
    memory_usage = random.uniform(100, 500)
    provider.metrics.set_gauge(
        "langswarm_memory_usage_mb",
        memory_usage
    )
    
    # CPU usage (gauge) - percentage
    cpu_usage = random.uniform(10, 80)
    provider.metrics.set_gauge(
        "langswarm_cpu_usage_percent",
        cpu_usage
    )
    
    # Active sessions (gauge)
    active_sessions = random.randint(10, 100)
    provider.metrics.set_gauge(
        "langswarm_active_sessions",
        active_sessions
    )
    
    # Queue sizes (gauge)
    for queue_type in ["task_queue", "message_queue", "result_queue"]:
        queue_size = random.randint(0, 50)
        provider.metrics.set_gauge(
            "langswarm_queue_size",
            queue_size,
            queue_type=queue_type
        )
    
    # Error rate (gauge)
    error_rate = random.uniform(0.01, 0.05)  # 1-5% error rate
    provider.metrics.set_gauge(
        "langswarm_error_rate",
        error_rate
    )
    
    # Throughput (counter)
    requests_per_minute = random.randint(50, 200)
    provider.metrics.increment_counter(
        "langswarm_requests_per_minute",
        requests_per_minute
    )


if __name__ == "__main__":
    print("📊 LangSwarm + Prometheus Metrics Example")
    print("=" * 50)
    print("This example will:")
    print("1. Configure LangSwarm with Prometheus metrics")
    print("2. Generate realistic metrics for agents, workflows, tools, and system")
    print("3. Expose metrics on port 8000 for Prometheus scraping")
    print()
    print("📈 Metrics endpoint: http://localhost:8000/metrics")
    print("🐳 Make sure Prometheus is running and configured to scrape localhost:8000")
    print("📊 View metrics in Prometheus at: http://localhost:9090")
    print()
    print("Example Prometheus queries to try:")
    print("- rate(langswarm_agent_requests_total[5m])")
    print("- histogram_quantile(0.95, langswarm_agent_response_time_seconds)")
    print("- langswarm_active_agents")
    print("- sum by (tool) (rate(langswarm_tool_executions_total[5m]))")
    print()
    
    asyncio.run(main())
