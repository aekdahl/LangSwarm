#!/usr/bin/env python3
"""
Smart Tool Auto-Discovery: Environment Detection System
======================================================

This module provides environment-based tool detection and auto-configuration.
It scans the environment for:
- API tokens and credentials
- Cloud provider configurations
- Custom tool files
- Available dependencies

Part of the LangSwarm Simplification Project - Priority 3.
"""

import os
import sys
import importlib
import subprocess
import importlib.util
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentCapabilities:
    """
    Comprehensive system capabilities detection for intelligent configuration.
    
    This class provides detailed information about the system environment
    to enable smart tool selection, resource allocation, and configuration.
    """
    # Model availability
    available_models: List[str]
    preferred_model: str
    
    # System resources
    available_memory_mb: int
    cpu_cores: int
    storage_available_gb: float
    
    # Network and access
    internet_access: bool
    max_concurrent_requests: int
    
    # Environment context
    environment_type: str  # "development", "production", "testing", "local"
    container_runtime: Optional[str]  # "docker", "podman", None
    platform: str  # "darwin", "linux", "windows"
    
    # Tool capabilities
    has_docker: bool
    has_git: bool
    has_python: bool
    python_version: str
    
    # API credentials available
    available_apis: List[str]
    
    # Performance characteristics
    is_low_resource: bool
    is_cloud_environment: bool
    supports_gpu: bool
    
    @classmethod
    def detect_system_capabilities(cls) -> 'EnvironmentCapabilities':
        """
        Automatically detect system capabilities and return EnvironmentCapabilities instance.
        
        Returns:
            EnvironmentCapabilities: Detected system capabilities
        """
        logger.info("🔍 Detecting system capabilities...")
        
        # Detect available models (simplified - could be enhanced with actual API checks)
        available_models = cls._detect_available_models()
        preferred_model = cls._get_preferred_model(available_models)
        
        # System resources
        memory_mb = cls._detect_memory()
        cpu_cores = cls._detect_cpu_cores()
        storage_gb = cls._detect_storage()
        
        # Network and performance
        internet_access = cls._check_internet_access()
        max_requests = cls._estimate_max_concurrent_requests(memory_mb, cpu_cores)
        
        # Environment detection
        env_type = cls._detect_environment_type()
        container_runtime = cls._detect_container_runtime()
        platform = sys.platform
        
        # Tool availability
        has_docker = cls._check_command_available("docker")
        has_git = cls._check_command_available("git")
        has_python = True  # We're running Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # API credentials
        available_apis = cls._detect_available_apis()
        
        # Performance characteristics
        is_low_resource = memory_mb < 2000 or cpu_cores < 2
        is_cloud_environment = cls._detect_cloud_environment()
        supports_gpu = cls._detect_gpu_support()
        
        capabilities = cls(
            available_models=available_models,
            preferred_model=preferred_model,
            available_memory_mb=memory_mb,
            cpu_cores=cpu_cores,
            storage_available_gb=storage_gb,
            internet_access=internet_access,
            max_concurrent_requests=max_requests,
            environment_type=env_type,
            container_runtime=container_runtime,
            platform=platform,
            has_docker=has_docker,
            has_git=has_git,
            has_python=has_python,
            python_version=python_version,
            available_apis=available_apis,
            is_low_resource=is_low_resource,
            is_cloud_environment=is_cloud_environment,
            supports_gpu=supports_gpu
        )
        
        logger.info(f"✅ Detected capabilities: {memory_mb}MB RAM, {cpu_cores} cores, {len(available_models)} models")
        return capabilities
    
    @staticmethod
    def _detect_available_models() -> List[str]:
        """Detect available LLM models based on API keys and configuration"""
        models = []
        
        # OpenAI models
        if os.getenv("OPENAI_API_KEY"):
            models.extend(["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
        
        # Anthropic models
        if os.getenv("ANTHROPIC_API_KEY"):
            models.extend(["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"])
        
        # Google models
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            models.extend(["gemini-pro", "gemini-1.5-pro"])
        
        # Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            models.extend(["gpt-4", "gpt-35-turbo"])
        
        # Local models (Ollama, etc.)
        if EnvironmentCapabilities._check_command_available("ollama"):
            models.extend(["llama3", "mistral", "codellama"])
        
        # Fallback models always available in most setups
        if not models:
            models = ["gpt-4o-mini"]  # Reasonable fallback
        
        return list(set(models))  # Remove duplicates
    
    @staticmethod
    def _get_preferred_model(available_models: List[str]) -> str:
        """Select preferred model based on availability and performance"""
        # Preference order for general use
        preference_order = [
            "gpt-4o",
            "claude-3-5-sonnet-20241022", 
            "gpt-4o-mini",
            "claude-3-haiku-20240307",
            "gemini-pro",
            "gpt-3.5-turbo"
        ]
        
        for model in preference_order:
            if model in available_models:
                return model
        
        # Fallback to first available
        return available_models[0] if available_models else "gpt-4o-mini"
    
    @staticmethod
    def _detect_memory() -> int:
        """Detect available system memory in MB"""
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(["sysctl", "-n", "hw.memsize"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    bytes_memory = int(result.stdout.strip())
                    return bytes_memory // (1024 * 1024)  # Convert to MB
            elif sys.platform.startswith("linux"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb_memory = int(line.split()[1])
                            return kb_memory // 1024  # Convert KB to MB
            elif sys.platform == "win32":
                import psutil
                return psutil.virtual_memory().total // (1024 * 1024)
        except Exception as e:
            logger.warning(f"⚠️ Could not detect memory: {e}")
        
        # Fallback estimate
        return 4096  # 4GB reasonable default
    
    @staticmethod
    def _detect_cpu_cores() -> int:
        """Detect number of CPU cores"""
        try:
            import os
            return os.cpu_count() or 2
        except Exception:
            return 2  # Conservative fallback
    
    @staticmethod
    def _detect_storage() -> float:
        """Detect available storage in GB"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            return free / (1024 ** 3)  # Convert to GB
        except Exception:
            return 10.0  # 10GB fallback
    
    @staticmethod
    def _check_internet_access() -> bool:
        """Check if internet access is available"""
        try:
            import urllib.request
            urllib.request.urlopen("https://www.google.com", timeout=5)
            return True
        except Exception:
            return False
    
    @staticmethod
    def _estimate_max_concurrent_requests(memory_mb: int, cpu_cores: int) -> int:
        """Estimate maximum concurrent requests based on resources"""
        # Conservative estimation based on memory and CPU
        memory_factor = memory_mb // 1000  # ~1 request per GB
        cpu_factor = cpu_cores
        return min(max(memory_factor, cpu_factor, 1), 10)  # Between 1-10
    
    @staticmethod
    def _detect_environment_type() -> str:
        """Detect environment type (development, production, testing)"""
        # Check environment variables
        env_indicators = {
            "development": ["DEVELOPMENT", "DEV", "DEBUG"],
            "production": ["PRODUCTION", "PROD"],
            "testing": ["TEST", "TESTING", "CI"],
        }
        
        for env_type, indicators in env_indicators.items():
            for indicator in indicators:
                if os.getenv(indicator) or os.getenv(f"{indicator}_MODE"):
                    return env_type
        
        # Check common CI environment variables
        ci_vars = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL"]
        if any(os.getenv(var) for var in ci_vars):
            return "testing"
        
        # Default to development for local environments
        return "development"
    
    @staticmethod
    def _detect_container_runtime() -> Optional[str]:
        """Detect container runtime if available"""
        if EnvironmentCapabilities._check_command_available("docker"):
            return "docker"
        elif EnvironmentCapabilities._check_command_available("podman"):
            return "podman"
        return None
    
    @staticmethod
    def _check_command_available(command: str) -> bool:
        """Check if a command is available in PATH"""
        try:
            result = subprocess.run([command, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    @staticmethod
    def _detect_available_apis() -> List[str]:
        """Detect available API credentials"""
        apis = []
        
        # Common API credentials to check
        api_checks = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "github": ["GITHUB_TOKEN", "GITHUB_ACCESS_TOKEN"],
            "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            "gcp": ["GOOGLE_APPLICATION_CREDENTIALS", "GCLOUD_PROJECT"],
            "azure": ["AZURE_CLIENT_ID", "AZURE_TENANT_ID"]
        }
        
        for api_name, env_vars in api_checks.items():
            if any(os.getenv(var) for var in env_vars):
                apis.append(api_name)
        
        return apis
    
    @staticmethod
    def _detect_cloud_environment() -> bool:
        """Detect if running in a cloud environment"""
        # Check for common cloud environment indicators
        cloud_indicators = [
            "AWS_REGION", "AWS_LAMBDA_FUNCTION_NAME",  # AWS
            "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT",     # Google Cloud
            "AZURE_CLIENT_ID", "WEBSITE_INSTANCE_ID",  # Azure
            "HEROKU_APP_NAME",                         # Heroku
            "VERCEL", "NETLIFY",                       # Edge platforms
        ]
        
        return any(os.getenv(indicator) for indicator in cloud_indicators)
    
    @staticmethod
    def _detect_gpu_support() -> bool:
        """Detect if GPU support is available"""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Check for AMD GPU (basic check)
            result = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get a summary of detected resources"""
        return {
            "memory_gb": round(self.available_memory_mb / 1024, 1),
            "cpu_cores": self.cpu_cores,
            "storage_gb": round(self.storage_available_gb, 1),
            "models_available": len(self.available_models),
            "preferred_model": self.preferred_model,
            "environment": self.environment_type,
            "platform": self.platform,
            "internet_access": self.internet_access,
            "container_runtime": self.container_runtime,
            "apis_available": len(self.available_apis),
            "performance_class": "high" if not self.is_low_resource else "low"
        }
    
    def suggest_configuration(self) -> Dict[str, Any]:
        """Suggest optimal configuration based on detected capabilities"""
        suggestions = {
            "recommended_agents": 1 if self.is_low_resource else min(3, self.cpu_cores),
            "enable_memory": not self.is_low_resource,
            "enable_streaming": True,
            "max_tokens": 4000 if self.is_low_resource else 8000,
            "concurrent_requests": self.max_concurrent_requests,
        }
        
        # Tool recommendations based on available APIs
        recommended_tools = ["filesystem"]
        if "github" in self.available_apis:
            recommended_tools.append("github")
        if self.internet_access:
            recommended_tools.append("web_search")
        if not self.is_low_resource:
            recommended_tools.extend(["aggregation", "consensus"])
        
        suggestions["recommended_tools"] = recommended_tools
        
        return suggestions

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert capabilities to dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation of capabilities
        """
        return {
            "available_models": self.available_models,
            "preferred_model": self.preferred_model,
            "available_memory_mb": self.available_memory_mb,
            "cpu_cores": self.cpu_cores,
            "storage_available_gb": self.storage_available_gb,
            "internet_access": self.internet_access,
            "max_concurrent_requests": self.max_concurrent_requests,
            "environment_type": self.environment_type,
            "container_runtime": self.container_runtime,
            "platform": self.platform,
            "has_docker": self.has_docker,
            "has_git": self.has_git,
            "has_python": self.has_python,
            "python_version": self.python_version,
            "available_apis": self.available_apis,
            "is_low_resource": self.is_low_resource,
            "is_cloud_environment": self.is_cloud_environment,
            "supports_gpu": self.supports_gpu
        }


@dataclass
class ToolPreset:
    """Tool configuration preset with smart defaults"""
    id: str
    type: str
    description: str
    local_mode: bool = True
    pattern: str = "direct"
    methods: List[Dict[str, str]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    environment_vars: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    custom_config: Dict[str, Any] = field(default_factory=dict)


class EnvironmentDetector:
    """Environment-based tool detection and auto-configuration"""
    
    def __init__(self):
        self.available_tools = {}
        self.detected_environments = {}
        self._load_tool_presets()
    
    def detect_capabilities(self) -> EnvironmentCapabilities:
        """
        Detect system capabilities using EnvironmentCapabilities.
        
        This method provides the interface expected by the config loader
        and delegates to the comprehensive capabilities detection.
        
        Returns:
            EnvironmentCapabilities: Detected system capabilities
        """
        return EnvironmentCapabilities.detect_system_capabilities()
    
    def _load_tool_presets(self):
        """Load built-in tool presets with smart defaults"""
        self.tool_presets = {
            # Built-in MCP tools
            "filesystem": ToolPreset(
                id="filesystem",
                type="mcpfilesystem",
                description="Local filesystem access for reading files and listing directories",
                local_mode=True,
                pattern="direct",
                methods=[
                    {"read_file": "Read file contents"},
                    {"list_directory": "List directory contents"}
                ],
                environment_vars=[],  # Always available
                dependencies=[]
            ),
            
            "github": ToolPreset(
                id="github",
                type="mcpgithubtool",
                description="GitHub API integration for repository operations",
                local_mode=True,
                pattern="intent",
                methods=[
                    {"get_repository": "Get repository information"},
                    {"list_issues": "List repository issues"},
                    {"create_issue": "Create a new issue"},
                    {"search_repositories": "Search for repositories"}
                ],
                environment_vars=["GITHUB_TOKEN", "GITHUB_PAT"],
                dependencies=["requests", "pygithub"],
                settings={
                    "base_url": "https://api.github.com",
                    "timeout": 30
                }
            ),
            
            "dynamic_forms": ToolPreset(
                id="dynamic_forms",
                type="mcpforms",
                description="Dynamic form generation for configuration interfaces",
                local_mode=True,
                pattern="direct",
                methods=[
                    {"generate_form_schema": "Generate form schema from configuration"},
                    {"get_available_forms": "List all available form types"},
                    {"get_form_definition": "Get raw form definition"}
                ],
                environment_vars=[],
                dependencies=[]
            ),
            
            # Cloud provider tools (future)
            "aws": ToolPreset(
                id="aws",
                type="mcpaws",
                description="AWS cloud services integration",
                local_mode=True,
                pattern="intent",
                methods=[
                    {"list_s3_buckets": "List S3 buckets"},
                    {"describe_ec2_instances": "Describe EC2 instances"},
                    {"get_cloudformation_stacks": "Get CloudFormation stacks"}
                ],
                environment_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE"],
                dependencies=["boto3", "botocore"],
                settings={
                    "region": "us-east-1"
                }
            ),
            
            "gcp": ToolPreset(
                id="gcp",
                type="mcpgcp",
                description="Google Cloud Platform integration",
                local_mode=True,
                pattern="intent",
                methods=[
                    {"list_projects": "List GCP projects"},
                    {"list_compute_instances": "List Compute Engine instances"},
                    {"list_storage_buckets": "List Cloud Storage buckets"}
                ],
                environment_vars=["GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT"],
                dependencies=["google-cloud-core", "google-auth"],
                settings={}
            ),
            
            "docker": ToolPreset(
                id="docker",
                type="mcpdocker",
                description="Docker container management",
                local_mode=True,
                pattern="intent",
                methods=[
                    {"list_containers": "List Docker containers"},
                    {"build_image": "Build Docker image"},
                    {"run_container": "Run Docker container"}
                ],
                environment_vars=["DOCKER_HOST"],
                dependencies=["docker"],
                settings={}
            )
        }
    
    def detect_environment(self) -> Dict[str, Any]:
        """Detect available tools based on environment variables and dependencies"""
        detection_results = {
            "available_tools": [],
            "missing_credentials": [],
            "missing_dependencies": [],
            "recommendations": [],
            "environment_summary": {}
        }
        
        print("🔍 Detecting environment for Smart Tool Auto-Discovery...")
        
        for tool_id, preset in self.tool_presets.items():
            tool_status = self._check_tool_availability(preset)
            
            if tool_status["available"]:
                detection_results["available_tools"].append({
                    "id": tool_id,
                    "preset": preset,
                    "status": tool_status
                })
                print(f"   ✅ {tool_id}: Available")
            else:
                missing_items = []
                if tool_status["missing_env_vars"]:
                    missing_items.extend(tool_status["missing_env_vars"])
                    detection_results["missing_credentials"].append({
                        "tool": tool_id,
                        "missing_vars": tool_status["missing_env_vars"]
                    })
                
                if tool_status["missing_dependencies"]:
                    missing_items.extend(tool_status["missing_dependencies"])
                    detection_results["missing_dependencies"].append({
                        "tool": tool_id,
                        "missing_deps": tool_status["missing_dependencies"]
                    })
                
                if missing_items:
                    print(f"   ❌ {tool_id}: Missing {', '.join(missing_items)}")
                    detection_results["recommendations"].append(
                        f"To enable {tool_id}: {self._get_tool_setup_recommendation(preset, tool_status)}"
                    )
                else:
                    # Available but may not be requested
                    print(f"   ⚠️  {tool_id}: Available but not configured")
        
        # Add custom tool detection
        custom_tools = self._detect_custom_tools()
        if custom_tools:
            detection_results["available_tools"].extend(custom_tools)
            print(f"   🔧 Found {len(custom_tools)} custom tools")
        
        detection_results["environment_summary"] = {
            "total_available": len(detection_results["available_tools"]),
            "built_in_tools": len([t for t in detection_results["available_tools"] if "preset" in t]),
            "custom_tools": len(custom_tools),
            "missing_credentials": len(detection_results["missing_credentials"]),
            "missing_dependencies": len(detection_results["missing_dependencies"])
        }
        
        return detection_results
    
    def _check_tool_availability(self, preset: ToolPreset) -> Dict[str, Any]:
        """Check if a tool preset is available in the current environment"""
        missing_env_vars = []
        missing_dependencies = []
        
        # Check environment variables (if any required)
        for env_var in preset.environment_vars:
            if not os.getenv(env_var):
                missing_env_vars.append(env_var)
        
        # Check dependencies
        for dep in preset.dependencies:
            if not self._check_dependency(dep):
                missing_dependencies.append(dep)
        
        # Special case: tools with no requirements are always available
        if not preset.environment_vars and not preset.dependencies:
            available = True
        else:
            # Tool is available if all requirements are met
            available = not missing_env_vars and not missing_dependencies
        
        return {
            "available": available,
            "missing_env_vars": missing_env_vars,
            "missing_dependencies": missing_dependencies,
            "preset": preset
        }
    
    def _check_dependency(self, package_name: str) -> bool:
        """Check if a Python package is available"""
        try:
            importlib.import_module(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False
    
    def _get_tool_setup_recommendation(self, preset: ToolPreset, status: Dict[str, Any]) -> str:
        """Generate setup recommendation for a tool"""
        recommendations = []
        
        if status["missing_env_vars"]:
            env_vars = ", ".join(status["missing_env_vars"])
            recommendations.append(f"Set environment variables: {env_vars}")
        
        if status["missing_dependencies"]:
            deps = " ".join(status["missing_dependencies"])
            recommendations.append(f"Install: pip install {deps}")
        
        return " | ".join(recommendations)
    
    def _detect_custom_tools(self) -> List[Dict[str, Any]]:
        """Detect custom tools in ./tools/ directory"""
        custom_tools = []
        tools_dir = Path("./tools")
        
        if not tools_dir.exists():
            return custom_tools
        
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name == "__init__.py":
                continue
                
            try:
                # Basic detection - look for tool classes
                with open(tool_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Simple heuristic: look for class definitions that might be tools
                if "class " in content and ("Tool" in content or "MCP" in content):
                    tool_id = tool_file.stem
                    custom_tools.append({
                        "id": tool_id,
                        "type": "custom",
                        "description": f"Custom tool from {tool_file}",
                        "path": str(tool_file),
                        "local_mode": True,
                        "pattern": "direct"
                    })
            except Exception as e:
                print(f"   ⚠️  Could not scan {tool_file}: {e}")
        
        return custom_tools
    
    def auto_discover_tools(self, requested_tools: List[str] = None) -> List[Dict[str, Any]]:
        """
        Auto-discover and configure tools based on environment.
        
        Args:
            requested_tools: List of tool IDs to discover. If None, discovers all available.
            
        Returns:
            List of tool configurations ready for use
        """
        detection_results = self.detect_environment()
        available_tools = detection_results["available_tools"]
        
        # Filter by requested tools if specified
        if requested_tools:
            available_tools = [
                tool for tool in available_tools 
                if tool["id"] in requested_tools
            ]
        
        # Convert to tool configurations
        tool_configs = []
        for tool_info in available_tools:
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
                    **preset.custom_config
                }
                
                # Add any environment-specific settings
                if preset.settings:
                    config.update(preset.settings)
                    
            else:
                # Custom tool
                config = {
                    "id": tool_info["id"],
                    "type": tool_info["type"],
                    "description": tool_info["description"],
                    "local_mode": tool_info.get("local_mode", True),
                    "pattern": tool_info.get("pattern", "direct"),
                    "path": tool_info.get("path")
                }
            
            tool_configs.append(config)
        
        return tool_configs
    
    def get_tool_preset(self, tool_id: str) -> Optional[ToolPreset]:
        """Get a tool preset by ID"""
        return self.tool_presets.get(tool_id)
    
    def get_available_tool_ids(self) -> List[str]:
        """Get list of all available tool IDs"""
        detection_results = self.detect_environment()
        return [tool["id"] for tool in detection_results["available_tools"]]
    
    def recommend_tools_for_use_case(self, use_case: str) -> List[str]:
        """Recommend tools based on use case description"""
        recommendations = []
        use_case_lower = use_case.lower()
        
        # Simple keyword-based recommendations
        if any(keyword in use_case_lower for keyword in ["file", "directory", "read", "filesystem"]):
            recommendations.append("filesystem")
        
        if any(keyword in use_case_lower for keyword in ["github", "repository", "repo", "git"]):
            recommendations.append("github")
        
        if any(keyword in use_case_lower for keyword in ["form", "input", "configuration", "ui"]):
            recommendations.append("dynamic_forms")
        
        if any(keyword in use_case_lower for keyword in ["aws", "s3", "ec2", "lambda"]):
            recommendations.append("aws")
        
        if any(keyword in use_case_lower for keyword in ["gcp", "google cloud", "compute engine"]):
            recommendations.append("gcp")
        
        if any(keyword in use_case_lower for keyword in ["docker", "container", "containerize"]):
            recommendations.append("docker")
        
        return recommendations


# Global instance for easy access
environment_detector = EnvironmentDetector()

# Convenience functions
def auto_discover_tools(requested_tools: List[str] = None) -> List[Dict[str, Any]]:
    """
    Auto-discover tools based on environment detection.
    
    Args:
        requested_tools: List of tool IDs to discover. If None, discovers all available.
        
    Returns:
        List of tool configurations ready for use
        
    Example:
        # Discover specific tools
        tools = auto_discover_tools(["filesystem", "github"])
        
        # Discover all available tools
        tools = auto_discover_tools()
    """
    return environment_detector.auto_discover_tools(requested_tools)


def detect_available_tools() -> Dict[str, Any]:
    """
    Detect what tools are available in the current environment.
    
    Returns:
        Dictionary with detection results and recommendations
    """
    return environment_detector.detect_environment()


def get_tool_recommendations(use_case: str) -> List[str]:
    """
    Get tool recommendations based on use case.
    
    Args:
        use_case: The use case description (e.g., "coding", "research", "support")
        
    Returns:
        List of recommended tool names
    """
    recommendations = {
        "coding": ["filesystem", "github", "codebase_indexer"],
        "research": ["filesystem", "github", "aggregation", "consensus"],
        "support": ["filesystem", "files"],
        "creative": ["filesystem", "files"],
        "analytical": ["filesystem", "aggregation", "multi_agent_reranking"],
        "general": ["filesystem"],
    }
    
    use_case_lower = use_case.lower()
    
    # Try exact match first
    if use_case_lower in recommendations:
        return recommendations[use_case_lower]
    
    # Try partial matches
    for key, tools in recommendations.items():
        if key in use_case_lower or use_case_lower in key:
            return tools
    
    # Default fallback
    return recommendations["general"]


def detect_environment() -> Dict[str, Any]:
    """
    Comprehensive environment detection and analysis.
    
    This function provides a complete environment analysis including
    system capabilities, available tools, and intelligent recommendations.
    
    Returns:
        Dict containing comprehensive environment information:
        - capabilities: EnvironmentCapabilities object
        - available_tools: List of available tools
        - tool_recommendations: Suggested tools based on capabilities
        - system_summary: Human-readable summary
        - optimization_suggestions: Performance and configuration suggestions
    """
    print("🔍 Running comprehensive environment detection...")
    
    # Detect system capabilities
    capabilities = EnvironmentCapabilities.detect_system_capabilities()
    
    # Get available tools using the environment detector instance
    available_tools_info = environment_detector.detect_environment()
    available_tools = [tool['id'] for tool in available_tools_info['available_tools']]
    
    # Get intelligent tool recommendations
    suggestions = capabilities.suggest_configuration()
    recommended_tools = suggestions["recommended_tools"]
    
    # Filter recommendations by actually available tools
    viable_recommendations = [tool for tool in recommended_tools if tool in available_tools]
    
    # Create system summary
    resource_summary = capabilities.get_resource_summary()
    system_summary = {
        "performance_class": resource_summary["performance_class"],
        "memory": f"{resource_summary['memory_gb']}GB",
        "cpu_cores": resource_summary["cpu_cores"],
        "platform": capabilities.platform,
        "environment_type": capabilities.environment_type,
        "internet_access": capabilities.internet_access,
        "models_available": len(capabilities.available_models),
        "preferred_model": capabilities.preferred_model,
        "apis_available": capabilities.available_apis,
        "tools_available": len(available_tools),
        "container_runtime": capabilities.container_runtime
    }
    
    # Generate optimization suggestions
    optimization_suggestions = []
    
    if capabilities.is_low_resource:
        optimization_suggestions.extend([
            "Consider using lighter models like gpt-4o-mini for better performance",
            "Disable memory features to conserve resources",
            "Limit concurrent requests to prevent resource exhaustion"
        ])
    
    if not capabilities.internet_access:
        optimization_suggestions.append("Limited to local tools - consider enabling internet access for web-based tools")
    
    if len(capabilities.available_apis) < 2:
        optimization_suggestions.append("Add more API credentials to unlock additional tools and models")
    
    if not capabilities.has_docker and "docker" in [tool.get('type', '') for tool in available_tools_info['available_tools']]:
        optimization_suggestions.append("Install Docker to enable containerized tools")
    
    if capabilities.supports_gpu:
        optimization_suggestions.append("GPU detected - consider using local models for enhanced performance")
    
    # Prepare comprehensive result
    result = {
        "capabilities": capabilities,
        "available_tools": available_tools_info['available_tools'],
        "environment_summary": available_tools_info['environment_summary'],
        "tool_recommendations": {
            "recommended": viable_recommendations,
            "all_available": available_tools,
            "setup_required": [tool for tool in recommended_tools if tool not in available_tools]
        },
        "system_summary": system_summary,
        "optimization_suggestions": optimization_suggestions,
        "configuration_suggestions": suggestions,
        "timestamp": available_tools_info.get('timestamp', 'current')
    }
    
    # Print summary
    print(f"\n🎯 Environment Detection Complete")
    print(f"📊 System: {system_summary['performance_class']} performance, {system_summary['memory']} RAM, {system_summary['cpu_cores']} cores")
    print(f"🤖 Models: {system_summary['models_available']} available (preferred: {system_summary['preferred_model']})")
    print(f"🔧 Tools: {system_summary['tools_available']} available, {len(viable_recommendations)} recommended")
    print(f"🌐 Environment: {system_summary['environment_type']} on {system_summary['platform']}")
    
    if optimization_suggestions:
        print(f"\n💡 Optimization suggestions:")
        for suggestion in optimization_suggestions[:3]:  # Show top 3 suggestions
            print(f"   • {suggestion}")
    
    return result 