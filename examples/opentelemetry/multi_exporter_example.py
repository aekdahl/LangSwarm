#!/usr/bin/env python3
"""
LangSwarm Multi-Exporter OpenTelemetry Example

This example demonstrates how to configure LangSwarm to export telemetry
data to multiple observability platforms simultaneously.

Prerequisites:
1. Install LangSwarm with OpenTelemetry support:
   pip install langswarm[opentelemetry]

2. Start observability stack (using Docker Compose):
   Create docker-compose.yml with Jaeger, Prometheus, and Grafana
   
3. This example exports to:
   - Jaeger (traces)
   - Prometheus (metrics)
   - OTLP endpoint (traces + metrics)
"""

import asyncio
import logging
import os
from datetime import datetime

from langswarm.core.observability import (
    ObservabilityProvider,
    ObservabilityConfig,
    LogLevel,
    TraceSpan,
    MetricPoint,
    MetricType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function demonstrating multi-exporter setup"""
    
    # Configure observability with multiple exporters
    config = ObservabilityConfig(
        # Basic observability settings
        enabled=True,
        log_level=LogLevel.INFO,
        tracing_enabled=True,
        metrics_enabled=True,
        
        # OpenTelemetry configuration
        opentelemetry_enabled=True,
        opentelemetry_service_name="langswarm-multi-exporter",
        opentelemetry_service_version="1.0.0",
        
        # Export to multiple destinations
        # 1. Jaeger for distributed tracing
        opentelemetry_jaeger_endpoint=os.getenv(
            "JAEGER_ENDPOINT", 
            "http://localhost:14268/api/traces"
        ),
        
        # 2. OTLP endpoint (could be another Jaeger, DataDog, etc.)
        opentelemetry_otlp_endpoint=os.getenv(
            "OTLP_ENDPOINT",
            "http://localhost:4317"
        ),
        opentelemetry_otlp_headers={
            "Authorization": f"Bearer {os.getenv('OTLP_TOKEN', 'demo-token')}",
            "X-Source": "langswarm-multi-example"
        },
        
        # 3. Prometheus for metrics
        opentelemetry_prometheus_enabled=True,
        opentelemetry_prometheus_port=int(os.getenv("PROMETHEUS_PORT", "8000")),
        opentelemetry_prometheus_host="0.0.0.0",
    )
    
    # Initialize observability provider
    provider = ObservabilityProvider(config)
    await provider.start()
    
    logger.info("🚀 Starting LangSwarm with multi-exporter OpenTelemetry")
    logger.info("📊 Exporting to:")
    logger.info(f"   - Jaeger: {config.opentelemetry_jaeger_endpoint}")
    logger.info(f"   - OTLP: {config.opentelemetry_otlp_endpoint}")
    logger.info(f"   - Prometheus: http://localhost:{config.opentelemetry_prometheus_port}/metrics")
    
    try:
        # Demonstrate comprehensive observability
        await demonstrate_comprehensive_tracing(provider)
        await demonstrate_custom_metrics(provider)
        await demonstrate_error_tracking(provider)
        await demonstrate_performance_monitoring(provider)
        
    finally:
        # Ensure all data is exported
        await provider.flush()
        await provider.stop()
        logger.info("✅ Multi-exporter example completed!")


async def demonstrate_comprehensive_tracing(provider):
    """Demonstrate comprehensive distributed tracing"""
    
    logger.info("🔍 Demonstrating comprehensive tracing...")
    
    # Create a complex trace with multiple nested spans
    with provider.tracer.start_span("user_request") as root_span:
        root_span.add_tag("user_id", "user_12345")
        root_span.add_tag("request_type", "complex_analysis")
        root_span.add_tag("priority", "high")
        
        # Authentication span
        with provider.tracer.start_span("authentication") as auth_span:
            auth_span.add_tag("auth_method", "jwt")
            await asyncio.sleep(0.1)  # Simulate auth check
            auth_span.add_tag("auth_result", "success")
        
        # Input validation span
        with provider.tracer.start_span("input_validation") as validation_span:
            validation_span.add_tag("input_size", 1024)
            validation_span.add_tag("validation_rules", 5)
            await asyncio.sleep(0.05)
            validation_span.add_tag("validation_result", "passed")
        
        # Main processing with parallel operations
        with provider.tracer.start_span("main_processing") as processing_span:
            processing_span.add_tag("processing_type", "parallel")
            
            # Simulate parallel operations
            tasks = []
            operations = ["data_analysis", "content_generation", "quality_check"]
            
            for operation in operations:
                task = asyncio.create_task(
                    simulate_operation(provider, operation)
                )
                tasks.append(task)
            
            # Wait for all operations to complete
            results = await asyncio.gather(*tasks)
            processing_span.add_tag("parallel_operations", len(operations))
            processing_span.add_tag("all_successful", all(results))
        
        # Response formatting
        with provider.tracer.start_span("response_formatting") as response_span:
            response_span.add_tag("format", "json")
            response_span.add_tag("compression", "gzip")
            await asyncio.sleep(0.02)
            response_span.add_tag("response_size", 2048)
        
        root_span.add_tag("total_operations", 6)
        root_span.add_tag("request_status", "completed")


async def simulate_operation(provider, operation_name):
    """Simulate an individual operation with tracing"""
    
    with provider.tracer.start_span(f"operation.{operation_name}") as span:
        span.add_tag("operation", operation_name)
        
        # Simulate different processing times and characteristics
        if operation_name == "data_analysis":
            span.add_tag("algorithm", "ml_classifier")
            span.add_tag("data_points", 10000)
            await asyncio.sleep(0.3)
            span.add_tag("accuracy", 0.95)
            
        elif operation_name == "content_generation":
            span.add_tag("model", "gpt-4")
            span.add_tag("tokens_generated", 500)
            await asyncio.sleep(0.8)
            span.add_tag("quality_score", 0.92)
            
        elif operation_name == "quality_check":
            span.add_tag("checks_performed", 8)
            await asyncio.sleep(0.1)
            span.add_tag("issues_found", 0)
        
        # Record operation metrics
        provider.metrics.increment_counter(
            "operations_completed",
            operation=operation_name,
            status="success"
        )
        
        return True


async def demonstrate_custom_metrics(provider):
    """Demonstrate custom metrics collection"""
    
    logger.info("📊 Demonstrating custom metrics...")
    
    # Business metrics
    provider.metrics.increment_counter(
        "business_events_total",
        event_type="user_signup",
        source="web_app",
        plan="premium"
    )
    
    provider.metrics.increment_counter(
        "business_events_total", 
        event_type="subscription_renewal",
        source="api",
        plan="enterprise"
    )
    
    # Performance metrics
    provider.metrics.record_histogram(
        "api_response_time_seconds",
        0.245,
        endpoint="/api/v1/analyze",
        method="POST",
        status_code="200"
    )
    
    provider.metrics.record_histogram(
        "database_query_duration_seconds",
        0.089,
        query_type="SELECT",
        table="user_data",
        index_used="true"
    )
    
    # Resource utilization
    provider.metrics.set_gauge(
        "memory_usage_bytes",
        1024 * 1024 * 256,  # 256 MB
        component="agent_pool"
    )
    
    provider.metrics.set_gauge(
        "connection_pool_size",
        25,
        pool_type="database",
        status="active"
    )
    
    # Custom business logic metrics
    provider.metrics.set_gauge(
        "active_user_sessions",
        142,
        region="us-west-2"
    )
    
    provider.metrics.record_histogram(
        "content_quality_score",
        0.87,
        content_type="article",
        ai_model="gpt-4"
    )


async def demonstrate_error_tracking(provider):
    """Demonstrate error tracking and monitoring"""
    
    logger.info("🚨 Demonstrating error tracking...")
    
    # Simulate various types of errors
    error_scenarios = [
        ("validation_error", "Invalid input format", False),
        ("timeout_error", "External API timeout", True),
        ("rate_limit_error", "API rate limit exceeded", True),
        ("internal_error", "Unexpected server error", False)
    ]
    
    for error_type, error_message, is_retryable in error_scenarios:
        with provider.tracer.start_span(f"error_scenario.{error_type}") as span:
            span.add_tag("error_type", error_type)
            span.add_tag("error_message", error_message)
            span.add_tag("is_retryable", is_retryable)
            span.add_tag("severity", "high" if not is_retryable else "medium")
            
            # Simulate error occurrence
            await asyncio.sleep(0.1)
            
            # Mark span as error
            span.set_status("error")
            span.add_log("error", error_message)
            
            # Record error metrics
            provider.metrics.increment_counter(
                "errors_total",
                error_type=error_type,
                is_retryable=str(is_retryable).lower(),
                component="api_handler"
            )
            
            # Record error rate
            provider.metrics.set_gauge(
                "error_rate_percent",
                2.5,  # 2.5% error rate
                component="api_handler",
                time_window="5m"
            )


async def demonstrate_performance_monitoring(provider):
    """Demonstrate performance monitoring capabilities"""
    
    logger.info("⚡ Demonstrating performance monitoring...")
    
    # Simulate performance-critical operations
    operations = [
        ("database_query", 0.045, {"query_complexity": "simple"}),
        ("cache_lookup", 0.002, {"cache_type": "redis"}),
        ("external_api_call", 0.234, {"api_provider": "openai"}),
        ("file_processing", 0.156, {"file_size_mb": 2.5}),
        ("ml_inference", 0.678, {"model_size": "large"}),
    ]
    
    for operation, duration, tags in operations:
        with provider.tracer.start_span(f"perf.{operation}") as span:
            # Add performance-related tags
            for key, value in tags.items():
                span.add_tag(key, value)
            
            span.add_tag("duration_ms", duration * 1000)
            
            # Simulate the operation
            await asyncio.sleep(duration)
            
            # Record performance metrics
            provider.metrics.record_histogram(
                "operation_duration_seconds",
                duration,
                operation=operation,
                **{k: str(v) for k, v in tags.items()}
            )
            
            # Record throughput
            provider.metrics.increment_counter(
                "operations_per_second",
                operation=operation
            )
            
            # Performance thresholds
            threshold = 0.5  # 500ms threshold
            if duration > threshold:
                provider.metrics.increment_counter(
                    "slow_operations_total",
                    operation=operation,
                    threshold_ms=int(threshold * 1000)
                )
                
                span.add_tag("performance_warning", True)
                span.add_log("warning", f"Operation exceeded {threshold}s threshold")


if __name__ == "__main__":
    print("🌐 LangSwarm Multi-Exporter OpenTelemetry Example")
    print("=" * 60)
    print("This example demonstrates exporting to multiple platforms:")
    print("📊 Jaeger - Distributed tracing visualization")
    print("📈 Prometheus - Metrics collection and alerting")
    print("🔗 OTLP - Generic endpoint for any compatible platform")
    print()
    print("Environment variables (optional):")
    print("- JAEGER_ENDPOINT: Jaeger collector endpoint")
    print("- OTLP_ENDPOINT: OTLP receiver endpoint")
    print("- OTLP_TOKEN: Authentication token for OTLP")
    print("- PROMETHEUS_PORT: Prometheus metrics port")
    print()
    print("🚀 Starting multi-exporter demonstration...")
    print()
    
    asyncio.run(main())
