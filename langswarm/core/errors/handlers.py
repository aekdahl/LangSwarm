"""
LangSwarm V2 Error Handlers

Centralized error handling with severity-based routing, 
recovery mechanisms, and comprehensive logging.
"""

import logging
import time
from typing import Dict, Callable, Any, Optional, List
from collections import defaultdict

from .types import (
    LangSwarmError, 
    ErrorSeverity, 
    ErrorCategory, 
    ErrorContext,
    CriticalError
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handling with severity-based routing
    
    Provides consistent error handling across all LangSwarm components
    with automatic routing based on error severity and category.
    """
    
    def __init__(self):
        self._handlers: Dict[ErrorSeverity, Callable] = {
            ErrorSeverity.CRITICAL: self._handle_critical,
            ErrorSeverity.ERROR: self._handle_error,
            ErrorSeverity.WARNING: self._handle_warning,
            ErrorSeverity.INFO: self._handle_info,
        }
        
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._error_history: List[Dict[str, Any]] = []
        self._max_history = 1000  # Keep last 1000 errors
        
        # Recovery strategies
        self._recovery_strategies: Dict[str, Callable] = {}
        
        # Circuit breaker for critical errors
        self._critical_error_count = 0
        self._critical_error_threshold = 5
        self._circuit_breaker_active = False
        self._last_critical_error_time = 0
        self._circuit_breaker_timeout = 300  # 5 minutes
    
    def handle(self, error: Exception, component: str = "unknown") -> bool:
        """
        Handle any error with appropriate routing
        
        Args:
            error: The exception to handle
            component: Component where error occurred
            
        Returns:
            bool: True if system should continue, False if halt required
        """
        # Handle None error gracefully
        if error is None:
            error = Exception("None error")
        
        # Convert to LangSwarmError if needed
        if not isinstance(error, LangSwarmError):
            ls_error = self._convert_to_langswarm_error(error, component)
        else:
            ls_error = error
            # Update context component if different
            if ls_error.context.component == "unknown" and component != "unknown":
                ls_error.context.component = component
        
        # Check and potentially reset circuit breaker for critical errors
        if ls_error.is_critical():
            self._check_circuit_breaker_reset()
            if self._circuit_breaker_active:
                logger.critical("Circuit breaker active - suppressing additional critical errors")
                return False
        
        # Track error frequency
        error_key = f"{ls_error.category.value}:{ls_error.context.component}"
        self._error_counts[error_key] += 1
        
        # Add to error history
        self._add_to_history(ls_error)
        
        # Route to appropriate handler
        handler = self._handlers.get(ls_error.severity, self._handle_error)
        should_continue = handler(ls_error)
        
        # Update circuit breaker state
        if ls_error.is_critical():
            self._update_circuit_breaker()
        
        # Attempt recovery if strategy exists
        if not should_continue:
            recovery_attempted = self._attempt_recovery(ls_error)
            if recovery_attempted:
                logger.info(f"Recovery attempted for {ls_error.category.value} error")
                return True  # Recovery attempted, allow continuation
        
        return should_continue
    
    def _convert_to_langswarm_error(self, error: Exception, component: str) -> LangSwarmError:
        """Convert generic exceptions to LangSwarm errors"""
        error_msg = str(error).lower()
        
        # Create error context
        context = ErrorContext(component=component, operation="error_conversion")
        
        # Classify error based on message content and type
        if any(keyword in error_msg for keyword in ["api", "key", "auth", "token"]):
            return CriticalError(
                f"Authentication error: {str(error)}",
                context=context,
                suggestion="Check your API keys and authentication configuration",
                cause=error
            )
        elif any(keyword in error_msg for keyword in ["config", "yaml", "json", "parse"]):
            from .types import ConfigurationError
            return ConfigurationError(
                f"Configuration error: {str(error)}",
                context=context,
                suggestion="Review your configuration file for syntax errors",
                cause=error
            )
        elif any(keyword in error_msg for keyword in ["network", "connection", "timeout"]):
            from .types import NetworkError
            return NetworkError(
                f"Network error: {str(error)}",
                context=context,
                suggestion="Check your network connection and try again",
                cause=error
            )
        elif any(keyword in error_msg for keyword in ["permission", "access", "forbidden"]):
            from .types import PermissionError
            return PermissionError(
                f"Permission error: {str(error)}",
                context=context,
                suggestion="Check file permissions or access rights",
                cause=error
            )
        else:
            # Generic error
            return LangSwarmError(
                str(error),
                context=context,
                cause=error,
                user_facing=False
            )
    
    def _handle_critical(self, error: LangSwarmError) -> bool:
        """Handle critical errors - halt system"""
        logger.critical(f"🚨 CRITICAL ERROR: {error}")
        
        # Print to console for immediate visibility
        print(f"\n🚨 CRITICAL FAILURE - SYSTEM HALTED\n{error}\n")
        
        # Log debug information
        if hasattr(error, 'get_debug_info'):
            debug_info = error.get_debug_info()
            logger.critical(f"Debug info: {debug_info}")
        
        return False  # Halt execution
    
    def _handle_error(self, error: LangSwarmError) -> bool:
        """Handle regular errors - log and continue"""
        logger.error(f"❌ ERROR: {error}")
        
        # Log additional context for debugging
        if error.context and error.context.metadata:
            logger.error(f"Error context: {error.context.metadata}")
        
        return True  # Continue execution
    
    def _handle_warning(self, error: LangSwarmError) -> bool:
        """Handle warnings - log and continue"""
        logger.warning(f"⚠️ WARNING: {error}")
        return True  # Continue execution
    
    def _handle_info(self, error: LangSwarmError) -> bool:
        """Handle info messages - log and continue"""
        logger.info(f"ℹ️ INFO: {error}")
        return True  # Continue execution
    
    def _add_to_history(self, error: LangSwarmError):
        """Add error to history for analysis"""
        error_record = {
            'timestamp': time.time(),
            'error_type': error.__class__.__name__,
            'severity': error.severity.value,
            'category': error.category.value,
            'component': error.context.component,
            'operation': error.context.operation,
            'message': error.message
        }
        
        self._error_history.append(error_record)
        
        # Trim history if too long
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
    
    def _update_circuit_breaker(self):
        """Update circuit breaker state for critical errors"""
        current_time = time.time()
        
        # Check and reset circuit breaker if timeout has passed
        if (self._circuit_breaker_active and 
            current_time - self._last_critical_error_time > self._circuit_breaker_timeout):
            self._circuit_breaker_active = False
            self._critical_error_count = 0
            logger.info("Circuit breaker reset - critical error timeout passed")
        
        self._critical_error_count += 1
        self._last_critical_error_time = current_time
        
        # Activate circuit breaker if threshold exceeded
        if self._critical_error_count >= self._critical_error_threshold:
            self._circuit_breaker_active = True
            logger.critical(f"Circuit breaker activated - {self._critical_error_count} critical errors")
    
    def _check_circuit_breaker_reset(self):
        """Check and reset circuit breaker if timeout has passed"""
        current_time = time.time()
        if (self._circuit_breaker_active and 
            current_time - self._last_critical_error_time > self._circuit_breaker_timeout):
            self._circuit_breaker_active = False
            self._critical_error_count = 0
            logger.info("Circuit breaker reset - critical error timeout passed")
            return True
        return False
    
    def _attempt_recovery(self, error: LangSwarmError) -> bool:
        """Attempt to recover from error using registered strategies"""
        # Try different patterns for recovery strategy lookup
        patterns = [
            f"{error.category.value}:{error.__class__.__name__}",
            f"{error.category.value}:*",
            f"*:{error.__class__.__name__}",
            "*:*"
        ]
        
        for pattern in patterns:
            if pattern in self._recovery_strategies:
                try:
                    recovery_func = self._recovery_strategies[pattern]
                    result = recovery_func(error)
                    if result:
                        logger.info(f"Recovery successful using pattern: {pattern}")
                    return result
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed for pattern {pattern}: {recovery_error}")
                    return False
        
        return False
    
    def register_recovery_strategy(self, error_pattern: str, recovery_func: Callable):
        """Register a recovery strategy for specific error patterns"""
        self._recovery_strategies[error_pattern] = recovery_func
        logger.info(f"Recovery strategy registered for: {error_pattern}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': dict(self._error_counts),
            'total_errors': len(self._error_history),
            'critical_error_count': self._critical_error_count,
            'circuit_breaker_active': self._circuit_breaker_active,
            'recent_errors': self._error_history[-10:] if self._error_history else []
        }
    
    def reset_statistics(self):
        """Reset error statistics (useful for testing)"""
        self._error_counts.clear()
        self._error_history.clear()
        self._critical_error_count = 0
        self._circuit_breaker_active = False


# Global error handler instance
_global_handler = ErrorHandler()


def handle_error(error: Exception, component: str = "unknown") -> bool:
    """
    Global error handling function
    
    Args:
        error: Exception to handle
        component: Component where error occurred
        
    Returns:
        bool: True if system should continue, False if halt required
    """
    return _global_handler.handle(error, component)


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _global_handler


def register_recovery_strategy(error_pattern: str, recovery_func: Callable):
    """Register a recovery strategy for specific error patterns"""
    _global_handler.register_recovery_strategy(error_pattern, recovery_func)
