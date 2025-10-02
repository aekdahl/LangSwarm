"""
Web Request Tool - V2 Built-in Tool

Provides basic HTTP request capabilities for web APIs and data fetching.
Security-focused with request validation and safe defaults.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse, urljoin

from langswarm.tools.base import BaseTool, ToolResult, create_tool_metadata, create_method_schema
from langswarm.tools.interfaces import ToolType, ToolCapability


class WebRequestTool(BaseTool):
    """
    Built-in tool for HTTP web requests.
    
    Provides safe HTTP operations:
    - GET, POST, PUT, DELETE requests
    - JSON and form data support
    - Header management
    - Response parsing
    - Timeout and security controls
    """
    
    def __init__(self, timeout: int = 30, max_response_size: int = 10 * 1024 * 1024, allowed_domains: Optional[List[str]] = None):
        """
        Initialize web request tool
        
        Args:
            timeout: Request timeout in seconds
            max_response_size: Maximum response size in bytes
            allowed_domains: List of allowed domains (None for no restrictions)
        """
        self.timeout = timeout
        self.max_response_size = max_response_size
        self.allowed_domains = allowed_domains or []
        
        metadata = create_tool_metadata(
            tool_id="builtin_web_request",
            name="web_request",
            description="HTTP web request tool with security controls",
            version="2.0.0",
            tool_type=ToolType.BUILTIN,
            capabilities=[ToolCapability.NETWORK, ToolCapability.API_INTEGRATION, ToolCapability.DATA_ACCESS]
        )
        
        # Add methods
        metadata.add_method(create_method_schema(
            name="get",
            description="Perform HTTP GET request",
            parameters={
                "url": {"type": "string", "required": True, "description": "URL to request"},
                "headers": {"type": "object", "required": False, "description": "HTTP headers"},
                "params": {"type": "object", "required": False, "description": "URL parameters"},
                "timeout": {"type": "integer", "required": False, "description": "Request timeout in seconds"}
            },
            returns="HTTP response with status, headers, and content"
        ))
        
        metadata.add_method(create_method_schema(
            name="post",
            description="Perform HTTP POST request",
            parameters={
                "url": {"type": "string", "required": True, "description": "URL to request"},
                "data": {"type": "object", "required": False, "description": "JSON data to send"},
                "headers": {"type": "object", "required": False, "description": "HTTP headers"},
                "timeout": {"type": "integer", "required": False, "description": "Request timeout in seconds"}
            },
            returns="HTTP response with status, headers, and content"
        ))
        
        metadata.add_method(create_method_schema(
            name="put",
            description="Perform HTTP PUT request",
            parameters={
                "url": {"type": "string", "required": True, "description": "URL to request"},
                "data": {"type": "object", "required": False, "description": "JSON data to send"},
                "headers": {"type": "object", "required": False, "description": "HTTP headers"},
                "timeout": {"type": "integer", "required": False, "description": "Request timeout in seconds"}
            },
            returns="HTTP response with status, headers, and content"
        ))
        
        metadata.add_method(create_method_schema(
            name="delete",
            description="Perform HTTP DELETE request",
            parameters={
                "url": {"type": "string", "required": True, "description": "URL to request"},
                "headers": {"type": "object", "required": False, "description": "HTTP headers"},
                "timeout": {"type": "integer", "required": False, "description": "Request timeout in seconds"}
            },
            returns="HTTP response with status, headers, and content"
        ))
        
        metadata.add_method(create_method_schema(
            name="head",
            description="Perform HTTP HEAD request",
            parameters={
                "url": {"type": "string", "required": True, "description": "URL to request"},
                "headers": {"type": "object", "required": False, "description": "HTTP headers"},
                "timeout": {"type": "integer", "required": False, "description": "Request timeout in seconds"}
            },
            returns="HTTP response headers and status"
        ))
        
        super().__init__(metadata)
    
    def _validate_url(self, url: str) -> str:
        """Validate URL and check against allowed domains"""
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
            
            # Check domain restrictions
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                raise ValueError(f"Domain {parsed.netloc} not in allowed domains: {self.allowed_domains}")
            
            # Block localhost and private IPs if no domains specified
            if not self.allowed_domains:
                hostname = parsed.hostname
                if hostname in ['localhost', '127.0.0.1', '::1']:
                    raise ValueError("Localhost requests are blocked by default")
                
                # Basic private IP check
                if hostname and (hostname.startswith('10.') or 
                               hostname.startswith('192.168.') or 
                               hostname.startswith('172.')):
                    raise ValueError("Private IP addresses are blocked by default")
            
            return url
        except Exception as e:
            raise ValueError(f"Invalid URL {url}: {e}")
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare HTTP headers with defaults"""
        default_headers = {
            'User-Agent': 'LangSwarm-V2-WebRequestTool/2.0.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        if headers:
            default_headers.update(headers)
        
        return default_headers
    
    def _parse_response(self, response, include_content: bool = True) -> Dict[str, Any]:
        """Parse HTTP response into standard format"""
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "url": str(response.url),
            "elapsed_seconds": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None,
            "size_bytes": len(response.content) if include_content else None
        }
        
        if include_content:
            # Try to parse as JSON first
            try:
                result["json"] = response.json()
                result["content_type"] = "json"
            except:
                # Fall back to text
                try:
                    result["text"] = response.text
                    result["content_type"] = "text"
                except:
                    # Binary content
                    result["content"] = f"<binary data: {len(response.content)} bytes>"
                    result["content_type"] = "binary"
        
        return result
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        import requests
        
        validated_url = self._validate_url(url)
        timeout = kwargs.pop('timeout', self.timeout)
        headers = self._prepare_headers(kwargs.pop('headers', None))
        
        try:
            start_time = time.time()
            response = requests.request(
                method=method,
                url=validated_url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
            
            # Check response size
            if len(response.content) > self.max_response_size:
                raise ValueError(f"Response too large: {len(response.content)} bytes > {self.max_response_size}")
            
            return self._parse_response(response)
            
        except requests.exceptions.Timeout:
            raise ValueError(f"Request timed out after {timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise ValueError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {e}")
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, 
                  params: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Perform HTTP GET request"""
        kwargs = {}
        if params:
            kwargs['params'] = params
        if timeout:
            kwargs['timeout'] = timeout
        if headers:
            kwargs['headers'] = headers
            
        return await self._make_request('GET', url, **kwargs)
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Perform HTTP POST request"""
        kwargs = {}
        if data:
            kwargs['json'] = data
            if headers is None:
                headers = {}
            headers['Content-Type'] = 'application/json'
        if timeout:
            kwargs['timeout'] = timeout
        if headers:
            kwargs['headers'] = headers
            
        return await self._make_request('POST', url, **kwargs)
    
    async def put(self, url: str, data: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Perform HTTP PUT request"""
        kwargs = {}
        if data:
            kwargs['json'] = data
            if headers is None:
                headers = {}
            headers['Content-Type'] = 'application/json'
        if timeout:
            kwargs['timeout'] = timeout
        if headers:
            kwargs['headers'] = headers
            
        return await self._make_request('PUT', url, **kwargs)
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[int] = None) -> Dict[str, Any]:
        """Perform HTTP DELETE request"""
        kwargs = {}
        if timeout:
            kwargs['timeout'] = timeout
        if headers:
            kwargs['headers'] = headers
            
        return await self._make_request('DELETE', url, **kwargs)
    
    async def head(self, url: str, headers: Optional[Dict[str, str]] = None,
                   timeout: Optional[int] = None) -> Dict[str, Any]:
        """Perform HTTP HEAD request"""
        kwargs = {}
        if timeout:
            kwargs['timeout'] = timeout
        if headers:
            kwargs['headers'] = headers
            
        response = await self._make_request('HEAD', url, **kwargs)
        # HEAD responses don't include content
        return {k: v for k, v in response.items() if k not in ['json', 'text', 'content']}
    
    def run(self, input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        MCP-compatible run method
        """
        if input_data is None:
            input_data = kwargs
        
        method = input_data.get('method', 'get')
        method_args = {k: v for k, v in input_data.items() if k != 'method'}
        
        if method == 'get':
            return asyncio.run(self.get(**method_args))
        elif method == 'post':
            return asyncio.run(self.post(**method_args))
        elif method == 'put':
            return asyncio.run(self.put(**method_args))
        elif method == 'delete':
            return asyncio.run(self.delete(**method_args))
        elif method == 'head':
            return asyncio.run(self.head(**method_args))
        else:
            raise ValueError(f"Unknown method: {method}")
