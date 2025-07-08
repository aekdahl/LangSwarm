# Filesystem MCP Tool Template

## Description

Read-only access to the local filesystem via MCP protocol. Provides secure file reading and directory listing capabilities with proper path validation and error handling. All operations are read-only for security with UTF-8 text file support.

## Instructions

**Tool Type**: Direct method calls AND intent-based calls
**Tool ID**: filesystem

### Methods Available:
- **list_directory**: List the contents of a directory
- **read_file**: Read the contents of a text file

### How to Use:
**For Direct Calls**: Call list_directory with a directory path to see its contents, or read_file with a file path to read text content. Paths must be valid and accessible on the local filesystem.
**For Intent-Based**: Describe what you want to do with the filesystem in natural language (e.g., "show me what's in the config directory", "read the README file", "check what files are in the project root"). The system will parse your intent and execute the appropriate filesystem operation.

### Parameters (for direct calls):
- **For list_directory**: path (required) - Valid directory path
- **For read_file**: path (required) - Valid file path to text file

### Intent-Based Examples:
- "Show me what files are in the /home/user/documents directory"
- "Read the contents of the configuration file"
- "List all files in the current project directory"
- "What's inside the logs folder?"
- "Read the README.md file"
- "Show me the contents of the scripts directory"

### Usage Context:
- Use when you need to examine directory contents
- Use when you want to read configuration files or text documents
- Use when exploring file system structure
- Use when checking if files exist at specific paths
- Use for any read-only filesystem operations
- Use intent-based calls for natural language filesystem requests

### Output:
- **list_directory**: Returns path and array of directory contents (sorted alphabetically)
- **read_file**: Returns path and file content as UTF-8 encoded string

### Limitations:
- Read-only operations only - no write, delete, or modify operations
- Text files only (UTF-8 encoding) - no binary file support
- Must have proper file system permissions to access paths
- Paths must exist and be accessible
- Intent-based calls require natural language processing to extract file paths

## Brief

Filesystem MCP tool 