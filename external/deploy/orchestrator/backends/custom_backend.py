"""
Custom Backend Manager for adoption-only backends
"""
import json
import subprocess
import logging
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime

from .base_backend import BackendManager, BackendCapabilities

logger = logging.getLogger(__name__)


class CustomBackendManager(BackendManager):
    """Manager for custom backends that can only be adopted"""
    
    def __init__(self, project_id: str, region: str = "europe-west1"):
        super().__init__(project_id, region)
        self.backend_type = "custom"
        self.capabilities = BackendCapabilities(
            create=False,           # Cannot create new instances
            adopt=True,             # Can adopt existing instances
            delete=False,           # Cannot delete from Cloud Run
            update_prompts=True,    # Can update prompts
            remove_from_admin=True  # Can remove from admin tracking
        )
        
        # In-memory storage for adopted instances
        # In production, this should be a database
        self.adopted_instances = {}
    
    async def deploy_instance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Custom backends cannot be deployed"""
        raise NotImplementedError(
            "Custom backends can only be adopted, not created. "
            "Use adopt_instance() instead."
        )
    
    async def adopt_instance(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Adopt an existing Cloud Run service"""
        logger.info(f"Attempting to adopt custom backend: {service_name}")
        
        # Get service URL
        service_url = await self.get_service_url(service_name)
        if not service_url:
            raise ValueError(f"Service {service_name} not found in project {self.project_id}")
        
        # Validate service health and compatibility
        health_check = await self.validate_service_health(service_url)
        if not health_check["valid"]:
            raise ValueError(f"Service validation failed: {health_check['error']}")
        
        health_data = health_check["health_data"]
        
        # Verify it's a custom backend
        if health_data.get("backend_type") != "custom":
            raise ValueError(
                f"Service is not a custom backend (found: {health_data.get('backend_type')})"
            )
        
        # Check prompt management capability
        prompt_mgmt = health_data.get("prompt_management", {})
        if not prompt_mgmt.get("enabled"):
            raise ValueError("Service does not support prompt management")
        
        # Create instance record
        instance_record = self.create_instance_record(service_name, {
            "adopted_at": datetime.utcnow().isoformat(),
            "service_url": service_url,
            "version": health_data.get("version", "unknown"),
            "prompt_method": prompt_mgmt.get("method", "api"),
            "capabilities": self.capabilities.to_dict(),
            "health_data": health_data
        })
        
        # Store in memory (replace with database in production)
        self.adopted_instances[service_name] = instance_record
        
        logger.info(f"Successfully adopted custom backend: {service_name}")
        return instance_record
    
    async def update_prompts(self, instance_id: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Update instance prompts via API"""
        instance = self.adopted_instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found or not adopted")
        
        service_url = instance["service_url"]
        prompt_method = instance["prompt_method"]
        
        if prompt_method == "api":
            return await self._update_prompts_via_api(service_url, prompts)
        elif prompt_method == "env_vars":
            return await self._update_prompts_via_env_vars(instance_id, prompts)
        else:
            raise ValueError(f"Unsupported prompt update method: {prompt_method}")
    
    async def _update_prompts_via_api(self, service_url: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Update prompts via the service's API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{service_url}/api/prompts",
                    json=prompts,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API update failed: HTTP {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    return {
                        "success": True,
                        "method": "api",
                        "updated_prompts": result.get("updated_prompts", list(prompts.keys())),
                        "restart_required": result.get("restart_required", False),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Failed to update prompts via API: {e}")
            return {
                "success": False,
                "method": "api",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _update_prompts_via_env_vars(self, service_name: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Update prompts via Cloud Run environment variables"""
        try:
            # Convert prompts to environment variable format
            env_vars = []
            for key, value in prompts.items():
                env_var_name = f"CUSTOM_PROMPT_{key.upper()}"
                env_vars.append(f"{env_var_name}={value}")
            
            # Update Cloud Run service
            env_var_string = ",".join(env_vars)
            
            result = subprocess.run([
                "gcloud", "run", "services", "update", service_name,
                "--project", self.project_id,
                "--region", self.region,
                "--update-env-vars", env_var_string
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"gcloud update failed: {result.stderr}")
            
            return {
                "success": True,
                "method": "env_vars",
                "updated_prompts": list(prompts.keys()),
                "restart_required": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update prompts via env vars: {e}")
            return {
                "success": False,
                "method": "env_vars", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_prompts(self, instance_id: str) -> Dict[str, Any]:
        """Get current prompt values"""
        instance = self.adopted_instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found or not adopted")
        
        service_url = instance["service_url"]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/api/prompts", timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get prompts: HTTP {response.status}")
                    
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Failed to get prompts for {instance_id}: {e}")
            raise
    
    async def get_prompt_schema(self, instance_id: str) -> Dict[str, Any]:
        """Get prompt configuration schema"""
        instance = self.adopted_instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found or not adopted")
        
        service_url = instance["service_url"]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/api/prompts/schema", timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get prompt schema: HTTP {response.status}")
                    
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Failed to get prompt schema for {instance_id}: {e}")
            raise
    
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all adopted instances"""
        return list(self.adopted_instances.values())
    
    async def delete_instance(self, instance_id: str) -> bool:
        """Custom backends cannot be deleted from Cloud Run"""
        raise NotImplementedError(
            "Custom backends cannot be deleted from Cloud Run. "
            "Use remove_from_admin() to remove from orchestrator tracking."
        )
    
    async def remove_from_admin(self, instance_id: str) -> bool:
        """Remove instance from admin tracking without deleting the service"""
        if instance_id in self.adopted_instances:
            del self.adopted_instances[instance_id]
            logger.info(f"Removed {instance_id} from admin tracking")
            return True
        return False
    
    async def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed instance information"""
        instance = self.adopted_instances.get(instance_id)
        if not instance:
            return None
        
        # Enhance with current health status
        try:
            health_check = await self.validate_service_health(instance["service_url"])
            instance = instance.copy()
            instance["current_health"] = health_check
        except Exception as e:
            logger.warning(f"Failed to get current health for {instance_id}: {e}")
        
        return instance
    
    async def list_orphaned_services(self) -> List[Dict[str, Any]]:
        """Find custom backend services that aren't being managed"""
        try:
            # Get all Cloud Run services in the project
            result = subprocess.run([
                "gcloud", "run", "services", "list",
                "--project", self.project_id,
                "--region", self.region,
                "--format", "json"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list services: {result.stderr}")
                return []
            
            all_services = json.loads(result.stdout)
            orphaned = []
            
            for service in all_services:
                service_name = service["metadata"]["name"]
                service_url = service.get("status", {}).get("url")
                
                # Skip if already adopted
                if service_name in self.adopted_instances:
                    continue
                
                # Check if it's a custom backend
                if service_url:
                    health_check = await self.validate_service_health(service_url)
                    if (health_check["valid"] and 
                        health_check["health_data"].get("backend_type") == "custom"):
                        
                        orphaned.append({
                            "name": service_name,
                            "url": service_url,
                            "status": service.get("status", {}).get("conditions", [{}])[0].get("status", "unknown"),
                            "created": service.get("metadata", {}).get("creationTimestamp"),
                            "health_data": health_check["health_data"]
                        })
            
            return orphaned
            
        except Exception as e:
            logger.error(f"Failed to list orphaned services: {e}")
            return []
    
    async def validate_custom_backend_compatibility(self, service_name: str) -> Dict[str, Any]:
        """Comprehensive validation for custom backend adoption"""
        service_url = await self.get_service_url(service_name)
        if not service_url:
            return {
                "compatible": False,
                "error": f"Service {service_name} not found"
            }
        
        # Check health endpoint
        health_check = await self.validate_service_health(service_url)
        if not health_check["valid"]:
            return {
                "compatible": False,
                "error": f"Health check failed: {health_check['error']}"
            }
        
        health_data = health_check["health_data"]
        
        # Validate required endpoints
        endpoints_to_check = ["/api/prompts", "/api/prompts/schema"]
        endpoint_results = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints_to_check:
                    try:
                        async with session.get(f"{service_url}{endpoint}", timeout=5) as response:
                            endpoint_results[endpoint] = {
                                "available": response.status == 200,
                                "status": response.status
                            }
                    except Exception as e:
                        endpoint_results[endpoint] = {
                            "available": False,
                            "error": str(e)
                        }
        except Exception as e:
            return {
                "compatible": False,
                "error": f"Failed to check endpoints: {e}"
            }
        
        # Check if all required endpoints are available
        missing_endpoints = [
            endpoint for endpoint, result in endpoint_results.items()
            if not result["available"]
        ]
        
        return {
            "compatible": len(missing_endpoints) == 0,
            "service_name": service_name,
            "service_url": service_url,
            "health_data": health_data,
            "endpoint_results": endpoint_results,
            "missing_endpoints": missing_endpoints,
            "error": f"Missing required endpoints: {missing_endpoints}" if missing_endpoints else None
        }
