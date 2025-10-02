"""
LangSwarm V2 Configuration Validation

Comprehensive validation system for V2 configurations with:
- Schema-based validation
- Cross-reference validation
- Environment validation
- Performance validation
- Security validation
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .schema import (
    LangSwarmConfig, AgentConfig, ToolConfig, WorkflowConfig,
    ProviderType, MemoryBackend, LogLevel
)
from langswarm.core.errors import ValidationError


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    severity: ValidationSeverity
    category: str
    field: str
    message: str
    suggestion: Optional[str] = None
    section: Optional[str] = None
    
    def __str__(self) -> str:
        base = f"[{self.severity.value.upper()}] {self.category}"
        if self.section:
            base += f".{self.section}"
        base += f".{self.field}: {self.message}"
        if self.suggestion:
            base += f" Suggestion: {self.suggestion}"
        return base


class ConfigurationValidator:
    """
    Comprehensive configuration validator for LangSwarm V2.
    
    Validates:
    - Schema compliance
    - Cross-references between components
    - Environment requirements
    - Performance implications
    - Security considerations
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, warnings are treated as errors (DEFAULT: True for fail-fast behavior)
        """
        self.strict_mode = strict_mode
        self.issues: List[ValidationIssue] = []
    
    def validate(self, config: LangSwarmConfig) -> Tuple[bool, List[ValidationIssue]]:
        """
        Comprehensive configuration validation.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, issues_list)
        """
        self.issues = []
        
        logger.info("Starting comprehensive configuration validation")
        
        # Schema validation
        self._validate_schema(config)
        
        # Cross-reference validation
        self._validate_cross_references(config)
        
        # Environment validation
        self._validate_environment(config)
        
        # Performance validation
        self._validate_performance(config)
        
        # Security validation
        self._validate_security(config)
        
        # Best practices validation
        self._validate_best_practices(config)
        
        # Determine if configuration is valid
        error_count = len([issue for issue in self.issues if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
        warning_count = len([issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING])
        
        is_valid = error_count == 0 and (not self.strict_mode or warning_count == 0)
        
        logger.info(f"Validation complete: {len(self.issues)} issues found ({error_count} errors, {warning_count} warnings)")
        
        return is_valid, self.issues
    
    def _validate_schema(self, config: LangSwarmConfig):
        """Validate basic schema compliance"""
        
        # Validate version
        if not config.version or not config.version.startswith("2."):
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "version",
                f"Invalid version '{config.version}', expected '2.x'",
                "Use version '2.0' for V2 configurations"
            ))
        
        # Validate required fields
        if not config.agents:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "schema",
                "agents",
                "No agents configured",
                "Add at least one agent for functionality"
            ))
        
        # Validate agent schemas
        for i, agent in enumerate(config.agents):
            self._validate_agent_schema(agent, i)
        
        # Validate tool schemas
        for tool_id, tool in config.tools.items():
            self._validate_tool_schema(tool, tool_id)
        
        # Validate workflow schemas
        for i, workflow in enumerate(config.workflows):
            self._validate_workflow_schema(workflow, i)
    
    def _validate_agent_schema(self, agent: AgentConfig, index: int):
        """Validate individual agent schema"""
        section = f"agents[{index}]"
        
        # Validate ID
        if not agent.id or not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', agent.id):
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "id",
                f"Invalid agent ID '{agent.id}', must start with letter and contain only alphanumeric, underscore, or dash",
                "Use format: 'my_agent' or 'my-agent'",
                section
            ))
        
        # Validate provider
        if agent.provider not in ProviderType:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema", 
                "provider",
                f"Invalid provider '{agent.provider}'",
                f"Use one of: {', '.join([p.value for p in ProviderType])}",
                section
            ))
        
        # Validate temperature
        if not 0.0 <= agent.temperature <= 2.0:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "temperature",
                f"Temperature {agent.temperature} out of range [0.0, 2.0]",
                "Use values between 0.0 (deterministic) and 2.0 (very creative)",
                section
            ))
        
        # Validate max_tokens
        if agent.max_tokens is not None and agent.max_tokens <= 0:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "max_tokens",
                f"max_tokens must be positive, got {agent.max_tokens}",
                "Use positive integer or null for model default",
                section
            ))
        
        # Validate model for provider
        self._validate_model_for_provider(agent, section)
    
    def _validate_model_for_provider(self, agent: AgentConfig, section: str):
        """Validate model compatibility with provider"""
        
        valid_models = {
            ProviderType.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            ProviderType.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            ProviderType.GEMINI: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            ProviderType.COHERE: ["command-r-plus", "command-r", "command"],
            ProviderType.AZURE_OPENAI: ["gpt-4", "gpt-4-32k", "gpt-35-turbo"],
            ProviderType.MOCK: ["mock-model"]
        }
        
        if agent.provider in valid_models:
            if agent.model not in valid_models[agent.provider]:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    "schema",
                    "model",
                    f"Model '{agent.model}' may not be compatible with provider '{agent.provider.value}'",
                    f"Consider using: {', '.join(valid_models[agent.provider][:3])}",
                    section
                ))
    
    def _validate_tool_schema(self, tool: ToolConfig, tool_id: str):
        """Validate individual tool schema"""
        section = f"tools.{tool_id}"
        
        # Validate ID matches key
        if tool.id != tool_id:
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "id",
                f"Tool ID '{tool.id}' doesn't match key '{tool_id}'",
                "Ensure tool ID matches the dictionary key",
                section
            ))
        
        # Validate tool type
        valid_tool_types = ["builtin", "memory", "utility", "workflow", "integration", "custom"]
        if tool.type not in valid_tool_types:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "schema",
                "type",
                f"Unknown tool type '{tool.type}'",
                f"Consider using: {', '.join(valid_tool_types)}",
                section
            ))
    
    def _validate_workflow_schema(self, workflow: WorkflowConfig, index: int):
        """Validate individual workflow schema"""
        section = f"workflows[{index}]"
        
        # Validate ID
        if not workflow.id or not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', workflow.id):
            self.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "schema",
                "id",
                f"Invalid workflow ID '{workflow.id}'",
                "Use alphanumeric characters, underscores, or dashes",
                section
            ))
        
        # Validate steps
        if not workflow.steps and not workflow.simple_syntax:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "schema",
                "steps",
                "Workflow has no steps or simple syntax",
                "Add workflow steps or simple syntax definition",
                section
            ))
    
    def _validate_cross_references(self, config: LangSwarmConfig):
        """Validate cross-references between configuration components"""
        
        # Collect all agent IDs
        agent_ids = {agent.id for agent in config.agents}
        tool_ids = set(config.tools.keys())
        
        # Validate agent tool references
        for i, agent in enumerate(config.agents):
            for tool_id in agent.tools:
                if tool_id not in tool_ids:
                    self.issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "cross_reference",
                        "tools",
                        f"Agent '{agent.id}' references unknown tool '{tool_id}'",
                        f"Add tool '{tool_id}' to tools section or remove reference",
                        f"agents[{i}]"
                    ))
        
        # Validate workflow agent references
        for i, workflow in enumerate(config.workflows):
            for j, step in enumerate(workflow.steps):
                if step.get("type") == "agent":
                    agent_id = step.get("agent_id")
                    if agent_id and agent_id not in agent_ids:
                        self.issues.append(ValidationIssue(
                            ValidationSeverity.ERROR,
                            "cross_reference",
                            "agent_id",
                            f"Workflow '{workflow.id}' step {j} references unknown agent '{agent_id}'",
                            f"Add agent '{agent_id}' or fix reference",
                            f"workflows[{i}].steps[{j}]"
                        ))
        
        # Validate tool access control
        for tool_id, tool in config.tools.items():
            if tool.allowed_agents:
                for allowed_agent in tool.allowed_agents:
                    if allowed_agent not in agent_ids:
                        self.issues.append(ValidationIssue(
                            ValidationSeverity.WARNING,
                            "cross_reference",
                            "allowed_agents",
                            f"Tool '{tool_id}' allows unknown agent '{allowed_agent}'",
                            "Remove reference or add agent",
                            f"tools.{tool_id}"
                        ))
    
    def _validate_environment(self, config: LangSwarmConfig):
        """Validate environment requirements"""
        
        # Check required environment variables
        required_env_vars = []
        
        # Collect required API keys based on providers
        provider_env_map = {
            ProviderType.OPENAI: config.security.openai_api_key_env,
            ProviderType.ANTHROPIC: config.security.anthropic_api_key_env,
            ProviderType.GEMINI: config.security.gemini_api_key_env,
            ProviderType.COHERE: config.security.cohere_api_key_env,
        }
        
        used_providers = {agent.provider for agent in config.agents}
        
        for provider in used_providers:
            if provider in provider_env_map and provider != ProviderType.MOCK:
                env_var = provider_env_map[provider]
                if not os.getenv(env_var):
                    self.issues.append(ValidationIssue(
                        ValidationSeverity.WARNING,
                        "environment",
                        "api_key",
                        f"Environment variable '{env_var}' not set for provider '{provider.value}'",
                        f"Set {env_var} environment variable or use mock provider for testing",
                        "security"
                    ))
        
        # Check memory backend requirements
        if config.memory.backend == MemoryBackend.REDIS:
            redis_url = config.memory.config.get("url", "redis://localhost:6379")
            if "localhost" in redis_url:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.INFO,
                    "environment",
                    "memory_backend",
                    "Redis backend configured with localhost",
                    "Ensure Redis server is running locally",
                    "memory"
                ))
        
        # Check file permissions for SQLite
        if config.memory.backend == MemoryBackend.SQLITE:
            db_path = config.memory.config.get("db_path", "langswarm.db")
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.access(db_dir, os.W_OK):
                self.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    "environment",
                    "file_permissions",
                    f"No write permission for SQLite database directory: {db_dir}",
                    "Ensure directory is writable or change database path",
                    "memory"
                ))
    
    def _validate_performance(self, config: LangSwarmConfig):
        """Validate performance implications"""
        
        # Check for too many concurrent agents
        if len(config.agents) > 10:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "performance",
                "agent_count",
                f"Large number of agents ({len(config.agents)}) may impact performance",
                "Consider reducing agent count or optimizing resource usage",
                "agents"
            ))
        
        # Check memory settings
        total_max_tokens = sum(
            agent.max_tokens for agent in config.agents 
            if agent.max_tokens is not None
        )
        if total_max_tokens > 100000:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "performance",
                "token_limits",
                f"High total max_tokens ({total_max_tokens}) across agents",
                "Consider reducing individual agent max_tokens",
                "agents"
            ))
        
        # Check workflow complexity
        for i, workflow in enumerate(config.workflows):
            step_count = len(workflow.steps)
            if step_count > 20:
                self.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    "performance",
                    "workflow_complexity",
                    f"Workflow '{workflow.id}' has many steps ({step_count})",
                    "Consider breaking into smaller workflows",
                    f"workflows[{i}]"
                ))
    
    def _validate_security(self, config: LangSwarmConfig):
        """Validate security considerations"""
        
        # Check for debug settings in production
        if config.observability.log_level == LogLevel.DEBUG:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "security",
                "debug_logging",
                "Debug logging enabled may expose sensitive information",
                "Use INFO or WARNING level in production",
                "observability"
            ))
        
        # Check CORS settings
        if "*" in config.server.cors_origins:
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "security",
                "cors_wildcard",
                "CORS wildcard (*) allows all origins",
                "Specify exact origins in production",
                "server"
            ))
        
        # Check SSL configuration
        if not config.server.ssl_enabled and config.server.host != "localhost":
            self.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "security",
                "ssl_disabled",
                "SSL not enabled for non-localhost server",
                "Enable SSL for production deployments",
                "server"
            ))
        
        # Check memory encryption
        if not config.security.encrypt_memory and config.memory.backend != MemoryBackend.IN_MEMORY:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "security",
                "memory_encryption",
                "Memory encryption disabled for persistent backend",
                "Consider enabling memory encryption for sensitive data",
                "security"
            ))
    
    def _validate_best_practices(self, config: LangSwarmConfig):
        """Validate best practices and recommendations"""
        
        # Check for descriptive names
        for i, agent in enumerate(config.agents):
            if not agent.name or agent.name == agent.id.replace("_", " ").title():
                self.issues.append(ValidationIssue(
                    ValidationSeverity.INFO,
                    "best_practices",
                    "naming",
                    f"Agent '{agent.id}' has generic or missing name",
                    "Use descriptive names for better clarity",
                    f"agents[{i}]"
                ))
        
        # Check for system prompts
        agents_without_prompts = [
            agent for agent in config.agents 
            if not agent.system_prompt or len(agent.system_prompt.strip()) < 10
        ]
        if agents_without_prompts:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "best_practices",
                "system_prompts",
                f"{len(agents_without_prompts)} agents have minimal or missing system prompts",
                "Add detailed system prompts for better agent behavior",
                "agents"
            ))
        
        # Check for tool usage
        agents_without_tools = [agent for agent in config.agents if not agent.tools]
        if agents_without_tools and config.tools:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "best_practices",
                "tool_usage",
                f"{len(agents_without_tools)} agents have no tools configured",
                "Consider adding tools to enhance agent capabilities",
                "agents"
            ))
        
        # Check for workflow documentation
        undocumented_workflows = [
            workflow for workflow in config.workflows 
            if not workflow.description
        ]
        if undocumented_workflows:
            self.issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                "best_practices",
                "documentation",
                f"{len(undocumented_workflows)} workflows have no description",
                "Add descriptions to workflows for better maintainability",
                "workflows"
            ))


def validate_config(config: LangSwarmConfig, strict_mode: bool = True) -> Tuple[bool, List[ValidationIssue]]:
    """
    Convenience function to validate configuration.
    
    Args:
        config: Configuration to validate
        strict_mode: If True, warnings are treated as errors (DEFAULT: True for fail-fast behavior)
        
    Returns:
        Tuple of (is_valid, issues_list)
    """
    validator = ConfigurationValidator(strict_mode)
    return validator.validate(config)


def format_validation_report(issues: List[ValidationIssue]) -> str:
    """
    Format validation issues into a readable report.
    
    Args:
        issues: List of validation issues
        
    Returns:
        Formatted report string
    """
    if not issues:
        return "✅ Configuration validation passed with no issues."
    
    # Group issues by severity
    by_severity = {}
    for issue in issues:
        severity = issue.severity
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(issue)
    
    report_lines = ["📋 Configuration Validation Report", "=" * 50]
    
    # Summary
    total_issues = len(issues)
    error_count = len(by_severity.get(ValidationSeverity.ERROR, []))
    warning_count = len(by_severity.get(ValidationSeverity.WARNING, []))
    info_count = len(by_severity.get(ValidationSeverity.INFO, []))
    
    report_lines.append(f"Total Issues: {total_issues}")
    report_lines.append(f"  ❌ Errors: {error_count}")
    report_lines.append(f"  ⚠️  Warnings: {warning_count}")
    report_lines.append(f"  ℹ️  Info: {info_count}")
    report_lines.append("")
    
    # Details by severity
    severity_order = [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, ValidationSeverity.WARNING, ValidationSeverity.INFO]
    severity_icons = {
        ValidationSeverity.CRITICAL: "🚨",
        ValidationSeverity.ERROR: "❌",
        ValidationSeverity.WARNING: "⚠️",
        ValidationSeverity.INFO: "ℹ️"
    }
    
    for severity in severity_order:
        if severity in by_severity:
            issues_for_severity = by_severity[severity]
            icon = severity_icons[severity]
            report_lines.append(f"{icon} {severity.value.upper()} ({len(issues_for_severity)} issues)")
            report_lines.append("-" * 30)
            
            for issue in issues_for_severity:
                report_lines.append(f"  • {issue.category}.{issue.field}: {issue.message}")
                if issue.section:
                    report_lines.append(f"    Section: {issue.section}")
                if issue.suggestion:
                    report_lines.append(f"    💡 {issue.suggestion}")
                report_lines.append("")
    
    return "\n".join(report_lines)
