try:
    from pydantic import Field
except ImportError:
    def Field(default, description=""):
        return default

try:
    from langchain.tools import Tool as BaseClass  # Try importing LangChain's Tool
except ImportError:
    try:
        from pydantic import BaseModel as BaseClass
    except ImportError:
        # Fallback BaseClass when Pydantic is missing
        BaseClass = object

import inspect
from typing import Dict, Any


class BaseTool(BaseClass):  # Conditional Inheritance
    name: str = Field(..., description="A generic name for the tool.")
    description: str = Field(..., description="Description for the tool.")
    instruction: str = Field(..., description="Instructions for the tool.")
    identifier: str = Field(..., description="Unique identifier for the tool.")
    brief: str = Field(..., description="short description of the tool.")
    
    # Class-level flag to bypass Pydantic validation for MCP tools
    _bypass_pydantic = False
    
    def __init_subclass__(cls, **kwargs):
        """Handle subclass initialization for MCP tools"""
        super().__init_subclass__(**kwargs)
        # Enable Pydantic bypass for MCP tool subclasses
        if 'MCP' in cls.__name__ or getattr(cls, '_is_mcp_tool', False):
            cls._bypass_pydantic = True
    
    class Config:
        """Allow additional fields to prevent Pydantic validation errors."""
        extra = "allow"
        #arbitrary_types_allowed = True  # Allow non-Pydantic fields

    def __init__(self, name, description, instruction, identifier=None, brief=None, **kwargs):
        """
        Initialize the base tool.

        :param name: str - Tool name
        :param description: str - Tool description
        :param instruction: str - Usage instructions for the tool
        :param identifier: str - Unique identifier for the tool
        :param brief: str - Short description of the tool
        :param kwargs: Additional arguments (ignored if LangChain is unavailable)
        """
        # Handle MCP tools with Pydantic bypass
        if getattr(self.__class__, '_bypass_pydantic', False):
            # For MCP tools, bypass Pydantic entirely by setting attributes directly on __dict__
            object.__setattr__(self, '__dict__', {})
            self.__dict__.update({
                'name': name,
                'description': description,
                'instruction': instruction,
                'identifier': identifier or name,
                'brief': brief or f"{name} tool",
                'func': self.run,
                'return_direct': kwargs.get('return_direct', False),
                'verbose': kwargs.get('verbose', False),
            })
            
            # Set MCP-specific attributes if this is an MCP tool
            self._setup_mcp_attributes(identifier, name, kwargs)
            
            # Set all additional kwargs as attributes
            for key, value in kwargs.items():
                self.__dict__[key] = value
        else:
            # For regular tools, use normal Pydantic validation
            super().__init__(
                name=name,
                description=description,
                func=self.run,  # Ensures compatibility with LangChain
                **kwargs,
            )

            self.name = name
            self.description = description
            self.instruction = instruction  # Keep LangSwarm's registry requirement
            if identifier:
                self.identifier = identifier
            if brief:
                self.brief = brief
    
    def _setup_mcp_attributes(self, identifier, name, kwargs):
        """Setup common MCP tool attributes"""
        self.__dict__.update({
            'id': identifier,
            'type': name,
        })
        
        # Set up MCP server reference if provided
        if 'mcp_server' in kwargs:
            self.__dict__['mcp_server'] = kwargs['mcp_server']
        
        # Handle workflow patterns for MCP tools
        if kwargs.get("pattern") == "intent":
            # For intent-based calls, set default workflow based on tool name
            default_workflow = f"{identifier}_workflow" if identifier else f"{name}_workflow"
            self.__dict__['main_workflow'] = kwargs.get("main_workflow", default_workflow)
        elif "main_workflow" in kwargs:
            # For direct pattern tools, main_workflow is optional
            self.__dict__['main_workflow'] = kwargs.get("main_workflow")
    
    def invoke(self, input_data):
        """LangChain invoke method compatibility for MCP tools"""
        return self.run(input_data)
    
    def _run(self, *args, **kwargs):
        """LangChain _run method compatibility for MCP tools"""
        if args:
            return self.run(args[0])
        return self.run(kwargs)
    
    def _handle_mcp_structured_input(self, input_data, method_handlers):
        """
        Common handler for MCP structured input like {"method": "...", "params": {...}}
        
        This method provides standardized handling for MCP tool calls, including:
        - Method routing based on input data
        - Parameter validation and error handling
        - Consistent error messages for unknown methods
        - Automatic parameter unpacking for handler functions
        
        Example usage in MCP tool subclass:
            def run(self, input_data=None):
                method_handlers = {
                    "list_files": my_list_function,
                    "read_file": my_read_function,
                }
                return self._handle_mcp_structured_input(input_data, method_handlers)
        
        :param input_data: Input data from tool call
        :param method_handlers: Dict mapping method names to handler functions
        :return: Result from method handler or error message
        """
        if isinstance(input_data, dict):
            method = input_data.get("method")
            params = input_data.get("params", {})
            
            if method in method_handlers:
                handler = method_handlers[method]
                try:
                    return handler(**params)
                except TypeError as e:
                    if "required positional argument" in str(e) or "missing" in str(e):
                        # Extract required parameter from error message
                        return f"Error: {method} {str(e)}"
                    raise
            else:
                available_methods = list(method_handlers.keys())
                return f"Error: Unknown method '{method}'. Available methods: {available_methods}"
        
        # Handle non-dict input (legacy or workflow-based calls)
        return f"{getattr(self, 'name', 'MCP tool')} called with input: {input_data}"        

    def use(self, *args, **kwargs):
        """Redirects to the `run` method for compatibility with LangChain tools."""
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """Override this method to define the tool's behavior."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def _safe_call(self, func, *args, **kwargs):
        """Safely calls a function:
        - Ignores unexpected keyword arguments
        - Returns error if required arguments are missing
        """

        func_signature = inspect.signature(func)
        params = func_signature.parameters

        # Identify required parameters (excluding *args, **kwargs and those with default values)
        required_params = [
            name for name, param in params.items()
            if param.default is param.empty
            and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
        ]

        # Filter kwargs to valid ones
        accepted_args = params.keys()
        valid_kwargs = {k: v for k, v in kwargs.items() if k in accepted_args}

        # Check for missing required arguments
        missing_required = [
            p for p in required_params
            if p not in valid_kwargs and p not in func_signature.bind_partial(*args).arguments
        ]

        if missing_required:
            return f"Error: Missing required arguments: {missing_required}"

        # Safe call with filtered valid kwargs
        return func(*args, **valid_kwargs)

