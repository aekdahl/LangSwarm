"""
LangSwarm Configuration Error Helpers

Provides enhanced error messages with clear, actionable guidance for common configuration issues.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json
from langswarm.core.errors import ConfigurationError, ErrorContext


class ConfigErrorHelper:
    """Helper class for providing detailed configuration error messages."""
    
    @staticmethod
    def file_not_found(file_path: str, search_paths: List[str]) -> ConfigurationError:
        """Create a helpful error for missing configuration files."""
        suggestion_paths = [
            "langswarm.yaml",
            "config/langswarm.yaml",
            "configs/langswarm.yaml"
        ]
        
        return ConfigurationError(
            f"Configuration file '{file_path}' not found",
            context=ErrorContext(
                component="ConfigurationLoader",
                operation="load_configuration",
                metadata={
                    "requested_file": file_path,
                    "searched_paths": search_paths
                }
            ),
            suggestion=(
                "Create a configuration file in one of these locations:\n"
                f"  • {suggestion_paths[0]} (recommended)\n"
                f"  • {suggestion_paths[1]}\n"
                f"  • {suggestion_paths[2]}\n\n"
                "Example minimal configuration:\n"
                "```yaml\n"
                "version: \"2.0\"\n"
                "agents:\n"
                "  - id: \"assistant\"\n"
                "    provider: \"openai\"\n"
                "    model: \"gpt-3.5-turbo\"\n"
                "```"
            )
        )
    
    @staticmethod
    def yaml_syntax_error(file_path: str, error: yaml.YAMLError) -> ConfigurationError:
        """Create a helpful error for YAML syntax issues."""
        line_info = ""
        if hasattr(error, 'problem_mark'):
            mark = error.problem_mark
            line_info = f" (line {mark.line + 1}, column {mark.column + 1})"
        
        return ConfigurationError(
            f"Invalid YAML syntax in configuration file{line_info}",
            context=ErrorContext(
                component="ConfigurationLoader",
                operation="parse_yaml",
                metadata={
                    "file": file_path,
                    "yaml_error": str(error)
                }
            ),
            suggestion=(
                "Check your YAML syntax:\n"
                "  • Ensure proper indentation (use spaces, not tabs)\n"
                "  • Check for missing colons after keys\n"
                "  • Verify quotes are properly closed\n"
                "  • Look for special characters that need escaping\n\n"
                "You can validate your YAML at: https://www.yamllint.com/"
            ),
            cause=error
        )
    
    @staticmethod
    def missing_required_field(field: str, section: str, example_value: Any = None) -> ConfigurationError:
        """Create a helpful error for missing required fields."""
        example = ""
        if example_value:
            if isinstance(example_value, str):
                example = f'\n\nExample:\n{section}:\n  {field}: "{example_value}"'
            else:
                example = f'\n\nExample:\n{section}:\n  {field}: {example_value}'
        
        return ConfigurationError(
            f"Missing required field '{field}' in {section}",
            context=ErrorContext(
                component="ConfigurationValidator",
                operation="validate_required_fields",
                metadata={
                    "field": field,
                    "section": section
                }
            ),
            suggestion=(
                f"Add the '{field}' field to your {section} configuration.{example}\n\n"
                f"This field is required for proper operation."
            )
        )
    
    @staticmethod
    def invalid_agent_config(agent_id: str, issue: str, suggestion: str) -> ConfigurationError:
        """Create a helpful error for agent configuration issues."""
        return ConfigurationError(
            f"Invalid agent configuration for '{agent_id}': {issue}",
            context=ErrorContext(
                component="AgentValidator",
                operation="validate_agent",
                metadata={
                    "agent_id": agent_id,
                    "issue": issue
                }
            ),
            suggestion=suggestion
        )
    
    @staticmethod
    def missing_api_key(provider: str, env_var: str) -> ConfigurationError:
        """Create a helpful error for missing API keys."""
        provider_docs = {
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com/api-keys",
            "google": "https://makersuite.google.com/app/apikey",
            "cohere": "https://dashboard.cohere.ai/api-keys",
            "mistral": "https://console.mistral.ai/api-keys"
        }
        
        doc_url = provider_docs.get(provider, "your provider's documentation")
        
        return ConfigurationError(
            f"API key not found for {provider} provider",
            context=ErrorContext(
                component="ConfigurationValidator",
                operation="validate_api_keys",
                metadata={
                    "provider": provider,
                    "env_var": env_var
                }
            ),
            suggestion=(
                f"Set your {provider.upper()} API key:\n"
                f"  1. Get your API key from: {doc_url}\n"
                f"  2. Set the environment variable:\n"
                f"     • Linux/Mac: export {env_var}='your-api-key'\n"
                f"     • Windows: set {env_var}=your-api-key\n"
                f"  3. Or add it to a .env file:\n"
                f"     {env_var}=your-api-key"
            )
        )
    
    @staticmethod
    def invalid_model(provider: str, model: str, valid_models: List[str]) -> ConfigurationError:
        """Create a helpful error for invalid model selection."""
        return ConfigurationError(
            f"Invalid model '{model}' for {provider} provider",
            context=ErrorContext(
                component="ConfigurationValidator",
                operation="validate_model",
                metadata={
                    "provider": provider,
                    "model": model,
                    "valid_models": valid_models
                }
            ),
            suggestion=(
                f"Choose a valid model for {provider}:\n" +
                "\n".join(f"  • {m}" for m in valid_models[:5]) +
                (f"\n  ... and {len(valid_models) - 5} more" if len(valid_models) > 5 else "")
            )
        )
    
    @staticmethod
    def circular_dependency(item_type: str, cycle: List[str]) -> ConfigurationError:
        """Create a helpful error for circular dependencies."""
        cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
        
        return ConfigurationError(
            f"Circular dependency detected in {item_type}",
            context=ErrorContext(
                component="DependencyValidator",
                operation="validate_dependencies",
                metadata={
                    "item_type": item_type,
                    "cycle": cycle
                }
            ),
            suggestion=(
                f"Remove the circular dependency:\n"
                f"  Current cycle: {cycle_str}\n\n"
                f"Each {item_type} can only depend on others that don't create a loop."
            )
        )
    
    @staticmethod
    def invalid_reference(ref_type: str, ref_id: str, available: List[str]) -> ConfigurationError:
        """Create a helpful error for invalid references."""
        similar = [a for a in available if ref_id.lower() in a.lower() or a.lower() in ref_id.lower()]
        
        suggestion = f"Available {ref_type}s:\n" + "\n".join(f"  • {a}" for a in available[:5])
        if similar:
            suggestion = f"Did you mean one of these?\n" + "\n".join(f"  • {s}" for s in similar[:3]) + f"\n\n{suggestion}"
        
        return ConfigurationError(
            f"Reference to undefined {ref_type}: '{ref_id}'",
            context=ErrorContext(
                component="ReferenceValidator",
                operation="validate_references",
                metadata={
                    "ref_type": ref_type,
                    "ref_id": ref_id,
                    "available": available
                }
            ),
            suggestion=suggestion
        )
    
    @staticmethod
    def incompatible_options(option1: str, option2: str, reason: str) -> ConfigurationError:
        """Create a helpful error for incompatible configuration options."""
        return ConfigurationError(
            f"Incompatible configuration options: '{option1}' and '{option2}'",
            context=ErrorContext(
                component="CompatibilityValidator",
                operation="validate_compatibility",
                metadata={
                    "option1": option1,
                    "option2": option2,
                    "reason": reason
                }
            ),
            suggestion=(
                f"These options cannot be used together: {reason}\n"
                f"Choose one approach or adjust your configuration."
            )
        )
    
    @staticmethod
    def deprecated_option(old_option: str, new_option: str, example: Optional[str] = None) -> ConfigurationError:
        """Create a helpful error for deprecated configuration options."""
        suggestion = f"Replace '{old_option}' with '{new_option}'"
        if example:
            suggestion += f"\n\nExample:\n{example}"
            
        return ConfigurationError(
            f"Deprecated configuration option: '{old_option}'",
            context=ErrorContext(
                component="ConfigurationLoader",
                operation="validate_options",
                metadata={
                    "old_option": old_option,
                    "new_option": new_option
                }
            ),
            suggestion=suggestion
        )
    
    @staticmethod
    def environment_variable_missing(var_name: str, description: str, example: Optional[str] = None) -> ConfigurationError:
        """Create a helpful error for missing environment variables."""
        suggestion = f"Set the environment variable '{var_name}'"
        if description:
            suggestion += f"\n{description}"
        if example:
            suggestion += f"\n\nExample:\nexport {var_name}=\"{example}\""
            
        return ConfigurationError(
            f"Required environment variable '{var_name}' not set",
            context=ErrorContext(
                component="EnvironmentValidator",
                operation="validate_environment",
                metadata={
                    "var_name": var_name
                }
            ),
            suggestion=suggestion
        )
    
    @staticmethod
    def invalid_memory_config(backend: str, issue: str) -> ConfigurationError:
        """Create a helpful error for memory configuration issues."""
        backend_requirements = {
            "sqlite": "No special requirements - works out of the box",
            "chromadb": "Install with: pip install chromadb",
            "redis": "Requires Redis server running. Install: pip install redis",
            "bigquery": "Requires Google Cloud project and credentials",
            "qdrant": "Requires Qdrant server or cloud instance",
            "elasticsearch": "Requires Elasticsearch server"
        }
        
        req = backend_requirements.get(backend, "Check documentation for requirements")
        
        return ConfigurationError(
            f"Invalid memory configuration for {backend}: {issue}",
            context=ErrorContext(
                component="MemoryValidator",
                operation="validate_memory_config",
                metadata={
                    "backend": backend,
                    "issue": issue
                }
            ),
            suggestion=(
                f"Fix the memory configuration:\n"
                f"  Issue: {issue}\n"
                f"  Requirements: {req}\n\n"
                "For development, use 'sqlite' for simplicity:\n"
                "```yaml\n"
                "memory:\n"
                "  backend: sqlite\n"
                "```"
            )
        )
    
    @staticmethod
    def workflow_syntax_error(workflow_id: str, syntax: str, issue: str) -> ConfigurationError:
        """Create a helpful error for workflow syntax issues."""
        examples = {
            "simple": "assistant -> user",
            "chain": "researcher -> analyzer -> writer -> user",
            "parallel": "agent1, agent2, agent3 -> aggregator -> user",
            "conditional": "classifier -> (specialist1 | specialist2) -> user"
        }
        
        return ConfigurationError(
            f"Invalid workflow syntax in '{workflow_id}': {issue}",
            context=ErrorContext(
                component="WorkflowValidator",
                operation="validate_workflow_syntax",
                metadata={
                    "workflow_id": workflow_id,
                    "syntax": syntax,
                    "issue": issue
                }
            ),
            suggestion=(
                f"Fix the workflow syntax. Examples:\n" +
                "\n".join(f"  • {name}: {ex}" for name, ex in examples.items()) +
                f"\n\nYour syntax: {syntax}\n"
                f"Issue: {issue}"
            )
        )


def get_helpful_suggestions(error_type: str, **kwargs) -> List[str]:
    """Get helpful suggestions for different error types."""
    
    if error_type == "missing_api_key":
        provider = kwargs.get("provider", "")
        suggestions = []
        
        if provider == "openai":
            suggestions = [
                "1. Get an API key from https://platform.openai.com/api-keys",
                "2. Set environment variable: export OPENAI_API_KEY='your-key-here'",
                "3. Or add to your shell profile for persistence"
            ]
        elif provider == "anthropic":
            suggestions = [
                "1. Get an API key from https://console.anthropic.com/", 
                "2. Set environment variable: export ANTHROPIC_API_KEY='your-key-here'",
                "3. Or add to your shell profile for persistence"
            ]
        elif provider == "google":
            suggestions = [
                "1. Get an API key from Google AI Studio",
                "2. Set environment variable: export GOOGLE_API_KEY='your-key-here'",
                "3. Or add to your shell profile for persistence"
            ]
        else:
            suggestions = [
                "1. Check your provider documentation for API key setup",
                "2. Set the appropriate environment variable",
                "3. Verify the key has the correct permissions"
            ]
        
        return suggestions
    
    elif error_type == "file_not_found":
        file_type = kwargs.get("file_type", "")
        suggestions = [
            "1. Check if the file exists in the current directory",
            "2. Verify the file path is correct",
            "3. Ensure you have read permissions"
        ]
        
        if file_type == "config":
            suggestions.extend([
                "4. Try creating a minimal langswarm.yaml file",
                "5. Use absolute path if relative path fails"
            ])
        
        return suggestions
    
    elif error_type == "missing_dependency":
        package = kwargs.get("package", "")
        suggestions = [
            f"1. Install the package: pip install {package}",
            "2. Check if you're in the correct virtual environment",
            "3. Consider installing optional dependencies: pip install langswarm[full]"
        ]
        
        return suggestions
    
    elif error_type == "invalid_provider":
        suggestions = [
            "1. Use one of these supported providers:",
            "   • openai (for GPT models)",
            "   • anthropic (for Claude models)",
            "   • google (for Gemini models)",
            "   • cohere (for Command models)",
            "   • mistral (for Mistral models)",
            "2. Check spelling and capitalization",
            "3. Install provider dependencies if needed"
        ]
        
        return suggestions
    
    else:
        return [
            "1. Check the documentation for this feature",
            "2. Verify your configuration syntax",
            "3. Look for typos or missing required fields"
        ]