from memory.rerankers.rerank import BaseReranker  # Import missing base class.
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

class BM25Reranker(BaseReranker):
    def __init__(self, documents):
        from rank_bm25 import BM25Okapi
        self.bm25 = BM25Okapi([doc["text"].split() for doc in documents])

    def rerank(self, query, documents):
        """
        Rerank documents using BM25 scoring.
        """
        scores = self.bm25.get_scores(query.split())
        for doc, score in zip(documents, scores):
            doc["score"] = score
        return sorted(documents, key=lambda x: x["score"], reverse=True)


class MetadataReranker(BaseReranker):
    def __init__(self, metadata_field, reverse=True):
        self.metadata_field = metadata_field
        self.reverse = reverse

    def rerank(self, query, documents):
        """
        Rerank documents based on a metadata field.
        """
        return sorted(
            documents,
            key=lambda doc: doc.get("metadata", {}).get(self.metadata_field, 0),
            reverse=self.reverse
        )


class DPRReranker(BaseReranker):
    """
    DPR-based Reranker for LangSwarm.

    Methods:
        rerank(query: str, documents: list) -> list:
            Rerank the provided documents based on the semantic similarity to the query.
    """
    def __init__(self, query_encoder_model: str, doc_encoder_model: str):
        """
        Initialize the DPRReranker with pretrained models.

        Args:
            query_encoder_model (str): Hugging Face model name for the query encoder.
            doc_encoder_model (str): Hugging Face model name for the document encoder.
        """
        self.query_tokenizer = AutoTokenizer.from_pretrained(query_encoder_model)
        self.query_encoder = AutoModel.from_pretrained(query_encoder_model)
        self.doc_tokenizer = AutoTokenizer.from_pretrained(doc_encoder_model)
        self.doc_encoder = AutoModel.from_pretrained(doc_encoder_model)

    def _encode(self, texts: List[str], tokenizer, model):
        """
        Encode the input texts using the tokenizer and model.

        Args:
            texts (List[str]): A list of input texts.
            tokenizer: The tokenizer instance.
            model: The model instance.

        Returns:
            torch.Tensor: Encoded text representations.
        """
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token embeddings
        return embeddings

    def rerank(self, query: str, documents: List[dict]) -> List[dict]:
        """
        Rerank the provided documents based on the semantic similarity to the query.

        Args:
            query (str): The query string.
            documents (list): A list of dictionaries containing 'text' for each document.

        Returns:
            list: A list of documents sorted by relevance scores in descending order.
        """
        # Encode the query
        query_embedding = self._encode([query], self.query_tokenizer, self.query_encoder)

        # Encode the documents
        doc_texts = [doc['text'] for doc in documents]
        doc_embeddings = self._encode(doc_texts, self.doc_tokenizer, self.doc_encoder)

        # Compute cosine similarity
        query_embedding = query_embedding / query_embedding.norm(dim=1, keepdim=True)
        doc_embeddings = doc_embeddings / doc_embeddings.norm(dim=1, keepdim=True)
        scores = torch.mm(query_embedding, doc_embeddings.t()).squeeze(0).tolist()

        # Attach scores to documents and sort
        for doc, score in zip(documents, scores):
            doc['score'] = score
        ranked_documents = sorted(documents, key=lambda x: x['score'], reverse=True)

        return ranked_documents
