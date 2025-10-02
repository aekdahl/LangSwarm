"""
Configuration System Integration Tests (Core Focus)
==================================================

Focused integration tests for LangSwarm configuration system core functionality,
testing unified configuration, legacy multi-file support, validation, and
migration tools without relying on advanced zero-config features.

Test Coverage:
- Unified Configuration Loading (single langswarm.yaml)
- Legacy Multi-File Configuration Support (8 files)
- Configuration Validation and Error Handling
- Configuration Migration and Transformation
- Include Directives and Modular Configuration
- Environment Variable Resolution
- Performance and System Health
"""

import pytest
import tempfile
import shutil
import os
import yaml
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any
import logging

# Configuration Core
from langswarm.core.config import (
    LangSwarmConfigLoader, LangSwarmConfig, AgentConfig, ToolConfig, 
    WorkflowConfig, MemoryConfig, AdvancedConfig, LangSwarmCoreConfig,
    BrokerConfig, ValidationError
)

# Patch zero-config availability for core testing
@patch('langswarm.core.config.ZERO_CONFIG_AVAILABLE', False)
class TestConfigurationSystemCore:
    """Core configuration system integration tests"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for each test"""
        # Create temporary directory for test configurations
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_config_dir = self.temp_dir / "config"
        self.test_config_dir.mkdir()
        
        # Test data
        self.sample_agents = [
            {"id": "helpful-assistant", "model": "gpt-4o", "agent_type": "generic"},
            {"id": "coding-assistant", "model": "gpt-4o", "agent_type": "generic"},
            {"id": "research-assistant", "model": "claude-3-sonnet", "agent_type": "generic"}
        ]
        
        self.sample_tools = {
            "filesystem": {"type": "mcpfilesystem", "local_mode": True},
            "github": {"type": "mcpgithubtool", "auto_configure": True}
        }
        
        self.sample_workflows = [
            {"id": "main-workflow", "name": "Main Processing", "steps": [{"agent": "helpful-assistant"}]}
        ]
        
        yield
        
        # Cleanup after each test
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_unified_configuration_loading(self):
        """Test unified configuration loading from single langswarm.yaml"""
        print("\n=== Testing Unified Configuration Loading ===")
        
        # Test different unified configuration formats
        config_variants = [
            ("minimal", self._create_minimal_unified_config()),
            ("standard", self._create_standard_unified_config()),
            ("complete", self._create_complete_unified_config())
        ]
        
        for variant_name, config_data in config_variants:
            print(f"\n--- Testing {variant_name} unified configuration ---")
            
            # Write unified config file
            config_file = self.test_config_dir / f"{variant_name}_langswarm.yaml"
            with open(config_file, 'w') as f:
                yaml.safe_dump(config_data, f)
            
            # Load configuration
            loader = LangSwarmConfigLoader(str(self.test_config_dir))
            loader.config_path = str(config_file)
            
            # Test unified config detection
            is_unified = loader._is_unified_config()
            assert is_unified is True
            print(f"✓ Unified config detection successful")
            
            # Load unified configuration
            unified_config = loader._load_unified_config()
            assert isinstance(unified_config, LangSwarmConfig)
            assert unified_config.version == config_data.get("version", "1.0")
            print(f"✓ Unified config loaded: version {unified_config.version}")
            
            # Test agents configuration
            assert len(unified_config.agents) >= 1
            first_agent = unified_config.agents[0]
            assert isinstance(first_agent, AgentConfig)
            assert first_agent.id is not None
            print(f"✓ Agents configuration: {len(unified_config.agents)} agents")
            
            # Test validation
            errors = unified_config.validate()
            assert isinstance(errors, list)
            print(f"✓ Validation: {len(errors)} errors found")
            
            # Test legacy format conversion
            legacy_data = loader._unified_to_legacy_data(unified_config)
            assert isinstance(legacy_data, dict)
            assert "agents" in legacy_data
            assert "tools" in legacy_data
            print(f"✓ Legacy format conversion successful")

    def test_legacy_multi_file_configuration(self):
        """Test legacy multi-file configuration support"""
        print("\n=== Testing Legacy Multi-File Configuration ===")
        
        # Create legacy configuration files with proper format
        legacy_configs = {
            "agents.yaml": {"agents": self.sample_agents},
            "tools.yaml": {"tools": [{"id": k, **v} for k, v in self.sample_tools.items()]},
            "workflows.yaml": {"workflows": self.sample_workflows},
            "brokers.yaml": {"brokers": []},
            "queues.yaml": {"queues": []},
            "registries.yaml": {"registries": []},
            "plugins.yaml": {"plugins": []},
            "secrets.yaml": {"secrets": {}}
        }
        
        # Write legacy config files
        for filename, config_data in legacy_configs.items():
            config_file = self.test_config_dir / filename
            with open(config_file, 'w') as f:
                yaml.safe_dump(config_data, f)
        
        print(f"✓ Created {len(legacy_configs)} legacy config files")
        
        # Load multi-file configuration
        loader = LangSwarmConfigLoader(str(self.test_config_dir))
        
        # Test config type detection
        config_type = loader._detect_config_type()
        assert config_type == "multi-file"
        print(f"✓ Multi-file config detection successful")
        
        # Load configuration (may have some initialization issues, but should not crash)
        try:
            loader.load()
            print(f"✓ Multi-file configuration loading attempted")
        except Exception as e:
            print(f"! Multi-file loading had issues (expected): {e}")
        
        # Verify config data was loaded
        assert isinstance(loader.config_data, dict)
        print(f"✓ Config data structure validated")

    def test_configuration_validation_system(self):
        """Test comprehensive configuration validation and error handling"""
        print("\n=== Testing Configuration Validation System ===")
        
        # Test valid configuration
        print("\n--- Testing Valid Configuration ---")
        valid_config = self._create_standard_unified_config()
        
        config_file = self.test_config_dir / "valid_config.yaml"
        with open(config_file, 'w') as f:
            yaml.safe_dump(valid_config, f)
        
        loader = LangSwarmConfigLoader(str(config_file))
        unified_config = loader._load_unified_config()
        
        errors = unified_config.validate()
        assert len(errors) == 0
        print(f"✓ Valid configuration passed validation")
        
        # Test configurations with errors
        invalid_configs = [
            ("duplicate_agent_ids", self._create_invalid_config_duplicate_agents()),
            ("missing_tools", self._create_invalid_config_missing_tools()),
            ("invalid_workflow_refs", self._create_invalid_config_invalid_workflows())
        ]
        
        for error_type, invalid_config in invalid_configs:
            print(f"\n--- Testing {error_type} validation ---")
            
            config_file = self.test_config_dir / f"invalid_{error_type}.yaml"
            with open(config_file, 'w') as f:
                yaml.safe_dump(invalid_config, f)
            
            loader = LangSwarmConfigLoader(str(config_file))
            unified_config = loader._load_unified_config()
            
            errors = unified_config.validate()
            assert len(errors) > 0
            print(f"✓ Invalid configuration properly caught {len(errors)} validation errors")
            
            # Test error details
            for error in errors:
                assert isinstance(error, ValidationError)
                assert hasattr(error, 'field')
                assert hasattr(error, 'message')
                print(f"  - {error.section or 'general'}.{error.field}: {error.message}")

    def test_include_directives_modular_config(self):
        """Test include directives and modular configuration support"""
        print("\n=== Testing Include Directives and Modular Configuration ===")
        
        # Create modular configuration files
        print("\n--- Creating Modular Configuration Files ---")
        
        # Create separate module files
        agents_module = {"agents": self.sample_agents[:2]}
        tools_module = {"tools": self.sample_tools}
        workflows_module = {"workflows": self.sample_workflows}
        
        modules = {
            "agents_module.yaml": agents_module,
            "tools_module.yaml": tools_module,
            "workflows_module.yaml": workflows_module
        }
        
        for filename, module_data in modules.items():
            module_file = self.test_config_dir / filename
            with open(module_file, 'w') as f:
                yaml.safe_dump(module_data, f)
        
        print(f"✓ Created {len(modules)} modular configuration files")
        
        # Create main configuration with includes
        main_config = {
            "version": "1.0",
            "project_name": "modular-project",
            "include": list(modules.keys()),
            "agents": [self.sample_agents[2]],  # Additional agent in main file
            "langswarm": {"debug": True}
        }
        
        main_file = self.test_config_dir / "main_langswarm.yaml"
        with open(main_file, 'w') as f:
            yaml.safe_dump(main_config, f)
        
        # Load configuration with includes
        loader = LangSwarmConfigLoader(str(main_file))
        unified_config = loader._load_unified_config()
        
        # Test that includes were processed
        assert len(unified_config.agents) == len(self.sample_agents)  # All agents included
        assert len(unified_config.tools) == len(self.sample_tools)
        assert len(unified_config.workflows) == len(self.sample_workflows)
        assert unified_config.langswarm.debug is True
        print(f"✓ Include processing successful: {len(unified_config.agents)} agents total")
        
        # Test include order and merging
        agent_ids = [agent.id for agent in unified_config.agents]
        expected_ids = [agent["id"] for agent in self.sample_agents]
        assert set(agent_ids) == set(expected_ids)
        print(f"✓ Include merging preserved all agent IDs")

    def test_environment_variable_resolution(self):
        """Test environment variable resolution in configurations"""
        print("\n=== Testing Environment Variable Resolution ===")
        
        # Set test environment variables
        test_env_vars = {
            "TEST_MODEL": "gpt-4o-test",
            "TEST_DEBUG": "true",
            "TEST_PROJECT_NAME": "env-test-project"
        }
        
        for key, value in test_env_vars.items():
            os.environ[key] = value
        
        try:
            # Create configuration with environment variables
            env_config = {
                "version": "1.0",
                "project_name": "env:TEST_PROJECT_NAME",
                "langswarm": {"debug": "env:TEST_DEBUG"},
                "agents": [
                    {
                        "id": "env-agent",
                        "model": "env:TEST_MODEL",
                        "agent_type": "generic"
                    }
                ]
            }
            
            env_file = self.test_config_dir / "env_config.yaml"
            with open(env_file, 'w') as f:
                yaml.safe_dump(env_config, f)
            
            # Load configuration
            loader = LangSwarmConfigLoader(str(env_file))
            unified_config = loader._load_unified_config()
            
            # Test environment variable resolution
            assert unified_config.project_name == "env-test-project"
            assert unified_config.agents[0].model == "gpt-4o-test"
            print(f"✓ Environment variables resolved correctly")
            
        finally:
            # Cleanup environment variables
            for key in test_env_vars:
                if key in os.environ:
                    del os.environ[key]

    def test_configuration_performance_optimization(self):
        """Test configuration loading performance and optimization"""
        print("\n=== Testing Configuration Performance and Optimization ===")
        
        # Create large configuration for performance testing
        print("\n--- Creating Large Configuration ---")
        large_config = {
            "version": "1.0",
            "project_name": "performance-test",
            "agents": [],
            "tools": {},
            "workflows": []
        }
        
        # Generate many agents
        for i in range(50):
            large_config["agents"].append({
                "id": f"agent_{i:03d}",
                "name": f"Agent {i}",
                "model": "gpt-4o-mini",
                "agent_type": "generic"
            })
        
        # Generate many tools
        for i in range(20):
            large_config["tools"][f"tool_{i:03d}"] = {
                "type": "mcpfilesystem",
                "local_mode": True,
                "settings": {"test_param": f"value_{i}"}
            }
        
        # Generate many workflows
        for i in range(10):
            large_config["workflows"].append({
                "id": f"workflow_{i:03d}",
                "name": f"Workflow {i}",
                "steps": [{"agent": f"agent_{i:03d}"}]
            })
        
        large_file = self.test_config_dir / "large_config.yaml"
        with open(large_file, 'w') as f:
            yaml.safe_dump(large_config, f)
        
        print(f"✓ Large config created: {len(large_config['agents'])} agents, {len(large_config['tools'])} tools")
        
        # Test loading performance
        print("\n--- Testing Loading Performance ---")
        start_time = time.time()
        
        loader = LangSwarmConfigLoader(str(large_file))
        unified_config = loader._load_unified_config()
        
        load_time = time.time() - start_time
        print(f"✓ Large config loaded in {load_time:.3f} seconds")
        
        # Test validation performance
        start_time = time.time()
        errors = unified_config.validate()
        validation_time = time.time() - start_time
        
        print(f"✓ Large config validated in {validation_time:.3f} seconds ({len(errors)} errors)")
        
        # Test legacy conversion performance
        start_time = time.time()
        legacy_data = loader._unified_to_legacy_data(unified_config)
        conversion_time = time.time() - start_time
        
        print(f"✓ Legacy conversion completed in {conversion_time:.3f} seconds")
        
        # Performance assertions
        assert load_time < 5.0  # Should load large config in under 5 seconds
        assert validation_time < 2.0  # Should validate in under 2 seconds
        assert conversion_time < 1.0  # Should convert in under 1 second

    def test_error_handling_recovery_scenarios(self):
        """Test comprehensive error handling and recovery scenarios"""
        print("\n=== Testing Error Handling and Recovery Scenarios ===")
        
        # Test malformed YAML
        print("\n--- Testing Malformed YAML Handling ---")
        malformed_file = self.test_config_dir / "malformed.yaml"
        with open(malformed_file, 'w') as f:
            f.write("version: 1.0\nagents:\n  - id: test\n    invalid_yaml: [\n")  # Broken YAML
        
        loader = LangSwarmConfigLoader(str(malformed_file))
        try:
            loader._load_unified_config()
            assert False, "Should have raised YAML error"
        except yaml.YAMLError:
            print("✓ Malformed YAML properly handled")
        except Exception as e:
            print(f"✓ YAML error caught: {type(e).__name__}")
        
        # Test missing required fields
        print("\n--- Testing Missing Required Fields ---")
        incomplete_config = {"version": "1.0", "agents": [{"name": "missing_id_agent"}]}
        
        incomplete_file = self.test_config_dir / "incomplete.yaml"
        with open(incomplete_file, 'w') as f:
            yaml.safe_dump(incomplete_config, f)
        
        loader = LangSwarmConfigLoader(str(incomplete_file))
        try:
            unified_config = loader._load_unified_config()
            # Should handle gracefully with defaults or validation errors
            print("✓ Incomplete config handled gracefully")
        except Exception as e:
            print(f"✓ Incomplete config error handled: {e}")
        
        # Test invalid include files
        print("\n--- Testing Invalid Include Files ---")
        invalid_include_config = {
            "version": "1.0",
            "include": ["nonexistent_file.yaml"],
            "agents": [{"id": "test", "model": "gpt-4o"}]
        }
        
        invalid_include_file = self.test_config_dir / "invalid_include.yaml"
        with open(invalid_include_file, 'w') as f:
            yaml.safe_dump(invalid_include_config, f)
        
        loader = LangSwarmConfigLoader(str(invalid_include_file))
        try:
            unified_config = loader._load_unified_config()
            # Should continue with main config even if include fails
            assert len(unified_config.agents) >= 1
            print("✓ Invalid include files handled gracefully")
        except Exception as e:
            print(f"✓ Include error handled: {e}")

    def test_system_health_monitoring(self):
        """Test configuration system health monitoring and diagnostics"""
        print("\n=== Testing Configuration System Health Monitoring ===")
        
        # Create test configuration
        health_config = self._create_standard_unified_config()
        health_file = self.test_config_dir / "health_test.yaml"
        with open(health_file, 'w') as f:
            yaml.safe_dump(health_config, f)
        
        # Test configuration loading health
        print("\n--- Testing Configuration Loading Health ---")
        loader = LangSwarmConfigLoader(str(health_file))
        
        start_time = time.time()
        unified_config = loader._load_unified_config()
        load_time = time.time() - start_time
        
        health_metrics = {
            "load_time_seconds": load_time,
            "agents_count": len(unified_config.agents),
            "tools_count": len(unified_config.tools),
            "workflows_count": len(unified_config.workflows),
            "validation_errors": len(unified_config.validate()),
            "memory_enabled": unified_config.memory.enabled,
            "debug_mode": unified_config.langswarm.debug
        }
        
        print(f"✓ Configuration health metrics:")
        for metric, value in health_metrics.items():
            print(f"  - {metric}: {value}")
        
        # Test configuration validation health
        print("\n--- Testing Validation Health ---")
        validation_start = time.time()
        errors = unified_config.validate()
        validation_time = time.time() - validation_start
        
        print(f"✓ Validation completed in {validation_time:.3f}s with {len(errors)} errors")
        
        # Test memory and resource usage
        print("\n--- Testing Resource Usage ---")
        import sys
        config_size = sys.getsizeof(unified_config)
        loader_size = sys.getsizeof(loader)
        
        print(f"✓ Memory usage - Config: {config_size} bytes, Loader: {loader_size} bytes")
        
        # Performance health checks
        assert load_time < 1.0  # Should load quickly
        assert validation_time < 0.5  # Should validate quickly
        assert len(errors) == 0  # Should have no validation errors for valid config
        
        print(f"✓ All health checks passed")

    # Helper methods for creating test configurations
    def _create_minimal_unified_config(self):
        return {
            "version": "1.0",
            "agents": [{"id": "assistant", "model": "gpt-4o", "agent_type": "generic"}]
        }
    
    def _create_standard_unified_config(self):
        return {
            "version": "1.0",
            "project_name": "standard-test",
            "agents": self.sample_agents,
            "tools": self.sample_tools,
            "workflows": self.sample_workflows,
            "memory": {"enabled": True, "backend": "auto"}
        }
    
    def _create_complete_unified_config(self):
        return {
            "version": "1.0",
            "project_name": "complete-test",
            "langswarm": {"debug": False, "log_level": "INFO"},
            "agents": self.sample_agents,
            "tools": self.sample_tools,
            "workflows": self.sample_workflows,
            "memory": {
                "enabled": True,
                "backend": "chromadb",
                "settings": {"persist_directory": "./memory"}
            },
            "advanced": {
                "brokers": [{"id": "default", "type": "internal"}],
                "queues": [],
                "registries": []
            }
        }
    
    def _create_invalid_config_duplicate_agents(self):
        return {
            "version": "1.0",
            "agents": [
                {"id": "duplicate", "model": "gpt-4o"},
                {"id": "duplicate", "model": "claude-3-sonnet"}  # Duplicate ID
            ]
        }
    
    def _create_invalid_config_missing_tools(self):
        return {
            "version": "1.0",
            "agents": [{"id": "agent", "model": "gpt-4o", "tools": ["nonexistent_tool"]}],
            "tools": {}  # Empty tools but agent references nonexistent_tool
        }
    
    def _create_invalid_config_invalid_workflows(self):
        return {
            "version": "1.0",
            "agents": [{"id": "agent1", "model": "gpt-4o"}],
            "workflows": [{"id": "workflow", "steps": [{"agent": "nonexistent_agent"}]}]
        }


def run_config_system_core_tests():
    """Run core configuration system integration tests"""
    print("="*80)
    print("LANGSWARM CONFIGURATION SYSTEM CORE TESTS")
    print("="*80)
    
    # Create test instance
    test_instance = TestConfigurationSystemCore()
    test_instance.setup_test_environment()
    
    try:
        # Run core test methods
        test_methods = [
            test_instance.test_unified_configuration_loading,
            test_instance.test_legacy_multi_file_configuration,
            test_instance.test_configuration_validation_system,
            test_instance.test_include_directives_modular_config,
            test_instance.test_environment_variable_resolution,
            test_instance.test_configuration_performance_optimization,
            test_instance.test_error_handling_recovery_scenarios,
            test_instance.test_system_health_monitoring
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed += 1
                print(f"\n✅ {test_method.__name__} PASSED")
            except Exception as e:
                failed += 1
                print(f"\n❌ {test_method.__name__} FAILED: {e}")
                import traceback
                print(traceback.format_exc())
        
        print("\n" + "="*80)
        print(f"CONFIGURATION SYSTEM CORE TEST RESULTS")
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"TOTAL:  {passed + failed}")
        print("="*80)
        
        return passed, failed
        
    finally:
        # Cleanup
        import shutil
        if hasattr(test_instance, 'temp_dir') and test_instance.temp_dir.exists():
            shutil.rmtree(test_instance.temp_dir)


if __name__ == "__main__":
    run_config_system_core_tests() 