class LangChainEmbeddingReranker(BaseReranker):
    def __init__(self, embedding_function):
        self.embedding_function = embedding_function

    def rerank(self, query, documents):
        """
        Rerank documents using LangChain embeddings.
        """
        query_embedding = self.embedding_function.embed_query(query)
        results = []
        for doc in documents:
            doc_embedding = self.embedding_function.embed_text(doc["text"])
            score = sum(q * d for q, d in zip(query_embedding, doc_embedding))
            results.append({"text": doc["text"], "metadata": doc.get("metadata", {}), "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)


