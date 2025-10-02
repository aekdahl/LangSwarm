"""
File Operations Tool - V2 Built-in Tool

Provides basic file operations for reading, writing, and managing files.
Security-focused with path validation and safe defaults.
"""

import asyncio
import json
import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from langswarm.tools.base import BaseTool, ToolResult, create_tool_metadata, create_method_schema
from langswarm.tools.interfaces import ToolType, ToolCapability


class FileOperationsTool(BaseTool):
    """
    Built-in tool for basic file operations.
    
    Provides secure file operations:
    - Read and write text files
    - List directory contents
    - Get file information
    - Basic file management (copy, move, delete)
    - Path validation and security checks
    """
    
    def __init__(self, base_path: Optional[str] = None, max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize file operations tool
        
        Args:
            base_path: Base directory to restrict operations to (for security)
            max_file_size: Maximum file size to read/write in bytes (default 10MB)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.max_file_size = max_file_size
        
        metadata = create_tool_metadata(
            tool_id="builtin_file_operations",
            name="file_operations",
            description="Basic file operations with security constraints",
            version="2.0.0",
            tool_type=ToolType.BUILTIN,
            capabilities=[ToolCapability.FILE_SYSTEM, ToolCapability.DATA_ACCESS]
        )
        
        # Add methods
        metadata.add_method(create_method_schema(
            name="read_file",
            description="Read content from a text file",
            parameters={
                "path": {"type": "string", "required": True, "description": "Path to file to read"},
                "encoding": {"type": "string", "required": False, "default": "utf-8", "description": "File encoding"}
            },
            returns="File content as string"
        ))
        
        metadata.add_method(create_method_schema(
            name="write_file",
            description="Write content to a text file",
            parameters={
                "path": {"type": "string", "required": True, "description": "Path to file to write"},
                "content": {"type": "string", "required": True, "description": "Content to write"},
                "encoding": {"type": "string", "required": False, "default": "utf-8", "description": "File encoding"},
                "create_dirs": {"type": "boolean", "required": False, "default": False, "description": "Create parent directories if needed"}
            },
            returns="Success message with file info"
        ))
        
        metadata.add_method(create_method_schema(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "path": {"type": "string", "required": False, "default": ".", "description": "Directory path to list"},
                "include_hidden": {"type": "boolean", "required": False, "default": False, "description": "Include hidden files"},
                "details": {"type": "boolean", "required": False, "default": False, "description": "Include file details"}
            },
            returns="List of directory contents"
        ))
        
        metadata.add_method(create_method_schema(
            name="file_info",
            description="Get information about a file or directory",
            parameters={
                "path": {"type": "string", "required": True, "description": "Path to file or directory"}
            },
            returns="File information including size, permissions, timestamps"
        ))
        
        metadata.add_method(create_method_schema(
            name="file_exists",
            description="Check if a file or directory exists",
            parameters={
                "path": {"type": "string", "required": True, "description": "Path to check"}
            },
            returns="Boolean indicating if path exists"
        ))
        
        metadata.add_method(create_method_schema(
            name="create_directory",
            description="Create a directory",
            parameters={
                "path": {"type": "string", "required": True, "description": "Directory path to create"},
                "parents": {"type": "boolean", "required": False, "default": False, "description": "Create parent directories if needed"}
            },
            returns="Success message"
        ))
        
        metadata.add_method(create_method_schema(
            name="delete_file",
            description="Delete a file or empty directory",
            parameters={
                "path": {"type": "string", "required": True, "description": "Path to delete"}
            },
            returns="Success message"
        ))
        
        super().__init__(metadata)
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path within base directory"""
        try:
            # Convert to Path and resolve
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.base_path / file_path
            
            resolved_path = file_path.resolve()
            
            # Check if path is within base directory
            try:
                resolved_path.relative_to(self.base_path.resolve())
            except ValueError:
                raise ValueError(f"Path {path} is outside allowed base directory {self.base_path}")
            
            return resolved_path
        except Exception as e:
            raise ValueError(f"Invalid path {path}: {e}")
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read content from a text file"""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Check file size
        size = file_path.stat().st_size
        if size > self.max_file_size:
            raise ValueError(f"File too large: {size} bytes > {self.max_file_size}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            raise ValueError(f"Unable to decode file with encoding {encoding}: {e}")
    
    async def write_file(self, path: str, content: str, encoding: str = "utf-8", create_dirs: bool = False) -> Dict[str, Any]:
        """Write content to a text file"""
        file_path = self._validate_path(path)
        
        # Check content size
        content_size = len(content.encode(encoding))
        if content_size > self.max_file_size:
            raise ValueError(f"Content too large: {content_size} bytes > {self.max_file_size}")
        
        # Create parent directories if needed
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        elif not file_path.parent.exists():
            raise FileNotFoundError(f"Parent directory does not exist: {file_path.parent}")
        
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            stat_info = file_path.stat()
            return {
                "success": True,
                "path": str(file_path),
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            }
        except Exception as e:
            raise ValueError(f"Unable to write file: {e}")
    
    async def list_directory(self, path: str = ".", include_hidden: bool = False, details: bool = False) -> List[Dict[str, Any]]:
        """List contents of a directory"""
        dir_path = self._validate_path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        items = []
        try:
            for item in sorted(dir_path.iterdir()):
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file"
                }
                
                if details:
                    try:
                        stat_info = item.stat()
                        item_info.update({
                            "size": stat_info.st_size if item.is_file() else None,
                            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                            "permissions": oct(stat_info.st_mode)[-3:],
                            "path": str(item)
                        })
                    except OSError:
                        item_info["error"] = "Cannot access file info"
                
                items.append(item_info)
            
            return items
        except PermissionError:
            raise ValueError(f"Permission denied accessing directory: {path}")
    
    async def file_info(self, path: str) -> Dict[str, Any]:
        """Get information about a file or directory"""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        try:
            stat_info = file_path.stat()
            return {
                "path": str(file_path),
                "name": file_path.name,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat_info.st_size if file_path.is_file() else None,
                "permissions": oct(stat_info.st_mode)[-3:],
                "owner_readable": bool(stat_info.st_mode & stat.S_IRUSR),
                "owner_writable": bool(stat_info.st_mode & stat.S_IWUSR),
                "owner_executable": bool(stat_info.st_mode & stat.S_IXUSR),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat()
            }
        except OSError as e:
            raise ValueError(f"Unable to get file info: {e}")
    
    async def file_exists(self, path: str) -> bool:
        """Check if a file or directory exists"""
        try:
            file_path = self._validate_path(path)
            return file_path.exists()
        except ValueError:
            return False
    
    async def create_directory(self, path: str, parents: bool = False) -> Dict[str, Any]:
        """Create a directory"""
        dir_path = self._validate_path(path)
        
        if dir_path.exists():
            if dir_path.is_dir():
                return {"success": True, "message": "Directory already exists", "path": str(dir_path)}
            else:
                raise ValueError(f"Path exists but is not a directory: {path}")
        
        try:
            dir_path.mkdir(parents=parents)
            return {"success": True, "message": "Directory created", "path": str(dir_path)}
        except FileNotFoundError:
            raise ValueError(f"Parent directory does not exist: {dir_path.parent}")
        except OSError as e:
            raise ValueError(f"Unable to create directory: {e}")
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file or empty directory"""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        try:
            if file_path.is_file():
                file_path.unlink()
                return {"success": True, "message": "File deleted", "path": str(file_path)}
            elif file_path.is_dir():
                file_path.rmdir()  # Only removes empty directories
                return {"success": True, "message": "Directory deleted", "path": str(file_path)}
            else:
                raise ValueError(f"Unknown file type: {path}")
        except OSError as e:
            if "Directory not empty" in str(e):
                raise ValueError(f"Directory not empty: {path}")
            else:
                raise ValueError(f"Unable to delete: {e}")
    
    def run(self, input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        MCP-compatible run method
        """
        if input_data is None:
            input_data = kwargs
        
        method = input_data.get('method', 'list_directory')
        method_args = {k: v for k, v in input_data.items() if k != 'method'}
        
        if method == 'read_file':
            return asyncio.run(self.read_file(**method_args))
        elif method == 'write_file':
            return asyncio.run(self.write_file(**method_args))
        elif method == 'list_directory':
            return asyncio.run(self.list_directory(**method_args))
        elif method == 'file_info':
            return asyncio.run(self.file_info(**method_args))
        elif method == 'file_exists':
            return asyncio.run(self.file_exists(**method_args))
        elif method == 'create_directory':
            return asyncio.run(self.create_directory(**method_args))
        elif method == 'delete_file':
            return asyncio.run(self.delete_file(**method_args))
        else:
            raise ValueError(f"Unknown method: {method}")
