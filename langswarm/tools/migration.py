"""
LangSwarm V2 Tool Migration System

Provides comprehensive tools for migrating legacy tools (Synapse, RAG, Plugins)
to the V2 unified tool system with full compatibility and enhanced capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type, Union
from pathlib import Path
import importlib

from .interfaces import IToolInterface, ToolType
from .adapters import (
    SynapseToolAdapter, RAGToolAdapter, PluginToolAdapter,
    LegacyToolAdapter, AdapterFactory
)
from .registry import ToolRegistry


class ToolMigrator:
    """
    Comprehensive tool migration system for converting legacy tools to V2.
    
    Handles:
    - Synapse tools (consensus, branching, routing, voting, aggregation)
    - RAG/Memory adapters (SQLite, Redis, ChromaDB, etc.)
    - Plugin system tools
    - Custom legacy tools
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()
        self.logger = logging.getLogger(__name__)
        
        # Migration statistics
        self._migration_stats = {
            "synapse_tools": 0,
            "rag_tools": 0,
            "plugin_tools": 0,
            "custom_tools": 0,
            "failed_migrations": 0,
            "total_migrated": 0
        }
        
        # Tool discovery patterns
        self._synapse_patterns = [
            'consensus', 'branching', 'routing', 'voting', 'aggregation'
        ]
        
        self._rag_patterns = [
            'adapter', 'retriever', 'database', 'memory', 'rag'
        ]
        
        self._plugin_patterns = [
            'plugin', 'extension', 'addon'
        ]
    
    async def migrate_synapse_tools(self, synapse_module_path: str = "langswarm.synapse.tools") -> List[IToolInterface]:
        """
        Migrate all Synapse tools to V2.
        
        Args:
            synapse_module_path: Path to Synapse tools module
            
        Returns:
            List of migrated V2 tools
        """
        self.logger.info("Starting Synapse tool migration")
        migrated_tools = []
        
        try:
            # Discover Synapse tools
            synapse_tools = await self._discover_synapse_tools(synapse_module_path)
            
            for tool_name, tool_class in synapse_tools.items():
                try:
                    # Create tool instance (if needed)
                    if isinstance(tool_class, type):
                        # Need to instantiate - create with minimal config
                        tool_instance = self._create_synapse_instance(tool_class)
                    else:
                        tool_instance = tool_class
                    
                    # Create V2 adapter
                    adapter = SynapseToolAdapter(
                        tool_instance,
                        tool_id=f"synapse_{tool_name}",
                        name=f"Synapse {tool_name.title()}",
                        description=f"Migrated Synapse {tool_name} tool with V2 interface"
                    )
                    
                    # Register the adapted tool
                    success = self.registry.register(adapter)
                    if success:
                        migrated_tools.append(adapter)
                        self._migration_stats["synapse_tools"] += 1
                        self.logger.info(f"Migrated Synapse tool: {tool_name}")
                    else:
                        self.logger.warning(f"Failed to register Synapse tool: {tool_name}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to migrate Synapse tool {tool_name}: {e}")
                    self._migration_stats["failed_migrations"] += 1
            
            self.logger.info(f"Synapse migration complete: {len(migrated_tools)} tools migrated")
            
        except Exception as e:
            self.logger.error(f"Synapse tool discovery failed: {e}")
        
        return migrated_tools
    
    async def migrate_rag_tools(self, memory_module_path: str = "langswarm.memory.adapters") -> List[IToolInterface]:
        """
        Migrate all RAG/Memory adapters to V2 tools.
        
        Args:
            memory_module_path: Path to memory adapters module
            
        Returns:
            List of migrated V2 memory tools
        """
        self.logger.info("Starting RAG/Memory tool migration")
        migrated_tools = []
        
        try:
            # Discover RAG adapters
            rag_adapters = await self._discover_rag_adapters(memory_module_path)
            
            for adapter_name, adapter_class in rag_adapters.items():
                try:
                    # Create adapter instance (if needed)
                    if isinstance(adapter_class, type):
                        # Need to instantiate - create with minimal config
                        adapter_instance = self._create_rag_instance(adapter_class, adapter_name)
                    else:
                        adapter_instance = adapter_class
                    
                    # Create V2 memory tool
                    tool = RAGToolAdapter(
                        adapter_instance,
                        tool_id=f"memory_{adapter_name}",
                        name=f"Memory {adapter_name.title()}",
                        description=f"Migrated {adapter_name} memory tool with V2 interface"
                    )
                    
                    # Register the adapted tool
                    success = await self.registry.register_tool(tool)
                    if success:
                        migrated_tools.append(tool)
                        self._migration_stats["rag_tools"] += 1
                        self.logger.info(f"Migrated RAG tool: {adapter_name}")
                    else:
                        self.logger.warning(f"Failed to register RAG tool: {adapter_name}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to migrate RAG tool {adapter_name}: {e}")
                    self._migration_stats["failed_migrations"] += 1
            
            self.logger.info(f"RAG migration complete: {len(migrated_tools)} tools migrated")
            
        except Exception as e:
            self.logger.error(f"RAG tool discovery failed: {e}")
        
        return migrated_tools
    
    async def migrate_plugin_tools(self, plugin_registry_path: str = "langswarm.cortex.registry.plugins") -> List[IToolInterface]:
        """
        Migrate plugin system tools to V2.
        
        Args:
            plugin_registry_path: Path to plugin registry
            
        Returns:
            List of migrated V2 plugin tools
        """
        self.logger.info("Starting Plugin tool migration")
        migrated_tools = []
        
        try:
            # Discover plugin tools
            plugin_tools = await self._discover_plugin_tools(plugin_registry_path)
            
            for plugin_name, plugin_instance in plugin_tools.items():
                try:
                    # Create V2 plugin adapter
                    adapter = PluginToolAdapter(
                        plugin_instance,
                        tool_id=f"plugin_{plugin_name}",
                        name=f"Plugin {plugin_name.title()}",
                        description=f"Migrated plugin {plugin_name} with V2 interface"
                    )
                    
                    # Register the adapted tool
                    success = self.registry.register(adapter)
                    if success:
                        migrated_tools.append(adapter)
                        self._migration_stats["plugin_tools"] += 1
                        self.logger.info(f"Migrated Plugin tool: {plugin_name}")
                    else:
                        self.logger.warning(f"Failed to register Plugin tool: {plugin_name}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to migrate Plugin tool {plugin_name}: {e}")
                    self._migration_stats["failed_migrations"] += 1
            
            self.logger.info(f"Plugin migration complete: {len(migrated_tools)} tools migrated")
            
        except Exception as e:
            self.logger.error(f"Plugin tool discovery failed: {e}")
        
        return migrated_tools
    
    async def migrate_all_legacy_tools(self) -> Dict[str, List[IToolInterface]]:
        """
        Migrate all legacy tools from all categories.
        
        Returns:
            Dictionary with migration results by category
        """
        self.logger.info("Starting comprehensive legacy tool migration")
        
        results = {
            "synapse": await self.migrate_synapse_tools(),
            "rag": await self.migrate_rag_tools(),
            "plugins": await self.migrate_plugin_tools()
        }
        
        # Update total statistics
        self._migration_stats["total_migrated"] = sum(len(tools) for tools in results.values())
        
        # Log migration summary
        self.logger.info("Legacy tool migration complete:")
        self.logger.info(f"  Synapse tools: {len(results['synapse'])}")
        self.logger.info(f"  RAG tools: {len(results['rag'])}")
        self.logger.info(f"  Plugin tools: {len(results['plugins'])}")
        self.logger.info(f"  Total migrated: {self._migration_stats['total_migrated']}")
        self.logger.info(f"  Failed migrations: {self._migration_stats['failed_migrations']}")
        
        return results
    
    async def migrate_custom_tool(
        self,
        tool: Any,
        tool_id: str = None,
        tool_type: ToolType = None,
        **kwargs
    ) -> Optional[IToolInterface]:
        """
        Migrate a custom legacy tool using automatic adapter selection.
        
        Args:
            tool: Legacy tool instance
            tool_id: Optional tool ID
            tool_type: Optional tool type hint
            **kwargs: Additional configuration
            
        Returns:
            Migrated V2 tool or None if migration failed
        """
        try:
            # Use adapter factory to create appropriate adapter
            adapter = AdapterFactory.create_adapter(tool, tool_id=tool_id, **kwargs)
            
            if adapter:
                # Register the adapted tool
                success = self.registry.register(adapter)
                if success:
                    self._migration_stats["custom_tools"] += 1
                    self.logger.info(f"Migrated custom tool: {adapter.metadata.id}")
                    return adapter
                else:
                    self.logger.warning(f"Failed to register custom tool: {adapter.metadata.id}")
            else:
                self.logger.warning(f"No suitable adapter found for tool: {type(tool).__name__}")
                
        except Exception as e:
            self.logger.error(f"Failed to migrate custom tool: {e}")
            self._migration_stats["failed_migrations"] += 1
        
        return None
    
    async def _discover_synapse_tools(self, module_path: str) -> Dict[str, Any]:
        """Discover available Synapse tools"""
        discovered_tools = {}
        
        try:
            # Import and scan Synapse tools module
            synapse_tools_module = importlib.import_module(module_path)
            
            # Scan for tool directories
            for pattern in self._synapse_patterns:
                try:
                    tool_module = importlib.import_module(f"{module_path}.{pattern}.main")
                    
                    # Look for tool classes
                    for attr_name in dir(tool_module):
                        attr = getattr(tool_module, attr_name)
                        if (isinstance(attr, type) and 
                            'Tool' in attr.__name__ and
                            pattern.lower() in attr.__name__.lower()):
                            discovered_tools[pattern] = attr
                            break
                            
                except ImportError:
                    self.logger.debug(f"Synapse tool module not found: {pattern}")
                    continue
                    
        except ImportError as e:
            self.logger.warning(f"Failed to import Synapse tools module {module_path}: {e}")
        
        return discovered_tools
    
    async def _discover_rag_adapters(self, module_path: str) -> Dict[str, Any]:
        """Discover available RAG adapters"""
        discovered_adapters = {}
        
        try:
            # Common RAG adapter types to look for
            adapter_types = [
                'sqlite', 'redis', 'chromadb', 'milvus', 'qdrant',
                'elasticsearch', 'bigquery', 'pinecone', 'gcs', 'llamaindex'
            ]
            
            for adapter_type in adapter_types:
                try:
                    # Try different import patterns
                    import_patterns = [
                        f"{module_path}.{adapter_type}",
                        f"{module_path}._langswarm.{adapter_type}.main",
                        f"{module_path}.langchain",  # For langchain adapters
                        f"{module_path}.llamaindex"  # For llamaindex adapters
                    ]
                    
                    for pattern in import_patterns:
                        try:
                            adapter_module = importlib.import_module(pattern)
                            
                            # Look for adapter classes
                            for attr_name in dir(adapter_module):
                                attr = getattr(adapter_module, attr_name)
                                if (isinstance(attr, type) and 
                                    'Adapter' in attr.__name__ and
                                    adapter_type.lower() in attr.__name__.lower()):
                                    discovered_adapters[adapter_type] = attr
                                    break
                            
                            if adapter_type in discovered_adapters:
                                break
                                
                        except ImportError:
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"Failed to discover RAG adapter {adapter_type}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Failed to discover RAG adapters: {e}")
        
        return discovered_adapters
    
    async def _discover_plugin_tools(self, registry_path: str) -> Dict[str, Any]:
        """Discover available plugin tools"""
        discovered_plugins = {}
        
        try:
            # Import plugin registry
            plugin_module = importlib.import_module(registry_path)
            
            # Look for plugin registry or plugin instances
            if hasattr(plugin_module, 'PluginRegistry'):
                registry = plugin_module.PluginRegistry()
                if hasattr(registry, 'plugins'):
                    discovered_plugins.update(registry.plugins)
                elif hasattr(registry, 'get_plugins'):
                    discovered_plugins.update(registry.get_plugins())
            
            # Also check for direct plugin instances in module
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if ('plugin' in attr_name.lower() and 
                    not isinstance(attr, type) and
                    callable(attr)):
                    discovered_plugins[attr_name] = attr
                    
        except ImportError as e:
            self.logger.warning(f"Failed to import plugin registry {registry_path}: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to discover plugins: {e}")
        
        return discovered_plugins
    
    def _create_synapse_instance(self, tool_class: Type) -> Any:
        """Create a Synapse tool instance with minimal configuration"""
        class_name = tool_class.__name__.lower()
        
        if 'consensus' in class_name:
            # Create with dummy agents
            return tool_class(
                identifier="migrated_consensus",
                agents=[],  # Empty agents list for migration
            )
        elif 'branching' in class_name:
            return tool_class(
                identifier="migrated_branching",
                agents=[],
            )
        elif 'routing' in class_name:
            return tool_class(
                identifier="migrated_routing",
                route=1,
                bots={},
                main_bot=None
            )
        elif 'voting' in class_name:
            return tool_class(
                identifier="migrated_voting",
                agents=[],
            )
        elif 'aggregation' in class_name:
            return tool_class(
                identifier="migrated_aggregation",
                agents=[],
            )
        else:
            # Generic instantiation
            return tool_class(identifier="migrated_synapse_tool")
    
    def _create_rag_instance(self, adapter_class: Type, adapter_name: str) -> Any:
        """Create a RAG adapter instance with minimal configuration"""
        if 'sqlite' in adapter_name.lower():
            return adapter_class(
                identifier=f"migrated_{adapter_name}",
                db_path=":memory:"
            )
        elif 'redis' in adapter_name.lower():
            return adapter_class(
                identifier=f"migrated_{adapter_name}",
                redis_url="redis://localhost:6379/0"
            )
        elif 'chromadb' in adapter_name.lower():
            return adapter_class(
                identifier=f"migrated_{adapter_name}",
                collection_name="migration_test"
            )
        else:
            # Generic instantiation
            return adapter_class(identifier=f"migrated_{adapter_name}")
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """Get migration statistics"""
        return self._migration_stats.copy()
    
    def reset_stats(self):
        """Reset migration statistics"""
        self._migration_stats = {
            "synapse_tools": 0,
            "rag_tools": 0,
            "plugin_tools": 0,
            "custom_tools": 0,
            "failed_migrations": 0,
            "total_migrated": 0
        }


class ToolCompatibilityLayer:
    """
    Compatibility layer for existing tool usage patterns.
    
    Provides compatibility with V1 tool calling patterns while
    using the V2 tool system underneath.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)
    
    async def execute_legacy_call(
        self,
        tool_type: str,
        method: str,
        instance_name: str,
        action: str = "",
        parameters: Dict[str, Any] = None
    ) -> Any:
        """
        Execute legacy tool call format.
        
        Compatible with existing patterns like:
        {
          "type": "rag",
          "method": "execute",
          "instance_name": "sqlite_memory",
          "action": "query",
          "parameters": {"query": "search text"}
        }
        """
        try:
            # Find tool by instance name or type
            tool = await self._find_legacy_tool(tool_type, instance_name)
            
            if not tool:
                raise ValueError(f"Tool not found: {instance_name} ({tool_type})")
            
            # Execute using V2 interface
            if method == "execute":
                input_data = {
                    "action": action,
                    "parameters": parameters or {}
                }
                return await tool.execute("run", input_data)
            
            elif method == "request":
                # Handle request for tool information
                return {
                    "tool_id": tool.metadata.id,
                    "name": tool.metadata.name,
                    "description": tool.metadata.description,
                    "methods": [method.name for method in tool.metadata.methods],
                    "type": tool.metadata.tool_type.value
                }
            
            else:
                # Direct method call
                return await tool.execute(method, parameters or {})
                
        except Exception as e:
            self.logger.error(f"Legacy tool call failed: {e}")
            raise
    
    async def _find_legacy_tool(self, tool_type: str, instance_name: str) -> Optional[IToolInterface]:
        """Find tool by legacy naming patterns"""
        # Try exact instance name first
        tools = await self.registry.find_tools(name=instance_name)
        if tools:
            return tools[0]
        
        # Try by tool ID
        tool = await self.registry.get_tool(instance_name)
        if tool:
            return tool
        
        # Search by type and tags
        type_mapping = {
            "rag": ToolType.MEMORY,
            "rags": ToolType.MEMORY,
            "retriever": ToolType.MEMORY,
            "retrievers": ToolType.MEMORY,
            "memory": ToolType.MEMORY,
            "synapse": ToolType.WORKFLOW,
            "plugin": ToolType.UTILITY,
            "workflow": ToolType.WORKFLOW
        }
        
        if tool_type.lower() in type_mapping:
            target_type = type_mapping[tool_type.lower()]
            tools = await self.registry.find_tools(tool_type=target_type)
            
            # Try to match by name similarity
            for tool in tools:
                if (instance_name.lower() in tool.metadata.name.lower() or
                    instance_name.lower() in tool.metadata.id.lower()):
                    return tool
        
        return None


# Global migrator instance
_global_migrator: Optional[ToolMigrator] = None


def get_tool_migrator(registry: Optional[ToolRegistry] = None) -> ToolMigrator:
    """Get the global tool migrator instance"""
    global _global_migrator
    if _global_migrator is None:
        _global_migrator = ToolMigrator(registry)
    return _global_migrator


async def migrate_all_tools(registry: Optional[ToolRegistry] = None) -> Dict[str, List[IToolInterface]]:
    """
    Convenience function to migrate all legacy tools.
    
    Args:
        registry: Tool registry to use for registration
        
    Returns:
        Dictionary with migration results by category
    """
    migrator = get_tool_migrator(registry)
    return await migrator.migrate_all_legacy_tools()


async def create_compatibility_layer(registry: ToolRegistry) -> ToolCompatibilityLayer:
    """
    Create compatibility layer for legacy tool usage.
    
    Args:
        registry: V2 tool registry
        
    Returns:
        Compatibility layer instance
    """
    return ToolCompatibilityLayer(registry)
