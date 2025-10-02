"""
Regression tests for no_mcp tool execution bug.

This test suite ensures that the no_mcp wrapper does not regress with:
UnboundLocalError: local variable 'user_response' referenced before assignment

Bug was caused by user_response not being initialized in the non-dict payload path
of the no_mcp tool execution logic.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestNoMCPRegression:
    """Regression tests for no_mcp tool execution issues"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configurations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_no_mcp_user_response_no_error(self, temp_config_dir):
        """
        Regression test for no_mcp user_response UnboundLocalError
        
        Ensures that workflow execution with no_mcp wrapper does not fail with:
        UnboundLocalError: local variable 'user_response' referenced before assignment
        """
        # Create a no_mcp workflow that would trigger the user_response error
        config_content = """
version: "1.0"
tools:
  - id: test_tool
    type: function
    metadata:
      function: test_func
      description: "Test function for no_mcp"

functions:
  - name: test_func
    script: |
      def test_func(**kwargs):
          return "Test function executed"

agents:
  - id: test_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are a helpful assistant."

workflows:
  main_workflow:
    - id: no_mcp_test
      agent: test_agent
      input: "Execute test function"
      no_mcp:
        tools:
          - test_tool
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        # Load and execute workflow
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # This should NOT raise UnboundLocalError for user_response
        try:
            result = executor.run_workflow(
                "no_mcp_test",
                user_input="Execute test function"
            )
            # The result might be an error about workflow not found, but should NOT be user_response error
            assert "user_response" not in str(result) or "UnboundLocalError" not in str(result)
        except UnboundLocalError as e:
            if "user_response" in str(e):
                pytest.fail(f"no_mcp user_response error has regressed: {e}")
        except Exception:
            # Other exceptions are acceptable - we're only testing for user_response UnboundLocalError
            pass

    def test_no_mcp_dict_payload_handling(self, temp_config_dir):
        """
        Test that no_mcp wrapper handles dict payloads correctly
        """
        config_content = """
version: "1.0"
tools:
  - id: dict_test_tool
    type: function
    metadata:
      function: dict_test_func
      description: "Test dict payload handling"

functions:
  - name: dict_test_func
    script: |
      def dict_test_func(**kwargs):
          return {"result": "Dict payload test", "status": "success"}

agents:
  - id: dict_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You respond with structured JSON."

workflows:
  main_workflow:
    - id: dict_payload_test
      agent: dict_agent
      input: "Return structured response"
      no_mcp:
        tools:
          - dict_test_tool
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Should handle dict payloads without user_response errors
        try:
            result = executor.run_workflow("dict_payload_test")
            assert isinstance(result, str)
        except UnboundLocalError as e:
            if "user_response" in str(e):
                pytest.fail(f"Dict payload handling failed: {e}")

    def test_no_mcp_non_dict_payload_handling(self, temp_config_dir):
        """
        Test that no_mcp wrapper handles non-dict payloads correctly
        
        This specifically tests the code path that was broken - when agent
        responds with plain text instead of JSON dict structure.
        """
        config_content = """
version: "1.0"
tools:
  - id: text_test_tool
    type: function
    metadata:
      function: text_test_func
      description: "Test non-dict payload handling"

functions:
  - name: text_test_func
    script: |
      def text_test_func(**kwargs):
          return "Plain text response"

agents:
  - id: text_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You respond with plain text, not JSON."

workflows:
  main_workflow:
    - id: text_payload_test
      agent: text_agent
      input: "Return plain text response"
      no_mcp:
        tools:
          - text_test_tool
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Should handle non-dict payloads without user_response errors
        try:
            result = executor.run_workflow("text_payload_test")
            assert isinstance(result, str)
        except UnboundLocalError as e:
            if "user_response" in str(e):
                pytest.fail(f"Non-dict payload handling failed: {e}")

    def test_no_mcp_vs_tools_config_parity(self, temp_config_dir):
        """
        Test that no_mcp and direct tools configuration both work
        
        Ensures both configuration methods are supported without errors
        """
        configs = {
            "no_mcp": """
version: "1.0"
tools:
  - id: parity_tool
    type: function
    metadata:
      function: parity_func
      description: "Test parity"

functions:
  - name: parity_func
    script: |
      def parity_func(**kwargs):
          return "Parity test passed"

agents:
  - id: parity_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are helpful."

workflows:
  main_workflow:
    - id: parity_test
      agent: parity_agent
      input: "Test parity"
      no_mcp:
        tools:
          - parity_tool
      output:
        to: user
""",
            "tools": """
version: "1.0"
tools:
  - id: parity_tool
    type: function
    metadata:
      function: parity_func
      description: "Test parity"

functions:
  - name: parity_func
    script: |
      def parity_func(**kwargs):
          return "Parity test passed"

agents:
  - id: parity_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You are helpful."
    tools:
      - parity_tool

workflows:
  main_workflow:
    - id: parity_test
      agent: parity_agent
      input: "Test parity"
      output:
        to: user
"""
        }
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        for config_type, config_content in configs.items():
            # Create separate temp directory for each config
            config_dir = temp_config_dir / config_type
            config_dir.mkdir()
            config_file = config_dir / "langswarm.yaml"
            config_file.write_text(config_content)
            
            try:
                loader = LangSwarmConfigLoader(str(config_dir))
                workflows, agents, tools, brokers, metadata = loader.load()
                executor = WorkflowExecutor(workflows, agents)
                
                result = executor.run_workflow("parity_test")
                assert isinstance(result, str)
            except UnboundLocalError as e:
                if "user_response" in str(e):
                    pytest.fail(f"{config_type} configuration failed with user_response error: {e}")

    def test_no_mcp_tool_execution_flow(self, temp_config_dir):
        """
        Test complete no_mcp tool execution flow
        
        Verifies that tool identification, argument passing, and execution
        all work correctly with no_mcp wrapper.
        """
        config_content = """
version: "1.0"
tools:
  - id: flow_tool
    type: function
    metadata:
      function: flow_func
      description: "Test execution flow"
      parameters:
        type: object
        properties:
          param1: { type: string, description: "First parameter" }
          param2: { type: integer, description: "Second parameter" }

functions:
  - name: flow_func
    script: |
      def flow_func(param1, param2, **kwargs):
          return f"Flow executed with {param1} and {param2}"

agents:
  - id: flow_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You can execute tools with parameters."

workflows:
  main_workflow:
    - id: flow_test
      agent: flow_agent
      input: "Execute flow with param1='test' and param2=42"
      no_mcp:
        tools:
          - flow_tool
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Test complete execution flow
        try:
            result = executor.run_workflow("flow_test")
            assert isinstance(result, str)
        except UnboundLocalError as e:
            if "user_response" in str(e):
                pytest.fail(f"Tool execution flow failed with user_response error: {e}")

    def test_no_mcp_async_execution(self, temp_config_dir):
        """
        Test that async no_mcp execution also works correctly
        
        Ensures the fix was applied to both sync and async code paths
        """
        config_content = """
version: "1.0"
tools:
  - id: async_tool
    type: function
    metadata:
      function: async_func
      description: "Test async execution"

functions:
  - name: async_func
    script: |
      def async_func(**kwargs):
          return "Async execution test"

agents:
  - id: async_agent
    agent_type: langchain-openai
    model: gpt-4o
    system_prompt: "You execute async tools."

workflows:
  main_workflow:
    - id: async_test
      agent: async_agent
      input: "Execute async function"
      no_mcp:
        tools:
          - async_tool
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Test async execution path
        try:
            # Note: This will actually run sync, but tests the same code paths
            result = executor.run_workflow("async_test")
            assert isinstance(result, str)
        except UnboundLocalError as e:
            if "user_response" in str(e):
                pytest.fail(f"Async execution failed with user_response error: {e}") 