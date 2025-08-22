"""
Project and Instance Registry
Proper separation of projects and AAF instances
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.cloud import firestore
from google.api_core import exceptions
import uuid

logger = logging.getLogger(__name__)

class ProjectInstanceRegistry:
    """
    Enhanced registry that properly separates projects and instances
    
    Data Model:
    - Project: A customer's GCP project that can contain multiple AAF instances
    - Instance: A single AAF deployment (Cloud Run service) within a project
    """
    
    def __init__(self, registry_project_id: str, collection_name: str = "aaf_projects_v2"):
        self.registry_project_id = registry_project_id
        self.collection_name = collection_name
        self.db = firestore.Client(project=registry_project_id)
        self.collection = self.db.collection(collection_name)
        logger.info(f"Initialized ProjectInstanceRegistry with project {registry_project_id}")
    
    def _get_timestamp(self):
        """Get current timestamp"""
        return datetime.utcnow()
    
    # === PROJECT MANAGEMENT ===
    
    async def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create a new project record"""
        try:
            project_id = project_data['project_id']
            
            # Check if project already exists
            doc_ref = self.collection.document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                logger.warning(f"Project {project_id} already exists")
                return False
            
            # Create project with empty instances
            project_record = {
                'project_id': project_id,
                'project_name': project_data.get('project_name', project_id),
                'customer_info': project_data.get('customer_info', {}),
                'region': project_data.get('region', 'europe-west1'),
                'billing_account': project_data.get('billing_account'),
                'status': 'active',
                'created_at': self._get_timestamp(),
                'last_updated': self._get_timestamp(),
                'instances': {},
                'instance_count': 0
            }
            
            doc_ref.set(project_record)
            logger.info(f"Created project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating project {project_data.get('project_id')}: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        try:
            doc_ref = self.collection.document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    async def list_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """List projects by status"""
        try:
            if status == "all":
                query = self.collection
            else:
                query = self.collection.where('status', '==', status)
            
            docs = query.stream()
            projects = []
            
            for doc in docs:
                project_data = doc.to_dict()
                # Add summary information
                project_data['total_instances'] = len(project_data.get('instances', {}))
                project_data['active_instances'] = len([
                    inst for inst in project_data.get('instances', {}).values() 
                    if inst.get('status') == 'active'
                ])
                projects.append(project_data)
            
            return projects
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project information"""
        try:
            doc_ref = self.collection.document(project_id)
            updates['last_updated'] = self._get_timestamp()
            
            doc_ref.update(updates)
            logger.info(f"Updated project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    async def delete_project(self, project_id: str, hard_delete: bool = False) -> bool:
        """Delete project (soft delete by default)"""
        try:
            if hard_delete:
                # Permanently delete the document
                doc_ref = self.collection.document(project_id)
                doc_ref.delete()
                logger.info(f"Hard deleted project {project_id}")
            else:
                # Soft delete - mark as deleted
                await self.update_project(project_id, {'status': 'deleted'})
                logger.info(f"Soft deleted project {project_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    # === INSTANCE MANAGEMENT ===
    
    def _generate_instance_id(self, project_id: str) -> str:
        """Generate a unique instance ID"""
        timestamp = int(datetime.utcnow().timestamp())
        random_suffix = str(uuid.uuid4())[:8]
        return f"aaf-{project_id[:10]}-{timestamp}-{random_suffix}"
    
    async def create_instance(self, project_id: str, instance_data: Dict[str, Any]) -> Optional[str]:
        """Create a new AAF instance within a project"""
        try:
            # Generate instance ID if not provided
            instance_id = instance_data.get('instance_id') or self._generate_instance_id(project_id)
            
            doc_ref = self.collection.document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.error(f"Project {project_id} does not exist")
                return None
            
            project_data = doc.to_dict()
            instances = project_data.get('instances', {})
            
            # Check if instance already exists
            if instance_id in instances:
                logger.warning(f"Instance {instance_id} already exists in project {project_id}")
                return None
            
            # Create instance record
            instance_record = {
                'instance_id': instance_id,
                'service_name': instance_data.get('service_name', instance_id),
                'service_url': instance_data.get('service_url'),
                'region': instance_data.get('region', project_data.get('region', 'europe-west1')),
                'aaf_config': instance_data.get('aaf_config', {}),
                'management_api_secret': instance_data.get('management_api_secret'),
                'status': 'active',
                'created_at': self._get_timestamp(),
                'last_updated': self._get_timestamp(),
                'health_status': 'unknown'
            }
            
            # Add instance to project
            instances[instance_id] = instance_record
            
            # Update project document
            doc_ref.update({
                'instances': instances,
                'instance_count': len(instances),
                'last_updated': self._get_timestamp()
            })
            
            logger.info(f"Created instance {instance_id} in project {project_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"Error creating instance in project {project_id}: {e}")
            return None
    
    async def get_instance(self, project_id: str, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get specific instance information"""
        try:
            project = await self.get_project(project_id)
            if not project:
                return None
            
            instances = project.get('instances', {})
            return instances.get(instance_id)
            
        except Exception as e:
            logger.error(f"Error getting instance {instance_id} in project {project_id}: {e}")
            return None
    
    async def list_instances(self, project_id: str, status: str = "active") -> List[Dict[str, Any]]:
        """List instances in a project"""
        try:
            project = await self.get_project(project_id)
            if not project:
                return []
            
            instances = project.get('instances', {})
            
            if status == "all":
                return list(instances.values())
            else:
                return [inst for inst in instances.values() if inst.get('status') == status]
            
        except Exception as e:
            logger.error(f"Error listing instances for project {project_id}: {e}")
            return []
    
    async def update_instance(self, project_id: str, instance_id: str, updates: Dict[str, Any]) -> bool:
        """Update instance information"""
        try:
            doc_ref = self.collection.document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.error(f"Project {project_id} does not exist")
                return False
            
            project_data = doc.to_dict()
            instances = project_data.get('instances', {})
            
            if instance_id not in instances:
                logger.error(f"Instance {instance_id} not found in project {project_id}")
                return False
            
            # Update instance
            instance = instances[instance_id]
            instance.update(updates)
            instance['last_updated'] = self._get_timestamp()
            
            # Update project document
            doc_ref.update({
                'instances': instances,
                'last_updated': self._get_timestamp()
            })
            
            logger.info(f"Updated instance {instance_id} in project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating instance {instance_id} in project {project_id}: {e}")
            return False
    
    async def delete_instance(self, project_id: str, instance_id: str, hard_delete: bool = False) -> bool:
        """Delete instance from project"""
        try:
            doc_ref = self.collection.document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.error(f"Project {project_id} does not exist")
                return False
            
            project_data = doc.to_dict()
            instances = project_data.get('instances', {})
            
            if instance_id not in instances:
                logger.error(f"Instance {instance_id} not found in project {project_id}")
                return False
            
            if hard_delete:
                # Completely remove instance
                del instances[instance_id]
                logger.info(f"Hard deleted instance {instance_id} from project {project_id}")
            else:
                # Soft delete - mark as deleted
                instances[instance_id]['status'] = 'deleted'
                instances[instance_id]['last_updated'] = self._get_timestamp()
                logger.info(f"Soft deleted instance {instance_id} in project {project_id}")
            
            # Update project document
            doc_ref.update({
                'instances': instances,
                'instance_count': len([inst for inst in instances.values() if inst.get('status') != 'deleted']),
                'last_updated': self._get_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting instance {instance_id} in project {project_id}: {e}")
            return False
    
    # === COMPATIBILITY METHODS (for migration) ===
    
    async def get_project_by_service_name(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Find project containing an instance with specific service name"""
        try:
            # Query all projects
            docs = self.collection.stream()
            
            for doc in docs:
                project_data = doc.to_dict()
                instances = project_data.get('instances', {})
                
                for instance_id, instance in instances.items():
                    if instance.get('service_name') == service_name:
                        # Return both project and instance info
                        return {
                            'project': project_data,
                            'instance': instance,
                            'instance_id': instance_id
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding project by service name {service_name}: {e}")
            return None
