"""
BigQuery Session Manager
Unified session and conversation storage using BigQuery
"""
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)


class BigQuerySessionManager:
    """
    Session manager using BigQuery for storage
    
    Benefits:
    - Persistent across container restarts
    - Scalable for multiple instances
    - Integrated with conversation storage
    - No additional infrastructure needed
    """
    
    def __init__(
        self, 
        project_id: str, 
        dataset_id: str, 
        table_id: str = "sessions",
        location: str = "US",
        default_ttl: int = 3600
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.location = location
        self.default_ttl = default_ttl
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        if bigquery is None:
            raise ValueError("google-cloud-bigquery is required for BigQuery session storage")
        
        self.client = bigquery.Client(project=project_id, location=location)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create sessions table if it doesn't exist"""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"BigQuery sessions table exists: {self.table_ref}")
        except NotFound:
            # Create the dataset if it doesn't exist
            try:
                self.client.get_dataset(f"{self.project_id}.{self.dataset_id}")
            except NotFound:
                dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
                dataset.location = self.location
                self.client.create_dataset(dataset)
                logger.info(f"Created BigQuery dataset: {self.dataset_id}")
            
            # Create the sessions table
            schema = [
                bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("session_data", "JSON", mode="REQUIRED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("last_activity", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("expires_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("agent_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("user_context", "JSON", mode="NULLABLE"),
            ]
            
            table = bigquery.Table(self.table_ref, schema=schema)
            table.description = f"AAF chatbot session storage"
            self.client.create_table(table)
            logger.info(f"Created BigQuery sessions table: {self.table_ref}")
    
    async def create_session(
        self, 
        session_id: Optional[str] = None, 
        agent_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **initial_data
    ) -> str:
        """Create a new session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=self.default_ttl)
        
        session_data = {
            "session_id": session_id,
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "message_count": 0,
            "status": "active",
            **initial_data
        }
        
        row = {
            "session_id": session_id,
            "session_data": json.dumps(session_data),
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "agent_id": agent_id,
            "user_context": json.dumps(user_context or {}),
        }
        
        try:
            errors = self.client.insert_rows_json(self.table_ref, [row])
            if errors:
                logger.error(f"Failed to create session: {errors}")
                raise Exception(f"Failed to create session: {errors}")
            
            logger.info(f"Created session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        query = f"""
        SELECT 
            session_id,
            session_data,
            created_at,
            last_activity,
            expires_at,
            agent_id,
            user_context
        FROM `{self.table_ref}`
        WHERE session_id = @session_id
        AND expires_at > CURRENT_TIMESTAMP()
        ORDER BY last_activity DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if not results:
                return None
            
            row = results[0]
            session_data = dict(row.session_data) if row.session_data else {}
            
            # Update last activity
            await self._update_last_activity(session_id)
            
            return {
                "session_id": row.session_id,
                "data": session_data,
                "created_at": row.created_at.isoformat(),
                "last_activity": row.last_activity.isoformat(),
                "expires_at": row.expires_at.isoformat(),
                "agent_id": row.agent_id,
                "user_context": dict(row.user_context) if row.user_context else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def update_session(
        self, 
        session_id: str, 
        data: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session data"""
        
        # Get current session
        current = await self.get_session(session_id)
        if not current:
            return False
        
        # Prepare update data
        updates = []
        parameters = [bigquery.ScalarQueryParameter("session_id", "STRING", session_id)]
        
        if data:
            # Merge with existing session data
            current_data = current.get("data", {})
            current_data.update(data)
            updates.append("session_data = @session_data")
            parameters.append(
                bigquery.ScalarQueryParameter("session_data", "JSON", json.dumps(current_data))
            )
        
        if agent_id is not None:
            updates.append("agent_id = @agent_id")
            parameters.append(bigquery.ScalarQueryParameter("agent_id", "STRING", agent_id))
        
        if user_context is not None:
            # Merge with existing user context
            current_context = current.get("user_context", {})
            current_context.update(user_context)
            updates.append("user_context = @user_context")
            parameters.append(
                bigquery.ScalarQueryParameter("user_context", "JSON", json.dumps(current_context))
            )
        
        # Always update last activity
        updates.append("last_activity = CURRENT_TIMESTAMP()")
        
        if not updates:
            return True  # Nothing to update
        
        query = f"""
        UPDATE `{self.table_ref}`
        SET {', '.join(updates)}
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=parameters)
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion
            logger.debug(f"Updated session: {session_id}")
            return True
            
        except Exception as e:
            error_message = str(e)
            # Handle BigQuery streaming buffer limitation gracefully
            if "streaming buffer" in error_message.lower() and "not supported" in error_message.lower():
                logger.warning(f"Cannot update session {session_id} in streaming buffer - this is expected for new sessions")
                return True  # Don't fail, just skip the update
            else:
                logger.error(f"Error updating session {session_id}: {e}")
                return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        query = f"""
        DELETE FROM `{self.table_ref}`
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """Extend session expiration"""
        ttl = ttl or self.default_ttl
        
        query = f"""
        UPDATE `{self.table_ref}`
        SET 
            expires_at = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL @ttl SECOND),
            last_activity = CURRENT_TIMESTAMP()
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
                bigquery.ScalarQueryParameter("ttl", "INT64", ttl)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            return True
            
        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            return False
    
    async def list_active_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List active sessions"""
        query = f"""
        SELECT 
            session_id,
            session_data,
            created_at,
            last_activity,
            expires_at,
            agent_id,
            user_context
        FROM `{self.table_ref}`
        WHERE expires_at > CURRENT_TIMESTAMP()
        ORDER BY last_activity DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            sessions = []
            for row in results:
                sessions.append({
                    "session_id": row.session_id,
                    "data": dict(row.session_data) if row.session_data else {},
                    "created_at": row.created_at.isoformat(),
                    "last_activity": row.last_activity.isoformat(),
                    "expires_at": row.expires_at.isoformat(),
                    "agent_id": row.agent_id,
                    "user_context": dict(row.user_context) if row.user_context else {}
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        query = f"""
        WITH session_stats AS (
          SELECT 
            COUNT(*) as total_active_sessions,
            COUNT(DISTINCT agent_id) as unique_agents,
            AVG(TIMESTAMP_DIFF(last_activity, created_at, SECOND)) as avg_session_duration_seconds,
            MIN(created_at) as oldest_session,
            MAX(last_activity) as most_recent_activity
          FROM `{self.table_ref}`
          WHERE expires_at > CURRENT_TIMESTAMP()
        ),
        recent_activity AS (
          SELECT COUNT(*) as sessions_last_hour
          FROM `{self.table_ref}`
          WHERE last_activity > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
          AND expires_at > CURRENT_TIMESTAMP()
        )
        SELECT 
          s.*,
          r.sessions_last_hour
        FROM session_stats s
        CROSS JOIN recent_activity r
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                return {
                    "total_active_sessions": row.total_active_sessions,
                    "unique_agents": row.unique_agents,
                    "avg_session_duration_seconds": float(row.avg_session_duration_seconds) if row.avg_session_duration_seconds else 0,
                    "oldest_session": row.oldest_session.isoformat() if row.oldest_session else None,
                    "most_recent_activity": row.most_recent_activity.isoformat() if row.most_recent_activity else None,
                    "sessions_last_hour": row.sessions_last_hour,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "total_active_sessions": 0,
                    "unique_agents": 0,
                    "avg_session_duration_seconds": 0,
                    "sessions_last_hour": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        query = f"""
        DELETE FROM `{self.table_ref}`
        WHERE expires_at <= CURRENT_TIMESTAMP()
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            
            # Get count of deleted rows (BigQuery doesn't return this directly)
            # So we'll just log that cleanup ran
            logger.info("Cleaned up expired sessions")
            return 0  # BigQuery doesn't easily return affected row count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def increment_message_count(self, session_id: str) -> bool:
        """Increment message count for a session"""
        query = f"""
        UPDATE `{self.table_ref}`
        SET 
            session_data = JSON_SET(
                session_data, 
                '$.message_count', 
                CAST(COALESCE(JSON_EXTRACT_SCALAR(session_data, '$.message_count'), '0') AS INT64) + 1
            ),
            last_activity = CURRENT_TIMESTAMP()
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            return True
            
        except Exception as e:
            error_message = str(e)
            # Handle BigQuery streaming buffer limitation gracefully
            if "streaming buffer" in error_message.lower() and "not supported" in error_message.lower():
                logger.warning(f"Cannot update session {session_id} in streaming buffer - this is expected for new sessions")
                return True  # Don't fail, just skip the update
            else:
                logger.error(f"Error incrementing message count for session {session_id}: {e}")
                return False
    
    async def _update_last_activity(self, session_id: str):
        """Update last activity timestamp"""
        query = f"""
        UPDATE `{self.table_ref}`
        SET last_activity = CURRENT_TIMESTAMP()
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        except Exception as e:
            error_message = str(e)
            # Handle BigQuery streaming buffer limitation gracefully
            if "streaming buffer" in error_message.lower() and "not supported" in error_message.lower():
                logger.warning(f"Cannot update last activity for session {session_id} in streaming buffer - this is expected for new sessions")
            else:
                logger.error(f"Error updating last activity for session {session_id}: {e}")


# Factory function for session manager
def create_session_manager(
    project_id: str,
    dataset_id: str,
    table_id: str = "sessions",
    location: str = "US",
    ttl: int = 3600
) -> BigQuerySessionManager:
    """Create BigQuery session manager"""
    return BigQuerySessionManager(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        location=location,
        default_ttl=ttl
    )
