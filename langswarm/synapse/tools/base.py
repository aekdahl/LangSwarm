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
        """Safely calls a function and detects incorrect arguments."""
        # ToDo: Now it returns if any argument is invalid, it should only return if
        # required arguments are missing, else we just skip invalid ones.

        func_signature = inspect.signature(func)
        accepted_args = func_signature.parameters.keys()  # Valid argument names

        # Separate valid and invalid arguments
        valid_kwargs = {k: v for k, v in kwargs.items() if k in accepted_args}
        invalid_kwargs = {k: v for k, v in kwargs.items() if k not in accepted_args}

        # If there are invalid arguments, return an error message instead of calling
        if invalid_kwargs:
            return f"Error: Unexpected arguments {list(invalid_kwargs.keys())}. Expected: {list(accepted_args)}"

        # Call the function with only valid arguments
        return func(*args, **valid_kwargs)
