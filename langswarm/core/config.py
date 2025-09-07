# ToDo: Add field validation!

import os
import re
import ast
import sys
import time
import json
import yaml
import socket
import asyncio
import inspect
import tempfile
import importlib
import subprocess
import numpy as np
import pandas as pd
import nest_asyncio
from pathlib import Path
from jinja2 import Template
from cerberus import Validator
from simpleeval import SimpleEval
from inspect import signature, Parameter
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field

# Enhanced error handling imports
try:
    from langswarm.core.errors import (
        ConfigurationNotFoundError, 
        InvalidAgentBehaviorError,
        UnknownToolError,
        WorkflowNotFoundError,
        InvalidWorkflowSyntaxError,
        InvalidMemoryTierError,
        ZeroConfigDependencyError,
        AgentToolError,
        create_helpful_error,
        format_validation_errors
    )
except ImportError:
    # Fallback to standard errors if enhanced errors module not available
    ConfigurationNotFoundError = FileNotFoundError
    InvalidAgentBehaviorError = ValueError
    UnknownToolError = ValueError
    WorkflowNotFoundError = ValueError
    InvalidWorkflowSyntaxError = ValueError
    InvalidMemoryTierError = ValueError
    ZeroConfigDependencyError = RuntimeError
    AgentToolError = RuntimeError
    create_helpful_error = lambda error_type, **kwargs: Exception(f"{error_type}: {kwargs}")
    format_validation_errors = lambda errors: f"Validation errors: {errors}"

# @v0.0.1
# AgentFactory import moved to lazy loading to prevent circular imports
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
from langswarm.core.utils.subutilities.formatting import Formatting

# @v... Later...

#from langswarm.memory.adapters.langswarm import ChromaDBAdapter
#from langswarm.cortex.plugins.process_toolkit import ProcessToolkit

#from langswarm.cortex.react.agent import ReActAgent
#from langswarm.core.defaults.prompts.system import FormatParseableJSON

#from langswarm.synapse.tools.github.main import GitHubTool,ToolSettings
#from langswarm.synapse.tools.files.main import FilesystemTool
#from langswarm.synapse.tools.tasklist.main import TaskListTool


try:
    from langswarm.cortex.registry.plugins import PluginRegistry
except ImportError:
    PluginRegistry = {}

try:
    from langswarm.synapse.registry.tools import ToolRegistry
except ImportError:
    ToolRegistry = {}

try:
    from langswarm.memory.registry.rags import RAGRegistry
except ImportError:
    RAGRegistry = {}

# Zero-config imports
try:
    from .detection import EnvironmentDetector, auto_discover_tools, detect_available_tools
    from .defaults import SmartDefaults
    ZERO_CONFIG_AVAILABLE = True
    import logging
    logging.info("✅ Zero-config functionality available")
except ImportError as e:
    ZERO_CONFIG_AVAILABLE = False
    import logging
    logging.warning(f"Zero-config functionality not available: {e}. Install required dependencies: psutil, requests")


# ===== UNIFIED CONFIGURATION SCHEMA =====
# New unified configuration schema for single-file configuration support

@dataclass
class LangSwarmCoreConfig:
    """Core LangSwarm framework settings"""
    debug: bool = False
    log_level: str = "INFO"
    config_validation: bool = True
    
@dataclass
class AgentConfig:
    """Unified agent configuration"""
    id: str
    name: Optional[str] = None
    model: str = "gpt-4o"
    behavior: Optional[str] = None  # New simplified behavior system
    system_prompt: Optional[str] = None
    agent_type: str = "generic"
    tools: List[str] = field(default_factory=list)
    memory: Union[bool, Dict[str, Any]] = False
    streaming: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    top_p: Optional[float] = None
    response_format: Optional[str] = None
    
@dataclass
class ToolConfig:
    """Unified tool configuration"""
    id: Optional[str] = None
    type: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    auto_configure: bool = False
    local_mode: bool = True
    
@dataclass
class WorkflowConfig:
    """Unified workflow configuration with Workflow Simplification support"""
    id: str
    name: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    @staticmethod
    def from_simple_syntax(workflow_id: str, simple_syntax: str, available_agents: List[str] = None) -> 'WorkflowConfig':
        """
        Workflow Simplification: Create complex workflow from simple syntax
        
        Supported patterns:
        - "assistant -> user" (simple agent to user)
        - "extractor -> summarizer -> user" (chained agents)
        - "analyzer -> reviewer -> formatter -> user" (multi-step chain)
        - "agent1, agent2 -> consensus -> user" (parallel then merge)
        - "router -> (specialist1 | specialist2) -> user" (conditional routing)
        
        Args:
            workflow_id: Unique workflow identifier
            simple_syntax: Simple workflow syntax string
            available_agents: List of available agent IDs for validation
            
        Returns:
            Full WorkflowConfig with generated steps
        """
        available_agents = available_agents or []
        
        # Parse the simple syntax
        steps = WorkflowConfig._parse_simple_syntax(simple_syntax, available_agents)
        
        return WorkflowConfig(
            id=workflow_id,
            name=f"Generated from: {simple_syntax}",
            steps=steps
        )
    
    @staticmethod
    def _parse_simple_syntax(syntax: str, available_agents: List[str]) -> List[Dict[str, Any]]:
        """Parse simple workflow syntax into complex step definitions"""
        syntax = syntax.strip()
        
        # Handle different workflow patterns
        if " -> " in syntax:
            return WorkflowConfig._parse_linear_workflow(syntax, available_agents)
        elif " | " in syntax:
            return WorkflowConfig._parse_conditional_workflow(syntax, available_agents)
        elif ", " in syntax:
            return WorkflowConfig._parse_parallel_workflow(syntax, available_agents)
        else:
            # Single agent workflow
            return WorkflowConfig._parse_single_agent_workflow(syntax, available_agents)
    
    @staticmethod
    def _parse_linear_workflow(syntax: str, available_agents: List[str]) -> List[Dict[str, Any]]:
        """Parse linear workflow: agent1 -> agent2 -> user"""
        parts = [part.strip() for part in syntax.split(" -> ")]
        steps = []
        
        for i, part in enumerate(parts):
            step_id = f"step_{i+1}_{part.replace(' ', '_')}"
            
            if part == "user":
                # Final step - output to user
                if i > 0:
                    # Previous step should output to user
                    steps[-1]["output"] = {"to": "user"}
                break
            
            # Check if this is a known agent
            if part in available_agents:
                # Agent step
                step = {
                    "id": step_id,
                    "agent": part,
                    "input": "${context.user_input}" if i == 0 else f"${{context.step_outputs.{steps[i-1]['id']}}}",
                }
                
                # Add output routing (except for last step before user)
                if i < len(parts) - 2:  # Not the last agent step
                    next_step_id = f"step_{i+2}_{parts[i+1].replace(' ', '_')}"
                    step["output"] = {"to": next_step_id}
                
                steps.append(step)
            else:
                # Unknown agent - create a placeholder or tool call
                step = {
                    "id": step_id,
                    "function": "langswarm.core.utils.workflows.functions.custom_function",
                    "args": {
                        "operation": part,
                        "input": "${context.user_input}" if i == 0 else f"${{context.step_outputs.{steps[i-1]['id']}}}"
                    }
                }
                
                if i < len(parts) - 2:
                    next_step_id = f"step_{i+2}_{parts[i+1].replace(' ', '_')}"
                    step["output"] = {"to": next_step_id}
                
                steps.append(step)
        
        return steps
    
    @staticmethod
    def _parse_conditional_workflow(syntax: str, available_agents: List[str]) -> List[Dict[str, Any]]:
        """Parse conditional workflow: router -> (agent1 | agent2) -> user"""
        # For now, implement as a simple router step
        # TODO: Implement full conditional logic
        
        parts = syntax.split(" -> ")
        router_part = parts[0].strip()
        
        if "(" in syntax and "|" in syntax:
            # Extract conditional agents
            condition_part = syntax[syntax.find("(")+1:syntax.find(")")]
            agents = [agent.strip() for agent in condition_part.split(" | ")]
            
            steps = [
                {
                    "id": "routing_decision",
                    "agent": router_part if router_part in available_agents else "routing_agent",
                    "input": "${context.user_input}",
                    "output": {"to": "conditional_execution"}
                },
                {
                    "id": "conditional_execution", 
                    "function": "langswarm.core.utils.workflows.functions.conditional_router",
                    "args": {
                        "available_agents": agents,
                        "routing_input": "${context.step_outputs.routing_decision}"
                    },
                    "output": {"to": "user"}
                }
            ]
            return steps
        
        # Fallback to linear parsing
        return WorkflowConfig._parse_linear_workflow(syntax, available_agents)
    
    @staticmethod
    def _parse_parallel_workflow(syntax: str, available_agents: List[str]) -> List[Dict[str, Any]]:
        """Parse parallel workflow: agent1, agent2 -> consensus -> user"""
        if " -> " in syntax:
            parts = syntax.split(" -> ")
            parallel_part = parts[0].strip()
            rest = " -> ".join(parts[1:])
            
            if ", " in parallel_part:
                parallel_agents = [agent.strip() for agent in parallel_part.split(", ")]
                
                # Create fan-out steps
                fan_out_steps = []
                for i, agent in enumerate(parallel_agents):
                    step = {
                        "id": f"parallel_{i+1}_{agent.replace(' ', '_')}",
                        "agent": agent if agent in available_agents else "parallel_agent",
                        "input": "${context.user_input}",
                        "async": True,
                        "fan_key": "parallel_execution"
                    }
                    fan_out_steps.append(step)
                
                # Create consensus/merger step
                consensus_steps = WorkflowConfig._parse_linear_workflow(rest, available_agents)
                if consensus_steps:
                    consensus_steps[0]["input"] = "${context.parallel_outputs}"
                    consensus_steps[0]["is_fan_in"] = True
                    consensus_steps[0]["fan_key"] = "parallel_execution"
                
                return fan_out_steps + consensus_steps
        
        # Fallback to linear parsing
        return WorkflowConfig._parse_linear_workflow(syntax, available_agents)
    
    @staticmethod
    def _parse_single_agent_workflow(syntax: str, available_agents: List[str]) -> List[Dict[str, Any]]:
        """Parse single agent workflow: just agent name"""
        agent_name = syntax.strip()
        
        return [{
            "id": f"single_step_{agent_name.replace(' ', '_')}",
            "agent": agent_name if agent_name in available_agents else "default_agent",
            "input": "${context.user_input}",
            "output": {"to": "user"}
        }]
    
    @staticmethod
    def get_workflow_templates() -> Dict[str, str]:
        """Get common workflow templates for easy copy-paste"""
        return {
            "simple_chat": "assistant -> user",
            "analyze_and_respond": "analyzer -> responder -> user", 
            "extract_and_summarize": "extractor -> summarizer -> user",
            "review_process": "drafter -> reviewer -> editor -> user",
            "research_workflow": "researcher -> analyzer -> summarizer -> user",
            "consensus_building": "expert1, expert2, expert3 -> consensus -> user",
            "routing_workflow": "router -> (specialist1 | specialist2) -> user",
            "quality_assurance": "processor -> validator -> formatter -> user",
            "multi_step_analysis": "collector -> processor -> analyzer -> reporter -> user",
            "collaborative_writing": "writer -> editor -> proofreader -> user"
        }
    
    def to_simple_syntax(self) -> Optional[str]:
        """Convert complex workflow back to simple syntax (if possible)"""
        if not self.steps:
            return None
        
        # Try to detect linear workflow pattern
        if len(self.steps) >= 2:
            agents = []
            
            for step in self.steps:
                if "agent" in step:
                    agents.append(step["agent"])
                elif "function" in step:
                    # Extract operation name from function step
                    if "args" in step and "operation" in step["args"]:
                        agents.append(step["args"]["operation"])
                    else:
                        agents.append("custom_function")
            
            # Check if it ends with user output
            if self.steps[-1].get("output", {}).get("to") == "user":
                agents.append("user")
            
            return " -> ".join(agents)
        
        return None
    
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Get workflow complexity metrics for optimization suggestions"""
        if not self.steps:
            return {"complexity": "empty", "steps": 0, "suggestions": ["Add workflow steps"]}
        
        step_count = len(self.steps)
        has_parallel = any(step.get("async") or step.get("fan_key") for step in self.steps)
        has_conditions = any("condition" in str(step) for step in self.steps)
        agent_count = len(set(step.get("agent") for step in self.steps if step.get("agent")))
        
        # Determine complexity level
        if step_count <= 2 and not has_parallel and not has_conditions:
            complexity = "simple"
            suggestions = ["Consider using simple syntax: 'agent -> user'"]
        elif step_count <= 5 and not has_parallel:
            complexity = "moderate"
            suggestions = ["Consider using simple syntax: 'agent1 -> agent2 -> user'"]
        elif has_parallel and not has_conditions:
            complexity = "parallel"
            suggestions = ["Consider using parallel syntax: 'agent1, agent2 -> consensus -> user'"]
        else:
            complexity = "complex"
            suggestions = ["Complex workflow - manual YAML configuration recommended"]
        
        return {
            "complexity": complexity,
            "steps": step_count,
            "agents": agent_count,
            "has_parallel": has_parallel,
            "has_conditions": has_conditions,
            "suggestions": suggestions,
            "simple_syntax": self.to_simple_syntax()
        }
    
@dataclass
class MemoryConfig:
    """Unified memory configuration with Memory Made Simple support"""
    enabled: bool = False
    backend: str = "auto"  # auto, sqlite, redis, chromadb, etc.
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # MemoryPro configuration for Pro features
    memorypro_enabled: bool = False
    memorypro_mode: str = "internal"  # internal, external
    memorypro_api_url: Optional[str] = None
    memorypro_api_key: Optional[str] = None
    memorypro_api_secret: Optional[str] = None
    memorypro_webhook_url: Optional[str] = None
    memorypro_webhook_secret: Optional[str] = None
    
    def get_memorypro_config(self) -> Dict[str, Any]:
        """Get MemoryPro configuration with environment variable fallbacks"""
        import os
        
        return {
            "enabled": self.memorypro_enabled or os.getenv("MEMORYPRO_ENABLED", "false").lower() == "true",
            "mode": self.memorypro_mode or os.getenv("MEMORYPRO_MODE", "internal"),
            "api_url": self.memorypro_api_url or os.getenv("MEMORYPRO_API_URL"),
            "api_key": self.memorypro_api_key or os.getenv("MEMORYPRO_API_KEY"),
            "api_secret": self.memorypro_api_secret or os.getenv("MEMORYPRO_API_SECRET"),
            "webhook_url": self.memorypro_webhook_url or os.getenv("MEMORYPRO_WEBHOOK_URL"),
            "webhook_secret": self.memorypro_webhook_secret or os.getenv("MEMORYPRO_WEBHOOK_SECRET")
        }
    
    def is_external_memorypro(self) -> bool:
        """Check if external MemoryPro mode is enabled and configured"""
        config = self.get_memorypro_config()
        return (
            config["enabled"] and 
            config["mode"] == "external" and 
            config["api_url"] and 
            config["api_key"] and 
            config["api_secret"]
        )
    
    @staticmethod
    def setup_memory(config_input: Union[bool, str, Dict[str, Any]]) -> 'MemoryConfig':
        """
        Memory Made Simple: Create memory configuration from simplified inputs
        
        Three tiers of complexity:
        1. memory: true → auto-select SQLite for development
        2. memory: "production" → auto-select appropriate production backend
        3. memory: {backend: custom, config: {...}} → full control
        
        Args:
            config_input: Simple memory configuration input
            
        Returns:
            Fully configured MemoryConfig object
        """
        import os
        
        # Tier 1: memory: true (or false)
        if isinstance(config_input, bool):
            if not config_input:
                return MemoryConfig(enabled=False)
            
            return MemoryConfig(
                enabled=True,
                backend="sqlite",
                settings={
                    "db_path": os.path.join(os.getcwd(), "langswarm_memory.db"),
                    "max_memory_size": "100MB",
                    "persistence": True,
                    "description": "Development SQLite database"
                }
            )
        
        # Tier 2: memory: "production" (or other environment strings)
        if isinstance(config_input, str):
            env_type = config_input.lower()
            
            if env_type == "production":
                # Smart production backend selection
                backend, settings = MemoryConfig._select_production_backend()
                return MemoryConfig(
                    enabled=True,
                    backend=backend,
                    settings=settings
                )
            
            elif env_type in ["development", "dev", "local"]:
                # Enhanced development setup
                return MemoryConfig(
                    enabled=True,
                    backend="sqlite",
                    settings={
                        "db_path": os.path.join(os.getcwd(), "langswarm_dev_memory.db"),
                        "max_memory_size": "200MB",
                        "persistence": True,
                        "vacuum_interval": "1h",
                        "description": "Enhanced development SQLite database"
                    }
                )
            
            elif env_type in ["testing", "test"]:
                # Testing environment with in-memory database
                return MemoryConfig(
                    enabled=True,
                    backend="sqlite",
                    settings={
                        "db_path": ":memory:",
                        "max_memory_size": "50MB",
                        "persistence": False,
                        "description": "Testing in-memory database"
                    }
                )
            
            elif env_type == "cloud":
                # Cloud-optimized configuration
                backend, settings = MemoryConfig._select_cloud_backend()
                return MemoryConfig(
                    enabled=True,
                    backend=backend,
                    settings=settings
                )
            
            else:
                # Unknown string, fall back to auto with the string as backend hint
                return MemoryConfig(
                    enabled=True,
                    backend=env_type,
                    settings={"description": f"Custom {env_type} backend"}
                )
        
        # Tier 3: memory: {backend: custom, config: {...}} (full control)
        if isinstance(config_input, dict):
            return MemoryConfig(
                enabled=config_input.get("enabled", True),
                backend=config_input.get("backend", "auto"),
                settings=config_input.get("settings", {}),
                memorypro_enabled=config_input.get("memorypro_enabled", False),
                memorypro_mode=config_input.get("memorypro_mode", "internal"),
                memorypro_api_url=config_input.get("memorypro_api_url"),
                memorypro_api_key=config_input.get("memorypro_api_key"),
                memorypro_api_secret=config_input.get("memorypro_api_secret"),
                memorypro_webhook_url=config_input.get("memorypro_webhook_url"),
                memorypro_webhook_secret=config_input.get("memorypro_webhook_secret")
            )
        
        # Fallback: disable memory for unknown types
        return MemoryConfig(enabled=False)
    
    @staticmethod
    def _select_production_backend() -> tuple[str, Dict[str, Any]]:
        """Select optimal production memory backend based on available services"""
        import os
        
        # Check for cloud provider environment variables
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CLOUD_PROJECT"):
            # Google Cloud environment - use BigQuery for analytics
            return "bigquery", {
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "langswarm-prod"),
                "dataset_id": "langswarm_memory",
                "table_id": "agent_conversations",
                "location": "US",
                "max_memory_size": "10GB",
                "retention_days": 365,
                "description": "Production BigQuery analytics backend"
            }
        
        elif os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_DEFAULT_REGION"):
            # AWS environment - use Elasticsearch for search and analytics
            return "elasticsearch", {
                "index_name": "langswarm_memory",
                "max_memory_size": "5GB",
                "retention_days": 90,
                "replicas": 1,
                "shards": 2,
                "description": "Production Elasticsearch backend"
            }
        
        elif os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
            # Redis available - use for fast access
            redis_url = os.getenv("REDIS_URL") or f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379"
            return "redis", {
                "redis_url": redis_url,
                "max_memory_size": "1GB",
                "persistence": True,
                "ttl": 2592000,  # 30 days
                "description": "Production Redis backend"
            }
        
        else:
            # Fallback to ChromaDB for vector search in production
            return "chromadb", {
                "persist_directory": "/var/lib/langswarm/memory",
                "collection_name": "langswarm_production",
                "max_memory_size": "2GB",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "description": "Production ChromaDB vector backend"
            }
    
    @staticmethod
    def _select_cloud_backend() -> tuple[str, Dict[str, Any]]:
        """Select optimal cloud memory backend for distributed deployments"""
        import os
        
        # Prioritize cloud-native solutions
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return "bigquery", {
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "langswarm-cloud"),
                "dataset_id": "langswarm_memory",
                "table_id": "distributed_conversations",
                "location": "US",
                "max_memory_size": "100GB",
                "partitioning": "timestamp",
                "description": "Cloud BigQuery distributed backend"
            }
        
        elif os.getenv("AWS_ACCESS_KEY_ID"):
            return "elasticsearch", {
                "cloud_id": os.getenv("ELASTICSEARCH_CLOUD_ID"),
                "api_key": os.getenv("ELASTICSEARCH_API_KEY"),
                "index_name": "langswarm_cloud",
                "max_memory_size": "50GB",
                "description": "Cloud Elasticsearch distributed backend"
            }
        
        else:
            # Fallback to Qdrant for cloud vector search
            return "qdrant", {
                "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
                "collection_name": "langswarm_cloud",
                "vector_size": 384,
                "max_memory_size": "10GB",
                "description": "Cloud Qdrant vector backend"
            }
    
    def get_tier_description(self) -> str:
        """Get a human-readable description of the memory configuration tier"""
        if not self.enabled:
            return "Tier 0: Memory disabled"
        
        backend_descriptions = {
            "sqlite": "Tier 1: Simple SQLite (Development)",
            "chromadb": "Tier 2: ChromaDB Vector Search (Production)",
            "redis": "Tier 2: Redis Fast Access (Production)",
            "bigquery": "Tier 3: BigQuery Analytics (Cloud)",
            "elasticsearch": "Tier 3: Elasticsearch Search (Cloud)",
            "qdrant": "Tier 3: Qdrant Vector (Cloud)"
        }
        
        description = backend_descriptions.get(self.backend, f"Custom: {self.backend}")
        settings_desc = self.settings.get("description", "")
        
        if settings_desc:
            return f"{description} - {settings_desc}"
        return description
    
@dataclass
class BrokerConfig:
    """Message broker configuration"""
    id: str
    type: str = "internal"
    settings: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class AdvancedConfig:
    """Advanced configuration for complex setups"""
    brokers: List[BrokerConfig] = field(default_factory=list)
    queues: List[Dict[str, Any]] = field(default_factory=list)
    registries: List[Dict[str, Any]] = field(default_factory=list)
    plugins: List[Dict[str, Any]] = field(default_factory=list)
    retrievers: List[Dict[str, Any]] = field(default_factory=list)
    
@dataclass
class ValidationError:
    """Configuration validation error"""
    field: str
    message: str
    section: Optional[str] = None
    
@dataclass
class LangSwarmConfig:
    """Unified configuration schema for LangSwarm"""
    version: str = "1.0"
    project_name: Optional[str] = None
    langswarm: LangSwarmCoreConfig = field(default_factory=LangSwarmCoreConfig)
    agents: List[AgentConfig] = field(default_factory=list)
    tools: Dict[str, ToolConfig] = field(default_factory=dict)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    
    # Include directive for advanced users who want to split configs
    include: Optional[List[str]] = None
    
    def validate(self) -> List[ValidationError]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Validate agents
        agent_ids = set()
        for agent in self.agents:
            if agent.id in agent_ids:
                errors.append(ValidationError("id", f"Duplicate agent ID: {agent.id}", "agents"))
            agent_ids.add(agent.id)
            
            # Validate tools exist
            for tool_id in agent.tools:
                if tool_id not in self.tools:
                    errors.append(ValidationError("tools", f"Agent {agent.id} references unknown tool: {tool_id}", "agents"))
        
        # Validate workflows reference existing agents
        for workflow in self.workflows:
            for step in workflow.steps:
                if "agent" in step and step["agent"] not in agent_ids:
                    errors.append(ValidationError("agent", f"Workflow {workflow.id} references unknown agent: {step['agent']}", "workflows"))
        
        return errors
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert unified config to legacy multi-file format for backward compatibility"""
        legacy_config = {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "model": agent.model,
                    "agent_type": agent.agent_type,
                    "system_prompt": agent.system_prompt,
                    "tools": agent.tools,
                    "max_tokens": agent.max_tokens,
                    "temperature": agent.temperature,
                    "response_format": agent.response_format,
                } for agent in self.agents
            ],
            "tools": [
                {
                    "id": tool_id,
                    "type": tool_config.type,
                    "settings": tool_config.settings,
                } for tool_id, tool_config in self.tools.items()
            ],
            "workflows": [
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "steps": workflow.steps,
                } for workflow in self.workflows
            ],
            "brokers": [
                {
                    "id": broker.id,
                    "type": broker.type,
                    "settings": broker.settings,
                } for broker in self.advanced.brokers
            ],
            "queues": self.advanced.queues,
            "registries": self.advanced.registries,
            "plugins": self.advanced.plugins,
            "retrievers": self.advanced.retrievers,
        }
        return legacy_config

# ===== END UNIFIED CONFIGURATION SCHEMA =====


LS_DEFAULT_CONFIG_FILES = [
    "agents.yaml", "tools.yaml", "retrievers.yaml", "plugins.yaml",
    "registries.yaml", "workflows.yaml", "secrets.yaml", "brokers.yaml"
]

LS_SCHEMAS = {
    "agents": {
        "id": {"type": "string", "required": True},
        "agent_type": {"type": "string", "required": True},
        "model": {"type": "string", "required": True},
        "system_prompt": {"type": "string"},
    },
    "tools": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "retrievers": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "plugins": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "workflows": {
        "id": {"type": "string", "required": True},
        "steps": {"type": "list", "required": True},
    },
}

class LangSwarmConfigLoader:
    def __init__(self, config_path="."):
        self.config_path = config_path
        self.config_data = {}
        self.agents = {}
        self.retrievers = {}
        self.tools = {}
        self.tools_metadata = {}
        self.plugins = {}
        self.brokers = {}
        # this will hold type_name → class mappings
        self.tool_classes: Dict[str, type] = {}
        self._load_builtin_tool_classes()
        
        # For unified configuration
        self.unified_config: Optional[LangSwarmConfig] = None
        self.is_unified = False
        
        # Zero-config components (lazy-loaded)
        self.environment_detector = None
        self.capabilities = None
        self.smart_defaults = None

    def _load_builtin_tool_classes(self):
        """Load builtin MCP tool classes"""
        # Import MCP tool wrapper classes
        from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool
        from langswarm.mcp.tools.mcpgithubtool.main import MCPGitHubTool
        from langswarm.mcp.tools.dynamic_forms.main import DynamicFormsMCPTool
        from langswarm.mcp.tools.remote.main import RemoteMCPTool
        from langswarm.mcp.tools.tasklist.main import TasklistMCPTool
        from langswarm.mcp.tools.message_queue_publisher.main import MessageQueuePublisherMCPTool
        from langswarm.mcp.tools.message_queue_consumer.main import MessageQueueConsumerMCPTool
        from langswarm.mcp.tools.gcp_environment.main import GCPEnvironmentMCPTool
        from langswarm.mcp.tools.codebase_indexer.main import CodebaseIndexerMCPTool
        from langswarm.mcp.tools.workflow_executor.main import WorkflowExecutorMCPTool
        
        # Import BigQuery Vector Search tool (with graceful fallback)
        try:
            from langswarm.mcp.tools.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
            BIGQUERY_TOOL_AVAILABLE = True
        except ImportError as e:
            BigQueryVectorSearchMCPTool = None
            BIGQUERY_TOOL_AVAILABLE = False
            import logging
            logging.warning(f"BigQuery Vector Search tool not available: {e}. Install google-cloud-bigquery to enable.")
        
        # Import Daytona tools (with graceful fallback)
        try:
            from langswarm.mcp.tools.daytona_environment.main import DaytonaEnvironmentMCPTool
            DAYTONA_CLOUD_AVAILABLE = True
        except ImportError as e:
            DaytonaEnvironmentMCPTool = None
            DAYTONA_CLOUD_AVAILABLE = False
            import logging
            logging.warning(f"Daytona Environment tool not available: {e}. Install daytona SDK to enable cloud integration.")
        
        try:
            from langswarm.mcp.tools.daytona_self_hosted.main import SelfHostedDaytonaManager
            # Create a tool class wrapper for self-hosted (since it doesn't follow the same pattern)
            class DaytonaSelfHostedMCPTool:
                def __init__(self, identifier: str, **kwargs):
                    self.identifier = identifier
                    self.manager = SelfHostedDaytonaManager()
                    
            DAYTONA_SELF_HOSTED_AVAILABLE = True
        except ImportError as e:
            DaytonaSelfHostedMCPTool = None
            DAYTONA_SELF_HOSTED_AVAILABLE = False
            import logging
            logging.warning(f"Daytona Self-Hosted tool not available: {e}. Ensure Daytona CLI is installed for self-hosted integration.")
        
        self.tool_classes = {
            "mcpfilesystem": FilesystemMCPTool,
            "mcpgithubtool": MCPGitHubTool,
            "mcpforms": DynamicFormsMCPTool,
            "mcpremote": RemoteMCPTool,
            "mcptasklist": TasklistMCPTool,
            "mcpmessage_queue_publisher": MessageQueuePublisherMCPTool,
            "mcpmessage_queue_consumer": MessageQueueConsumerMCPTool,
            "mcpcodebase_indexer": CodebaseIndexerMCPTool,
            "mcpworkflow_executor": WorkflowExecutorMCPTool,
            "mcpgcp_environment": GCPEnvironmentMCPTool,
            # add more here (or via register_tool_class below)
        }
        
        # Add BigQuery tool if available
        if BIGQUERY_TOOL_AVAILABLE:
            self.tool_classes["mcpbigquery_vector_search"] = BigQueryVectorSearchMCPTool
        
        # Add Daytona tools if available
        if DAYTONA_CLOUD_AVAILABLE:
            self.tool_classes["daytona_environment"] = DaytonaEnvironmentMCPTool
            
        if DAYTONA_SELF_HOSTED_AVAILABLE:
            self.tool_classes["daytona_self_hosted"] = DaytonaSelfHostedMCPTool

    def register_tool_class(self, _type: str, cls: type):
        """Allow adding new tool classes at runtime."""
        self.tool_classes[_type.lower()] = cls
    
    def _detect_config_type(self) -> str:
        """Auto-detect configuration approach"""
        # If config_path is a file (not directory), check if it's a unified config
        if os.path.isfile(self.config_path):
            return self.config_path if self._is_file_unified_config(self.config_path) else "multi-file"
        
        # Check for unified configuration file in directory
        unified_candidates = ["langswarm.yaml", "langswarm.yml", "config.yaml", "config.yml"]
        
        for candidate in unified_candidates:
            candidate_path = os.path.join(self.config_path, candidate)
            if os.path.exists(candidate_path) and self._is_file_unified_config(candidate_path):
                return candidate_path
        
        # Check for multi-file configuration
        if os.path.exists(os.path.join(self.config_path, "agents.yaml")):
            return "multi-file"
        
        raise ConfigurationNotFoundError(self.config_path)
    
    def _is_file_unified_config(self, file_path: str) -> bool:
        """Check if a specific file is a unified configuration"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # A unified config typically has:
            # 1. A version field
            # 2. An agents section (which can be a list or contain agents)
            # 3. Does NOT have the structure of legacy multi-file configs
            
            has_version = "version" in data
            has_agents = "agents" in data
            
            # Check if it looks like a legacy agents.yaml (which would have agents but no version)
            if has_agents and not has_version:
                # Could be legacy agents.yaml - check if agents is a simple list of agent dicts
                agents = data.get("agents", [])
                if isinstance(agents, list) and len(agents) > 0:
                    # If all agents have traditional fields and no behavior, likely legacy
                    for agent in agents[:3]:  # Check first 3 agents
                        if isinstance(agent, dict) and "behavior" not in agent:
                            return False  # Looks like legacy format
            
            # If it has version OR agents (including simplified syntax), consider it unified
            return has_version or has_agents
            
        except Exception:
            return False
    
    def _is_unified_config(self) -> bool:
        """Check if using unified configuration"""
        try:
            config_type = self._detect_config_type()
            return config_type != "multi-file"
        except FileNotFoundError:
            return False
    
    def _load_unified_config(self) -> LangSwarmConfig:
        """Load unified configuration from single file"""
        config_file = self._detect_config_type()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Process includes if specified
        if "include" in data:
            data = self._process_includes(data, os.path.dirname(config_file))
        
        # Resolve environment variables and prompts
        self._resolve_env_vars(data)
        if "agents" in data:
            self._resolve_prompts(data["agents"], os.path.dirname(config_file))
        
        # Convert to unified config format
        unified_config = self._dict_to_unified_config(data)
        
        # Validate configuration
        errors = unified_config.validate()
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error.section or 'general'}.{error.field}: {error.message}")
        
        return unified_config
    
    def _process_includes(self, data: Dict[str, Any], base_path: str) -> Dict[str, Any]:
        """Process include directives in configuration"""
        includes = data.pop("include", [])
        
        for include_file in includes:
            include_path = os.path.join(base_path, include_file)
            if os.path.exists(include_path):
                with open(include_path, 'r', encoding='utf-8') as f:
                    include_data = yaml.safe_load(f) or {}
                
                # Merge included data (includes override main config)
                for key, value in include_data.items():
                    if key in data and isinstance(data[key], list) and isinstance(value, list):
                        data[key].extend(value)
                    elif key in data and isinstance(data[key], dict) and isinstance(value, dict):
                        data[key].update(value)
                    else:
                        data[key] = value
        
        return data
    
    def _dict_to_unified_config(self, data: Dict[str, Any]) -> LangSwarmConfig:
        """Convert dictionary to unified configuration object"""
        # Handle agents with zero-config support
        agents_data = data.get("agents", [])
        if ZERO_CONFIG_AVAILABLE:
            agents = self._process_zero_config_agents(agents_data)
        else:
            agents = self._process_standard_agents(agents_data)
        
        # Handle tools - support both old dict format and new list format
        tools = {}
        tools_data = data.get("tools", {})
        
        if isinstance(tools_data, list):
            # New list format: [{"id": "tool1", "type": "mcpfilesystem", ...}, ...]
            for tool_item in tools_data:
                if isinstance(tool_item, dict) and "id" in tool_item:
                    tool_id = tool_item["id"]
                    tool_config = ToolConfig(
                        id=tool_id,
                        type=tool_item.get("type"),
                        settings=tool_item.get("settings", {}),
                        auto_configure=tool_item.get("auto_configure", False),
                        local_mode=tool_item.get("local_mode", True)
                    )
                    tools[tool_id] = tool_config
        elif isinstance(tools_data, dict):
            # Old dict format: {"tool1": {"type": "mcpfilesystem", ...}, ...}
            for tool_id, tool_data in tools_data.items():
                if isinstance(tool_data, dict):
                    tool_config = ToolConfig(
                        id=tool_id,
                        type=tool_data.get("type"),
                        settings=tool_data.get("settings", {}),
                        auto_configure=tool_data.get("auto_configure", False),
                        local_mode=tool_data.get("local_mode", True)
                    )
                    tools[tool_id] = tool_config
        
        # Handle workflows with Workflow Simplification support
        workflows = []
        agent_ids = [agent.id for agent in agents]  # Get available agent IDs for validation
        
        for workflow_data in data.get("workflows", []):
            if isinstance(workflow_data, str):
                # Simple syntax: "assistant -> user"
                workflow_id = f"simple_workflow_{len(workflows) + 1}"
                workflow_config = WorkflowConfig.from_simple_syntax(
                    workflow_id=workflow_id,
                    simple_syntax=workflow_data,
                    available_agents=agent_ids
                )
                workflows.append(workflow_config)
                
            elif isinstance(workflow_data, dict):
                # Check if it's a simple workflow definition
                if "simple" in workflow_data:
                    # Simple syntax in dict format: {"id": "my_workflow", "simple": "assistant -> user"}
                    workflow_config = WorkflowConfig.from_simple_syntax(
                        workflow_id=workflow_data["id"],
                        simple_syntax=workflow_data["simple"],
                        available_agents=agent_ids
                    )
                    # Override name if provided
                    if "name" in workflow_data:
                        workflow_config.name = workflow_data["name"]
                    workflows.append(workflow_config)
                    
                elif "workflow" in workflow_data:
                    # Simple syntax in workflow field: {"id": "my_workflow", "workflow": "assistant -> user"}
                    workflow_config = WorkflowConfig.from_simple_syntax(
                        workflow_id=workflow_data["id"],
                        simple_syntax=workflow_data["workflow"],
                        available_agents=agent_ids
                    )
                    if "name" in workflow_data:
                        workflow_config.name = workflow_data["name"]
                    workflows.append(workflow_config)
                    
                else:
                    # Complex workflow definition (existing format)
                    workflow_config = WorkflowConfig(
                        id=workflow_data["id"],
                        name=workflow_data.get("name"),
                        steps=workflow_data.get("steps", [])
                    )
                    workflows.append(workflow_config)
        
        # Handle memory with Memory Made Simple
        memory_data = data.get("memory", False)
        memory_config = MemoryConfig.setup_memory(memory_data)
        
        # Handle advanced configuration
        advanced_data = data.get("advanced", {})
        brokers = []
        for broker_data in advanced_data.get("brokers", []):
            broker_config = BrokerConfig(
                id=broker_data["id"],
                type=broker_data.get("type", "internal"),
                settings=broker_data.get("settings", {})
            )
            brokers.append(broker_config)
        
        advanced_config = AdvancedConfig(
            brokers=brokers,
            queues=advanced_data.get("queues", []),
            registries=advanced_data.get("registries", []),
            plugins=advanced_data.get("plugins", []),
            retrievers=advanced_data.get("retrievers", [])
        )
        
        # Handle core langswarm settings
        langswarm_data = data.get("langswarm", {})
        langswarm_config = LangSwarmCoreConfig(
            debug=langswarm_data.get("debug", False),
            log_level=langswarm_data.get("log_level", "INFO"),
            config_validation=langswarm_data.get("config_validation", True)
        )
        
        return LangSwarmConfig(
            version=data.get("version", "1.0"),
            project_name=data.get("project_name"),
            langswarm=langswarm_config,
            agents=agents,
            tools=tools,
            workflows=workflows,
            memory=memory_config,
            advanced=advanced_config
        )
    
    def _unified_to_legacy_data(self, unified_config: LangSwarmConfig) -> Dict[str, Any]:
        """Convert unified config to legacy format for existing processing"""
        legacy_data = unified_config.to_legacy_format()
        
        # Convert workflows to expected format
        workflows_dict = {}
        for workflow in legacy_data["workflows"]:
            workflows_dict[workflow["id"]] = workflow
        
        return {
            "agents": legacy_data["agents"],
            "tools": legacy_data["tools"],
            "workflows": workflows_dict,
            "brokers": legacy_data["brokers"],
            "queues": legacy_data["queues"],
            "registries": legacy_data["registries"],
            "plugins": legacy_data["plugins"],
            "retrievers": legacy_data["retrievers"]
        }
    
    def load_single_config(self, config_path: str = "langswarm.yaml") -> LangSwarmConfig:
        """Load configuration from single unified file"""
        original_path = self.config_path
        self.config_path = config_path
        
        try:
            unified_config = self._load_unified_config()
            return unified_config
        finally:
            self.config_path = original_path
    
    # ===== ZERO-CONFIG AGENT SUPPORT =====
    
    def _ensure_zero_config_initialized(self):
        """Lazy-initialize zero-config components"""
        if not ZERO_CONFIG_AVAILABLE:
            return False
        
        if self.environment_detector is None:
            self.environment_detector = EnvironmentDetector()
            
        if self.capabilities is None:
            self.capabilities = self.environment_detector.detect_capabilities()
            
        if self.smart_defaults is None:
            self.smart_defaults = SmartDefaults(self.capabilities)
            
        return True
    
    def _process_zero_config_agents(self, agents_config: List[Any]) -> List[AgentConfig]:
        """Process agents with zero-config enhancement"""
        if not self._ensure_zero_config_initialized():
            # Fallback to standard processing
            return self._process_standard_agents(agents_config)
        
        processed_agents = []
        
        for agent_spec in agents_config:
            if isinstance(agent_spec, str):
                # Minimal syntax: agents: ["assistant"]
                agent_config = self.smart_defaults.generate_agent_config(
                    agent_id=agent_spec,
                    behavior="helpful"
                )
                processed_agents.append(agent_config)
                
            elif isinstance(agent_spec, dict):
                agent_id = agent_spec.get("id")
                if not agent_id:
                    continue
                
                behavior = agent_spec.get("behavior", "helpful")
                
                # Generate smart defaults first
                agent_config = self.smart_defaults.generate_agent_config(agent_id, behavior)
                
                # Override with any explicitly provided values
                for key, value in agent_spec.items():
                    if hasattr(agent_config, key) and value is not None:
                        setattr(agent_config, key, value)
                
                # Handle capability-based tool selection
                if "capabilities" in agent_spec:
                    expanded_tools = self.smart_defaults.expand_capabilities(agent_spec["capabilities"])
                    agent_config.tools = expanded_tools
                
                processed_agents.append(agent_config)
        
        logging.info(f"🤖 Zero-config: Processed {len(processed_agents)} agents with smart defaults")
        
        return processed_agents
    
    def _process_standard_agents(self, agents_config: List[Any]) -> List[AgentConfig]:
        """Fallback standard agent processing when zero-config unavailable"""
        agents = []
        
        for agent_data in agents_config:
            if isinstance(agent_data, str):
                # Convert string to minimal dict
                agent_data = {"id": agent_data}
            
            if isinstance(agent_data, dict) and "id" in agent_data:
                agent_config = AgentConfig(
                    id=agent_data["id"],
                    name=agent_data.get("name"),
                    model=agent_data.get("model", "gpt-4o"),
                    behavior=agent_data.get("behavior"),
                    system_prompt=agent_data.get("system_prompt"),
                    agent_type=agent_data.get("agent_type", "generic"),
                    tools=agent_data.get("tools", []),
                    memory=agent_data.get("memory", False),
                    streaming=agent_data.get("streaming", False),
                    max_tokens=agent_data.get("max_tokens"),
                    temperature=agent_data.get("temperature"),
                    presence_penalty=agent_data.get("presence_penalty"),
                    frequency_penalty=agent_data.get("frequency_penalty"),
                    top_p=agent_data.get("top_p"),
                    response_format=agent_data.get("response_format")
                )
                agents.append(agent_config)
        
        return agents
    
    def create_zero_config_agent(self, agent_id: str, behavior: str = "helpful", **overrides) -> AgentConfig:
        """Create a zero-config agent programmatically"""
        if not self._ensure_zero_config_initialized():
            raise RuntimeError("Zero-config functionality not available. Install required dependencies: psutil, requests")
        
        return self.smart_defaults.generate_agent_config(agent_id, behavior, **overrides)
    
    def get_environment_info(self) -> Optional[Dict[str, Any]]:
        """Get detected environment information"""
        if not self._ensure_zero_config_initialized():
            return None
        
        return self.capabilities.to_dict()
    
    def suggest_behavior_for_description(self, description: str) -> str:
        """Suggest optimal behavior based on description"""
        if not self._ensure_zero_config_initialized():
            return "helpful"
        
        return self.smart_defaults.suggest_behavior(description)
    
    def get_available_behaviors(self) -> List[str]:
        """Get list of all available behavior presets"""
        return [
            "helpful", "coding", "research", "creative", 
            "analytical", "support", "conversational", "educational"
        ]
    
    # ========== ZERO-CONFIG AGENT CREATION HELPERS ==========
    
    def create_simple_agent(
        self, 
        agent_id: str, 
        behavior: str = "helpful",
        model: str = "gpt-4o",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create a simple agent with behavior-driven configuration.
        
        Args:
            agent_id: Unique identifier for the agent
            behavior: Behavior preset (helpful, coding, research, creative, analytical, support, conversational, educational)
            model: LLM model to use (defaults to gpt-4o)
            tools: List of tool names to enable
            **kwargs: Additional agent configuration options
            
        Returns:
            AgentConfig: Ready-to-use agent configuration
            
        Example:
            # Create a coding assistant with filesystem access
            agent = config_loader.create_simple_agent(
                agent_id="code_helper",
                behavior="coding", 
                tools=["filesystem", "github"]
            )
        """
        # Validate behavior
        available_behaviors = self.get_available_behaviors()
        if behavior not in available_behaviors:
            print(f"⚠️  Unknown behavior '{behavior}'. Available: {', '.join(available_behaviors)}")
            print(f"   Using 'helpful' as fallback.")
            behavior = "helpful"
        
        # Create agent configuration
        agent_config = AgentConfig(
            id=agent_id,
            name=kwargs.get("name", agent_id.replace("_", " ").title()),
            model=model,
            behavior=behavior,
            agent_type=kwargs.get("agent_type", "generic"),
            tools=tools or [],
            memory=kwargs.get("memory", False),
            streaming=kwargs.get("streaming", False),
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
            top_p=kwargs.get("top_p"),
            response_format=kwargs.get("response_format")
        )
        
        # Generate system prompt if not provided
        if not kwargs.get("system_prompt"):
            agent_config.system_prompt = self._generate_behavior_prompt(behavior, tools or [])
        else:
            agent_config.system_prompt = kwargs["system_prompt"]
        
        return agent_config
    
    def create_coding_assistant(
        self,
        agent_id: str = "coding_assistant",
        model: str = "gpt-4o",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create a specialized coding assistant with filesystem and GitHub tools.
        
        Args:
            agent_id: Agent identifier (defaults to 'coding_assistant')
            model: LLM model (defaults to gpt-4o for best coding performance)
            tools: Additional tools beyond default filesystem and github
            **kwargs: Additional configuration options
            
        Returns:
            AgentConfig: Coding assistant ready for development tasks
        """
        default_tools = ["filesystem", "github"]
        if tools:
            # Merge with defaults, avoiding duplicates
            all_tools = list(dict.fromkeys(default_tools + tools))
        else:
            all_tools = default_tools
            
        return self.create_simple_agent(
            agent_id=agent_id,
            behavior="coding",
            model=model,
            tools=all_tools,
            **kwargs
        )
    
    def create_research_assistant(
        self,
        agent_id: str = "research_assistant", 
        model: str = "gpt-4o",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create a research assistant with web search and analysis tools.
        
        Args:
            agent_id: Agent identifier (defaults to 'research_assistant')
            model: LLM model (defaults to gpt-4o for best analysis)
            tools: Additional tools beyond default web_search
            **kwargs: Additional configuration options
            
        Returns:
            AgentConfig: Research assistant ready for information gathering
        """
        default_tools = ["web_search", "filesystem"]
        if tools:
            all_tools = list(dict.fromkeys(default_tools + tools))
        else:
            all_tools = default_tools
            
        return self.create_simple_agent(
            agent_id=agent_id,
            behavior="research",
            model=model,
            tools=all_tools,
            **kwargs
        )
    
    def create_support_agent(
        self,
        agent_id: str = "support_agent",
        model: str = "gpt-4o-mini",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create a customer support agent with helpful tools.
        
        Args:
            agent_id: Agent identifier (defaults to 'support_agent')
            model: LLM model (defaults to gpt-4o-mini for cost efficiency)
            tools: Additional tools beyond defaults
            **kwargs: Additional configuration options
            
        Returns:
            AgentConfig: Support agent ready for customer assistance
        """
        default_tools = ["dynamic-forms", "filesystem"]
        if tools:
            all_tools = list(dict.fromkeys(default_tools + tools))
        else:
            all_tools = default_tools
            
        return self.create_simple_agent(
            agent_id=agent_id,
            behavior="support",
            model=model,
            tools=all_tools,
            **kwargs
        )
    
    def create_conversational_agent(
        self,
        agent_id: str = "chat_agent",
        model: str = "gpt-4o-mini",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create a conversational agent optimized for natural dialogue.
        
        Args:
            agent_id: Agent identifier (defaults to 'chat_agent')
            model: LLM model (defaults to gpt-4o-mini for responsiveness)
            tools: Tools to enable (minimal by default for faster responses)
            **kwargs: Additional configuration options
            
        Returns:
            AgentConfig: Conversational agent ready for natural chat
        """
        return self.create_simple_agent(
            agent_id=agent_id,
            behavior="conversational",
            model=model,
            tools=tools or [],
            **kwargs
        )
    
    def create_multi_behavior_agent(
        self,
        agent_id: str,
        primary_behavior: str,
        secondary_behaviors: List[str],
        model: str = "gpt-4o",
        tools: Optional[List[str]] = None,
        **kwargs
    ) -> AgentConfig:
        """
        Create an agent that combines multiple behavior patterns.
        
        Args:
            agent_id: Agent identifier
            primary_behavior: Main behavior pattern
            secondary_behaviors: Additional behavior aspects to incorporate
            model: LLM model to use
            tools: Tools to enable
            **kwargs: Additional configuration options
            
        Returns:
            AgentConfig: Multi-behavior agent configuration
        """
        # Generate combined behavior prompt
        available_behaviors = self.get_available_behaviors()
        
        # Validate behaviors
        all_behaviors = [primary_behavior] + secondary_behaviors
        for behavior in all_behaviors:
            if behavior not in available_behaviors:
                print(f"⚠️  Unknown behavior '{behavior}'. Available: {', '.join(available_behaviors)}")
        
        # Create custom behavior description
        custom_behavior = f"""You are a versatile assistant combining multiple expertise areas:

**Primary Focus**: {primary_behavior.title()} - {self._get_behavior_description(primary_behavior)}

**Additional Capabilities**:"""
        
        for behavior in secondary_behaviors:
            if behavior in available_behaviors:
                custom_behavior += f"\n- {behavior.title()}: {self._get_behavior_description(behavior)}"
        
        custom_behavior += """

Adapt your approach based on the user's needs, drawing from your combined expertise to provide the most helpful response."""
        
        # Create agent with custom system prompt
        system_prompt = custom_behavior + self._generate_behavior_prompt(primary_behavior, tools or []).split("## Response Format", 1)[1] if "## Response Format" in self._generate_behavior_prompt(primary_behavior, tools or []) else self._generate_behavior_prompt(primary_behavior, tools or [])
        
        return AgentConfig(
            id=agent_id,
            name=kwargs.get("name", agent_id.replace("_", " ").title()),
            model=model,
            behavior=primary_behavior,  # Store primary for reference
            system_prompt=system_prompt,
            agent_type=kwargs.get("agent_type", "generic"),
            tools=tools or [],
            memory=kwargs.get("memory", False),
            streaming=kwargs.get("streaming", False),
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
            top_p=kwargs.get("top_p"),
            response_format=kwargs.get("response_format")
        )
    
    def _get_behavior_description(self, behavior: str) -> str:
        """Get short description of a behavior for multi-behavior agents"""
        descriptions = {
            "helpful": "General assistance and problem-solving",
            "coding": "Programming, debugging, and technical guidance",
            "research": "Information gathering and analysis",
            "creative": "Idea generation and creative problem-solving",
            "analytical": "Data analysis and logical reasoning",
            "support": "Customer service and issue resolution",
            "conversational": "Natural dialogue and engagement", 
            "educational": "Teaching and learning facilitation"
        }
        return descriptions.get(behavior, f"{behavior} assistance")

    def load(self):
        # Detect configuration type and handle accordingly
        if self._is_unified_config():
            self.is_unified = True
            self.unified_config = self._load_unified_config()
            
            # Convert unified config to legacy format for existing processing
            legacy_data = self._unified_to_legacy_data(self.unified_config)
            self.config_data = legacy_data
            
            # Apply behavior-driven system prompt generation if needed
            self._apply_behavior_system_prompts()
            
            # Continue with existing initialization logic
            self._load_secrets()
            self._initialize_brokers()
            self._initialize_retrievers()
            self._initialize_tools()
            self._initialize_plugins()
            self._initialize_agents()
        else:
            # Use existing multi-file configuration logic
            self._load_secrets()
            self._load_config_files()
            self._initialize_brokers()
            self._initialize_retrievers()
            self._initialize_tools()
            self._initialize_plugins()
            self._initialize_agents()
        
        return (
            self.config_data.get('workflows', {}), 
            self.agents, 
            self.brokers, 
            # self.config_data.get('tools', []),
            list(self.tools.values()),  # Return instantiated tools, not raw config
            self.tools_metadata
        )
    
    def _apply_behavior_system_prompts(self):
        """Apply behavior-driven system prompt generation for unified configs"""
        if not self.unified_config:
            return
        
        # Generate system prompts based on behavior for agents that don't have explicit prompts
        for agent_data in self.config_data.get('agents', []):
            if not agent_data.get('system_prompt') and agent_data.get('behavior'):
                behavior = agent_data['behavior']
                generated_prompt = self._generate_behavior_prompt(behavior, agent_data.get('tools', []))
                agent_data['system_prompt'] = generated_prompt
    
    def _generate_behavior_prompt(self, behavior: str, tools: List[str]) -> str:
        """Generate comprehensive system prompt based on behavior and available tools"""
        
        # Enhanced behavior prompts with professional, detailed personalities
        behavior_prompts = {
            "helpful": """You are a helpful and intelligent assistant. Your core principles:
- Always be polite, respectful, and considerate in your responses
- Provide accurate, well-researched information when possible
- If uncertain, clearly state limitations and suggest next steps
- Break down complex topics into understandable explanations
- Anticipate follow-up questions and provide comprehensive context
- Maintain a friendly but professional tone""",
            
            "coding": """You are an expert programming assistant with deep technical knowledge. Your expertise includes:
- Writing clean, efficient, and well-documented code
- Debugging complex issues and explaining root causes
- Code review with constructive feedback and best practices
- Architecture design and technical decision guidance
- Multiple programming languages, frameworks, and development tools
- Security considerations and performance optimization
- Always explain your reasoning and provide examples when helpful""",
            
            "research": """You are a thorough research assistant specialized in information analysis. Your approach:
- Systematically gather information from multiple angles
- Critically evaluate sources and evidence quality
- Present findings in a clear, structured format
- Identify patterns, trends, and key insights
- Distinguish between facts, opinions, and speculation
- Provide comprehensive context and background information
- Suggest additional research directions when relevant""",
            
            "creative": """You are a creative assistant focused on inspiration and innovation. Your strengths:
- Generating original ideas and unique perspectives
- Brainstorming solutions from unconventional angles
- Supporting creative writing, storytelling, and content creation
- Helping with artistic and design challenges
- Encouraging experimentation and creative risk-taking
- Building upon ideas to develop them further
- Balancing creativity with practical considerations""",
            
            "analytical": """You are an analytical assistant specializing in logical reasoning and data interpretation. Your methodology:
- Approach problems systematically using structured analysis
- Break down complex issues into manageable components
- Apply logical frameworks and analytical methods
- Identify patterns, correlations, and causal relationships
- Present findings with clear evidence and reasoning
- Consider multiple perspectives and potential biases
- Provide actionable insights based on thorough analysis""",
            
            "support": """You are a customer support assistant focused on resolution and satisfaction. Your approach:
- Listen carefully and acknowledge user concerns with empathy
- Ask clarifying questions to fully understand issues
- Provide step-by-step guidance with clear instructions
- Anticipate common follow-up questions and address them proactively
- Escalate complex issues appropriately when needed
- Follow up to ensure problems are fully resolved
- Maintain patience and professionalism even in challenging situations""",
            
            "conversational": """You are a conversational assistant designed for natural, engaging dialogue. Your style:
- Maintain a warm, friendly, and approachable personality
- Ask thoughtful questions to keep conversations flowing
- Show genuine interest in topics and user perspectives
- Share relevant insights and experiences when appropriate
- Adapt your communication style to match the user's tone
- Remember context from earlier in the conversation
- Balance being informative with being entertaining""",
            
            "educational": """You are an educational assistant focused on teaching and learning. Your teaching philosophy:
- Adapt explanations to the learner's level and background
- Use examples, analogies, and visual aids when helpful
- Break complex concepts into progressive learning steps
- Encourage questions and provide patient, thorough answers
- Check for understanding before moving to advanced topics
- Provide practice opportunities and real-world applications
- Foster critical thinking and independent problem-solving skills"""
        }
        
        # Use exact match or fallback to helpful behavior
        if behavior in behavior_prompts:
            base_prompt = behavior_prompts[behavior]
        else:
            # For custom behaviors, create a basic prompt
            base_prompt = f"You are a {behavior} assistant. {behavior_prompts['helpful']}"
        
        # Add comprehensive JSON format instructions
        json_format_instructions = """

## Response Format

**CRITICAL**: You must always respond using this exact JSON structure:

```json
{
  "response": "Your message to the user explaining what you're doing or responding to their query",
  "mcp": {
    "tool": "tool_name",
    "method": "method_name",
    "params": {"param1": "value1", "param2": "value2"}
  }
}
```

**Format Rules:**
- **REQUIRED**: `response` field containing your message to the user
- **OPTIONAL**: `mcp` field for tool calls (only when you need to use tools)
- **Never mix plain text with JSON** - always use this structured format
- **Multiple tool calls**: Make one call, see results, then make another in next response

**Response Patterns:**

**Conversation only** (no tools needed):
```json
{
  "response": "I understand your question about data analysis. Based on the information provided, here are the key insights..."
}
```

**Tool usage** (when you need to perform an action):
```json
{
  "response": "I'll read that configuration file to understand the current settings and help troubleshoot the issue.",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "/config/app.json"}
  }
}
```

**Intent-based tool usage** (when expressing what you want to accomplish):
```json
{
  "response": "Let me search the codebase for similar error patterns to help diagnose this issue.",
  "mcp": {
    "tool": "github",
    "intent": "search for error patterns related to authentication failures",
    "context": "user experiencing login issues after recent security update - need debugging analysis"
  }
}
```"""

        # Add tool-specific instructions based on available tools
        if tools:
            tool_instructions = "\n\n## Available Tools\n\nYou have access to the following tools to help users:"
            
            tool_descriptions = {
                "filesystem": {
                    "description": "File and directory operations",
                    "capabilities": [
                        "Read file contents to analyze configurations, logs, or code",
                        "List directory contents to understand project structure",
                        "Help with file-related troubleshooting and analysis"
                    ],
                    "examples": [
                        'Read config: `{"tool": "filesystem", "method": "read_file", "params": {"path": "/config/app.json"}}`',
                        'List directory: `{"tool": "filesystem", "method": "list_directory", "params": {"path": "/src"}}`'
                    ]
                },
                "github": {
                    "description": "GitHub repository management and development workflow",
                    "capabilities": [
                        "Create and manage issues for bug reports and feature requests",
                        "Search repositories for code patterns and documentation",
                        "Manage pull requests and code reviews",
                        "Access repository information and statistics"
                    ],
                    "examples": [
                        'Create issue: `{"tool": "github", "intent": "create issue for authentication bug", "context": "critical login failure"}`',
                        'Search code: `{"tool": "github", "intent": "find error handling patterns", "context": "need examples of exception handling"}`'
                    ]
                },
                "dynamic-forms": {
                    "description": "Interactive form generation for configuration and data collection",
                    "capabilities": [
                        "Generate configuration forms based on user context",
                        "Create interactive interfaces for complex setup processes",
                        "Provide structured data collection for user preferences"
                    ],
                    "examples": [
                        'Generate form: `{"tool": "dynamic-forms", "method": "generate_interactive_response", "params": {"context": "user wants to configure AI preferences"}}`'
                    ]
                },
                "calculator": {
                    "description": "Mathematical calculations and computations",
                    "capabilities": [
                        "Perform complex mathematical calculations",
                        "Handle algebraic expressions and equations",
                        "Process statistical and financial computations"
                    ],
                    "examples": [
                        'Calculate: `{"tool": "calculator", "method": "calculate", "params": {"expression": "sqrt(25) + 10 * 2"}}`'
                    ]
                },
                "web_search": {
                    "description": "Web search and information retrieval",
                    "capabilities": [
                        "Search the web for current information and updates",
                        "Find recent news, documentation, and resources",
                        "Verify facts and gather external information"
                    ],
                    "examples": [
                        'Search web: `{"tool": "web_search", "method": "search", "params": {"query": "latest Python security updates 2024"}}`'
                    ]
                }
            }
            
            for tool in tools:
                if tool in tool_descriptions:
                    info = tool_descriptions[tool]
                    tool_instructions += f"""

### {tool.title()} Tool
**Purpose**: {info['description']}

**Capabilities**:
{chr(10).join(f"- {cap}" for cap in info['capabilities'])}

**Usage Examples**:
{chr(10).join(f"- {example}" for example in info['examples'])}"""
                else:
                    # Generic tool description for unknown tools
                    tool_instructions += f"""

### {tool.title()} Tool
**Purpose**: {tool} functionality for enhanced capabilities
**Usage**: Use intent-based calls to describe what you want to accomplish with this tool"""
            
            tool_instructions += """

**Tool Usage Guidelines**:
- Use tools when they can provide better assistance than conversation alone
- Always explain what you're going to do before using a tool
- For complex operations, prefer intent-based calls that describe your goal
- For simple, well-defined operations, use direct method calls
- Wait for tool results before proceeding with additional tool calls"""
        
        # Combine all parts
        full_prompt = base_prompt + json_format_instructions
        if tools:
            full_prompt += tool_instructions
        
        return full_prompt

    def _load_secrets(self):
        secrets_path = os.path.join(self.config_path, "secrets.yaml")
        secrets_dict = yaml.safe_load(open(secrets_path)) if os.path.exists(secrets_path) else {}
        yaml.SafeLoader.add_constructor("!secret", self._make_secret_constructor(secrets_dict))

    def _initialize_brokers(self):
        # Import message broker classes on demand
        try:
            from langswarm.mcp.tools.message_queue_publisher.main import InMemoryBroker, RedisBroker, GCPPubSubBroker
        except ImportError:
            # If MCP tools not available, skip broker initialization
            return
            
        for broker in self.config_data.get("brokers", []):
            if broker["type"] in ["internal", "local", "in_memory"]:
                self.brokers[broker["id"]] = InMemoryBroker()
            elif broker["type"] == "redis":
                settings = broker.get("settings", {})
                self.brokers[broker["id"]] = RedisBroker(**settings)
            elif broker["type"] in ["gcp", "gcp_pubsub"]:
                settings = broker.get("settings", {})
                project = settings.get("project") or settings.get("gcp_project")
                if project:
                    self.brokers[broker["id"]] = GCPPubSubBroker(project)
                else:
                    print(f"Warning: GCP broker {broker['id']} missing project configuration")

    def _make_secret_constructor(self, secrets_dict):
        def secret_constructor(loader, node):
            secret_key = loader.construct_scalar(node)
            return secrets_dict.get(secret_key, os.getenv(secret_key, f"<missing:{secret_key}>"))
        return secret_constructor

    def _load_config_files(self):
        for filename in LS_DEFAULT_CONFIG_FILES:
            full_path = os.path.join(self.config_path, filename)
            if os.path.exists(full_path):
                key = filename.replace(".yaml", "")
                self.config_data[key] = self._load_yaml_file(full_path).get(key, {})
                self._validate_yaml_section(key, self.config_data[key])

    def _validate_yaml_section(self, section, entries):
        schema = LS_SCHEMAS.get(section.rstrip("s"))
        if not schema:
            return
        validator = Validator(schema)
        for entry in entries:
            if not validator.validate(entry):
                print(f"❌ Validation failed in section '{section}': {validator.errors}")

    def _load_yaml_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}

        # 1) resolve any env:FOO → os.getenv("FOO")
        self._resolve_env_vars(data)

        # 2) then pull in any prompt‑file references
        self._resolve_prompts(data, os.path.dirname(filepath))

        return data

    def _resolve_prompts(self, obj, base_path):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str) and ("prompt" in k or "instruction" in k or "description" in k) and v.endswith((".md", ".txt")):
                    file_path = os.path.join(base_path, v)
                    if os.path.isfile(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            obj[k.replace('_file', '')] = f.read()
                            del obj[k]
                elif isinstance(v, list) and ("prompt" in k or "instruction" in k or "description" in k) and all(isinstance(item, str) and item.endswith((".md", ".txt")) for item in v):
                    # 🌟 New: Handle list of prompt files
                    contents = []
                    for item in v:
                        file_path = os.path.join(base_path, item)
                        if os.path.isfile(file_path):
                            with open(file_path, "r", encoding="utf-8") as f:
                                contents.append(f.read())
                    combined = '\n\n---\n\n'.join(contents)
                    obj[k.replace('_file', '')] = combined
                    del obj[k]
                else:
                    self._resolve_prompts(v, base_path)
        elif isinstance(obj, list):
            for item in obj:
                self._resolve_prompts(item, base_path)

    def _resolve_env_vars(self, obj):
        """
        Recursively walk a loaded YAML structure and:
         • replace any string "env:FOO" with os.getenv("FOO", "")  
         • replace any string "setenv:BAR" by setting os.environ[key]=BAR
           where `key` is the dict key, and then obj[key] = BAR.
        """
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str):
                    if v.startswith("env:"):
                        env_key = v.split("env:", 1)[1]
                        obj[k] = os.getenv(env_key, "")
                    elif v.startswith("setenv:"):
                        val = v.split("setenv:", 1)[1]
                        # 1) set the environment variable
                        os.environ[k] = val
                        # 2) replace in our config dict
                        obj[k] = val
                    else:
                        # recurse into nested dict or list
                        # (only if it's neither env: nor setenv:)
                        continue  # leave other strings alone
                else:
                    # recurse into non‑string values
                    self._resolve_env_vars(v)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item.startswith("env:"):
                    env_key = item.split("env:", 1)[1]
                    obj[i] = os.getenv(env_key, "")
                elif isinstance(item, str) and item.startswith("setenv:"):
                    # lists have no "key" name, so we can't set
                    # os.environ[name] here — skip or log:
                    val = item.split("setenv:", 1)[1]
                    obj[i] = val
                else:
                    self._resolve_env_vars(item)
    
    def _initialize_retrievers(self):
        for retriever in self.config_data.get("retrievers", []):
            try:
                from langswarm.memory.adapters._langswarm.chromadb.main import ChromaDBAdapter
                self.retrievers[retriever["id"]] = self._initialize_component(retriever, ChromaDBAdapter)
            except ImportError:
                print(f"Warning: ChromaDB not available, skipping retriever {retriever['id']}")
                continue
        
    def _initialize_tools(self):
        self.tools_metadata = {}  # New dict for storing metadata explicitly
        
        # **SMART TOOL AUTO-DISCOVERY**
        # Check if tools should be auto-discovered
        tools_config = self.config_data.get("tools", [])
        
        # If no tools.yaml exists or tools list is empty, try auto-discovery
        if not tools_config and ZERO_CONFIG_AVAILABLE:
            print("🔍 No tools configuration found. Attempting Smart Tool Auto-Discovery...")
            auto_discovered = self._auto_discover_tools()
            if auto_discovered:
                tools_config = auto_discovered
                self.config_data["tools"] = tools_config
                print(f"   ✅ Auto-discovered {len(auto_discovered)} tools")
        
        # Process each tool configuration (supports both full config and simplified syntax)
        for tool_cfg in tools_config:
            # **SIMPLIFIED TOOL SYNTAX SUPPORT**
            # Convert simplified syntax (just tool names) to full configuration
            if isinstance(tool_cfg, str):
                tool_cfg = self._expand_simplified_tool_syntax(tool_cfg)
                if not tool_cfg:
                    continue  # Skip if tool couldn't be auto-configured
            
            ttype = tool_cfg.get("type", "unknown").lower()

            # Always store metadata, even if no class is found
            if "metadata" in tool_cfg:
                self.tools_metadata[tool_cfg["id"]] = tool_cfg["metadata"]
        
            # Skip actual instantiation for function-type
            if ttype == "function":
                print(f"ℹ️ Skipping '{ttype}' entry — not a tool, only metadata registered.")
                continue

            # 1) see if user explicitly pointed at a class path
            if "class" in tool_cfg:
                module_path, class_name = tool_cfg["class"].rsplit(".", 1)
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)

            # 2) otherwise fall back to our registry
            else:
                cls = self.tool_classes.get(ttype)

            if not cls:
                print(f"⚠️  Unknown tool type '{ttype}' in tool '{tool_cfg.get('id', 'unnamed')}', skipping initialization.")
                print(f"   Available tool types: {list(self.tool_classes.keys())}")
                print(f"   Tip: Use 'type: function' for metadata-only tools or register custom tool classes.")
                continue

            # build the instance
            self.tools[tool_cfg["id"]] = self._initialize_component(tool_cfg, cls)
    
    def _auto_discover_tools(self) -> List[Dict[str, Any]]:
        """Auto-discover available tools based on environment detection"""
        if not ZERO_CONFIG_AVAILABLE:
            return []
        
        try:
            # Initialize environment detector if not already done
            if not hasattr(self, '_environment_detector'):
                self._environment_detector = EnvironmentDetector()
            
            # Discover all available tools
            detected_tools = self._environment_detector.auto_discover_tools()
            
            # Convert to tool configuration format
            tool_configs = []
            for tool_info in detected_tools:
                if "preset" in tool_info:
                    # Built-in tool with preset
                    preset = tool_info["preset"]
                    config = {
                        "id": preset.id,
                        "type": preset.type,
                        "description": preset.description,
                        "local_mode": preset.local_mode,
                        "pattern": preset.pattern,
                        "methods": preset.methods,
                    }
                    
                    # Add preset settings
                    if preset.settings:
                        config.update(preset.settings)
                    
                    # Add custom config
                    if preset.custom_config:
                        config.update(preset.custom_config)
                        
                else:
                    # Custom tool
                    config = {
                        "id": tool_info["id"],
                        "type": tool_info["type"],
                        "description": tool_info["description"],
                        "local_mode": tool_info.get("local_mode", True),
                        "pattern": tool_info.get("pattern", "direct"),
                    }
                    
                    if "path" in tool_info:
                        config["path"] = tool_info["path"]
                
                tool_configs.append(config)
            
            return tool_configs
            
        except Exception as e:
            print(f"   ⚠️  Auto-discovery failed: {e}")
            return []
    
    def _expand_simplified_tool_syntax(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Expand simplified tool syntax (just tool name) to full configuration.
        
        Args:
            tool_name: Simple tool name like "filesystem" or "github"
            
        Returns:
            Full tool configuration dict or None if tool not available
        """
        if not ZERO_CONFIG_AVAILABLE:
            print(f"   ⚠️  Cannot expand '{tool_name}': Zero-config not available")
            return None
        
        try:
            # Initialize environment detector if not already done
            if not hasattr(self, '_environment_detector'):
                self._environment_detector = EnvironmentDetector()
            
            # Get preset for this tool
            preset = self._environment_detector.get_tool_preset(tool_name)
            if not preset:
                print(f"   ⚠️  Unknown tool preset: '{tool_name}'")
                return None
            
            # Check if tool is available in current environment
            status = self._environment_detector._check_tool_availability(preset)
            if not status["available"]:
                missing_items = []
                if status["missing_env_vars"]:
                    missing_items.extend(status["missing_env_vars"])
                if status["missing_dependencies"]:
                    missing_items.extend(status["missing_dependencies"])
                
                print(f"   ⚠️  Tool '{tool_name}' not available: Missing {', '.join(missing_items)}")
                return None
            
            # Create full configuration from preset
            config = {
                "id": preset.id,
                "type": preset.type,
                "description": preset.description,
                "local_mode": preset.local_mode,
                "pattern": preset.pattern,
                "methods": preset.methods,
            }
            
            # Add preset settings
            if preset.settings:
                config.update(preset.settings)
            
            # Add custom config
            if preset.custom_config:
                config.update(preset.custom_config)
            
            print(f"   ✅ Expanded '{tool_name}' to {preset.type} with {len(preset.methods)} methods")
            return config
            
        except Exception as e:
            print(f"   ⚠️  Failed to expand '{tool_name}': {e}")
            return None
    
    def get_available_tools_info(self) -> Dict[str, Any]:
        """Get information about available tools for user guidance"""
        if not ZERO_CONFIG_AVAILABLE:
            return {"error": "Zero-config functionality not available"}
        
        # Initialize environment detector if not already done
        if not hasattr(self, '_environment_detector'):
            self._environment_detector = EnvironmentDetector()
        
        return self._environment_detector.detect_environment()
    
    def suggest_tools_for_behavior(self, behavior: str) -> List[str]:
        """Suggest tools based on agent behavior"""
        if not ZERO_CONFIG_AVAILABLE:
            return []
        
        # Initialize environment detector if not already done
        if not hasattr(self, '_environment_detector'):
            self._environment_detector = EnvironmentDetector()
        
        behavior_tool_map = {
            "coding": ["filesystem", "github"],
            "research": ["filesystem", "github"],
            "helpful": ["filesystem"],
            "analytical": ["filesystem"],
            "creative": ["filesystem"],
            "support": ["dynamic_forms"],
            "conversational": [],
            "educational": ["filesystem"]
        }
        
        # Get base suggestions for behavior
        suggested_tools = behavior_tool_map.get(behavior, ["filesystem"])
        
        # Filter to only available tools
        available_tool_ids = self._environment_detector.get_available_tool_ids()
        available_suggestions = [tool for tool in suggested_tools if tool in available_tool_ids]
        
        return available_suggestions
    
    def _process_simplified_agent_tools(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process simplified tool syntax in agent configurations"""
        tools = agent_config.get("tools", [])
        if not tools:
            return agent_config
        
        # Check if any tools are in simplified format (just strings)
        has_simplified = any(isinstance(tool, str) for tool in tools)
        
        if has_simplified and ZERO_CONFIG_AVAILABLE:
            # Initialize environment detector if not already done
            if not hasattr(self, '_environment_detector'):
                self._environment_detector = EnvironmentDetector()
            
            expanded_tools = []
            for tool in tools:
                if isinstance(tool, str):
                    # First check if this is a defined tool ID in the tools section
                    tools_config = self.config_data.get("tools", [])
                    tool_ids = {t.get("id") for t in tools_config if isinstance(t, dict) and "id" in t}
                    
                    if tool in tool_ids:
                        # This is a reference to a defined tool, keep it as-is
                        expanded_tools.append(tool)
                    else:
                        # Check if this tool is available as a preset
                        preset = self._environment_detector.get_tool_preset(tool)
                        if preset:
                            status = self._environment_detector._check_tool_availability(preset)
                            if status["available"]:
                                expanded_tools.append(tool)
                            else:
                                missing = status.get("missing_env_vars", []) + status.get("missing_dependencies", [])
                                print(f"   ⚠️  Skipping tool '{tool}' for agent '{agent_config.get('id', 'unnamed')}': Missing {', '.join(missing)}")
                        else:
                            print(f"   ⚠️  Unknown tool '{tool}' for agent '{agent_config.get('id', 'unnamed')}'")
                else:
                    # Tool is already in full format
                    expanded_tools.append(tool)
            
            agent_config["tools"] = expanded_tools
        
        return agent_config

    def _initialize_plugins(self):
        for plugin in self.config_data.get("plugins", []):
            if plugin["type"].lower() == "processtoolkit":
                try:
                    # ProcessToolkit import would go here if it exists
                    # For now, skip since it's not defined
                    print(f"Warning: ProcessToolkit not available, skipping plugin {plugin['id']}")
                    continue
                except ImportError:
                    print(f"Warning: ProcessToolkit not available, skipping plugin {plugin['id']}")
                    continue

    def _initialize_component(self, config, cls):
        # For MCP tools, ensure all required fields are provided
        if config["type"].startswith("mcp"):
            config_args = {
                "identifier": config["id"], 
                "name": config["type"],
                "description": config.get("description", f"MCP tool: {config['type']}"),
                "instruction": config.get("instruction", f"Use the {config['type']} MCP tool"),
                "brief": config.get("brief", f"{config['type']} tool"),
                **{k: v for k, v in config.items() if k not in ["id", "type", "description", "instruction", "brief"]},
                **config.get("settings", {})
            }
        else:
            config_args = {"identifier": config["id"], "name": config["type"], **config.get("settings", {})}
        return self._call_with_valid_args(cls, config_args)

    def _call_with_valid_args(self, func, config):
        sig = signature(func)
        valid_params = sig.parameters
        accepts_kwargs = any(p.kind == Parameter.VAR_KEYWORD for p in valid_params.values())
        filtered_args = {k: v for k, v in config.items() if k in valid_params}
        extra_kwargs = {k: v for k, v in config.items() if k not in valid_params}
        return func(**filtered_args, **extra_kwargs) if accepts_kwargs else func(**filtered_args)

    def _initialize_agents(self):
        for agent in self.config_data.get("agents", []):
            try:
                agent_type = agent.get("register_as", "agent")
                
                # **SMART TOOL AUTO-DISCOVERY FOR AGENTS**
                # Process simplified tool syntax before registry assignment
                agent = self._process_simplified_agent_tools(agent)
                
                agent = self._assign_registries(agent)
                agent = self._setup_memory(agent)
                agent["system_prompt"] = self._render_system_prompt(agent)

                # Lazy import to prevent circular imports
                from langswarm.core.factory.agents import AgentFactory
                creator = getattr(AgentFactory, f"create_{agent_type}", AgentFactory.create)
                self.agents[agent["id"]] = self._call_with_valid_args(creator, {"name": agent["id"], **agent})
                
            except ValueError as e:
                if "API key" in str(e):
                    print(f"⚠️  Agent '{agent['id']}' requires API key: {e}")
                    print(f"   Skipping initialization. Agent will be available but non-functional until API key is provided.")
                    # Store agent config for later initialization when API key becomes available
                    self.agents[agent["id"]] = {
                        "id": agent["id"],
                        "status": "pending_api_key",
                        "config": agent,
                        "error": str(e)
                    }
                else:
                    print(f"❌ Failed to initialize agent '{agent['id']}': {e}")
                    raise
            except Exception as e:
                print(f"❌ Unexpected error initializing agent '{agent['id']}': {e}")
                print(f"   Skipping this agent. Check agent configuration.")
                # Continue with other agents instead of failing entirely
                continue

    def _assign_registries(self, agent):
        if "retrievers" in agent:
            reg = RAGRegistry()
            for _id in agent["retrievers"]:
                reg.register_rag(self.retrievers[_id.lower()])
            agent["rag_registry"] = reg
        if "tools" in agent:
            reg = ToolRegistry()
            for _id in agent["tools"]:
                reg.register_tool(self.tools[_id.lower()])
            agent["tool_registry"] = reg
        if "plugins" in agent:
            reg = PluginRegistry()
            for _id in agent["plugins"]:
                reg.register_plugin(self.plugins[_id.lower()])
            agent["plugin_registry"] = reg
        
        # NAVIGATION TOOL AUTO-REGISTRATION
        # Check if this agent will be used in navigation-enabled steps
        if self._agent_needs_navigation_tool(agent["id"]):
            # Create or get existing tool registry
            if "tool_registry" not in agent:
                agent["tool_registry"] = ToolRegistry()
            
            # Add navigation tool to registry
            from langswarm.features.intelligent_navigation.navigator import NavigationTool
            nav_tool = NavigationTool()
            agent["tool_registry"].register_tool(nav_tool)
            
            # Store navigation context for the agent
            agent["navigation_context"] = self._get_navigation_context(agent["id"])
        
        return agent
        
    def _agent_needs_navigation_tool(self, agent_id: str) -> bool:
        """Check if agent will be used in navigation-enabled steps"""
        workflows = self.config_data.get('workflows', {})
        for workflow_id, workflow_list in workflows.items():
            # workflow_list is a list of workflow definitions
            for workflow_data in (workflow_list if isinstance(workflow_list, list) else [workflow_list]):
                for step in workflow_data.get('steps', []):
                    if step.get('agent') == agent_id and 'navigation' in step:
                        return True
        return False
    
    def _get_navigation_context(self, agent_id: str) -> Dict[str, Any]:
        """Get navigation context for agent"""
        navigation_contexts = {}
        workflows = self.config_data.get('workflows', {})
        
        for workflow_id, workflow_list in workflows.items():
            # workflow_list is a list of workflow definitions
            for workflow_data in (workflow_list if isinstance(workflow_list, list) else [workflow_list]):
                for step in workflow_data.get('steps', []):
                    if step.get('agent') == agent_id and 'navigation' in step:
                        navigation_contexts[step['id']] = step['navigation']
        
        return navigation_contexts

    def _setup_memory(self, agent):
        if "memory_adapter" in agent:
            agent["memory_adapter"] = self.retrievers.get(agent["memory_adapter"])
        if "memory_summary_adapter" in agent:
            agent["memory_summary_adapter"] = self.retrievers.get(agent["memory_summary_adapter"])
        return agent

    def _render_system_prompt(self, agent):
        # Try multiple template locations
        template_paths = [
            'templates/system_prompt_template.md',  # User's custom template
            'langswarm/core/templates/system_prompt_template.md',  # LangSwarm default
            os.path.join(os.path.dirname(__file__), 'templates/system_prompt_template.md')  # Relative to this file
        ]
        
        template_path = None
        for path in template_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            return agent.get("system_prompt", "")

        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        # Load and conditionally include fragment templates
        fragment_content = self._load_prompt_fragments(agent)
        
        # Append fragments to main template
        if fragment_content:
            template_str += "\n\n" + fragment_content

        template = Template(template_str)
        def _lookup_many(ids, source):
            result = []
            for _id in ids:
                if _id in source:
                    src = source[_id]
                    if hasattr(src, 'get'):  # It's a dict (config)
                        tool_info = {
                            "id": _id, 
                            "description": src.get("description", ""), 
                            "instruction": src.get("instruction", "")
                        }
                        # Add schema information if available
                        if "schema" in src:
                            tool_info["schema"] = src["schema"]
                        result.append(tool_info)
                    else:  # It's an instance (tool object)
                        tool_info = {
                            "id": _id,
                            "description": getattr(src, 'description', f'{_id} tool'),
                            "instruction": getattr(src, 'instruction', f'Use the {_id} tool')
                        }
                        # Add schema information for MCP tools
                        if hasattr(src, 'mcp_server') or hasattr(src, 'server'):
                            # Try to get schema from MCP server
                            mcp_server = getattr(src, 'mcp_server', None) or getattr(src, 'server', None)
                            if mcp_server and hasattr(mcp_server, 'tasks'):
                                schemas = {}
                                for task_name, task_meta in mcp_server.tasks.items():
                                    if hasattr(task_meta["input_model"], "schema"):
                                        schemas[task_name] = task_meta["input_model"].schema()
                                if schemas:
                                    tool_info["schema"] = schemas
                        # Also check for explicit schema attribute
                        elif hasattr(src, 'schema'):
                            tool_info["schema"] = getattr(src, 'schema')
                        result.append(tool_info)
            return result

        return template.render(
            system_prompt=agent.get("system_prompt"),
            retrievers=_lookup_many(agent.get("retrievers", []), self.retrievers),
            tools=_lookup_many(agent.get("tools", []), self.tools),
            plugins=_lookup_many(agent.get("plugins", []), self.plugins)
        )
    


    def _load_prompt_fragments(self, agent):
        """Load conditional prompt fragments based on agent configuration"""
        fragments = []
        fragments_dir = os.path.join(os.path.dirname(__file__), "templates", "fragments")
        
        # Check what capabilities this agent has
        agent_tools = agent.get("tools", [])
        agent_config = agent.get("config", {})
        
        # 1. Include clarification fragment if agent has intent-based tools or retry capabilities
        has_intent_tools = self._agent_has_intent_tools(agent_tools)
        has_retry_capability = self._agent_has_retry_capability(agent_tools, agent_config)
        
        if has_intent_tools or has_retry_capability:
            clarification_path = os.path.join(fragments_dir, "clarification.md")
            if os.path.exists(clarification_path):
                with open(clarification_path, "r", encoding="utf-8") as f:
                    fragments.append(f.read())
        
        # 2. Include retry fragment if agent has retry capabilities  
        if has_retry_capability:
            retry_path = os.path.join(fragments_dir, "retry.md")
            if os.path.exists(retry_path):
                with open(retry_path, "r", encoding="utf-8") as f:
                    fragments.append(f.read())
        
        # 3. Include intent workflow fragment if agent has intent-based tools
        if has_intent_tools:
            intent_path = os.path.join(fragments_dir, "intent_workflow.md")
            if os.path.exists(intent_path):
                with open(intent_path, "r", encoding="utf-8") as f:
                    fragments.append(f.read())
        
        # 4. Include cross-workflow clarification fragment if agent can do cross-workflow operations
        has_cross_workflow_capability = has_intent_tools or self._agent_has_cross_workflow_tools(agent_tools)
        if has_cross_workflow_capability:
            cross_workflow_path = os.path.join(fragments_dir, "cross_workflow_clarification.md")
            if os.path.exists(cross_workflow_path):
                with open(cross_workflow_path, "r", encoding="utf-8") as f:
                    fragments.append(f.read())
        
        return "\n\n".join(fragments)
    
    def _agent_has_cross_workflow_tools(self, tool_ids):
        """Check if agent has tools that can invoke sub-workflows"""
        # Any agent with MCP tools or workflow invocation capabilities
        # could potentially need cross-workflow clarification
        return len(tool_ids) > 0  # Simple heuristic - any agent with tools
    
    def _agent_has_intent_tools(self, tool_ids):
        """Check if agent has tools that support intent-based calling"""
        for tool_id in tool_ids:
            if tool_id in self.tools:
                tool = self.tools[tool_id]
                # Check if tool supports intent-based pattern
                if hasattr(tool, 'pattern') and tool.pattern == "intent":
                    return True
                # Check if tool has main_workflow (indicates intent capability)
                if hasattr(tool, 'main_workflow') and tool.main_workflow:
                    return True
        return False
    
    def _agent_has_retry_capability(self, tool_ids, agent_config):
        """Check if agent or its tools have retry capabilities"""
        # Check agent-level retry configuration
        if agent_config.get("retry_enabled", False):
            return True
        
        # Check if any tools have retry capabilities
        for tool_id in tool_ids:
            if tool_id in self.tools:
                tool = self.tools[tool_id]
                # Check tool configuration for retry settings
                if hasattr(tool, 'retry_enabled') and tool.retry_enabled:
                    return True
                # Check if tool has workflows with retry steps
                if hasattr(tool, 'workflows') and self._tool_workflows_have_retry(tool):
                    return True
        
        return False
    
    def _handle_cross_workflow_clarification(self, step_id: str, prompt: str, context: str, scope: str) -> str:
        """Handle clarification requests that need to bubble up through workflow hierarchy"""
        print(f"🌊 Cross-workflow clarification (scope: {scope})")
        print(f"   Prompt: {prompt}")
        print(f"   Context: {context}")
        
        # Create clarification metadata for tracking
        clarification_data = {
            "step_id": step_id,
            "prompt": prompt,
            "context": context,
            "scope": scope,
            "workflow_id": self.context.get("current_workflow_id"),
            "request_id": self.context.get("request_id"),
            "timestamp": time.time()
        }
        
        if scope == "parent_workflow":
            # Route to parent workflow via special output
            parent_clarification = {
                "type": "clarification_request",
                "data": clarification_data,
                "response_needed": True
            }
            
            # Store the clarification state for later resumption
            self.context.setdefault("pending_clarifications", {})[step_id] = clarification_data
            
            # Route this to the parent workflow output handler
            self._handle_output(step_id, {"to": "parent_workflow_clarification"}, parent_clarification)
            
            return f"PARENT_CLARIFICATION_PENDING: {prompt}"
            
        elif scope == "root_user":
            # Route all the way back to the original user
            root_clarification = {
                "type": "clarification_request", 
                "data": clarification_data,
                "response_needed": True
            }
            
            # Store the clarification state
            self.context.setdefault("pending_clarifications", {})[step_id] = clarification_data
            
            # Route to root user
            self._handle_output(step_id, {"to": "user"}, root_clarification)
            
            return f"ROOT_CLARIFICATION_PENDING: {prompt}"
        
        else:
            # Fallback to local clarification
            return f"CLARIFICATION_NEEDED: {prompt}"
    
    def _resume_after_clarification(self, step_id: str, clarification_response: str) -> None:
        """Resume workflow execution after clarification is resolved"""
        if step_id in self.context.get("pending_clarifications", {}):
            clarification_data = self.context["pending_clarifications"][step_id]
            
            print(f"🔄 Resuming workflow after clarification")
            print(f"   Original prompt: {clarification_data['prompt']}")
            print(f"   Clarification response: {clarification_response}")
            
            # Add clarification response to context for the step to use
            self.context["clarification_response"] = clarification_response
            self.context["clarification_context"] = clarification_data["context"]
            
            # Remove from pending clarifications
            del self.context["pending_clarifications"][step_id]
            
            # Re-execute the step with additional context
            step = self._get_step_by_id(step_id)
            self._execute_step(step, mark_visited=False)
    
    def _tool_workflows_have_retry(self, tool):
        """Check if tool's workflows contain retry configurations"""
        try:
            # This is a simplified check - in practice you'd parse the workflow YAML
            if hasattr(tool, 'main_workflow'):
                return True  # Assume workflow tools can have retry
        except:
            pass
        return False

    def _handle_step_error(self, step: Dict, step_id: str, visit_key: str, error: Exception):
        print(f"❌ Error in step {step_id}: {error}")

        if step.get("retry"):
            retries = self.context["retry_counters"].get(visit_key, 0)
            if retries < step["retry"]:
                print(f"🔄 Retrying step {step_id} (attempt {retries + 1})")
                self.context["retry_counters"][visit_key] = retries + 1
                return self._execute_step(step, mark_visited=False)
            else:
                print(f"⚠️ Retry limit reached for {step_id}")

        if step.get("rollback_to"):
            rollbacks = self.context["rollback_counters"].get(visit_key, 0)
            rollback_limit = step.get("rollback_limit", 1)
            if rollbacks < rollback_limit:
                rollback_step = step["rollback_to"]
                print(f"🔙 Rolling back from {step_id} to {rollback_step} (attempt {rollbacks + 1})")
                self.context["rollback_counters"][visit_key] = rollbacks + 1
                return self._execute_by_step_id(rollback_step, mark_visited=False)
            else:
                print(f"⚠️ Rollback limit reached for {step_id}")

        raise error
        
    # The core loop runner:
    def _run_loop_iteration(self, loop_id, step):
        state = self.context["loops"][loop_id]
        idx   = state["index"]
        var   = step["loop"].get("var", "item")

        # Done?
        if idx >= len(state["values"]) or idx >= state["max"]:
            # collect results into step_outputs
            self.context["step_outputs"][loop_id] = state["results"]
            return self._handle_output(
                loop_id,
                {"collect": step["output"]["collect"], "to": step["output"]["to"]},
                state["results"],
                step
            )

        # bind the next element
        self.context[var] = state["values"][idx]

        # run the body step
        body_step = self._get_step_by_id(step["loop"]["body"])
        self._execute_step(body_step)

        # capture its output and advance
        state["results"].append(self.context["step_outputs"][body_step["id"]])
        state["index"] += 1

        # and recurse
        return self._run_loop_iteration(loop_id, step)

    # New helper to kick off a loop:
    def _start_loop(self, step):
        loop = step["loop"]
        values = self._resolve_input(loop["for_each"])
        var    = loop.get("var", "item")
        max_i  = int(self._resolve_input(loop.get("max", len(values))))

        # Initialize loop state
        self.context.setdefault("loops", {})[step["id"]] = {
            "values": values, "index": 0, "max": max_i, "results": []
        }
        return self._run_loop_iteration(step["id"], step)

    def _build_no_mcp_system_prompt(self, tools_metadata: dict):
        prompt = """
Your job is to decide which backend function should handle the user's request, and with what arguments.

**IMPORTANT**: You must respond using this exact structured JSON format:

{
  "response": "Brief explanation of what you're doing for the user",
  "tool": "function_name",
  "args": {"param": "value"}
}

When given a user message, you must:
1. Map it unambiguously to exactly one of the available tools (see list below).
2. Include a brief explanation in the "response" field about what you're doing
3. Pass the tool id as the "tool" parameter in the reply.
4. Extract and normalize the required parameters for that tool in the "args" field.

        """
        prompt += """
If any required parameter is missing or ambiguous, instead return:
{
  "response": "I need more information to help you with that.",
  "tool": "clarify",
  "args": {"prompt": "a single, clear follow-up question"}
}
        """
        prompt += "Available functions:\n\n"
    
        for tid, meta in tools_metadata.items():
            prompt += f"- **{tid}**: {meta['description']}\n"
            prompt += json.dumps(meta['parameters'], indent=2)
            prompt += "\n\n"

        prompt += "---\n\n"
        prompt += """
**Response Requirements:**
- Always return valid JSON with "response", "tool", and "args" fields
- Include a user-friendly explanation in the "response" field
- Choose the precise tool based on the user's request
- Fill all required parameters or ask for clarification
- NEVER return plain text - always use the JSON structure
        """
    
        return prompt

    def _get_visit_key(self, step: Dict) -> str:
        """
        Generate a unique visit key for a workflow step.
        
        This key is used to track whether a step has been visited before,
        enabling proper handling of retry logic and preventing infinite loops.
        
        Args:
            step: The workflow step dictionary
            
        Returns:
            A unique string identifier for the step
        """
        step_id = step.get('id', 'unknown')
        
        # Include retry context in the visit key if the step has retry capability
        if step.get('retry'):
            retry_count = self.context.get("retry_counters", {}).get(step_id, 0)
            return f"{step_id}:retry:{retry_count}"
        
        # For loop steps, include loop iteration context
        if 'loop' in step:
            loop_id = step['loop'].get('id', step_id)
            iteration = self.context.get("loop_counters", {}).get(loop_id, 0)
            return f"{step_id}:loop:{loop_id}:iteration:{iteration}"
        
        # For fan-in steps, include fan key context
        if step.get('fan_key'):
            fan_key = step['fan_key']
            return f"{step_id}:fan:{fan_key}"
        
        # Default visit key is just the step ID
        return step_id

    def _recheck_pending_fanins(self):
        """
        Check if any pending fan-in steps are ready to execute.
        
        Fan-in steps are only executed when all their required fan-out steps have completed.
        This method is called after any step completes to check if any pending fan-ins
        should now be executed.
        """
        if not hasattr(self, 'context') or not self.context:
            return
            
        pending_fanins = self.context.get("pending_fanins", {})
        
        # Check each fan-in group
        for fan_key, step_ids in list(pending_fanins.items()):
            if not step_ids:
                continue
                
            # Execute all pending fan-in steps for this fan key
            for step_id in list(step_ids):
                try:
                    target_step = self._get_step_by_id(step_id)
                    if target_step:
                        print(f"🔄 Executing pending fan-in step: {step_id}")
                        self._execute_step(target_step)
                        # Remove from pending after successful execution
                        step_ids.discard(step_id)
                except Exception as e:
                    print(f"⚠️ Error executing pending fan-in step {step_id}: {e}")
                    # Remove failed step from pending to avoid infinite retries
                    step_ids.discard(step_id)
            
            # Clean up empty fan-in groups
            if not step_ids:
                del pending_fanins[fan_key]

    async def _recheck_pending_fanins_async(self):
        """
        Async version of _recheck_pending_fanins.
        
        Check if any pending fan-in steps are ready to execute asynchronously.
        """
        if not hasattr(self, 'context') or not self.context:
            return
            
        pending_fanins = self.context.get("pending_fanins", {})
        
        # Check each fan-in group
        for fan_key, step_ids in list(pending_fanins.items()):
            if not step_ids:
                continue
                
            # Execute all pending fan-in steps for this fan key
            tasks = []
            for step_id in list(step_ids):
                try:
                    target_step = self._get_step_by_id(step_id)
                    if target_step:
                        print(f"🔄 Executing pending fan-in step: {step_id} (async)")
                        tasks.append(self._execute_step_async(target_step))
                        # Remove from pending after queuing for execution
                        step_ids.discard(step_id)
                except Exception as e:
                    print(f"⚠️ Error queuing pending fan-in step {step_id}: {e}")
                    # Remove failed step from pending to avoid infinite retries
                    step_ids.discard(step_id)
            
            # Execute all tasks concurrently
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Clean up empty fan-in groups
            if not step_ids:
                del pending_fanins[fan_key]

    def _resolve_condition_branch(self, condition):
        """
        Resolve a condition and return the appropriate branch.
        
        Args:
            condition: The condition configuration dict
            
        Returns:
            The branch to execute (step_id, dict, or None)
        """
        if not condition:
            return None
            
        # Handle different condition types
        if isinstance(condition, dict):
            # Check for if/then/else structure
            if "if" in condition:
                condition_expr = condition["if"]
                then_branch = condition.get("then")
                else_branch = condition.get("else")
                
                # Evaluate the condition
                try:
                    result = self._evaluate_condition(condition_expr)
                    if result:
                        return then_branch
                    else:
                        return else_branch
                except Exception as e:
                    print(f"⚠️ Error evaluating condition '{condition_expr}': {e}")
                    return else_branch
            
            # Check for switch/case structure
            elif "switch" in condition:
                switch_value = self._resolve_input(condition["switch"])
                cases = condition.get("cases", {})
                default_case = condition.get("default")
                
                # Find matching case
                for case_value, case_branch in cases.items():
                    if str(switch_value) == str(case_value):
                        return case_branch
                
                # Return default case if no match
                return default_case
            
            # Check for exists condition
            elif "exists" in condition:
                path = condition["exists"]
                try:
                    value = self._resolve_input(f"${{{path}}}")
                    exists = value is not None and value != ""
                    then_branch = condition.get("then")
                    else_branch = condition.get("else")
                    return then_branch if exists else else_branch
                except Exception:
                    return condition.get("else")
        
        # If condition is a simple string, treat it as a direct step reference
        elif isinstance(condition, str):
            return condition
        
        return None

    def _make_output_serializable(self, output):
        if isinstance(output, pd.DataFrame):
            return {
                "__type__": "DataFrame",
                "value": output.to_dict(orient="split")  # safer for roundtrip
            }
        elif isinstance(output, pd.Series):
            return {
                "__type__": "Series",
                "value": output.to_dict()
            }
        elif isinstance(output, np.ndarray):
            return {
                "__type__": "ndarray",
                "value": output.tolist()
            }
        else:
            return output  # passthrough for everything else

    def _execute_step(self, step: Dict, mark_visited=True):
        return self._execute_step_inner_sync(step, mark_visited)

    async def _execute_step_async(self, step: Dict, mark_visited=True):
        return await self._execute_step_inner_async(step, mark_visited)

    @WorkflowIntelligence.track_step
    def _execute_step_inner_sync(self, step: Dict, mark_visited: bool = True):
        if not step:
            return
    
        step_id   = step['id']
        visit_key = self._get_visit_key(step)
        print(f"\n▶ Executing step: {step_id} (visit_key={visit_key}) (async=False)")
        
        # Initialize navigation_choice to prevent NameError
        navigation_choice = None
    
        if visit_key in self.context["visited_steps"]:
            if step.get("retry") and self.context["retry_counters"].get(visit_key, 0) < step["retry"]:
                print(f"🔁 Step {step_id} retry allowed.")
            else:
                print(f"🔁 Step {step_id} already done, skipping.")
                return
                
        if "loop" in step:
            return self._start_loop(step)
                
        if 'invoke_workflow' in step:
            wf_id = step['invoke_workflow']
            inp = self._resolve_input(step.get("input"))
            output = self.run_workflow(wf_id, inp)
            
        elif 'agent' in step:
            agent = self.agents[step['agent']]
            
            # Initialize navigation_choice for this agent step
            navigation_choice = None
            
            # NAVIGATION SUPPORT: Check if this step has navigation config
            if 'navigation' in step:
                # Set up navigation context for the agent
                from langswarm.features.intelligent_navigation.navigator import NavigationContext
                nav_context = NavigationContext(
                    workflow_id=getattr(self, 'workflow_id', 'unknown'),
                    current_step=step['id'],
                    context_data=self.context,
                    step_history=self.context.get('step_history', []),
                    available_steps=step['navigation'].get('available_steps', [])
                )
                
                # Store navigation context in agent if it has the capability
                if hasattr(agent, 'navigation_context'):
                    agent.navigation_context = nav_context
            
            # Execute agent
            raw_input = step.get("input")
            if isinstance(raw_input, dict):
                resolved = {k: self._resolve_input(v) for k, v in raw_input.items()}
                output = agent.chat(f"{resolved}")
            else:
                output = agent.chat(self._resolve_input(raw_input))
            
            # NAVIGATION SUPPORT: Check if agent made a navigation choice
            if 'navigation' in step:
                navigation_choice = self._extract_navigation_choice(output, step)
                
                if navigation_choice:
                    # Agent chose a navigation step
                    chosen_step = navigation_choice['step_id']
                    reasoning = navigation_choice.get('reasoning', '')
                    confidence = navigation_choice.get('confidence', 1.0)
                    
                    # Track navigation decision
                    self._track_navigation_decision(step['id'], chosen_step, reasoning, confidence)
                    
                    # Create navigation result
                    result = {
                        'navigation_choice': chosen_step,
                        'reasoning': reasoning,
                        'confidence': confidence
                    }
                else:
                    result = output
            else:
                result = output
                
        elif 'no_mcp' in step:
            tools_raw = step['no_mcp']['tools']
            tool_ids = [t if isinstance(t, str) else t["name"] for t in tools_raw]
            tool_metadata = {tid: self.tools_metadata[tid] for tid in tool_ids}
            tool_options = {
                (t if isinstance(t, str) else t["name"]): ({} if isinstance(t, str) else t)
                for t in tools_raw
            }
        
            system_prompt = self._build_no_mcp_system_prompt(tool_metadata)
        
            agent_id = step["agent"]
            agent = self.agents[agent_id]
            agent.update_system_prompt(system_prompt=system_prompt)
        
            agent_input = self._resolve_input(step.get("input"))
            response = agent.chat(agent_input)
        
            try:
                payload = self.formatting_utils.safe_json_loads(response)
                if payload is None:
                    payload = response
            except Exception:
                payload = response
        
            # Handle both old and new response formats
            if isinstance(payload, dict):
                # New structured format: {"response": "text", "tool": "name", "args": {...}}
                user_response = payload.get('response', '')
                tool_name = payload.get('tool', payload.get('name'))  # Support both 'tool' and 'name' for backward compatibility
                args = payload.get('args', {})
                
                # Log user response if present
                if user_response:
                    print(f"Agent response: {user_response}")
            else:
                # Fallback for plain text responses
                user_response = str(payload)  # Initialize user_response for non-dict responses
                tool_name = None
                args = {}
                print(f"Agent response (non-JSON): {payload}")
        
            if tool_name in ['clarify', 'chat', 'unknown']:
                try:
                    result = str(args.get('prompt', args))
                except Exception:
                    result = str(args)
            elif tool_name in tool_metadata:
                func = self._resolve_function(tool_metadata[tool_name]['function'])
                step_args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
                args = {k: self._resolve_input(v) for k, v in args.items()}
                args.setdefault("context", self.context)
                args.update(step_args)
                result = func(**args)
        
                # 🔁 Optional repeatable history and retry limit
                opts = tool_options.get(tool_name, {})
                if opts.get("repeatable"):
                    agent_history = self.context.setdefault("tool_history", {}).setdefault(agent_id, {})
                    agent_retries = self.context.setdefault("tool_retries", {}).setdefault(agent_id, {})
                    agent_history.setdefault(tool_name, []).append(result)
                    agent_retries[tool_name] = agent_retries.get(tool_name, 0) + 1
        
                    max_retry = opts.get("retry_limit", 3)
                    if agent_retries[tool_name] < max_retry:
                        history_str = "\n".join(f"- {r}" for r in agent_history[tool_name])
                        step["input"] = f"{agent_input}\n\nHistory for tool '{tool_name}':\n{history_str}"
                        self._execute_step(step, mark_visited=False)
                        return
            elif tool_name:
                raise ValueError(f"Unknown tool selected by agent: {tool_name}")
            else:
                # No tool call, just return the response text
                result = user_response or str(payload)
                
        elif 'function' in step:
            func = self._resolve_function(step['function'], script=step.get('script'))
            args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
            args.setdefault("context", self.context)
            try:
                result = func(**args)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"\n🚨 Exception in function `{step['function']}`:\n{tb}")
                raise  # Re-raise to keep workflow intelligence working

            if result == "__NOT_READY__":
                fan_key = step.get("fan_key", "default")
                self.context["pending_fanins"][f"{step_id}@{fan_key}"] = step
                return
        else:
            # Handle other step types
            result = "Step executed"
            
        # Store result
        self.context['previous_output'] = result
        self.context['step_outputs'][step['id']] = result
        
        # Handle regular output routing (if no navigation was used)
        if 'output' in step and not navigation_choice:
            self._handle_output(step['id'], step['output'], result, step)
    
    def _extract_navigation_choice(self, response: str, step: Dict) -> Optional[Dict]:
        """Extract navigation choice from agent response"""
        if 'navigation' not in step:
            return None
            
        # Try to parse as JSON first
        try:
            parsed = self.formatting_utils.safe_json_loads(response)
            if parsed and isinstance(parsed, dict):
                # Check for navigation tool call
                if parsed.get('tool') == 'navigate_workflow' or parsed.get('name') == 'navigate_workflow':
                    args = parsed.get('args', parsed.get('arguments', {}))
                    return {
                        'step_id': args.get('step_id'),
                        'reasoning': args.get('reasoning', ''),
                        'confidence': args.get('confidence', 1.0)
                    }
        except:
            pass
            
        return None
    
    def _track_navigation_decision(self, current_step: str, chosen_step: str, reasoning: str, confidence: float):
        """Track navigation decision for analytics"""
        try:
            from langswarm.features.intelligent_navigation.tracker import NavigationTracker, NavigationDecision
            from datetime import datetime
            import uuid
            
            # Create navigation decision record
            decision = NavigationDecision(
                decision_id=str(uuid.uuid4()),
                workflow_id=self.workflow_id,
                step_id=current_step,
                agent_id=self.context.get('current_agent', 'unknown'),
                chosen_step=chosen_step,
                available_steps=[step['id'] for step in self.context.get('available_navigation_steps', [])],
                reasoning=reasoning,
                confidence=confidence,
                context_hash=str(hash(str(self.context))),
                timestamp=datetime.now(),
                execution_time_ms=0.0  # Could be measured
            )
            
            # Track the decision
            tracker = NavigationTracker()
            tracker.track_decision(decision)
            
        except Exception as e:
            print(f"⚠️  Failed to track navigation decision: {e}")
    
    def _route_to_step(self, step_id: str, result: Dict):
        """Route to chosen step"""
        # Find the target step
        workflow_data = self.config_data.get('workflows', {}).get(self.workflow_id, {})
        target_step = None
        
        for step in workflow_data.get('steps', []):
            if step['id'] == step_id:
                target_step = step
                break
        
        if not target_step:
            raise ValueError(f"Navigation target step '{step_id}' not found in workflow")
        
        # Execute the target step
        self._execute_step(target_step)

    @WorkflowIntelligence.track_step
    async def _execute_step_inner_async(self, step: Dict, mark_visited: bool = True):
        if not step:
            return
    
        step_id   = step['id']
        visit_key = self._get_visit_key(step)
        print(f"\n▶ Executing step: {step_id} (visit_key={visit_key}) (async=True)")
    
        if visit_key in self.context["visited_steps"]:
            if step.get("retry") and self.context["retry_counters"].get(visit_key, 0) < step["retry"]:
                print(f"🔁 Step {step_id} retry allowed.")
            else:
                print(f"🔁 Step {step_id} already done, skipping.")
                return
    
        if 'invoke_workflow' in step:
            wf_id = step['invoke_workflow']
            inp   = self._resolve_input(step.get("input"))
            output = await self.run_workflow_async(wf_id, inp)
        elif 'no_mcp' in step:
            tools_raw = step['no_mcp']['tools']
            tool_ids = [t if isinstance(t, str) else t["name"] for t in tools_raw]
            tool_metadata = {tid: self.tools_metadata[tid] for tid in tool_ids}
            tool_options = {
                (t if isinstance(t, str) else t["name"]): ({} if isinstance(t, str) else t)
                for t in tools_raw
            }
        
            system_prompt = self._build_no_mcp_system_prompt(tool_metadata)
        
            agent_id = step["agent"]
            agent = self.agents[agent_id]
            agent.update_system_prompt(system_prompt=system_prompt)
        
            agent_input = self._resolve_input(step.get("input"))
            response = agent.chat(agent_input)
        
            try:
                payload = self.formatting_utils.safe_json_loads(response)
                if payload is None:
                    payload = response
            except Exception:
                payload = response
        
            # Handle both old and new response formats
            if isinstance(payload, dict):
                # New structured format: {"response": "text", "tool": "name", "args": {...}}
                user_response = payload.get('response', '')
                tool_name = payload.get('tool', payload.get('name'))  # Support both 'tool' and 'name' for backward compatibility
                args = payload.get('args', {})
                
                # Log user response if present
                if user_response:
                    print(f"Agent response: {user_response}")
            else:
                # Fallback for plain text responses
                user_response = str(payload)  # Initialize user_response for non-dict responses
                tool_name = None
                args = {}
                print(f"Agent response (non-JSON): {payload}")
        
            if tool_name in ['clarify', 'chat', 'unknown']:
                try:
                    result = str(args.get('prompt', args))
                except Exception:
                    result = str(args)
            elif tool_name in tool_metadata:
                func = self._resolve_function(tool_metadata[tool_name]['function'])
                step_args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
                args = {k: self._resolve_input(v) for k, v in args.items()}
                args.setdefault("context", self.context)
                args.update(step_args)
                result = await func(**args)
        
                # 🔁 Optional repeatable history and retry limit
                opts = tool_options.get(tool_name, {})
                if opts.get("repeatable"):
                    agent_history = self.context.setdefault("tool_history", {}).setdefault(agent_id, {})
                    agent_retries = self.context.setdefault("tool_retries", {}).setdefault(agent_id, {})
                    agent_history.setdefault(tool_name, []).append(result)
                    agent_retries[tool_name] = agent_retries.get(tool_name, 0) + 1
        
                    max_retry = opts.get("retry_limit", 3)
                    if agent_retries[tool_name] < max_retry:
                        history_str = "\n".join(f"- {r}" for r in agent_history[tool_name])
                        step["input"] = f"{agent_input}\n\nHistory for tool '{tool_name}':\n{history_str}"
                        await self._execute_step_async(step, mark_visited=False)
                        return
            elif tool_name:
                raise ValueError(f"Unknown tool selected by agent: {tool_name}")
            else:
                # No tool call, just return the response text
                result = user_response or str(payload)
        
            self.context['previous_output'] = result
            self.context['step_outputs'][step['id']] = result
        
            # 🧠 Determine dynamic output override
            opts = tool_options.get(tool_name, {})
            if opts.get("return_to_agent"):
                to_target = opts.get("return_to", agent_id)
                self._handle_output(step['id'], {"to": to_target}, result, step)
            else:
                if "output" in step:
                    self.intelligence.end_step(step_id, status="success", output=result)
                    self._handle_output(step['id'], step["output"], result, step)
        
            if mark_visited:
                visit_key = self._get_visit_key(step)
                self.context["visited_steps"].add(visit_key)
        
            return
        else:
            try:
                if 'agent' in step:
                    agent = self.agents[step['agent']]
                    
                    # Initialize navigation_choice for this agent step
                    navigation_choice = None
                    
                    # NAVIGATION SUPPORT: Check if this step has navigation config
                    if 'navigation' in step:
                        # Set up navigation context for the agent
                        from langswarm.features.intelligent_navigation.navigator import NavigationContext
                        nav_context = NavigationContext(
                            workflow_id=self.workflow_id,
                            current_step=step['id'],
                            context_data=self.context,
                            step_history=self.context.get('step_history', []),
                            available_steps=step['navigation'].get('available_steps', [])
                        )
                        
                        # Store navigation context in agent if it has the capability
                        if hasattr(agent, 'navigation_context'):
                            agent.navigation_context = nav_context
                    
                    # Execute agent
                    raw_input = step.get("input")
                    if isinstance(raw_input, dict):
                        resolved = {k: self._resolve_input(v) for k, v in raw_input.items()}
                        output = agent.chat(f"{resolved}")
                    else:
                        output = agent.chat(self._resolve_input(raw_input))
                    
                    # NAVIGATION SUPPORT: Check if agent made a navigation choice
                    if 'navigation' in step:
                        navigation_choice = self._extract_navigation_choice(output, step)
                        
                        if navigation_choice:
                            # Agent chose a navigation step
                            chosen_step = navigation_choice['step_id']
                            reasoning = navigation_choice.get('reasoning', '')
                            confidence = navigation_choice.get('confidence', 1.0)
                            
                            # Track navigation decision
                            self._track_navigation_decision(step['id'], chosen_step, reasoning, confidence)
                            
                            # Create navigation result
                            output = {
                                'navigation_choice': chosen_step,
                                'reasoning': reasoning,
                                'confidence': confidence,
                                'response': output
                            }
                            
                            # Store result and route to chosen step
                            self.context['previous_output'] = output
                            self.context['step_outputs'][step['id']] = output
                            
                            # Mark this step as visited
                            if mark_visited:
                                self.context["visited_steps"].add(visit_key)
                            
                            # Route to chosen step
                            self._route_to_step(chosen_step, output)
                            return
        
                elif 'function' in step:
                    func = self._resolve_function(step['function'], script=step.get('script'))
                    args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
                    args.setdefault("context", self.context)
                    try:
                        output = func(**args)
                    except Exception as e:
                        import traceback
                        tb = traceback.format_exc()
                        print(f"\n🚨 Exception in function `{step['function']}`:\n{tb}")
                        raise  # Re-raise to keep workflow intelligence working
        
                    if output == "__NOT_READY__":
                        fan_key = step.get("fan_key", "default")
                        self.context["pending_fanins"][f"{step_id}@{fan_key}"] = step
                        return
                else:
                    raise ValueError(f"⚠️ Step {step_id} missing 'agent' or 'function'")
    
            except Exception as e:
                self._handle_step_error(step, step_id, visit_key, e)
        
        output = self._make_output_serializable(output)
        if isinstance(output, (pd.DataFrame, pd.Series, np.ndarray)):
            print(f"⚠️ Auto-converted non-serializable output ({type(output).__name__}) to JSON-safe format.")
        
        # Explicitly store outputs regardless of conditional steps:
        self.context['previous_output'] = output
        self.context['step_outputs'][step_id] = output
        
        if "output" in step:
            self.intelligence.end_step(step_id, status="success", output=output)
            to_targets = step["output"].get("to", [])
            if not isinstance(to_targets, list):
                to_targets = [to_targets]
        
            if any(isinstance(t, dict) and "condition" in t for t in to_targets):
                self._handle_output(step_id, step["output"], output, step)
                if mark_visited:
                    self.context["visited_steps"].add(visit_key)
                return  # Important: return here explicitly after handling condition
            else:
                self._handle_output(step_id, step["output"], output, step)
        
        if mark_visited:
            self.context["visited_steps"].add(visit_key)
        
        if step.get("fan_key"):
            self._recheck_pending_fanins()

    def _handle_output(
        self,
        step_id: str,
        output_def: Dict,
        output: str,
        step: Optional[Dict] = None,
    ) -> None:
        """
        Route the `output` of *step_id* to the targets declared in its YAML.

        • Strings in `to:` are interpreted as step‑ids or the literal `"user"`.
        • Dict targets (`{"step": …}`, `{"condition": …}` …) are handled too.
        • If the target step is a **fan‑in** (marked `is_fan_in = True`) we only
          queue it in `context["pending_fanins"][fan_key]`; it will be executed by
          the periodic re‑check once *all* required fan‑out steps complete.
        """

        print("output_def:", output_def)
        targets = output_def.get("to", [])
        if not isinstance(targets, list):
            targets = [targets]

        print(f"\n🗣  Step \"{step_id}\" produced output:\n{output}\n")

        fan_key = step.get("fan_key") if step else None

        for target in targets:
            # ────────────────────────────────────────────────────────────────
            # 1️⃣ target supplied as **plain string**
            # ────────────────────────────────────────────────────────────────
            if isinstance(target, str):

                # 1a. send to user ----------------------------------------------------------------
                if target == "user":
                    # ── keep whichever branch you already use ───────────
                    if hasattr(self, "message_broker") and self.message_broker:
                        self.message_broker.return_to_user(
                            output,
                            context={"step_id": step_id,
                                     "request_id": self.context.get("request_id")},
                        )
                    else:                                                # ← fallback
                        self.context["user_output"] = output
                    print("💬  Output was returned to user\n")
                    continue  # nothing else to do for the "user" pseudo‑step

                # 1b. normal step‑id ----------------------------------------------------------------
                    
                #print("target:", target)
                target_step = self._get_step_by_id(target)

                # If it's a fan‑in we just queue it
                if fan_key and target_step.get("is_fan_in"):
                    self.context["pending_fanins"].setdefault(fan_key, set()).add(
                        target_step["id"]
                    )
                    continue
                    
                #print("target_step:", target_step)

                # otherwise execute immediately
                self._execute_step(target_step)
                continue  # ----- next target --------------------------------------

            # ────────────────────────────────────────────────────────────────
            # 2️⃣ target supplied as **dict**
            # ────────────────────────────────────────────────────────────────
            if isinstance(target, dict):

                # 2a. {"step": …}
                if "step" in target:
                    target_step = self._get_step_by_id(target["step"])

                    if fan_key and target_step.get("is_fan_in"):
                        self.context["pending_fanins"].setdefault(fan_key, set()).add(
                            target_step["id"]
                        )
                    else:
                        self._execute_step(target_step)

                # 2b. {"invoke": subflow_id}
                elif "invoke" in target:
                    self._run_subflow(
                        subflow_id=target["invoke"],
                        input_text=output,
                        await_response=target.get("await", False),
                    )

                # 2c. {"condition": {...}}
                elif isinstance(target, dict) and "condition" in target:
                    branch = self._resolve_condition_branch(target.get("condition"))
                    if branch:
                        if isinstance(branch, str):
                            # It's a direct step id → load and execute
                            target_step = self._get_step_by_id(branch)
                            self._execute_step(target_step)
                        elif isinstance(branch, dict):
                            # It's a nested output → treat it as another output instruction
                            self._handle_output(step_id, {"to": branch}, output, step)
                    
                    # ✅ VERY IMPORTANT
                    return  # STOP here — don't fall through and save 'True/False' as output

                # 2d. {"generate_steps": ...}
                elif "generate_steps" in target:
                    self._run_generated_subflow(
                        input_text=output,
                        limit=target.get("limit"),
                        return_to=target.get("return_to"),
                    )

    async def _handle_output_async(self, step_id, output_def, output, step):
        targets = output_def.get("to", [])
        if not isinstance(targets, list):
            targets = [targets]

        fan_key = step.get("fan_key")
        tasks = []
        
        # -----------------------------------------------------------
        # inside async _handle_output_async()
        # -----------------------------------------------------------
        for target in targets:

            # ─────────── target is a plain string id ───────────
            if isinstance(target, str):
                if target == "user":
                    if hasattr(self, "message_broker") and self.message_broker:
                        self.message_broker.return_to_user(
                            output,
                            context={"step_id": step_id,
                                     "request_id": self.context.get("request_id")}
                        )
                    else:
                        self.context["user_output"] = output
                    print("\n💬 Output was returned to user")
                    continue

                # normal "step id"
                target_step = self._get_step_by_id(target)
                if fan_key:
                    target_step["fan_key"] = fan_key
                    #  🆕  Only register fan‑in steps – do NOT schedule them here
                    if target_step.get("is_fan_in"):
                        self.context["pending_fanins"].setdefault(fan_key, set()).add(target_step["id"])
                        continue                # <-- do NOT add to tasks
                
                tasks.append(self._execute_step_async(target_step))

            # ─────────── target is a mapping (dict) ───────────
            elif isinstance(target, dict):
                if "step" in target:
                    target_step = self._get_step_by_id(target["step"])
                    if fan_key:
                        target_step["fan_key"] = fan_key
                        if target_step.get("is_fan_in"):
                            self.context["pending_fanins"].setdefault(fan_key, set()).add(target_step["id"])
                            continue                # <-- do NOT add to tasks
                    
                    tasks.append(self._execute_step_async(target_step))

                elif "invoke" in target:
                    await self._run_subflow_async(target['invoke'], output, await_response=target.get("await", False))

                elif isinstance(target, dict) and "condition" in target:
                    branch = self._resolve_condition_branch(target.get("condition"))
                    if branch:
                        if isinstance(branch, str):
                            target_step = self._get_step_by_id(branch)
                            await self._execute_step_async(target_step)
                        elif isinstance(branch, dict):
                            await self._handle_output_async(step_id, {"to": branch}, output, step)
    
                    # ✅ VERY IMPORTANT
                    return  # STOP here — don't fall through and save 'True/False' as output

                elif "generate_steps" in target:
                    await self._run_generated_subflow_async(output, limit=target.get("limit"), return_to=target.get("return_to"))

        # 🚀 Run all async fan-out tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)

    def _get_step_by_id(self, step_id: str) -> Dict:
        step = next((s for s in self._get_workflow(self.context["current_workflow_id"])["steps"] if s["id"] == step_id), None)
        if not step:
            raise ValueError(f"Workflow step '{step_id}' not found in current workflow.")
        return step
    
    def _execute_by_step_id(self, step_id: str, await_response: bool = True, mark_visited: bool = True, fan_key: Optional[str] = None):
        step = self._get_step_by_id(step_id)
        if step:
            self._execute_step(step, mark_visited=mark_visited, fan_key=fan_key)

    def _run_subflow(self, subflow_id: str, input_text: str, await_response: bool = True):
        subflow = next((s for s in self.workflows.get("subflows", []) if s['id'] == subflow_id), None)
        if not subflow:
            print(f"⚠️ Subflow {subflow_id} not found.")
            return

        func = self._resolve_function(subflow['entrypoint'])
        mapped_input = {
            k: self._resolve_input(v) for k, v in subflow.get("input_map", {}).items()
        }
        result = func(**mapped_input)

        if await_response and subflow.get("return_to"):
            self.context['previous_output'] = result
            print(f"\n🔁 Returning output to step: {subflow['return_to']}")
            self._execute_by_step_id(subflow["return_to"])

    def _run_generated_subflow(self, input_text: str, limit: int = 3, return_to: Optional[str] = None):
        for i in range(limit):
            print(f"\n🌀 Iteration {i+1}/{limit}")
            output = f"Step {i+1} based on: {input_text}"
            self.context['previous_output'] = output

        if return_to:
            self._execute_by_step_id(return_to)

    def _evaluate_condition(self, expr: str) -> bool:
        resolved_expr = self._resolve_input(expr)
        s = SimpleEval(names=self.context)
        try:
            return bool(s.eval(resolved_expr))
        except Exception as e:
            print(f"Condition eval error: {e}")
            print(f"Resolved expr was: {resolved_expr}")
            return False

    def _evaluate_expression(self, expr: str):
        """
        Safely resolves dot-separated access into self.context,
        e.g., 'context.step_outputs.fetch' → self.context['step_outputs']['fetch']
        """
        try:
            if not expr.startswith("context."):
                raise ValueError("Only access to 'context.*' is allowed")

            parts = expr.split(".")[1:]  # drop 'context'
            value = self.context
            for part in parts:
                if isinstance(value, dict):
                    value = value[part]
                elif isinstance(value, list):
                    value = value[int(part)]
                else:
                    raise TypeError(f"Cannot access '{part}' on non-container: {value}")
            return value

        except Exception as e:
            print(f"⚠️ Failed to resolve '${{{expr}}}': {e}")
            return f"<error:{expr}>"

    def _resolve_input(self, value):
        # Handle special wrapped types first
        if isinstance(value, dict) and "__type__" in value:
            t = value["__type__"]
            if t == "DataFrame":
                return pd.DataFrame(**value["value"])
            elif t == "Series":
                return pd.Series(value["value"])
            elif t == "ndarray":
                return np.array(value["value"])
    
        # Resolve single variable reference → return native type
        if isinstance(value, str):
            pattern = re.compile(r"\${([^}]+)}")
            matches = pattern.findall(value)
    
            if len(matches) == 1 and value.strip() == f"${{{matches[0]}}}":
                keys = matches[0].split(".")
                if keys[0] == "context":
                    keys = keys[1:]
                return self._safe_resolve(keys, self.context)
    
            # Otherwise resolve inline substitutions
            for match in matches:
                try:
                    keys = match.split(".")
                    if keys[0] == "context":
                        keys = keys[1:]
                    resolved = self._safe_resolve(keys, self.context)
                    value = value.replace(f"${{{match}}}", str(resolved))
                except Exception as e:
                    print(f"⚠️ Failed to resolve: ${{{match}}} — {e}")
            return value
    
        # Recursively resolve containers
        if isinstance(value, dict):
            return {k: self._resolve_input(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_input(v) for v in value]
    
        return value

    def _safe_resolve(self, path_parts, context):
        current = context
        for part in path_parts:
            # Handle indexed access like [0]
            if "[" in part and "]" in part:
                base, index = re.match(r"(.*?)\[(\d+)\]", part).groups()
                current = current[base][int(index)]
            else:
                current = current[part]
        return current
   
    def _resolve_function(self, path: str, script: Optional[str] = None):
        if script:
            # Compile the script and extract the function
            local_namespace = {}
            exec(script, {}, local_namespace)
            func_name = path.split(".")[-1]
            return local_namespace[func_name]

        # Otherwise, load from module
        parts = path.split(".")
        module_name = ".".join(parts[:-1])
        func_name = parts[-1]
        module = importlib.import_module(module_name)
        return getattr(module, func_name)

    def _get_workflow(self, workflow_id: str) -> Dict:
        workflow = next((wf for wf in self.workflows.get("main_workflow", []) if wf['id'] == workflow_id), None)

        if not workflow:
            workflow = self.workflows.get("main_workflow", [{}])[0]

        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found. Ensure your workflows.yaml file starts with:\n\nworkflows:\n   main_workflow:...")

        # ⬇️ Grab intelligence settings if they exist in the workflow
        settings = workflow.get("settings", {}).get("intelligence", {})
        self.intelligence.config.update(settings)

        # Map fan_keys to steps
        fan_key_to_steps = {}
        explicit_fan_in_map = {}

        for step in workflow.get("steps", []):
            fan_key = step.get("fan_key")
            if fan_key:
                fan_key_to_steps.setdefault(fan_key, []).append(step)

                # Capture explicit fan-in if provided
                if "fan_in_id" in step:
                    explicit_fan_in_map[fan_key] = step["fan_in_id"]

        # Mark fan-in steps
        for fan_key, steps in fan_key_to_steps.items():
            fan_in_id = explicit_fan_in_map.get(fan_key)
            if fan_in_id:
                fan_in_step = next((s for s in steps if s["id"] == fan_in_id), None)
            else:
                fan_in_step = steps[-1]  # Fallback: last one with same fan_key

            if fan_in_step:
                fan_in_step["is_fan_in"] = True

        return workflow

class ToolDeployer:
    """
    Deploy any containerized MCP tool via Terraform.
    Accepts the list of raw tool‑definitions you loaded from tools.yaml.
    """

    def __init__(self, tools):
        # Grab the raw tool‑configs
        if isinstance(tools, list):
            self.tools = {cfg["id"]: cfg for cfg in tools}
        else:
            self.tools = tools
        # map tool_id → {container_name, image_name}
        self._deploy_info = {}
        
    def cleanup(self, tool_id: str) -> None:
        """
        Stop and remove a Cloud Run–emulated Docker container, and optionally
        delete its image.

        :param container_name: the local container you spun up (default: mcp-summarizer-dev)
        :param image_name:  if provided, the name/tag of the image to remove
        """
        import docker
        
        client = docker.from_env()

        info = self._deploy_info.get(tool_id)
        
        tool = self.tools.get(tool_id, {})
        
        print("tool: ", dir(tool))
        
        cfg = (
            (tool.get("settings") if isinstance(tool, dict) else None)
            or getattr(tool, "settings", {})
            or {}
        )
        
        # fallback to defaults if somehow deploy() wasn't called
        container_name = info["container_name"] if info else f"{tool_id}-mcp-container"
        image_name     = info["image_name"]     if info else cfg["image"]

        # stop & remove container
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
            print(f"✅ Stopped and removed container '{container_name}'")
        except docker.errors.NotFound:
            print(f"⚠️ Container '{container_name}' not found")

        # remove image, if asked
        if image_name:
            try:
                client.images.remove(image=image_name, force=True)
                print(f"🗑️ Removed image '{image_name}'")
            except docker.errors.ImageNotFound:
                print(f"⚠️ Image '{image_name}' not found")

    def deploy(
        self,
        tool_id: str,
        state_bucket: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """
        1) look up the tool.yaml entry by tool_id
        2) resolve any env:FOO entries
        3) write terraform.tfvars.json
        4) terraform init/apply (with optional remote GCS state)
        """
        if tool_id not in self.tools:
            raise ValueError(f"Tool '{tool_id}' not found in loaded configs")
        
        tool = self.tools.get(tool_id, {})
        cfg = (
            (tool.get("settings") if isinstance(tool, dict) else None)
            or getattr(tool, "settings", {})
            or {}
        )
        
        if cfg is None:
            raise ValueError(f"Tool '{tool_id}' does not have any settings.")

        env_map = cfg.get("env", {})
        # resolve any env: prefix
        resolved = {
            k: (os.getenv(v.split("env:",1)[1], "") if isinstance(v, str) and v.startswith("env:") else v)
            for k, v in env_map.items()
        }
        
        # pick whatever convention you like:
        container_name = f"{tool_id}-mcp-container"
        
        if cfg.get("image", None) is None:
            image = cfg.get("image")
            github_url = cfg.get("github_url")
            registry_url = cfg.get("to_registry_url")
            context_path = cfg.get("build_context_path", ".")

            # If image is not defined but github_url is present, build locally
            if not image and github_url:
                print(f"🔍 No image defined. Cloning and building from: {github_url}")
                with tempfile.TemporaryDirectory() as tmpdir:
                    repo_path = Path(tmpdir) / "repo"
                    self._clone_repo(github_url, str(repo_path))

                    # Resolve the build context inside the repo
                    build_context = repo_path / context_path
                    if not build_context.exists():
                        print(f"❌ Build context path '{build_context}' does not exist.")
                        sys.exit(1)

                    # Build the image locally
                    self._build_docker_image(str(build_context), tool_id)

                    # If registry is defined, push the image and update YAML
                    if registry_url:
                        cfg["image"] = self._push_docker_image(tool_id, registry_url)
                    else:
                        print(f"✅ Built image '{tool_id}' locally (not pushed).")
            else:
                print(f"❌ Both image and github_url is missing for '{tool_id}'. There is no code to build from.")
        
        mode = cfg.get("mode", "http")  # 🔥 NEW: support 'stdio' mode alongside 'http'

        if mode == 'stdio':  # 🔥 NEW: stdio‑mode deployment
            print(f"🔥 StdIO‑mode tool '{tool_id}' is deployed upon tool call.")
            return
        
        if cfg.get("deployment_target", None) == 'gcp':
            tfvars = {
                "tool_id":    tool_id,
                "image":      cfg["image"],
                "port":       cfg["port"],
                "mode":       cfg.get("mode", "http"),
                "env_vars":   resolved,
                "region":     cfg.get("region", "us-central1"),
                "project_id": project_id or cfg.get("project_id") or os.getenv("GCP_PROJECT_ID",""),
            }

            # dump tfvars into your module folder
            tfvars_path = "terraform/deploy/terraform.tfvars.json"
            with open(tfvars_path, "w") as out:
                json.dump(tfvars, out, indent=2)

            # terraform init
            init_cmd = [
                "terraform", "-chdir=terraform/deploy", "init"
            ]
            
            state_bucket = cfg.get("state_bucket", state_bucket)
            if state_bucket:
                init_cmd += ["-backend-config", f"bucket={state_bucket}"]

            subprocess.run(init_cmd, check=True)

            # terraform apply
            subprocess.run([
                "terraform", "-chdir=terraform/deploy",
                "apply", "-var-file=terraform.tfvars.json", "-auto-approve"
            ], check=True)

            print(f"🚀 Tool '{tool_id}' deployed to GCP!")
        else:
            # local mode
            print(f"🚀 Deploying tool '{tool_id}' locally...")
            image   = cfg.get("image", f"mcp-{tool_id}")
            port    = cfg.get("port", 3000)
            mode    = cfg.get("mode", "http")

            # Deploy the Docker container locally
            payload = None  # If your tool needs custom JSON, pass it here

            result = self._deploy_locally_via_docker(
                image=image,
                name=container_name,
                env_vars=resolved,
                port=port,
                mode=mode,
                payload=payload,
            )

            self._deploy_info[tool_id] = {
                "container_name": container_name,
                "image_name": image,
                "local_url": f"http://localhost:{port}" if mode == "http" else None,
                "deployment_info": result,
            }

            print(f"✅ Tool '{tool_id}' is running locally!")
            return result

    def _running_in_docker(self) -> bool:
        """Check if we're already inside a Docker container to avoid Docker-in-Docker issues."""
        try:
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                return "docker" in content or "container" in content
        except (FileNotFoundError, PermissionError):
            # /proc/1/cgroup might not be accessible on all systems
            return os.path.exists("/.dockerenv")
    
    def _deploy_locally_via_docker(
        self,
        image: str,
        name: str,
        env_vars: dict,
        port: Optional[int] = None,
        mode: str = "http",
        payload: Optional[str] = None,
    ) -> Union[bool, Dict[str, Any]]:
        """
        Deploy a tool locally using Docker, mimicking Cloud Run behavior.
        
        :param image: Docker image name/tag
        :param name: Container name
        :param env_vars: Environment variables to pass to the container
        :param port: Port to expose (for http mode)
        :param mode: 'http' or 'stdio'
        :param payload: Optional JSON payload to send (for stdio mode)
        :return: True if successful, or dict with container info
        """
        import docker
        
        # Check if we're running inside Docker
        if self._running_in_docker():
            print("⚠️ Running inside Docker container - using host network mode")
            network_mode = "host"
        else:
            network_mode = None
        
        try:
            client = docker.from_env()
            
            # Check if container with this name already exists
            try:
                existing = client.containers.get(name)
                print(f"🔄 Container '{name}' already exists. Stopping and removing...")
                existing.stop()
                existing.remove()
            except docker.errors.NotFound:
                pass
            
            if mode == "stdio":
                # For stdio mode, run container and pipe input/output
                print(f"🔧 Running stdio-mode container: {image}")
                
                container = client.containers.run(
                    image=image,
                    name=name,
                    environment=env_vars,
                    detach=False,
                    stdin_open=True,
                    tty=False,
                    network_mode=network_mode,
                    remove=True,  # Auto-remove after execution
                    input=payload.encode() if payload else None
                )
                
                # Return the output
                return {
                    "mode": "stdio",
                    "output": container.decode() if isinstance(container, bytes) else str(container),
                    "success": True
                }
                
            else:  # http mode
                print(f"🌐 Starting HTTP container: {image} on port {port}")
                
                # Port mapping for HTTP mode
                ports = {f"{port}/tcp": port} if port and network_mode != "host" else None
                
                container = client.containers.run(
                    image=image,
                    name=name,
                    environment=env_vars,
                    ports=ports,
                    detach=True,
                    network_mode=network_mode,
                    restart_policy={"Name": "unless-stopped"}
                )
                
                print(f"✅ Container '{name}' started successfully")
                print(f"🔗 Available at: http://localhost:{port}")
                
                return {
                    "mode": "http",
                    "container_id": container.id,
                    "container_name": name,
                    "port": port,
                    "url": f"http://localhost:{port}",
                    "success": True
                }
                
        except docker.errors.ImageNotFound:
            print(f"❌ Docker image '{image}' not found. Please build or pull the image first.")
            return False
        except docker.errors.APIError as e:
            print(f"❌ Docker API error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error deploying container: {e}")
            return False
            
    def _clone_repo(self, git_url, dest_dir):
        subprocess.run(["git", "clone", git_url, dest_dir], check=True)

    def _build_docker_image(self, context_dir: str, tag: str):
        subprocess.run(["docker", "build", "-t", tag, context_dir], check=True)

    def _push_docker_image(self, tag: str, registry_url: str):
        full_tag = f"{registry_url}/{tag}"
        subprocess.run(["docker", "tag", tag, full_tag], check=True)
        subprocess.run(["docker", "push", full_tag], check=True)
        return full_tag


# Missing workflow execution methods for LangSwarmConfigLoader
def _add_workflow_methods_to_config_loader():
    """Add missing workflow execution methods to LangSwarmConfigLoader"""
    
    def run_workflow(self, workflow_id: str, user_input: str = "", **kwargs):
        """
        Execute a workflow with the given input.
        
        Args:
            workflow_id: ID of the workflow to execute
            user_input: Input text for the workflow
            **kwargs: Additional parameters for workflow execution
            
        Returns:
            Workflow execution result
        """
        # Initialize workflow context
        self.context = {
            'user_input': user_input,
            'previous_output': None,
            'step_outputs': {},
            'visited_steps': set(),
            'retry_counters': {},
            'pending_fanins': {},
            **kwargs
        }
        
        # Get the workflow
        workflow = self._get_workflow(workflow_id)
        
        # Execute workflow steps
        if workflow and workflow.get('steps'):
            for step in workflow['steps']:
                # Execute each step
                self._execute_step(step)
            
            # Return the final output
            return self.context.get('previous_output', "Workflow completed")
        else:
            raise ValueError(f"Workflow '{workflow_id}' has no steps to execute")
    
    async def run_workflow_async(self, workflow_id: str, user_input: str = "", **kwargs):
        """
        Execute a workflow asynchronously with the given input.
        
        Args:
            workflow_id: ID of the workflow to execute
            user_input: Input text for the workflow
            **kwargs: Additional parameters for workflow execution
            
        Returns:
            Workflow execution result
        """
        # Initialize workflow context
        self.context = {
            'user_input': user_input,
            'previous_output': None,
            'step_outputs': {},
            'visited_steps': set(),
            'retry_counters': {},
            'pending_fanins': {},
            **kwargs
        }
        
        # Get the workflow
        workflow = self._get_workflow(workflow_id)
        
        # Execute workflow steps asynchronously
        if workflow and workflow.get('steps'):
            for step in workflow['steps']:
                # Execute each step asynchronously
                await self._execute_step_async(step)
            
            # Return the final output
            return self.context.get('previous_output', "Workflow completed")
        else:
            raise ValueError(f"Workflow '{workflow_id}' has no steps to execute")
    
    # Add methods to the class
    LangSwarmConfigLoader.run_workflow = run_workflow
    LangSwarmConfigLoader.run_workflow_async = run_workflow_async

# Apply the missing methods
_add_workflow_methods_to_config_loader()


class WorkflowExecutor:
    """
    Workflow execution wrapper for legacy compatibility.
    
    This class provides a simplified interface for executing workflows
    loaded via LangSwarmConfigLoader, maintaining backward compatibility
    with existing code that expects a separate WorkflowExecutor class.
    """
    
    def __init__(self, workflows: Dict[str, Any], agents: Dict[str, Any], **kwargs):
        """
        Initialize WorkflowExecutor with loaded workflows and agents.
        
        Args:
            workflows: Dictionary of workflows from LangSwarmConfigLoader.load()
            agents: Dictionary of agents from LangSwarmConfigLoader.load()
            **kwargs: Additional configuration options
        """
        self.workflows = workflows
        self.agents = agents
        self.config_kwargs = kwargs
        
        # Create a minimal config loader instance for workflow execution
        self._config_loader = None
        self._initialize_config_loader()
    
    @property
    def context(self):
        """Access the workflow execution context from the underlying config loader"""
        if self._config_loader and hasattr(self._config_loader, 'context'):
            return self._config_loader.context
        return {}
    
    @context.setter  
    def context(self, value):
        """Set the workflow execution context on the underlying config loader"""
        if self._config_loader:
            self._config_loader.context = value
        else:
            # Store for later initialization
            self._pending_context = value
    
    def _initialize_config_loader(self):
        """Initialize a config loader instance for workflow execution"""
        try:
            # Create a minimal config loader with the provided data
            self._config_loader = LangSwarmConfigLoader()
            self._config_loader.workflows = self.workflows
            self._config_loader.agents = self.agents
            
            # Set up minimal required attributes
            self._config_loader.tools = {}
            self._config_loader.tools_metadata = {}
            self._config_loader.brokers = {}
            self._config_loader.config_data = {
                'workflows': self.workflows,
                'agents': []  # Leave empty - agents are already initialized instances
            }
            
            # Initialize formatting utilities if needed
            if not hasattr(self._config_loader, 'formatting_utils'):
                from langswarm.core.utils.subutilities.formatting import Formatting
                self._config_loader.formatting_utils = Formatting()
            
            # Initialize workflow intelligence if needed
            if not hasattr(self._config_loader, 'intelligence'):
                from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence
                self._config_loader.intelligence = WorkflowIntelligence()
            
            # Apply any pending context that was set before initialization
            if hasattr(self, '_pending_context'):
                self._config_loader.context = self._pending_context
                delattr(self, '_pending_context')
                
        except Exception as e:
            print(f"⚠️ Warning: Could not fully initialize WorkflowExecutor: {e}")
            print("⚠️ Some advanced workflow features may not be available")
            self._config_loader = None
    
    def run_workflow(self, workflow_id: str, user_input: str = "", **kwargs) -> str:
        """
        Execute a workflow and return the result.
        
        Args:
            workflow_id: ID of the workflow to execute
            user_input: Input text for the workflow (supports both user_input and **kwargs)
            **kwargs: Additional parameters, including legacy user_input parameter
            
        Returns:
            str: Workflow execution result
            
        Example:
            executor = WorkflowExecutor(workflows, agents)
            result = executor.run_workflow("simple_filesystem_workflow", user_input="Read file.txt")
        """
        # Handle legacy parameter names
        if 'user_input' in kwargs:
            user_input = kwargs.pop('user_input')
        
        if not self._config_loader:
            return f"❌ WorkflowExecutor not properly initialized - cannot execute workflow '{workflow_id}'"
        
        try:
            # Execute the workflow using the config loader
            result = self._config_loader.run_workflow(workflow_id, user_input, **kwargs)
            return str(result) if result is not None else "Workflow completed successfully"
            
        except Exception as e:
            error_msg = f"❌ Workflow execution error: {e}"
            print(error_msg)
            return error_msg
    
    async def run_workflow_async(self, workflow_id: str, user_input: str = "", **kwargs) -> str:
        """
        Execute a workflow asynchronously and return the result.
        
        Args:
            workflow_id: ID of the workflow to execute
            user_input: Input text for the workflow
            **kwargs: Additional parameters
            
        Returns:
            str: Workflow execution result
        """
        # Handle legacy parameter names
        if 'user_input' in kwargs:
            user_input = kwargs.pop('user_input')
            
        if not self._config_loader:
            return f"❌ WorkflowExecutor not properly initialized - cannot execute workflow '{workflow_id}'"
        
        try:
            # Execute the workflow asynchronously using the config loader
            result = await self._config_loader.run_workflow_async(workflow_id, user_input, **kwargs)
            return str(result) if result is not None else "Workflow completed successfully"
            
        except Exception as e:
            error_msg = f"❌ Async workflow execution error: {e}"
            print(error_msg)
            return error_msg
    
    def get_available_workflows(self) -> List[str]:
        """
        Get list of available workflow IDs.
        
        Returns:
            List[str]: List of workflow IDs
        """
        if isinstance(self.workflows, dict):
            # Handle main_workflow structure
            main_workflows = self.workflows.get('main_workflow', [])
            if isinstance(main_workflows, list):
                return [wf.get('id', f'workflow_{i}') for i, wf in enumerate(main_workflows)]
            return list(self.workflows.keys())
        return []
    
    def get_workflow_info(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get information about a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict[str, Any]: Workflow information
        """
        try:
            if self._config_loader:
                workflow = self._config_loader._get_workflow(workflow_id)
                return {
                    'id': workflow.get('id', workflow_id),
                    'name': workflow.get('name', 'Unnamed Workflow'),
                    'steps': len(workflow.get('steps', [])),
                    'description': workflow.get('description', 'No description available')
                }
        except Exception as e:
            return {
                'id': workflow_id,
                'error': f"Could not retrieve workflow info: {e}"
            }
        
        return {'id': workflow_id, 'error': 'Workflow not found'}
