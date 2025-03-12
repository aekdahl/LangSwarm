class BaseWorkflow:
    def __init__(self, agent, retrievers, rerankers=None):
        self.agent = agent
        self.retrievers = retrievers
        self.rerankers = rerankers or []

    def process_data(self, raw_data, metadata=None):
        metadata = metadata or {}
        return [{"text": entry.strip(), "metadata": metadata} for entry in raw_data]

    def load_data(self, data):
        for retriever in self.retrievers:
            retriever.add_documents(data)

    def query_and_rerank(self, query):
        # Retrieve data from all retrievers
        documents = []
        for retriever in self.retrievers:
            documents.extend(retriever.query(query))

        if not documents:
            print("No documents retrieved.")
            return None

        # Rerank if rerankers are defined
        for reranker in self.rerankers:
            documents = reranker.rerank(query, documents)

        if not documents:
            print("No documents could be reranked.")
            return None

        return documents

    def generate_response(self, query, context):
        input_text = f"Query: {query}\nContext: {context}"
        return self.agent.generate_response(input_text)
