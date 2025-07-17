# mcp/tools/filesystem/main.py

import os
from pydantic import BaseModel
from typing import List
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool

# === Schemas ===
class ListDirInput(BaseModel):
    path: str

class ListDirOutput(BaseModel):
    path: str
    contents: List[str]

class ReadFileInput(BaseModel):
    path: str

class ReadFileOutput(BaseModel):
    path: str
    content: str

# === Handlers ===
def list_directory(path: str):
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    contents = os.listdir(path)
    return {"contents": contents, "path": path}

def read_file(path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as file:
        content = file.read()
    return {"content": content, "path": path}

# === Build MCP Server ===
server = BaseMCPToolServer(
    name="filesystem",
    description="Read-only access to the local filesystem via MCP.",
    local_mode=True  # 🔧 Enable local mode!
)

server.add_task(
    name="list_directory",
    description="List the contents of a directory.",
    input_model=ListDirInput,
    output_model=ListDirOutput,
    handler=list_directory
)

server.add_task(
    name="read_file",
    description="Read the contents of a text file.",
    input_model=ReadFileInput,
    output_model=ReadFileOutput,
    handler=read_file
)

# Build app (None if local_mode=True)
app = server.build_app()

# === LangChain-Compatible Tool Class ===
class FilesystemMCPTool(BaseTool):
    """
    Filesystem MCP tool for local and remote operations.
    
    Supports both local mode (direct filesystem operations) and remote mode (via MCP).
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, mcp_url: str = None, **kwargs):
        # Set defaults for filesystem MCP tool
        description = kwargs.pop('description', "Read-only access to the local filesystem via MCP")
        instruction = kwargs.pop('instruction', "Use this tool to list directories and read files from the local filesystem")
        brief = kwargs.pop('brief', "Filesystem MCP tool")
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        
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
        """Execute filesystem MCP methods locally"""
        # Define method handlers for this tool
        method_handlers = {
            "list_directory": list_directory,
            "read_file": read_file,
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except Exception as e:
            return f"Error: Unknown method '{method}'. Available methods: {list(method_handlers.keys())}"

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.filesystem.main:app", host="0.0.0.0", port=4020, reload=True)
