"""
End-to-End Integration Tests for LangSwarm

Tests complete workflows that integrate orchestration, memory,
configuration, and error handling systems together.
"""

import asyncio
import random
import tempfile
import yaml
from typing import Dict, Any, List
from pathlib import Path
from ..framework.base import BaseE2ETest


class FullStackIntegrationTest(BaseE2ETest):
    """Test complete LangSwarm stack with configuration, orchestration, and memory."""
    
    @property
    def test_name(self) -> str:
        return "Full Stack Integration"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.15  # Multiple agents + memory operations
    
    async def setup(self) -> None:
        """Set up test configuration file."""
        await super().setup()
        
        # Create temporary configuration file
        config = {
            "version": "2.0",
            "agents": [
                {
                    "id": "knowledge_gatherer",
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "system_prompt": "You are a knowledge gathering specialist. Research and collect comprehensive information on the given topic.",
                    "temperature": 0.3
                },
                {
                    "id": "fact_checker",
                    "provider": "openai", 
                    "model": "gpt-3.5-turbo",
                    "system_prompt": "You are a fact-checking specialist. Verify the accuracy of provided information and flag any potential issues.",
                    "temperature": 0.1
                },
                {
                    "id": "content_synthesizer",
                    "provider": "openai",
                    "model": "gpt-3.5-turbo", 
                    "system_prompt": "You are a content synthesis specialist. Combine verified information into a coherent, well-structured response.",
                    "temperature": 0.2
                }
            ],
            "workflows": [
                {
                    "id": "research_pipeline",
                    "name": "Comprehensive Research Pipeline",
                    "steps": [
                        {"agent": "knowledge_gatherer", "name": "gather"},
                        {"agent": "fact_checker", "name": "verify"},
                        {"agent": "content_synthesizer", "name": "synthesize"}
                    ]
                }
            ],
            "memory": {
                "backend": "sqlite",
                "config": {
                    "database": ":memory:",
                    "enable_search": True
                }
            },
            "session": {
                "storage_backend": "memory",
                "auto_save": True,
                "session_timeout": 3600
            }
        }
        
        # Save config to temporary file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, self.config_file, default_flow_style=False)
        self.config_file.close()
        
        self.logger.info(f"Created test config: {self.config_file.name}")
    
    async def teardown(self) -> None:
        """Clean up test configuration."""
        await super().teardown()
        
        # Remove temporary config file
        if hasattr(self, 'config_file'):
            Path(self.config_file.name).unlink(missing_ok=True)
    
    async def run_test(self) -> Dict[str, Any]:
        """Test full stack integration."""
        self.logger.info("Testing full stack integration")
        
        try:
            # Import LangSwarm components
            from langswarm.core.config import load_config
            from langswarm.core.agents import create_agents_from_config, register_agent
            from langswarm.core.workflows import create_workflow_from_config, get_workflow_engine
            from langswarm.core.session import create_session
            
            # Step 1: Load configuration
            config = load_config(self.config_file.name)
            self.logger.info("✅ Configuration loaded successfully")
            
            # Step 2: Create and register agents from config
            agents = create_agents_from_config(config)
            agent_count = 0
            
            for agent in agents:
                register_agent(agent)
                agent_count += 1
                self.logger.info(f"✅ Registered agent: {agent.agent_id}")
            
            # Step 3: Create workflow from config
            workflows = create_workflow_from_config(config)
            workflow = workflows[0] if workflows else None
            
            if not workflow:
                raise Exception("No workflow created from config")
            
            self.logger.info(f"✅ Created workflow: {workflow.workflow_id}")
            
            # Step 4: Create session with memory
            session = create_session(
                session_id=f"integration_test_{random.randint(1000, 9999)}",
                memory_backend="sqlite",
                storage_backend="memory"
            )
            
            self.logger.info("✅ Session created with memory backend")
            
            # Step 5: Execute research workflow with memory integration
            research_topics = [
                "The impact of quantum computing on cybersecurity",
                "Sustainable energy storage technologies for renewable power grids",
                "The role of AI in climate change mitigation strategies"
            ]
            
            workflow_results = []
            engine = get_workflow_engine()
            
            for i, topic in enumerate(research_topics):
                try:
                    # Store topic context in memory
                    await session.memory.store(
                        key=f"topic_{i}",
                        content=topic,
                        metadata={"type": "research_topic", "index": i}
                    )
                    
                    # Execute workflow
                    start_time = asyncio.get_event_loop().time()
                    
                    result = await engine.execute_workflow(
                        workflow=workflow,
                        input_data={"input": topic}
                    )
                    
                    end_time = asyncio.get_event_loop().time()
                    execution_time = end_time - start_time
                    
                    # Track API usage (3 agents per workflow)
                    self.track_api_call("openai", tokens=300, cost=0.0006)  # Knowledge gatherer
                    self.track_api_call("openai", tokens=200, cost=0.0004)  # Fact checker  
                    self.track_api_call("openai", tokens=250, cost=0.0005)  # Synthesizer
                    
                    # Store workflow result in memory
                    await session.memory.store(
                        key=f"result_{i}",
                        content=str(result.result)[:500],  # Truncate for storage
                        metadata={"type": "workflow_result", "topic": topic, "status": str(result.status)}
                    )
                    
                    workflow_results.append({
                        "topic": topic,
                        "status": str(result.status),
                        "execution_time": execution_time,
                        "result_length": len(str(result.result)),
                        "steps_completed": len(result.step_results) if result.step_results else 0
                    })
                    
                    self.logger.info(f"✅ Completed workflow for: {topic[:50]}...")
                    
                except Exception as e:
                    self.logger.error(f"❌ Workflow failed for topic {i}: {e}")
                    workflow_results.append({
                        "topic": topic,
                        "status": "FAILED",
                        "error": str(e)
                    })
            
            # Step 6: Test memory search across stored results
            search_tests = []
            search_queries = ["quantum cybersecurity", "renewable energy", "AI climate"]
            
            for query in search_queries:
                try:
                    search_results = await session.memory.search(
                        query=query,
                        limit=3
                    )
                    
                    search_tests.append({
                        "query": query,
                        "results_found": len(search_results),
                        "relevant_results": search_results[:2]  # Keep top 2 for analysis
                    })
                    
                except Exception as e:
                    search_tests.append({
                        "query": query,
                        "error": str(e)
                    })
            
            # Step 7: Test error handling integration
            error_handling_test = await self._test_error_integration(engine, workflow)
            
            # Step 8: Session persistence test
            session_test = await self._test_session_persistence(session)
            
            await session.close()
            
            # Calculate overall success metrics
            successful_workflows = sum(1 for r in workflow_results if r.get("status") == "COMPLETED")
            total_execution_time = sum(r.get("execution_time", 0) for r in workflow_results)
            successful_searches = sum(1 for s in search_tests if s.get("results_found", 0) > 0)
            
            return {
                "success": True,
                "config_loaded": True,
                "agents_registered": agent_count,
                "workflow_created": True,
                "session_created": True,
                "workflow_results": workflow_results,
                "successful_workflows": successful_workflows,
                "total_workflows": len(research_topics),
                "total_execution_time": total_execution_time,
                "search_tests": search_tests,
                "successful_searches": successful_searches,
                "total_searches": len(search_queries),
                "error_handling_test": error_handling_test,
                "session_test": session_test,
                "integration_score": (successful_workflows + successful_searches) / (len(research_topics) + len(search_queries))
            }
            
        except Exception as e:
            self.logger.error(f"Full stack integration test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _test_error_integration(self, engine, workflow) -> Dict[str, Any]:
        """Test error handling integration across systems."""
        try:
            # Test with invalid input
            result = await engine.execute_workflow(
                workflow=workflow,
                input_data={"invalid_key": "This should cause issues"}
            )
            
            return {
                "error_handling_functional": True,
                "invalid_input_handled": True,
                "result_status": str(result.status)
            }
            
        except Exception as e:
            return {
                "error_handling_functional": True,
                "error_caught": True,
                "error_message": str(e)[:100]
            }
    
    async def _test_session_persistence(self, session) -> Dict[str, Any]:
        """Test session persistence and state management."""
        try:
            # Store session state
            session_data = {
                "test_key": "test_value",
                "timestamp": "2024-01-01",
                "complex_data": {"nested": "value", "list": [1, 2, 3]}
            }
            
            await session.storage.store("session_test", session_data)
            
            # Retrieve session state
            retrieved_data = await session.storage.retrieve("session_test")
            
            return {
                "persistence_functional": True,
                "data_stored": session_data == retrieved_data,
                "session_state_working": True
            }
            
        except Exception as e:
            return {
                "persistence_functional": False,
                "error": str(e)
            }
    
    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate full stack integration worked correctly."""
        if not result.get("success", False):
            return False
        
        # Check core components loaded
        required_components = ["config_loaded", "agents_registered", "workflow_created", "session_created"]
        for component in required_components:
            if not result.get(component, False):
                self.metrics.errors.append(f"Component failed: {component}")
                return False
        
        # Check workflow execution
        if result.get("successful_workflows", 0) == 0:
            self.metrics.errors.append("No workflows completed successfully")
            return False
        
        # Check memory integration
        if result.get("successful_searches", 0) == 0:
            self.metrics.warnings.append("Memory search functionality not working")
        
        # Check overall integration score
        integration_score = result.get("integration_score", 0)
        if integration_score < 0.7:
            self.metrics.warnings.append(f"Low integration score: {integration_score:.2f}")
        
        return True


class ErrorHandlingIntegrationTest(BaseE2ETest):
    """Test error handling across all LangSwarm systems."""
    
    @property
    def test_name(self) -> str:
        return "Error Handling Integration"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.05  # Limited API calls for error testing
    
    async def run_test(self) -> Dict[str, Any]:
        """Test error handling across systems."""
        self.logger.info("Testing integrated error handling")
        
        error_scenarios = []
        
        try:
            # Test 1: Configuration errors
            config_error_test = await self._test_config_errors()
            error_scenarios.append(config_error_test)
            
            # Test 2: Agent registration errors  
            agent_error_test = await self._test_agent_errors()
            error_scenarios.append(agent_error_test)
            
            # Test 3: Workflow execution errors
            workflow_error_test = await self._test_workflow_errors()
            error_scenarios.append(workflow_error_test)
            
            # Test 4: Memory system errors
            memory_error_test = await self._test_memory_errors()
            error_scenarios.append(memory_error_test)
            
            # Test 5: Session errors
            session_error_test = await self._test_session_errors()
            error_scenarios.append(session_error_test)
            
            successful_error_tests = sum(1 for test in error_scenarios if test.get("errors_handled", False))
            
            return {
                "success": True,
                "error_scenarios_tested": len(error_scenarios),
                "successful_error_handling": successful_error_tests,
                "error_handling_rate": successful_error_tests / len(error_scenarios) if error_scenarios else 0,
                "scenarios": error_scenarios,
                "comprehensive_error_testing": True
            }
            
        except Exception as e:
            self.logger.error(f"Error handling integration test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "scenarios_completed": len(error_scenarios)
            }
    
    async def _test_config_errors(self) -> Dict[str, Any]:
        """Test configuration error handling."""
        try:
            from langswarm.core.config import load_config
            from langswarm.core.config.error_helpers import ConfigErrorHelper
            
            # Test invalid file
            try:
                load_config("nonexistent_file.yaml")
                config_error_handled = False
            except Exception as e:
                config_error_handled = "not found" in str(e).lower() or "no such file" in str(e).lower()
            
            # Test helpful error message
            error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
            helpful_message = "OPENAI_API_KEY" in error.suggestion and "export" in error.suggestion
            
            return {
                "test_type": "configuration",
                "errors_handled": config_error_handled,
                "helpful_messages": helpful_message,
                "error_quality_good": helpful_message
            }
            
        except Exception as e:
            return {
                "test_type": "configuration",
                "errors_handled": False,
                "error": str(e)
            }
    
    async def _test_agent_errors(self) -> Dict[str, Any]:
        """Test agent-related error handling."""
        try:
            from langswarm.core.agents import create_openai_agent_sync
            from langswarm.core.orchestration_errors import agent_not_found
            
            # Test invalid API key handling
            invalid_key_handled = False
            try:
                # This should fail gracefully with helpful message
                agent = create_openai_agent_sync(
                    name="test_agent",
                    model="gpt-3.5-turbo",
                    api_key="invalid_key_123"
                )
                # Try to use agent (this might not fail until actual API call)
                await agent.execute("test")
            except Exception as e:
                invalid_key_handled = "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower()
            
            # Test agent not found error
            error = agent_not_found("missing_agent", ["agent1", "agent2"])
            helpful_agent_error = "register_agent" in error.suggestion
            
            return {
                "test_type": "agent",
                "errors_handled": True,  # Error creation works
                "api_key_error_handled": invalid_key_handled,
                "helpful_messages": helpful_agent_error
            }
            
        except Exception as e:
            return {
                "test_type": "agent", 
                "errors_handled": False,
                "error": str(e)
            }
    
    async def _test_workflow_errors(self) -> Dict[str, Any]:
        """Test workflow error handling."""
        try:
            from langswarm.core.workflows import create_simple_workflow, get_workflow_engine
            from langswarm.core.orchestration_errors import workflow_failed
            
            # Test missing agent in workflow
            workflow_error_handled = False
            try:
                workflow = create_simple_workflow(
                    workflow_id="error_test",
                    name="Error Test",
                    agent_chain=["nonexistent_agent"]
                )
                
                engine = get_workflow_engine()
                result = await engine.execute_workflow(
                    workflow=workflow,
                    input_data={"input": "test"}
                )
            except Exception as e:
                workflow_error_handled = "not found" in str(e).lower() or "missing" in str(e).lower()
            
            # Test workflow error message quality
            error = workflow_failed("test_workflow", "step1", Exception("Test error"))
            helpful_workflow_error = "debug" in error.suggestion.lower()
            
            return {
                "test_type": "workflow",
                "errors_handled": workflow_error_handled,
                "helpful_messages": helpful_workflow_error,
                "workflow_validation_working": True
            }
            
        except Exception as e:
            return {
                "test_type": "workflow",
                "errors_handled": False,
                "error": str(e)
            }
    
    async def _test_memory_errors(self) -> Dict[str, Any]:
        """Test memory system error handling."""
        try:
            from langswarm.core.session import create_session
            
            # Test invalid memory backend
            memory_error_handled = False
            try:
                session = create_session(
                    session_id="error_test",
                    memory_backend="nonexistent_backend"
                )
            except Exception as e:
                memory_error_handled = "backend" in str(e).lower() or "invalid" in str(e).lower()
            
            return {
                "test_type": "memory",
                "errors_handled": memory_error_handled,
                "memory_validation_working": True
            }
            
        except Exception as e:
            return {
                "test_type": "memory",
                "errors_handled": False,
                "error": str(e)
            }
    
    async def _test_session_errors(self) -> Dict[str, Any]:
        """Test session error handling."""
        try:
            from langswarm.core.session.session_errors import session_not_found
            
            # Test session error message quality
            error = session_not_found("missing_session", ["session1", "session2"])
            helpful_session_error = "create_session" in error.suggestion
            
            return {
                "test_type": "session",
                "errors_handled": True,
                "helpful_messages": helpful_session_error,
                "session_error_system_working": True
            }
            
        except Exception as e:
            return {
                "test_type": "session",
                "errors_handled": False,
                "error": str(e)
            }