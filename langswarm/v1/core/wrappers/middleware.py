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
    from langswarm.v1.synapse.registry.tools import ToolRegistry
except ImportError:
    ToolRegistry = {}

try:
    from langswarm.v1.memory.registry.rags import RAGRegistry
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
        from langswarm.v1.core.config import ToolDeployer
        try:
            # Try to get tools list from registry
            tools_list = getattr(self.tool_registry, 'tools', [])
            self.tool_deployer = ToolDeployer(tools_list)
        except Exception:
            # Fallback for test environments or incomplete registries
            self.tool_deployer = None
        
        # Initialize workflow context
        self.workflow_context = None
        
        self.ask_to_continue_regex = r"\[AGENT_REQUEST:PROCEED_WITH_INTERNAL_STEP\]"
    
    def set_workflow_context(self, context):
        """Set the workflow context for use in tool calls"""
        print(f"🔍 DEBUG set_workflow_context called with context keys: {list(context.keys()) if context else 'None'}")
        self.workflow_context = context
    
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

        # 2a) Try importlib.resources (Python 3.9+)
        try:
            pkg = importlib.import_module(pkg_name)
            # Get the package directory path for importlib.resources
            pkg_module_file = inspect.getsourcefile(pkg)
            if pkg_module_file:
                pkg_dir = os.path.dirname(os.path.abspath(pkg_module_file))
            else:
                # Fallback: use the package __path__ if available
                pkg_dir = getattr(pkg, '__path__', [None])[0] or '.'
            
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

    def use_mcp_workflow(self, tool_id: str, intent: str, context: str = "") -> Dict:
        """
        Intent-based MCP tool invocation.
        Uses the tool's orchestration workflow to interpret natural language intent.
        """
        from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        # Get tool handler
        handler = None
        if isinstance(self.tool_registry, dict):
            handler = self.tool_registry.get(tool_id)
        else:
            handler = self.tool_registry.get_tool(tool_id)
            
        if not handler:
            raise ValueError(f"Tool '{tool_id}' not found in registry")
        
        # Find and load workflow
        config_path, workflow_path = self._find_workflow_path(handler)
        
        if not os.path.exists(workflow_path):
            # IMPROVED: Check if tool provides its own intent handling
            self._log_event(f"No workflow found for tool {tool_id}, checking tool-level intent support", "warning")
            
            # Check if the tool itself can handle intent-based calls directly
            if hasattr(handler, 'handle_intent'):
                try:
                    self._log_event(f"Using tool-level intent handler: {tool_id}.handle_intent", "info")
                    return handler.handle_intent(intent, context)
                except Exception as tool_error:
                    self._log_event(f"Tool-level intent handler failed: {tool_error}", "error")
            
            # If no workflow and no tool-level intent handler, raise error
            raise FileNotFoundError(f"No workflow found for tool: {tool_id} at {workflow_path} and tool does not support direct intent handling")

        loader = LangSwarmConfigLoader(config_path=config_path)
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Convert tools list back to dictionary if needed
        if isinstance(tools, list):
            # Convert list of tool instances to dict: {tool_id: tool_instance}
            tools_dict = {}
            for tool_instance in tools:
                if hasattr(tool_instance, 'identifier'):
                    tools_dict[tool_instance.identifier] = tool_instance
                elif hasattr(tool_instance, 'name'):
                    tools_dict[tool_instance.name] = tool_instance
                else:
                    # Fallback: use class name
                    tools_dict[type(tool_instance).__name__] = tool_instance
            tools = tools_dict
        
        # Pass user's tool registry to workflow executor instead of isolated tools
        # This ensures MCP workflows have access to the user's configured tools
        user_tools = {}
        user_tools_metadata = {}
        
        if hasattr(self, 'tool_registry') and self.tool_registry:
            if isinstance(self.tool_registry, dict):
                user_tools = self.tool_registry
            else:
                # If it's a registry object, extract the tools
                if hasattr(self.tool_registry, 'tools'):
                    user_tools = self.tool_registry.tools
                elif hasattr(self.tool_registry, 'get_all_tools'):
                    user_tools = self.tool_registry.get_all_tools()
        
        # Also try to get tools_metadata from the agent if available
        if hasattr(self, 'tools_metadata'):
            user_tools_metadata = self.tools_metadata
        elif hasattr(self, 'tool_registry') and hasattr(self.tool_registry, 'tools_metadata'):
            user_tools_metadata = self.tool_registry.tools_metadata
        
        # Merge user tools with any tools from the workflow directory
        # User tools take precedence over isolated workflow tools
        merged_tools = {**tools, **user_tools}
        merged_tools_metadata = {**tools_metadata, **user_tools_metadata}
        
        executor = WorkflowExecutor(workflows, agents, tools=merged_tools, tools_metadata=merged_tools_metadata)
        executor.context["request_id"] = str(uuid.uuid4())
        
        # Format input for intent-based processing
        user_input = f"Intent: {intent}"
        if context:
            user_input += f"\nContext: {context}"
        
        # Pass tool_deployer if available, otherwise let executor handle defaults
        # Provide both user_input and user_query for maximum compatibility with workflows
        kwargs = {
            "user_input": user_input,
            "user_query": user_input  # Alias for backwards compatibility
        }
        if self.tool_deployer:
            kwargs["tool_deployer"] = self.tool_deployer
            
        # Execute the main workflow (use the key that points to the actual workflow list)
        # The workflows dict structure is: {"main_workflow": [{"id": "actual_id", "steps": [...]}]}
        # We want to execute the first workflow in the main_workflow list
        main_workflows = workflows.get("main_workflow", [])
        if main_workflows and isinstance(main_workflows, list) and len(main_workflows) > 0:
            # Get the first workflow definition and use its ID
            first_workflow = main_workflows[0]
            if isinstance(first_workflow, dict) and "id" in first_workflow:
                workflow_id = first_workflow["id"]
            else:
                # Fallback if no ID found
                workflow_id = "main_workflow"
        else:
            # Fallback if no main_workflow found
            workflow_id = "main_workflow"
            
        output = executor.run_workflow(workflow_id, **kwargs)
        
        print("MCP Intent-based output:", output)
        return output

    def use_mcp_direct(self, tool_id: str, method: str, params: Dict) -> Dict:
        """
        Direct MCP tool invocation.
        Bypasses orchestration workflow for simple method calls.
        """
        print(f"🔍 Middleware Direct MCP call: {tool_id}.{method} with params: {list(params.keys()) if params else 'None'}")
        from langswarm.v1.core.utils.workflows.functions import mcp_call
        
        # Get tool handler to determine MCP URL/mode
        handler = None
        
        # First try workflow context if available (prioritizes workflow-loaded tools)
        if self.workflow_context and 'config_loader' in self.workflow_context:
            config_loader = self.workflow_context['config_loader']
            if hasattr(config_loader, 'tools') and isinstance(config_loader.tools, dict):
                handler = config_loader.tools.get(tool_id)
                if handler:
                    print(f"🔍 Found tool '{tool_id}' in workflow context")
        
        # Fallback to regular tool registry
        if not handler:
            if isinstance(self.tool_registry, dict):
                handler = self.tool_registry.get(tool_id)
            else:
                handler = self.tool_registry.get_tool(tool_id)
            
            if handler:
                print(f"🔍 Found tool '{tool_id}' in agent tool registry")
            
        if not handler:
            available_tools = []
            # Try to get available tools from both sources for better error message
            if self.workflow_context and 'config_loader' in self.workflow_context:
                config_loader = self.workflow_context['config_loader']
                if hasattr(config_loader, 'tools') and isinstance(config_loader.tools, dict):
                    available_tools.extend(config_loader.tools.keys())
            
            if isinstance(self.tool_registry, dict):
                available_tools.extend(self.tool_registry.keys())
            elif hasattr(self.tool_registry, 'tools'):
                available_tools.extend(getattr(self.tool_registry, 'tools', {}).keys())
                
            available_tools = list(set(available_tools))  # Remove duplicates
            error_msg = f"Tool '{tool_id}' not found in registry. Available tools: {available_tools}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Build MCP URL based on tool configuration
        # First check if it's a local mode MCP tool
        local_mode = getattr(handler, 'local_mode', False)
        if local_mode:
            mcp_url = f"local://{tool_id}"
        elif hasattr(handler, 'mcp_url') and handler.mcp_url:
            mcp_url = handler.mcp_url
        else:
            # For MCP tools without explicit URL, default to local mode
            # This handles cases where tools are configured for local operation
            tool_type = getattr(handler, 'identifier', tool_id)
            if any(mcp_type in str(type(handler)).lower() for mcp_type in ['mcp', 'filesystem', 'forms', 'github']):
                print(f"🔧 Defaulting to local mode for MCP tool '{tool_id}'")
                mcp_url = f"local://{tool_id}"
            else:
                raise ValueError(f"Tool '{tool_id}' has no MCP URL configuration")
        
        # Make direct MCP call
        payload = {
            "name": method,
            "arguments": params
        }
        
        # Build context with tool_deployer and workflow context if available
        context = {}
        if self.tool_deployer:
            context["tool_deployer"] = self.tool_deployer
        
        # Include workflow context if available (contains config_loader for tool instances)
        print(f"🔍 DEBUG middleware: self.workflow_context = {type(self.workflow_context) if self.workflow_context else 'None'}")
        if self.workflow_context:
            print(f"🔍 DEBUG middleware: workflow_context keys = {list(self.workflow_context.keys())}")
            context.update(self.workflow_context)
        else:
            print(f"🔍 DEBUG middleware: No workflow context available")
            
        result = mcp_call(
            mcp_url=mcp_url,
            payload=payload,
            context=context
        )
        
        print("MCP Direct output:", result)
        return result

    def use_mcp_tool(self, tool, tool_id: str, tool_type: str, workflow_id: str, input_data: str) -> Dict:
        """
        Legacy method for backward compatibility.
        High-level entrypoint to call an MCP tool via its associated workflow.
        - Loads workflow from langswarm/mcp/tools/{tool_id}/workflows.yaml
        - Injects input_data into the workflow
        - Returns the output from the subflow
        """
        from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        #print("tool_type", tool_type)
        #workflow_path = os.path.join("..", "..", "mcp", "tools", tool_id, "workflows.yaml")
        config_path, workflow_path = self._find_workflow_path(tool)

        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"No workflow found for tool: {tool_id} at {workflow_path}")

        #print('Load Config...', config_path)
        loader = LangSwarmConfigLoader(config_path=config_path)
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        #print('Load Workflow...', workflows)
        executor = WorkflowExecutor(workflows, agents)
        executor.context["request_id"] = str(uuid.uuid4())  # Unique per request
        
        #print("input_data:", input_data)
        # Pass tool_deployer if available
        kwargs = {"user_input": input_data}
        if self.tool_deployer:
            kwargs["tool_deployer"] = self.tool_deployer
            
        output = executor.run_workflow(workflow_id, **kwargs)

        print("MCP output", output)
        return output

    def to_middleware(self, agent_input):
        """
        Enhanced middleware that supports both intent-based and direct MCP tool patterns.
        
        Intent-based: {"mcp": {"tool": "github_mcp", "intent": "create issue", "context": "..."}}
        Direct: {"mcp": {"tool": "filesystem", "method": "read_file", "params": {"path": "/tmp/file"}}}

        :param agent_input: dict - The agent's structured input.
        :return: Tuple[int, str] - (status_code, result).
        """
        
        # CRITICAL: Check if middleware is disabled for this agent
        if hasattr(self, '_AgentWrapper__allow_middleware') and not self._AgentWrapper__allow_middleware:
            # Middleware is disabled - extract response text and ignore any tool calls
            if isinstance(agent_input, dict):
                if 'response' in agent_input:
                    # Extract the guidance/response and return it (ignore mcp field)
                    self._log_event("Middleware disabled - returning response text, ignoring tool calls", "info")
                    return 200, agent_input['response']
                elif 'mcp' in agent_input:
                    # ERROR: Internal agent making tool calls without providing response guidance
                    # This indicates a configuration or prompt issue that should be fixed
                    error_msg = f"CONFIGURATION ERROR: Internal agent '{getattr(self, 'name', 'unknown')}' attempted tool call without providing response guidance. This agent should be configured to provide text responses only."
                    self._log_event(error_msg, "error")
                    return 500, error_msg
                else:
                    # Return raw input if it's a simple text response
                    return 200, str(agent_input)
            else:
                # Return raw input as string for non-dict inputs
                return 200, str(agent_input)
        
        # ToDo: Handle RAG
        # ToDo: Handle multiple actions
        # ToDo: Validate agent_input
        
        if not agent_input:
            # If no action is detected, return input unchanged
            self._log_event("No action detected, forwarding input", "info")
            return 200, agent_input
            
        # Ensure agent_input is a dictionary
        if not isinstance(agent_input, dict):
            self._log_event(f"Invalid agent_input type: {type(agent_input)}, expected dict", "error")
            return 400, f"Invalid input type: {type(agent_input)}, expected dict"

        # Handle MCP-specific routing
        if 'mcp' in agent_input:
            mcp_data = agent_input['mcp']
            tool_id = mcp_data.get('tool')
            
            if not tool_id:
                return 400, "MCP request missing 'tool' field"
            
            try:
                if 'intent' in mcp_data:
                    # Intent-based pattern: Use tool's orchestration workflow
                    self._log_event(f"Using intent-based MCP: {tool_id}", "info")
                    result = self.use_mcp_workflow(
                        tool_id=tool_id,
                        intent=mcp_data['intent'],
                        context=mcp_data.get('context', '')
                    )
                    return 201, json.dumps(result, indent=2)
                    
                elif 'method' in mcp_data:
                    # Direct pattern: Call specific method
                    self._log_event(f"Using direct MCP: {tool_id}.{mcp_data['method']}", "info")
                    result = self.use_mcp_direct(
                        tool_id=tool_id,
                        method=mcp_data['method'],
                        params=mcp_data.get('params', {})
                    )
                    
                    # Enhanced error handling for parameter validation and retry guidance
                    if isinstance(result, dict):
                        if result.get('critical'):
                            error_msg = f"🚨 CRITICAL MCP TOOL FAILURE: {tool_id}.{mcp_data['method']} - {result.get('error', 'Unknown error')}"
                            print(error_msg)
                            self._log_event(error_msg, "error")
                        elif result.get('error_type') == 'parameter_validation_error':
                            # Handle parameter validation errors with actionable feedback
                            self._handle_parameter_validation_error(tool_id, mcp_data['method'], result)
                    
                    return 201, json.dumps(result, indent=2)
                    
                else:
                    return 400, "MCP request must have either 'intent' or 'method' field"
                    
            except Exception as e:
                self._log_event(f"MCP tool {tool_id} error: {e}", "error")
                return 500, f"[ERROR] {str(e)}"

        # Detect action type for legacy tools
        try:
            actions = [{"_id": key, **value} for key, value in agent_input.items()]
        except AttributeError as e:
            self._log_event(f"Error processing legacy actions: {e}, agent_input: {agent_input}", "error")
            return 400, f"Unable to process input: {agent_input}"
        
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
            if hasattr(handler, 'type') and handler.type.lower().startswith('mcp'):
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

    def _handle_parameter_validation_error(self, tool_id, method, error_result):
        """
        Handle parameter validation errors with enhanced logging and retry guidance.
        This provides actionable feedback to help agents correct their usage.
        """
        guidance = error_result.get('guidance', 'Parameter validation failed')
        retry_enabled = error_result.get('retry_enabled', True)
        
        # Log the validation error with actionable information
        self._log_event(
            f"Parameter validation failed for {tool_id}.{method}: {guidance}", 
            "warning"
        )
        
        # Log retry information
        if retry_enabled:
            self._log_event(
                f"Retry enabled for {tool_id}.{method} - agent should correct parameters and try again", 
                "info"
            )
            print(f"🔄 RETRY GUIDANCE: {guidance}")
        else:
            self._log_event(
                f"Retry disabled for {tool_id}.{method} - agent will receive error without retry suggestion", 
                "warning"
            )
            print(f"❌ NO RETRY: {guidance}")
        
        # Optional: Add retry tracking (could be used for analytics)
        if hasattr(self, '_retry_tracker'):
            self._retry_tracker.record_validation_error(tool_id, method, guidance)
    
    def _log_event(self, message, level, **metadata):
        """
        Log an event to GlobalLogger.
        :param message: str - Log message.
        :param level: str - Log level.
        :param metadata: dict - Additional log metadata.
        """
        self.log_event(f"Agent {self.name}: {message}", level)  
