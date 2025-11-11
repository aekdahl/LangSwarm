"""
BigQuery Session Storage - Append-Only Pattern
==============================================

Proper BigQuery implementation that follows BigQuery best practices:
- Append-only operations (no updates)
- Query latest session state when needed
- Use partitioning and clustering for performance
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import json

from .storage import SessionStorage
from .models import LangSwarmSession, SessionMetadata, SessionStatus

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)


class BigQuerySessionStorage(SessionStorage):
    """
    BigQuery session storage using append-only pattern.
    
    Instead of updating records, this storage:
    1. Appends new session events/updates
    2. Queries for latest state when needed
    3. Uses event sourcing pattern for session lifecycle
    """
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str = "session_events"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        if bigquery is None:
            raise ImportError("google-cloud-bigquery is required for BigQuery session storage")
        
        self.client = bigquery.Client(project=project_id)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create session events table if it doesn't exist"""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"✅ BigQuery session table exists: {self.table_ref}")
        except:
            logger.info(f"📝 Creating BigQuery session table: {self.table_ref}")
            
            schema = [
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),  # created, updated, message_added, etc.
                bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("session_data", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("message_data", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
            ]
            
            table = bigquery.Table(self.table_ref, schema=schema)
            
            # Add partitioning and clustering for performance
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="event_timestamp"
            )
            table.clustering_fields = ["session_id", "user_id", "event_type"]
            
            table = self.client.create_table(table)
            logger.info(f"✅ Created session table: {table.table_id}")
    
    def save_session(self, session: LangSwarmSession) -> bool:
        """
        Save session by appending events (never updates).
        
        Args:
            session: Session to save
            
        Returns:
            bool: True if successful
        """
        try:
            # Determine event type based on session state
            existing_state = self._get_latest_session_event(session.session_id)
            event_type = "session_updated" if existing_state else "session_created"
            
            event = {
                "event_id": str(uuid4()),
                "session_id": session.session_id,
                "user_id": session.user_id,
                "event_type": event_type,
                "event_timestamp": datetime.utcnow().isoformat(),
                "session_data": session.to_dict(),
                "message_data": None,
                "metadata": {
                    "created_at": session.metadata.created_at.isoformat() if session.metadata.created_at else None,
                    "updated_at": session.metadata.updated_at.isoformat() if session.metadata.updated_at else None,
                    "source": "langswarm_session_storage"
                }
            }
            
            # Append event to BigQuery (no updates!)
            errors = self.client.insert_rows_json(self.table_ref, [event])
            if errors:
                logger.error(f"❌ Failed to save session {session.session_id}: {errors}")
                return False
            
            logger.debug(f"✅ Session saved: {session.session_id} ({event_type})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving session {session.session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[LangSwarmSession]:
        """
        Load session by querying latest state from events.
        
        Args:
            session_id: Session identifier
            
        Returns:
            LangSwarmSession or None if not found
        """
        try:
            query = f"""
            SELECT 
                session_data,
                event_timestamp
            FROM `{self.table_ref}`
            WHERE session_id = @session_id 
              AND event_type IN ('session_created', 'session_updated')
              AND session_data IS NOT NULL
            ORDER BY event_timestamp DESC
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job)
            
            if not results:
                logger.debug(f"⚠️ Session not found: {session_id}")
                return None
            
            row = results[0]
            session_data = row.session_data
            
            # Reconstruct session from data
            session = LangSwarmSession.from_dict(session_data)
            
            logger.debug(f"✅ Session loaded: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"❌ Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Mark session as deleted by appending a deletion event.
        (BigQuery doesn't support actual deletes in streaming buffer)
        
        Args:
            session_id: Session to mark as deleted
            
        Returns:
            bool: True if successful
        """
        try:
            event = {
                "event_id": str(uuid4()),
                "session_id": session_id,
                "user_id": None,
                "event_type": "session_deleted",
                "event_timestamp": datetime.utcnow().isoformat(),
                "session_data": None,
                "message_data": None,
                "metadata": {
                    "deleted_at": datetime.utcnow().isoformat(),
                    "source": "langswarm_session_storage"
                }
            }
            
            errors = self.client.insert_rows_json(self.table_ref, [event])
            if errors:
                logger.error(f"❌ Failed to delete session {session_id}: {errors}")
                return False
            
            logger.info(f"✅ Session marked as deleted: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[SessionMetadata]:
        """
        List sessions by querying latest states.
        
        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of sessions
            
        Returns:
            List of session metadata
        """
        try:
            where_conditions = ["event_type IN ('session_created', 'session_updated')", "session_data IS NOT NULL"]
            query_params = []
            
            if user_id:
                where_conditions.append("user_id = @user_id")
                query_params.append(bigquery.ScalarQueryParameter("user_id", "STRING", user_id))
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            WITH latest_sessions AS (
                SELECT 
                    session_id,
                    session_data,
                    event_timestamp,
                    ROW_NUMBER() OVER (
                        PARTITION BY session_id 
                        ORDER BY event_timestamp DESC
                    ) as rn
                FROM `{self.table_ref}`
                WHERE {where_clause}
            ),
            filtered_sessions AS (
                SELECT 
                    session_id,
                    session_data,
                    event_timestamp
                FROM latest_sessions
                WHERE rn = 1
                AND NOT EXISTS (
                    SELECT 1 FROM `{self.table_ref}` deleted
                    WHERE deleted.session_id = latest_sessions.session_id
                    AND deleted.event_type = 'session_deleted'
                    AND deleted.event_timestamp > latest_sessions.event_timestamp
                )
            )
            SELECT 
                session_id,
                session_data,
                event_timestamp
            FROM filtered_sessions
            ORDER BY event_timestamp DESC
            LIMIT @limit
            """
            
            query_params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))
            
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            query_job = self.client.query(query, job_config=job_config)
            
            sessions = []
            for row in query_job:
                try:
                    session_data = row.session_data
                    metadata = SessionMetadata.from_dict(session_data.get("metadata", {}))
                    
                    # Apply status filter if specified
                    if status is None or metadata.status == status:
                        sessions.append(metadata)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing session metadata: {e}")
                    continue
            
            logger.debug(f"✅ Listed {len(sessions)} sessions")
            return sessions[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"❌ Error listing sessions: {e}")
            return []
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata by appending an update event.
        
        Args:
            session_id: Session to update
            metadata: New metadata values
            
        Returns:
            bool: True if successful
        """
        try:
            # Load current session
            session = self.load_session(session_id)
            if not session:
                logger.warning(f"⚠️ Cannot update metadata - session not found: {session_id}")
                return False
            
            # Update metadata
            for key, value in metadata.items():
                if hasattr(session.metadata, key):
                    setattr(session.metadata, key, value)
            
            # Save updated session (will append update event)
            return self.save_session(session)
            
        except Exception as e:
            logger.error(f"❌ Error updating session metadata {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """
        Mark expired sessions as deleted.
        (Actual cleanup would be done by BigQuery scheduled queries)
        
        Args:
            max_age_days: Age threshold in days
            
        Returns:
            Number of sessions marked for deletion
        """
        try:
            cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff = cutoff.replace(day=cutoff.day - max_age_days)
            
            # Find expired sessions
            query = f"""
            SELECT DISTINCT session_id
            FROM `{self.table_ref}`
            WHERE event_type IN ('session_created', 'session_updated')
              AND event_timestamp < @cutoff
              AND session_id NOT IN (
                  SELECT session_id 
                  FROM `{self.table_ref}` 
                  WHERE event_type = 'session_deleted'
              )
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("cutoff", "TIMESTAMP", cutoff)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            expired_sessions = [row.session_id for row in query_job]
            
            # Mark each as deleted
            deleted_count = 0
            for session_id in expired_sessions:
                if self.delete_session(session_id):
                    deleted_count += 1
            
            logger.info(f"✅ Marked {deleted_count} expired sessions for deletion")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired sessions: {e}")
            return 0
    
    def _get_latest_session_event(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest event for a session (internal helper)"""
        try:
            query = f"""
            SELECT event_type, event_timestamp
            FROM `{self.table_ref}`
            WHERE session_id = @session_id
            ORDER BY event_timestamp DESC
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job)
            
            if results:
                row = results[0]
                return {
                    "event_type": row.event_type,
                    "event_timestamp": row.event_timestamp
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting latest session event for {session_id}: {e}")
            return None
