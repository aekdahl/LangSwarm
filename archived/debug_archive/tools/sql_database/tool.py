#!/usr/bin/env python3
"""
SQL Database Debug Tool

A debug-specific implementation of SQL database operations for testing
and debugging purposes with comprehensive tracing and error handling.
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# Import LangSwarm components
from langswarm.tools.base import BaseTool, ToolResult
from langswarm.core.errors import ConfigurationError, ValidationError


@dataclass
class SQLQueryResult:
    """Result from SQL query execution"""
    query: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time_ms: float
    rows_affected: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "rows_affected": self.rows_affected
        }


class SQLDatabaseTool(BaseTool):
    """
    Debug-focused SQL Database Tool
    
    This tool provides SQL database operations with comprehensive debugging,
    tracing, and error handling for testing purposes. Supports multiple
    database backends including SQLite, PostgreSQL, and MySQL.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SQL Database Tool"""
        super().__init__(
            tool_id="sql_database",
            name="SQL Database Tool", 
            description="Debug-focused SQL database operations and analysis",
            config=config
        )
        
        # Database configuration
        self.db_type = self.config.get('db_type', 'sqlite')
        self.connection_string = self.config.get('connection_string')
        self.database_path = self.config.get('database_path', 'debug_test.db')
        
        # Connection settings
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.database_name = self.config.get('database_name', 'test_db')
        
        # Query settings
        self.query_timeout = self.config.get('query_timeout', 30)
        self.max_rows = self.config.get('max_rows', 1000)
        
        # Debug settings
        self.debug_mode = self.config.get('debug_mode', True)
        self.trace_queries = self.config.get('trace_queries', True)
        self.safe_mode = self.config.get('safe_mode', True)  # Prevents destructive operations
        
        # Connection pool
        self._connection = None
        
        self._validate_config()
        self._setup_test_data()
    
    def _validate_config(self):
        """Validate configuration"""
        supported_db_types = ['sqlite', 'postgresql', 'mysql']
        if self.db_type not in supported_db_types:
            raise ConfigurationError(
                f"Unsupported database type: {self.db_type}. "
                f"Supported types: {supported_db_types}"
            )
        
        if self.db_type == 'sqlite':
            # Ensure database directory exists
            db_path = Path(self.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        elif self.db_type in ['postgresql', 'mysql']:
            if not all([self.host, self.username, self.database_name]):
                raise ConfigurationError(
                    f"For {self.db_type}, host, username, and database_name are required"
                )
    
    def _setup_test_data(self):
        """Set up test data for debugging purposes"""
        if self.db_type == 'sqlite':
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()
                
                # Create test tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        department TEXT,
                        salary REAL,
                        hire_date TEXT,
                        active BOOLEAN DEFAULT 1
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS departments (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        budget REAL,
                        manager_id INTEGER
                    )
                """)
                
                # Insert sample data if tables are empty
                cursor.execute("SELECT COUNT(*) FROM employees")
                if cursor.fetchone()[0] == 0:
                    sample_employees = [
                        (1, 'Alice Johnson', 'Engineering', 95000, '2022-01-15', 1),
                        (2, 'Bob Smith', 'Marketing', 75000, '2021-06-01', 1),
                        (3, 'Carol Davis', 'Engineering', 105000, '2020-03-10', 1),
                        (4, 'David Wilson', 'Sales', 85000, '2022-08-20', 1),
                        (5, 'Eve Brown', 'HR', 70000, '2021-11-05', 0),
                        (6, 'Frank Miller', 'Engineering', 98000, '2023-02-14', 1),
                        (7, 'Grace Lee', 'Marketing', 72000, '2022-04-18', 1),
                        (8, 'Henry Taylor', 'Sales', 88000, '2021-09-12', 1)
                    ]
                    
                    cursor.executemany(
                        "INSERT INTO employees (id, name, department, salary, hire_date, active) VALUES (?, ?, ?, ?, ?, ?)",
                        sample_employees
                    )
                
                cursor.execute("SELECT COUNT(*) FROM departments")
                if cursor.fetchone()[0] == 0:
                    sample_departments = [
                        (1, 'Engineering', 500000, 1),
                        (2, 'Marketing', 200000, 2),
                        (3, 'Sales', 300000, 4),
                        (4, 'HR', 150000, 5)
                    ]
                    
                    cursor.executemany(
                        "INSERT INTO departments (id, name, budget, manager_id) VALUES (?, ?, ?, ?)",
                        sample_departments
                    )
                
                conn.commit()
                conn.close()
                
                self.logger.info("Test data setup completed for SQLite database")
                
            except Exception as e:
                self.logger.error(f"Failed to setup test data: {e}")
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> SQLQueryResult:
        """
        Execute SQL query
        
        Args:
            query: SQL query string
            params: Query parameters for prepared statements
        
        Returns:
            SQLQueryResult with query results and metadata
        """
        start_time = datetime.now()
        params = params or []
        
        self.logger.info(f"Executing SQL query: {query[:100]}...")
        
        # Safety check for destructive operations
        if self.safe_mode:
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
            query_upper = query.upper().strip()
            for keyword in dangerous_keywords:
                if query_upper.startswith(keyword):
                    return SQLQueryResult(
                        query=query,
                        results=[],
                        metadata={
                            "error": f"Dangerous operation '{keyword}' blocked by safe mode",
                            "safe_mode": True
                        },
                        execution_time_ms=0,
                        rows_affected=0
                    )
        
        try:
            if self.db_type == 'sqlite':
                result = await self._execute_sqlite_query(query, params)
            elif self.db_type == 'postgresql':
                result = await self._execute_postgresql_query(query, params)
            elif self.db_type == 'mysql':
                result = await self._execute_mysql_query(query, params)
            else:
                raise ConfigurationError(f"Unsupported database type: {self.db_type}")
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            result.execution_time_ms = execution_time_ms
            
            if self.trace_queries:
                self.logger.debug(f"Query executed in {execution_time_ms:.2f}ms, {result.rows_affected} rows affected")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return SQLQueryResult(
                query=query,
                results=[],
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "db_type": self.db_type
                },
                execution_time_ms=execution_time_ms,
                rows_affected=0
            )
    
    async def _execute_sqlite_query(self, query: str, params: List) -> SQLQueryResult:
        """Execute query on SQLite database"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            
            # Get results for SELECT queries
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                rows_affected = len(results)
            else:
                results = []
                rows_affected = cursor.rowcount
                conn.commit()
            
            return SQLQueryResult(
                query=query,
                results=results[:self.max_rows],  # Limit results
                metadata={
                    "db_type": "sqlite",
                    "database_path": self.database_path,
                    "total_rows": len(results) if query.strip().upper().startswith('SELECT') else rows_affected,
                    "limited": len(results) > self.max_rows
                },
                execution_time_ms=0,  # Will be set by caller
                rows_affected=rows_affected
            )
            
        finally:
            conn.close()
    
    async def _execute_postgresql_query(self, query: str, params: List) -> SQLQueryResult:
        """Execute query on PostgreSQL database"""
        try:
            import asyncpg
        except ImportError:
            raise ConfigurationError(
                "PostgreSQL support requires asyncpg. Install with: pip install asyncpg"
            )
        
        # Build connection string
        conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port or 5432}/{self.database_name}"
        
        conn = await asyncpg.connect(conn_str)
        
        try:
            if query.strip().upper().startswith('SELECT'):
                rows = await conn.fetch(query, *params)
                results = [dict(row) for row in rows]
                rows_affected = len(results)
            else:
                result = await conn.execute(query, *params)
                results = []
                # Parse rows affected from result string (e.g., "INSERT 0 5")
                rows_affected = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
            
            return SQLQueryResult(
                query=query,
                results=results[:self.max_rows],
                metadata={
                    "db_type": "postgresql",
                    "host": self.host,
                    "database": self.database_name,
                    "total_rows": len(results) if query.strip().upper().startswith('SELECT') else rows_affected,
                    "limited": len(results) > self.max_rows
                },
                execution_time_ms=0,
                rows_affected=rows_affected
            )
            
        finally:
            await conn.close()
    
    async def _execute_mysql_query(self, query: str, params: List) -> SQLQueryResult:
        """Execute query on MySQL database"""
        try:
            import aiomysql
        except ImportError:
            raise ConfigurationError(
                "MySQL support requires aiomysql. Install with: pip install aiomysql"
            )
        
        conn = await aiomysql.connect(
            host=self.host,
            port=self.port or 3306,
            user=self.username,
            password=self.password,
            db=self.database_name
        )
        
        try:
            cursor = await conn.cursor()
            
            await cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                rows = await cursor.fetchall()
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]
                rows_affected = len(results)
            else:
                results = []
                rows_affected = cursor.rowcount
                await conn.commit()
            
            return SQLQueryResult(
                query=query,
                results=results[:self.max_rows],
                metadata={
                    "db_type": "mysql",
                    "host": self.host,
                    "database": self.database_name,
                    "total_rows": len(results) if query.strip().upper().startswith('SELECT') else rows_affected,
                    "limited": len(results) > self.max_rows
                },
                execution_time_ms=0,
                rows_affected=rows_affected
            )
            
        finally:
            await conn.ensure_closed()
    
    async def execute(self, method: str, params: Dict[str, Any]) -> ToolResult:
        """
        Execute tool method
        
        Supported methods:
        - query: Execute SQL query
        - health_check: Check database connection and health
        - get_schema: Get database schema information
        - get_tables: List all tables in database
        - analyze_table: Get detailed table information
        """
        
        try:
            if method == "query":
                query = params.get("query")
                if not query:
                    return ToolResult(
                        success=False,
                        data={"error": "Query parameter is required"},
                        metadata={"method": method}
                    )
                
                query_params = params.get("params", [])
                result = await self.execute_query(query, query_params)
                
                return ToolResult(
                    success=len(result.metadata.get("error", "")) == 0,
                    data=result.to_dict(),
                    metadata={
                        "method": method,
                        "execution_time_ms": result.execution_time_ms,
                        "rows_affected": result.rows_affected
                    }
                )
            
            elif method == "health_check":
                health_result = await self._health_check()
                return ToolResult(
                    success=health_result["healthy"],
                    data=health_result,
                    metadata={"method": method}
                )
            
            elif method == "get_schema":
                schema_result = await self._get_schema()
                return ToolResult(
                    success="error" not in schema_result,
                    data=schema_result,
                    metadata={"method": method}
                )
            
            elif method == "get_tables":
                tables_result = await self._get_tables()
                return ToolResult(
                    success="error" not in tables_result,
                    data=tables_result,
                    metadata={"method": method}
                )
            
            elif method == "analyze_table":
                table_name = params.get("table_name")
                if not table_name:
                    return ToolResult(
                        success=False,
                        data={"error": "table_name parameter is required"},
                        metadata={"method": method}
                    )
                
                analysis_result = await self._analyze_table(table_name)
                return ToolResult(
                    success="error" not in analysis_result,
                    data=analysis_result,
                    metadata={"method": method}
                )
            
            else:
                return ToolResult(
                    success=False,
                    data={"error": f"Unknown method: {method}"},
                    metadata={"method": method}
                )
                
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                success=False,
                data={"error": str(e), "error_type": type(e).__name__},
                metadata={"method": method}
            )
    
    async def _health_check(self) -> Dict[str, Any]:
        """Check database connection and health"""
        checks = {
            "database_accessible": False,
            "test_query_successful": False,
            "test_data_available": False
        }
        
        try:
            # Test basic connection
            result = await self.execute_query("SELECT 1 as test")
            checks["database_accessible"] = len(result.metadata.get("error", "")) == 0
            checks["test_query_successful"] = checks["database_accessible"]
            
            if checks["database_accessible"]:
                # Check for test data
                result = await self.execute_query("SELECT COUNT(*) as count FROM employees")
                if len(result.results) > 0 and result.results[0].get("count", 0) > 0:
                    checks["test_data_available"] = True
                    
        except Exception as e:
            self.logger.debug(f"Health check error: {e}")
        
        return {
            "healthy": all(checks.values()),
            "checks": checks,
            "config": {
                "db_type": self.db_type,
                "database_path": self.database_path if self.db_type == 'sqlite' else None,
                "host": self.host if self.db_type != 'sqlite' else None,
                "database_name": self.database_name,
                "safe_mode": self.safe_mode
            }
        }
    
    async def _get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if self.db_type == 'sqlite':
                # Get table list and schema
                result = await self.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                
                tables = {}
                for row in result.results:
                    table_name = row['name']
                    # Get table schema
                    schema_result = await self.execute_query(f"PRAGMA table_info({table_name})")
                    tables[table_name] = {
                        "columns": schema_result.results,
                        "type": "table"
                    }
                
                return {
                    "db_type": "sqlite",
                    "database_path": self.database_path,
                    "tables": tables
                }
            
            else:
                # For PostgreSQL/MySQL, use information_schema
                result = await self.execute_query("""
                    SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """)
                
                tables = {}
                for row in result.results:
                    table_name = row['table_name']
                    if table_name not in tables:
                        tables[table_name] = {"columns": [], "type": "table"}
                    
                    tables[table_name]["columns"].append({
                        "name": row['column_name'],
                        "type": row['data_type'],
                        "nullable": row['is_nullable'] == 'YES'
                    })
                
                return {
                    "db_type": self.db_type,
                    "database": self.database_name,
                    "tables": tables
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _get_tables(self) -> Dict[str, Any]:
        """Get list of tables in database"""
        try:
            if self.db_type == 'sqlite':
                result = await self.execute_query(
                    "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name"
                )
            else:
                result = await self.execute_query("""
                    SELECT table_name as name, table_type as type
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            
            return {
                "tables": result.results,
                "count": len(result.results)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific table"""
        try:
            analysis = {"table_name": table_name}
            
            # Get row count
            count_result = await self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            analysis["row_count"] = count_result.results[0]["count"] if count_result.results else 0
            
            # Get sample data
            sample_result = await self.execute_query(f"SELECT * FROM {table_name} LIMIT 5")
            analysis["sample_data"] = sample_result.results
            
            # Get column information
            if self.db_type == 'sqlite':
                schema_result = await self.execute_query(f"PRAGMA table_info({table_name})")
                analysis["columns"] = schema_result.results
            else:
                schema_result = await self.execute_query(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                analysis["columns"] = schema_result.results
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "table_name": table_name
            }


# Factory function for easy instantiation
def create_sql_database_tool(config: Optional[Dict[str, Any]] = None) -> SQLDatabaseTool:
    """Create SQL Database Tool instance"""
    return SQLDatabaseTool(config)


# CLI interface for direct testing
async def main():
    """CLI interface for testing the tool directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SQL Database Debug Tool")
    parser.add_argument("--query", "-q", required=True, help="SQL query to execute")
    parser.add_argument("--db-type", "-t", default="sqlite", choices=["sqlite", "postgresql", "mysql"], help="Database type")
    parser.add_argument("--database", "-d", help="Database name/path")
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--username", "-u", help="Database username")
    parser.add_argument("--password", "-p", help="Database password")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create tool
    config = {
        "db_type": args.db_type,
        "database_path": args.database or "debug_test.db",
        "database_name": args.database or "test_db",
        "host": args.host,
        "username": args.username,
        "password": args.password,
        "debug_mode": args.debug
    }
    
    tool = create_sql_database_tool(config)
    
    # Execute query
    result = await tool.execute("query", {"query": args.query})
    
    # Print results
    print(json.dumps(result.data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
