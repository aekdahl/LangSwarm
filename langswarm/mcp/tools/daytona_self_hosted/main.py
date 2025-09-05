# mcp/tools/daytona_self_hosted/main.py

import os
import json
import asyncio
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import uvicorn
import aiohttp
import subprocess

from langswarm.mcp.server_base import BaseMCPToolServer

# === Pydantic Schemas (Reusing from main Daytona tool) ===

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

# === Self-Hosted Daytona Manager ===

class SelfHostedDaytonaManager:
    def __init__(self, daytona_server_url: str = None, use_cli: bool = True):
        """
        Initialize Self-Hosted Daytona Manager
        
        Args:
            daytona_server_url: URL of self-hosted Daytona server (if using HTTP API)
            use_cli: Whether to use Daytona CLI commands (default for self-hosted)
        """
        self.daytona_server_url = daytona_server_url or os.getenv("DAYTONA_SERVER_URL", "http://localhost:8080")
        self.use_cli = use_cli
        
        # Verify Daytona CLI is available if using CLI mode
        if self.use_cli:
            self._verify_daytona_cli()
    
    def _verify_daytona_cli(self):
        """Verify that Daytona CLI is installed and accessible"""
        try:
            result = subprocess.run(["daytona", "version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Daytona CLI not found or not working")
        except FileNotFoundError:
            raise Exception("Daytona CLI not installed. Please install from https://github.com/daytonaio/daytona")
    
    async def _run_daytona_command(self, command: List[str]) -> Dict[str, Any]:
        """Run a Daytona CLI command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                "daytona", *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "success": process.returncode == 0
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    async def create_sandbox(self, input_data: CreateSandboxInput) -> CreateSandboxOutput:
        """Create a new Daytona workspace using self-hosted instance"""
        try:
            # Build daytona create command
            command = ["create"]
            
            # Add repository if specified
            if input_data.git_repo:
                command.append(input_data.git_repo)
                if input_data.git_branch:
                    command.extend(["--branch", input_data.git_branch])
            
            # Add name if specified
            if input_data.name:
                command.extend(["--name", input_data.name])
            
            # Add environment variables
            if input_data.environment_vars:
                for key, value in input_data.environment_vars.items():
                    command.extend(["--env", f"{key}={value}"])
            
            # Add custom image if specified
            if input_data.image:
                command.extend(["--image", input_data.image])
            
            result = await self._run_daytona_command(command)
            
            if result["success"]:
                # Extract workspace ID from output (this is implementation-specific)
                sandbox_id = self._extract_workspace_id(result["stdout"])
                
                return CreateSandboxOutput(
                    sandbox_id=sandbox_id,
                    name=input_data.name or f"workspace-{sandbox_id[:8]}",
                    language=input_data.language,
                    status="running",
                    message=f"Successfully created workspace {sandbox_id}"
                )
            else:
                return CreateSandboxOutput(
                    sandbox_id="",
                    name="",
                    language=input_data.language,
                    status="error",
                    message=f"Error creating workspace: {result['stderr']}"
                )
        
        except Exception as e:
            return CreateSandboxOutput(
                sandbox_id="",
                name="",
                language=input_data.language,
                status="error",
                message=f"Error creating workspace: {str(e)}"
            )
    
    def _extract_workspace_id(self, output: str) -> str:
        """Extract workspace ID from daytona create output"""
        # This is a simplified extraction - in reality, you'd parse the actual output format
        lines = output.strip().split('\n')
        for line in lines:
            if 'workspace' in line.lower() and ('created' in line.lower() or 'id' in line.lower()):
                # Extract ID from output (implementation depends on actual CLI output format)
                parts = line.split()
                for part in parts:
                    if len(part) > 8 and '-' in part:  # Likely an ID
                        return part
        return f"workspace-{hash(output) % 100000}"  # Fallback
    
    async def execute_code(self, input_data: ExecuteCodeInput) -> ExecuteCodeOutput:
        """Execute code in a Daytona workspace"""
        try:
            # Use daytona exec command
            command = ["exec", input_data.sandbox_id]
            
            # Create a temporary script file content
            if input_data.language == "python":
                exec_command = f"python3 -c '{input_data.code}'"
            elif input_data.language == "javascript" or input_data.language == "node":
                exec_command = f"node -e '{input_data.code}'"
            else:
                exec_command = input_data.code
            
            command.append(exec_command)
            
            start_time = asyncio.get_event_loop().time()
            result = await self._run_daytona_command(command)
            end_time = asyncio.get_event_loop().time()
            
            return ExecuteCodeOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                execution_time=end_time - start_time,
                message="Code executed successfully" if result["success"] else "Code execution failed"
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
        """Execute shell command in a Daytona workspace"""
        try:
            # Use daytona exec command
            command = ["exec", input_data.sandbox_id, input_data.command]
            
            start_time = asyncio.get_event_loop().time()
            result = await self._run_daytona_command(command)
            end_time = asyncio.get_event_loop().time()
            
            return ExecuteShellOutput(
                sandbox_id=input_data.sandbox_id,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                execution_time=end_time - start_time,
                message="Command executed successfully" if result["success"] else "Command execution failed"
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
        """Perform file operations in a Daytona workspace"""
        try:
            if input_data.operation == "read":
                # Use exec to cat the file
                command = ["exec", input_data.sandbox_id, f"cat {input_data.file_path}"]
                result = await self._run_daytona_command(command)
                
                if result["success"]:
                    return FileOperationOutput(
                        sandbox_id=input_data.sandbox_id,
                        operation="read",
                        file_path=input_data.file_path,
                        success=True,
                        content=result["stdout"],
                        message=f"Successfully read file {input_data.file_path}"
                    )
                else:
                    return FileOperationOutput(
                        sandbox_id=input_data.sandbox_id,
                        operation="read",
                        file_path=input_data.file_path,
                        success=False,
                        message=f"Failed to read file: {result['stderr']}"
                    )
            
            elif input_data.operation == "write":
                # Use exec to write to file
                escaped_content = input_data.content.replace("'", "'\"'\"'")
                command = ["exec", input_data.sandbox_id, f"echo '{escaped_content}' > {input_data.file_path}"]
                result = await self._run_daytona_command(command)
                
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="write",
                    file_path=input_data.file_path,
                    success=result["success"],
                    message=f"Successfully wrote to file {input_data.file_path}" if result["success"] else f"Failed to write file: {result['stderr']}"
                )
            
            elif input_data.operation == "list":
                # Use exec to list directory
                command = ["exec", input_data.sandbox_id, f"ls -la {input_data.file_path}"]
                result = await self._run_daytona_command(command)
                
                files = result["stdout"].split('\n') if result["success"] else []
                
                return FileOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation="list",
                    file_path=input_data.file_path,
                    success=result["success"],
                    files=files,
                    message=f"Successfully listed directory {input_data.file_path}" if result["success"] else f"Failed to list directory: {result['stderr']}"
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
        """Perform git operations in a Daytona workspace"""
        try:
            # Build git command
            if input_data.operation == "clone":
                if not input_data.repository_url:
                    raise ValueError("Repository URL is required for clone operation")
                git_cmd = f"git clone {input_data.repository_url}"
                if input_data.branch:
                    git_cmd += f" -b {input_data.branch}"
            elif input_data.operation == "pull":
                git_cmd = "git pull"
            elif input_data.operation == "push":
                git_cmd = "git push"
            elif input_data.operation == "status":
                git_cmd = "git status"
            elif input_data.operation == "commit":
                if not input_data.commit_message:
                    raise ValueError("Commit message is required for commit operation")
                git_cmd = f'git add -A && git commit -m "{input_data.commit_message}"'
            elif input_data.operation == "checkout":
                if not input_data.branch:
                    raise ValueError("Branch name is required for checkout operation")
                git_cmd = f"git checkout {input_data.branch}"
            else:
                return GitOperationOutput(
                    sandbox_id=input_data.sandbox_id,
                    operation=input_data.operation,
                    success=False,
                    output="",
                    message=f"Unsupported git operation: {input_data.operation}"
                )
            
            # Add working directory if specified
            if input_data.working_directory:
                git_cmd = f"cd {input_data.working_directory} && {git_cmd}"
            
            # Execute via daytona exec
            command = ["exec", input_data.sandbox_id, git_cmd]
            result = await self._run_daytona_command(command)
            
            return GitOperationOutput(
                sandbox_id=input_data.sandbox_id,
                operation=input_data.operation,
                success=result["success"],
                output=result["stdout"],
                message="Git operation completed successfully" if result["success"] else f"Git operation failed: {result['stderr']}"
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
        """List all available workspaces"""
        try:
            command = ["list"]
            result = await self._run_daytona_command(command)
            
            if result["success"]:
                # Parse workspace list from output
                workspaces = self._parse_workspace_list(result["stdout"])
                
                return ListSandboxesOutput(
                    sandboxes=workspaces,
                    count=len(workspaces),
                    message=f"Found {len(workspaces)} workspaces"
                )
            else:
                return ListSandboxesOutput(
                    sandboxes=[],
                    count=0,
                    message=f"Error listing workspaces: {result['stderr']}"
                )
            
        except Exception as e:
            return ListSandboxesOutput(
                sandboxes=[],
                count=0,
                message=f"Error listing workspaces: {str(e)}"
            )
    
    def _parse_workspace_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse workspace list from daytona list output"""
        workspaces = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line and not line.startswith('NAME') and not line.startswith('---'):
                # Parse workspace information from line
                # This is simplified - actual parsing depends on CLI output format
                parts = line.split()
                if len(parts) >= 2:
                    workspace = {
                        "sandbox_id": parts[0],
                        "name": parts[0],
                        "status": parts[1] if len(parts) > 1 else "unknown",
                        "language": "unknown",
                        "created_at": "unknown"
                    }
                    workspaces.append(workspace)
        
        return workspaces
    
    async def delete_sandbox(self, input_data: DeleteSandboxInput) -> DeleteSandboxOutput:
        """Delete a Daytona workspace"""
        try:
            command = ["delete", input_data.sandbox_id, "--force"]
            result = await self._run_daytona_command(command)
            
            return DeleteSandboxOutput(
                sandbox_id=input_data.sandbox_id,
                success=result["success"],
                message=f"Successfully deleted workspace {input_data.sandbox_id}" if result["success"] else f"Error deleting workspace: {result['stderr']}"
            )
            
        except Exception as e:
            return DeleteSandboxOutput(
                sandbox_id=input_data.sandbox_id,
                success=False,
                message=f"Error deleting workspace: {str(e)}"
            )
    
    async def get_sandbox_info(self, input_data: SandboxInfoInput) -> SandboxInfoOutput:
        """Get detailed information about a workspace"""
        try:
            command = ["info", input_data.sandbox_id]
            result = await self._run_daytona_command(command)
            
            if result["success"]:
                # Parse workspace info from output
                info = self._parse_workspace_info(result["stdout"])
                
                return SandboxInfoOutput(
                    sandbox_id=input_data.sandbox_id,
                    name=info.get("name", input_data.sandbox_id),
                    language=info.get("language", "unknown"),
                    status=info.get("status", "unknown"),
                    created_at=info.get("created_at", "unknown"),
                    last_accessed=info.get("last_accessed", "unknown"),
                    git_repo=info.get("git_repo"),
                    environment_vars=info.get("environment_vars", {}),
                    message=f"Retrieved information for workspace {input_data.sandbox_id}"
                )
            else:
                return SandboxInfoOutput(
                    sandbox_id=input_data.sandbox_id,
                    name="",
                    language="",
                    status="error",
                    created_at="",
                    last_accessed="",
                    environment_vars={},
                    message=f"Error getting workspace info: {result['stderr']}"
                )
            
        except Exception as e:
            return SandboxInfoOutput(
                sandbox_id=input_data.sandbox_id,
                name="",
                language="",
                status="error",
                created_at="",
                last_accessed="",
                environment_vars={},
                message=f"Error getting workspace info: {str(e)}"
            )
    
    def _parse_workspace_info(self, output: str) -> Dict[str, Any]:
        """Parse workspace info from daytona info output"""
        info = {}
        lines = output.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                info[key] = value
        
        return info

# === MCP Handler Functions ===

# Global manager instance
manager = None

def get_manager():
    """Get or create the global manager"""
    global manager
    if manager is None:
        manager = SelfHostedDaytonaManager()
    return manager

def create_sandbox(**kwargs) -> dict:
    """Create a new Daytona workspace"""
    try:
        mgr = get_manager()
        input_obj = CreateSandboxInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.create_sandbox(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": "", "message": f"Failed to create workspace: {str(e)}"}

def execute_code(**kwargs) -> dict:
    """Execute code in a workspace"""
    try:
        mgr = get_manager()
        input_obj = ExecuteCodeInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.execute_code(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to execute code: {str(e)}"}

def execute_shell(**kwargs) -> dict:
    """Execute shell command in a workspace"""
    try:
        mgr = get_manager()
        input_obj = ExecuteShellInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.execute_shell(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to execute shell command: {str(e)}"}

def file_operation(**kwargs) -> dict:
    """Perform file operations in a workspace"""
    try:
        mgr = get_manager()
        input_obj = FileOperationInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.file_operation(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to perform file operation: {str(e)}"}

def git_operation(**kwargs) -> dict:
    """Perform git operations in a workspace"""
    try:
        mgr = get_manager()
        input_obj = GitOperationInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.git_operation(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to perform git operation: {str(e)}"}

def list_sandboxes(**kwargs) -> dict:
    """List all workspaces"""
    try:
        mgr = get_manager()
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.list_sandboxes())
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandboxes": [], "count": 0, 
                "message": f"Failed to list workspaces: {str(e)}"}

def delete_sandbox(**kwargs) -> dict:
    """Delete a workspace"""
    try:
        mgr = get_manager()
        input_obj = DeleteSandboxInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.delete_sandbox(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to delete workspace: {str(e)}"}

def get_sandbox_info(**kwargs) -> dict:
    """Get workspace information"""
    try:
        mgr = get_manager()
        input_obj = SandboxInfoInput(**kwargs)
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mgr.get_sandbox_info(input_obj))
            return result.dict()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "sandbox_id": kwargs.get("sandbox_id", ""), 
                "message": f"Failed to get workspace info: {str(e)}"}

# === MCP Server Configuration ===

server = BaseMCPToolServer(
    name="daytona_self_hosted",
    description="Self-hosted Daytona integration via CLI for secure on-premises development environments",
    local_mode=False  # This runs as an HTTP server
)

# Register all MCP tasks
server.add_task(
    name="create_sandbox",
    description="Create a new Daytona workspace in self-hosted instance",
    input_model=CreateSandboxInput,
    output_model=CreateSandboxOutput,
    handler=create_sandbox
)

server.add_task(
    name="execute_code",
    description="Execute Python or other code in a self-hosted Daytona workspace",
    input_model=ExecuteCodeInput,
    output_model=ExecuteCodeOutput,
    handler=execute_code
)

server.add_task(
    name="execute_shell",
    description="Execute shell commands in a self-hosted Daytona workspace",
    input_model=ExecuteShellInput,
    output_model=ExecuteShellOutput,
    handler=execute_shell
)

server.add_task(
    name="file_operation",
    description="Perform file operations in a self-hosted Daytona workspace",
    input_model=FileOperationInput,
    output_model=FileOperationOutput,
    handler=file_operation
)

server.add_task(
    name="git_operation",
    description="Perform git operations in a self-hosted Daytona workspace",
    input_model=GitOperationInput,
    output_model=GitOperationOutput,
    handler=git_operation
)

server.add_task(
    name="list_sandboxes",
    description="List all available self-hosted Daytona workspaces",
    input_model=type('EmptyInput', (BaseModel,), {}),
    output_model=ListSandboxesOutput,
    handler=list_sandboxes
)

server.add_task(
    name="delete_sandbox",
    description="Delete a self-hosted Daytona workspace",
    input_model=DeleteSandboxInput,
    output_model=DeleteSandboxOutput,
    handler=delete_sandbox
)

server.add_task(
    name="get_sandbox_info",
    description="Get detailed information about a self-hosted Daytona workspace",
    input_model=SandboxInfoInput,
    output_model=SandboxInfoOutput,
    handler=get_sandbox_info
)

# Build app
app = server.build_app()

# === Entry Point ===
if __name__ == "__main__":
    print("🚀 Starting Self-Hosted Daytona MCP Server on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)


