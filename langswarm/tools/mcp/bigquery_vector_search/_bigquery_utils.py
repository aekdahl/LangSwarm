"""
Shared BigQuery utilities for vector search operations.

This module contains common patterns and utilities that can be reused
across BigQuery-based tools and reduce code duplication.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound as BQNotFound

logger = logging.getLogger(__name__)

class BigQueryManager:
    """Centralized BigQuery client and common operations manager"""
    
    def __init__(self, project_id: str = None, location: str = "EU"):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self.project_id:
            raise ValueError("project_id is required or GOOGLE_CLOUD_PROJECT environment variable must be set")
        
        self.location = location or os.getenv('BIGQUERY_LOCATION', 'EU')
        self._client = None
    
    @property
    def client(self) -> bigquery.Client:
        """Lazy-loaded BigQuery client"""
        if self._client is None:
            self._client = bigquery.Client(project=self.project_id, location=self.location)
        return self._client
    
    def build_similarity_query(
        self,
        dataset_id: str,
        table_name: str,
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> str:
        """Build optimized similarity search SQL query"""
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        return f"""
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
            FROM `{self.project_id}.{dataset_id}.{table_name}`
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
        WHERE similarity >= {similarity_threshold}
        ORDER BY similarity DESC
        LIMIT {limit}
        """
    
    def execute_similarity_search(
        self,
        dataset_id: str,
        table_name: str,
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Execute similarity search and return formatted results"""
        
        # 🔍 DEBUG: Log BigQuery execution details
        print(f"🔍 BigQuery DEBUG: Starting similarity search")
        print(f"  Project: {self.project_id}")
        print(f"  Dataset: {dataset_id}")
        print(f"  Table: {table_name}")
        print(f"  Embedding dimensions: {len(query_embedding)}")
        print(f"  Similarity threshold: {similarity_threshold}")
        print(f"  Limit: {limit}")
        
        query = self.build_similarity_query(
            dataset_id, table_name, query_embedding, similarity_threshold, limit
        )
        
        # 🔍 DEBUG: Log the exact SQL query
        print(f"🔍 BigQuery SQL Query (first 300 chars):")
        print(f"  {query[:300]}...")
        
        print(f"🔍 BigQuery: Executing query...")
        query_job = self.client.query(query)
        
        # 🔍 DEBUG: Log query job details
        print(f"🔍 BigQuery Job: {query_job.job_id}")
        print(f"🔍 BigQuery State: {query_job.state}")
        
        results = list(query_job.result())
        
        # 🔍 DEBUG: Log raw BigQuery response
        print(f"🔍 BigQuery RAW RESPONSE:")
        print(f"  Total rows returned: {len(results)}")
        print(f"  Job bytes processed: {query_job.total_bytes_processed}")
        print(f"  Job cache hit: {query_job.cache_hit}")
        
        if results:
            print(f"  First row data:")
            first_row = results[0]
            print(f"    document_id: {first_row.document_id}")
            print(f"    similarity: {first_row.similarity}")
            print(f"    content preview: {first_row.content[:50]}...")
        else:
            print(f"  ❌ NO ROWS RETURNED FROM BIGQUERY!")
            
            # 🔍 DEBUG: Additional diagnostic info
            print(f"🔍 BigQuery DIAGNOSTICS:")
            print(f"  Query job errors: {query_job.errors}")
            print(f"  Query job state: {query_job.state}")
            print(f"  Query job ended: {query_job.ended}")
            
            # Check if the table exists and has data
            try:
                table_ref = self.client.dataset(dataset_id).table(table_name)
                table = self.client.get_table(table_ref)
                print(f"  Table exists: ✅ with {table.num_rows} total rows")
                
                # Try a simple count query
                count_query = f"SELECT COUNT(*) as total FROM `{self.project_id}.{dataset_id}.{table_name}`"
                count_job = self.client.query(count_query)
                count_result = list(count_job.result())
                total_count = count_result[0].total if count_result else 0
                print(f"  Table accessible: ✅ {total_count} rows via COUNT query")
                
            except Exception as table_error:
                print(f"  Table access error: {table_error}")
        
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
            
            # Parse metadata safely
            if row.metadata:
                try:
                    result["metadata"] = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                except (json.JSONDecodeError, TypeError):
                    result["metadata"] = row.metadata
            
            formatted_results.append(result)
        
        print(f"🔍 BigQuery FINAL: Returning {len(formatted_results)} formatted results")
        return formatted_results
    
    def get_document_by_id(
        self,
        dataset_id: str,
        table_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID"""
        
        query = f"""
        SELECT 
            document_id,
            content,
            url,
            title,
            metadata,
            created_at
        FROM `{self.project_id}.{dataset_id}.{table_name}`
        WHERE document_id = @document_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", document_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return None
        
        row = results[0]
        result = {
            "document_id": row.document_id,
            "content": row.content,
            "url": row.url,
            "title": row.title,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        
        # Parse metadata safely
        if row.metadata:
            try:
                result["metadata"] = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
            except (json.JSONDecodeError, TypeError):
                result["metadata"] = row.metadata
        
        return result
    
    def list_embedding_datasets(self, pattern: str = None) -> List[Dict[str, Any]]:
        """List datasets that contain tables with embedding columns"""
        
        datasets = []
        for dataset in self.client.list_datasets():
            dataset_id = dataset.dataset_id
            
            # Apply pattern filter if provided
            if pattern and pattern.lower() not in dataset_id.lower():
                continue
            
            # Check for tables with embeddings
            tables = []
            try:
                for table in self.client.list_tables(dataset.reference):
                    # Check if table has embedding column
                    table_ref = self.client.get_table(table.reference)
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
                    "location": getattr(dataset, 'location', 'unknown')
                })
        
        return datasets
    
    def get_table_info(self, dataset_id: str, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        
        table_ref = self.client.dataset(dataset_id).table(table_name)
        table = self.client.get_table(table_ref)
        
        # Get sample of recent documents
        sample_query = f"""
        SELECT 
            document_id,
            title,
            url,
            CHAR_LENGTH(content) as content_length,
            created_at
        FROM `{self.project_id}.{dataset_id}.{table_name}`
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        query_job = self.client.query(sample_query)
        sample_docs = [dict(row) for row in query_job.result()]
        
        # Format sample docs
        for doc in sample_docs:
            if doc.get('created_at'):
                doc['created_at'] = doc['created_at'].isoformat()
        
        return {
            "dataset_id": dataset_id,
            "table_name": table_name,
            "total_rows": table.num_rows,
            "size_bytes": table.num_bytes,
            "created": table.created.isoformat() if table.created else None,
            "modified": table.modified.isoformat() if table.modified else None,
            "table_schema": [{"name": field.name, "type": field.field_type} for field in table.schema],
            "sample_documents": sample_docs
        }

class EmbeddingHelper:
    """Helper utilities for embedding operations"""
    
    @staticmethod
    def validate_embedding(embedding: List[float], expected_dim: int = None) -> bool:
        """Validate embedding format and dimensions"""
        if not isinstance(embedding, list):
            return False
        
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        
        if expected_dim and len(embedding) != expected_dim:
            return False
        
        return True
    
    @staticmethod
    def normalize_embedding(embedding: List[float]) -> List[float]:
        """Normalize embedding vector (L2 normalization)"""
        import math
        magnitude = math.sqrt(sum(x * x for x in embedding))
        return [x / magnitude for x in embedding] if magnitude > 0 else embedding

class QueryBuilder:
    """Advanced query builder for complex BigQuery operations"""
    
    @staticmethod
    def build_multi_table_search(
        project_id: str,
        tables: List[Dict[str, str]],  # [{"dataset": "ds1", "table": "t1"}, ...]
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> str:
        """Build query that searches across multiple tables"""
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Build UNION ALL for multiple tables
        union_parts = []
        for table_info in tables:
            dataset_id = table_info["dataset"]
            table_name = table_info["table"]
            
            union_parts.append(f"""
            SELECT 
                '{dataset_id}.{table_name}' as source_table,
                document_id,
                content,
                url,
                title,
                metadata,
                created_at,
                embedding
            FROM `{project_id}.{dataset_id}.{table_name}`
            WHERE embedding IS NOT NULL
            """)
        
        union_query = " UNION ALL ".join(union_parts)
        
        return f"""
        WITH query_embedding AS (
            SELECT {embedding_str} as query_vector
        ),
        all_documents AS (
            {union_query}
        ),
        similarities AS (
            SELECT 
                source_table,
                document_id,
                content,
                url,
                title,
                metadata,
                created_at,
                (1 - ML.DISTANCE(embedding, (SELECT query_vector FROM query_embedding), 'COSINE')) as similarity
            FROM all_documents
        )
        SELECT 
            source_table,
            document_id,
            content,
            url,
            title,
            metadata,
            created_at,
            similarity
        FROM similarities
        WHERE similarity >= {similarity_threshold}
        ORDER BY similarity DESC
        LIMIT {limit}
        """
    
    @staticmethod
    def build_filtered_search(
        project_id: str,
        dataset_id: str,
        table_name: str,
        query_embedding: List[float],
        filters: Dict[str, Any] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> str:
        """Build similarity search with additional filters"""
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Build WHERE conditions
        where_conditions = ["embedding IS NOT NULL"]
        
        if filters:
            for field, value in filters.items():
                if isinstance(value, str):
                    where_conditions.append(f"{field} = '{value}'")
                elif isinstance(value, (int, float)):
                    where_conditions.append(f"{field} = {value}")
                elif isinstance(value, list):
                    # Support for IN queries
                    if all(isinstance(v, str) for v in value):
                        value_list = "'" + "','".join(value) + "'"
                        where_conditions.append(f"{field} IN ({value_list})")
        
        where_clause = " AND ".join(where_conditions)
        
        return f"""
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
                (1 - ML.DISTANCE(embedding, (SELECT query_vector FROM query_embedding), 'COSINE')) as similarity
            FROM `{project_id}.{dataset_id}.{table_name}`
            WHERE {where_clause}
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
        WHERE similarity >= {similarity_threshold}
        ORDER BY similarity DESC
        LIMIT {limit}
        """
