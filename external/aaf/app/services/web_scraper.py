"""
Web Scraper and Embedding Service
Uses Crawl4AI MCP server for scraping and stores embeddings in BigQuery for vector search
"""

import asyncio
import hashlib
import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

import openai
from google.cloud import bigquery

logger = logging.getLogger(__name__)


class WebScrapingService:
    """Service for scraping websites and storing embeddings in BigQuery"""
    
    def __init__(self, 
                 project_id: str,
                 dataset_id: str = "vector_search",
                 table_name: str = "embeddings",
                 openai_api_key: str = None,
                 crawl4ai_base_url: str = None):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.bq_client = bigquery.Client(project=project_id)
        
        # Crawl4AI MCP server configuration
        self.crawl4ai_base_url = crawl4ai_base_url or os.getenv('CRAWL4AI_BASE_URL')
        if not self.crawl4ai_base_url:
            raise ValueError("CRAWL4AI_BASE_URL environment variable or crawl4ai_base_url parameter is required")
        
        # Note: Table creation will happen on first use
        self._table_initialized = False
    
    async def _ensure_table_exists(self):
        """Ensure the BigQuery table exists with proper schema"""
        try:
            dataset_ref = self.bq_client.dataset(self.dataset_id)
            
            # Create dataset if it doesn't exist
            try:
                self.bq_client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "europe-west1"  # Match your region
                self.bq_client.create_dataset(dataset)
                logger.info(f"Created dataset: {self.dataset_id}")
            
            # Define table schema
            schema = [
                bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "FLOAT", mode="REPEATED"),
                bigquery.SchemaField("metadata", "STRING", mode="NULLABLE"),  # JSON string
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("content_hash", "STRING", mode="REQUIRED"),
            ]
            
            table_ref = dataset_ref.table(self.table_name)
            
            # Create table if it doesn't exist
            try:
                self.bq_client.get_table(table_ref)
                logger.info(f"Table {self.table_name} already exists")
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                self.bq_client.create_table(table)
                logger.info(f"Created table: {self.table_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure table exists: {e}")
            raise
    
    async def _ensure_table_if_needed(self):
        """Ensure table is initialized on first use"""
        if not self._table_initialized:
            await self._ensure_table_exists()
            self._table_initialized = True

    async def scrape_and_embed_url(self, 
                                  url: str,
                                  max_content_length: int = 8000,
                                  chunk_size: int = 1000,
                                  chunk_overlap: int = 200) -> Dict[str, Any]:
        """
        Scrape a URL and store embeddings in BigQuery
        
        Args:
            url: URL to scrape
            max_content_length: Maximum content length to process
            chunk_size: Size of each chunk for embedding
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dict with scraping results
        """
        try:
            # Ensure table is initialized
            await self._ensure_table_if_needed()
            
            # Scrape the URL
            content_data = await self._scrape_url(url)
            
            if not content_data:
                return {"success": False, "error": "Failed to scrape URL"}
            
            # Process content into chunks
            chunks = self._chunk_text(content_data["content"], chunk_size, chunk_overlap)
            
            # Limit total content length
            total_content = content_data["content"][:max_content_length]
            
            # Generate embeddings for chunks
            embeddings = []
            for chunk in chunks:
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                
                embedding = await self._get_embedding(chunk)
                embeddings.append({
                    "content": chunk,
                    "embedding": embedding
                })
            
            if not embeddings:
                return {"success": False, "error": "No meaningful content found"}
            
            # Store in BigQuery
            stored_docs = await self._store_embeddings(
                url=url,
                title=content_data["title"],
                content=total_content,
                embeddings=embeddings,
                metadata=content_data.get("metadata", {})
            )
            
            return {
                "success": True,
                "url": url,
                "title": content_data["title"],
                "chunks_processed": len(embeddings),
                "documents_stored": len(stored_docs),
                "document_ids": stored_docs
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape and embed URL {url}: {e}")
            return {"success": False, "error": str(e)}
    
    def _call_crawl4ai_mcp(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call Crawl4AI MCP server tool"""
        try:
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": f"call-{tool_name}-{int(datetime.now().timestamp())}"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.crawl4ai_base_url,
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for web scraping
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP error: {result['error']}")
            
            return result.get("result", {})
            
        except Exception as e:
            logger.error(f"Failed to call Crawl4AI MCP: {e}")
            raise

    async def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a URL using Crawl4AI MCP server"""
        try:
            # Call Crawl4AI MCP server to scrape the URL
            # Note: Making sync call to MCP server (not async since it's HTTP)
            scrape_result = self._call_crawl4ai_mcp("scrape", {
                "url": url,
                "wait_for": 2,  # Wait 2 seconds for page to load
                "extraction_strategy": "LLMExtractionStrategy",
                "extraction_config": {
                    "provider": "openai/gpt-4o-mini",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Page title"},
                            "content": {"type": "string", "description": "Main content text"},
                            "description": {"type": "string", "description": "Page description"},
                            "key_points": {"type": "array", "items": {"type": "string"}, "description": "Key points from the content"}
                        }
                    }
                }
            })
            
            if not scrape_result or "content" not in scrape_result:
                logger.warning(f"No content extracted from URL: {url}")
                return None
            
            # Extract structured data from MCP response
            extracted_data = scrape_result.get("extracted_content", {})
            if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except json.JSONDecodeError:
                    extracted_data = {}
            
            # Fallback to raw content if structured extraction failed
            title = (extracted_data.get("title") or 
                    scrape_result.get("title") or 
                    urlparse(url).netloc)
            
            content = (extracted_data.get("content") or 
                      scrape_result.get("content", ""))
            
            # Create metadata
            metadata = {
                "scraped_at": datetime.utcnow().isoformat(),
                "domain": urlparse(url).netloc,
                "content_length": len(content),
                "scraper": "crawl4ai_mcp"
            }
            
            # Add extracted metadata
            if extracted_data.get("description"):
                metadata["description"] = extracted_data["description"]
            if extracted_data.get("key_points"):
                metadata["key_points"] = extracted_data["key_points"]
            
            # Add raw scraping metadata
            if scrape_result.get("metadata"):
                metadata.update(scrape_result["metadata"])
            
            return {
                "title": title,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            return None
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the end
                for i in range(min(200, chunk_size // 4)):
                    if end - i > start and text[end - i:end - i + 1] in '.!?':
                        end = end - i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise
    
    async def _store_embeddings(self, 
                               url: str,
                               title: str,
                               content: str,
                               embeddings: List[Dict],
                               metadata: Dict) -> List[str]:
        """Store embeddings in BigQuery"""
        try:
            table_ref = self.bq_client.dataset(self.dataset_id).table(self.table_name)
            
            # Prepare rows for insertion
            rows = []
            document_ids = []
            
            for i, emb_data in enumerate(embeddings):
                document_id = f"{hashlib.md5(url.encode()).hexdigest()}_{i}"
                content_hash = hashlib.md5(emb_data["content"].encode()).hexdigest()
                
                row = {
                    "document_id": document_id,
                    "url": url,
                    "title": title,
                    "content": emb_data["content"],
                    "embedding": emb_data["embedding"],
                    "metadata": json.dumps(metadata),
                    "created_at": datetime.utcnow(),
                    "content_hash": content_hash
                }
                
                rows.append(row)
                document_ids.append(document_id)
            
            # Insert rows
            errors = self.bq_client.insert_rows_json(table_ref, rows)
            
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                raise Exception(f"Failed to insert rows: {errors}")
            
            logger.info(f"Stored {len(rows)} embeddings for URL: {url}")
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise
    
    async def update_existing_url(self, url: str) -> Dict[str, Any]:
        """Update embeddings for an existing URL (re-scrape and replace)"""
        try:
            # First, delete existing entries for this URL
            delete_query = f"""
            DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_name}`
            WHERE url = @url
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("url", "STRING", url)
                ]
            )
            
            query_job = self.bq_client.query(delete_query, job_config=job_config)
            query_job.result()  # Wait for completion
            
            # Now scrape and embed again
            return await self.scrape_and_embed_url(url)
            
        except Exception as e:
            logger.error(f"Failed to update URL {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_stored_urls(self) -> List[Dict[str, Any]]:
        """Get list of URLs that have been scraped and stored"""
        try:
            query = f"""
            SELECT 
                url,
                title,
                COUNT(*) as chunk_count,
                MAX(created_at) as last_updated,
                ANY_VALUE(metadata) as metadata
            FROM `{self.project_id}.{self.dataset_id}.{self.table_name}`
            GROUP BY url, title
            ORDER BY last_updated DESC
            """
            
            query_job = self.bq_client.query(query)
            results = []
            
            for row in query_job.result():
                result = {
                    "url": row.url,
                    "title": row.title,
                    "chunk_count": row.chunk_count,
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None
                }
                
                # Parse metadata
                if row.metadata:
                    try:
                        result["metadata"] = json.loads(row.metadata)
                    except (json.JSONDecodeError, TypeError):
                        result["metadata"] = {}
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get stored URLs: {e}")
            return []
