"""
Persistent Configuration Manager for AAF
Enhances existing config system with Firestore persistence and versioning
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.cloud import firestore
from google.api_core import exceptions
import uuid
import yaml

logger = logging.getLogger(__name__)


class PersistentConfigManager:
    """
    Enhances existing config management with persistent Firestore storage
    - Maintains compatibility with existing endpoints
    - Adds versioning and backup capabilities  
    - Stores in Firestore for persistence across container restarts
    """
    
    def __init__(self, project_id: str, instance_id: str):
        self.project_id = project_id
        self.instance_id = instance_id
        self.db = firestore.Client(project=project_id)
        
        # Firestore paths
        self.config_collection = f"aaf_instances/{instance_id}/configurations"
        self.current_doc_path = f"aaf_instances/{instance_id}"
        
        logger.info(f"PersistentConfigManager initialized for instance {instance_id}")
    
    async def save_config(
        self, 
        config_data: Dict[str, Any],
        changelog: str = "Configuration update",
        user_id: str = "system"
    ) -> str:
        """
        Save configuration with automatic versioning
        Compatible with existing config-editor/update endpoint
        """
        try:
            # Generate version info
            version_id = f"v{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
            config_hash = hashlib.sha256(json.dumps(config_data, sort_keys=True).encode()).hexdigest()[:16]
            
            # Get current version for parent tracking
            current_config = await self.get_current_config()
            current_version = current_config.get("version") if current_config else None
            
            # Create version document
            version_doc = {
                "version": version_id,
                "config_data": config_data,
                "created_at": firestore.SERVER_TIMESTAMP,
                "changelog": changelog,
                "user_id": user_id,
                "config_hash": config_hash,
                "parent_version": current_version
            }
            
            # Save version
            version_ref = self.db.collection(self.config_collection).document(version_id)
            version_ref.set(version_doc)
            
            # Update current config pointer
            current_ref = self.db.document(self.current_doc_path)
            current_ref.set({
                "current_version": version_id,
                "config_data": config_data,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "updated_by": user_id,
                "config_hash": config_hash,
                "instance_id": self.instance_id,
                "project_id": self.project_id
            }, merge=True)  # Merge to preserve other instance data
            
            logger.info(f"Saved config version {version_id} for instance {self.instance_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    async def get_current_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current configuration
        Compatible with existing config-editor/current endpoint
        """
        try:
            current_ref = self.db.document(self.current_doc_path)
            doc = current_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get("config_data")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current config: {e}")
            return None
    
    async def get_config_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get specific configuration version"""
        try:
            version_ref = self.db.collection(self.config_collection).document(version)
            doc = version_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get config version {version}: {e}")
            return None
    
    async def list_config_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List configuration versions"""
        try:
            versions_ref = self.db.collection(self.config_collection)\
                                 .order_by("created_at", direction=firestore.Query.DESCENDING)\
                                 .limit(limit)
            
            docs = versions_ref.stream()
            versions = []
            
            for doc in docs:
                version_data = doc.to_dict()
                # Convert Firestore timestamp for JSON serialization
                if 'created_at' in version_data and version_data['created_at']:
                    version_data['created_at'] = version_data['created_at'].isoformat()
                versions.append(version_data)
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to list config versions: {e}")
            return []
    
    async def rollback_to_version(self, target_version: str, user_id: str = "system") -> bool:
        """
        Rollback to a specific version
        Creates a new version with rollback note
        """
        try:
            # Get target version
            target_config = await self.get_config_version(target_version)
            if not target_config:
                logger.error(f"Target version {target_version} not found")
                return False
            
            # Save as new version
            changelog = f"Rollback to version {target_version}"
            new_version = await self.save_config(
                target_config['config_data'],
                changelog,
                user_id
            )
            
            logger.info(f"Rolled back to version {target_version} (new version: {new_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback to version {target_version}: {e}")
            return False
    
    async def create_backup(self, backup_name: str = None) -> str:
        """
        Create explicit backup of current configuration
        Returns backup ID
        """
        try:
            current_config = await self.get_current_config()
            if not current_config:
                raise ValueError("No current configuration to backup")
            
            backup_name = backup_name or f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            backup_id = await self.save_config(
                current_config,
                f"Manual backup: {backup_name}",
                "system"
            )
            
            logger.info(f"Created backup {backup_id} with name {backup_name}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    async def get_instance_metadata(self) -> Dict[str, Any]:
        """Get instance metadata including config info"""
        try:
            current_ref = self.db.document(self.current_doc_path)
            doc = current_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Convert timestamps
                if 'last_updated' in data and data['last_updated']:
                    data['last_updated'] = data['last_updated'].isoformat()
                
                return {
                    "instance_id": self.instance_id,
                    "project_id": self.project_id,
                    "current_version": data.get("current_version"),
                    "last_updated": data.get("last_updated"),
                    "updated_by": data.get("updated_by"),
                    "config_hash": data.get("config_hash")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get instance metadata: {e}")
            return {}


# Global instance for singleton pattern
_config_manager: Optional[PersistentConfigManager] = None


def get_persistent_config_manager() -> PersistentConfigManager:
    """Get or create persistent config manager singleton"""
    global _config_manager
    
    if _config_manager is None:
        from .config import get_settings
        settings = get_settings()
        
        # Extract instance ID from environment or generate
        instance_id = settings.management_api_secret.split('-')[-1][:8] if settings.management_api_secret else "default"
        
        _config_manager = PersistentConfigManager(
            project_id=settings.google_cloud_project,
            instance_id=instance_id
        )
    
    return _config_manager
