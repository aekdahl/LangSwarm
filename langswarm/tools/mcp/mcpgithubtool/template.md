# GitHub Integration Tool

## Description

Intelligent GitHub integration for repository management, issue tracking, pull requests, and code collaboration with natural language intent processing.

## Instructions

This tool provides comprehensive GitHub operations with two calling approaches:

### Intent-Based Calling (Recommended for Complex Operations)

Use **`mcpgithubtool`** with natural language intent for complex or multi-step GitHub operations:

**Parameters:**
- `intent`: What you want to accomplish on GitHub
- `context`: Relevant details (repo, labels, priorities, etc.)

**When to use:**
- Complex multi-step tasks: "Review and merge all approved PRs"
- Report generation: "Summarize all bugs closed this sprint"
- Intelligent automation: "Create release notes from recent commits"
- Contextual operations: "Handle the urgent production issue"

**Examples:**
- "Create a bug report for login issues" → intent="create bug issue for login authentication errors", context="authentication system, high priority"
- "Merge ready pull requests" → intent="merge all approved pull requests", context="release branch, passing tests"

### Direct Method Calling (For Specific Operations)

Use specific methods when you know exactly what to do:

**`mcpgithubtool.create_issue`** - Create a new GitHub issue
- **Parameters:** title, body, labels (array), assignees (optional)
- **Use when:** Creating a single, well-defined issue

**`mcpgithubtool.manage_pr`** - Manage pull requests
- **Parameters:** action (create/merge/review), pr_number, comments
- **Use when:** Specific PR operations with known PR numbers

**`mcpgithubtool.handle_repository`** - Repository operations
- **Parameters:** repo_name, action (create/update/archive)
- **Use when:** Managing repository settings or structure

**`mcpgithubtool.track_milestones`** - Milestone management
- **Parameters:** milestone_name, due_date, issues_list
- **Use when:** Creating or updating project milestones

**`mcpgithubtool.generate_reports`** - Generate activity reports
- **Parameters:** report_type, date_range, filters
- **Use when:** Extracting metrics or generating summaries

### Decision Guide

**Use intent-based** when:
- User request is vague or exploratory
- Operation requires interpretation
- Multiple steps might be needed
- Context matters more than exact parameters

**Use direct methods** when:
- User provides specific details (exact issue title, PR number)
- Single, atomic operation
- You have all required parameters

### Common Scenarios

1. **Bug reporting**: Intent-based → interprets severity, assigns labels
2. **PR management**: Direct method → you have PR number
3. **Release planning**: Intent-based → analyzes what needs to be done
4. **Specific issue creation**: Direct method → you have exact title/body

## Brief

GitHub integration with intelligent intent processing for repository management and automation.
