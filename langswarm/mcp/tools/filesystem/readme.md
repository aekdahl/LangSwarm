# 🗂 Enhanced Filesystem MCP Tool

A comprehensive filesystem access tool with configurable permissions, full CRUD operations, and **Google Cloud Storage (GCS) support** implemented using the MCP (Model-Compatible Protocol).

---

## ✅ Features

- **🔐 Permission-Based Access**: Configurable read-only, read-write, and forbidden zones
- **📁 Full CRUD Operations**: Create, read, update, delete files and directories
- **☁️ Google Cloud Storage**: Seamless GCS integration with gs:// URLs
- **🔀 Hybrid Operations**: Mix local filesystem and cloud storage operations
- **🛡️ Security Features**: Path validation, permission checking, safety controls
- **📊 Enhanced Metadata**: File info, timestamps, permissions, sizes
- **🔧 Local Mode**: Direct filesystem operations without HTTP server
- **🔗 MCP Compatible**: Standard MCP protocol implementation
- **⚡ LangChain Integration**: Works seamlessly with LangSwarm agents

---

## 🔐 Permission System

The tool uses a zone-based permission system for enhanced security:

- **`read_only`**: Can list directories and read files
- **`read_write`**: Full CRUD operations allowed
- **`forbidden`**: No access allowed

### Default Permissions

```python
DEFAULT_PERMISSIONS = {
    # Local filesystem permissions
    "/": "read_only",                      # Root is read-only
    "~/": "read_only",                     # Home is read-only  
    "~/agent_workspace/": "read_write",    # Agent workspace allows CRUD
    
    # Google Cloud Storage permissions  
    "gs://": "read_only",                  # GCS buckets read-only by default
    "gs://agent-workspace/": "read_write", # Agent GCS workspace allows CRUD
}
```

---

## 📁 Folder Structure

```
mcp/tools/filesystem/
├── main.py            # Enhanced MCP server with CRUD + permissions
├── workflows.yaml     # LangSwarm-compatible tool usage workflows
├── agents.yaml        # Specialized agents for filesystem operations
├── template.md        # LLM-consumable tool instructions
└── readme.md          # You're here
```

---

## ⚙️ Configuration

### Basic Configuration

```yaml
# tools.yaml
tools:
  - id: filesystem
    type: mcpfilesystem
    description: "Enhanced filesystem access with CRUD operations"
```

### Advanced Configuration with Custom Permissions

```yaml
# tools.yaml
tools:
  - id: filesystem_secure
    type: mcpfilesystem
    description: "Secure filesystem with custom permission zones"
    gcs_project_id: "your-gcp-project-id"  # Optional GCS project
    permissions:
      # Local permissions
      "/": "read_only"
      "/tmp/": "read_write"
      "/home/user/projects/": "read_write"
      "/home/user/sensitive/": "forbidden"
      "~/agent_workspace/": "read_write"
      
      # GCS permissions
      "gs://": "read_only"
      "gs://data-bucket/": "read_only"
      "gs://agent-workspace/": "read_write"
      "gs://sensitive-bucket/": "forbidden"
```

### GCS-Only Configuration

```yaml
# tools.yaml  
tools:
  - id: gcs_filesystem
    type: mcpfilesystem
    description: "GCS-focused filesystem with minimal local access"
    gcs_project_id: "your-gcp-project-id"
    permissions:
      # Minimal local access
      "~/agent_workspace/temp/": "read_write"
      "/": "forbidden"
      
      # Extensive GCS access
      "gs://data-lake/": "read_only"
      "gs://ml-models/": "read_only" 
      "gs://agent-outputs/": "read_write"
```

### Agent Configuration

```yaml
# agents.yaml
agents:
  - id: file_manager
    agent_type: openai
    model: gpt-4o
    system_prompt: |
      You have access to enhanced filesystem operations with permission-based access:
      
      **Read Operations (available in read_only and read_write zones):**
      - list_directory: List directory contents with metadata
      - read_file: Read file contents with encoding support
      - get_file_info: Get detailed file/directory information
      
      **Write Operations (require read_write permissions):**
      - write_file: Create or overwrite files
      - update_file: Append to or update files
      - delete_file: Delete files or directories
      - create_directory: Create new directories
      
      **Always check permissions first using get_file_info!**
      
      Use structured MCP calls:
      {
        "mcp": {
          "tool": "filesystem",
          "method": "write_file",
          "params": {
            "path": "~/agent_workspace/output.txt",
            "content": "Hello, World!",
            "create_dirs": true
          }
        }
      }
    tools:
      - filesystem
```

---

## 🔧 Available Methods

### Read Operations

#### list_directory
Lists directory contents with enhanced metadata.

**Input:**
```json
{
  "path": "/path/to/directory",
  "show_hidden": false,
  "recursive": false
}
```

**Output:**
```json
{
  "path": "/path/to/directory",
  "contents": [
    {
      "name": "file1.txt",
      "type": "file",
      "size": 1024,
      "modified": "2024-01-15T10:30:00",
      "permissions": "644"
    }
  ],
  "total_items": 1,
  "permission_level": "read_only"
}
```

#### read_file
Reads file contents with encoding support.

**Input:**
```json
{
  "path": "/path/to/file.txt",
  "encoding": "utf-8"
}
```

**Output:**
```json
{
  "path": "/path/to/file.txt",
  "content": "File contents here...",
  "size_bytes": 1024,
  "encoding": "utf-8"
}
```

#### get_file_info
Gets detailed file/directory information.

**Input:**
```json
{
  "path": "/path/to/item"
}
```

**Output:**
```json
{
  "path": "/path/to/item",
  "exists": true,
  "type": "file",
  "size_bytes": 1024,
  "permissions": "644",
  "created": "2024-01-15T10:00:00",
  "modified": "2024-01-15T10:30:00",
  "permission_level": "read_write"
}
```

### Write Operations (Require read_write permissions)

#### write_file
Creates or overwrites a file.

**Input:**
```json
{
  "path": "~/agent_workspace/new_file.txt",
  "content": "Hello, World!",
  "encoding": "utf-8",
  "create_dirs": true
}
```

**Output:**
```json
{
  "path": "~/agent_workspace/new_file.txt",
  "status": "created",
  "bytes_written": 13
}
```

#### update_file
Updates file content by appending or overwriting.

**Input:**
```json
{
  "path": "~/agent_workspace/log.txt",
  "content": "\nNew log entry",
  "mode": "append",
  "encoding": "utf-8"
}
```

**Output:**
```json
{
  "path": "~/agent_workspace/log.txt",
  "status": "appended",
  "bytes_written": 15
}
```

#### delete_file
Deletes a file or directory.

**Input:**
```json
{
  "path": "~/agent_workspace/temp.txt",
  "force": false
}
```

**Output:**
```json
{
  "path": "~/agent_workspace/temp.txt",
  "status": "deleted",
  "deleted_type": "file"
}
```

#### create_directory
Creates a new directory.

**Input:**
```json
{
  "path": "~/agent_workspace/new_folder",
  "parents": true
}
```

**Output:**
```json
{
  "path": "~/agent_workspace/new_folder",
  "status": "created"
}
```

---

## 🛡️ Safety & Security Features

### Permission Checking
- Every operation checks permissions first
- Clear error messages for permission denials
- Configurable permission zones

### Path Validation
- Prevents path traversal attacks (`../` blocked)
- Normalizes and validates all paths
- Absolute path resolution

### Safe Defaults
- Read-only access by default
- Write operations require explicit read_write permission
- Empty directories only deleted by default (use `force: true` for non-empty)

### Error Handling
- Comprehensive error messages
- Permission errors clearly identified
- File not found vs permission denied distinction

---

## 🚀 Usage Examples

### Safe Document Reading
```python
# Agent can read from read_only zones
result = fs_tool.run({
    "method": "read_file",
    "params": {"path": "/home/user/documents/readme.txt"}
})
```

### Secure File Creation
```python
# Agent can create files in read_write zones
result = fs_tool.run({
    "method": "write_file", 
    "params": {
        "path": "~/agent_workspace/output.json",
        "content": '{"result": "success"}',
        "create_dirs": true
    }
})
```

### Permission Checking
```python
# Check permissions before operations
info = fs_tool.run({
    "method": "get_file_info",
    "params": {"path": "/some/path"}
})

if info["permission_level"] == "read_write":
    # Proceed with write operations
    pass
```

---

## 🧩 Integration Example

```python
from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool

# Create filesystem tool with custom permissions
custom_permissions = {
    "/": "read_only",
    "/tmp/": "read_write", 
    "/workspace/": "read_write",
    "/sensitive/": "forbidden"
}

fs_tool = FilesystemMCPTool(
    identifier="filesystem",
    name="Enhanced Filesystem Tool",
    permissions=custom_permissions
)

# Use in agent for safe file operations
result = fs_tool.run({
    "method": "write_file",
    "params": {
        "path": "/workspace/output.txt",
        "content": "Generated content"
    }
})
```

---

## 🔄 Migration from Original Filesystem Tool

The enhanced tool is backward compatible:

- Original `list_directory` and `read_file` methods work unchanged
- New methods provide additional functionality
- Permission system adds security without breaking existing workflows
- Configuration remains the same for basic usage

---

## 📋 Best Practices

1. **Always check permissions first** using `get_file_info`
2. **Use specific permission zones** rather than broad access
3. **Set `create_dirs: true`** when creating files in new directories
4. **Use `force: false`** by default for delete operations
5. **Handle permission errors gracefully** in agent workflows
6. **Test permission configurations** before deploying agents

---

## 🔍 Troubleshooting

### Permission Denied Errors
- Check if path is in a `read_write` zone for write operations
- Verify permission configuration matches intended access patterns
- Use `get_file_info` to check current permission level

### Path Not Found Errors
- Ensure parent directories exist or use `create_dirs: true`
- Check path spelling and case sensitivity
- Verify path is accessible and not in `forbidden` zone

### File Encoding Issues
- Specify correct encoding for non-UTF8 files
- Use binary operations for non-text files (not currently supported)
- Check file is actually text content before reading

---

## 🛠 Dependencies

- Python 3.8+
- FastAPI (for HTTP mode)
- Uvicorn (for HTTP mode)
- Pydantic (for schema validation)

Install with:
```bash
pip install fastapi uvicorn pydantic
```

---

## 🧭 Roadmap

- ✅ **Enhanced CRUD operations** (completed)
- ✅ **Permission-based access control** (completed)
- ✅ **Path safety validation** (completed)
- ✅ **Enhanced metadata** (completed)
- 🔄 **Binary file support** (planned)
- 🔄 **File watching/monitoring** (planned)
- ☁️ **Pluggable backends** (S3, GCS, etc.)
- 🔐 **Advanced permission templates** (planned)

---

## 📚 References

- [Anthropic MCP Spec](https://github.com/anthropics/mcp)
- LangSwarm internal: `use_tool()`, `workflows.yaml`, `mcp_call()`
- [LangSwarm MCP Tools Guide](../../README.md)

---

Built with ❤️ for secure, agent-first filesystem operations.