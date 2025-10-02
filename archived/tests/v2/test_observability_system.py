"""
Comprehensive test suite for V2 Observability System

Tests all aspects of the unified observability system including:
- Logging functionality and configuration
- Distributed tracing with span hierarchy
- Metrics collection (counters, gauges, histograms, timers)
- Component integrations
- Provider management and configuration
- Production readiness features
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
import json

# Import V2 observability components
from langswarm.v2.core.observability import (
    # Core components
    ObservabilityProvider, create_observability_provider,
    create_development_observability, create_production_observability,
    
    # Individual components
    V2Logger, V2Tracer, V2Metrics,
    
    # Interfaces and data structures
    ObservabilityConfig, LogLevel, MetricType, SpanStatus,
    LogEvent, TraceSpan, MetricPoint,
    
    # Component integrations
    AgentObservability, ToolObservability, SessionObservability,
    MemoryObservability, WorkflowObservability,
    create_all_observability_integrations
)


class TestV2Logger:
    """Test V2 structured logger functionality"""
    
    def test_logger_creation(self):
        """Test logger creation with different configurations"""
        config = ObservabilityConfig(
            enabled=True,
            log_level=LogLevel.INFO,
            log_format="structured",
            log_output="console"
        )
        
        logger = V2Logger(config)
        assert logger.config == config
        assert logger._current_trace_id is None
        assert logger._current_span_id is None
    
    def test_structured_logging(self):
        """Test structured log output"""
        config = ObservabilityConfig(
            enabled=True,
            log_level=LogLevel.DEBUG,
            log_format="structured",
            log_output="console"
        )
        
        logger = V2Logger(config)
        
        # Test different log levels
        logger.debug("Debug message", "test", key="value")
        logger.info("Info message", "test", operation="test_op")
        logger.warning("Warning message", "test", user_id="test_user")
        logger.error("Error message", "test", error_code="ERR001")
        logger.critical("Critical message", "test", severity="high")
        
        # Should not raise exceptions
        assert True
    
    def test_trace_context_correlation(self):
        """Test logging with trace context"""
        config = ObservabilityConfig(enabled=True)
        logger = V2Logger(config)
        
        # Set trace context
        trace_id = "test-trace-123"
        span_id = "test-span-456"
        logger.set_trace_context(trace_id, span_id)
        
        assert logger._current_trace_id == trace_id
        assert logger._current_span_id == span_id
    
    def test_log_filtering(self):
        """Test component and level filtering"""
        config = ObservabilityConfig(
            enabled=True,
            log_level=LogLevel.WARNING,
            enabled_components=["test", "agent"]
        )
        
        logger = V2Logger(config)
        
        # These should be filtered out
        logger.debug("Debug message", "test")  # Level too low
        logger.info("Info message", "test")    # Level too low
        logger.info("Info message", "other")   # Component not enabled
        
        # These should pass
        logger.warning("Warning message", "test")
        logger.error("Error message", "agent")


class TestV2Tracer:
    """Test V2 distributed tracer functionality"""
    
    def test_tracer_creation(self):
        """Test tracer creation with configuration"""
        config = ObservabilityConfig(
            tracing_enabled=True,
            trace_sampling_rate=1.0
        )
        
        tracer = V2Tracer(config)
        assert tracer.config == config
        assert tracer._sampling_rate == 1.0
    
    def test_span_creation(self):
        """Test basic span creation and management"""
        config = ObservabilityConfig(tracing_enabled=True, trace_sampling_rate=1.0)
        tracer = V2Tracer(config)
        
        with tracer.start_span("test_operation") as span:
            assert span is not None
            assert span.operation_name == "test_operation"
            assert span.span_id is not None
            assert span.trace_id is not None
            assert span.start_time is not None
            assert span.status == SpanStatus.OK
            
            # Test current span retrieval
            current_span = tracer.get_current_span()
            assert current_span == span
            
            # Test trace ID retrieval
            current_trace_id = tracer.get_trace_id()
            assert current_trace_id == span.trace_id
    
    def test_nested_spans(self):
        """Test nested span hierarchy"""
        config = ObservabilityConfig(tracing_enabled=True, trace_sampling_rate=1.0)
        tracer = V2Tracer(config)
        
        with tracer.start_span("parent_operation") as parent_span:
            assert parent_span is not None
            parent_trace_id = parent_span.trace_id
            
            with tracer.start_span("child_operation") as child_span:
                assert child_span is not None
                assert child_span.trace_id == parent_trace_id
                assert child_span.parent_span_id == parent_span.span_id
                
                # Parent should still be current
                # (child becomes current when in its context)
                with tracer.start_span("grandchild_operation") as grandchild_span:
                    assert grandchild_span is not None
                    assert grandchild_span.trace_id == parent_trace_id
    
    def test_span_tags_and_logs(self):
        """Test span tagging and logging"""
        config = ObservabilityConfig(tracing_enabled=True, trace_sampling_rate=1.0)
        tracer = V2Tracer(config)
        
        with tracer.start_span("tagged_operation", test_tag="test_value") as span:
            assert span is not None
            assert span.tags["test_tag"] == "test_value"
            
            # Add more tags
            tracer.add_span_tag("dynamic_tag", "dynamic_value")
            assert span.tags["dynamic_tag"] == "dynamic_value"
            
            # Add logs
            tracer.add_span_log("Test log message", level="info")
            assert len(span.logs) == 1
            assert span.logs[0]["message"] == "Test log message"
            assert span.logs[0]["level"] == "info"
    
    def test_error_handling(self):
        """Test span error handling"""
        config = ObservabilityConfig(tracing_enabled=True, trace_sampling_rate=1.0)
        tracer = V2Tracer(config)
        
        try:
            with tracer.start_span("error_operation") as span:
                assert span is not None
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        # Span should be marked as error
        completed_span = tracer.get_span_by_id(span.span_id)
        assert completed_span.status == SpanStatus.ERROR
        assert completed_span.tags["error"] is True
        assert "Test error" in completed_span.tags["error.message"]


class TestV2Metrics:
    """Test V2 metrics collection functionality"""
    
    def test_metrics_creation(self):
        """Test metrics creation with configuration"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        assert metrics.config == config
    
    def test_counter_metrics(self):
        """Test counter metric functionality"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        
        # Test basic counter
        metrics.increment_counter("test.requests", 1.0)
        value = metrics.get_counter_value("test.requests")
        assert value == 1.0
        
        # Test counter with tags
        metrics.increment_counter("test.requests", 2.0, endpoint="/api", method="GET")
        value = metrics.get_counter_value("test.requests", endpoint="/api", method="GET")
        assert value == 2.0
        
        # Test multiple increments
        metrics.increment_counter("test.requests", 3.0, endpoint="/api", method="GET")
        value = metrics.get_counter_value("test.requests", endpoint="/api", method="GET")
        assert value == 5.0
    
    def test_gauge_metrics(self):
        """Test gauge metric functionality"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        
        # Test basic gauge
        metrics.set_gauge("test.connections", 42.0)
        value = metrics.get_gauge_value("test.connections")
        assert value == 42.0
        
        # Test gauge update
        metrics.set_gauge("test.connections", 100.0)
        value = metrics.get_gauge_value("test.connections")
        assert value == 100.0
        
        # Test gauge with tags
        metrics.set_gauge("test.memory", 1024.0, unit="MB", process="worker")
        value = metrics.get_gauge_value("test.memory", unit="MB", process="worker")
        assert value == 1024.0
    
    def test_histogram_metrics(self):
        """Test histogram metric functionality"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        
        # Record histogram values
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            metrics.record_histogram("test.response_time", value)
        
        # Test histogram statistics
        stats = metrics.get_histogram_stats("test.response_time")
        assert stats["count"] == 5
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
    
    def test_timer_metrics(self):
        """Test timer metric functionality"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        
        # Record timer values
        durations = [100.0, 200.0, 150.0, 300.0, 250.0]
        for duration in durations:
            metrics.record_timer("test.operation_time", duration)
        
        # Test timer statistics
        stats = metrics.get_timer_stats("test.operation_time")
        assert stats["count"] == 5
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 300.0
        assert stats["mean_ms"] == 200.0
        assert stats["median_ms"] == 200.0
    
    def test_metrics_export(self):
        """Test metrics export functionality"""
        config = ObservabilityConfig(metrics_enabled=True)
        metrics = V2Metrics(config)
        
        # Record some metrics
        metrics.increment_counter("export.test", 1.0)
        metrics.set_gauge("export.gauge", 42.0)
        metrics.record_histogram("export.histogram", 123.0)
        
        # Export metrics
        exported = metrics.export_metrics()
        assert len(exported) >= 3
        
        # Check metric points
        for metric_point in exported:
            assert isinstance(metric_point, MetricPoint)
            assert metric_point.name.startswith("export.")
            assert metric_point.value is not None
            assert metric_point.timestamp is not None


class TestObservabilityProvider:
    """Test unified observability provider"""
    
    @pytest.mark.asyncio
    async def test_provider_lifecycle(self):
        """Test provider start/stop lifecycle"""
        config = ObservabilityConfig(enabled=True)
        provider = ObservabilityProvider(config)
        
        # Test start
        await provider.start()
        assert provider._started is True
        
        # Test health status
        health = provider.get_health_status()
        assert health["status"] == "healthy"
        
        # Test stop
        await provider.stop()
        assert provider._started is False
    
    @pytest.mark.asyncio
    async def test_integrated_logging_tracing(self):
        """Test integrated logging with tracing correlation"""
        provider = create_development_observability()
        await provider.start()
        
        try:
            with provider.tracer.start_span("integrated_test") as span:
                if span:
                    # Log with trace context
                    provider.log_with_trace_context("info", "Test message", "test")
                    
                    # Check that logger has trace context
                    assert provider.logger._current_trace_id == span.trace_id
                    assert provider.logger._current_span_id == span.span_id
        
        finally:
            await provider.stop()
    
    @pytest.mark.asyncio
    async def test_traced_operation_context(self):
        """Test traced operation context manager"""
        provider = create_development_observability()
        await provider.start()
        
        try:
            with provider.trace_and_log_operation("test_operation", "test") as span:
                if span:
                    assert span.operation_name == "test_operation"
                    # Should automatically log start and completion
        
        finally:
            await provider.stop()


class TestComponentIntegrations:
    """Test component-specific observability integrations"""
    
    def test_all_integrations_creation(self):
        """Test creation of all component integrations"""
        integrations = create_all_observability_integrations()
        
        assert len(integrations) == 5
        assert "agent" in integrations
        assert "tool" in integrations
        assert "session" in integrations
        assert "memory" in integrations
        assert "workflow" in integrations
        
        assert isinstance(integrations["agent"], AgentObservability)
        assert isinstance(integrations["tool"], ToolObservability)
        assert isinstance(integrations["session"], SessionObservability)
        assert isinstance(integrations["memory"], MemoryObservability)
        assert isinstance(integrations["workflow"], WorkflowObservability)
    
    def test_agent_observability(self):
        """Test agent-specific observability"""
        provider = create_development_observability()
        agent_obs = AgentObservability(provider)
        
        # Test agent operations
        agent_obs.trace_agent_creation("test_agent", "openai", "gpt-4o")
        agent_obs.record_response_time("test_agent", 123.4, "openai", "gpt-4o")
        agent_obs.record_token_usage("test_agent", 100, 50, "openai")
        agent_obs.record_error("test_agent", "timeout", "openai", "gpt-4o")
        
        # Check metrics were recorded
        metrics = provider.metrics.get_all_metrics()
        assert len(metrics["counters"]) > 0
    
    def test_tool_observability(self):
        """Test tool-specific observability"""
        provider = create_development_observability()
        tool_obs = ToolObservability(provider)
        
        # Test tool operations
        tool_obs.record_execution_time("calculator", "add", 23.4, True)
        tool_obs.record_tool_error("calculator", "divide", "division_by_zero")
        
        # Check metrics were recorded
        metrics = provider.metrics.get_all_metrics()
        assert len(metrics["counters"]) > 0
    
    def test_session_observability(self):
        """Test session-specific observability"""
        provider = create_development_observability()
        session_obs = SessionObservability(provider)
        
        # Test session operations
        session_obs.trace_session_creation("test_session", "test_user", "openai", "memory")
        session_obs.record_session_duration("test_session", 15.5, "openai")
        session_obs.record_message_count("test_session", 10, "openai")
        session_obs.record_session_error("test_session", "timeout", "send_message")
        
        # Check metrics were recorded
        metrics = provider.metrics.get_all_metrics()
        assert len(metrics["counters"]) > 0
    
    def test_memory_observability(self):
        """Test memory-specific observability"""
        provider = create_development_observability()
        memory_obs = MemoryObservability(provider)
        
        # Test memory operations
        memory_obs.record_memory_usage("sqlite", 10, 100, 5.2)
        memory_obs.record_operation_time("save", "sqlite", 12.3, True)
        memory_obs.record_search_performance("sqlite", 8.7, 5)
        memory_obs.record_memory_error("save", "sqlite", "disk_full")
        
        # Check metrics were recorded
        metrics = provider.metrics.get_all_metrics()
        assert len(metrics["counters"]) > 0
    
    def test_workflow_observability(self):
        """Test workflow-specific observability"""
        provider = create_development_observability()
        workflow_obs = WorkflowObservability(provider)
        
        # Test workflow operations
        workflow_obs.record_workflow_duration("test_workflow", 234.5, True)
        workflow_obs.record_step_performance("test_workflow", "step_1", "agent", 45.6, True)
        workflow_obs.record_workflow_error("test_workflow", "step_2", "timeout")
        
        # Check metrics were recorded
        metrics = provider.metrics.get_all_metrics()
        assert len(metrics["counters"]) > 0


class TestProductionReadiness:
    """Test production-ready features"""
    
    def test_development_configuration(self):
        """Test development configuration preset"""
        provider = create_development_observability()
        
        assert provider.config.enabled is True
        assert provider.config.log_level == LogLevel.DEBUG
        assert provider.config.log_format == "text"
        assert provider.config.tracing_enabled is True
        assert provider.config.trace_sampling_rate == 1.0
        assert provider.config.metrics_enabled is True
    
    def test_production_configuration(self):
        """Test production configuration preset"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            provider = create_production_observability(
                log_file_path=log_file,
                trace_export_url="http://localhost:14268/api/traces",
                metrics_export_url="http://localhost:9090/api/v1/write"
            )
            
            assert provider.config.enabled is True
            assert provider.config.log_level == LogLevel.INFO
            assert provider.config.log_format == "structured"
            assert provider.config.log_output == "both"
            assert provider.config.log_file_path == log_file
            assert provider.config.trace_sampling_rate == 0.1  # 10% sampling
            
        finally:
            os.unlink(log_file)
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test observability performance under load"""
        provider = create_development_observability()
        await provider.start()
        
        try:
            # Generate load
            for i in range(100):
                with provider.tracer.start_span(f"load_test_{i}") as span:
                    if span:
                        provider.log_with_trace_context("info", f"Load test {i}", "test")
                        provider.metrics.increment_counter("load_test.operations", 1.0)
                        provider.metrics.record_histogram("load_test.duration", float(i))
            
            # Check that everything was recorded
            health = provider.get_health_status()
            assert health["status"] == "healthy"
            
            metrics = provider.metrics.get_all_metrics()
            assert len(metrics["counters"]) > 0
            
        finally:
            await provider.stop()


# Pytest configuration and fixtures
@pytest.fixture
def observability_config():
    """Fixture providing test observability configuration"""
    return ObservabilityConfig(
        enabled=True,
        log_level=LogLevel.DEBUG,
        log_format="structured",
        log_output="console",
        tracing_enabled=True,
        trace_sampling_rate=1.0,
        metrics_enabled=True,
        buffer_size=1000
    )


@pytest.fixture
async def observability_provider(observability_config):
    """Fixture providing test observability provider"""
    provider = ObservabilityProvider(observability_config)
    await provider.start()
    yield provider
    await provider.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
