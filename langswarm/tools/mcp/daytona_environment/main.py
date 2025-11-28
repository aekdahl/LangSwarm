# mcp/tools/daytona_environment/main.py

import os
import json
import asyncio
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.tools.base import BaseTool
from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin

# === Pydantic Schemas ===

class CreateSandboxInput(BaseModel):
    language: str = "python"
    image: Optional[str] = None
    name: Optional[str] = None
    git_repo: Optional[str] = None
    git_branch: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    persistent: bool = False

class CreateSandboxOutput(BaseModel):
    sandbox_id: str
    name: str
    language: str
    status: str
    preview_url: Optional[str] = None
    message: str

class ExecuteCodeInput(BaseModel):
    sandbox_id: str
    code: str
    language: str = "python"
    working_directory: Optional[str] = None

class ExecuteCodeOutput(BaseModel):
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    message: str

class ExecuteShellInput(BaseModel):
    sandbox_id: str
    command: str
    working_directory: Optional[str] = None

class ExecuteShellOutput(BaseModel):
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    message: str

class FileOperationInput(BaseModel):
    sandbox_id: str
    operation: str  # "upload", "download", "list", "create", "delete", "read", "write"
    file_path: str
    content: Optional[str] = None
    local_path: Optional[str] = None

class FileOperationOutput(BaseModel):
    sandbox_id: str
    operation: str
    file_path: str
    success: bool
    content: Optional[str] = None
    files: Optional[List[str]] = None
    message: str

class ListSandboxesOutput(BaseModel):
    sandboxes: List[Dict[str, Any]]
    count: int
    message: str

class DeleteSandboxInput(BaseModel):
    sandbox_id: str

class DeleteSandboxOutput(BaseModel):
    sandbox_id: str
    success: bool
    message: str

class GitOperationInput(BaseModel):
    sandbox_id: str
    operation: str  # "clone", "pull", "push", "status", "commit", "checkout"
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    commit_message: Optional[str] = None
    working_directory: Optional[str] = None

class GitOperationOutput(BaseModel):
    sandbox_id: str
    operation: str
    success: bool
    output: str
    message: str

class SandboxInfoInput(BaseModel):
    sandbox_id: str

class SandboxInfoOutput(BaseModel):
    sandbox_id: str
    name: str
    language: str
    status: str
    created_at: str
    last_accessed: str
    preview_url: Optional[str] = None
    git_repo: Optional[str] = None
    environment_vars: Dict[str, str]
    message: str

# === Daytona Environment Manager ===

class DaytonaEnvironmentManager:
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize Daytona Environment Manager
        
        Args:
            api_key: Daytona API key (defaults to DAYTONA_API_KEY env var)
            api_url: Daytona API URL (defaults to DAYTONA_API_URL env var or app.daytona.io)
        """
        self.api_key = api_key or os.getenv("DAYTONA_API_KEY")
        self.api_url = api_url or os.getenv("DAYTONA_API_URL", "https://app.daytona.io")
        
        if not self.api_key:
            raise ValueError("Daytona API key is required. Set DAYTONA_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Daytona client
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Daytona SDK client"""
        try:
            from daytona import Daytona, DaytonaConfig
            self._client = Daytona(DaytonaConfig(api_key=self.api_key, api_url=self.api_url))
        except ImportError:
            raise ImportError("Daytona SDK not found. Install with: pip install daytona")
    
    async def create_sandbox(self, input_data: CreateSandboxInput) -> CreateSandboxOutput:
        """Create a new Daytona sandbox environment"""
        try:
            from daytona import CreateSandboxParams
            
            # Prepare sandbox parameters
            params = CreateSandboxParams(
                language=input_data.language,
                image=input_data.image,
                name=input_data.name,
                git_repo=input_data.git_repo,
                git_branch=input_data.git_branch,
                environment_vars=input_data.environment_vars or {},
                persistent=input_data.persistent
            )
            
            # Create the sandbox
            sandbox = await asyncio.to_thread(self._client.create, params)
            
            return CreateSandboxOutput(
                sandbox_id=sandbox.id,
                name=sandbox.name or f"sandbox-{sandbox.id[:8]}",
                language=input_data.language,
                status="running",
                preview_url=getattr(sandbox, 'preview_url', None),
                message=f"Successfully created sandbox {sandbox.id}"
            )
            
        except Exception as e:
            return CreateSandboxOutput(
                sandbox_id="",
                name="",
                language=input_data.language,
                status="error",
                message=f"Error creating sandbox: {str(e)}"
            )
    
    async def execute_code(self, input_data: ExecuteCodeInput) -> ExecuteCodeOutput:
        """Execute code in a Daytona sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            if input_data.working_directory:
                # Change to working directory if specified
                await asyncio.to_thread(
                    sandbox.process.shell_run, 
                    f"cd {input_data.working_directory}"
                )
            
            # Execute the code
            start_time = asyncio.get_event_loop().time()
            result = await asyncio.to_thread(sandbox.process.code_run, input_data.code)
            end_time = asyncio.get_event_loop().time()
            
            return ExecuteCodeOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=result.exit_code,
                stdout=result.result,
                stderr=result.stderr if hasattr(result, 'stderr') else "",
                execution_time=end_time - start_time,
                message="Code executed successfully" if result.exit_code == 0 else "Code execution failed"
            )
            
        except Exception as e:
            return ExecuteCodeOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                message=f"Error executing code: {str(e)}"
            )
    
    async def execute_shell(self, input_data: ExecuteShellInput) -> ExecuteShellOutput:
        """Execute shell command in a Daytona sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            if input_data.working_directory:
                # Change to working directory if specified
                command = f"cd {input_data.working_directory} && {input_data.command}"
            else:
                command = input_data.command
            
            # Execute the shell command
            start_time = asyncio.get_event_loop().time()
            result = await asyncio.to_thread(sandbox.process.shell_run, command)
            end_time = asyncio.get_event_loop().time()
            
            return ExecuteShellOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=result.exit_code,
                stdout=result.result,
                stderr=result.stderr if hasattr(result, 'stderr') else "",
                execution_time=end_time - start_time,
                message="Command executed successfully" if result.exit_code == 0 else "Command execution failed"
            )
            
        except Exception as e:
            return ExecuteShellOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                message=f"Error executing command: {str(e)}"
            )
    
    async def file_operation(self, input_data: FileOperationInput) -> FileOperationOutput:
        """Perform file operations in a Daytona sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            if input_data.operation == "read":
                content = await asyncio.to_thread(sandbox.files.read, input_data.file_path)
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="read",
                    file_path=input_data.file_path,
                    success=True,
                    content=content,
                    message=f"Successfully read file {input_data.file_path}"
                )
            
            elif input_data.operation == "write":
                await asyncio.to_thread(
                    sandbox.files.write, 
                    input_data.file_path, 
                    input_data.content or ""
                )
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="write",
                    file_path=input_data.file_path,
                    success=True,
                    message=f"Successfully wrote to file {input_data.file_path}"
                )
            
            elif input_data.operation == "list":
                files = await asyncio.to_thread(sandbox.files.list, input_data.file_path)
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="list",
                    file_path=input_data.file_path,
                    success=True,
                    files=files,
                    message=f"Successfully listed directory {input_data.file_path}"
                )
            
            elif input_data.operation == "delete":
                await asyncio.to_thread(sandbox.files.delete, input_data.file_path)
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="delete",
                    file_path=input_data.file_path,
                    success=True,
                    message=f"Successfully deleted {input_data.file_path}"
                )
            
            elif input_data.operation == "upload" and input_data.local_path:
                await asyncio.to_thread(
                    sandbox.files.upload, 
                    input_data.local_path, 
                    input_data.file_path
                )
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="upload",
                    file_path=input_data.file_path,
                    success=True,
                    message=f"Successfully uploaded {input_data.local_path} to {input_data.file_path}"
                )
            
            elif input_data.operation == "download" and input_data.local_path:
                await asyncio.to_thread(
                    sandbox.files.download, 
                    input_data.file_path, 
                    input_data.local_path
                )
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="download",
                    file_path=input_data.file_path,
                    success=True,
                    message=f"Successfully downloaded {input_data.file_path} to {input_data.local_path}"
                )
            
            else:
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation=input_data.operation,
                    file_path=input_data.file_path,
                    success=False,
                    message=f"Unsupported file operation: {input_data.operation}"
                )
                
        except Exception as e:
            return FileOperationOutput(
                sandbox_id=input_data.sandbox_id,
                operation=input_data.operation,
                file_path=input_data.file_path,
                success=False,
                message=f"Error performing file operation: {str(e)}"
            )
    
    async def git_operation(self, input_data: GitOperationInput) -> GitOperationOutput:
        """Perform git operations in a Daytona sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            if input_data.operation == "clone":
                if not input_data.repository_url:
                    raise ValueError("Repository URL is required for clone operation")
                
                command = f"git clone {input_data.repository_url}"
                if input_data.branch:
                    command += f" -b {input_data.branch}"
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
                
            elif input_data.operation == "pull":
                command = "git pull"
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
                
            elif input_data.operation == "push":
                command = "git push"
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
                
            elif input_data.operation == "status":
                command = "git status"
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
                
            elif input_data.operation == "commit":
                if not input_data.commit_message:
                    raise ValueError("Commit message is required for commit operation")
                command = f'git add -A && git commit -m "{input_data.commit_message}"'
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
                
            elif input_data.operation == "checkout":
                if not input_data.branch:
                    raise ValueError("Branch name is required for checkout operation")
                command = f"git checkout {input_data.branch}"
                if input_data.working_directory:
                    command = f"cd {input_data.working_directory} && {command}"
            
            else:
                return GitOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation=input_data.operation,
                    success=False,
                    output="",
                    message=f"Unsupported git operation: {input_data.operation}"
                )
            
            # Execute the git command
            result = await asyncio.to_thread(sandbox.process.shell_run, command)
            
            return GitOperationOutput(
                sandbox_id=input_data.sandbox_id,
                operation=input_data.operation,
                success=result.exit_code == 0,
                output=result.result,
                message="Git operation completed successfully" if result.exit_code == 0 else "Git operation failed"
            )
            
        except Exception as e:
            return GitOperationOutput(
                sandbox_id=input_data.sandbox_id,
                operation=input_data.operation,
                success=False,
                output="",
                message=f"Error performing git operation: {str(e)}"
            )
    
    async def list_sandboxes(self) -> ListSandboxesOutput:
        """List all available sandboxes"""
        try:
            sandboxes = await asyncio.to_thread(self._client.list)
            
            sandbox_list = []
            for sandbox in sandboxes:
                sandbox_info = {
                    "sandbox_id": sandbox.id,
                    "name": sandbox.name or f"sandbox-{sandbox.id[:8]}",
                    "status": getattr(sandbox, 'status', 'unknown'),
                    "language": getattr(sandbox, 'language', 'unknown'),
                    "created_at": getattr(sandbox, 'created_at', 'unknown'),
                    "preview_url": getattr(sandbox, 'preview_url', None)
                }
                sandbox_list.append(sandbox_info)
            
            return ListSandboxesOutput(
                sandboxes=sandbox_list,
                count=len(sandbox_list),
                message=f"Found {len(sandbox_list)} sandboxes"
            )
            
        except Exception as e:
            return ListSandboxesOutput(
                sandboxes=[],
                count=0,
                message=f"Error listing sandboxes: {str(e)}"
            )
    
    async def delete_sandbox(self, input_data: DeleteSandboxInput) -> DeleteSandboxOutput:
        """Delete a Daytona sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            # Delete the sandbox
            await asyncio.to_thread(self._client.remove, sandbox)
            
            return DeleteSandboxOutput(
                sandbox_id=input_data.sandbox_id,
                success=True,
                message=f"Successfully deleted sandbox {input_data.sandbox_id}"
            )
            
        except Exception as e:
            return DeleteSandboxOutput(
                sandbox_id=input_data.sandbox_id,
                success=False,
                message=f"Error deleting sandbox: {str(e)}"
            )
    
    async def get_sandbox_info(self, input_data: SandboxInfoInput) -> SandboxInfoOutput:
        """Get detailed information about a sandbox"""
        try:
            # Get sandbox reference
            sandbox = self._get_sandbox(input_data.sandbox_id)
            
            return SandboxInfoOutput(
                sandbox_id=sandbox.id,
                name=sandbox.name or f"sandbox-{sandbox.id[:8]}",
                language=getattr(sandbox, 'language', 'unknown'),
                status=getattr(sandbox, 'status', 'unknown'),
                created_at=getattr(sandbox, 'created_at', 'unknown'),
                last_accessed=getattr(sandbox, 'last_accessed', 'unknown'),
                preview_url=getattr(sandbox, 'preview_url', None),
                git_repo=getattr(sandbox, 'git_repo', None),
                environment_vars=getattr(sandbox, 'environment_vars', {}),
                message=f"Retrieved information for sandbox {sandbox.id}"
            )
            
        except Exception as e:
            return SandboxInfoOutput(
                sandbox_id=input_data.sandbox_id,
                name="",
                language="",
                status="error",
                created_at="",
                last_accessed="",
                message=f"Error getting sandbox info: {str(e)}"
            )
    
    def _get_sandbox(self, sandbox_id: str):
        """Get sandbox reference by ID or name"""
        try:
            # List all sandboxes to find the target
            sandboxes = self._client.list()
            
            # Try to find by ID first
            target = next((s for s in sandboxes if s.id == sandbox_id), None)
            
            # If not found, try to find by name
            if not target:
                target = next((s for s in sandboxes if getattr(s, 'name', None) == sandbox_id), None)
            
            if target:
                return target
                
            # If still not found, and it looks like a UUID, maybe we can just return a proxy
            # But for safety, let's raise if we can't find it in the list
            raise ValueError(f"Sandbox '{sandbox_id}' not found")
            
        except Exception as e:
            # Fallback for when list() fails or other issues
            # If we can't verify, we return a proxy object assuming it exists (legacy behavior)
            # but log a warning if possible
            if "Sandbox" in str(e) and "not found" in str(e):
                raise e
            return type('Sandbox', (), {'id': sandbox_id, 'process': type('Process', (), {'code_run': lambda x: type('Result', (), {'exit_code': 1, 'result': '', 'stderr': 'Sandbox connection failed'})(), 'shell_run': lambda x: type('Result', (), {'exit_code': 1, 'result': '', 'stderr': 'Sandbox connection failed'})()})(), 'files': type('Files', (), {'read': lambda x: '', 'write': lambda x, y: None, 'list': lambda x: [], 'delete': lambda x: None, 'upload': lambda x, y: None, 'download': lambda x, y: None})()})()

# === MCP Tool Handler Functions ===

# Global environment manager instance
env_manager = None

def get_env_manager():
    """Get or create the global environment manager"""
    global env_manager
    if env_manager is None:
        env_manager = DaytonaEnvironmentManager()
    return env_manager

def create_sandbox(**kwargs) -> dict:
    """Create a new Daytona sandbox"""
    try:
        manager = get_env_manager()
        input_obj = CreateSandboxInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.create_sandbox(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": "", "message": f"Failed to create sandbox: {str(e)}"}

def execute_code(**kwargs) -> dict:
    """Execute code in a sandbox"""
    try:
        manager = get_env_manager()
        input_obj = ExecuteCodeInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.execute_code(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to execute code: {str(e)}"}

def execute_shell(**kwargs) -> dict:
    """Execute shell command in a sandbox"""
    try:
        manager = get_env_manager()
        input_obj = ExecuteShellInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.execute_shell(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to execute shell command: {str(e)}"}

def file_operation(**kwargs) -> dict:
    """Perform file operations in a sandbox"""
    try:
        manager = get_env_manager()
        input_obj = FileOperationInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.file_operation(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to perform file operation: {str(e)}"}

def git_operation(**kwargs) -> dict:
    """Perform git operations in a sandbox"""
    try:
        manager = get_env_manager()
        input_obj = GitOperationInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.git_operation(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to perform git operation: {str(e)}"}

def list_sandboxes(**kwargs) -> dict:
    """List all sandboxes"""
    try:
        manager = get_env_manager()
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.list_sandboxes())
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandboxes": [], "count": 0, 
                "message": f"Failed to list sandboxes: {str(e)}"}

def delete_sandbox(**kwargs) -> dict:
    """Delete a sandbox"""
    try:
        manager = get_env_manager()
        input_obj = DeleteSandboxInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.delete_sandbox(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to delete sandbox: {str(e)}"}

def get_sandbox_info(**kwargs) -> dict:
    """Get sandbox information"""
    try:
        manager = get_env_manager()
        input_obj = SandboxInfoInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(manager.get_sandbox_info(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to get sandbox info: {str(e)}"}

# === MCP Server Configuration ===

server = BaseMCPToolServer(
    name="daytona_environment",
    description="Secure and elastic infrastructure for running AI-generated code using Daytona sandboxes",
    local_mode=True
)

# Register all MCP tasks
server.add_task(
    name="create_sandbox",
    description="Create a new Daytona sandbox environment for code execution",
    input_model=CreateSandboxInput,
    output_model=CreateSandboxOutput,
    handler=create_sandbox
)

server.add_task(
    name="execute_code",
    description="Execute Python or other code in a Daytona sandbox",
    input_model=ExecuteCodeInput,
    output_model=ExecuteCodeOutput,
    handler=execute_code
)

server.add_task(
    name="execute_shell",
    description="Execute shell commands in a Daytona sandbox",
    input_model=ExecuteShellInput,
    output_model=ExecuteShellOutput,
    handler=execute_shell
)

server.add_task(
    name="file_operation",
    description="Perform file operations (read, write, upload, download, list, delete) in a sandbox",
    input_model=FileOperationInput,
    output_model=FileOperationOutput,
    handler=file_operation
)

server.add_task(
    name="git_operation",
    description="Perform git operations (clone, pull, push, commit, status, checkout) in a sandbox",
    input_model=GitOperationInput,
    output_model=GitOperationOutput,
    handler=git_operation
)

server.add_task(
    name="list_sandboxes",
    description="List all available Daytona sandboxes",
    input_model=type('EmptyInput', (BaseModel,), {}),  # Empty input schema
    output_model=ListSandboxesOutput,
    handler=list_sandboxes
)

server.add_task(
    name="delete_sandbox",
    description="Delete a Daytona sandbox",
    input_model=DeleteSandboxInput,
    output_model=DeleteSandboxOutput,
    handler=delete_sandbox
)

server.add_task(
    name="get_sandbox_info",
    description="Get detailed information about a specific sandbox",
    input_model=SandboxInfoInput,
    output_model=SandboxInfoOutput,
    handler=get_sandbox_info
)

# Build app (None if local_mode=True)
app = server.build_app()

# === LangChain-Compatible Tool Class ===
class DaytonaEnvironmentMCPTool(MCPProtocolMixin, BaseTool):
    """
    Daytona Environment MCP tool for secure code execution and development environments.
    
    Provides secure and elastic infrastructure for running AI-generated code using Daytona sandboxes.
    Supports sandbox lifecycle management, code execution, file operations, and git integration.
    
    Features:
    - Lightning-fast sandbox creation (sub-90ms)
    - Isolated runtime for secure code execution
    - Programmatic control via File, Git, LSP, and Execute APIs
    - OCI/Docker compatibility
    - Unlimited persistence options
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, 
                 mcp_url: str = None, api_key: str = None, api_url: str = None, **kwargs):
        # Set defaults for Daytona MCP tool
        description = kwargs.pop('description', "Secure and elastic infrastructure for running AI-generated code using Daytona sandboxes")
        instruction = kwargs.pop('instruction', "Use this tool to create sandboxes, execute code, manage files, and perform git operations in isolated environments")
        brief = kwargs.pop('brief', "Daytona Environment MCP tool")
        
        # Add MCP server reference
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        object.__setattr__(self, 'api_key', api_key)
        object.__setattr__(self, 'api_url', api_url)
        
        # Initialize with BaseTool (handles all MCP setup automatically)
        super().__init__(
            name=name or "DaytonaEnvironmentMCPTool",
            description=description,
            tool_id=identifier,
            **kwargs
        )
        
        # Register methods explicitly for V2 discovery
        # Create Sandbox
        schema = CreateSandboxInput.model_json_schema()
        self.add_method(
            name="create_sandbox",
            description="Create a new Daytona sandbox environment",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=CreateSandboxOutput.model_json_schema()
        )
        
        # Execute Code
        schema = ExecuteCodeInput.model_json_schema()
        self.add_method(
            name="execute_code",
            description="Execute Python or other code in a Daytona sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=ExecuteCodeOutput.model_json_schema()
        )
        
        # Execute Shell
        schema = ExecuteShellInput.model_json_schema()
        self.add_method(
            name="execute_shell",
            description="Execute shell commands in a Daytona sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=ExecuteShellOutput.model_json_schema()
        )
        
        # File Operation
        schema = FileOperationInput.model_json_schema()
        self.add_method(
            name="file_operation",
            description="Perform file operations (read, write, upload, download, list, delete) in a sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=FileOperationOutput.model_json_schema()
        )
        
        # Git Operation
        schema = GitOperationInput.model_json_schema()
        self.add_method(
            name="git_operation",
            description="Perform git operations (clone, pull, push, commit, status, checkout) in a sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=GitOperationOutput.model_json_schema()
        )
        
        # List Sandboxes
        # Empty input schema for list_sandboxes
        self.add_method(
            name="list_sandboxes",
            description="List all available Daytona sandboxes",
            parameters={},
            required=[],
            returns=ListSandboxesOutput.model_json_schema()
        )
        
        # Delete Sandbox
        schema = DeleteSandboxInput.model_json_schema()
        self.add_method(
            name="delete_sandbox",
            description="Delete a Daytona sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=DeleteSandboxOutput.model_json_schema()
        )
        
        # Get Sandbox Info
        schema = SandboxInfoInput.model_json_schema()
        self.add_method(
            name="get_sandbox_info",
            description="Get detailed information about a specific sandbox",
            parameters=schema.get("properties", {}),
            required=schema.get("required", []),
            returns=SandboxInfoOutput.model_json_schema()
        )
    
    # V2 Direct Method Calls - Expose operations as class methods
    def create_sandbox(self, name: str = None, image: str = "python:3.11", **kwargs):
        """Create a new Daytona sandbox environment"""
        return create_sandbox(name=name, image=image, **kwargs)
    
    def execute_code(self, sandbox_id: str, code: str, language: str = "python", **kwargs):
        """Execute code in a sandbox environment"""
        return execute_code(sandbox_id=sandbox_id, code=code, language=language, **kwargs)
    
    def execute_shell(self, sandbox_id: str, command: str, **kwargs):
        """Execute shell command in a sandbox"""
        return execute_shell(sandbox_id=sandbox_id, command=command, **kwargs)
    
    def file_operation(self, sandbox_id: str, operation: str, path: str, content: str = None, **kwargs):
        """Perform file operations in sandbox (read/write/delete)"""
        return file_operation(sandbox_id=sandbox_id, operation=operation, path=path, content=content, **kwargs)
    
    def git_operation(self, sandbox_id: str, operation: str, repo_url: str = None, **kwargs):
        """Perform git operations in sandbox (clone/pull/push)"""
        return git_operation(sandbox_id=sandbox_id, operation=operation, repo_url=repo_url, **kwargs)
    
    def list_sandboxes(self, **kwargs):
        """List all available sandboxes"""
        return list_sandboxes()
    
    def delete_sandbox(self, sandbox_id: str, **kwargs):
        """Delete a sandbox environment"""
        return delete_sandbox(sandbox_id=sandbox_id)
    
    def get_sandbox_info(self, sandbox_id: str, **kwargs):
        """Get detailed information about a sandbox"""
        return get_sandbox_info(sandbox_id=sandbox_id)
    
    def run(self, input_data=None):
        """Execute Daytona environment MCP methods locally"""
        if not input_data:
            return {"error": "No input data provided"}
        
        # Handle both string and dict inputs
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON input"}
        
        method = input_data.get("method")
        params = input_data.get("params", {})
        
        if not method:
            return {"error": "No method specified"}
        
        # Map method calls to handler functions
        method_handlers = {
            "create_sandbox": create_sandbox,
            "execute_code": execute_code,
            "execute_shell": execute_shell,
            "file_operation": file_operation,
            "git_operation": git_operation,
            "list_sandboxes": list_sandboxes,
            "delete_sandbox": delete_sandbox,
            "get_sandbox_info": get_sandbox_info
        }
        
        handler = method_handlers.get(method)
        if not handler:
            return {"error": f"Unknown method: {method}"}
        
        try:
            # Call handler with parameters unpacked
            result = handler(**params)
            return result
        except Exception as e:
            return {"error": f"Error executing {method}: {str(e)}"}

# === Entry Point ===
if __name__ == "__main__":
    if app:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Running in local mode - no HTTP server started")
        # Example usage in local mode
        tool = DaytonaEnvironmentMCPTool(identifier="daytona_env_example", local_mode=True)
        
        # Test creating a sandbox
        result = tool.run({
            "method": "list_sandboxes",
            "params": {}
        })
        print("List sandboxes result:", result)
