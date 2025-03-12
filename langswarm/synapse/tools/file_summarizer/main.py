from abc import ABC, abstractmethod


class FileSummarizer(BaseTool):
    """
    A tool to summarize the contents of a file and write the summary back to the database.

    Purpose: To create high-level summaries of individual files, describing their purpose, 
    key functions/classes, and interactions with other project components.
    """
    def __init__(self, llm_agent, name="File Summarizer", description="Summarizes a file and writes the summary back to the database."):
        """
        Initialize the File Summarizer tool.

        Args:
            llm_agent: The LLM agent to use for summarization.
        """
        super().__init__(name, description)
        self.llm_agent = llm_agent

    def use(self, adapter, file_id):
        """
        Summarizes a file retrieved from the database and writes the summary back.

        Args:
            adapter (DatabaseAdapter): The database adapter to fetch and write the file.
            file_id (str): The unique ID of the file to summarize.

        Returns:
            dict: A dictionary with the file ID and its generated summary.
        """
        # Step 1: Fetch the file content using the file ID
        file_content = self._fetch_file_content(adapter, file_id)
        if not file_content:
            raise ValueError(f"File with ID {file_id} not found in the database.")

        # Step 2: Summarize the file content
        summary = self._generate_summary(file_content)

        # Step 3: Write the summary back to the database
        self._write_summary_to_database(adapter, file_id, summary)

        return {"file_id": file_id, "summary": summary}

    def _fetch_file_content(self, adapter, file_id):
        """
        Fetch the file content using the database adapter.

        Args:
            adapter (DatabaseAdapter): The database adapter instance.
            file_id (str): The unique ID of the file to retrieve.

        Returns:
            str: The content of the file.
        """
        results = adapter.query({"id": file_id})
        if not results or "text" not in results[0]:
            return None
        return results[0]["text"]

    def _generate_summary(self, file_content):
        """
        Generate a high-level summary of the file using the LLM agent.

        Args:
            file_content (str): The content of the file to summarize.

        Returns:
            str: The generated summary of the file.
        """
        prompt = (
            "Summarize the following file content, describing its purpose, key functions or classes, "
            "and how it interacts with other parts of the project:\n\n"
            f"{file_content}"
        )
        return self.llm_agent.run(prompt)

    def _write_summary_to_database(self, adapter, file_id, summary):
        """
        Write the generated summary back to the database.

        Args:
            adapter (DatabaseAdapter): The database adapter instance.
            file_id (str): The unique ID of the file.
            summary (str): The generated summary to write.
        """
        metadata = {"summary": summary}
        adapter.add_metadata(file_id=file_id, metadata=metadata)

"""
from adapters.pinecone_adapter import PineconeAdapter
from llm_agent import LLMAdapter  # Placeholder for your LLM agent

# Initialize the database adapter
adapter = PineconeAdapter(api_key="your_api_key", environment="your_env", index_name="your_index_name")

# Initialize the LLM agent
llm_agent = LLMAdapter(api_key="your_llm_api_key")

# Initialize the File Summarizer tool
file_summarizer = FileSummarizer(llm_agent=llm_agent)

# File ID to summarize
file_id = "unique_file_id_123"

# Summarize the file and write the summary back to the database
result = file_summarizer.use(adapter=adapter, file_id=file_id)

print(f"Summary for file {result['file_id']}:")
print(result["summary"])
"""
