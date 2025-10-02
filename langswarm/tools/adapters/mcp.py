"""
LangSwarm V2 MCP Tool Adapter

Adapter for existing MCP tools to provide enhanced V2 interface compatibility.
"""

from typing import Any, Dict, List, Optional
import logging

from ..interfaces import ToolType, ToolCapability
from ..base import ToolSchema
from .base import LegacyToolAdapter

logger = logging.getLogger(__name__)


class MCPToolAdapter(LegacyToolAdapter):
    """
    Adapter for existing MCP tools to V2 interface.
    
    MCP tools typically have:
    - run(input_data) method for execution
    - MCP server integration
    - Local and remote execution modes
    - Tool-specific functionality
    """
    
    def __init__(self, mcp_tool: Any, **kwargs):
        # Determine MCP tool type
        mcp_type = self._determine_mcp_type(mcp_tool)
        
        super().__init__(
            legacy_tool=mcp_tool,
            tool_type=self._map_to_v2_type(mcp_type),
            capabilities=[
                ToolCapability.READ,
                ToolCapability.WRITE,
                ToolCapability.EXECUTE,
                ToolCapability.ASYNC
            ],
            **kwargs
        )
        
        self._adapter_type = "mcp"
        self._mcp_type = mcp_type
        
        # Add MCP-specific tags
        self.add_tag("mcp")
        self.add_tag(mcp_type)
        
        # Add enhanced capabilities if available
        if hasattr(mcp_tool, 'local_mode'):
            self.add_tag("local_mode")
        if hasattr(mcp_tool, 'mcp_server'):
            self.add_tag("server_integrated")
        
        # Add MCP-specific methods
        self._add_mcp_methods()
        
        
        self._logger.info(f"Adapted MCP tool: {self.metadata.id} ({mcp_type})")
    
    def _determine_mcp_type(self, tool: Any) -> str:
        """Determine the type of MCP tool"""
        class_name = tool.__class__.__name__.lower()
        
        if 'filesystem' in class_name or 'file' in class_name:
            return "filesystem"
        elif 'github' in class_name or 'git' in class_name:
            return "github"
        elif 'database' in class_name or 'sql' in class_name:
            return "database"
        elif 'workflow' in class_name:
            return "workflow"
        elif 'form' in class_name:
            return "forms"
        elif 'voice' in class_name or 'realtime' in class_name:
            return "voice"
        elif 'tasklist' in class_name or 'task' in class_name:
            return "tasklist"
        elif 'remote' in class_name:
            return "remote"
        elif 'indexer' in class_name or 'codebase' in class_name:
            return "indexer"
        elif 'message' in class_name or 'queue' in class_name:
            return "messaging"
        else:
            return "generic"
    
    def _map_to_v2_type(self, mcp_type: str) -> ToolType:
        """Map MCP tool type to V2 ToolType"""
        mapping = {
            "filesystem": ToolType.FILESYSTEM,
            "github": ToolType.API,
            "database": ToolType.DATABASE,
            "workflow": ToolType.WORKFLOW,
            "forms": ToolType.UTILITY,
            "voice": ToolType.UTILITY,
            "tasklist": ToolType.UTILITY,
            "remote": ToolType.API,
            "indexer": ToolType.UTILITY,
            "messaging": ToolType.NETWORK,
            "generic": ToolType.MCP
        }
        return mapping.get(mcp_type, ToolType.MCP)
    
    def _add_mcp_methods(self):
        """Add MCP-specific method schemas"""
        # Main execute method
        execute_schema = ToolSchema(
            name="execute",
            description=f"Execute {self._mcp_type} MCP tool operation",
            parameters={
                "operation": {
                    "type": "string",
                    "description": "Operation to perform"
                },
                "parameters": {
                    "type": "object",
                    "description": "Operation parameters"
                },
                "options": {
                    "type": "object",
                    "description": "Additional execution options"
                }
            },
            returns={
                "type": "object",
                "description": "Execution result",
                "properties": {
                    "success": {"type": "boolean", "description": "Operation success"},
                    "result": {"type": "any", "description": "Operation result"},
                    "metadata": {"type": "object", "description": "Execution metadata"}
                }
            },
            required=["operation"],
            examples=[
                {
                    "operation": "read_file",
                    "parameters": {"path": "/tmp/example.txt"}
                }
            ]
        )
        self._metadata.add_method(execute_schema)
        
        # Add type-specific methods
        if self._mcp_type == "filesystem":
            self._add_filesystem_methods()
        elif self._mcp_type == "database":
            self._add_database_methods()
        elif self._mcp_type == "github":
            self._add_github_methods()
        elif self._mcp_type == "workflow":
            self._add_workflow_methods()
        elif self._mcp_type == "tasklist":
            self._add_tasklist_methods()
        
        # Generic MCP methods
        self._add_generic_mcp_methods()
    
    def _add_filesystem_methods(self):
        """Add filesystem-specific methods"""
        methods = [
            ("read_file", "Read file contents", {"path": {"type": "string", "description": "File path"}}),
            ("write_file", "Write file contents", {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "File content"}
            }),
            ("list_directory", "List directory contents", {"path": {"type": "string", "description": "Directory path"}}),
            ("create_directory", "Create directory", {"path": {"type": "string", "description": "Directory path"}}),
            ("delete_file", "Delete file", {"path": {"type": "string", "description": "File path"}}),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "any", "description": "Operation result"},
                required=["path"] if "path" in params else []
            )
            self._metadata.add_method(schema)
    
    def _add_database_methods(self):
        """Add database-specific methods"""
        methods = [
            ("query", "Execute database query", {
                "sql": {"type": "string", "description": "SQL query"},
                "parameters": {"type": "array", "description": "Query parameters"}
            }),
            ("execute", "Execute database command", {
                "sql": {"type": "string", "description": "SQL command"}
            }),
            ("get_schema", "Get database schema", {}),
            ("list_tables", "List database tables", {}),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "any", "description": "Operation result"},
                required=["sql"] if "sql" in params else []
            )
            self._metadata.add_method(schema)
    
    def _add_github_methods(self):
        """Add GitHub-specific methods"""
        methods = [
            ("get_repository", "Get repository information", {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            }),
            ("create_issue", "Create GitHub issue", {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "array", "description": "Issue labels"}
            }),
            ("list_issues", "List repository issues", {
                "state": {"type": "string", "description": "Issue state", "default": "open"}
            }),
            ("get_file_content", "Get file content from repository", {
                "path": {"type": "string", "description": "File path in repository"}
            }),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "GitHub API response"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def _add_workflow_methods(self):
        """Add workflow-specific methods"""
        methods = [
            ("execute_workflow", "Execute workflow", {
                "workflow_config": {"type": "object", "description": "Workflow configuration"},
                "inputs": {"type": "object", "description": "Workflow inputs"}
            }),
            ("get_workflow_status", "Get workflow execution status", {
                "execution_id": {"type": "string", "description": "Execution ID"}
            }),
            ("list_workflows", "List available workflows", {}),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "Workflow result"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def _add_tasklist_methods(self):
        """Add tasklist-specific methods"""
        methods = [
            ("create_task", "Create new task", {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {"type": "string", "description": "Task priority", "default": "medium"}
            }),
            ("list_tasks", "List tasks", {
                "status": {"type": "string", "description": "Task status filter", "default": "all"}
            }),
            ("update_task", "Update task", {
                "task_id": {"type": "string", "description": "Task ID"},
                "updates": {"type": "object", "description": "Task updates"}
            }),
            ("delete_task", "Delete task", {
                "task_id": {"type": "string", "description": "Task ID"}
            }),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "Task operation result"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def _add_generic_mcp_methods(self):
        """Add generic MCP methods"""
        # Health check
        health_schema = ToolSchema(
            name="health_check",
            description="Check tool health and status",
            parameters={},
            returns={
                "type": "object",
                "description": "Health status",
                "properties": {
                    "status": {"type": "string", "description": "Health status"},
                    "details": {"type": "object", "description": "Health details"}
                }
            },
            required=[]
        )
        self._metadata.add_method(health_schema)
        
        # Get capabilities
        capabilities_schema = ToolSchema(
            name="get_capabilities",
            description="Get tool capabilities",
            parameters={},
            returns={
                "type": "object",
                "description": "Tool capabilities",
                "properties": {
                    "operations": {"type": "array", "description": "Available operations"},
                    "features": {"type": "object", "description": "Feature flags"}
                }
            },
            required=[]
        )
        self._metadata.add_method(capabilities_schema)
    
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Execute MCP tool with enhanced parameter handling.
        
        MCP tools typically expect run(input_data) with various input formats.
        """
        try:
            # Handle structured input
            if isinstance(input_data, dict):
                # Check for method-specific call
                if "method" in input_data:
                    method = input_data["method"]
                    parameters = input_data.get("parameters", {})
                    return self._call_mcp_method(method, parameters)
                
                # Check for operation-specific call
                elif "operation" in input_data:
                    operation = input_data["operation"]
                    parameters = input_data.get("parameters", {})
                    return self._call_mcp_operation(operation, parameters)
                
                # Direct parameter call
                else:
                    return self._legacy_tool.run(input_data)
            
            # Handle string input
            elif isinstance(input_data, str):
                # Try to parse as operation
                return self._legacy_tool.run({"operation": input_data})
            
            # Handle kwargs
            elif kwargs:
                return self._legacy_tool.run(kwargs)
            
            # Default call
            else:
                return self._legacy_tool.run(input_data)
                
        except Exception as e:
            self._logger.error(f"MCP tool execution failed: {e}")
            raise
    
    def _call_mcp_method(self, method: str, parameters: Dict[str, Any]) -> Any:
        """Call specific MCP method"""
        # Check if tool has the method directly
        if hasattr(self._legacy_tool, method):
            method_func = getattr(self._legacy_tool, method)
            return method_func(**parameters)
        
        # Use run with method information
        return self._legacy_tool.run({
            "method": method,
            "parameters": parameters
        })
    
    def _call_mcp_operation(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Call specific MCP operation"""
        return self._legacy_tool.run({
            "operation": operation,
            "parameters": parameters
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for MCP tools"""
        base_health = super().health_check()
        
        base_health.update({
            "mcp_type": self._mcp_type,
            "mcp_capabilities": [cap.value for cap in self.metadata.capabilities],
        })
        
        # Check MCP-specific attributes
        if hasattr(self._legacy_tool, 'local_mode'):
            base_health["local_mode"] = getattr(self._legacy_tool, 'local_mode')
        
        if hasattr(self._legacy_tool, 'mcp_server'):
            base_health["has_mcp_server"] = True
        
        # Check if MCP tool has its own health check
        try:
            if hasattr(self._legacy_tool, 'health_check'):
                mcp_health = self._legacy_tool.health_check()
                base_health["mcp_health"] = mcp_health
        except Exception as e:
            base_health["mcp_health_error"] = str(e)
        
        return base_health
