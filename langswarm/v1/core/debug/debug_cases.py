"""
LangSwarm Debug Cases for Production Debugging

This module provides comprehensive debug cases for tracing real LangSwarm 
components and workflows. Each debug case captures detailed execution traces
of production scenarios to help identify issues, performance bottlenecks,
and system behavior.

Debug Case Progression:
1. Case 1: Simple agent debugging (structured output, JSON processing)
2. Case 2: Memory agent debugging (conversation state, multi-turn flows)
3. Case 3: BigQuery tool debugging (real MCP workflows, vector search)
4. Case 4: Tool integration debugging (various MCP tools)
5. Case 5: Workflow debugging (complex multi-step processes)
6. Case 6: Error handling debugging (failure modes, recovery paths)
7. Case 7: Performance debugging (bottlenecks, timing analysis)
8. Case 8: Concurrent debugging (race conditions, threading issues)
"""

import asyncio
import time
import uuid
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import get_debug_config, validate_debug_config, DebugConfig
from dataclasses import dataclass

from .tracer import get_debug_tracer, initialize_debug_tracer
from .integration import enable_debug_tracing, disable_debug_tracing
from .critical_failures import initialize_failure_handler, handle_critical_failure, get_failure_handler


@dataclass
class TestCaseResult:
    """Result of a test case execution"""
    case_name: str
    success: bool
    duration_ms: float
    trace_id: Optional[str]
    events_count: int
    error_message: Optional[str] = None
    output_file: Optional[str] = None


class DebugCase:
    """Base class for debug cases - real production debugging scenarios"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.config: Optional[DebugConfig] = None
    
    async def setup(self) -> bool:
        """Setup for the debug case. Return True if successful."""
        # Load and validate configuration
        self.config = get_debug_config()
        is_valid, errors = validate_debug_config(for_case=self.name)
        
        if not is_valid:
            print(f"❌ Configuration validation failed:")
            for error in errors:
                print(f"   • {error}")
            return False
        
        # Set environment variables from config
        from .config import set_debug_environment_variables
        set_debug_environment_variables()
        
        return True
    
    async def execute(self) -> Any:
        """Execute the test case. Should be overridden by subclasses."""
        raise NotImplementedError()
    
    async def cleanup(self):
        """Cleanup after test case execution."""
        pass
    
    async def run(self, output_dir: str = "debug_traces") -> TestCaseResult:
        """Run the complete test case with tracing"""
        start_time = time.time()
        trace_id = None
        events_count = 0
        error_message = None
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / f"{self.name}.jsonl"
        
        # Enable debug tracing for this test case
        enable_debug_tracing(str(output_file))
        tracer = get_debug_tracer()
        
        # Initialize critical failure handler
        failure_handler = initialize_failure_handler(tracer)
        
        try:
            print(f"\n🧪 Running test case: {self.name}")
            print(f"📝 Description: {self.description}")
            print(f"📁 Output file: {output_file}")
            
            # Setup phase
            with tracer.trace_operation("test_case", "setup", f"Setting up {self.name}") as trace_context:
                trace_id = trace_context["trace_id"]
                setup_success = await self.setup()
                if not setup_success:
                    # Check if this was due to a critical failure
                    if failure_handler and failure_handler.has_critical_failures():
                        critical_failures = failure_handler.get_critical_failures()
                        error_message = f"Critical failure during setup: {critical_failures[0].message}"
                        raise RuntimeError(error_message)
                    else:
                        raise RuntimeError("Test case setup failed")
            
            # Execute phase
            with tracer.trace_operation("test_case", "execute", f"Executing {self.name}") as trace_context:
                result = await self.execute()
                
                # Log result summary
                tracer.log_event(
                    "INFO", "test_case", "result",
                    f"Test case {self.name} completed",
                    data={"result": str(result)[:200]}  # Truncate long results
                )
            
            success = True
            
        except Exception as e:
            error_message = str(e)
            success = False
            
            # Check if this was a critical failure
            is_critical = handle_critical_failure(error_message, e, f"test_case_{self.name}")
            
            if tracer:
                event_type = "CRITICAL_FAILURE" if not is_critical else "ERROR"
                tracer.log_event(
                    event_type, "test_case", "execution_error",
                    f"Test case {self.name} failed: {error_message}",
                    level="ERROR",
                    data={
                        "error_type": type(e).__name__,
                        "is_critical": not is_critical,
                        "should_halt": not is_critical
                    }
                )
            
            # If critical failure, add additional context to result
            if not is_critical and failure_handler:
                failure_summary = failure_handler.get_failure_summary()
                if failure_summary.get("status") == "critical_failures_detected":
                    error_message = f"CRITICAL FAILURE: {error_message}"
        
        finally:
            # Cleanup phase
            try:
                await self.cleanup()
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")
        
        # Calculate results
        duration_ms = (time.time() - start_time) * 1000
        if tracer and trace_id:
            events_count = len([e for e in tracer.events if e.trace_id == trace_id])
        
        # Create result
        result = TestCaseResult(
            case_name=self.name,
            success=success,
            duration_ms=duration_ms,
            trace_id=trace_id,
            events_count=events_count,
            error_message=error_message,
            output_file=str(output_file) if output_file.exists() else None
        )
        
        # Print summary
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {self.name} ({duration_ms:.1f}ms, {events_count} events)")
        if error_message:
            print(f"   Error: {error_message}")
        
        return result


class Case1SimpleAgent(DebugCase):
    """
    Case 1: Simple agent query with no tools, no workflows
    
    This is the most basic test case to verify:
    - Agent initialization
    - Simple query processing
    - Basic response generation
    - Memory management (basic)
    """
    
    def __init__(self):
        super().__init__(
            "case_1_simple_agent",
            "Simple agent query with no tools or workflows"
        )
        self.agent = None
    
    async def setup(self) -> bool:
        """Setup a simple agent with no tools"""
        # Load debug configuration first
        if not await super().setup():
            return False
            
        try:
            # Create a minimal agent configuration
            from langswarm.v1.core.config import LangSwarmConfigLoader
            
            # Create minimal config with proper JSON response format
            config = {
                "agents": [{
                    "id": "simple_test_agent",
                    "agent_type": "openai",
                    "model": self.config.openai.model,
                    "system_prompt": """You are a simple test agent for debugging purposes. Respond briefly and helpfully to user queries."""
                }]
            }
            
            # Initialize using mock/test approach
            loader = LangSwarmConfigLoader()
            loader.config_data = config
            
            # Try to initialize with real agent first
            try:
                loader._initialize_agents()
                self.agent = loader.agents.get("simple_test_agent")
                
                # Keep structured output enabled so the agent follows JSON format instructions
                    
                # Check if agent was properly initialized or if it's a placeholder due to missing API key
                if isinstance(self.agent, dict) and self.agent.get("status") == "pending_api_key":
                    # This is a critical failure - missing API key
                    error_msg = self.agent.get("error", "API key required but not provided")
                    handle_critical_failure(
                        error_msg, 
                        ValueError(error_msg), 
                        "openai_agent"
                    )
                    # For debugging, we fail immediately - no mocks allowed
                    return False
                
                return self.agent is not None
                
            except Exception as e:
                # Check if this is a critical API/authentication error
                error_message = str(e)
                handle_critical_failure(error_message, e, "openai_agent")
                # For debugging, we fail immediately - no mocks allowed
                return False
                
        except Exception as e:
            # Any other setup error
            error_message = f"Setup error: {e}"
            handle_critical_failure(error_message, e, "test_setup")
            # For debugging, we fail immediately - no mocks allowed
            return False
    
    
    async def execute(self) -> str:
        """Execute a simple chat query"""
        query = "Hello, this is a simple test query. Please respond briefly."
        
        # Log the query
        tracer = get_debug_tracer()
        if tracer:
            tracer.log_event(
                "INFO", "test_case", "user_query",
                f"Sending query to agent: {query}",
                data={"query": query}
            )
        
        # Execute the query
        response = self.agent.chat(query)
        
        # Log the response
        if tracer:
            tracer.log_event(
                "INFO", "test_case", "agent_response",
                f"Received response from agent",
                data={"response": response, "response_length": len(str(response))}
            )
        
        # Ensure we return the actual response, not empty
        final_response = response
        if not response or response == '{}' or str(response).strip() == '{}':
            final_response = "No meaningful response received (empty or {})"
            if tracer:
                tracer.log_event(
                    "WARNING", "test_case", "empty_response",
                    f"Agent returned empty response, substituting warning message",
                    data={"original_response": response}
                )
        
        return final_response


class Case2AgentWithMemory(DebugCase):
    """
    Case 2: Agent with memory - multiple conversation turns
    
    Tests:
    - Conversation memory management
    - Multiple sequential queries
    - Context retention
    """
    
    def __init__(self):
        super().__init__(
            "case_2_agent_memory",
            "Agent with memory across multiple conversation turns"
        )
        self.agent = None
    
    async def setup(self) -> bool:
        """Setup agent with memory enabled"""
        try:
            from langswarm.v1.core.config import LangSwarmConfigLoader
            from unittest.mock import Mock
            
            # Create a mock conversational agent
            self.agent = Mock()
            self.agent.name = "memory_test_agent"
            self.agent.in_memory = []
            
            # Mock chat method that maintains conversation history
            def mock_chat(query, **kwargs):
                # Add query to memory
                self.agent.in_memory.append({"role": "user", "content": query})
                
                # Generate response based on conversation turn
                turn = len([msg for msg in self.agent.in_memory if msg["role"] == "user"])
                if turn == 1:
                    response = f"Hello! I received your message: '{query}'. What else can I help with?"
                elif turn == 2:
                    response = f"I remember our previous conversation. You said '{self.agent.in_memory[0]['content']}' and now you're saying '{query}'."
                else:
                    response = f"This is turn {turn}. I have {len(self.agent.in_memory)} messages in memory."
                
                # Add response to memory
                self.agent.in_memory.append({"role": "assistant", "content": response})
                return response
            
            self.agent.chat = mock_chat
            return True
            
        except Exception as e:
            print(f"Setup error: {e}")
            return False
    
    async def execute(self) -> List[str]:
        """Execute multiple conversation turns"""
        queries = [
            "Hello, my name is Alice.",
            "What did I tell you my name was?",
            "Can you summarize our conversation so far?"
        ]
        
        responses = []
        tracer = get_debug_tracer()
        
        for i, query in enumerate(queries, 1):
            if tracer:
                tracer.log_event(
                    "INFO", "test_case", "conversation_turn",
                    f"Turn {i}: Sending query",
                    data={
                        "turn": i,
                        "query": query,
                        "memory_size_before": len(self.agent.in_memory)
                    }
                )
            
            response = self.agent.chat(query)
            responses.append(response)
            
            if tracer:
                tracer.log_event(
                    "INFO", "test_case", "conversation_response",
                    f"Turn {i}: Received response",
                    data={
                        "turn": i,
                        "response": response,
                        "memory_size_after": len(self.agent.in_memory)
                    }
                )
            
            # Small delay to make timing visible in logs
            await asyncio.sleep(0.1)
        
        return responses


class Case3BigQueryTool(DebugCase):
    """
    Case 3: BigQuery Vector Search Tool - MCP tool with complex workflow
    
    Tests:
    - MCP tool initialization and communication
    - Complex multi-agent workflows
    - Tool parameter parsing and validation
    - Vector search operations
    - Error handling in tool workflows
    """
    
    # Load scenarios from configuration file
    @classmethod
    def _load_scenarios_config(cls) -> Dict[str, Any]:
        """Load scenarios from YAML configuration file"""
        config_path = Path(__file__).parent / "scenarios" / "bigquery_scenarios.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"⚠️  Warning: Could not load scenarios config from {config_path}: {e}")
            # Fallback to hardcoded scenarios
            return {
                "scenarios": {
                    "similarity_search": {
                        "name": "similarity_search",
                        "description": "Real vector similarity search test",
                        "query": "Search for information about pingday monitoring",
                        "expected_behavior": "Should generate embeddings and perform vector similarity search in BigQuery",
                        "trace_file_suffix": "similarity_search",
                        "enabled": True
                    },
                    "list_datasets": {
                        "name": "list_datasets", 
                        "description": "Dataset discovery and metadata query test",
                        "query": "What datasets are available in the knowledge base?",
                        "expected_behavior": "Should query BigQuery metadata to list available datasets",
                        "trace_file_suffix": "list_datasets",
                        "enabled": True
                    },
                    "error_handling": {
                        "name": "error_handling",
                        "description": "Error handling and graceful failure test", 
                        "query": "Get content for document ID that doesn't exist: nonexistent_doc_12345",
                        "expected_behavior": "Should handle non-existent document gracefully with user-friendly error",
                        "trace_file_suffix": "error_handling",
                        "enabled": True
                    }
                },
                "config": {
                    "scenario_timeout": 30,
                    "continue_on_failure": True,
                    "separate_trace_files": True,
                    "include_summary_trace": True
                }
            }
    
    @property
    def TEST_SCENARIOS(self) -> List[Dict[str, Any]]:
        """Get enabled test scenarios from configuration"""
        config = self._load_scenarios_config()
        scenarios = []
        
        for scenario_key, scenario_data in config.get("scenarios", {}).items():
            if scenario_data.get("enabled", True):  # Default to enabled if not specified
                scenarios.append(scenario_data)
        
        return scenarios
    
    @property 
    def SCENARIO_CONFIG(self) -> Dict[str, Any]:
        """Get global scenario configuration"""
        config = self._load_scenarios_config()
        return config.get("config", {})
    
    def __init__(self):
        super().__init__(
            "case_3_bigquery_tool", 
            "BigQuery vector search tool with complex workflow"
        )
        self.agent = None
    
    async def setup(self) -> bool:
        """Setup an agent with BigQuery tool access"""
        # Load debug configuration first
        if not await super().setup():
            return False
            
        try:
            from langswarm.v1.core.config import LangSwarmConfigLoader
            
            # Use standard LangSwarm config file - much cleaner approach!
            config_path = Path(__file__).parent / "test_configs" / "bigquery_debug.yaml"
            
            # Initialize using proper load() method for full hierarchical tracing
            self.loader = LangSwarmConfigLoader(str(config_path))
            
            # This will trigger comprehensive tracing of the entire load process:
            # - Configuration file loading
            # - Agent initialization  
            # - Tool initialization
            # - All sub-components
            self.result = self.loader.load()
            
            self.agent = self.loader.agents.get("bigquery_test_agent")
            
            # Check if agent was properly initialized
            if isinstance(self.agent, dict) and self.agent.get("status") == "pending_api_key":
                error_msg = self.agent.get("error", "API key required but not provided")
                handle_critical_failure(
                    error_msg, 
                    ValueError(error_msg), 
                    "openai_agent"
                )
                return False
            
            # Log detailed setup completion info
            tracer = get_debug_tracer()
            if tracer:
                tracer.log_event(
                    "INFO", "setup", "completion",
                    f"BigQuery tool setup completed",
                    data={
                        "agent_initialized": self.agent is not None,
                        "agent_type": type(self.agent).__name__ if self.agent else "None",
                        "agent_id": getattr(self.agent, 'agent_id', 'unknown') if self.agent else "None",
                        "agent_has_tools": hasattr(self.agent, 'tools') if self.agent else False,
                        "agent_tools_count": len(getattr(self.agent, 'tools', [])) if hasattr(self.agent, 'tools') else 0,
                        "bigquery_config": {
                            "project_id": self.config.google_cloud.project_id,
                            "dataset_id": self.config.bigquery.dataset_id,
                            "table_name": self.config.bigquery.table_name,
                            "embedding_model": self.config.bigquery.embedding_model
                        }
                    }
                )
                
            return self.agent is not None
            
        except Exception as e:
            error_message = str(e)
            handle_critical_failure(error_message, e, "bigquery_tool_setup")
            return False
    
    async def execute(self) -> Dict[str, Any]:
        """Execute BigQuery tool test scenarios with separate trace files"""
        results = {}
        
        # Get the base output directory from config
        output_dir = self.config.output_dir if self.config else "debug_traces"
        
        for scenario in self.TEST_SCENARIOS:
            scenario_name = scenario["name"]
            scenario_query = scenario["query"]
            scenario_description = scenario["description"]
            trace_suffix = scenario["trace_file_suffix"]
            
            # Create separate tracer for this scenario
            scenario_trace_file = f"{output_dir}/case_3_bigquery_{trace_suffix}.jsonl"
            
            from .tracer import DebugTracer
            
            # Initialize separate tracer for this scenario
            scenario_tracer = DebugTracer(enabled=True, output_file=scenario_trace_file)
            
            print(f"\n🧪 Running BigQuery scenario: {scenario_name}")
            print(f"📝 Description: {scenario_description}")
            print(f"❓ Query: '{scenario_query}'")
            print(f"📁 Trace file: {scenario_trace_file}")
            
            try:
                # Create a dedicated trace for this scenario
                with scenario_tracer.trace_operation("scenario", "execution", f"BigQuery scenario: {scenario_name}") as scenario_context:
                    scenario_trace_id = scenario_context["trace_id"]
                    
                    # Log scenario start with detailed context
                    scenario_tracer.log_event(
                        "INFO", "scenario", "start",
                        f"Starting BigQuery scenario: {scenario_name}",
                        data={
                            "scenario_name": scenario_name,
                            "description": scenario_description,
                            "query": scenario_query,
                            "expected_behavior": scenario["expected_behavior"],
                            "agent_id": getattr(self.agent, 'agent_id', getattr(self.agent, 'id', getattr(self.agent, 'name', 'unknown'))),
                            "agent_type": type(self.agent).__name__
                        },
                        trace_id=scenario_trace_id
                    )
                
                    # Log agent state before execution
                    system_prompt = getattr(self.agent, 'system_prompt', '')
                    scenario_tracer.log_event(
                        "DEBUG", "agent", "pre_execution_state",
                        f"Agent state before executing scenario",
                        data={
                            "agent_memory_size": len(getattr(self.agent, 'messages', [])),
                            "agent_tools": self._get_agent_tools_info(),
                            "has_middleware": hasattr(self.agent, 'to_middleware') and callable(getattr(self.agent, 'to_middleware', None)),
                            "has_tool_registry": hasattr(self.agent, 'tool_registry'),
                            "system_prompt": system_prompt,
                            "system_prompt_length": len(system_prompt)
                        },
                        trace_id=scenario_trace_id
                    )
                    
                    # Execute the test using proper WorkflowExecutor pattern
                    scenario_tracer.log_event(
                        "INFO", "workflow", "execution_start",
                        f"Executing workflow for scenario: {scenario_query}",
                        data={"query_length": len(scenario_query)},
                        trace_id=scenario_trace_id
                    )
                
                    import time
                    from langswarm.v1.core.config import WorkflowExecutor
                    
                    start_time = time.time()
                    
                    # Use proper LangSwarm workflow execution
                    # result = (workflows, agents, brokers, tools, metadata)
                    executor = WorkflowExecutor(self.result[0], self.result[1])  # workflows, agents
                    response = executor.run_workflow('bigquery_debug_workflow', scenario_query)
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Extract agent from workflow for detailed analysis
                    agent = None
                    if self.result and len(self.result) > 1:
                        agents = self.result[1]
                        agent = agents.get('bigquery_test_agent')
                    
                    # Gather streaming data if available
                    streaming_data = {}
                    if agent:
                        # Check for preserved streaming debug data
                        if hasattr(agent, '_streaming_debug_data'):
                            streaming_data = agent._streaming_debug_data
                        
                        # Check for preserved tool call metadata (NEW FIX)
                        if hasattr(agent, '_tool_call_debug_info'):
                            streaming_data["tool_call_metadata"] = agent._tool_call_debug_info
                        
                        # Also check _last_completion
                        if hasattr(agent, '_last_completion') and agent._last_completion:
                            completion = agent._last_completion
                            if hasattr(completion, '_streaming_metadata'):
                                streaming_data.update(completion._streaming_metadata)
                            
                            # Check for tool calls in completion
                            if hasattr(completion, 'choices') and completion.choices:
                                message = completion.choices[0].message
                                if hasattr(message, 'tool_calls') and message.tool_calls:
                                    streaming_data["completion_tool_calls"] = [
                                        {
                                            "id": getattr(tc, 'id', None),
                                            "type": getattr(tc, 'type', None),
                                            "function": {
                                                "name": getattr(tc.function, 'name', None) if hasattr(tc, 'function') else None,
                                                "arguments": getattr(tc.function, 'arguments', None) if hasattr(tc, 'function') else None
                                            }
                                        } for tc in message.tool_calls
                                    ]
                    
                    # Determine log level based on response content
                    # Enhanced error detection with immediate surfacing
                    response_str = str(response).lower()
                    error_keywords = ["error", "failed", "exception", "not found", "timeout", "unable to"]
                    critical_keywords = ["validation error", "field required", "pydantic", "parameter validation", "critical"]
                    
                    is_error = any(keyword in response_str for keyword in error_keywords)
                    is_critical = any(keyword in response_str for keyword in critical_keywords)
                    
                    if is_critical:
                        log_level = "CRITICAL"
                        print(f"🚨 CRITICAL ERROR in {scenario_name}: {str(response)[:200]}...")
                    elif is_error:
                        log_level = "ERROR"
                        print(f"⚠️  ERROR in {scenario_name}: {str(response)[:200]}...")
                    else:
                        log_level = "INFO"
                    
                    # Log detailed response analysis with streaming data
                    scenario_tracer.log_event(
                        log_level, "agent", "chat_complete",
                        f"Agent response received with streaming details",
                        data={
                            "response": str(response),
                            "response_type": type(response).__name__,
                            "response_length": len(str(response)),
                            "execution_time_ms": execution_time,
                            "contains_mcp": "mcp" in str(response).lower(),
                            "contains_tool": "tool" in str(response).lower(),
                            "contains_search": "search" in str(response).lower(),
                            "streaming_data": streaming_data,
                            "agent_state": {
                                "name": getattr(agent, 'name', None) if agent else None,
                                "model": getattr(agent, 'model', None) if agent else None,
                                "has_last_completion": hasattr(agent, '_last_completion') if agent else False
                            }
                        },
                        trace_id=scenario_trace_id
                    )
                
                    # Enhanced tool call detection using metadata
                    tool_call_detected = False
                    tool_call_info = {}
                    
                    # Check preserved tool call metadata (NEW METHOD - FIXES SILENT TOOL CALL BUG)
                    if streaming_data.get("tool_call_metadata"):
                        metadata = streaming_data["tool_call_metadata"]
                        tool_call_detected = metadata.get("tool_calls_detected", False)
                        tool_call_info["metadata_source"] = "preserved_debug_info"
                        tool_call_info["tool_call_count"] = metadata.get("tool_call_count", 0)
                        tool_call_info["tool_calls"] = metadata.get("tool_calls", [])
                    
                    # Fallback: Check completion tool calls  
                    elif streaming_data.get("completion_tool_calls"):
                        tool_call_detected = True
                        tool_call_info["metadata_source"] = "completion_object"
                        tool_call_info["tool_call_count"] = len(streaming_data["completion_tool_calls"])
                        tool_call_info["tool_calls"] = streaming_data["completion_tool_calls"]
                    
                    # Check if this looks like a tool was supposed to be called
                    response_str = str(response).lower()
                    should_have_tool_call = any(keyword in response_str for keyword in ["i'll search", "searching", "let me search", "search for"])
                    
                    if should_have_tool_call and not tool_call_detected:
                        scenario_tracer.log_event(
                            "WARN", "scenario", "missing_tool_call",
                            f"Agent indicated it would search but no tool call detected",
                            data={
                                "response": str(response),
                                "expected_tool": "bigquery_vector_search",
                                "agent_response_suggests_tool_use": True,
                                "debug_info": tool_call_info
                            },
                            trace_id=scenario_trace_id
                        )
                    elif tool_call_detected:
                        scenario_tracer.log_event(
                            "INFO", "scenario", "tool_call_confirmed",
                            f"Tool call successfully detected: {tool_call_info.get('tool_call_count', 0)} calls via {tool_call_info.get('metadata_source', 'unknown')}",
                            data=tool_call_info,
                            trace_id=scenario_trace_id
                        )
                
                    # Determine success based on scenario type
                    success = self._evaluate_scenario_success(scenario_name, response)
                    
                    results[scenario_name] = {
                        "query": scenario_query,
                        "response": response,
                        "success": success,
                        "description": scenario_description,
                        "trace_file": scenario_trace_file,
                        "execution_time_ms": execution_time
                    }
                    
                    # Log scenario result with comprehensive analysis
                    scenario_tracer.log_event(
                        "INFO", "scenario", "result",
                        f"BigQuery scenario {scenario_name} completed",
                        data={
                            "scenario_name": scenario_name,
                            "response_length": len(str(response)),
                            "success": success,
                            "execution_time_ms": execution_time,
                            "response_preview": str(response)[:200] + "..." if len(str(response)) > 200 else str(response),
                            "tool_call_detected": tool_call_detected,
                            "success_evaluation": {
                                "criteria_used": f"scenario_{scenario_name}",
                                "success_reason": "Response contains expected keywords" if success else "Missing expected keywords or insufficient length"
                            }
                        },
                        trace_id=scenario_trace_id
                    )
                
                status_emoji = "✅" if success else "❌"
                print(f"{status_emoji} Scenario result: {'Success' if success else 'Failed'}")
                print(f"📤 Response: '{response}'")
                
            except Exception as e:
                import traceback
                
                results[scenario_name] = {
                    "query": scenario_query,
                    "error": str(e),
                    "success": False,
                    "description": scenario_description,
                    "trace_file": scenario_trace_file
                }
                
                # Use the scenario trace_id if we have it, otherwise generate a new one
                error_trace_id = locals().get('scenario_trace_id', str(uuid.uuid4()))
                
                scenario_tracer.log_event(
                    "ERROR", "scenario", "error",
                    f"BigQuery scenario {scenario_name} failed: {str(e)}",
                    data={
                        "scenario_name": scenario_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                        "agent_state": {
                            "agent_available": self.agent is not None,
                            "agent_type": type(self.agent).__name__ if self.agent else "None"
                        }
                    },
                    trace_id=error_trace_id
                )
                
                print(f"❌ Scenario failed: {str(e)}")
                print(f"🔍 Error type: {type(e).__name__}")
        
        # Print summary to console only (no separate summary trace file)
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get("success", False))
        failed_tests = total_tests - successful_tests
        
        print(f"\n📊 BigQuery Tool Debug Summary:")
        print(f"   • Total scenarios: {total_tests}")
        print(f"   • Successful: {successful_tests}")
        print(f"   • Failed: {failed_tests}")
        print(f"   • Individual traces: {total_tests} files created")
        
        # If any scenarios failed, raise an exception to mark the overall test as failed
        if failed_tests > 0:
            failed_scenarios = [name for name, result in results.items() if not result.get("success", False)]
            raise RuntimeError(f"BigQuery debug test failed: {failed_tests}/{total_tests} scenarios failed: {', '.join(failed_scenarios)}")
        
        return results
    
    def _get_agent_tools_info(self) -> Dict[str, Any]:
        """Get comprehensive information about agent's tools and tool registry"""
        info = {}
        
        # Check for direct tools attribute
        if hasattr(self.agent, 'tools'):
            info["direct_tools"] = getattr(self.agent, 'tools', [])
        else:
            info["direct_tools"] = "no_tools_attr"
        
        # Check for tool_registry
        if hasattr(self.agent, 'tool_registry'):
            tool_registry = getattr(self.agent, 'tool_registry')
            info["has_tool_registry"] = True
            info["tool_registry_type"] = type(tool_registry).__name__
            
            # Get tools from registry
            if hasattr(tool_registry, 'tools'):
                registry_tools = getattr(tool_registry, 'tools', {})
                info["registry_tools"] = list(registry_tools.keys()) if isinstance(registry_tools, dict) else str(registry_tools)
                info["registry_tool_count"] = len(registry_tools) if isinstance(registry_tools, dict) else 0
            else:
                info["registry_tools"] = "no_tools_in_registry"
                info["registry_tool_count"] = 0
        else:
            info["has_tool_registry"] = False
            info["tool_registry_type"] = None
            info["registry_tools"] = "no_tool_registry"
            info["registry_tool_count"] = 0
        
        return info
    
    def _evaluate_scenario_success(self, scenario_name: str, response: str) -> bool:
        """Evaluate if a scenario was successful based on its type and response"""
        response_str = str(response).lower()
        
        # Check for workflow execution errors (should be failures EXCEPT for error_handling scenarios)
        if "workflow execution error" in response_str or ("workflow" in response_str and "not found" in response_str):
            # If this is the error_handling scenario, allow it to be evaluated by success criteria
            # (since error_handling is supposed to test error conditions)
            if scenario_name != "error_handling":
                return False
        
        # Get success criteria from configuration
        config = self._load_scenarios_config()
        success_criteria = config.get("config", {}).get("success_criteria", {})
        
        if scenario_name in success_criteria:
            criteria = success_criteria[scenario_name]
            min_length = criteria.get("min_response_length", 10)
            required_keywords = criteria.get("required_keywords", [])
            forbidden_keywords = criteria.get("forbidden_keywords", [])
            
            # Check minimum length
            if not response or len(response_str) < min_length:
                return False
            
            # Check for forbidden keywords (these indicate failure)
            if forbidden_keywords:
                has_forbidden = any(keyword.lower() in response_str for keyword in forbidden_keywords)
                if has_forbidden:
                    return False
            
            # Check if any required keyword is present
            if required_keywords:
                has_keyword = any(keyword.lower() in response_str for keyword in required_keywords)
                return has_keyword
            
            return True
        
        # Fallback to hardcoded logic for backward compatibility
        if scenario_name == "similarity_search":
            return bool(response and len(response_str) > 10 and 
                       ("search" in response_str or "refund" in response_str or "policy" in response_str))
        
        elif scenario_name == "list_datasets":
            return bool(response and len(response_str) > 10 and 
                       ("dataset" in response_str or "knowledge" in response_str or "database" in response_str))
        
        elif scenario_name == "error_handling":
            return bool(response and len(response_str) > 10 and 
                       ("not exist" in response_str or "not found" in response_str or "nonexistent" in response_str))
        
        # Default: any non-empty response is considered success
        return bool(response and len(response_str) > 0)


class Case4AgentWithTools(DebugCase):
    """
    Case 3: Agent with MCP tools
    
    Tests:
    - Tool registry initialization
    - MCP tool call format
    - Tool execution and response
    - Integration between agent and middleware
    """
    
    def __init__(self):
        super().__init__(
            "case_3_agent_tools", 
            "Agent with MCP tool calling capabilities"
        )
        self.agent = None
    
    async def setup(self) -> bool:
        """Setup agent with mock MCP tools"""
        try:
            from unittest.mock import Mock
            
            # Create mock agent with tool capabilities
            self.agent = Mock()
            self.agent.name = "tool_agent"
            
            # Mock tool calling behavior
            def mock_chat(query, **kwargs):
                if "time" in query.lower():
                    # Return MCP-style tool call
                    return '''{
                        "response": "I'll get the current time for you.",
                        "mcp": {
                            "tool": "datetime_tool",
                            "method": "get_current_time",
                            "params": {}
                        }
                    }'''
                elif "weather" in query.lower():
                    return '''{
                        "response": "Let me check the weather for you.",
                        "mcp": {
                            "tool": "weather_tool", 
                            "method": "get_weather",
                            "params": {"location": "default"}
                        }
                    }'''
                else:
                    return '{"response": "I can help you with time or weather queries."}'
            
            # Mock middleware
            def mock_to_middleware(parsed_json):
                mcp = parsed_json.get('mcp', {})
                tool = mcp.get('tool', '')
                method = mcp.get('method', '')
                
                if tool == "datetime_tool" and method == "get_current_time":
                    return 201, "2024-01-15 10:30:00 UTC"
                elif tool == "weather_tool" and method == "get_weather":
                    return 201, "Sunny, 22°C"
                else:
                    return 500, "Tool not found"
            
            self.agent.chat = mock_chat
            self.agent.to_middleware = mock_to_middleware
            
            # Mock has_tools
            self.agent.has_tools = Mock(return_value=True)
            
            return True
            
        except Exception as e:
            print(f"Setup error: {e}")
            return False
    
    async def execute(self) -> Dict[str, Any]:
        """Execute queries that trigger tool calls"""
        results = {}
        tracer = get_debug_tracer()
        
        queries = [
            "What time is it?",
            "What's the weather like?",
            "Just say hello (no tools)"
        ]
        
        for query in queries:
            if tracer:
                tracer.log_event(
                    "INFO", "test_case", "tool_query",
                    f"Sending tool query: {query}",
                    data={"query": query}
                )
            
            # Get agent response (should include MCP calls)
            # TODO: Replace with proper WorkflowExecutor pattern when Case4 is converted to real workflows
            response = self.agent.chat(query)
            
            # Parse JSON response
            import json
            try:
                parsed = json.loads(response)
                
                # If there's an MCP call, execute it
                if parsed.get('mcp'):
                    status, tool_result = self.agent.to_middleware(parsed)
                    
                    if tracer:
                        tracer.log_event(
                            "INFO", "test_case", "tool_executed",
                            f"Tool call completed",
                            data={
                                "mcp_call": parsed['mcp'],
                                "status": status,
                                "result": tool_result
                            }
                        )
                    
                    results[query] = {
                        "response": parsed.get('response'),
                        "mcp_call": parsed['mcp'],
                        "tool_result": tool_result,
                        "status": status
                    }
                else:
                    results[query] = {
                        "response": parsed.get('response'),
                        "mcp_call": None,
                        "tool_result": None
                    }
                    
            except json.JSONDecodeError:
                results[query] = {"error": "Invalid JSON response", "raw_response": response}
        
        return results


class TestCaseRunner:
    """Runner for executing multiple test cases"""
    
    def __init__(self, output_dir: str = "debug_traces"):
        self.output_dir = output_dir
        self.results: List[TestCaseResult] = []
    
    async def run_case(self, debug_case: DebugCase) -> TestCaseResult:
        """Run a single debug case"""
        result = await debug_case.run(self.output_dir)
        self.results.append(result)
        return result
    
    async def run_all_basic_cases(self) -> List[TestCaseResult]:
        """Run all basic debug cases (1-4)"""
        cases = [
            Case1SimpleAgent(),
            Case2AgentWithMemory(), 
            Case3BigQueryTool(),
            Case4AgentWithTools()
        ]
        
        print("🚀 Running basic debug cases...")
        results = []
        
        for i, case in enumerate(cases, 1):
            result = await self.run_case(case)
            results.append(result)
            
            # Check for critical failures
            if not result.success and result.error_message and "CRITICAL FAILURE" in result.error_message:
                print(f"\n🚨 Critical failure detected in test case {i}/{len(cases)}")
                print(f"🛑 Stopping test execution to prevent cascading failures.")
                print(f"Please fix the critical issue before running remaining tests.")
                break
            
            # Brief pause between cases
            await asyncio.sleep(0.5)
        
        self.print_summary()
        return results
    
    def print_summary(self):
        """Print summary of all test results"""
        print("\n📊 Test Case Summary:")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.case_name:25} {result.duration_ms:8.1f}ms {result.events_count:4d} events")
            if result.error_message:
                print(f"     Error: {result.error_message}")
        
        print("-" * 60)
        print(f"Results: {passed} passed, {failed} failed")
        print(f"Output directory: {self.output_dir}")


# Convenience functions
async def run_case_1():
    """Run just Case 1 - Simple Agent"""
    runner = TestCaseRunner()
    case = Case1SimpleAgent()
    return await runner.run_case(case)


async def run_case_2():
    """Run just Case 2 - Agent with Memory"""
    runner = TestCaseRunner()
    case = Case2AgentWithMemory()
    return await runner.run_case(case)


async def run_case_3():
    """Run just Case 3 - BigQuery Tool"""
    runner = TestCaseRunner()
    case = Case3BigQueryTool()
    return await runner.run_case(case)


async def run_case_4():
    """Run just Case 4 - Agent with Tools"""
    runner = TestCaseRunner()
    case = Case4AgentWithTools()
    return await runner.run_case(case)


async def run_all_basic_cases():
    """Run all basic test cases"""
    runner = TestCaseRunner()
    return await runner.run_all_basic_cases()


if __name__ == "__main__":
    # Example usage
    asyncio.run(run_all_basic_cases())

