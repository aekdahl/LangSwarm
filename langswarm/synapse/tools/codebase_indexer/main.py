import os
from typing import Dict, List
import json

from ..base import BaseTool
from .config import ToolSettings

class CodebaseIndexer(BaseTool):
    """
    Tool for indexing a codebase by querying the database for metadata and creating a file/folder structure.
    """
        
    def __init__(
        self, 
        identifier,
        adapter,
        **kwargs
    ):
        
        if not isinstance(adapter, DatabaseAdapter):
            raise ValueError("The adapter must be an instance of DatabaseAdapter.")
        
        self.adapter = adapter
        self.identifier = identifier
        self.brief = (
            f"Indexes file and folder structures from a database query."
        )

        super().__init__(
            name="CodebaseIndexer",
            description=(
                f"Indexes file and folder structures from a database query."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.voting = LLMVoting(clients=agents, **kwargs)

    def run(self, payload = {}, action="use"):
        """Handles file operations based on the provided action and parameters."""
        
        # Map actions to corresponding functions
        action_map = {
            "help": self._help,
            "use": self.use,
        }

        # Execute the corresponding action
        if action in action_map: 
            return self._safe_call(action_map[action], **payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def use(self, query: Dict = None, output_format: str = "dict") -> Dict:
        """
        Indexes the codebase by fetching metadata from the database and building a file/folder structure.

        Args:
            query (Dict, optional): Pre-written query to fetch metadata.
            output_format (str): Output format of the index. Options: "dict", "json". Defaults to "dict".

        Returns:
            Dict: A nested dictionary representing the file/folder structure.
        """

        # Step 1: Query the database for metadata
        try:
            metadata_results = self.adapter.query(query=query)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch metadata from the database: {e}")

        if not metadata_results:
            raise ValueError("No metadata retrieved from the database.")

        # Step 2: Build the file/folder structure
        file_structure = self._build_file_structure(metadata_results)

        # Step 3: Output the index
        if output_format == "json":
            return json.dumps(file_structure, indent=2)
        elif output_format == "dict":
            return file_structure
        else:
            raise ValueError("Invalid output_format. Choose 'dict' or 'json'.")

    def _build_file_structure(self, metadata_results: List[Dict]) -> Dict:
        """
        Builds a nested file/folder structure from metadata results.

        Args:
            metadata_results (List[Dict]): Metadata results from the database query.

        Returns:
            Dict: A nested dictionary representing the file/folder structure.
        """
        file_structure = {}

        for record in metadata_results:
            # Extract the file path from metadata
            file_path = record.get("metadata", {}).get("path", "")
            if not file_path:
                continue

            # Break the path into components
            path_parts = file_path.split(os.sep)

            # Recursively build the nested dictionary structure
            current_level = file_structure
            for part in path_parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        return file_structure

"""
from adapters.pinecone_adapter import PineconeAdapter

# Initialize the adapter
adapter = PineconeAdapter(api_key="your_api_key", environment="your_env", index_name="your_index_name")

# Initialize the indexer tool
indexer = CodebaseIndexer()

# Define the pre-written query to fetch only metadata
query = {"file_type": "code"}  # Adjust this query as per the database schema

# Run the tool to generate the file and folder structure
file_structure = indexer.use(adapter=adapter, query=query, output_format="dict")

# Print the file structure
print("File Structure:")
for folder, sub_structure in file_structure.items():
    print(f"{folder}: {sub_structure}")

"""
