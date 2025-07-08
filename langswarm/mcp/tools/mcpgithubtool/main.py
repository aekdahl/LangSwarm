import os
from langswarm.synapse.tools.base import BaseTool
from langswarm.mcp.tools.template_loader import get_cached_tool_template


class MCPGitHubTool(BaseTool):
    """
    GitHub MCP tool that properly inherits from BaseTool.
    
    This tool is designed for intent-based calls with complex GitHub operations
    like creating issues, managing pull requests, and repository management.
    It leverages workflows for orchestration and MCP servers for GitHub API access.
    """

    # Flag to enable Pydantic bypass and MCP functionality
    _is_mcp_tool = True

    def __init__(
        self,
        identifier: str,
        name: str,
        description: str = "",
        instruction: str = "",
        brief: str = "",
        **kwargs
    ):
        """Initialize GitHub MCP tool with simplified architecture"""
        # Load template values for defaults
        current_dir = os.path.dirname(__file__)
        template_values = get_cached_tool_template(current_dir)
        
        # Set defaults from template if not provided
        description = description or template_values.get('description', 'GitHub repository management via MCP with full API access')
        instruction = instruction or template_values.get('instruction', 'Use this tool for GitHub operations like creating issues, managing PRs, and repository management')
        brief = brief or template_values.get('brief', 'GitHub MCP tool')
        
        # GitHub MCP tools are typically intent-based with workflows
        # Set default pattern and workflow if not specified
        if "pattern" not in kwargs:
            kwargs["pattern"] = "intent"
        if "main_workflow" not in kwargs and kwargs.get("pattern") == "intent":
            kwargs["main_workflow"] = "main_workflow"  # From workflows.yaml
        
        # Initialize with BaseTool (handles all MCP setup automatically)
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
