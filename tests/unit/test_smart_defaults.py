"""
Unit tests for smart defaults configuration system.
"""
import pytest
from langswarm.core.config.smart_defaults import SmartDefaults


class TestSmartDefaults:
    """Test smart defaults application."""
    
    def test_minimal_config_expansion(self):
        """Test minimal config gets proper defaults."""
        minimal = {
            "version": "2.0",
            "agents": [{
                "id": "assistant",
                "model": "gpt-3.5-turbo"
            }]
        }
        
        expanded = SmartDefaults.apply_defaults(minimal)
        
        # Check agent defaults applied
        agent = expanded["agents"][0]
        assert agent["provider"] == "openai"
        assert agent["temperature"] == 0.7
        assert "system_prompt" in agent
        assert agent["name"] == "Assistant"
        
        # Check memory defaults added
        assert "memory" in expanded
        assert expanded["memory"]["backend"] == "sqlite"
        assert expanded["memory"]["settings"]["persist_directory"] == "./langswarm_data"
    
    def test_provider_auto_detection(self):
        """Test provider detection from model names."""
        test_cases = [
            ("gpt-3.5-turbo", "openai"),
            ("gpt-4", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("gemini-pro", "google"),
            ("command", "cohere"),
            ("mistral-tiny", "mistral"),
            ("unknown-model", "openai"),  # Default fallback
        ]
        
        for model, expected_provider in test_cases:
            config = {
                "version": "2.0",
                "agents": [{"id": "test", "model": model}]
            }
            
            expanded = SmartDefaults.apply_defaults(config)
            assert expanded["agents"][0]["provider"] == expected_provider
    
    def test_security_defaults_applied(self):
        """Test security defaults are added."""
        minimal = {
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        }
        
        expanded = SmartDefaults.apply_defaults(minimal)
        
        assert "security" in expanded
        security = expanded["security"]
        assert security["api_key_validation"] == True
        assert security["input_sanitization"] == True
        assert security["rate_limiting"]["enabled"] == True
        assert security["rate_limiting"]["requests_per_minute"] == 60
    
    def test_observability_defaults_applied(self):
        """Test observability defaults are added."""
        minimal = {
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        }
        
        expanded = SmartDefaults.apply_defaults(minimal)
        
        assert "observability" in expanded
        obs = expanded["observability"]
        assert obs["logging"]["level"] == "INFO"
        assert obs["logging"]["format"] == "structured"
        assert obs["tracing"]["enabled"] == False
        assert obs["metrics"]["enabled"] == False
    
    def test_tool_shortcuts_expansion(self):
        """Test tool shortcuts are expanded properly."""
        config = {
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}],
            "tools": ["filesystem", "web_search"]
        }
        
        expanded = SmartDefaults.apply_defaults(config)
        
        tools = expanded["tools"]
        assert isinstance(tools, dict)
        assert "filesystem" in tools
        assert "web_search" in tools
        assert tools["filesystem"]["type"] == "mcp"
        assert tools["filesystem"]["local_mode"] == True
    
    def test_workflow_string_parsing(self):
        """Test workflow string shortcuts are parsed."""
        config = {
            "version": "2.0",
            "agents": [{"id": "agent1", "model": "gpt-3.5-turbo"}],
            "workflows": ["agent1 -> user"]
        }
        
        expanded = SmartDefaults.apply_defaults(config)
        
        workflows = expanded["workflows"]
        assert len(workflows) == 1
        workflow = workflows[0]
        assert isinstance(workflow, dict)
        assert "id" in workflow
        assert "steps" in workflow
        assert workflow["description"] == "Auto-generated from: agent1 -> user"
    
    def test_existing_config_preserved(self):
        """Test existing configuration values are preserved."""
        config = {
            "version": "2.0",
            "agents": [{
                "id": "assistant",
                "model": "gpt-4",
                "temperature": 0.8,
                "system_prompt": "Custom prompt"
            }],
            "memory": {
                "backend": "redis",
                "settings": {"host": "custom-host"}
            }
        }
        
        expanded = SmartDefaults.apply_defaults(config)
        
        agent = expanded["agents"][0]
        assert agent["temperature"] == 0.8  # Preserved
        assert agent["system_prompt"] == "Custom prompt"  # Preserved
        assert expanded["memory"]["backend"] == "redis"  # Preserved
        assert expanded["memory"]["settings"]["host"] == "custom-host"  # Preserved
    
    def test_minimal_validation(self):
        """Test minimal configuration validation."""
        # Valid minimal config
        valid_config = {
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        }
        errors = SmartDefaults.validate_minimal_config(valid_config)
        assert len(errors) == 0
        
        # Missing version
        invalid_config = {
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        }
        errors = SmartDefaults.validate_minimal_config(invalid_config)
        assert any("version" in error for error in errors)
        
        # Missing agents
        invalid_config = {
            "version": "2.0",
            "agents": []
        }
        errors = SmartDefaults.validate_minimal_config(invalid_config)
        assert any("agent" in error for error in errors)
        
        # Agent missing model
        invalid_config = {
            "version": "2.0",
            "agents": [{"id": "test"}]
        }
        errors = SmartDefaults.validate_minimal_config(invalid_config)
        assert any("model" in error or "provider" in error for error in errors)
    
    def test_provider_specific_defaults(self):
        """Test provider-specific defaults are applied correctly."""
        # OpenAI
        config = {"version": "2.0", "agents": [{"id": "test", "model": "gpt-4"}]}
        expanded = SmartDefaults.apply_defaults(config)
        agent = expanded["agents"][0]
        assert agent["provider"] == "openai"
        assert agent["top_p"] == 1.0
        assert agent["frequency_penalty"] == 0.0
        
        # Anthropic
        config = {"version": "2.0", "agents": [{"id": "test", "model": "claude-3-sonnet"}]}
        expanded = SmartDefaults.apply_defaults(config)
        agent = expanded["agents"][0]
        assert agent["provider"] == "anthropic"
        assert "Claude" in agent["system_prompt"]
        
        # Google
        config = {"version": "2.0", "agents": [{"id": "test", "model": "gemini-pro"}]}
        expanded = SmartDefaults.apply_defaults(config)
        agent = expanded["agents"][0]
        assert agent["provider"] == "google"
        assert agent["top_p"] == 0.95
        assert agent["top_k"] == 40
    
    def test_memory_backend_defaults(self):
        """Test memory backend specific defaults."""
        # SQLite defaults
        config = {"version": "2.0", "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]}
        expanded = SmartDefaults.apply_defaults(config)
        memory = expanded["memory"]
        assert memory["backend"] == "sqlite"
        assert memory["settings"]["persist_directory"] == "./langswarm_data"
        assert memory["settings"]["enable_embeddings"] == False
        
        # Redis defaults when specified
        config = {
            "version": "2.0", 
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}],
            "memory": {"backend": "redis"}
        }
        expanded = SmartDefaults.apply_defaults(config)
        memory = expanded["memory"]
        assert memory["backend"] == "redis"
        assert memory["settings"]["host"] == "localhost"
        assert memory["settings"]["port"] == 6379