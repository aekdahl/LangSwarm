class HybridRetrievalWorkflow:
    """
    Combines dense and sparse retrieval mechanisms to balance semantic relevance
    and keyword-based matching (e.g., using embeddings and BM25).

    Attributes:
        dense_retriever (object): A dense retriever (e.g., Pinecone or FAISS).
        sparse_retriever (object): A sparse retriever (e.g., BM25).

    Usage Example:
    --------------
    # Initialize retrievers
    dense_retriever = PineconeAdapter(pinecone_instance)
    sparse_retriever = BM25Retriever(documents)

    # Create hybrid workflow
    hybrid_workflow = HybridRetrievalWorkflow(dense_retriever, sparse_retriever)

    # Perform retrieval
    results = hybrid_workflow.run("What is LangSwarm?")
    print("Hybrid Retrieval Results:", results)
    """
    def __init__(self, dense_retriever, sparse_retriever):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

    def run(self, query):
        """
        Perform hybrid retrieval.

        Args:
            query (str): The user's query.

        Returns:
            list: Merged and deduplicated results.
        """
        dense_results = self.dense_retriever.query(query)
        sparse_results = self.sparse_retriever.query(query)

        # Merge and deduplicate results
        combined = {doc['text']: doc for doc in dense_results + sparse_results}
        return list(combined.values())


class MultiSourceRetrievalWorkflow:
    """
    Retrieves data from multiple sources and aggregates results.

    Attributes:
        retrievers (list): A list of retrievers for different sources.

    Usage Example:
    --------------
    # Initialize multiple retrievers
    retriever_1 = PineconeAdapter(pinecone_instance)
    retriever_2 = SQLRetriever(database_uri)

    # Create multi-source workflow
    multi_source_workflow = MultiSourceRetrievalWorkflow([retriever_1, retriever_2])

    # Perform retrieval
    results = multi_source_workflow.run("What is LangSwarm?")
    print("Multi-Source Retrieval Results:", results)
    """
    def __init__(self, retrievers):
        self.retrievers = retrievers

    def run(self, query):
        """
        Perform retrieval from all sources.

        Args:
            query (str): The user's query.

        Returns:
            list: Combined results from all sources.
        """
        all_results = []
        for retriever in self.retrievers:
            all_results.extend(retriever.query(query))
        return all_results


class TemporalRetrievalWorkflow:
    """
    Retrieves documents based on temporal constraints.

    Attributes:
        retriever (object): The base retriever.
        time_filter (function): A function to filter results by time.

    Usage Example:
    --------------
    # Define a time filter function
    def recent_filter(doc):
        return doc.get("metadata", {}).get("timestamp") >= "2025-01-01"

    # Initialize temporal workflow
    retriever = PineconeAdapter(pinecone_instance)
    temporal_workflow = TemporalRetrievalWorkflow(retriever, recent_filter)

    # Perform retrieval
    results = temporal_workflow.run("What is LangSwarm?")
    print("Temporal Retrieval Results:", results)
    """
    def __init__(self, retriever, time_filter):
        self.retriever = retriever
        self.time_filter = time_filter

    def run(self, query):
        """
        Retrieve and filter results by time.

        Args:
            query (str): The user's query.

        Returns:
            list: Filtered results.
        """
        results = self.retriever.query(query)
        return [doc for doc in results if self.time_filter(doc)]


class FederatedRetrievalWorkflow:
    """
    Retrieves data from distributed databases or indices.

    Attributes:
        retrievers (list): A list of distributed retrievers.

    Usage Example:
    --------------
    # Initialize distributed retrievers
    retriever_1 = PineconeAdapter(pinecone_instance)
    retriever_2 = WeaviateAdapter(weaviate_url)

    # Create federated workflow
    federated_workflow = FederatedRetrievalWorkflow([retriever_1, retriever_2])

    # Perform retrieval
    results = federated_workflow.run("What is LangSwarm?")
    print("Federated Retrieval Results:", results)
    """
    def __init__(self, retrievers):
        self.retrievers = retrievers

    def run(self, query):
        """
        Perform federated retrieval.

        Args:
            query (str): The user's query.

        Returns:
            list: Combined results from all sources.
        """
        all_results = []
        for retriever in self.retrievers:
            all_results.extend(retriever.query(query))
        return all_results


class CrossDomainRetrievalWorkflow:
    """
    Routes queries to domain-specific retrievers.

    Attributes:
        domain_retrievers (dict): A dictionary mapping domains to retrievers.

    Usage Example:
    --------------
    # Define retrievers for each domain
    retriever_medical = PineconeAdapter(pinecone_instance)
    retriever_legal = FAISSAdapter(index_path="legal_index.json")

    # Map retrievers to domains
    domain_retrievers = {
        "medical": retriever_medical,
        "legal": retriever_legal
    }

    # Create cross-domain workflow
    cross_domain_workflow = CrossDomainRetrievalWorkflow(domain_retrievers)

    # Perform domain-specific retrieval
    results = cross_domain_workflow.run("What is LangSwarm?", "medical")
    print("Cross-Domain Retrieval Results:", results)
    """
    def __init__(self, domain_retrievers):
        self.domain_retrievers = domain_retrievers

    def run(self, query, domain):
        """
        Retrieve data from the appropriate domain.

        Args:
            query (str): The user's query.
            domain (str): The target domain.

        Returns:
            list: Results from the specified domain.
        """
        retriever = self.domain_retrievers.get(domain)
        if retriever is None:
            raise ValueError(f"No retriever found for domain: {domain}")
        return retriever.query(query)
