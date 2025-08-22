"""
Vector Search RAG Tool - Local MCP for Semantic Search
Loads documents into BigQuery Vector Search and provides semantic search capabilities
"""
import logging
import asyncio
import json
import uuid
import hashlib
import re
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
import aiofiles
import numpy as np

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class DocumentLoadRequest(BaseModel):
    """Document load request for vector search"""
    source_type: str = Field(..., description="Type of data source: file, url, text, web")
    source_path: Optional[str] = Field(None, description="Path or URL to data source")
    content: Optional[str] = Field(None, description="Direct text content to load")
    collection_name: str = Field(..., description="Collection name for organizing documents")
    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: List[str] = Field(default=[], description="Tags for categorizing documents")
    chunk_size: int = Field(default=1000, description="Characters per chunk for large documents")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    encoding: str = Field(default="utf-8", description="File encoding")
    extract_metadata: bool = Field(default=True, description="Extract metadata from source")
    auto_title: bool = Field(default=True, description="Auto-generate title from content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentLoadResponse(BaseModel):
    """Document load response model"""
    load_id: str = Field(..., description="Unique load identifier")
    collection_name: str = Field(..., description="Collection name")
    documents_loaded: int = Field(..., description="Number of documents loaded")
    chunks_created: int = Field(..., description="Number of text chunks created")
    embeddings_generated: int = Field(..., description="Number of embeddings generated")
    processing_time: float = Field(..., description="Processing time in seconds")
    source_size: Optional[int] = Field(None, description="Source content size in characters")
    checksum: Optional[str] = Field(None, description="Content checksum")
    created_at: str = Field(..., description="Creation timestamp")
    success: bool = Field(..., description="Whether load was successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    sample_chunks: Optional[List[str]] = Field(None, description="Sample text chunks")


class VectorSearchRequest(BaseModel):
    """Vector search request model"""
    query: str = Field(..., description="Natural language search query")
    collection_name: Optional[str] = Field(None, description="Specific collection to search (optional)")
    limit: int = Field(default=5, description="Maximum number of results to return")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score (0-1)")
    include_metadata: bool = Field(default=True, description="Include document metadata in results")
    tags_filter: Optional[List[str]] = Field(None, description="Filter by document tags")
    date_range: Optional[Dict[str, str]] = Field(None, description="Filter by date range")
    rerank: bool = Field(default=True, description="Apply semantic reranking to results")


class SearchResult(BaseModel):
    """Individual search result"""
    document_id: str = Field(..., description="Unique document identifier")
    collection_name: str = Field(..., description="Collection name")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Relevant content chunk")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    tags: List[str] = Field(default=[], description="Document tags")
    created_at: str = Field(..., description="Document creation timestamp")
    source_path: Optional[str] = Field(None, description="Original source path")


class VectorSearchResponse(BaseModel):
    """Vector search response model"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time: float = Field(..., description="Search processing time in seconds")
    collections_searched: List[str] = Field(..., description="Collections that were searched")
    success: bool = Field(..., description="Whether search was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class VectorSearchRAGTool:
    """Local MCP tool for vector search and RAG"""
    
    def __init__(self, project_id: str, dataset_id: str, embedding_model: str = "text-embedding-3-small"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.embedding_model = embedding_model
        self.name = "vector_search_rag"
        self.description = "Load documents and perform semantic search using BigQuery Vector Search"
        self.collections = {}  # Cache of loaded collection metadata
        self.bigquery_client = None
        self.openai_client = None
        self.vector_table = "document_vectors"
        self.metadata_table = "document_metadata"
        
    async def initialize(self):
        """Initialize BigQuery and OpenAI clients"""
        try:
            # Check if BigQuery is available
            if bigquery is None:
                raise ImportError("google-cloud-bigquery not installed")
                
            # Initialize BigQuery client
            self.bigquery_client = bigquery.Client(project=self.project_id)
            
            # Initialize OpenAI client for embeddings
            import openai
            settings = get_settings()
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Ensure tables exist
            await self._ensure_tables_exist()
            
            # Load existing collections metadata
            await self._load_collections_cache()
            
            logger.info(f"Vector search RAG tool initialized with BigQuery dataset: {self.dataset_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector search RAG tool: {e}")
            raise
    
    async def _ensure_tables_exist(self):
        """Create BigQuery tables if they don't exist"""
        
        # Vector embeddings table schema
        vector_schema = [
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("collection_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("chunk_index", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT", mode="REPEATED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        # Document metadata table schema
        metadata_schema = [
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("collection_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source_path", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
            bigquery.SchemaField("total_chunks", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("content_size", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("metadata_json", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("checksum", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        # Create tables
        await self._create_table_if_not_exists(self.vector_table, vector_schema)
        await self._create_table_if_not_exists(self.metadata_table, metadata_schema)
    
    async def _create_table_if_not_exists(self, table_name: str, schema: List):
        """Create a BigQuery table if it doesn't exist"""
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        try:
            # Check if table exists
            self.bigquery_client.get_table(table_id)
            logger.info(f"Table {table_id} already exists")
        except Exception:
            # Create table
            table = bigquery.Table(table_id, schema=schema)
            table = self.bigquery_client.create_table(table)
            logger.info(f"Created table {table_id}")
    
    async def _load_collections_cache(self):
        """Load existing collections metadata into cache"""
        try:
            query = f"""
            SELECT 
                collection_name,
                COUNT(*) as document_count,
                SUM(total_chunks) as total_chunks,
                MAX(created_at) as last_updated
            FROM `{self.project_id}.{self.dataset_id}.{self.metadata_table}`
            GROUP BY collection_name
            """
            
            job = self.bigquery_client.query(query)
            results = job.result()
            
            for row in results:
                self.collections[row.collection_name] = {
                    "document_count": row.document_count,
                    "total_chunks": row.total_chunks,
                    "last_updated": row.last_updated.isoformat()
                }
            
            logger.info(f"Loaded {len(self.collections)} collections into cache")
            
        except Exception as e:
            logger.warning(f"Failed to load collections cache: {e}")
    
    async def load_document(self, request: DocumentLoadRequest) -> DocumentLoadResponse:
        """Load a document into BigQuery Vector Search"""
        start_time = datetime.now()
        load_id = f"load_{uuid.uuid4().hex[:8]}"
        
        try:
            # Get content from source
            content, source_size = await self._get_content_from_source(request)
            
            # Generate title if needed
            if request.auto_title and not request.title:
                request.title = await self._generate_title(content[:500])
            
            # Split content into chunks
            chunks = await self._split_content(content, request.chunk_size, request.chunk_overlap)
            
            # Generate embeddings for chunks
            embeddings = await self._generate_embeddings(chunks)
            
            # Create document ID
            document_id = f"doc_{uuid.uuid4().hex}"
            
            # Calculate checksum
            checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # Store document metadata
            await self._store_document_metadata(
                document_id=document_id,
                request=request,
                total_chunks=len(chunks),
                content_size=len(content),
                checksum=checksum
            )
            
            # Store vector embeddings
            await self._store_document_vectors(
                document_id=document_id,
                collection_name=request.collection_name,
                chunks=chunks,
                embeddings=embeddings
            )
            
            # Update collections cache
            if request.collection_name not in self.collections:
                self.collections[request.collection_name] = {
                    "document_count": 0,
                    "total_chunks": 0,
                    "last_updated": datetime.now().isoformat()
                }
            
            self.collections[request.collection_name]["document_count"] += 1
            self.collections[request.collection_name]["total_chunks"] += len(chunks)
            self.collections[request.collection_name]["last_updated"] = datetime.now().isoformat()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Successfully loaded document {document_id} with {len(chunks)} chunks")
            
            return DocumentLoadResponse(
                load_id=load_id,
                collection_name=request.collection_name,
                documents_loaded=1,
                chunks_created=len(chunks),
                embeddings_generated=len(embeddings),
                processing_time=processing_time,
                source_size=source_size,
                checksum=checksum,
                created_at=datetime.now().isoformat(),
                success=True,
                sample_chunks=chunks[:3] if chunks else []
            )
            
        except Exception as e:
            logger.error(f"Document loading failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DocumentLoadResponse(
                load_id=load_id,
                collection_name=request.collection_name,
                documents_loaded=0,
                chunks_created=0,
                embeddings_generated=0,
                processing_time=processing_time,
                created_at=datetime.now().isoformat(),
                success=False,
                error=str(e)
            )
    
    async def _get_content_from_source(self, request: DocumentLoadRequest) -> tuple[str, int]:
        """Extract content from various sources"""
        
        if request.source_type == "text" and request.content:
            return request.content, len(request.content)
        
        elif request.source_type == "file" and request.source_path:
            return await self._load_from_file(request.source_path, request.encoding)
        
        elif request.source_type == "url" and request.source_path:
            return await self._load_from_url(request.source_path)
        
        elif request.source_type == "web" and request.source_path:
            # Use web scraper tool if available
            return await self._load_from_web(request.source_path)
        
        else:
            raise ValueError(f"Invalid source configuration: {request.source_type}")
    
    async def _load_from_file(self, file_path: str, encoding: str) -> tuple[str, int]:
        """Load content from a file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() == '.txt':
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
        
        elif path.suffix.lower() == '.json':
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                data = json.loads(await f.read())
                content = json.dumps(data, indent=2)
        
        elif path.suffix.lower() in ['.md', '.markdown']:
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
        
        else:
            # Try to read as text
            try:
                async with aiofiles.open(path, 'r', encoding=encoding) as f:
                    content = await f.read()
            except UnicodeDecodeError:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return content, len(content)
    
    async def _load_from_url(self, url: str) -> tuple[str, int]:
        """Load content from a URL"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: Failed to fetch {url}")
                
                content = await response.text()
                return content, len(content)
    
    async def _load_from_web(self, url: str) -> tuple[str, int]:
        """Load content from web using scraper tool"""
        try:
            # Import here to avoid circular imports
            from .web_scraper import create_web_scraper_tool
            
            settings = get_settings()
            mcp_url = getattr(settings, 'crawl4ai_mcp_url', None)
            api_key = getattr(settings, 'crawl4ai_api_key', None)
            
            if not mcp_url:
                # Fallback to simple URL loading
                return await self._load_from_url(url)
            
            # Use web scraper
            scraper = create_web_scraper_tool(mcp_url, api_key)
            from .web_scraper import WebScrapingRequest
            
            scrape_request = WebScrapingRequest(
                url=url,
                extract_text=True,
                extract_metadata=True,
                remove_ads=True,
                remove_navigation=True
            )
            
            result = await scraper.scrape_url(scrape_request)
            
            if result.success and result.text_content:
                content = f"Title: {result.title or 'Unknown'}\n\n{result.text_content}"
                return content, len(content)
            else:
                raise Exception(f"Web scraping failed: {result.error}")
                
        except Exception as e:
            logger.warning(f"Web scraping failed, falling back to URL: {e}")
            return await self._load_from_url(url)
    
    async def _generate_title(self, content_sample: str) -> str:
        """Generate a title using OpenAI"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate a concise, descriptive title for the following content. Return only the title, no quotes or extra text."},
                    {"role": "user", "content": content_sample}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            return title
            
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return f"Document {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    async def _split_content(self, content: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split content into overlapping chunks"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at word boundaries
            if end < len(content):
                # Look for sentence endings first
                sentence_end = content.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundaries
                    word_end = content.rfind(' ', start, end)
                    if word_end > start + chunk_size // 2:
                        end = word_end
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - chunk_overlap)
        
        return chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            # Process in batches to avoid API limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def _store_document_metadata(
        self,
        document_id: str,
        request: DocumentLoadRequest,
        total_chunks: int,
        content_size: int,
        checksum: str
    ):
        """Store document metadata in BigQuery"""
        
        metadata_json = json.dumps(request.metadata or {})
        
        rows_to_insert = [{
            "document_id": document_id,
            "collection_name": request.collection_name,
            "title": request.title or "Untitled",
            "description": request.description,
            "source_type": request.source_type,
            "source_path": request.source_path,
            "tags": request.tags,
            "total_chunks": total_chunks,
            "content_size": content_size,
            "metadata_json": metadata_json,
            "checksum": checksum,
            "created_at": datetime.now()
        }]
        
        table_id = f"{self.project_id}.{self.dataset_id}.{self.metadata_table}"
        table = self.bigquery_client.get_table(table_id)
        
        errors = self.bigquery_client.insert_rows_json(table, rows_to_insert)
        if errors:
            raise Exception(f"Failed to insert metadata: {errors}")
    
    async def _store_document_vectors(
        self,
        document_id: str,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """Store document vectors in BigQuery"""
        
        rows_to_insert = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            rows_to_insert.append({
                "document_id": document_id,
                "collection_name": collection_name,
                "chunk_index": i,
                "content": chunk,
                "embedding": embedding,
                "created_at": datetime.now()
            })
        
        table_id = f"{self.project_id}.{self.dataset_id}.{self.vector_table}"
        table = self.bigquery_client.get_table(table_id)
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            errors = self.bigquery_client.insert_rows_json(table, batch)
            if errors:
                raise Exception(f"Failed to insert vectors: {errors}")
    
    async def search_documents(self, request: VectorSearchRequest) -> VectorSearchResponse:
        """Perform semantic search across documents"""
        start_time = datetime.now()
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([request.query])
            query_vector = query_embedding[0]
            
            # Build search query
            search_query = self._build_search_query(request, query_vector)
            
            # Execute search
            job = self.bigquery_client.query(search_query)
            results = job.result()
            
            # Process results
            search_results = []
            collections_searched = set()
            
            for row in results:
                collections_searched.add(row.collection_name)
                
                search_results.append(SearchResult(
                    document_id=row.document_id,
                    collection_name=row.collection_name,
                    title=row.title,
                    content=row.content,
                    similarity_score=float(row.similarity_score),
                    metadata=json.loads(row.metadata_json) if row.metadata_json else {},
                    tags=list(row.tags) if row.tags else [],
                    created_at=row.created_at.isoformat(),
                    source_path=row.source_path
                ))
            
            # Apply reranking if requested
            if request.rerank and len(search_results) > 1:
                search_results = await self._rerank_results(request.query, search_results)
            
            search_time = (datetime.now() - start_time).total_seconds()
            
            return VectorSearchResponse(
                query=request.query,
                results=search_results,
                total_results=len(search_results),
                search_time=search_time,
                collections_searched=list(collections_searched),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            search_time = (datetime.now() - start_time).total_seconds()
            
            return VectorSearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                search_time=search_time,
                collections_searched=[],
                success=False,
                error=str(e)
            )
    
    def _build_search_query(self, request: VectorSearchRequest, query_vector: List[float]) -> str:
        """Build BigQuery vector search query"""
        
        # Convert query vector to string format for BigQuery
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"
        
        # Base query with vector similarity
        base_query = f"""
        WITH search_results AS (
            SELECT 
                v.document_id,
                v.collection_name,
                v.content,
                m.title,
                m.source_path,
                m.tags,
                m.metadata_json,
                m.created_at,
                ML.DISTANCE(v.embedding, {vector_str}, 'COSINE') as distance,
                (1 - ML.DISTANCE(v.embedding, {vector_str}, 'COSINE')) as similarity_score
            FROM `{self.project_id}.{self.dataset_id}.{self.vector_table}` v
            JOIN `{self.project_id}.{self.dataset_id}.{self.metadata_table}` m
                ON v.document_id = m.document_id
            WHERE (1 - ML.DISTANCE(v.embedding, {vector_str}, 'COSINE')) >= {request.similarity_threshold}
        """
        
        # Add collection filter
        if request.collection_name:
            base_query += f" AND v.collection_name = '{request.collection_name}'"
        
        # Add tags filter
        if request.tags_filter:
            tags_condition = " OR ".join([f"'{tag}' IN UNNEST(m.tags)" for tag in request.tags_filter])
            base_query += f" AND ({tags_condition})"
        
        # Add date range filter
        if request.date_range:
            if 'start' in request.date_range:
                base_query += f" AND m.created_at >= '{request.date_range['start']}'"
            if 'end' in request.date_range:
                base_query += f" AND m.created_at <= '{request.date_range['end']}'"
        
        # Complete query with ordering and limit
        base_query += f"""
        )
        SELECT *
        FROM search_results
        ORDER BY similarity_score DESC
        LIMIT {request.limit}
        """
        
        return base_query
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Rerank results using cross-encoder or similar technique"""
        try:
            # Simple reranking using content length and keyword matching
            # In production, you might use a cross-encoder model
            
            query_lower = query.lower()
            query_words = set(re.findall(r'\w+', query_lower))
            
            def rerank_score(result: SearchResult) -> float:
                content_lower = result.content.lower()
                content_words = set(re.findall(r'\w+', content_lower))
                
                # Keyword overlap
                keyword_overlap = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
                
                # Content quality (prefer longer, more substantial content)
                content_quality = min(len(result.content) / 1000, 1.0)
                
                # Combine with original similarity
                return (result.similarity_score * 0.7) + (keyword_overlap * 0.2) + (content_quality * 0.1)
            
            # Rerank results
            results.sort(key=rerank_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return results
    
    async def list_collections(self) -> Dict[str, Any]:
        """List all available collections"""
        return {
            "success": True,
            "collections": self.collections,
            "total_collections": len(self.collections)
        }
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a collection"""
        try:
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            # Get sample documents
            query = f"""
            SELECT title, description, tags, created_at
            FROM `{self.project_id}.{self.dataset_id}.{self.metadata_table}`
            WHERE collection_name = '{collection_name}'
            ORDER BY created_at DESC
            LIMIT 5
            """
            
            job = self.bigquery_client.query(query)
            results = job.result()
            
            sample_docs = []
            for row in results:
                sample_docs.append({
                    "title": row.title,
                    "description": row.description,
                    "tags": list(row.tags) if row.tags else [],
                    "created_at": row.created_at.isoformat()
                })
            
            collection_info = self.collections[collection_name].copy()
            collection_info["sample_documents"] = sample_docs
            
            return {
                "success": True,
                "collection": collection_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for LangSwarm integration"""
        return {
            "name": self.name,
            "description": self.description,
            "functions": [
                {
                    "name": "load_document",
                    "description": "Load a document into vector search for semantic retrieval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source_type": {
                                "type": "string",
                                "enum": ["file", "url", "text", "web"],
                                "description": "Type of data source"
                            },
                            "source_path": {
                                "type": "string",
                                "description": "Path or URL to data source"
                            },
                            "content": {
                                "type": "string",
                                "description": "Direct text content to load"
                            },
                            "collection_name": {
                                "type": "string",
                                "description": "Collection name for organizing documents"
                            },
                            "title": {
                                "type": "string",
                                "description": "Document title"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorizing documents"
                            }
                        },
                        "required": ["source_type", "collection_name"]
                    }
                },
                {
                    "name": "search_documents",
                    "description": "Search documents using natural language queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query"
                            },
                            "collection_name": {
                                "type": "string",
                                "description": "Specific collection to search (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum number of results"
                            },
                            "similarity_threshold": {
                                "type": "number",
                                "default": 0.7,
                                "description": "Minimum similarity score (0-1)"
                            },
                            "tags_filter": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by document tags"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "list_collections",
                    "description": "List all available document collections",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    async def call_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """LangSwarm tool call interface"""
        try:
            if function_name == "load_document":
                request = DocumentLoadRequest(**arguments)
                result = await self.load_document(request)
                
                return {
                    "success": result.success,
                    "content": {
                        "load_id": result.load_id,
                        "collection_name": result.collection_name,
                        "documents_loaded": result.documents_loaded,
                        "chunks_created": result.chunks_created,
                        "embeddings_generated": result.embeddings_generated,
                        "processing_time": result.processing_time,
                        "sample_chunks": result.sample_chunks
                    },
                    "error": result.error
                }
            
            elif function_name == "search_documents":
                request = VectorSearchRequest(**arguments)
                result = await self.search_documents(request)
                
                return {
                    "success": result.success,
                    "content": {
                        "query": result.query,
                        "results": [r.dict() for r in result.results],
                        "total_results": result.total_results,
                        "search_time": result.search_time,
                        "collections_searched": result.collections_searched
                    },
                    "error": result.error
                }
            
            elif function_name == "list_collections":
                return await self.list_collections()
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}",
                    "content": None
                }
                
        except Exception as e:
            logger.error(f"Vector search RAG tool call error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }


def create_vector_search_rag_tool(project_id: str, dataset_id: str, embedding_model: str = "text-embedding-3-small") -> VectorSearchRAGTool:
    """Factory function to create vector search RAG tool"""
    return VectorSearchRAGTool(project_id, dataset_id, embedding_model)


# Tool registration for LangSwarm
def get_vector_search_rag_tool_config() -> Dict[str, Any]:
    """Get vector search RAG tool configuration for LangSwarm"""
    settings = get_settings()
    
    # Get configuration from environment
    project_id = getattr(settings, 'google_cloud_project', None)
    dataset_id = getattr(settings, 'bigquery_dataset_id', None)
    embedding_model = getattr(settings, 'embedding_model', 'text-embedding-3-small')
    
    if not project_id or not dataset_id:
        logger.warning("BigQuery configuration not complete. Vector search RAG tool will not be available.")
        return None
    
    return {
        "type": "local_mcp",
        "name": "vector_search_rag",
        "description": "Load documents and perform semantic search using BigQuery Vector Search",
        "config": {
            "project_id": project_id,
            "dataset_id": dataset_id,
            "embedding_model": embedding_model,
            "auto_initialize": True
        }
    }
