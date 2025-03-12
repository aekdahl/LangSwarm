import os
import inspect
from typing import Type, Optional, List

try:
    from pydantic import Field
except ImportError:
    def Field(default, description=""):
        return default
    
from langswarm.memory.adapters.database_adapter import DatabaseAdapter
from ..base import BaseTool
from .config import ToolSettings

class FilesystemTool(BaseTool):
    """
    A LangSwarm-compatible tool for managing file operations.
    
    Features:
    - Check permissions before accessing files
    - Read, write, update, and delete files
    - Supports common file types
    """
    #BASE_DIR: str = Field(..., description="short description of the field.")
    ALLOWED_FILE_TYPES = {".txt", ".json", ".csv", ".md", ".py"}
    BASE_DIR = os.path.expanduser("~/agent_files")
        
    def __init__(
        self, 
        identifier,
        directory: Optional[str] = None,
        adapter: Optional[Type[DatabaseAdapter]] = None
    ):
        BASE_DIR = os.path.abspath(directory) or self.BASE_DIR
            
        if adapter is not None and not isinstance(adapter, DatabaseAdapter):
            raise TypeError(
                f"Argument 'adapter' must be a subclass of DatabaseAdapter if provided, got {type(adapter).__name__}")

        super().__init__(
            name="FilesystemTool",
            description=(
                f"A tool to securely create, read, update, and delete files in {BASE_DIR}."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.BASE_DIR = BASE_DIR
        self.identifier = identifier
        self.brief = (
            f"A tool to securely create, read, update, and delete files in {BASE_DIR}. "
            f"Use the help action to get instructions: execute_tool:{identifier}|help|"+"{}"
        )
        os.makedirs(self.BASE_DIR, exist_ok=True)

        self.db = adapter

    def _validate_path(self, filename, folder=False):
        """Ensures the file is within the allowed directory and has an allowed extension."""
        ext = os.path.splitext(filename)[-1]
        if not folder and ext not in self.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type '{ext}' is not allowed.")
            
        full_path = os.path.abspath(os.path.join(self.BASE_DIR, filename))

        # Ensure path remains within BASE_DIR
        if not full_path.startswith(self.BASE_DIR + os.sep):  
            raise PermissionError("Access outside the allowed directory is not permitted. It could be due to a leading '/', if not intended, remove it and try again.")

        return full_path
    
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

    def run(self, payload = {}, action="read_file"):
        """Handles file operations based on the provided action and parameters."""
        
        # Map actions to corresponding functions
        action_map = {
            "help": self._help,
            "read_file": self.read_file,
            "create_file": self.create_file,
            "update_file": self.update_file,
            "delete_file": self.delete_file,
            "list_files": self.list_files,
            "list_all_files_and_folders": self.list_all_files_and_folders,
            "create_directory": self.create_directory,
        }

        # Execute the corresponding action
        if action in action_map: 
            return self._safe_call(action_map[action], **payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def create_file(self, filename, content):
        filepath = self._validate_path(filename)
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            return f"File '{filename}' already exists."
            #raise FileExistsError(f"File '{filename}' already exists.")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filename}' created."

    def read_file(self, filename):
        filepath = self._validate_path(filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filename}' does not exist.")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def update_file(self, filename, content, append=True):
        filepath = self._validate_path(filename)
        mode = "a" if append else "w"
        with open(filepath, mode, encoding="utf-8") as f:
            f.write(content)
        return f"File '{filename}' updated."

    def delete_file(self, filename):
        filepath = self._validate_path(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"File '{filename}' deleted."
        raise FileNotFoundError(f"File '{filename}' does not exist.")

    def list_files(self):
        return os.listdir(self.BASE_DIR)
    
    def _help(self):
        return self.instruction

    def list_all_files_and_folders(self, base_dir, recursive=True):
        """
        List all files and folders in a given directory.

        :param base_dir: The base directory to list files and folders from.
        :param recursive: If True, list all files and folders recursively.
        :return: A list of file and folder paths.
        """
        base_dir = self._validate_path(base_dir, folder=True)
        
        if not os.path.exists(base_dir):
            return f"Error: The directory '{base_dir}' does not exist."
    
        try:
            if recursive:
                # Recursive: Walk through all subdirectories
                return [os.path.join(root, name) 
                        for root, dirs, files in os.walk(base_dir) 
                        for name in dirs + files]
            else:
                # Non-recursive: List only top-level files and folders
                return [os.path.join(base_dir, name) for name in os.listdir(base_dir)]
        except PermissionError:
            return f"Error: Permission denied when accessing '{base_dir}'."
    
    def create_directory(self, path: str):
        """
        Creates a new directory at the specified path.

        :param path: str - The directory path to create.

        :return: dict - Status of directory creation.
        """

        if not path:
            return {"status": "error", "message": "Missing directory path."}
        
        path = self._validate_path(path)

        try:
            # Ensure the directory does not already exist
            if not os.path.exists(path):
                os.makedirs(path)  # ✅ Create directory (including parents if needed)
                return {"status": "success", "message": f"Directory '{path}' created successfully."}
            else:
                return {"status": "error", "message": f"Directory '{path}' already exists."}

        except Exception as e:
            return {"status": "error", "message": f"Failed to create directory '{path}': {str(e)}"}