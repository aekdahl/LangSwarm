"""
Knowledge Management API
Endpoints for scraping websites and managing knowledge base
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from ..core.config import get_settings
from ..services.web_scraper import WebScrapingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class ScrapeRequest(BaseModel):
    """Request model for scraping a URL"""
    url: HttpUrl
    max_content_length: int = 8000
    chunk_size: int = 1000
    chunk_overlap: int = 200


class ScrapeResponse(BaseModel):
    """Response model for scraping results"""
    success: bool
    url: str
    title: Optional[str] = None
    chunks_processed: Optional[int] = None
    documents_stored: Optional[int] = None
    document_ids: Optional[List[str]] = None
    error: Optional[str] = None


class StoredUrlInfo(BaseModel):
    """Information about a stored URL"""
    url: str
    title: str
    chunk_count: int
    last_updated: Optional[str] = None
    metadata: dict = {}


# Initialize web scraping service
settings = get_settings()
scraper_service = WebScrapingService(
    project_id=settings.google_cloud_project,
    dataset_id=getattr(settings, 'vector_dataset_id', 'vector_search'),
    table_name=getattr(settings, 'vector_table_name', 'embeddings'),
    openai_api_key=settings.openai_api_key,
    crawl4ai_base_url=getattr(settings, 'crawl4ai_base_url', None)
)


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape a URL and store embeddings in BigQuery
    
    This endpoint will:
    1. Scrape content from the provided URL
    2. Extract and clean the text
    3. Split content into chunks
    4. Generate embeddings for each chunk
    5. Store everything in BigQuery for vector search
    """
    try:
        logger.info(f"Starting scrape for URL: {request.url}")
        
        result = await scraper_service.scrape_and_embed_url(
            url=str(request.url),
            max_content_length=request.max_content_length,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        return ScrapeResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to scrape URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.put("/scrape/{url_hash}")
async def update_scraped_url(url_hash: str, request: ScrapeRequest):
    """
    Update an existing scraped URL (re-scrape and replace)
    """
    try:
        result = await scraper_service.update_existing_url(str(request.url))
        return ScrapeResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to update URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/urls", response_model=List[StoredUrlInfo])
async def list_stored_urls():
    """
    Get list of all URLs that have been scraped and stored
    """
    try:
        urls = await scraper_service.get_stored_urls()
        return [StoredUrlInfo(**url) for url in urls]
        
    except Exception as e:
        logger.error(f"Failed to list stored URLs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list URLs: {str(e)}")


@router.delete("/urls")
async def delete_url_data(url: HttpUrl):
    """
    Delete all data for a specific URL
    """
    try:
        # This would require implementing a delete method in WebScrapingService
        # For now, return not implemented
        raise HTTPException(status_code=501, detail="Delete functionality not yet implemented")
        
    except Exception as e:
        logger.error(f"Failed to delete URL data: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/stats")
async def get_knowledge_stats():
    """
    Get statistics about the knowledge base
    """
    try:
        urls = await scraper_service.get_stored_urls()
        
        total_urls = len(urls)
        total_chunks = sum(url.get('chunk_count', 0) for url in urls)
        
        return {
            "total_urls": total_urls,
            "total_chunks": total_chunks,
            "urls": urls
        }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
