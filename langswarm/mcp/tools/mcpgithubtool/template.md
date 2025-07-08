# GitHub MCP Tool Template

## Description

Local GitHub repository management tool providing comprehensive access to repository operations, Git commands, and project management capabilities. Enables repository cloning, branch management, file operations, and Git workflow automation through a local MCP interface.

## Instructions

**Tool Type**: Direct method calls AND intent-based calls
**Tool ID**: mcpgithubtool

### Methods Available:
- **clone_repository**: Clone a GitHub repository to local system
- **create_branch**: Create new Git branch
- **commit_changes**: Commit staged changes with message
- **push_changes**: Push local changes to remote repository
- **pull_changes**: Pull latest changes from remote
- **get_repository_info**: Get repository status and information
- **list_branches**: List all local and remote branches
- **create_pull_request**: Create pull request (requires GitHub API access)
- **merge_pull_request**: Merge pull request (requires GitHub API access)

### How to Use:
**For Direct Calls**: Call specific methods with required parameters (repository URL, branch names, commit messages, etc.)
**For Intent-Based**: Describe what you want to accomplish with Git/GitHub in natural language (e.g., "clone the user/repo repository", "create a new branch for feature development", "commit my changes with a descriptive message"). The system will parse your intent and execute the appropriate Git operations.

### Parameters (for direct calls):
- **repository_url**: GitHub repository URL (for clone operations)
- **branch_name**: Name of branch to create, switch to, or operate on
- **commit_message**: Descriptive message for commits
- **file_paths**: Array of file paths for selective operations
- **pull_request_title**: Title for pull request creation
- **pull_request_body**: Description for pull request

### Intent-Based Examples:
- "Clone the microsoft/vscode repository to my local machine"
- "Create a new branch called 'feature/user-authentication'"
- "Commit my changes with the message 'Add user login functionality'"
- "Push my feature branch to the remote repository"
- "Pull the latest changes from the main branch"
- "Show me the status of my repository"
- "Create a pull request for my feature branch"
- "List all available branches in this repository"

### Usage Context:
- Use when you need to manage GitHub repositories locally
- Use when performing Git operations (clone, commit, push, pull)
- Use when creating and managing branches
- Use when working with pull requests
- Use when checking repository status and information
- Use for automated Git workflow operations
- Use intent-based calls for natural language Git operations

### Output:
Returns operation results, repository information, branch lists, commit status, and error messages for failed operations.

### Limitations:
- Requires local Git installation and configuration
- GitHub API operations require authentication tokens
- Pull request operations require appropriate repository permissions
- Network connectivity required for remote operations
- Intent-based calls require natural language processing to extract Git parameters

## Brief

GitHub MCP tool 