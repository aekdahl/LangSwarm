"""
Real BigQuery Vector Search Debug Tool

This debug tool uses the ACTUAL LangSwarm BigQuery Vector Search tool
to test real functionality and identify real issues.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add project root to path for LangSwarm imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the ACTUAL LangSwarm BigQuery tool
try:
    from langswarm.core.config import ConfigurationLoader, load_config
    from langswarm.tools.registry import ToolRegistry
    from langswarm.tools.base import ToolResult
    LANGSWARM_AVAILABLE = True
except ImportError as e:
    print(f"❌ LangSwarm import failed: {e}")
    LANGSWARM_AVAILABLE = False
    ToolResult = None

# Import tracer
from debug.tools.tracer import get_debug_tracer, trace_event

logger = logging.getLogger(__name__)


class RealBigQueryDebugTool:
    """Debug wrapper for the ACTUAL LangSwarm BigQuery Vector Search tool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with the real LangSwarm BigQuery tool"""
        self.config = config or {}
        self.tracer = get_debug_tracer()
        
        if not LANGSWARM_AVAILABLE:
            raise ImportError("LangSwarm is not available - cannot create real BigQuery tool")
        
        # Configuration for the real tool
        self.project_id = self.config.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = self.config.get('dataset_id', 'vector_search')
        self.table_name = self.config.get('table_name', 'embeddings')
        self.location = self.config.get('location') or os.getenv('BIGQUERY_LOCATION', 'EU')
        
        if self.tracer:
            trace_event(
                "INFO",
                "real_bigquery_debug_tool",
                "init",
                "Initializing real BigQuery tool",
                "INFO",
                {
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "table_name": self.table_name,
                    "location": self.location,
                    "langswarm_available": LANGSWARM_AVAILABLE
                }
            )
        
        # Try to create the actual LangSwarm BigQuery tool
        try:
            self._create_real_tool()
            logger.info(f"Real BigQuery Debug Tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize real BigQuery tool: {e}")
            if self.tracer:
                trace_event(
                    "ERROR",
                    "real_bigquery_debug_tool",
                    "init",
                    f"Failed to initialize real tool: {e}",
                    "ERROR",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "project_id": self.project_id,
                        "dataset_id": self.dataset_id
                    }
                )
            raise
    
    def _create_real_tool(self):
        """Create the actual LangSwarm BigQuery tool"""
        
        # Method 1: Try using the tool registry
        try:
            registry = ToolRegistry()
            
            # Try to get the BigQuery tool from registry
            tool_config = {
                'project_id': self.project_id,
                'dataset_id': self.dataset_id,
                'table_name': self.table_name,
                'location': self.location,
                'max_results': self.config.get('max_results', 5),
                'default_similarity_threshold': self.config.get('similarity_threshold', 0.01)
            }
            
            # Try to create the tool using LangSwarm's registry
            self.bigquery_tool = registry.create_tool(
                tool_id="bigquery_vector_search",
                tool_type="mcp",
                config=tool_config
            )
            
            logger.info("Successfully created BigQuery tool via ToolRegistry")
            return
            
        except Exception as e:
            logger.warning(f"ToolRegistry approach failed: {e}")
        
        # Method 2: Try direct import and instantiation
        try:
            from langswarm.tools.mcp.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
            
            self.bigquery_tool = BigQueryVectorSearchMCPTool(
                identifier="debug_bigquery_search",
                settings={
                    'project_id': self.project_id,
                    'dataset_id': self.dataset_id,
                    'table_name': self.table_name,
                    'location': self.location,
                    'max_results': self.config.get('max_results', 5),
                    'default_similarity_threshold': self.config.get('similarity_threshold', 0.01)
                }
            )
            
            logger.info("Successfully created BigQuery tool via direct import")
            return
            
        except Exception as e:
            logger.warning(f"Direct import approach failed: {e}")
        
        # Method 3: Try using config loader
        try:
            # Create a temporary config file for the BigQuery tool
            temp_config = {
                'version': '1.0',
                'project_name': 'debug_bigquery_test',
                'tools': [
                    {
                        'id': 'bigquery_vector_search',
                        'type': 'mcp',
                        'location': 'langswarm.tools.mcp.bigquery_vector_search',
                        'config': {
                            'project_id': self.project_id,
                            'dataset_id': self.dataset_id,
                            'table_name': self.table_name,
                            'location': self.location,
                            'max_results': self.config.get('max_results', 5),
                            'default_similarity_threshold': self.config.get('similarity_threshold', 0.01)
                        }
                    }
                ]
            }
            
            import tempfile
            import yaml
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(temp_config, f)
                temp_config_path = f.name
            
            try:
                loader = ConfigurationLoader()
                config = loader.load(temp_config_path)
                tools = {tool.id: tool for tool in config.tools}
                
                if 'bigquery_vector_search' in tools:
                    self.bigquery_tool = tools['bigquery_vector_search']
                    logger.info("Successfully created BigQuery tool via config loader")
                    return
                else:
                    raise ValueError("BigQuery tool not found in loaded tools")
                    
            finally:
                os.unlink(temp_config_path)
                
        except Exception as e:
            logger.error(f"Config loader approach failed: {e}")
            raise RuntimeError(f"All methods to create real BigQuery tool failed. Last error: {e}")
    
    async def search(self, query: str, **kwargs) -> ToolResult:
        """Perform a real vector similarity search using the actual LangSwarm tool"""
        
        if self.tracer:
            trace_event(
                "START",
                "real_bigquery_debug_tool",
                "search",
                f"Starting REAL BigQuery search: {query[:50]}...",
                "INFO",
                {
                    "query": query,
                    "query_length": len(query),
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "table_name": self.table_name,
                    "location": self.location,
                    "tool_type": type(self.bigquery_tool).__name__,
                    **kwargs
                }
            )
        
        try:
            start_time = datetime.now()
            
            # Use the ACTUAL LangSwarm BigQuery tool
            search_params = {
                "query": query,
                "limit": kwargs.get('limit', self.config.get('max_results', 5)),
                "similarity_threshold": kwargs.get('similarity_threshold', self.config.get('similarity_threshold', 0.01))
            }
            
            # Try different methods to call the real tool
            result = None
            
            # Method 1: Try run_async if available
            if hasattr(self.bigquery_tool, 'run_async'):
                result = await self.bigquery_tool.run_async(search_params)
            # Method 2: Try direct similarity_search if available
            elif hasattr(self.bigquery_tool, 'similarity_search'):
                result = await self.bigquery_tool.similarity_search(**search_params)
            # Method 3: Try execute method
            elif hasattr(self.bigquery_tool, 'execute'):
                result = await self.bigquery_tool.execute("similarity_search", search_params)
            else:
                # Inspect the tool to see what methods are available
                available_methods = [method for method in dir(self.bigquery_tool) if not method.startswith('_')]
                raise AttributeError(f"Don't know how to call BigQuery tool. Available methods: {available_methods}")
            
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Trace successful completion
            if self.tracer:
                trace_event(
                    "SUCCESS",
                    "real_bigquery_debug_tool",
                    "search",
                    f"REAL BigQuery search completed",
                    "INFO",
                    {
                        "query": query,
                        "execution_time_ms": execution_time_ms,
                        "result_type": type(result).__name__,
                        "result_success": getattr(result, 'success', None) if hasattr(result, 'success') else None,
                        "project_id": self.project_id,
                        "dataset_id": self.dataset_id,
                        "location": self.location
                    }
                )
            
            # Convert result to ToolResult format
            if isinstance(result, dict):
                return ToolResult(
                    success=result.get('success', True),
                    data=result.get('results', result.get('data', result)),
                    metadata={
                        "method": "search",
                        "query": query,
                        "execution_time_ms": execution_time_ms,
                        "total_results": result.get('total_results', len(result.get('results', []))),
                        "dataset": f"{self.dataset_id}.{self.table_name}",
                        "project_id": self.project_id,
                        "location": self.location,
                        "tool_type": type(self.bigquery_tool).__name__,
                        "raw_result_type": type(result).__name__
                    }
                )
            elif hasattr(result, 'success'):
                # Looks like a ToolResult already
                return result
            else:
                return ToolResult(
                    success=True,
                    data=result,
                    metadata={
                        "method": "search",
                        "query": query,
                        "execution_time_ms": execution_time_ms,
                        "project_id": self.project_id,
                        "location": self.location,
                        "tool_type": type(self.bigquery_tool).__name__,
                        "raw_result_type": type(result).__name__
                    }
                )
                
        except Exception as e:
            # Trace the error
            if self.tracer:
                trace_event(
                    "ERROR",
                    "real_bigquery_debug_tool",
                    "search",
                    f"REAL BigQuery search failed: {e}",
                    "ERROR",
                    {
                        "query": query,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "project_id": self.project_id,
                        "dataset_id": self.dataset_id,
                        "location": self.location,
                        "tool_type": type(self.bigquery_tool).__name__ if hasattr(self, 'bigquery_tool') else 'unknown'
                    }
                )
            
            logger.error(f"Real BigQuery search failed: {e}")
            return ToolResult(
                success=False,
                data=[],
                metadata={
                    "method": "search",
                    "query": query,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "location": self.location
                }
            )
    
    async def list_datasets(self) -> ToolResult:
        """List available datasets using the real tool"""
        
        if self.tracer:
            trace_event(
                "START",
                "real_bigquery_debug_tool",
                "list_datasets",
                "Listing datasets with REAL BigQuery tool",
                "INFO",
                {
                    "operation": "list_datasets",
                    "project_id": self.project_id,
                    "location": self.location,
                    "tool_type": type(self.bigquery_tool).__name__
                }
            )
        
        try:
            start_time = datetime.now()
            
            # Try to call list_datasets on the real tool
            result = None
            
            if hasattr(self.bigquery_tool, 'run_async'):
                result = await self.bigquery_tool.run_async({"method": "list_datasets", "params": {}})
            elif hasattr(self.bigquery_tool, 'list_datasets'):
                result = await self.bigquery_tool.list_datasets()
            elif hasattr(self.bigquery_tool, 'execute'):
                result = await self.bigquery_tool.execute("list_datasets", {})
            else:
                raise AttributeError("Don't know how to call list_datasets on the real tool")
            
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            if self.tracer:
                trace_event(
                    "SUCCESS",
                    "real_bigquery_debug_tool",
                    "list_datasets",
                    "Successfully listed datasets with real tool",
                    "INFO",
                    {
                        "execution_time_ms": execution_time_ms,
                        "result_type": type(result).__name__,
                        "project_id": self.project_id,
                        "location": self.location
                    }
                )
            
            # Convert to ToolResult
            if isinstance(result, dict):
                return ToolResult(
                    success=result.get('success', True),
                    data=result.get('datasets', result.get('data', result)),
                    metadata={
                        "method": "list_datasets",
                        "execution_time_ms": execution_time_ms,
                        "total_datasets": result.get('total_datasets', 0),
                        "project_id": self.project_id,
                        "location": self.location,
                        "tool_type": type(self.bigquery_tool).__name__
                    }
                )
            else:
                return ToolResult(
                    success=True,
                    data=result,
                    metadata={
                        "method": "list_datasets",
                        "execution_time_ms": execution_time_ms,
                        "project_id": self.project_id,
                        "location": self.location,
                        "tool_type": type(self.bigquery_tool).__name__
                    }
                )
                
        except Exception as e:
            if self.tracer:
                trace_event(
                    "ERROR",
                    "real_bigquery_debug_tool",
                    "list_datasets",
                    f"Failed to list datasets: {e}",
                    "ERROR",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "project_id": self.project_id,
                        "location": self.location
                    }
                )
            
            logger.error(f"Failed to list datasets: {e}")
            return ToolResult(
                success=False,
                data=[],
                metadata={
                    "method": "list_datasets",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def health_check(self) -> ToolResult:
        """Perform a health check using the real tool"""
        
        if self.tracer:
            trace_event(
                "START",
                "real_bigquery_debug_tool",
                "health_check",
                "Performing health check with REAL BigQuery tool",
                "INFO",
                {
                    "operation": "health_check",
                    "project_id": self.project_id,
                    "location": self.location,
                    "tool_type": type(self.bigquery_tool).__name__
                }
            )
        
        try:
            # Try to perform a simple operation to check health
            result = await self.list_datasets()
            
            is_healthy = result.success
            
            if self.tracer:
                trace_event(
                    "SUCCESS" if is_healthy else "ERROR",
                    "real_bigquery_debug_tool",
                    "health_check",
                    f"Health check {'passed' if is_healthy else 'failed'}",
                    "INFO" if is_healthy else "ERROR",
                    {
                        "health_status": "healthy" if is_healthy else "unhealthy",
                        "project_id": self.project_id,
                        "location": self.location,
                        "tool_available": hasattr(self, 'bigquery_tool')
                    }
                )
            
            return ToolResult(
                success=is_healthy,
                data={
                    "status": "healthy" if is_healthy else "unhealthy",
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "location": self.location,
                    "tool_type": type(self.bigquery_tool).__name__,
                    "langswarm_available": LANGSWARM_AVAILABLE,
                    "checks": {
                        "tool_created": hasattr(self, 'bigquery_tool'),
                        "project_id_configured": bool(self.project_id),
                        "dataset_id_configured": bool(self.dataset_id),
                        "location_configured": bool(self.location),
                        "list_datasets_works": result.success
                    }
                },
                metadata={
                    "method": "health_check",
                    "health_status": "healthy" if is_healthy else "unhealthy",
                    "error": result.metadata.get('error') if not result.success else None
                }
            )
            
        except Exception as e:
            if self.tracer:
                trace_event(
                    "ERROR",
                    "real_bigquery_debug_tool",
                    "health_check",
                    f"Health check failed: {e}",
                    "ERROR",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "project_id": self.project_id,
                        "location": self.location
                    }
                )
            
            logger.error(f"Health check failed: {e}")
            return ToolResult(
                success=False,
                data={"status": "unhealthy"},
                metadata={
                    "method": "health_check",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )


def create_bigquery_search_tool(config: Optional[Dict[str, Any]] = None) -> RealBigQueryDebugTool:
    """Factory function to create a REAL BigQuery debug tool"""
    return RealBigQueryDebugTool(config)