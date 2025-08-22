"""
Unified Orchestrator v3 - Multi-Backend Support
Supports both AAF (LangSwarm) and Custom backends
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from backends.aaf_backend import AAFBackendManager
from backends.custom_backend import CustomBackendManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Unified Backend Orchestrator",
    description="Multi-backend orchestrator for AAF and Custom backends",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UnifiedOrchestrator:
    """Unified orchestrator managing multiple backend types"""
    
    def __init__(self):
        self.backend_managers = {
            "aaf": AAFBackendManager,
            "custom": CustomBackendManager
        }
        self.active_managers = {}  # project_id -> {backend_type -> manager}
    
    def get_backend_manager(self, backend_type: str, project_id: str, region: str = "europe-west1"):
        """Get or create a backend manager for the specified type and project"""
        if backend_type not in self.backend_managers:
            raise ValueError(f"Unsupported backend type: {backend_type}")
        
        # Create manager key
        manager_key = f"{project_id}:{region}"
        
        if manager_key not in self.active_managers:
            self.active_managers[manager_key] = {}
        
        if backend_type not in self.active_managers[manager_key]:
            manager_class = self.backend_managers[backend_type]
            self.active_managers[manager_key][backend_type] = manager_class(project_id, region)
        
        return self.active_managers[manager_key][backend_type]
    
    def get_supported_backends(self) -> Dict[str, Dict[str, Any]]:
        """Get information about supported backend types"""
        backends = {}
        
        for backend_type, manager_class in self.backend_managers.items():
            # Create a temporary instance to get capabilities
            temp_manager = manager_class("temp", "temp")
            backends[backend_type] = {
                "name": backend_type.upper(),
                "capabilities": temp_manager.capabilities.to_dict(),
                "description": temp_manager.__class__.__doc__ or f"{backend_type} backend manager"
            }
        
        return backends


# Global orchestrator instance
orchestrator = UnifiedOrchestrator()


# Pydantic models
class CreateInstanceRequest(BaseModel):
    backend_type: str
    project_id: str
    region: str = "europe-west1"
    configuration: Dict[str, Any]


class AdoptInstanceRequest(BaseModel):
    backend_type: str
    project_id: str
    region: str = "europe-west1"
    service_name: str
    additional_config: Optional[Dict[str, Any]] = None


class UpdatePromptsRequest(BaseModel):
    prompts: Dict[str, str]
    update_reason: Optional[str] = "Prompt update via orchestrator"


class ValidationRequest(BaseModel):
    backend_type: str
    project_id: str
    region: str = "europe-west1"
    service_name: str


# API Routes

@app.get("/")
async def root():
    """Root endpoint with orchestrator information"""
    return {
        "service": "Unified Backend Orchestrator",
        "version": "3.0.0",
        "supported_backends": orchestrator.get_supported_backends(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/backends")
async def list_supported_backends():
    """List all supported backend types and their capabilities"""
    return orchestrator.get_supported_backends()


@app.get("/api/backend-templates")
async def get_backend_templates():
    """Get backend templates for frontend (compatibility endpoint)"""
    from config.backend_templates import get_backend_template
    
    templates = {}
    for backend_type in ["aaf", "custom"]:
        templates[backend_type] = get_backend_template(backend_type)
    
    return templates


@app.post("/api/v1/{backend_type}/instances")
async def create_instance(backend_type: str, request: CreateInstanceRequest):
    """Create a new instance (if supported by backend type)"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, request.project_id, request.region)
        
        # Check if backend supports creation
        if not manager.capabilities.create:
            raise HTTPException(
                status_code=405,
                detail=f"{backend_type} backends can only be adopted, not created"
            )
        
        result = await manager.deploy_instance(request.configuration)
        return result
        
    except NotImplementedError as e:
        raise HTTPException(status_code=405, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create {backend_type} instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/{backend_type}/instances/adopt")
async def adopt_instance(backend_type: str, request: AdoptInstanceRequest):
    """Adopt an existing instance"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, request.project_id, request.region)
        
        # Check if backend supports adoption
        if not manager.capabilities.adopt:
            raise HTTPException(
                status_code=405,
                detail=f"{backend_type} backends do not support adoption"
            )
        
        result = await manager.adopt_instance(
            request.service_name,
            **(request.additional_config or {})
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to adopt {backend_type} instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/{backend_type}/instances")
async def list_instances(backend_type: str, project_id: str, region: str = "europe-west1"):
    """List all instances of a specific backend type"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        instances = await manager.list_instances()
        return instances
        
    except Exception as e:
        logger.error(f"Failed to list {backend_type} instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/{backend_type}/instances/{instance_id}")
async def get_instance_info(backend_type: str, instance_id: str, project_id: str, region: str = "europe-west1"):
    """Get detailed information about a specific instance"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        instance = await manager.get_instance_info(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        return instance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get {backend_type} instance info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/{backend_type}/instances/{instance_id}")
async def delete_instance(backend_type: str, instance_id: str, project_id: str, region: str = "europe-west1"):
    """Delete an instance (if supported by backend type)"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        
        # Check if backend supports deletion
        if not manager.capabilities.delete:
            raise HTTPException(
                status_code=405,
                detail=f"{backend_type} backends cannot be deleted. Use remove_from_admin instead."
            )
        
        success = await manager.delete_instance(instance_id)
        return {"deleted": success, "instance_id": instance_id}
        
    except NotImplementedError as e:
        raise HTTPException(status_code=405, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete {backend_type} instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/{backend_type}/instances/{instance_id}/admin")
async def remove_from_admin(backend_type: str, instance_id: str, project_id: str, region: str = "europe-west1"):
    """Remove instance from admin tracking (for adoption-only backends)"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        
        # Check if backend supports admin removal
        if not manager.capabilities.remove_from_admin:
            raise HTTPException(
                status_code=405,
                detail=f"{backend_type} backends should be deleted completely, not removed from admin"
            )
        
        success = await manager.remove_from_admin(instance_id)
        return {"removed_from_admin": success, "instance_id": instance_id}
        
    except Exception as e:
        logger.error(f"Failed to remove {backend_type} instance from admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Prompt Management Endpoints

@app.get("/api/v1/{backend_type}/instances/{instance_id}/prompts/schema")
async def get_prompt_schema(backend_type: str, instance_id: str, project_id: str, region: str = "europe-west1"):
    """Get the prompt configuration schema for an instance"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        schema = await manager.get_prompt_schema(instance_id)
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get prompt schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/{backend_type}/instances/{instance_id}/prompts")
async def get_prompts(backend_type: str, instance_id: str, project_id: str, region: str = "europe-west1"):
    """Get current prompt values for an instance"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        prompts = await manager.get_prompts(instance_id)
        return prompts
        
    except Exception as e:
        logger.error(f"Failed to get prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/{backend_type}/instances/{instance_id}/prompts")
async def update_prompts(
    backend_type: str, 
    instance_id: str, 
    request: UpdatePromptsRequest, 
    project_id: str, 
    region: str = "europe-west1"
):
    """Update prompt values for an instance"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        
        # Check if backend supports prompt updates
        if not manager.capabilities.update_prompts:
            raise HTTPException(
                status_code=405,
                detail=f"{backend_type} backends do not support prompt updates"
            )
        
        result = await manager.update_prompts(instance_id, request.prompts)
        return result
        
    except Exception as e:
        logger.error(f"Failed to update prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Discovery and Validation Endpoints

@app.get("/api/v1/{backend_type}/orphaned-services")
async def list_orphaned_services(backend_type: str, project_id: str, region: str = "europe-west1"):
    """List services that can be adopted (for adoption-capable backends)"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, project_id, region)
        
        # Check if this is a custom backend (which supports orphan discovery)
        if hasattr(manager, 'list_orphaned_services'):
            orphaned = await manager.list_orphaned_services()
            return orphaned
        else:
            return []
        
    except Exception as e:
        logger.error(f"Failed to list orphaned services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/{backend_type}/validate-service")
async def validate_service_compatibility(backend_type: str, request: ValidationRequest):
    """Validate if a service is compatible for adoption"""
    try:
        manager = orchestrator.get_backend_manager(backend_type, request.project_id, request.region)
        
        # Check if this is a custom backend (which supports validation)
        if hasattr(manager, 'validate_custom_backend_compatibility'):
            validation = await manager.validate_custom_backend_compatibility(request.service_name)
            return validation
        else:
            # For AAF backends, do basic health check
            service_url = await manager.get_service_url(request.service_name)
            if service_url:
                health_check = await manager.validate_service_health(service_url)
                return {
                    "compatible": health_check["valid"],
                    "service_name": request.service_name,
                    "service_url": service_url,
                    "health_data": health_check.get("health_data"),
                    "error": health_check.get("error")
                }
            else:
                return {
                    "compatible": False,
                    "error": f"Service {request.service_name} not found"
                }
        
    except Exception as e:
        logger.error(f"Failed to validate service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Status Endpoints

@app.get("/health")
async def health_check():
    """Orchestrator health check"""
    return {
        "status": "healthy",
        "service": "unified-orchestrator",
        "version": "3.0.0",
        "supported_backends": list(orchestrator.backend_managers.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }


# === HELPER FUNCTIONS ===

async def discover_aaf_instances_in_project(project_id: str) -> List[Dict[str, Any]]:
    """Discover AAF instances by scanning Cloud Run services in a project"""
    try:
        from google.cloud import run_v2
        import aiohttp
        
        # Initialize the Cloud Run client
        client = run_v2.ServicesClient()
        
        # List all Cloud Run services in the project
        parent = f"projects/{project_id}/locations/-"  # Search all regions
        
        aaf_instances = []
        
        try:
            services = client.list_services(parent=parent)
            
            for service in services:
                service_name = service.name.split("/")[-1]  # Extract just the name
                
                # Check if this looks like an AAF instance
                if (service_name.startswith("aaf-instance-") or 
                    service_name.endswith("-backend") or
                    ("aaf" in service_name.lower() and not "orchestrator" in service_name.lower())):
                    
                    # Extract service URL and region
                    service_url = service.uri if hasattr(service, 'uri') else ""
                    region = service.name.split("/")[3] if len(service.name.split("/")) > 3 else "europe-west1"
                    
                    # Create instance info with what we know
                    instance_info = {
                        "id": service_name,
                        "name": service_name,
                        "status": "unknown",
                        "region": region,
                        "url": service_url,
                        "created_at": None,
                        "gcp_project": project_id
                    }
                    
                    # Try to verify it's actually an AAF instance by checking health
                    if service_url:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(f"{service_url}/health", timeout=10) as resp:
                                    if resp.status == 200:
                                        health_data = await resp.json()
                                        # If it has AAF-like health response, update status
                                        if isinstance(health_data, dict):
                                            instance_info["status"] = "running"
                        except Exception as health_error:
                            logger.debug(f"Health check failed for {service_name}: {health_error}")
                            # Still include it but leave status as unknown
                    
                    aaf_instances.append(instance_info)
                    
        except Exception as api_error:
            logger.warning(f"Could not list Cloud Run services in {project_id}: {api_error}")
        
        return aaf_instances
        
    except Exception as e:
        logger.error(f"Error discovering AAF instances in project {project_id}: {e}")
        return []


# === BACKWARD COMPATIBILITY ENDPOINTS ===
# These endpoints provide compatibility with v2 frontend expectations

@app.get("/projects")
async def list_projects_compat():
    """Backward compatibility: List officially managed projects from Firestore registry"""
    try:
        from google.cloud import firestore
        
        # Connect to Firestore registry
        db = firestore.Client(project="enkl-saas")
        
        all_projects = []
        
        # Read from aaf_projects_v2 collection (newer format)
        try:
            projects_collection = db.collection("aaf_projects_v2")
            
            for doc in projects_collection.stream():
                project_data = doc.to_dict()
                
                # Skip if project is not active
                if project_data.get("status") != "active":
                    continue
                
                project_id = project_data.get("project_id")
                if not project_id:
                    continue
                
                # Get current instances for this project by discovering Cloud Run services
                current_instances = await discover_aaf_instances_in_project(project_id)
                
                # Build project response with Firestore data + current instance status
                customer_info = project_data.get("customer_info", {})
                
                all_projects.append({
                    "project_id": project_id,
                    "project_name": project_data.get("project_name", project_id),
                    "status": project_data.get("status", "active"),
                    "region": project_data.get("region", "europe-west1"),
                    "created_at": project_data.get("created_at"),
                    "last_updated": project_data.get("last_updated", datetime.utcnow().isoformat()),
                    "gcp_project": project_id,
                    
                    # Use customer info from Firestore
                    "customer_info": {
                        "name": customer_info.get("name", "Unknown Customer"),
                        "email": customer_info.get("email", f"admin@{project_id}.com"),
                        "company": customer_info.get("company", project_id)
                    },
                    "service_url": current_instances[0].get("url", "") if current_instances else "",
                    "health_status": "healthy" if any(i.get("status") == "running" for i in current_instances) else "unknown",
                    "last_health_check": datetime.utcnow().isoformat(),
                    
                    "instances": current_instances  # Current live instances
                })
                
        except Exception as firestore_error:
            logger.error(f"Error reading from Firestore: {firestore_error}")
            # Fallback to empty list rather than discovery
            
        return {"projects": all_projects}
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return {"projects": []}


@app.get("/projects/{project_id}")
async def get_project_compat(project_id: str):
    """Backward compatibility: Get specific project details from Firestore registry"""
    try:
        from google.cloud import firestore
        
        # Connect to Firestore registry
        db = firestore.Client(project="enkl-saas")
        
        # Look for the project in Firestore
        projects_collection = db.collection("aaf_projects_v2")
        
        for doc in projects_collection.stream():
            project_data = doc.to_dict()
            
            # Check if this is the project we're looking for
            if project_data.get("project_id") == project_id and project_data.get("status") == "active":
                
                # Get current instances for this project
                current_instances = await discover_aaf_instances_in_project(project_id)
                
                # Build project response with Firestore data + current instance status
                customer_info = project_data.get("customer_info", {})
                
                return {
                    "project_id": project_id,
                    "project_name": project_data.get("project_name", project_id),
                    "status": project_data.get("status", "active"),
                    "region": project_data.get("region", "europe-west1"),
                    "created_at": project_data.get("created_at"),
                    "last_updated": project_data.get("last_updated", datetime.utcnow().isoformat()),
                    "gcp_project": project_id,
                    
                    # Use customer info from Firestore
                    "customer_info": {
                        "name": customer_info.get("name", "Unknown Customer"),
                        "email": customer_info.get("email", f"admin@{project_id}.com"),
                        "company": customer_info.get("company", project_id)
                    },
                    "service_url": current_instances[0].get("url", "") if current_instances else "",
                    "health_status": "healthy" if any(i.get("status") == "running" for i in current_instances) else "unknown",
                    "last_health_check": datetime.utcnow().isoformat(),
                    
                    "instances": current_instances
                }
        
        # If not found in Firestore
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found in registry")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
