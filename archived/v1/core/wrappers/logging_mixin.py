from typing import Any, Optional
from langswarm.core.base.log import GlobalLogger

try:
    from langsmith.tracing import LangSmithTracer
except ImportError:
    LangSmithTracer = None

class LoggingMixin:
    """
    Mixin for managing logging using GlobalLogger with optional LangSmith integration.
    """

    def _initialize_logger(self, name: str, agent: Any, langsmith_api_key: Optional[str]) -> None:
        """
        Initialize the logger, delegating to GlobalLogger.

        Parameters:
        - name (str): Name of the logger.
        - agent (Any): The agent to check for existing LangSmith integration.
        - langsmith_api_key (Optional[str]): API key for LangSmith, if provided.
        """
        # Initialize the global logger (ensures LangSmith is set up if API key is provided)
        GlobalLogger.initialize(name=name, langsmith_api_key=langsmith_api_key)
            
        # If the agent already has a LangSmith tracer, use it
        #if hasattr(agent, "tracer") and LangSmithTracer and isinstance(agent.tracer, LangSmithTracer):
        if hasattr(agent, "tracer") and type(agent.tracer).__name__ == "LangSmithTracer":
            self.logger = agent.tracer
            print(f"LangSmith tracer found for agent {name}. Using it for logging.")
            return

        # Otherwise, fallback to using GlobalLogger
        self.logger = GlobalLogger

    def log_event(self, *args, **kwargs):
        """
        Log an event using GlobalLogger.
        """
        self.logger.log_event(*args, **kwargs)

    def log(self, *args, **kwargs):
        """
        Alias for log_event to maintain consistency.
        """
        self.log_event(*args, **kwargs)
