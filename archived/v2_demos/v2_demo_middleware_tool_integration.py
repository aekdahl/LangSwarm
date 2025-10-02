#!/usr/bin/env python3
"""
LangSwarm V2 Middleware-Tool Integration Demonstration

This script demonstrates the integration between the V2 middleware pipeline
and the V2 tool system, showing how tools can be executed through the 
middleware for enhanced request processing, validation, and observability.
"""

import asyncio
import json
from datetime import datetime


async def demo_basic_tool_execution():
    """Demonstrate basic tool execution through middleware"""
    print("=" * 60)
    print("🔧 BASIC TOOL EXECUTION THROUGH MIDDLEWARE")
    print("=" * 60)
    
    try:
        from langswarm.v2.core.middleware import create_default_pipeline
        from langswarm.v2.core.middleware.context import RequestContext, RequestType
        from langswarm.v2.tools.builtin import SystemStatusTool
        
        # Create middleware pipeline and tool
        pipeline = create_default_pipeline()
        tool = SystemStatusTool()
        
        print(f"✅ Created middleware pipeline with {len(pipeline._interceptors)} interceptors")
        print(f"✅ Created tool: {tool.metadata.name}")
        print()
        
        # Create request context for tool execution
        context = RequestContext(
            action_id="system_status.health_check",
            method="health_check",
            request_type=RequestType.TOOL_CALL,
            params={},
            metadata={
                "tool_id": tool.metadata.id,
                "tool_name": tool.metadata.name,
                "tool_type": tool.metadata.tool_type.value
            }
        )
        
        print("📤 Processing tool request through middleware:")
        print(f"   Action: {context.action_id}")
        print(f"   Method: {context.method}")
        print(f"   Request ID: {context.request_id}")
        print()
        
        # Process through middleware (this will go through all interceptors)
        response = await pipeline.process(context)
        
        print("📥 Middleware Response:")
        print(f"   Status: {response.status.value}")
        print(f"   Success: {response.is_success()}")
        print(f"   Processing time: {response.processing_time:.3f}s")
        print(f"   Interceptors used: {response.metadata.get('interceptor_chain', [])}")
        print()
        
    except Exception as e:
        print(f"❌ Basic tool execution demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_tool_execution_interceptor():
    """Demonstrate custom tool execution interceptor"""
    print("=" * 60)
    print("🛠️ CUSTOM TOOL EXECUTION INTERCEPTOR")
    print("=" * 60)
    
    try:
        from langswarm.v2.core.middleware import Pipeline
        from langswarm.v2.core.middleware.context import RequestContext, ResponseContext, RequestType
        from langswarm.v2.core.middleware.interfaces import ResponseStatus
        from langswarm.v2.core.middleware.interceptors.base import BaseInterceptor
        from langswarm.v2.tools.builtin import TextProcessorTool
        
        # Create custom tool execution interceptor
        class ToolExecutionInterceptor(BaseInterceptor):
            def __init__(self):
                super().__init__("tool_executor", priority=100)
                self.tools = {}
            
            def add_tool(self, tool):
                """Register a tool for execution"""
                self.tools[tool.metadata.name] = tool
                self.tools[tool.metadata.id] = tool
            
            async def _process(self, context: RequestContext, next_interceptor):
                # Check if this is a tool call
                if context.request_type == RequestType.TOOL_CALL:
                    tool_id = context.metadata.get("tool_id") or context.action_id.split(".")[0]
                    
                    if tool_id in self.tools:
                        tool = self.tools[tool_id]
                        
                        # Execute the tool method
                        try:
                            if hasattr(tool, context.method):
                                method_func = getattr(tool, context.method)
                                result = await method_func(**context.params)
                            else:
                                # Use run method
                                result_coro = tool.run({
                                    "method": context.method,
                                    **context.params
                                })
                                if asyncio.iscoroutine(result_coro):
                                    result = await result_coro
                                else:
                                    result = result_coro
                            
                            return ResponseContext.success(
                                context.request_id,
                                result,
                                tool_executed=tool.metadata.name,
                                tool_method=context.method
                            )
                        except Exception as e:
                            return ResponseContext.error_response(
                                context.request_id,
                                e,
                                ResponseStatus.INTERNAL_ERROR,
                                tool_execution_error=str(e)
                            )
                    else:
                        return ResponseContext.error_response(
                            context.request_id,
                            ValueError(f"Tool not found: {tool_id}"),
                            ResponseStatus.NOT_FOUND
                        )
                
                # Not a tool call, continue pipeline
                return await next_interceptor(context)
        
        # Create pipeline with tool execution interceptor
        pipeline = Pipeline()
        tool_interceptor = ToolExecutionInterceptor()
        
        # Register some tools
        text_tool = TextProcessorTool()
        tool_interceptor.add_tool(text_tool)
        
        pipeline.add_interceptor(tool_interceptor)
        
        print(f"✅ Created pipeline with custom tool interceptor")
        print(f"✅ Registered tool: {text_tool.metadata.name}")
        print()
        
        # Test tool execution through middleware
        context = RequestContext(
            action_id="text_processor.analyze",
            method="analyze",
            request_type=RequestType.TOOL_CALL,
            params={"text": "LangSwarm V2 middleware integration test"},
            metadata={
                "tool_id": text_tool.metadata.id,
                "tool_name": text_tool.metadata.name
            }
        )
        
        print("📤 Executing tool through custom interceptor:")
        print(f"   Tool: {context.metadata['tool_name']}")
        print(f"   Method: {context.method}")
        print(f"   Text: '{context.params['text']}'")
        print()
        
        response = await pipeline.process(context)
        
        print("📥 Tool Execution Result:")
        print(f"   Status: {response.status.value}")
        print(f"   Success: {response.is_success()}")
        if response.is_success():
            result = response.result
            print(f"   Words analyzed: {result.get('words', 0)}")
            print(f"   Characters: {result.get('length', 0)}")
            print(f"   Unique words: {result.get('unique_words', 0)}")
        print(f"   Tool executed: {response.metadata.get('tool_executed', 'none')}")
        print()
        
    except Exception as e:
        print(f"❌ Tool execution interceptor demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_tool_validation_middleware():
    """Demonstrate tool parameter validation through middleware"""
    print("=" * 60)
    print("🔍 TOOL PARAMETER VALIDATION MIDDLEWARE")
    print("=" * 60)
    
    try:
        from langswarm.v2.core.middleware import Pipeline
        from langswarm.v2.core.middleware.context import RequestContext, ResponseContext, RequestType
        from langswarm.v2.core.middleware.interfaces import ResponseStatus
        from langswarm.v2.core.middleware.interceptors.base import BaseInterceptor
        from langswarm.v2.tools.builtin import FileOperationsTool
        
        # Create validation interceptor
        class ToolValidationInterceptor(BaseInterceptor):
            def __init__(self):
                super().__init__("tool_validator", priority=50)  # Run before execution
            
            async def _process(self, context: RequestContext, next_interceptor):
                if context.request_type == RequestType.TOOL_CALL:
                    # Validate tool parameters
                    validation_result = self._validate_tool_params(context)
                    if not validation_result["valid"]:
                        return ResponseContext.error_response(
                            context.request_id,
                            ValueError(validation_result["error"]),
                            ResponseStatus.BAD_REQUEST,
                            validation_error=validation_result["error"]
                        )
                
                return await next_interceptor(context)
            
            def _validate_tool_params(self, context: RequestContext):
                """Validate tool parameters"""
                # Basic validation rules
                if context.action_id.startswith("file_operations"):
                    if context.method in ["read_file", "write_file", "delete_file"]:
                        if "path" not in context.params:
                            return {"valid": False, "error": "Missing required parameter: path"}
                        
                        path = context.params["path"]
                        if not isinstance(path, str) or not path.strip():
                            return {"valid": False, "error": "Parameter 'path' must be a non-empty string"}
                        
                        # Security check: prevent access to sensitive paths
                        if any(sensitive in path.lower() for sensitive in ["/etc/", "/root/", "passwd"]):
                            return {"valid": False, "error": "Access to sensitive paths is not allowed"}
                
                return {"valid": True}
        
        # Create execution interceptor (simplified)
        class SimpleToolExecutor(BaseInterceptor):
            def __init__(self):
                super().__init__("simple_executor", priority=100)
                import tempfile
                self.file_tool = FileOperationsTool(base_path=tempfile.gettempdir())
            
            async def _process(self, context: RequestContext, next_interceptor):
                if context.request_type == RequestType.TOOL_CALL and context.action_id.startswith("file_operations"):
                    try:
                        method_func = getattr(self.file_tool, context.method)
                        result = await method_func(**context.params)
                        return ResponseContext.success(context.request_id, result)
                    except Exception as e:
                        return ResponseContext.error_response(context.request_id, e)
                
                return await next_interceptor(context)
        
        # Create pipeline with validation
        pipeline = Pipeline()
        pipeline.add_interceptor(ToolValidationInterceptor())
        pipeline.add_interceptor(SimpleToolExecutor())
        
        print("✅ Created pipeline with validation and execution interceptors")
        print()
        
        # Test valid request
        print("🔍 Testing valid file operation:")
        valid_context = RequestContext(
            action_id="file_operations.file_exists",
            method="file_exists",
            request_type=RequestType.TOOL_CALL,
            params={"path": "test.txt"}
        )
        
        response = await pipeline.process(valid_context)
        print(f"   Status: {response.status.value}")
        print(f"   Success: {response.is_success()}")
        if response.is_success():
            print(f"   File exists: {response.result}")
        print()
        
        # Test invalid request (missing parameter)
        print("🚫 Testing invalid request (missing parameter):")
        invalid_context1 = RequestContext(
            action_id="file_operations.read_file",
            method="read_file",
            request_type=RequestType.TOOL_CALL,
            params={}  # Missing 'path' parameter
        )
        
        response = await pipeline.process(invalid_context1)
        print(f"   Status: {response.status.value}")
        print(f"   Success: {response.is_success()}")
        if response.is_error():
            print(f"   Error: {response.metadata.get('validation_error', 'Unknown error')}")
        print()
        
        # Test security validation
        print("🛡️ Testing security validation (sensitive path):")
        security_context = RequestContext(
            action_id="file_operations.read_file",
            method="read_file",
            request_type=RequestType.TOOL_CALL,
            params={"path": "/etc/passwd"}  # Sensitive path
        )
        
        response = await pipeline.process(security_context)
        print(f"   Status: {response.status.value}")
        print(f"   Success: {response.is_success()}")
        if response.is_error():
            print(f"   Security Error: {response.metadata.get('validation_error', 'Unknown error')}")
        print()
        
    except Exception as e:
        print(f"❌ Tool validation middleware demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_tool_observability():
    """Demonstrate tool observability through middleware"""
    print("=" * 60)
    print("📊 TOOL OBSERVABILITY MIDDLEWARE")
    print("=" * 60)
    
    try:
        from langswarm.v2.core.middleware import Pipeline
        from langswarm.v2.core.middleware.context import RequestContext, ResponseContext, RequestType
        from langswarm.v2.core.middleware.interceptors.base import BaseInterceptor
        from langswarm.v2.tools.builtin import SystemStatusTool, TextProcessorTool
        import time
        
        # Create observability interceptor
        class ToolObservabilityInterceptor(BaseInterceptor):
            def __init__(self):
                super().__init__("tool_observability", priority=10)  # Run first
                self.metrics = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "tools_used": {},
                    "average_execution_time": 0.0
                }
                self.execution_times = []
            
            async def _process(self, context: RequestContext, next_interceptor):
                if context.request_type == RequestType.TOOL_CALL:
                    # Track request
                    self.metrics["total_requests"] += 1
                    start_time = time.time()
                    
                    # Extract tool info
                    tool_name = context.metadata.get("tool_name", context.action_id.split(".")[0])
                    if tool_name not in self.metrics["tools_used"]:
                        self.metrics["tools_used"][tool_name] = 0
                    self.metrics["tools_used"][tool_name] += 1
                    
                    print(f"   📈 Tracking: {tool_name}.{context.method}")
                    
                    # Process request
                    response = await next_interceptor(context)
                    
                    # Track completion
                    execution_time = time.time() - start_time
                    self.execution_times.append(execution_time)
                    
                    if response.is_success():
                        self.metrics["successful_requests"] += 1
                        print(f"   ✅ Success: {execution_time:.3f}s")
                    else:
                        self.metrics["failed_requests"] += 1
                        print(f"   ❌ Failed: {execution_time:.3f}s")
                    
                    # Update average
                    self.metrics["average_execution_time"] = sum(self.execution_times) / len(self.execution_times)
                    
                    # Add observability metadata
                    return response.with_metadata(
                        execution_time=execution_time,
                        total_requests=self.metrics["total_requests"],
                        tool_metrics=self.metrics["tools_used"].copy()
                    )
                
                return await next_interceptor(context)
            
            def get_metrics(self):
                return self.metrics.copy()
        
        # Simple tool executor
        class MockToolExecutor(BaseInterceptor):
            def __init__(self):
                super().__init__("mock_executor", priority=100)
                self.tools = {
                    "system_status": SystemStatusTool(),
                    "text_processor": TextProcessorTool()
                }
            
            async def _process(self, context: RequestContext, next_interceptor):
                if context.request_type == RequestType.TOOL_CALL:
                    tool_name = context.action_id.split(".")[0]
                    if tool_name in self.tools:
                        tool = self.tools[tool_name]
                        try:
                            # Simulate some processing time
                            await asyncio.sleep(0.1)
                            
                            result_coro = tool.run({"method": context.method, **context.params})
                            if asyncio.iscoroutine(result_coro):
                                result = await result_coro
                            else:
                                result = result_coro
                            
                            return ResponseContext.success(context.request_id, result)
                        except Exception as e:
                            return ResponseContext.error_response(context.request_id, e)
                
                return await next_interceptor(context)
        
        # Create pipeline with observability
        pipeline = Pipeline()
        observability = ToolObservabilityInterceptor()
        pipeline.add_interceptor(observability)
        pipeline.add_interceptor(MockToolExecutor())
        
        print("✅ Created pipeline with observability tracking")
        print()
        
        # Execute several tool calls
        test_calls = [
            ("system_status.health_check", "health_check", {}),
            ("text_processor.analyze", "analyze", {"text": "Hello World"}),
            ("system_status.system_info", "system_info", {}),
            ("text_processor.transform", "transform", {"text": "test", "operations": ["upper"]}),
            ("system_status.health_check", "health_check", {}),  # Duplicate to show metrics
        ]
        
        print("🔄 Executing multiple tool calls:")
        for action_id, method, params in test_calls:
            context = RequestContext(
                action_id=action_id,
                method=method,
                request_type=RequestType.TOOL_CALL,
                params=params,
                metadata={"tool_name": action_id.split(".")[0]}
            )
            
            response = await pipeline.process(context)
        
        print()
        print("📊 Final Metrics:")
        metrics = observability.get_metrics()
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Successful: {metrics['successful_requests']}")
        print(f"   Failed: {metrics['failed_requests']}")
        print(f"   Average execution time: {metrics['average_execution_time']:.3f}s")
        print(f"   Tools used: {dict(metrics['tools_used'])}")
        print()
        
    except Exception as e:
        print(f"❌ Tool observability demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all middleware-tool integration demonstrations"""
    print("🚀 LangSwarm V2 Middleware-Tool Integration Demonstration")
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Run all demos
    await demo_basic_tool_execution()
    await demo_tool_execution_interceptor()
    await demo_tool_validation_middleware()
    await demo_tool_observability()
    
    print("=" * 60)
    print("✅ Middleware-Tool Integration Demonstration Complete!")
    print("=" * 60)
    print()
    print("🎯 Key Capabilities Demonstrated:")
    print("   • Tool execution through middleware pipeline")
    print("   • Custom tool execution interceptors")
    print("   • Parameter validation and security controls")
    print("   • Comprehensive observability and metrics")
    print("   • Request/response context management")
    print("   • Error handling and status reporting")
    print()
    print("The V2 middleware and tool systems work seamlessly together!")


if __name__ == "__main__":
    asyncio.run(main())
