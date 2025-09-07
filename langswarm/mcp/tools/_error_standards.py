"""
Standard error response patterns for LangSwarm MCP tools.

This module defines consistent error response formats that all MCP tools should use
to ensure a uniform experience across the tool ecosystem.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class StandardErrorResponse(BaseModel):
    """Standard error response format for all MCP tools"""
    success: bool = False
    error: str
    error_type: str = "general"
    tool_name: Optional[str] = None
    method: Optional[str] = None
    suggestion: Optional[str] = None


def create_error_response(
    error_message: str,
    error_type: str = "general",
    tool_name: Optional[str] = None,
    method: Optional[str] = None,
    suggestion: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Human-readable error description
        error_type: Type of error (validation, connection, auth, etc.)
        tool_name: Name of the tool that generated the error
        method: Method that failed
        suggestion: Helpful suggestion for resolving the error
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": error_message,
        "error_type": error_type,
        "tool_name": tool_name,
        "method": method,
        "suggestion": suggestion
    }


def create_parameter_error(
    parameter_name: str,
    expected_value: str,
    provided_value: Any = None,
    tool_name: Optional[str] = None,
    method: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized parameter validation error.
    
    Args:
        parameter_name: Name of the invalid parameter
        expected_value: Description of expected parameter value/type
        provided_value: The value that was provided (optional)
        tool_name: Name of the tool
        method: Method that failed
        
    Returns:
        Standardized parameter error response
    """
    error_msg = f"Invalid parameter '{parameter_name}': Expected {expected_value}"
    if provided_value is not None:
        error_msg += f", got {type(provided_value).__name__}: {provided_value}"
    
    suggestion = f"Please provide '{parameter_name}' as {expected_value}"
    
    return create_error_response(
        error_message=error_msg,
        error_type="parameter_validation",
        tool_name=tool_name,
        method=method,
        suggestion=suggestion
    )


def create_authentication_error(
    missing_credential: str,
    tool_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized authentication error.
    
    Args:
        missing_credential: Name of missing credential/environment variable
        tool_name: Name of the tool
        
    Returns:
        Standardized authentication error response
    """
    return create_error_response(
        error_message=f"Authentication failed: Missing {missing_credential}",
        error_type="authentication", 
        tool_name=tool_name,
        suggestion=f"Please set the {missing_credential} environment variable"
    )


def create_connection_error(
    service_name: str,
    details: str = "",
    tool_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized connection error.
    
    Args:
        service_name: Name of the service that couldn't be reached
        details: Additional error details
        tool_name: Name of the tool
        
    Returns:
        Standardized connection error response
    """
    error_msg = f"Connection failed: Unable to connect to {service_name}"
    if details:
        error_msg += f" - {details}"
    
    return create_error_response(
        error_message=error_msg,
        error_type="connection",
        tool_name=tool_name,
        suggestion=f"Please check {service_name} availability and your network connection"
    )


# Standard error types for consistency
class ErrorTypes:
    GENERAL = "general"
    PARAMETER_VALIDATION = "parameter_validation" 
    AUTHENTICATION = "authentication"
    CONNECTION = "connection"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
