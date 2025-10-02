import pytest
import json
from langswarm.core.wrappers.middleware import MiddlewareMixin

        
class DummyTool:
    def summarize(self, **kwargs):
        return {"result": f"ran summarize with {kwargs}"}

    def run(self, payload):
        print("Running DummyTool with payload:", payload)
        try:
            method = payload.get("method")
            params = payload.get("params", {})
            if method == "summarize":
                return {"result": f"summary of {params['text']}"}
            return {"result": "method not supported"}
        except Exception as e:
            print("❌ DummyTool error:", e)
            return {"error": str(e)}


class DummyToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, tool):
        self._tools[name] = tool

    def get_tool(self, name):
        return self._tools.get(name)

    def get_plugin(self, name):
        return None  # ensure not used

class DummyRAGRegistry:
    def get_rag(self, name):
        return None  # ensure not used


@pytest.fixture
def middleware():
    tool_registry = DummyToolRegistry()
    rag_registry = DummyRAGRegistry()
    plugin_registry = DummyToolRegistry()  # reuse class but leave empty

    tool_registry.register("summarizer", DummyTool())

    instance = MiddlewareMixin(
        tool_registry=tool_registry,
        rag_registry=rag_registry,
        plugin_registry=plugin_registry
    )
    instance.name = "test-agent"  # Used in log messages
    instance.timeout = 5  # or whatever default you expect
    instance.log_event = lambda *args, **kwargs: None  # Stub out logger
    return instance


def test_middleware_success(middleware):
    action = {
        "summarizer": {
            "method": "summarize",
            "params": {"text": "hello"}
        }
    }
    status, result = middleware.to_middleware(action)
    print("Result:", status, result)  # 👈 temporary debug line
    assert status == 201, f"Expected 201, got {status}. Response: {result}"
    assert "summary" in result
    assert "hello" in result


def test_middleware_empty_input(middleware):
    status, result = middleware.to_middleware(None)
    assert status == 200


def test_middleware_action_not_found(middleware):
    action = {
        "unknown": {
            "method": "do",
            "params": {}
        }
    }
    status, result = middleware.to_middleware(action)
    assert status == 404
    assert "not found" in result.lower()
