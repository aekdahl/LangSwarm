"""
LangSwarm V2 RAG/Memory Tool Adapter

Adapter for RAG/Memory tools to provide V2 interface compatibility.
Converts database adapters and retrievers to unified MCP-style memory tools.
"""

from typing import Any, Dict, List, Optional
import logging

from ..interfaces import ToolType, ToolCapability
from ..base import ToolSchema
from .base import LegacyToolAdapter

logger = logging.getLogger(__name__)


class RAGToolAdapter(LegacyToolAdapter):
    """
    Adapter for RAG/Memory tools to V2 interface.
    
    RAG tools typically have:
    - query(query, filters) method for retrieval
    - add_documents(data) method for storage
    - delete(identifier) method for deletion
    - Database adapter interface
    """
    
    def __init__(self, rag_tool: Any, **kwargs):
        # Determine storage type
        storage_type = self._determine_storage_type(rag_tool)
        
        super().__init__(
            legacy_tool=rag_tool,
            tool_type=ToolType.MEMORY,  # RAG tools are memory tools
            capabilities=[
                ToolCapability.READ,
                ToolCapability.WRITE,
                ToolCapability.EXECUTE,
                ToolCapability.ASYNC
            ],
            **kwargs
        )
        
        self._adapter_type = "rag"
        self._storage_type = storage_type
        
        # Add memory-related tags
        self.add_tag("memory")
        self.add_tag("retrieval")
        self.add_tag("rag")
        self.add_tag(storage_type)
        
        # Add RAG-specific methods
        self._add_rag_methods()
        
        self._logger.info(f"Adapted RAG tool: {self.metadata.id} ({storage_type})")
    
    def _determine_storage_type(self, tool: Any) -> str:
        """Determine the type of storage backend"""
        class_name = tool.__class__.__name__.lower()
        module_name = tool.__class__.__module__.lower()
        
        if 'sqlite' in class_name or 'sqlite' in module_name:
            return "sqlite"
        elif 'redis' in class_name or 'redis' in module_name:
            return "redis"
        elif 'chroma' in class_name or 'chroma' in module_name:
            return "chromadb"
        elif 'milvus' in class_name or 'milvus' in module_name:
            return "milvus"
        elif 'qdrant' in class_name or 'qdrant' in module_name:
            return "qdrant"
        elif 'elasticsearch' in class_name or 'elasticsearch' in module_name:
            return "elasticsearch"
        elif 'bigquery' in class_name or 'bigquery' in module_name:
            return "bigquery"
        elif 'gcs' in class_name or 'gcs' in module_name:
            return "gcs"
        elif 'llamaindex' in class_name or 'llamaindex' in module_name:
            return "llamaindex"
        else:
            return "unknown"
    
    def _add_rag_methods(self):
        """Add RAG-specific method schemas"""
        # Query/retrieval method
        query_schema = ToolSchema(
            name="query",
            description="Query the memory/knowledge base for relevant information",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query text"
                },
                "filters": {
                    "type": "object",
                    "description": "Metadata filters for query refinement",
                    "properties": {
                        "conditions": {
                            "type": "array",
                            "description": "Filter conditions",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string", "description": "Metadata field"},
                                    "operator": {"type": "string", "description": "Comparison operator"},
                                    "value": {"type": "any", "description": "Filter value"}
                                }
                            }
                        },
                        "logic": {
                            "type": "string",
                            "description": "Logic operator (AND/OR)",
                            "enum": ["AND", "OR"],
                            "default": "AND"
                        }
                    }
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            returns={
                "type": "array",
                "description": "Retrieved documents",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Document content"},
                        "metadata": {"type": "object", "description": "Document metadata"},
                        "score": {"type": "number", "description": "Relevance score"}
                    }
                }
            },
            required=["query"],
            examples=[
                {
                    "query": "machine learning algorithms",
                    "filters": {
                        "conditions": [
                            {"field": "category", "operator": "==", "value": "AI"}
                        ],
                        "logic": "AND"
                    },
                    "top_k": 5
                }
            ]
        )
        self._metadata.add_method(query_schema)
        
        # Add documents method
        add_docs_schema = ToolSchema(
            name="add_documents",
            description="Add documents to the memory/knowledge base",
            parameters={
                "documents": {
                    "type": "array",
                    "description": "Documents to add",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Document ID"},
                            "content": {"type": "string", "description": "Document content"},
                            "metadata": {"type": "object", "description": "Document metadata"}
                        },
                        "required": ["content"]
                    }
                }
            },
            returns={
                "type": "object",
                "description": "Operation result",
                "properties": {
                    "success": {"type": "boolean", "description": "Operation success"},
                    "added_count": {"type": "integer", "description": "Number of documents added"},
                    "errors": {"type": "array", "description": "Any errors encountered"}
                }
            },
            required=["documents"],
            examples=[
                {
                    "documents": [
                        {
                            "id": "doc1",
                            "content": "Machine learning is a subset of AI",
                            "metadata": {"category": "AI", "year": 2024}
                        }
                    ]
                }
            ]
        )
        self._metadata.add_method(add_docs_schema)
        
        # Delete documents method
        delete_schema = ToolSchema(
            name="delete",
            description="Delete documents from the memory/knowledge base",
            parameters={
                "document_ids": {
                    "type": "array",
                    "description": "IDs of documents to delete",
                    "items": {"type": "string"}
                },
                "filters": {
                    "type": "object",
                    "description": "Alternatively, delete by metadata filters"
                }
            },
            returns={
                "type": "object",
                "description": "Deletion result",
                "properties": {
                    "success": {"type": "boolean", "description": "Operation success"},
                    "deleted_count": {"type": "integer", "description": "Number of documents deleted"}
                }
            },
            required=[],
            examples=[
                {"document_ids": ["doc1", "doc2"]},
                {"filters": {"conditions": [{"field": "category", "operator": "==", "value": "obsolete"}]}}
            ]
        )
        self._metadata.add_method(delete_schema)
        
        # Capabilities method
        capabilities_schema = ToolSchema(
            name="capabilities",
            description="Get storage backend capabilities",
            parameters={},
            returns={
                "type": "object",
                "description": "Backend capabilities",
                "properties": {
                    "vector_search": {"type": "boolean", "description": "Supports vector search"},
                    "metadata_filtering": {"type": "boolean", "description": "Supports metadata filtering"},
                    "full_text_search": {"type": "boolean", "description": "Supports full-text search"},
                    "batch_operations": {"type": "boolean", "description": "Supports batch operations"}
                }
            },
            required=[]
        )
        self._metadata.add_method(capabilities_schema)
        
        # Statistics method
        stats_schema = ToolSchema(
            name="stats",
            description="Get storage statistics",
            parameters={},
            returns={
                "type": "object",
                "description": "Storage statistics",
                "properties": {
                    "document_count": {"type": "integer", "description": "Total documents"},
                    "storage_size": {"type": "string", "description": "Storage size"},
                    "last_updated": {"type": "string", "description": "Last update timestamp"}
                }
            },
            required=[]
        )
        self._metadata.add_method(stats_schema)
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Execute RAG tool with enhanced parameter handling.
        
        RAG tools typically support multiple calling patterns:
        - Direct method calls (query, add_documents, delete)
        - Action-based calls with 'action' parameter
        """
        try:
            # Handle different input patterns
            if isinstance(input_data, dict):
                action = input_data.get("action", kwargs.get("action", "query"))
                parameters = input_data.get("parameters", input_data)
            elif isinstance(input_data, str):
                # String input is treated as a query
                action = "query"
                parameters = {"query": input_data}
            else:
                action = kwargs.get("action", "query")
                parameters = kwargs
            
            # Route to appropriate method
            if action == "query" or action == "search":
                return self._handle_query(parameters)
            elif action == "add_documents" or action == "add":
                return self._handle_add_documents(parameters)
            elif action == "delete" or action == "remove":
                return self._handle_delete(parameters)
            elif action == "capabilities":
                return self._handle_capabilities()
            elif action == "stats" or action == "statistics":
                return self._handle_stats()
            else:
                # Try direct method call on legacy tool
                if hasattr(self._legacy_tool, action):
                    method = getattr(self._legacy_tool, action)
                    return method(**parameters)
                else:
                    raise ValueError(f"RAG tool does not support action: {action}")
                    
        except Exception as e:
            self._logger.error(f"RAG tool execution failed: {e}")
            raise
    
    def _handle_query(self, parameters: Dict[str, Any]) -> Any:
        """Handle query/search operations"""
        query = parameters.get("query", "")
        filters = parameters.get("filters", None)
        top_k = parameters.get("top_k", 10)
        
        if hasattr(self._legacy_tool, 'query'):
            # Standard query method
            if filters:
                return self._legacy_tool.query(query, filters=filters, k=top_k)
            else:
                return self._legacy_tool.query(query, k=top_k)
        elif hasattr(self._legacy_tool, 'search'):
            # Alternative search method
            return self._legacy_tool.search(query, limit=top_k, filters=filters)
        else:
            raise NotImplementedError(f"RAG tool {self.metadata.id} does not support query operations")
    
    def _handle_add_documents(self, parameters: Dict[str, Any]) -> Any:
        """Handle document addition"""
        documents = parameters.get("documents", [])
        
        if hasattr(self._legacy_tool, 'add_documents'):
            return self._legacy_tool.add_documents(documents)
        elif hasattr(self._legacy_tool, 'add'):
            return self._legacy_tool.add(documents)
        elif hasattr(self._legacy_tool, 'insert'):
            return self._legacy_tool.insert(documents)
        else:
            raise NotImplementedError(f"RAG tool {self.metadata.id} does not support document addition")
    
    def _handle_delete(self, parameters: Dict[str, Any]) -> Any:
        """Handle document deletion"""
        document_ids = parameters.get("document_ids", [])
        filters = parameters.get("filters", None)
        
        if hasattr(self._legacy_tool, 'delete'):
            if document_ids:
                # Delete by IDs
                if len(document_ids) == 1:
                    return self._legacy_tool.delete(document_ids[0])
                else:
                    # Batch delete
                    results = []
                    for doc_id in document_ids:
                        results.append(self._legacy_tool.delete(doc_id))
                    return results
            elif filters:
                # Delete by filters (if supported)
                return self._legacy_tool.delete(filters)
        
        raise NotImplementedError(f"RAG tool {self.metadata.id} does not support deletion")
    
    def _handle_capabilities(self) -> Dict[str, Any]:
        """Handle capabilities query"""
        if hasattr(self._legacy_tool, 'capabilities'):
            return self._legacy_tool.capabilities()
        else:
            # Infer capabilities from available methods
            caps = {
                "vector_search": hasattr(self._legacy_tool, 'query'),
                "metadata_filtering": True,  # Most RAG tools support this
                "full_text_search": hasattr(self._legacy_tool, 'search'),
                "batch_operations": hasattr(self._legacy_tool, 'add_documents')
            }
            return caps
    
    def _handle_stats(self) -> Dict[str, Any]:
        """Handle statistics query"""
        if hasattr(self._legacy_tool, 'stats'):
            return self._legacy_tool.stats()
        elif hasattr(self._legacy_tool, 'get_stats'):
            return self._legacy_tool.get_stats()
        else:
            return {
                "document_count": "unknown",
                "storage_size": "unknown",
                "last_updated": "unknown",
                "backend": self._storage_type
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for RAG tools"""
        base_health = super().health_check()
        
        base_health.update({
            "storage_type": self._storage_type,
            "memory_capabilities": [cap.value for cap in self.metadata.capabilities],
        })
        
        # Check storage connectivity
        try:
            if hasattr(self._legacy_tool, 'capabilities'):
                base_health["backend_capabilities"] = self._legacy_tool.capabilities()
        except Exception as e:
            base_health["backend_error"] = str(e)
        
        return base_health
