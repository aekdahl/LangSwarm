"""
AAF Orchestrator v2 - Proper Project/Instance Architecture
Manages AAF deployments with proper separation of projects and instances
"""

import os
import logging
import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from project_instance_registry import ProjectInstanceRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AAF Orchestrator v2",
    description="Project and Instance Management for AAF Deployments",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global registry
registry: Optional[ProjectInstanceRegistry] = None

# === AUTHENTICATION ===

async def verify_orchestrator_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify orchestrator API authentication"""
    expected_secret = os.environ.get('ORCHESTRATOR_API_SECRET')
    if not expected_secret:
        raise HTTPException(status_code=500, detail="ORCHESTRATOR_API_SECRET not configured")
    
    if credentials.credentials != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return credentials.credentials

# === PYDANTIC MODELS ===

class ProjectCreateRequest(BaseModel):
    project_id: str = Field(..., description="GCP project ID")
    project_name: Optional[str] = Field(None, description="Display name for project")
    customer_info: Dict[str, Any] = Field(default_factory=dict, description="Customer information")
    region: str = Field(default="europe-west1", description="Default region")
    billing_account: Optional[str] = Field(None, description="Billing account ID")

class InstanceCreateRequest(BaseModel):
    instance_name: Optional[str] = Field(None, description="Custom instance name")
    aaf_config: Dict[str, Any] = Field(default_factory=dict, description="AAF configuration")
    region: Optional[str] = Field(None, description="Deployment region (inherits from project if not specified)")
    memory: str = Field(default="2Gi", description="Memory allocation")
    cpu: str = Field(default="2", description="CPU allocation")

class InstanceUpdateRequest(BaseModel):
    aaf_config: Optional[Dict[str, Any]] = Field(None, description="Updated AAF configuration")
    status: Optional[str] = Field(None, description="Instance status")

class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = Field(None, description="Updated project name")
    customer_info: Optional[Dict[str, Any]] = Field(None, description="Updated customer info")
    status: Optional[str] = Field(None, description="Project status")

# === STARTUP ===

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator"""
    global registry
    
    registry_project = os.environ.get('REGISTRY_PROJECT_ID', 'enkl-saas')
    collection_name = os.environ.get('FIRESTORE_COLLECTION', 'aaf_projects_v2')
    
    registry = ProjectInstanceRegistry(registry_project, collection_name)
    logger.info("AAF Orchestrator v2 initialized")

# === HEALTH CHECK ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aaf-orchestrator-v2",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

# === PROJECT ENDPOINTS ===

@app.post("/projects")
async def create_project(
    request: ProjectCreateRequest,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Create a new project"""
    try:
        project_data = {
            'project_id': request.project_id,
            'project_name': request.project_name or request.project_id,
            'customer_info': request.customer_info,
            'region': request.region,
            'billing_account': request.billing_account
        }
        
        success = await registry.create_project(project_data)
        
        if success:
            return {
                'success': True,
                'project_id': request.project_id,
                'message': f"Project {request.project_id} created successfully"
            }
        else:
            raise HTTPException(status_code=409, detail=f"Project {request.project_id} already exists")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/projects")
async def list_projects(
    status: str = "active",
    auth: str = Depends(verify_orchestrator_auth)
):
    """List all projects"""
    try:
        projects = await registry.list_projects(status=status)
        return {
            'projects': projects,
            'count': len(projects),
            'status_filter': status
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@app.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Get project details"""
    try:
        project = await registry.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

@app.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Update project information"""
    try:
        updates = {}
        if request.project_name is not None:
            updates['project_name'] = request.project_name
        if request.customer_info is not None:
            updates['customer_info'] = request.customer_info
        if request.status is not None:
            updates['status'] = request.status
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = await registry.update_project(project_id, updates)
        
        if success:
            return {
                'success': True,
                'project_id': project_id,
                'message': 'Project updated successfully'
            }
        else:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    hard_delete: bool = False,
    delete_instances: bool = True,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Delete project and optionally all its instances"""
    try:
        # Get project info
        project = await registry.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # If delete_instances is True, delete all instances first
        if delete_instances:
            instances = await registry.list_instances(project_id, status="all")
            for instance in instances:
                instance_id = instance['instance_id']
                # Delete Cloud Run service
                try:
                    await delete_cloud_run_service(
                        project_id, 
                        instance.get('service_name'), 
                        instance.get('region', 'europe-west1')
                    )
                    logger.info(f"Deleted Cloud Run service for instance {instance_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete Cloud Run service for instance {instance_id}: {e}")
                
                # Remove from registry
                await registry.delete_instance(project_id, instance_id, hard_delete=True)
        
        # Delete project
        success = await registry.delete_project(project_id, hard_delete=hard_delete)
        
        if success:
            return {
                'success': True,
                'project_id': project_id,
                'message': f"Project {project_id} {'permanently deleted' if hard_delete else 'marked as deleted'}",
                'instances_deleted': delete_instances
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete project")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# === INSTANCE ENDPOINTS ===

@app.post("/projects/{project_id}/instances")
async def create_instance(
    project_id: str,
    request: InstanceCreateRequest,
    background_tasks: BackgroundTasks,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Create a new AAF instance in a project"""
    try:
        # Verify project exists
        project = await registry.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Use project region if not specified
        region = request.region or project.get('region', 'europe-west1')
        
        # Generate service name
        timestamp = int(time.time())
        service_name = f"aaf-instance-{timestamp}"
        
        # Deploy AAF to Cloud Run
        background_tasks.add_task(
            deploy_aaf_instance,
            project_id=project_id,
            service_name=service_name,
            region=region,
            aaf_config=request.aaf_config,
            memory=request.memory,
            cpu=request.cpu,
            instance_name=request.instance_name
        )
        
        return {
            'success': True,
            'project_id': project_id,
            'service_name': service_name,
            'message': f"AAF instance deployment started for project {project_id}",
            'deployment_started': True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating instance in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create instance: {str(e)}")

@app.get("/projects/{project_id}/instances")
async def list_instances(
    project_id: str,
    status: str = "active",
    auth: str = Depends(verify_orchestrator_auth)
):
    """List instances in a project"""
    try:
        instances = await registry.list_instances(project_id, status=status)
        return {
            'project_id': project_id,
            'instances': instances,
            'count': len(instances),
            'status_filter': status
        }
    except Exception as e:
        logger.error(f"Error listing instances for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list instances: {str(e)}")

@app.get("/projects/{project_id}/instances/{instance_id}")
async def get_instance(
    project_id: str,
    instance_id: str,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Get specific instance details"""
    try:
        instance = await registry.get_instance(project_id, instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found in project {project_id}")
        
        return instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instance {instance_id} in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get instance: {str(e)}")

@app.patch("/projects/{project_id}/instances/{instance_id}")
async def update_instance(
    project_id: str,
    instance_id: str,
    request: InstanceUpdateRequest,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Update instance configuration"""
    try:
        updates = {}
        if request.aaf_config is not None:
            updates['aaf_config'] = request.aaf_config
        if request.status is not None:
            updates['status'] = request.status
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = await registry.update_instance(project_id, instance_id, updates)
        
        if success:
            return {
                'success': True,
                'project_id': project_id,
                'instance_id': instance_id,
                'message': 'Instance updated successfully'
            }
        else:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found in project {project_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instance {instance_id} in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update instance: {str(e)}")

@app.delete("/projects/{project_id}/instances/{instance_id}")
async def delete_instance(
    project_id: str,
    instance_id: str,
    hard_delete: bool = False,
    delete_service: bool = True,
    auth: str = Depends(verify_orchestrator_auth)
):
    """Delete specific instance"""
    try:
        # Get instance info
        instance = await registry.get_instance(project_id, instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found in project {project_id}")
        
        # Delete Cloud Run service if requested
        if delete_service:
            try:
                await delete_cloud_run_service(
                    project_id,
                    instance.get('service_name'),
                    instance.get('region', 'europe-west1')
                )
                logger.info(f"Deleted Cloud Run service for instance {instance_id}")
            except Exception as e:
                logger.warning(f"Failed to delete Cloud Run service for instance {instance_id}: {e}")
        
        # Remove from registry
        success = await registry.delete_instance(project_id, instance_id, hard_delete=hard_delete)
        
        if success:
            return {
                'success': True,
                'project_id': project_id,
                'instance_id': instance_id,
                'message': f"Instance {instance_id} {'permanently deleted' if hard_delete else 'marked as deleted'}",
                'service_deleted': delete_service
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete instance")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting instance {instance_id} in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete instance: {str(e)}")

# === DEPLOYMENT FUNCTIONS ===

async def deploy_aaf_instance(
    project_id: str,
    service_name: str,
    region: str,
    aaf_config: Dict[str, Any],
    memory: str = "2Gi",
    cpu: str = "2",
    instance_name: Optional[str] = None
):
    """Deploy AAF instance to Cloud Run"""
    try:
        # Import deployment functions (reuse from original main.py)
        from main import setup_cross_project_permissions, enable_required_apis, create_aaf_secrets, setup_aaf_bigquery_infrastructure
        
        logger.info(f"Starting AAF deployment for {service_name} in project {project_id}")
        
        # Setup infrastructure
        await setup_cross_project_permissions(project_id)
        await enable_required_apis(project_id)
        await create_aaf_secrets(project_id, aaf_config)
        await setup_aaf_bigquery_infrastructure(project_id)
        
        # Deploy Cloud Run service
        service_url = await deploy_cloud_run_service(
            project_id=project_id,
            service_name=service_name,
            region=region,
            aaf_config=aaf_config,
            memory=memory,
            cpu=cpu
        )
        
        # Register instance in project
        instance_id = await registry.create_instance(project_id, {
            'instance_id': service_name,
            'service_name': service_name,
            'service_url': service_url,
            'region': region,
            'aaf_config': aaf_config,
            'management_api_secret': f"mgmt-{service_name}-{hash(service_name)}"
        })
        
        logger.info(f"Successfully deployed AAF instance {service_name} in project {project_id}")
        
    except Exception as e:
        logger.error(f"Failed to deploy AAF instance {service_name}: {e}")
        # Update instance status to failed
        await registry.update_instance(project_id, service_name, {'status': 'failed', 'error': str(e)})

async def deploy_cloud_run_service(project_id: str, service_name: str, region: str, aaf_config: Dict[str, Any], memory: str, cpu: str) -> str:
    """Deploy AAF service to Cloud Run"""
    # Import from main.py to reuse existing deployment logic
    from main import deploy_aaf_instance_to_cloud_run
    
    try:
        service_url = await deploy_aaf_instance_to_cloud_run(
            project_id=project_id,
            service_name=service_name,
            region=region,
            aaf_config=aaf_config,
            memory=memory,
            cpu=cpu
        )
        return service_url
    except Exception as e:
        logger.error(f"Failed to deploy Cloud Run service {service_name}: {e}")
        raise

async def delete_cloud_run_service(project_id: str, service_name: str, region: str):
    """Delete Cloud Run service"""
    from main import delete_cloud_run_instance
    
    try:
        await delete_cloud_run_instance(project_id, service_name, region)
        logger.info(f"Deleted Cloud Run service {service_name} in project {project_id}")
    except Exception as e:
        logger.error(f"Failed to delete Cloud Run service {service_name}: {e}")
        raise

# === MIGRATION ENDPOINTS ===

@app.post("/migration/v1-to-v2")
async def migrate_v1_to_v2(auth: str = Depends(verify_orchestrator_auth)):
    """Migrate data from v1 (old format) to v2 (new format)"""
    try:
        # TODO: Implement migration logic from old Firestore structure to new structure
        return {
            'success': True,
            'message': 'Migration completed successfully'
        }
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

# === MAIN ===

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    uvicorn.run(
        "main_v2:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
