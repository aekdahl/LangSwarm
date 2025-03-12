class HuggingFaceReranker(BaseReranker):
    """
    Reranker using Hugging Face SentenceTransformer models for semantic similarity.

    If the specified model is unavailable, a default model ('all-MiniLM-L6-v2') is used as a fallback.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Default lightweight model for general-purpose reranking

    def __init__(self, model_name=None):
        """
        Initialize the HuggingFaceReranker.

        Args:
            model_name (str): Name of the Hugging Face model to use. Defaults to `DEFAULT_MODEL`.
        """
        from sentence_transformers import SentenceTransformer, util
        self.util = util
        self.model_name = model_name or self.DEFAULT_MODEL

        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"Error loading model '{self.model_name}': {e}")
            print(f"Falling back to default model: '{self.DEFAULT_MODEL}'")
            self.model = SentenceTransformer(self.DEFAULT_MODEL)

    def rerank(self, query, documents):
        """
        Rerank documents based on semantic similarity to the query.

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

        query_embedding = self.model.encode(query, convert_to_tensor=True)
        results = []
        for doc in documents:
            doc_embedding = self.model.encode(doc["text"], convert_to_tensor=True)
            score = self.util.pytorch_cos_sim(query_embedding, doc_embedding).item()
            results.append({"text": doc["text"], "metadata": doc.get("metadata", {}), "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def validate_model(model_name):
        """
        Validate if the specified model is available for use.

        Args:
            model_name (str): Name of the Hugging Face model.

        Returns:
            bool: True if the model is available, False otherwise.
        """
        from sentence_transformers import SentenceTransformer
        try:
            SentenceTransformer(model_name)
            return True
        except Exception as e:
            print(f"Validation failed for model '{model_name}': {e}")
            return False



class HuggingFaceSemanticReranker(BaseReranker):
    """
    Reranks documents based on semantic similarity using Hugging Face models.

    Supports pre-trained and fine-tuned models for specific domains.

    Pre-Trained and Domain-Specific Models:
    ---------------------------------------
    General Models:
        - "all-MiniLM-L6-v2": Lightweight, general-purpose semantic similarity.
        - "all-mpnet-base-v2": High-performance general-purpose model.
    
    Domain-Specific Models:
        - Biomedical:
            - "sci-bert/scibert-scivocab-uncased": Optimized for scientific research.
            - "biobert-v1.1": Fine-tuned for biomedical text.
        - Legal:
            - "nlpaueb/legal-bert-base-uncased": Designed for legal documents.
        - Finance:
            - "finbert": Fine-tuned for financial data.
        - Customer Support:
            - "paraphrase-multilingual-mpnet-base-v2": Multilingual customer query handling.

    Usage Example:
    --------------
    1. Initialize the reranker:
        reranker = HuggingFaceSemanticReranker(model_name="biobert-v1.1")

    2. Provide query and documents:
        query = "What are the effects of this drug on the immune system?"
        documents = [
            {"text": "This drug enhances immune response in patients with cancer."},
            {"text": "The medication targets immune cells to reduce inflammation."},
        ]

    3. Perform reranking:
        results = reranker.rerank(query, documents)

    Returns:
        A list of documents sorted by relevance score.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the reranker with a Hugging Face model.

        Args:
            model_name (str): Name of the Hugging Face model to use.
        """
        from sentence_transformers import SentenceTransformer, util
        self.model = SentenceTransformer(model_name)

    def rerank(self, query, documents):
        """
        Rerank documents based on semantic similarity to the query.

        Args:
            query (str): The query string.
            documents (list): List of documents with 'text' and optional 'metadata'.

        Returns:
            list: Documents sorted by relevance score.
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        results = []
        for doc in documents:
            doc_embedding = self.model.encode(doc["text"], convert_to_tensor=True)
            score = util.pytorch_cos_sim(query_embedding, doc_embedding).item()
            results.append({"text": doc["text"], "metadata": doc.get("metadata", {}), "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)


class HuggingFaceDPRReranker(BaseReranker):
    def __init__(self, model_name="facebook/dpr-question_encoder-single-nq-base"):
        from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer, DPRContextEncoder
        self.query_model = DPRQuestionEncoder.from_pretrained(model_name)
        self.query_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained(model_name)
        self.context_model = DPRContextEncoder.from_pretrained(model_name)

    def rerank(self, query, documents):
        """
        Rerank documents using Dense Passage Retrieval (DPR).
        """
        query_inputs = self.query_tokenizer(query, return_tensors="pt")
        query_embedding = self.query_model(**query_inputs).pooler_output

        results = []
        for doc in documents:
            context_inputs = self.query_tokenizer(doc["text"], return_tensors="pt")
            context_embedding = self.context_model(**context_inputs).pooler_output
            score = (query_embedding * context_embedding).sum().item()
            results.append({"text": doc["text"], "metadata": doc.get("metadata", {}), "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)


