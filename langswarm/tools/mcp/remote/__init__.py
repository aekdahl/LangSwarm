"""
Remote MCP Tool
===============

Generic tool for connecting to remote MCP servers via HTTP/HTTPS.
Supports authentication, schema discovery, and full JSON-RPC MCP protocol.
"""

from .main import RemoteMCPTool, create_user_mcp_tool

__all__ = ["RemoteMCPTool", "create_user_mcp_tool"]