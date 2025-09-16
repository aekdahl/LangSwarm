# mcp/tools/bigquery_vector_search/main_simplified.py

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.mcp.tools._error_standards import create_error_response, create_parameter_error, create_authentication_error, create_connection_error, ErrorTypes

# Python 3.11+ compatibility
try:
    from langswarm.core.utils.python_compat import (
        OpenAIClientFactory, IS_PYTHON_311_PLUS
    )
except ImportError:
    IS_PYTHON_311_PLUS = sys.version_info >= (3, 11)
    OpenAIClientFactory = None

# Optional BigQuery support
try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound as BQNotFound
    from ._bigquery_utils import BigQueryManager, EmbeddingHelper, QueryBuilder
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    BigQueryManager = None

# Optional OpenAI support for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# === Configuration ===
DEFAULT_CONFIG = {
    "project_id": None,  # Will use GOOGLE_CLOUD_PROJECT env var
    "dataset_id": "vector_search",
    "table_name": "embeddings",
    "embedding_model": "text-embedding-3-small",
    "default_similarity_threshold": 0.7,  # Conservative default
    "max_results": 10                     # Reasonable default
}

# === Schemas ===
class SimilaritySearchInput(BaseModel):
    query: str
    query_embedding: Optional[List[float]] = None
    limit: Optional[int] = None  # Will be set from config if not provided
    similarity_threshold: Optional[float] = None  # Will be set from config if not provided
    dataset_id: Optional[str] = None
    table_name: Optional[str] = None

class SimilaritySearchOutput(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    dataset: str
    error: Optional[str] = None

class ListDatasetsInput(BaseModel):
    pattern: Optional[str] = None

class ListDatasetsOutput(BaseModel):
    success: bool
    datasets: List[Dict[str, Any]]
    total_datasets: int
    error: Optional[str] = None

class GetContentInput(BaseModel):
    document_id: str
    dataset_id: Optional[str] = None
    table_name: Optional[str] = None

class GetContentOutput(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DatasetInfoInput(BaseModel):
    dataset_id: str
    table_name: str

class DatasetInfoOutput(BaseModel):
    success: bool
    dataset_id: str
    table_name: str
    total_rows: Optional[int] = None
    size_bytes: Optional[int] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    table_schema: Optional[List[Dict[str, str]]] = None
    sample_documents: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# === Core Business Logic ===

async def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for text using OpenAI with Python 3.11+ compatibility"""
    
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI support requires: pip install openai")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Use compatibility factory for Python 3.11+
    if OpenAIClientFactory:
        async with OpenAIClientFactory.get_async_context_manager(api_key) as client:
            response = await client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
    else:
        # Fallback for older versions
        client = openai.AsyncOpenAI(api_key=api_key)
        try:
            response = await client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        finally:
            if hasattr(client, 'close'):
                try:
                    await client.close()
                except:
                    pass

# === Unified Async Handlers ===

async def similarity_search(input_data: SimilaritySearchInput, config: dict = None) -> SimilaritySearchOutput:
    """Perform vector similarity search in BigQuery using shared utilities"""
    try:
        # Use provided config or fall back to default
        effective_config = config or DEFAULT_CONFIG
        
        # Get configuration
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = input_data.dataset_id or effective_config["dataset_id"]
        table_name = input_data.table_name or effective_config["table_name"]
        
        # Apply config defaults for optional parameters
        limit = input_data.limit if input_data.limit is not None else effective_config["max_results"]
        similarity_threshold = input_data.similarity_threshold if input_data.similarity_threshold is not None else effective_config["default_similarity_threshold"]
        
        print(f"🔧 Config source: {'tool_instance' if config else 'global_default'}")
        print(f"🔧 Config applied: limit={limit}, similarity_threshold={similarity_threshold}")
        if config:
            print(f"🔧 Full tool config: {effective_config}")
        
        # Generate embedding if not provided
        if input_data.query_embedding is None:
            logger.info(f"Generating embedding for query: {input_data.query[:100]}...")
            query_embedding = await get_embedding(input_data.query)
            logger.info(f"Embedding generated successfully, dimension: {len(query_embedding)}")
        else:
            query_embedding = input_data.query_embedding
        
        # Validate embedding
        if not EmbeddingHelper.validate_embedding(query_embedding):
            raise ValueError("Invalid embedding format")
        
        # Use BigQuery manager for search
        bq_manager = BigQueryManager(project_id)
        results = bq_manager.execute_similarity_search(
            dataset_id=dataset_id,
            table_name=table_name,
            query_embedding=query_embedding,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        
        return SimilaritySearchOutput(
            success=True,
            query=input_data.query,
            results=results,
            total_results=len(results),
            dataset=f"{dataset_id}.{table_name}"
        )
        
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return SimilaritySearchOutput(
            success=False,
            query=input_data.query,
            results=[],
            total_results=0,
            dataset=f"{dataset_id}.{table_name}",
            error=str(e)
        )

async def list_datasets(input_data: ListDatasetsInput) -> ListDatasetsOutput:
    """List available vector search datasets using shared utilities"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or "production-pingday"
        bq_manager = BigQueryManager(project_id)
        datasets = bq_manager.list_embedding_datasets(input_data.pattern)
        
        return ListDatasetsOutput(
            success=True,
            datasets=datasets,
            total_datasets=len(datasets)
        )
        
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return ListDatasetsOutput(
            success=False,
            datasets=[],
            total_datasets=0,
            error=str(e)
        )

async def get_content(input_data: GetContentInput) -> GetContentOutput:
    """Retrieve full content by document ID using shared utilities"""
    try:
        dataset_id = input_data.dataset_id or DEFAULT_CONFIG["dataset_id"]
        table_name = input_data.table_name or DEFAULT_CONFIG["table_name"]
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or "production-pingday"
        bq_manager = BigQueryManager(project_id)
        result = bq_manager.get_document_by_id(dataset_id, table_name, input_data.document_id)
        
        if not result:
            return GetContentOutput(
                success=False,
                error=f"Document not found: {input_data.document_id}"
            )
        
        return GetContentOutput(
            success=True,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Failed to get content: {e}")
        return GetContentOutput(
            success=False,
            error=str(e)
        )

async def dataset_info(input_data: DatasetInfoInput) -> DatasetInfoOutput:
    """Get detailed information about a dataset/table using shared utilities"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        bq_manager = BigQueryManager(project_id)
        
        info = bq_manager.get_table_info(input_data.dataset_id, input_data.table_name)
        
        return DatasetInfoOutput(
            success=True,
            **info
        )
        
    except Exception as e:
        logger.error(f"Failed to get dataset info: {e}")
        return DatasetInfoOutput(
            success=False,
            dataset_id=input_data.dataset_id,
            table_name=input_data.table_name,
            error=str(e)
        )

# === MCP Server ===
server = BaseMCPToolServer(
    name="bigquery_vector_search",  # Default name, will be overridden by tool identifier
    description="BigQuery vector similarity search for knowledge base queries.",
    local_mode=True
)

# Add operations
async def _similarity_search_handler(**kwargs):
    """Wrapper for similarity_search that handles keyword arguments from call_task"""
    # Convert keyword arguments to SimilaritySearchInput object
    input_data = SimilaritySearchInput(**kwargs)
    # CRITICAL FIX: Use server's tool_config if available
    config_to_use = getattr(server, 'tool_config', None)
    return await similarity_search(input_data, config=config_to_use)

server.add_task(
    name="similarity_search",
    description="Perform vector similarity search to find relevant content.",
    input_model=SimilaritySearchInput,
    output_model=SimilaritySearchOutput,
    handler=_similarity_search_handler
)

async def _get_content_handler(**kwargs):
    """Wrapper for get_content that handles keyword arguments from call_task"""
    input_data = GetContentInput(**kwargs)
    return await get_content(input_data)

async def _list_datasets_handler(**kwargs):
    """Wrapper for list_datasets that handles keyword arguments from call_task"""
    input_data = ListDatasetsInput(**kwargs)
    return await list_datasets(input_data)

async def _dataset_info_handler(**kwargs):
    """Wrapper for dataset_info that handles keyword arguments from call_task"""
    input_data = DatasetInfoInput(**kwargs)
    return await dataset_info(input_data)

server.add_task(
    name="get_content",
    description="Retrieve full document content by document ID.",
    input_model=GetContentInput,
    output_model=GetContentOutput,
    handler=_get_content_handler
)

server.add_task(
    name="list_datasets",
    description="List available vector search datasets and tables.",
    input_model=ListDatasetsInput,
    output_model=ListDatasetsOutput,
    handler=_list_datasets_handler
)

server.add_task(
    name="dataset_info",
    description="Get detailed information about a specific dataset/table.",
    input_model=DatasetInfoInput,
    output_model=DatasetInfoOutput,
    handler=_dataset_info_handler
)

# Create FastAPI app
app = server.build_app()

# === LangChain-Compatible Tool Class ===
try:
    from langswarm.synapse.tools.base import BaseTool
    
    class BigQueryVectorSearchMCPTool(BaseTool):
        """
        Simplified BigQuery Vector Search MCP tool for semantic knowledge base search.
        
        Features:
        - Vector similarity search using embeddings
        - Document retrieval by ID
        - Dataset management and inspection
        - Unified async execution model
        """
        _bypass_pydantic = True
        
        def preprocess_parameters(self, params, explicit_method=None):
            """BigQuery-specific parameter preprocessing and method detection"""
            # Handle None params gracefully
            if params is None:
                params = {}
            input_data = params
            
            # CRITICAL FIX: If explicit method is provided, use it instead of detecting
            if explicit_method and explicit_method in ["similarity_search", "list_datasets", "get_content", "dataset_info"]:
                # For explicit methods, just clean the parameters without changing the method
                if "input" in params:
                    input_data = params["input"]
                    if isinstance(input_data, str):
                        try:
                            import json
                            input_data = json.loads(input_data)
                        except:
                            input_data = {}
                    elif not isinstance(input_data, dict):
                        input_data = {}
                # Check if parameters are nested under method names
                elif explicit_method in params:
                    input_data = params[explicit_method]
                
                # VALIDATION: Ensure similarity_search has query parameter
                # BUT don't change the method - let BigQuery validation handle the error
                if explicit_method == "similarity_search":
                    if not input_data or "query" not in input_data or not input_data.get("query"):
                        # Agent called similarity_search without proper query - return error in params
                        # Don't change method to list_datasets - that's misleading!
                        return explicit_method, {"error": "similarity_search requires 'query' parameter"}
                
                return explicit_method, input_data if input_data else {}
            
            # Original logic for when no explicit method is provided
            # Check if it's wrapped in an "input" parameter
            if "input" in params:
                # Parse the nested input JSON
                input_data = params["input"]
                if isinstance(input_data, str):
                    try:
                        import json
                        input_data = json.loads(input_data)
                    except:
                        input_data = {}
                elif not isinstance(input_data, dict):
                    input_data = {}
            
            # Check for nested MCP structure (CRITICAL FIX for agent nesting)
            elif "mcp" in params and isinstance(params["mcp"], dict):
                # Agent generated nested MCP call - extract the inner method and params
                nested_mcp = params["mcp"]
                if "method" in nested_mcp and nested_mcp["method"] in ["similarity_search", "list_datasets", "get_content", "dataset_info"]:
                    return nested_mcp["method"], nested_mcp.get("params", {})
            
            # Check if parameters are nested under method names (CRITICAL FIX)
            elif "similarity_search" in params:
                input_data = params["similarity_search"]
            elif "get_content" in params:
                input_data = params["get_content"] 
            elif "list_datasets" in params:
                input_data = params["list_datasets"]
            elif "dataset_info" in params:
                input_data = params["dataset_info"]
            
            # Detect method based on parameter patterns
            if "query" in input_data:
                return "similarity_search", input_data
            elif "document_id" in input_data:
                return "get_content", input_data
            elif "pattern" in input_data or ("pattern" in params and params != input_data):
                return "list_datasets", input_data
            elif "dataset_id" in input_data and "table_name" in input_data:
                return "dataset_info", input_data
            else:
                # IMPROVED FALLBACK: For empty params, default to list_datasets (safer than similarity_search)
                return "list_datasets", input_data if input_data else {}
        
        def handle_intent(self, intent: str, context: Optional[str] = None) -> Any:
            """
            Handle intent-based calls directly without requiring a workflow.
            This provides a fallback when no workflow is available.
            
            Args:
                intent: Natural language intent
                context: Optional context information
                
            Returns:
                Result of the intent execution
            """
            try:
                # Use built-in logging instead of self.logger
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Handling intent directly: '{intent}' with context: '{context}'")
                
                # Simple intent-to-method mapping for BigQuery
                intent_lower = intent.lower()
                if "search" in intent_lower or "find" in intent_lower:
                    method = "similarity_search"
                    params = {"query": intent}
                elif "list" in intent_lower or "show" in intent_lower:
                    method = "list_datasets" 
                    params = {}
                elif "get" in intent_lower or "retrieve" in intent_lower:
                    method = "get_content"
                    params = {"document_id": context if context else "unknown"}
                else:
                    method = "similarity_search"  # Default fallback
                    params = {"query": intent}
                
                logger.info(f"Intent mapped to: {method} with params {params}")
                
                # Execute the method directly using async functions
                import asyncio
                
                if method == "similarity_search":
                    # Convert params to proper input model
                    search_input = SimilaritySearchInput(**params)
                    return asyncio.run(similarity_search(search_input))
                elif method == "list_datasets":
                    # Convert params to proper input model
                    list_input = ListDatasetsInput(**params)
                    return asyncio.run(list_datasets(list_input))
                elif method == "get_content":
                    # Convert params to proper input model
                    content_input = GetContentInput(**params)
                    return asyncio.run(get_content(content_input))
                elif method == "get_embedding":
                    # Direct call to get_embedding
                    text = params.get("text", "")
                    model = params.get("model", "text-embedding-3-small")
                    return asyncio.run(get_embedding(text, model))
                else:
                    raise ValueError(f"Unknown method: {method}")
                
            except Exception as e:
                logger.error(f"Intent handling failed: {e}")
                raise

        def __init__(self, identifier: str, **kwargs):
            # Extract template-based values with fallbacks (like filesystem tool pattern)
            description = kwargs.pop('description', "Search company knowledge base using BigQuery vector similarity")
            instruction = kwargs.pop('instruction', """Use this tool to perform semantic searches on your knowledge base stored in BigQuery.

IMPORTANT PARAMETERS:
- Use 'query' (NOT 'keyword') for search text
- Use 'limit' for number of results (default: 10) 
- Use 'similarity_threshold' for relevance (default: 0.7)

Example usage:
{
  "tool": "bigquery_vector_search",
  "method": "similarity_search", 
  "params": {
    "query": "refund policy for enterprise customers",
    "limit": 5,
    "similarity_threshold": 0.8
  }
}""")
            brief = kwargs.pop('brief', "BigQuery vector search for semantic knowledge retrieval")
            
            super().__init__(
                name="BigQuery Vector Search",
                description=description,
                instruction=instruction,
                identifier=identifier,
                brief=brief,
                **kwargs
            )
            
            # Update server name to match tool identifier for proper registration
            server.name = identifier
            # Re-register with the correct name
            if server.local_mode:
                server._register_globally()
            
            object.__setattr__(self, 'server', server)
            
            # Start with default config
            config = DEFAULT_CONFIG.copy()
            
            # Override with any provided configuration parameters
            # Support both direct parameters and config dict
            if 'config' in kwargs:
                config.update(kwargs['config'])
                
            # Support direct parameter passing
            config_params = {
                'project_id', 'dataset_id', 'table_name', 'embedding_model',
                'default_similarity_threshold', 'max_results', 'similarity_threshold'
            }
            for param in config_params:
                if param in kwargs:
                    config[param] = kwargs[param]
                    
            # Handle similarity_threshold alias
            if 'similarity_threshold' in kwargs:
                config['default_similarity_threshold'] = kwargs['similarity_threshold']
            
            object.__setattr__(self, 'default_config', config)
            
            # CRITICAL FIX: Pass the tool's config to the server so it can use it
            # The server is what actually handles the MCP calls, so it needs the config
            object.__setattr__(server, 'tool_config', config)
            
            # Debug: Log the final configuration
            print(f"🔧 BigQuery Tool Constructor kwargs: {kwargs}")
            print(f"🔧 BigQuery Tool Final Config: {config}")
        
        async def run_async(self, input_data=None):
            """Unified async execution method"""
            try:
                # Parse input and determine method
                if isinstance(input_data, str):
                    # Simple string query
                    method = "similarity_search"
                    params = {"query": input_data}
                elif isinstance(input_data, dict):
                    # Check for parameter naming issues first
                    if "keyword" in input_data and "query" not in input_data:
                        return create_parameter_error(
                            "keyword", "string (use 'query' parameter)", input_data.get("keyword"),
                            "bigquery_vector_search", "similarity_search"
                        )
                    if "search" in input_data and "query" not in input_data:
                        return create_parameter_error(
                            "search", "string (use 'query' parameter)", input_data.get("search"),
                            "bigquery_vector_search", "similarity_search"
                        )
                    if "text" in input_data and "query" not in input_data:
                        return create_parameter_error(
                            "text", "string (use 'query' parameter)", input_data.get("text"),
                            "bigquery_vector_search", "similarity_search"
                        )
                    
                    # Structured input
                    if "method" in input_data and "params" in input_data:
                        method = input_data["method"]
                        params = input_data["params"]
                    elif "query" in input_data:
                        method = "similarity_search"
                        params = input_data
                    elif "document_id" in input_data:
                        method = "get_content"
                        params = input_data
                    else:
                        return create_error_response(
                            "Cannot determine method from input",
                            ErrorTypes.PARAMETER_VALIDATION,
                            "bigquery_vector_search"
                        )
                else:
                    return create_error_response(
                        f"Unsupported input type: {type(input_data)}",
                        ErrorTypes.PARAMETER_VALIDATION,
                        "bigquery_vector_search"
                    )
                
                # Route to appropriate handler
                if method == "similarity_search":
                    input_obj = SimilaritySearchInput(**params)
                    # Use server's tool_config if available, fallback to self.default_config
                    server_config = getattr(self.server, 'tool_config', None) if hasattr(self, 'server') else None
                    config_to_use = server_config or self.default_config
                    result = await similarity_search(input_obj, config=config_to_use)
                elif method == "get_content":
                    input_obj = GetContentInput(**params)
                    result = await get_content(input_obj)
                elif method == "list_datasets":
                    input_obj = ListDatasetsInput(**params)
                    result = await list_datasets(input_obj)
                elif method == "dataset_info":
                    input_obj = DatasetInfoInput(**params)
                    result = await dataset_info(input_obj)
                else:
                    available_methods = ["similarity_search", "get_content", "list_datasets", "dataset_info"]
                    return create_error_response(
                        f"Unknown method: {method}. Available: {available_methods}",
                        ErrorTypes.PARAMETER_VALIDATION,
                        "bigquery_vector_search"
                    )
                
                return result.dict()
                
            except Exception as e:
                logger.error(f"BigQuery tool execution failed: {e}")
                return create_error_response(
                    str(e), ErrorTypes.GENERAL, "bigquery_vector_search"
                )
        
        def run(self, input_data=None):
            """Synchronous wrapper for async execution"""
            import asyncio
            import threading
            
            # Handle different event loop scenarios
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, need to run in thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.run_async(input_data))
                        return future.result()
                else:
                    # No running loop, can use asyncio.run directly
                    return asyncio.run(self.run_async(input_data))
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(self.run_async(input_data))

except ImportError:
    BigQueryVectorSearchMCPTool = None
    logger.warning("BigQuery Vector Search MCP tool class not available - BaseTool import failed")

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
    else:
        uvicorn.run("langswarm.mcp.tools.bigquery_vector_search.main_simplified:app", host="0.0.0.0", port=4021, reload=True)
