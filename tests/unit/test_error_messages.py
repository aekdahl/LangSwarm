"""
Unit tests for enhanced error messages system.

Tests the error helper system that provides context-aware error messages
to help users resolve configuration and setup issues.
"""
import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from langswarm.core.config.error_helpers import (
    ConfigErrorHelper,
    ConfigurationError,
    get_helpful_suggestions
)


class TestConfigErrorHelper:
    """Test the configuration error helper system."""
    
    def test_file_not_found_error(self):
        """Test file not found error with suggestions."""
        search_paths = ["/home/user", "/etc/langswarm", "./config"]
        error = ConfigErrorHelper.file_not_found("config.yaml", search_paths)
        
        assert isinstance(error, ConfigurationError)
        assert "config.yaml" in str(error)
        assert "not found" in str(error)
        assert all(path in str(error) for path in search_paths)
    
    def test_missing_api_key_openai(self):
        """Test missing OpenAI API key error."""
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        
        assert isinstance(error, ConfigurationError)
        assert "OPENAI_API_KEY" in str(error)
        assert "export" in str(error) or "set" in str(error)
        assert "https://platform.openai.com" in str(error)
    
    def test_missing_api_key_anthropic(self):
        """Test missing Anthropic API key error."""
        error = ConfigErrorHelper.missing_api_key("anthropic", "ANTHROPIC_API_KEY")
        
        assert isinstance(error, ConfigurationError)
        assert "ANTHROPIC_API_KEY" in str(error)
        assert "https://console.anthropic.com" in str(error)
    
    def test_missing_api_key_google(self):
        """Test missing Google API key error."""
        error = ConfigErrorHelper.missing_api_key("google", "GOOGLE_API_KEY")
        
        assert isinstance(error, ConfigurationError)
        assert "GOOGLE_API_KEY" in str(error)
        assert "Google AI Studio" in str(error) or "google" in str(error).lower()
    
    def test_invalid_yaml_syntax(self):
        """Test invalid YAML syntax error."""
        yaml_content = "invalid: yaml: content: ["
        line_number = 1
        
        error = ConfigErrorHelper.invalid_yaml_syntax(yaml_content, line_number)
        
        assert isinstance(error, ConfigurationError)
        assert "YAML syntax" in str(error)
        assert "line 1" in str(error)
        assert "invalid: yaml: content: [" in str(error)
    
    def test_missing_required_field(self):
        """Test missing required field error."""
        error = ConfigErrorHelper.missing_required_field("model", "agents[0]")
        
        assert isinstance(error, ConfigurationError)
        assert "model" in str(error)
        assert "agents[0]" in str(error)
        assert "required" in str(error)
    
    def test_invalid_provider(self):
        """Test invalid provider error with suggestions."""
        error = ConfigErrorHelper.invalid_provider("invalid_provider")
        
        assert isinstance(error, ConfigurationError)
        assert "invalid_provider" in str(error)
        assert "openai" in str(error)  # Should suggest valid providers
        assert "anthropic" in str(error)
    
    def test_dependency_missing(self):
        """Test missing dependency error."""
        error = ConfigErrorHelper.dependency_missing("redis", "memory backend")
        
        assert isinstance(error, ConfigurationError)
        assert "redis" in str(error)
        assert "memory backend" in str(error)
        assert "pip install" in str(error)
    
    def test_configuration_conflict(self):
        """Test configuration conflict error."""
        error = ConfigErrorHelper.configuration_conflict(
            "memory.backend", 
            "redis", 
            "memory.enabled", 
            False
        )
        
        assert isinstance(error, ConfigurationError)
        assert "memory.backend" in str(error)
        assert "memory.enabled" in str(error)
        assert "conflict" in str(error).lower()


class TestGetHelpfulSuggestions:
    """Test the suggestion system for various error scenarios."""
    
    def test_api_key_suggestions(self):
        """Test API key setup suggestions."""
        suggestions = get_helpful_suggestions("missing_api_key", provider="openai")
        
        assert len(suggestions) > 0
        assert any("export OPENAI_API_KEY" in s for s in suggestions)
        assert any("platform.openai.com" in s for s in suggestions)
    
    def test_file_suggestions(self):
        """Test file location suggestions."""
        suggestions = get_helpful_suggestions("file_not_found", file_type="config")
        
        assert len(suggestions) > 0
        assert any("langswarm.yaml" in s for s in suggestions)
        assert any("current directory" in s for s in suggestions)
    
    def test_dependency_suggestions(self):
        """Test dependency installation suggestions."""
        suggestions = get_helpful_suggestions("missing_dependency", package="redis")
        
        assert len(suggestions) > 0
        assert any("pip install redis" in s for s in suggestions)
        assert any("optional" in s.lower() for s in suggestions)
    
    def test_provider_suggestions(self):
        """Test provider configuration suggestions."""
        suggestions = get_helpful_suggestions("invalid_provider")
        
        assert len(suggestions) > 0
        assert any("openai" in s for s in suggestions)
        assert any("anthropic" in s for s in suggestions)
        assert any("google" in s for s in suggestions)


class TestErrorMessageContext:
    """Test that error messages include helpful context."""
    
    def test_error_includes_current_directory(self):
        """Test that file errors include current directory info."""
        error = ConfigErrorHelper.file_not_found("config.yaml", ["."])
        
        error_str = str(error)
        assert "current directory" in error_str.lower() or "." in error_str
    
    def test_error_includes_environment_info(self):
        """Test that API key errors include environment setup info."""
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        
        error_str = str(error)
        assert "environment" in error_str.lower() or "export" in error_str
    
    def test_error_includes_documentation_links(self):
        """Test that errors include links to documentation."""
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        
        error_str = str(error)
        assert "http" in error_str  # Should contain documentation URL
    
    def test_error_includes_fix_examples(self):
        """Test that errors include concrete fix examples."""
        error = ConfigErrorHelper.missing_required_field("model", "agents[0]")
        
        error_str = str(error)
        assert "example" in error_str.lower() or "gpt-3.5-turbo" in error_str


class TestConfigurationValidation:
    """Test configuration validation with helpful errors."""
    
    def test_empty_config_error(self):
        """Test helpful error for completely empty config."""
        # This would be called by the config validator
        error = ConfigErrorHelper.missing_required_field("version", "root")
        
        assert "version" in str(error)
        assert "required" in str(error)
    
    def test_agent_without_model_error(self):
        """Test error when agent is missing model."""
        error = ConfigErrorHelper.missing_required_field("model", "agents[0]")
        
        assert "model" in str(error)
        assert "agents[0]" in str(error)
    
    def test_invalid_model_format_error(self):
        """Test error for invalid model format."""
        error = ConfigErrorHelper.invalid_value(
            "model", 
            "invalid-model-123", 
            "Should be a valid model name like 'gpt-3.5-turbo' or 'claude-3-sonnet'"
        )
        
        assert "invalid-model-123" in str(error)
        assert "gpt-3.5-turbo" in str(error)
        assert "claude-3-sonnet" in str(error)


class TestErrorFormattingAndDisplay:
    """Test error message formatting and display."""
    
    def test_error_has_proper_formatting(self):
        """Test that errors are properly formatted."""
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        
        error_str = str(error)
        # Should have clear structure
        assert "\n" in error_str  # Multi-line for readability
        assert len(error_str) > 50  # Detailed enough to be helpful
        assert len(error_str) < 1000  # Not overwhelming
    
    def test_error_includes_action_items(self):
        """Test that errors include clear action items."""
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        
        error_str = str(error)
        # Should include actionable steps
        assert any(word in error_str.lower() for word in ["1.", "2.", "step", "first", "then"])
    
    def test_error_includes_solution_priority(self):
        """Test that errors prioritize most likely solutions."""
        error = ConfigErrorHelper.file_not_found("config.yaml", [".", "/etc", "/home"])
        
        error_str = str(error)
        # Current directory should be mentioned first as most likely solution
        lines = error_str.split('\n')
        current_dir_line = next((i for i, line in enumerate(lines) if '.' in line), None)
        other_dir_line = next((i for i, line in enumerate(lines) if '/etc' in line), None)
        
        if current_dir_line is not None and other_dir_line is not None:
            assert current_dir_line < other_dir_line


class TestErrorCategories:
    """Test different categories of errors."""
    
    def test_configuration_errors(self):
        """Test configuration-related errors."""
        categories = [
            ConfigErrorHelper.missing_required_field("model", "agents[0]"),
            ConfigErrorHelper.invalid_yaml_syntax("bad: yaml: [", 1),
            ConfigErrorHelper.configuration_conflict("a", "1", "b", "2")
        ]
        
        for error in categories:
            assert isinstance(error, ConfigurationError)
            assert len(str(error)) > 20  # Reasonably detailed
    
    def test_setup_errors(self):
        """Test setup-related errors."""
        categories = [
            ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY"),
            ConfigErrorHelper.dependency_missing("redis", "memory"),
            ConfigErrorHelper.file_not_found("config.yaml", ["."])
        ]
        
        for error in categories:
            assert isinstance(error, ConfigurationError)
            assert "http" in str(error).lower() or "install" in str(error).lower()
    
    def test_validation_errors(self):
        """Test validation-related errors."""
        categories = [
            ConfigErrorHelper.invalid_provider("bad_provider"),
            ConfigErrorHelper.invalid_value("temperature", "invalid", "Should be 0.0-2.0")
        ]
        
        for error in categories:
            assert isinstance(error, ConfigurationError)
            assert "invalid" in str(error).lower() or "should" in str(error).lower()


class TestErrorContextualHelp:
    """Test contextual help based on user environment."""
    
    @patch('platform.system')
    def test_platform_specific_instructions(self, mock_system):
        """Test that instructions are platform-specific."""
        # Test Windows
        mock_system.return_value = "Windows"
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        assert "set OPENAI_API_KEY" in str(error) or "setx" in str(error)
        
        # Test Unix/Linux/Mac
        mock_system.return_value = "Linux"
        error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        assert "export OPENAI_API_KEY" in str(error)
    
    @patch('os.path.exists')
    def test_file_existence_checking(self, mock_exists):
        """Test that error messages check for common file locations."""
        mock_exists.return_value = False
        
        error = ConfigErrorHelper.file_not_found("config.yaml", ["."])
        
        # Should mention checking common locations
        error_str = str(error)
        assert "check" in error_str.lower() or "look" in error_str.lower()
    
    def test_development_vs_production_context(self):
        """Test different help for development vs production."""
        # Development context (missing API key)
        dev_error = ConfigErrorHelper.missing_api_key("openai", "OPENAI_API_KEY")
        assert "development" in str(dev_error).lower() or "testing" in str(dev_error).lower()
        
        # Production context (configuration conflict)
        prod_error = ConfigErrorHelper.configuration_conflict("a", "1", "b", "2")
        assert len(str(prod_error)) > 50  # Should be detailed for production issues