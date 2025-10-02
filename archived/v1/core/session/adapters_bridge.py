"""
Adapters Bridge
===============

Bridge adapters that make existing _langswarm adapters compatible 
with the hybrid session management system.

This allows session management to leverage the sophisticated storage
capabilities of ChromaDB, Redis, Elasticsearch, etc. while maintaining
the same interface.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from langswarm.memory.adapters.database_adapter import DatabaseAdapter

logger = logging.getLogger(__name__)


class SessionDatabaseBridge:
    """
    Bridge that makes DatabaseAdapter compatible with session management
    
    This wrapper translates session management operations into 
    database adapter operations, allowing us to use existing
    sophisticated storage backends.
    """
    
    def __init__(self, adapter: DatabaseAdapter):
        """
        Initialize bridge with existing database adapter
        
        Args:
            adapter: Any existing _langswarm DatabaseAdapter
        """
        self.adapter = adapter
        self.logger = logging.getLogger(f"{__name__}.{adapter.__class__.__name__}")
        
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add session documents to storage
        
        Args:
            documents: List of documents with 'key', 'text', and 'metadata' fields
            
        Returns:
            List of document IDs
        """
        try:
            # Convert to adapter format
            adapter_docs = []
            for doc in documents:
                adapter_doc = {
                    "id": doc.get("key", ""),
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {})
                }
                adapter_docs.append(adapter_doc)
            
            # Add to adapter
            return self.adapter.add_documents(adapter_docs)
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query session storage
        
        Args:
            query: Search query
            filters: Query filters
            k: Number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            # Convert filters to adapter format
            adapter_filters = self._convert_filters(filters) if filters else None
            
            # Query adapter
            results = self.adapter.query(
                query=query,
                filters=adapter_filters,
                k=k
            )
            
            # Convert results to expected format
            formatted_results = []
            for result in results:
                formatted_result = {
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0)
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Failed to query: {e}")
            raise
    
    def _convert_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert session management filters to adapter format
        
        Args:
            filters: Session management filters
            
        Returns:
            Adapter-compatible filters
        """
        try:
            # Extract conditions
            conditions = filters.get("conditions", [])
            
            # Convert to adapter format
            adapter_filters = {}
            
            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")
                
                # Simple conversion - can be enhanced based on specific adapter needs
                if operator == "==":
                    adapter_filters[field] = value
                elif operator == "!=":
                    adapter_filters[f"{field}_not"] = value
                elif operator == ">=":
                    adapter_filters[f"{field}_gte"] = value
                elif operator == "<=":
                    adapter_filters[f"{field}_lte"] = value
            
            return adapter_filters
            
        except Exception as e:
            self.logger.warning(f"Filter conversion failed: {e}")
            return {}


class HybridAdapterFactory:
    """
    Factory for creating hybrid-compatible adapters from existing _langswarm adapters
    """
    
    @classmethod
    def create_chromadb_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create ChromaDB adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.chromadb.main import ChromaDBAdapter
            
            # Create ChromaDB adapter with config
            adapter = ChromaDBAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create ChromaDB adapter: {e}")
            return None
    
    @classmethod
    def create_sqlite_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create SQLite adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.sqlite.main import SQLiteAdapter
            
            # Create SQLite adapter with config
            adapter = SQLiteAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create SQLite adapter: {e}")
            return None
    
    @classmethod
    def create_redis_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create Redis adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.redis.main import RedisAdapter
            
            # Create Redis adapter with config
            adapter = RedisAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create Redis adapter: {e}")
            return None
    
    @classmethod
    def create_qdrant_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create Qdrant adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.qdrant.main import QdrantAdapter
            
            # Create Qdrant adapter with config
            adapter = QdrantAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create Qdrant adapter: {e}")
            return None
    
    @classmethod
    def create_elasticsearch_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create Elasticsearch adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.elasticsearch.main import ElasticsearchAdapter
            
            # Create Elasticsearch adapter with config
            adapter = ElasticsearchAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create Elasticsearch adapter: {e}")
            return None
    
    @classmethod
    def create_bigquery_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create BigQuery adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.bigquery.main import BigQueryAdapter
            
            # Create BigQuery adapter with config
            adapter = BigQueryAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create BigQuery adapter: {e}")
            return None
    
    @classmethod
    def create_gcs_adapter(cls, **config) -> Optional[SessionDatabaseBridge]:
        """Create GCS adapter for session management"""
        try:
            from langswarm.memory.adapters._langswarm.gcs.main import GCSAdapter
            
            # Create GCS adapter with config
            adapter = GCSAdapter(**config)
            
            # Wrap in bridge
            return SessionDatabaseBridge(adapter)
            
        except Exception as e:
            logger.error(f"Failed to create GCS adapter: {e}")
            return None
    
    @classmethod
    def create_adapter(cls, adapter_type: str, **config) -> Optional[SessionDatabaseBridge]:
        """
        Create adapter by type
        
        Args:
            adapter_type: Type of adapter to create
            **config: Adapter configuration
            
        Returns:
            SessionDatabaseBridge or None if creation fails
        """
        creator_map = {
            "chromadb": cls.create_chromadb_adapter,
            "sqlite": cls.create_sqlite_adapter,
            "redis": cls.create_redis_adapter,
            "qdrant": cls.create_qdrant_adapter,
            "elasticsearch": cls.create_elasticsearch_adapter,
            "bigquery": cls.create_bigquery_adapter,
            "gcs": cls.create_gcs_adapter
        }
        
        creator = creator_map.get(adapter_type.lower())
        if creator:
            return creator(**config)
        else:
            logger.error(f"Unknown adapter type: {adapter_type}")
            return None


class MockSessionAdapter:
    """
    Mock adapter for testing and development
    
    This provides the same interface as SessionDatabaseBridge
    but stores everything in memory for testing purposes.
    """
    
    def __init__(self, **kwargs):
        self.documents = []
        self.logger = logging.getLogger(f"{__name__}.MockAdapter")
        # Accept any kwargs for compatibility
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to mock storage"""
        ids = []
        for doc in documents:
            doc_id = doc.get("key", f"doc_{len(self.documents)}")
            self.documents.append({
                "id": doc_id,
                "text": doc.get("text", ""),
                "metadata": doc.get("metadata", {}),
                "score": 1.0
            })
            ids.append(doc_id)
        
        self.logger.info(f"Added {len(documents)} documents to mock storage")
        return ids
    
    def query(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """Query mock storage"""
        # Simple text matching for mock
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            text = doc.get("text", "").lower()
            metadata = doc.get("metadata", {})
            
            # Simple text matching
            if query_lower in text:
                # Apply filters if provided
                if filters:
                    conditions = filters.get("conditions", [])
                    match = True
                    
                    for condition in conditions:
                        field = condition.get("field")
                        operator = condition.get("operator")
                        value = condition.get("value")
                        
                        if field in metadata:
                            if operator == "==" and metadata[field] != value:
                                match = False
                                break
                            elif operator == "!=" and metadata[field] == value:
                                match = False
                                break
                    
                    if not match:
                        continue
                
                results.append({
                    "text": doc.get("text", ""),
                    "metadata": metadata,
                    "score": 0.9  # Mock score
                })
                
                if len(results) >= k:
                    break
        
        self.logger.info(f"Mock query '{query}' returned {len(results)} results")
        return results 