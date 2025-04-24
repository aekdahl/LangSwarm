import unittest
from unittest.mock import MagicMock, patch
from langswarm.core.wrappers.base_wrapper import BaseWrapper


class DummyAgent:
    def __init__(self):
        self.model = "dummy-model"
        self.task = "text-generation"

    def run(self):
        return "output"


class TestBaseWrapper(unittest.TestCase):

    @patch("langswarm.core.wrappers.base_wrapper.AgentRegistry")
    def test_init_registers_agent(self, mock_registry):
        agent = DummyAgent()
        wrapper = BaseWrapper(name="dummy_agent", agent=agent, metadata={"test": "value"})

        mock_registry.register.assert_called_once_with(
            name="dummy_agent",
            agent=wrapper,
            agent_type="DummyAgent",
            metadata={"test": "value"},
        )

    def test_get_module_path(self):
        path = BaseWrapper._get_module_path(DummyAgent)
        self.assertIn("DummyAgent", path)

    def test_is_openai_llm(self):
        agent = DummyAgent()
        self.assertFalse(BaseWrapper._is_openai_llm(agent))

    def test_is_langchain_agent(self):
        agent = MagicMock()
        agent.__module__ = "langchain.llms"
        self.assertTrue(BaseWrapper._is_langchain_agent(agent))

    def test_is_hugging_face_agent_by_module(self):
        agent = MagicMock()
        agent.__module__ = "transformers.models"
        agent.model = "hf-model"
        agent.task = "text-gen"
        self.assertTrue(BaseWrapper._is_hugging_face_agent(agent))

    def test_is_hugging_face_agent_by_attributes(self):
        agent = MagicMock()
        delattr(agent, "__module__")
        agent.model = "hf-model"
        agent.task = "text-gen"
        self.assertTrue(BaseWrapper._is_hugging_face_agent(agent))

    def test_is_llamaindex_agent_by_module(self):
        agent = MagicMock()
        agent.__class__.__module__ = "llama_index.query_engine"
        self.assertTrue(BaseWrapper._is_llamaindex_agent(agent))

    def test_is_llamaindex_agent_by_query_method(self):
        agent = MagicMock()
        agent.__class__.__module__ = "custom.module"
        agent.query = MagicMock()
        self.assertTrue(BaseWrapper._is_llamaindex_agent(agent))

    def test_validate_agent_valid(self):
        agent = DummyAgent()
        wrapper = BaseWrapper(name="valid_agent", agent=agent)
        # No exception should be raised
        wrapper._validate_agent()

    def test_validate_agent_invalid(self):
        agent = object()
        wrapper = BaseWrapper(name="invalid_agent", agent=agent)
        with self.assertRaises(ValueError):
            wrapper._validate_agent()


if __name__ == "__main__":
    unittest.main()
