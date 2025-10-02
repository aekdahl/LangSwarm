import unittest
from unittest.mock import patch, MagicMock
from langswarm.core.factory.agents import AgentFactory

class TestAgentFactoryCreate(unittest.TestCase):
    @patch("langswarm.core.factory.agents.AgentWrapper")
    @patch("langswarm.core.factory.agents.AgentFactory._create_base_agent")
    def test_create_method_wraps_agent_and_registers(self, mock_create_base_agent, mock_agent_wrapper):
        # Mock base agent and wrapper
        mock_agent = MagicMock()
        mock_wrapper_instance = MagicMock()
        mock_create_base_agent.return_value = mock_agent
        mock_agent_wrapper.return_value = mock_wrapper_instance

        # Call AgentFactory.create
        result = AgentFactory.create(
            name="test-agent",
            agent_type="openai",
            model="gpt-3.5-turbo",
            openai_api_key="fake-key"
        )

        # Validate
        mock_create_base_agent.assert_called_once_with("openai", None, model="gpt-3.5-turbo", openai_api_key="fake-key")
        mock_agent_wrapper.assert_called_once_with(
            name="test-agent",
            agent=mock_agent,
            memory=None,
            agent_type="openai",
            langsmith_api_key=None,
            model="gpt-3.5-turbo",
            openai_api_key="fake-key"  # include this!
        )
        self.assertEqual(result, mock_wrapper_instance)
