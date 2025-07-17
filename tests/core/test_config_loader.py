import unittest
from unittest.mock import patch, mock_open, MagicMock
from langswarm.core.config import LangSwarmConfigLoader

class TestLangSwarmConfigLoader(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="""
agents:
  - id: test_agent
    agent_type: openai
    model: gpt-3.5-turbo
""")
    @patch("os.path.exists", return_value=True)
    @patch("langswarm.core.factory.agents.AgentFactory.create")
    @patch("langswarm.core.config.LangSwarmConfigLoader._load_builtin_tool_classes")
    def test_load_agents_only(self, mock_load_tools, mock_create, mock_exists, mock_file):
        mock_agent_instance = MagicMock()
        mock_create.return_value = mock_agent_instance

        loader = LangSwarmConfigLoader(config_path=".")
        workflows, agents, brokers, tools, tools_metadata = loader.load()

        # Check that we have agents data
        self.assertIn("test_agent", agents)
        self.assertEqual(agents["test_agent"], mock_agent_instance)

        mock_create.assert_called_once()
        called_args = mock_create.call_args[1]
        self.assertEqual(called_args["name"], "test_agent")
        self.assertEqual(called_args["agent_type"], "openai")
        self.assertEqual(called_args["model"], "gpt-3.5-turbo")

if __name__ == "__main__":
    unittest.main()
