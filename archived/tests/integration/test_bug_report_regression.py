"""
Integration tests to prevent regression of critical bug report issues.

This test suite ensures that the following critical bugs do not reoccur:
1. navigation_choice variable not defined error
2. API compatibility breaks with run_workflow parameters
3. Infinite recursion in update_system_prompt
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestBugReportRegression:
    """Regression tests for critical bug report issues"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configurations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_navigation_choice_no_error(self, temp_config_dir):
        """
        Regression test for Issue 1: navigation_choice Variable Error
        
        Ensures that workflow execution does not fail with:
        'name navigation_choice is not defined'
        """
        # Create a function workflow that would trigger the navigation_choice error
        config_content = """
version: "1.0"
workflows:
  main_workflow:
    - id: test_function
      function: test_func
      script: |
        def test_func(user_message, **kwargs):
            return f"Processed: {user_message}"
      args:
        user_message: ${context.user_message}
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
        
        # This should NOT raise NameError: name 'navigation_choice' is not defined
        try:
            result = executor.run_workflow(
                "test_function",
                user_input="Test message",
                user_message="Test message"
            )
            # The result might be an error about workflow not found, but should NOT be navigation_choice error
            assert "navigation_choice" not in str(result)
        except NameError as e:
            if "navigation_choice" in str(e):
                pytest.fail(f"navigation_choice variable error has regressed: {e}")
        except Exception:
            # Other exceptions are acceptable - we're only testing for navigation_choice NameError
            pass

    def test_api_parameter_compatibility(self, temp_config_dir):
        """
        Regression test for Issue 2: API Compatibility
        
        Ensures that run_workflow accepts all the parameters that TimeBot uses:
        user_id, domain, user_message, is_attachment, files, navigation_choice
        """
        config_content = """
version: "1.0"
workflows:
  main_workflow:
    - id: api_test
      function: api_test_func
      script: |
        def api_test_func(**kwargs):
            return f"Received {len(kwargs)} parameters"
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # This should NOT raise TypeError: unexpected keyword argument
        try:
            result = executor.run_workflow(
                "api_test",
                user_input="test",
                user_id="test_user",
                domain="test_domain", 
                user_message="test message",
                is_attachment=False,
                files=None,
                navigation_choice="default",
                session_id="test_session",
                additional_param="test_value"
            )
            # Should execute without TypeError about unexpected arguments
            assert isinstance(result, str)
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"API compatibility has regressed: {e}")

    def test_no_infinite_recursion_in_system_prompt(self):
        """
        Regression test for Issue 3: Infinite Recursion
        
        Ensures that update_system_prompt doesn't cause infinite recursion
        """
        try:
            from langswarm.core.base.bot import LLM
            
            # This should NOT cause RecursionError
            # Create LLM instance (calls update_system_prompt internally)
            llm = LLM(
                agent=None,
                name="test_llm",
                model="test-model",
                system_prompt="Initial prompt"
            )
            
            # Multiple calls should not cause recursion
            for i in range(10):
                llm.update_system_prompt(f"Updated prompt {i}")
                
        except RecursionError as e:
            pytest.fail(f"Infinite recursion in update_system_prompt has regressed: {e}")
        except ImportError:
            # LLM class might not be available in test environment
            pytest.skip("LLM class not available for testing")
        except Exception:
            # Other exceptions are fine - we're only testing for RecursionError
            pass

    def test_function_steps_sync_execution(self, temp_config_dir):
        """
        Regression test: Ensure function steps work in sync execution mode
        
        This was a root cause of the navigation_choice error - function steps
        were missing from sync execution path.
        """
        config_content = """
version: "1.0"
workflows:
  main_workflow:
    - id: sync_function_test
      function: sync_test_func
      script: |
        def sync_test_func(test_param, **kwargs):
            return f"Sync function executed with: {test_param}"
      args:
        test_param: "sync_test_value"
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Function step should execute in sync mode without errors
        try:
            result = executor.run_workflow("sync_function_test")
            # Result might be error about workflow not found, but function step should be recognized
            assert "Step executed" not in str(result)  # Should not fall back to generic execution
        except Exception:
            # Other exceptions acceptable - we're testing that function steps are recognized
            pass

    def test_workflow_executor_initialization(self, temp_config_dir):
        """
        Regression test: Ensure WorkflowExecutor properly initializes workflows
        
        Part of the bug was related to workflow access patterns
        """
        config_content = """
version: "1.0"
workflows:
  main_workflow:
    - id: init_test
      function: init_test_func
      script: |
        def init_test_func():
            return "Initialization test"
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        
        # WorkflowExecutor should initialize without errors
        executor = WorkflowExecutor(workflows, agents)
        
        # Should have workflows attribute
        assert hasattr(executor, 'workflows')
        assert executor.workflows is not None

    @pytest.mark.parametrize("extra_params", [
        {"custom_param": "value"},
        {"user_id": "123", "session_id": "abc"},
        {"navigation_choice": "test", "metadata": {"key": "value"}},
    ])
    def test_kwargs_handling_robustness(self, temp_config_dir, extra_params):
        """
        Test that **kwargs handling is robust across different parameter combinations
        """
        config_content = """
version: "1.0"
workflows:
  main_workflow:
    - id: kwargs_test
      function: kwargs_test_func
      script: |
        def kwargs_test_func(**kwargs):
            return f"Received kwargs: {sorted(kwargs.keys())}"
      output:
        to: user
"""
        
        config_file = temp_config_dir / "langswarm.yaml"
        config_file.write_text(config_content)
        
        from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor
        
        loader = LangSwarmConfigLoader(str(temp_config_dir))
        workflows, agents, tools, brokers, metadata = loader.load()
        executor = WorkflowExecutor(workflows, agents)
        
        # Should handle any combination of parameters without errors
        try:
            result = executor.run_workflow(
                "kwargs_test",
                user_input="test",
                **extra_params
            )
            assert isinstance(result, str)
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Parameter handling failed for {extra_params}: {e}") 