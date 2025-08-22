"""
Tools API for AAF Backend
Provides endpoints to manage and use custom tools
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..core.tool_manager import get_tool_manager, ToolManager
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolCallRequest(BaseModel):
    """Tool call request model"""
    tool_name: str = Field(..., description="Name of the tool to call")
    function_name: str = Field(..., description="Function name to call")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")


class WebScrapingRequest(BaseModel):
    """Web scraping request model"""
    url: str = Field(..., description="URL to scrape")
    extract_text: bool = Field(default=True, description="Extract text content")
    extract_links: bool = Field(default=False, description="Extract links")
    extract_images: bool = Field(default=False, description="Extract images")
    extract_metadata: bool = Field(default=True, description="Extract metadata")
    css_selector: Optional[str] = Field(None, description="CSS selector for specific content")
    remove_ads: bool = Field(default=True, description="Remove advertisements")
    remove_navigation: bool = Field(default=True, description="Remove navigation")


class DocumentLoadRequest(BaseModel):
    """Document loading request model"""
    source_type: str = Field(..., description="Source type: file, url, text, web")
    source_path: Optional[str] = Field(None, description="Path or URL to data source")
    content: Optional[str] = Field(None, description="Direct text content")
    collection_name: str = Field(..., description="Collection name for organizing documents")
    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: list[str] = Field(default=[], description="Tags for categorization")


class VectorSearchRequest(BaseModel):
    """Vector search request model"""
    query: str = Field(..., description="Natural language search query")
    collection_name: Optional[str] = Field(None, description="Specific collection to search")
    limit: int = Field(default=5, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score (0-1)")
    tags_filter: Optional[list[str]] = Field(None, description="Filter by document tags")
    include_metadata: bool = Field(default=True, description="Include document metadata")


@router.get("/")
async def list_tools(manager: ToolManager = Depends(get_tool_manager)):
    """
    List all available tools and their capabilities
    
    Returns information about web scraper, data loader, and other custom tools.
    """
    try:
        return await manager.list_tools()
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/{tool_name}/status")
async def get_tool_status(
    tool_name: str,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Get status information for a specific tool
    
    Includes configuration, availability, and tool-specific metrics.
    """
    try:
        return await manager.get_tool_status(tool_name)
    except Exception as e:
        logger.error(f"Failed to get tool status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tool status: {str(e)}"
        )


@router.post("/call")
async def call_tool(
    request: ToolCallRequest,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Call a custom tool function
    
    Generic endpoint for calling any tool function with arguments.
    """
    try:
        result = await manager.call_tool(
            request.tool_name,
            request.function_name,
            request.arguments
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Tool call failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tool call failed: {str(e)}"
        )


@router.post("/web-scraper/scrape")
async def scrape_url(
    request: WebScrapingRequest,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Scrape content from a web page
    
    Uses the remote crawl4ai MCP server to extract content from websites.
    """
    try:
        # Call the web scraper tool
        result = await manager.call_tool(
            "web_scraper",
            "scrape_url",
            request.dict()
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Web scraping failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web scraping error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Web scraping failed: {str(e)}"
        )


@router.post("/vector-rag/load")
async def load_document(
    request: DocumentLoadRequest,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Load a document into BigQuery Vector Search for semantic retrieval
    
    Supports files, URLs, direct text, and web scraping. Automatically creates
    embeddings and stores them for semantic search.
    """
    try:
        # Call the vector search RAG tool
        result = await manager.call_tool(
            "vector_search_rag",
            "load_document",
            request.dict()
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Document loading failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document loading error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document loading failed: {str(e)}"
        )


@router.post("/vector-rag/search")
async def search_documents(
    request: VectorSearchRequest,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Perform semantic search across loaded documents
    
    Uses natural language queries to find relevant documents using
    BigQuery Vector Search with cosine similarity.
    """
    try:
        # Call the vector search RAG tool
        result = await manager.call_tool(
            "vector_search_rag",
            "search_documents",
            request.dict()
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Vector search failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vector search failed: {str(e)}"
        )


@router.get("/vector-rag/collections")
async def list_collections(manager: ToolManager = Depends(get_tool_manager)):
    """
    List all document collections
    
    Returns metadata about available collections and their document counts.
    """
    try:
        # Call the vector search RAG tool
        result = await manager.call_tool(
            "vector_search_rag",
            "list_collections",
            {}
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to list collections")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List collections error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/vector-rag/collections/{collection_name}")
async def get_collection_info(
    collection_name: str,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Get detailed information about a collection
    
    Returns document count, sample documents, and metadata.
    """
    try:
        # Get the vector search RAG tool directly
        tool = manager.tools.get("vector_search_rag")
        if not tool:
            raise HTTPException(
                status_code=503,
                detail="Vector search RAG tool not available"
            )
        
        result = await tool.get_collection_info(collection_name)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", f"Collection {collection_name} not found")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get collection info error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )


@router.post("/vector-rag/collections/{collection_name}/search")
async def search_collection(
    collection_name: str,
    request: VectorSearchRequest,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Search within a specific collection
    
    Performs semantic search limited to documents in the specified collection.
    """
    try:
        # Force the collection filter
        search_request = request.copy()
        search_request.collection_name = collection_name
        
        # Call the vector search RAG tool
        result = await manager.call_tool(
            "vector_search_rag",
            "search_documents",
            search_request.dict()
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Collection search failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Collection search failed: {str(e)}"
        )


@router.post("/web-scraper/batch")
async def scrape_multiple_urls(
    urls: list[str],
    extract_text: bool = True,
    extract_links: bool = False,
    extract_images: bool = False,
    manager: ToolManager = Depends(get_tool_manager)
):
    """
    Scrape multiple URLs in batch
    
    Processes multiple URLs concurrently for efficiency.
    """
    try:
        # Validate input
        if len(urls) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 URLs allowed per batch"
            )
        
        # Get the web scraper tool directly for batch processing
        tool = manager.tools.get("web_scraper")
        if not tool:
            raise HTTPException(
                status_code=503,
                detail="Web scraper tool not available"
            )
        
        # Process URLs in batch
        from ..tools.web_scraper import WebScrapingRequest
        
        results = await tool.scrape_multiple_urls(
            urls,
            extract_text=extract_text,
            extract_links=extract_links,
            extract_images=extract_images
        )
        
        return {
            "success": True,
            "results": [result.dict() for result in results],
            "total_processed": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch scraping error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch scraping failed: {str(e)}"
        )
