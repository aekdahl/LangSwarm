from memory.rerankers.base import BaseReranker  # Import missing base class.

class OpenAIReranker(BaseReranker):
    """
    A reranker using OpenAI's language models for relevance ranking.

    The reranker uses a structured JSON format for output, ensuring robustness and reliability.
    """

    def __init__(self, model_name="gpt-4"):
        """
        Initialize the OpenAIReranker.

        Args:
            model_name (str): Name of the OpenAI model to use (e.g., "gpt-4").
        """
        from langchain.llms import OpenAI
        self.llm = OpenAI(model_name=model_name)

    def rerank(self, query, documents):
        """
        Rerank documents based on relevance to the query.

        Args:
            query (str): The query string.
            documents (list): List of documents with 'text' and optional 'metadata'.

        Returns:
            list: Documents sorted by relevance score.
        """
        # Validate inputs
        if not isinstance(query, str):
            raise ValueError("Query must be a string.")
        if not isinstance(documents, list) or not all(isinstance(doc, dict) for doc in documents):
            raise ValueError("Documents must be a list of dictionaries.")

        # Construct prompt
        prompt = self._construct_prompt(query, documents)

        # Generate response
        try:
            response = self.llm(prompt)
            ranked_indices = self._parse_response(response, len(documents))
        except Exception as e:
            print(f"Error during reranking: {e}")
            return []

        # Map ranked indices back to documents
        ranked_documents = [documents[i] for i in ranked_indices]
        return ranked_documents

    def _construct_prompt(self, query, documents):
        """
        Construct a structured prompt for the OpenAI model.

        Args:
            query (str): The query string.
            documents (list): List of documents.

        Returns:
            str: The constructed prompt.
        """
        doc_list = "\n".join([f"{i + 1}. {doc['text']}" for i, doc in enumerate(documents)])
        prompt = (
            f"Rerank the following documents based on their relevance to the query.\n\n"
            f"Query: {query}\n\nDocuments:\n{doc_list}\n\n"
            f"Respond with a JSON array of indices in the order of relevance, e.g., [3, 1, 2]."
        )
        return prompt

    def _parse_response(self, response, num_docs):
        """
        Parse and validate the response from the OpenAI model.

        Args:
            response (str): The raw response from the model.
            num_docs (int): Number of documents in the input.

        Returns:
            list: List of ranked indices.

        Raises:
            ValueError: If the response is invalid or incomplete.
        """
        try:
            # Parse JSON response
            ranked_indices = json.loads(response)

            # Validate the output format
            if not isinstance(ranked_indices, list) or not all(
                isinstance(idx, int) and 1 <= idx <= num_docs for idx in ranked_indices
            ):
                raise ValueError("Response does not contain a valid list of indices.")
            if len(set(ranked_indices)) != num_docs:
                raise ValueError("Response indices are incomplete or contain duplicates.")

            # Convert to zero-based indexing
            return [idx - 1 for idx in ranked_indices]
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid response format: {e}")

