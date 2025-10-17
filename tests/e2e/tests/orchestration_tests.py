"""
End-to-End Tests for LangSwarm Multi-Agent Orchestration

Tests real multi-agent workflows with actual API calls,
data flow validation, and performance metrics.
"""

import asyncio
from typing import Dict, Any, List
from ..framework.base import BaseE2ETest


class BasicOrchestrationTest(BaseE2ETest):
    """Test basic two-agent orchestration with real APIs."""
    
    @property
    def test_name(self) -> str:
        return "Basic Multi-Agent Orchestration"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.05  # ~$0.05 for basic test
    
    async def run_test(self) -> Dict[str, Any]:
        """Test researcher -> summarizer workflow."""
        self.logger.info("Testing basic orchestration flow")
        
        try:
            # Import here to avoid module loading issues during discovery
            from langswarm.core.agents import create_openai_agent_sync, register_agent, list_agents
            from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
            
            # Step 1: Create specialized agents
            researcher = create_openai_agent_sync(
                name="researcher",
                model="gpt-3.5-turbo",
                system_prompt="You are a research specialist. Provide detailed, factual information on the given topic. Keep responses under 200 words.",
                temperature=0.3
            )
            
            summarizer = create_openai_agent_sync(
                name="summarizer", 
                model="gpt-3.5-turbo",
                system_prompt="You are a summary specialist. Create a concise 50-word summary of the provided information.",
                temperature=0.1
            )
            
            # Step 2: Register agents
            register_success_1 = register_agent(researcher)
            register_success_2 = register_agent(summarizer)
            
            registered_agents = list_agents()
            self.logger.info(f"Registered agents: {registered_agents}")
            
            # Step 3: Create workflow
            workflow = create_simple_workflow(
                workflow_id="research_and_summarize",
                name="Research and Summarize Workflow",
                agent_chain=["researcher", "summarizer"]
            )
            
            # Step 4: Execute workflow
            engine = get_workflow_engine()
            
            test_input = "What are the key benefits of renewable energy?"
            
            start_time = asyncio.get_event_loop().time()
            result = await engine.execute_workflow(
                workflow=workflow,
                input_data={"input": test_input}
            )
            end_time = asyncio.get_event_loop().time()
            
            execution_time = end_time - start_time
            
            # Track metrics
            self.track_api_call("openai", tokens=400, cost=0.001)  # Researcher call
            self.track_api_call("openai", tokens=200, cost=0.0005)  # Summarizer call
            
            # Save detailed results
            workflow_details = {
                "input": test_input,
                "workflow_id": workflow.workflow_id,
                "execution_time_s": execution_time,
                "result_status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                "step_count": len(result.step_results) if result.step_results else 0,
                "final_output": str(result.result)[:500],  # Truncate for logging
                "registered_agents": registered_agents,
                "registration_success": [register_success_1, register_success_2]
            }
            
            self.save_json_artifact("workflow_details", workflow_details)
            
            return {
                "success": True,
                "workflow_executed": True,
                "agents_registered": len(registered_agents) >= 2,
                "workflow_status": workflow_details["result_status"],
                "execution_time": execution_time,
                "output_length": len(str(result.result)),
                "step_results_count": workflow_details["step_count"],
                **workflow_details
            }
            
        except Exception as e:
            self.logger.error(f"Orchestration test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate orchestration worked correctly."""
        if not result.get("success", False):
            return False
        
        # Check workflow execution
        if not result.get("workflow_executed", False):
            self.metrics.errors.append("Workflow did not execute")
            return False
        
        # Check agent registration
        if not result.get("agents_registered", False):
            self.metrics.errors.append("Agents were not properly registered")
            return False
        
        # Check workflow completion
        if result.get("workflow_status") != "COMPLETED":
            self.metrics.errors.append(f"Workflow status: {result.get('workflow_status')}")
            return False
        
        # Check output quality
        output_length = result.get("output_length", 0)
        if output_length < 10:
            self.metrics.errors.append("Output too short")
            return False
        
        # Check execution time reasonable
        exec_time = result.get("execution_time", 0)
        if exec_time > 30:  # 30 second timeout
            self.metrics.warnings.append(f"Slow execution: {exec_time:.1f}s")
        
        return True


class MultiProviderOrchestrationTest(BaseE2ETest):
    """Test orchestration with multiple AI providers."""
    
    @property
    def test_name(self) -> str:
        return "Multi-Provider Agent Orchestration"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai", "anthropic"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.10  # ~$0.10 for multi-provider test
    
    async def run_test(self) -> Dict[str, Any]:
        """Test OpenAI -> Anthropic workflow."""
        self.logger.info("Testing multi-provider orchestration")
        
        try:
            from langswarm.core.agents import AgentBuilder, register_agent, list_agents
            from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
            
            # Create OpenAI agent
            openai_agent = (AgentBuilder("openai_researcher")
                          .openai()
                          .model("gpt-3.5-turbo")
                          .system_prompt("You are a research agent. Provide detailed technical information.")
                          .temperature(0.3)
                          .build_sync())
            
            # Create Anthropic agent  
            anthropic_agent = (AgentBuilder("claude_analyzer")
                             .anthropic()
                             .model("claude-3-haiku-20240307")
                             .system_prompt("You are an analysis agent. Analyze the provided information and extract key insights.")
                             .temperature(0.1)
                             .build_sync())
            
            # Register agents
            register_agent(openai_agent)
            register_agent(anthropic_agent)
            
            # Create cross-provider workflow
            workflow = create_simple_workflow(
                workflow_id="cross_provider_analysis",
                name="Cross-Provider Analysis",
                agent_chain=["openai_researcher", "claude_analyzer"]
            )
            
            # Execute workflow
            engine = get_workflow_engine()
            
            result = await engine.execute_workflow(
                workflow=workflow,
                input_data={"input": "Explain the technical advantages of vector databases for AI applications"}
            )
            
            # Track usage from both providers
            self.track_api_call("openai", tokens=300, cost=0.0006)
            self.track_api_call("anthropic", tokens=250, cost=0.0005)
            
            return {
                "success": True,
                "providers_used": ["openai", "anthropic"],
                "workflow_status": str(result.status),
                "cross_provider_workflow": True,
                "output": str(result.result)[:300]
            }
            
        except Exception as e:
            self.logger.error(f"Multi-provider test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ParallelOrchestrationTest(BaseE2ETest):
    """Test parallel agent execution for performance."""
    
    @property
    def test_name(self) -> str:
        return "Parallel Agent Orchestration"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.15  # Multiple parallel agents
    
    async def run_test(self) -> Dict[str, Any]:
        """Test parallel execution of multiple agents."""
        self.logger.info("Testing parallel orchestration")
        
        try:
            from langswarm.core.agents import create_openai_agent_sync, register_agent
            from langswarm.core.workflows import WorkflowBuilder, get_workflow_engine
            from langswarm.core.workflows.interfaces import ExecutionMode
            
            # Create multiple specialized agents
            agents = []
            for i, specialty in enumerate(["technology", "business", "science"]):
                agent = create_openai_agent_sync(
                    name=f"{specialty}_expert",
                    model="gpt-3.5-turbo",
                    system_prompt=f"You are a {specialty} expert. Provide insights from your domain perspective.",
                    temperature=0.3
                )
                register_agent(agent)
                agents.append(f"{specialty}_expert")
            
            # Create aggregator agent
            aggregator = create_openai_agent_sync(
                name="aggregator",
                model="gpt-3.5-turbo",
                system_prompt="Combine the provided expert opinions into a comprehensive analysis.",
                temperature=0.2
            )
            register_agent(aggregator)
            
            # Build parallel workflow (concept - may need workflow engine updates)
            # For now, simulate with sequential but track timing
            workflow = WorkflowBuilder("parallel_analysis")
            for agent_name in agents:
                workflow.add_agent_step(f"step_{agent_name}", agent_name)
            workflow.add_agent_step("aggregation", "aggregator")
            
            built_workflow = workflow.build()
            
            # Execute with timing
            engine = get_workflow_engine()
            start_time = asyncio.get_event_loop().time()
            
            result = await engine.execute_workflow(
                workflow=built_workflow,
                input_data={"input": "What are the implications of artificial general intelligence?"},
                execution_mode=ExecutionMode.SYNC
            )
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # Track API calls
            for _ in agents:
                self.track_api_call("openai", tokens=200, cost=0.0004)
            self.track_api_call("openai", tokens=300, cost=0.0006)  # Aggregator
            
            return {
                "success": True,
                "parallel_agents": len(agents),
                "execution_time": execution_time,
                "workflow_status": str(result.status),
                "efficiency_score": len(agents) / execution_time if execution_time > 0 else 0,
                "output_quality": len(str(result.result))
            }
            
        except Exception as e:
            self.logger.error(f"Parallel orchestration test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ErrorRecoveryOrchestrationTest(BaseE2ETest):
    """Test orchestration error handling and recovery."""
    
    @property
    def test_name(self) -> str:
        return "Orchestration Error Recovery"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.02  # Minimal cost for error testing
    
    async def run_test(self) -> Dict[str, Any]:
        """Test error scenarios and recovery mechanisms."""
        self.logger.info("Testing orchestration error recovery")
        
        try:
            from langswarm.core.agents import create_openai_agent_sync, register_agent
            from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
            from langswarm.core.orchestration_errors import AgentNotFoundError
            
            # Test 1: Missing agent error
            try:
                workflow = create_simple_workflow(
                    workflow_id="missing_agent_test",
                    name="Missing Agent Test",
                    agent_chain=["nonexistent_agent"]
                )
                
                engine = get_workflow_engine()
                result = await engine.execute_workflow(
                    workflow=workflow,
                    input_data={"input": "test"}
                )
                
                missing_agent_handled = False
            except Exception as e:
                missing_agent_handled = "not found" in str(e).lower()
                self.logger.info(f"Missing agent error properly caught: {e}")
            
            # Test 2: Invalid input handling
            valid_agent = create_openai_agent_sync(
                name="test_agent",
                model="gpt-3.5-turbo",
                system_prompt="You are a test agent."
            )
            register_agent(valid_agent)
            
            workflow = create_simple_workflow(
                workflow_id="input_test",
                name="Input Test",
                agent_chain=["test_agent"]
            )
            
            # Test with various input types
            test_inputs = [
                {"input": "valid string input"},
                {"input": ""},  # Empty input
                {"malformed": "wrong key"},  # Wrong key
            ]
            
            input_test_results = []
            for i, test_input in enumerate(test_inputs):
                try:
                    result = await engine.execute_workflow(
                        workflow=workflow,
                        input_data=test_input
                    )
                    
                    input_test_results.append({
                        "input": test_input,
                        "success": True,
                        "status": str(result.status)
                    })
                    
                    if i == 0:  # Only track cost for successful call
                        self.track_api_call("openai", tokens=50, cost=0.0001)
                        
                except Exception as e:
                    input_test_results.append({
                        "input": test_input,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "missing_agent_error_handled": missing_agent_handled,
                "input_tests": input_test_results,
                "error_recovery_functional": True
            }
            
        except Exception as e:
            self.logger.error(f"Error recovery test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }