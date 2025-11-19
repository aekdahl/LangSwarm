# Filesystem Tool

## Description

Smart file system operations with natural language intent understanding for reading, writing, searching, and managing files and directories.

## Instructions

This tool provides file system operations with two calling approaches:

### Intent-Based Calling (Smart File Operations)

Use **`filesystem`** with natural language intent for exploratory or complex file operations:

**Parameters:**
- `intent`: What file operation you want to perform
- `context`: Relevant details (file types, time ranges, purposes)

**When to use:**
- Finding files: "Show me recent log files"
- Searching content: "Find config files that mention API keys"
- Exploring structure: "What Python files changed today?"
- Complex operations: "Clean up temporary files older than 7 days"

**Examples:**
- "Find all Python files modified today" → intent="list Python files modified today", context="code review, recent changes"
- "Show latest server logs" → intent="get most recent log files", context="debugging, server logs directory"

### Direct Method Calling (Specific Operations)

**`filesystem.read_file`** - Read file contents
- **Parameters:** path (required), encoding (optional)
- **Use when:** Reading a specific known file

**`filesystem.write_file`** - Write or update file
- **Parameters:** path, content, mode (write/append)
- **Use when:** Creating or modifying a specific file

**`filesystem.list_directory`** - List directory contents
- **Parameters:** path, pattern (optional), recursive (optional)
- **Use when:** Listing files in a known directory

**`filesystem.search_files`** - Search for files
- **Parameters:** pattern, directory, content_search (optional)
- **Use when:** Finding files matching specific criteria

**`filesystem.manage_permissions`** - File permission operations
- **Parameters:** path, permissions, recursive (optional)
- **Use when:** Changing file access rights

### Decision Guide

**Use intent-based** when:
- User asks vaguely: "show me logs"
- Need to interpret: "find config files"
- Multiple steps: "find and read error logs"
- Time-based: "recent files", "modified today"

**Use direct methods** when:
- Exact path known: `/var/log/app.log`
- Single specific operation: read this file
- Programmatic use: iterating over known paths

### Safety Notes

- Tool respects file system permissions
- Write operations require explicit confirmation
- Sensitive paths may be restricted

## Brief

File system operations with intelligent intent processing for file management and content search.
