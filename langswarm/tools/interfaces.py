"""
LangSwarm V2 Tool System Interfaces

Defines the core interfaces for the unified tool system.
These interfaces ensure type safety, consistency, and clear contracts
between all tool components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, AsyncIterator
from datetime import datetime
from enum import Enum
import json


class ToolType(Enum):
    """Types of tools in the unified system"""
    MCP = "mcp"                      # Enhanced MCP tools
    MEMORY = "memory"                # Memory/retrieval tools (converted from RAGs)
    WORKFLOW = "workflow"            # Workflow/utility tools (converted from Synapse)
    FILESYSTEM = "filesystem"        # File operations
    NETWORK = "network"             # Network operations
    DATABASE = "database"           # Database operations
    API = "api"                     # API integrations
    UTILITY = "utility"             # General utility functions
    BUILTIN = "builtin"             # Built-in V2 tools


class ToolCapability(Enum):
    """Capabilities that tools can support"""
    READ = "read"                   # Read-only operations
    WRITE = "write"                 # Write operations
    EXECUTE = "execute"             # Execute commands
    STREAM = "stream"               # Streaming operations
    BATCH = "batch"                 # Batch operations
    ASYNC = "async"                 # Async execution
    CACHE = "cache"                 # Result caching
    VALIDATE = "validate"           # Input validation
    
    # Additional capabilities for built-in tools
    FILE_SYSTEM = "file_system"     # File and directory operations
    NETWORK = "network"             # Network and HTTP operations
    DATA_PROCESSING = "data_processing"  # Data transformation and analysis
    AI_INTEGRATION = "ai_integration"    # AI model and service integration
    DATABASE = "database"           # Database connectivity and operations
    API_INTEGRATION = "api_integration"  # External API integrations
    MONITORING = "monitoring"       # System monitoring and observability
    SECURITY = "security"           # Security and authentication operations
    WORKFLOW = "workflow"           # Workflow and automation capabilities
    COMMUNICATION = "communication" # Messaging and communication tools
    DIAGNOSTIC = "diagnostic"       # System diagnostics and debugging
    INTROSPECTION = "introspection" # System introspection and reflection
    TEXT_PROCESSING = "text_processing"  # Text analysis and manipulation
    FORMATTING = "formatting"       # Data formatting and presentation
    ENCODING = "encoding"           # Data encoding and decoding
    DOCUMENTATION = "documentation" # Documentation generation and management
    DATA_ACCESS = "data_access"     # Data reading and writing operations


class ExecutionMode(Enum):
    """Tool execution modes"""
    SYNC = "sync"                   # Synchronous execution
    ASYNC = "async"                 # Asynchronous execution
    STREAM = "stream"               # Streaming execution
    BATCH = "batch"                 # Batch execution


class ToolSchema:
    """Schema definition for tool methods and parameters"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        returns: Dict[str, Any],
        required: List[str] = None,
        examples: List[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.returns = returns
        self.required = required or []
        self.examples = examples or []
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate parameters against schema"""
        # Check required parameters
        for req_param in self.required:
            if req_param not in params:
                return False
        
        # Basic type checking could be added here
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "returns": self.returns,
            "required": self.required,
            "examples": self.examples
        }


class IToolMetadata(ABC):
    """Interface for tool metadata"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique tool identifier"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Tool version"""
        pass
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """Type of tool"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[ToolCapability]:
        """List of tool capabilities"""
        pass
    
    @property
    @abstractmethod
    def methods(self) -> Dict[str, ToolSchema]:
        """Available methods with their schemas"""
        pass
    
    @property
    @abstractmethod
    def tags(self) -> List[str]:
        """Tool tags for categorization"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        pass


class IToolExecution(ABC):
    """Interface for tool execution"""
    
    @abstractmethod
    async def execute(
        self, 
        method: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a tool method asynchronously
        
        Args:
            method: Method name to execute
            parameters: Method parameters
            context: Execution context (user_id, session_id, etc.)
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def execute_sync(
        self,
        method: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a tool method synchronously
        
        Args:
            method: Method name to execute
            parameters: Method parameters
            context: Execution context
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    async def execute_stream(
        self,
        method: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Any]:
        """
        Execute a tool method with streaming results
        
        Args:
            method: Method name to execute
            parameters: Method parameters
            context: Execution context
            
        Yields:
            Streaming results
        """
        pass
    
    @abstractmethod
    def validate_method(self, method: str, parameters: Dict[str, Any]) -> bool:
        """
        Validate method and parameters
        
        Args:
            method: Method name
            parameters: Method parameters
            
        Returns:
            True if valid
        """
        pass


class IToolInterface(ABC):
    """Main interface that all V2 tools must implement"""
    
    @property
    @abstractmethod
    def metadata(self) -> IToolMetadata:
        """Tool metadata"""
        pass
    
    @property
    @abstractmethod
    def execution(self) -> IToolExecution:
        """Tool execution interface"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the tool with configuration
        
        Args:
            config: Tool configuration
            
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup tool resources
        
        Returns:
            True if cleanup successful
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check tool health status
        
        Returns:
            Health status information
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM consumption
        
        Returns:
            Tool schema in MCP format
        """
        pass


class IToolRegistry(ABC):
    """Interface for tool registry"""
    
    @abstractmethod
    def register(self, tool: IToolInterface) -> bool:
        """
        Register a tool
        
        Args:
            tool: Tool to register
            
        Returns:
            True if registration successful
        """
        pass
    
    @abstractmethod
    def unregister(self, tool_id: str) -> bool:
        """
        Unregister a tool
        
        Args:
            tool_id: ID of tool to unregister
            
        Returns:
            True if unregistration successful
        """
        pass
    
    @abstractmethod
    def get_tool(self, tool_id: str) -> Optional[IToolInterface]:
        """
        Get a tool by ID
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool instance or None
        """
        pass
    
    @abstractmethod
    def list_tools(self, 
                   tool_type: Optional[ToolType] = None,
                   capabilities: Optional[List[ToolCapability]] = None,
                   tags: Optional[List[str]] = None
                   ) -> List[IToolInterface]:
        """
        List tools with optional filtering
        
        Args:
            tool_type: Filter by tool type
            capabilities: Filter by capabilities
            tags: Filter by tags
            
        Returns:
            List of matching tools
        """
        pass
    
    @abstractmethod
    def search_tools(self, query: str) -> List[IToolInterface]:
        """
        Search tools by description or functionality
        
        Args:
            query: Search query
            
        Returns:
            List of matching tools
        """
        pass
    
    @property
    @abstractmethod
    def tool_count(self) -> int:
        """Number of registered tools"""
        pass
    
    @abstractmethod
    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tool schemas for LLM consumption
        
        Returns:
            Dictionary mapping tool_id to schema
        """
        pass


class IToolDiscovery(ABC):
    """Interface for tool discovery and auto-registration"""
    
    @abstractmethod
    def discover_tools(self, 
                       search_paths: List[str],
                       patterns: Optional[List[str]] = None
                       ) -> List[Dict[str, Any]]:
        """
        Discover tools in given paths
        
        Args:
            search_paths: Paths to search for tools
            patterns: File patterns to match
            
        Returns:
            List of discovered tool configurations
        """
        pass
    
    @abstractmethod
    def auto_register(self, registry: IToolRegistry) -> int:
        """
        Auto-register discovered tools
        
        Args:
            registry: Registry to register tools in
            
        Returns:
            Number of tools registered
        """
        pass


class IToolConfiguration(ABC):
    """Interface for tool configuration management"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load tool configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate tool configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def merge_configs(self, 
                      base_config: Dict[str, Any],
                      override_config: Dict[str, Any]
                      ) -> Dict[str, Any]:
        """
        Merge configuration dictionaries
        
        Args:
            base_config: Base configuration
            override_config: Override configuration
            
        Returns:
            Merged configuration
        """
        pass


class IToolAdapter(ABC):
    """Interface for adapting legacy tools to V2 interface"""
    
    @abstractmethod
    def adapt(self, legacy_tool: Any) -> IToolInterface:
        """
        Adapt a legacy tool to V2 interface
        
        Args:
            legacy_tool: Legacy tool instance
            
        Returns:
            V2-compatible tool interface
        """
        pass
    
    @abstractmethod
    def can_adapt(self, tool: Any) -> bool:
        """
        Check if tool can be adapted
        
        Args:
            tool: Tool to check
            
        Returns:
            True if adaptable
        """
        pass
    
    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        """List of supported legacy tool types"""
        pass
