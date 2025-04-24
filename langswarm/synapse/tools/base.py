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
    
    class Config:
        """Allow additional fields to prevent Pydantic validation errors."""
        extra = "allow"
        #arbitrary_types_allowed = True  # Allow non-Pydantic fields

    def __init__(self, name, description, instruction, **kwargs):
        """
        Initialize the base tool.

        :param name: str - Tool name
        :param description: str - Tool description
        :param instruction: str - Usage instructions for the tool
        :param kwargs: Additional arguments (ignored if LangChain is unavailable)
        """
        super().__init__(
            name=name,
            description=description,
            func=self.run,  # Ensures compatibility with LangChain
            **kwargs,
        )

        self.name = name
        self.description = description
        self.instruction = instruction  # Keep LangSwarm's registry requirement        

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

