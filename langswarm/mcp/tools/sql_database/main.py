# langswarm/mcp/tools/sql_database/main.py

import os
import re
import json
import logging
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from pydantic import BaseModel, Field
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.mcp.tools._error_standards import (
    create_error_response, create_parameter_error, create_authentication_error,
    create_connection_error, ErrorTypes
)

# Optional database drivers
DATABASE_SUPPORT = {
    'sqlite': True,  # Always available
    'postgresql': False,
    'mysql': False,
    'oracle': False,
    'mssql': False
}

try:
    import psycopg2
    DATABASE_SUPPORT['postgresql'] = True
except ImportError:
    pass

try:
    import mysql.connector
    DATABASE_SUPPORT['mysql'] = True
except ImportError:
    pass

try:
    import cx_Oracle
    DATABASE_SUPPORT['oracle'] = True
except ImportError:
    pass

try:
    import pyodbc
    DATABASE_SUPPORT['mssql'] = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# === Configuration ===
DEFAULT_CONFIG = {
    "db_type": "sqlite",
    "allowed_operations": ["SELECT"],  # Very restrictive by default
    "max_rows": 1000,
    "timeout_seconds": 30,
    "enable_intent_parsing": True,
    "enable_query_logging": True,
    "allowed_tables": None,  # None = all tables allowed
    "blocked_keywords": ["DROP", "TRUNCATE", "ALTER", "CREATE", "DELETE"],
    "enable_explain_only": False  # If True, only EXPLAIN queries allowed
}

# === Security Configuration ===
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "xp_", "sp_", "SHUTDOWN", "KILL", "LOAD_FILE",
    "INTO OUTFILE", "INTO DUMPFILE", "LOAD DATA", "BACKUP", "RESTORE"
]

SAFE_OPERATIONS = ["SELECT", "INSERT", "UPDATE", "EXPLAIN", "DESCRIBE", "SHOW"]

# === Schemas ===
class QueryInput(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters for prepared statements")
    limit: Optional[int] = Field(None, description="Maximum number of rows to return")
    explain_only: Optional[bool] = Field(False, description="Only explain the query, don't execute")

class QueryOutput(BaseModel):
    success: bool
    query: str
    results: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    columns: Optional[List[str]] = None
    execution_time_ms: float = 0
    query_plan: Optional[str] = None
    warnings: Optional[List[str]] = None
    error: Optional[str] = None

class DatabaseInfoInput(BaseModel):
    include_schema: Optional[bool] = Field(True, description="Include table schema information")
    table_pattern: Optional[str] = Field(None, description="Pattern to filter table names")

class DatabaseInfoOutput(BaseModel):
    success: bool
    database_type: str
    database_name: str
    tables: List[Dict[str, Any]]
    total_tables: int
    connection_info: Dict[str, Any]
    error: Optional[str] = None

class IntentQueryInput(BaseModel):
    intent: str = Field(..., description="Natural language description of what data you need")
    context: Optional[str] = Field(None, description="Additional context about the query purpose")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Additional constraints or parameters")

class IntentQueryOutput(BaseModel):
    success: bool
    intent: str
    generated_query: str
    results: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    columns: Optional[List[str]] = None
    execution_time_ms: float = 0
    explanation: Optional[str] = None
    warnings: Optional[List[str]] = None
    error: Optional[str] = None

# === Security & Query Validation ===

class QueryValidator:
    """Validates and sanitizes SQL queries based on security configuration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allowed_operations = set(op.upper() for op in config.get('allowed_operations', ['SELECT']))
        self.blocked_keywords = set(kw.upper() for kw in config.get('blocked_keywords', DANGEROUS_KEYWORDS))
        self.allowed_tables = config.get('allowed_tables')
        
    def validate_query(self, query: str) -> Tuple[bool, str, List[str]]:
        """
        Validate query against security rules.
        Returns: (is_valid, sanitized_query, warnings)
        """
        warnings = []
        original_query = query
        query = query.strip()
        
        if not query:
            return False, "", ["Empty query provided"]
        
        # Remove comments to prevent comment-based injection
        query = self._remove_sql_comments(query)
        
        # Check for blocked keywords
        query_upper = query.upper()
        for keyword in self.blocked_keywords:
            if keyword in query_upper:
                return False, "", [f"Blocked keyword '{keyword}' found in query"]
        
        # Extract and validate operation
        operation = self._extract_operation(query)
        if operation not in self.allowed_operations:
            allowed_list = ", ".join(self.allowed_operations)
            return False, "", [f"Operation '{operation}' not allowed. Allowed: {allowed_list}"]
        
        # Validate table access if restricted
        if self.allowed_tables is not None:
            tables_in_query = self._extract_table_names(query)
            for table in tables_in_query:
                if table not in self.allowed_tables:
                    return False, "", [f"Access to table '{table}' not allowed"]
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r';\s*\w+',  # Multiple statements
            r'--\s*\w+',  # SQL comments with content
            r'/\*.*?\*/',  # Multi-line comments
            r'\bUNION\s+SELECT\b',  # Union injection
            r'\bOR\s+1\s*=\s*1\b',  # Classic injection
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                warnings.append(f"Potentially dangerous pattern detected: {pattern}")
        
        # Validate query structure
        if not self._is_valid_sql_structure(query):
            return False, "", ["Invalid SQL query structure"]
        
        return True, query, warnings
    
    def _remove_sql_comments(self, query: str) -> str:
        """Remove SQL comments from query"""
        # Remove single-line comments
        query = re.sub(r'--.*?$', '', query, flags=re.MULTILINE)
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        return query
    
    def _extract_operation(self, query: str) -> str:
        """Extract the primary SQL operation from query"""
        query = query.strip().upper()
        # Handle WITH clauses
        if query.startswith('WITH'):
            # Find the main operation after WITH clause
            match = re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', query)
            return match.group(1) if match else "UNKNOWN"
        
        # Direct operation
        for op in SAFE_OPERATIONS + list(DANGEROUS_KEYWORDS):
            if query.startswith(op):
                return op
        return "UNKNOWN"
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query"""
        # This is a simplified extraction - could be enhanced with proper SQL parsing
        tables = []
        
        # Find FROM clauses
        from_matches = re.finditer(r'\bFROM\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)', query, re.IGNORECASE)
        for match in from_matches:
            tables.append(match.group(1).lower())
        
        # Find JOIN clauses
        join_matches = re.finditer(r'\bJOIN\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)', query, re.IGNORECASE)
        for match in join_matches:
            tables.append(match.group(1).lower())
        
        # Find INSERT/UPDATE tables
        insert_matches = re.finditer(r'\b(?:INSERT\s+INTO|UPDATE)\s+([a-zA-Z_]\w*)', query, re.IGNORECASE)
        for match in insert_matches:
            tables.append(match.group(1).lower())
        
        return list(set(tables))  # Remove duplicates
    
    def _is_valid_sql_structure(self, query: str) -> bool:
        """Basic validation of SQL query structure"""
        # Check for balanced parentheses
        open_count = query.count('(')
        close_count = query.count(')')
        if open_count != close_count:
            return False
        
        # Check for balanced quotes
        single_quotes = query.count("'")
        double_quotes = query.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return False
        
        return True

# === Database Connection Management ===

class DatabaseConnection:
    """Manages database connections with support for multiple database types"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_type = config.get('db_type', 'sqlite').lower()
        self.connection = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            if self.db_type == 'sqlite':
                return self._connect_sqlite()
            elif self.db_type == 'postgresql':
                return self._connect_postgresql()
            elif self.db_type == 'mysql':
                return self._connect_mysql()
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def _connect_sqlite(self) -> bool:
        """Connect to SQLite database"""
        db_path = self.config.get('db_path')
        if not db_path:
            raise ValueError("db_path is required for SQLite")
        
        # Validate path exists and is accessible
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        self.connection = sqlite3.connect(
            db_path,
            timeout=self.config.get('timeout_seconds', 30)
        )
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
        return True
    
    def _connect_postgresql(self) -> bool:
        """Connect to PostgreSQL database"""
        if not DATABASE_SUPPORT['postgresql']:
            raise ImportError("PostgreSQL support requires: pip install psycopg2-binary")
        
        conn_params = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 5432),
            'database': self.config.get('database'),
            'user': self.config.get('user'),
            'password': self.config.get('password'),
        }
        
        # Remove None values
        conn_params = {k: v for k, v in conn_params.items() if v is not None}
        
        self.connection = psycopg2.connect(**conn_params)
        return True
    
    def _connect_mysql(self) -> bool:
        """Connect to MySQL database"""
        if not DATABASE_SUPPORT['mysql']:
            raise ImportError("MySQL support requires: pip install mysql-connector-python")
        
        conn_params = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 3306),
            'database': self.config.get('database'),
            'user': self.config.get('user'),
            'password': self.config.get('password'),
        }
        
        # Remove None values
        conn_params = {k: v for k, v in conn_params.items() if v is not None}
        
        self.connection = mysql.connector.connect(**conn_params)
        return True
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """
        Execute SQL query and return results.
        Returns: (rows, columns, execution_time_ms)
        """
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        start_time = datetime.now()
        
        try:
            cursor = self.connection.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            # Get column names
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch results
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    if hasattr(row, '_asdict'):  # sqlite3.Row
                        results.append(dict(row))
                    else:  # Regular tuple
                        results.append(dict(zip(columns, row)))
            else:
                # Non-SELECT query (INSERT, UPDATE, etc.)
                columns = []
                results = []
                self.connection.commit()
            
            cursor.close()
            
        except Exception as e:
            if hasattr(self.connection, 'rollback'):
                self.connection.rollback()
            raise e
        
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return results, columns, execution_time_ms
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database structure"""
        if self.db_type == 'sqlite':
            return self._get_sqlite_info()
        elif self.db_type == 'postgresql':
            return self._get_postgresql_info()
        elif self.db_type == 'mysql':
            return self._get_mysql_info()
        else:
            return {}
    
    def _get_sqlite_info(self) -> Dict[str, Any]:
        """Get SQLite database information"""
        cursor = self.connection.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables = []
        for table_name in table_names:
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'nullable': not row[3],
                    'primary_key': bool(row[5])
                })
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            tables.append({
                'name': table_name,
                'columns': columns,
                'row_count': row_count
            })
        
        cursor.close()
        
        return {
            'database_type': 'sqlite',
            'database_name': self.config.get('db_path', 'unknown'),
            'tables': tables,
            'total_tables': len(tables)
        }
    
    def _get_postgresql_info(self) -> Dict[str, Any]:
        """Get PostgreSQL database information"""
        cursor = self.connection.cursor()
        
        # Get tables from public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables = []
        for table_name in table_names:
            # Get column info
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3]
                })
            
            # Get row count (approximate)
            cursor.execute(f"SELECT reltuples::BIGINT FROM pg_class WHERE relname = %s", (table_name,))
            result = cursor.fetchone()
            row_count = int(result[0]) if result else 0
            
            tables.append({
                'name': table_name,
                'columns': columns,
                'row_count': row_count
            })
        
        cursor.close()
        
        return {
            'database_type': 'postgresql',
            'database_name': self.config.get('database', 'unknown'),
            'tables': tables,
            'total_tables': len(tables)
        }
    
    def _get_mysql_info(self) -> Dict[str, Any]:
        """Get MySQL database information"""
        cursor = self.connection.cursor()
        
        # Get tables
        cursor.execute("SHOW TABLES")
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables = []
        for table_name in table_names:
            # Get column info
            cursor.execute(f"DESCRIBE {table_name}")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'key': row[3],
                    'default': row[4]
                })
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            tables.append({
                'name': table_name,
                'columns': columns,
                'row_count': row_count
            })
        
        cursor.close()
        
        return {
            'database_type': 'mysql',
            'database_name': self.config.get('database', 'unknown'),
            'tables': tables,
            'total_tables': len(tables)
        }
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

# === Intent-Based Query Generation ===
# NOTE: Intent handling is now done in workflows via dedicated agents.
# The IntentQueryGenerator class has been removed as it's redundant.

# Legacy class kept for reference (will be removed in next version)
class IntentQueryGenerator:
    """Generates SQL queries from natural language intents"""
    
    def __init__(self, db_connection: DatabaseConnection, config: Dict[str, Any]):
        self.db_connection = db_connection
        self.config = config
        self.database_info = None
        
    def get_database_schema(self) -> str:
        """Get a text representation of the database schema for context"""
        if not self.database_info:
            self.database_info = self.db_connection.get_database_info()
        
        schema_text = f"Database: {self.database_info.get('database_name', 'unknown')}\n"
        schema_text += f"Type: {self.database_info.get('database_type', 'unknown')}\n\n"
        
        for table in self.database_info.get('tables', []):
            schema_text += f"Table: {table['name']} ({table.get('row_count', 0)} rows)\n"
            for column in table.get('columns', []):
                nullable = "NULL" if column.get('nullable', True) else "NOT NULL"
                pk = " (PRIMARY KEY)" if column.get('primary_key', False) else ""
                schema_text += f"  - {column['name']}: {column['type']} {nullable}{pk}\n"
            schema_text += "\n"
        
        return schema_text
    
    def generate_query_from_intent(self, intent: str, context: Optional[str] = None, constraints: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Generate SQL query from natural language intent.
        Returns: (sql_query, explanation)
        
        Note: This is a simplified implementation. In production, you might want to integrate
        with an LLM or more sophisticated NLP system.
        """
        
        # Get database schema for context
        schema = self.get_database_schema()
        
        # Simple intent parsing patterns
        intent_lower = intent.lower()
        
        # Detect query type
        if any(word in intent_lower for word in ['find', 'get', 'show', 'list', 'count', 'how many']):
            return self._generate_select_query(intent, context, constraints, schema)
        elif any(word in intent_lower for word in ['add', 'insert', 'create']):
            return self._generate_insert_query(intent, context, constraints, schema)
        elif any(word in intent_lower for word in ['update', 'change', 'modify']):
            return self._generate_update_query(intent, context, constraints, schema)
        else:
            # Default to SELECT
            return self._generate_select_query(intent, context, constraints, schema)
    
    def _generate_select_query(self, intent: str, context: Optional[str], constraints: Optional[Dict[str, Any]], schema: str) -> Tuple[str, str]:
        """Generate SELECT query from intent"""
        
        # This is a simplified implementation
        # In production, you'd use more sophisticated NLP or LLM integration
        
        intent_lower = intent.lower()
        
        # Try to identify table names in intent
        tables = []
        if self.database_info:
            for table in self.database_info.get('tables', []):
                table_name = table['name'].lower()
                if table_name in intent_lower or table_name.rstrip('s') in intent_lower:
                    tables.append(table['name'])
        
        if not tables:
            # Use first table as default
            if self.database_info and self.database_info.get('tables'):
                tables = [self.database_info['tables'][0]['name']]
            else:
                return "SELECT 1", "Unable to determine target table from intent"
        
        # Build basic SELECT query
        query = f"SELECT * FROM {tables[0]}"
        explanation = f"Selecting all columns from {tables[0]} table"
        
        # Add constraints if provided
        if constraints:
            where_conditions = []
            for key, value in constraints.items():
                if isinstance(value, str):
                    where_conditions.append(f"{key} = '{value}'")
                else:
                    where_conditions.append(f"{key} = {value}")
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
                explanation += f" with conditions: {', '.join(where_conditions)}"
        
        # Add LIMIT to prevent large result sets
        max_rows = self.config.get('max_rows', 1000)
        if 'limit' not in intent_lower:
            query += f" LIMIT {max_rows}"
            explanation += f" (limited to {max_rows} rows for safety)"
        
        return query, explanation
    
    def _generate_insert_query(self, intent: str, context: Optional[str], constraints: Optional[Dict[str, Any]], schema: str) -> Tuple[str, str]:
        """Generate INSERT query from intent"""
        return "-- INSERT queries require explicit column values", "INSERT operations require specific data values to be provided"
    
    def _generate_update_query(self, intent: str, context: Optional[str], constraints: Optional[Dict[str, Any]], schema: str) -> Tuple[str, str]:
        """Generate UPDATE query from intent"""
        return "-- UPDATE queries require explicit conditions", "UPDATE operations require specific conditions and values to be provided"

# === Core Handlers ===

async def execute_query(input_data: QueryInput, config: Dict[str, Any]) -> QueryOutput:
    """Execute a SQL query with security validation"""
    
    start_time = datetime.now()
    
    try:
        # Initialize validator and database connection
        validator = QueryValidator(config)
        db_conn = DatabaseConnection(config)
        
        # Validate query
        is_valid, sanitized_query, warnings = validator.validate_query(input_data.query)
        if not is_valid:
            return QueryOutput(
                success=False,
                query=input_data.query,
                error=f"Query validation failed: {'; '.join(warnings)}",
                warnings=warnings
            )
        
        # Connect to database
        if not db_conn.connect():
            return QueryOutput(
                success=False,
                query=input_data.query,
                error="Failed to connect to database"
            )
        
        try:
            # Execute query
            if input_data.explain_only or config.get('enable_explain_only', False):
                # Execute EXPLAIN instead of actual query
                explain_query = f"EXPLAIN QUERY PLAN {sanitized_query}"
                results, columns, execution_time = db_conn.execute_query(explain_query)
                
                return QueryOutput(
                    success=True,
                    query=sanitized_query,
                    results=results,
                    row_count=len(results),
                    columns=columns,
                    execution_time_ms=execution_time,
                    query_plan=json.dumps(results, indent=2),
                    warnings=warnings
                )
            else:
                # Execute actual query
                results, columns, execution_time = db_conn.execute_query(
                    sanitized_query, 
                    input_data.parameters
                )
                
                # Apply row limit
                max_rows = input_data.limit or config.get('max_rows', 1000)
                if len(results) > max_rows:
                    results = results[:max_rows]
                    warnings.append(f"Results truncated to {max_rows} rows")
                
                return QueryOutput(
                    success=True,
                    query=sanitized_query,
                    results=results,
                    row_count=len(results),
                    columns=columns,
                    execution_time_ms=execution_time,
                    warnings=warnings
                )
        
        finally:
            db_conn.close()
    
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return QueryOutput(
            success=False,
            query=input_data.query,
            error=str(e),
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )

async def get_database_info(input_data: DatabaseInfoInput, config: Dict[str, Any]) -> DatabaseInfoOutput:
    """Get information about the database structure"""
    
    try:
        db_conn = DatabaseConnection(config)
        
        if not db_conn.connect():
            return DatabaseInfoOutput(
                success=False,
                database_type="unknown",
                database_name="unknown",
                tables=[],
                total_tables=0,
                connection_info={},
                error="Failed to connect to database"
            )
        
        try:
            info = db_conn.get_database_info()
            
            # Filter tables by pattern if provided
            tables = info.get('tables', [])
            if input_data.table_pattern:
                pattern = input_data.table_pattern.lower()
                tables = [t for t in tables if pattern in t['name'].lower()]
            
            # Remove schema details if not requested
            if not input_data.include_schema:
                for table in tables:
                    table.pop('columns', None)
            
            return DatabaseInfoOutput(
                success=True,
                database_type=info.get('database_type', 'unknown'),
                database_name=info.get('database_name', 'unknown'),
                tables=tables,
                total_tables=len(tables),
                connection_info={
                    'db_type': config.get('db_type'),
                    'allowed_operations': config.get('allowed_operations', []),
                    'max_rows': config.get('max_rows', 1000)
                }
            )
        
        finally:
            db_conn.close()
    
    except Exception as e:
        logger.error(f"Database info retrieval failed: {e}")
        return DatabaseInfoOutput(
            success=False,
            database_type="unknown",
            database_name="unknown",
            tables=[],
            total_tables=0,
            connection_info={},
            error=str(e)
        )

async def intent_query(input_data: IntentQueryInput, config: Dict[str, Any]) -> IntentQueryOutput:
    """Execute query based on natural language intent"""
    
    start_time = datetime.now()
    
    try:
        # Check if intent parsing is enabled
        if not config.get('enable_intent_parsing', True):
            return IntentQueryOutput(
                success=False,
                intent=input_data.intent,
                generated_query="",
                error="Intent-based querying is disabled"
            )
        
        db_conn = DatabaseConnection(config)
        
        if not db_conn.connect():
            return IntentQueryOutput(
                success=False,
                intent=input_data.intent,
                generated_query="",
                error="Failed to connect to database"
            )
        
        try:
            # Generate query from intent
            generator = IntentQueryGenerator(db_conn, config)
            generated_query, explanation = generator.generate_query_from_intent(
                input_data.intent,
                input_data.context,
                input_data.constraints
            )
            
            # Validate generated query
            validator = QueryValidator(config)
            is_valid, sanitized_query, warnings = validator.validate_query(generated_query)
            
            if not is_valid:
                return IntentQueryOutput(
                    success=False,
                    intent=input_data.intent,
                    generated_query=generated_query,
                    error=f"Generated query validation failed: {'; '.join(warnings)}",
                    explanation=explanation,
                    warnings=warnings
                )
            
            # Execute the generated query
            results, columns, execution_time = db_conn.execute_query(sanitized_query)
            
            # Apply row limit
            max_rows = config.get('max_rows', 1000)
            if len(results) > max_rows:
                results = results[:max_rows]
                warnings.append(f"Results truncated to {max_rows} rows")
            
            return IntentQueryOutput(
                success=True,
                intent=input_data.intent,
                generated_query=sanitized_query,
                results=results,
                row_count=len(results),
                columns=columns,
                execution_time_ms=execution_time,
                explanation=explanation,
                warnings=warnings
            )
        
        finally:
            db_conn.close()
    
    except Exception as e:
        logger.error(f"Intent query failed: {e}")
        return IntentQueryOutput(
            success=False,
            intent=input_data.intent,
            generated_query="",
            error=str(e),
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )

# === MCP Server ===
server = BaseMCPToolServer(
    name="sql_database",
    description="Secure SQL database querying tool with intent-based natural language support",
    local_mode=True
)

# Add operations
server.add_task(
    name="execute_query",
    description="Execute a SQL query with security validation and restrictions",
    input_model=QueryInput,
    output_model=QueryOutput,
    handler=lambda input_data: execute_query(input_data, DEFAULT_CONFIG)
)

server.add_task(
    name="get_database_info",
    description="Get information about database structure, tables, and schema",
    input_model=DatabaseInfoInput,
    output_model=DatabaseInfoOutput,
    handler=lambda input_data: get_database_info(input_data, DEFAULT_CONFIG)
)

# NOTE: intent_query task removed - intent handling now done in workflows
# server.add_task(
#     name="intent_query",
#     description="Execute queries based on natural language intent with automatic SQL generation",
#     input_model=IntentQueryInput,
#     output_model=IntentQueryOutput,
#     handler=lambda input_data: intent_query(input_data, DEFAULT_CONFIG)
# )

# Create FastAPI app
app = server.build_app()

# === LangChain-Compatible Tool Class ===
try:
    from langswarm.synapse.tools.base import BaseTool
    
    class SQLDatabaseMCPTool(BaseTool):
        """
        Secure SQL Database MCP tool with intent-based querying and configurable restrictions.
        
        Features:
        - Multi-database support (SQLite, PostgreSQL, MySQL)
        - Security validation and query restrictions
        - Intent-based natural language querying
        - Configurable operation whitelisting
        - Query logging and monitoring
        """
        _bypass_pydantic = True
        
        def __init__(self, identifier: str):
            super().__init__(
                name="SQL Database Query Tool",
                description="Execute secure SQL queries with intent-based natural language support",
                instruction="""Use this tool to query SQL databases safely with built-in security restrictions.

SECURITY FEATURES:
- Only allowed operations are permitted (configurable)
- Dangerous keywords are blocked (DROP, DELETE, etc.)
- Query validation and sanitization
- Row limits and timeouts
- Table access restrictions

USAGE PATTERNS:

1. Direct SQL Query:
{
  "tool": "sql_database",
  "method": "execute_query",
  "params": {
    "query": "SELECT * FROM users WHERE active = 1 LIMIT 10"
  }
}

2. Intent-Based Query (Recommended):
{
  "tool": "sql_database",
  "intent": "show me all active users from the last month",
  "context": "user management dashboard"
}

3. Database Information:
{
  "tool": "sql_database", 
  "method": "get_database_info",
  "params": {"include_schema": true}
}

PARAMETERS:
- query: SQL query string (validated for security)
- intent: Natural language description for auto-generation
- parameters: Parameters for prepared statements
- limit: Maximum rows to return
- explain_only: Only show query plan, don't execute

SECURITY: Tool automatically blocks dangerous operations and validates all queries.""",
                identifier=identifier,
                brief="Secure SQL database querying with intent-based natural language support"
            )
            object.__setattr__(self, 'server', server)
            object.__setattr__(self, 'config', DEFAULT_CONFIG.copy())
        
        def configure(self, config: dict):
            """Configure the SQL tool with database connection and security settings"""
            # Merge with default config
            updated_config = DEFAULT_CONFIG.copy()
            updated_config.update(config)
            object.__setattr__(self, 'config', updated_config)
            
            # Validate configuration
            self._validate_config(updated_config)
        
        def _validate_config(self, config: Dict[str, Any]):
            """Validate tool configuration"""
            db_type = config.get('db_type', 'sqlite')
            
            if db_type not in DATABASE_SUPPORT:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            if not DATABASE_SUPPORT[db_type]:
                raise ImportError(f"Database type '{db_type}' requires additional dependencies")
            
            if db_type == 'sqlite':
                db_path = config.get('db_path')
                if not db_path:
                    raise ValueError("db_path is required for SQLite databases")
                if not os.path.exists(db_path):
                    raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        async def run_async(self, input_data=None):
            """Unified async execution method"""
            try:
                # Parse input and determine method
                if isinstance(input_data, str):
                    # Simple string - treat as intent
                    method = "intent_query"
                    params = {"intent": input_data}
                elif isinstance(input_data, dict):
                    # Check for common parameter issues
                    if "sql" in input_data and "query" not in input_data:
                        return create_parameter_error(
                            "sql", "query (SQL string)", input_data.get("sql"),
                            "sql_database", "execute_query"
                        )
                    
                    # Determine method from input
                    if "method" in input_data and "params" in input_data:
                        method = input_data["method"]
                        params = input_data["params"]
                    elif "intent" in input_data:
                        method = "intent_query"
                        params = input_data
                    elif "query" in input_data:
                        method = "execute_query"
                        params = input_data
                    elif "include_schema" in input_data or "table_pattern" in input_data:
                        method = "get_database_info"
                        params = input_data
                    else:
                        return create_error_response(
                            "Cannot determine method from input. Provide 'query' for SQL, 'intent' for natural language, or 'method'/'params'",
                            ErrorTypes.PARAMETER_VALIDATION,
                            "sql_database"
                        )
                else:
                    return create_error_response(
                        f"Unsupported input type: {type(input_data)}",
                        ErrorTypes.PARAMETER_VALIDATION,
                        "sql_database"
                    )
                
                # Route to appropriate handler
                if method == "execute_query":
                    input_obj = QueryInput(**params)
                    result = await execute_query(input_obj, self.config)
                elif method == "get_database_info":
                    input_obj = DatabaseInfoInput(**params)
                    result = await get_database_info(input_obj, self.config)
                elif method == "intent_query":
                    input_obj = IntentQueryInput(**params)
                    result = await intent_query(input_obj, self.config)
                else:
                    available_methods = ["execute_query", "get_database_info", "intent_query"]
                    return create_error_response(
                        f"Unknown method: {method}. Available: {available_methods}",
                        ErrorTypes.PARAMETER_VALIDATION,
                        "sql_database"
                    )
                
                return result.dict()
                
            except Exception as e:
                logger.error(f"SQL database tool execution failed: {e}")
                return create_error_response(
                    str(e), ErrorTypes.GENERAL, "sql_database"
                )
        
        def run(self, input_data=None):
            """Synchronous wrapper for async execution"""
            import asyncio
            
            # Handle different event loop scenarios
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, need to run in thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.run_async(input_data))
                        return future.result()
                else:
                    # No running loop, can use asyncio.run directly
                    return asyncio.run(self.run_async(input_data))
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(self.run_async(input_data))

except ImportError:
    SQLDatabaseMCPTool = None
    logger.warning("SQL Database MCP tool class not available - BaseTool import failed")

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        
        # Print supported database types
        print("\nSupported database types:")
        for db_type, supported in DATABASE_SUPPORT.items():
            status = "✅" if supported else "❌"
            print(f"  {status} {db_type}")
    else:
        uvicorn.run("langswarm.mcp.tools.sql_database.main:app", host="0.0.0.0", port=4022, reload=True)
