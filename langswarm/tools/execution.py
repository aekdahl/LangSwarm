"""
LangSwarm V2 Tool Execution Engine

Advanced execution engine that integrates with V2 middleware and error systems.
Provides async execution, context management, and comprehensive observability.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator
import logging

from langswarm.core.errors import handle_error, ToolError, ErrorContext
from langswarm.core.middleware.context import RequestContext, ResponseContext
from langswarm.core.middleware.interfaces import ResponseStatus

from .interfaces import IToolInterface, IToolExecution
from .base import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for tool execution"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
    
    def with_retry(self) -> 'ExecutionContext':
        """Create context for retry attempt"""
        return ExecutionContext(
            user_id=self.user_id,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
            request_id=self.request_id,
            timestamp=datetime.now(),
            metadata=self.metadata,
            timeout=self.timeout,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries
        )


@dataclass
class ExecutionResult:
    """Result from tool execution"""
    success: bool
    tool_id: str
    method: str
    data: Any = None
    error: Optional[str] = None
    context: Optional[ExecutionContext] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": self.success,
            "tool_id": self.tool_id,
            "method": self.method,
            "data": self.data,
            "error": self.error,
            "context": self.context.to_dict() if self.context else None,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def to_tool_result(self) -> ToolResult:
        """Convert to ToolResult for backward compatibility"""
        return ToolResult(
            success=self.success,
            data=self.data,
            error=self.error,
            metadata=self.metadata,
            execution_time=self.execution_time,
            timestamp=self.timestamp
        )
    
    @classmethod
    def success_result(
        cls, 
        tool_id: str, 
        method: str, 
        data: Any,
        context: Optional[ExecutionContext] = None,
        **metadata
    ) -> 'ExecutionResult':
        """Create successful execution result"""
        return cls(
            success=True,
            tool_id=tool_id,
            method=method,
            data=data,
            context=context,
            metadata=metadata
        )
    
    @classmethod
    def error_result(
        cls,
        tool_id: str,
        method: str,
        error: str,
        context: Optional[ExecutionContext] = None,
        **metadata
    ) -> 'ExecutionResult':
        """Create error execution result"""
        return cls(
            success=False,
            tool_id=tool_id,
            method=method,
            error=error,
            context=context,
            metadata=metadata
        )


class ToolExecutor:
    """
    Advanced tool execution engine with middleware integration.
    
    Features:
    - Async execution with timeout handling
    - Retry logic with exponential backoff
    - Integration with V2 middleware pipeline
    - Comprehensive error handling
    - Execution statistics and monitoring
    - Context propagation and metadata tracking
    """
    
    def __init__(
        self,
        default_timeout: float = 30.0,
        default_retries: int = 3,
        enable_statistics: bool = True
    ):
        self.default_timeout = default_timeout
        self.default_retries = default_retries
        self.enable_statistics = enable_statistics
        
        # Execution statistics
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "retried_executions": 0,
            "timeout_executions": 0,
            "total_execution_time": 0.0
        }
        
        # Per-tool statistics
        self._tool_stats: Dict[str, Dict[str, Any]] = {}
        
        self._logger = logging.getLogger("tool_executor")
    
    async def execute(
        self,
        tool: IToolInterface,
        method: str,
        parameters: Dict[str, Any],
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """Execute a tool method with full error handling and retry logic"""
        # Create execution context if not provided
        if context is None:
            context = ExecutionContext(
                timeout=self.default_timeout,
                max_retries=self.default_retries
            )
        
        tool_id = tool.metadata.id
        start_time = time.time()
        
        # Update statistics
        if self.enable_statistics:
            self._update_execution_stats(tool_id, "started")
        
        try:
            # Execute with retry logic
            result = await self._execute_with_retry(tool, method, parameters, context)
            
            # Update timing
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Update statistics
            if self.enable_statistics:
                status = "success" if result.success else "error"
                self._update_execution_stats(tool_id, status, execution_time)
            
            self._logger.debug(
                f"Tool execution completed: {tool_id}.{method} "
                f"in {execution_time:.3f}s (success: {result.success})"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Handle unexpected errors
            handle_error(e, f"tool_executor_{tool_id}")
            
            if self.enable_statistics:
                self._update_execution_stats(tool_id, "error", execution_time)
            
            return ExecutionResult.error_result(
                tool_id=tool_id,
                method=method,
                error=f"Execution engine error: {str(e)}",
                context=context,
                execution_time=execution_time,
                engine_error=True
            )
    
    async def _execute_with_retry(
        self,
        tool: IToolInterface,
        method: str,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute with retry logic"""
        last_error = None
        
        for attempt in range(context.max_retries + 1):
            try:
                # Update context for retry
                if attempt > 0:
                    context = context.with_retry()
                    if self.enable_statistics:
                        self._stats["retried_executions"] += 1
                    
                    self._logger.debug(
                        f"Retrying tool execution: {tool.metadata.id}.{method} "
                        f"(attempt {attempt + 1}/{context.max_retries + 1})"
                    )
                    
                    # Exponential backoff
                    await asyncio.sleep(min(2 ** attempt, 10))
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute_tool_method(tool, method, parameters, context),
                    timeout=context.timeout
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Tool execution timeout after {context.timeout}s"
                if self.enable_statistics:
                    self._stats["timeout_executions"] += 1
                
                self._logger.warning(
                    f"Tool execution timeout: {tool.metadata.id}.{method} "
                    f"(attempt {attempt + 1})"
                )
                
                # Don't retry timeouts on final attempt
                if attempt >= context.max_retries:
                    break
                    
            except Exception as e:
                last_error = str(e)
                self._logger.warning(
                    f"Tool execution error: {tool.metadata.id}.{method} "
                    f"(attempt {attempt + 1}): {e}"
                )
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    break
        
        # All retries exhausted
        return ExecutionResult.error_result(
            tool_id=tool.metadata.id,
            method=method,
            error=last_error or "Unknown error",
            context=context,
            retries_exhausted=True
        )
    
    async def _execute_tool_method(
        self,
        tool: IToolInterface,
        method: str,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute the actual tool method"""
        try:
            # Use tool's execution interface
            result = await tool.execution.execute(
                method=method,
                parameters=parameters,
                context=context.to_dict()
            )
            
            # Convert ToolResult to ExecutionResult
            if isinstance(result, ToolResult):
                return ExecutionResult(
                    success=result.success,
                    tool_id=tool.metadata.id,
                    method=method,
                    data=result.data,
                    error=result.error,
                    context=context,
                    execution_time=result.execution_time,
                    timestamp=result.timestamp,
                    metadata=result.metadata
                )
            else:
                # Handle direct result
                return ExecutionResult.success_result(
                    tool_id=tool.metadata.id,
                    method=method,
                    data=result,
                    context=context
                )
                
        except Exception as e:
            error_msg = str(e)
            
            # Enhanced error context
            error_context = ErrorContext(
                component=f"tool_{tool.metadata.id}",
                operation=method,
                metadata={
                    "tool_type": tool.metadata.tool_type.value,
                    "parameters": parameters,
                    "context": context.to_dict()
                }
            )
            
            # Use V2 error handling
            handle_error(e, f"tool_{tool.metadata.id}_{method}")
            
            return ExecutionResult.error_result(
                tool_id=tool.metadata.id,
                method=method,
                error=error_msg,
                context=context,
                exception_type=type(e).__name__
            )
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry"""
        # Network-related errors are typically retryable
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # Some tool errors are retryable
        if isinstance(error, ToolError):
            return error.severity.value in ["warning", "error"]  # Not critical
        
        # Default: don't retry
        return False
    
    def _update_execution_stats(
        self,
        tool_id: str,
        status: str,
        execution_time: float = 0.0
    ):
        """Update execution statistics"""
        # Global stats
        if status == "started":
            self._stats["total_executions"] += 1
        elif status == "success":
            self._stats["successful_executions"] += 1
            self._stats["total_execution_time"] += execution_time
        elif status == "error":
            self._stats["failed_executions"] += 1
            self._stats["total_execution_time"] += execution_time
        
        # Per-tool stats
        if tool_id not in self._tool_stats:
            self._tool_stats[tool_id] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "average_time": 0.0
            }
        
        tool_stats = self._tool_stats[tool_id]
        
        if status == "started":
            tool_stats["executions"] += 1
        elif status == "success":
            tool_stats["successes"] += 1
            tool_stats["total_time"] += execution_time
        elif status == "error":
            tool_stats["failures"] += 1
            tool_stats["total_time"] += execution_time
        
        # Update average time
        if tool_stats["executions"] > 0:
            tool_stats["average_time"] = tool_stats["total_time"] / tool_stats["executions"]
    
    async def execute_batch(
        self,
        batch_requests: List[Dict[str, Any]],
        context: Optional[ExecutionContext] = None,
        max_concurrent: int = 10
    ) -> List[ExecutionResult]:
        """Execute multiple tool calls concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(request: Dict[str, Any]) -> ExecutionResult:
            async with semaphore:
                tool = request["tool"]
                method = request["method"]
                parameters = request.get("parameters", {})
                
                return await self.execute(tool, method, parameters, context)
        
        # Execute all requests concurrently
        tasks = [execute_single(request) for request in batch_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                request = batch_requests[i]
                processed_results.append(
                    ExecutionResult.error_result(
                        tool_id=request["tool"].metadata.id,
                        method=request["method"],
                        error=f"Batch execution error: {str(result)}",
                        context=context,
                        batch_error=True
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        global_stats = self._stats.copy()
        
        # Calculate derived statistics
        if global_stats["total_executions"] > 0:
            global_stats["success_rate"] = (
                global_stats["successful_executions"] / global_stats["total_executions"]
            )
            global_stats["average_execution_time"] = (
                global_stats["total_execution_time"] / global_stats["total_executions"]
            )
        else:
            global_stats["success_rate"] = 0.0
            global_stats["average_execution_time"] = 0.0
        
        return {
            "global": global_stats,
            "per_tool": self._tool_stats.copy()
        }
    
    def reset_statistics(self):
        """Reset all statistics"""
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "retried_executions": 0,
            "timeout_executions": 0,
            "total_execution_time": 0.0
        }
        self._tool_stats.clear()
        self._logger.info("Tool executor statistics reset")


# Global tool executor instance
_global_executor = ToolExecutor()


def get_global_executor() -> ToolExecutor:
    """Get the global tool executor"""
    return _global_executor


async def execute_tool(
    tool: IToolInterface,
    method: str,
    parameters: Dict[str, Any],
    context: Optional[ExecutionContext] = None
) -> ExecutionResult:
    """Convenience function for tool execution"""
    return await _global_executor.execute(tool, method, parameters, context)
