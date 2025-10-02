import pytest
from langswarm.memory.adapters.database_adapter import DatabaseAdapter


class MockDatabaseAdapter(DatabaseAdapter):
    def __init__(self):
        super().__init__("mock", "Mock adapter", "Use this to mock a DB")
        self._store = []

    def add_documents(self, data):
        self._store.append(data)
        return True

    def query(self, query, filters=None, k=5):
        return self._store[:k]

    def delete(self, identifier):
        return True

    def capabilities(self):
        return {"add": True, "query": True, "delete": True}

    def translate_filters(self, filters):
        return filters


def test_add_documents_and_query_limit():
    adapter = MockDatabaseAdapter()
    adapter.add_documents({"text": "doc1"})
    adapter.add_documents({"text": "doc2"})
    adapter.add_documents({"text": "doc3"})

    results = adapter.query("query", k=2)
    assert len(results) == 2


def test_get_relevant_documents_uses_query_and_k():
    adapter = MockDatabaseAdapter()
    for i in range(10):
        adapter.add_documents({"text": f"doc{i}"})

    results = adapter.get_relevant_documents("query", k=3)
    assert len(results) == 3
    assert results[0]["text"] == "doc0"


def test_has_stored_files_true():
    adapter = MockDatabaseAdapter()
    adapter.add_documents({"text": "something"})

    assert adapter._has_stored_files("query") is True


def test_standardize_output_structure():
    adapter = MockDatabaseAdapter()
    result = adapter.standardize_output("text", "source", {"x": 1}, "id-1")
    assert result["text"] == "text"
    assert result["source"] == "source"
    assert result["metadata"] == {"x": 1}
    assert result["id"] == "id-1"
