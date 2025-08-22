"""
Firestore Project Registry
Real-time project registry with better performance than BigQuery
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.cloud import firestore
from google.api_core import exceptions

logger = logging.getLogger(__name__)

class FirestoreProjectRegistry:
    """
    Firestore-based project registry for better performance and real-time updates
    """
    
    def __init__(self, project_id: str, collection_name: str = "aaf_projects"):
        self.project_id = project_id
        self.collection_name = collection_name
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection(collection_name)
        
        # In-memory cache for ultra-fast access
        self._cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 60  # 1 minute cache
    
    async def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create a new project entry"""
        try:
            project_id = project_data['project_id']
            
            # Add timestamps
            now = datetime.utcnow()
            project_data.update({
                'created_at': now,
                'last_updated': now,
                'status': 'active',
                'health_status': 'unknown'
            })
            
            # Create document
            self.collection.document(project_id).set(project_data)
            
            # Update cache
            self._cache[project_id] = project_data
            self._cache_expiry[project_id] = datetime.utcnow() + timedelta(seconds=self._cache_ttl)
            
            logger.info(f"Created project registry entry: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project {project_data.get('project_id')}: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        
        # Check cache first
        if project_id in self._cache:
            if datetime.utcnow() < self._cache_expiry.get(project_id, datetime.min):
                return self._cache[project_id]
        
        try:
            doc = self.collection.document(project_id).get()
            
            if doc.exists:
                project_data = doc.to_dict()
                
                # Convert Firestore timestamps to ISO strings
                if 'created_at' in project_data:
                    project_data['created_at'] = project_data['created_at'].isoformat()
                if 'last_updated' in project_data:
                    project_data['last_updated'] = project_data['last_updated'].isoformat()
                if 'last_health_check' in project_data:
                    project_data['last_health_check'] = project_data['last_health_check'].isoformat()
                
                # Update cache
                self._cache[project_id] = project_data
                self._cache_expiry[project_id] = datetime.utcnow() + timedelta(seconds=self._cache_ttl)
                
                return project_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None
    
    async def list_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """List all projects with given status"""
        try:
            query = self.collection.where("status", "==", status)
            docs = query.stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                project_data['project_id'] = doc.id
                
                # Convert timestamps
                if 'created_at' in project_data:
                    project_data['created_at'] = project_data['created_at'].isoformat()
                if 'last_updated' in project_data:
                    project_data['last_updated'] = project_data['last_updated'].isoformat()
                if 'last_health_check' in project_data:
                    project_data['last_health_check'] = project_data['last_health_check'].isoformat()
                
                projects.append(project_data)
            
            # Sort by creation date (newest first)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project data"""
        try:
            # Add last_updated timestamp
            updates['last_updated'] = datetime.utcnow()
            
            # Update document
            self.collection.document(project_id).update(updates)
            
            # Invalidate cache
            if project_id in self._cache:
                del self._cache[project_id]
                if project_id in self._cache_expiry:
                    del self._cache_expiry[project_id]
            
            logger.info(f"Updated project: {project_id}")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Project {project_id} not found for update")
            return False
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return False
    
    async def update_project_health(self, project_id: str, health_status: str) -> bool:
        """Update project health status"""
        return await self.update_project(project_id, {
            'health_status': health_status,
            'last_health_check': datetime.utcnow()
        })
    
    async def delete_project(self, project_id: str) -> bool:
        """Mark project as deleted (soft delete)"""
        return await self.update_project(project_id, {
            'status': 'deleted'
        })
    
    async def get_projects_by_customer(self, customer_email: str) -> List[Dict[str, Any]]:
        """Get all projects for a specific customer"""
        try:
            query = self.collection.where("customer_info.email", "==", customer_email)
            docs = query.stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                project_data['project_id'] = doc.id
                projects.append(project_data)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get projects for customer {customer_email}: {e}")
            return []
    
    def create_real_time_listener(self, callback):
        """Create real-time listener for project changes"""
        def on_snapshot(docs, changes, read_time):
            for change in changes:
                if change.type.name == 'ADDED':
                    callback('added', change.document.id, change.document.to_dict())
                elif change.type.name == 'MODIFIED':
                    callback('modified', change.document.id, change.document.to_dict())
                elif change.type.name == 'REMOVED':
                    callback('removed', change.document.id, change.document.to_dict())
        
        # Listen to all projects
        return self.collection.on_snapshot(on_snapshot)
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        try:
            # Count by status
            active_query = self.collection.where("status", "==", "active")
            active_count = len(list(active_query.stream()))
            
            deleted_query = self.collection.where("status", "==", "deleted")
            deleted_count = len(list(deleted_query.stream()))
            
            # Count by health status
            healthy_query = self.collection.where("health_status", "==", "healthy")
            healthy_count = len(list(healthy_query.stream()))
            
            unhealthy_query = self.collection.where("health_status", "==", "unhealthy")
            unhealthy_count = len(list(unhealthy_query.stream()))
            
            return {
                'total_projects': active_count + deleted_count,
                'active_projects': active_count,
                'deleted_projects': deleted_count,
                'healthy_projects': healthy_count,
                'unhealthy_projects': unhealthy_count,
                'unknown_health': active_count - healthy_count - unhealthy_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
