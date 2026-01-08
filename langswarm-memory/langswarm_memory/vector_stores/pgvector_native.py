"""
LangSwarm V2 Native PGVector Store

PostgreSQL-based vector storage using the pgvector extension.
Scalable, production-grade vector storage with full ACID compliance.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to import asyncpg, but allow running without it (will raise on usage)
try:
    import asyncpg
    from asyncpg import Connection
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    Connection = Any

from .interfaces import (
    IVectorStore, VectorDocument, VectorQuery, VectorResult, 
    VectorStoreConfig, VectorStoreError, ConnectionError, QueryError
)

logger = logging.getLogger(__name__)


class NativePGVectorStore(IVectorStore):
    """
    Native PostgreSQL (pgvector) vector store implementation.
    
    Uses the official pgvector extension for efficient similarity search.
    Requires PostgreSQL 9.6+ with pgvector installed.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize PGVector store.
        
        Args:
            config: Vector store configuration
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is not available. Install with: pip install asyncpg")
            
        self.config = config
        
        # Extract connection details
        params = config.connection_params
        self.dsn = params.get("dsn")
        self.host = params.get("host", "localhost")
        self.port = params.get("port", 5432)
        self.database = params.get("database", "langswarm")
        self.user = params.get("user", "postgres")
        self.password = params.get("password", "postgres")
        
        self.table_name = params.get("table_name", "vectors")
        self.pool_min_size = params.get("pool_min_size", 1)
        self.pool_max_size = params.get("pool_max_size", 10)
        
        self._pool = None
        self._connected = False
        
        logger.debug(f"Initialized PGVector store: {self.host}:{self.port}/{self.database}")
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL and Initialize Schema"""
        try:
            # Create connection pool
            if self.dsn:
                self._pool = await asyncpg.create_pool(
                    dsn=self.dsn,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size
                )
            else:
                self._pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size
                )
            
            # Initialize schema
            async with self._pool.acquire() as conn:
                await self._init_schema(conn)
            
            self._connected = True
            logger.info(f"Connected to PGVector store: {self.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e
            
    async def _init_schema(self, conn: Connection):
        """Initialize pgvector extension and table"""
        # Enable pgvector extension
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception as e:
            logger.error("Failed to enable pgvector extension. Ensure it is installed on the server.")
            raise VectorStoreError(f"pgvector extension init failed: {e}") from e
            
        # Create vectors table
        # Note: We use the defined embedding dimension for the vector column
        dim = self.config.embedding_dimension
        
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector({dim}),
                metadata JSONB,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for cosine similarity (using HNSW for performance or IVFFlat)
        # We'll default to HNSW (Hierarchical Navigable Small Worlds) if available (pgvector 0.5+)
        # Falling back to IVFFlat or none if it fails would be complex, so we try HNSW first.
        # Note: <-> is Euclidean, <=> is Cosine, <#> is Inner Product
        
        index_method = self.config.connection_params.get("index_method", "hnsw")
        metric_op = "vector_cosine_ops" # Cosine
        
        if self.config.metric == "euclidean":
            metric_op = "vector_l2_ops"
        elif self.config.metric == "dotproduct":
            metric_op = "vector_ip_ops"
            
        # Only create index if table is new-ish or we want to force it.
        # Actually, creating index IF NOT EXISTS is tricky in PG syntax for custom ops.
        # We'll SKIP automatic efficient index creation for now to avoid complexity with 
        # existing data vs empty tables, and let the user manage indexes if needed, 
        # OR we try a safe "CREATE INDEX IF NOT EXISTS"
        
        index_name = f"idx_{self.table_name}_embedding_{index_method}"
        try:
           await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {self.table_name} 
                USING {index_method} (embedding {metric_op})
            """)
        except Exception as e:
            logger.warning(f"Could not create vector index (might be insufficient data for IVFFlat or unsupported method): {e}")

    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL"""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
            
            self._connected = False
            logger.debug("Disconnected from PGVector")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from PGVector: {e}")
            return False

    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create a new table/partition equivalent"""
        # For PG, we treat 'create_index' as creating a new table if needed,
        # but typically this is handled in connect/init. 
        # We'll forward to a table creation helper similar to init.
        # This might be used for namespacing.
        
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                 await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {name} (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector({dimension}),
                        metadata JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            return True
        except Exception as e:
            logger.error(f"Failed to create table usage: {e}")
            return False

    async def delete_index(self, name: str) -> bool:
        """Drop usage table"""
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                await conn.execute(f"DROP TABLE IF EXISTS {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop table {name}: {e}")
            return False

    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents"""
        if not documents:
            return True
            
        try:
            if not self._connected:
                await self.connect()

            async with self._pool.acquire() as conn:
                # Prepare data
                records = []
                for doc in documents:
                    records.append((
                        doc.id,
                        doc.content,
                        doc.embedding, # asyncpg handles list -> vector
                        json.dumps(doc.metadata) if doc.metadata else "{}",
                        doc.timestamp or datetime.utcnow()
                    ))
                
                # Execute upsert
                await conn.executemany(f"""
                    INSERT INTO {self.table_name} (id, content, embedding, metadata, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                """, records)
                
            logger.debug(f"Upserted {len(documents)} documents to PGVector")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert to PGVector: {e}")
            return False

    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query similar vectors"""
        try:
            if not self._connected:
                await self.connect()
                
            # Operator mapping
            # <=> cosine distance
            # <-> euclidean distance
            # <#> negative inner product
            op = "<=>"
            if self.config.metric == "euclidean":
                op = "<->"
            elif self.config.metric == "dotproduct":
                op = "<#>"
                
            async with self._pool.acquire() as conn:
                # Build filter clause
                where_clauses = ["1=1"]
                params = [json.dumps(query.embedding)] # $1
                param_idx = 2
                
                if query.filters:
                    for k, v in query.filters.items():
                        # Simple equality check on top-level keys
                        # Postgres JSONB containment: metadata @> '{"k": "v"}'
                        where_clauses.append(f"metadata @> ${param_idx}::jsonb")
                        params.append(json.dumps({k: v}))
                        param_idx += 1
                
                where_sql = " AND ".join(where_clauses)
                
                # Query
                # We return 1 - distance for cosine similarity score approximation
                # pgvector returns distance, we want similarity
                
                sql = f"""
                    SELECT id, content, metadata, 1 - (embedding {op} $1) as similarity
                    FROM {self.table_name}
                    WHERE {where_sql}
                    ORDER BY embedding {op} $1
                    LIMIT ${param_idx}
                """
                params.append(query.top_k)
                
                rows = await conn.fetch(sql, *params)
                
                results = []
                for row in rows:
                    score = float(row['similarity'])
                    if query.min_score and score < query.min_score:
                        continue
                        
                    results.append(VectorResult(
                        id=row['id'],
                        content=row['content'] if query.include_content else "",
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        score=score
                    ))
                    
                return results

        except Exception as e:
            logger.error(f"Failed to query PGVector: {e}")
            raise QueryError(f"PGVector query failed: {e}") from e

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID"""
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(f"""
                    SELECT id, content, embedding, metadata, timestamp
                    FROM {self.table_name}
                    WHERE id = $1
                """, doc_id)
                
                if not row:
                    return None
                    
                # Convert embedding (str representation or list) to list
                embedding_val = row['embedding']
                if isinstance(embedding_val, str):
                    # parse string "[1,2,3]"
                    embedding = json.loads(embedding_val)
                else:
                    embedding = list(embedding_val)

                return VectorDocument(
                    id=row['id'],
                    content=row['content'],
                    embedding=embedding,
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    timestamp=row['timestamp']
                )
                
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by ID"""
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                await conn.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE id = ANY($1)
                """, doc_ids)
                
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs"""
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                where_clauses = ["1=1"]
                params = []
                param_idx = 1
                
                if filters:
                    for k, v in filters.items():
                        where_clauses.append(f"metadata @> ${param_idx}::jsonb")
                        params.append(json.dumps({k: v}))
                        param_idx += 1
                
                sql = f"""
                    SELECT id FROM {self.table_name}
                    WHERE {" AND ".join(where_clauses)}
                    ORDER BY created_at DESC
                    LIMIT ${param_idx}
                """
                params.append(limit)
                
                rows = await conn.fetch(sql, *params)
                return [r['id'] for r in rows]
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        try:
            if not self._connected:
                await self.connect()
                
            async with self._pool.acquire() as conn:
                count_row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.table_name}")
                size_row = await conn.fetchrow(f"SELECT pg_total_relation_size($1)", self.table_name)
                
                count = count_row[0] if count_row else 0
                size = size_row[0] if size_row else 0
                
                return {
                    "total_vectors": count,
                    "table_size_bytes": size,
                    "table_size_mb": round(size / (1024*1024), 2),
                    "store_type": "postgres",
                    "table_name": self.table_name
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> bool:
        """Check connection"""
        try:
            if not self._connected:
                return False
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
