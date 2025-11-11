"""
Debug Integration for LangSwarm

This module provides integration hooks to inject debug tracing into existing
LangSwarm components without major code changes. It uses monkey patching and
mixins to add tracing capabilities.
"""

import functools
import json
from typing import Any, Dict, Optional
from .tracer import get_debug_tracer, trace_event


def serialize_agent_config(agent, max_depth=3, _current_depth=0):
    """
    Safely serialize an agent's configuration and settings for debug tracing.
    
    Args:
        agent: The agent object to serialize
        max_depth: Maximum recursion depth to prevent infinite loops
        _current_depth: Current recursion depth (internal use)
    
    Returns:
        Dict: Serialized agent configuration
    """
    if _current_depth >= max_depth:
        return {"_serialization_limit_reached": True, "type": str(type(agent))}
    
    try:
        config = {
            "agent_name": getattr(agent, 'name', None),
            "agent_type": type(agent).__name__,
            "agent_class": f"{agent.__class__.__module__}.{agent.__class__.__name__}",
            "model": getattr(agent, 'model', None),
            "agent_repr": repr(agent)[:200],
        }
        
        # Core configuration
        if hasattr(agent, 'model_details'):
            config["model_details"] = _safe_serialize(agent.model_details, max_depth, _current_depth + 1)
        
        # Memory configuration
        config["memory_info"] = {
            "has_memory": hasattr(agent, 'memory') and agent.memory is not None,
            "is_conversational": getattr(agent, 'is_conversational', False),
            "memory_adapter": str(type(getattr(agent, 'memory_adapter', None))),
            "memory_size": len(getattr(agent, 'in_memory', [])) if hasattr(agent, 'in_memory') and agent.in_memory else 0
        }
        
        # Tool configuration
        tool_info = {
            "has_tool_registry": hasattr(agent, 'tool_registry') and agent.tool_registry is not None,
            "tools_count": 0,
            "tool_names": []
        }
        
        if hasattr(agent, 'tool_registry') and agent.tool_registry:
            try:
                # Try different ways to get tool information
                if hasattr(agent.tool_registry, 'list_tools'):
                    tools = agent.tool_registry.list_tools()
                    tool_info["tools_count"] = len(tools)
                    tool_info["tool_names"] = [str(tool) for tool in tools[:10]]  # Limit to first 10
                elif hasattr(agent.tool_registry, 'tools'):
                    tools_dict = getattr(agent.tool_registry, 'tools', {})
                    tool_info["tools_count"] = len(tools_dict)
                    tool_info["tool_names"] = list(tools_dict.keys())[:10]  # Limit to first 10
                elif isinstance(agent.tool_registry, dict):
                    tool_info["tools_count"] = len(agent.tool_registry)
                    tool_info["tool_names"] = list(agent.tool_registry.keys())[:10]  # Limit to first 10
            except Exception as e:
                tool_info["tool_error"] = str(e)
        
        config["tool_info"] = tool_info
        
        # Session and streaming configuration
        config["session_info"] = {
            "session_manager": str(type(getattr(agent, 'session_manager', None))),
            "current_session_id": getattr(agent, 'current_session_id', None),
            "response_mode": getattr(agent, 'response_mode', None),
            "streaming_enabled": getattr(agent, 'streaming_enabled', False)
        }
        
        # Agent-specific settings
        config["agent_settings"] = {
            "timeout": getattr(agent, 'timeout', None),
            "max_response_length": getattr(agent, 'max_response_length', None),
            "max_tokens": getattr(agent, 'max_tokens', None),
            "use_native_tool_calling": getattr(agent, 'use_native_tool_calling', None),
            "context_limit": getattr(agent, 'model_details', {}).get('limit') if hasattr(agent, 'model_details') else None
        }
        
        # Plugin and RAG configuration
        config["extension_info"] = {
            "has_plugin_registry": hasattr(agent, 'plugin_registry') and agent.plugin_registry is not None,
            "has_rag_registry": hasattr(agent, 'rag_registry') and agent.rag_registry is not None,
            "has_broker": hasattr(agent, 'broker') and agent.broker is not None
        }
        
        # System prompt info (complete for debugging dynamic content)
        if hasattr(agent, 'system_prompt') and agent.system_prompt:
            system_prompt = str(agent.system_prompt)
            config["system_prompt_info"] = {
                "has_system_prompt": True,
                "system_prompt_length": len(system_prompt),
                "system_prompt_full": system_prompt  # Full prompt for debugging dynamic content
            }
        else:
            config["system_prompt_info"] = {"has_system_prompt": False}
        
        return config
        
    except Exception as e:
        return {
            "serialization_error": str(e),
            "agent_type": str(type(agent)),
            "agent_repr": repr(agent)[:200]
        }


def _safe_serialize(obj, max_depth=3, _current_depth=0):
    """
    Safely serialize an object, handling circular references and complex types.
    """
    if _current_depth >= max_depth:
        return {"_serialization_limit_reached": True, "type": str(type(obj))}
    
    try:
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [_safe_serialize(item, max_depth, _current_depth + 1) for item in obj[:10]]  # Limit list length
        elif isinstance(obj, dict):
            return {k: _safe_serialize(v, max_depth, _current_depth + 1) for k, v in list(obj.items())[:10]}  # Limit dict size
        else:
            # For complex objects, just return type and string representation
            return {
                "type": str(type(obj)),
                "value": str(obj)[:200]  # Truncate long strings
            }
    except Exception as e:
        return {"serialization_error": str(e), "type": str(type(obj))}


class TracingMixin:
    """
    Mixin to add tracing capabilities to any class.
    Can be used with agents, workflows, or other components.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._trace_id: Optional[str] = None
    
    def _get_trace_context(self) -> Dict[str, Any]:
        """Get tracing context for this instance"""
        context = {}
        if hasattr(self, 'name'):
            context['instance_name'] = self.name
        if hasattr(self, '__class__'):
            context['class'] = self.__class__.__name__
        return context
    
    def _trace_event(self, event_type: str, component: str, operation: str, 
                    message: str, level: str = "INFO", data: Optional[Dict[str, Any]] = None):
        """Log a trace event with instance context"""
        combined_data = self._get_trace_context()
        if data:
            combined_data.update(data)
        
        trace_event(event_type, component, operation, message, level, combined_data)
    
    def _trace_info(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an info trace event"""
        component = getattr(self, '_trace_component', 'unknown')
        self._trace_event("INFO", component, operation, message, "INFO", data)
    
    def _trace_error(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an error trace event"""
        component = getattr(self, '_trace_component', 'unknown')
        self._trace_event("ERROR", component, operation, message, "ERROR", data)


def trace_agent_wrapper():
    """
    Monkey patch the AgentWrapper class to add debug tracing.
    This adds tracing to the main chat() and _call_agent() methods.
    """
    try:
        from langswarm.v1.core.wrappers.generic import AgentWrapper
        
        # Store original methods
        original_chat = AgentWrapper.chat
        original_call_agent = AgentWrapper._call_agent
        
        def traced_chat(self, q=None, reset=False, erase_query=False, 
                       remove_linebreaks=False, session_id=None, 
                       start_new_session=False, **kwargs):
            """Traced version of AgentWrapper.chat()"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_chat(self, q, reset, erase_query, remove_linebreaks, 
                                   session_id, start_new_session, **kwargs)
            
            with tracer.trace_agent_query(self.name, q or "No query") as trace_context:
                # Log session info
                if session_id or start_new_session:
                    tracer.log_event(
                        "INFO", "agent", "session_management",
                        f"Session management: session_id={session_id}, start_new={start_new_session}",
                        data={"session_id": session_id, "start_new_session": start_new_session}
                    )
                
                # Log memory reset if applicable
                if reset:
                    tracer.log_event(
                        "INFO", "agent", "memory_reset",
                        f"Resetting agent memory for {self.name}"
                    )
                
                try:
                    result = original_chat(self, q, reset, erase_query, remove_linebreaks,
                                         session_id, start_new_session, **kwargs)
                    
                    # Log successful response
                    tracer.log_event(
                        "INFO", "agent", "response_generated",
                        f"Agent {self.name} generated response",
                        data={"response_length": len(result) if result else 0}
                    )
                    
                    return result
                    
                except Exception as e:
                    # Log error details
                    tracer.log_event(
                        "ERROR", "agent", "chat_error",
                        f"Error in agent chat: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        def traced_call_agent(self, q, erase_query=False, remove_linebreaks=False):
            """Traced version of AgentWrapper._call_agent()"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_call_agent(self, q, erase_query, remove_linebreaks)
            
            with tracer.trace_operation("agent", "llm_call", f"Calling LLM for agent {self.name}") as trace_context:
                # Log query details
                tracer.log_event(
                    "INFO", "agent", "query_processing",
                    f"Processing query for agent {self.name}",
                    data={
                        "query": q,
                        "query_length": len(q) if q else 0,
                        "erase_query": erase_query,
                        "remove_linebreaks": remove_linebreaks,
                        "agent_type": type(self.agent).__name__,
                        "model": getattr(self, 'model', 'unknown')
                    }
                )
                
                # Log memory state
                if hasattr(self, 'in_memory') and self.in_memory:
                    tracer.log_event(
                        "INFO", "agent", "memory_state",
                        f"Agent has {len(self.in_memory)} messages in memory",
                        data={"memory_size": len(self.in_memory)}
                    )
                
                try:
                    result = original_call_agent(self, q, erase_query, remove_linebreaks)
                    
                    # Log response details
                    tracer.log_event(
                        "INFO", "agent", "llm_response",
                        f"LLM responded for agent {self.name}",
                        data={
                            "response": result,
                            "response_length": len(result) if result else 0
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "agent", "llm_error",
                        f"LLM call failed for agent {self.name}: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        # Store original streaming method
        original_call_chat_completions = AgentWrapper._call_chat_completions_api
        
        def traced_call_chat_completions_api(self, messages, config=None):
            """Traced version of AgentWrapper._call_chat_completions_api() with streaming capture"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_call_chat_completions(self, messages, config)
            
            streaming_enabled = config and config.get('streaming', {}).get('stream', False)
            
            try:
                tracer.log_event(
                    "START", "llm", "api_call",
                    f"Starting Chat Completions API call for {self.name}",
                    data={
                        "agent_name": self.name,
                        "model": getattr(self, 'model', 'unknown'),
                        "message_count": len(messages) if messages else 0,
                        "streaming_enabled": streaming_enabled
                    }
                )
                
                # If streaming, capture streaming data
                if streaming_enabled:
                    # Call original method and capture streaming details
                    result = original_call_chat_completions(self, messages, config)
                    
                    # Extract streaming information from the result if available
                    streaming_data = {}
                    if hasattr(self, '_last_completion') and self._last_completion:
                        completion = self._last_completion
                        if hasattr(completion, '_streaming_metadata'):
                            streaming_data = completion._streaming_metadata
                    
                    # Log streaming completion
                    tracer.log_event(
                        "INFO", "llm", "streaming_complete",
                        f"Streaming response completed for {self.name}",
                        data={
                            "agent_name": self.name,
                            "streaming_metadata": streaming_data,
                            "response_type": str(type(result)),
                            "has_response": result.get("response") is not None if isinstance(result, dict) else "unknown",
                            "has_tool_calls": "mcp" in result if isinstance(result, dict) else "unknown",
                            "tool_calls": result.get("mcp") if isinstance(result, dict) else None
                        }
                    )
                else:
                    # Non-streaming call
                    result = original_call_chat_completions(self, messages, config)
                
                tracer.log_event(
                    "END", "llm", "api_call", 
                    f"Completed Chat Completions API call for {self.name}",
                    data={
                        "agent_name": self.name,
                        "response_type": str(type(result)),
                        "has_response": result.get("response") is not None if isinstance(result, dict) else "unknown",
                        "has_tool_calls": "mcp" in result if isinstance(result, dict) else "unknown"
                    }
                )
                
                return result
                
            except Exception as e:
                tracer.log_event(
                    "ERROR", "llm", "api_call_error",
                    f"Chat Completions API call failed for {self.name}: {str(e)}",
                    level="ERROR",
                    data={"error_type": type(e).__name__, "error_message": str(e)}
                )
                raise
        
        # Apply monkey patches
        AgentWrapper.chat = traced_chat
        AgentWrapper._call_agent = traced_call_agent
        AgentWrapper._call_chat_completions_api = traced_call_chat_completions_api
        
        print("✅ Debug tracing enabled for AgentWrapper")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to enable agent tracing: {e}")
        return False


def trace_langswarm_config_loader():
    """
    Monkey patch the LangSwarmConfigLoader to add comprehensive debug tracing.
    This adds tracing to all major configuration loading and initialization steps.
    """
    try:
        from langswarm.v1.core.config import LangSwarmConfigLoader
        
        # Store original methods
        original_load = LangSwarmConfigLoader.load
        original_load_config_files = LangSwarmConfigLoader._load_config_files
        original_initialize_agents = LangSwarmConfigLoader._initialize_agents
        original_initialize_tools = LangSwarmConfigLoader._initialize_tools
        original_initialize_retrievers = LangSwarmConfigLoader._initialize_retrievers
        original_initialize_brokers = LangSwarmConfigLoader._initialize_brokers
        original_initialize_plugins = LangSwarmConfigLoader._initialize_plugins
        
        def traced_load(self):
            """Traced version of LangSwarmConfigLoader.load()"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_load(self)
            
            with tracer.trace_operation("config_loader", "load", "Loading LangSwarm configuration") as trace_context:
                tracer.log_event(
                    "INFO", "config_loader", "load_start",
                    f"Starting configuration load from {self.config_path}",
                    data={
                        "config_path": str(self.config_path),
                        "is_unified": self._is_unified_config() if hasattr(self, '_is_unified_config') else "unknown"
                    }
                )
                
                try:
                    result = original_load(self)
                    
                    # Log configuration summary
                    tracer.log_event(
                        "INFO", "config_loader", "load_complete",
                        "Configuration loading completed successfully",
                        data={
                            "agents_count": len(self.agents),
                            "tools_count": len(self.tools),
                            "workflows_count": len(self.config_data.get('workflows', {})),
                            "brokers_count": len(self.brokers),
                            "retrievers_count": len(self.retrievers)
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "config_loader", "load_error",
                        f"Configuration loading failed: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        def traced_load_config_files(self):
            """Traced version of config file loading"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_load_config_files(self)
            
            with tracer.trace_operation("config_loader", "load_files", "Loading configuration files") as trace_context:
                tracer.log_event(
                    "INFO", "config_loader", "files_scan_start",
                    f"Scanning for configuration files in {self.config_path}"
                )
                
                try:
                    result = original_load_config_files(self)
                    
                    tracer.log_event(
                        "INFO", "config_loader", "files_loaded",
                        "Configuration files loaded successfully",
                        data={"config_keys": list(self.config_data.keys())}
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "config_loader", "files_error",
                        f"Failed to load configuration files: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        def traced_initialize_agents(self):
            """Traced version of agent initialization"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_initialize_agents(self)
            
            with tracer.trace_operation("config_loader", "init_agents", "Initializing agents") as trace_context:
                agent_configs = self.config_data.get('agents', [])
                tracer.log_event(
                    "INFO", "config_loader", "agents_init_start",
                    f"Initializing {len(agent_configs)} agents",
                    data={"agent_count": len(agent_configs)}
                )
                
                try:
                    result = original_initialize_agents(self)
                    
                    # Log each initialized agent
                    for agent_id, agent in self.agents.items():
                        # Helper function to properly count tools
                        def count_agent_tools(agent):
                            # Handle case where agent initialization failed (stored as dict)
                            if isinstance(agent, dict):
                                if agent.get('status') == 'pending_api_key':
                                    # Check the original config for tools
                                    config = agent.get('config', {})
                                    tools_config = config.get('tools', [])
                                    return len(tools_config) if tools_config else 0
                                return 0
                            
                            # Handle normal agent objects
                            if not hasattr(agent, 'tool_registry') or not agent.tool_registry:
                                return 0
                                
                            # Check different tool registry implementations
                            if hasattr(agent.tool_registry, 'list_tools'):
                                try:
                                    tools = agent.tool_registry.list_tools()
                                    return len(tools)
                                except Exception:
                                    pass
                                    
                            # Fallback: check if tool_registry has tools dict
                            if hasattr(agent.tool_registry, 'tools'):
                                tools_dict = getattr(agent.tool_registry, 'tools', {})
                                return len(tools_dict)
                                
                            # Fallback: check if tool_registry is a dict itself
                            if isinstance(agent.tool_registry, dict):
                                return len(agent.tool_registry)
                                
                            return 0
                        
                        # Handle different agent states (actual agent vs pending config)
                        if isinstance(agent, dict) and agent.get('status') == 'pending_api_key':
                            tracer.log_event(
                                "WARN", "config_loader", "agent_initialization_skipped",
                                f"Agent '{agent_id}' initialization skipped due to missing API key",
                                data={
                                    "agent_id": agent_id,
                                    "agent_type": "pending",
                                    "model": agent.get('config', {}).get('model', 'unknown'),
                                    "has_memory": False,
                                    "tools_count": count_agent_tools(agent),
                                    "error": agent.get('error', 'Unknown error')
                                }
                            )
                        else:
                            tracer.log_event(
                                "INFO", "config_loader", "agent_initialized",
                                f"Agent '{agent_id}' initialized successfully",
                                data={
                                    "agent_id": agent_id,
                                    "agent_type": type(agent).__name__,
                                    "model": getattr(agent, 'model', 'unknown'),
                                    "has_memory": hasattr(agent, 'memory') and agent.memory is not None,
                                    "tools_count": count_agent_tools(agent)
                                }
                            )
                    
                    tracer.log_event(
                        "INFO", "config_loader", "agents_init_complete",
                        f"All {len(self.agents)} agents initialized successfully"
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "config_loader", "agents_init_error",
                        f"Agent initialization failed: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        def traced_initialize_tools(self):
            """Traced version of tool initialization"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_initialize_tools(self)
            
            with tracer.trace_operation("config_loader", "init_tools", "Initializing tools") as trace_context:
                tool_configs = self.config_data.get('tools', {})
                
                # Handle both dict and list formats for tool_configs
                if isinstance(tool_configs, dict):
                    tool_names = list(tool_configs.keys())
                elif isinstance(tool_configs, list):
                    tool_names = [tool.get('id', 'unnamed') for tool in tool_configs if isinstance(tool, dict)]
                else:
                    tool_names = []
                
                tracer.log_event(
                    "INFO", "config_loader", "tools_init_start",
                    f"Initializing {len(tool_configs)} tools",
                    data={"tool_count": len(tool_configs), "tool_names": tool_names}
                )
                
                try:
                    result = original_initialize_tools(self)
                    
                    # Log each initialized tool
                    for tool_id, tool in self.tools.items():
                        tracer.log_event(
                            "INFO", "config_loader", "tool_initialized",
                            f"Tool '{tool_id}' initialized successfully",
                            data={
                                "tool_id": tool_id,
                                "tool_type": type(tool).__name__,
                                "tool_class": tool.__class__.__module__ + "." + tool.__class__.__name__
                            }
                        )
                    
                    tracer.log_event(
                        "INFO", "config_loader", "tools_init_complete",
                        f"All {len(self.tools)} tools initialized successfully"
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "config_loader", "tools_init_error",
                        f"Tool initialization failed: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        # Apply monkey patches for deep config loader tracing
        LangSwarmConfigLoader.load = traced_load
        LangSwarmConfigLoader._load_config_files = traced_load_config_files
        LangSwarmConfigLoader._initialize_agents = traced_initialize_agents
        LangSwarmConfigLoader._initialize_tools = traced_initialize_tools
        
        print("✅ Debug tracing enabled for LangSwarmConfigLoader")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to enable config loader tracing: {e}")
        return False


def trace_workflow_executor():
    """
    Monkey patch the workflow executor to add debug tracing.
    This adds tracing to workflow step execution.
    """
    try:
        from langswarm.v1.core.config import LangSwarmConfigLoader
        
        # Store original method
        original_execute_step = LangSwarmConfigLoader._execute_step_inner_sync
        
        def traced_execute_step(self, step: Dict, mark_visited: bool = True):
            """Traced version of workflow step execution"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_execute_step(self, step, mark_visited)
            
            step_id = step.get('id', 'unknown')
            workflow_id = getattr(self, 'workflow_id', 'unknown')
            
            with tracer.trace_workflow_step(workflow_id, step_id, step) as trace_context:
                # Log step details
                tracer.log_event(
                    "INFO", "workflow", "step_start",
                    f"Starting step {step_id} in workflow {workflow_id}",
                    data={
                        "step_id": step_id,
                        "workflow_id": workflow_id,
                        "step_type": self._get_step_type(step),
                        "mark_visited": mark_visited,
                        "step_data": step
                    }
                )
                
                # Check if step was already visited
                visit_key = self._get_visit_key(step)
                if visit_key in self.context.get("visited_steps", {}):
                    tracer.log_event(
                        "INFO", "workflow", "step_skipped",
                        f"Step {step_id} already visited, checking retry logic",
                        data={"visit_key": visit_key}
                    )
                
                try:
                    result = original_execute_step(self, step, mark_visited)
                    
                    # Log successful completion
                    tracer.log_event(
                        "INFO", "workflow", "step_completed",
                        f"Step {step_id} completed successfully",
                        data={"result_type": type(result).__name__ if result else "None"}
                    )
                    
                    return result
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "workflow", "step_error",
                        f"Step {step_id} failed: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        def _get_step_type(self, step: Dict) -> str:
            """Helper to determine step type"""
            if 'agent' in step:
                return 'agent'
            elif 'invoke_workflow' in step:
                return 'invoke_workflow'
            elif 'function' in step:
                return 'function'
            elif 'loop' in step:
                return 'loop'
            elif 'no_mcp' in step:
                return 'no_mcp'
            else:
                return 'unknown'
        
        # Apply monkey patch
        LangSwarmConfigLoader._execute_step_inner_sync = traced_execute_step
        LangSwarmConfigLoader._get_step_type = _get_step_type
        
        print("✅ Debug tracing enabled for WorkflowExecutor")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to enable workflow tracing: {e}")
        return False


def trace_middleware():
    """
    Monkey patch the middleware system to add debug tracing.
    This adds tracing to MCP tool calls.
    """
    try:
        from langswarm.v1.core.wrappers.middleware import MiddlewareMixin
        
        # Check if to_middleware method exists
        if not hasattr(MiddlewareMixin, 'to_middleware'):
            print("⚠️  MiddlewareMixin.to_middleware not found, skipping middleware tracing")
            return True
        
        # Store original method
        original_to_middleware = MiddlewareMixin.to_middleware
        
        def traced_to_middleware(self, parsed_json):
            """Traced version of middleware tool calling"""
            tracer = get_debug_tracer()
            if not tracer or not tracer.enabled:
                return original_to_middleware(self, parsed_json)
            
            mcp_data = parsed_json.get('mcp', {})
            tool_name = mcp_data.get('tool', 'unknown')
            method = mcp_data.get('method', 'unknown')
            params = mcp_data.get('params', {})
            
            with tracer.trace_tool_call(tool_name, method, params) as trace_context:
                # Log tool call details
                tracer.log_event(
                    "INFO", "middleware", "tool_call_start",
                    f"Calling tool {tool_name}.{method}",
                    data={
                        "tool_name": tool_name,
                        "method": method,
                        "params": params,
                        "agent_name": getattr(self, 'name', 'unknown')
                    }
                )
                
                try:
                    status, response = original_to_middleware(self, parsed_json)
                    
                    # Log tool response
                    tracer.log_event(
                        "INFO", "middleware", "tool_call_completed",
                        f"Tool {tool_name}.{method} completed with status {status}",
                        data={
                            "status": status,
                            "response": response,
                            "response_length": len(str(response)) if response else 0
                        }
                    )
                    
                    return status, response
                    
                except Exception as e:
                    tracer.log_event(
                        "ERROR", "middleware", "tool_call_error",
                        f"Tool {tool_name}.{method} failed: {str(e)}",
                        level="ERROR",
                        data={"error_type": type(e).__name__, "error_message": str(e)}
                    )
                    raise
        
        # Apply monkey patch
        MiddlewareMixin.to_middleware = traced_to_middleware
        
        print("✅ Debug tracing enabled for Middleware")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to enable middleware tracing: {e}")
        return False


def enable_debug_tracing(
    output_file: str = "langswarm_debug.jsonl",
    trace_agents: bool = True,
    trace_workflows: bool = True,
    trace_middleware_calls: bool = True,
    trace_config_loader: bool = True
) -> bool:
    """
    Enable debug tracing for LangSwarm components.
    
    Args:
        output_file: Path to output debug log file
        trace_agents: Enable agent tracing
        trace_workflows: Enable workflow tracing  
        trace_middleware_calls: Enable middleware/tool tracing
        trace_config_loader: Enable deep config loader tracing
    
    Returns:
        bool: True if tracing was enabled successfully
    """
    from .tracer import initialize_debug_tracer
    
    # Initialize global tracer
    tracer = initialize_debug_tracer(enabled=True, output_file=output_file)
    
    # Track success
    success = True
    
    # Enable component tracing
    if trace_agents:
        success &= trace_agent_wrapper()
    
    if trace_config_loader:
        success &= trace_langswarm_config_loader()
    
    if trace_workflows:
        success &= trace_workflow_executor()
    
    if trace_middleware_calls:
        success &= trace_middleware()
    
    if success:
        print(f"🎯 Debug tracing enabled! Logs will be written to: {output_file}")
        trace_event("INFO", "debug", "initialization", "Debug tracing system initialized")
    else:
        print("⚠️  Some tracing components failed to initialize")
    
    return success


def disable_debug_tracing():
    """Disable debug tracing by setting the global tracer to None"""
    from .tracer import _global_tracer
    if _global_tracer:
        _global_tracer.enabled = False
        print("🔇 Debug tracing disabled")
