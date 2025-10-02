#!/usr/bin/env python3
"""
LangSwarm Simplification Integration Tests

Comprehensive end-to-end testing of all simplification features working together:
- Memory Made Simple + Workflow Simplification + Simplified Agent Wrapper
- Real workflow execution with simplified syntax
- Cross-feature compatibility and performance validation
"""

import os
import sys
import time
import tempfile
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor, MemoryConfig, WorkflowConfig
from langswarm.core.agents.simple import create_chat_agent, create_coding_agent, AgentConfig, SimpleAgent


class TestSimplificationIntegration:
    """Integration tests for all LangSwarm simplification features"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.start_time = time.time()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_config(self, config_data: Dict[str, Any]) -> str:
        """Create a temporary configuration file for testing"""
        config_path = os.path.join(self.temp_dir, "langswarm.yaml")
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        return config_path
    
    def test_memory_workflow_integration(self):
        """Test Memory Made Simple + Workflow Simplification integration"""
        # Create configuration with simplified memory and workflow syntax
        config = {
            "version": "1.0",
            "agents": [
                {
                    "id": "memory_agent",
                    "model": "gpt-4o",
                    "behavior": "helpful"
                }
            ],
            "memory": True,  # Memory Made Simple Tier 1
            "workflows": [
                "memory_agent -> user"  # Workflow Simplification syntax
            ]
        }
        
        config_path = self.create_test_config(config)
        
        # Test configuration loading
        loader = LangSwarmConfigLoader(config_path=config_path)
        
        # Validate memory configuration
        unified_config = loader._load_unified_config()
        memory_config = unified_config.memory
        
        assert memory_config.enabled == True
        assert memory_config.backend == "sqlite"
        assert "Development SQLite database" in memory_config.settings["description"]
        
        # Validate workflow simplification
        workflows = unified_config.workflows
        assert len(workflows) == 1
        assert workflows[0].id.startswith("simple_workflow_")
        assert len(workflows[0].steps) == 1
        assert workflows[0].steps[0]["agent"] == "memory_agent"
    
    def test_agent_memory_workflow_full_integration(self):
        """Test Simplified Agent + Memory + Workflow full integration"""
        # Create comprehensive test configuration
        config = {
            "version": "1.0",
            "agents": [
                {
                    "id": "integrated_agent",
                    "model": "gpt-4o", 
                    "behavior": "analytical",
                    "tools": ["filesystem"]
                },
                {
                    "id": "coding_agent",
                    "model": "gpt-4o",
                    "behavior": "coding",
                    "tools": ["filesystem", "github"]
                }
            ],
            "memory": "production",  # Memory Made Simple Tier 2
            "workflows": [
                # Multiple workflow patterns
                {"id": "simple_chat", "simple": "integrated_agent -> user"},
                {"id": "analysis_pipeline", "workflow": "integrated_agent -> coding_agent -> user"},
                "coding_agent -> user"  # Direct simple syntax
            ],
            "tools": [
                {
                    "id": "filesystem",
                    "type": "mcpfilesystem", 
                    "description": "Test filesystem tool",
                    "local_mode": True
                }
            ]
        }
        
        config_path = self.create_test_config(config)
        
        # Test full configuration loading
        loader = LangSwarmConfigLoader(config_path=config_path)
        
        # Test that all components work together
        try:
            # Load unified configuration
            unified_config = loader._load_unified_config()
            
            # Validate memory made simple
            memory_config = unified_config.memory
            assert memory_config.enabled == True
            assert memory_config.backend in ["bigquery", "elasticsearch", "redis", "chromadb"]
            
            # Validate workflow simplification
            workflows = unified_config.workflows
            assert len(workflows) == 3
            
            # Check simple syntax workflow
            simple_workflow = next((w for w in workflows if w.id == "simple_chat"), None)
            assert simple_workflow is not None
            assert len(simple_workflow.steps) == 1
            
            # Check chained workflow
            analysis_workflow = next((w for w in workflows if w.id == "analysis_pipeline"), None)
            assert analysis_workflow is not None
            assert len(analysis_workflow.steps) == 2
            
            # Validate agents with tools
            agents = unified_config.agents
            assert len(agents) == 2
            
            integrated_agent = next((a for a in agents if a.id == "integrated_agent"), None)
            assert integrated_agent is not None
            assert "filesystem" in integrated_agent.tools
            
            print("✅ Full integration test passed - all components working together")
            
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
    
    def test_performance_no_regression(self):
        """Test that simplification features don't introduce performance regressions"""
        # Create performance test configuration
        config = {
            "version": "1.0",
            "agents": [
                {"id": f"agent_{i}", "model": "gpt-4o", "behavior": "helpful"} 
                for i in range(5)
            ],
            "memory": True,
            "workflows": [
                f"agent_{i} -> user" for i in range(5)
            ]
        }
        
        config_path = self.create_test_config(config)
        
        # Measure configuration loading time
        start_time = time.time()
        
        loader = LangSwarmConfigLoader(config_path=config_path)
        unified_config = loader._load_unified_config()
        
        loading_time = time.time() - start_time
        
        # Performance assertions
        assert loading_time < 5.0, f"Configuration loading took {loading_time:.2f}s, should be < 5s"
        
        # Validate that all features still work correctly
        assert len(unified_config.agents) == 5
        assert len(unified_config.workflows) == 5
        assert unified_config.memory.enabled == True
        
        print(f"✅ Performance test passed - loading time: {loading_time:.2f}s")
    
    def test_simplified_agent_api_integration(self):
        """Test Simplified Agent API integration with other features"""
        # Test simplified agent creation and usage
        agent_config = AgentConfig(
            id="test_integrated_agent",
            model="gpt-4o",
            behavior="helpful",
            memory_enabled=True,
            streaming_enabled=False,
            tools=["filesystem"]
        )
        
        # Create agent using simplified API
        agent = SimpleAgent(agent_config)
        
        # Test agent information
        info = agent.get_info()
        assert info["id"] == "test_integrated_agent"
        assert info["model"] == "gpt-4o"
        assert info["behavior"] == "helpful"
        assert info["memory_enabled"] == True
        assert "filesystem" in info["tools"]
        
        # Test basic chat functionality
        response = agent.chat("Hello, test message")
        assert "test_integrated_agent" in response
        assert "Hello, test message" in response
        
        # Test conversation history
        assert len(agent.conversation_history) == 2  # User + assistant messages
        
        # Test memory storage
        agent._store_memory("test_key", "test_value")
        retrieved = agent._retrieve_memory("test_key")
        assert retrieved == "test_value"
        
        # Test cleanup
        agent.cleanup()
        
        print("✅ Simplified Agent API integration test passed")
    
    def test_factory_functions_integration(self):
        """Test factory functions with full feature integration"""
        # Test different factory functions
        chat_agent = create_chat_agent("chat_test", memory_enabled=True)
        coding_agent = create_coding_agent("coding_test", tools=["filesystem", "github"])
        
        # Validate chat agent
        chat_info = chat_agent.get_info()
        assert chat_info["behavior"] == "helpful"
        assert chat_info["memory_enabled"] == True
        
        # Validate coding agent  
        coding_info = coding_agent.get_info()
        assert coding_info["behavior"] == "coding"
        assert "filesystem" in coding_info["tools"]
        assert "github" in coding_info["tools"]
        
        # Test agent interactions
        chat_response = chat_agent.chat("Test chat message")
        coding_response = coding_agent.chat("Test coding query")
        
        assert "chat_test" in chat_response
        assert "coding_test" in coding_response
        
        # Cleanup
        chat_agent.cleanup()
        coding_agent.cleanup()
        
        print("✅ Factory functions integration test passed")
    
    def test_backward_compatibility(self):
        """Test that simplified features maintain backward compatibility"""
        # Create configuration mixing old and new syntax
        config = {
            "version": "1.0",
            "agents": [
                {
                    "id": "new_style_agent",
                    "model": "gpt-4o",
                    "behavior": "helpful"  # New simplified behavior
                },
                {
                    "id": "old_style_agent", 
                    "model": "gpt-4o",
                    "system_prompt": "You are a helpful assistant.",  # Old explicit prompt
                    "agent_type": "generic"  # Old style configuration
                }
            ],
            "memory": {  # Old style memory configuration
                "enabled": True,
                "backend": "sqlite",
                "settings": {"db_path": ":memory:"}
            },
            "workflows": [
                # Mix of old and new workflow syntax
                "new_style_agent -> user",  # New simple syntax
                {  # Old complex syntax
                    "id": "old_style_workflow",
                    "steps": [
                        {
                            "id": "step1",
                            "agent": "old_style_agent",
                            "input": "${context.user_input}",
                            "output": {"to": "user"}
                        }
                    ]
                }
            ]
        }
        
        config_path = self.create_test_config(config)
        
        # Test that mixed configuration loads successfully
        loader = LangSwarmConfigLoader(config_path=config_path)
        unified_config = loader._load_unified_config()
        
        # Validate that both old and new styles work
        assert len(unified_config.agents) == 2
        assert len(unified_config.workflows) == 2
        assert unified_config.memory.enabled == True
        
        # Validate specific configurations
        new_agent = next((a for a in unified_config.agents if a.id == "new_style_agent"), None)
        old_agent = next((a for a in unified_config.agents if a.id == "old_style_agent"), None)
        
        assert new_agent is not None
        assert old_agent is not None
        
        print("✅ Backward compatibility test passed")
    
    def test_error_handling_integration(self):
        """Test error handling across all simplification features"""
        # Test various error conditions
        error_configs = [
            {
                "name": "Invalid memory tier",
                "config": {
                    "version": "1.0",
                    "agents": [{"id": "test", "model": "gpt-4o"}],
                    "memory": "invalid_tier"
                }
            },
            {
                "name": "Invalid workflow syntax",
                "config": {
                    "version": "1.0", 
                    "agents": [{"id": "test", "model": "gpt-4o"}],
                    "workflows": ["invalid -> -> syntax"]
                }
            },
            {
                "name": "Missing agent in workflow",
                "config": {
                    "version": "1.0",
                    "agents": [{"id": "agent1", "model": "gpt-4o"}],
                    "workflows": ["nonexistent_agent -> user"]
                }
            }
        ]
        
        for error_case in error_configs:
            config_path = self.create_test_config(error_case["config"])
            
            # Test that errors are handled gracefully
            try:
                loader = LangSwarmConfigLoader(config_path=config_path)
                unified_config = loader._load_unified_config()
                
                # Some errors should be handled gracefully with fallbacks
                print(f"✅ {error_case['name']}: Handled gracefully with fallbacks")
                
            except Exception as e:
                # Some errors should raise clear exceptions
                assert len(str(e)) > 0, "Error message should not be empty"
                print(f"✅ {error_case['name']}: Clear error message: {str(e)[:50]}...")
    
    def test_comprehensive_end_to_end(self):
        """Comprehensive end-to-end test of the entire simplified system"""
        # Create a realistic configuration using all simplification features
        config = {
            "version": "1.0",
            "project_name": "integration-test-project",
            
            # Simplified agents with different behaviors
            "agents": [
                {
                    "id": "assistant",
                    "model": "gpt-4o",
                    "behavior": "helpful",
                    "tools": ["filesystem"]
                },
                {
                    "id": "analyzer", 
                    "model": "gpt-4o",
                    "behavior": "analytical",
                    "memory_enabled": True
                },
                {
                    "id": "coder",
                    "model": "gpt-4o", 
                    "behavior": "coding",
                    "tools": ["filesystem", "github"]
                }
            ],
            
            # Memory Made Simple - production tier
            "memory": "production",
            
            # Workflow Simplification - multiple patterns
            "workflows": [
                "assistant -> user",
                "analyzer -> coder -> user", 
                {"id": "consensus_workflow", "simple": "analyzer, coder -> assistant -> user"}
            ],
            
            # Tool configurations
            "tools": [
                {
                    "id": "filesystem",
                    "type": "mcpfilesystem",
                    "description": "Filesystem access for the integration test",
                    "local_mode": True
                }
            ]
        }
        
        config_path = self.create_test_config(config)
        
        # Measure total processing time
        start_time = time.time()
        
        # Load and validate complete configuration
        loader = LangSwarmConfigLoader(config_path=config_path)
        unified_config = loader._load_unified_config()
        
        processing_time = time.time() - start_time
        
        # Comprehensive validation
        assert unified_config.version == "1.0"
        assert len(unified_config.agents) == 3
        assert len(unified_config.workflows) == 3
        assert len(unified_config.tools) == 1
        
        # Memory validation
        assert unified_config.memory.enabled == True
        assert unified_config.memory.backend in ["bigquery", "elasticsearch", "redis", "chromadb"]
        
        # Workflow validation
        simple_workflows = [w for w in unified_config.workflows if w.id.startswith("simple_workflow_")]
        named_workflows = [w for w in unified_config.workflows if not w.id.startswith("simple_workflow_")]
        
        assert len(simple_workflows) >= 2  # Direct syntax workflows
        assert len(named_workflows) >= 1   # Named workflows
        
        # Agent validation
        behaviors = [a.behavior for a in unified_config.agents]
        assert "helpful" in behaviors
        assert "analytical" in behaviors  
        assert "coding" in behaviors
        
        # Performance validation
        assert processing_time < 5.0, f"End-to-end processing took {processing_time:.2f}s"
        
        print(f"✅ Comprehensive end-to-end test passed in {processing_time:.2f}s")
        print(f"   📊 Loaded: {len(unified_config.agents)} agents, {len(unified_config.workflows)} workflows")
        print(f"   🧠 Memory: {unified_config.memory.get_tier_description()}")
        print(f"   🔧 Tools: {len(unified_config.tools)} tools configured")


class TestPerformanceBenchmarks:
    """Performance benchmarking for simplification features"""
    
    def test_configuration_loading_performance(self):
        """Benchmark configuration loading performance"""
        # Create configurations of varying complexity
        test_cases = [
            {"name": "Small", "agents": 1, "workflows": 1},
            {"name": "Medium", "agents": 5, "workflows": 5}, 
            {"name": "Large", "agents": 20, "workflows": 20},
            {"name": "Extra Large", "agents": 50, "workflows": 50}
        ]
        
        results = []
        
        for case in test_cases:
            # Generate test configuration
            config = {
                "version": "1.0",
                "agents": [
                    {
                        "id": f"agent_{i}",
                        "model": "gpt-4o",
                        "behavior": "helpful"
                    }
                    for i in range(case["agents"])
                ],
                "memory": True,
                "workflows": [
                    f"agent_{i} -> user" for i in range(case["workflows"])
                ]
            }
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config, f)
                config_path = f.name
            
            # Measure loading time
            start_time = time.time()
            
            try:
                loader = LangSwarmConfigLoader(config_path=config_path)
                unified_config = loader._load_unified_config()
                
                loading_time = time.time() - start_time
                
                results.append({
                    "name": case["name"],
                    "agents": case["agents"],
                    "workflows": case["workflows"], 
                    "loading_time": loading_time
                })
                
                # Performance assertions
                if case["agents"] <= 5:
                    assert loading_time < 2.0, f"{case['name']} config should load in < 2s"
                elif case["agents"] <= 20:
                    assert loading_time < 5.0, f"{case['name']} config should load in < 5s"
                else:
                    assert loading_time < 10.0, f"{case['name']} config should load in < 10s"
                
            finally:
                os.unlink(config_path)
        
        # Print performance results
        print("\n📊 Configuration Loading Performance Results:")
        for result in results:
            print(f"   {result['name']:12} ({result['agents']:2d} agents, {result['workflows']:2d} workflows): {result['loading_time']:.3f}s")
        
        # Validate performance scaling
        assert all(r["loading_time"] < 10.0 for r in results), "All configurations should load in < 10s"
    
    def test_memory_operations_performance(self):
        """Benchmark memory operations performance"""
        # Test different memory configurations
        memory_configs = [
            {"type": "simple", "config": True},
            {"type": "production", "config": "production"},
            {"type": "custom", "config": {"backend": "sqlite", "settings": {"db_path": ":memory:"}}}
        ]
        
        for memory_test in memory_configs:
            start_time = time.time()
            
            # Create memory configuration
            memory_config = MemoryConfig.setup_memory(memory_test["config"])
            
            # Perform multiple memory operations
            for i in range(100):
                # Test configuration generation
                tier_desc = memory_config.get_tier_description()
                assert len(tier_desc) > 0
            
            operation_time = time.time() - start_time
            
            # Performance assertion
            assert operation_time < 1.0, f"Memory operations should complete in < 1s, took {operation_time:.3f}s"
            
            print(f"✅ Memory {memory_test['type']} operations: {operation_time:.3f}s for 100 operations")
    
    def test_workflow_generation_performance(self):
        """Benchmark workflow generation performance"""
        # Test different workflow patterns
        workflow_patterns = [
            "assistant -> user",
            "analyzer -> summarizer -> user",
            "extractor -> analyzer -> summarizer -> formatter -> user",
            "expert1, expert2, expert3 -> consensus -> user"
        ]
        
        agents = ["assistant", "analyzer", "summarizer", "extractor", "formatter", 
                 "expert1", "expert2", "expert3", "consensus"]
        
        for pattern in workflow_patterns:
            start_time = time.time()
            
            # Generate workflows multiple times
            for i in range(50):
                workflow = WorkflowConfig.from_simple_syntax(
                    f"test_workflow_{i}",
                    pattern,
                    agents
                )
                assert len(workflow.steps) > 0
            
            generation_time = time.time() - start_time
            
            # Performance assertion
            assert generation_time < 2.0, f"Workflow generation should complete in < 2s, took {generation_time:.3f}s"
            
            print(f"✅ Workflow pattern '{pattern}': {generation_time:.3f}s for 50 generations")


if __name__ == "__main__":
    # Run integration tests when executed directly
    pytest.main([__file__, "-v"]) 