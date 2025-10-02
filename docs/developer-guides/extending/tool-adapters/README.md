# Building Custom Tool Adapters for LangSwarm V2

**Complete guide for creating adapters that migrate legacy tools to V2 architecture**

## 🎯 Overview

LangSwarm V2 provides a comprehensive adapter framework for migrating legacy tools to the unified V2 tool system. Build custom adapters to integrate any legacy tool type while maintaining backward compatibility and gaining V2 capabilities.

**Adapter Types:**
- **Synapse Adapters**: Multi-agent workflow tools (consensus, branching, routing)
- **RAG Adapters**: Memory and document storage tools
- **Plugin Adapters**: Utility and integration tools
- **Custom Adapters**: Any legacy tool with custom behavior

---

## 🏗️ Adapter Architecture

### **Base Adapter Framework**

```python
from langswarm.tools.adapters.base import LegacyToolAdapter
from langswarm.tools.interfaces import ToolType, IToolCapability
from typing import Dict, List, Any, Optional

class CustomToolAdapter(LegacyToolAdapter):
    """Base class for all legacy tool adapters"""
    
    def __init__(
        self,
        legacy_tool: Any,
        tool_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(legacy_tool, tool_id, tool_name, **kwargs)
        
        # Set tool type and category
        self.tool_type = ToolType.UTILITY  # or WORKFLOW, MEMORY
        self.tool_category = "custom"
        
        # Initialize adapter-specific properties
        self._capabilities_cache = None
        self._schema_cache = {}
    
    async def _detect_capabilities(self) -> List[str]:
        """Detect what the legacy tool can do"""
        capabilities = []
        
        # Check for common methods
        if hasattr(self.legacy_tool, "execute"):
            capabilities.append("execute")
        if hasattr(self.legacy_tool, "query"):
            capabilities.append("query")
        if hasattr(self.legacy_tool, "process"):
            capabilities.append("process")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate JSON schema for method parameters"""
        if method_name == "execute":
            return {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input data"},
                    "options": {"type": "object", "default": {}, "description": "Execution options"}
                },
                "required": ["input"]
            }
        return {}
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute the legacy tool method"""
        if method_name == "execute":
            return await self._safe_execute(
                self.legacy_tool.execute,
                parameters.get("input"),
                options=parameters.get("options", {})
            )
        else:
            raise ToolExecutionError(f"Unknown method: {method_name}")
    
    async def _safe_execute(self, method, *args, **kwargs):
        """Safely execute legacy method with error handling"""
        try:
            # Handle both sync and async methods
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                return method(*args, **kwargs)
        except Exception as e:
            raise ToolExecutionError(f"Legacy tool execution failed: {str(e)}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the legacy tool"""
        try:
            # Check if tool has health check method
            if hasattr(self.legacy_tool, "health_check"):
                health = await self._safe_execute(self.legacy_tool.health_check)
                return {"status": "healthy", "details": health}
            else:
                # Basic connectivity check
                return {"status": "healthy", "message": "Tool accessible"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

---

## 🔄 Synapse Tool Adapters

### **Consensus Tool Adapter**

```python
from langswarm.tools.adapters.synapse import SynapseToolAdapter

class ConsensusSynapseAdapter(SynapseToolAdapter):
    """Adapter for Synapse consensus tools"""
    
    def __init__(self, legacy_consensus_tool, **kwargs):
        super().__init__(legacy_consensus_tool, **kwargs)
        self.tool_type = ToolType.WORKFLOW
        self.synapse_type = "consensus"
    
    async def _detect_capabilities(self) -> List[str]:
        """Consensus-specific capabilities"""
        capabilities = ["query", "consensus", "help"]
        
        # Check for agent management
        if hasattr(self.legacy_tool, "get_agents"):
            capabilities.append("get_agents")
        if hasattr(self.legacy_tool, "add_agent"):
            capabilities.append("add_agent")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate schemas for consensus methods"""
        schemas = {
            "query": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question for consensus"},
                    "confidence_threshold": {"type": "number", "default": 0.7},
                    "max_iterations": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            },
            "consensus": {
                "type": "object", 
                "properties": {
                    "query": {"type": "string"},
                    "agents": {"type": "array", "items": {"type": "string"}},
                    "voting_method": {"type": "string", "enum": ["majority", "weighted", "unanimous"]}
                },
                "required": ["query"]
            }
        }
        return schemas.get(method_name, {})
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute consensus-specific methods"""
        if method_name == "query":
            # Map to legacy run method
            return await self._safe_execute(
                self.legacy_tool.run,
                payload={"query": parameters["query"]},
                action="query"
            )
        elif method_name == "consensus":
            # Execute consensus with parameters
            return await self._safe_execute(
                self.legacy_tool.run,
                payload=parameters,
                action="consensus"
            )
        elif method_name == "get_agents":
            # Get agent information
            if hasattr(self.legacy_tool, "agents"):
                return {"agents": [agent.identifier for agent in self.legacy_tool.agents]}
            return {"agents": []}
        else:
            return await super()._execute_method(method_name, parameters)

# Usage
consensus_tool = LangSwarmConsensusTool(identifier="consensus", agents=agents)
consensus_adapter = ConsensusSynapseAdapter(consensus_tool)

# Execute through V2 interface
result = await consensus_adapter.execute("query", {"query": "What is AI?"})
```

### **Branching Tool Adapter**

```python
class BranchingSynapseAdapter(SynapseToolAdapter):
    """Adapter for Synapse branching tools"""
    
    def __init__(self, legacy_branching_tool, **kwargs):
        super().__init__(legacy_branching_tool, **kwargs)
        self.synapse_type = "branching"
    
    async def _detect_capabilities(self) -> List[str]:
        return ["query", "branch", "help", "get_agents"]
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate schemas for branching methods"""
        if method_name == "branch":
            return {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query for diverse responses"},
                    "branch_count": {"type": "integer", "default": 3, "minimum": 2, "maximum": 10},
                    "diversity_threshold": {"type": "number", "default": 0.8}
                },
                "required": ["query"]
            }
        return super()._generate_method_schema(method_name)
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute branching-specific methods"""
        if method_name == "branch":
            return await self._safe_execute(
                self.legacy_tool.run,
                payload=parameters,
                action="branch"
            )
        return await super()._execute_method(method_name, parameters)

# Usage
branching_tool = LangSwarmBranchingTool(identifier="branching", agents=agents)
branching_adapter = BranchingSynapseAdapter(branching_tool)

result = await branching_adapter.execute("branch", {
    "query": "Explain machine learning",
    "branch_count": 5
})
```

---

## 💾 RAG Tool Adapters

### **SQLite RAG Adapter**

```python
from langswarm.tools.adapters.rag import RAGToolAdapter

class SQLiteRAGAdapter(RAGToolAdapter):
    """Adapter for SQLite-based RAG tools"""
    
    def __init__(self, legacy_sqlite_adapter, **kwargs):
        super().__init__(legacy_sqlite_adapter, **kwargs)
        self.tool_type = ToolType.MEMORY
        self.storage_type = "sqlite"
    
    async def _detect_capabilities(self) -> List[str]:
        """SQLite-specific capabilities"""
        capabilities = ["query", "add", "delete", "stats"]
        
        # Check for advanced features
        if hasattr(self.legacy_tool, "similarity_search"):
            capabilities.append("similarity_search")
        if hasattr(self.legacy_tool, "update_document"):
            capabilities.append("update")
        if hasattr(self.legacy_tool, "bulk_add"):
            capabilities.append("bulk_add")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate schemas for RAG operations"""
        schemas = {
            "query": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100},
                    "filters": {"type": "object", "default": {}, "description": "Metadata filters"},
                    "min_relevance": {"type": "number", "default": 0.0, "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["query"]
            },
            "add": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Document content"},
                    "metadata": {"type": "object", "default": {}, "description": "Document metadata"},
                    "document_id": {"type": "string", "description": "Optional document ID"}
                },
                "required": ["content"]
            },
            "delete": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID to delete"},
                    "filters": {"type": "object", "description": "Delete by filters"}
                }
            }
        }
        return schemas.get(method_name, {})
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute RAG-specific methods"""
        if method_name == "query":
            # Map to legacy query method
            return await self._safe_execute(
                self.legacy_tool.query,
                parameters["query"],
                limit=parameters.get("limit", 10),
                filters=parameters.get("filters", {}),
                min_relevance=parameters.get("min_relevance", 0.0)
            )
        elif method_name == "add":
            # Map to legacy add method
            return await self._safe_execute(
                self.legacy_tool.add_document,
                content=parameters["content"],
                metadata=parameters.get("metadata", {}),
                document_id=parameters.get("document_id")
            )
        elif method_name == "delete":
            # Map to legacy delete method
            if "document_id" in parameters:
                return await self._safe_execute(
                    self.legacy_tool.delete_document,
                    parameters["document_id"]
                )
            else:
                return await self._safe_execute(
                    self.legacy_tool.delete_by_filters,
                    parameters.get("filters", {})
                )
        elif method_name == "stats":
            # Get storage statistics
            return await self._safe_execute(self.legacy_tool.get_statistics)
        else:
            return await super()._execute_method(method_name, parameters)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Check SQLite database health"""
        try:
            # Check database connection
            stats = await self._safe_execute(self.legacy_tool.get_statistics)
            return {
                "status": "healthy",
                "document_count": stats.get("document_count", 0),
                "storage_size_mb": stats.get("storage_size_mb", 0),
                "last_updated": stats.get("last_updated")
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Usage
sqlite_adapter = SQLiteAdapter(identifier="sqlite", db_path="memory.db")
rag_adapter = SQLiteRAGAdapter(sqlite_adapter)

# Query documents
results = await rag_adapter.execute("query", {
    "query": "machine learning",
    "limit": 5,
    "filters": {"category": "AI"}
})

# Add document
await rag_adapter.execute("add", {
    "content": "Machine learning is a subset of AI...",
    "metadata": {"category": "AI", "author": "Expert"}
})
```

### **ChromaDB RAG Adapter**

```python
class ChromaDBRAGAdapter(RAGToolAdapter):
    """Adapter for ChromaDB-based RAG tools"""
    
    def __init__(self, legacy_chromadb_adapter, **kwargs):
        super().__init__(legacy_chromadb_adapter, **kwargs)
        self.storage_type = "chromadb"
    
    async def _detect_capabilities(self) -> List[str]:
        """ChromaDB-specific capabilities"""
        capabilities = ["query", "add", "delete", "stats", "similarity_search"]
        
        # Check for vector operations
        if hasattr(self.legacy_tool, "get_embeddings"):
            capabilities.append("get_embeddings")
        if hasattr(self.legacy_tool, "update_embeddings"):
            capabilities.append("update_embeddings")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """ChromaDB-specific schemas"""
        if method_name == "similarity_search":
            return {
                "type": "object",
                "properties": {
                    "query_vector": {"type": "array", "items": {"type": "number"}},
                    "limit": {"type": "integer", "default": 10},
                    "distance_threshold": {"type": "number", "default": 0.8}
                },
                "required": ["query_vector"]
            }
        return super()._generate_method_schema(method_name)
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute ChromaDB-specific methods"""
        if method_name == "similarity_search":
            return await self._safe_execute(
                self.legacy_tool.similarity_search,
                query_vector=parameters["query_vector"],
                n_results=parameters.get("limit", 10),
                distance_threshold=parameters.get("distance_threshold", 0.8)
            )
        return await super()._execute_method(method_name, parameters)

# Usage
chromadb_adapter = ChromaDBAdapter(identifier="chromadb", collection_name="documents")
chroma_rag_adapter = ChromaDBRAGAdapter(chromadb_adapter)

# Vector similarity search
results = await chroma_rag_adapter.execute("similarity_search", {
    "query_vector": [0.1, 0.2, 0.3, ...],  # Embedding vector
    "limit": 5
})
```

---

## 🔌 Plugin Tool Adapters

### **Notification Plugin Adapter**

```python
from langswarm.tools.adapters.plugin import PluginToolAdapter

class NotificationPluginAdapter(PluginToolAdapter):
    """Adapter for notification plugins"""
    
    def __init__(self, legacy_plugin, **kwargs):
        super().__init__(legacy_plugin, **kwargs)
        self.tool_type = ToolType.UTILITY
        self.plugin_type = "notification"
    
    async def _detect_capabilities(self) -> List[str]:
        """Notification-specific capabilities"""
        capabilities = ["execute", "send", "notify"]
        
        # Check for channel support
        if hasattr(self.legacy_tool, "list_channels"):
            capabilities.append("list_channels")
        if hasattr(self.legacy_tool, "configure_channel"):
            capabilities.append("configure_channel")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate notification schemas"""
        schemas = {
            "send": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message content"},
                    "channel": {"type": "string", "description": "Target channel"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
                    "recipients": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["message", "channel"]
            },
            "notify": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title"},
                    "body": {"type": "string", "description": "Notification body"},
                    "type": {"type": "string", "enum": ["info", "warning", "error"], "default": "info"}
                },
                "required": ["title", "body"]
            }
        }
        return schemas.get(method_name, {})
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute notification methods"""
        if method_name in ["execute", "send"]:
            return await self._safe_execute(
                self.legacy_tool.send,
                message=parameters["message"],
                channel=parameters["channel"],
                priority=parameters.get("priority", "normal"),
                recipients=parameters.get("recipients", [])
            )
        elif method_name == "notify":
            return await self._safe_execute(
                self.legacy_tool.notify,
                title=parameters["title"],
                body=parameters["body"],
                notification_type=parameters.get("type", "info")
            )
        else:
            return await super()._execute_method(method_name, parameters)

# Usage
notification_plugin = NotificationPlugin(config={"provider": "slack"})
notification_adapter = NotificationPluginAdapter(notification_plugin)

# Send notification
result = await notification_adapter.execute("send", {
    "message": "Workflow completed successfully",
    "channel": "#alerts",
    "priority": "high"
})
```

### **Integration Plugin Adapter**

```python
class IntegrationPluginAdapter(PluginToolAdapter):
    """Adapter for integration plugins"""
    
    def __init__(self, legacy_plugin, **kwargs):
        super().__init__(legacy_plugin, **kwargs)
        self.plugin_type = "integration"
    
    async def _detect_capabilities(self) -> List[str]:
        """Integration-specific capabilities"""
        capabilities = ["execute", "connect", "sync", "integrate"]
        
        # Check for specific integration features
        if hasattr(self.legacy_tool, "authenticate"):
            capabilities.append("authenticate")
        if hasattr(self.legacy_tool, "get_status"):
            capabilities.append("get_status")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Integration schemas"""
        if method_name == "integrate":
            return {
                "type": "object",
                "properties": {
                    "source_system": {"type": "string"},
                    "target_system": {"type": "string"},
                    "data": {"type": "object"},
                    "mapping": {"type": "object", "default": {}},
                    "options": {"type": "object", "default": {}}
                },
                "required": ["source_system", "target_system", "data"]
            }
        return super()._generate_method_schema(method_name)
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute integration methods"""
        if method_name == "integrate":
            return await self._safe_execute(
                self.legacy_tool.integrate,
                source=parameters["source_system"],
                target=parameters["target_system"],
                data=parameters["data"],
                mapping=parameters.get("mapping", {}),
                options=parameters.get("options", {})
            )
        return await super()._execute_method(method_name, parameters)

# Usage
integration_plugin = IntegrationPlugin(config={"type": "api_bridge"})
integration_adapter = IntegrationPluginAdapter(integration_plugin)

# Integrate data between systems
result = await integration_adapter.execute("integrate", {
    "source_system": "crm",
    "target_system": "analytics",
    "data": {"customer_id": "123", "purchase_amount": 100},
    "mapping": {"customer_id": "user_id"}
})
```

---

## 🔧 Advanced Adapter Features

### **Multi-Method Detection**

```python
class SmartAdapter(LegacyToolAdapter):
    """Adapter with intelligent method detection"""
    
    async def _detect_capabilities(self) -> List[str]:
        """Intelligently detect all tool capabilities"""
        capabilities = []
        
        # Common method patterns
        method_patterns = {
            "execute": ["execute", "run", "process", "perform"],
            "query": ["query", "search", "find", "get"],
            "add": ["add", "insert", "create", "store"],
            "update": ["update", "modify", "edit", "change"],
            "delete": ["delete", "remove", "drop", "clear"]
        }
        
        for capability, method_names in method_patterns.items():
            for method_name in method_names:
                if hasattr(self.legacy_tool, method_name):
                    capabilities.append(capability)
                    break
        
        # Check for special interfaces
        if hasattr(self.legacy_tool, "__call__"):
            capabilities.append("call")
        if hasattr(self.legacy_tool, "__iter__"):
            capabilities.append("iterate")
        
        return capabilities
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute with intelligent method mapping"""
        method_mapping = {
            "execute": ["execute", "run", "process", "perform"],
            "query": ["query", "search", "find", "get"],
            "add": ["add", "insert", "create", "store"],
        }
        
        if method_name in method_mapping:
            for legacy_method in method_mapping[method_name]:
                if hasattr(self.legacy_tool, legacy_method):
                    legacy_func = getattr(self.legacy_tool, legacy_method)
                    return await self._safe_execute(legacy_func, **parameters)
        
        raise ToolExecutionError(f"Method {method_name} not supported")
```

### **Parameter Adaptation**

```python
class ParameterAdaptingAdapter(LegacyToolAdapter):
    """Adapter that adapts parameters between V1 and V2 formats"""
    
    def __init__(self, legacy_tool, parameter_mapping=None, **kwargs):
        super().__init__(legacy_tool, **kwargs)
        self.parameter_mapping = parameter_mapping or {}
    
    async def _adapt_parameters(self, method_name: str, v2_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt V2 parameters to V1 format"""
        adapted = {}
        
        # Apply parameter mapping
        mapping = self.parameter_mapping.get(method_name, {})
        for v2_param, value in v2_parameters.items():
            v1_param = mapping.get(v2_param, v2_param)
            adapted[v1_param] = value
        
        # Handle special conversions
        if method_name == "query" and "filters" in adapted:
            # Convert V2 filters to V1 format
            adapted["where_clause"] = self._convert_filters_to_where(adapted.pop("filters"))
        
        return adapted
    
    def _convert_filters_to_where(self, filters: Dict[str, Any]) -> str:
        """Convert V2 filters to V1 WHERE clause"""
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            else:
                conditions.append(f"{key} = {value}")
        return " AND ".join(conditions)
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute with parameter adaptation"""
        adapted_params = await self._adapt_parameters(method_name, parameters)
        
        # Execute with adapted parameters
        if hasattr(self.legacy_tool, method_name):
            method = getattr(self.legacy_tool, method_name)
            return await self._safe_execute(method, **adapted_params)
        else:
            raise ToolExecutionError(f"Method {method_name} not found")

# Usage with parameter mapping
parameter_mapping = {
    "query": {
        "query": "search_text",
        "limit": "max_results",
        "filters": "conditions"
    },
    "add": {
        "content": "document_text",
        "metadata": "doc_metadata"
    }
}

adapter = ParameterAdaptingAdapter(
    legacy_tool=legacy_tool,
    parameter_mapping=parameter_mapping
)
```

### **Health Monitoring**

```python
class HealthMonitoringAdapter(LegacyToolAdapter):
    """Adapter with comprehensive health monitoring"""
    
    def __init__(self, legacy_tool, health_check_interval=60, **kwargs):
        super().__init__(legacy_tool, **kwargs)
        self.health_check_interval = health_check_interval
        self.last_health_check = None
        self.health_history = []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Comprehensive health monitoring"""
        now = datetime.now()
        
        # Check if we need a fresh health check
        if (self.last_health_check is None or 
            (now - self.last_health_check).seconds > self.health_check_interval):
            
            health_status = await self._perform_health_check()
            self.last_health_check = now
            self.health_history.append({
                "timestamp": now,
                "status": health_status["status"]
            })
            
            # Keep only last 100 health checks
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
        
        return {
            "status": self.health_history[-1]["status"] if self.health_history else "unknown",
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "check_interval": self.health_check_interval,
            "history_count": len(self.health_history),
            "uptime_percentage": self._calculate_uptime()
        }
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform actual health check"""
        try:
            # Test basic functionality
            if hasattr(self.legacy_tool, "health_check"):
                result = await self._safe_execute(self.legacy_tool.health_check)
                return {"status": "healthy", "details": result}
            
            # Test a simple operation
            if hasattr(self.legacy_tool, "ping"):
                await self._safe_execute(self.legacy_tool.ping)
                return {"status": "healthy", "message": "Ping successful"}
            
            # Basic attribute check
            if hasattr(self.legacy_tool, "status"):
                status = self.legacy_tool.status
                return {"status": "healthy" if status == "active" else "degraded"}
            
            return {"status": "healthy", "message": "Basic checks passed"}
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _calculate_uptime(self) -> float:
        """Calculate uptime percentage from health history"""
        if not self.health_history:
            return 100.0
        
        healthy_count = sum(1 for h in self.health_history if h["status"] == "healthy")
        return (healthy_count / len(self.health_history)) * 100
```

---

## 📚 Best Practices

### **Adapter Design Principles**
- **Single Responsibility**: Each adapter should handle one tool type
- **Interface Compliance**: Always implement the base adapter interface
- **Error Handling**: Provide comprehensive error handling and recovery
- **Documentation**: Document adapter behavior and parameter mappings

### **Performance Considerations**
- **Method Caching**: Cache capability detection and schema generation
- **Lazy Loading**: Only load legacy tools when needed
- **Resource Management**: Properly manage legacy tool lifecycle
- **Health Monitoring**: Implement regular health checks

### **Testing Strategies**
- **Mock Legacy Tools**: Create mock versions for testing
- **Parameter Validation**: Test parameter adaptation and validation
- **Error Scenarios**: Test error handling and recovery
- **Performance Testing**: Measure adapter overhead

### **Migration Patterns**
- **Gradual Migration**: Start with simple adapters, add complexity gradually
- **Backward Compatibility**: Maintain compatibility with existing usage patterns
- **Documentation**: Document migration process and breaking changes
- **Validation**: Validate adapter behavior against legacy tool behavior

---

**Building custom tool adapters enables seamless migration of any legacy tool to LangSwarm V2's unified architecture while preserving functionality and adding modern capabilities like health monitoring, schema generation, and type safety.**
