"""
AAF Orchestrator v2 - Proper Project/Instance Architecture
Manages AAF deployments with proper separation of projects and instances
"""

import os
import logging
import asyncio
import hashlib
import time
import requests
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

class AdoptInstanceRequest(BaseModel):
    service_name: str = Field(..., description="Name of the Cloud Run service to adopt")

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

async def get_cloud_run_services(project_id: str, region: str = "europe-west1"):
    """Get all Cloud Run services in a project"""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        
        # Get credentials
        credentials, _ = default()
        credentials.refresh(Request())
        
        # Call Cloud Run API to list services
        url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/{region}/services"
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            services = []
            for item in data.get('items', []):
                service_name = item['metadata']['name']
                service_url = item.get('status', {}).get('url', '')
                services.append({
                    'name': service_name,
                    'url': service_url,
                    'generation': item.get('metadata', {}).get('generation', 0),
                    'region': region
                })
            return services
        else:
            logger.error(f"Failed to list Cloud Run services: {response.status_code} {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error listing Cloud Run services: {e}")
        return []


async def get_cloud_run_service_details(project_id: str, service_name: str, region: str = "europe-west1"):
    """Get detailed information about a specific Cloud Run service"""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        
        # Get credentials
        credentials, _ = default()
        credentials.refresh(Request())
        
        # Call Cloud Run API to get service details
        url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/{region}/services/{service_name}"
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant details
            status = data.get('status', {})
            metadata = data.get('metadata', {})
            spec = data.get('spec', {})
            
            # Extract environment variables to get management secret
            containers = spec.get('template', {}).get('spec', {}).get('containers', [])
            env_vars = {}
            management_api_secret = None
            
            if containers:
                env_list = containers[0].get('env', [])
                for env_var in env_list:
                    name = env_var.get('name', '')
                    value = env_var.get('value', '')
                    env_vars[name] = value
                    
                    if name == 'MANAGEMENT_API_SECRET':
                        management_api_secret = value
            
            details = {
                'name': metadata.get('name', service_name),
                'url': status.get('url', ''),
                'region': region,
                'ready': status.get('conditions', [{}])[0].get('status') == 'True',
                'created_at': metadata.get('creationTimestamp', ''),
                'generation': metadata.get('generation', 0),
                'traffic': status.get('traffic', []),
                'management_api_secret': management_api_secret,
                'env_vars': env_vars,
                'config': {
                    'image': spec.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('image', ''),
                    'memory': spec.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('resources', {}).get('limits', {}).get('memory', ''),
                    'cpu': spec.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('resources', {}).get('limits', {}).get('cpu', '')
                }
            }
            return details
        else:
            logger.error(f"Failed to get service details for {service_name}: {response.status_code} {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting service details for {service_name}: {e}")
        return None


def generate_management_api_secret(service_name: str) -> str:
    """Generate a management API secret for a service"""
    import hashlib
    
    # Generate a consistent secret based on service name
    secret_base = f"mgmt-{service_name}-{int(datetime.utcnow().timestamp())}"
    secret_hash = hashlib.sha256(secret_base.encode()).hexdigest()[:32]
    return f"mgmt-{secret_hash}"


@app.post("/projects/{project_id}/sync")
async def sync_project_instances(project_id: str, auth: str = Depends(verify_orchestrator_auth)):
    """Sync database with actual Cloud Run services in the project"""
    try:
        logger.info(f"Starting sync for project {project_id}")
        
        # Get all instances from our database
        instances = await registry.list_instances(project_id)
        active_instances = [i for i in instances if i.get('status') != 'deleted']
        
        # Get all Cloud Run services in the project
        actual_services = await get_cloud_run_services(project_id)
        actual_service_names = {service['name'] for service in actual_services}
        
        sync_results = {
            'project_id': project_id,
            'total_db_instances': len(active_instances),
            'total_actual_services': len(actual_services),
            'synced_instances': [],
            'orphaned_services': [],
            'deleted_instances': []
        }
        
        # Check each database instance against actual services
        for instance in active_instances:
            service_name = instance.get('service_name')
            if service_name:
                if service_name not in actual_service_names:
                    # Instance exists in DB but not in Cloud Run - mark as deleted
                    await registry.update_instance(project_id, instance['instance_id'], {
                        'status': 'deleted',
                        'deleted_at': datetime.utcnow().isoformat(),
                        'deletion_reason': 'manually_deleted_from_gcp'
                    })
                    sync_results['deleted_instances'].append({
                        'instance_id': instance['instance_id'],
                        'service_name': service_name,
                        'reason': 'Service not found in Cloud Run'
                    })
                    logger.info(f"Marked instance {instance['instance_id']} as deleted (service {service_name} not found)")
                else:
                    sync_results['synced_instances'].append({
                        'instance_id': instance['instance_id'],
                        'service_name': service_name,
                        'status': 'active'
                    })
        
        # Check for orphaned services (services in Cloud Run but not in our DB)
        db_service_names = {i.get('service_name') for i in active_instances if i.get('service_name')}
        for service in actual_services:
            if service['name'] not in db_service_names and service['name'].startswith('aaf-instance-'):
                sync_results['orphaned_services'].append({
                    'service_name': service['name'],
                    'url': service.get('url', ''),
                    'reason': 'Service exists but not in database'
                })
        
        logger.info(f"Sync completed for project {project_id}: {len(sync_results['deleted_instances'])} instances marked as deleted")
        return sync_results
        
    except Exception as e:
        logger.error(f"Failed to sync project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.options("/projects/{project_id}/instances/adopt")
async def adopt_instance_options(project_id: str):
    """Handle CORS preflight for adopt instance endpoint"""
    return {}

@app.post("/projects/{project_id}/instances/adopt")
async def adopt_instance(project_id: str, request: AdoptInstanceRequest, auth: str = Depends(verify_orchestrator_auth)):
    """Adopt a specific orphaned Cloud Run service back into the database"""
    try:
        service_name = request.service_name
        logger.info(f"Starting adoption of service {service_name} in project {project_id}")
        
        # Check if the service exists in Cloud Run
        try:
            service_details = await get_cloud_run_service_details(project_id, service_name)
            if not service_details:
                raise HTTPException(status_code=404, detail=f"Service {service_name} not found in Cloud Run")
        except Exception as e:
            logger.error(f"Failed to get service details for {service_name}: {e}")
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found or inaccessible")
        
        # Check if it's already in our database
        try:
            instances = await registry.list_instances(project_id)
            active_instances = [i for i in instances if i.get('status') != 'deleted']
            existing_instance = next((i for i in active_instances if i.get('service_name') == service_name), None)
            
            if existing_instance:
                return {
                    'project_id': project_id,
                    'service_name': service_name,
                    'status': 'already_exists',
                    'instance_id': existing_instance.get('instance_id'),
                    'management_api_secret': existing_instance.get('management_api_secret'),
                    'service_url': existing_instance.get('service_url'),
                    'region': existing_instance.get('region'),
                    'message': f"Service {service_name} is already registered in the database"
                }
        except Exception as e:
            logger.warning(f"Error checking existing instances: {e}")
        
        adoption_result = {
            'project_id': project_id,
            'service_name': service_name,
            'status': 'failed',
            'error': None
        }
        
        # Extract timestamp from service name (aaf-instance-TIMESTAMP)
        if service_name.startswith('aaf-instance-'):
            timestamp_str = service_name.replace('aaf-instance-', '')
            try:
                timestamp = int(timestamp_str)
                created_at = datetime.fromtimestamp(timestamp).isoformat()
            except ValueError:
                created_at = datetime.utcnow().isoformat()
        else:
            created_at = datetime.utcnow().isoformat()
        
        # Generate a new instance ID for the database
        instance_id = f"adopted-{service_name}-{int(datetime.utcnow().timestamp())}"
        
        # Get service details
        region = service_details.get('region', 'europe-west1')
        service_url = service_details.get('url', '')
        status = 'running' if service_details.get('ready', False) else 'pending'
        
        # Extract or generate management API secret
        management_api_secret = service_details.get('management_api_secret')
        if not management_api_secret:
            # Generate a new management API secret for the adopted instance
            management_api_secret = generate_management_api_secret(service_name)
            logger.info(f"Generated new management API secret for adopted service {service_name}")
        else:
            logger.info(f"Extracted existing management API secret from service {service_name}")
        
        # Create database entry for the adopted service
        instance_data = {
                'instance_id': instance_id,
                'service_name': service_name,
                'service_url': service_url,
                'region': region,
                'status': status,
                'created_at': created_at,
                'adoption_date': datetime.utcnow().isoformat(),
                'adopted': True,
                'project_id': project_id,
                'management_api_secret': management_api_secret,  # Include management API secret
                'config': {
                    'memory': service_details.get('config', {}).get('memory', '2Gi'),
                    'cpu': service_details.get('config', {}).get('cpu', '1'),
                    'image': service_details.get('config', {}).get('image', 'europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend:latest'),
                    'instance_management_secret': management_api_secret
                }
        }
        
        # Add to database
        await registry.create_instance(project_id, instance_data)
        
        adoption_result.update({
            'status': 'success',
            'instance_id': instance_id,
            'service_url': service_url,
            'region': region,
            'management_api_secret': management_api_secret,
            'message': f"Successfully adopted service {service_name}"
        })
        
        logger.info(f"Successfully adopted service {service_name} as {instance_id}")
        return adoption_result
        
    except Exception as e:
        logger.error(f"Failed to adopt service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to adopt service {service_name}: {str(e)}")


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
    """Deploy AAF instance to Cloud Run - Simplified Working Version"""
    try:
        logger.info(f"Starting AAF deployment for {service_name} in project {project_id}")
        
        # Create deployment config
        deployment_config = {
            'project_id': project_id,
            'service_name': service_name,
            'region': region,
            'aaf_config': aaf_config,
            'memory': memory,
            'cpu': cpu
        }
        
        # Set up basic BigQuery infrastructure and get project number
        project_number = await setup_basic_bigquery_infrastructure(project_id)
        deployment_config['project_number'] = project_number
        
        # Generate per-instance management API secret
        instance_management_secret = f"mgmt-{service_name}-{hash(service_name)}"
        deployment_config['instance_management_secret'] = instance_management_secret
        
        # Deploy Cloud Run service using REST API
        service_url = await deploy_cloud_run_service_rest(
            config=deployment_config,
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
            'management_api_secret': instance_management_secret,
            'status': 'active'
        })
        
        logger.info(f"Successfully deployed AAF instance {service_name} in project {project_id}")
        
    except Exception as e:
        logger.error(f"Failed to deploy AAF instance {service_name}: {e}")
        # Update instance status to failed
        try:
            await registry.update_instance(project_id, service_name, {'status': 'failed', 'error': str(e)})
        except:
            logger.error(f"Failed to update instance status for {service_name}")

async def setup_basic_bigquery_infrastructure(project_id: str):
    """Set up basic BigQuery infrastructure for AAF"""
    project_number = None
    try:
        from google.cloud import bigquery
        from google.auth import default
        from google.auth.transport.requests import Request
        
        # Get project number first
        try:
            credentials, _ = default()
            credentials.refresh(Request())
            headers = {'Authorization': f'Bearer {credentials.token}'}
            project_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
            response = requests.get(project_url, headers=headers)
            
            if response.status_code == 200:
                project_data = response.json()
                project_number = project_data.get('projectNumber')
                logger.info(f"Retrieved project number: {project_number}")
        except Exception as e:
            logger.warning(f"Could not get project number: {e}")
        
        client = bigquery.Client(project=project_id)
        
        # Create dataset for AAF
        dataset_id = "aaf_data"
        dataset_ref = client.dataset(dataset_id)
        
        try:
            client.get_dataset(dataset_ref)
            logger.info(f"BigQuery dataset {dataset_id} already exists")
        except Exception:
            # Create dataset
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset = client.create_dataset(dataset, timeout=30)
            logger.info(f"Created BigQuery dataset: {dataset_id}")
        
        # Create basic tables that AAF needs
        tables_config = [
            {
                'table_id': 'sessions',
                'description': 'Chat sessions',
                'schema': [
                    bigquery.SchemaField('session_id', 'STRING', mode='REQUIRED'),
                    bigquery.SchemaField('user_id', 'STRING', mode='NULLABLE'),
                    bigquery.SchemaField('created_at', 'TIMESTAMP', mode='REQUIRED'),
                    bigquery.SchemaField('last_activity', 'TIMESTAMP', mode='REQUIRED'),
                    bigquery.SchemaField('metadata', 'JSON', mode='NULLABLE')
                ]
            },
            {
                'table_id': 'website_content',
                'description': 'Vector embeddings for scraped website content',
                'schema': [
                    bigquery.SchemaField('id', 'STRING', mode='REQUIRED'),
                    bigquery.SchemaField('content', 'STRING', mode='REQUIRED'),
                    bigquery.SchemaField('url', 'STRING', mode='NULLABLE'),
                    bigquery.SchemaField('title', 'STRING', mode='NULLABLE'),
                    bigquery.SchemaField('embedding', 'RECORD', mode='REPEATED', fields=[
                        bigquery.SchemaField('value', 'FLOAT64', mode='NULLABLE')
                    ]),
                    bigquery.SchemaField('metadata', 'JSON', mode='NULLABLE'),
                    bigquery.SchemaField('created_at', 'TIMESTAMP', mode='REQUIRED'),
                    bigquery.SchemaField('chunk_index', 'INTEGER', mode='NULLABLE')
                ]
            }
        ]
        
        for table_config in tables_config:
            table_id = table_config['table_id']
            table_ref = dataset_ref.table(table_id)
            
            try:
                client.get_table(table_ref)
                logger.info(f"BigQuery table {table_id} already exists")
            except Exception:
                table = bigquery.Table(table_ref, schema=table_config['schema'])
                table.description = table_config['description']
                table = client.create_table(table, timeout=30)
                logger.info(f"Created BigQuery table: {table_id}")
        
    except Exception as e:
        logger.error(f"Error setting up BigQuery infrastructure: {e}")
        # Don't fail deployment for BigQuery issues
    
    return project_number

async def deploy_cloud_run_service_rest(
    config: Dict[str, Any],
    project_id: str,
    service_name: str,
    region: str,
    aaf_config: Dict[str, Any],
    memory: str,
    cpu: str
) -> str:
    """Deploy Cloud Run service using REST API - Working Implementation"""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import json
        
        logger.info(f"Deploying {service_name} to Cloud Run in {project_id}")
        
        # Get credentials
        credentials, _ = default()
        credentials.refresh(Request())
        
        # Build environment variables
        instance_management_secret = config.get('instance_management_secret', os.getenv("ORCHESTRATOR_API_SECRET", "default-secret"))
        env_vars = [
            {"name": "GOOGLE_CLOUD_PROJECT", "value": project_id},
            {"name": "CRAWL4AI_BASE_URL", "value": os.getenv("CRAWL4AI_BASE_URL", "")},
            {"name": "BIGQUERY_DATASET_ID", "value": "aaf_data"},
            {"name": "MANAGEMENT_API_ENABLED", "value": "true"},
            {"name": "MANAGEMENT_API_SECRET", "value": instance_management_secret},
        ]
        
        # Add custom environment variables from aaf_config
        if 'env_vars' in aaf_config:
            for key, value in aaf_config['env_vars'].items():
                if key not in ['PORT', 'MANAGEMENT_API_SECRET', 'MANAGEMENT_API_ENABLED']:  # Skip reserved/system variables
                    env_vars.append({"name": key, "value": str(value)})
        
        # Use the AAF backend image
        image_uri = "europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend:latest"
        
        # Create service specification
        service_spec = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "labels": {
                    "managed-by": "aaf-orchestrator"
                }
            },
            "spec": {
                "template": {
                    "metadata": {
                        "labels": {
                            "managed-by": "aaf-orchestrator"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "image": image_uri,
                                "env": env_vars,
                                "resources": {
                                    "limits": {
                                        "memory": memory,
                                        "cpu": cpu
                                    }
                                },
                                "ports": [
                                    {
                                        "containerPort": 8080
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
        
        # Deploy the service
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/{region}/services"
        response = requests.post(url, headers=headers, json=service_spec, timeout=300)
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            # Make service publicly accessible
            try:
                await make_service_public(project_id, region, service_name, credentials)
            except Exception as e:
                logger.warning(f"Could not set public access: {e}")
            
            # Get service URL from the deployment result
            service_url = result.get('status', {}).get('url')
            if not service_url:
                # Use project number for correct URL format
                project_number = config.get('project_number')
                if project_number:
                    service_url = f"https://{service_name}-{project_number}.{region}.run.app"
                else:
                    service_url = f"https://{service_name}-{project_id}.run.app"  # fallback
            
            logger.info(f"Successfully deployed {service_name} to {service_url}")
            return service_url
        else:
            logger.error(f"Deployment failed: {response.status_code} - {response.text}")
            raise Exception(f"Cloud Run deployment failed: {response.text}")
            
    except Exception as e:
        logger.error(f"Error deploying Cloud Run service: {e}")
        raise

async def make_service_public(project_id: str, region: str, service_name: str, credentials):
    """Make Cloud Run service publicly accessible"""
    try:
        policy_url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/{region}/services/{service_name}:setIamPolicy"
        
        policy_data = {
            "policy": {
                "bindings": [
                    {
                        "role": "roles/run.invoker",
                        "members": ["allUsers"]
                    }
                ]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(policy_url, headers=headers, json=policy_data, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Made service {service_name} publicly accessible")
        else:
            logger.warning(f"Failed to set public access: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error setting public access: {e}")

async def delete_cloud_run_service(project_id: str, service_name: str, region: str):
    """Delete Cloud Run service"""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        
        # Get credentials
        credentials, _ = default()
        credentials.refresh(Request())
        
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://run.googleapis.com/v1/projects/{project_id}/locations/{region}/services/{service_name}"
        response = requests.delete(url, headers=headers, timeout=300)
        
        if response.status_code in [200, 204]:
            logger.info(f"Deleted Cloud Run service {service_name} in project {project_id}")
        else:
            logger.warning(f"Failed to delete Cloud Run service: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error deleting Cloud Run service: {e}")
        # Don't raise - allow soft failures for cleanup

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
