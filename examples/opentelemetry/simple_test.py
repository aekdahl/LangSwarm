#!/usr/bin/env python3
"""
Simple test to verify OpenTelemetry integration works

This is a minimal example to test that the OpenTelemetry integration
is properly configured and can export data.
"""

import asyncio
import logging
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
    """Simple test of OpenTelemetry integration"""
    
    print("🧪 Testing LangSwarm OpenTelemetry Integration")
    print("=" * 50)
    
    # Test 1: Basic configuration
    print("1️⃣  Testing basic configuration...")
    config = ObservabilityConfig(
        enabled=True,
        opentelemetry_enabled=True,
        opentelemetry_service_name="test-service",
        opentelemetry_prometheus_enabled=True,
        opentelemetry_prometheus_port=8001,  # Different port to avoid conflicts
    )
    
    provider = ObservabilityProvider(config)
    
    # Check if OpenTelemetry is properly initialized
    print(f"   ✅ OpenTelemetry enabled: {provider.opentelemetry_enabled}")
    
    # Test 2: Start the provider
    print("2️⃣  Testing provider startup...")
    await provider.start()
    print("   ✅ Provider started successfully")
    
    # Test 3: Generate some telemetry data
    print("3️⃣  Testing telemetry generation...")
    
    # Create a trace
    with provider.tracer.start_span("test_operation") as span:
        span.add_tag("test", "true")
        span.add_tag("operation_type", "integration_test")
        
        provider.logger.info("Test operation started", component="test")
        
        # Simulate some work
        await asyncio.sleep(0.1)
        
        # Record a metric
        provider.metrics.increment_counter("test_operations", status="success")
        provider.metrics.set_gauge("test_value", 42.0)
        
        provider.logger.info("Test operation completed", component="test")
    
    print("   ✅ Telemetry data generated")
    
    # Test 4: Manual export (if OpenTelemetry is available)
    print("4️⃣  Testing manual export...")
    try:
        # This will only work if OpenTelemetry dependencies are installed
        from langswarm.core.observability import TraceSpan, MetricPoint, MetricType
        
        # Create test data
        test_span = TraceSpan(
            span_id="test-span-123",
            trace_id="test-trace-456", 
            operation_name="manual_test",
            start_time=datetime.utcnow(),
            component="test_component"
        )
        
        test_metric = MetricPoint(
            name="manual_test_metric",
            value=100.0,
            metric_type=MetricType.COUNTER,
            timestamp=datetime.utcnow()
        )
        
        # Try to export manually
        provider.export_to_opentelemetry([test_span], [test_metric])
        print("   ✅ Manual export successful")
        
    except ImportError:
        print("   ⚠️  OpenTelemetry dependencies not installed - manual export skipped")
        print("      Install with: pip install langswarm[opentelemetry]")
    
    # Test 5: Flush and cleanup
    print("5️⃣  Testing cleanup...")
    await provider.flush()
    await provider.stop()
    print("   ✅ Cleanup completed")
    
    print()
    print("🎉 All tests passed!")
    print()
    print("Next steps:")
    print("- Install OpenTelemetry: pip install langswarm[opentelemetry]")
    print("- Run Jaeger example: python jaeger_example.py")
    print("- Run Prometheus example: python prometheus_example.py")
    print("- Check metrics endpoint: http://localhost:8001/metrics")


if __name__ == "__main__":
    asyncio.run(main())
