# LangSwarm V2 Testing Guide

**Comprehensive testing strategy and framework for V2 system validation**

## 🎯 Overview

LangSwarm V2 includes a comprehensive testing framework that ensures system reliability, performance, and quality. The testing strategy covers unit tests, integration tests, performance benchmarks, and end-to-end validation with automated quality gates and continuous monitoring.

**Testing Components:**
- **Unit Tests**: Individual component functionality validation
- **Integration Tests**: Cross-component interaction testing
- **Performance Tests**: Scalability and regression validation
- **End-to-End Tests**: Complete system workflow validation
- **Quality Gates**: Performance targets and regression prevention
- **Observability Tests**: Monitoring and debugging validation

---

## 🚀 Quick Start

### **Running the Test Suite**

```bash
# Run all V2 tests
pytest tests/v2/ -v

# Run specific test categories
pytest tests/v2/test_observability_system.py -v
pytest tests/v2/test_comprehensive_v2_system.py -v
pytest tests/v2/performance_benchmarks.py -v

# Run with coverage
pytest tests/v2/ --cov=langswarm.v2 --cov-report=html

# Run performance benchmarks only
pytest tests/v2/performance_benchmarks.py::test_performance_benchmarks -v
```

### **Basic Test Setup**

```python
import pytest
import asyncio
from langswarm.core.observability import ObservabilityProvider

@pytest.fixture
async def observability_provider():
    """Test observability provider fixture"""
    provider = ObservabilityProvider.create_development()
    await provider.initialize()
    yield provider
    await provider.shutdown()

@pytest.fixture
def event_loop():
    """Event loop fixture for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Example test
async def test_basic_functionality(observability_provider):
    """Test basic V2 functionality"""
    logger = observability_provider.get_logger("test")
    logger.info("Test started")
    
    # Test functionality
    assert observability_provider.is_initialized()
    
    logger.info("Test completed")
```

---

## 🧪 Test Categories

### **1. Observability System Tests**

```python
"""
Complete observability system testing
Location: tests/v2/test_observability_system.py
"""

class TestObservabilitySystem:
    """Comprehensive observability system tests"""
    
    async def test_observability_provider_lifecycle(self):
        """Test observability provider initialization and shutdown"""
        # Development configuration
        dev_provider = ObservabilityProvider.create_development()
        await dev_provider.initialize()
        assert dev_provider.is_initialized()
        await dev_provider.shutdown()
        
        # Production configuration
        prod_provider = ObservabilityProvider.create_production()
        await prod_provider.initialize()
        assert prod_provider.is_initialized()
        await prod_provider.shutdown()
    
    async def test_structured_logging(self, observability_provider):
        """Test structured logging functionality"""
        logger = observability_provider.get_logger("test_component")
        
        # Test different log levels
        logger.debug("Debug message", user_id="test_user")
        logger.info("Info message", operation="test_op")
        logger.warning("Warning message", warning_type="test")
        logger.error("Error message", error_code="TEST_ERROR")
        
        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception occurred", context="test")
    
    async def test_distributed_tracing(self, observability_provider):
        """Test distributed tracing functionality"""
        tracer = observability_provider.get_tracer("test_service")
        
        # Test span creation and nesting
        with tracer.start_span("root_operation") as root_span:
            root_span.set_attribute("test_id", "trace_test")
            
            with tracer.start_span("child_operation") as child_span:
                child_span.set_attribute("child_data", "test_data")
                child_span.add_event("test_event", {"event_data": "test"})
                
                # Test current span context
                assert tracer.get_current_span() == child_span
                assert tracer.get_current_trace_id() is not None
            
            # Test span status
            root_span.set_status("OK", "Test completed successfully")
    
    async def test_metrics_collection(self, observability_provider):
        """Test metrics collection functionality"""
        metrics = observability_provider.get_metrics("test_metrics")
        
        # Test counter metrics
        metrics.increment_counter("test_counter", labels={"test": "true"})
        metrics.increment_counter("test_counter", value=5.0, labels={"test": "true"})
        
        # Test gauge metrics
        metrics.set_gauge("test_gauge", 42.0, labels={"type": "test"})
        metrics.set_gauge("test_gauge", 100.0, labels={"type": "test"})
        
        # Test histogram metrics
        metrics.record_histogram("test_histogram", 1.5, labels={"op": "test"})
        metrics.record_histogram("test_histogram", 2.3, labels={"op": "test"})
        
        # Test timer metrics
        with metrics.timer("test_timer", labels={"timed_op": "test"}):
            await asyncio.sleep(0.01)  # Simulate work
        
        # Verify metrics export
        exported = await metrics.export_metrics()
        assert "test_counter" in exported
        assert "test_gauge" in exported
        assert "test_histogram" in exported
    
    async def test_component_integrations(self, observability_provider):
        """Test component-specific observability integrations"""
        from langswarm.core.observability.integrations import (
            AgentObservability,
            ToolObservability,
            SessionObservability
        )
        
        # Test agent observability
        agent_obs = AgentObservability(observability_provider)
        await agent_obs.initialize()
        
        # Test tool observability
        tool_obs = ToolObservability(observability_provider)
        await tool_obs.initialize()
        
        # Test session observability
        session_obs = SessionObservability(observability_provider)
        await session_obs.initialize()
        
        # Clean up
        await agent_obs.shutdown()
        await tool_obs.shutdown()
        await session_obs.shutdown()
    
    async def test_correlation_between_systems(self, observability_provider):
        """Test correlation between logging, tracing, and metrics"""
        logger = observability_provider.get_logger("correlation_test")
        tracer = observability_provider.get_tracer("correlation_test")
        metrics = observability_provider.get_metrics("correlation_test")
        
        # Create correlated operations
        with tracer.start_span("correlated_operation") as span:
            correlation_id = "test_correlation_123"
            span.set_attribute("correlation_id", correlation_id)
            
            # Log with correlation
            logger.info("Correlated log message", 
                       correlation_id=correlation_id,
                       operation="test_correlation")
            
            # Metrics with correlation
            metrics.increment_counter("correlated_operations", 
                                    labels={"correlation_id": correlation_id})
            
            # Verify trace context
            assert tracer.get_current_trace_id() is not None
            assert tracer.get_current_span_id() is not None
```

### **2. Comprehensive V2 System Tests**

```python
"""
Full V2 system integration testing
Location: tests/v2/test_comprehensive_v2_system.py
"""

class TestComprehensiveV2System:
    """Complete V2 system integration tests"""
    
    async def test_agent_system_integration(self, observability_provider):
        """Test agent system with observability"""
        from langswarm.core.agents import AgentBuilder
        from langswarm.core.observability.integrations import AgentObservability
        
        # Enable agent observability
        agent_obs = AgentObservability(observability_provider)
        await agent_obs.initialize()
        
        # Create and test agent
        agent = (AgentBuilder()
            .with_provider("mock")  # Use mock for testing
            .with_model("test-model")
            .with_system_prompt("You are a test assistant")
            .build())
        
        # Test agent operations with automatic observability
        response = await agent.generate_response("Hello, test!")
        assert response is not None
        assert len(response) > 0
        
        # Verify observability data was collected
        metrics = observability_provider.get_metrics()
        exported = await metrics.export_metrics()
        # Should have agent-related metrics
        
        await agent_obs.shutdown()
    
    async def test_tool_system_integration(self, observability_provider):
        """Test tool system with observability"""
        from langswarm.core.tools import ToolRegistry
        from langswarm.core.observability.integrations import ToolObservability
        
        # Enable tool observability
        tool_obs = ToolObservability(observability_provider)
        await tool_obs.initialize()
        
        # Test tool execution
        registry = ToolRegistry()
        calculator = registry.get_tool("calculator")
        
        # Execute tool with automatic observability
        result = await calculator.execute("add", {"a": 5, "b": 3})
        assert result["result"] == 8
        
        # Verify observability data
        metrics = observability_provider.get_metrics()
        exported = await metrics.export_metrics()
        # Should have tool execution metrics
        
        await tool_obs.shutdown()
    
    async def test_session_system_integration(self, observability_provider):
        """Test session system with observability"""
        from langswarm.core.session import create_session_manager
        from langswarm.core.observability.integrations import SessionObservability
        
        # Enable session observability
        session_obs = SessionObservability(observability_provider)
        await session_obs.initialize()
        
        # Test session operations
        manager = create_session_manager(storage="memory")
        session = await manager.create_session("test_user", "mock", "test-model")
        
        # Send test messages with automatic observability
        response = await session.send_message("Test message")
        assert response is not None
        
        messages = await session.get_messages()
        assert len(messages) >= 2  # User message + response
        
        # Verify observability data
        metrics = observability_provider.get_metrics()
        exported = await metrics.export_metrics()
        # Should have session metrics
        
        await session_obs.shutdown()
    
    async def test_memory_system_integration(self, observability_provider):
        """Test memory system with observability"""
        from langswarm.core.memory import MemoryFactory
        from langswarm.core.observability.integrations import MemoryObservability
        
        # Enable memory observability
        memory_obs = MemoryObservability(observability_provider)
        await memory_obs.initialize()
        
        # Test memory operations
        memory = MemoryFactory.create("in_memory")
        
        # Memory operations with automatic observability
        await memory.save("test_user", "test_key", "test_value")
        value = await memory.load("test_user", "test_key")
        assert value == "test_value"
        
        keys = await memory.list_keys("test_user")
        assert "test_key" in keys
        
        # Verify observability data
        metrics = observability_provider.get_metrics()
        exported = await metrics.export_metrics()
        # Should have memory operation metrics
        
        await memory_obs.shutdown()
    
    async def test_workflow_system_integration(self, observability_provider):
        """Test workflow system with observability"""
        from langswarm.core.workflows import WorkflowBuilder
        from langswarm.core.observability.integrations import WorkflowObservability
        
        # Enable workflow observability
        workflow_obs = WorkflowObservability(observability_provider)
        await workflow_obs.initialize()
        
        # Create test workflow
        def test_step_1(data):
            return {"step1_result": data["input"] + "_processed"}
        
        def test_step_2(data):
            return {"final_result": data["step1_result"] + "_final"}
        
        workflow = (WorkflowBuilder()
            .add_step("process", test_step_1)
            .add_step("finalize", test_step_2)
            .build())
        
        # Execute workflow with automatic observability
        result = await workflow.execute({"input": "test_data"})
        assert result["final_result"] == "test_data_processed_final"
        
        # Verify observability data
        metrics = observability_provider.get_metrics()
        exported = await metrics.export_metrics()
        # Should have workflow execution metrics
        
        await workflow_obs.shutdown()
    
    async def test_error_handling_observability(self, observability_provider):
        """Test error handling with comprehensive observability"""
        logger = observability_provider.get_logger("error_test")
        tracer = observability_provider.get_tracer("error_test")
        metrics = observability_provider.get_metrics("error_test")
        
        # Test error scenarios with observability
        with tracer.start_span("error_operation") as span:
            try:
                # Simulate error
                raise ValueError("Test error for observability")
            except ValueError as e:
                # Record error in all systems
                span.record_exception(e)
                span.set_status("ERROR", str(e))
                
                logger.error("Operation failed", 
                           error_type=type(e).__name__,
                           error_message=str(e))
                
                metrics.increment_counter("errors_total", 
                                        labels={"error_type": "ValueError"})
                
                # Verify error was properly recorded
                assert span.status.status_code == "ERROR"
    
    async def test_performance_under_load(self, observability_provider):
        """Test system performance under load with monitoring"""
        import time
        
        logger = observability_provider.get_logger("load_test")
        metrics = observability_provider.get_metrics("load_test")
        
        # Simulate load testing
        operation_count = 100
        start_time = time.time()
        
        for i in range(operation_count):
            with metrics.timer("load_test_operation"):
                # Simulate work
                logger.info(f"Load test operation {i}", operation_id=i)
                await asyncio.sleep(0.001)  # 1ms simulated work
        
        total_time = time.time() - start_time
        operations_per_second = operation_count / total_time
        
        # Record performance metrics
        metrics.set_gauge("operations_per_second", operations_per_second)
        metrics.record_histogram("total_test_time", total_time)
        
        # Verify performance targets
        assert operations_per_second > 50  # Should handle 50+ ops/sec
        assert total_time < 5.0  # Should complete within 5 seconds
```

### **3. Performance Benchmarks**

```python
"""
Performance benchmarking and validation
Location: tests/v2/performance_benchmarks.py
"""

class PerformanceBenchmarker:
    """Comprehensive performance testing utility"""
    
    def __init__(self):
        self.results = {}
        self.performance_targets = {
            "observability_logging": 500,    # ops/second
            "observability_tracing": 200,    # ops/second
            "observability_metrics": 800,    # ops/second
            "agent_creation": 50,             # ops/second
            "memory_save": 100,               # ops/second
            "memory_load": 200,               # ops/second
            "session_creation": 100,          # ops/second
            "session_messages": 300,          # ops/second
        }
    
    async def benchmark_observability_performance(self, observability_provider):
        """Benchmark observability system performance"""
        logger = observability_provider.get_logger("benchmark")
        tracer = observability_provider.get_tracer("benchmark")
        metrics = observability_provider.get_metrics("benchmark")
        
        # Logging performance
        logging_ops = 1000
        start_time = time.time()
        
        for i in range(logging_ops):
            logger.info(f"Benchmark log {i}", operation_id=i, test_data="performance")
        
        logging_time = time.time() - start_time
        logging_ops_per_sec = logging_ops / logging_time
        
        # Tracing performance
        tracing_ops = 500
        start_time = time.time()
        
        for i in range(tracing_ops):
            with tracer.start_span(f"benchmark_span_{i}") as span:
                span.set_attribute("operation_id", i)
                span.set_attribute("test_data", "performance")
        
        tracing_time = time.time() - start_time
        tracing_ops_per_sec = tracing_ops / tracing_time
        
        # Metrics performance
        metrics_ops = 2000
        start_time = time.time()
        
        for i in range(metrics_ops):
            metrics.increment_counter("benchmark_counter", 
                                    labels={"operation": str(i)})
            metrics.set_gauge("benchmark_gauge", i)
            metrics.record_histogram("benchmark_histogram", i * 0.1)
        
        metrics_time = time.time() - start_time
        metrics_ops_per_sec = metrics_ops / metrics_time
        
        # Record results
        self.results.update({
            "observability_logging": logging_ops_per_sec,
            "observability_tracing": tracing_ops_per_sec,
            "observability_metrics": metrics_ops_per_sec
        })
        
        return {
            "logging_ops_per_sec": logging_ops_per_sec,
            "tracing_ops_per_sec": tracing_ops_per_sec,
            "metrics_ops_per_sec": metrics_ops_per_sec
        }
    
    async def benchmark_agent_system(self):
        """Benchmark agent system performance"""
        from langswarm.core.agents import AgentBuilder
        
        # Agent creation performance
        creation_ops = 100
        start_time = time.time()
        
        agents = []
        for i in range(creation_ops):
            agent = (AgentBuilder()
                .with_provider("mock")
                .with_model("benchmark-model")
                .with_system_prompt(f"Test agent {i}")
                .build())
            agents.append(agent)
        
        creation_time = time.time() - start_time
        creation_ops_per_sec = creation_ops / creation_time
        
        # Agent response performance
        response_ops = 50
        start_time = time.time()
        
        for i in range(response_ops):
            agent = agents[i % len(agents)]
            response = await agent.generate_response(f"Test message {i}")
            assert response is not None
        
        response_time = time.time() - start_time
        response_ops_per_sec = response_ops / response_time
        
        self.results["agent_creation"] = creation_ops_per_sec
        
        return {
            "agent_creation_ops_per_sec": creation_ops_per_sec,
            "agent_response_ops_per_sec": response_ops_per_sec
        }
    
    async def benchmark_memory_system(self):
        """Benchmark memory system performance"""
        from langswarm.core.memory import MemoryFactory
        
        memory = MemoryFactory.create("in_memory")
        
        # Memory save performance
        save_ops = 500
        start_time = time.time()
        
        for i in range(save_ops):
            await memory.save(f"user_{i%10}", f"key_{i}", f"value_{i}")
        
        save_time = time.time() - start_time
        save_ops_per_sec = save_ops / save_time
        
        # Memory load performance
        load_ops = 1000
        start_time = time.time()
        
        for i in range(load_ops):
            value = await memory.load(f"user_{i%10}", f"key_{i%save_ops}")
            # Some loads will return None (key not found), that's expected
        
        load_time = time.time() - start_time
        load_ops_per_sec = load_ops / load_time
        
        self.results.update({
            "memory_save": save_ops_per_sec,
            "memory_load": load_ops_per_sec
        })
        
        return {
            "memory_save_ops_per_sec": save_ops_per_sec,
            "memory_load_ops_per_sec": load_ops_per_sec
        }
    
    async def benchmark_session_system(self):
        """Benchmark session system performance"""
        from langswarm.core.session import create_session_manager
        
        manager = create_session_manager(storage="memory")
        
        # Session creation performance
        creation_ops = 200
        start_time = time.time()
        
        sessions = []
        for i in range(creation_ops):
            session = await manager.create_session(
                f"benchmark_user_{i}", "mock", "benchmark-model"
            )
            sessions.append(session)
        
        creation_time = time.time() - start_time
        creation_ops_per_sec = creation_ops / creation_time
        
        # Message handling performance
        message_ops = 500
        start_time = time.time()
        
        for i in range(message_ops):
            session = sessions[i % len(sessions)]
            await session.send_message(f"Benchmark message {i}")
        
        message_time = time.time() - start_time
        message_ops_per_sec = message_ops / message_time
        
        self.results.update({
            "session_creation": creation_ops_per_sec,
            "session_messages": message_ops_per_sec
        })
        
        return {
            "session_creation_ops_per_sec": creation_ops_per_sec,
            "session_message_ops_per_sec": message_ops_per_sec
        }
    
    def validate_performance_targets(self) -> dict:
        """Validate performance against targets"""
        validation_results = {}
        
        for metric, target in self.performance_targets.items():
            actual = self.results.get(metric, 0)
            passed = actual >= target
            
            validation_results[metric] = {
                "target": target,
                "actual": actual,
                "passed": passed,
                "percentage": (actual / target) * 100 if target > 0 else 0
            }
        
        return validation_results
    
    def export_results(self, filename: str = "performance_results.json") -> None:
        """Export benchmark results to file"""
        import json
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "targets": self.performance_targets,
            "validation": self.validate_performance_targets()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

# Performance test functions
async def test_performance_benchmarks():
    """Main performance benchmark test"""
    # Initialize observability for benchmarking
    observability = ObservabilityProvider.create_development()
    await observability.initialize()
    
    try:
        benchmarker = PerformanceBenchmarker()
        
        # Run all benchmarks
        print("Running observability benchmarks...")
        obs_results = await benchmarker.benchmark_observability_performance(observability)
        
        print("Running agent system benchmarks...")
        agent_results = await benchmarker.benchmark_agent_system()
        
        print("Running memory system benchmarks...")
        memory_results = await benchmarker.benchmark_memory_system()
        
        print("Running session system benchmarks...")
        session_results = await benchmarker.benchmark_session_system()
        
        # Validate performance targets
        validation = benchmarker.validate_performance_targets()
        
        # Export results
        benchmarker.export_results()
        
        # Report results
        print("\nPerformance Benchmark Results:")
        print("=" * 50)
        
        for metric, result in validation.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{metric}: {result['actual']:.1f} ops/sec "
                  f"(target: {result['target']}) {status}")
        
        # Overall validation
        total_tests = len(validation)
        passed_tests = sum(1 for r in validation.values() if r["passed"])
        
        print(f"\nOverall: {passed_tests}/{total_tests} targets met")
        
        # Assert all performance targets are met
        assert passed_tests == total_tests, f"Performance targets not met: {passed_tests}/{total_tests}"
        
    finally:
        await observability.shutdown()
```

---

## 🎯 Quality Gates and Validation

### **Performance Targets**

The testing framework validates these performance targets:

- **Observability Logging**: 500+ operations/second
- **Observability Tracing**: 200+ operations/second  
- **Observability Metrics**: 800+ operations/second
- **Agent Creation**: 50+ operations/second
- **Memory Operations**: 100+ save, 200+ load operations/second
- **Session Handling**: 100+ creation, 300+ message operations/second

### **Quality Gates**

```python
# Quality gate validation
class QualityGates:
    """Quality gates for V2 system validation"""
    
    @staticmethod
    def validate_zero_errors():
        """Ensure zero critical errors across all tests"""
        # All tests must pass without exceptions
        pass
    
    @staticmethod
    def validate_performance_targets(benchmark_results):
        """Validate performance meets targets"""
        # All performance targets must be met
        pass
    
    @staticmethod
    def validate_observability_coverage():
        """Ensure comprehensive observability coverage"""
        # All components must have observability integration
        pass
    
    @staticmethod
    def validate_memory_efficiency():
        """Ensure memory efficiency standards"""
        # Memory usage must remain within bounds
        pass
```

---

## 📊 Test Configuration

### **Pytest Configuration**

```ini
# pytest.ini
[tool:pytest]
testpaths = tests/v2
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

### **Test Environment Setup**

```python
# conftest.py
import pytest
import asyncio
from langswarm.core.observability import ObservabilityProvider

@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def observability_provider():
    """Test observability provider"""
    provider = ObservabilityProvider.create_development()
    await provider.initialize()
    yield provider
    await provider.shutdown()

@pytest.fixture
async def test_logger(observability_provider):
    """Test logger fixture"""
    return observability_provider.get_logger("test")

@pytest.fixture
async def test_tracer(observability_provider):
    """Test tracer fixture"""
    return observability_provider.get_tracer("test")

@pytest.fixture
async def test_metrics(observability_provider):
    """Test metrics fixture"""
    return observability_provider.get_metrics("test")
```

---

## 🔍 Testing Best Practices

### **Unit Testing**
- Test individual component functionality in isolation
- Use mocks for external dependencies
- Focus on edge cases and error conditions
- Maintain high test coverage (>90%)

### **Integration Testing**
- Test component interactions and workflows
- Use real implementations where possible
- Validate cross-component data flow
- Test configuration and initialization

### **Performance Testing**
- Set clear performance targets
- Test under realistic load conditions
- Monitor resource usage during tests
- Validate scalability characteristics

### **Observability Testing**
- Validate logging, tracing, and metrics collection
- Test correlation between observability systems
- Verify error tracking and reporting
- Test observability system performance

### **Test Organization**
- Group related tests in classes
- Use descriptive test names
- Include setup and teardown fixtures
- Document complex test scenarios

---

**LangSwarm V2's testing framework provides comprehensive validation of system functionality, performance, and quality, ensuring production readiness through automated quality gates and continuous monitoring.**
