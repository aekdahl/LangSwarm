"""
Tool Manager for AAF Backend
Manages integration of custom tools with LangSwarm
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path

from .config import get_settings
from ..tools import (
    create_web_scraper_tool, 
    get_web_scraper_tool_config,
    create_vector_search_rag_tool,
    get_vector_search_rag_tool_config
)

logger = logging.getLogger(__name__)


class ToolManager:
    """Manages custom tools for AAF backend"""
    
    def __init__(self):
        self.tools = {}
        self.tool_configs = {}
        self.settings = get_settings()
        
    async def initialize_tools(self):
        """Initialize all available tools"""
        try:
            # Initialize web scraper tool
            await self._initialize_web_scraper()
            
            # Initialize vector search RAG tool  
            await self._initialize_vector_search_rag()
            
            # Update LangSwarm configuration
            await self._update_langswarm_config()
            
            logger.info(f"Tool manager initialized with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise
    
    async def _initialize_web_scraper(self):
        """Initialize web scraper tool"""
        try:
            # Check if crawl4ai MCP is configured
            mcp_url = getattr(self.settings, 'crawl4ai_mcp_url', None)
            api_key = getattr(self.settings, 'crawl4ai_api_key', None)
            
            if mcp_url:
                tool = create_web_scraper_tool(mcp_url, api_key)
                self.tools['web_scraper'] = tool
                self.tool_configs['web_scraper'] = get_web_scraper_tool_config()
                
                logger.info("Web scraper tool initialized")
            else:
                logger.info("Web scraper tool not configured (CRAWL4AI_MCP_URL not set)")
                
        except Exception as e:
            logger.error(f"Failed to initialize web scraper tool: {e}")
    
    async def _initialize_vector_search_rag(self):
        """Initialize vector search RAG tool"""
        try:
            # Get BigQuery configuration
            project_id = getattr(self.settings, 'google_cloud_project', None)
            dataset_id = getattr(self.settings, 'bigquery_dataset_id', None)
            embedding_model = getattr(self.settings, 'embedding_model', 'text-embedding-3-small')
            
            if project_id and dataset_id:
                tool = create_vector_search_rag_tool(project_id, dataset_id, embedding_model)
                await tool.initialize()
                
                self.tools['vector_search_rag'] = tool
                self.tool_configs['vector_search_rag'] = get_vector_search_rag_tool_config()
                
                logger.info(f"Vector search RAG tool initialized with BigQuery dataset: {dataset_id}")
            else:
                logger.info("Vector search RAG tool not configured (missing BigQuery settings)")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector search RAG tool: {e}")
    
    async def _update_langswarm_config(self):
        """Update LangSwarm configuration with custom tools"""
        try:
            config_path = Path("config/langswarm.yaml")
            
            # Load current configuration
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}
            
            # Ensure tools section exists
            if 'tools' not in config:
                config['tools'] = []
            
            # Add custom tools to configuration
            existing_tool_names = {tool.get('name') for tool in config['tools']}
            
            for tool_name, tool_config in self.tool_configs.items():
                if tool_config and tool_name not in existing_tool_names:
                    # Add tool configuration
                    if tool_config['type'] == 'remote_mcp':
                        config['tools'].append({
                            'name': tool_name,
                            'type': 'remote_mcp',
                            'server_url': tool_config['config']['server_url'],
                            'api_key': tool_config['config'].get('api_key'),
                            'timeout': tool_config['config'].get('timeout', 60),
                            'retry_count': tool_config['config'].get('retry_count', 3)
                        })
                    elif tool_config['type'] == 'local_mcp':
                        config['tools'].append({
                            'name': tool_name,
                            'type': 'local_mcp',
                            'description': tool_config['description'],
                            'functions': self._get_tool_functions(tool_name)
                        })
            
            # Write updated configuration
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info("LangSwarm configuration updated with custom tools")
            
        except Exception as e:
            logger.error(f"Failed to update LangSwarm configuration: {e}")
    
    def _get_tool_functions(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get function definitions for a tool"""
        tool = self.tools.get(tool_name)
        if tool and hasattr(tool, 'get_tool_schema'):
            schema = tool.get_tool_schema()
            return schema.get('functions', [])
        return []
    
    async def call_tool(self, tool_name: str, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a custom tool function"""
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not found",
                    "content": None
                }
            
            # Call the tool
            if hasattr(tool, 'call_tool'):
                if tool_name == 'vector_search_rag':
                    # Vector search RAG uses function-based calling
                    return await tool.call_tool(function_name, arguments)
                else:
                    # Web scraper uses direct calling
                    return await tool.call_tool(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} does not support function calls",
                    "content": None
                }
                
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}.{function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools and their capabilities"""
        tools_info = {}
        
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'get_tool_schema'):
                schema = tool.get_tool_schema()
                tools_info[tool_name] = {
                    "name": schema.get("name", tool_name),
                    "description": schema.get("description", ""),
                    "type": self.tool_configs.get(tool_name, {}).get("type", "unknown"),
                    "functions": schema.get("functions", []),
                    "parameters": schema.get("parameters", {})
                }
            else:
                tools_info[tool_name] = {
                    "name": tool_name,
                    "description": getattr(tool, 'description', ''),
                    "type": "unknown",
                    "functions": []
                }
        
        return {
            "success": True,
            "tools": tools_info,
            "count": len(tools_info)
        }
    
    async def get_tool_status(self, tool_name: str) -> Dict[str, Any]:
        """Get status information for a specific tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found"
            }
        
        status = {
            "name": tool_name,
            "available": True,
            "type": self.tool_configs.get(tool_name, {}).get("type", "unknown")
        }
        
        # Add tool-specific status information
        if tool_name == "web_scraper":
            status.update({
                "mcp_server_url": getattr(self.settings, 'crawl4ai_mcp_url', None),
                "authenticated": bool(getattr(self.settings, 'crawl4ai_api_key', None))
            })
        elif tool_name == "vector_search_rag":
            status.update({
                "project_id": getattr(self.settings, 'google_cloud_project', None),
                "dataset_id": getattr(self.settings, 'bigquery_dataset_id', None),
                "collections_loaded": len(getattr(tool, 'collections', {}))
            })
        
        return {
            "success": True,
            "status": status
        }
    
    async def close(self):
        """Close all tools and cleanup resources"""
        for tool_name, tool in self.tools.items():
            try:
                if hasattr(tool, 'close'):
                    await tool.close()
                logger.info(f"Closed {tool_name} tool")
            except Exception as e:
                logger.error(f"Error closing {tool_name} tool: {e}")
        
        self.tools.clear()
        self.tool_configs.clear()


# Global tool manager instance
tool_manager = None

async def get_tool_manager() -> ToolManager:
    """Get or create the global tool manager"""
    global tool_manager
    if tool_manager is None:
        tool_manager = ToolManager()
        await tool_manager.initialize_tools()
    return tool_manager

async def close_tool_manager():
    """Close the global tool manager"""
    global tool_manager
    if tool_manager:
        await tool_manager.close()
        tool_manager = None
