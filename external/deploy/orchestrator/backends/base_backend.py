"""
Base backend abstraction for the unified orchestrator
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import logging

logger = logging.getLogger(__name__)


class BackendManager(ABC):
    """Abstract base class for backend managers"""
    
    def __init__(self, project_id: str, region: str = "europe-west1"):
        self.project_id = project_id
        self.region = region
        self.backend_type = getattr(self, 'backend_type', 'unknown')
    
    @abstractmethod
    async def deploy_instance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a new instance (if supported by backend type)"""
        pass
    
    @abstractmethod
    async def adopt_instance(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Adopt an existing Cloud Run service"""
        pass
    
    @abstractmethod
    async def update_prompts(self, instance_id: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Update instance prompts"""
        pass
    
    @abstractmethod
    async def get_prompts(self, instance_id: str) -> Dict[str, Any]:
        """Get current prompt values"""
        pass
    
    @abstractmethod
    async def get_prompt_schema(self, instance_id: str) -> Dict[str, Any]:
        """Get prompt configuration schema"""
        pass
    
    @abstractmethod
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List managed instances"""
        pass
    
    @abstractmethod
    async def delete_instance(self, instance_id: str) -> bool:
        """Delete an instance (if supported by backend type)"""
        pass
    
    @abstractmethod
    async def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed instance information"""
        pass
    
    # Common utility methods
    async def validate_service_health(self, service_url: str) -> Dict[str, Any]:
        """Validate that a service is healthy and compatible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/health", timeout=10) as response:
                    if response.status != 200:
                        return {"valid": False, "error": f"Health check failed: HTTP {response.status}"}
                    
                    health_data = await response.json()
                    
                    # Check required fields
                    required_fields = ["status", "backend_type"]
                    missing_fields = [field for field in required_fields if field not in health_data]
                    
                    if missing_fields:
                        return {
                            "valid": False, 
                            "error": f"Missing required health fields: {missing_fields}"
                        }
                    
                    if health_data["status"] != "healthy":
                        return {
                            "valid": False,
                            "error": f"Service not healthy: {health_data['status']}"
                        }
                    
                    return {
                        "valid": True,
                        "health_data": health_data
                    }
                    
        except Exception as e:
            logger.error(f"Health check failed for {service_url}: {e}")
            return {"valid": False, "error": f"Health check failed: {str(e)}"}
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the URL for a Cloud Run service"""
        try:
            # Use gcloud to get service URL
            import subprocess
            import json
            
            result = subprocess.run([
                "gcloud", "run", "services", "describe", service_name,
                "--project", self.project_id,
                "--region", self.region,
                "--format", "json"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to get service URL: {result.stderr}")
                return None
            
            service_data = json.loads(result.stdout)
            return service_data.get("status", {}).get("url")
            
        except Exception as e:
            logger.error(f"Error getting service URL for {service_name}: {e}")
            return None
    
    def create_instance_record(self, service_name: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a standard instance record"""
        record = {
            "instance_id": service_name,
            "service_name": service_name,
            "backend_type": self.backend_type,
            "project_id": self.project_id,
            "region": self.region,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        if additional_data:
            record.update(additional_data)
        
        return record


class BackendCapabilities:
    """Define what operations a backend supports"""
    
    def __init__(
        self,
        create: bool = True,
        adopt: bool = True,
        delete: bool = True,
        update_prompts: bool = True,
        remove_from_admin: bool = False
    ):
        self.create = create
        self.adopt = adopt
        self.delete = delete
        self.update_prompts = update_prompts
        self.remove_from_admin = remove_from_admin
    
    def to_dict(self) -> Dict[str, bool]:
        return {
            "create": self.create,
            "adopt": self.adopt,
            "delete": self.delete,
            "update_prompts": self.update_prompts,
            "remove_from_admin": self.remove_from_admin
        }
