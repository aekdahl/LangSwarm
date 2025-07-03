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
        raise ValueError(f"Not a directory: {path}")
    return {"path": path, "contents": sorted(os.listdir(path))}

def read_file(path: str):
    if not os.path.isfile(path):
        raise ValueError(f"Not a file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return {"path": path, "content": f.read()}

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
    Filesystem MCP tool that properly inherits from BaseTool.
    
    This is a template for creating MCP tools with minimal boilerplate:
    
    1. Set _is_mcp_tool = True to enable MCP functionality
    2. Define tool-specific defaults in __init__
    3. Add mcp_server reference to kwargs
    4. Create method_handlers dict in run() method
    5. Use self._handle_mcp_structured_input() for standardized handling
    
    The BaseTool automatically handles:
    - Pydantic validation bypass for MCP tools
    - MCP attribute setup (id, type, workflows)
    - LangChain compatibility (invoke, _run, func)
    - Structured input parsing and error handling
    """
    
    # Flag to enable Pydantic bypass and MCP functionality
    _is_mcp_tool = True
    
    def __init__(self, identifier: str, name: str, description: str = "", instruction: str = "", brief: str = "", **kwargs):
        # Set defaults for filesystem MCP tool
        description = description or "Read-only access to the local filesystem via MCP"
        instruction = instruction or "Use this tool to list directories and read files from the local filesystem"
        brief = brief or "Filesystem MCP tool"
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
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
        return self._handle_mcp_structured_input(input_data, method_handlers)

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.filesystem.main:app", host="0.0.0.0", port=4020, reload=True)
