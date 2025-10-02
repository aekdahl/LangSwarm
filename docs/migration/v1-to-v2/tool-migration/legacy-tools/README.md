# V1 to V2 Legacy Tool Migration Guide

**Comprehensive migration guide for Synapse, RAG, and Plugin tools to V2 unified architecture**

## 🎯 Overview

LangSwarm V2 provides seamless migration for all V1 legacy tool types through comprehensive adapters and automated migration systems. Transform fragmented V1 tool ecosystems into a unified V2 architecture while maintaining 100% backward compatibility.

**Legacy Tool Types:**
- **Synapse Tools**: Multi-agent workflow tools (consensus, branching, routing, voting, aggregation)
- **RAG Tools**: Memory and document storage adapters (SQLite, Redis, ChromaDB, etc.)
- **Plugin Tools**: Utility and integration plugins
- **Custom Tools**: User-defined legacy tools

---

## 🔄 Migration Overview

### **Before V2: Fragmented V1 System**

```python
# V1 Synapse Tools - Complex Setup
from langswarm.synapse.tools.consensus import LangSwarmConsensusTool
consensus = LangSwarmConsensusTool(identifier="test", agents=agents)
result = consensus.run(payload={"query": "question"}, action="query")

# V1 RAG Adapters - Adapter-Specific
from langswarm.memory.adapters.sqlite_adapter import SQLiteAdapter
adapter = SQLiteAdapter(identifier="db", db_path="memory.db")
results = adapter.query("search text", filters={...})

# V1 Plugins - Registry-Based
plugin_registry.get_plugin("notification").execute(action="send", data={...})
```

### **After V2: Unified System**

```python
# V2 Unified Interface - All Tools
from langswarm.tools import ToolRegistry

registry = ToolRegistry()

# All tools use same V2 interface
consensus_result = await registry.get_tool("synapse_consensus").execute("query", {"query": "question"})
memory_result = await registry.get_tool("memory_sqlite").execute("query", {"query": "search text"})
plugin_result = await registry.get_tool("plugin_notification").execute("execute", {"action": "send"})
```

---

## 📊 Migration Benefits

### **Complexity Reduction**

| Aspect | V1 Legacy System | V2 Unified System | Improvement |
|--------|------------------|-------------------|-------------|
| **Tool Interfaces** | 3+ different patterns | Single V2 interface | 90% simpler |
| **Registration** | Separate registries | Unified registry | Single discovery |
| **Method Calls** | Type-specific calls | Unified execute() | Consistent API |
| **Error Handling** | Various patterns | V2 error system | Standardized |
| **Health Monitoring** | Limited/inconsistent | Comprehensive | Better observability |

### **Feature Enhancements**

| Feature | V1 Support | V2 Support | Enhancement |
|---------|------------|------------|-------------|
| **Type Safety** | Limited | Full schemas | 100% type coverage |
| **Health Checks** | Tool-specific | Standardized | Consistent monitoring |
| **Capabilities** | Implicit | Explicit schemas | Clear interfaces |
| **Error Recovery** | Basic | Comprehensive | Better reliability |
| **Performance** | Variable | Optimized | Consistent performance |

---

## 🔧 Synapse Tool Migration

### **Migration Process**

Synapse tools are migrated as **Workflow** tools with preserved multi-agent functionality:

#### **1. Consensus Tool Migration**

```python
# V1 Consensus Tool
from langswarm.synapse.tools.consensus import LangSwarmConsensusTool

# Original setup
agents = [agent1, agent2, agent3]
consensus_tool = LangSwarmConsensusTool(
    identifier="consensus",
    agents=agents,
    confidence_threshold=0.7
)

# V1 usage
result = consensus_tool.run(
    payload={"query": "What is the best approach to AI safety?"},
    action="query"
)

# V2 Migration - Automatic
from langswarm.tools.migration import ToolMigrator

migrator = ToolMigrator()
migration_result = await migrator.migrate_synapse_tools()

# V2 usage - Unified Interface
from langswarm.tools import ToolRegistry

registry = ToolRegistry()
consensus_v2 = registry.get_tool("synapse_consensus")

# Same functionality, unified interface
result = await consensus_v2.execute("query", {
    "query": "What is the best approach to AI safety?",
    "confidence_threshold": 0.7
})
```

#### **2. Branching Tool Migration**

```python
# V1 Branching Tool
from langswarm.synapse.tools.branching import LangSwarmBranchingTool

branching_tool = LangSwarmBranchingTool(
    identifier="branching",
    agents=agents,
    diversity_threshold=0.8
)

# V1 usage
branches = branching_tool.run(
    payload={"query": "Explain machine learning"},
    action="branch"
)

# V2 Migration
branching_v2 = registry.get_tool("synapse_branching")

# V2 usage
branches = await branching_v2.execute("branch", {
    "query": "Explain machine learning",
    "branch_count": 5,
    "diversity_threshold": 0.8
})
```

#### **3. Routing Tool Migration**

```python
# V1 Routing Tool
from langswarm.synapse.tools.routing import LangSwarmRoutingTool

routing_tool = LangSwarmRoutingTool(
    identifier="routing",
    agents=specialized_agents,
    routing_strategy="expertise_based"
)

# V1 usage
routed_result = routing_tool.run(
    payload={"query": "Complex technical question"},
    action="route"
)

# V2 Migration
routing_v2 = registry.get_tool("synapse_routing")

# V2 usage
routed_result = await routing_v2.execute("route", {
    "query": "Complex technical question",
    "routing_strategy": "expertise_based",
    "agent_pool": ["specialist1", "specialist2", "specialist3"]
})
```

### **Synapse Migration Features**

All Synapse tools gain V2 capabilities:

```python
# Get tool capabilities
capabilities = await consensus_v2.get_capabilities()
print(f"Capabilities: {capabilities}")
# Output: ['query', 'consensus', 'help', 'get_agents']

# Get method schema
schema = await consensus_v2.get_method_schema("consensus")
print(f"Schema: {schema}")

# Health monitoring
health = await consensus_v2.get_health_status()
print(f"Health: {health['status']}")

# Agent information
agents_info = await consensus_v2.execute("get_agents", {})
print(f"Agents: {agents_info['agents']}")
```

---

## 💾 RAG Tool Migration

### **Migration Process**

RAG tools are migrated as **Memory** tools with unified document operations:

#### **1. SQLite Adapter Migration**

```python
# V1 SQLite Adapter
from langswarm.memory.adapters.sqlite_adapter import SQLiteAdapter

sqlite_adapter = SQLiteAdapter(
    identifier="sqlite_memory",
    db_path="/data/memory.db",
    table_name="documents",
    enable_wal=True
)

# V1 usage
await sqlite_adapter.add_document(
    content="Machine learning is a subset of AI",
    metadata={"category": "AI", "source": "textbook"}
)

results = await sqlite_adapter.query(
    "machine learning",
    limit=5,
    filters={"category": "AI"}
)

# V2 Migration
rag_migration = await migrator.migrate_rag_tools()

# V2 usage - Unified Interface
memory_v2 = registry.get_tool("memory_sqlite")

# Same operations, unified interface
await memory_v2.execute("add", {
    "content": "Machine learning is a subset of AI",
    "metadata": {"category": "AI", "source": "textbook"}
})

results = await memory_v2.execute("query", {
    "query": "machine learning",
    "limit": 5,
    "filters": {"category": "AI"}
})
```

#### **2. Redis Adapter Migration**

```python
# V1 Redis Adapter
from langswarm.memory.adapters.redis_adapter import RedisAdapter

redis_adapter = RedisAdapter(
    identifier="redis_memory",
    host="localhost",
    port=6379,
    db=0,
    ttl=86400
)

# V1 usage
await redis_adapter.store_document(
    doc_id="doc_123",
    content="Redis is an in-memory data store",
    metadata={"type": "database"}
)

# V2 Migration
redis_v2 = registry.get_tool("memory_redis")

# V2 usage
await redis_v2.execute("add", {
    "content": "Redis is an in-memory data store",
    "metadata": {"type": "database"},
    "document_id": "doc_123"
})
```

#### **3. ChromaDB Adapter Migration**

```python
# V1 ChromaDB Adapter
from langswarm.memory.adapters.chromadb_adapter import ChromaDBAdapter

chromadb_adapter = ChromaDBAdapter(
    identifier="chromadb_memory",
    persist_directory="/data/chromadb",
    collection_name="documents",
    embedding_model="all-MiniLM-L6-v2"
)

# V1 usage - Vector search
similar_docs = await chromadb_adapter.similarity_search(
    query_vector=embedding_vector,
    n_results=5,
    distance_threshold=0.8
)

# V2 Migration
chromadb_v2 = registry.get_tool("memory_chromadb")

# V2 usage - Preserved vector capabilities
similar_docs = await chromadb_v2.execute("similarity_search", {
    "query_vector": embedding_vector,
    "limit": 5,
    "distance_threshold": 0.8
})
```

### **RAG Migration Features**

All RAG tools gain unified interface with backend-specific capabilities:

```python
# Universal RAG operations across all backends
storage_types = ["sqlite", "redis", "chromadb", "elasticsearch"]

for storage_type in storage_types:
    tool = registry.get_tool(f"memory_{storage_type}")
    
    # Same interface, different backends
    await tool.execute("add", {"content": "Test document"})
    results = await tool.execute("query", {"query": "test"})
    stats = await tool.execute("stats", {})
    
    print(f"{storage_type}: {stats['document_count']} documents")
```

---

## 🔌 Plugin Tool Migration

### **Migration Process**

Plugins are migrated as **Utility** tools with flexible execution patterns:

#### **1. Notification Plugin Migration**

```python
# V1 Notification Plugin
class NotificationPlugin:
    def __init__(self, config):
        self.config = config
        self.provider = config.get("provider", "email")
    
    def execute(self, action, data):
        if action == "send":
            return self.send_notification(data["message"], data["channel"])
    
    def send_notification(self, message, channel):
        # Send notification logic
        return {"status": "sent", "message_id": "msg_123"}

# V1 usage
notification_plugin = NotificationPlugin({"provider": "slack"})
result = notification_plugin.execute("send", {
    "message": "Workflow completed",
    "channel": "#alerts"
})

# V2 Migration
plugin_migration = await migrator.migrate_plugin_tools()

# V2 usage
notification_v2 = registry.get_tool("plugin_notification")

result = await notification_v2.execute("execute", {
    "action": "send",
    "data": {
        "message": "Workflow completed",
        "channel": "#alerts"
    }
})
```

#### **2. Integration Plugin Migration**

```python
# V1 Integration Plugin
class IntegrationPlugin:
    def integrate(self, source, target, data, mapping=None):
        # Integration logic
        return {"status": "integrated", "records": len(data)}

# V1 usage
integration_plugin = IntegrationPlugin()
result = integration_plugin.integrate(
    source="crm",
    target="analytics",
    data=customer_data,
    mapping=field_mapping
)

# V2 Migration
integration_v2 = registry.get_tool("plugin_integration")

# V2 usage
result = await integration_v2.execute("integrate", {
    "source_system": "crm",
    "target_system": "analytics",
    "data": customer_data,
    "mapping": field_mapping
})
```

### **Plugin Migration Features**

All plugins gain V2 capabilities:

```python
# Plugin type detection
plugin_types = await migrator.detect_plugin_types()
print(f"Plugin types: {plugin_types}")
# Output: ['notification', 'integration', 'workflow', 'utility']

# Plugin-specific capabilities
for plugin_type in plugin_types:
    plugin_tool = registry.get_tool(f"plugin_{plugin_type}")
    capabilities = await plugin_tool.get_capabilities()
    print(f"{plugin_type}: {capabilities}")
```

---

## 🤖 Automated Migration

### **Batch Migration**

```python
from langswarm.tools.migration import ToolMigrator

async def complete_migration():
    """Complete automated migration of all legacy tools"""
    
    migrator = ToolMigrator()
    
    # Discover all legacy tools
    discovery = await migrator.discover_legacy_tools()
    print(f"Discovered {discovery.total_tools} legacy tools:")
    print(f"  Synapse: {len(discovery.synapse_tools)}")
    print(f"  RAG: {len(discovery.rag_adapters)}")
    print(f"  Plugins: {len(discovery.plugins)}")
    
    # Migrate all discovered tools
    migration = await migrator.migrate_discovered_tools(discovery)
    print(f"Migration results:")
    print(f"  Successful: {migration.success_count}")
    print(f"  Failed: {migration.error_count}")
    
    # Register migrated tools
    registry = ToolRegistry()
    for tool_adapter in migration.successful_migrations:
        registry.register_tool(tool_adapter)
    
    print(f"Registered {len(migration.successful_migrations)} tools")
    
    return migration

# Run complete migration
migration_result = await complete_migration()
```

### **Selective Migration**

```python
async def selective_migration():
    """Migrate specific tool types"""
    
    migrator = ToolMigrator()
    
    # Migrate only Synapse consensus tools
    synapse_migration = await migrator.migrate_synapse_tools(
        tool_types=["consensus"]
    )
    
    # Migrate only SQLite and Redis RAG tools
    rag_migration = await migrator.migrate_rag_tools(
        backends=["sqlite", "redis"]
    )
    
    # Migrate only notification plugins
    plugin_migration = await migrator.migrate_plugin_tools(
        plugin_types=["notification"]
    )
    
    total_migrated = (
        synapse_migration.success_count +
        rag_migration.success_count +
        plugin_migration.success_count
    )
    
    print(f"Selective migration completed: {total_migrated} tools")

await selective_migration()
```

---

## 🔧 Migration Configuration

### **Custom Migration Rules**

```python
from langswarm.tools.migration import MigrationConfig

# Configure migration behavior
migration_config = MigrationConfig(
    # Tool identification
    preserve_identifiers=True,
    auto_generate_names=True,
    name_prefix="v2_",
    
    # Registration settings
    auto_register=True,
    registry_namespace="migrated",
    
    # Error handling
    error_handling="graceful",
    rollback_on_failure=True,
    continue_on_error=True,
    
    # Performance settings
    batch_size=50,
    timeout_seconds=30,
    max_concurrent_migrations=10,
    
    # Validation
    validate_migrations=True,
    test_migrations=True,
    health_check_enabled=True
)

migrator = ToolMigrator(config=migration_config)
```

### **Custom Tool Rules**

```python
# Define tool-specific migration rules
custom_rules = {
    "synapse_tools": {
        "consensus": {
            "new_name": "ai_consensus_v2",
            "description": "V2 AI consensus tool with enhanced capabilities",
            "tags": ["ai", "consensus", "multi-agent", "v2"],
            "timeout": 60,
            "retry_count": 3
        },
        "branching": {
            "capabilities": ["query", "branch", "help", "optimize"],
            "performance_tuning": {
                "max_branches": 10,
                "parallel_execution": True
            }
        }
    },
    "rag_tools": {
        "sqlite": {
            "connection_pool_size": 20,
            "cache_size": 1000,
            "enable_wal": True
        },
        "chromadb": {
            "batch_size": 100,
            "embedding_cache_size": 5000
        }
    },
    "plugins": {
        "notification": {
            "rate_limits": {
                "requests_per_minute": 60,
                "burst_size": 10
            },
            "retry_policy": {
                "max_retries": 3,
                "exponential_backoff": True
            }
        }
    }
}

migrator = ToolMigrator(custom_rules=custom_rules)
```

---

## 📊 Migration Validation

### **Pre-Migration Testing**

```python
async def validate_before_migration():
    """Validate legacy tools before migration"""
    
    migrator = ToolMigrator()
    
    # Discover legacy tools
    discovery = await migrator.discover_legacy_tools()
    
    # Test legacy tools
    validation_results = []
    
    for synapse_tool in discovery.synapse_tools:
        try:
            # Test basic functionality
            result = synapse_tool.run(
                payload={"query": "test"},
                action="query"
            )
            validation_results.append({
                "tool": synapse_tool.identifier,
                "type": "synapse",
                "status": "working",
                "result": result
            })
        except Exception as e:
            validation_results.append({
                "tool": synapse_tool.identifier,
                "type": "synapse", 
                "status": "error",
                "error": str(e)
            })
    
    # Validate discovery completeness
    working_tools = [r for r in validation_results if r["status"] == "working"]
    print(f"Pre-migration validation: {len(working_tools)}/{len(validation_results)} tools working")
    
    return validation_results

pre_validation = await validate_before_migration()
```

### **Post-Migration Testing**

```python
async def validate_after_migration(migration_result):
    """Validate migrated tools"""
    
    registry = ToolRegistry()
    validation_results = []
    
    for tool_info in migration_result.successful_migrations:
        tool = registry.get_tool(tool_info.tool_id)
        
        try:
            # Test basic V2 functionality
            capabilities = await tool.get_capabilities()
            health = await tool.get_health_status()
            
            # Test execution
            if "query" in capabilities:
                result = await tool.execute("query", {"query": "test"})
                execution_status = "success"
            else:
                execution_status = "no_query_capability"
            
            validation_results.append({
                "tool_id": tool_info.tool_id,
                "original_type": tool_info.original_type,
                "capabilities": len(capabilities),
                "health": health["status"],
                "execution": execution_status,
                "status": "working"
            })
            
        except Exception as e:
            validation_results.append({
                "tool_id": tool_info.tool_id,
                "status": "error",
                "error": str(e)
            })
    
    # Summary
    working_count = len([r for r in validation_results if r["status"] == "working"])
    print(f"Post-migration validation: {working_count}/{len(validation_results)} tools working")
    
    return validation_results

post_validation = await validate_after_migration(migration_result)
```

---

## 📋 Migration Checklist

### **Pre-Migration**
- [ ] **Tool Inventory**: Document all legacy Synapse, RAG, and Plugin tools
- [ ] **Functionality Testing**: Verify all legacy tools work correctly
- [ ] **Configuration Backup**: Save all tool configurations and data
- [ ] **Migration Planning**: Choose migration strategy (batch vs selective)
- [ ] **Environment Setup**: Set up V2 development environment

### **Migration Execution**
- [ ] **Discovery**: Run automatic tool discovery
- [ ] **Validation**: Validate discovered tools
- [ ] **Migration**: Execute tool migration
- [ ] **Testing**: Test migrated tools
- [ ] **Registration**: Register tools in V2 registry

### **Post-Migration**
- [ ] **Functionality Verification**: Verify all migrated tools work
- [ ] **Performance Testing**: Test tool performance
- [ ] **Integration Testing**: Test with V2 agents and workflows
- [ ] **Documentation Update**: Update documentation for V2 usage
- [ ] **Legacy Cleanup**: Clean up legacy tool configurations

### **Production Deployment**
- [ ] **Staged Rollout**: Deploy to development, staging, production
- [ ] **Monitoring Setup**: Configure tool health monitoring
- [ ] **Error Handling**: Set up error alerting and recovery
- [ ] **Performance Monitoring**: Track tool performance metrics
- [ ] **User Training**: Train users on V2 tool usage

---

## 🎯 Migration Success Metrics

### **Functional Success**
- [ ] **100% Tool Discovery**: All legacy tools discovered and categorized
- [ ] **High Migration Success Rate**: >95% successful migrations
- [ ] **Feature Preservation**: All tool functionality preserved
- [ ] **V2 Enhancement**: Tools gain V2 capabilities (schemas, health, monitoring)

### **Performance Success**
- [ ] **Equal or Better Performance**: Migrated tools perform as well or better
- [ ] **Consistent Response Times**: Predictable tool execution times
- [ ] **Health Monitoring**: All tools report health status
- [ ] **Error Recovery**: Improved error handling and recovery

### **Developer Experience**
- [ ] **Unified Interface**: Single interface for all tool types
- [ ] **Type Safety**: Schema validation for all tool methods
- [ ] **Better Documentation**: Clear method schemas and capabilities
- [ ] **Easier Testing**: Simplified tool testing and mocking

---

**LangSwarm V2's legacy tool migration system provides seamless transition from fragmented V1 tool ecosystems to a unified, modern architecture while preserving all functionality and adding powerful new capabilities.**
