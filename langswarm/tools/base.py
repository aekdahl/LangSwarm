"""
LangSwarm V2 Base Tool Implementation

Provides base classes and utilities for implementing V2 tools.
All V2 tools should inherit from BaseTool or implement IToolInterface directly.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator
import logging

# V1/V2 compatibility for error handling
try:
    from langswarm.core.errors import handle_error, ToolError, ErrorContext
except ImportError:
    try:
        from langswarm.v1.core.errors import handle_error, ToolError, ErrorContext
    except ImportError:
        # Fallback for minimal environments
        class ToolError(Exception):
            pass
        class ErrorContext:
            def __init__(self, **kwargs):
                pass
        def handle_error(func):
            return func

from .interfaces import (
    IToolInterface,
    IToolMetadata, 
    IToolExecution,
    ToolType,
    ToolCapability,
    ToolSchema,
    ExecutionMode
)
from ..core.observability.auto_instrumentation import (
    AutoInstrumentedMixin, auto_trace_operation, auto_record_metric, auto_log_operation
)

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Structured result from tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def success_result(cls, data: Any, **metadata) -> 'ToolResult':
        """Create a successful result"""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod 
    def error_result(cls, error: str, **metadata) -> 'ToolResult':
        """Create an error result"""
        return cls(success=False, error=error, metadata=metadata)


class ToolMetadata(IToolMetadata):
    """Implementation of tool metadata"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        instruction: str = None,
        version: str = "1.0.0",
        tool_type: ToolType = ToolType.MCP,
        capabilities: List[ToolCapability] = None,
        methods: Dict[str, ToolSchema] = None,
        tags: List[str] = None,
        author: str = "LangSwarm",
        homepage: str = "",
        license: str = "MIT"
    ):
        self._id = id
        self._name = name
        self._description = description
        self._instruction = instruction
        self._version = version
        self._tool_type = tool_type
        self._capabilities = capabilities or []
        self._methods = methods or {}
        self._tags = tags or []
        self._author = author
        self._homepage = homepage
        self._license = license
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def instruction(self) -> Optional[str]:
        return self._instruction
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def tool_type(self) -> ToolType:
        return self._tool_type
    
    @property
    def capabilities(self) -> List[ToolCapability]:
        return self._capabilities.copy()
    
    @property
    def methods(self) -> Dict[str, ToolSchema]:
        return self._methods.copy()
    
    @property
    def tags(self) -> List[str]:
        return self._tags.copy()
    
    @property
    def author(self) -> str:
        return self._author
    
    @property
    def homepage(self) -> str:
        return self._homepage
    
    @property
    def license(self) -> str:
        return self._license
    
    def add_method(self, schema: ToolSchema):
        """Add a method schema"""
        self._methods[schema.name] = schema
    
    def add_capability(self, capability: ToolCapability):
        """Add a capability"""
        if capability not in self._capabilities:
            self._capabilities.append(capability)
    
    def add_tag(self, tag: str):
        """Add a tag"""
        if tag not in self._tags:
            self._tags.append(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": self.tool_type.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "methods": {name: schema.to_dict() for name, schema in self.methods.items()},
            "tags": self.tags,
            "author": self.author,
            "homepage": self.homepage,
            "license": self.license
        }
        if self.instruction:
            result["instruction"] = self.instruction
        return result


class ToolExecution(IToolExecution, AutoInstrumentedMixin):
    """Base implementation of tool execution with automatic instrumentation"""
    
    def __init__(self, tool_instance: Any):
        self._tool = tool_instance
        self._execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_time": 0.0
        }
        
        # Set component name for auto-instrumentation
        self._component_name = "tool"
        
        # Initialize auto-instrumentation mixin
        super().__init__()
    
    def _get_tool_name(self) -> str:
        """Safely get tool name with fallbacks for different tool types"""
        # Try V2 metadata (for V2 tools)
        if hasattr(self._tool, 'metadata') and hasattr(self._tool.metadata, 'id'):
            return self._tool.metadata.id
        
        # Try MCP tool identifier (this is the canonical MCP tool ID)
        if hasattr(self._tool, 'identifier'):
            return self._tool.identifier
        
        # Try legacy name attribute
        if hasattr(self._tool, 'name') and isinstance(self._tool.name, str):
            return self._tool.name.lower().replace(' ', '_')
        
        # Last resort: derive from class name (should rarely happen for built-in tools)
        class_name = type(self._tool).__name__
        # Handle common MCP tool class naming patterns
        if class_name.endswith('MCPTool'):
            # BigQueryVectorSearchMCPTool -> bigquery_vector_search
            tool_name = class_name[:-7]  # Remove 'MCPTool'
            # Convert CamelCase to snake_case
            import re
            tool_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', tool_name).lower()
            return f"mcp{tool_name}"
        
        return class_name.lower()
    
    async def execute(
        self, 
        method: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a tool method asynchronously with automatic instrumentation"""
        start_time = time.time()
        self._execution_stats["total_calls"] += 1
        
        tool_name = self._get_tool_name()
        
        with self._auto_trace("execute",
                             tool_name=tool_name,
                             method=method,
                             parameter_count=len(parameters) if parameters else 0,
                             has_context=context is not None) as span:
            
            try:
                self._auto_log("info", f"Executing tool method: {tool_name}.{method}",
                              tool_name=tool_name, method=method,
                              parameter_count=len(parameters) if parameters else 0)
                
                # Validate method and parameters
                if not self.validate_method(method, parameters):
                    error_msg = f"Method '{method}' not found or invalid parameters"
                    self._execution_stats["failed_calls"] += 1
                    
                    # Record validation error metrics
                    self._auto_record_metric("executions_total", 1.0, "counter",
                                           tool_name=tool_name, method=method, status="validation_error")
                    
                    if span:
                        span.add_tag("validation_error", True)
                        span.set_status("error")
                    
                    return ToolResult.error_result(error_msg)
                
                # Get the method handler
                handler = self._get_method_handler(method)
                if not handler:
                    error_msg = f"Method '{method}' not found"
                    self._execution_stats["failed_calls"] += 1
                    
                    # Record method not found error
                    self._auto_record_metric("executions_total", 1.0, "counter",
                                           tool_name=tool_name, method=method, status="method_not_found")
                    
                    if span:
                        span.add_tag("method_not_found", True)
                        span.set_status("error")
                    
                    return ToolResult.error_result(error_msg)
                
                if span:
                    span.add_tag("handler_type", "async" if asyncio.iscoroutinefunction(handler) else "sync")
                
                # Execute the method with nested tracing
                with self._auto_trace("method_call",
                                     tool_name=tool_name,
                                     method=method,
                                     is_async=asyncio.iscoroutinefunction(handler)) as method_span:
                    
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(**parameters)
                    else:
                        # Run sync method in executor
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: handler(**parameters)
                        )
                    
                    if method_span:
                        method_span.add_tag("result_type", type(result).__name__)
                        method_span.add_tag("result_size", len(str(result)) if result else 0)
                
                execution_time = time.time() - start_time
                self._execution_stats["successful_calls"] += 1
                self._execution_stats["total_time"] += execution_time
                
                # Record success metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       tool_name=tool_name, method=method, status="success")
                self._auto_record_metric("execution_duration_seconds", execution_time, "histogram",
                                       tool_name=tool_name, method=method)
                self._auto_record_metric("execution_result_size", len(str(result)) if result else 0, "histogram",
                                       tool_name=tool_name, method=method)
                
                if span:
                    span.add_tag("execution_success", True)
                    span.add_tag("execution_time_ms", execution_time * 1000)
                    span.add_tag("result_size", len(str(result)) if result else 0)
                
                self._auto_log("info", f"Tool execution completed: {tool_name}.{method}",
                              tool_name=tool_name, method=method,
                              execution_time_ms=execution_time * 1000,
                              success=True)
                
                return ToolResult.success_result(
                    result,
                    method=method,
                    execution_time=execution_time,
                    context=context
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self._execution_stats["failed_calls"] += 1
                self._execution_stats["total_time"] += execution_time
                
                # Use V2 error handling
                should_continue = handle_error(e, f"tool_{tool_name}")
                
                # Record error metrics
                self._auto_record_metric("executions_total", 1.0, "counter",
                                       tool_name=tool_name, method=method, status="error")
                self._auto_record_metric("execution_errors_total", 1.0, "counter",
                                       tool_name=tool_name, method=method, error_type=type(e).__name__)
                self._auto_record_metric("execution_duration_seconds", execution_time, "histogram",
                                       tool_name=tool_name, method=method, status="error")
                
                if span:
                    span.add_tag("execution_success", False)
                    span.add_tag("error_type", type(e).__name__)
                    span.add_tag("error_message", str(e))
                    span.add_tag("execution_time_ms", execution_time * 1000)
                    span.set_status("error")
                
                self._auto_log("error", f"Tool execution failed: {tool_name}.{method}: {e}",
                              tool_name=tool_name, method=method,
                              error_type=type(e).__name__,
                              execution_time_ms=execution_time * 1000)
                
                error_msg = str(e)
                return ToolResult.error_result(
                    error_msg,
                    method=method,
                    execution_time=execution_time,
                    context=context,
                    exception_type=type(e).__name__
                )
    
    def execute_sync(
        self,
        method: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a tool method synchronously"""
        # Run async method in sync context
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.execute(method, parameters, context))
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(self.execute(method, parameters, context))
    
    async def execute_stream(
        self,
        method: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Any]:
        """Execute a tool method with streaming results"""
        # Check if method supports streaming
        if not hasattr(self._tool, f"{method}_stream"):
            # Fallback to regular execution
            result = await self.execute(method, parameters, context)
            yield result
            return
        
        # Get streaming handler
        stream_handler = getattr(self._tool, f"{method}_stream")
        
        try:
            async for item in stream_handler(**parameters):
                yield item
        except Exception as e:
            handle_error(e, f"tool_{self._get_tool_name()}_stream")
            yield ToolResult.error_result(str(e), method=f"{method}_stream")
    
    def validate_method(self, method: str, parameters: Dict[str, Any]) -> bool:
        """Validate method and parameters"""
        # Check if method exists in metadata
        if hasattr(self._tool, 'metadata') and hasattr(self._tool.metadata, 'methods'):
            if method in self._tool.metadata.methods:
                schema = self._tool.metadata.methods[method]
                return schema.validate_parameters(parameters)
        
        # Fallback: check if method exists on tool (but not if it's an auto-generated Mock child)
        if hasattr(self._tool, method):
            attr = getattr(self._tool, method)
            # Don't consider auto-generated Mock children as valid methods
            if hasattr(attr, '_mock_parent') and hasattr(attr, '_mock_name'):
                return False
            return callable(attr)
        
        # Check if tool has run method
        if hasattr(self._tool, 'run'):
            run_attr = getattr(self._tool, 'run')
            # Don't consider auto-generated Mock children as valid
            if hasattr(run_attr, '_mock_parent') and hasattr(run_attr, '_mock_name'):
                return False
            return callable(run_attr)
        
        return False
    
    def _get_method_handler(self, method: str) -> Optional[callable]:
        """Get the handler for a method"""
        # Try direct method first
        if hasattr(self._tool, method):
            attr = getattr(self._tool, method)
            # Don't consider auto-generated Mock children as valid methods
            if hasattr(attr, '_mock_parent') and hasattr(attr, '_mock_name'):
                return None
            if callable(attr):
                return attr
        
        # Try run method with method parameter (like current MCP tools)
        if hasattr(self._tool, 'run'):
            run_method = getattr(self._tool, 'run')
            # Don't consider auto-generated Mock children as valid
            if hasattr(run_method, '_mock_parent') and hasattr(run_method, '_mock_name'):
                return None
            return lambda **params: run_method(input_data=params)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = self._execution_stats.copy()
        if stats["total_calls"] > 0:
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
            stats["average_time"] = stats["total_time"] / stats["total_calls"]
        else:
            stats["success_rate"] = 0.0
            stats["average_time"] = 0.0
        
        return stats


class BaseTool(IToolInterface):
    """
    Base class for all V2 tools.
    
    Provides standard implementation of IToolInterface with sensible defaults.
    Tools can inherit from this class and override specific methods as needed.
    """
    
    def __init__(
        self,
        metadata: Optional[ToolMetadata] = None,
        tool_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "1.0.0",
        tool_type: ToolType = ToolType.MCP,
        capabilities: List[ToolCapability] = None,
        tags: List[str] = None,
        config: Dict[str, Any] = None
    ):
        # Accept either metadata object or individual parameters
        if metadata is not None:
            self._metadata = metadata
        else:
            if tool_id is None or name is None or description is None:
                raise ValueError("Either metadata object or tool_id, name, and description must be provided")
            self._metadata = ToolMetadata(
                id=tool_id,
                name=name,
                description=description,
                version=version,
                tool_type=tool_type,
                capabilities=capabilities or [ToolCapability.READ],
                tags=tags or []
            )
        
        # Create execution handler
        self._execution = ToolExecution(self)
        
        # Store configuration
        self._config = config or {}
        self._initialized = False
        self._logger = logging.getLogger(f"tool.{tool_id}")
    
    @property
    def metadata(self) -> IToolMetadata:
        """Tool metadata"""
        return self._metadata
    
    @property
    def execution(self) -> IToolExecution:
        """Tool execution interface"""
        return self._execution
    
    @property
    def config(self) -> Dict[str, Any]:
        """Tool configuration"""
        return self._config.copy()
    
    @property
    def logger(self) -> logging.Logger:
        """Tool logger"""
        return self._logger
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the tool with configuration"""
        try:
            self._config.update(config)
            
            # Call subclass initialization
            await self._initialize_impl()
            
            self._initialized = True
            self._logger.info(f"Tool {self.metadata.id} initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize tool {self.metadata.id}: {e}")
            handle_error(e, f"tool_{self.metadata.id}_init")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup tool resources"""
        try:
            # Call subclass cleanup
            await self._cleanup_impl()
            
            self._initialized = False
            self._logger.info(f"Tool {self.metadata.id} cleaned up successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to cleanup tool {self.metadata.id}: {e}")
            handle_error(e, f"tool_{self.metadata.id}_cleanup")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check tool health status"""
        return {
            "tool_id": self.metadata.id,
            "initialized": self._initialized,
            "status": "healthy" if self._initialized else "not_initialized",
            "uptime": time.time() - getattr(self, '_start_time', time.time()),
            "statistics": self._execution.get_statistics(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM consumption"""
        schema = {
            "id": self.metadata.id,
            "name": self.metadata.name,
            "description": self.metadata.description,
            "type": self.metadata.tool_type.value,
            "methods": {}
        }
        
        # Add method schemas
        for method_name, method_schema in self.metadata.methods.items():
            schema["methods"][method_name] = method_schema.to_dict()
        
        return schema
    
    # Methods for subclasses to override
    
    async def _initialize_impl(self):
        """Override this method to provide custom initialization"""
        pass
    
    async def _cleanup_impl(self):
        """Override this method to provide custom cleanup"""
        pass
    
    # Convenience methods for adding metadata
    
    def add_method(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        returns: Dict[str, Any],
        required: List[str] = None,
        examples: List[Dict[str, Any]] = None
    ):
        """Add a method to the tool metadata"""
        schema = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            returns=returns,
            required=required,
            examples=examples
        )
        self._metadata.add_method(schema)
    
    def add_capability(self, capability: ToolCapability):
        """Add a capability to the tool"""
        self._metadata.add_capability(capability)
    
    def add_tag(self, tag: str):
        """Add a tag to the tool"""
        self._metadata.add_tag(tag)
    
    # Legacy compatibility methods
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Legacy compatibility method.
        
        This method provides compatibility with existing tool interfaces.
        Override this method to implement tool functionality.
        """
        raise NotImplementedError("Subclasses must implement the 'run' method or specific method handlers")
    
    def use(self, *args, **kwargs) -> Any:
        """Alias for run method (LangChain compatibility)"""
        return self.run(*args, **kwargs)


# Convenience functions for creating tools

def create_tool_metadata(
    tool_id: str,
    name: str,
    description: str,
    **kwargs
) -> ToolMetadata:
    """Create tool metadata with defaults"""
    return ToolMetadata(
        id=tool_id,
        name=name,
        description=description,
        **kwargs
    )


def create_method_schema(
    name: str,
    description: str,
    parameters: Dict[str, Any] = None,
    returns: Any = None,
    **kwargs
) -> ToolSchema:
    """Create method schema with defaults"""
    if returns is None:
        returns = {"type": "object", "description": "Method result"}
    elif isinstance(returns, str):
        returns = {"type": "object", "description": returns}
    
    return ToolSchema(
        name=name,
        description=description,
        parameters=parameters or {},
        returns=returns,
        **kwargs
    )
