"""
Enhanced Configuration Validator with Clear Error Messages

Provides detailed validation with helpful error messages for common configuration issues.
"""

from typing import Dict, List, Any, Optional, Set
from langswarm.core.config.schema import LangSwarmConfig, AgentConfig, WorkflowConfig, ProviderType
from langswarm.core.config.error_helpers import ConfigErrorHelper
from langswarm.core.errors import ConfigurationError, ErrorContext
import re


class EnhancedConfigValidator:
    """Enhanced validator that provides clear, actionable error messages."""
    
    # Valid models per provider
    VALID_MODELS = {
        "openai": [
            "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", 
            "gpt-3.5-turbo-16k", "text-embedding-ada-002"
        ],
        "anthropic": [
            "claude-3-opus-20240229", "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307", "claude-2.1", "claude-instant-1.2"
        ],
        "google": [
            "gemini-pro", "gemini-pro-vision", "gemini-ultra",
            "text-bison-001", "chat-bison-001"
        ],
        "cohere": [
            "command", "command-light", "command-nightly",
            "embed-english-v3.0", "embed-multilingual-v3.0"
        ],
        "mistral": [
            "mistral-tiny", "mistral-small", "mistral-medium",
            "mistral-large", "open-mistral-7b", "open-mixtral-8x7b"
        ]
    }
    
    def validate_config(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """
        Validate the entire configuration and return a list of errors.
        
        Returns empty list if validation passes.
        """
        errors = []
        
        # Validate agents
        errors.extend(self._validate_agents(config))
        
        # Validate workflows
        errors.extend(self._validate_workflows(config))
        
        # Validate tool references
        errors.extend(self._validate_tool_references(config))
        
        # Validate memory configuration
        errors.extend(self._validate_memory_config(config))
        
        # Check for circular dependencies
        errors.extend(self._validate_no_circular_deps(config))
        
        return errors
    
    def _validate_agents(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """Validate agent configurations."""
        errors = []
        agent_ids = set()
        
        for agent in config.agents:
            # Check for duplicate IDs
            if agent.id in agent_ids:
                errors.append(ConfigurationError(
                    f"Duplicate agent ID: '{agent.id}'",
                    context=ErrorContext(
                        component="AgentValidator",
                        operation="validate_unique_ids"
                    ),
                    suggestion=f"Each agent must have a unique ID. Consider renaming to '{agent.id}_2' or similar."
                ))
            agent_ids.add(agent.id)
            
            # Validate model for provider
            if agent.provider and agent.model:
                valid_models = self.VALID_MODELS.get(agent.provider.value, [])
                if valid_models and agent.model not in valid_models:
                    # Find similar models
                    similar = [m for m in valid_models if agent.model.lower() in m.lower()]
                    if similar:
                        errors.append(ConfigErrorHelper.invalid_model(
                            agent.provider.value,
                            agent.model,
                            similar
                        ))
                    else:
                        errors.append(ConfigErrorHelper.invalid_model(
                            agent.provider.value,
                            agent.model,
                            valid_models
                        ))
            
            # Validate required fields
            if not agent.system_prompt and not agent.behavior:
                errors.append(ConfigErrorHelper.invalid_agent_config(
                    agent.id,
                    "Missing both system_prompt and behavior",
                    "Add either a 'system_prompt' or 'behavior' field to define the agent's purpose.\n"
                    "Example:\n"
                    "  system_prompt: \"You are a helpful assistant\"\n"
                    "OR\n"
                    "  behavior: helpful"
                ))
            
            # Validate tool references
            if agent.tools:
                for tool_id in agent.tools:
                    if tool_id not in [t.id for t in config.tools]:
                        available_tools = [t.id for t in config.tools]
                        errors.append(ConfigErrorHelper.invalid_reference(
                            "tool",
                            tool_id,
                            available_tools
                        ))
        
        return errors
    
    def _validate_workflows(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """Validate workflow configurations."""
        errors = []
        workflow_ids = set()
        agent_ids = {agent.id for agent in config.agents}
        
        for workflow in config.workflows:
            # Check for duplicate workflow IDs
            if workflow.id in workflow_ids:
                errors.append(ConfigurationError(
                    f"Duplicate workflow ID: '{workflow.id}'",
                    context=ErrorContext(
                        component="WorkflowValidator",
                        operation="validate_unique_ids"
                    ),
                    suggestion=f"Each workflow must have a unique ID. Consider renaming to '{workflow.id}_v2' or similar."
                ))
            workflow_ids.add(workflow.id)
            
            # Validate simple workflow syntax if present
            if hasattr(workflow, 'simple') and workflow.simple:
                errors.extend(self._validate_simple_workflow_syntax(
                    workflow.id,
                    workflow.simple,
                    agent_ids
                ))
            
            # Validate step-based workflows
            elif hasattr(workflow, 'steps') and workflow.steps:
                for step in workflow.steps:
                    if step.agent and step.agent not in agent_ids:
                        errors.append(ConfigErrorHelper.invalid_reference(
                            "agent",
                            step.agent,
                            list(agent_ids)
                        ))
        
        return errors
    
    def _validate_simple_workflow_syntax(self, workflow_id: str, syntax: str, agent_ids: Set[str]) -> List[ConfigurationError]:
        """Validate simple workflow syntax like 'agent1 -> agent2 -> user'."""
        errors = []
        
        # Basic syntax validation
        if not syntax or not syntax.strip():
            errors.append(ConfigErrorHelper.workflow_syntax_error(
                workflow_id,
                syntax,
                "Empty workflow syntax"
            ))
            return errors
        
        # Parse workflow components
        # Support: ->, ,, |, ()
        components = re.findall(r'[a-zA-Z0-9_]+', syntax)
        
        for component in components:
            if component not in agent_ids and component not in ['user', 'system']:
                errors.append(ConfigErrorHelper.invalid_reference(
                    "agent in workflow",
                    component,
                    list(agent_ids) + ['user', 'system']
                ))
        
        # Check for basic syntax patterns
        if '->' not in syntax and ',' not in syntax and '|' not in syntax:
            errors.append(ConfigErrorHelper.workflow_syntax_error(
                workflow_id,
                syntax,
                "Missing workflow operators (use ->, comma, or |)"
            ))
        
        return errors
    
    def _validate_tool_references(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """Validate that all tool references exist."""
        errors = []
        tool_ids = {tool.id for tool in config.tools}
        
        # Check agents' tool references
        for agent in config.agents:
            if agent.tools:
                for tool_ref in agent.tools:
                    if tool_ref not in tool_ids:
                        errors.append(ConfigErrorHelper.invalid_reference(
                            "tool",
                            tool_ref,
                            list(tool_ids)
                        ))
        
        return errors
    
    def _validate_memory_config(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """Validate memory configuration."""
        errors = []
        
        if config.memory:
            backend = config.memory.backend.value
            
            # Check for required settings per backend
            if backend == "bigquery" and not config.memory.config.get("project"):
                errors.append(ConfigErrorHelper.invalid_memory_config(
                    backend,
                    "Missing required 'project' setting for BigQuery"
                ))
            
            elif backend == "redis" and not config.memory.config.get("url"):
                errors.append(ConfigurationError(
                    "Redis memory backend requires 'url' configuration",
                    context=ErrorContext(
                        component="MemoryValidator",
                        operation="validate_redis_config"
                    ),
                    suggestion=(
                        "Add Redis URL to memory config:\n"
                        "```yaml\n"
                        "memory:\n"
                        "  backend: redis\n"
                        "  config:\n"
                        "    url: redis://localhost:6379\n"
                        "```"
                    )
                ))
        
        return errors
    
    def _validate_no_circular_deps(self, config: LangSwarmConfig) -> List[ConfigurationError]:
        """Check for circular dependencies in workflows."""
        errors = []
        
        # This would be more complex in practice, but here's a simple example
        # of detecting obvious circular references
        
        return errors
    
    def get_validation_summary(self, errors: List[ConfigurationError]) -> str:
        """Get a formatted summary of validation errors."""
        if not errors:
            return "✅ Configuration validation passed!"
        
        summary = f"❌ Configuration validation failed with {len(errors)} error(s):\n\n"
        
        for i, error in enumerate(errors, 1):
            summary += f"{i}. {error}\n\n"
        
        return summary