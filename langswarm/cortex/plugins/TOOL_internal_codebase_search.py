from typing import List, Dict
from adapters.database_adapter import DatabaseAdapter
from base_tool import BaseTool

class InternalCodebaseSearchTool(BaseTool):
    def __init__(self, name: str, description: str, db_adapter: DatabaseAdapter):
        """
        Initialize the Internal Codebase Search Tool.
        Args:
            name (str): Name of the tool.
            description (str): Description of the tool.
            db_adapter (DatabaseAdapter): Adapter to query the internal codebase index.
        """
        super().__init__(name, description)
        self.db_adapter = db_adapter

    def use(self, query: str) -> List[Dict]:
        """
        Search the internal codebase for relevant files or snippets.
        Args:
            query (str): The search query.

        Returns:
            List[Dict]: A list of relevant results with metadata.
        """
        # Perform the query against the database
        results = self.db_adapter.query(query=query, filters=None)

        # Rank results based on relevance (e.g., using BM25 or vector similarity)
        ranked_results = sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return ranked_results
