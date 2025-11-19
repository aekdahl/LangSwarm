"""
LangSwarm V2 Tool Registry

Modern service registry with auto-discovery, dependency injection,
and comprehensive tool management capabilities.
"""

import os
import importlib
import inspect
import json
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime
import logging

from langswarm.core.errors import handle_error, ToolError, ErrorContext, ErrorSeverity

from .interfaces import (
    IToolInterface,
    IToolRegistry,
    IToolDiscovery,
    ToolType,
    ToolCapability
)
from .base import BaseTool
from .adapters.mcp_adapter import auto_adapt_mcp_tools

logger = logging.getLogger(__name__)


class ToolRegistry(IToolRegistry):
    """
    Modern tool registry with auto-discovery and service management (Singleton).
    
    Provides:
    - Tool registration and management
    - Auto-discovery of tools
    - Filtering and search capabilities
    - Schema generation for LLM consumption
    - Health monitoring and statistics
    
    Note: This is a singleton to ensure all parts of the application share the same registry.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, name: str = "default"):
        """Singleton pattern - always return the same instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "default"):
        """Initialize only once, even if called multiple times"""
        # Skip initialization if already done
        if self._initialized:
            return
            
        self.name = name
        self._tools: Dict[str, IToolInterface] = {}
        self._tool_types: Dict[ToolType, Set[str]] = {tool_type: set() for tool_type in ToolType}
        self._capabilities: Dict[ToolCapability, Set[str]] = {cap: set() for cap in ToolCapability}
        self._tags: Dict[str, Set[str]] = {}
        self._logger = logging.getLogger(f"registry.{name}")
        
        # Statistics
        self._registration_count = 0
        self._successful_registrations = 0
        self._failed_registrations = 0
        
        # Mark as initialized
        self._initialized = True
    
    def register(self, tool: IToolInterface) -> bool:
        """Register a tool"""
        self._registration_count += 1
        
        try:
            tool_id = tool.metadata.id
            
            # FAIL FAST: Duplicate registration is a configuration error
            if tool_id in self._tools:
                raise ToolError(
                    f"Tool {tool_id} is already registered",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_registry", "register"),
                    suggestion=f"Unregister tool {tool_id} first or use a different tool ID"
                )
            
            # Register the tool
            self._tools[tool_id] = tool
            
            # Update indices
            self._tool_types[tool.metadata.tool_type].add(tool_id)
            
            for capability in tool.metadata.capabilities:
                self._capabilities[capability].add(tool_id)
            
            for tag in tool.metadata.tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(tool_id)
            
            self._successful_registrations += 1
            self._logger.info(f"Registered tool: {tool_id} ({tool.metadata.tool_type.value})")
            return True
            
        except Exception as e:
            self._failed_registrations += 1
            # FAIL FAST: Tool registration failures are critical
            raise ToolError(
                f"Failed to register tool: {e}",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("tool_registry", "register"),
                suggestion="Check tool metadata, dependencies, and implementation",
                cause=e
            )
    
    def unregister(self, tool_id: str) -> bool:
        """Unregister a tool"""
        try:
            if tool_id not in self._tools:
                # FAIL FAST: Attempting to unregister non-existent tool is an error
                raise ToolError(
                    f"Tool {tool_id} not found for unregistration",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_registry", "unregister"),
                    suggestion=f"Check if tool {tool_id} is registered first"
                )
            
            tool = self._tools[tool_id]
            
            # Remove from indices
            self._tool_types[tool.metadata.tool_type].discard(tool_id)
            
            for capability in tool.metadata.capabilities:
                self._capabilities[capability].discard(tool_id)
            
            for tag in tool.metadata.tags:
                if tag in self._tags:
                    self._tags[tag].discard(tool_id)
                    # Clean up empty tag sets
                    if not self._tags[tag]:
                        del self._tags[tag]
            
            # Cleanup tool
            try:
                if hasattr(tool, 'cleanup'):
                    if inspect.iscoroutinefunction(tool.cleanup):
                        import asyncio
                        asyncio.create_task(tool.cleanup())
                    else:
                        tool.cleanup()
            except Exception as cleanup_error:
                # FAIL FAST: Tool cleanup failures are critical
                raise ToolError(
                    f"Error during tool cleanup for {tool_id}: {cleanup_error}",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_registry", "cleanup"),
                    suggestion=f"Check tool {tool_id} cleanup implementation",
                    cause=cleanup_error
                )
            
            # Remove from registry
            del self._tools[tool_id]
            
            self._logger.info(f"Unregistered tool: {tool_id}")
            return True
            
        except Exception as e:
            # FAIL FAST: Tool unregistration failures are critical
            raise ToolError(
                f"Failed to unregister tool {tool_id}: {e}",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("tool_registry", "unregister"),
                suggestion=f"Check if tool {tool_id} exists and can be properly cleaned up",
                cause=e
            )
    
    def get_tool(self, tool_id: str) -> Optional[IToolInterface]:
        """Get a tool by ID"""
        return self._tools.get(tool_id)
    
    def has_tool(self, tool_id: str) -> bool:
        """Check if tool is registered"""
        return tool_id in self._tools
    
    def list_tools(self, 
                   tool_type: Optional[ToolType] = None,
                   capabilities: Optional[List[ToolCapability]] = None,
                   tags: Optional[List[str]] = None
                   ) -> List[IToolInterface]:
        """List tools with optional filtering"""
        tool_ids = set(self._tools.keys())
        
        # Filter by tool type
        if tool_type:
            tool_ids &= self._tool_types[tool_type]
        
        # Filter by capabilities (tools must have ALL specified capabilities)
        if capabilities:
            for capability in capabilities:
                tool_ids &= self._capabilities[capability]
        
        # Filter by tags (tools must have ALL specified tags)
        if tags:
            for tag in tags:
                if tag in self._tags:
                    tool_ids &= self._tags[tag]
                else:
                    # Tag doesn't exist, no tools match
                    tool_ids = set()
                    break
        
        return [self._tools[tool_id] for tool_id in tool_ids]
    
    def search_tools(self, query: str) -> List[IToolInterface]:
        """Search tools by description or functionality"""
        query_lower = query.lower()
        matching_tools = []
        
        for tool in self._tools.values():
            # Search in name and description
            if (query_lower in tool.metadata.name.lower() or 
                query_lower in tool.metadata.description.lower()):
                matching_tools.append(tool)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in tool.metadata.tags):
                matching_tools.append(tool)
                continue
            
            # Search in method names and descriptions
            for method_schema in tool.metadata.methods.values():
                if (query_lower in method_schema.name.lower() or
                    query_lower in method_schema.description.lower()):
                    matching_tools.append(tool)
                    break
        
        return matching_tools
    
    @property
    def tool_count(self) -> int:
        """Number of registered tools"""
        return len(self._tools)
    
    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool schemas for LLM consumption - FAIL FAST on schema errors"""
        schemas = {}
        for tool_id, tool in self._tools.items():
            # FAIL FAST: Schema generation failures are critical - no fallbacks
            try:
                schemas[tool_id] = tool.get_schema()
            except Exception as e:
                raise ToolError(
                    f"Schema generation failed for tool {tool_id}: {e}",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_registry", "get_schemas"),
                    suggestion=f"Ensure tool {tool_id} implements proper schema generation. "
                              f"Check tool.get_schema() method and metadata configuration.",
                    cause=e
                )
        
        return schemas
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        tool_type_counts = {
            tool_type.value: len(tools) 
            for tool_type, tools in self._tool_types.items()
        }
        
        capability_counts = {
            capability.value: len(tools)
            for capability, tools in self._capabilities.items()
        }
        
        return {
            "registry_name": self.name,
            "total_tools": self.tool_count,
            "tool_types": tool_type_counts,
            "capabilities": capability_counts,
            "tags": {tag: len(tools) for tag, tools in self._tags.items()},
            "registration_stats": {
                "total_attempts": self._registration_count,
                "successful": self._successful_registrations,
                "failed": self._failed_registrations
            }
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Export tool configurations"""
        config = {
            "registry_name": self.name,
            "tools": []
        }
        
        for tool in self._tools.values():
            tool_config = {
                "id": tool.metadata.id,
                "name": tool.metadata.name,
                "description": tool.metadata.description,
                "type": tool.metadata.tool_type.value,
                "version": tool.metadata.version,
                "capabilities": [cap.value for cap in tool.metadata.capabilities],
                "tags": tool.metadata.tags
            }
            config["tools"].append(tool_config)
        
        return config
    
    def clear(self):
        """Clear all tools from registry"""
        tool_ids = list(self._tools.keys())
        for tool_id in tool_ids:
            self.unregister(tool_id)
        
        self._logger.info(f"Cleared all tools from registry {self.name}")
    
    def auto_populate_with_mcp_tools(self, mcp_tools_directory: str = None) -> int:
        """Auto-populate registry with adapted MCP tools"""
        if mcp_tools_directory is None:
            # Use package-relative path that works in both dev and production
            import langswarm.tools.mcp
            mcp_tools_directory = str(Path(langswarm.tools.mcp.__file__).parent)
        
        try:
            adapted_tools = auto_adapt_mcp_tools(mcp_tools_directory)
            registered_count = 0
            
            for adapter in adapted_tools:
                try:
                    if self.register(adapter):
                        registered_count += 1
                except Exception as e:
                    self._logger.warning(f"Failed to register adapted tool {adapter.metadata.id}: {e}")
            
            self._logger.info(f"✅ Auto-populated registry with {registered_count}/{len(adapted_tools)} MCP tools")
            return registered_count
            
        except Exception as e:
            self._logger.error(f"❌ Failed to auto-populate registry with MCP tools: {e}")
            return 0


class ServiceRegistry:
    """
    Advanced service registry with dependency injection and lifecycle management.
    
    Provides enterprise-grade tool management with:
    - Multiple registry support
    - Dependency injection
    - Lifecycle management
    - Health monitoring
    """
    
    def __init__(self):
        self._registries: Dict[str, ToolRegistry] = {}
        self._default_registry = "default"
        self._logger = logging.getLogger("service_registry")
        
        # Create default registry
        self._registries[self._default_registry] = ToolRegistry(self._default_registry)
    
    def create_registry(self, name: str) -> ToolRegistry:
        """Create a new tool registry"""
        if name in self._registries:
            # FAIL FAST: Duplicate registry creation is a configuration error
            raise ToolError(
                f"Registry {name} already exists",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("service_registry", "create_registry"),
                suggestion=f"Use get_registry('{name}') to access existing registry or choose a different name"
            )
        
        registry = ToolRegistry(name)
        self._registries[name] = registry
        self._logger.info(f"Created registry: {name}")
        return registry
    
    def get_registry(self, name: str = None) -> Optional[ToolRegistry]:
        """Get a registry by name"""
        registry_name = name or self._default_registry
        return self._registries.get(registry_name)
    
    def list_registries(self) -> List[str]:
        """List all registry names"""
        return list(self._registries.keys())
    
    def register_tool(self, tool: IToolInterface, registry_name: str = None) -> bool:
        """Register a tool in specified registry"""
        registry = self.get_registry(registry_name)
        if not registry:
            # FAIL FAST: Missing registry is a configuration error
            raise ToolError(
                f"Registry {registry_name} not found",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("service_registry", "register_tool"),
                suggestion=f"Ensure registry {registry_name} exists or use default registry"
            )
        
        return registry.register(tool)
    
    def get_tool(self, tool_id: str, registry_name: str = None) -> Optional[IToolInterface]:
        """Get a tool from specified registry"""
        if registry_name:
            registry = self.get_registry(registry_name)
            return registry.get_tool(tool_id) if registry else None
        
        # Search all registries
        for registry in self._registries.values():
            tool = registry.get_tool(tool_id)
            if tool:
                return tool
        
        return None
    
    def search_all_tools(self, query: str) -> Dict[str, List[IToolInterface]]:
        """Search tools across all registries"""
        results = {}
        for registry_name, registry in self._registries.items():
            tools = registry.search_tools(query)
            if tools:
                results[registry_name] = tools
        
        return results
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get schemas from all registries"""
        all_schemas = {}
        for registry_name, registry in self._registries.items():
            all_schemas[registry_name] = registry.get_schemas()
        
        return all_schemas
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check across all registries - FAIL FAST on tool failures"""
        health = {
            "service_registry": "healthy",
            "registries": {},
            "total_tools": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        for registry_name, registry in self._registries.items():
            registry_health = {
                "status": "healthy",
                "tool_count": registry.tool_count,
                "statistics": registry.get_statistics()
            }
            
            # Check individual tools - FAIL FAST on any tool health check failure
            tool_health = {}
            for tool_id, tool in registry._tools.items():
                try:
                    tool_health[tool_id] = tool.health_check()
                except Exception as e:
                    # FAIL FAST: Individual tool health failures are critical
                    raise ToolError(
                        f"Health check failed for tool {tool_id} in registry {registry_name}: {e}",
                        severity=ErrorSeverity.CRITICAL,
                        context=ErrorContext("service_registry", "health_check"),
                        suggestion=f"Tool {tool_id} is not functioning properly. "
                                  f"Check tool configuration, dependencies, and implementation.",
                        cause=e
                    )
            
            registry_health["tools"] = tool_health
            health["registries"][registry_name] = registry_health
            health["total_tools"] += registry.tool_count
        
        return health


class ToolDiscovery(IToolDiscovery):
    """Tool discovery system for auto-registration"""
    
    def __init__(self):
        self._logger = logging.getLogger("tool_discovery")
    
    def discover_tools(self, 
                       search_paths: List[str],
                       patterns: Optional[List[str]] = None
                       ) -> List[Dict[str, Any]]:
        """Discover tools in given paths - FAIL FAST on any errors"""
        patterns = patterns or ["**/main.py", "**/tool.py", "**/*_tool.py"]
        discovered = []
        
        for search_path in search_paths:
            path = Path(search_path)
            if not path.exists():
                # FAIL FAST: Missing search paths are configuration errors
                raise ToolError(
                    f"Tool discovery search path does not exist: {search_path}",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_discovery", "discover_tools"),
                    suggestion=f"Ensure the path {search_path} exists or remove it from search paths"
                )
            
            for pattern in patterns:
                for tool_file in path.glob(pattern):
                    tool_config = self._analyze_tool_file(tool_file)
                    if tool_config:
                        discovered.append(tool_config)
                    # Note: _analyze_tool_file now fails fast on errors, no try/except needed
        
        self._logger.info(f"Discovered {len(discovered)} tools")
        return discovered
    
    
    def auto_register(self, registry: IToolRegistry) -> int:
        """Auto-register discovered tools - FAIL FAST on any errors"""
        # Common tool discovery paths
        search_paths = [
            "langswarm/v2/tools/mcp",        # V2 MCP tools (new location)
            "langswarm/mcp/tools",           # Legacy MCP tools (fallback)
            "langswarm/v2/tools/builtin",
            "langswarm/synapse/tools",
            "."  # Current directory
        ]
        
        discovered = self.discover_tools(search_paths)
        registered_count = 0
        
        for tool_config in discovered:
            # FAIL FAST: No fallbacks for tool creation or registration failures
            tool = self._create_tool_from_config(tool_config)
            if not tool:
                raise ToolError(
                    f"Failed to create tool from config: {tool_config.get('class_name', 'unknown')}",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_discovery", "create_tool"),
                    suggestion="Check tool class implementation and required parameters"
                )
            
            if not registry.register(tool):
                raise ToolError(
                    f"Failed to register tool: {tool.metadata.id}",
                    severity=ErrorSeverity.CRITICAL,
                    context=ErrorContext("tool_discovery", "register_tool"),
                    suggestion="Check for duplicate tool IDs or registry configuration issues"
                )
            
            registered_count += 1
        
        self._logger.info(f"Auto-registered {registered_count} tools")
        return registered_count
    
    def _analyze_tool_file(self, tool_file: Path) -> Optional[Dict[str, Any]]:
        """Analyze a Python file for tool classes - FAIL FAST on errors"""
        # FAIL FAST: No try/except - let import and analysis errors bubble up
        spec = importlib.util.spec_from_file_location("tool_module", tool_file)
        if not spec or not spec.loader:
            raise ToolError(
                f"Could not create module spec for tool file: {tool_file}",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("tool_discovery", "analyze_file"),
                suggestion=f"Check if {tool_file} is a valid Python file"
            )
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for tool classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, BaseTool) or 
                hasattr(obj, 'metadata') or 
                name.endswith('Tool') or 
                name.endswith('MCPTool')):
                
                return {
                    "file_path": str(tool_file),
                    "class_name": name,
                    "module_name": module.__name__,
                    "tool_class": obj
                }
        
        # If no tool classes found, this is likely a configuration error
        raise ToolError(
            f"No valid tool classes found in {tool_file}",
            severity=ErrorSeverity.CRITICAL,
            context=ErrorContext("tool_discovery", "analyze_file"),
            suggestion=f"Ensure {tool_file} contains a class that extends BaseTool or has 'metadata' attribute"
        )
    
    def _create_tool_from_config(self, config: Dict[str, Any]) -> Optional[IToolInterface]:
        """Create a tool instance from discovery config - FAIL FAST with NO defaults"""
        tool_class = config["tool_class"]
        
        # FAIL FAST: No "reasonable defaults" - tools must be properly configured
        if not issubclass(tool_class, BaseTool):
            raise ToolError(
                f"Tool class {config['class_name']} does not extend BaseTool",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("tool_discovery", "create_tool"),
                suggestion=f"Ensure {config['class_name']} extends BaseTool properly"
            )
        
        # Check if tool requires parameters beyond self
        sig = inspect.signature(tool_class.__init__)
        required_params = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.default == param.empty:
                required_params.append(param_name)
        
        # FAIL FAST: If tool requires parameters, this is a configuration error
        if required_params:
            raise ToolError(
                f"Tool {config['class_name']} requires explicit configuration parameters: {required_params}",
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext("tool_discovery", "create_tool"),
                suggestion=f"Tool {config['class_name']} cannot be auto-discovered. "
                          f"Either make all parameters optional with defaults, or configure it explicitly."
            )
        
        # Only instantiate if no required parameters
        return tool_class()


# Global service registry instance
_global_service_registry = ServiceRegistry()


def get_global_registry() -> ServiceRegistry:
    """Get the global service registry"""
    return _global_service_registry


def auto_discover_tools(registry_name: str = None) -> int:
    """Auto-discover and register tools"""
    discovery = ToolDiscovery()
    registry = _global_service_registry.get_registry(registry_name)
    if not registry:
        # FAIL FAST: Missing registry for auto-discovery is critical
        raise ToolError(
            f"Registry {registry_name} not found for auto-discovery",
            severity=ErrorSeverity.CRITICAL,
            context=ErrorContext("auto_discover_tools", "get_registry"),
            suggestion=f"Ensure registry {registry_name} exists before attempting auto-discovery"
        )
    
    return discovery.auto_register(registry)
