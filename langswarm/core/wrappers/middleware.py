
import os
import re
import sys
import uuid
import traceback

try:
    import signal as LS_SIGNAL
except ImportError:
    LS_SIGNAL = None

import threading
import time
import json

from typing import List, Dict

try:
    from langswarm.cortex.registry.plugins import PluginRegistry
except ImportError:
    PluginRegistry = {}

try:
    from langswarm.synapse.registry.tools import ToolRegistry
except ImportError:
    ToolRegistry = {}

try:
    from langswarm.memory.registry.rags import RAGRegistry
except ImportError:
    RAGRegistry = {}


class MiddlewareMixin:
    """
    Middleware layer for routing agent inputs to tools, plugins, or the agent itself.
    Instance-specific implementation for agent-specific tools and plugins.
    """
    def __init__(self, tool_registry=None, plugin_registry=None, rag_registry=None):
        """
        Initialize the middleware.
        """
        self.rag_registry = rag_registry or (RAGRegistry() if callable(RAGRegistry) else RAGRegistry)
        self.tool_registry = tool_registry or (ToolRegistry() if callable(ToolRegistry) else ToolRegistry)
        self.plugin_registry = plugin_registry or (PluginRegistry() if callable(PluginRegistry) else PluginRegistry)
        
        # assume you can get the raw tools list from your loader or registry
        from langswarm.core.config import ToolDeployer
        self.tool_deployer = ToolDeployer(self.tool_registry.tools)
        
        self.ask_to_continue_regex = r"\[AGENT_REQUEST:PROCEED_WITH_INTERNAL_STEP\]"
    
    def _find_workflow_path(self, handler, filename="workflows.yaml") -> str:
        """
        Given a tool _instance_ or its class, find the workflows.yaml sitting
        alongside its module.  
        Raises FileNotFoundError if none is found.
        """
        import importlib
        import inspect
        from importlib import resources
        # 1) figure out the module/package where the handler class lives
        mod_name = handler.__class__.__module__
        pkg_name = mod_name.rsplit('.', 1)[0]   # drop the class name

        # 2a) Try importlib.resources (Python 3.9+)
        try:
            pkg = importlib.import_module(pkg_name)
            # this gives a Traversable object pointing at the package dir
            candidate = resources.files(pkg).joinpath(filename)
            if candidate.is_file():
                return str(pkg_dir), str(candidate)
        except (ImportError, AttributeError):
            pass

        # 2b) Fallback: inspect the source file and look alongside it
        module = importlib.import_module(pkg_name)
        module_file = inspect.getsourcefile(module)
        if module_file:
            pkg_dir = os.path.dirname(os.path.abspath(module_file))
            candidate = os.path.join(pkg_dir, "workflows.yaml")
            if os.path.isfile(candidate):
                return str(pkg_dir), str(candidate)

        raise FileNotFoundError(f"No workflows.yaml found in package {pkg_name!r}")

    def use_mcp_tool(self, tool, tool_id: str, tool_type: str, workflow_id: str, input_data: str) -> Dict:
        """
        High-level entrypoint to call an MCP tool via its associated workflow.
        - Loads workflow from langswarm/mcp/tools/{tool_id}/workflows.yaml
        - Injects input_data into the workflow
        - Returns the output from the subflow
        """
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        #print("tool_type", tool_type)
        #workflow_path = os.path.join("..", "..", "mcp", "tools", tool_id, "workflows.yaml")
        config_path, workflow_path = self._find_workflow_path(tool)

        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"No workflow found for tool: {tool_id} at {workflow_path}")

        #print('Load Config...', config_path)
        loader = LangSwarmConfigLoader(config_path=config_path)
        workflows, agents, brokers, tools = loader.load()
        
        #print('Load Workflow...', workflows)
        executor = WorkflowExecutor(workflows, agents)
        executor.context["request_id"] = str(uuid.uuid4())  # Unique per request
        
        #print("input_data:", input_data)
        output = executor.run_workflow(workflow_id, user_input=input_data, tool_deployer = self.tool_deployer)

        print("MCP output", output)
        return output

    def to_middleware(self, agent_input):
        """
        Process agent input and route it appropriately.

        :param agent_input: str - The agent's input.
        :return: Tuple[int, str] - (status_code, result).
        """
        
        # ToDo: Handle RAG
        # ToDo: Handle multiple actions
        # ToDo: Validate agent_input
        
        if not agent_input:
            # If no action is detected, return input unchanged
            self._log_event("No action detected, forwarding input", "info")
            return 200, agent_input

        # Detect action type
        actions = [{"_id": key, **value} for key, value in agent_input.items()]
        
        print("Actions:", actions)
        
        # Process each action and collect responses
        results = [self._route_action(**action) for action in actions]
        #results = [self._route_action(action["_id"], action["method"], action.get("params", {})) for action in actions]


        # Extract statuses and responses
        statuses, responses = zip(*results)  # Unzipping the tuple list

        # Determine final status:
        # - If any status is NOT 200 or 201 → return that status.
        # - Else if any status is 201 → return 201.
        # - Otherwise, return 200.
        if any(status not in {200, 201} for status in statuses):
            final_status = next(status for status in statuses if status not in {200, 201})
        elif 201 in statuses:
            final_status = 201
        else:
            final_status = 200

        # Concatenate responses into one string
        final_response = "\n\n".join(responses)

        # ToDo: Implement below

        # Truncate to fit context
        # ToDo: OptimizerManager holds a summarizer if needed
        #return self.utils.truncate_text_to_tokens(
        #    aggregated_response, 
        #    self.model_details["limit"], 
        #    tokenizer_name=self.model_details.get("name", "gpt2"),
        #    current_conversation=self.share_conversation()
        #)

        return final_status, final_response

    def _route_action(self, _id, method, params):
        handler = None
        
        print("inputs: ", (_id, method, params))

        if isinstance(self.rag_registry, dict):
            handler = self.rag_registry.get(_id)
        else:
            handler = self.rag_registry.get_rag(_id)
        if handler is None:
            if isinstance(self.tool_registry, dict):
                handler = self.tool_registry.get(_id)
            else:
                handler = self.tool_registry.get_tool(_id)
        if handler is None:
            if isinstance(self.plugin_registry, dict):
                handler = self.plugin_registry.get(_id)
            else:
                handler = self.plugin_registry.get_plugin(_id)
        
        if handler:
            self._log_event(f"Executing: {_id} - {method}", "info")

            # otherwise fall back to your existing HTTP / handler.run path
            try:
                result = self._execute_with_timeout(handler, method, params)
            except Exception as e:
                self._log_event(f"Tool {_id} error: {e}", "error")
                return 500, f"[ERROR] {str(e)}"
            return 201, json.dumps(result, indent=2)

        self._log_event(f"Action not found: {_id} - {method}", "error")
        return 404, f"{_id.capitalize()} '{method}' not found."


    def _execute_with_timeout(self, handler, method, params):
        """
        Execute a handler with a timeout.
        :param handler: callable - The action handler.
        :param params: dict - Parameters for the handler.
        :return: str - The result of the handler.
        """
        self.timer = None
        def timeout_handler(signum, frame):
            raise TimeoutError("Action execution timed out.")

        if LS_SIGNAL and hasattr(LS_SIGNAL, "SIGALRM"):
            LS_SIGNAL.signal(LS_SIGNAL.SIGALRM, timeout_handler)
            LS_SIGNAL.alarm(self.timeout)
        else:
            # Fallback to threading.Timer for timeout handling
            def timer_handler():
                print("Execution timed out!")
                raise TimeoutError("Execution timed out!")

            # Create a timer to simulate timeout
            self.timer = threading.Timer(self.timeout, timer_handler)
            self.timer.start()

        try:
            start_time = time.time()
            if handler.type.lower().startswith('mcp'):
                result = self.use_mcp_tool(handler, handler.id, handler.type, handler.main_workflow, f"Tool use input: {method} and {params}")
            else:
                result = handler.run({"method": method, "params": params})
            execution_time = time.time() - start_time
            self._log_event("Action executed successfully", "info", execution_time=execution_time)
            return result
        except TimeoutError:
            self._log_event("Action execution timed out", "error")
            return "The action timed out."
        except Exception as e:
            tb = traceback.format_exc()
            # log the full traceback and the context
            self._log_event(
                f"❌ Error executing action. Error {e}\n"
                f"    Method: {method!r}\n"
                f"    Params: {params}\n"
                f"{tb}",
                "error"
            )
            return f"An error occurred with action {method}: {e}"
        finally:
            if LS_SIGNAL and hasattr(LS_SIGNAL, "SIGALRM"):
                LS_SIGNAL.alarm(0)
            elif self.timer and self.timer.is_alive():
                self.timer.cancel()

    def _log_event(self, message, level, **metadata):
        """
        Log an event to GlobalLogger.
        :param message: str - Log message.
        :param level: str - Log level.
        :param metadata: dict - Additional log metadata.
        """
        self.log_event(f"Agent {self.name}: {message}", level)  
