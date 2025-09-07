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
    "default_similarity_threshold": 0.7,
    "max_results": 50
}

# === Schemas ===
class SimilaritySearchInput(BaseModel):
    query: str
    query_embedding: Optional[List[float]] = None
    limit: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7
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

async def similarity_search(input_data: SimilaritySearchInput) -> SimilaritySearchOutput:
    """Perform vector similarity search in BigQuery using shared utilities"""
    try:
        # Get configuration
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = input_data.dataset_id or DEFAULT_CONFIG["dataset_id"]
        table_name = input_data.table_name or DEFAULT_CONFIG["table_name"]
        
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
            similarity_threshold=input_data.similarity_threshold,
            limit=input_data.limit
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
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = input_data.dataset_id or DEFAULT_CONFIG["dataset_id"]
        table_name = input_data.table_name or DEFAULT_CONFIG["table_name"]
        
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
    name="bigquery_vector_search",
    description="BigQuery vector similarity search for knowledge base queries.",
    local_mode=True
)

# Add operations
server.add_task(
    name="similarity_search",
    description="Perform vector similarity search to find relevant content.",
    input_model=SimilaritySearchInput,
    output_model=SimilaritySearchOutput,
    handler=lambda input_data: similarity_search(input_data)
)

server.add_task(
    name="get_content",
    description="Retrieve full document content by document ID.",
    input_model=GetContentInput,
    output_model=GetContentOutput,
    handler=lambda input_data: get_content(input_data)
)

server.add_task(
    name="list_datasets",
    description="List available vector search datasets and tables.",
    input_model=ListDatasetsInput,
    output_model=ListDatasetsOutput,
    handler=lambda input_data: list_datasets(input_data)
)

server.add_task(
    name="dataset_info",
    description="Get detailed information about a specific dataset/table.",
    input_model=DatasetInfoInput,
    output_model=DatasetInfoOutput,
    handler=lambda input_data: dataset_info(input_data)
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
        
        def __init__(self, identifier: str):
            super().__init__(
                name="BigQuery Vector Search",
                description="Search company knowledge base using BigQuery vector similarity",
                instruction="""Use this tool to perform semantic searches on your knowledge base stored in BigQuery.

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
}""",
                identifier=identifier,
                brief="BigQuery vector search for semantic knowledge retrieval"
            )
            object.__setattr__(self, 'server', server)
            object.__setattr__(self, 'default_config', DEFAULT_CONFIG.copy())
        
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
                    result = await similarity_search(input_obj)
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
