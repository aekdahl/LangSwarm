"""
Critical Failure Detection and Handling for LangSwarm Debug System

This module provides detection and handling of critical failures that should
halt execution immediately, such as:
- Missing API keys (OpenAI, Anthropic, etc.)
- Model initialization failures
- Network connectivity issues
- Invalid model configurations

Critical failures are distinguished from recoverable errors and cause
immediate termination with clear diagnostic information.
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass


class FailureType(Enum):
    """Classification of failure types"""
    CRITICAL = "critical"       # Must halt execution
    RECOVERABLE = "recoverable" # Can continue with degraded functionality
    WARNING = "warning"         # Note but continue normally


@dataclass
class FailureInfo:
    """Information about a detected failure"""
    failure_type: FailureType
    category: str              # e.g., "api_key", "model_init", "network"
    component: str             # e.g., "openai", "anthropic", "agent"
    message: str              # Human-readable error message
    suggestion: str           # What user should do to fix it
    original_error: Optional[Exception] = None


class CriticalFailureDetector:
    """
    Detects and classifies failures to determine if execution should halt.
    
    This class analyzes error messages and exceptions to identify critical
    failures that indicate fundamental problems that will prevent successful
    execution.
    """
    
    # Patterns for detecting critical failures
    CRITICAL_PATTERNS = {
        "api_key": [
            r"api key.*not found",
            r"api key.*missing",
            r"api key.*required",
            r"authentication.*failed",
            r"unauthorized.*api",
            r"invalid.*api.*key",
            r"openai_api_key.*not.*set",
            r"anthropic_api_key.*not.*set"
        ],
        "model_init": [
            r"model.*not.*found",
            r"model.*initialization.*failed",
            r"unsupported.*model",
            r"model.*unavailable",
            r"failed.*to.*load.*model"
        ],
        "network": [
            r"connection.*refused",
            r"network.*unreachable",
            r"timeout.*connecting",
            r"dns.*resolution.*failed",
            r"ssl.*certificate.*error"
        ],
        "configuration": [
            r"invalid.*configuration",
            r"missing.*required.*parameter",
            r"configuration.*validation.*failed"
        ]
    }
    
    # Suggestions for fixing critical failures
    SUGGESTIONS = {
        "api_key": "Set the required API key as an environment variable (e.g., OPENAI_API_KEY) or pass it explicitly in the configuration.",
        "model_init": "Check that the model name is correct and the model is available. Verify your API access permissions.",
        "network": "Check your internet connection and any firewall/proxy settings. Verify the API endpoint is accessible.",
        "configuration": "Review your configuration for required parameters and correct formatting."
    }
    
    def detect_failure(self, error_message: str, exception: Optional[Exception] = None, component: str = "unknown") -> FailureInfo:
        """
        Analyze an error to determine if it's a critical failure.
        
        Args:
            error_message: The error message to analyze
            exception: Optional exception object for additional context
            component: The component where the error occurred
            
        Returns:
            FailureInfo object with classification and details
        """
        error_lower = error_message.lower()
        
        # Check for critical patterns
        for category, patterns in self.CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return FailureInfo(
                        failure_type=FailureType.CRITICAL,
                        category=category,
                        component=component,
                        message=error_message,
                        suggestion=self.SUGGESTIONS.get(category, "Please check the error details and configuration."),
                        original_error=exception
                    )
        
        # Check for specific exception types that are critical
        if exception:
            if isinstance(exception, (ValueError, TypeError)) and any(keyword in error_lower for keyword in ["api key", "authentication", "unauthorized"]):
                return FailureInfo(
                    failure_type=FailureType.CRITICAL,
                    category="api_key",
                    component=component,
                    message=error_message,
                    suggestion=self.SUGGESTIONS["api_key"],
                    original_error=exception
                )
        
        # Default to recoverable for unknown errors
        return FailureInfo(
            failure_type=FailureType.RECOVERABLE,
            category="unknown",
            component=component,
            message=error_message,
            suggestion="This appears to be a recoverable error. Check the logs for more details.",
            original_error=exception
        )
    
    def is_critical_failure(self, error_message: str, exception: Optional[Exception] = None) -> bool:
        """
        Quick check if an error represents a critical failure.
        
        Args:
            error_message: The error message to check
            exception: Optional exception object
            
        Returns:
            True if this is a critical failure that should halt execution
        """
        failure_info = self.detect_failure(error_message, exception)
        return failure_info.failure_type == FailureType.CRITICAL


class CriticalFailureHandler:
    """
    Handles critical failures by logging them appropriately and determining
    whether to halt execution.
    """
    
    def __init__(self, tracer=None):
        self.tracer = tracer
        self.detector = CriticalFailureDetector()
        self.critical_failures: List[FailureInfo] = []
    
    def handle_failure(self, error_message: str, exception: Optional[Exception] = None, component: str = "unknown") -> bool:
        """
        Handle a failure and determine if execution should continue.
        
        Args:
            error_message: The error message
            exception: Optional exception object
            component: The component where the error occurred
            
        Returns:
            True if execution should continue, False if it should halt
        """
        failure_info = self.detector.detect_failure(error_message, exception, component)
        
        # Log the failure with appropriate level
        if self.tracer:
            level = "ERROR" if failure_info.failure_type == FailureType.CRITICAL else "WARN"
            self.tracer.log_event(
                "CRITICAL_FAILURE" if failure_info.failure_type == FailureType.CRITICAL else "FAILURE",
                component,
                "failure_detection",
                f"Critical failure detected: {failure_info.message}",
                level=level,
                data={
                    "failure_type": failure_info.failure_type.value,
                    "category": failure_info.category,
                    "suggestion": failure_info.suggestion,
                    "original_error": str(failure_info.original_error) if failure_info.original_error else None
                }
            )
        
        # Store critical failures
        if failure_info.failure_type == FailureType.CRITICAL:
            self.critical_failures.append(failure_info)
            self._print_critical_failure(failure_info)
            return False  # Halt execution
        else:
            self._print_recoverable_failure(failure_info)
            return True   # Continue execution
    
    def _print_critical_failure(self, failure_info: FailureInfo):
        """Print a critical failure message to console"""
        print(f"\n🚨 CRITICAL FAILURE DETECTED 🚨")
        print(f"Component: {failure_info.component}")
        print(f"Category: {failure_info.category}")
        print(f"Error: {failure_info.message}")
        print(f"💡 Solution: {failure_info.suggestion}")
        print(f"\n⛔ Execution halted due to critical failure.")
        print(f"Please fix the issue above before proceeding.\n")
    
    def _print_recoverable_failure(self, failure_info: FailureInfo):
        """Print a recoverable failure message to console"""
        print(f"\n⚠️  Recoverable Issue Detected")
        print(f"Component: {failure_info.component}")
        print(f"Error: {failure_info.message}")
        if failure_info.suggestion:
            print(f"💡 Suggestion: {failure_info.suggestion}")
        print(f"Continuing with execution...\n")
    
    def has_critical_failures(self) -> bool:
        """Check if any critical failures have been detected"""
        return len(self.critical_failures) > 0
    
    def get_critical_failures(self) -> List[FailureInfo]:
        """Get list of all critical failures detected"""
        return self.critical_failures.copy()
    
    def clear_failures(self):
        """Clear the failure history"""
        self.critical_failures.clear()
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """Get a summary of all failures detected"""
        if not self.critical_failures:
            return {"status": "no_critical_failures"}
        
        categories = {}
        for failure in self.critical_failures:
            if failure.category not in categories:
                categories[failure.category] = []
            categories[failure.category].append({
                "component": failure.component,
                "message": failure.message,
                "suggestion": failure.suggestion
            })
        
        return {
            "status": "critical_failures_detected",
            "count": len(self.critical_failures),
            "categories": categories,
            "first_failure": {
                "component": self.critical_failures[0].component,
                "category": self.critical_failures[0].category,
                "message": self.critical_failures[0].message
            } if self.critical_failures else None
        }


# Global failure handler instance
_global_failure_handler: Optional[CriticalFailureHandler] = None


def initialize_failure_handler(tracer=None) -> CriticalFailureHandler:
    """Initialize the global critical failure handler"""
    global _global_failure_handler
    _global_failure_handler = CriticalFailureHandler(tracer)
    return _global_failure_handler


def get_failure_handler() -> Optional[CriticalFailureHandler]:
    """Get the global critical failure handler"""
    return _global_failure_handler


def handle_critical_failure(error_message: str, exception: Optional[Exception] = None, component: str = "unknown") -> bool:
    """
    Convenience function to handle a failure using the global handler.
    
    Returns:
        True if execution should continue, False if it should halt
    """
    if _global_failure_handler:
        return _global_failure_handler.handle_failure(error_message, exception, component)
    else:
        # Fallback: assume critical if contains key patterns
        detector = CriticalFailureDetector()
        if detector.is_critical_failure(error_message, exception):
            print(f"🚨 CRITICAL FAILURE: {error_message}")
            print("⛔ Execution halted. Please fix the issue and try again.")
            return False
        return True


def is_critical_error(error_message: str, exception: Optional[Exception] = None) -> bool:
    """
    Quick check if an error is critical.
    
    Returns:
        True if this error should halt execution
    """
    detector = CriticalFailureDetector()
    return detector.is_critical_failure(error_message, exception)
