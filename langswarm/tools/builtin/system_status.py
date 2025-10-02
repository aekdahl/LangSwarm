"""
System Status Tool - V2 Built-in Tool

Provides system health, status, and diagnostic information for LangSwarm.
Useful for monitoring, debugging, and system introspection.
"""

import asyncio
import json
import platform
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

from langswarm.tools.base import BaseTool, ToolResult, create_tool_metadata, create_method_schema
from langswarm.tools.interfaces import ToolType, ToolCapability


class SystemStatusTool(BaseTool):
    """
    Built-in tool for system status monitoring and diagnostics.
    
    Provides information about:
    - System health and uptime
    - Python environment details
    - LangSwarm version and components
    - Memory and performance metrics
    - Tool registry status
    """
    
    def __init__(self):
        metadata = create_tool_metadata(
            tool_id="builtin_system_status",
            name="system_status",
            description="System status monitoring and diagnostic tool",
            version="2.0.0",
            tool_type=ToolType.BUILTIN,
            capabilities=[ToolCapability.DIAGNOSTIC, ToolCapability.MONITORING, ToolCapability.INTROSPECTION]
        )
        
        # Add methods
        metadata.add_method(create_method_schema(
            name="health_check",
            description="Get overall system health status",
            parameters={},
            returns="Overall health status with basic metrics"
        ))
        
        metadata.add_method(create_method_schema(
            name="system_info",
            description="Get detailed system information",
            parameters={},
            returns="Detailed system information including platform, Python version, etc."
        ))
        
        metadata.add_method(create_method_schema(
            name="performance_metrics",
            description="Get current performance metrics",
            parameters={},
            returns="Performance metrics including memory usage and response times"
        ))
        
        metadata.add_method(create_method_schema(
            name="component_status",
            description="Get status of LangSwarm components",
            parameters={},
            returns="Status of V2 error system, middleware, and tool registry"
        ))
        
        super().__init__(metadata)
        self._start_time = time.time()
    
    async def health_check(self) -> Dict[str, Any]:
        """Quick health check with basic metrics"""
        uptime = time.time() - self._start_time
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "langswarm_v2": "active"
        }
    
    async def system_info(self) -> Dict[str, Any]:
        """Get detailed system information"""
        return {
            "system": {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "hostname": platform.node()
            },
            "python": {
                "version": sys.version,
                "version_info": {
                    "major": sys.version_info.major,
                    "minor": sys.version_info.minor,
                    "micro": sys.version_info.micro,
                    "releaselevel": sys.version_info.releaselevel,
                    "serial": sys.version_info.serial
                },
                "executable": sys.executable,
                "prefix": sys.prefix,
                "path": sys.path[:5]  # First 5 paths to avoid too much data
            },
            "process": {
                "pid": None,  # We'll add this if psutil is available
                "memory_info": None,
                "cpu_percent": None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        # Basic metrics without external dependencies
        uptime = time.time() - self._start_time
        
        metrics = {
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now().isoformat(),
            "python_objects": len(gc.get_objects()) if 'gc' in globals() else None,
            "async_tasks": len(asyncio.all_tasks()) if hasattr(asyncio, 'all_tasks') else None
        }
        
        # Try to get memory info if psutil is available
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            metrics["memory"] = {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            }
            metrics["cpu_percent"] = round(process.cpu_percent(), 2)
        except ImportError:
            metrics["memory"] = "psutil not available"
            metrics["cpu_percent"] = "psutil not available"
        
        return metrics
    
    async def component_status(self) -> Dict[str, Any]:
        """Get status of LangSwarm V2 components"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check V2 Error System
        try:
            from langswarm.core.errors import get_error_handler
            error_handler = get_error_handler()
            status["components"]["error_system"] = {
                "status": "active",
                "handler_active": error_handler is not None,
                "features": ["centralized_handling", "circuit_breaker", "recovery_strategies"]
            }
        except Exception as e:
            status["components"]["error_system"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check V2 Middleware
        try:
            from langswarm.core.middleware import Pipeline, create_default_pipeline
            # Try to create a pipeline to test middleware
            pipeline = create_default_pipeline()
            status["components"]["middleware"] = {
                "status": "active",
                "pipeline_available": pipeline is not None,
                "features": ["interceptor_pipeline", "context_management", "async_execution"]
            }
        except Exception as e:
            status["components"]["middleware"] = {
                "status": "error", 
                "error": str(e)
            }
        
        # Check V2 Tool System
        try:
            from langswarm.tools import ToolRegistry, ServiceRegistry
            registry = ToolRegistry()
            service_registry = ServiceRegistry()
            status["components"]["tool_system"] = {
                "status": "active",
                "registry_available": registry is not None,
                "service_registry_available": service_registry is not None,
                "features": ["unified_interface", "auto_discovery", "execution_engine"]
            }
        except Exception as e:
            status["components"]["tool_system"] = {
                "status": "error",
                "error": str(e)
            }
        
        return status
    
    def run(self, input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        MCP-compatible run method - returns coroutines that can be awaited
        """
        if input_data is None:
            input_data = kwargs
        
        method = input_data.get('method', 'health_check')
        
        if method == 'health_check':
            return self.health_check()
        elif method == 'system_info':
            return self.system_info()
        elif method == 'performance_metrics':
            return self.performance_metrics()
        elif method == 'component_status':
            return self.component_status()
        else:
            raise ValueError(f"Unknown method: {method}")


# Import gc for object counting if available
try:
    import gc
except ImportError:
    pass
