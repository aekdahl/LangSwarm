import pytest
import logging
from unittest.mock import patch, MagicMock
from langswarm.core.base.log import GlobalLogger


def test_initialize_creates_logger_and_adds_stream_handler():
    GlobalLogger._logger = None  # Reset for test
    GlobalLogger.initialize()
    assert GlobalLogger._logger is not None
    assert isinstance(GlobalLogger._logger.handlers[0], logging.StreamHandler)


def test_initialize_adds_extra_handler_once():
    class DummyHandler(logging.Handler):
        def emit(self, record):
            pass

    dummy_handler = DummyHandler()
    GlobalLogger.initialize(extra_handler=dummy_handler)
    handler_count = sum(isinstance(h, DummyHandler) for h in GlobalLogger._logger.handlers)
    assert handler_count == 1


@patch("langswarm.core.base.log.LangSmithTracer", new_callable=MagicMock)
def test_initialize_with_langsmith(mock_tracer_class):
    mock_instance = MagicMock()
    mock_tracer_class.return_value = mock_instance  # Make sure it's callable
    GlobalLogger._langsmith_tracer = None
    GlobalLogger._logger = None  # Reset logger
    GlobalLogger.initialize(langsmith_api_key="dummy-key")
    mock_tracer_class.assert_called_once_with(api_key="dummy-key")

    
#@pytest.mark.skip(reason="Skipping until caplog integration is fixed")
def test_global_logger_can_log(caplog):
    GlobalLogger.reset()
    GlobalLogger.initialize(name="TestLogger")
    GlobalLogger.attach_handler(caplog.handler)

    with caplog.at_level(logging.INFO):
        GlobalLogger.log("This is a test log", level="info")

    assert any("This is a test log" in r.message for r in caplog.records)


@patch.object(GlobalLogger, "_log_with_langsmith")
def test_log_routes_to_langsmith(mock_langsmith):
    GlobalLogger._langsmith_tracer = MagicMock()
    GlobalLogger.log("msg", level="info", metadata={"foo": "bar"})
    mock_langsmith.assert_called_once()


def test_has_handler_correctly_detects_handler_type():
    GlobalLogger.initialize()
    assert GlobalLogger.has_handler(logging.StreamHandler)
    assert not GlobalLogger.has_handler(logging.FileHandler)
