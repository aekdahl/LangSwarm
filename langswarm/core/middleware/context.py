"""
LangSwarm V2 Middleware Context Objects

Immutable request and response context objects that flow through the middleware pipeline.
Provides type safety and structured data handling.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import json

from .interfaces import IRequestContext, IResponseContext, RequestType, ResponseStatus


@dataclass(frozen=True)
class MiddlewareMetadata:
    """Metadata container for middleware operations"""
    execution_time: Optional[float] = None
    handler_type: Optional[str] = None
    handler_name: Optional[str] = None
    interceptor_chain: list = field(default_factory=list)
    retry_count: int = 0
    cache_hit: bool = False
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            'execution_time': self.execution_time,
            'handler_type': self.handler_type,
            'handler_name': self.handler_name,
            'interceptor_chain': self.interceptor_chain,
            'retry_count': self.retry_count,
            'cache_hit': self.cache_hit,
            'trace_id': self.trace_id,
            'span_id': self.span_id
        }


@dataclass(frozen=True)
class RequestContext:
    """
    Immutable request context that flows through the middleware pipeline.
    Contains all information needed to process a request.
    
    This is a concrete implementation that satisfies the IRequestContext interface.
    """
    action_id: str
    method: str
    request_type: RequestType = RequestType.TOOL_CALL
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_context: Optional[Dict[str, Any]] = None
    
    def with_metadata(self, **new_metadata) -> 'RequestContext':
        """Create new context with additional metadata"""
        updated_metadata = {**self.metadata, **new_metadata}
        return RequestContext(
            request_id=self.request_id,
            request_type=self.request_type,
            action_id=self.action_id,
            method=self.method,
            params=self.params,
            metadata=updated_metadata,
            timestamp=self.timestamp,
            user_id=self.user_id,
            session_id=self.session_id,
            workflow_context=self.workflow_context
        )
    
    def with_params(self, **new_params) -> 'RequestContext':
        """Create new context with updated parameters"""
        updated_params = {**self.params, **new_params}
        return RequestContext(
            request_id=self.request_id,
            request_type=self.request_type,
            action_id=self.action_id,
            method=self.method,
            params=updated_params,
            metadata=self.metadata,
            timestamp=self.timestamp,
            user_id=self.user_id,
            session_id=self.session_id,
            workflow_context=self.workflow_context
        )
    
    def with_workflow_context(self, workflow_context: Dict[str, Any]) -> 'RequestContext':
        """Create new context with workflow context"""
        return RequestContext(
            request_id=self.request_id,
            request_type=self.request_type,
            action_id=self.action_id,
            method=self.method,
            params=self.params,
            metadata=self.metadata,
            timestamp=self.timestamp,
            user_id=self.user_id,
            session_id=self.session_id,
            workflow_context=workflow_context
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            'request_id': self.request_id,
            'request_type': self.request_type.value,
            'action_id': self.action_id,
            'method': self.method,
            'params': self.params,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'workflow_context': self.workflow_context
        }
    
    def to_json(self) -> str:
        """Convert context to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestContext':
        """Create RequestContext from dictionary"""
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.now())
        request_type = RequestType(data.get('request_type', RequestType.TOOL_CALL.value))
        
        return cls(
            request_id=data.get('request_id', str(uuid.uuid4())),
            request_type=request_type,
            action_id=data['action_id'],
            method=data['method'],
            params=data.get('params', {}),
            metadata=data.get('metadata', {}),
            timestamp=timestamp,
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            workflow_context=data.get('workflow_context')
        )
    
    @classmethod
    def from_legacy_params(cls, action_id: str, method: str, params: Dict[str, Any], **kwargs) -> 'RequestContext':
        """Create RequestContext from legacy middleware parameters for V1 compatibility"""
        return cls(
            action_id=action_id,
            method=method,
            params=params,
            **kwargs
        )


@dataclass(frozen=True)
class ResponseContext:
    """
    Immutable response context returned from middleware pipeline.
    Contains results and metadata from request processing.
    
    This is a concrete implementation that satisfies the IResponseContext interface.
    """
    request_id: str
    status: ResponseStatus
    result: Any = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    def is_success(self) -> bool:
        """Check if the response indicates success"""
        return self.status in (ResponseStatus.SUCCESS, ResponseStatus.CREATED, ResponseStatus.ACCEPTED)
    
    def is_error(self) -> bool:
        """Check if the response indicates an error"""
        return not self.is_success()
    
    def with_metadata(self, **new_metadata) -> 'ResponseContext':
        """Create new response with additional metadata"""
        updated_metadata = {**self.metadata, **new_metadata}
        return ResponseContext(
            request_id=self.request_id,
            status=self.status,
            result=self.result,
            error=self.error,
            metadata=updated_metadata,
            timestamp=self.timestamp,
            processing_time=self.processing_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization"""
        return {
            'request_id': self.request_id,
            'status': self.status.value,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'error_type': type(self.error).__name__ if self.error else None,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'is_success': self.is_success()
        }
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_legacy_format(self) -> tuple:
        """Convert to legacy (status_code, response_body) format for V1 compatibility"""
        if self.is_success():
            if isinstance(self.result, (dict, list)):
                return self.status.value, json.dumps(self.result, indent=2)
            else:
                return self.status.value, str(self.result) if self.result is not None else ""
        else:
            error_message = str(self.error) if self.error else "Unknown error"
            return self.status.value, f"[ERROR] {error_message}"
    
    @classmethod
    def success(
        cls, 
        request_id: str, 
        result: Any, 
        processing_time: float = 0.0,
        **metadata
    ) -> 'ResponseContext':
        """Create a successful response"""
        return cls(
            request_id=request_id,
            status=ResponseStatus.SUCCESS,
            result=result,
            processing_time=processing_time,
            metadata=metadata
        )
    
    @classmethod
    def created(
        cls, 
        request_id: str, 
        result: Any, 
        processing_time: float = 0.0,
        **metadata
    ) -> 'ResponseContext':
        """Create a created response (201)"""
        return cls(
            request_id=request_id,
            status=ResponseStatus.CREATED,
            result=result,
            processing_time=processing_time,
            metadata=metadata
        )
    
    @classmethod
    def error(
        cls, 
        request_id: str, 
        error: Exception, 
        status: ResponseStatus = ResponseStatus.INTERNAL_ERROR,
        processing_time: float = 0.0,
        **metadata
    ) -> 'ResponseContext':
        """Create an error response"""
        return cls(
            request_id=request_id,
            status=status,
            error=error,
            processing_time=processing_time,
            metadata=metadata
        )
    
    @classmethod
    def error_response(
        cls, 
        request_id: str, 
        error: Exception, 
        status: ResponseStatus = ResponseStatus.INTERNAL_ERROR,
        processing_time: float = 0.0,
        **metadata
    ) -> 'ResponseContext':
        """Create an error response (alias for error method)"""
        return cls.error(request_id, error, status, processing_time, **metadata)
    
    @classmethod
    def not_found(
        cls, 
        request_id: str, 
        action_id: str,
        processing_time: float = 0.0,
        **metadata
    ) -> 'ResponseContext':
        """Create a not found response (404)"""
        from langswarm.core.errors import ToolError, ErrorContext
        error = ToolError(
            f"Action '{action_id}' not found",
            context=ErrorContext("middleware", "routing"),
            suggestion="Check that the action ID is correct and the handler is registered"
        )
        return cls(
            request_id=request_id,
            status=ResponseStatus.NOT_FOUND,
            error=error,
            processing_time=processing_time,
            metadata=metadata
        )
