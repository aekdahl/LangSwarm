"""
Multi-Tool Manager for AAF Backend
Enhanced tool manager supporting multiple instances from different sources
"""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

from .config import get_settings
from ..tools import (
    create_web_scraper_tool, 
    get_web_scraper_tool_config,
    create_vector_search_rag_tool,
    get_vector_search_rag_tool_config
)

logger = logging.getLogger(__name__)


class ToolConfiguration(BaseModel):
    """Tool configuration model"""
    tool_id: str = Field(..., description="Unique tool identifier")
    tool_type: str = Field(..., description="Type of tool (web_scraper, vector_search_rag)")
    name: str = Field(..., description="Display name for the tool")
    description: Optional[str] = Field(None, description="Tool description")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    config: Dict[str, Any] = Field(..., description="Tool-specific configuration")
    tags: List[str] = Field(default=[], description="Tags for categorizing tools")
    priority: int = Field(default=0, description="Tool priority for ordering")


class ToolSource(BaseModel):
    """Tool source configuration"""
    source_id: str = Field(..., description="Unique source identifier")
    source_type: str = Field(..., description="Source type (env, file, api, dynamic)")
    source_path: Optional[str] = Field(None, description="Path to source configuration")
    tools: List[ToolConfiguration] = Field(..., description="Tools from this source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Source metadata")


class MultiToolManager:
    """Enhanced tool manager supporting multiple tool instances"""
    
    def __init__(self):
        self.tools = {}  # tool_id -> tool_instance
        self.tool_configs = {}  # tool_id -> ToolConfiguration
        self.tool_sources = {}  # source_id -> ToolSource
        self.settings = get_settings()
        self.tool_factories = {
            "web_scraper": self._create_web_scraper_tool,
            "vector_search_rag": self._create_vector_search_rag_tool
        }
        
    async def initialize_tools(self):
        """Initialize all tools from all sources"""
        try:
            # Load from environment variables (legacy support)
            await self._load_from_environment()
            
            # Load from configuration files
            await self._load_from_config_files()
            
            # Load from dynamic sources (API, database, etc.)
            await self._load_from_dynamic_sources()
            
            # Initialize all configured tools
            await self._initialize_all_tools()
            
            # Update LangSwarm configuration
            await self._update_langswarm_config()
            
            logger.info(f"Multi-tool manager initialized with {len(self.tools)} tools from {len(self.tool_sources)} sources")
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-tool manager: {e}")
            raise
    
    async def _load_from_environment(self):
        """Load tool configurations from environment variables"""
        tools = []
        
        # Web scraper from environment
        mcp_url = getattr(self.settings, 'crawl4ai_mcp_url', None)
        api_key = getattr(self.settings, 'crawl4ai_api_key', None)
        
        if mcp_url:
            tools.append(ToolConfiguration(
                tool_id="web_scraper_default",
                tool_type="web_scraper",
                name="Default Web Scraper",
                description="Web scraper from environment configuration",
                config={
                    "mcp_server_url": mcp_url,
                    "api_key": api_key
                },
                tags=["environment", "web_scraping"]
            ))
        
        # Vector RAG from environment
        project_id = getattr(self.settings, 'google_cloud_project', None)
        dataset_id = getattr(self.settings, 'bigquery_dataset_id', None)
        embedding_model = getattr(self.settings, 'embedding_model', 'text-embedding-3-small')
        
        if project_id and dataset_id:
            tools.append(ToolConfiguration(
                tool_id="vector_rag_default",
                tool_type="vector_search_rag",
                name="Default Vector Search RAG",
                description="Vector search RAG from environment configuration",
                config={
                    "project_id": project_id,
                    "dataset_id": dataset_id,
                    "embedding_model": embedding_model
                },
                tags=["environment", "vector_search"]
            ))
        
        if tools:
            source = ToolSource(
                source_id="environment",
                source_type="env",
                tools=tools,
                metadata={"loaded_at": "startup", "source": "environment_variables"}
            )
            self.tool_sources["environment"] = source
            
            for tool_config in tools:
                self.tool_configs[tool_config.tool_id] = tool_config
    
    async def _load_from_config_files(self):
        """Load tool configurations from YAML/JSON files"""
        config_dir = Path("config/tools")
        
        if not config_dir.exists():
            logger.info("No tools configuration directory found")
            return
        
        for config_file in config_dir.glob("*.yaml"):
            await self._load_config_file(config_file)
        
        for config_file in config_dir.glob("*.json"):
            await self._load_config_file(config_file)
    
    async def _load_config_file(self, config_file: Path):
        """Load tools from a specific configuration file"""
        try:
            import os
            from string import Template
            
            # Read file content
            with open(config_file, 'r') as f:
                file_content = f.read()
            
            # Substitute environment variables
            template = Template(file_content)
            substituted_content = template.safe_substitute(os.environ)
            
            # Parse the substituted content
            if config_file.suffix == '.yaml':
                config_data = yaml.safe_load(substituted_content)
            else:
                config_data = json.loads(substituted_content)
            
            # Parse source configuration
            source_data = config_data.get('source', {})
            tools_data = config_data.get('tools', [])
            
            if not tools_data:
                logger.warning(f"No tools found in {config_file}")
                return
            
            # Create tool configurations
            tools = []
            for tool_data in tools_data:
                tool_config = ToolConfiguration(**tool_data)
                tools.append(tool_config)
            
            # Create source
            source = ToolSource(
                source_id=source_data.get('source_id', f"file_{config_file.stem}"),
                source_type="file",
                source_path=str(config_file),
                tools=tools,
                metadata={
                    "file_path": str(config_file),
                    "loaded_at": "startup"
                }
            )
            
            self.tool_sources[source.source_id] = source
            
            for tool_config in tools:
                self.tool_configs[tool_config.tool_id] = tool_config
            
            logger.info(f"Loaded {len(tools)} tools from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load tools from {config_file}: {e}")
    
    async def _load_from_dynamic_sources(self):
        """Load tools from dynamic sources (API, database, etc.)"""
        # This method can be extended to load from:
        # - REST API endpoints
        # - Database configurations
        # - Remote configuration services
        # - Plugin directories
        
        # Example: Load from API endpoint
        dynamic_config_url = getattr(self.settings, 'tools_config_api_url', None)
        if dynamic_config_url:
            await self._load_from_api(dynamic_config_url)
    
    async def _load_from_api(self, api_url: str):
        """Load tool configurations from API endpoint"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        config_data = await response.json()
                        
                        # Process API response similar to config file
                        sources_data = config_data.get('sources', [])
                        
                        for source_data in sources_data:
                            tools = [ToolConfiguration(**t) for t in source_data.get('tools', [])]
                            
                            source = ToolSource(
                                source_id=source_data['source_id'],
                                source_type="api",
                                tools=tools,
                                metadata={
                                    "api_url": api_url,
                                    "loaded_at": "startup"
                                }
                            )
                            
                            self.tool_sources[source.source_id] = source
                            
                            for tool_config in tools:
                                self.tool_configs[tool_config.tool_id] = tool_config
                        
                        logger.info(f"Loaded tools from API: {api_url}")
                    else:
                        logger.warning(f"Failed to load tools from API: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to load tools from API {api_url}: {e}")
    
    async def _initialize_all_tools(self):
        """Initialize all configured tools"""
        initialization_tasks = []
        
        for tool_id, tool_config in self.tool_configs.items():
            if tool_config.enabled:
                task = self._initialize_single_tool(tool_id, tool_config)
                initialization_tasks.append(task)
        
        # Initialize tools concurrently
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        # Log results
        successful = 0
        failed = 0
        
        for i, result in enumerate(results):
            tool_id = list(self.tool_configs.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to initialize tool {tool_id}: {result}")
                failed += 1
            else:
                successful += 1
        
        logger.info(f"Tool initialization complete: {successful} successful, {failed} failed")
    
    async def _initialize_single_tool(self, tool_id: str, tool_config: ToolConfiguration):
        """Initialize a single tool instance"""
        try:
            factory = self.tool_factories.get(tool_config.tool_type)
            if not factory:
                raise ValueError(f"Unknown tool type: {tool_config.tool_type}")
            
            tool_instance = await factory(tool_id, tool_config)
            self.tools[tool_id] = tool_instance
            
            logger.info(f"Initialized tool: {tool_id} ({tool_config.tool_type})")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool {tool_id}: {e}")
            raise
    
    async def _create_web_scraper_tool(self, tool_id: str, tool_config: ToolConfiguration):
        """Factory method for web scraper tools"""
        config = tool_config.config
        
        mcp_server_url = config.get('mcp_server_url')
        api_key = config.get('api_key')
        
        if not mcp_server_url:
            raise ValueError(f"Web scraper tool {tool_id} missing mcp_server_url")
        
        tool = create_web_scraper_tool(mcp_server_url, api_key)
        
        # Add custom metadata
        tool.tool_id = tool_id
        tool.display_name = tool_config.name
        tool.tags = tool_config.tags
        
        return tool
    
    async def _create_vector_search_rag_tool(self, tool_id: str, tool_config: ToolConfiguration):
        """Factory method for vector search RAG tools"""
        config = tool_config.config
        
        project_id = config.get('project_id')
        dataset_id = config.get('dataset_id')
        embedding_model = config.get('embedding_model', 'text-embedding-3-small')
        
        if not project_id or not dataset_id:
            raise ValueError(f"Vector RAG tool {tool_id} missing project_id or dataset_id")
        
        tool = create_vector_search_rag_tool(project_id, dataset_id, embedding_model)
        await tool.initialize()
        
        # Add custom metadata
        tool.tool_id = tool_id
        tool.display_name = tool_config.name
        tool.tags = tool_config.tags
        
        return tool
    
    async def add_tool_source(self, source: ToolSource) -> bool:
        """Dynamically add a new tool source"""
        try:
            # Validate source
            if source.source_id in self.tool_sources:
                logger.warning(f"Tool source {source.source_id} already exists, replacing")
            
            # Add source
            self.tool_sources[source.source_id] = source
            
            # Initialize tools from this source
            for tool_config in source.tools:
                if tool_config.enabled:
                    self.tool_configs[tool_config.tool_id] = tool_config
                    await self._initialize_single_tool(tool_config.tool_id, tool_config)
            
            # Update LangSwarm configuration
            await self._update_langswarm_config()
            
            logger.info(f"Added tool source {source.source_id} with {len(source.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add tool source {source.source_id}: {e}")
            return False
    
    async def remove_tool_source(self, source_id: str) -> bool:
        """Remove a tool source and its tools"""
        try:
            if source_id not in self.tool_sources:
                logger.warning(f"Tool source {source_id} not found")
                return False
            
            source = self.tool_sources[source_id]
            
            # Remove tools from this source
            for tool_config in source.tools:
                tool_id = tool_config.tool_id
                if tool_id in self.tools:
                    tool = self.tools[tool_id]
                    if hasattr(tool, 'close'):
                        await tool.close()
                    del self.tools[tool_id]
                    del self.tool_configs[tool_id]
            
            # Remove source
            del self.tool_sources[source_id]
            
            # Update LangSwarm configuration
            await self._update_langswarm_config()
            
            logger.info(f"Removed tool source {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove tool source {source_id}: {e}")
            return False
    
    async def get_tools_by_type(self, tool_type: str) -> List[str]:
        """Get all tool IDs of a specific type"""
        return [
            tool_id for tool_id, config in self.tool_configs.items()
            if config.tool_type == tool_type and config.enabled
        ]
    
    async def get_tools_by_tag(self, tag: str) -> List[str]:
        """Get all tool IDs with a specific tag"""
        return [
            tool_id for tool_id, config in self.tool_configs.items()
            if tag in config.tags and config.enabled
        ]
    
    async def call_tool(self, tool_id: str, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool by ID"""
        try:
            if tool_id not in self.tools:
                return {
                    "success": False,
                    "error": f"Tool {tool_id} not found",
                    "content": None
                }
            
            tool = self.tools[tool_id]
            tool_config = self.tool_configs[tool_id]
            
            # Call the tool based on its type
            if hasattr(tool, 'call_tool'):
                if tool_config.tool_type == 'vector_search_rag':
                    return await tool.call_tool(function_name, arguments)
                else:
                    return await tool.call_tool(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Tool {tool_id} does not support function calls",
                    "content": None
                }
                
        except Exception as e:
            logger.error(f"Tool call failed for {tool_id}.{function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def call_tool_by_type(self, tool_type: str, function_name: str, arguments: Dict[str, Any], prefer_tags: List[str] = None) -> Dict[str, Any]:
        """Call the first available tool of a specific type"""
        tools_of_type = await self.get_tools_by_type(tool_type)
        
        if not tools_of_type:
            return {
                "success": False,
                "error": f"No tools of type {tool_type} available",
                "content": None
            }
        
        # Prefer tools with specific tags
        if prefer_tags:
            for tag in prefer_tags:
                tagged_tools = await self.get_tools_by_tag(tag)
                matching_tools = [t for t in tools_of_type if t in tagged_tools]
                if matching_tools:
                    return await self.call_tool(matching_tools[0], function_name, arguments)
        
        # Use first available tool
        return await self.call_tool(tools_of_type[0], function_name, arguments)
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools with their metadata"""
        tools_info = {}
        
        for tool_id, tool in self.tools.items():
            config = self.tool_configs[tool_id]
            
            # Get source info
            source_info = None
            for source in self.tool_sources.values():
                if any(t.tool_id == tool_id for t in source.tools):
                    source_info = {
                        "source_id": source.source_id,
                        "source_type": source.source_type,
                        "source_path": source.source_path
                    }
                    break
            
            # Get tool schema
            schema = {}
            if hasattr(tool, 'get_tool_schema'):
                schema = tool.get_tool_schema()
            
            tools_info[tool_id] = {
                "tool_id": tool_id,
                "tool_type": config.tool_type,
                "name": config.name,
                "description": config.description,
                "enabled": config.enabled,
                "tags": config.tags,
                "priority": config.priority,
                "source": source_info,
                "schema": schema
            }
        
        return {
            "success": True,
            "tools": tools_info,
            "total_tools": len(tools_info),
            "total_sources": len(self.tool_sources),
            "tools_by_type": {
                tool_type: len(await self.get_tools_by_type(tool_type))
                for tool_type in set(config.tool_type for config in self.tool_configs.values())
            }
        }
    
    async def get_tool_status(self, tool_id: str) -> Dict[str, Any]:
        """Get detailed status for a specific tool"""
        if tool_id not in self.tools:
            return {
                "success": False,
                "error": f"Tool {tool_id} not found"
            }
        
        tool = self.tools[tool_id]
        config = self.tool_configs[tool_id]
        
        # Get source info
        source_info = None
        for source in self.tool_sources.values():
            if any(t.tool_id == tool_id for t in source.tools):
                source_info = source.dict()
                break
        
        status = {
            "tool_id": tool_id,
            "name": config.name,
            "tool_type": config.tool_type,
            "enabled": config.enabled,
            "tags": config.tags,
            "available": True,
            "source": source_info
        }
        
        # Add tool-specific status
        if config.tool_type == "web_scraper":
            status.update({
                "mcp_server_url": getattr(tool, 'mcp_server_url', None),
                "authenticated": bool(getattr(tool, 'api_key', None))
            })
        elif config.tool_type == "vector_search_rag":
            status.update({
                "project_id": getattr(tool, 'project_id', None),
                "dataset_id": getattr(tool, 'dataset_id', None),
                "collections_loaded": len(getattr(tool, 'collections', {}))
            })
        
        return {
            "success": True,
            "status": status
        }
    
    async def _update_langswarm_config(self):
        """Update LangSwarm configuration with all tools"""
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
            
            # Clear existing custom tools
            config['tools'] = [
                tool for tool in config['tools']
                if not tool.get('name', '').startswith(('web_scraper', 'vector_search_rag'))
            ]
            
            # Add all configured tools
            for tool_id, tool_config in self.tool_configs.items():
                if not tool_config.enabled:
                    continue
                
                if tool_config.tool_type == 'web_scraper':
                    config['tools'].append({
                        'name': tool_id,
                        'type': 'remote_mcp',
                        'server_url': tool_config.config.get('mcp_server_url'),
                        'api_key': tool_config.config.get('api_key'),
                        'timeout': 60,
                        'retry_count': 3,
                        'description': tool_config.description
                    })
                elif tool_config.tool_type == 'vector_search_rag':
                    config['tools'].append({
                        'name': tool_id,
                        'type': 'local_mcp',
                        'description': tool_config.description,
                        'functions': self._get_tool_functions(tool_id)
                    })
            
            # Write updated configuration
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Updated LangSwarm configuration with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to update LangSwarm configuration: {e}")
    
    def _get_tool_functions(self, tool_id: str) -> List[Dict[str, Any]]:
        """Get function definitions for a tool"""
        tool = self.tools.get(tool_id)
        if tool and hasattr(tool, 'get_tool_schema'):
            schema = tool.get_tool_schema()
            return schema.get('functions', [])
        return []
    
    async def close(self):
        """Close all tools and cleanup resources"""
        for tool_id, tool in self.tools.items():
            try:
                if hasattr(tool, 'close'):
                    await tool.close()
                logger.info(f"Closed tool: {tool_id}")
            except Exception as e:
                logger.error(f"Error closing tool {tool_id}: {e}")
        
        self.tools.clear()
        self.tool_configs.clear()
        self.tool_sources.clear()


# Global multi-tool manager instance
multi_tool_manager = None

async def get_multi_tool_manager() -> MultiToolManager:
    """Get or create the global multi-tool manager"""
    global multi_tool_manager
    if multi_tool_manager is None:
        multi_tool_manager = MultiToolManager()
        await multi_tool_manager.initialize_tools()
    return multi_tool_manager

async def close_multi_tool_manager():
    """Close the global multi-tool manager"""
    global multi_tool_manager
    if multi_tool_manager:
        await multi_tool_manager.close()
        multi_tool_manager = None
