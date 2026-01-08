import asyncio
from typing import List, Dict, Any, Optional

class HybridMemoryManager:
    """
    Orchestrates multiple memory adapters (e.g., Vector Store + Keyword Search)
    to provide a unified memory interface.
    """
    def __init__(self, adapters: List[Any]):
        self.adapters = adapters

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to all registered adapters.
        """
        tasks = []
        for adapter in self.adapters:
            if hasattr(adapter, "add_documents"):
                # Check if async capable, otherwise run in executor if needed
                # For this implementation, we assume adapters have async methods or we await them directly
                # If synchronous, we'd wrap in run_in_executor
                if asyncio.iscoroutinefunction(adapter.add_documents):
                    tasks.append(adapter.add_documents(documents))
                else:
                    # Sync adapter fallback
                    adapter.add_documents(documents)
        
        if tasks:
            await asyncio.gather(*tasks)

    async def query(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Query all adapters and aggregate results.
        """
        tasks = []
        for adapter in self.adapters:
            # Check availability of query method
            if hasattr(adapter, "query"):
                if asyncio.iscoroutinefunction(adapter.query):
                    tasks.append(adapter.query(query, top_k=top_k, **kwargs))
                else:
                    # Mock result for sync adapter or call it
                    # In a real scenario, correct async wrapping is needed
                    pass

        if not tasks:
            return []

        results_list = await asyncio.gather(*tasks)
        
        # Flatten and Deduplicate
        all_results = []
        seen_ids = set()
        
        for results in results_list:
            for res in results:
                # Assume result has 'id' or use text hash
                doc_id = res.get("id") or hash(res.get("text", ""))
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append(res)
        
        # Sort by score if available
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return all_results[:top_k]

    async def delete(self, document_ids: List[str]):
        """
        Delete documents from all adapters.
        """
        tasks = []
        for adapter in self.adapters:
             if hasattr(adapter, "delete"):
                if asyncio.iscoroutinefunction(adapter.delete):
                    tasks.append(adapter.delete(document_ids))
                else:
                    adapter.delete(document_ids)
        
        if tasks:
            await asyncio.gather(*tasks)

    def to_framework(self, framework: str = "langchain") -> Any:
        """
        Convert the workflow into a format compatible with LangChain or LlamaIndex.
        Args:
            framework (str): The target framework, either "langchain" or "llamaindex".
        Returns:
            object: A framework-compatible retrieval object.
        """
        if framework == "langchain":
            try:
                from langchain_core.vectorstores import VectorStore
                from langchain_core.documents import Document
            except ImportError:
                raise ImportError("langchain-core is required for LangChain integration")

            class MultiSourceLangChain(VectorStore):
                """LangChain-compatible wrapper for HybridMemoryManager."""
                def __init__(self, manager):
                    self.manager = manager
                    self.embeddings = None # Required abstract property

                def add_texts(self, texts, metadatas=None, **kwargs):
                    docs = []
                    for i, text in enumerate(texts):
                        meta = metadatas[i] if metadatas else {}
                        docs.append({"text": text, "metadata": meta})
                    # Use run_until_complete since VectorStore API is sync usually
                    # Or users should use aarch? For now blocking for compatibility
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.manager.add_documents(docs))
                    return [str(i) for i in range(len(texts))]

                def similarity_search(self, query, k=10, **kwargs):
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(self.manager.query(query, top_k=k))
                    # Convert to LangChain Documents
                    return [Document(page_content=r.get("text", ""), metadata=r.get("metadata", {})) for r in results]
                
                @classmethod
                def from_texts(cls, *args, **kwargs):
                    raise NotImplementedError("Use HybridMemoryManager directly")

            return MultiSourceLangChain(self)

        elif framework == "llamaindex":
            try:
                from llama_index.core.base.base_query_engine import BaseQueryEngine
                from llama_index.core.schema import Response, NodeWithScore, TextNode
            except ImportError:
                raise ImportError("llama-index-core is required for LlamaIndex integration")

            class MultiSourceLlamaIndex(BaseQueryEngine):
                """LlamaIndex-compatible wrapper for HybridMemoryManager."""
                def __init__(self, manager):
                    super().__init__(callback_manager=None)
                    self.manager = manager

                def _query(self, query_bundle) -> Response:
                    query_str = query_bundle.query_str
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(self.manager.query(query_str))
                    
                    # Convert to Response
                    nodes = []
                    for res in results:
                        node = NodeWithScore(node=TextNode(text=res.get("text", "")), score=res.get("score", 0.0))
                        nodes.append(node)
                        
                    return Response(response=str(results), source_nodes=nodes)
                
                async def aquery(self, query_bundle) -> Response:
                    query_str = query_bundle.query_str
                    results = await self.manager.query(query_str)
                     # Convert to Response
                    nodes = []
                    for res in results:
                         node = NodeWithScore(node=TextNode(text=res.get("text", "")), score=res.get("score", 0.0))
                         nodes.append(node)
                    return Response(response=str(results), source_nodes=nodes)

            return MultiSourceLlamaIndex(self)

        else:
            raise ValueError(f"Unsupported framework: {framework}")
