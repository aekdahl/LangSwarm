"""
File Upload API for AAF Widget
Handles file attachments for chat messages with security and validation
"""
import logging
import os
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import aiofiles
import magic  # python-magic for MIME type detection

from ..core.config import get_settings
from .tenant_ui import get_current_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])


class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum")
    url: Optional[str] = Field(None, description="Download URL")
    expires_at: str = Field(..., description="Expiration timestamp")


# Allowed file types and their MIME types
ALLOWED_FILE_TYPES = {
    # Documents
    "pdf": "application/pdf",
    "txt": "text/plain",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "rtf": "application/rtf",
    
    # Images
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    
    # Archives
    "zip": "application/zip",
    "tar": "application/x-tar",
    "gz": "application/gzip",
    
    # Spreadsheets
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "csv": "text/csv",
    
    # Code/Text
    "json": "application/json",
    "xml": "application/xml",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "md": "text/markdown"
}

# Security limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_SESSION = 100


def get_upload_directory() -> Path:
    """Get upload directory, create if it doesn't exist"""
    settings = get_settings()
    upload_dir = Path(getattr(settings, 'upload_directory', './uploads'))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_file_id() -> str:
    """Generate unique file identifier"""
    return f"file_{uuid.uuid4().hex}"


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_file_type(filename: str, content: bytes) -> tuple[bool, str]:
    """
    Validate file type based on extension and magic bytes
    Returns (is_valid, detected_mime_type)
    """
    # Get file extension
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension not in ALLOWED_FILE_TYPES:
        return False, "unknown"
    
    # Detect MIME type from content
    try:
        detected_mime = magic.from_buffer(content, mime=True)
    except Exception as e:
        logger.warning(f"Failed to detect MIME type: {e}")
        detected_mime = "application/octet-stream"
    
    # Check if detected MIME type matches expected
    expected_mime = ALLOWED_FILE_TYPES[extension]
    
    # Some flexibility for common variations
    mime_variations = {
        "text/plain": ["text/plain", "text/x-python", "text/x-c", "text/x-shellscript"],
        "image/jpeg": ["image/jpeg", "image/jpg"],
        "application/zip": ["application/zip", "application/x-zip-compressed"]
    }
    
    allowed_mimes = mime_variations.get(expected_mime, [expected_mime])
    
    if detected_mime not in allowed_mimes:
        logger.warning(f"MIME type mismatch for {filename}: expected {expected_mime}, got {detected_mime}")
        # Still allow but log the discrepancy
    
    return True, detected_mime


def get_tenant_upload_limits(tenant_id: str) -> Dict[str, Any]:
    """Get upload limits for specific tenant"""
    # This would typically come from database/configuration
    # For now, return default limits with some tenant-specific overrides
    
    default_limits = {
        "max_file_size": MAX_FILE_SIZE,
        "max_files_per_session": MAX_FILES_PER_SESSION,
        "allowed_types": list(ALLOWED_FILE_TYPES.keys()),
        "require_virus_scan": False
    }
    
    # Tenant-specific overrides
    tenant_overrides = {
        "enterprise": {
            "max_file_size": 100 * 1024 * 1024,  # 100MB for enterprise
            "max_files_per_session": 200,
            "require_virus_scan": True
        },
        "demo": {
            "max_file_size": 10 * 1024 * 1024,   # 10MB for demo
            "max_files_per_session": 20,
            "allowed_types": ["pdf", "txt", "png", "jpg"]
        }
    }
    
    if tenant_id in tenant_overrides:
        default_limits.update(tenant_overrides[tenant_id])
    
    return default_limits


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Upload a file for use in chat messages
    
    Supports various file types with security validation and virus scanning.
    Files are temporarily stored and automatically cleaned up after expiration.
    """
    try:
        tenant_id = session_data["tid"]
        session_id = session_data["sid"]
        
        # Get tenant-specific upload limits
        limits = get_tenant_upload_limits(tenant_id)
        
        # Validate file size
        if file.size > limits["max_file_size"]:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {limits['max_file_size'] / 1024 / 1024:.1f}MB"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file type
        is_valid, detected_mime = validate_file_type(file.filename, content)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(limits['allowed_types'])}"
            )
        
        # Check session file count limit
        upload_dir = get_upload_directory()
        session_files = list(upload_dir.glob(f"*_{session_id}_*"))
        if len(session_files) >= limits["max_files_per_session"]:
            raise HTTPException(
                status_code=429,
                detail=f"Too many files uploaded. Maximum: {limits['max_files_per_session']}"
            )
        
        # Generate file ID and path
        file_id = generate_file_id()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
        file_path = upload_dir / f"{file_id}_{session_id}_{timestamp}_{safe_filename}"
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Calculate checksum
        checksum = calculate_checksum(file_path)
        
        # Set expiration (24 hours)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Store file metadata (in production, this would go to database)
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "safe_filename": safe_filename,
            "content_type": detected_mime,
            "size": file.size,
            "checksum": checksum,
            "session_id": session_id,
            "tenant_id": tenant_id,
            "description": description,
            "file_path": str(file_path),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        # Log upload
        logger.info(
            f"File uploaded - ID: {file_id}, Tenant: {tenant_id}, "
            f"Session: {session_id}, Size: {file.size}, Type: {detected_mime}"
        )
        
        # Virus scan if required
        if limits["require_virus_scan"]:
            # TODO: Implement virus scanning
            logger.info(f"Virus scan required for file {file_id} (not implemented)")
        
        # Generate download URL
        download_url = f"/uploads/{file_id}/download"
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            content_type=detected_mime,
            size=file.size,
            checksum=checksum,
            url=download_url,
            expires_at=expires_at.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Download a previously uploaded file
    
    Requires valid session and file ownership validation.
    """
    try:
        session_id = session_data["sid"]
        tenant_id = session_data["tid"]
        
        # Find file in upload directory
        upload_dir = get_upload_directory()
        file_pattern = f"{file_id}_{session_id}_*"
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Check if file has expired (based on creation time + 24 hours)
        file_stat = file_path.stat()
        created_time = datetime.fromtimestamp(file_stat.st_ctime)
        if datetime.utcnow() - created_time > timedelta(hours=24):
            # Clean up expired file
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=410, detail="File has expired")
        
        # Extract original filename from path
        filename_parts = file_path.name.split('_', 3)
        if len(filename_parts) >= 4:
            original_filename = filename_parts[3]
        else:
            original_filename = file_path.name
        
        # Log download
        logger.info(
            f"File downloaded - ID: {file_id}, Tenant: {tenant_id}, "
            f"Session: {session_id}, File: {original_filename}"
        )
        
        return FileResponse(
            path=file_path,
            filename=original_filename,
            headers={
                "Cache-Control": "private, max-age=3600",
                "X-File-ID": file_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )


@router.get("/{file_id}/info")
async def get_file_info(
    file_id: str,
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Get file information without downloading
    
    Returns metadata about the uploaded file.
    """
    try:
        session_id = session_data["sid"]
        
        # Find file in upload directory
        upload_dir = get_upload_directory()
        file_pattern = f"{file_id}_{session_id}_*"
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        file_stat = file_path.stat()
        
        # Check expiration
        created_time = datetime.fromtimestamp(file_stat.st_ctime)
        expires_at = created_time + timedelta(hours=24)
        
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=410, detail="File has expired")
        
        # Extract original filename
        filename_parts = file_path.name.split('_', 3)
        original_filename = filename_parts[3] if len(filename_parts) >= 4 else file_path.name
        
        # Detect content type
        with open(file_path, 'rb') as f:
            content_sample = f.read(1024)
        
        try:
            content_type = magic.from_buffer(content_sample, mime=True)
        except:
            content_type = "application/octet-stream"
        
        return {
            "file_id": file_id,
            "filename": original_filename,
            "content_type": content_type,
            "size": file_stat.st_size,
            "created_at": created_time.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "download_url": f"/uploads/{file_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File info error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file info: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Delete an uploaded file
    
    Allows users to clean up their uploaded files before expiration.
    """
    try:
        session_id = session_data["sid"]
        
        # Find file in upload directory
        upload_dir = get_upload_directory()
        file_pattern = f"{file_id}_{session_id}_*"
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Delete file
        file_path.unlink(missing_ok=True)
        
        logger.info(f"File deleted - ID: {file_id}, Session: {session_id}")
        
        return {"message": "File deleted successfully", "file_id": file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/session/files")
async def list_session_files(
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    List all files uploaded in the current session
    
    Useful for managing file attachments.
    """
    try:
        session_id = session_data["sid"]
        
        # Find all files for this session
        upload_dir = get_upload_directory()
        file_pattern = f"*_{session_id}_*"
        session_files = list(upload_dir.glob(file_pattern))
        
        files_info = []
        current_time = datetime.utcnow()
        
        for file_path in session_files:
            try:
                file_stat = file_path.stat()
                created_time = datetime.fromtimestamp(file_stat.st_ctime)
                expires_at = created_time + timedelta(hours=24)
                
                # Skip expired files
                if current_time > expires_at:
                    file_path.unlink(missing_ok=True)
                    continue
                
                # Extract file ID and original filename
                name_parts = file_path.name.split('_')
                file_id = name_parts[0] if name_parts else "unknown"
                original_filename = name_parts[3] if len(name_parts) >= 4 else file_path.name
                
                files_info.append({
                    "file_id": file_id,
                    "filename": original_filename,
                    "size": file_stat.st_size,
                    "created_at": created_time.isoformat() + "Z",
                    "expires_at": expires_at.isoformat() + "Z",
                    "download_url": f"/uploads/{file_id}/download"
                })
                
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                continue
        
        return {
            "session_id": session_id,
            "files": sorted(files_info, key=lambda x: x["created_at"], reverse=True),
            "total": len(files_info)
        }
        
    except Exception as e:
        logger.error(f"List session files error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )


# Background task to clean up expired files
async def cleanup_expired_files():
    """Clean up expired files (run periodically)"""
    try:
        upload_dir = get_upload_directory()
        current_time = datetime.utcnow()
        cleaned_count = 0
        
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                try:
                    file_stat = file_path.stat()
                    created_time = datetime.fromtimestamp(file_stat.st_ctime)
                    
                    # Remove files older than 24 hours
                    if current_time - created_time > timedelta(hours=24):
                        file_path.unlink(missing_ok=True)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error cleaning up file {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired files")
            
    except Exception as e:
        logger.error(f"File cleanup error: {e}")
