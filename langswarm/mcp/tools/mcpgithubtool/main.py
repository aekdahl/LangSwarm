import os
from langswarm.synapse.tools.base import BaseTool
from langswarm.mcp.tools.template_loader import get_cached_tool_template


class MCPGitHubTool(BaseTool):
    """
    GitHub MCP tool for repository and issue management.
    
    This tool provides GitHub API integration through MCP protocol,
    supporting repository operations, issue management, and code analysis.
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, **kwargs):
        """Initialize GitHub MCP tool with simplified architecture"""
        # Load template values for defaults
        current_dir = os.path.dirname(__file__)
        template_values = get_cached_tool_template(current_dir)
        
        # Set defaults for GitHub MCP tool
        description = kwargs.pop('description', "GitHub repository and issue management via MCP")
        instruction = kwargs.pop('instruction', "Use this tool to interact with GitHub repositories, issues, and pull requests")
        brief = kwargs.pop('brief', "GitHub MCP tool")
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        
        # Initialize with BaseTool
        super().__init__(
            name=name,
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )

    def run(self, input_data=None):
        """
        Execute GitHub MCP operations.
        
        For intent-based calls, this would be handled by middleware calling workflows.
        For direct calls, we provide a basic handler for GitHub methods.
        """
        # GitHub methods that could be called directly
        github_methods = {
            "list_repositories": "list_repositories",
            "get_repository": "get_repository", 
            "list_issues": "list_issues",
            "get_issue": "get_issue",
            "create_issue": "create_issue",
            "update_issue": "update_issue",
            "list_pull_requests": "list_pull_requests",
            "get_pull_request": "get_pull_request",
            "create_pull_request": "create_pull_request",
            "merge_pull_request": "merge_pull_request",
            "list_commits": "list_commits",
            "get_commit": "get_commit",
            "list_branches": "list_branches",
            "get_branch": "get_branch",
            "create_branch": "create_branch",
            "get_file_contents": "get_file_contents",
            "create_file": "create_file",
            "update_file": "update_file",
            "delete_file": "delete_file",
            "list_workflows": "list_workflows",
            "run_workflow": "run_workflow",
            "list_workflow_runs": "list_workflow_runs",
            "get_workflow_run": "get_workflow_run",
            "list_comments": "list_comments",
            "create_comment": "create_comment",
            "delete_comment": "delete_comment"
        }
        
        # For direct calls, provide method routing
        if isinstance(input_data, dict) and input_data.get("method") in github_methods:
            # This would need actual GitHub MCP server connection for real calls
            method = input_data.get("method")
            params = input_data.get("params", {})
            return f"GitHub MCP call: {method} with params {params} (requires MCP server connection)"
        
        # For intent-based calls or unstructured input, provide helpful message
        return f"GitHub MCP tool - Use intent-based patterns for complex operations via workflows. Input: {input_data}"
