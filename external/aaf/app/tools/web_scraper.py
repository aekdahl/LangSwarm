"""
Web Scraper Tool - Remote MCP Integration
Connects to hosted crawl4ai MCP server for web scraping capabilities
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
from pydantic import BaseModel, Field, HttpUrl

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class WebScrapingRequest(BaseModel):
    """Web scraping request model"""
    url: HttpUrl = Field(..., description="URL to scrape")
    extract_text: bool = Field(default=True, description="Extract text content")
    extract_links: bool = Field(default=False, description="Extract all links")
    extract_images: bool = Field(default=False, description="Extract image URLs")
    extract_metadata: bool = Field(default=True, description="Extract page metadata")
    follow_redirects: bool = Field(default=True, description="Follow redirects")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    user_agent: Optional[str] = Field(None, description="Custom user agent")
    css_selector: Optional[str] = Field(None, description="CSS selector for specific content")
    remove_ads: bool = Field(default=True, description="Remove advertisements")
    remove_navigation: bool = Field(default=True, description="Remove navigation elements")


class WebScrapingResponse(BaseModel):
    """Web scraping response model"""
    url: str = Field(..., description="Scraped URL")
    title: Optional[str] = Field(None, description="Page title")
    text_content: Optional[str] = Field(None, description="Extracted text content")
    links: Optional[List[str]] = Field(None, description="Extracted links")
    images: Optional[List[str]] = Field(None, description="Extracted image URLs")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Page metadata")
    word_count: Optional[int] = Field(None, description="Word count of extracted text")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    success: bool = Field(..., description="Whether scraping was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class WebScraperTool:
    """Remote MCP web scraper tool using crawl4ai service"""
    
    def __init__(self, mcp_server_url: str, api_key: Optional[str] = None):
        self.mcp_server_url = mcp_server_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        self.name = "web_scraper"
        self.description = "Extract content from web pages using advanced scraping"
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session with proper headers"""
        if self.session is None:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AAF-WebScraper/1.0"
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_url(self, request: WebScrapingRequest) -> WebScrapingResponse:
        """Scrape a URL using the remote crawl4ai MCP server"""
        start_time = datetime.now()
        
        try:
            session = await self.get_session()
            
            # Prepare MCP request payload
            mcp_payload = {
                "method": "call_tool",
                "params": {
                    "name": "crawl_url",
                    "arguments": {
                        "url": str(request.url),
                        "extract_text": request.extract_text,
                        "extract_links": request.extract_links,
                        "extract_images": request.extract_images,
                        "extract_metadata": request.extract_metadata,
                        "follow_redirects": request.follow_redirects,
                        "timeout": request.timeout,
                        "css_selector": request.css_selector,
                        "remove_ads": request.remove_ads,
                        "remove_navigation": request.remove_navigation
                    }
                }
            }
            
            if request.user_agent:
                mcp_payload["params"]["arguments"]["user_agent"] = request.user_agent
            
            # Make request to crawl4ai MCP server
            async with session.post(f"{self.mcp_server_url}/mcp", json=mcp_payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"MCP server error {response.status}: {error_text}")
                    
                    return WebScrapingResponse(
                        url=str(request.url),
                        success=False,
                        error=f"MCP server error: {response.status} - {error_text}",
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
                
                result = await response.json()
                
                # Process MCP response
                if result.get("error"):
                    return WebScrapingResponse(
                        url=str(request.url),
                        success=False,
                        error=result["error"]["message"],
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
                
                content = result.get("result", {}).get("content", {})
                
                # Extract word count if text content is available
                word_count = None
                if content.get("text"):
                    word_count = len(content["text"].split())
                
                return WebScrapingResponse(
                    url=str(request.url),
                    title=content.get("title"),
                    text_content=content.get("text"),
                    links=content.get("links", []) if request.extract_links else None,
                    images=content.get("images", []) if request.extract_images else None,
                    metadata=content.get("metadata", {}) if request.extract_metadata else None,
                    word_count=word_count,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    success=True
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during web scraping: {e}")
            return WebScrapingResponse(
                url=str(request.url),
                success=False,
                error=f"Network error: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"Unexpected error during web scraping: {e}")
            return WebScrapingResponse(
                url=str(request.url),
                success=False,
                error=f"Unexpected error: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def scrape_multiple_urls(self, urls: List[str], **kwargs) -> List[WebScrapingResponse]:
        """Scrape multiple URLs concurrently"""
        
        # Create requests for all URLs
        requests = []
        for url in urls:
            request = WebScrapingRequest(url=url, **kwargs)
            requests.append(request)
        
        # Process concurrently with semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def scrape_with_semaphore(req):
            async with semaphore:
                return await self.scrape_url(req)
        
        tasks = [scrape_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {urls[i]}: {result}")
                processed_results.append(WebScrapingResponse(
                    url=urls[i],
                    success=False,
                    error=str(result),
                    processing_time=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for LangSwarm integration"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL to scrape content from"
                    },
                    "extract_text": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to extract text content"
                    },
                    "extract_links": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to extract all links"
                    },
                    "extract_images": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to extract image URLs"
                    },
                    "extract_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to extract page metadata"
                    },
                    "css_selector": {
                        "type": "string",
                        "description": "CSS selector to extract specific content"
                    },
                    "remove_ads": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to remove advertisements"
                    },
                    "remove_navigation": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to remove navigation elements"
                    }
                },
                "required": ["url"]
            }
        }
    
    async def call_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """LangSwarm tool call interface"""
        try:
            # Create request from arguments
            request = WebScrapingRequest(**arguments)
            
            # Perform scraping
            result = await self.scrape_url(request)
            
            # Return result in LangSwarm format
            return {
                "success": result.success,
                "content": {
                    "url": result.url,
                    "title": result.title,
                    "text": result.text_content,
                    "links": result.links,
                    "images": result.images,
                    "metadata": result.metadata,
                    "word_count": result.word_count,
                    "processing_time": result.processing_time
                },
                "error": result.error
            }
            
        except Exception as e:
            logger.error(f"Web scraper tool call error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }


def create_web_scraper_tool(mcp_server_url: str, api_key: Optional[str] = None) -> WebScraperTool:
    """Factory function to create web scraper tool"""
    return WebScraperTool(mcp_server_url, api_key)


# Tool registration for LangSwarm
def get_web_scraper_tool_config() -> Dict[str, Any]:
    """Get web scraper tool configuration for LangSwarm"""
    settings = get_settings()
    
    # Get configuration from environment
    mcp_server_url = getattr(settings, 'crawl4ai_mcp_url', None)
    api_key = getattr(settings, 'crawl4ai_api_key', None)
    
    if not mcp_server_url:
        logger.warning("Crawl4AI MCP server URL not configured. Web scraper tool will not be available.")
        return None
    
    return {
        "type": "remote_mcp",
        "name": "web_scraper",
        "description": "Extract content from web pages using advanced scraping",
        "config": {
            "server_url": mcp_server_url,
            "api_key": api_key,
            "timeout": 60,
            "retry_count": 3
        }
    }
