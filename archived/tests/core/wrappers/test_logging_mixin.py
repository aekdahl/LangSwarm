import unittest
from unittest.mock import MagicMock, patch
from langswarm.core.wrappers.logging_mixin import LoggingMixin
from langswarm.core.base.log import GlobalLogger


class TestLoggingMixin(unittest.TestCase):
    def setUp(self):
        self.mixin = LoggingMixin()

    def test_initialize_logger_with_langsmith(self):
        agent = MagicMock()
        agent.tracer.__class__.__name__ = "LangSmithTracer"

        self.mixin._initialize_logger("TestLogger", agent, "fake_api_key")
        self.assertEqual(self.mixin.logger, agent.tracer)

    @patch.object(GlobalLogger, "initialize")
    def test_initialize_logger_with_global_logger(self, mock_initialize):
        agent = MagicMock()
        if hasattr(agent, "tracer"):
            del agent.tracer  # Ensure no tracer
        self.mixin._initialize_logger("TestLogger", agent, None)
        self.assertEqual(self.mixin.logger, GlobalLogger)
        mock_initialize.assert_called_once_with(name="TestLogger", langsmith_api_key=None)

    def test_log_event_delegates_to_logger(self):
        self.mixin.logger = MagicMock()
        self.mixin.log_event("Test event", level="info")
        self.mixin.logger.log_event.assert_called_once_with("Test event", level="info")

    def test_log_alias(self):
        self.mixin.logger = MagicMock()
        self.mixin.log("Alias log test", level="info")
        self.mixin.logger.log_event.assert_called_once_with("Alias log test", level="info")
