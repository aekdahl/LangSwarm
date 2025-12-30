# LangSwarm V2 Configuration API Reference

**Complete API reference for the V2 configuration system**

## 🎯 Overview

LangSwarm V2's configuration API provides a comprehensive, type-safe interface for loading, validating, and managing configurations. The API replaces the monolithic V1 configuration system with a clean, modular architecture that supports single-file, multi-file, template-based, and environment-aware configurations.

**Core Modules:**
- **`schema`**: Type-safe configuration classes and enums
- **`loaders`**: Configuration loading and migration utilities
- **`validation`**: Comprehensive validation system
- **`utils`**: Configuration management utilities

---

## 📦 Package API

### **Main Package Interface**

```python
from langswarm.core.config import (
    # Configuration Loading
    load_config,
    load_template,
    save_config,
    
    # Validation
    validate_config,
    validate_environment,
    
    # Utilities
    compare_configs,
    merge_configs,
    optimize_config,
    export_template,
    
    # Schema Classes
    LangSwarmConfig,
    AgentConfig,
    ToolConfig,
    WorkflowConfig,
    MemoryConfig,
    SecurityConfig,
    ObservabilityConfig,
    ServerConfig,
    
    # Enums
    LLMProvider,
    MemoryBackend,
    ToolType,
    
    # Migration
    migrate_v1_config,
    
    # Global Configuration
    get_global_config,
    set_global_config
)
```

---

## 🏗️ Configuration Schema

### **LangSwarmConfig**

```python
@dataclass
class LangSwarmConfig:
    """Main LangSwarm configuration container"""
    
    agents: List[AgentConfig] = field(default_factory=list)
    tools: List[ToolConfig] = field(default_factory=list)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID"""
        
    def get_tool(self, tool_id: str) -> Optional[ToolConfig]:
        """Get tool configuration by ID"""
        
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """Get workflow configuration by ID"""
        
    def validate(self) -> Tuple[bool, List[ValidationIssue]]:
        """Validate entire configuration"""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LangSwarmConfig':
        """Create from dictionary"""
```

### **AgentConfig**

```python
@dataclass
class AgentConfig:
    """Agent configuration with provider-specific settings"""
    
    id: str
    name: str
    provider: LLMProvider
    model: str
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key_env: str = ""
    api_base_url: str = ""
    timeout_seconds: int = 30
    retry_count: int = 3
    streaming: bool = False
    response_format: str = "text"  # text, json
    
    # Provider-specific settings
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: List[str] = field(default_factory=list)
    
    def validate(self) -> List[ValidationIssue]:
        """Validate agent configuration"""
        
    def get_provider_settings(self) -> Dict[str, Any]:
        """Get provider-specific settings"""
```

### **ToolConfig**

```python
@dataclass
class ToolConfig:
    """Tool configuration for various tool types"""
    
    id: str
    name: str
    type: ToolType  # mcp, memory, plugin, synapse
    description: str = ""
    enabled: bool = True
    timeout_seconds: int = 30
    retry_count: int = 3
    
    # Type-specific configurations
    server_config: Optional[Dict[str, Any]] = None      # MCP tools
    backend: Optional[MemoryBackend] = None             # Memory tools
    connection_params: Dict[str, Any] = field(default_factory=dict)
    plugin_config: Optional[Dict[str, Any]] = None      # Plugin tools
    synapse_config: Optional[Dict[str, Any]] = None     # Synapse tools
    
    def validate(self) -> List[ValidationIssue]:
        """Validate tool configuration"""
        
    def get_type_specific_config(self) -> Dict[str, Any]:
        """Get configuration specific to tool type"""
```

### **WorkflowConfig**

```python
@dataclass
class WorkflowConfig:
    """Workflow configuration with execution settings"""
    
    id: str
    name: str
    agent_id: str
    tool_ids: List[str] = field(default_factory=list)
    description: str = ""
    execution_mode: str = "sequential"  # sequential, parallel, conditional
    max_iterations: int = 10
    timeout_seconds: int = 300
    error_handling: str = "stop"  # stop, continue, retry
    retry_count: int = 3
    
    # V1 compatibility
    v1_yaml_path: Optional[str] = None
    
    def validate(self, available_agents: List[str], available_tools: List[str]) -> List[ValidationIssue]:
        """Validate workflow configuration against available agents and tools"""
```

### **MemoryConfig**

```python
@dataclass
class MemoryConfig:
    """Memory system configuration"""
    
    default_backend: MemoryBackend = MemoryBackend.SQLITE
    backends: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Global memory settings
    max_memory_size: int = 1000000  # Maximum memory items
    cleanup_interval: int = 3600    # Cleanup interval in seconds
    compression_enabled: bool = True
    
    def get_backend_config(self, backend: MemoryBackend) -> Dict[str, Any]:
        """Get configuration for specific backend"""
        
    def validate(self) -> List[ValidationIssue]:
        """Validate memory configuration"""
```

### **SecurityConfig**

```python
@dataclass
class SecurityConfig:
    """Security configuration"""
    
    # API Security
    api_key_rotation_enabled: bool = False
    api_key_rotation_days: int = 30
    
    # Rate Limiting
    rate_limiting_enabled: bool = False
    requests_per_minute: int = 60
    burst_size: int = 10
    
    # Access Control
    allowed_origins: List[str] = field(default_factory=list)
    require_authentication: bool = False
    
    # Data Security
    encrypt_at_rest: bool = False
    encrypt_in_transit: bool = True
    
    def validate(self) -> List[ValidationIssue]:
        """Validate security configuration"""
```

### **ObservabilityConfig**

```python
@dataclass
class ObservabilityConfig:
    """Observability configuration for logging, metrics, and tracing"""
    
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    
@dataclass
class LoggingConfig:
    """Logging configuration"""
    
    level: str = "INFO"         # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "standard"    # standard, json, detailed
    output: str = "console"     # console, file, both
    file_path: str = "langswarm.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
@dataclass
class MetricsConfig:
    """Metrics configuration"""
    
    enabled: bool = False
    export_interval: int = 60   # seconds
    prometheus_port: int = 9090
    include_system_metrics: bool = True
    
@dataclass
class TracingConfig:
    """Tracing configuration"""
    
    enabled: bool = False
    output_file: str = "traces.jsonl"
    sampling_rate: float = 1.0  # 0.0 to 1.0
    include_agent_traces: bool = True
    include_tool_traces: bool = True
```

### **ServerConfig**

```python
@dataclass
class ServerConfig:
    """Server configuration"""
    
    host: str = "localhost"
    port: int = 8000
    workers: int = 1
    debug: bool = False
    reload: bool = False
    
    # API Configuration
    api_prefix: str = "/api/v2"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Performance
    max_request_size: int = 16777216  # 16MB
    request_timeout: int = 30
    
    def validate(self) -> List[ValidationIssue]:
        """Validate server configuration"""
```

---

## 🔧 Configuration Enums

### **LLMProvider**

```python
class LLMProvider(Enum):
    """Supported LLM providers"""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    TOGETHER = "together"
    
    @classmethod
    def from_string(cls, value: str) -> 'LLMProvider':
        """Convert string to enum value"""
        
    def get_default_models(self) -> List[str]:
        """Get default models for this provider"""
        
    def get_api_key_env_var(self) -> str:
        """Get standard environment variable name for API key"""
```

### **MemoryBackend**

```python
class MemoryBackend(Enum):
    """Supported memory backends"""
    
    SQLITE = "sqlite"
    REDIS = "redis"
    CHROMADB = "chromadb"
    ELASTICSEARCH = "elasticsearch"
    BIGQUERY = "bigquery"
    MEMORY = "memory"  # In-memory only
    
    @classmethod
    def from_string(cls, value: str) -> 'MemoryBackend':
        """Convert string to enum value"""
        
    def get_required_dependencies(self) -> List[str]:
        """Get required Python packages for this backend"""
        
    def get_connection_params_schema(self) -> Dict[str, Any]:
        """Get JSON schema for connection parameters"""
```

### **ToolType**

```python
class ToolType(Enum):
    """Tool type classifications"""
    
    MCP = "mcp"           # Model Context Protocol tools
    MEMORY = "memory"     # Memory/RAG tools
    PLUGIN = "plugin"     # Plugin-based tools
    SYNAPSE = "synapse"   # Multi-agent Synapse tools
    UTILITY = "utility"   # General utility tools
    WORKFLOW = "workflow" # Workflow orchestration tools
    
    @classmethod
    def from_string(cls, value: str) -> 'ToolType':
        """Convert string to enum value"""
```

---

## 📁 Configuration Loading

### **load_config()**

```python
def load_config(
    path: Union[str, Path, None] = None,
    search_paths: List[str] = None,
    environment_substitution: bool = True,
    validate: bool = True
) -> LangSwarmConfig:
    """Load configuration from file with auto-discovery
    
    Args:
        path: Configuration file path (auto-discovered if None)
        search_paths: Directories to search for config files
        environment_substitution: Enable ${VAR} substitution
        validate: Validate configuration after loading
        
    Returns:
        Loaded and validated configuration
        
    Raises:
        ConfigurationError: If loading or validation fails
        FileNotFoundError: If configuration file not found
        ValidationError: If configuration is invalid
    """

# Usage examples
config = load_config()                          # Auto-discover
config = load_config("langswarm.yaml")         # Specific file
config = load_config("config.yaml", validate=False)  # Skip validation
```

### **load_template()**

```python
def load_template(template_name: str) -> LangSwarmConfig:
    """Load pre-built configuration template
    
    Args:
        template_name: Template name (simple_chatbot, development_setup, production_setup)
        
    Returns:
        Configuration loaded from template
        
    Raises:
        TemplateNotFoundError: If template doesn't exist
    """

# Available templates
config = load_template("simple_chatbot")     # Basic chatbot setup
config = load_template("development_setup")  # Development environment
config = load_template("production_setup")   # Production environment
```

### **save_config()**

```python
def save_config(
    config: LangSwarmConfig,
    path: Union[str, Path],
    include_comments: bool = False,
    validate: bool = True
) -> None:
    """Save configuration to file
    
    Args:
        config: Configuration to save
        path: Output file path
        include_comments: Include explanatory comments
        validate: Validate before saving
        
    Raises:
        ConfigurationError: If saving fails
        ValidationError: If configuration is invalid
    """

# Usage examples
save_config(config, "langswarm.yaml")
save_config(config, "config_with_docs.yaml", include_comments=True)
```

---

## ✅ Configuration Validation

### **validate_config()**

```python
def validate_config(config: LangSwarmConfig) -> Tuple[bool, ValidationReport]:
    """Comprehensive configuration validation
    
    Args:
        config: Configuration to validate
        
    Returns:
        Tuple of (is_valid, validation_report)
    """

# Usage
is_valid, report = validate_config(config)

if not is_valid:
    print(f"Configuration has {len(report.issues)} issues:")
    for issue in report.issues:
        print(f"  {issue.severity}: {issue.message}")
```

### **validate_environment()**

```python
def validate_environment(config: LangSwarmConfig) -> Tuple[bool, List[str]]:
    """Validate required environment variables
    
    Args:
        config: Configuration to check
        
    Returns:
        Tuple of (is_valid, missing_variables)
    """

# Usage
is_valid, missing = validate_environment(config)

if not is_valid:
    print(f"Missing environment variables: {missing}")
```

### **ValidationReport**

```python
@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    
    is_valid: bool
    issues: List[ValidationIssue]
    
    @property
    def error_count(self) -> int:
        """Count of ERROR-level issues"""
        
    @property
    def warning_count(self) -> int:
        """Count of WARNING-level issues"""
        
    @property
    def info_count(self) -> int:
        """Count of INFO-level issues"""
        
    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        
    def get_issues_by_component(self, component: str) -> List[ValidationIssue]:
        """Get issues filtered by component"""

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    
    severity: str           # ERROR, WARNING, INFO, CRITICAL
    message: str           # Human-readable message
    component: str         # Component path (e.g., "agents[0].provider")
    suggestion: str        # Suggested fix
    category: str          # Issue category
    
    def __str__(self) -> str:
        return f"{self.severity}: {self.message}"
```

---

## 🔄 Configuration Migration

### **migrate_v1_config()**

```python
def migrate_v1_config(
    v1_config_path: Union[str, Path],
    output_path: Union[str, Path, None] = None,
    preserve_structure: bool = False
) -> Tuple[LangSwarmConfig, List[MigrationWarning]]:
    """Migrate V1 configuration to V2 format
    
    Args:
        v1_config_path: Path to V1 configuration directory
        output_path: Output path for V2 config (optional)
        preserve_structure: Keep V1 directory structure
        
    Returns:
        Tuple of (migrated_config, migration_warnings)
        
    Raises:
        MigrationError: If migration fails
        FileNotFoundError: If V1 config not found
    """

# Usage
config, warnings = migrate_v1_config("./old_config")

if warnings:
    print(f"Migration completed with {len(warnings)} warnings:")
    for warning in warnings:
        print(f"  {warning.message}")
```

### **MigrationWarning**

```python
@dataclass
class MigrationWarning:
    """Migration warning information"""
    
    category: str          # Category of warning
    message: str          # Warning message
    suggestion: str       # Suggested action
    v1_path: str          # Original V1 path
    v2_path: str          # New V2 path
```

---

## 🛠️ Configuration Utilities

### **compare_configs()**

```python
def compare_configs(
    config1: LangSwarmConfig,
    config2: LangSwarmConfig
) -> ConfigurationComparison:
    """Compare two configurations
    
    Args:
        config1: First configuration
        config2: Second configuration
        
    Returns:
        Detailed comparison report
    """

# Usage
comparison = compare_configs(old_config, new_config)

print(f"Differences: {len(comparison.differences)}")
for diff in comparison.differences:
    print(f"  {diff.change_type}: {diff.path}")
```

### **merge_configs()**

```python
def merge_configs(
    base_config: LangSwarmConfig,
    override_config: LangSwarmConfig,
    merge_strategy: str = "override"
) -> LangSwarmConfig:
    """Merge two configurations
    
    Args:
        base_config: Base configuration
        override_config: Configuration to merge in
        merge_strategy: Merge strategy (override, append, deep)
        
    Returns:
        Merged configuration
    """

# Usage
merged = merge_configs(base_config, env_config)
```

### **optimize_config()**

```python
def optimize_config(config: LangSwarmConfig) -> Dict[str, List[OptimizationSuggestion]]:
    """Analyze configuration for optimization opportunities
    
    Args:
        config: Configuration to analyze
        
    Returns:
        Optimization suggestions by category
    """

# Usage
suggestions = optimize_config(config)

for category, optimizations in suggestions.items():
    print(f"\n{category}:")
    for opt in optimizations:
        print(f"  • {opt.description}")
        print(f"    Impact: {opt.impact}")
        print(f"    Effort: {opt.effort}")
```

### **export_template()**

```python
def export_template(
    config: LangSwarmConfig,
    output_path: Union[str, Path],
    include_comments: bool = True,
    include_examples: bool = True
) -> None:
    """Export configuration as documented template
    
    Args:
        config: Configuration to export
        output_path: Template file path
        include_comments: Add explanatory comments
        include_examples: Include example values
    """

# Usage
export_template(config, "my_template.yaml", include_comments=True)
```

---

## 🌍 Global Configuration

### **Global Configuration Management**

```python
def get_global_config() -> Optional[LangSwarmConfig]:
    """Get globally set configuration"""

def set_global_config(config: LangSwarmConfig) -> None:
    """Set global configuration"""

def clear_global_config() -> None:
    """Clear global configuration"""

# Usage
set_global_config(load_config("langswarm.yaml"))

# Access from anywhere
config = get_global_config()
if config:
    agent = config.get_agent("main_agent")
```

---

## 🔧 Advanced Configuration Patterns

### **Environment-Specific Configuration**

```python
import os
from langswarm.core.config import load_config, merge_configs

# Load base configuration
base_config = load_config("base.yaml")

# Load environment-specific overrides
env = os.getenv("ENVIRONMENT", "development")
env_config = load_config(f"{env}.yaml")

# Merge configurations
config = merge_configs(base_config, env_config)

# Set as global
set_global_config(config)
```

### **Runtime Configuration Updates**

```python
# Load initial configuration
config = load_config("langswarm.yaml")

# Update at runtime
agent = config.get_agent("main_agent")
if agent:
    agent.temperature = 0.8
    agent.max_tokens = 4096

# Validate changes
is_valid, report = validate_config(config)

if is_valid:
    set_global_config(config)
else:
    print("Configuration update invalid:", report.issues)
```

### **Configuration Monitoring**

```python
import threading
import time
from pathlib import Path

class ConfigurationWatcher:
    """Watch configuration file for changes"""
    
    def __init__(self, config_path: str, callback: callable):
        self.config_path = Path(config_path)
        self.callback = callback
        self.last_modified = self.config_path.stat().st_mtime
        
    def start(self):
        """Start watching for changes"""
        threading.Thread(target=self._watch, daemon=True).start()
        
    def _watch(self):
        while True:
            try:
                current_modified = self.config_path.stat().st_mtime
                if current_modified > self.last_modified:
                    self.last_modified = current_modified
                    # Reload and validate
                    new_config = load_config(str(self.config_path))
                    self.callback(new_config)
            except Exception as e:
                print(f"Configuration watch error: {e}")
            time.sleep(1)

# Usage
def on_config_change(new_config):
    """Handle configuration changes"""
    is_valid, report = validate_config(new_config)
    if is_valid:
        set_global_config(new_config)
        print("Configuration reloaded")
    else:
        print("Invalid configuration update:", report.issues)

watcher = ConfigurationWatcher("langswarm.yaml", on_config_change)
watcher.start()
```

---

## ❌ Exception Handling

### **Configuration Exceptions**

```python
class ConfigurationError(Exception):
    """Base configuration error"""

class FileNotFoundError(ConfigurationError):
    """Configuration file not found"""

class ValidationError(ConfigurationError):
    """Configuration validation failed"""

class MigrationError(ConfigurationError):
    """Configuration migration failed"""

class TemplateNotFoundError(ConfigurationError):
    """Template not found"""

class EnvironmentError(ConfigurationError):
    """Environment validation failed"""

# Usage with error handling
try:
    config = load_config("langswarm.yaml")
except FileNotFoundError:
    print("Configuration file not found, using defaults")
    config = load_template("simple_chatbot")
except ValidationError as e:
    print(f"Configuration validation failed: {e}")
    exit(1)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    exit(1)
```

---

**LangSwarm V2's configuration API provides a comprehensive, type-safe interface for managing complex AI application configurations with enterprise-grade features and comprehensive validation.**
