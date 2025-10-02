"""
LangSwarm V2 Validation Interceptor

Validates requests before they reach execution.
Provides parameter validation, security checks, and request sanitization.
"""

import logging
from typing import Callable, Dict, Any, List

from langswarm.core.errors import ValidationError, ErrorContext

from ..interfaces import IRequestContext, IResponseContext, ResponseStatus
from ..context import ResponseContext
from .base import BaseInterceptor

logger = logging.getLogger(__name__)


class ValidationInterceptor(BaseInterceptor):
    """
    Interceptor that validates requests before execution.
    
    Performs parameter validation, security checks, and request sanitization.
    """
    
    def __init__(self, priority: int = 200):
        """
        Initialize validation interceptor.
        
        Args:
            priority: Priority for interceptor ordering
        """
        super().__init__(name="validation", priority=priority)
        
        # Validation statistics
        self._validation_failures = 0
        self._security_blocks = 0
    
    async def _process(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Validate the request and call next interceptor if valid.
        
        Args:
            context: The request context
            next_interceptor: Function to call next interceptor
            
        Returns:
            Response context with validation results
        """
        logger.debug(f"Validating request for {context.action_id}.{context.method}")
        
        # Perform validation checks
        validation_errors = []
        
        # Basic validation
        validation_errors.extend(self._validate_basic_fields(context))
        
        # Parameter validation
        validation_errors.extend(self._validate_parameters(context))
        
        # Security validation
        validation_errors.extend(self._validate_security(context))
        
        if validation_errors:
            self._validation_failures += 1
            logger.warning(f"Validation failed for {context.action_id}: {validation_errors}")
            
            return ResponseContext.error(
                context.request_id,
                ValidationError(
                    f"Request validation failed: {'; '.join(validation_errors)}",
                    context=ErrorContext("validation", "request_validation"),
                    suggestion="Check request parameters and format"
                ),
                ResponseStatus.BAD_REQUEST,
                validation_errors=validation_errors,
                validation_interceptor="validation"
            )
        
        logger.debug(f"Request validation passed for {context.action_id}")
        
        # Validation passed, continue with next interceptor
        return await next_interceptor(context)
    
    def _validate_basic_fields(self, context: IRequestContext) -> List[str]:
        """
        Validate basic required fields.
        
        Args:
            context: Request context
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not context.action_id or not context.action_id.strip():
            errors.append("action_id is required")
        
        if not context.method or not context.method.strip():
            errors.append("method is required")
        
        if context.action_id and len(context.action_id) > 100:
            errors.append("action_id too long (max 100 characters)")
        
        if context.method and len(context.method) > 50:
            errors.append("method name too long (max 50 characters)")
        
        return errors
    
    def _validate_parameters(self, context: IRequestContext) -> List[str]:
        """
        Validate request parameters.
        
        Args:
            context: Request context
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        params = context.params
        
        # Check parameter size
        if params and len(str(params)) > 10000:  # 10KB limit
            errors.append("parameters too large (max 10KB)")
        
        # Check for dangerous parameter names/values
        if params:
            dangerous_keys = ['__', 'exec', 'eval', 'import', 'open', 'file']
            for key in params.keys():
                if any(dangerous in str(key).lower() for dangerous in dangerous_keys):
                    errors.append(f"potentially dangerous parameter name: {key}")
        
        return errors
    
    def _validate_security(self, context: IRequestContext) -> List[str]:
        """
        Perform security validation.
        
        Args:
            context: Request context
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for suspicious patterns
        action_id = context.action_id.lower()
        method = context.method.lower()
        
        # Block obviously malicious patterns
        suspicious_patterns = ['..//', '\\..\\', 'rm -rf', 'del /f', 'format c:', 'DROP TABLE']
        
        for pattern in suspicious_patterns:
            if pattern in action_id or pattern in method:
                self._security_blocks += 1
                errors.append(f"suspicious pattern detected: {pattern}")
        
        # Check parameter values for potential injection
        if context.params:
            param_str = str(context.params).lower()
            injection_patterns = ['select * from', 'union select', '<script', 'javascript:', 'eval(']
            
            for pattern in injection_patterns:
                if pattern in param_str:
                    self._security_blocks += 1
                    errors.append(f"potential injection detected: {pattern}")
        
        return errors
    
    def can_handle(self, context: IRequestContext) -> bool:
        """
        Check if this interceptor should handle the request.
        
        Validation interceptor should handle all requests.
        
        Args:
            context: The request context
            
        Returns:
            True if interceptor is enabled
        """
        return self.enabled
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        base_stats = self.get_statistics()
        
        validation_failure_rate = (self._validation_failures / self._request_count 
                                 if self._request_count > 0 else 0.0)
        
        base_stats.update({
            'validation_failures': self._validation_failures,
            'security_blocks': self._security_blocks,
            'validation_failure_rate': validation_failure_rate
        })
        
        return base_stats
    
    def reset_statistics(self) -> None:
        """Reset validation statistics"""
        super().reset_statistics()
        self._validation_failures = 0
        self._security_blocks = 0
