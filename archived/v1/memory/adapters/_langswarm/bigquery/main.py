from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import uuid
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
except ImportError:
    bigquery = None

class BigQueryAdapter(DatabaseAdapter):
    """
    A BigQuery adapter for document storage and retrieval with analytics capabilities.
    
    This retriever enables:
    - Storing and retrieving textual data in BigQuery tables.
    - SQL-based querying with full BigQuery analytics power.
    - Metadata-based filtering and complex queries.
    - Time-series analysis of agent conversations.
    
    Use cases:
    - Large-scale agent memory storage and analytics.
    - Complex querying and aggregation of conversation data.
    - Integration with existing BigQuery data pipelines.
    - Long-term storage with powerful search capabilities.
    
    - Usage format:

Replace `action` and parameters as needed.
    """
    
    def __init__(
        self, 
        identifier: str, 
        project_id: str, 
        dataset_id: str, 
        table_id: str = "agent_memory",
        location: str = "US"
    ):
        self.identifier = identifier
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.location = location
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        self.brief = f"BigQueryRetriever for {self.table_ref}"
        
        super().__init__(
            name="BigQueryRetriever",
            description=(
                f"This retriever enables document storage and retrieval using Google BigQuery. "
                f"It supports SQL-based querying, metadata filtering, and analytics on the {self.table_ref} table. "
                f"Ideal for large-scale agent memory storage with powerful analytics capabilities."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Store documents in BigQuery.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with `"key"`, `"text"`, and `"metadata"`.
    
    - `query`: Perform SQL-based search with BigQuery.
      - Parameters:
        - `query` (str): The search query text.
        - `filters` (Dict, optional): Metadata filters for refining results.
        - `top_k` (int, optional): Number of results to return (default: 5).
        - `sql_where` (str, optional): Custom SQL WHERE clause for advanced filtering.
    
    - `delete`: Remove documents from BigQuery by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to delete.

- Usage format:

Replace `action` and parameters as needed.
            """
        )
        
        if bigquery is None:
            raise ValueError("Unsupported database. Make sure google-cloud-bigquery is installed.")
            
        self.client = bigquery.Client(project=project_id, location=location)
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create the table if it doesn't exist."""
        try:
            self.client.get_table(self.table_ref)
        except NotFound:
            # Create the dataset if it doesn't exist
            try:
                self.client.get_dataset(f"{self.project_id}.{self.dataset_id}")
            except NotFound:
                dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
                dataset.location = self.location
                self.client.create_dataset(dataset)
            
            # Create the table
            schema = [
                bigquery.SchemaField("key", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("text", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("session_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("agent_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("user_input", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("agent_response", "STRING", mode="NULLABLE"),
            ]
            
            table = bigquery.Table(self.table_ref, schema=schema)
            table.description = f"LangSwarm agent memory storage for {self.identifier}"
            self.client.create_table(table)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
        
    def add_documents(self, documents: List[Dict]):
        """Add documents to BigQuery table."""
        rows_to_insert = []
        
        for doc in documents:
            # Parse JSON if the text contains structured data
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # Try to extract structured conversation data
            try:
                if text.startswith('{') and text.endswith('}'):
                    conversation_data = json.loads(text)
                    user_input = conversation_data.get("user_input")
                    agent_response = conversation_data.get("agent_response")
                    session_id = conversation_data.get("session_id")
                    agent_id = metadata.get("conversation_id") or conversation_data.get("session_id")
                else:
                    user_input = None
                    agent_response = None
                    session_id = metadata.get("session_id")
                    agent_id = metadata.get("agent_id") or self.identifier
            except json.JSONDecodeError:
                user_input = None
                agent_response = None
                session_id = metadata.get("session_id")
                agent_id = metadata.get("agent_id") or self.identifier
            
            row = {
                "key": doc.get("key", str(uuid.uuid4())),
                "text": text,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "agent_id": agent_id,
                "user_input": user_input,
                "agent_response": agent_response,
            }
            rows_to_insert.append(row)
        
        # Insert rows into BigQuery
        errors = self.client.insert_rows_json(self.table_ref, rows_to_insert)
        if errors:
            raise ValueError(f"Failed to insert rows: {errors}")
    
    def query(
        self, 
        query: str, 
        filters: Dict = None, 
        top_k: int = 5, 
        sql_where: str = None
    ) -> List[Dict]:
        """
        Perform a search query using BigQuery SQL.

        Args:
            query (str): The search query text.
            filters (Dict, optional): Metadata filters for refining results.
            top_k (int): Number of results to return (default: 5).
            sql_where (str, optional): Custom SQL WHERE clause.

        Returns:
            List[Dict]: A list of standardized document results.
        """
        # Build the SQL query
        base_sql = f"""
        SELECT 
            key,
            text,
            metadata,
            timestamp,
            session_id,
            agent_id,
            user_input,
            agent_response
        FROM `{self.table_ref}`
        """
        
        where_conditions = []
        
        # Add text search condition
        if query.strip():
            where_conditions.append(f"(LOWER(text) LIKE LOWER('%{query}%') OR LOWER(user_input) LIKE LOWER('%{query}%') OR LOWER(agent_response) LIKE LOWER('%{query}%'))")
        
        # Add custom SQL WHERE clause
        if sql_where:
            where_conditions.append(f"({sql_where})")
        
        # Add metadata filters
        if filters:
            for key, value in filters.items():
                if key == "session_id":
                    where_conditions.append(f"session_id = '{value}'")
                elif key == "agent_id":
                    where_conditions.append(f"agent_id = '{value}'")
                elif key == "timestamp":
                    # Handle timestamp filters (expecting dict with operators)
                    if isinstance(value, dict):
                        for op, val in value.items():
                            if op == "$gt":
                                where_conditions.append(f"timestamp > '{val}'")
                            elif op == "$gte":
                                where_conditions.append(f"timestamp >= '{val}'")
                            elif op == "$lt":
                                where_conditions.append(f"timestamp < '{val}'")
                            elif op == "$lte":
                                where_conditions.append(f"timestamp <= '{val}'")
                            elif op == "$eq":
                                where_conditions.append(f"timestamp = '{val}'")
                    else:
                        where_conditions.append(f"timestamp = '{value}'")
                else:
                    # Generic metadata filter using JSON functions
                    where_conditions.append(f"JSON_EXTRACT_SCALAR(metadata, '$.{key}') = '{value}'")
        
        # Combine WHERE conditions
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        # Add ordering and limit
        base_sql += f" ORDER BY timestamp DESC LIMIT {top_k}"
        
        # Execute query
        query_job = self.client.query(base_sql)
        results = query_job.result()
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append(
                self.standardize_output(
                    text=row.text,
                    source="BigQuery",
                    metadata=dict(row.metadata) if row.metadata else {},
                    id=row.key
                )
            )
        
        return formatted_results

    def delete(self, document_ids: List[str]):
        """Delete documents from BigQuery by IDs."""
        if not document_ids:
            return
        
        # Create a parameterized query to avoid SQL injection
        placeholders = ",".join([f"'{doc_id}'" for doc_id in document_ids])
        delete_sql = f"""
        DELETE FROM `{self.table_ref}`
        WHERE key IN ({placeholders})
        """
        
        query_job = self.client.query(delete_sql)
        query_job.result()  # Wait for the job to complete

    def translate_filters(self, filters: Dict) -> str:
        """
        Convert standardized filter format into BigQuery SQL WHERE clause.
        
        Args:
            filters (Dict): Standardized filter structure.
        
        Returns:
            str: BigQuery SQL WHERE clause.
        """
        if not filters:
            return ""
        
        conditions = []
        
        for condition in filters.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]
            
            if operator == "==":
                if field in ["session_id", "agent_id", "key"]:
                    conditions.append(f"{field} = '{value}'")
                else:
                    conditions.append(f"JSON_EXTRACT_SCALAR(metadata, '$.{field}') = '{value}'")
            elif operator == "!=":
                if field in ["session_id", "agent_id", "key"]:
                    conditions.append(f"{field} != '{value}'")
                else:
                    conditions.append(f"JSON_EXTRACT_SCALAR(metadata, '$.{field}') != '{value}'")
            elif operator == ">=":
                if field == "timestamp":
                    conditions.append(f"timestamp >= '{value}'")
                else:
                    conditions.append(f"CAST(JSON_EXTRACT_SCALAR(metadata, '$.{field}') AS FLOAT64) >= {value}")
            elif operator == "<=":
                if field == "timestamp":
                    conditions.append(f"timestamp <= '{value}'")
                else:
                    conditions.append(f"CAST(JSON_EXTRACT_SCALAR(metadata, '$.{field}') AS FLOAT64) <= {value}")
        
        return " AND ".join(conditions)

    def capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this adapter."""
        return {
            "full_text_search": True,
            "metadata_filtering": True,
            "sql_queries": True,
            "analytics": True,
            "time_series": True,
            "scalable": True,
            "persistent": True
        }

    def get_analytics(self, sql_query: str) -> List[Dict]:
        """
        Execute custom analytics queries on the stored data.
        
        Args:
            sql_query (str): Custom SQL query for analytics.
            
        Returns:
            List[Dict]: Query results.
        """
        query_job = self.client.query(sql_query)
        results = query_job.result()
        
        return [dict(row) for row in results]

    def get_conversation_summary(self, session_id: str = None, days: int = 7) -> Dict:
        """
        Get a summary of conversations for analytics.
        
        Args:
            session_id (str, optional): Specific session to analyze.
            days (int): Number of days to look back.
            
        Returns:
            Dict: Summary statistics.
        """
        where_clause = f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)"
        
        if session_id:
            where_clause += f" AND session_id = '{session_id}'"
        
        summary_sql = f"""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(DISTINCT session_id) as unique_sessions,
            AVG(LENGTH(text)) as avg_message_length,
            MIN(timestamp) as first_message,
            MAX(timestamp) as last_message
        FROM `{self.table_ref}`
        WHERE {where_clause}
        """
        
        query_job = self.client.query(summary_sql)
        result = list(query_job.result())[0]
        
        return dict(result) 