"""
Central Error Monitoring for LangSwarm

This module provides centralized error detection and reporting to ensure
critical tool failures are immediately visible and never buried in logs.
"""

import logging
import time
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class ErrorMonitor:
    """Centralized error monitoring and reporting system"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.critical_errors = []
        self.recent_errors = []
        
    def report_tool_validation_error(self, tool_name: str, method: str, error: str, params: Dict[str, Any] = None):
        """Report a tool parameter validation error"""
        timestamp = time.time()
        error_key = f"{tool_name}.{method}"
        
        self.error_counts[error_key] += 1
        
        error_info = {
            "timestamp": timestamp,
            "type": "validation_error",
            "tool": tool_name,
            "method": method,
            "error": error,
            "params": params,
            "severity": "critical"
        }
        
        self.critical_errors.append(error_info)
        self.recent_errors.append(error_info)
        
        # Keep only last 100 recent errors
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
        
        # Immediate console alert
        print(f"🚨 TOOL VALIDATION ERROR #{self.error_counts[error_key]}: {tool_name}.{method}")
        print(f"   Error: {error}")
        if params:
            print(f"   Params: {params}")
        print("   🔍 This type of error should be fixed immediately!")
        
        logger.error(f"Tool validation error in {error_key}: {error}")
        
    def report_tool_execution_error(self, tool_name: str, method: str, error: str, error_type: str = None):
        """Report a tool execution error"""
        timestamp = time.time()
        error_key = f"{tool_name}.{method}"
        
        self.error_counts[error_key] += 1
        
        error_info = {
            "timestamp": timestamp,
            "type": "execution_error",
            "tool": tool_name,
            "method": method,
            "error": error,
            "error_type": error_type,
            "severity": "high"
        }
        
        self.recent_errors.append(error_info)
        
        # Keep only last 100 recent errors
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
        
        # Console alert for repeated errors
        if self.error_counts[error_key] > 1:
            print(f"⚠️  REPEATED TOOL ERROR #{self.error_counts[error_key]}: {tool_name}.{method}")
            print(f"   Error: {error}")
            
        logger.error(f"Tool execution error in {error_key}: {error}")
        
    def report_silent_tool_failure(self, scenario: str, expected_tool: str, response: str):
        """Report when a tool should have been called but wasn't"""
        timestamp = time.time()
        
        error_info = {
            "timestamp": timestamp,
            "type": "silent_failure",
            "scenario": scenario,
            "expected_tool": expected_tool,
            "response_preview": response[:200],
            "severity": "medium"
        }
        
        self.recent_errors.append(error_info)
        
        print(f"🔍 TOOL CALL DETECTION ISSUE in {scenario}: Expected {expected_tool} but no tool call detected")
        print(f"   Response: {response[:100]}...")
        
        logger.warning(f"Silent tool failure in {scenario}: expected {expected_tool}")
        
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors"""
        critical_count = len([e for e in self.recent_errors if e.get("severity") == "critical"])
        high_count = len([e for e in self.recent_errors if e.get("severity") == "high"])
        
        return {
            "total_errors": len(self.recent_errors),
            "critical_errors": critical_count,
            "high_priority_errors": high_count,
            "error_counts_by_tool": dict(self.error_counts),
            "recent_errors": self.recent_errors[-10:],  # Last 10 errors
            "status": "critical" if critical_count > 0 else ("warning" if high_count > 0 else "ok")
        }
        
    def clear_errors(self):
        """Clear all error tracking (for testing)"""
        self.error_counts.clear()
        self.critical_errors.clear()
        self.recent_errors.clear()

# Global error monitor instance
error_monitor = ErrorMonitor()

def report_tool_validation_error(tool_name: str, method: str, error: str, params: Dict[str, Any] = None):
    """Global function to report tool validation errors"""
    error_monitor.report_tool_validation_error(tool_name, method, error, params)

def report_tool_execution_error(tool_name: str, method: str, error: str, error_type: str = None):
    """Global function to report tool execution errors"""
    error_monitor.report_tool_execution_error(tool_name, method, error, error_type)

def report_silent_tool_failure(scenario: str, expected_tool: str, response: str):
    """Global function to report silent tool failures"""
    error_monitor.report_silent_tool_failure(scenario, expected_tool, response)

def get_error_summary() -> Dict[str, Any]:
    """Get current error summary"""
    return error_monitor.get_error_summary()
