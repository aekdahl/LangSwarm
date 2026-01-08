import pytest
import sys
from unittest.mock import MagicMock
from langswarm_pro.core.memory.hybrid import HybridMemoryManager

# Mock LangChain and LlamaIndex modules if not installed
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.vectorstores"] = MagicMock()
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["llama_index.core.base"] = MagicMock()
sys.modules["llama_index.core.base.base_query_engine"] = MagicMock()
sys.modules["llama_index.core.schema"] = MagicMock()

@pytest.mark.asyncio
async def test_to_langchain():
    manager = HybridMemoryManager([])
    
    # We expect the import to succeed because of mocks (or install)
    # Ideally we mock the import within the method if not testing with real deps,
    # but since the method imports inside, we rely on the env.
    
    # Check if we can create it (even if mocks are returned)
    try:
        lc_store = manager.to_framework("langchain")
        assert lc_store is not None
        assert hasattr(lc_store, "similarity_search")
    except ImportError:
        pytest.skip("LangChain not installed")

@pytest.mark.asyncio
async def test_to_llamaindex():
    manager = HybridMemoryManager([])
    try:
        li_engine = manager.to_framework("llamaindex")
        assert li_engine is not None
        assert hasattr(li_engine, "query") or hasattr(li_engine, "_query")
    except ImportError:
         pytest.skip("LlamaIndex not installed")

@pytest.mark.asyncio
async def test_invalid_framework():
    manager = HybridMemoryManager([])
    with pytest.raises(ValueError, match="Unsupported framework"):
        manager.to_framework("invalid")
