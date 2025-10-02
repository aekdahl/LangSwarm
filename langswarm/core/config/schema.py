"""
LangSwarm V2 Configuration Schema

Comprehensive, type-safe configuration schema with validation, defaults,
and migration support. Replaces the monolithic 4,600+ line config.py with
a clean, modular system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Literal
from enum import Enum
import uuid
from datetime import datetime


class LogLevel(Enum):
    """Logging levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG" 
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProviderType(Enum):
    """LLM Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    COHERE = "cohere"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    MOCK = "mock"


class MemoryBackend(Enum):
    """Memory backend types"""
    IN_MEMORY = "in_memory"
    SQLITE = "sqlite"
    REDIS = "redis"
    POSTGRES = "postgres"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    AUTO = "auto"


class WorkflowEngine(Enum):
    """Workflow execution engines"""
    V2_NATIVE = "v2_native"
    PROMPT_FLOW = "prompt_flow"
    LANGCHAIN = "langchain"
    AUTO = "auto"


@dataclass
class AgentConfig:
    """Clean agent configuration"""
    id: str
    name: Optional[str] = None
    provider: ProviderType = ProviderType.OPENAI
    model: str = "gpt-4o"
    
    # Core settings
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    
    # Advanced settings
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    
    # LangSwarm features
    tools: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    streaming: bool = False
    
    # Provider-specific config
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and set defaults"""
        if not self.name:
            self.name = self.id.replace("_", " ").title()
        
        # Validate temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {self.temperature}")
        
        # Validate max_tokens
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")


@dataclass
class ToolConfig:
    """Unified tool configuration"""
    id: str
    type: str  # tool type (memory, utility, workflow, etc.)
    enabled: bool = True
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Access control
    allowed_agents: Optional[List[str]] = None
    
    # Metadata
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set defaults"""
        if not self.name:
            self.name = self.id.replace("_", " ").title()


@dataclass  
class WorkflowConfig:
    """Clean workflow configuration"""
    id: str
    name: Optional[str] = None
    engine: WorkflowEngine = WorkflowEngine.V2_NATIVE
    
    # Workflow definition
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Simple syntax support (V1 compatibility)
    simple_syntax: Optional[str] = None
    
    # Execution settings
    parallel: bool = False
    timeout: Optional[int] = None
    retry_count: int = 0
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set defaults and validate"""
        if not self.name:
            self.name = self.id.replace("_", " ").title()
        
        # Convert simple syntax to steps if provided
        if self.simple_syntax and not self.steps:
            self.steps = self._parse_simple_syntax(self.simple_syntax)
    
    def _parse_simple_syntax(self, syntax: str) -> List[Dict[str, Any]]:
        """Parse simple workflow syntax (V1 compatibility)"""
        # Basic implementation - would be expanded for full V1 compatibility
        steps = []
        parts = [part.strip() for part in syntax.split("->")]
        
        for i, part in enumerate(parts):
            if part.lower() == "user":
                # Final output step
                steps.append({
                    "type": "output",
                    "target": "user"
                })
            else:
                # Agent step
                steps.append({
                    "type": "agent",
                    "agent_id": part,
                    "output_key": f"step_{i}_output"
                })
        
        return steps


@dataclass
class MemoryConfig:
    """Simplified memory configuration"""
    enabled: bool = True
    backend: MemoryBackend = MemoryBackend.AUTO
    
    # Backend settings
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Session settings
    max_messages: int = 100
    auto_summarize: bool = True
    summary_threshold: int = 50
    
    # Advanced settings
    ttl_seconds: Optional[int] = None
    compression: bool = False


@dataclass
class SecurityConfig:
    """Security and authentication settings"""
    
    # API Keys (environment variables)
    openai_api_key_env: str = "OPENAI_API_KEY"
    anthropic_api_key_env: str = "ANTHROPIC_API_KEY"
    gemini_api_key_env: str = "GEMINI_API_KEY"
    cohere_api_key_env: str = "COHERE_API_KEY"
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: Optional[int] = None
    
    # Access control
    allowed_hosts: Optional[List[str]] = None
    require_auth: bool = False
    
    # Data protection
    encrypt_memory: bool = False
    log_sensitive_data: bool = False


@dataclass
class ObservabilityConfig:
    """Observability and monitoring settings"""
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_file: Optional[str] = None
    structured_logging: bool = True
    
    # Tracing
    tracing_enabled: bool = False
    trace_sample_rate: float = 1.0
    trace_output_file: Optional[str] = None
    
    # Metrics
    metrics_enabled: bool = False
    metrics_port: int = 8080
    
    # Health checks
    health_check_enabled: bool = True
    health_check_port: int = 8081


@dataclass
class ServerConfig:
    """Server and API configuration"""
    
    # Basic settings
    host: str = "localhost"
    port: int = 8000
    workers: int = 1
    
    # Advanced settings
    reload: bool = False
    ssl_enabled: bool = False
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    
    # CORS
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class LangSwarmConfig:
    """
    Main LangSwarm V2 configuration.
    
    Clean, modular configuration that replaces the 4,600+ line monolithic
    config.py with a type-safe, validated system.
    """
    
    # Metadata
    version: str = "2.0"
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Core components
    agents: List[AgentConfig] = field(default_factory=list)
    tools: Dict[str, ToolConfig] = field(default_factory=dict)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    
    # System configuration
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # Advanced settings
    experimental_features: Dict[str, bool] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Multi-file configuration support
    includes: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate()
    
    def _validate(self):
        """Comprehensive configuration validation"""
        errors = []
        
        # Validate unique agent IDs
        agent_ids = set()
        for agent in self.agents:
            if agent.id in agent_ids:
                errors.append(f"Duplicate agent ID: {agent.id}")
            agent_ids.add(agent.id)
        
        # Validate tool references in agents
        for agent in self.agents:
            for tool_id in agent.tools:
                if tool_id not in self.tools:
                    errors.append(f"Agent {agent.id} references unknown tool: {tool_id}")
        
        # Validate workflow agent references
        for workflow in self.workflows:
            for step in workflow.steps:
                if step.get("type") == "agent":
                    agent_id = step.get("agent_id")
                    if agent_id and agent_id not in agent_ids:
                        errors.append(f"Workflow {workflow.id} references unknown agent: {agent_id}")
        
        # Validate unique workflow IDs
        workflow_ids = set()
        for workflow in self.workflows:
            if workflow.id in workflow_ids:
                errors.append(f"Duplicate workflow ID: {workflow.id}")
            workflow_ids.add(workflow.id)
        
        if errors:
            raise ValueError(f"Configuration validation errors:\n" + "\n".join(f"  - {error}" for error in errors))
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID"""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def get_tool(self, tool_id: str) -> Optional[ToolConfig]:
        """Get tool by ID"""
        return self.tools.get(tool_id)
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """Get workflow by ID"""
        for workflow in self.workflows:
            if workflow.id == workflow_id:
                return workflow
        return None
    
    def add_agent(self, agent: AgentConfig):
        """Add agent with validation"""
        if self.get_agent(agent.id):
            raise ValueError(f"Agent with ID {agent.id} already exists")
        self.agents.append(agent)
    
    def add_tool(self, tool: ToolConfig):
        """Add tool with validation"""
        if tool.id in self.tools:
            raise ValueError(f"Tool with ID {tool.id} already exists")
        self.tools[tool.id] = tool
    
    def add_workflow(self, workflow: WorkflowConfig):
        """Add workflow with validation"""
        if self.get_workflow(workflow.id):
            raise ValueError(f"Workflow with ID {workflow.id} already exists")
        self.workflows.append(workflow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        def convert_value(value):
            if isinstance(value, Enum):
                return value.value
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return value
        
        return convert_value(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LangSwarmConfig':
        """Create from dictionary"""
        # Convert nested dictionaries back to dataclasses
        config_data = data.copy()
        
        # Convert agents
        if 'agents' in config_data:
            agents = []
            for agent_data in config_data['agents']:
                if isinstance(agent_data, dict):
                    # Convert provider string back to enum
                    if 'provider' in agent_data and isinstance(agent_data['provider'], str):
                        agent_data['provider'] = ProviderType(agent_data['provider'])
                    agents.append(AgentConfig(**agent_data))
                else:
                    agents.append(agent_data)
            config_data['agents'] = agents
        
        # Convert tools
        if 'tools' in config_data:
            tools = {}
            for tool_id, tool_data in config_data['tools'].items():
                if isinstance(tool_data, dict):
                    tools[tool_id] = ToolConfig(**tool_data)
                else:
                    tools[tool_id] = tool_data
            config_data['tools'] = tools
        
        # Convert workflows
        if 'workflows' in config_data:
            workflows = []
            for workflow_data in config_data['workflows']:
                if isinstance(workflow_data, dict):
                    # Convert engine string back to enum
                    if 'engine' in workflow_data and isinstance(workflow_data['engine'], str):
                        workflow_data['engine'] = WorkflowEngine(workflow_data['engine'])
                    workflows.append(WorkflowConfig(**workflow_data))
                else:
                    workflows.append(workflow_data)
            config_data['workflows'] = workflows
        
        # Convert nested configs
        if 'memory' in config_data and isinstance(config_data['memory'], dict):
            memory_data = config_data['memory'].copy()
            if 'backend' in memory_data and isinstance(memory_data['backend'], str):
                memory_data['backend'] = MemoryBackend(memory_data['backend'])
            config_data['memory'] = MemoryConfig(**memory_data)
        
        if 'security' in config_data and isinstance(config_data['security'], dict):
            config_data['security'] = SecurityConfig(**config_data['security'])
        
        if 'observability' in config_data and isinstance(config_data['observability'], dict):
            obs_data = config_data['observability'].copy()
            if 'log_level' in obs_data and isinstance(obs_data['log_level'], str):
                obs_data['log_level'] = LogLevel(obs_data['log_level'])
            config_data['observability'] = ObservabilityConfig(**obs_data)
        
        if 'server' in config_data and isinstance(config_data['server'], dict):
            config_data['server'] = ServerConfig(**config_data['server'])
        
        return cls(**config_data)


# Configuration templates for common use cases
class ConfigTemplates:
    """Pre-built configuration templates"""
    
    @staticmethod
    def simple_chatbot(agent_name: str = "assistant", provider: ProviderType = ProviderType.OPENAI) -> LangSwarmConfig:
        """Simple chatbot configuration"""
        return LangSwarmConfig(
            name=f"Simple {agent_name.title()} Chatbot",
            agents=[
                AgentConfig(
                    id=agent_name,
                    provider=provider,
                    system_prompt="You are a helpful AI assistant.",
                    temperature=0.7
                )
            ]
        )
    
    @staticmethod
    def development_setup() -> LangSwarmConfig:
        """Development configuration with debug settings"""
        return LangSwarmConfig(
            name="Development Setup",
            agents=[
                AgentConfig(
                    id="dev_assistant",
                    provider=ProviderType.OPENAI,
                    model="gpt-4o",
                    system_prompt="You are a helpful development assistant.",
                    tools=["filesystem", "web_search"],
                    streaming=True
                )
            ],
            tools={
                "filesystem": ToolConfig(
                    id="filesystem",
                    type="builtin",
                    description="File system operations"
                ),
                "web_search": ToolConfig(
                    id="web_search",
                    type="builtin", 
                    description="Web search capabilities"
                )
            },
            memory=MemoryConfig(
                backend=MemoryBackend.SQLITE,
                config={"db_path": "dev_memory.db"}
            ),
            observability=ObservabilityConfig(
                log_level=LogLevel.DEBUG,
                tracing_enabled=True,
                metrics_enabled=True
            ),
            server=ServerConfig(
                reload=True,
                cors_enabled=True
            )
        )
    
    @staticmethod
    def production_setup() -> LangSwarmConfig:
        """Production configuration with optimized settings"""
        return LangSwarmConfig(
            name="Production Setup",
            memory=MemoryConfig(
                backend=MemoryBackend.REDIS,
                config={
                    "url": "redis://localhost:6379",
                    "key_prefix": "langswarm:prod:"
                }
            ),
            security=SecurityConfig(
                require_auth=True,
                encrypt_memory=True,
                log_sensitive_data=False,
                rate_limit_requests_per_minute=1000
            ),
            observability=ObservabilityConfig(
                log_level=LogLevel.INFO,
                structured_logging=True,
                metrics_enabled=True,
                health_check_enabled=True
            ),
            server=ServerConfig(
                host="0.0.0.0",
                workers=4,
                cors_origins=["https://yourdomain.com"]
            )
        )
