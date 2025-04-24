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
    @patch("langswarm.core.config.AgentFactory.create")
    def test_load_agents_only(self, mock_create, mock_exists, mock_file):
        mock_agent_instance = MagicMock()
        mock_create.return_value = mock_agent_instance

        loader = LangSwarmConfigLoader(config_path=".")
        config_data, agents = loader.load()

        self.assertIn("agents", config_data)
        self.assertEqual(len(config_data["agents"]), 1)

        self.assertIn("test_agent", agents)
        self.assertEqual(agents["test_agent"], mock_agent_instance)

        mock_create.assert_called_once()
        called_args = mock_create.call_args[1]
        self.assertEqual(called_args["name"], "test_agent")
        self.assertEqual(called_args["agent_type"], "openai")
        self.assertEqual(called_args["model"], "gpt-3.5-turbo")

if __name__ == "__main__":
    unittest.main()
