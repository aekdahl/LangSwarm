import re
import sys

try:
    import signal as LS_SIGNAL
except ImportError:
    LS_SIGNAL = None

import threading
import time
import json

from typing import List

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
        self.rag_registry = rag_registry or RAGRegistry()
        self.tool_registry = tool_registry or ToolRegistry()
        self.plugin_registry = plugin_registry or PluginRegistry()
        #self.rag_command_regex = r"execute_(?:rag|retriever):([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{[^}]*\})"
        
        # self.tool_command_regex = r"execute_tool:([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{[^}]*\})"
        #self.tool_command_regex = r"execute_tool:([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{.*\})"
        
        #self.plugin_command_regex = r"execute_plugin:([a-zA-Z0-9_]+)\|([a-zA-Z0-9_]+)\|(\{[^}]*\})"
        #self.request_rags_regex = r"request:rags\|([^\s<].*)"
        #self.request_tools_regex = r"request:tools\|([^\s<].*)"
        #self.request_plugin_regex = r"request:plugins\|([^\s<].*)"
        self.ask_to_continue_regex = r"\[AGENT_REQUEST:PROCEED_WITH_INTERNAL_STEP\]"
        
        # Not working as intended, leave for now
        # ToDo: Fix this check
        #self.check_for_continuation = r"(?<=\b)(?:I(?:'m| am| will| am now| will now| will go ahead)\s+(?:go(?:ing)? to|proceed(?:ing)? to|execute|start|begin|attempt|perform|carry out)|Executing\s+the\b)[^.!?]*[.!?](?!(?:\s+\S|$))"
        # ToDo: Add these cases to regex: "Let’s proceed with that now."
        # "Executing the fetch action now."

    def to_middleware(self, agent_input):
        """
        Process agent input and route it appropriately.

        :param agent_input: str - The agent's input.
        :return: Tuple[int, str] - (status_code, result).
        """
        
        # ToDo: Handle RAG

        # Detect action type
        actions = self._parse_action(agent_input)
        if actions:
            #status, action_result = self._route_action(*action_details)
            #return status, self._respond_to_user([agent_input, action_result])
        
            # Process each action and collect responses
            results = [self._route_action(*action) for action in actions]

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

        # If no action is detected, return input unchanged
        self._log_event("No action detected, forwarding input", "info")
        return 200, agent_input
    
    def _extract_json_from_text(self, text):
        """
        Extracts and merges multiple JSON blocks enclosed within START>>> and <<<END tags (case insensitive).
        Parses each JSON block separately and combines them into a single 'calls' list.
        Handles malformed JSON gracefully.
        """
        #pattern = re.compile(
        #    r"(?i)START>>>(.*?)<<<END", 
        #    re.DOTALL
        #)  # Case insensitive match
        
        pattern = re.compile(
            r"START>>>\s*(\{[\s\S]*?\})\s*<<<END", 
            re.DOTALL | re.IGNORECASE | re.MULTILINE
        ) # Case insensitive match
        
        matches = pattern.findall(text)

        if not matches:
            #self._log_event(f"No match found via regex in: {text}", "info")
            print("No match found via regex. Trying manual extraction...")

            # Step 2: If regex fails, manually search for START>>> and <<<END
            start_idx = text.lower().find("start>>>")
            end_idx = text.lower().find("<<<end")

            if start_idx != -1 and end_idx != -1:
                raw_section = text[start_idx + 8:end_idx].strip()  # Extract between START>>> and <<<END
                #print("Manually Extracted Raw Section:", raw_section)

                # Locate the first '{' and last '}'
                json_start = raw_section.find("{")
                json_end = raw_section.rfind("}")

                if json_start != -1 and json_end != -1:
                    raw_json_text = raw_section[json_start:json_end + 1]  # Get only valid JSON
                    print("Cleaned Extracted JSON:", raw_json_text)
                    matches = [raw_json_text]
            elif start_idx != -1:
                self._log_event(f"Found start, but not end in: {text}", "info")
            elif end_idx != -1:
                self._log_event(f"Found end, but not start in: {text}", "info")

        all_calls = []  # Collect all calls across multiple JSON blocks

        for json_str in matches:
            json_str = json_str.strip()
            try:
                parsed_json = self.utils.safe_json_loads(json_str)

                # Ensure "calls" is always structured as a list
                if isinstance(parsed_json, dict) and "calls" in parsed_json:
                    if not isinstance(parsed_json["calls"], list):
                        parsed_json["calls"] = [parsed_json["calls"]]  # Wrap single call in list
                    all_calls.extend(parsed_json["calls"])
                else:
                    # If no "calls" key exists, wrap entire JSON object in a list
                    all_calls.append(parsed_json)

            except json.JSONDecodeError as e:
                # Extract problematic JSON snippet
                error_position = e.pos
                snippet = json_str[max(0, error_position - 20):error_position + 20]
                print(f"JSON parsing error at position {error_position}: {snippet}")
                self._log_event(f"JSON parsing error at position {error_position}: {snippet}", "info")

        self._log_event(f"Returning number of calls. {len(all_calls)}", "info")
        return all_calls if all_calls else []  # Return as merged JSON structure

    def _parse_action(self, reasoning: str) -> list:
        """
        Parse the reasoning output to detect tool or plugin actions.

        :param reasoning: str - The reasoning output containing potential actions.
        :return: List[Tuple[str, str, str, str, dict]] - List of (action_type, action_method, action_name, action, params).
        
        {
          "type": "tool",
          "method": "execute",
          "instance_name": "local_file_system",
          "action": "create_file",
          "parameters": {
            "filename": "test.py",
            "content": "print('Hello World')"
          }
        }
        """
        actions = []
        reasoning = self.utils._parse_for_actions(reasoning)
        
        try:
            actions = [(
                x.get("type"), 
                x.get("method"), 
                x.get("instance_name", x.get("name", "undefined")), 
                x.get("action", "undefined"), 
                x.get("parameters", {})
            ) for x in self._extract_json_from_text(reasoning)]
            self._log_event(f"Identified actions: {len(actions)}", "info")
        except (SyntaxError, ValueError, json.JSONDecodeError) as e:
            self._log_event(f"Failed to parse action: {e}", "warning")

        return actions if actions else None

    def _route_action(self, action_type, action_method, action_name, action, arguments):
        """
        Route actions to the appropriate handler with timeout handling.
        :param action_type: str - Type of action (tool or plugin).
        :param action_method: str - Method of action (execute or request).
        :param action_name: str - Name of the action.
        :param params: dict - Parameters for the action.
        :return: Tuple[int, str] - (status_code, result).
        """
        handler = None
        
        if action_type in ["rag", "rags", "retriever", "retrievers"]:
            if action_method == "execute":
                handler = self.rag_registry.get_rag(action_name)
            elif action_method == "request":
                handler = self.rag_registry.search_rags(action_name)
                return 201, json.dumps(handler)
        elif action_type in ["tool", "tools"]:
            if action_method == "execute":
                handler = self.tool_registry.get_tool(action_name)
            elif action_method == "request":
                handler = self.tool_registry.search_tools(action_name)
                return 201, json.dumps(handler)
        elif action_type in ["plugin", "plugins"]:
            if action_method == "execute":
                handler = self.plugin_registry.get_plugin(action_name)
            elif action_method == "request":
                handler = self.plugin_registry.search_plugins(action_name)
                return 201, json.dumps(handler)

        # ToDo: OptimizerManager holds a query expander if needed
        
        #retrieved_docs = self.query_retrievers(query, use_all, retriever_names)

        # Aggregate and rank results (simplified ranking here)
        # ToDo: Add Rerank to get the best result first
        # ToDo: OptimizerManager holds a Reranker if needed
        
        if handler:
            self._log_event(f"Executing: {action_name} - {action}", "info")
            return 201, self._execute_with_timeout(handler, action, arguments)

        self._log_event(f"Action not found: {action_type} - {action_name}", "error")
        return 404, f"{action_type.capitalize()} '{action_name}' not found."

    def _execute_with_timeout(self, handler, action, arguments):
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
            result = handler.run(arguments, action=action)
            execution_time = time.time() - start_time
            self._log_event("Action executed successfully", "info", execution_time=execution_time)
            return result
        except TimeoutError:
            self._log_event("Action execution timed out", "error")
            return "The action timed out."
        except Exception as e:
            self._log_event(f"Error executing action {action}, with args: {arguments} - {e}", "error")
            return f"An error occurred with action {action}: {e}"
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
        self.log_event(f"ReAct agent {self.name}: {message}", level)  