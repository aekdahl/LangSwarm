# Tasklist Tool

## Description

Smart task management with natural language task creation for project management, productivity tracking, and team coordination.

## Instructions

This tool provides task management with two calling approaches:

### Intent-Based Calling (Natural Task Management)

Use **`tasklist`** with natural language intent for intelligent task operations:

**Parameters:**
- `intent`: What task operation you want to perform
- `context`: Relevant details (deadlines, priorities, team members)

**When to use:**
- Creating tasks from descriptions: "Add task to update security docs by Friday"
- Finding tasks: "Show overdue tasks for development team"
- Bulk operations: "Mark all testing tasks as completed"
- Complex queries: "What's left to do before the release?"

**Examples:**
- "Add high-priority security review task" → intent="create task to review and update security documentation by Friday", context="security audit, compliance deadline, high priority"
- "Show overdue tasks" → intent="list all overdue tasks for the development team", context="sprint review, task tracking"

### Direct Method Calling (Specific Operations)

**`tasklist.add_task`** - Create a new task
- **Parameters:** title, description (optional), priority, due_date (optional)
- **Use when:** Adding a single well-defined task

**`tasklist.update_task`** - Modify existing task
- **Parameters:** task_id, updates (dict of fields to change)
- **Use when:** Updating specific task with known ID

**`tasklist.list_tasks`** - Query tasks
- **Parameters:** filters (status/priority/assignee), sort_by
- **Use when:** Getting tasks with specific criteria

**`tasklist.complete_task`** - Mark task as done
- **Parameters:** task_id, completion_notes (optional)
- **Use when:** Marking specific task complete

**`tasklist.set_priorities`** - Reorder task priorities
- **Parameters:** task_ids (list), priority_order
- **Use when:** Bulk priority adjustments

### Decision Guide

**Use intent-based** when:
- User describes tasks naturally
- Creating from conversation
- Complex filtering needed
- Exploring what needs to be done

**Use direct methods** when:
- You have task IDs
- Simple CRUD operations
- Programmatic task management
- Known exact parameters

### Common Scenarios

1. **Task creation from chat**: Intent-based
2. **Mark specific task done**: complete_task with ID
3. **Sprint planning**: Intent-based for filtering and analysis
4. **Status updates**: update_task with known ID

## Brief

Task management with intelligent intent processing for productivity and project coordination.
