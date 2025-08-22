"""
Multi-Tools API for AAF Backend
Enhanced API endpoints supporting multiple tool instances
"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..core.multi_tool_manager import get_multi_tool_manager, MultiToolManager, ToolConfiguration, ToolSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multitools", tags=["multitools"])


class ToolCallRequest(BaseModel):
    """Tool call request with specific tool ID"""
    tool_id: str = Field(..., description="Specific tool ID to call")
    function_name: str = Field(..., description="Function name to call")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")


class TypedToolCallRequest(BaseModel):
    """Tool call request by tool type"""
    tool_type: str = Field(..., description="Tool type to call")
    function_name: str = Field(..., description="Function name to call")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")
    prefer_tags: Optional[List[str]] = Field(None, description="Preferred tool tags")


class WebScrapingRequest(BaseModel):
    """Web scraping request with tool selection"""
    url: str = Field(..., description="URL to scrape")
    tool_id: Optional[str] = Field(None, description="Specific scraper tool ID")
    prefer_tags: Optional[List[str]] = Field(None, description="Preferred tool tags")
    extract_text: bool = Field(default=True, description="Extract text content")
    extract_links: bool = Field(default=False, description="Extract links")
    extract_images: bool = Field(default=False, description="Extract images")
    extract_metadata: bool = Field(default=True, description="Extract metadata")
    css_selector: Optional[str] = Field(None, description="CSS selector for specific content")
    remove_ads: bool = Field(default=True, description="Remove advertisements")
    remove_navigation: bool = Field(default=True, description="Remove navigation")


class VectorSearchRequest(BaseModel):
    """Vector search request with tool selection"""
    query: str = Field(..., description="Natural language search query")
    tool_id: Optional[str] = Field(None, description="Specific RAG tool ID")
    prefer_tags: Optional[List[str]] = Field(None, description="Preferred tool tags")
    collection_name: Optional[str] = Field(None, description="Specific collection to search")
    limit: int = Field(default=5, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score (0-1)")
    include_metadata: bool = Field(default=True, description="Include document metadata")


class DocumentLoadRequest(BaseModel):
    """Document loading request with tool selection"""
    source_type: str = Field(..., description="Source type: file, url, text, web")
    source_path: Optional[str] = Field(None, description="Path or URL to data source")
    content: Optional[str] = Field(None, description="Direct text content")
    collection_name: str = Field(..., description="Collection name for organizing documents")
    tool_id: Optional[str] = Field(None, description="Specific RAG tool ID")
    prefer_tags: Optional[List[str]] = Field(None, description="Preferred tool tags")
    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: List[str] = Field(default=[], description="Tags for categorization")


class ToolSourceRequest(BaseModel):
    """Request to add a new tool source"""
    source: ToolSource = Field(..., description="Tool source configuration")


@router.get("/")
async def list_all_tools(manager: MultiToolManager = Depends(get_multi_tool_manager)):
    """
    List all available tools from all sources
    
    Returns comprehensive information about all tools including their
    sources, configurations, and capabilities.
    """
    try:
        return await manager.list_tools()
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/by-type/{tool_type}")
async def get_tools_by_type(
    tool_type: str,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Get all tools of a specific type
    
    Returns all available tools matching the specified type.
    """
    try:
        tool_ids = await manager.get_tools_by_type(tool_type)
        
        if not tool_ids:
            raise HTTPException(
                status_code=404,
                detail=f"No tools of type {tool_type} found"
            )
        
        # Get detailed info for each tool
        tools = {}
        for tool_id in tool_ids:
            status = await manager.get_tool_status(tool_id)
            if status.get("success"):
                tools[tool_id] = status["status"]
        
        return {
            "success": True,
            "tool_type": tool_type,
            "tools": tools,
            "count": len(tools)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tools by type: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools by type: {str(e)}"
        )


@router.get("/by-tag/{tag}")
async def get_tools_by_tag(
    tag: str,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Get all tools with a specific tag
    
    Returns all available tools that have the specified tag.
    """
    try:
        tool_ids = await manager.get_tools_by_tag(tag)
        
        if not tool_ids:
            raise HTTPException(
                status_code=404,
                detail=f"No tools with tag '{tag}' found"
            )
        
        # Get detailed info for each tool
        tools = {}
        for tool_id in tool_ids:
            status = await manager.get_tool_status(tool_id)
            if status.get("success"):
                tools[tool_id] = status["status"]
        
        return {
            "success": True,
            "tag": tag,
            "tools": tools,
            "count": len(tools)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tools by tag: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools by tag: {str(e)}"
        )


@router.get("/{tool_id}/status")
async def get_tool_status(
    tool_id: str,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Get detailed status for a specific tool
    
    Returns configuration, availability, and tool-specific metrics.
    """
    try:
        return await manager.get_tool_status(tool_id)
    except Exception as e:
        logger.error(f"Failed to get tool status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tool status: {str(e)}"
        )


@router.post("/call")
async def call_specific_tool(
    request: ToolCallRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Call a specific tool by ID
    
    Directly calls a tool by its unique ID with the specified function and arguments.
    """
    try:
        result = await manager.call_tool(
            request.tool_id,
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


@router.post("/call-by-type")
async def call_tool_by_type(
    request: TypedToolCallRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Call the best available tool of a specific type
    
    Automatically selects the best tool of the specified type, optionally
    preferring tools with specific tags.
    """
    try:
        result = await manager.call_tool_by_type(
            request.tool_type,
            request.function_name,
            request.arguments,
            request.prefer_tags
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
        logger.error(f"Typed tool call error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Typed tool call failed: {str(e)}"
        )


@router.post("/web-scraper/scrape")
async def scrape_with_selection(
    request: WebScrapingRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Scrape content with automatic or manual tool selection
    
    Scrapes a URL using either a specific tool ID or the best available
    web scraper based on tags.
    """
    try:
        # Prepare arguments
        scrape_args = {
            "url": request.url,
            "extract_text": request.extract_text,
            "extract_links": request.extract_links,
            "extract_images": request.extract_images,
            "extract_metadata": request.extract_metadata,
            "css_selector": request.css_selector,
            "remove_ads": request.remove_ads,
            "remove_navigation": request.remove_navigation
        }
        
        # Use specific tool or select by type/tags
        if request.tool_id:
            result = await manager.call_tool(request.tool_id, "scrape_url", scrape_args)
        else:
            result = await manager.call_tool_by_type(
                "web_scraper", 
                "scrape_url", 
                scrape_args,
                request.prefer_tags
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


@router.post("/vector-rag/search")
async def search_with_selection(
    request: VectorSearchRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Perform semantic search with automatic or manual tool selection
    
    Searches documents using either a specific RAG tool ID or the best
    available tool based on tags.
    """
    try:
        # Prepare arguments
        search_args = {
            "query": request.query,
            "collection_name": request.collection_name,
            "limit": request.limit,
            "similarity_threshold": request.similarity_threshold,
            "include_metadata": request.include_metadata
        }
        
        # Use specific tool or select by type/tags
        if request.tool_id:
            result = await manager.call_tool(request.tool_id, "search_documents", search_args)
        else:
            result = await manager.call_tool_by_type(
                "vector_search_rag",
                "search_documents",
                search_args,
                request.prefer_tags
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


@router.post("/vector-rag/load")
async def load_document_with_selection(
    request: DocumentLoadRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Load documents with automatic or manual tool selection
    
    Loads documents using either a specific RAG tool ID or the best
    available tool based on tags.
    """
    try:
        # Prepare arguments
        load_args = {
            "source_type": request.source_type,
            "source_path": request.source_path,
            "content": request.content,
            "collection_name": request.collection_name,
            "title": request.title,
            "description": request.description,
            "tags": request.tags
        }
        
        # Use specific tool or select by type/tags
        if request.tool_id:
            result = await manager.call_tool(request.tool_id, "load_document", load_args)
        else:
            result = await manager.call_tool_by_type(
                "vector_search_rag",
                "load_document",
                load_args,
                request.prefer_tags
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


@router.post("/sources")
async def add_tool_source(
    request: ToolSourceRequest,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Dynamically add a new tool source
    
    Adds a new source with multiple tools and initializes them.
    """
    try:
        success = await manager.add_tool_source(request.source)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to add tool source"
            )
        
        return {
            "success": True,
            "message": f"Tool source {request.source.source_id} added successfully",
            "tools_added": len(request.source.tools)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add tool source error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add tool source: {str(e)}"
        )


@router.delete("/sources/{source_id}")
async def remove_tool_source(
    source_id: str,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Remove a tool source and all its tools
    
    Removes a source and properly closes all associated tools.
    """
    try:
        success = await manager.remove_tool_source(source_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Tool source {source_id} not found"
            )
        
        return {
            "success": True,
            "message": f"Tool source {source_id} removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove tool source error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove tool source: {str(e)}"
        )


@router.get("/sources")
async def list_tool_sources(manager: MultiToolManager = Depends(get_multi_tool_manager)):
    """
    List all tool sources
    
    Returns information about all configured tool sources.
    """
    try:
        sources_info = {}
        
        for source_id, source in manager.tool_sources.items():
            sources_info[source_id] = {
                "source_id": source.source_id,
                "source_type": source.source_type,
                "source_path": source.source_path,
                "tools_count": len(source.tools),
                "tools": [
                    {
                        "tool_id": tool.tool_id,
                        "name": tool.name,
                        "tool_type": tool.tool_type,
                        "enabled": tool.enabled,
                        "tags": tool.tags,
                        "priority": tool.priority
                    }
                    for tool in source.tools
                ],
                "metadata": source.metadata
            }
        
        return {
            "success": True,
            "sources": sources_info,
            "total_sources": len(sources_info)
        }
        
    except Exception as e:
        logger.error(f"List sources error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sources: {str(e)}"
        )


@router.post("/web-scraper/batch")
async def scrape_multiple_urls_with_selection(
    urls: List[str],
    tool_id: Optional[str] = None,
    prefer_tags: Optional[List[str]] = None,
    extract_text: bool = True,
    extract_links: bool = False,
    extract_images: bool = False,
    manager: MultiToolManager = Depends(get_multi_tool_manager)
):
    """
    Scrape multiple URLs with tool selection
    
    Processes multiple URLs using the best available scraper.
    """
    try:
        # Validate input
        if len(urls) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 URLs allowed per batch"
            )
        
        # Determine which tool to use
        if tool_id:
            if tool_id not in manager.tools:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tool {tool_id} not found"
                )
            tool = manager.tools[tool_id]
        else:
            # Find best web scraper
            scrapers = await manager.get_tools_by_type("web_scraper")
            if not scrapers:
                raise HTTPException(
                    status_code=503,
                    detail="No web scraper tools available"
                )
            
            # Apply tag preferences
            if prefer_tags:
                for tag in prefer_tags:
                    tagged_scrapers = await manager.get_tools_by_tag(tag)
                    matching = [s for s in scrapers if s in tagged_scrapers]
                    if matching:
                        tool = manager.tools[matching[0]]
                        break
                else:
                    tool = manager.tools[scrapers[0]]
            else:
                tool = manager.tools[scrapers[0]]
        
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
            "tool_used": getattr(tool, 'tool_id', 'unknown'),
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
