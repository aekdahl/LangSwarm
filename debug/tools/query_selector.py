"""
Simple Query Selector for Debug Tools

Provides basic query selection functionality for testing.
"""

from typing import Optional, Tuple, Any


class QueryOption:
    """Simple query option class"""
    
    def __init__(self, name: str, query: str, description: str, category: str = "basic"):
        self.name = name
        self.query = query
        self.description = description
        self.category = category


def select_query_interactive(tool_name: str, auto_mode: bool = False) -> Tuple[Optional[str], Optional[QueryOption]]:
    """
    Simple query selection for debug tools
    
    Returns:
        Tuple of (query_string, query_option) or (None, None) if cancelled
    """
    
    # Simple predefined queries for testing
    test_queries = {
        "bigquery": [
            QueryOption("Simple Test", "test", "Basic connectivity test", "test"),
            QueryOption("Search Query", "machine learning", "Search for ML content", "basic"),
            QueryOption("API Documentation", "API authentication", "Find API docs", "technical")
        ],
        "sql": [
            QueryOption("List Tables", "SELECT name FROM sqlite_master WHERE type='table'", "List all tables", "basic"),
            QueryOption("Employee Count", "SELECT COUNT(*) FROM employees", "Count employees", "basic"),
            QueryOption("Department Summary", "SELECT department, COUNT(*) as count FROM employees GROUP BY department", "Department stats", "analysis")
        ]
    }
    
    if auto_mode:
        # Return first available query for auto mode
        queries = test_queries.get(tool_name, [])
        if queries:
            return queries[0].query, queries[0]
        return "test", QueryOption("Auto Test", "test", "Automatic test query", "auto")
    
    # Interactive mode - just return a simple test query for now
    queries = test_queries.get(tool_name, [])
    if queries:
        print(f"Using test query: {queries[0].name}")
        return queries[0].query, queries[0]
    
    # Fallback
    return "test", QueryOption("Default Test", "test", "Default test query", "default")