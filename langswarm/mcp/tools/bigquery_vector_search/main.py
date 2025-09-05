# mcp/tools/bigquery_vector_search/main.py

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer

# Optional BigQuery support
try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound as BQNotFound
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

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

# === Helper Functions ===
def get_bigquery_client(project_id: str = None) -> bigquery.Client:
    """Get BigQuery client with project configuration"""
    if not BIGQUERY_AVAILABLE:
        raise ImportError("BigQuery support requires: pip install google-cloud-bigquery")
    
    actual_project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
    if not actual_project_id:
        raise ValueError("project_id is required or GOOGLE_CLOUD_PROJECT environment variable must be set")
    
    return bigquery.Client(project=actual_project_id)

async def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for text using OpenAI"""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI support requires: pip install openai")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    response = await client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float"
    )
    
    return response.data[0].embedding

# === Task Handlers ===
def similarity_search(input_data: SimilaritySearchInput) -> SimilaritySearchOutput:
    """Perform vector similarity search in BigQuery"""
    try:
        # Get configuration
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = input_data.dataset_id or DEFAULT_CONFIG["dataset_id"]
        table_name = input_data.table_name or DEFAULT_CONFIG["table_name"]
        
        # Initialize BigQuery client
        bq_client = get_bigquery_client(project_id)
        
        # Check if embedding is provided, if not return error for sync method
        if input_data.query_embedding is None:
            return SimilaritySearchOutput(
                success=False,
                query=input_data.query,
                results=[],
                total_results=0,
                dataset=f"{dataset_id}.{table_name}",
                error="query_embedding is required (async embedding generation not supported in sync method)"
            )
        
        # Construct similarity search query
        embedding_str = f"[{','.join(map(str, input_data.query_embedding))}]"
        
        sql_query = f"""
        WITH query_embedding AS (
            SELECT {embedding_str} as query_vector
        ),
        similarities AS (
            SELECT 
                document_id,
                content,
                url,
                title,
                metadata,
                created_at,
                ML.DISTANCE(embedding, (SELECT query_vector FROM query_embedding), 'COSINE') as distance,
                (1 - ML.DISTANCE(embedding, (SELECT query_vector FROM query_embedding), 'COSINE')) as similarity
            FROM `{project_id}.{dataset_id}.{table_name}`
            WHERE embedding IS NOT NULL
        )
        SELECT 
            document_id,
            content,
            url,
            title,
            metadata,
            created_at,
            similarity
        FROM similarities
        WHERE similarity >= {input_data.similarity_threshold}
        ORDER BY similarity DESC
        LIMIT {input_data.limit}
        """
        
        # Execute query
        query_job = bq_client.query(sql_query)
        results = list(query_job.result())
        
        # Format results
        formatted_results = []
        for row in results:
            result = {
                "document_id": row.document_id,
                "content": row.content,
                "url": row.url,
                "title": row.title,
                "similarity": float(row.similarity),
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            
            # Parse metadata if it's a JSON string
            if row.metadata:
                try:
                    result["metadata"] = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                except (json.JSONDecodeError, TypeError):
                    result["metadata"] = row.metadata
            
            formatted_results.append(result)
        
        return SimilaritySearchOutput(
            success=True,
            query=input_data.query,
            results=formatted_results,
            total_results=len(formatted_results),
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
            error=f"Similarity search failed: {str(e)}"
        )

def list_datasets(input_data: ListDatasetsInput) -> ListDatasetsOutput:
    """List available vector search datasets"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        bq_client = get_bigquery_client(project_id)
        
        datasets = []
        for dataset in bq_client.list_datasets():
            dataset_id = dataset.dataset_id
            
            # Apply pattern filter if provided
            if input_data.pattern and input_data.pattern.lower() not in dataset_id.lower():
                continue
            
            # Check for tables with embeddings
            tables = []
            try:
                for table in bq_client.list_tables(dataset.reference):
                    # Check if table has embedding column
                    table_ref = bq_client.get_table(table.reference)
                    has_embeddings = any(field.name == 'embedding' for field in table_ref.schema)
                    
                    if has_embeddings:
                        tables.append({
                            "table_name": table.table_id,
                            "rows": table_ref.num_rows,
                            "created": table_ref.created.isoformat() if table_ref.created else None
                        })
            except Exception as e:
                logger.warning(f"Could not inspect tables in dataset {dataset_id}: {e}")
            
            if tables:  # Only include datasets with embedding tables
                datasets.append({
                    "dataset_id": dataset_id,
                    "tables": tables,
                    "location": dataset.location
                })
        
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
            error=f"Failed to list datasets: {str(e)}"
        )

def get_content(input_data: GetContentInput) -> GetContentOutput:
    """Retrieve full content by document ID"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = input_data.dataset_id or DEFAULT_CONFIG["dataset_id"]
        table_name = input_data.table_name or DEFAULT_CONFIG["table_name"]
        
        bq_client = get_bigquery_client(project_id)
        
        query = f"""
        SELECT 
            document_id,
            content,
            url,
            title,
            metadata,
            created_at
        FROM `{project_id}.{dataset_id}.{table_name}`
        WHERE document_id = @document_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", input_data.document_id)
            ]
        )
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return GetContentOutput(
                success=False,
                error=f"Document not found: {input_data.document_id}"
            )
        
        row = results[0]
        result = {
            "document_id": row.document_id,
            "content": row.content,
            "url": row.url,
            "title": row.title,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        
        # Parse metadata
        if row.metadata:
            try:
                result["metadata"] = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
            except (json.JSONDecodeError, TypeError):
                result["metadata"] = row.metadata
        
        return GetContentOutput(
            success=True,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Failed to get content: {e}")
        return GetContentOutput(
            success=False,
            error=f"Failed to get content: {str(e)}"
        )

def dataset_info(input_data: DatasetInfoInput) -> DatasetInfoOutput:
    """Get detailed information about a dataset/table"""
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        bq_client = get_bigquery_client(project_id)
        
        table_ref = bq_client.dataset(input_data.dataset_id).table(input_data.table_name)
        table = bq_client.get_table(table_ref)
        
        # Get sample of recent documents
        sample_query = f"""
        SELECT 
            document_id,
            title,
            url,
            CHAR_LENGTH(content) as content_length,
            created_at
        FROM `{project_id}.{input_data.dataset_id}.{input_data.table_name}`
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        query_job = bq_client.query(sample_query)
        sample_docs = [dict(row) for row in query_job.result()]
        
        # Format sample docs
        for doc in sample_docs:
            if doc.get('created_at'):
                doc['created_at'] = doc['created_at'].isoformat()
        
        return DatasetInfoOutput(
            success=True,
            dataset_id=input_data.dataset_id,
            table_name=input_data.table_name,
            total_rows=table.num_rows,
            size_bytes=table.num_bytes,
            created=table.created.isoformat() if table.created else None,
            modified=table.modified.isoformat() if table.modified else None,
            table_schema=[{"name": field.name, "type": field.field_type} for field in table.schema],
            sample_documents=sample_docs
        )
        
    except Exception as e:
        logger.error(f"Failed to get dataset info: {e}")
        return DatasetInfoOutput(
            success=False,
            dataset_id=input_data.dataset_id,
            table_name=input_data.table_name,
            error=f"Failed to get dataset info: {str(e)}"
        )

# === Build MCP Server ===
server = BaseMCPToolServer(
    name="bigquery_vector_search",
    description="BigQuery vector similarity search for knowledge base queries.",
    local_mode=True  # 🔧 Enable local mode!
)

# Add search operations
server.add_task(
    name="similarity_search",
    description="Perform vector similarity search to find relevant content.",
    input_model=SimilaritySearchInput,
    output_model=SimilaritySearchOutput,
    handler=similarity_search
)

server.add_task(
    name="get_content",
    description="Retrieve full document content by document ID.",
    input_model=GetContentInput,
    output_model=GetContentOutput,
    handler=get_content
)

# Add management operations
server.add_task(
    name="list_datasets",
    description="List available vector search datasets and tables.",
    input_model=ListDatasetsInput,
    output_model=ListDatasetsOutput,
    handler=list_datasets
)

server.add_task(
    name="dataset_info",
    description="Get detailed information about a specific dataset/table.",
    input_model=DatasetInfoInput,
    output_model=DatasetInfoOutput,
    handler=dataset_info
)

# Create FastAPI app for HTTP mode
app = server.build_app()

# === LangChain-Compatible Tool Class ===
try:
    from langswarm.synapse.tools.base import BaseTool
    
    class BigQueryVectorSearchMCPTool(BaseTool):
        """
        BigQuery Vector Search MCP tool for semantic knowledge base search.
        
        Features:
        - Vector similarity search using embeddings
        - Document retrieval by ID
        - Dataset management and inspection
        - Configurable similarity thresholds
        """
        _is_mcp_tool = True
        _bypass_pydantic = True  # Bypass Pydantic validation
        
        def __init__(self, identifier: str):
            # Initialize with required BaseTool parameters
            super().__init__(
                name="BigQuery Vector Search",
                description="Search company knowledge base using BigQuery vector similarity",
                instruction="Use this tool to perform semantic searches on your knowledge base stored in BigQuery. Provide a query and get relevant documents back.",
                identifier=identifier,
                brief="BigQuery vector search for semantic knowledge retrieval"
            )
            # Use object.__setattr__ to bypass Pydantic validation
            object.__setattr__(self, 'server', server)
            
            # Configure default settings
            object.__setattr__(self, 'default_config', DEFAULT_CONFIG.copy())
            
        async def similarity_search(self, query: str, limit: int = 10, similarity_threshold: float = 0.7, 
                                   dataset_id: str = None, table_name: str = None):
            """Perform vector similarity search with automatic embedding generation"""
            try:
                # Generate embedding for the query text
                logger.info(f"Generating embedding for query: {query[:100]}...")
                query_embedding = await get_embedding(query)
                logger.info(f"Embedding generated successfully, dimension: {len(query_embedding)}")
                
                search_input = SimilaritySearchInput(
                    query=query,
                    query_embedding=query_embedding,  # Add the generated embedding
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                    dataset_id=dataset_id or self.default_config["dataset_id"],
                    table_name=table_name or self.default_config["table_name"]
                )
                
                # Use the global handler functions defined above
                logger.info(f"Executing BigQuery search with {len(query_embedding)}-dim embedding...")
                result = similarity_search(search_input)
                logger.info(f"BigQuery search completed: {result.total_results} results found")
                return result.dict()
                
            except Exception as e:
                logger.error(f"BigQuery similarity search failed: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        async def get_content(self, document_id: str, dataset_id: str = None, table_name: str = None):
            """Get document content by ID"""
            try:
                content_input = GetContentInput(
                    document_id=document_id,
                    dataset_id=dataset_id or self.default_config["dataset_id"],
                    table_name=table_name or self.default_config["table_name"]
                )
                
                # Use the global handler functions defined above
                result = get_content(content_input)
                return result.dict()
                
            except Exception as e:
                logger.error(f"BigQuery get content failed: {e}")
                return {"success": False, "error": str(e)}
        
        async def list_datasets(self, pattern: str = None):
            """List available datasets"""
            try:
                list_input = ListDatasetsInput(pattern=pattern)
                
                # Use the global handler functions defined above
                result = list_datasets(list_input)
                return result.dict()
                
            except Exception as e:
                logger.error(f"BigQuery list datasets failed: {e}")
                return {"success": False, "error": str(e)}
        
        async def dataset_info(self, dataset_id: str, table_name: str):
            """Get dataset information"""
            try:
                info_input = DatasetInfoInput(
                    dataset_id=dataset_id,
                    table_name=table_name
                )
                
                # Use the global handler functions defined above
                result = dataset_info(info_input)
                return result.dict()
                
            except Exception as e:
                logger.error(f"BigQuery dataset info failed: {e}")
                return {"success": False, "error": str(e)}
        
        def run(self, input_data=None):
            """Generic run method for MCP tool calls (handles both sync and async contexts)"""
            import asyncio
            import concurrent.futures
            import threading
            import time
            
            logger.info(f"BigQuery tool run() called with input: {input_data}")
            logger.info(f"Input type: {type(input_data)}")
            
            start_time = time.time()
            
            try:
                # Simple approach: always use a separate thread with its own event loop
                # This avoids all the complexity of trying to reuse existing loops
                logger.info("Starting BigQuery tool execution in separate thread")
                
                def run_async_in_thread():
                    """Run the async function in a completely separate thread with its own event loop"""
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        logger.info("Created new event loop in thread")
                        result = new_loop.run_until_complete(self._async_run(input_data))
                        logger.info(f"Thread execution completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Thread execution failed: {e}")
                        return {"success": False, "error": str(e)}
                    finally:
                        # Clean shutdown of the event loop
                        try:
                            new_loop.close()
                            logger.info("Event loop closed cleanly")
                        except Exception as e:
                            logger.warning(f"Event loop cleanup warning: {e}")
                
                # Execute with timeout in separate thread
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    logger.info("Submitting task to thread pool")
                    future = executor.submit(run_async_in_thread)
                    
                    try:
                        # 30 second timeout to prevent hanging
                        result = future.result(timeout=30)
                        elapsed = time.time() - start_time
                        logger.info(f"BigQuery tool completed in {elapsed:.2f}s")
                        return result
                        
                    except concurrent.futures.TimeoutError:
                        elapsed = time.time() - start_time
                        logger.error(f"BigQuery tool timed out after {elapsed:.2f}s")
                        return {
                            "success": False, 
                            "error": f"Tool execution timed out after {elapsed:.2f} seconds"
                        }
                        
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"BigQuery tool execution failed after {elapsed:.2f}s: {e}")
                return {"success": False, "error": str(e)}
        
        async def _async_run(self, input_data=None):
            """Internal async implementation of run method"""
            try:
                # Handle different input formats
                if isinstance(input_data, dict):
                    # Check for structured MCP format
                    if "method" in input_data and "params" in input_data:
                        method = input_data["method"]
                        params = input_data["params"]
                        logger.info(f"Structured MCP call: method={method}, params={params}")
                    elif "method" in input_data:
                        method = input_data["method"]
                        params = {k: v for k, v in input_data.items() if k != "method"}
                        logger.info(f"Semi-structured call: method={method}, params={params}")
                    else:
                        # Assume it's a direct method call (most common for agents)
                        # Try to infer method from parameters or default to similarity_search
                        if "query" in input_data:
                            method = "similarity_search"
                            params = input_data
                            logger.info(f"Inferred similarity_search from query parameter")
                        elif "document_id" in input_data:
                            method = "get_content"
                            params = input_data
                            logger.info(f"Inferred get_content from document_id parameter")
                        else:
                            return {"success": False, "error": f"Cannot infer method from input: {input_data}"}
                else:
                    # Handle string input (simple query)
                    if isinstance(input_data, str):
                        method = "similarity_search"
                        params = {"query": input_data}
                        logger.info(f"String input converted to similarity_search: {input_data[:100]}...")
                    else:
                        return {"success": False, "error": f"Unsupported input type: {type(input_data)}"}
                
                # Route to appropriate method
                if method == "similarity_search":
                    logger.info(f"Calling similarity_search with params: {params}")
                    return await self.similarity_search(**params)
                elif method == "get_content":
                    logger.info(f"Calling get_content with params: {params}")
                    return await self.get_content(**params)
                elif method == "list_datasets":
                    logger.info(f"Calling list_datasets with params: {params}")
                    return await self.list_datasets(**params)
                elif method == "dataset_info":
                    logger.info(f"Calling dataset_info with params: {params}")
                    return await self.dataset_info(**params)
                else:
                    available_methods = ["similarity_search", "get_content", "list_datasets", "dataset_info"]
                    return {"success": False, "error": f"Unknown method: {method}. Available: {available_methods}"}
                    
            except Exception as e:
                logger.error(f"BigQuery tool _async_run() failed: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        def configure(self, config: dict):
            """Configure the tool with custom settings"""
            if config:
                self.default_config.update(config)
                logger.info(f"BigQuery tool configured: {self.default_config}")

except ImportError:
    # BaseTool not available - tool will only work in server mode
    BigQueryVectorSearchMCPTool = None
    logger.warning("BigQuery Vector Search MCP tool class not available - BaseTool import failed")

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.bigquery_vector_search.main:app", host="0.0.0.0", port=4021, reload=True)
