import logging
from typing import Optional

try:
    from langsmith import LangSmithTracer
except ImportError:
    LangSmithTracer = None


class GlobalLogger:
    """
    Singleton class for managing global logging with optional LangSmith integration.
    """

    _logger = None
    _langsmith_tracer = None

    @classmethod
    def initialize(cls, name="GlobalLogger", langsmith_api_key=None, extra_handler: Optional[logging.Handler] = None):
        """
        Initialize the global logger.

        Parameters:
        - name (str): Name of the logger.
        - langsmith_api_key (str, optional): API key for LangSmith. If provided, sets up LangSmith logging.
        - extra_handler (logging.Handler, optional): An additional handler (e.g., for UI output).
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(name)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            cls._logger.addHandler(handler)
            cls._logger.setLevel(logging.INFO)
            
            # ✅ Let pytest's caplog capture this logger too
            cls._logger.propagate = True
    
            print("Global logger initialized.")
            
        # Ensure extra handler is attached even if logger was already initialized
        if extra_handler and not any(isinstance(h, type(extra_handler)) for h in cls._logger.handlers):
            cls._logger.addHandler(extra_handler)
            print("Extra handler added to GlobalLogger.")

        if langsmith_api_key and cls._langsmith_tracer is None:
            cls._langsmith_tracer = LangSmithTracer(api_key=langsmith_api_key)
            print("LangSmith tracer added to global logger.")

    @classmethod
    def _ensure_initialized(cls):
        """
        Ensure that the logger is initialized. If not, initialize with default settings.
        """
        if cls._logger is None:
            print("Global logger was not initialized. Initializing with default settings.")
            cls.initialize()

    @classmethod
    def has_handler(cls, handler_type):
        """ Check if a specific type of handler is attached """
        return any(isinstance(h, handler_type) for h in cls._logger.handlers) if cls._logger else False
    
    @classmethod
    def log(cls, message, level="info", name=None, metadata=None):
        """
        Log a message using the global logger or LangSmith if available.

        Parameters:
        - message (str): The message to log.
        - level (str): The log level (e.g., 'info', 'error').
        - name (str): The name of the log entry.
        - metadata (dict, optional): Metadata for LangSmith logging.
        """
        cls._ensure_initialized()
        name = name or cls._logger.name

        if cls._langsmith_tracer:
            cls._log_with_langsmith(message, level, name, metadata)
        else:
            getattr(cls._logger, level.lower(), cls._logger.info)(message)

    @classmethod
    def log_event(cls, *args, **kwargs):
        """
        Alias for the `log` method.
        """
        cls.log(*args, **kwargs)

    @classmethod
    def _log_with_langsmith(cls, message, level, name, metadata):
        """
        Log messages using LangSmith tracer.
        """
        if level == 'error':
            cls._langsmith_tracer.log_error(
                name=name,
                input_data={"message": message},
                output_data={},
                metadata=metadata or {"level": level},
            )
        elif level == 'metric':
            cls._langsmith_tracer.log_metric(
                name=name,
                value=metadata.get("value", 0),
                metadata=metadata or {},
            )
        else:
            cls._langsmith_tracer.log_success(
                name=name,
                input_data={"message": message},
                output_data={},
                metadata=metadata or {"level": level},
            )
            
    @classmethod
    def reset(cls):
        """
        Reset the logger and LangSmith tracer. Useful for tests.
        """
        if cls._logger:
            for handler in list(cls._logger.handlers):
                cls._logger.removeHandler(handler)
        cls._logger = None
        cls._langsmith_tracer = None

    @classmethod
    def attach_handler(cls, handler):
        """
        Attach an external log handler (e.g., pytest caplog.handler).
        """
        cls._ensure_initialized()
        if not cls.has_handler(type(handler)):
            cls._logger.addHandler(handler)