import pytest
import asyncio
from typing import List, Dict, Any
from langswarm_pro.core.rag.optimizer import RAGOptimizer
from langswarm_pro.core.rag.pipeline import IngestionPipeline
from langswarm_pro.core.memory.hybrid import HybridMemoryManager

# Mock Adapter
class MockAdapter:
    def __init__(self):
        self.docs = []
    
    async def add_documents(self, documents):
        self.docs.extend(documents)
        
    async def query(self, query, top_k=5, **kwargs):
        return [doc for doc in self.docs if query in doc["text"]]

@pytest.mark.asyncio
async def test_rag_optimizer():
    optimizer = RAGOptimizer()
    docs = ["Hello world", "Another doc"]
    # Currently stubs
    summaries = await optimizer.summarize(docs)
    assert len(summaries) == 2
    assert "Summary of" in summaries[0]
    
    reranked = await optimizer.rerank("query", [{"text": "doc"}])
    assert len(reranked) == 1
    
    expanded = await optimizer.expand_query("test")
    assert len(expanded) == 1

@pytest.mark.asyncio
async def test_hybrid_manager():
    adapter1 = MockAdapter()
    adapter2 = MockAdapter()
    manager = HybridMemoryManager([adapter1, adapter2])
    
    docs = [{"text": "searchable content", "id": "1"}]
    await manager.add_documents(docs)
    
    assert len(adapter1.docs) == 1
    assert len(adapter2.docs) == 1
    
    results = await manager.query("searchable")
    # Both adapters return the doc, but hybrid manager should dedupe
    assert len(results) == 1
    assert results[0]["id"] == "1"

@pytest.mark.asyncio
async def test_ingestion_pipeline():
    # Mock manager
    manager = MockAdapter() 
    pipeline = IngestionPipeline(memory_manager=manager)
    
    # We mock the loader logic by overriding the method for test
    pipeline._load_content = lambda path: "This is some test content for chunking."
    
    count = await pipeline.run("test.txt")
    assert count > 0
    assert len(manager.docs) > 0
    assert "source" in manager.docs[0]["metadata"]
