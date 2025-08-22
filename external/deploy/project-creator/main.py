"""
AAF Project Creator Cloud Function Entry Point
Simple HTTP function to create GCP projects for AAF instances
"""

import os
import json
import logging
import uuid
from typing import Dict, Any
from google.cloud import resourcemanager_v3
from google.cloud import service_usage_v1 as serviceusage_v1
import functions_framework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required APIs to enable in new projects
REQUIRED_APIS = [
    'compute.googleapis.com',
    'cloudbuild.googleapis.com', 
    'run.googleapis.com',
    'bigquery.googleapis.com',
    'storage.googleapis.com',
    'iam.googleapis.com',
]

def create_gcp_project(project_name: str, customer_id: str) -> str:
    """Create a new GCP project"""
    try:
        client = resourcemanager_v3.ProjectsClient()
        
        # Generate unique project ID
        project_id = f"aaf-{customer_id}-{uuid.uuid4().hex[:8]}"
        
        # Determine parent resource
        parent = None
        organization_id = os.environ.get('ORGANIZATION_ID')
        if organization_id:
            parent = f"organizations/{organization_id}"
        
        # Create project request
        project_request = resourcemanager_v3.Project(
            project_id=project_id,
            display_name=project_name,
            parent=parent
        )
        
        # Create the project
        operation = client.create_project(project=project_request)
        result = operation.result(timeout=300)  # 5 minutes timeout
        
        logger.info(f"Created project: {project_id}")
        return project_id
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise

def enable_apis(project_id: str):
    """Enable required APIs for the project"""
    try:
        client = serviceusage_v1.ServiceUsageClient()
        
        for api in REQUIRED_APIS:
            service_name = f"projects/{project_id}/services/{api}"
            
            try:
                operation = client.enable_service(name=service_name)
                operation.result(timeout=300)
                logger.info(f"Enabled API: {api}")
            except Exception as e:
                logger.warning(f"Failed to enable {api}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to enable APIs: {e}")
        raise

@functions_framework.http
def create_project(request):
    """
    Cloud Function entry point for creating AAF projects
    """
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)
        
        # Handle GET request for health check
        if request.method == 'GET':
            response = {
                'service': 'AAF Project Creator',
                'status': 'running',
                'endpoints': {
                    'POST /': 'Create new AAF project',
                    'GET /': 'Health check'
                }
            }
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
            return (response, 200, headers)
        
        # Only allow POST requests for project creation
        if request.method != 'POST':
            return {'error': 'Only POST method allowed for project creation'}, 405
        
        # Get request data
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return {'error': 'No JSON data provided'}, 400
        
        # Extract required fields
        project_name = request_json.get('project_name')
        customer_id = request_json.get('customer_id', 'default')
        
        if not project_name:
            return {'error': 'project_name is required'}, 400
        
        logger.info(f"Creating project: {project_name} for customer: {customer_id}")
        
        # Step 1: Create GCP project
        project_id = create_gcp_project(project_name, customer_id)
        
        # Step 2: Enable APIs
        enable_apis(project_id)
        
        # Return success response
        result = {
            'success': True,
            'project_id': project_id,
            'project_name': project_name,
            'customer_id': customer_id,
            'status': 'created'
        }
        
        logger.info(f"Project creation completed: {result}")
        
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        
        return (result, 200, headers)
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        
        error_response = {
            'error': str(e), 
            'success': False
        }
        
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        
        return (error_response, 500, headers)