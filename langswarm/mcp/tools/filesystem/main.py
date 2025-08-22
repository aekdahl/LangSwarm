# mcp/tools/filesystem/main.py

import os
import stat
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import uvicorn
from datetime import datetime
import re
import io

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool

# Optional GCS support
try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound as GCSNotFound
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# === Permission Configuration ===
class PermissionZone:
    """Defines permission levels for filesystem paths"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write" 
    FORBIDDEN = "forbidden"

# Default permission configuration (supports both local and GCS paths)
DEFAULT_PERMISSIONS = {
    "/": PermissionZone.READ_ONLY,  # Root is read-only by default
    "~/": PermissionZone.READ_ONLY,  # Home is read-only by default
    "~/agent_workspace/": PermissionZone.READ_WRITE,  # Agent workspace is read-write
    "gs://": PermissionZone.READ_ONLY,  # GCS buckets read-only by default
    "gs://agent-workspace/": PermissionZone.READ_WRITE,  # Agent GCS workspace
}

# === Cloud Storage Support ===
class CloudStorageBackend:
    """Base class for cloud storage backends"""
    
    def list_objects(self, path: str, show_hidden: bool = False, recursive: bool = False) -> List[Dict]:
        raise NotImplementedError
    
    def read_object(self, path: str, encoding: str = "utf-8") -> Dict:
        raise NotImplementedError
    
    def write_object(self, path: str, content: str, encoding: str = "utf-8") -> Dict:
        raise NotImplementedError
    
    def delete_object(self, path: str) -> Dict:
        raise NotImplementedError
    
    def get_object_info(self, path: str) -> Dict:
        raise NotImplementedError

class GCSBackend(CloudStorageBackend):
    """Google Cloud Storage backend"""
    
    def __init__(self, project_id: str = None):
        if not GCS_AVAILABLE:
            raise ImportError("Google Cloud Storage support requires: pip install google-cloud-storage")
        
        self.client = storage.Client(project=project_id)
    
    def _parse_gcs_path(self, gcs_path: str) -> tuple:
        """Parse gs://bucket/path into bucket and object components"""
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_path}")
        
        path_parts = gcs_path[5:].split('/', 1)  # Remove gs:// prefix
        bucket_name = path_parts[0]
        object_path = path_parts[1] if len(path_parts) > 1 else ""
        
        return bucket_name, object_path
    
    def list_objects(self, path: str, show_hidden: bool = False, recursive: bool = False) -> List[Dict]:
        """List GCS objects with metadata"""
        bucket_name, prefix = self._parse_gcs_path(path)
        bucket = self.client.bucket(bucket_name)
        
        # Ensure prefix ends with / for directory-style listing
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        
        objects = []
        
        try:
            if recursive:
                # List all objects with prefix
                blobs = bucket.list_blobs(prefix=prefix)
            else:
                # List objects with delimiter for "folder" view
                blobs = bucket.list_blobs(prefix=prefix, delimiter='/')
            
            for blob in blobs:
                # Skip hidden files if requested
                blob_name = blob.name
                if not show_hidden and any(part.startswith('.') for part in blob_name.split('/')):
                    continue
                
                # Determine if this is a "directory" (prefix) or file
                is_directory = blob_name.endswith('/')
                relative_name = blob_name[len(prefix):] if prefix else blob_name
                
                if not relative_name:  # Skip the prefix itself
                    continue
                
                objects.append({
                    "name": relative_name.rstrip('/'),
                    "type": "directory" if is_directory else "file",
                    "size": 0 if is_directory else blob.size,
                    "modified": blob.updated.isoformat() if blob.updated else None,
                    "permissions": "644",  # GCS doesn't have traditional permissions
                    "etag": blob.etag,
                    "storage_class": blob.storage_class
                })
            
            # Handle "folder" prefixes from delimiter listing
            if hasattr(blobs, 'prefixes'):
                for folder_prefix in blobs.prefixes:
                    folder_name = folder_prefix[len(prefix):].rstrip('/')
                    if folder_name:
                        objects.append({
                            "name": folder_name,
                            "type": "directory",
                            "size": 0,
                            "modified": None,
                            "permissions": "755",
                            "etag": None,
                            "storage_class": None
                        })
        
        except Exception as e:
            raise PermissionError(f"Cannot access GCS path {path}: {str(e)}")
        
        return objects
    
    def read_object(self, path: str, encoding: str = "utf-8") -> Dict:
        """Read GCS object content"""
        bucket_name, object_path = self._parse_gcs_path(path)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        
        try:
            if not blob.exists():
                raise FileNotFoundError(f"GCS object not found: {path}")
            
            content = blob.download_as_text(encoding=encoding)
            
            return {
                "path": path,
                "content": content,
                "size_bytes": blob.size,
                "encoding": encoding,
                "etag": blob.etag,
                "content_type": blob.content_type
            }
        
        except UnicodeDecodeError:
            raise ValueError(f"Cannot decode GCS object {path} with encoding {encoding}")
        except Exception as e:
            raise PermissionError(f"Cannot read GCS object {path}: {str(e)}")
    
    def write_object(self, path: str, content: str, encoding: str = "utf-8") -> Dict:
        """Write content to GCS object"""
        bucket_name, object_path = self._parse_gcs_path(path)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        
        try:
            # Upload content
            blob.upload_from_string(content, content_type='text/plain')
            
            return {
                "path": path,
                "status": "created",
                "bytes_written": len(content.encode(encoding)),
                "etag": blob.etag
            }
        
        except Exception as e:
            raise PermissionError(f"Cannot write to GCS object {path}: {str(e)}")
    
    def delete_object(self, path: str) -> Dict:
        """Delete GCS object"""
        bucket_name, object_path = self._parse_gcs_path(path)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        
        try:
            if not blob.exists():
                raise FileNotFoundError(f"GCS object not found: {path}")
            
            blob.delete()
            
            return {
                "path": path,
                "status": "deleted",
                "deleted_type": "file"
            }
        
        except Exception as e:
            raise PermissionError(f"Cannot delete GCS object {path}: {str(e)}")
    
    def get_object_info(self, path: str) -> Dict:
        """Get GCS object information"""
        bucket_name, object_path = self._parse_gcs_path(path)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        
        try:
            blob.reload()  # Fetch metadata
            exists = blob.exists()
            
            if not exists:
                return {
                    "path": path,
                    "exists": False,
                    "type": None,
                    "size_bytes": None,
                    "permissions": None,
                    "created": None,
                    "modified": None,
                    "backend": "gcs"
                }
            
            return {
                "path": path,
                "exists": True,
                "type": "file",
                "size_bytes": blob.size,
                "permissions": "644",  # GCS doesn't have traditional permissions
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "modified": blob.updated.isoformat() if blob.updated else None,
                "backend": "gcs",
                "etag": blob.etag,
                "content_type": blob.content_type,
                "storage_class": blob.storage_class
            }
        
        except Exception as e:
            raise PermissionError(f"Cannot access GCS object {path}: {str(e)}")

# === Path Detection and Routing ===
def is_gcs_path(path: str) -> bool:
    """Check if path is a GCS URL"""
    return path.startswith("gs://")

def get_storage_backend(path: str, gcs_project_id: str = None) -> Optional[CloudStorageBackend]:
    """Get appropriate storage backend for path"""
    if is_gcs_path(path):
        if not GCS_AVAILABLE:
            raise ImportError("GCS support requires: pip install google-cloud-storage")
        return GCSBackend(project_id=gcs_project_id)
    return None

# === Schemas ===
class ListDirInput(BaseModel):
    path: str
    show_hidden: Optional[bool] = False
    recursive: Optional[bool] = False

class ListDirOutput(BaseModel):
    path: str
    contents: List[Dict[str, Union[str, int, bool]]]
    total_items: int
    permission_level: str

class ReadFileInput(BaseModel):
    path: str
    encoding: Optional[str] = "utf-8"

class ReadFileOutput(BaseModel):
    path: str
    content: str
    size_bytes: int
    encoding: str

class WriteFileInput(BaseModel):
    path: str
    content: str
    encoding: Optional[str] = "utf-8"
    create_dirs: Optional[bool] = True

class WriteFileOutput(BaseModel):
    path: str
    status: str
    bytes_written: int

class UpdateFileInput(BaseModel):
    path: str
    content: str
    mode: Optional[str] = "append"  # "append" or "overwrite"
    encoding: Optional[str] = "utf-8"

class UpdateFileOutput(BaseModel):
    path: str
    status: str
    bytes_written: int

class DeleteFileInput(BaseModel):
    path: str
    force: Optional[bool] = False

class DeleteFileOutput(BaseModel):
    path: str
    status: str
    deleted_type: str  # "file" or "directory"

class CreateDirInput(BaseModel):
    path: str
    parents: Optional[bool] = True

class CreateDirOutput(BaseModel):
    path: str
    status: str

class GetInfoInput(BaseModel):
    path: str

class GetInfoOutput(BaseModel):
    path: str
    exists: bool
    type: Optional[str]  # "file", "directory", "symlink"
    size_bytes: Optional[int]
    permissions: Optional[str]
    created: Optional[str]
    modified: Optional[str]
    permission_level: str

# === Permission System ===
def get_permission_level(path: str, permissions: Dict[str, str] = None) -> str:
    """Determine permission level for a given path (supports both local and GCS paths)"""
    if permissions is None:
        permissions = DEFAULT_PERMISSIONS
    
    # Handle GCS paths differently than local paths
    if is_gcs_path(path):
        # For GCS paths, use direct string matching with prefixes
        best_match = ""
        permission_level = PermissionZone.READ_ONLY
        
        for rule_path, level in permissions.items():
            if is_gcs_path(rule_path) and path.startswith(rule_path) and len(rule_path) > len(best_match):
                best_match = rule_path
                permission_level = level
        
        return permission_level
    else:
        # For local paths, use the original logic
        normalized_path = os.path.expanduser(os.path.abspath(path))
        
        # Check each permission rule (longest match wins)
        best_match = ""
        permission_level = PermissionZone.READ_ONLY
        
        for rule_path, level in permissions.items():
            # Skip GCS rules for local paths
            if is_gcs_path(rule_path):
                continue
                
            rule_path = os.path.expanduser(os.path.abspath(rule_path))
            if normalized_path.startswith(rule_path) and len(rule_path) > len(best_match):
                best_match = rule_path
                permission_level = level
        
        return permission_level

def check_permission(path: str, required_permission: str, permissions: Dict[str, str] = None) -> None:
    """Check if path has required permission level"""
    current_permission = get_permission_level(path, permissions)
    
    if current_permission == PermissionZone.FORBIDDEN:
        raise PermissionError(f"Access forbidden to path: {path}")
    
    if required_permission == PermissionZone.READ_WRITE and current_permission != PermissionZone.READ_WRITE:
        raise PermissionError(f"Write access denied to path: {path} (current: {current_permission})")

def validate_path_safety(path: str) -> str:
    """Validate path for safety and return normalized path (supports local and GCS paths)"""
    # Handle GCS paths
    if is_gcs_path(path):
        # Basic safety checks for GCS paths
        if ".." in path:
            raise ValueError("Path traversal not allowed in GCS paths")
        
        # Validate GCS path format
        if not re.match(r'^gs://[a-z0-9][a-z0-9\-_\.]*[a-z0-9](/.*)?$', path):
            raise ValueError("Invalid GCS path format")
        
        return path  # GCS paths don't need normalization
    else:
        # Handle local paths
        normalized_path = os.path.expanduser(os.path.abspath(path))
        
        # Basic safety checks
        if ".." in path:
            raise ValueError("Path traversal not allowed")
        
        return normalized_path

# === Enhanced Handlers ===
def list_directory(path: str, show_hidden: bool = False, recursive: bool = False, permissions: Dict[str, str] = None, gcs_project_id: str = None):
    """List directory contents with enhanced metadata (supports local and GCS paths)"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_ONLY, permissions)
    
    # Check if this is a GCS path
    if is_gcs_path(normalized_path):
        try:
            backend = get_storage_backend(normalized_path, gcs_project_id)
            contents = backend.list_objects(normalized_path, show_hidden, recursive)
            
            return {
                "path": path,
                "contents": contents,
                "total_items": len(contents),
                "permission_level": get_permission_level(normalized_path, permissions),
                "backend": "gcs"
            }
        except Exception as e:
            raise PermissionError(f"Cannot access GCS path {path}: {str(e)}")
    
    # Handle local filesystem
    if not os.path.isdir(normalized_path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    contents = []
    total_items = 0
    
    try:
        if recursive:
            # Recursive listing
            for root, dirs, files in os.walk(normalized_path):
                # Filter hidden items if needed
                if not show_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                # Add directories
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    rel_path = os.path.relpath(dir_path, normalized_path)
                    contents.append({
                        "name": rel_path,
                        "type": "directory",
                        "size": 0,
                        "modified": datetime.fromtimestamp(os.path.getmtime(dir_path)).isoformat(),
                        "permissions": oct(os.stat(dir_path).st_mode)[-3:]
                    })
                    total_items += 1
                
                # Add files
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, normalized_path)
                    stat_info = os.stat(file_path)
                    contents.append({
                        "name": rel_path,
                        "type": "file",
                        "size": stat_info.st_size,
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "permissions": oct(stat_info.st_mode)[-3:]
                    })
                    total_items += 1
        else:
            # Non-recursive listing
            items = os.listdir(normalized_path)
            if not show_hidden:
                items = [item for item in items if not item.startswith('.')]
            
            for item in items:
                item_path = os.path.join(normalized_path, item)
                stat_info = os.stat(item_path)
                is_dir = os.path.isdir(item_path)
                
                contents.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": 0 if is_dir else stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "permissions": oct(stat_info.st_mode)[-3:]
                })
                total_items += 1
    
    except PermissionError as e:
        raise PermissionError(f"Permission denied accessing directory: {path}")
    
    return {
        "path": path,
        "contents": contents,
        "total_items": total_items,
        "permission_level": get_permission_level(normalized_path, permissions),
        "backend": "local"
    }

def read_file(path: str, encoding: str = "utf-8", permissions: Dict[str, str] = None, gcs_project_id: str = None):
    """Read file contents with enhanced error handling (supports local and GCS paths)"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_ONLY, permissions)
    
    # Check if this is a GCS path
    if is_gcs_path(normalized_path):
        try:
            backend = get_storage_backend(normalized_path, gcs_project_id)
            result = backend.read_object(normalized_path, encoding)
            result["backend"] = "gcs"
            return result
        except Exception as e:
            raise PermissionError(f"Cannot read GCS object {path}: {str(e)}")
    
    # Handle local filesystem
    if not os.path.isfile(normalized_path):
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        with open(normalized_path, 'r', encoding=encoding) as file:
            content = file.read()
        
        size_bytes = os.path.getsize(normalized_path)
        
        return {
            "path": path,
            "content": content,
            "size_bytes": size_bytes,
            "encoding": encoding,
            "backend": "local"
        }
    except UnicodeDecodeError:
        raise ValueError(f"Cannot decode file {path} with encoding {encoding}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {path}")

def write_file(path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True, permissions: Dict[str, str] = None, gcs_project_id: str = None):
    """Write/create file with permission checking (supports local and GCS paths)"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_WRITE, permissions)
    
    # Check if this is a GCS path
    if is_gcs_path(normalized_path):
        try:
            backend = get_storage_backend(normalized_path, gcs_project_id)
            result = backend.write_object(normalized_path, content, encoding)
            result["backend"] = "gcs"
            return result
        except Exception as e:
            raise PermissionError(f"Cannot write to GCS object {path}: {str(e)}")
    
    # Handle local filesystem
    
    # Create parent directories if requested
    if create_dirs:
        parent_dir = os.path.dirname(normalized_path)
        if parent_dir and not os.path.exists(parent_dir):
            check_permission(parent_dir, PermissionZone.READ_WRITE, permissions)
            os.makedirs(parent_dir, exist_ok=True)
    
    try:
        with open(normalized_path, 'w', encoding=encoding) as file:
            file.write(content)
        
        bytes_written = len(content.encode(encoding))
        
        return {
            "path": path,
            "status": "created" if not os.path.exists(normalized_path) else "overwritten",
            "bytes_written": bytes_written
        }
    except PermissionError:
        raise PermissionError(f"Permission denied writing to file: {path}")

def update_file(path: str, content: str, mode: str = "append", encoding: str = "utf-8", permissions: Dict[str, str] = None):
    """Update file content (append or overwrite)"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_WRITE, permissions)
    
    if not os.path.isfile(normalized_path):
        raise FileNotFoundError(f"File not found: {path}")
    
    file_mode = "a" if mode == "append" else "w"
    
    try:
        with open(normalized_path, file_mode, encoding=encoding) as file:
            file.write(content)
        
        bytes_written = len(content.encode(encoding))
        
        return {
            "path": path,
            "status": f"{mode}ed",
            "bytes_written": bytes_written
        }
    except PermissionError:
        raise PermissionError(f"Permission denied updating file: {path}")

def delete_file(path: str, force: bool = False, permissions: Dict[str, str] = None):
    """Delete file or directory with safety checks"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_WRITE, permissions)
    
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"Path not found: {path}")
    
    is_directory = os.path.isdir(normalized_path)
    
    try:
        if is_directory:
            if force:
                import shutil
                shutil.rmtree(normalized_path)
            else:
                # Only delete empty directories by default
                os.rmdir(normalized_path)
        else:
            os.remove(normalized_path)
        
        return {
            "path": path,
            "status": "deleted",
            "deleted_type": "directory" if is_directory else "file"
        }
    except OSError as e:
        if is_directory and not force:
            raise ValueError(f"Directory not empty: {path}. Use force=True to delete non-empty directories.")
        else:
            raise PermissionError(f"Permission denied deleting: {path}")

def create_directory(path: str, parents: bool = True, permissions: Dict[str, str] = None):
    """Create directory with permission checking"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_WRITE, permissions)
    
    if os.path.exists(normalized_path):
        raise FileExistsError(f"Path already exists: {path}")
    
    try:
        if parents:
            os.makedirs(normalized_path, exist_ok=False)
        else:
            os.mkdir(normalized_path)
        
        return {
            "path": path,
            "status": "created"
        }
    except PermissionError:
        raise PermissionError(f"Permission denied creating directory: {path}")

def get_file_info(path: str, permissions: Dict[str, str] = None, gcs_project_id: str = None):
    """Get detailed file/directory information (supports local and GCS paths)"""
    normalized_path = validate_path_safety(path)
    check_permission(normalized_path, PermissionZone.READ_ONLY, permissions)
    
    # Check if this is a GCS path
    if is_gcs_path(normalized_path):
        try:
            backend = get_storage_backend(normalized_path, gcs_project_id)
            result = backend.get_object_info(normalized_path)
            result["permission_level"] = get_permission_level(normalized_path, permissions)
            return result
        except Exception as e:
            return {
                "path": path,
                "exists": False,
                "error": str(e),
                "backend": "gcs",
                "permission_level": get_permission_level(normalized_path, permissions)
            }
    
    # Handle local filesystem
    exists = os.path.exists(normalized_path)
    
    if not exists:
        return {
            "path": path,
            "exists": False,
            "type": None,
            "size_bytes": None,
            "permissions": None,
            "created": None,
            "modified": None,
            "permission_level": get_permission_level(normalized_path, permissions)
        }
    
    stat_info = os.stat(normalized_path)
    
    # Determine type
    if os.path.isfile(normalized_path):
        file_type = "file"
    elif os.path.isdir(normalized_path):
        file_type = "directory"
    elif os.path.islink(normalized_path):
        file_type = "symlink"
    else:
        file_type = "other"
    
    return {
        "path": path,
        "exists": True,
        "type": file_type,
        "size_bytes": stat_info.st_size,
        "permissions": oct(stat_info.st_mode)[-3:],
        "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
        "permission_level": get_permission_level(normalized_path, permissions)
    }

# === Build MCP Server ===
server = BaseMCPToolServer(
    name="filesystem",
    description="Enhanced filesystem access with configurable permissions for safe CRUD operations.",
    local_mode=True  # 🔧 Enable local mode!
)

# Read operations (available in all permission zones)
server.add_task(
    name="list_directory",
    description="List directory contents with metadata and permission info.",
    input_model=ListDirInput,
    output_model=ListDirOutput,
    handler=list_directory
)

server.add_task(
    name="read_file",
    description="Read file contents with encoding support.",
    input_model=ReadFileInput,
    output_model=ReadFileOutput,
    handler=read_file
)

server.add_task(
    name="get_file_info",
    description="Get detailed file/directory information and permissions.",
    input_model=GetInfoInput,
    output_model=GetInfoOutput,
    handler=get_file_info
)

# Write operations (require read_write permission)
server.add_task(
    name="write_file",
    description="Create or overwrite a file (requires write permissions).",
    input_model=WriteFileInput,
    output_model=WriteFileOutput,
    handler=write_file
)

server.add_task(
    name="update_file",
    description="Update file content by appending or overwriting (requires write permissions).",
    input_model=UpdateFileInput,
    output_model=UpdateFileOutput,
    handler=update_file
)

server.add_task(
    name="delete_file",
    description="Delete a file or directory (requires write permissions).",
    input_model=DeleteFileInput,
    output_model=DeleteFileOutput,
    handler=delete_file
)

server.add_task(
    name="create_directory",
    description="Create a new directory (requires write permissions).",
    input_model=CreateDirInput,
    output_model=CreateDirOutput,
    handler=create_directory
)

# Utility operation for agent self-discovery
class GetAllowedPathsInput(BaseModel):
    pass  # No parameters needed

class GetAllowedPathsOutput(BaseModel):
    local_filesystem: Dict
    google_cloud_storage: Dict
    permission_levels: Dict
    usage_guidelines: Dict
    available_operations: Dict

def get_allowed_paths_handler():
    """Handler for get_allowed_paths that works without instance context"""
    # This is a placeholder that will be overridden by the tool instance
    return {
        "local_filesystem": {"description": "Use the tool instance method for full details"},
        "google_cloud_storage": {"description": "Use the tool instance method for full details"},
        "permission_levels": DEFAULT_PERMISSIONS,
        "usage_guidelines": {"note": "Use get_allowed_paths method on tool instance for complete information"},
        "available_operations": {"read_operations": ["list_directory", "read_file", "get_file_info"]}
    }

server.add_task(
    name="get_allowed_paths",
    description="Get comprehensive information about allowed paths and permissions for the agent.",
    input_model=GetAllowedPathsInput,
    output_model=GetAllowedPathsOutput,
    handler=get_allowed_paths_handler
)

# Build app (None if local_mode=True)
app = server.build_app()

# === LangChain-Compatible Tool Class ===
class FilesystemMCPTool(BaseTool):
    """
    Enhanced Filesystem MCP tool with configurable permissions and CRUD operations.
    
    Features:
    - Configurable permission zones (read_only, read_write, forbidden)
    - Full CRUD operations (create, read, update, delete)
    - Safety features (path validation, permission checking)
    - Enhanced metadata (file info, timestamps, permissions)
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, mcp_url: str = None, 
                 permissions: Dict[str, str] = None, gcs_project_id: str = None, **kwargs):
        # Set defaults for enhanced filesystem MCP tool
        description = kwargs.pop('description', "Enhanced filesystem access with configurable permissions for safe CRUD operations (supports local and GCS paths)")
        instruction = kwargs.pop('instruction', (
            "Use this tool for filesystem operations with permission-based access control. "
            "Supports both local filesystem and Google Cloud Storage (GCS) paths. "
            "Available methods: list_directory, read_file, get_file_info, write_file, update_file, delete_file, create_directory. "
            "GCS paths use format: gs://bucket-name/path/to/object"
        ))
        brief = kwargs.pop('brief', "Enhanced Filesystem MCP tool with GCS support")
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
        # Initialize with BaseTool (handles all MCP setup automatically)
        super().__init__(
            name=name or f"EnhancedFilesystemMCPTool-{identifier}",
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
        
        # Store configuration AFTER parent initialization to prevent overrides
        object.__setattr__(self, 'permissions', permissions or DEFAULT_PERMISSIONS)
        object.__setattr__(self, 'gcs_project_id', gcs_project_id)
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
    
    def run(self, input_data=None):
        """Execute enhanced filesystem MCP methods locally with permission checking"""
        # Get configuration from instance
        permissions = getattr(self, 'permissions', DEFAULT_PERMISSIONS)
        gcs_project_id = getattr(self, 'gcs_project_id', None)
        
        # Define method handlers for this tool (with permissions and GCS config passed through)
        method_handlers = {
            "list_directory": lambda **kwargs: list_directory(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "read_file": lambda **kwargs: read_file(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "get_file_info": lambda **kwargs: get_file_info(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "write_file": lambda **kwargs: write_file(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "update_file": lambda **kwargs: update_file(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "delete_file": lambda **kwargs: delete_file(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "create_directory": lambda **kwargs: create_directory(permissions=permissions, gcs_project_id=gcs_project_id, **kwargs),
            "get_allowed_paths": lambda **kwargs: self.get_allowed_paths_info(),
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except PermissionError as e:
            return f"Permission Error: {str(e)}"
        except Exception as e:
            # Check if this is a method-related error by examining the input
            if isinstance(input_data, dict) and 'method' in input_data:
                method_name = input_data['method']
                return f"Error: Unknown method '{method_name}'. Available methods: {list(method_handlers.keys())}"
            else:
                return f"Error: {str(e)}"
    
    def get_permission_config(self) -> Dict[str, str]:
        """Get current permission configuration"""
        return getattr(self, 'permissions', DEFAULT_PERMISSIONS)
    
    def update_permissions(self, new_permissions: Dict[str, str]):
        """Update permission configuration"""
        object.__setattr__(self, 'permissions', new_permissions)
    
    def get_allowed_paths_info(self) -> Dict[str, any]:
        """Get comprehensive information about allowed paths and permissions for the agent"""
        permissions = getattr(self, 'permissions', DEFAULT_PERMISSIONS)
        gcs_project_id = getattr(self, 'gcs_project_id', None)
        
        # Categorize paths by permission level and backend
        local_paths = {"read_only": [], "read_write": [], "forbidden": []}
        gcs_paths = {"read_only": [], "read_write": [], "forbidden": []}
        
        for path, permission in permissions.items():
            if is_gcs_path(path):
                gcs_paths[permission].append(path)
            else:
                local_paths[permission].append(path)
        
        # Create detailed information
        path_info = {
            "local_filesystem": {
                "read_only_paths": local_paths["read_only"],
                "read_write_paths": local_paths["read_write"], 
                "forbidden_paths": local_paths["forbidden"],
                "description": "Local filesystem paths on this machine"
            },
            "google_cloud_storage": {
                "enabled": gcs_project_id is not None,
                "project_id": gcs_project_id,
                "read_only_paths": gcs_paths["read_only"],
                "read_write_paths": gcs_paths["read_write"],
                "forbidden_paths": gcs_paths["forbidden"],
                "description": "Google Cloud Storage buckets and paths",
                "path_format": "gs://bucket-name/path/to/object"
            },
            "permission_levels": {
                "read_only": "Can list directories and read files only",
                "read_write": "Full CRUD operations (create, read, update, delete)",
                "forbidden": "No access allowed - operations will fail"
            },
            "usage_guidelines": {
                "always_check_permissions": "Use get_file_info to check permissions before operations",
                "path_examples": {
                    "local_file": "~/agent_workspace/output.txt",
                    "local_directory": "~/agent_workspace/reports/",
                    "gcs_file": "gs://agent-workspace/data.json",
                    "gcs_directory": "gs://my-data-bucket/datasets/"
                },
                "safe_practices": [
                    "Check permissions with get_file_info before write operations",
                    "Use create_dirs: true when creating files in new directories", 
                    "Handle permission errors gracefully",
                    "Prefer specific paths over broad directory access"
                ]
            },
            "available_operations": {
                "read_operations": ["list_directory", "read_file", "get_file_info"],
                "write_operations": ["write_file", "update_file", "delete_file", "create_directory"],
                "utility_operations": ["get_allowed_paths"]
            }
        }
        
        return path_info

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.filesystem.main:app", host="0.0.0.0", port=4020, reload=True)
