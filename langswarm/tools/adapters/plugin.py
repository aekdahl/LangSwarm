"""
LangSwarm V2 Plugin Tool Adapter

Adapter for legacy plugin tools to provide V2 interface compatibility.
"""

from typing import Any, Dict, List, Optional
import logging

from ..interfaces import ToolType, ToolCapability
from ..base import ToolSchema
from .base import LegacyToolAdapter

logger = logging.getLogger(__name__)


class PluginToolAdapter(LegacyToolAdapter):
    """
    Adapter for legacy plugin tools to V2 interface.
    
    Plugin tools typically have:
    - execute() or run() methods
    - Plugin-specific functionality
    - Configuration parameters
    """
    
    def __init__(self, plugin_tool: Any, **kwargs):
        # Determine plugin type
        plugin_type = self._determine_plugin_type(plugin_tool)
        
        super().__init__(
            legacy_tool=plugin_tool,
            tool_type=ToolType.UTILITY,  # Plugins are typically utility tools
            capabilities=[
                ToolCapability.READ,
                ToolCapability.EXECUTE,
                ToolCapability.ASYNC
            ],
            **kwargs
        )
        
        self._adapter_type = "plugin"
        self._plugin_type = plugin_type
        
        # Add plugin-specific tags
        self.add_tag("plugin")
        self.add_tag("legacy")
        self.add_tag(plugin_type)
        
        # Add plugin-specific methods
        self._add_plugin_methods()
        
        self._logger.info(f"Adapted plugin tool: {self.metadata.id} ({plugin_type})")
    
    def _determine_plugin_type(self, tool: Any) -> str:
        """Determine the type of plugin tool"""
        class_name = tool.__class__.__name__.lower()
        module_name = tool.__class__.__module__.lower() if hasattr(tool.__class__, '__module__') else ""
        
        if 'notification' in class_name or 'reminder' in class_name:
            return "notification"
        elif 'workflow' in class_name:
            return "workflow"
        elif 'utility' in class_name or 'util' in class_name:
            return "utility"
        elif 'integration' in class_name:
            return "integration"
        else:
            return "generic"
    
    def _add_plugin_methods(self):
        """Add plugin-specific method schemas"""
        # Main execute method
        execute_schema = ToolSchema(
            name="execute",
            description=f"Execute {self._plugin_type} plugin functionality",
            parameters={
                "action": {
                    "type": "string",
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action parameters"
                },
                "config": {
                    "type": "object",
                    "description": "Plugin configuration"
                }
            },
            returns={
                "type": "object",
                "description": "Plugin execution result",
                "properties": {
                    "success": {"type": "boolean", "description": "Execution success"},
                    "result": {"type": "any", "description": "Execution result"},
                    "metadata": {"type": "object", "description": "Execution metadata"}
                }
            },
            required=["action"],
            examples=[
                {
                    "action": "process",
                    "parameters": {"input": "test data"}
                }
            ]
        )
        self._metadata.add_method(execute_schema)
        
        # Configuration method
        configure_schema = ToolSchema(
            name="configure",
            description="Configure plugin settings",
            parameters={
                "settings": {
                    "type": "object",
                    "description": "Plugin configuration settings"
                }
            },
            returns={
                "type": "object",
                "description": "Configuration result",
                "properties": {
                    "success": {"type": "boolean", "description": "Configuration success"},
                    "applied_settings": {"type": "object", "description": "Applied settings"}
                }
            },
            required=["settings"]
        )
        self._metadata.add_method(configure_schema)
        
        # Status method
        status_schema = ToolSchema(
            name="status",
            description="Get plugin status",
            parameters={},
            returns={
                "type": "object",
                "description": "Plugin status",
                "properties": {
                    "active": {"type": "boolean", "description": "Plugin active status"},
                    "version": {"type": "string", "description": "Plugin version"},
                    "configuration": {"type": "object", "description": "Current configuration"}
                }
            },
            required=[]
        )
        self._metadata.add_method(status_schema)
        
        # Add type-specific methods
        if self._plugin_type == "notification":
            self._add_notification_methods()
        elif self._plugin_type == "workflow":
            self._add_workflow_methods()
        elif self._plugin_type == "integration":
            self._add_integration_methods()
    
    def _add_notification_methods(self):
        """Add notification-specific methods"""
        methods = [
            ("send_notification", "Send notification", {
                "message": {"type": "string", "description": "Notification message"},
                "recipient": {"type": "string", "description": "Notification recipient"},
                "channel": {"type": "string", "description": "Notification channel", "default": "default"}
            }),
            ("schedule_reminder", "Schedule reminder", {
                "message": {"type": "string", "description": "Reminder message"},
                "schedule_time": {"type": "string", "description": "Schedule time"},
                "recurrence": {"type": "string", "description": "Recurrence pattern", "default": "once"}
            }),
            ("list_notifications", "List sent notifications", {
                "limit": {"type": "integer", "description": "Number of notifications to list", "default": 10}
            }),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "Operation result"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def _add_workflow_methods(self):
        """Add workflow-specific methods"""
        methods = [
            ("start_workflow", "Start workflow execution", {
                "workflow_id": {"type": "string", "description": "Workflow identifier"},
                "inputs": {"type": "object", "description": "Workflow inputs"}
            }),
            ("get_workflow_status", "Get workflow status", {
                "execution_id": {"type": "string", "description": "Execution identifier"}
            }),
            ("stop_workflow", "Stop workflow execution", {
                "execution_id": {"type": "string", "description": "Execution identifier"}
            }),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "Workflow operation result"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def _add_integration_methods(self):
        """Add integration-specific methods"""
        methods = [
            ("connect", "Connect to external service", {
                "service": {"type": "string", "description": "Service name"},
                "credentials": {"type": "object", "description": "Service credentials"}
            }),
            ("disconnect", "Disconnect from external service", {
                "service": {"type": "string", "description": "Service name"}
            }),
            ("sync_data", "Synchronize data with external service", {
                "service": {"type": "string", "description": "Service name"},
                "data": {"type": "object", "description": "Data to synchronize"}
            }),
            ("get_connection_status", "Get connection status", {
                "service": {"type": "string", "description": "Service name"}
            }),
        ]
        
        for method_name, description, params in methods:
            schema = ToolSchema(
                name=method_name,
                description=description,
                parameters=params,
                returns={"type": "object", "description": "Integration operation result"},
                required=[k for k, v in params.items() if "default" not in v]
            )
            self._metadata.add_method(schema)
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Execute plugin tool with enhanced parameter handling.
        
        Plugin tools typically have various execution patterns.
        """
        try:
            # Handle structured input
            if isinstance(input_data, dict):
                action = input_data.get("action", "execute")
                parameters = input_data.get("parameters", input_data)
                
                # Try action-based execution
                if hasattr(self._legacy_tool, action):
                    method = getattr(self._legacy_tool, action)
                    return self._call_plugin_method(method, parameters)
                
                # Use default execution method
                return self._execute_with_params(parameters)
            
            # Handle string input
            elif isinstance(input_data, str):
                return self._execute_with_params({"input": input_data})
            
            # Handle kwargs
            elif kwargs:
                return self._execute_with_params(kwargs)
            
            # Default execution
            else:
                return self._execute_with_params({})
                
        except Exception as e:
            self._logger.error(f"Plugin tool execution failed: {e}")
            raise
    
    def _execute_with_params(self, parameters: Dict[str, Any]) -> Any:
        """Execute plugin with parameters"""
        # Try common execution methods
        for method_name in ['execute', 'run', 'process', 'perform']:
            if hasattr(self._legacy_tool, method_name):
                method = getattr(self._legacy_tool, method_name)
                return self._call_plugin_method(method, parameters)
        
        # Try calling the plugin directly
        if callable(self._legacy_tool):
            return self._call_plugin_method(self._legacy_tool, parameters)
        
        raise NotImplementedError(f"Plugin {self.metadata.id} has no executable method")
    
    def _call_plugin_method(self, method: callable, parameters: Dict[str, Any]) -> Any:
        """Call plugin method with appropriate parameter handling"""
        try:
            # Try direct parameter passing
            return method(**parameters)
        except TypeError:
            # Try single parameter
            if len(parameters) == 1:
                key, value = next(iter(parameters.items()))
                return method(value)
            # Try no parameters
            elif not parameters:
                return method()
            # Try parameters as single dict
            else:
                return method(parameters)
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for plugin tools"""
        base_health = super().health_check()
        
        base_health.update({
            "plugin_type": self._plugin_type,
            "plugin_capabilities": [cap.value for cap in self.metadata.capabilities],
        })
        
        # Check plugin-specific attributes
        if hasattr(self._legacy_tool, 'version'):
            base_health["plugin_version"] = getattr(self._legacy_tool, 'version')
        
        if hasattr(self._legacy_tool, 'config'):
            base_health["has_configuration"] = True
        
        # Check if plugin has its own health check
        try:
            if hasattr(self._legacy_tool, 'health_check'):
                plugin_health = self._legacy_tool.health_check()
                base_health["plugin_health"] = plugin_health
            elif hasattr(self._legacy_tool, 'status'):
                plugin_status = self._legacy_tool.status()
                base_health["plugin_status"] = plugin_status
        except Exception as e:
            base_health["plugin_health_error"] = str(e)
        
        return base_health
