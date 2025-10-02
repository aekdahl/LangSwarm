# Tasklist MCP Tool

A comprehensive task management tool built on the MCP (Model-Compatible Protocol) framework with local mode support for LangSwarm workflows.

## Features

- ✅ **Full CRUD Operations**: Create, Read, Update, Delete tasks
- 📱 **Local Mode Support**: Zero-latency local execution
- 🧠 **Smart Persistence**: Auto-detects and uses LangSwarm memory adapters (BigQuery, Redis, SQLite, ChromaDB)
- 💾 **Fallback Storage**: Automatic JSON file backup when memory adapters unavailable
- 🎯 **Priority Management**: 5-level priority system (1=highest, 5=lowest)
- 📝 **Rich Task Data**: Description, completion status, priority, notes, timestamps
- 🤖 **Intent-Based Interface**: Natural language task management
- 🔧 **Direct API Calls**: Structured method invocation
- 🛡️ **Error Handling**: Comprehensive validation and error recovery
- 🔄 **Memory Integration**: Seamlessly integrates with your existing LangSwarm memory configuration

## Quick Start

### Using with LangSwarm

**Basic Configuration (Auto-Detection)**:
```yaml
tools:
  - id: tasklist
    type: mcptasklist
    description: "Smart task management with auto-detected persistence"
    local_mode: true
    pattern: "intent"
    main_workflow: "use_tasklist_tool"
    permission: anonymous
```

**With Memory Configuration**:
```yaml
# Global memory configuration (recommended)
memory: production  # Auto-detects BigQuery/Redis/SQLite

tools:
  - id: tasklist
    type: mcptasklist
    description: "Enterprise task management with smart persistence"
    local_mode: true
    pattern: "intent"
    main_workflow: "use_tasklist_tool"
    permission: anonymous
```

### Example Usage

**Natural Language (Intent-Based)**:
```
"Create a high-priority task for implementing user authentication"
"Mark task-1 as completed"
"Show me all my current tasks"
"Delete the old documentation task"
```

**Direct API Calls**:
```python
# Create a task
tool.run({
    "method": "create_task",
    "params": {
        "description": "Write API documentation",
        "priority": 2,
        "notes": "Include examples"
    }
})

# List all tasks
tool.run({
    "method": "list_tasks",
    "params": {}
})
```

## API Reference

### Methods

#### create_task
Create a new task with description, priority, and optional notes.

**Parameters**:
- `description` (string, required): Task description
- `priority` (integer, optional, default=1): Priority level (1-5)
- `notes` (string, optional): Additional notes

**Returns**: Task object with generated ID and metadata

#### update_task
Update properties of an existing task.

**Parameters**:
- `task_id` (string, required): Task identifier
- `description` (string, optional): New description
- `completed` (boolean, optional): Completion status
- `priority` (integer, optional): New priority level
- `notes` (string, optional): Updated notes

**Returns**: Updated task object

#### list_tasks
Retrieve all tasks sorted by priority.

**Parameters**: None

**Returns**: Array of tasks with count and summary

#### delete_task
Remove a task by its ID.

**Parameters**:
- `task_id` (string, required): Task identifier

**Returns**: Deletion confirmation with success status

#### get_task
Get details of a specific task.

**Parameters**:
- `task_id` (string, required): Task identifier

**Returns**: Complete task details

## Task Data Structure

```json
{
  "task_id": "task-1",
  "description": "Write API documentation",
  "completed": false,
  "priority": 2,
  "notes": "Include examples and error codes"
}
```

## Smart Persistence

The tasklist tool automatically detects and uses your LangSwarm memory configuration for optimal persistence:

### **Auto-Detection**
The tool automatically uses memory adapters when these environment variables are present:
```bash
# BigQuery
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Redis  
export REDIS_URL="redis://localhost:6379"

# Or general LangSwarm memory setting
export LANGSWARM_MEMORY="production"
```

### **Storage Options**

#### **🧠 Memory Adapter Storage (Preferred)**
- **BigQuery**: Enterprise-scale storage with analytics
- **Redis**: High-performance in-memory storage  
- **SQLite**: Local database storage
- **ChromaDB**: Vector-based storage with search capabilities
- **Format**: Structured documents with rich metadata
- **Benefits**: Searchable, scalable, integrates with LangSwarm analytics

#### **💾 File Storage (Fallback)**
- **Location**: `tasklist_data.json` in working directory
- **Format**: JSON with tasks and metadata
- **Use Case**: Development, environments without memory adapters

### **Configuration Examples**

#### **Basic (Auto-Detection)**
```yaml
tools:
  - id: tasklist
    type: mcptasklist
    # Automatically uses memory adapter if available
```

#### **Explicit Memory Adapter**
```python
# In Python code
from langswarm.mcp.tools.tasklist.main import TasklistMCPTool
from langswarm.memory.adapters._langswarm.bigquery.main import BigQueryAdapter

adapter = BigQueryAdapter(
    identifier="my_tasks",
    project_id="my-project", 
    dataset_id="tasks",
    table_id="user_tasks"
)

tool = TasklistMCPTool(
    identifier="my_tasklist",
    use_memory_adapter=True,
    memory_adapter=adapter
)
```

#### **Force File Storage**
```python
tool = TasklistMCPTool(
    identifier="my_tasklist", 
    use_memory_adapter=False  # Force JSON file storage
)
```

## Integration Patterns

### Workflow Integration
```yaml
workflows:
  - steps:
    - tool: tasklist
      input: |
        {
          "method": "create_task",
          "params": {
            "description": "${task_description}",
            "priority": 1
          }
        }
```

### Agent Integration
The tool includes pre-built agents for:
- Input normalization
- Action classification
- Parameter extraction
- Response formatting
- Error handling

## Advanced Usage

### Custom Workflows
The tool supports multiple workflow patterns:
- `use_tasklist_tool`: Full intent-based processing
- `direct_task_workflow`: Direct API calls
- `list_tasks_workflow`: Quick task listing
- `create_task_workflow`: Dedicated task creation

### Error Handling
Comprehensive error handling for:
- Invalid task IDs
- Missing parameters
- File system errors
- Data corruption
- Concurrent access

## Development

### Running Standalone
```bash
cd langswarm/mcp/tools/tasklist
python main.py
```

### Testing Different Storage Modes

**Auto-Detection Mode (Default)**:
```python
from langswarm.mcp.tools.tasklist.main import TasklistMCPTool

# Auto-detects memory adapter based on environment
tool = TasklistMCPTool(identifier="test_tasklist")
result = tool.run({
    "method": "create_task",
    "params": {
        "description": "Test task with auto-detection",
        "priority": 1
    }
})
print(result)
```

**Force File Storage Mode**:
```python
# Force JSON file storage (development/testing)
tool = TasklistMCPTool(
    identifier="test_file_storage",
    use_memory_adapter=False
)
result = tool.run({
    "method": "create_task",
    "params": {
        "description": "Test task with file storage",
        "priority": 1
    }
})
print(result)
```

**Explicit Memory Adapter**:
```python
from langswarm.memory.adapters._langswarm.sqlite.main import SQLiteAdapter

# Use specific memory adapter
adapter = SQLiteAdapter(
    identifier="tasklist_dev",
    db_path="dev_tasks.db"
)

tool = TasklistMCPTool(
    identifier="test_memory",
    use_memory_adapter=True,
    memory_adapter=adapter
)
result = tool.run({
    "method": "create_task",
    "params": {
        "description": "Test task with SQLite",
        "priority": 1
    }
})
print(result)
```

### Environment Setup for Auto-Detection

**BigQuery (Production)**:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

**Redis (High-Performance)**:
```bash
export REDIS_URL="redis://localhost:6379"
```

**General LangSwarm Memory**:
```bash
export LANGSWARM_MEMORY="production"
```

## Migration from Synapse Tool

This MCP tool is a direct replacement for the legacy `langswarm.synapse.tools.tasklist` with significantly enhanced features:

- ✅ **Local mode support** (new)
- ✅ **MCP protocol compliance** (new) 
- ✅ **Smart persistence with memory adapters** (new)
- ✅ **Auto-detection of storage backends** (new)
- ✅ **Rich metadata and timestamps** (new)
- ✅ **BigQuery/Redis/SQLite integration** (new)
- ✅ **Intent-based interface** (enhanced)
- ✅ **Persistent storage** (enhanced with memory adapters)
- ✅ **Priority management** (same)
- ✅ **CRUD operations** (same)

### Migration Benefits
- **Zero Config**: Auto-detects your existing LangSwarm memory configuration
- **Enterprise Ready**: Uses BigQuery, Redis, or SQLite for production workloads
- **Backwards Compatible**: Same API with enhanced persistence
- **Performance**: In-memory Redis storage for high-frequency task operations
- **Analytics**: Tasks stored with searchable metadata for reporting

### Migration Steps
1. Replace tool configuration in `tools.yaml`:
   ```yaml
   # Old synapse tool
   - id: tasklist
     type: tasklist
   
   # New MCP tool with smart persistence
   - id: tasklist
     type: mcptasklist
     local_mode: true
   ```
2. Update workflow references from synapse to MCP
3. Test functionality with existing workflows  
4. Verify persistence works with your memory configuration
5. Remove legacy tool dependencies

## Performance & Troubleshooting

### Storage Performance Comparison

| Storage Backend | Best For | Performance | Scalability |
|----------------|----------|-------------|-------------|
| **Redis** | High-frequency operations | ⚡ Excellent | 🚀 High |
| **SQLite** | Local development | ⚡ Very Good | 📈 Medium |
| **BigQuery** | Analytics & reporting | 📊 Good | 🚀 Enterprise |
| **File (JSON)** | Quick prototyping | 📝 Basic | 📈 Limited |

### Troubleshooting

**Tasks not persisting?**
```bash
# Check which storage mode is active
python3 -c "
from langswarm.mcp.tools.tasklist.main import TaskStorage
storage = TaskStorage()
print(f'Using memory adapter: {storage.use_memory_adapter}')
if storage.memory_adapter:
    print(f'Adapter type: {type(storage.memory_adapter).__name__}')
"
```

**Force specific storage mode:**
```bash
# Test file storage
export LANGSWARM_MEMORY="false"

# Test BigQuery 
export GOOGLE_CLOUD_PROJECT="your-project"
export LANGSWARM_MEMORY="production"

# Test Redis
export REDIS_URL="redis://localhost:6379"
```

**Check task data:**
```bash
# File storage
cat tasklist_data.json

# BigQuery (requires bq CLI)
bq query "SELECT * FROM your_dataset.agent_memory WHERE metadata.type = 'task'"
```

### Environment Validation

Quick validation script:
```bash
python3 -c "
import os
print('Environment Check:')
print(f'GOOGLE_CLOUD_PROJECT: {os.getenv(\"GOOGLE_CLOUD_PROJECT\", \"Not set\")}')
print(f'REDIS_URL: {os.getenv(\"REDIS_URL\", \"Not set\")}')
print(f'LANGSWARM_MEMORY: {os.getenv(\"LANGSWARM_MEMORY\", \"Not set\")}')
"
```

## License

Part of the LangSwarm framework. See main project license.