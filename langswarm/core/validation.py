"""
LangSwarm Configuration Validation

Provides real-time validation with helpful error messages and suggestions.
"""

import re
import os
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def add_error(self, message: str, suggestion: str = None):
        """Add a validation error with optional suggestion."""
        self.errors.append(message)
        self.is_valid = False
        if suggestion:
            self.suggestions.append(suggestion)
    
    def add_warning(self, message: str, suggestion: str = None):
        """Add a validation warning with optional suggestion."""
        self.warnings.append(message)
        if suggestion:
            self.suggestions.append(suggestion)
    
    def get_summary(self) -> str:
        """Get a formatted summary of validation results."""
        if self.is_valid and not self.warnings:
            return "✅ Configuration validation passed!"
        
        summary = []
        
        if self.errors:
            summary.append(f"❌ {len(self.errors)} error(s) found:")
            for i, error in enumerate(self.errors, 1):
                summary.append(f"   {i}. {error}")
        
        if self.warnings:
            summary.append(f"⚠️  {len(self.warnings)} warning(s):")
            for i, warning in enumerate(self.warnings, 1):
                summary.append(f"   {i}. {warning}")
        
        if self.suggestions:
            summary.append("\n💡 Suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                summary.append(f"   {i}. {suggestion}")
        
        return "\n".join(summary)


class LangSwarmValidator:
    """Comprehensive LangSwarm configuration validator."""
    
    # Valid behavior types
    VALID_BEHAVIORS = [
        "helpful", "coding", "research", "creative", "analytical", 
        "support", "conversational", "educational"
    ]
    
    # Valid memory tiers
    VALID_MEMORY_TIERS = [
        True, False, "true", "false", "production", "development", 
        "testing", "cloud"
    ]
    
    # Valid agent types
    VALID_AGENT_TYPES = [
        "openai", "langchain-openai", "generic", "anthropic", "huggingface"
    ]
    
    # Common MCP tool types
    KNOWN_TOOL_TYPES = [
        "mcpfilesystem", "mcpgithubtool", "mcpforms", "web_search", 
        "calculator", "database", "api_client"
    ]
    
    def __init__(self):
        self.result = ValidationResult(True, [], [], [])
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate complete LangSwarm configuration."""
        self.result = ValidationResult(True, [], [], [])
        
        # Validate top-level structure
        self._validate_top_level(config)
        
        # Validate agents
        if "agents" in config:
            self._validate_agents(config["agents"])
        
        # Validate workflows
        if "workflows" in config:
            self._validate_workflows(config["workflows"], config.get("agents", []))
        
        # Validate memory configuration
        if "memory" in config:
            self._validate_memory(config["memory"])
        
        # Validate tools
        if "tools" in config:
            self._validate_tools(config["tools"])
        
        return self.result
    
    def _validate_top_level(self, config: Dict[str, Any]):
        """Validate top-level configuration structure."""
        # Check for version
        if "version" not in config:
            self.result.add_warning(
                "No version specified in configuration",
                "Add 'version: \"1.0\"' to your configuration for better compatibility"
            )
        
        # Check for essential sections
        if "agents" not in config:
            self.result.add_error(
                "No agents defined in configuration",
                "Add at least one agent: agents: [{id: assistant, model: gpt-4o, behavior: helpful}]"
            )
        
        # Check for deprecated patterns
        if isinstance(config.get("agents"), dict):
            self.result.add_warning(
                "Agents defined as dictionary (legacy format)",
                "Consider using list format: agents: [{id: agent1, ...}, {id: agent2, ...}]"
            )
    
    def _validate_agents(self, agents: List[Dict[str, Any]]):
        """Validate agent configurations."""
        if not isinstance(agents, list):
            self.result.add_error(
                "Agents must be a list",
                "Use: agents: [{id: agent1, ...}, {id: agent2, ...}]"
            )
            return
        
        agent_ids = set()
        
        for i, agent in enumerate(agents):
            self._validate_agent(agent, i, agent_ids)
    
    def _validate_agent(self, agent: Dict[str, Any], index: int, agent_ids: set):
        """Validate individual agent configuration."""
        agent_ref = f"agents[{index}]"
        
        # Required fields
        if "id" not in agent:
            self.result.add_error(
                f"{agent_ref}: Missing required 'id' field",
                "Add a unique identifier: id: my_agent"
            )
        else:
            agent_id = agent["id"]
            
            # Check for duplicate IDs
            if agent_id in agent_ids:
                self.result.add_error(
                    f"{agent_ref}: Duplicate agent ID '{agent_id}'",
                    "Each agent must have a unique ID"
                )
            agent_ids.add(agent_id)
            
            # Update reference to use ID
            agent_ref = f"agent '{agent_id}'"
        
        # Model validation
        if "model" not in agent:
            self.result.add_warning(
                f"{agent_ref}: No model specified",
                "Add model field: model: gpt-4o"
            )
        
        # Behavior validation
        if "behavior" in agent:
            behavior = agent["behavior"]
            if behavior not in self.VALID_BEHAVIORS:
                self.result.add_error(
                    f"{agent_ref}: Invalid behavior '{behavior}'",
                    f"Use one of: {', '.join(self.VALID_BEHAVIORS)}"
                )
        elif "system_prompt" not in agent:
            self.result.add_warning(
                f"{agent_ref}: No behavior or system_prompt specified",
                "Add behavior: helpful or system_prompt: 'Custom prompt...'"
            )
        
        # Agent type validation
        if "agent_type" in agent:
            agent_type = agent["agent_type"]
            if agent_type not in self.VALID_AGENT_TYPES:
                self.result.add_warning(
                    f"{agent_ref}: Unknown agent_type '{agent_type}'",
                    f"Common types: {', '.join(self.VALID_AGENT_TYPES)}"
                )
        
        # Tools validation
        if "tools" in agent:
            self._validate_agent_tools(agent["tools"], agent_ref)
    
    def _validate_agent_tools(self, tools: List[str], agent_ref: str):
        """Validate agent tool references."""
        if not isinstance(tools, list):
            self.result.add_error(
                f"{agent_ref}: Tools must be a list",
                "Use: tools: [filesystem, web_search]"
            )
            return
        
        for tool in tools:
            if not isinstance(tool, str):
                self.result.add_error(
                    f"{agent_ref}: Tool names must be strings",
                    "Use: tools: ['filesystem', 'web_search']"
                )
    
    def _validate_workflows(self, workflows: List[Any], agents: List[Dict[str, Any]]):
        """Validate workflow configurations."""
        if not isinstance(workflows, list):
            self.result.add_error(
                "Workflows must be a list",
                "Use: workflows: ['agent1 -> user'] or workflows: [{id: wf1, simple: 'agent1 -> user'}]"
            )
            return
        
        # Get agent IDs for validation
        agent_ids = {agent.get("id") for agent in agents if agent.get("id")}
        
        for i, workflow in enumerate(workflows):
            self._validate_workflow(workflow, i, agent_ids)
    
    def _validate_workflow(self, workflow: Any, index: int, agent_ids: set):
        """Validate individual workflow configuration."""
        workflow_ref = f"workflows[{index}]"
        
        if isinstance(workflow, str):
            # Simple syntax workflow
            self._validate_simple_workflow_syntax(workflow, workflow_ref, agent_ids)
        elif isinstance(workflow, dict):
            # Complex workflow
            if "simple" in workflow or "workflow" in workflow:
                # Simple syntax in dict format
                syntax = workflow.get("simple") or workflow.get("workflow")
                self._validate_simple_workflow_syntax(syntax, workflow_ref, agent_ids)
            elif "steps" in workflow:
                # Complex workflow format
                self._validate_complex_workflow(workflow, workflow_ref, agent_ids)
            else:
                self.result.add_error(
                    f"{workflow_ref}: Invalid workflow format",
                    "Use simple syntax: 'agent -> user' or complex format with 'steps'"
                )
        else:
            self.result.add_error(
                f"{workflow_ref}: Workflow must be string or object",
                "Use: 'agent -> user' or {id: wf1, simple: 'agent -> user'}"
            )
    
    def _validate_simple_workflow_syntax(self, syntax: str, workflow_ref: str, agent_ids: set):
        """Validate simple workflow syntax."""
        if not syntax or not isinstance(syntax, str):
            self.result.add_error(
                f"{workflow_ref}: Empty or invalid workflow syntax",
                "Use format: 'agent1 -> agent2 -> user'"
            )
            return
        
        # Check for basic syntax patterns
        if "->" not in syntax:
            self.result.add_error(
                f"{workflow_ref}: Missing arrow (->) in workflow syntax",
                "Use format: 'agent1 -> agent2 -> user'"
            )
            return
        
        # Extract agent names from workflow
        # Simple pattern: agent1 -> agent2 -> user
        parts = [part.strip() for part in syntax.split("->")]
        
        for part in parts[:-1]:  # Exclude 'user' at the end
            # Handle parallel syntax: agent1, agent2
            if "," in part:
                agent_names = [name.strip() for name in part.split(",")]
            # Handle conditional syntax: (agent1 | agent2)
            elif "|" in part:
                # Extract agents from conditional syntax
                conditional_part = part.strip("()")
                agent_names = [name.strip() for name in conditional_part.split("|")]
            else:
                agent_names = [part.strip()]
            
            # Validate agent names
            for agent_name in agent_names:
                if agent_name and agent_name != "user" and agent_name not in agent_ids:
                    self.result.add_error(
                        f"{workflow_ref}: Unknown agent '{agent_name}' in workflow",
                        f"Define the agent or use one of: {', '.join(sorted(agent_ids))}"
                    )
    
    def _validate_complex_workflow(self, workflow: Dict[str, Any], workflow_ref: str, agent_ids: set):
        """Validate complex workflow format."""
        if "id" not in workflow:
            self.result.add_warning(
                f"{workflow_ref}: No ID specified for complex workflow",
                "Add id: my_workflow_name"
            )
        
        if "steps" not in workflow:
            self.result.add_error(
                f"{workflow_ref}: Complex workflow missing 'steps'",
                "Add steps: [{id: step1, agent: my_agent, ...}]"
            )
            return
        
        steps = workflow["steps"]
        if not isinstance(steps, list):
            self.result.add_error(
                f"{workflow_ref}: Steps must be a list",
                "Use: steps: [{id: step1, agent: my_agent}, ...]"
            )
            return
        
        for i, step in enumerate(steps):
            self._validate_workflow_step(step, f"{workflow_ref}.steps[{i}]", agent_ids)
    
    def _validate_workflow_step(self, step: Dict[str, Any], step_ref: str, agent_ids: set):
        """Validate individual workflow step."""
        if not isinstance(step, dict):
            self.result.add_error(
                f"{step_ref}: Step must be an object",
                "Use: {id: step1, agent: my_agent, input: '...', output: {...}}"
            )
            return
        
        # Check required fields
        if "id" not in step:
            self.result.add_error(
                f"{step_ref}: Missing step ID",
                "Add id: step_name"
            )
        
        if "agent" not in step and "function" not in step:
            self.result.add_error(
                f"{step_ref}: Step must have 'agent' or 'function'",
                "Add agent: my_agent or function: my_function"
            )
        
        # Validate agent reference
        if "agent" in step:
            agent_name = step["agent"]
            if agent_name not in agent_ids:
                self.result.add_error(
                    f"{step_ref}: Unknown agent '{agent_name}'",
                    f"Use one of: {', '.join(sorted(agent_ids))}"
                )
    
    def _validate_memory(self, memory_config: Any):
        """Validate memory configuration."""
        if memory_config in [True, False, "true", "false"]:
            # Simple boolean configuration
            return
        elif isinstance(memory_config, str):
            # Tier-based configuration
            if memory_config not in ["production", "development", "testing", "cloud"]:
                self.result.add_error(
                    f"Invalid memory tier: '{memory_config}'",
                    "Use: true, production, development, testing, or custom configuration"
                )
        elif isinstance(memory_config, dict):
            # Custom memory configuration
            if "backend" not in memory_config:
                self.result.add_warning(
                    "Custom memory configuration missing 'backend'",
                    "Specify backend: sqlite, chromadb, redis, etc."
                )
        else:
            self.result.add_error(
                "Invalid memory configuration format",
                "Use: true, 'production', or {backend: sqlite, settings: {...}}"
            )
    
    def _validate_tools(self, tools: List[Dict[str, Any]]):
        """Validate tool configurations."""
        if not isinstance(tools, list):
            self.result.add_error(
                "Tools must be a list",
                "Use: tools: [{id: tool1, type: mcpfilesystem}, ...]"
            )
            return
        
        tool_ids = set()
        
        for i, tool in enumerate(tools):
            self._validate_tool(tool, i, tool_ids)
    
    def _validate_tool(self, tool: Dict[str, Any], index: int, tool_ids: set):
        """Validate individual tool configuration."""
        tool_ref = f"tools[{index}]"
        
        if not isinstance(tool, dict):
            self.result.add_error(
                f"{tool_ref}: Tool must be an object",
                "Use: {id: my_tool, type: mcpfilesystem, ...}"
            )
            return
        
        # Required fields
        if "id" not in tool:
            self.result.add_error(
                f"{tool_ref}: Missing required 'id' field",
                "Add id: my_tool_name"
            )
        else:
            tool_id = tool["id"]
            if tool_id in tool_ids:
                self.result.add_error(
                    f"{tool_ref}: Duplicate tool ID '{tool_id}'",
                    "Each tool must have a unique ID"
                )
            tool_ids.add(tool_id)
            tool_ref = f"tool '{tool_id}'"
        
        if "type" not in tool:
            self.result.add_error(
                f"{tool_ref}: Missing required 'type' field",
                f"Add type field. Common types: {', '.join(self.KNOWN_TOOL_TYPES)}"
            )
        else:
            tool_type = tool["type"]
            if tool_type not in self.KNOWN_TOOL_TYPES:
                self.result.add_warning(
                    f"{tool_ref}: Unknown tool type '{tool_type}'",
                    f"Common types: {', '.join(self.KNOWN_TOOL_TYPES)}"
                )


def validate_config_file(file_path: str) -> ValidationResult:
    """Validate a LangSwarm configuration file."""
    import yaml
    
    validator = LangSwarmValidator()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            result = ValidationResult(False, [], [], [])
            result.add_error(
                "Configuration file is empty",
                "Add basic configuration: version: '1.0', agents: [...], workflows: [...]"
            )
            return result
        
        return validator.validate_config(config)
    
    except FileNotFoundError:
        result = ValidationResult(False, [], [], [])
        result.add_error(
            f"Configuration file not found: {file_path}",
            "Create a langswarm.yaml file with your configuration"
        )
        return result
    
    except yaml.YAMLError as e:
        result = ValidationResult(False, [], [], [])
        result.add_error(
            f"YAML syntax error: {e}",
            "Check YAML syntax - ensure proper indentation and no tabs"
        )
        return result
    
    except Exception as e:
        result = ValidationResult(False, [], [], [])
        result.add_error(
            f"Error reading configuration: {e}",
            "Check file permissions and content format"
        )
        return result


def validate_config_dict(config: Dict[str, Any]) -> ValidationResult:
    """Validate a LangSwarm configuration dictionary."""
    validator = LangSwarmValidator()
    return validator.validate_config(config)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        result = validate_config_file(config_file)
        print(result.get_summary())
        sys.exit(0 if result.is_valid else 1)
    else:
        print("Usage: python validation.py <config_file>")
        sys.exit(1) 