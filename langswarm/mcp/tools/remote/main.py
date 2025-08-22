#!/usr/bin/env python3
"""
Remote MCP Tool
===============

A generic tool for connecting to remote MCP servers via HTTP/HTTPS.
Supports full JSON-RPC MCP protocol with authentication, error handling,
and automatic schema discovery.
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
from datetime import datetime

# LangSwarm imports
from langswarm.synapse.tools.base import BaseTool

# === Remote MCP Tool Implementation ===

class RemoteMCPTool(BaseTool):
    """
    Generic remote MCP tool for connecting to external MCP servers.
    
    Supports:
    - HTTP/HTTPS MCP servers with JSON-RPC protocol
    - Authentication via API keys, JWT tokens, or custom headers
    - Automatic schema discovery and validation
    - Error handling and retry logic
    - Environment variable configuration
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, mcp_url: str = None,
                 headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30, retry_count: int = 3,
                 auto_initialize: bool = True, **kwargs):
        
        # Set defaults for remote MCP tool
        description = kwargs.pop('description', f"Remote MCP tool: {identifier}")
        instruction = kwargs.pop('instruction', f"Use the {identifier} remote MCP tool for external operations")
        brief = kwargs.pop('brief', f"Remote MCP: {identifier}")
        
        # Store remote MCP configuration
        object.__setattr__(self, 'mcp_url', mcp_url)
        object.__setattr__(self, 'headers', headers or {})
        object.__setattr__(self, 'timeout', timeout)
        object.__setattr__(self, 'retry_count', retry_count)
        object.__setattr__(self, 'auto_initialize', auto_initialize)
        
        # Remote tool state
        object.__setattr__(self, '_initialized', False)
        object.__setattr__(self, '_available_tools', {})
        object.__setattr__(self, '_last_error', None)
        
        # Initialize with BaseTool
        super().__init__(
            name=name or f"RemoteMCPTool-{identifier}",
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
        
        # Auto-initialize connection if requested
        if auto_initialize and mcp_url:
            try:
                self._initialize_connection()
            except Exception as e:
                print(f"⚠️  Remote MCP auto-initialization failed: {e}")
    
    def _initialize_connection(self) -> Dict[str, Any]:
        """Initialize connection to remote MCP server"""
        mcp_url = getattr(self, 'mcp_url', None)
        if not mcp_url:
            raise ValueError("mcp_url is required for remote MCP tools")
        
        # Step 1: Initialize
        init_response = self._make_request({
            "method": "initialize",
            "id": f"init-{int(time.time())}"
        })
        
        if "error" in init_response:
            raise Exception(f"Initialization failed: {init_response['error']}")
        
        # Step 2: Discover available tools
        tools_response = self._make_request({
            "method": "tools/list", 
            "id": f"list-{int(time.time())}"
        })
        
        if "error" in tools_response:
            raise Exception(f"Tool discovery failed: {tools_response['error']}")
        
        # Cache available tools and their schemas
        available_tools = getattr(self, '_available_tools', {})
        if "result" in tools_response and "tools" in tools_response["result"]:
            for tool in tools_response["result"]["tools"]:
                tool_name = tool.get("name")
                if tool_name:
                    available_tools[tool_name] = tool
        
        object.__setattr__(self, '_available_tools', available_tools)
        object.__setattr__(self, '_initialized', True)
        print(f"✅ Remote MCP '{self.identifier}' initialized with {len(available_tools)} tools")
        
        return {
            "initialized": True,
            "available_tools": list(available_tools.keys()),
            "server_info": init_response.get("result", {})
        }
    
    def _make_request(self, payload: Dict[str, Any], retry_attempt: int = 0) -> Dict[str, Any]:
        """Make HTTP request to remote MCP server with retry logic"""
        
        try:
            # Get instance attributes safely
            headers = getattr(self, 'headers', {})
            mcp_url = getattr(self, 'mcp_url', None)
            timeout = getattr(self, 'timeout', 30)
            
            # Prepare headers
            request_headers = {
                "Content-Type": "application/json",
                **headers
            }
            
            # Resolve environment variables in headers
            for key, value in request_headers.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    env_value = os.getenv(env_var)
                    if env_value:
                        request_headers[key] = env_value
                    else:
                        print(f"⚠️  Environment variable {env_var} not set")
            
            # Make request
            response = requests.post(
                mcp_url,
                headers=request_headers,
                json=payload,
                timeout=timeout
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                error_msg = "Authentication failed - check API key or JWT token"
                object.__setattr__(self, '_last_error', error_msg)
                return {"error": {"message": error_msg, "code": 401}}
            elif response.status_code == 400:
                error_msg = f"Bad request - {response.text}"
                object.__setattr__(self, '_last_error', error_msg)
                return {"error": {"message": error_msg, "code": 400}}
            elif response.status_code == 429:
                error_msg = f"Rate limit exceeded - waiting before retry"
                object.__setattr__(self, '_last_error', error_msg)
                # Retry on rate limits with exponential backoff
                retry_count = getattr(self, 'retry_count', 3)
                if retry_attempt < retry_count:
                    backoff_time = 2 ** retry_attempt
                    print(f"🔄 Rate limited - retrying in {backoff_time}s (attempt {retry_attempt + 1}/{retry_count})")
                    time.sleep(backoff_time)
                    return self._make_request(payload, retry_attempt + 1)
                return {"error": {"message": "Rate limit exceeded - max retries reached", "code": 429}}
            elif response.status_code >= 500:
                error_msg = f"Server error - {response.status_code}: {response.text}"
                object.__setattr__(self, '_last_error', error_msg)
                # Retry on server errors
                retry_count = getattr(self, 'retry_count', 3)
                if retry_attempt < retry_count:
                    backoff_time = 2 ** retry_attempt
                    print(f"🔄 Retrying request (attempt {retry_attempt + 1}/{retry_count}) in {backoff_time}s")
                    time.sleep(backoff_time)  # Exponential backoff
                    return self._make_request(payload, retry_attempt + 1)
                return {"error": {"message": error_msg, "code": response.status_code}}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            timeout = getattr(self, 'timeout', 30)
            error_msg = f"Request timeout after {timeout} seconds"
            object.__setattr__(self, '_last_error', error_msg)
            return {"error": {"message": error_msg, "code": "TIMEOUT"}}
        except requests.exceptions.ConnectionError:
            mcp_url = getattr(self, 'mcp_url', 'unknown')
            error_msg = f"Connection error to {mcp_url}"
            object.__setattr__(self, '_last_error', error_msg)
            return {"error": {"message": error_msg, "code": "CONNECTION_ERROR"}}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            object.__setattr__(self, '_last_error', error_msg)
            return {"error": {"message": error_msg, "code": "UNKNOWN_ERROR"}}
    
    def call_remote_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool on the remote MCP server"""
        
        # Ensure connection is initialized
        initialized = getattr(self, '_initialized', False)
        if not initialized:
            try:
                self._initialize_connection()
            except Exception as e:
                return {"error": f"Failed to initialize connection: {e}"}
        
        # Validate tool exists
        available_tools = getattr(self, '_available_tools', {})
        if tool_name not in available_tools:
            available = list(available_tools.keys())
            return {
                "error": f"Tool '{tool_name}' not available. Available tools: {available}"
            }
        
        # Prepare tool call payload
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": f"call-{tool_name}-{int(time.time())}"
        }
        
        # Make the call
        response = self._make_request(payload)
        
        # Process response
        if "error" in response:
            return {
                "success": False,
                "error": response["error"]["message"],
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": True,
                "result": response.get("result"),
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools and their schemas"""
        
        initialized = getattr(self, '_initialized', False)
        if not initialized:
            try:
                self._initialize_connection()
            except Exception as e:
                return {"error": f"Failed to initialize: {e}"}
        
        available_tools = getattr(self, '_available_tools', {})
        mcp_url = getattr(self, 'mcp_url', 'unknown')
        
        return {
            "tools": available_tools,
            "count": len(available_tools),
            "server_url": mcp_url
        }
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get schema for a specific tool"""
        
        available_tools = getattr(self, '_available_tools', {})
        if tool_name not in available_tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        return available_tools[tool_name]
    
    def check_connection(self) -> Dict[str, Any]:
        """Check connection status to remote MCP server"""
        
        try:
            response = self._make_request({
                "method": "initialize",
                "id": f"health-{int(time.time())}"
            })
            
            if "error" in response:
                last_error = getattr(self, '_last_error', None)
                return {
                    "connected": False,
                    "error": response["error"]["message"],
                    "last_error": last_error
                }
            else:
                mcp_url = getattr(self, 'mcp_url', 'unknown')
                available_tools = getattr(self, '_available_tools', {})
                return {
                    "connected": True,
                    "server_url": mcp_url,
                    "available_tools": len(available_tools),
                    "last_check": datetime.utcnow().isoformat()
                }
        except Exception as e:
            mcp_url = getattr(self, 'mcp_url', 'unknown')
            return {
                "connected": False,
                "error": str(e),
                "server_url": mcp_url
            }
    
    def run(self, input_data=None):
        """Execute remote MCP tool operations"""
        
        # Handle different input formats
        if isinstance(input_data, str):
            # Natural language intent
            return f"Remote MCP tool '{self.identifier}' received: {input_data}. Use structured calls with tool names and parameters."
        
        elif isinstance(input_data, dict):
            # Structured input
            if "method" in input_data:
                method = input_data["method"]
                params = input_data.get("params", {})
                
                if method == "call_tool":
                    tool_name = params.get("tool_name")
                    arguments = params.get("arguments", {})
                    return self.call_remote_tool(tool_name, arguments)
                
                elif method == "list_tools":
                    return self.get_available_tools()
                
                elif method == "get_schema":
                    tool_name = params.get("tool_name")
                    return self.get_tool_schema(tool_name)
                
                elif method == "check_connection":
                    return self.check_connection()
                
                else:
                    return {"error": f"Unknown method: {method}"}
            
            # Direct tool call format
            elif "tool_name" in input_data:
                tool_name = input_data["tool_name"]
                arguments = input_data.get("arguments", {})
                return self.call_remote_tool(tool_name, arguments)
            
            # MCP format
            elif "name" in input_data:
                tool_name = input_data["name"]
                arguments = input_data.get("arguments", {})
                return self.call_remote_tool(tool_name, arguments)
            
            else:
                return {"error": "Invalid input format. Expected tool_name and arguments."}
        
        else:
            return {"error": "Invalid input type. Expected string or dict."}

# === Convenience Functions ===

def create_user_mcp_tool(identifier: str = "user_mcp", api_key: str = None, **kwargs) -> RemoteMCPTool:
    """Create a User MCP (Agent Server) tool with default configuration"""
    
    # Default configuration for User MCP
    default_config = {
        "mcp_url": "https://silzzbehvqzdtwupbmur.functions.supabase.co/mcp-agent-server",
        "headers": {
            "x-api-key": api_key or "${USER_API_KEY}",
            "Content-Type": "application/json"
        },
        "timeout": 30,
        "retry_count": 3,
        "auto_initialize": True,
        "description": "User MCP (Agent Server) for project/task/team operations",
        "instruction": "Use this tool for user-scoped project, task, and team operations via the User MCP server"
    }
    
    # Merge with user-provided config
    config = {**default_config, **kwargs}
    
    return RemoteMCPTool(identifier=identifier, **config)

if __name__ == "__main__":
    # Test the remote MCP tool
    print("🧪 Testing Remote MCP Tool")
    
    # Create a test tool (requires USER_API_KEY environment variable)
    tool = create_user_mcp_tool()
    
    # Check connection
    status = tool.check_connection()
    print(f"Connection status: {status}")
    
    # List available tools
    tools = tool.get_available_tools()
    print(f"Available tools: {tools}")
    
    print("✅ Remote MCP Tool ready")