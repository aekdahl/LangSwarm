# LangSwarm V2 Legacy Tool Migration

**Complete migration system for Synapse, RAG, and Plugin tools to unified V2 architecture**

## 🎯 Overview

LangSwarm V2 provides comprehensive migration support for all legacy tool types, transforming fragmented V1 systems into a unified, modern tool architecture. Migrate Synapse, RAG, and Plugin tools seamlessly while maintaining 100% backward compatibility.

**Key Benefits:**
- **100% Legacy Support**: All existing tools work through V2 interface
- **Zero Breaking Changes**: Existing code continues working unchanged
- **Unified Interface**: Single V2 interface replaces multiple legacy patterns
- **Automated Migration**: Complete automation with discovery and batch processing
- **Enhanced Capabilities**: Legacy tools gain V2 features (schemas, health, monitoring)

---

## 🚀 Quick Start

### **Automatic Tool Migration**

```python
from langswarm.tools.migration import ToolMigrator

# Create migrator
migrator = ToolMigrator()

# Automatically discover and migrate all legacy tools
migration_result = await migrator.discover_and_migrate_all()

print(f"Migration Results:")
print(f"  Synapse tools: {migration_result.synapse_tools_migrated}")
print(f"  RAG tools: {migration_result.rag_tools_migrated}")
print(f"  Plugin tools: {migration_result.plugin_tools_migrated}")
print(f"  Custom tools: {migration_result.custom_tools_migrated}")
print(f"  Total tools: {migration_result.total_tools_migrated}")
```

### **Using Migrated Tools**

```python
from langswarm.tools import ToolRegistry

# Get unified tool registry
registry = ToolRegistry()

# All legacy tools now available through V2 interface
synapse_tool = registry.get_tool("synapse_consensus")
rag_tool = registry.get_tool("memory_sqlite")
plugin_tool = registry.get_tool("plugin_notification")

# Execute with unified V2 interface
consensus_result = await synapse_tool.execute("query", {"query": "What is AI?"})
memory_result = await rag_tool.execute("query", {"query": "search text"})
plugin_result = await plugin_tool.execute("execute", {"action": "send", "data": {...}})
```

---

## 🔄 Tool Type Migration

### **Synapse Tool Migration**

Synapse tools (consensus, branching, routing, voting, aggregation) are migrated as **Workflow** tools:

```python
# Before V2: Direct Synapse usage
from langswarm.synapse.tools.consensus import LangSwarmConsensusTool

consensus = LangSwarmConsensusTool(identifier="test", agents=agents)
result = consensus.run(payload={"query": "question"}, action="query")

# After V2: Unified tool interface
from langswarm.tools.adapters.synapse import SynapseToolAdapter

# Automatic migration
adapter = SynapseToolAdapter(legacy_tool=consensus)

# Or use through registry
consensus_tool = registry.get_tool("synapse_consensus")
result = await consensus_tool.execute("query", {"query": "question"})
```

#### **Supported Synapse Tools**

| Tool Type | V2 Category | Supported Methods |
|-----------|-------------|-------------------|
| **Consensus** | Workflow | query, help, consensus, get_agents |
| **Branching** | Workflow | query, help, branch, get_agents |
| **Routing** | Workflow | query, help, route, get_agents |
| **Voting** | Workflow | query, help, vote, get_agents |
| **Aggregation** | Workflow | query, help, aggregate, get_agents |

### **RAG/Memory Tool Migration**

RAG tools are migrated as **Memory** tools with unified document operations:

```python
# Before V2: Adapter-specific usage
from langswarm.memory.adapters.sqlite_adapter import SQLiteAdapter

adapter = SQLiteAdapter(identifier="db", db_path="memory.db")
results = adapter.query("search text", filters={...})

# After V2: Unified memory interface
from langswarm.tools.adapters.rag import RAGToolAdapter

# Automatic migration
rag_adapter = RAGToolAdapter(legacy_adapter=adapter)

# Or use through registry
memory_tool = registry.get_tool("memory_sqlite")
results = await memory_tool.execute("query", {
    "query": "search text",
    "filters": {...}
})
```

#### **Supported RAG Backends**

| Backend | Storage Type | V2 Tool Name |
|---------|-------------|--------------|
| **SQLite** | sqlite | memory_sqlite |
| **Redis** | redis | memory_redis |
| **ChromaDB** | chromadb | memory_chromadb |
| **Elasticsearch** | elasticsearch | memory_elasticsearch |
| **BigQuery** | bigquery | memory_bigquery |

### **Plugin Tool Migration**

Plugins are migrated as **Utility** tools with flexible execution patterns:

```python
# Before V2: Registry-based plugin usage
plugin_registry.get_plugin("notification").execute(action="send", data={...})

# After V2: Unified tool interface
from langswarm.tools.adapters.plugin import PluginToolAdapter

# Automatic migration
plugin_adapter = PluginToolAdapter(legacy_plugin=plugin_instance)

# Or use through registry
plugin_tool = registry.get_tool("plugin_notification")
result = await plugin_tool.execute("execute", {
    "action": "send",
    "data": {...}
})
```

#### **Supported Plugin Types**

| Plugin Type | V2 Category | Execution Methods |
|-------------|-------------|-------------------|
| **Notification** | Utility | execute, send, notify |
| **Workflow** | Utility | execute, run, process |
| **Integration** | Utility | execute, integrate, connect |
| **Generic** | Utility | execute, run, perform |

---

## 🤖 Automated Migration System

### **Tool Discovery**

```python
from langswarm.tools.migration import ToolMigrator

migrator = ToolMigrator()

# Discover all legacy tools
discovery_result = await migrator.discover_legacy_tools()

print(f"Discovered Tools:")
print(f"  Synapse tools: {len(discovery_result.synapse_tools)}")
print(f"  RAG adapters: {len(discovery_result.rag_adapters)}")
print(f"  Plugins: {len(discovery_result.plugins)}")
print(f"  Custom tools: {len(discovery_result.custom_tools)}")

# View discovered tools
for tool in discovery_result.synapse_tools:
    print(f"  Synapse: {tool.identifier} ({tool.tool_type})")

for adapter in discovery_result.rag_adapters:
    print(f"  RAG: {adapter.identifier} ({adapter.backend_type})")

for plugin in discovery_result.plugins:
    print(f"  Plugin: {plugin.name} ({plugin.plugin_type})")
```

### **Batch Migration**

```python
# Migrate all discovered tools
migration_result = await migrator.migrate_discovered_tools(discovery_result)

print(f"Migration Summary:")
print(f"  Successfully migrated: {migration_result.success_count}")
print(f"  Failed migrations: {migration_result.error_count}")
print(f"  Total tools processed: {migration_result.total_processed}")

# Review migration details
for success in migration_result.successful_migrations:
    print(f"✓ {success.tool_name}: {success.v2_tool_id}")

for error in migration_result.failed_migrations:
    print(f"✗ {error.tool_name}: {error.error_message}")
```

### **Individual Tool Migration**

```python
# Migrate specific tool types
synapse_migration = await migrator.migrate_synapse_tools()
rag_migration = await migrator.migrate_rag_tools()
plugin_migration = await migrator.migrate_plugin_tools()

# Migrate custom tools
custom_tools = [my_custom_tool_1, my_custom_tool_2]
custom_migration = await migrator.migrate_custom_tools(custom_tools)

# Migrate specific tool instance
specific_tool = my_legacy_tool
tool_adapter = await migrator.migrate_tool(specific_tool)
print(f"Migrated tool ID: {tool_adapter.tool_id}")
```

---

## 🔧 Migration Configuration

### **Migration Settings**

```python
from langswarm.tools.migration import MigrationConfig

# Configure migration behavior
config = MigrationConfig(
    auto_register=True,           # Automatically register migrated tools
    preserve_identifiers=True,    # Keep original tool identifiers
    health_check_enabled=True,    # Enable health monitoring
    error_handling="graceful",    # Graceful error handling
    batch_size=50,               # Process 50 tools per batch
    timeout_seconds=30,          # 30 second timeout per tool
    validation_enabled=True,     # Validate migrations
    rollback_enabled=True        # Enable rollback on failure
)

# Use configuration
migrator = ToolMigrator(config=config)
result = await migrator.discover_and_migrate_all()
```

### **Custom Migration Rules**

```python
# Define custom migration rules
custom_rules = {
    "synapse_tools": {
        "consensus": {
            "new_name": "ai_consensus",
            "description": "AI-powered consensus tool",
            "tags": ["ai", "consensus", "multi-agent"]
        }
    },
    "rag_tools": {
        "sqlite": {
            "memory_limits": {"max_documents": 10000},
            "performance_tuning": {"cache_size": 1000}
        }
    },
    "plugins": {
        "notification": {
            "execution_timeout": 60,
            "retry_count": 3
        }
    }
}

# Apply custom rules
migrator = ToolMigrator(custom_rules=custom_rules)
result = await migrator.discover_and_migrate_all()
```

---

## 🔍 Backward Compatibility

### **Legacy Calling Patterns**

The migration system maintains 100% backward compatibility with existing code:

```python
# V1 calling patterns continue to work
from langswarm.tools.migration import ToolCompatibilityLayer

compatibility = ToolCompatibilityLayer()

# Legacy Synapse call
result = await compatibility.execute_legacy_call({
    "type": "synapse",
    "method": "run",
    "instance_name": "consensus_tool",
    "action": "query",
    "parameters": {"query": "What is AI?"}
})

# Legacy RAG call
result = await compatibility.execute_legacy_call({
    "type": "rag",
    "method": "query",
    "instance_name": "sqlite_adapter",
    "parameters": {"query": "search text", "filters": {...}}
})

# Legacy Plugin call
result = await compatibility.execute_legacy_call({
    "type": "plugin",
    "method": "execute",
    "instance_name": "notification_plugin",
    "parameters": {"action": "send", "data": {...}}
})
```

### **Tool Name Resolution**

```python
# Multiple discovery strategies for legacy tool names
tool_strategies = [
    "exact_match",      # Match exact tool ID
    "name_similarity",  # Fuzzy name matching
    "type_inference",   # Infer from tool type
    "capability_match"  # Match by capabilities
]

# Find legacy tools by name
found_tool = await compatibility.find_legacy_tool(
    name="consensus",
    strategies=tool_strategies
)

if found_tool:
    result = await found_tool.execute("query", {"query": "question"})
```

---

## 📊 Migration Monitoring

### **Migration Statistics**

```python
# Get comprehensive migration statistics
stats = await migrator.get_migration_statistics()

print(f"Migration Statistics:")
print(f"  Total discoveries: {stats.total_discoveries}")
print(f"  Successful migrations: {stats.successful_migrations}")
print(f"  Failed migrations: {stats.failed_migrations}")
print(f"  Success rate: {stats.success_rate:.1%}")

# Tool type breakdown
print(f"Tool Type Breakdown:")
for tool_type, count in stats.tool_type_counts.items():
    print(f"  {tool_type}: {count}")

# Migration timeline
print(f"Migration Timeline:")
for entry in stats.timeline:
    print(f"  {entry.timestamp}: {entry.tool_name} - {entry.status}")
```

### **Health Monitoring**

```python
# Check health of migrated tools
health_report = await migrator.check_migrated_tools_health()

print(f"Health Report:")
print(f"  Healthy tools: {health_report.healthy_count}")
print(f"  Unhealthy tools: {health_report.unhealthy_count}")
print(f"  Unknown status: {health_report.unknown_count}")

# Detailed health status
for tool_health in health_report.tool_health_status:
    print(f"  {tool_health.tool_id}: {tool_health.status}")
    if tool_health.status != "healthy":
        print(f"    Error: {tool_health.error_message}")
```

### **Performance Analysis**

```python
# Analyze migration performance
performance = await migrator.analyze_migration_performance()

print(f"Performance Analysis:")
print(f"  Average migration time: {performance.avg_migration_time_ms}ms")
print(f"  Fastest migration: {performance.fastest_migration_ms}ms")
print(f"  Slowest migration: {performance.slowest_migration_ms}ms")
print(f"  Tools per second: {performance.tools_per_second:.1f}")

# Performance by tool type
for tool_type, perf in performance.by_tool_type.items():
    print(f"  {tool_type} average: {perf.avg_time_ms}ms")
```

---

## 🔧 Advanced Migration Features

### **Custom Adapter Development**

```python
from langswarm.tools.adapters.base import LegacyToolAdapter

class CustomToolAdapter(LegacyToolAdapter):
    """Custom adapter for legacy tools"""
    
    def __init__(self, legacy_tool, **kwargs):
        super().__init__(legacy_tool, **kwargs)
        self.tool_type = ToolType.UTILITY
        self.tool_category = "custom"
    
    async def _detect_capabilities(self) -> List[str]:
        """Detect tool capabilities"""
        capabilities = ["execute"]
        
        # Check for specific methods
        if hasattr(self.legacy_tool, "process"):
            capabilities.append("process")
        if hasattr(self.legacy_tool, "transform"):
            capabilities.append("transform")
        
        return capabilities
    
    async def _generate_method_schema(self, method_name: str) -> Dict[str, Any]:
        """Generate schema for specific method"""
        if method_name == "execute":
            return {
                "type": "object",
                "properties": {
                    "input_data": {"type": "string"},
                    "options": {"type": "object", "default": {}}
                },
                "required": ["input_data"]
            }
        return {}
    
    async def _execute_method(self, method_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute specific method"""
        if method_name == "execute":
            return await self.legacy_tool.process(
                parameters.get("input_data"),
                options=parameters.get("options", {})
            )
        elif method_name == "process":
            return await self.legacy_tool.process(parameters)
        else:
            raise ToolExecutionError(f"Unknown method: {method_name}")

# Register custom adapter
from langswarm.tools.adapters import AdapterFactory

AdapterFactory.register_adapter("custom_tool", CustomToolAdapter)

# Use in migration
custom_tools = [MyCustomTool(), AnotherCustomTool()]
migration_result = await migrator.migrate_custom_tools(custom_tools)
```

### **Migration Validation**

```python
# Validate migration results
validation_result = await migrator.validate_migration(migration_result)

if validation_result.is_valid:
    print("✓ Migration validation passed")
else:
    print("✗ Migration validation failed:")
    for error in validation_result.errors:
        print(f"  - {error.tool_id}: {error.error_message}")

# Test migrated tools
test_result = await migrator.test_migrated_tools(migration_result)

print(f"Tool Testing Results:")
print(f"  Passed: {test_result.passed_count}")
print(f"  Failed: {test_result.failed_count}")

for failure in test_result.failures:
    print(f"  ✗ {failure.tool_id}: {failure.test_name} - {failure.error}")
```

### **Migration Rollback**

```python
# Rollback migration if needed
rollback_result = await migrator.rollback_migration(migration_result)

if rollback_result.success:
    print("✓ Migration rolled back successfully")
    print(f"  Restored tools: {rollback_result.restored_count}")
else:
    print("✗ Rollback failed:")
    for error in rollback_result.errors:
        print(f"  - {error.tool_id}: {error.error_message}")

# Partial rollback
tools_to_rollback = ["synapse_consensus", "memory_sqlite"]
partial_rollback = await migrator.rollback_specific_tools(tools_to_rollback)
```

---

## 📚 Migration Examples

### **Complete Migration Workflow**

```python
import asyncio
from langswarm.tools.migration import ToolMigrator, MigrationConfig
from langswarm.tools import ToolRegistry

async def complete_migration_example():
    """Complete example of legacy tool migration"""
    
    # Configure migration
    config = MigrationConfig(
        auto_register=True,
        health_check_enabled=True,
        validation_enabled=True
    )
    
    # Create migrator
    migrator = ToolMigrator(config=config)
    
    # Step 1: Discover legacy tools
    print("Discovering legacy tools...")
    discovery = await migrator.discover_legacy_tools()
    print(f"Found {discovery.total_tools} legacy tools")
    
    # Step 2: Migrate all tools
    print("Migrating tools...")
    migration = await migrator.migrate_discovered_tools(discovery)
    print(f"Migrated {migration.success_count}/{migration.total_processed} tools")
    
    # Step 3: Validate migration
    print("Validating migration...")
    validation = await migrator.validate_migration(migration)
    if validation.is_valid:
        print("✓ Migration validation passed")
    else:
        print(f"✗ {len(validation.errors)} validation errors")
    
    # Step 4: Test migrated tools
    print("Testing migrated tools...")
    test_result = await migrator.test_migrated_tools(migration)
    print(f"Tests: {test_result.passed_count} passed, {test_result.failed_count} failed")
    
    # Step 5: Use migrated tools
    print("Using migrated tools...")
    registry = ToolRegistry()
    
    # List all tools
    all_tools = registry.list_tools()
    print(f"Total tools in registry: {len(all_tools)}")
    
    # Use specific migrated tools
    for tool_info in all_tools[:3]:  # Test first 3 tools
        tool = registry.get_tool(tool_info.tool_id)
        if tool:
            try:
                # Test basic capability
                capabilities = await tool.get_capabilities()
                print(f"✓ {tool_info.tool_id}: {len(capabilities)} capabilities")
            except Exception as e:
                print(f"✗ {tool_info.tool_id}: Error - {e}")
    
    return migration

# Run the migration
if __name__ == "__main__":
    migration_result = asyncio.run(complete_migration_example())
    print(f"Migration completed: {migration_result.success_count} tools migrated")
```

### **Selective Migration**

```python
async def selective_migration_example():
    """Example of selective tool migration"""
    
    migrator = ToolMigrator()
    
    # Migrate only Synapse tools
    synapse_result = await migrator.migrate_synapse_tools()
    print(f"Synapse tools migrated: {synapse_result.success_count}")
    
    # Migrate only specific RAG backends
    rag_backends = ["sqlite", "redis"]
    rag_result = await migrator.migrate_rag_tools(backends=rag_backends)
    print(f"RAG tools migrated: {rag_result.success_count}")
    
    # Migrate only notification plugins
    plugin_types = ["notification"]
    plugin_result = await migrator.migrate_plugin_tools(plugin_types=plugin_types)
    print(f"Plugin tools migrated: {plugin_result.success_count}")
    
    # Combined statistics
    total_migrated = (
        synapse_result.success_count + 
        rag_result.success_count + 
        plugin_result.success_count
    )
    print(f"Total tools migrated: {total_migrated}")

# Run selective migration
asyncio.run(selective_migration_example())
```

---

## 🎯 Migration Best Practices

### **Before Migration**
- **Inventory Legacy Tools**: Document all existing Synapse, RAG, and Plugin tools
- **Test Current Functionality**: Ensure all legacy tools work correctly before migration
- **Backup Configurations**: Save all tool configurations and data
- **Plan Migration Strategy**: Decide on batch vs selective migration approach

### **During Migration**
- **Start Small**: Test migration with non-critical tools first
- **Monitor Progress**: Use migration statistics to track progress
- **Validate Results**: Use validation and testing features
- **Handle Errors**: Review and address migration errors immediately

### **After Migration**
- **Test Functionality**: Verify all migrated tools work correctly
- **Update Code**: Gradually update code to use V2 patterns
- **Monitor Performance**: Track tool performance and health
- **Clean Up**: Remove legacy tool configurations when migration is complete

### **Production Considerations**
- **Staged Rollout**: Migrate development, staging, then production
- **Health Monitoring**: Monitor migrated tool health continuously
- **Rollback Plan**: Have rollback procedures ready
- **Documentation**: Update documentation to reflect V2 usage patterns

---

**LangSwarm V2's legacy tool migration system provides seamless migration from fragmented V1 tool systems to a unified V2 architecture while maintaining 100% backward compatibility and adding powerful new capabilities.**
