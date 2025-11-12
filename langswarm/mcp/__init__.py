"""
MCP Compatibility Layer

Re-exports MCP base classes from V1 for use by V2 tools.
This allows V2 MCP tools to access the MCP server infrastructure
which currently resides in the V1 codebase.
"""

try:
    from langswarm.v1.mcp.server_base import BaseMCPToolServer
except ImportError:
    BaseMCPToolServer = None

__all__ = ['BaseMCPToolServer']

