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
from langswarm.tools.mcp._error_standards import create_error_response, create_parameter_error, create_authentication_error, create_connection_error, ErrorTypes

# Python 3.11+ compatibility (V1/V2)
try:
    from langswarm.core.utils.python_compat import (
        OpenAIClientFactory, IS_PYTHON_311_PLUS
    )
except ImportError:
    try:
        from langswarm.v1.core.utils.python_compat import (
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
    "default_similarity_threshold": 0.01,  # Use more permissive default
    "max_results": 5,                      # Match working configuration
    "location": "europe-west1"             # Default to europe-west1 location, could also be EU
}

# === Schemas ===
class SimilaritySearchInput(BaseModel):
    query: str
    query_embedding: Optional[List[float]] = None
    limit: Optional[int] = None  # Will be set from config if not provided
    similarity_threshold: Optional[float] = None  # Will be set from config if not provided
    dataset_id: Optional[str] = None
    table_name: Optional[str] = None
    
    class Config:
        repr = False  # Disable automatic repr to prevent circular references
    
    def __repr__(self) -> str:
        """Safe repr that never causes circular references"""
        try:
            return f"SimilaritySearchInput(query='{self.query[:30]}...')"
        except Exception:
            return "SimilaritySearchInput(repr_error)"

class SimilaritySearchOutput(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    dataset: str
    error: Optional[str] = None
    
    class Config:
        repr = False  # Disable automatic repr to prevent circular references
    
    def __repr__(self) -> str:
        """Safe repr that never causes circular references"""
        try:
            success = getattr(self, 'success', 'unknown')
            total = getattr(self, 'total_results', 'unknown')
            return f"SimilaritySearchOutput(success={success}, total_results={total})"
        except Exception:
            return "SimilaritySearchOutput(repr_error)"

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
    
    # 🎯 V2 TRACING: Internal agent activity for embedding generation
    try:
        # Try V2 tracing first
        from langswarm.observability.trace_context import TraceContext
        from langswarm.observability.trace_logger import TraceLogger
        
        # Simple V2 tracing implementation
        logger.info(f"🎯 INTERNAL_LLM_CALL | get_embedding | model={model} | text_length={len(text)} | text_preview={text[:50]}...")
        
        return await _perform_embedding_call(text, model)
            
    except ImportError:
        # Fallback to V1 tracing
        try:
            # Try V2 path first
            from langswarm.core.debug import get_debug_tracer
            tracer = get_debug_tracer()
            if tracer and hasattr(tracer, 'enabled') and tracer.enabled:
                logger.info(f"🎯 V1_INTERNAL_LLM_CALL | get_embedding | model={model} | text_length={len(text)}")
            return await _perform_embedding_call(text, model)
        except ImportError:
            try:
                # Try V1 path
                from langswarm.v1.core.debug import get_debug_tracer
                tracer = get_debug_tracer()
                if tracer and hasattr(tracer, 'enabled') and tracer.enabled:
                    logger.info(f"🎯 V1_INTERNAL_LLM_CALL | get_embedding | model={model} | text_length={len(text)}")
                return await _perform_embedding_call(text, model)
            except ImportError:
                # No tracing available, proceed without tracing
                return await _perform_embedding_call(text, model)

async def _perform_embedding_call(text: str, model: str) -> List[float]:
    """Perform the actual embedding API call"""
    
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
            # Safe config printing to avoid circular reference issues
            config_keys = list(effective_config.keys()) if isinstance(effective_config, dict) else "non-dict"
            print(f"🔧 Tool config keys: {config_keys}")
        
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
        location = effective_config.get('location', DEFAULT_CONFIG['location'])
        bq_manager = BigQueryManager(project_id, location=location)
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
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required for BigQuery operations")
        bq_manager = BigQueryManager(project_id, location=DEFAULT_CONFIG['location'])
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
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required for BigQuery operations")
        bq_manager = BigQueryManager(project_id, location=DEFAULT_CONFIG['location'])
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
        bq_manager = BigQueryManager(project_id, location=DEFAULT_CONFIG['location'])
        
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

# Add tool-specific guidance for parameter validation errors
def _get_tool_specific_guidance(task_name, error_details):
    """Provide BigQuery-specific guidance for parameter validation errors"""
    field_name = error_details['field']
    error_type = error_details['type']
    
    if task_name == 'similarity_search':
        if field_name == 'query' and error_type == 'missing':
            return "Required parameter 'query' is missing. Please provide the text you want to search for. Example: {\"query\": \"Pingday monitoring\", \"limit\": 5}"
        elif field_name == 'query' and 'type_error' in error_type:
            return "Parameter 'query' must be a string. Please provide your search text as a string. Example: {\"query\": \"your search text\"}"
        elif field_name == 'limit' and ('type_error' in error_type or 'int_parsing' in error_type):
            return "Parameter 'limit' must be an integer. Please specify how many results you want (e.g., 5, 10). Example: {\"query\": \"search text\", \"limit\": 5}"
        elif field_name == 'similarity_threshold' and 'value_error' in error_type:
            return "Parameter 'similarity_threshold' must be a number between 0 and 1. Example: {\"query\": \"search text\", \"similarity_threshold\": 0.7}"
    
    elif task_name == 'get_content':
        if field_name == 'document_id' and error_type == 'missing':
            return "Required parameter 'document_id' is missing. Please provide the ID of the document you want to retrieve. Example: {\"document_id\": \"abc123_0\"}"
        elif field_name == 'document_id' and 'type_error' in error_type:
            return "Parameter 'document_id' must be a string. Example: {\"document_id\": \"your_document_id\"}"
    
    elif task_name == 'get_embedding':
        if field_name == 'text' and error_type == 'missing':
            return "Required parameter 'text' is missing. Please provide the text you want to embed. Example: {\"text\": \"your text to embed\"}"
        elif field_name == 'text' and 'type_error' in error_type:
            return "Parameter 'text' must be a string. Example: {\"text\": \"your text here\"}"
    
    elif task_name == 'list_datasets':
        # list_datasets has no required parameters, so provide general guidance
        return "This method lists available datasets and doesn't require any parameters. You can call it with an empty parameters object: {}"
    
    elif task_name == 'dataset_info':
        if field_name == 'dataset_id' and error_type == 'missing':
            return "Parameter 'dataset_id' is recommended for getting specific dataset information. Example: {\"dataset_id\": \"vector_search\"}"
    
    # Fallback for unknown patterns
    return f"Please check the parameter format for {task_name}. Refer to the tool documentation for correct parameter usage."

# Attach the guidance method to the server
server._get_tool_specific_guidance = _get_tool_specific_guidance

# Note: Enhanced error handling and guidance now provides actionable feedback
# that helps agents correct their parameter usage and retry successfully

# Add operations
async def _similarity_search_handler(**kwargs):
    """Wrapper for similarity_search that handles keyword arguments from call_task"""
    print(f"🔍 BigQuery similarity_search_handler called with kwargs: {list(kwargs.keys())}")
    
    # Convert keyword arguments to SimilaritySearchInput object
    try:
        input_data = SimilaritySearchInput(**kwargs)
        print(f"🔍 BigQuery input validation passed: query='{input_data.query[:50]}...', limit={input_data.limit}")
    except Exception as e:
        print(f"❌ BigQuery input validation failed: {e}")
        raise
    
    # CRITICAL FIX: Use server's tool_config if available
    config_to_use = getattr(server, 'tool_config', None)
    print(f"🔍 BigQuery config_to_use: {config_to_use is not None}")
    
    result = await similarity_search(input_data, config=config_to_use)
    print(f"🔍 BigQuery similarity_search completed: {len(result.results) if hasattr(result, 'results') else 'no results'} items")
    return result

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
    from langswarm.tools.base import BaseTool
    from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin
    
    class BigQueryVectorSearchMCPTool(MCPProtocolMixin, BaseTool):
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
        
        def __init__(self, identifier: str, **kwargs):
            # STEP 1: Build config first 
            config = DEFAULT_CONFIG.copy()
            
            # Handle settings dictionary  
            if 'settings' in kwargs and isinstance(kwargs['settings'], dict):
                config.update(kwargs['settings'])
                
            # Support nested config (deprecated but backward compatible)
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
            
            # NOTE: User config is properly applied to actual BigQuery calls
            # Template examples show generic defaults, but tool uses user's values
            
            # Load ONLY the Instructions section from template.md (not the full file)
            try:
                from langswarm.tools.mcp.template_loader import get_cached_tool_template
                import os
                tool_directory = os.path.dirname(__file__)
                template_values = get_cached_tool_template(tool_directory, strict_mode=True)
                
                # Use actual template content as designed
                description = kwargs.pop('description', template_values.get('description', "Advanced semantic search tool using AI embeddings"))
                instruction = kwargs.pop('instruction', template_values.get('instruction', "Use BigQuery vector search for semantic information retrieval"))
                brief = kwargs.pop('brief', template_values.get('brief', "Semantic search tool"))
                
                print(f"🔧 BigQuery tool loaded Instructions section: {len(instruction)} chars (was 9,333 full file)")
                
            except Exception as e:
                # EXPLICIT ERROR - don't hide template loading failures
                print(f"❌ CRITICAL: Failed to load template.md for BigQuery tool: {e}")
                print(f"❌ This could indicate missing template.md or parsing errors")
                # Still provide fallback but make the error visible
                description = kwargs.pop('description', "Search company knowledge base using BigQuery vector similarity")
                instruction = kwargs.pop('instruction', "Use this tool to perform semantic searches on your knowledge base stored in BigQuery.")
                brief = kwargs.pop('brief', "BigQuery vector search for semantic knowledge retrieval")
            
            super().__init__(
                name="BigQuery Vector Search",
                description=description,
                tool_id=identifier,
                config=config,  # Pass config to BaseTool
                **kwargs
            )
            
            # Update server name to match tool identifier for proper registration
            server.name = identifier
            # Re-register with the correct name
            if server.local_mode:
                server._register_globally()
            
            object.__setattr__(self, 'server', server)
            object.__setattr__(self, 'default_config', config)
            
            # CRITICAL FIX: Pass the tool's config to the server so it can use it
            # The server is what actually handles the MCP calls, so it needs the config
            # Create a safe copy to avoid circular references
            config_copy = config.copy() if isinstance(config, dict) else dict(config) if hasattr(config, 'items') else config
            object.__setattr__(server, 'tool_config', config_copy)
            
            # Debug: Log the final configuration (safe printing to avoid circular refs)
            kwargs_keys = list(kwargs.keys()) if isinstance(kwargs, dict) else "non-dict"
            config_keys = list(config.keys()) if isinstance(config, dict) else "non-dict"
            print(f"🔧 BigQuery Tool Constructor kwargs keys: {kwargs_keys}")
            print(f"🔧 BigQuery Tool Final Config keys: {config_keys}")
        
        async def run_async(self, input_data=None):
            """Unified async execution method - NO TRY BLOCK"""
            # Parse input and determine method
            if isinstance(input_data, str):
                # Simple string query - default to intent processing for intelligent routing
                return await self._handle_intent_call({
                    "intent": input_data,
                    "context": "user query"
                })
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
                    # Check for MCP structure first (from user-facing agents)
                    if "mcp" in input_data and isinstance(input_data["mcp"], dict):
                        mcp_data = input_data["mcp"]
                        if "method" in mcp_data and "params" in mcp_data:
                            method = mcp_data["method"]
                            params = mcp_data["params"]
                            print(f"🔍 Extracted from MCP structure: method={method}, params={params}")
                        else:
                            # MCP structure but incomplete, treat as ambiguous
                            return await self._handle_intent_call({
                                "intent": input_data.get("response", "Process this request"),
                                "context": f"incomplete MCP structure: {mcp_data}",
                            })
                    elif "method" in input_data and "params" in input_data:
                        method = input_data["method"]
                        params = input_data["params"]
                    elif "query" in input_data:
                        # Query parameter - could be search intent, let intent processing decide
                        return await self._handle_intent_call({
                            "intent": f"Search for: {input_data['query']}",
                            "context": "query parameter provided",
                            **{k: v for k, v in input_data.items() if k != 'query'}  # Pass other params as context
                        })
                    elif "document_id" in input_data:
                        method = "get_content"
                        params = input_data
                    else:
                        # Ambiguous input - let intent processing handle it intelligently
                        return await self._handle_intent_call({
                            "intent": "Process this request based on the provided parameters",
                            "context": f"ambiguous input with keys: {list(input_data.keys())}",
                            **input_data  # Pass all params as context
                        })
            else:
                return create_error_response(
                    f"Unsupported input type: {type(input_data)}",
                    ErrorTypes.PARAMETER_VALIDATION,
                    "bigquery_vector_search"
                )
            
            # Route to appropriate handler - NO TRY BLOCK
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
        
        async def _handle_intent_call(self, input_data):
            """Handle intent-based calling using LangSwarm workflow system"""
            intent = input_data.get("intent", "")
            context = input_data.get("context", "")
            
            # FORCE PRINT to ensure we see this
            print(f"🧠 LangSwarm Workflow: Processing intent '{intent}' with context '{context}'")
            logger.info(f"🧠 LangSwarm Workflow: Processing intent '{intent}' with context '{context}'")
            
            # Import LangSwarm workflow system (V1/V2 compatibility)
            try:
                from langswarm.core.config import LangSwarmConfigLoader
            except ImportError:
                from langswarm.v1.core.config import LangSwarmConfigLoader
            import os
            from pathlib import Path
            
            # Get tool directory and workflow config
            tool_directory = Path(__file__).parent
            workflows_config = tool_directory / "workflows.yaml"
            agents_config = tool_directory / "agents.yaml"
            
            if not workflows_config.exists():
                logger.error(f"No workflows.yaml found in {tool_directory}")
                raise FileNotFoundError("Tool workflow configuration not found")
            
            if not agents_config.exists():
                logger.error(f"No agents.yaml found in {tool_directory}")
                raise FileNotFoundError("Tool agents configuration not found")
                
            # Create temporary combined config for LangSwarm
            import tempfile
            import yaml
            
            # Load workflow and agent configs - NO TRY BLOCK
            with open(workflows_config, 'r') as f:
                workflow_data = yaml.safe_load(f)
            with open(agents_config, 'r') as f:
                agents_data = yaml.safe_load(f)
                
                # Create combined config - properly merge without overwriting
                combined_config = {}
                if workflow_data:
                    combined_config.update(workflow_data)
                if agents_data:
                    # Merge agents_data without overwriting existing keys
                    for key, value in agents_data.items():
                        if key in combined_config:
                            # If key exists, merge the values if they're both dicts or lists
                            if isinstance(combined_config[key], dict) and isinstance(value, dict):
                                combined_config[key].update(value)
                            elif isinstance(combined_config[key], list) and isinstance(value, list):
                                combined_config[key].extend(value)
                            else:
                                # For other types, keep the original value from workflow_data
                                print(f"🔍 DEBUG: Key '{key}' conflict - keeping workflow_data value")
                        else:
                            combined_config[key] = value
                
                # DEBUG: Log the combined config structure
                print(f"🔍 DEBUG: Workflow data keys: {list(workflow_data.keys()) if workflow_data else 'None'}")
                print(f"🔍 DEBUG: Agents data keys: {list(agents_data.keys()) if agents_data else 'None'}")
                print(f"🔍 DEBUG: Combined config keys: {list(combined_config.keys())}")
                logger.info(f"🔍 DEBUG: Workflow data keys: {list(workflow_data.keys()) if workflow_data else 'None'}")
                logger.info(f"🔍 DEBUG: Agents data keys: {list(agents_data.keys()) if agents_data else 'None'}")
                logger.info(f"🔍 DEBUG: Combined config keys: {list(combined_config.keys())}")
                
                if 'workflows' in combined_config:
                    workflows_section = combined_config['workflows']
                    print(f"🔍 DEBUG: Workflows section type: {type(workflows_section)}")
                    logger.info(f"🔍 DEBUG: Workflows section type: {type(workflows_section)}")
                    if isinstance(workflows_section, dict):
                        print(f"🔍 DEBUG: Workflows dict keys: {list(workflows_section.keys())}")
                        logger.info(f"🔍 DEBUG: Workflows dict keys: {list(workflows_section.keys())}")
                        if 'main_workflow' in workflows_section:
                            main_wf = workflows_section['main_workflow']
                            print(f"🔍 DEBUG: main_workflow type: {type(main_wf)}")
                            logger.info(f"🔍 DEBUG: main_workflow type: {type(main_wf)}")
                            if isinstance(main_wf, list) and len(main_wf) > 0:
                                print(f"🔍 DEBUG: First workflow ID: {main_wf[0].get('id', 'NO_ID')}")
                                logger.info(f"🔍 DEBUG: First workflow ID: {main_wf[0].get('id', 'NO_ID')}")
                        else:
                            print(f"🔍 DEBUG: No 'main_workflow' key found in workflows section")
                    else:
                        print(f"🔍 DEBUG: Workflows section is not a dict: {workflows_section}")
                else:
                    print(f"🔍 DEBUG: No 'workflows' key found in combined config")
                
                # Create temporary config file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                    yaml.dump(combined_config, temp_file)
                    temp_config_path = temp_file.name
                    logger.info(f"🔍 DEBUG: Temporary config file created: {temp_config_path}")
                
                # DEBUG: Read and log the temporary config file content - NO TRY BLOCK
                with open(temp_config_path, 'r') as debug_file:
                    temp_config_content = debug_file.read()
                    print(f"🔍 DEBUG: Temporary config file content (first 1000 chars):\n{temp_config_content[:1000]}")
                    logger.info(f"🔍 DEBUG: Temporary config file content (first 1000 chars):\n{temp_config_content[:1000]}")
                    
                    # Also check if 'workflows:' appears anywhere in the file
                    if 'workflows:' in temp_config_content:
                        print(f"🔍 DEBUG: 'workflows:' found in temp config file")
                    else:
                        print(f"🔍 DEBUG: 'workflows:' NOT found in temp config file")
                        print(f"🔍 DEBUG: File length: {len(temp_config_content)} chars")
                
                # Initialize LangSwarm config loader - NO TRY BLOCK
                print(f"🔍 DEBUG: About to initialize LangSwarmConfigLoader with: {temp_config_path}")
                loader = LangSwarmConfigLoader(temp_config_path)
                print(f"🔍 DEBUG: LangSwarmConfigLoader initialized successfully")
                
                # DEBUG: Check what workflows are available after loading
                print(f"🔍 DEBUG: Loader workflows type: {type(loader.workflows)}")
                logger.info(f"🔍 DEBUG: Loader workflows type: {type(loader.workflows)}")
                if hasattr(loader, 'workflows') and loader.workflows:
                    if isinstance(loader.workflows, dict):
                        print(f"🔍 DEBUG: Available workflow keys: {list(loader.workflows.keys())}")
                        logger.info(f"🔍 DEBUG: Available workflow keys: {list(loader.workflows.keys())}")
                        # Check if main_workflow exists and what's in it
                        if 'main_workflow' in loader.workflows:
                            main_wf = loader.workflows['main_workflow']
                            print(f"🔍 DEBUG: Loader main_workflow type: {type(main_wf)}")
                            if isinstance(main_wf, list) and len(main_wf) > 0:
                                print(f"🔍 DEBUG: Loader first workflow ID: {main_wf[0].get('id', 'NO_ID')}")
                    else:
                        print(f"🔍 DEBUG: Loader workflows is not a dict: {loader.workflows}")
                        logger.info(f"🔍 DEBUG: Loader workflows is not a dict: {loader.workflows}")
                else:
                    print(f"🔍 DEBUG: Loader has no workflows attribute or it's empty")
                    logger.info(f"🔍 DEBUG: Loader has no workflows attribute or it's empty")
                
                # CRITICAL: Execute workflow - NO TRY BLOCK TO REVEAL TRUE ERROR
                print(f"🔍 DEBUG: About to execute workflow 'bigquery_search_workflow'")
                result = await loader.run_workflow_async(
                    workflow_id="bigquery_search_workflow",
                    user_input=intent,
                    user_query=intent,
                    context=context
                )
                
                logger.info(f"🎯 LangSwarm Workflow Result: {result}")
                
                # Clean up temporary config file
                os.unlink(temp_config_path)
                
                # Return the workflow result
                return result
        
        # V2 Direct Method Calls - Expose operations as class methods
        async def similarity_search(self, query: str, limit: int = 10, similarity_threshold: float = 0.3, **kwargs):
            """
            Perform vector similarity search in BigQuery.
            
            Args:
                query: Search query text
                limit: Maximum number of results to return
                similarity_threshold: Minimum similarity score (0-1)
                
            Returns:
                Search results with similar documents
            """
            input_data = SimilaritySearchInput(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            result = await similarity_search(input_data, self.default_config)
            return result.dict() if hasattr(result, 'dict') else result
        
        async def get_content(self, document_id: str, **kwargs):
            """
            Retrieve full content by document ID.
            
            Args:
                document_id: Unique document identifier
                
            Returns:
                Document content and metadata
            """
            input_data = GetContentInput(document_id=document_id)
            result = await get_content(input_data)
            return result.dict() if hasattr(result, 'dict') else result
        
        async def list_datasets(self, pattern: str = None, **kwargs):
            """
            List available vector search datasets.
            
            Args:
                pattern: Optional pattern to filter datasets
                
            Returns:
                List of available datasets
            """
            input_data = ListDatasetsInput(pattern=pattern)
            result = await list_datasets(input_data)
            return result.dict() if hasattr(result, 'dict') else result
        
        async def dataset_info(self, dataset_id: str, table_name: str, **kwargs):
            """
            Get detailed information about a dataset/table.
            
            Args:
                dataset_id: BigQuery dataset ID
                table_name: Table name within the dataset
                
            Returns:
                Dataset schema and statistics
            """
            input_data = DatasetInfoInput(
                dataset_id=dataset_id,
                table_name=table_name
            )
            result = await dataset_info(input_data)
            return result.dict() if hasattr(result, 'dict') else result
        
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
