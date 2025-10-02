"""
LangSwarm V2 Configuration Utilities

Utility functions for configuration management, comparison, and optimization.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import asdict
import difflib

from .schema import LangSwarmConfig, AgentConfig, ToolConfig, WorkflowConfig


logger = logging.getLogger(__name__)


class ConfigurationComparator:
    """Compare two configurations and generate diff reports"""
    
    def __init__(self):
        self.differences: List[Dict[str, Any]] = []
    
    def compare(self, config1: LangSwarmConfig, config2: LangSwarmConfig) -> Dict[str, Any]:
        """
        Compare two configurations and return detailed differences.
        
        Args:
            config1: First configuration
            config2: Second configuration
            
        Returns:
            Dictionary containing comparison results
        """
        self.differences = []
        
        # Convert to dictionaries for comparison
        dict1 = config1.to_dict()
        dict2 = config2.to_dict()
        
        # Compare major sections
        self._compare_section(dict1.get("agents", []), dict2.get("agents", []), "agents")
        self._compare_section(dict1.get("tools", {}), dict2.get("tools", {}), "tools")
        self._compare_section(dict1.get("workflows", []), dict2.get("workflows", []), "workflows")
        self._compare_section(dict1.get("memory", {}), dict2.get("memory", {}), "memory")
        self._compare_section(dict1.get("security", {}), dict2.get("security", {}), "security")
        self._compare_section(dict1.get("observability", {}), dict2.get("observability", {}), "observability")
        self._compare_section(dict1.get("server", {}), dict2.get("server", {}), "server")
        
        # Generate summary
        summary = {
            "total_differences": len(self.differences),
            "sections_affected": len(set(diff["section"] for diff in self.differences)),
            "major_changes": len([diff for diff in self.differences if diff["type"] in ["added", "removed"]]),
            "modified_changes": len([diff for diff in self.differences if diff["type"] == "modified"]),
            "differences": self.differences
        }
        
        return summary
    
    def _compare_section(self, section1: Any, section2: Any, section_name: str, path: str = ""):
        """Recursively compare configuration sections"""
        current_path = f"{path}.{section_name}" if path else section_name
        
        if type(section1) != type(section2):
            self.differences.append({
                "type": "type_changed",
                "section": section_name,
                "path": current_path,
                "old_type": type(section1).__name__,
                "new_type": type(section2).__name__
            })
            return
        
        if isinstance(section1, dict) and isinstance(section2, dict):
            # Compare dictionary keys
            keys1 = set(section1.keys())
            keys2 = set(section2.keys())
            
            # Added keys
            for key in keys2 - keys1:
                self.differences.append({
                    "type": "added",
                    "section": section_name,
                    "path": f"{current_path}.{key}",
                    "value": section2[key]
                })
            
            # Removed keys
            for key in keys1 - keys2:
                self.differences.append({
                    "type": "removed",
                    "section": section_name,
                    "path": f"{current_path}.{key}",
                    "value": section1[key]
                })
            
            # Modified keys
            for key in keys1 & keys2:
                if section1[key] != section2[key]:
                    if isinstance(section1[key], (dict, list)):
                        self._compare_section(section1[key], section2[key], section_name, f"{current_path}.{key}")
                    else:
                        self.differences.append({
                            "type": "modified",
                            "section": section_name,
                            "path": f"{current_path}.{key}",
                            "old_value": section1[key],
                            "new_value": section2[key]
                        })
        
        elif isinstance(section1, list) and isinstance(section2, list):
            # Compare list contents (simplified)
            if len(section1) != len(section2):
                self.differences.append({
                    "type": "list_size_changed",
                    "section": section_name,
                    "path": current_path,
                    "old_size": len(section1),
                    "new_size": len(section2)
                })
            
            # Compare individual items (by index)
            min_len = min(len(section1), len(section2))
            for i in range(min_len):
                if section1[i] != section2[i]:
                    self._compare_section(section1[i], section2[i], section_name, f"{current_path}[{i}]")
        
        else:
            # Direct value comparison
            if section1 != section2:
                self.differences.append({
                    "type": "modified",
                    "section": section_name,
                    "path": current_path,
                    "old_value": section1,
                    "new_value": section2
                })


class ConfigurationOptimizer:
    """Optimize configurations for better performance and maintainability"""
    
    def optimize(self, config: LangSwarmConfig) -> Dict[str, Any]:
        """
        Analyze configuration and suggest optimizations.
        
        Args:
            config: Configuration to optimize
            
        Returns:
            Dictionary with optimization suggestions
        """
        optimizations = {
            "performance": [],
            "maintainability": [],
            "security": [],
            "cost": []
        }
        
        # Performance optimizations
        self._analyze_performance_optimizations(config, optimizations["performance"])
        
        # Maintainability optimizations
        self._analyze_maintainability_optimizations(config, optimizations["maintainability"])
        
        # Security optimizations
        self._analyze_security_optimizations(config, optimizations["security"])
        
        # Cost optimizations
        self._analyze_cost_optimizations(config, optimizations["cost"])
        
        return optimizations
    
    def _analyze_performance_optimizations(self, config: LangSwarmConfig, suggestions: List[Dict[str, Any]]):
        """Analyze performance optimization opportunities"""
        
        # Check for duplicate models
        model_usage = {}
        for agent in config.agents:
            key = f"{agent.provider.value}:{agent.model}"
            if key not in model_usage:
                model_usage[key] = []
            model_usage[key].append(agent.id)
        
        duplicate_models = {k: v for k, v in model_usage.items() if len(v) > 1}
        if duplicate_models:
            suggestions.append({
                "type": "model_consolidation",
                "description": "Multiple agents use the same model",
                "impact": "Potential for connection pooling and caching",
                "details": duplicate_models
            })
        
        # Check memory configuration
        if config.memory.max_messages > 1000:
            suggestions.append({
                "type": "memory_optimization",
                "description": "High max_messages setting may impact performance",
                "impact": "Reduced memory usage and faster processing",
                "recommendation": "Consider reducing max_messages or enabling auto_summarize"
            })
        
        # Check workflow complexity
        complex_workflows = [
            workflow for workflow in config.workflows 
            if len(workflow.steps) > 10
        ]
        if complex_workflows:
            suggestions.append({
                "type": "workflow_simplification",
                "description": f"{len(complex_workflows)} workflows have many steps",
                "impact": "Faster execution and easier debugging",
                "recommendation": "Break complex workflows into smaller, reusable workflows"
            })
    
    def _analyze_maintainability_optimizations(self, config: LangSwarmConfig, suggestions: List[Dict[str, Any]]):
        """Analyze maintainability optimization opportunities"""
        
        # Check for missing descriptions
        undocumented_items = 0
        undocumented_items += len([a for a in config.agents if not a.name or len(a.name) < 5])
        undocumented_items += len([t for t in config.tools.values() if not t.description])
        undocumented_items += len([w for w in config.workflows if not w.description])
        
        if undocumented_items > 0:
            suggestions.append({
                "type": "documentation",
                "description": f"{undocumented_items} components lack proper documentation",
                "impact": "Better maintainability and team collaboration",
                "recommendation": "Add names, descriptions, and documentation to all components"
            })
        
        # Check for consistent naming
        inconsistent_naming = []
        for agent in config.agents:
            if "_" in agent.id and "-" in agent.id:
                inconsistent_naming.append(f"agent.{agent.id}")
        
        if inconsistent_naming:
            suggestions.append({
                "type": "naming_consistency",
                "description": "Inconsistent naming conventions found",
                "impact": "Better code organization and readability",
                "details": inconsistent_naming[:5]  # Show first 5
            })
    
    def _analyze_security_optimizations(self, config: LangSwarmConfig, suggestions: List[Dict[str, Any]]):
        """Analyze security optimization opportunities"""
        
        # Check for plaintext secrets
        if config.observability.log_level.value in ["DEBUG", "TRACE"]:
            suggestions.append({
                "type": "logging_security",
                "description": "Debug logging may expose sensitive information",
                "impact": "Reduced security risk",
                "recommendation": "Use INFO level logging in production"
            })
        
        # Check CORS configuration
        if "*" in config.server.cors_origins:
            suggestions.append({
                "type": "cors_security",
                "description": "Wildcard CORS allows all origins",
                "impact": "Improved security against CSRF attacks",
                "recommendation": "Specify exact allowed origins"
            })
        
        # Check SSL configuration
        if not config.server.ssl_enabled and config.server.host != "localhost":
            suggestions.append({
                "type": "ssl_security",
                "description": "SSL not enabled for public server",
                "impact": "Encrypted communication",
                "recommendation": "Enable SSL with proper certificates"
            })
    
    def _analyze_cost_optimizations(self, config: LangSwarmConfig, suggestions: List[Dict[str, Any]]):
        """Analyze cost optimization opportunities"""
        
        # Check for expensive models
        expensive_models = ["gpt-4", "claude-3-opus-20240229", "gemini-1.5-pro"]
        expensive_agents = [
            agent for agent in config.agents 
            if any(expensive in agent.model.lower() for expensive in expensive_models)
        ]
        
        if expensive_agents:
            suggestions.append({
                "type": "model_cost",
                "description": f"{len(expensive_agents)} agents use expensive models",
                "impact": "Reduced API costs",
                "recommendation": "Consider using more cost-effective models for non-critical tasks",
                "details": [agent.id for agent in expensive_agents]
            })
        
        # Check max_tokens settings
        high_token_agents = [
            agent for agent in config.agents 
            if agent.max_tokens and agent.max_tokens > 4000
        ]
        
        if high_token_agents:
            suggestions.append({
                "type": "token_optimization",
                "description": f"{len(high_token_agents)} agents have high max_tokens",
                "impact": "Reduced token usage costs",
                "recommendation": "Review if high token limits are necessary",
                "details": [f"{agent.id}: {agent.max_tokens}" for agent in high_token_agents]
            })


class ConfigurationMerger:
    """Merge multiple configurations intelligently"""
    
    def merge(self, base_config: LangSwarmConfig, *override_configs: LangSwarmConfig) -> LangSwarmConfig:
        """
        Merge multiple configurations with intelligent conflict resolution.
        
        Args:
            base_config: Base configuration
            *override_configs: Override configurations (applied in order)
            
        Returns:
            Merged configuration
        """
        # Start with base configuration
        merged_dict = base_config.to_dict()
        
        # Apply each override
        for override_config in override_configs:
            override_dict = override_config.to_dict()
            merged_dict = self._deep_merge(merged_dict, override_dict)
        
        # Create merged configuration
        return LangSwarmConfig.from_dict(merged_dict)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge dictionaries with intelligent list handling"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # For agents and workflows, merge by ID
                    if key in ["agents", "workflows"]:
                        result[key] = self._merge_lists_by_id(result[key], value)
                    elif key == "tools":
                        # Tools are dictionaries, merge normally
                        result[key] = self._deep_merge(result[key], value)
                    else:
                        # For other lists, append unique items
                        existing_items = set(str(item) for item in result[key])
                        for item in value:
                            if str(item) not in existing_items:
                                result[key].append(item)
                else:
                    # Override with new value
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _merge_lists_by_id(self, base_list: List[Dict[str, Any]], override_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge lists of objects by ID field"""
        result = base_list.copy()
        base_ids = {item.get("id") for item in base_list if "id" in item}
        
        for override_item in override_list:
            item_id = override_item.get("id")
            if item_id in base_ids:
                # Update existing item
                for i, base_item in enumerate(result):
                    if base_item.get("id") == item_id:
                        result[i] = self._deep_merge(base_item, override_item)
                        break
            else:
                # Add new item
                result.append(override_item)
        
        return result


def export_config_template(config: LangSwarmConfig, output_path: str, include_comments: bool = True):
    """
    Export configuration as a template with comments.
    
    Args:
        config: Configuration to export
        output_path: Output file path
        include_comments: Whether to include explanatory comments
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    config_dict = config.to_dict()
    
    # Generate YAML with comments
    lines = []
    if include_comments:
        lines.extend([
            "# LangSwarm V2 Configuration Template",
            "# Generated from existing configuration",
            "",
            "# Configuration version (required)",
        ])
    
    # Convert to YAML string
    yaml_content = yaml.dump(config_dict, default_flow_style=False, indent=2, sort_keys=False)
    
    if include_comments:
        # Add section comments
        yaml_lines = yaml_content.split('\n')
        commented_lines = []
        
        for line in yaml_lines:
            if line.strip() and not line.startswith(' ') and ':' in line:
                section = line.split(':')[0].strip()
                if section in ['agents', 'tools', 'workflows', 'memory', 'security', 'observability', 'server']:
                    commented_lines.append(f"\n# {section.title()} configuration")
            commented_lines.append(line)
        
        yaml_content = '\n'.join(commented_lines)
    
    with open(output_file, 'w') as f:
        if include_comments:
            f.write('\n'.join(lines) + '\n')
        f.write(yaml_content)
    
    logger.info(f"Configuration template exported to: {output_file}")


def generate_config_diff(config1: LangSwarmConfig, config2: LangSwarmConfig, output_path: Optional[str] = None) -> str:
    """
    Generate a human-readable diff between two configurations.
    
    Args:
        config1: First configuration
        config2: Second configuration
        output_path: Optional file to save diff
        
    Returns:
        Diff string
    """
    # Convert to YAML for better readability
    yaml1 = yaml.dump(config1.to_dict(), default_flow_style=False, indent=2)
    yaml2 = yaml.dump(config2.to_dict(), default_flow_style=False, indent=2)
    
    # Generate diff
    diff = difflib.unified_diff(
        yaml1.splitlines(keepends=True),
        yaml2.splitlines(keepends=True),
        fromfile="config1.yaml",
        tofile="config2.yaml",
        lineterm=""
    )
    
    diff_content = ''.join(diff)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(diff_content)
        logger.info(f"Configuration diff saved to: {output_path}")
    
    return diff_content


def validate_config_environment(config: LangSwarmConfig) -> Dict[str, Any]:
    """
    Validate that the environment is properly configured for the given configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Environment validation results
    """
    results = {
        "valid": True,
        "missing_env_vars": [],
        "missing_dependencies": [],
        "warnings": []
    }
    
    # Check required environment variables
    providers_used = {agent.provider for agent in config.agents}
    
    env_var_map = {
        "openai": config.security.openai_api_key_env,
        "anthropic": config.security.anthropic_api_key_env,
        "gemini": config.security.gemini_api_key_env,
        "cohere": config.security.cohere_api_key_env,
    }
    
    for provider in providers_used:
        if provider.value in env_var_map:
            env_var = env_var_map[provider.value]
            if not os.getenv(env_var):
                results["missing_env_vars"].append(env_var)
                results["valid"] = False
    
    # Check memory backend requirements
    if config.memory.backend.value == "redis":
        # Check if Redis is accessible (simplified check)
        redis_url = config.memory.config.get("url", "redis://localhost:6379")
        if "localhost" in redis_url:
            results["warnings"].append("Redis backend requires local Redis server")
    
    # Check file permissions for SQLite
    if config.memory.backend.value == "sqlite":
        db_path = config.memory.config.get("db_path", "langswarm.db")
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if not os.access(db_dir, os.W_OK):
            results["warnings"].append(f"No write permission for directory: {db_dir}")
    
    return results
