"""
Project Creator Flask App for Cloud Run
"""
import os
import logging
import json
import time
import uuid
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from google.cloud import resourcemanager_v3, run_v2, bigquery
from google.cloud import service_usage_v1 as serviceusage_v1
from google.cloud import iam
try:
    from google.cloud import cloudbuild_v1
except ImportError:
    # Handle import error - cloudbuild_v1 not available
    cloudbuild_v1 = None
from google.oauth2 import service_account
import googleapiclient.discovery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Required APIs to enable
REQUIRED_APIS = [
    'compute.googleapis.com',
    'cloudbuild.googleapis.com',
    'run.googleapis.com',
    'bigquery.googleapis.com',
    'storage.googleapis.com',
    'iam.googleapis.com',
]

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

def create_gcp_project(project_name: str, customer_id: str) -> str:
    """Create a new GCP project"""
    try:
        client = resourcemanager_v3.ProjectsClient()
        
        # Generate unique project ID
        project_id = f"aaf-{customer_id}-{uuid.uuid4().hex[:8]}"
        
        # Create project request
        operation = client.create_project(
            project=resourcemanager_v3.Project(
                project_id=project_id,
                display_name=project_name,
                parent=f"organizations/{os.getenv('ORGANIZATION_ID')}" if os.getenv('ORGANIZATION_ID') else None
            )
        )
        
        # Wait for operation to complete
        result = operation.result(timeout=300)
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

@app.route('/', methods=['POST'])
def create_project():
    """
    Create project endpoint that matches the Cloud Function interface
    """
    try:
        # Get request data
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        project_name = request_json.get('project_name')
        customer_id = request_json.get('customer_id', 'default')
        
        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400
        
        logger.info(f"Creating project: {project_name} for customer: {customer_id}")
        
        # Create project
        project_id = create_gcp_project(project_name, customer_id)
        
        # Enable APIs
        enable_apis(project_id)
        
        result = {
            'success': True,
            'project_id': project_id,
            'project_name': project_name,
            'customer_id': customer_id,
            'status': 'created'
        }
        
        logger.info(f"Project creation completed: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for basic info"""
    return jsonify({
        'service': 'AAF Project Creator',
        'status': 'running',
        'endpoints': {
            'POST /': 'Create new AAF project',
            'GET /health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
