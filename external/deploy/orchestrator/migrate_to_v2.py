#!/usr/bin/env python3
"""
Migration script from AAF Orchestrator v1 to v2
Converts old project structure to new project/instance separation
"""

import asyncio
import logging
from datetime import datetime
from google.cloud import firestore

from firestore_registry import FirestoreProjectRegistry
from project_instance_registry import ProjectInstanceRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationTool:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.old_registry = FirestoreProjectRegistry(project_id, "aaf_projects")
        self.new_registry = ProjectInstanceRegistry(project_id, "aaf_projects_v2")
        
    async def migrate_all(self, dry_run: bool = True):
        """Migrate all data from v1 to v2 format"""
        logger.info(f"Starting migration {'(DRY RUN)' if dry_run else '(LIVE)'}")
        
        try:
            # Get all projects from old format
            old_projects = await self.old_registry.list_projects()
            logger.info(f"Found {len(old_projects)} projects to migrate")
            
            migrated_count = 0
            
            for old_project in old_projects:
                try:
                    success = await self.migrate_project(old_project, dry_run)
                    if success:
                        migrated_count += 1
                except Exception as e:
                    logger.error(f"Failed to migrate project {old_project.get('project_id')}: {e}")
            
            logger.info(f"Migration completed: {migrated_count}/{len(old_projects)} projects migrated")
            
            if dry_run:
                logger.info("This was a DRY RUN - no actual changes were made")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def migrate_project(self, old_project: dict, dry_run: bool = True) -> bool:
        """Migrate a single project from v1 to v2 format"""
        project_id = old_project.get('project_id')
        if not project_id:
            logger.warning("Project missing project_id, skipping")
            return False
        
        logger.info(f"Migrating project: {project_id}")
        
        try:
            # Create new project structure
            new_project_data = {
                'project_id': project_id,
                'project_name': old_project.get('project_name', project_id),
                'customer_info': old_project.get('customer_info', {}),
                'region': old_project.get('region', 'europe-west1'),
                'billing_account': old_project.get('billing_account'),
                'status': old_project.get('status', 'active'),
                'created_at': old_project.get('created_at', datetime.utcnow()),
                'last_updated': old_project.get('last_updated', datetime.utcnow())
            }
            
            # Create project in new format
            if not dry_run:
                project_created = await self.new_registry.create_project(new_project_data)
                if not project_created:
                    logger.warning(f"Project {project_id} already exists in v2, updating instead")
            else:
                logger.info(f"[DRY RUN] Would create project: {project_id}")
            
            # Convert old project data to instance data
            instance_data = {
                'service_name': old_project.get('service_name'),
                'service_url': old_project.get('service_url'),
                'region': old_project.get('region', 'europe-west1'),
                'aaf_config': old_project.get('aaf_config', {}),
                'management_api_secret': old_project.get('management_api_secret'),
                'health_status': old_project.get('health_status', 'unknown')
            }
            
            # Only create instance if we have service information
            if instance_data.get('service_name'):
                if not dry_run:
                    instance_id = await self.new_registry.create_instance(project_id, instance_data)
                    if instance_id:
                        logger.info(f"Created instance {instance_id} in project {project_id}")
                    else:
                        logger.warning(f"Failed to create instance in project {project_id}")
                else:
                    logger.info(f"[DRY RUN] Would create instance with service: {instance_data.get('service_name')}")
            else:
                logger.info(f"Project {project_id} has no service information, creating project only")
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating project {project_id}: {e}")
            return False
    
    async def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("Verifying migration...")
        
        # Compare counts
        old_projects = await self.old_registry.list_projects()
        new_projects = await self.new_registry.list_projects(status="all")
        
        logger.info(f"Old projects: {len(old_projects)}")
        logger.info(f"New projects: {len(new_projects)}")
        
        # Check each project
        for old_project in old_projects:
            project_id = old_project.get('project_id')
            new_project = await self.new_registry.get_project(project_id)
            
            if not new_project:
                logger.error(f"Project {project_id} not found in new format")
                continue
            
            # Check if instance was created (if old project had service)
            if old_project.get('service_name'):
                instances = await self.new_registry.list_instances(project_id, status="all")
                if not instances:
                    logger.error(f"Project {project_id} missing instance for service {old_project.get('service_name')}")
                else:
                    logger.info(f"Project {project_id} has {len(instances)} instances")
        
        logger.info("Migration verification completed")
    
    async def rollback_migration(self):
        """Rollback migration by deleting v2 collection"""
        logger.warning("Rolling back migration - this will delete all v2 data!")
        
        # Delete all documents in v2 collection
        docs = self.new_registry.collection.stream()
        batch = self.new_registry.db.batch()
        
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Commit in batches of 500
            if count % 500 == 0:
                batch.commit()
                batch = self.new_registry.db.batch()
        
        # Commit remaining
        if count % 500 != 0:
            batch.commit()
        
        logger.info(f"Rollback completed - deleted {count} documents from v2 collection")

async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate AAF Orchestrator from v1 to v2")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    
    args = parser.parse_args()
    
    migration = MigrationTool(args.project_id)
    
    if args.rollback:
        await migration.rollback_migration()
    elif args.verify:
        await migration.verify_migration()
    else:
        await migration.migrate_all(dry_run=args.dry_run)

if __name__ == "__main__":
    asyncio.run(main())
