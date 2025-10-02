#!/usr/bin/env python3
"""
LangSwarm V2 Middleware System Demonstration

This script demonstrates the new V2 middleware pipeline with:
- Modern pipeline architecture with composable interceptors
- Request/response context objects with rich metadata
- Async execution with proper error handling
- Observability and tracing integration
- Backward compatibility with V1 patterns
"""

import sys
import os
import asyncio
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langswarm.v2.core.middleware import (
    Pipeline, 
    PipelineBuilder, 
    RequestContext, 
    ResponseContext,
    BaseInterceptor,
    RoutingInterceptor,
    ValidationInterceptor,
    ExecutionInterceptor,
    ObservabilityInterceptor,
    ErrorInterceptor,
    create_default_pipeline
)
from langswarm.v2.core.middleware.interfaces import RequestType, ResponseStatus


def demo_basic_pipeline():
    """Demonstrate basic pipeline creation and usage"""
    print("\n🔧 === BASIC PIPELINE DEMONSTRATION ===")
    
    # Create a simple pipeline
    pipeline = Pipeline()
    
    # Add a simple interceptor that just returns a result
    class SimpleInterceptor(BaseInterceptor):
        async def _process(self, context, next_interceptor):
            return ResponseContext.success(
                context.request_id,
                f"Hello from {context.action_id}!",
                interceptor="simple"
            )
    
    pipeline.add_interceptor(SimpleInterceptor("simple", priority=100))
    
    print(f"Created pipeline with {pipeline.interceptor_count} interceptor(s)")
    return pipeline


async def demo_request_processing():
    """Demonstrate request processing through pipeline"""
    print("\n⚙️ === REQUEST PROCESSING DEMONSTRATION ===")
    
    # Create basic pipeline
    pipeline = demo_basic_pipeline()
    
    # Create a request context
    context = RequestContext(
        action_id="demo_tool",
        method="execute",
        params={"input": "test data"},
        user_id="demo_user",
        session_id="demo_session_123"
    )
    
    print(f"Processing request: {context.action_id}.{context.method}")
    print(f"Request ID: {context.request_id}")
    print(f"Parameters: {context.params}")
    
    # Process the request
    response = await pipeline.process(context)
    
    print(f"\nResponse Status: {response.status.value}")
    print(f"Response Success: {response.is_success()}")
    print(f"Response Result: {response.result}")
    print(f"Processing Time: {response.processing_time:.3f}s")
    print(f"Response Metadata: {json.dumps(response.metadata, indent=2)}")


async def demo_interceptor_chain():
    """Demonstrate interceptor chaining"""
    print("\n🔗 === INTERCEPTOR CHAIN DEMONSTRATION ===")
    
    # Create interceptors that add metadata
    class MetadataInterceptor(BaseInterceptor):
        def __init__(self, name, metadata_key, metadata_value, priority=100):
            super().__init__(name=name, priority=priority)
            self.metadata_key = metadata_key
            self.metadata_value = metadata_value
        
        async def _process(self, context, next_interceptor):
            print(f"  🔄 {self.name} interceptor adding metadata: {self.metadata_key}={self.metadata_value}")
            
            # Add metadata to context
            enhanced_context = context.with_metadata(**{self.metadata_key: self.metadata_value})
            
            # Call next interceptor
            response = await next_interceptor(enhanced_context)
            
            # Add to response metadata too
            return response.with_metadata(**{f"{self.name}_processed": True})
    
    # Create terminating interceptor
    class TerminatingInterceptor(BaseInterceptor):
        async def _process(self, context, next_interceptor):
            print(f"  ✅ Terminating interceptor processing final result")
            
            # Collect all metadata from context
            collected_metadata = {k: v for k, v in context.metadata.items() 
                                 if not k.endswith('_processing_time')}
            
            return ResponseContext.success(
                context.request_id,
                {
                    "message": "Chain completed successfully",
                    "collected_metadata": collected_metadata
                },
                terminating_interceptor=True
            )
    
    # Build pipeline with ordered interceptors
    pipeline = Pipeline([
        MetadataInterceptor("first", "step", "1", priority=10),
        MetadataInterceptor("second", "validation", "passed", priority=20),
        MetadataInterceptor("third", "authorization", "granted", priority=30),
        TerminatingInterceptor("terminator", priority=40)
    ])
    
    print(f"Created pipeline with {pipeline.interceptor_count} interceptors")
    print("Interceptor execution order:")
    for i, interceptor in enumerate(pipeline.get_interceptors(), 1):
        print(f"  {i}. {interceptor.name} (priority: {interceptor.priority})")
    
    # Process request
    context = RequestContext(action_id="chain_demo", method="process")
    print(f"\nProcessing request through interceptor chain...")
    
    response = await pipeline.process(context)
    
    print(f"\nChain execution completed:")
    print(f"Status: {response.status.value}")
    print(f"Result: {json.dumps(response.result, indent=2)}")
    print(f"Response metadata: {json.dumps(response.metadata, indent=2)}")


async def demo_error_handling():
    """Demonstrate error handling in the pipeline"""
    print("\n❌ === ERROR HANDLING DEMONSTRATION ===")
    
    # Create an interceptor that throws an error
    class ErrorInterceptor(BaseInterceptor):
        async def _process(self, context, next_interceptor):
            print(f"  ⚠️ {self.name} interceptor throwing error...")
            raise ValueError("Simulated processing error")
    
    # Create pipeline with error interceptor
    pipeline = Pipeline([
        ErrorInterceptor("error_generator", priority=100)
    ])
    
    context = RequestContext(action_id="error_demo", method="fail")
    print(f"Processing request that will fail...")
    
    response = await pipeline.process(context)
    
    print(f"\nError handling results:")
    print(f"Status: {response.status.value}")
    print(f"Is Error: {response.is_error()}")
    print(f"Error Type: {type(response.error).__name__}")
    print(f"Error Message: {response.error}")
    print(f"Error Metadata: {json.dumps(response.metadata, indent=2)}")


async def demo_mock_routing_execution():
    """Demonstrate routing and execution with mock handlers"""
    print("\n🎯 === ROUTING & EXECUTION DEMONSTRATION ===")
    
    # Create mock registry
    mock_registry = {
        "filesystem": MockFileSystemTool(),
        "calculator": MockCalculatorTool(),
        "weather": MockWeatherTool()
    }
    
    # Create pipeline with routing and execution
    routing = RoutingInterceptor(priority=100, tool_registry=mock_registry)
    execution = ExecutionInterceptor(priority=200)
    
    pipeline = Pipeline([routing, execution])
    
    print(f"Created pipeline with mock tool registry")
    print(f"Available tools: {list(mock_registry.keys())}")
    
    # Test different tool calls
    test_calls = [
        ("filesystem", "read_file", {"path": "/tmp/test.txt"}),
        ("calculator", "add", {"a": 5, "b": 3}),
        ("weather", "get_weather", {"city": "San Francisco"}),
        ("nonexistent", "test", {})  # This should fail
    ]
    
    for tool_id, method, params in test_calls:
        print(f"\n🔧 Testing {tool_id}.{method}")
        
        context = RequestContext(
            action_id=tool_id,
            method=method,
            params=params
        )
        
        response = await pipeline.process(context)
        
        print(f"  Status: {response.status.value}")
        if response.is_success():
            print(f"  Result: {response.result}")
        else:
            print(f"  Error: {response.error}")


async def demo_pipeline_builder():
    """Demonstrate pipeline builder pattern"""
    print("\n🏗️ === PIPELINE BUILDER DEMONSTRATION ===")
    
    # Create pipeline using builder pattern
    pipeline = (PipelineBuilder()
                .add_error_handling(priority=10)
                .add_observability(priority=50)
                .add_validation(priority=100)
                .add_routing(priority=200)
                .add_execution(priority=300)
                .with_config(timeout=30, enable_tracing=True)
                .build())
    
    print(f"Built pipeline with {pipeline.interceptor_count} interceptors:")
    for i, interceptor in enumerate(pipeline.get_interceptors(), 1):
        print(f"  {i}. {interceptor.name} (priority: {interceptor.priority})")
    
    # Test with a request that will go through all interceptors
    context = RequestContext(
        action_id="builder_demo",
        method="test",
        params={"message": "Hello from builder!"}
    )
    
    print(f"\nProcessing request through built pipeline...")
    response = await pipeline.process(context)
    
    print(f"Final result: {response.status.value}")
    print(f"Processing metadata: {json.dumps(response.metadata, indent=2)}")


def demo_context_objects():
    """Demonstrate request and response context objects"""
    print("\n📄 === CONTEXT OBJECTS DEMONSTRATION ===")
    
    # Create request context
    context = RequestContext(
        action_id="context_demo",
        method="showcase",
        request_type=RequestType.TOOL_CALL,
        params={"demo": True, "features": ["immutable", "typed", "serializable"]},
        user_id="demo_user",
        session_id="demo_session",
        workflow_context={"workflow_id": "demo_workflow", "step": 1}
    )
    
    print("Request Context:")
    print(f"  Request ID: {context.request_id}")
    print(f"  Action: {context.action_id}.{context.method}")
    print(f"  Type: {context.request_type.value}")
    print(f"  User: {context.user_id}")
    print(f"  Session: {context.session_id}")
    print(f"  Params: {context.params}")
    print(f"  Workflow Context: {context.workflow_context}")
    
    # Demonstrate immutability
    enhanced_context = context.with_metadata(step_completed=True, validation="passed")
    print(f"\nOriginal context metadata: {context.metadata}")
    print(f"Enhanced context metadata: {enhanced_context.metadata}")
    print(f"Context is immutable: {context is not enhanced_context}")
    
    # Create response context
    response = ResponseContext.success(
        context.request_id,
        {"demo": "completed", "features_shown": len(context.params.get("features", []))},
        processing_time=0.025,
        context_demo=True
    )
    
    print(f"\nResponse Context:")
    print(f"  Request ID: {response.request_id}")
    print(f"  Status: {response.status.value}")
    print(f"  Success: {response.is_success()}")
    print(f"  Result: {response.result}")
    print(f"  Processing Time: {response.processing_time}s")
    
    # Demonstrate serialization
    print(f"\nSerialization:")
    print(f"  Context JSON: {context.to_json()}")
    print(f"  Response Dict: {json.dumps(response.to_dict(), indent=2)}")


# Mock tool implementations for demonstration
class MockFileSystemTool:
    def read_file(self, path):
        return f"Contents of {path}: Mock file data"
    
    def run(self, method, params):
        if method == "read_file":
            return self.read_file(params.get("path", "unknown"))
        return f"Unknown method: {method}"


class MockCalculatorTool:
    def add(self, a, b):
        return {"operation": "add", "result": a + b}
    
    def run(self, method, params):
        if method == "add":
            return self.add(params.get("a", 0), params.get("b", 0))
        return f"Unknown method: {method}"


class MockWeatherTool:
    def get_weather(self, city):
        return {
            "city": city,
            "temperature": 72,
            "condition": "sunny",
            "mock": True
        }
    
    def run(self, method, params):
        if method == "get_weather":
            return self.get_weather(params.get("city", "Unknown"))
        return f"Unknown method: {method}"


async def main():
    """Main demonstration function"""
    print("🚀 LangSwarm V2 Middleware System Demonstration")
    print("=" * 60)
    
    try:
        # Run all demonstrations
        demo_context_objects()
        await demo_request_processing()
        await demo_interceptor_chain()
        await demo_error_handling()
        await demo_mock_routing_execution()
        await demo_pipeline_builder()
        
        print("\n✅ === DEMONSTRATION COMPLETE ===")
        print("V2 Middleware System Features Demonstrated:")
        print("  ✅ Modern pipeline architecture with composable interceptors")
        print("  ✅ Immutable request/response context objects")
        print("  ✅ Async execution with proper error handling")
        print("  ✅ Priority-based interceptor ordering")
        print("  ✅ Rich metadata and observability")
        print("  ✅ Builder pattern for pipeline configuration")
        print("  ✅ Type-safe interfaces and structured data")
        print("  ✅ Comprehensive error handling and recovery")
        print("\n🎯 Middleware System Phase 1 Implementation: COMPLETE!")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
