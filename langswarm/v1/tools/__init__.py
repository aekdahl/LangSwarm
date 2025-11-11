"""
LangSwarm Tools Module

Smart routing between V1 tool types and unified V2 tool system.
Provides backward compatibility while enabling gradual migration to V2.
"""

import os
import warnings
from typing import TYPE_CHECKING, Optional, Any, Dict, List

# V2 Tool System Availability Check
try:
    from ..v2.tools import (
        ToolRegistry as V2ToolRegistry,
        auto_discover_tools,
        BaseTool as V2BaseTool,
        ToolExecutor,
        AdapterFactory
    )
    from ..v2.tools.mcp import *  # MCP tools now in V2 location
    V2_TOOLS_AVAILABLE = True
except ImportError:
    V2_TOOLS_AVAILABLE = False

# V1 Legacy Tool Imports
try:
    # MCP tools from old location (if still there)
    from ..mcp.tools import *
except ImportError:
    pass

try:
    # Synapse tools
    from ..synapse.tools import *
except ImportError:
    pass

try:
    # Other V1 tool types
    from ..core.tools import *
except ImportError:
    pass


def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """Get feature flag from environment or configuration"""
    env_var = f"LANGSWARM_{flag_name.upper()}"
    return os.getenv(env_var, str(default)).lower() in ('true', '1', 'yes', 'on')


class SmartToolRegistry:
    """Smart tool registry that routes between V1 and V2 implementations"""
    
    def __new__(cls, *args, **kwargs):
        use_v2 = kwargs.pop('use_v2', None)
        if use_v2 is None:
            use_v2 = get_feature_flag('USE_V2_TOOLS', True)  # Default to V2 for tools
        
        if use_v2 and V2_TOOLS_AVAILABLE:
            return V2ToolRegistry(*args, **kwargs)
        else:
            # Fallback to basic registry for V1
            return _LegacyToolRegistry(*args, **kwargs)


class _LegacyToolRegistry:
    """Basic registry for V1 tool compatibility"""
    
    def __init__(self):
        self._tools = {}
        warnings.warn(
            "Using legacy tool registry. Consider upgrading to V2 unified tool system.",
            DeprecationWarning,
            stacklevel=3
        )
    
    def register(self, tool, name: str = None):
        """Register a tool"""
        tool_name = name or getattr(tool, 'name', str(tool))
        self._tools[tool_name] = tool
        return True
    
    def get_tool(self, name: str):
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self):
        """List all registered tools"""
        return list(self._tools.keys())


def get_tool(tool_name: str, registry_name: str = None, **kwargs):
    """Smart tool getter that works with both V1 and V2"""
    
    if V2_TOOLS_AVAILABLE and get_feature_flag('USE_V2_TOOLS', True):
        # Use V2 tool system
        registry = V2ToolRegistry() if not registry_name else V2ToolRegistry(registry_name)
        tool = registry.get_tool(tool_name)
        
        if tool:
            return tool
        
        # Try auto-discovery if tool not found
        discovered = auto_discover_tools(registry_name)
        if discovered > 0:
            return registry.get_tool(tool_name)
    
    # Fallback to V1 tool lookup
    warnings.warn(
        f"Tool '{tool_name}' not found in V2 system, using V1 fallback",
        UserWarning,
        stacklevel=2
    )
    
    # Try to find in legacy locations
    # This would implement V1 tool discovery logic
    return None


def migrate_tools_to_v2(source_paths: List[str] = None, dry_run: bool = False):
    """Migrate V1 tools to V2 system"""
    
    if not V2_TOOLS_AVAILABLE:
        raise RuntimeError("V2 tool system not available")
    
    from ..v2.tools.migration import ToolMigrator
    
    migrator = ToolMigrator()
    
    # Default paths to search for V1 tools
    if not source_paths:
        source_paths = [
            "langswarm/mcp/tools",  # Legacy MCP location
            "langswarm/synapse/tools",
            "langswarm/core/tools"
        ]
    
    if dry_run:
        print("🔍 Dry run - discovering tools that would be migrated:")
        for path in source_paths:
            print(f"  Searching: {path}")
        return
    
    # Perform actual migration
    result = migrator.discover_and_migrate_all(source_paths)
    
    print(f"Migration Results:")
    print(f"  MCP tools: {result.get('mcp_tools', 0)}")
    print(f"  Synapse tools: {result.get('synapse_tools', 0)}")
    print(f"  Other tools: {result.get('other_tools', 0)}")
    print(f"  Total migrated: {sum(result.values())}")
    
    return result


# Main exports - Smart routing during migration
ToolRegistry = SmartToolRegistry

# V2 exports (when available)
if V2_TOOLS_AVAILABLE:
    # V2 native classes for new development
    BaseTool = V2BaseTool
    ToolExecutor = ToolExecutor
    auto_discover_tools = auto_discover_tools
    
    # Migration utilities
    migrate_tools_to_v2 = migrate_tools_to_v2

# Migration utilities
def enable_v2_tools_globally():
    """Enable V2 tool system globally for this session"""
    os.environ['LANGSWARM_USE_V2_TOOLS'] = 'true'
    print("✅ V2 tool system enabled globally")

def disable_v2_tools_globally():
    """Disable V2 tool system globally for this session"""
    os.environ['LANGSWARM_USE_V2_TOOLS'] = 'false'
    print("✅ V1 tool system enabled globally")

def get_tools_version_info():
    """Get information about tool system versions and configuration"""
    
    info = {
        'v2_available': V2_TOOLS_AVAILABLE,
        'v2_enabled': get_feature_flag('USE_V2_TOOLS', True),
        'mcp_tools_location': None,
        'discovered_tools': {}
    }
    
    # Check where MCP tools are located
    try:
        import langswarm.v2.tools.mcp
        info['mcp_tools_location'] = 'langswarm/v2/tools/mcp/ (V2 location)'
    except ImportError:
        try:
            import langswarm.v1.mcp.tools
            info['mcp_tools_location'] = 'langswarm/mcp/tools/ (V1 location)'
        except ImportError:
            info['mcp_tools_location'] = 'Not found'
    
    # Try to get tool counts
    if V2_TOOLS_AVAILABLE:
        try:
            registry = V2ToolRegistry()
            discovered = auto_discover_tools()
            info['discovered_tools']['v2_count'] = discovered
            info['discovered_tools']['registered_tools'] = len(registry.list_tools())
        except Exception as e:
            info['discovered_tools']['error'] = str(e)
    
    return info

__all__ = [
    # Main interfaces (smart routing)
    'ToolRegistry',
    'get_tool',
    
    # V2 interfaces (when available)
    'BaseTool',
    'ToolExecutor',
    'auto_discover_tools',
    
    # Migration utilities
    'migrate_tools_to_v2',
    'enable_v2_tools_globally',
    'disable_v2_tools_globally',
    'get_tools_version_info'
]
