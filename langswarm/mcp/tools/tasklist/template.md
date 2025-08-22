# Tasklist MCP Tool Template

## Description

Task management MCP tool for creating, updating, listing, and deleting tasks with smart persistence. Provides comprehensive task management capabilities with priority levels, completion tracking, notes, timestamps, and intelligent storage using LangSwarm memory adapters (BigQuery, Redis, SQLite, ChromaDB) with automatic fallback to JSON file storage. Supports both direct method calls and natural language intent-based operations for seamless integration into workflows.

## Instructions

**Tool Type**: Direct method calls AND intent-based calls
**Tool ID**: tasklist

### Methods Available:
- **create_task**: Create a new task with description, priority, and notes
- **update_task**: Update existing task properties (description, completion, priority, notes)
- **list_tasks**: List all tasks sorted by priority
- **delete_task**: Remove a task by its ID
- **get_task**: Retrieve details of a specific task by ID

### How to Use:
**For Direct Calls**: Call specific methods with structured parameters. Use create_task to add new tasks, update_task to modify existing ones, list_tasks to see all tasks, delete_task to remove tasks, and get_task to view specific task details.

**For Intent-Based**: Describe what you want to do with your tasks in natural language (e.g., "create a task to write documentation", "mark task-1 as completed", "show me all my tasks", "delete the API testing task"). The system will parse your intent and execute the appropriate task operation with intelligent parameter extraction.

### Parameters (for direct calls):

**For create_task**:
- description (required) - Text describing what needs to be done
- priority (optional, default=1) - Priority level (1=highest, 5=lowest)
- notes (optional) - Additional context or details

**For update_task**:
- task_id (required) - The task identifier (e.g., "task-1")
- description (optional) - New task description
- completed (optional) - Boolean completion status (true/false)
- priority (optional) - New priority level (1-5)
- notes (optional) - Updated notes or additional context

**For delete_task**:
- task_id (required) - The task identifier to delete

**For get_task**:
- task_id (required) - The task identifier to retrieve

**For list_tasks**:
- No parameters required

### Intent-Based Examples:
- "Create a task to implement user authentication with priority 2"
- "Add a high-priority task for fixing the database connection bug"
- "Mark task-3 as completed"
- "Update task-1 description to include testing requirements"
- "Show me all my current tasks"
- "List all incomplete tasks"
- "Delete task-5"
- "Remove the old documentation task"
- "Get details for task-2"
- "What's the status of my API development task?"

### Direct Call Examples:
```json
// Create a new task
{
  "method": "create_task",
  "params": {
    "description": "Write API documentation",
    "priority": 2,
    "notes": "Include examples and error codes"
  }
}

// Update task completion
{
  "method": "update_task",
  "params": {
    "task_id": "task-1",
    "completed": true,
    "notes": "Completed successfully, ready for review"
  }
}

// List all tasks
{
  "method": "list_tasks",
  "params": {}
}

// Delete a task
{
  "method": "delete_task",
  "params": {
    "task_id": "task-3"
  }
}
```

### Usage Context:
- Use when you need to track project tasks and their progress
- Use for breaking down complex projects into manageable tasks
- Use when coordinating multiple subtasks in structured workflows
- Use for maintaining persistent todo lists across sessions
- Use when you need prioritized task management
- Use for tracking task completion status and progress
- Use intent-based calls for natural language task management requests
- Use direct calls when integrating with automated workflows or scripts

### Output:

**create_task**: Returns task object with generated task_id, description, completion status (false), priority, notes, and success message

**update_task**: Returns updated task object with all current properties and confirmation message

**list_tasks**: Returns array of all tasks sorted by priority, total count, and summary message

**delete_task**: Returns task_id, success status, and confirmation message

**get_task**: Returns complete task details including task_id, description, completion status, priority, notes, and retrieval message

### Task Structure:
Each task contains:
- **task_id**: Unique identifier (e.g., "task-1", "task-2")
- **description**: Main task description text
- **completed**: Boolean completion status (true/false)
- **priority**: Integer priority level (1=highest, 5=lowest)
- **notes**: Additional context or comments

### Smart Data Persistence:
- **Auto-Detection**: Automatically uses LangSwarm memory adapters when environment is configured
- **Memory Adapters**: BigQuery, Redis, SQLite, ChromaDB integration for enterprise storage
- **Fallback Storage**: JSON file (tasklist_data.json) when memory adapters unavailable
- **Rich Metadata**: Tasks stored with searchable metadata and timestamps
- **Cross-Session Persistence**: Data persists across tool restarts and system reboots
- **Thread-Safe Operations**: Concurrent access handling for all storage types

### Limitations:
- Local storage only - tasks are not synchronized across different instances
- JSON file storage may not be suitable for extremely large task lists (1000+ tasks)
- No built-in task scheduling or reminder functionality
- Priority levels are simple integers without advanced sorting rules
- Intent-based calls require natural language processing for parameter extraction
- No user authentication - all tasks are accessible to any user of the tool

### Error Handling:
- Returns clear error messages for invalid task IDs
- Graceful handling of missing required parameters
- Automatic validation of priority levels and data types
- Informative messages for file system errors or permission issues
- Recovery mechanisms for corrupted data files

## Brief

Task management MCP tool with local persistence supporting create, update, list, delete operations via direct calls or natural language intents.