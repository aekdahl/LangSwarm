"""
LangSwarm V2 Tool Adapters

Compatibility adapters for existing tool types to provide seamless migration
from V1 to V2 tool systems. These adapters wrap existing tools to provide
the V2 IToolInterface while maintaining backward compatibility.
"""

from .base import LegacyToolAdapter, AdapterFactory
from .synapse import SynapseToolAdapter
from .rag import RAGToolAdapter
from .plugin import PluginToolAdapter
from .mcp import MCPToolAdapter

__all__ = [
    'LegacyToolAdapter',
    'SynapseToolAdapter', 
    'RAGToolAdapter',
    'PluginToolAdapter',
    'MCPToolAdapter',
    'AdapterFactory'
]
