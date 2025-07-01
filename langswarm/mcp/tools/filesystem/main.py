# mcp/tools/filesystem/main.py

import os
from pydantic import BaseModel
from typing import List
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer

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

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.filesystem.main:app", host="0.0.0.0", port=4020, reload=True)
