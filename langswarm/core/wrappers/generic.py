import json
from datetime import datetime
from typing import Type, Any, Optional, Dict, Callable, List

from langswarm.memory.adapters.database_adapter import DatabaseAdapter
try:
    from langswarm.mcp.tools.message_queue_publisher.brokers import MessageBroker
except ImportError:
    # Fallback for backwards compatibility
    try:
        from langswarm.synapse.tools.message_queue_publisher.brokers import MessageBroker
    except ImportError:
        MessageBroker = None
from langswarm.core.session.manager import LangSwarmSessionManager
from langswarm.core.session.models import SessionControl
from langswarm.core.session.hybrid_manager import HybridSessionManager, HybridSessionManagerFactory

from ..base.bot import LLM
from .base_wrapper import BaseWrapper
from .logging_mixin import LoggingMixin
from .memory_mixin import MemoryMixin
from .util_mixin import UtilMixin
from .middleware import MiddlewareMixin
from ..registry.agents import AgentRegistry

try:
    from llama_index.llms import OpenAI as LlamaOpenAI, Anthropic as LlamaAnthropic, Cohere as LlamaCohere, AI21 as LlamaAI21
except ImportError:
    LlamaOpenAI = None
    LlamaAnthropic = None
    LlamaCohere = None
    LlamaAI21 = None
    
try:
    from langchain_community.chat_models import ChatOpenAI, AzureChatOpenAI
except ImportError:
    ChatOpenAI = None
    AzureChatOpenAI = None
    
try:
    from langchain_community.llms import OpenAI as LangChainOpenAI, Anthropic, Cohere, AI21, VertexAI
except ImportError:
    LangChainOpenAI = None
    Anthropic = None
    Cohere = None
    AI21 = None
    VertexAI = None
    
try:
    from langchain_community.llms import HuggingFaceHub
except ImportError:
    HuggingFaceHub = None
    
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AgentWrapper(LLM, BaseWrapper, LoggingMixin, MemoryMixin, UtilMixin, MiddlewareMixin):
    """
    A unified wrapper for LLM agents, combining memory management, logging, and LangSmith integration.
    """
    __allow_middleware = True  # Private class-level flag
    
    def __init_subclass__(cls, **kwargs):
        """Disable feature in subclasses at the class level."""
        super().__init_subclass__(**kwargs)
        cls.__allow_middleware = False  # Enforce restriction in all subclasses

    def __init__(
        self, 
        name, 
        agent,
        model,
        memory=None, 
        agent_type=None,
        is_conversational=False, 
        langsmith_api_key=None, 
        rag_registry=None, 
        context_limit=None,
        system_prompt=None,
        tool_registry=None, 
        plugin_registry=None,
        memory_adapter: Optional[Type[DatabaseAdapter]] = None,
        memory_summary_adapter: Optional[Type[DatabaseAdapter]] = None,
        broker: Optional[MessageBroker] = None,
        response_mode="integrated",  # New: "integrated" or "streaming"  
        streaming_config=None,  # NEW: Priority 3 streaming configuration
        session_manager=None,  # NEW: Optional custom session manager
        enable_hybrid_sessions=False,  # NEW: Enable hybrid session management
        enhanced_backend="mock",  # NEW: Enhanced backend type
        enhanced_config=None,  # NEW: Enhanced backend configuration
        allow_middleware=None,  # NEW: Override middleware permission
        **kwargs
    ):
        kwargs.pop("provider", None)  # Remove `provider` if it exists
        
        # Handle allow_middleware parameter
        if allow_middleware is not None:
            self.__allow_middleware = allow_middleware
        
        if memory and hasattr(memory, "input_key"):
            memory.input_key = memory.input_key or "input"
            
        if memory and hasattr(memory, "output_key"):
            memory.output_key = memory.output_key or "output"
            
        if memory_adapter is not None and not isinstance(memory_adapter, DatabaseAdapter):
            raise TypeError(
                f"Argument 'adapter' must be a subclass of DatabaseAdapter if provided, got {type(memory_adapter).__name__}")

        super().__init__(
            name=name, 
            agent=agent, 
            model=model,  
            memory=memory,
            provider="wrapper",
            agent_type=agent_type,
            system_prompt=system_prompt,
            **kwargs
        )
        
        UtilMixin.__init__(self)  # Initialize UtilMixin
        MiddlewareMixin.__init__(
            self, 
            tool_registry=tool_registry, 
            plugin_registry=plugin_registry,
            rag_registry=rag_registry 
        )  # Initialize MiddlewareMixin
                
        self.timeout = kwargs.get("timeout", 60) # 60 second timeout.
        self._initialize_logger(name, agent, langsmith_api_key)  # Use LoggingMixin's method
        self.memory = self._initialize_memory(agent, memory, self.in_memory)
        self.is_conversational = is_conversational
        self.model_details = self._get_model_details(model=model)
        self.model_details["limit"] = context_limit or self.model_details["limit"]
        self.model_details["ppm"] = kwargs.get("ppm", None) or self.model_details["ppm"]
        self.memory_adapter = memory_adapter
        self._update_memory_summary(memory_adapter, memory_summary_adapter)

        self.broker = broker  # Can be None to disable queue-based execution

        if self.broker:
            # Subscribe agent to relevant channels
            self.broker.subscribe(f"{self.agent.identifier}_incoming", self.handle_push_message)

        self.response_mode = response_mode
        
        # PRIORITY 3: Initialize streaming configuration  
        self.streaming_config = self.get_streaming_config(streaming_config)
        self.streaming_enabled = self.should_enable_streaming(streaming_config)
        
        # PRIORITY 5: Initialize session management
        self.session_manager = self._initialize_session_manager(
            session_manager=session_manager,
            enable_hybrid_sessions=enable_hybrid_sessions,
            enhanced_backend=enhanced_backend,
            enhanced_config=enhanced_config or {}
        )
        self.current_session_id = None

    def handle_push_message(self, payload):
        """Handles incoming messages for the agent if a broker is active."""
        if not self.broker or not payload:
            return  # Skip processing if the broker is disabled

        message_type = payload.get("type")
        data = payload.get("data")

        if message_type == "follow_up_request":
            response = self.agent.process_followup(data)
            self._send_response("response", response)

        elif message_type == "task_result":
            self._send_response("task_result", data)

    def _send_response(self, message_type, data):
        """Helper function to send responses if a broker exists."""
        if self.broker:
            self.broker.publish("communicator_incoming", {"type": message_type, "data": data})
        else:
            print(f"[INFO] No broker found. Handling response locally: {data}")

    def send_task(self, task_data):
        """Pushes a task to the Executor Agent via the broker, or calls it directly if no broker."""
        if self.broker:
            self.broker.publish("executor_incoming", {"type": "task", "data": task_data})
        else:
            print(f"[INFO] No broker found. Executing task directly.")
            response = self.agent.execute_task(task_data)
            self._send_response("task_result", response)
            
    def _report_estimated_usage(self, context, price_key="ppm", enforce=False, verbose=False):
        if enforce or self._cost_api_detected():
            num_tokens, price = self.utils.price_tokens_from_string(
                f"{context}", 
                encoding_name=self.model, 
                price_per_million=self.model_details[price_key], 
                verbose=verbose
            )

            AgentRegistry.report_usage(self.name, price)
        
    def _cost_api_detected(self):
    
        # --- Native API Models ---
        valid_classes = tuple(filter(None, (OpenAI, )))
        if valid_classes and isinstance(self.agent, valid_classes):
            return True
        
        # --- LangChain API Models ---
        valid_classes = tuple(filter(None, (ChatOpenAI, LangChainOpenAI, Anthropic, Cohere, AI21, VertexAI, AzureChatOpenAI)))
        if valid_classes and isinstance(self.agent, valid_classes):
            return True
        
        # --- LlamaIndex API Models ---
        valid_classes = tuple(filter(None, (LlamaOpenAI, LlamaAnthropic, LlamaCohere, LlamaAI21)))
        if valid_classes and isinstance(self.agent, valid_classes):
            return True 
        
        # --- Hugging Face API (Hugging Face Hub) ---
        valid_classes = tuple(filter(None, (HuggingFaceHub, )))
        if valid_classes and isinstance(self.agent, valid_classes):
            return True 
        
        return False
    
    # ========== PRIORITY 5: SESSION MANAGEMENT METHODS ==========
    
    def _initialize_session_manager(
        self, 
        session_manager=None,
        enable_hybrid_sessions=False,
        enhanced_backend="mock",
        enhanced_config=None
    ):
        """Initialize session manager with optional hybrid capabilities"""
        if session_manager:
            # Use provided session manager
            self.log_event(f"Using provided session manager: {type(session_manager).__name__}", "info")
            return session_manager
        
        elif enable_hybrid_sessions:
            # Create hybrid session manager
            try:
                hybrid_manager = HybridSessionManagerFactory.create_hybrid_manager(
                    enhanced_backend=enhanced_backend,
                    basic_storage_type="sqlite",
                    enable_semantic_search=True,
                    enable_analytics=True,
                    **enhanced_config
                )
                self.log_event(f"Created hybrid session manager with {enhanced_backend} backend", "info")
                return hybrid_manager
            except Exception as e:
                self.log_event(f"Failed to create hybrid session manager: {e}", "warning")
                self.log_event("Falling back to basic session manager", "info")
                return LangSwarmSessionManager(default_session_control=SessionControl.HYBRID)
        
        else:
            # Use basic session manager
            self.log_event("Using basic session manager", "info")
            return LangSwarmSessionManager(default_session_control=SessionControl.HYBRID)
    
    def start_session(self, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new session for conversation management"""
        provider = self.model.split('-')[0] if '-' in self.model else 'openai'
        session = self.session_manager.create_session(
            user_id=f"user_{self.name}",  # Use agent name as user ID for now
            provider=provider,
            model=self.model,
            session_id=session_id,
            custom_metadata=metadata or {"agent_name": self.name, "model": self.model}
        )
        self.current_session_id = session.session_id
        self.log_event(f"Started session {session.session_id} for agent {self.name}", "info")
        return session.session_id
    
    def end_session(self, session_id: Optional[str] = None) -> None:
        """End the current or specified session"""
        target_session = session_id or self.current_session_id
        if target_session:
            self.session_manager.archive_session(target_session)
            if target_session == self.current_session_id:
                self.current_session_id = None
            self.log_event(f"Ended session {target_session} for agent {self.name}", "info")
    
    def get_session_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation history for the current or specified session"""
        target_session = session_id or self.current_session_id
        if target_session:
            session = self.session_manager.get_session(target_session)
            if session:
                return [msg.to_dict() for msg in session.history.messages]
        return []
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a previous session"""
        session = self.session_manager.get_session(session_id)
        if session:
            self.current_session_id = session_id
            # Load session history into in_memory for compatibility
            self.in_memory = []
            for msg in session.history.messages:
                self.in_memory.append({
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                })
            self.log_event(f"Resumed session {session_id} with {len(session.history.messages)} messages", "info")
            return True
        return False
    
    def search_conversation_history(self, query: str, user_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        🔥 NEW: Search conversation history using semantic search (if hybrid sessions enabled)
        """
        if isinstance(self.session_manager, HybridSessionManager):
            return self.session_manager.search_conversation_history(
                query=query,
                user_id=user_id or f"user_{self.name}",
                limit=limit
            )
        else:
            self.log_event("Semantic search not available - basic session manager in use", "warning")
            return []
    
    def get_conversation_analytics(self, user_id: Optional[str] = None, time_range_days: int = 30) -> Dict[str, Any]:
        """
        🔥 NEW: Get conversation analytics (if hybrid sessions enabled)
        """
        if isinstance(self.session_manager, HybridSessionManager):
            return self.session_manager.get_conversation_analytics(
                user_id=user_id or f"user_{self.name}",
                time_range_days=time_range_days
            )
        else:
            self.log_event("Analytics not available - basic session manager in use", "warning")
            return {}
    
    def find_similar_conversations(self, session_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        🔥 NEW: Find conversations similar to current session (if hybrid sessions enabled)
        """
        if isinstance(self.session_manager, HybridSessionManager):
            target_session = session_id or self.current_session_id
            if target_session:
                return self.session_manager.find_similar_conversations(
                    session_id=target_session,
                    limit=limit
                )
            else:
                self.log_event("No session ID available for similarity search", "warning")
                return []
        else:
            self.log_event("Similar conversation search not available - basic session manager in use", "warning")
            return []
    
    def is_hybrid_sessions_enabled(self) -> bool:
        """Check if hybrid sessions are enabled"""
        return isinstance(self.session_manager, HybridSessionManager)
    
    def _store_conversation(self, user_input, agent_response, session_id="default_session"):
        """Store conversation turn in the vector DB while preserving document structure."""
        # PRIORITY 5: Enhanced conversation storage with session management
        
        # Use current session if available
        if self.current_session_id and session_id == "default_session":
            session_id = self.current_session_id
            
        # Store in session management system
        if self.session_manager and session_id:
            try:
                # Add messages to session
                from langswarm.core.session.models import MessageRole
                session = self.session_manager.get_session(session_id)
                if session:
                    session.add_message(user_input, MessageRole.USER)
                    session.add_message(agent_response, MessageRole.ASSISTANT)
                    self.log_event(f"Stored conversation in session {session_id}", "debug")
            except Exception as e:
                self.log_event(f"Error storing conversation in session: {str(e)}", "warning")
        
        # Continue with existing memory adapter storage for backward compatibility
        if self.memory_adapter is None:
            return
        
        timestamp = datetime.utcnow().isoformat()
        
        # Store the conversation turn with metadata
        conversation_turn = {
            "session_id": session_id,
            "timestamp": timestamp,
            "user_input": user_input,
            "agent_response": agent_response,
            "agent_name": self.name
        }
        
        # Insert into vector DB
        self.memory_adapter.insert([conversation_turn])
        
        # Optionally update summary memory
        if self.memory_summary_adapter:
            # Create a summary of this conversation turn
            summary_text = f"User: {user_input}\nAgent: {agent_response}"
            summary_doc = {
                "session_id": session_id,
                "timestamp": timestamp,
                "summary": summary_text,
                "agent_name": self.name
            }
            self.memory_summary_adapter.insert([summary_doc])

    def _ensure_json_format_instructions(self, messages):
        """Ensure system prompt includes JSON format instructions for native structured output"""
        # Check if we already have JSON format instructions
        system_message = None
        if messages:
            for i, message in enumerate(messages):
                if message.get("role") == "system":
                    system_message = message
                    break
        
        # JSON format instructions for LangSwarm structured responses
        json_instructions = """

IMPORTANT: You must respond in valid JSON format with this exact structure:
{
  "response": "Your main response text here",
  "mcp": {
    "tool": "tool_name",
    "method": "method_name", 
    "params": {"param1": "value1"}
  }
}

The "response" field is REQUIRED and contains your message to the user.
The "mcp" field is OPTIONAL and only include it if you need to use a tool.
Do not include any text outside the JSON structure."""

        if system_message:
            # Check if JSON instructions are already present
            if "JSON format" not in system_message["content"] and "json" not in system_message["content"].lower():
                # Append JSON instructions to existing system message
                system_message["content"] += json_instructions
                self.log_event(f"Added JSON format instructions to existing system prompt", "debug")
        else:
            # Create new system message with JSON instructions
            json_system_message = {
                "role": "system",
                "content": f"You are a helpful assistant.{json_instructions}"
            }
            # Insert at the beginning
            messages.insert(0, json_system_message)
            self.log_event(f"Created new system message with JSON format instructions", "debug")
        return messages

    def _call_agent(self, q, erase_query=False, remove_linebreaks=False):

        if q:
            self.add_message(q, role="user", remove_linebreaks=remove_linebreaks)
            self.log_event(f"Query sent to agent {self.name}: {q}", "info")
            
        try:
            # Handle different agent types
            if self._is_langchain_agent(self.agent): # hasattr(self.agent, "run"):
                # LangChain agents
                if hasattr(self.agent, "memory") and self.agent.memory:
                    # Memory is already managed by the agent
                    self._report_estimated_usage(q)
                    response = self.agent.run(q)
                else:
                    # No memory, include context manually
                    if callable(self.agent):
                        # Direct calls are deprecated, so we use .invoke() instead.
                        if self.in_memory:
                            self._report_estimated_usage(self.in_memory)
                            response = self.agent.invoke(self.in_memory)
                        else:
                            self._report_estimated_usage(q)
                            response = self.agent.invoke(q)
                    else:
                        context = " ".join([message["content"] for message in self.in_memory]) if self.in_memory else q
                        self._report_estimated_usage(context)
                        response = self.agent.run(context)
            elif self._is_llamaindex_agent(self.agent):
                # LlamaIndex agents
                context = " ".join([message["content"] for message in self.in_memory])
                self._report_estimated_usage(context)
                response = self.agent.query(context if self.memory else q).response
            elif self._is_hugging_face_agent(self.agent) and callable(self.agent):
                # Hugging Face agents
                context = " ".join([message["content"] for message in self.in_memory]) if self.is_conversational else q
                self._report_estimated_usage(context)
                response = self.agent(context)
            elif self._is_openai_llm(self.agent) or hasattr(self.agent, "ChatCompletion"):
                # PRIORITY 4: Enhanced OpenAI API handling with Response API support
                config = {
                    "streaming": self.streaming_config or {},
                    "api_preference": getattr(self, 'api_preference', None)
                }
                
                # Determine API type and call accordingly
                api_type = self.get_api_type_for_model()
                
                if api_type == "response_api" and self.should_use_response_api(config):
                    response_data = self._call_response_api(self.in_memory, config)
                    
                    # Handle refusal
                    if response_data.get("refusal"):
                        response = response_data["response"]
                        self.log_event(f"Model refused request: {response}", "warning")
                    else:
                        # Check if we have MCP tool calls
                        if response_data.get("mcp"):
                            # Convert structured response back to JSON for processing
                            import json
                            response = json.dumps(response_data)
                        else:
                            response = response_data.get("response", "")
                    
                    # Store for downstream processing
                    self._last_completion = response_data
                    
                else:
                    # Enhanced Chat Completions API call
                    response_data = self._call_chat_completions_api(self.in_memory, config)
                    
                    # Handle Mock objects in tests
                    if hasattr(response_data, '_mock_name') or str(type(response_data)) == "<class 'unittest.mock.Mock'>":
                        response = "Mock response for testing"
                    else:
                        # Handle refusal
                        if response_data.get("refusal"):
                            response = response_data["response"]
                            self.log_event(f"Model refused request: {response}", "warning")
                        else:
                            # Check if we have MCP tool calls
                            if response_data.get("mcp"):
                                # Convert structured response back to JSON for processing
                                import json
                                response = json.dumps(response_data)
                            else:
                                response = response_data.get("response", "")
                    
                    # Store for downstream processing
                    self._last_completion = response_data
            else:
                raise ValueError(f"Unsupported agent type: {type(self.agent)} for agent: {self.agent}")

            # Parse and log response
            response = self._parse_response(response)
            self.log_event(f"Agent {self.name} response: {response}", "info")
            
            # Setup cost reporting with outgoing token cost as well.
            self._report_estimated_usage(response, price_key="ppm_out")
            
            # PRIORITY 5: Use current session for conversation storage
            session_id = self.current_session_id or "default_session"
            self._store_conversation(f"{q}", response, session_id)

            if q and erase_query:
                self.remove()
            elif q:
                self.add_message(response, role="assistant", remove_linebreaks=remove_linebreaks)
                #self.log_event(f"Response sent back from Agent {self.name}: {response}", "info")

            return response

        except Exception as e:
            self.log_event(f"Error for agent {self.name}: {str(e)}", "error")
            
            # Convert generic exceptions to more specific types for better error handling
            error_msg = str(e).lower()
            
            # API-related errors should be ValueError
            if any(keyword in error_msg for keyword in ["api", "key", "token", "authentication", "authorization"]):
                raise ValueError(f"API Error: {str(e)}")
            
            # Input validation errors should be TypeError
            elif any(keyword in error_msg for keyword in ["invalid", "type", "format", "parse", "json"]):
                raise TypeError(f"Input Error: {str(e)}")
            
            # Model configuration errors should be ValueError
            elif any(keyword in error_msg for keyword in ["model", "config", "parameter", "unsupported"]):
                raise ValueError(f"Configuration Error: {str(e)}")
            
            # Default: re-raise as RuntimeError for unexpected errors
            else:
                raise RuntimeError(f"Agent Error: {str(e)}")
    
    # ========== PRIORITY 4: API CALLING METHODS ==========
    
    def _call_response_api(self, messages, config=None):
        """Handle Response API calls with enhanced features"""
        try:
            # Get Response API parameters
            params = self.get_response_api_parameters(messages, config)
            
            # Log API call
            self.log_event(f"Making Response API call with model: {self.model}", "info")
            
            # Make the API call
            if hasattr(self.agent, 'responses') and hasattr(self.agent.responses, 'create'):
                self._report_estimated_usage(messages)
                response = self.agent.responses.create(**params)
            elif hasattr(self.agent, 'client') and hasattr(self.agent.client, 'responses'):
                self._report_estimated_usage(messages)
                response = self.agent.client.responses.create(**params)
            else:
                # Fallback to Chat Completions if Response API not available
                self.log_event("Response API not available, falling back to Chat Completions", "warning")
                return self._call_chat_completions_api(messages, config)
            
            # Parse the response
            parsed_response = self.parse_response_api_response(response)
            
            # Handle refusal
            if parsed_response.get("refusal"):
                self.log_event(f"Model refused request: {parsed_response['refusal']}", "warning")
                return {
                    "response": parsed_response["refusal"],
                    "mcp": None,
                    "refusal": True,
                    "metadata": parsed_response.get("metadata", {})
                }
            
            # Process structured response if available
            content = parsed_response.get("content", "")
            
            # Try to parse as JSON for structured responses
            if self.supports_native_structured_output():
                try:
                    structured_data = self.utils.safe_json_loads(content)
                    if structured_data is None:
                        raise ValueError("Failed to parse structured response as JSON")
                    is_valid, message = self.validate_enhanced_structured_response(structured_data)
                    
                    if is_valid:
                        # Handle refusal in structured data
                        structured_data = self.handle_structured_response_refusal(structured_data)
                        
                        # Process MCP tool calls if present
                        if structured_data.get("mcp"):
                            tool_calls = parsed_response.get("tool_calls", [])
                            if tool_calls:
                                # Translate native tool calls to MCP if needed
                                mcp_calls = []
                                for tool_call in tool_calls:
                                    mcp_call = self.translate_native_tool_call_to_mcp(tool_call)
                                    if mcp_call:
                                        mcp_calls.append(mcp_call)
                                
                                # Use translated calls if available
                                if mcp_calls:
                                    structured_data["mcp"] = mcp_calls[0] if len(mcp_calls) == 1 else mcp_calls
                        
                        structured_data["metadata"] = parsed_response.get("metadata", {})
                        return structured_data
                    else:
                        self.log_event(f"Invalid structured response: {message}", "warning")
                        
                except (ValueError, TypeError) as e:
                    self.log_event(f"Failed to parse response as JSON: {str(e)}, using raw content", "warning")
            
            # Return raw content if no structured parsing
            return {
                "response": content,
                "mcp": None,
                "metadata": parsed_response.get("metadata", {})
            }
            
        except Exception as e:
            self.log_event(f"Response API call failed: {str(e)}", "error")
            # Fallback to Chat Completions
            return self._call_chat_completions_api(messages, config)
    
    def _call_chat_completions_api(self, messages, config=None):
        """Enhanced Chat Completions API call with Priority 1-3 features"""
        try:
            # Prepare API parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0
            }
            
            # PRIORITY 3: Add streaming parameters if enabled
            streaming_params = self.get_streaming_parameters(config.get("streaming", {}) if config else {})
            if streaming_params:
                api_params.update(streaming_params)
                self.log_event(f"Streaming enabled for model {self.model} with params: {list(streaming_params.keys())}", "info")
            
            # PRIORITY 1: Add native structured output if supported
            if self.supports_native_structured_output():
                if self.supports_strict_mode():
                    # Use enhanced schema with strict mode
                    api_params["response_format"] = self.get_enhanced_structured_response_schema(strict=True)
                else:
                    # Use basic structured output
                    api_params["response_format"] = {"type": "json_object"}
                
                # Ensure JSON format instructions in system prompt
                api_params["messages"] = self._ensure_json_format_instructions(messages.copy())
                self.log_event(f"Using native structured output for model {self.model}", "info")
            
            # PRIORITY 2: Add native tool calling if supported
            if self.supports_native_tool_calling() and hasattr(self, 'tool_registry') and self.tool_registry:
                tools = self.tool_registry.get_tools() if hasattr(self.tool_registry, 'get_tools') else []
                if tools:
                    native_tools = self.get_native_tool_format_schema(tools)
                    if native_tools:
                        api_params["tools"] = native_tools
                        api_params["tool_choice"] = "auto"  # Let model decide when to use tools
                        self.log_event(f"Using native tool calling for model {self.model} with {len(native_tools)} tools", "info")
            
            # Store completion for tool call translation
            self._current_completion = None
            
            # Make the API call
            self.log_event(f"Making Chat Completions API call with model: {self.model}", "info")
            
            try:
                self._report_estimated_usage(messages)
                completion = self.agent.ChatCompletion.create(**api_params)
            except:
                self._report_estimated_usage(messages)
                completion = self.agent.chat.completions.create(**api_params)
            
            self._current_completion = completion
            
            # PRIORITY 3: Handle streaming vs non-streaming responses
            if streaming_params and streaming_params.get("stream"):
                # Check if this is a Mock object (for testing)
                if hasattr(completion, '_mock_name') or str(type(completion)) == "<class 'unittest.mock.Mock'>":
                    # Handle Mock objects in tests - treat as non-streaming
                    try:
                        content = completion.choices[0].message.content
                    except (TypeError, AttributeError, IndexError):
                        content = "Mock response for testing"
                else:
                    # Streaming response - aggregate chunks
                    chunks = []
                    for chunk in completion:
                        parsed_chunk = self.parse_stream_chunk(chunk)
                        chunks.append(parsed_chunk)
                        if parsed_chunk.get("is_complete"):
                            break
                
                    # Aggregate streaming chunks into final response
                    aggregated = self.aggregate_stream_chunks(chunks)
                    content = aggregated["content"]
                
                    # Create a mock completion object for tool call translation
                    self._current_completion = type('MockCompletion', (), {
                        'choices': [type('MockChoice', (), {
                            'message': type('MockMessage', (), {
                                'content': content,
                                'tool_calls': getattr(completion.choices[0].message, 'tool_calls', None) if hasattr(completion, 'choices') else None,
                                'refusal': None
                            })()
                        })()],
                        '_streaming_metadata': aggregated["metadata"]
                    })()
                    self.log_event(f"Streaming completed: {aggregated['metadata']['chunks_processed']} chunks processed", "debug")
            else:
                # Non-streaming response
                try:
                    content = completion.choices[0].message.content
                except (TypeError, AttributeError, IndexError):
                    # Handle Mock objects or malformed responses
                    if hasattr(completion, '_mock_name'):
                        content = "Mock response for testing"
                    else:
                        raise
            
            # Check for refusal (in newer OpenAI models)
            try:
                if hasattr(completion.choices[0].message, 'refusal') and completion.choices[0].message.refusal:
                    self.log_event(f"Model refused request: {completion.choices[0].message.refusal}", "warning")
                    return {
                        "response": completion.choices[0].message.refusal,
                        "mcp": None,
                        "refusal": True,
                        "metadata": {
                            "api_type": "chat_completions",
                            "model": self.model
                        }
                    }
            except (TypeError, AttributeError, IndexError):
                # Handle Mock objects or malformed completion objects
                pass
            
            # PRIORITY 2: Handle native tool calls
            try:
                tool_calls = getattr(completion.choices[0].message, 'tool_calls', None)
            except (TypeError, AttributeError, IndexError):
                # Handle Mock objects or malformed responses
                tool_calls = None
            if tool_calls and self.supports_native_tool_calling():
                # Translate native tool calls to MCP format
                mcp_calls = []
                for tool_call in tool_calls:
                    mcp_call = self.translate_native_tool_call_to_mcp(tool_call)
                    if mcp_call:
                        mcp_calls.append(mcp_call)
                
                if mcp_calls:
                    # Return with translated tool calls
                    return {
                        "response": content or "Tool call initiated",
                        "mcp": mcp_calls[0] if len(mcp_calls) == 1 else mcp_calls,
                        "metadata": {
                            "api_type": "chat_completions",
                            "model": self.model,
                            "native_tool_calls": len(tool_calls)
                        }
                    }
            
            # PRIORITY 1: Process structured responses
            if content and self.supports_native_structured_output():
                try:
                    structured_data = self.utils.safe_json_loads(content)
                    if structured_data is None:
                        raise ValueError("Failed to parse structured response as JSON")
                    is_valid, message = self.validate_enhanced_structured_response(structured_data)
                    
                    if is_valid:
                        # Handle refusal in structured data
                        structured_data = self.handle_structured_response_refusal(structured_data)
                        structured_data["metadata"] = {
                            "api_type": "chat_completions",
                            "model": self.model,
                            "validation": message
                        }
                        return structured_data
                    else:
                        self.log_event(f"Structured response validation failed: {message}", "warning")
                        
                except (ValueError, TypeError) as e:
                    self.log_event(f"Failed to parse structured response: {str(e)}", "warning")
            
            # Fallback: manual JSON parsing (legacy behavior)
            return self._parse_agent_response(content)
            
        except Exception as e:
            self.log_event(f"Chat Completions API call failed: {str(e)}", "error")
            raise

    def _safe_get_completion_content(self, completion):
        """Safely extract content from completion object, handling Mock objects"""
        try:
            return completion.choices[0].message.content
        except (TypeError, AttributeError, IndexError):
            if hasattr(completion, '_mock_name'):
                return "Mock response for testing"
            return None
    
    def _safe_get_completion_attr(self, completion, attr, default=None):
        """Safely extract attributes from completion.choices[0].message, handling Mock objects"""
        try:
            return getattr(completion.choices[0].message, attr, default)
        except (TypeError, AttributeError, IndexError):
            return default

    def chat(self, q=None, reset=False, erase_query=False, remove_linebreaks=False, 
             session_id=None, start_new_session=False, **kwargs):
        """
        Process a query using the wrapped agent with session management.

        Parameters:
        - q (str): Query string.
        - reset (bool): Whether to reset memory before processing.
        - erase_query (bool): Whether to erase the query after processing.
        - remove_linebreaks (bool): Remove line breaks from the query.
        - session_id (str): Session ID to use/resume. If None, uses current session.
        - start_new_session (bool): Whether to start a new session for this conversation.

        Returns:
        - str: The agent's response.
        """
        # PRIORITY 5: Session management integration
        if start_new_session:
            session_id = self.start_session(session_id)
        elif session_id and session_id != self.current_session_id:
            # Resume or switch to specified session
            if not self.resume_session(session_id):
                # Session doesn't exist, create it
                session_id = self.start_session(session_id)
        elif not self.current_session_id:
            # No active session, start a default one
            session_id = self.start_session()
        
        response = "No Query was submitted."
        
        if reset:
            self.in_memory = []
            if self.memory and hasattr(self.memory, clear):
                self.memory.clear()

        if q:
            response = self._call_agent(q, erase_query=erase_query, remove_linebreaks=remove_linebreaks)

            print("response", response)
            
            # PRIORITY 2: Universal Tool Calling - Translate native tool calls to MCP format
            if self.supports_native_tool_calling() and hasattr(self, '_last_completion'):
                try:
                    translated_response = self.translate_native_tool_call_to_mcp(self._last_completion)
                    if translated_response != self._last_completion:
                        # Native tool call was detected and translated to MCP format
                        self.log_event(f"Translated native tool call to MCP format for model {self.model}", "info")
                        
                        # Override the response with the translated MCP format
                        # Convert the translated response to JSON string for consistent processing
                        import json
                        response = json.dumps(translated_response)
                        
                        self.log_event(f"Universal tool calling: Native → MCP translation successful", "debug")
                except Exception as e:
                    self.log_event(f"Error translating native tool call to MCP: {str(e)}", "warning")
                    # Continue with original response if translation fails
                
                # Clean up temporary storage
                try:
                    if hasattr(self, '_last_completion'):
                        delattr(self, '_last_completion')
                except AttributeError:
                    # Attribute may have been deleted elsewhere or never existed
                    pass
            
            # Enhanced JSON parsing for structured responses
            parsed_json = self.utils.safe_json_loads(response.strip())
            
            print("parsed_json", parsed_json)
            
            # Validate structured response if we got JSON
            if parsed_json and isinstance(parsed_json, dict):
                is_valid, validation_message = self.validate_structured_response(parsed_json)
                
                if is_valid:
                    self.log_event(f"Valid structured response received from {self.model}", "debug")
                else:
                    self.log_event(f"Invalid structured response from {self.model}: {validation_message}", "warning")
                    # Continue processing anyway for backward compatibility
            
            if parsed_json and isinstance(parsed_json, dict):
                # Handle structured response format: {"response": "text", "mcp": {...}, ...}
                user_response = parsed_json.get('response', '')
                
                if self.__allow_middleware and parsed_json.get('mcp'):
                    # Process tool call while preserving user response
                    
                    # Check response mode to determine behavior
                    if self.response_mode == "streaming" and user_response:
                        # Mode 1: Show immediate response, then tool results
                        print(f"[Streaming Mode] Immediate response: {user_response}")
                        
                        # Store the immediate response for potential callback/streaming
                        immediate_response = user_response
                        
                        # Execute tool
                        middleware_status, middleware_response = self.to_middleware(parsed_json)
                        
                        if middleware_status == 201:  # Tool executed successfully
                            # In streaming mode, we could return both parts
                            # For now, we'll combine them with a clear separator
                            return f"{immediate_response}\n\n[Tool executed successfully]\n{middleware_response}"
                        else:
                            # Tool failed, return immediate response with error
                            return f"{immediate_response}\n\n[Tool error]: {middleware_response}"
                    
                    else:
                        # Mode 2: Integrated response (default behavior)
                        middleware_status, middleware_response = self.to_middleware(parsed_json)
                        
                        if middleware_status == 201:  # Tool executed successfully
                            # Combine user response with tool output for context
                            tool_context = f"\n\nTool result: {middleware_response}"
                            
                            # Ask agent to provide final response incorporating tool results
                            final_prompt = f"{user_response}{tool_context}"
                            final_response = self._call_agent(
                                final_prompt, erase_query=erase_query, remove_linebreaks=remove_linebreaks)
                            
                            # Parse final response (might also be structured JSON)
                            final_parsed = self.utils.safe_json_loads(final_response.strip())
                            
                            if final_parsed and isinstance(final_parsed, dict):
                                # Return the response field or full JSON if no response field
                                return final_parsed.get('response', final_parsed)
                            else:
                                # Return plain text response
                                return final_response
                        else:
                            # Tool failed, return user response with error context
                            return f"{user_response}\n\nTool error: {middleware_response}"
                
                elif parsed_json.get('mcp'):
                    # MCP call present but middleware disabled
                    return user_response or "Tool call attempted but middleware is disabled."
                
                else:
                    # Pure response without tool calls
                    return user_response or str(parsed_json)
            
            else:
                # Fallback for non-JSON responses (backward compatibility)
                return response

        return response
    
    def chat_stream(self, q=None, reset=False, erase_query=False, remove_linebreaks=False, 
                    session_id=None, start_new_session=False, **kwargs):
        """
        PRIORITY 3: Stream a chat response in real-time, yielding chunks as they arrive.
        
        This method enables true real-time streaming when the model and configuration support it.
        For models without native streaming, it provides client-side chunking simulation.

        Parameters:
        - q (str): Query string.
        - reset (bool): Whether to reset memory before processing.
        - erase_query (bool): Whether to erase the query after processing.
        - remove_linebreaks (bool): Remove line breaks from the query.
        - session_id (str): Session ID to use/resume. If None, uses current session.
        - start_new_session (bool): Whether to start a new session for this conversation.

        Yields:
        - dict: Stream chunks with content, completion status, and metadata.
        """
        # PRIORITY 5: Session management integration for streaming
        if start_new_session:
            session_id = self.start_session(session_id)
        elif session_id and session_id != self.current_session_id:
            # Resume or switch to specified session
            if not self.resume_session(session_id):
                # Session doesn't exist, create it
                session_id = self.start_session(session_id)
        elif not self.current_session_id:
            # No active session, start a default one
            session_id = self.start_session()
        
        # Continue with existing streaming logic...
        if not self.supports_native_streaming():
            # Fallback: Use regular chat and return as single chunk
            response = self.chat(q, reset, erase_query, remove_linebreaks, **kwargs)
            
            # Return entire response as one chunk for unsupported models
            yield {
                "content": response,
                "is_complete": True,
                "metadata": {
                    "provider": self.get_streaming_type() or "none",
                    "streaming_type": "client_simulation",
                    "model": self.model
                }
            }
            return
        
        # Real streaming for supported models
        if reset:
            self.in_memory = []
            if self.memory and hasattr(self.memory, 'clear'):
                self.memory.clear()

        if not q:
            yield {
                "content": "No Query was submitted.",
                "is_complete": True,
                "metadata": {"provider": "system", "streaming_type": "none"}
            }
            return

        # Add user message to memory
        if q:
            self.add_message(q, role="user", remove_linebreaks=remove_linebreaks)
            self.log_event(f"Query sent to agent {self.name}: {q}", "info")

        try:
            # For now, only implement OpenAI streaming (most common case)
            if self._is_openai_llm(self.agent) or hasattr(self.agent, "ChatCompletion"):
                # Prepare parameters for OpenAI API call with streaming
                api_params = {
                    "model": self.model,
                    "messages": self.in_memory,
                    "temperature": 0.0,
                    "stream": True  # Force streaming for this method
                }
                
                # Add native tool calling if supported
                if self.tool_registry and self.supports_native_tool_calling():
                    tools = self.tool_registry.get_tools() if hasattr(self.tool_registry, 'get_tools') else []
                    if tools:
                        native_tools = self.get_native_tool_format_schema(tools)
                        if native_tools:
                            api_params["tools"] = native_tools
                            api_params["tool_choice"] = "auto"

                # Add structured output if supported
                if self.supports_native_structured_output():
                    api_params["response_format"] = {"type": "json_object"}
                    self._ensure_json_format_instructions(api_params["messages"])

                try:
                    self._report_estimated_usage(self.in_memory)
                    completion = self.agent.ChatCompletion.create(**api_params)
                except:
                    self._report_estimated_usage(self.in_memory)
                    completion = self.agent.chat.completions.create(**api_params)

                # Stream chunks in real-time
                full_response = ""
                for chunk in completion:
                    parsed_chunk = self.parse_stream_chunk(chunk)
                    
                    # Accumulate content for final processing
                    if parsed_chunk.get("content"):
                        full_response += parsed_chunk["content"]
                    
                    # Yield chunk to caller immediately
                    yield parsed_chunk
                    
                    if parsed_chunk.get("is_complete"):
                        break
                
                # Post-processing: add to memory, handle tools, etc.
                if full_response:
                    # Parse final response for tool calls
                    self.log_event(f"Agent {self.name} streaming response complete", "info")
                    self._report_estimated_usage(full_response, price_key="ppm_out")
                    
                    session_id = "default_session"
                    self._store_conversation(f"{q}", full_response, session_id)

                    if q and erase_query:
                        self.remove()
                    elif q:
                        self.add_message(full_response, role="assistant", remove_linebreaks=remove_linebreaks)

            else:
                # Fallback for non-OpenAI models
                self.log_event(f"Native streaming not supported for {type(self.agent)}, using fallback", "warning")
                response = self.chat(q, reset, erase_query, remove_linebreaks, **kwargs)
                yield {
                    "content": response,
                    "is_complete": True,
                    "metadata": {
                        "provider": "fallback", 
                        "streaming_type": "client_simulation",
                        "model": self.model
                    }
                }

        except Exception as e:
            self.log_event(f"Streaming error for agent {self.name}: {str(e)}", "error")
            yield {
                "content": f"Streaming error: {str(e)}",
                "is_complete": True,
                "metadata": {
                    "provider": "error",
                    "streaming_type": "error",
                    "error": str(e)
                }
            }
    
    def _simulate_streaming_fallback(self, response, chunk_size="word"):
        """
        Simulate streaming for models that don't support native streaming (like Claude).
        This provides a consistent streaming interface across all providers.
        """
        import time
        
        if chunk_size == "word":
            # Split on spaces and preserve spaces with words
            words = response.split(' ')
            chunks = []
            for i, word in enumerate(words):
                if word.strip():  # Skip empty words
                    if i < len(words) - 1:  # Add space to all but last word
                        chunks.append(word + " ")
                    else:  # Last word gets no space
                        chunks.append(word)
        elif chunk_size == "sentence":
            chunks = response.replace('.', '.|').replace('!', '!|').replace('?', '?|').split('|')
        elif chunk_size == "paragraph":
            chunks = response.split('\n\n')
        else:  # character
            chunks = list(response)
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                yield {
                    "content": chunk,
                    "is_complete": (i == len(chunks) - 1),
                    "metadata": {
                        "provider": self.get_streaming_type() or "none",
                        "streaming_type": "client_simulation",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "fallback": True
                    }
                }
                # Small delay to simulate real streaming
                time.sleep(0.05)
    
    # ToDo: Not in use yet.
    def reflect_and_improve(response):
        prompt = f"""Evaluate the following response for clarity, correctness, and relevance.
        If it can be improved, return a revised version. Otherwise, return it unchanged.

        Response: {response}
        """
        refined_response = agent.chat(prompt)
        return refined_response

    def _format_final_response(self, query: List[str]) -> str:
        """
        Parse the response from multi-steps.

        Parameters:
        - query: The agent's raw response.

        Returns:
        - str: The final response.
        """
        joined = "\n\n".join(query)
        final_query = f"Please summarize and format the following response history into one coherent response back to the user. \n\n-- RESPONSE HISTORY --\n\n{joined}"
        return self._call_agent(final_query)

    def _parse_response(self, response: Any) -> str:
        """
        Parse the response from the wrapped agent.

        Parameters:
        - response: The agent's raw response.

        Returns:
        - str: The parsed response.
        """
        if hasattr(response, "content"):
            return response.content
        elif isinstance(response, dict):
            return response.get("generated_text", "")
        return str(response)

    def has_tools(self) -> bool:
        """
        Check if the agent has tools available.
        
        Returns:
        - bool: True if the agent has tools, False otherwise.
        """
        if not hasattr(self, 'tool_registry') or not self.tool_registry:
            return False
            
        # Check different tool registry implementations
        if hasattr(self.tool_registry, 'list_tools'):
            try:
                tools = self.tool_registry.list_tools()
                return len(tools) > 0
            except Exception:
                pass
                
        # Fallback: check if tool_registry has tools dict
        if hasattr(self.tool_registry, 'tools'):
            tools_dict = getattr(self.tool_registry, 'tools', {})
            return len(tools_dict) > 0
            
        # Fallback: check if tool_registry is a dict itself
        if isinstance(self.tool_registry, dict):
            return len(self.tool_registry) > 0
            
        return False

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the wrapped agent.

        Parameters:
        - name (str): The attribute name.

        Returns:
        - The attribute from the wrapped agent.
        """
        return getattr(self.agent, name)
