"""
LangSwarm V2 Native SQLite Vector Store

SQLite-based vector storage with similarity search using numpy operations.
Lightweight alternative for development and small-scale deployments.
"""

import sqlite3
import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .interfaces import (
    IVectorStore, VectorDocument, VectorQuery, VectorResult, 
    VectorStoreConfig, VectorStoreError, ConnectionError, QueryError
)


logger = logging.getLogger(__name__)


class NativeSQLiteStore(IVectorStore):
    """
    Native SQLite vector store implementation.
    
    Provides vector storage and similarity search using SQLite with numpy
    operations for similarity calculations. Ideal for development and
    small-scale deployments.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize SQLite vector store.
        
        Args:
            config: Vector store configuration with SQLite parameters
        """
        self.config = config
        self.db_path = config.connection_params.get("db_path", "langswarm_vectors.db")
        self.table_name = config.connection_params.get("table_name", "vectors")
        self._connected = False
        
        # Thread pool for database operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sqlite_vector")
        
        logger.debug(f"Initialized SQLite vector store: {self.db_path}")
    
    async def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            # Create database directory if needed
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize database in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._init_database
            )
            
            self._connected = True
            logger.info(f"Connected to SQLite vector store: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise ConnectionError(f"Failed to connect to SQLite: {e}") from e
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dimension INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp ON {self.table_name} (timestamp)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_dimension ON {self.table_name} (dimension)")
            
            conn.commit()
    
    async def disconnect(self) -> bool:
        """Disconnect from SQLite"""
        try:
            if self._executor:
                self._executor.shutdown(wait=True)
            self._connected = False
            logger.debug("Disconnected from SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from SQLite: {e}")
            return False
    
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create SQLite table (index)"""
        try:
            if not self._connected:
                await self.connect()
            
            # Create table with specified name
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._create_table, name, dimension
            )
            
            logger.info(f"Created SQLite table: {name} (dimension: {dimension})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create SQLite table {name}: {e}")
            return False
    
    def _create_table(self, name: str, dimension: int):
        """Create table synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dimension INTEGER DEFAULT {dimension},
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{name}_timestamp ON {name} (timestamp)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{name}_dimension ON {name} (dimension)")
            
            conn.commit()
    
    async def delete_index(self, name: str) -> bool:
        """Delete SQLite table (index)"""
        try:
            if not self._connected:
                await self.connect()
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._drop_table, name
            )
            
            logger.info(f"Deleted SQLite table: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete SQLite table {name}: {e}")
            return False
    
    def _drop_table(self, name: str):
        """Drop table synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DROP TABLE IF EXISTS {name}")
            conn.commit()
    
    async def upsert_documents(self, documents: List[VectorDocument]) -> bool:
        """Insert or update documents in SQLite"""
        try:
            if not self._connected:
                await self.connect()
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._upsert_documents_sync, documents
            )
            
            logger.debug(f"Upserted {len(documents)} documents to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert documents to SQLite: {e}")
            return False
    
    def _upsert_documents_sync(self, documents: List[VectorDocument]):
        """Upsert documents synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            for doc in documents:
                # Convert embedding to bytes
                embedding_bytes = np.array(doc.embedding, dtype=np.float32).tobytes()
                metadata_json = json.dumps(doc.metadata) if doc.metadata else "{}"
                
                conn.execute(f"""
                    INSERT OR REPLACE INTO {self.table_name} 
                    (id, content, embedding, metadata, timestamp, dimension)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc.id,
                    doc.content,
                    embedding_bytes,
                    metadata_json,
                    doc.timestamp.isoformat() if doc.timestamp else datetime.utcnow().isoformat(),
                    len(doc.embedding)
                ))
            
            conn.commit()
    
    async def query(self, query: VectorQuery) -> List[VectorResult]:
        """Query SQLite for similar vectors using numpy similarity"""
        try:
            if not self._connected:
                await self.connect()
            
            results = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._query_sync, query
            )
            
            logger.debug(f"SQLite query returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query SQLite: {e}")
            raise QueryError(f"Failed to query SQLite: {e}") from e
    
    def _query_sync(self, query: VectorQuery) -> List[VectorResult]:
        """Query synchronously with numpy similarity calculation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build WHERE clause for metadata filters
            where_clause = ""
            params = []
            
            if query.filters:
                conditions = []
                for field, value in query.filters.items():
                    conditions.append(f"json_extract(metadata, '$.{field}') = ?")
                    params.append(value)
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            # Get all vectors (with filtering)
            sql = f"""
                SELECT id, content, embedding, metadata, timestamp 
                FROM {self.table_name} 
                {where_clause}
            """
            
            rows = conn.execute(sql, params).fetchall()
            
            if not rows:
                return []
            
            # Calculate similarities using numpy
            query_vector = np.array(query.embedding, dtype=np.float32)
            similarities = []
            
            for row in rows:
                # Convert embedding from bytes back to numpy array
                stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                
                # Calculate cosine similarity
                dot_product = np.dot(query_vector, stored_embedding)
                norm_query = np.linalg.norm(query_vector)
                norm_stored = np.linalg.norm(stored_embedding)
                
                if norm_query == 0 or norm_stored == 0:
                    similarity = 0.0
                else:
                    similarity = dot_product / (norm_query * norm_stored)
                
                similarities.append((similarity, row))
            
            # Sort by similarity (descending) and take top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_results = similarities[:query.top_k]
            
            # Convert to VectorResult objects
            results = []
            for similarity, row in top_results:
                # Filter by minimum score if specified
                if query.min_score and similarity < query.min_score:
                    continue
                
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                content = row['content'] if query.include_content else ""
                
                result = VectorResult(
                    id=row['id'],
                    content=content,
                    metadata=metadata,
                    score=float(similarity)
                )
                results.append(result)
            
            return results
    
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID from SQLite"""
        try:
            if not self._connected:
                await self.connect()
            
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._get_document_sync, doc_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from SQLite: {e}")
            return None
    
    def _get_document_sync(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            row = conn.execute(f"""
                SELECT id, content, embedding, metadata, timestamp
                FROM {self.table_name}
                WHERE id = ?
            """, (doc_id,)).fetchone()
            
            if not row:
                return None
            
            # Convert embedding from bytes
            embedding = np.frombuffer(row['embedding'], dtype=np.float32).tolist()
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            timestamp = datetime.fromisoformat(row['timestamp'])
            
            return VectorDocument(
                id=row['id'],
                content=row['content'],
                embedding=embedding,
                metadata=metadata,
                timestamp=timestamp
            )
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs from SQLite"""
        try:
            if not self._connected:
                await self.connect()
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._delete_documents_sync, doc_ids
            )
            
            logger.debug(f"Deleted {len(doc_ids)} documents from SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from SQLite: {e}")
            return False
    
    def _delete_documents_sync(self, doc_ids: List[str]):
        """Delete documents synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ",".join(["?" for _ in doc_ids])
            conn.execute(f"DELETE FROM {self.table_name} WHERE id IN ({placeholders})", doc_ids)
            conn.commit()
    
    async def list_documents(self, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """List document IDs from SQLite"""
        try:
            if not self._connected:
                await self.connect()
            
            doc_ids = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._list_documents_sync, limit, filters
            )
            
            logger.debug(f"Listed {len(doc_ids)} documents from SQLite")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to list documents from SQLite: {e}")
            return []
    
    def _list_documents_sync(self, limit: int, filters: Optional[Dict[str, Any]]) -> List[str]:
        """List documents synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            # Build WHERE clause for filters
            where_clause = ""
            params = []
            
            if filters:
                conditions = []
                for field, value in filters.items():
                    conditions.append(f"json_extract(metadata, '$.{field}') = ?")
                    params.append(value)
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            # Get document IDs
            sql = f"""
                SELECT id FROM {self.table_name} 
                {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            return [row[0] for row in rows]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get SQLite database statistics"""
        try:
            if not self._connected:
                await self.connect()
            
            stats = await asyncio.get_event_loop().run_in_executor(
                self._executor, self._get_stats_sync
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get SQLite stats: {e}")
            return {"error": str(e)}
    
    def _get_stats_sync(self) -> Dict[str, Any]:
        """Get stats synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            # Get table stats
            result = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()
            total_vectors = result[0] if result else 0
            
            # Get average dimension
            result = conn.execute(f"SELECT AVG(dimension) FROM {self.table_name}").fetchone()
            avg_dimension = int(result[0]) if result and result[0] else 0
            
            # Get database file size
            db_path = Path(self.db_path)
            file_size = db_path.stat().st_size if db_path.exists() else 0
            
            return {
                "total_vectors": total_vectors,
                "average_dimension": avg_dimension,
                "database_size_bytes": file_size,
                "database_size_mb": round(file_size / (1024 * 1024), 2),
                "store_type": "sqlite",
                "table_name": self.table_name,
                "db_path": str(self.db_path)
            }
    
    async def health_check(self) -> bool:
        """Check SQLite database health"""
        try:
            if not self._connected:
                return False
            
            # Try a simple query
            await self.get_stats()
            return True
            
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False
