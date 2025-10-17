#!/usr/bin/env python3
"""
LangSwarm E2E Interactive Setup Script

Interactive setup that prompts for missing configuration and confirms existing values.
Provides a user-friendly way to configure the E2E testing environment.
"""

import os
import sys
import json
import subprocess
import getpass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Colors for terminal output
class Colors:
    """Terminal color codes."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

@dataclass
class ConfigValue:
    """Configuration value with metadata."""
    key: str
    value: Optional[str]
    description: str
    required: bool = False
    sensitive: bool = False
    validator: Optional[callable] = None

class InteractiveSetup:
    """Interactive setup wizard for E2E testing."""
    
    def __init__(self):
        self.config_values: Dict[str, ConfigValue] = {}
        self.env_file = Path(".env")
        self.config_file = Path("tests/e2e/config/test_config.json")
        
    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
        
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")
        
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")
        
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.RED}❌ {text}{Colors.ENDC}")
        
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")
        
    def prompt_value(self, config: ConfigValue) -> str:
        """Prompt user for a configuration value."""
        # Build prompt
        prompt = f"\n{Colors.BOLD}{config.description}{Colors.ENDC}\n"
        
        if config.value:
            if config.sensitive:
                masked = config.value[:4] + "*" * (len(config.value) - 8) + config.value[-4:]
                prompt += f"Current: {Colors.GREEN}{masked}{Colors.ENDC}\n"
            else:
                prompt += f"Current: {Colors.GREEN}{config.value}{Colors.ENDC}\n"
            prompt += "Press Enter to keep current value, or enter new value: "
        else:
            if config.required:
                prompt += f"{Colors.YELLOW}(Required){Colors.ENDC} "
            prompt += "Enter value: "
            
        # Get input
        if config.sensitive:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt).strip()
            
        # Use existing value if empty input
        if not value and config.value:
            return config.value
            
        # Validate if provided
        if value and config.validator:
            is_valid, error_msg = config.validator(value)
            if not is_valid:
                self.print_error(error_msg)
                return self.prompt_value(config)  # Retry
                
        return value
    
    def validate_api_key(self, key_name: str) -> callable:
        """Create API key validator."""
        def validator(value: str) -> Tuple[bool, Optional[str]]:
            if key_name == "OPENAI_API_KEY" and not value.startswith("sk-"):
                return False, "OpenAI API keys should start with 'sk-'"
            if len(value) < 20:
                return False, f"{key_name} seems too short"
            return True, None
        return validator
    
    def validate_gcp_project(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate GCP project ID."""
        if not value or value == "(unset)":
            return False, "Invalid project ID"
        if len(value) < 6 or len(value) > 30:
            return False, "Project ID must be 6-30 characters"
        return True, None
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists."""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_gcp_project(self) -> Optional[str]:
        """Get current GCP project."""
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True
            )
            project = result.stdout.strip()
            return project if project and project != "(unset)" else None
        except:
            return None
    
    def load_existing_config(self):
        """Load existing configuration from environment and files."""
        self.print_info("Checking existing configuration...")
        
        # API Keys
        api_keys = [
            ("OPENAI_API_KEY", "OpenAI API Key", True),
            ("ANTHROPIC_API_KEY", "Anthropic API Key", True),
            ("GOOGLE_API_KEY", "Google API Key", False),
            ("COHERE_API_KEY", "Cohere API Key", False),
            ("MISTRAL_API_KEY", "Mistral API Key", False),
        ]
        
        for key, desc, required in api_keys:
            self.config_values[key] = ConfigValue(
                key=key,
                value=os.getenv(key),
                description=desc,
                required=required,
                sensitive=True,
                validator=self.validate_api_key(key)
            )
        
        # GCP Configuration
        if self.check_command_exists("gcloud"):
            gcp_project = self.get_gcp_project()
            self.config_values["GCP_PROJECT"] = ConfigValue(
                key="GCP_PROJECT",
                value=gcp_project or os.getenv("GCP_PROJECT"),
                description="Google Cloud Project ID",
                required=False,
                validator=self.validate_gcp_project
            )
            
            self.config_values["GOOGLE_APPLICATION_CREDENTIALS"] = ConfigValue(
                key="GOOGLE_APPLICATION_CREDENTIALS",
                value=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "tests/e2e/credentials/gcp-service-account.json"),
                description="Path to GCP service account JSON file",
                required=False
            )
        
        # Database URLs
        self.config_values["REDIS_URL"] = ConfigValue(
            key="REDIS_URL",
            value=os.getenv("REDIS_URL", "redis://localhost:6379"),
            description="Redis connection URL",
            required=False
        )
        
        # Test Settings
        self.config_values["MAX_COST_PER_TEST"] = ConfigValue(
            key="MAX_COST_PER_TEST",
            value=os.getenv("MAX_COST_PER_TEST", "1.0"),
            description="Maximum cost per test in USD",
            required=False
        )
        
        self.config_values["MAX_PARALLEL_TESTS"] = ConfigValue(
            key="MAX_PARALLEL_TESTS",
            value=os.getenv("MAX_PARALLEL_TESTS", "3"),
            description="Maximum parallel test execution",
            required=False
        )
    
    def show_current_config(self):
        """Show current configuration status."""
        self.print_header("Current Configuration")
        
        # Group by category
        categories = {
            "AI Providers": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "COHERE_API_KEY", "MISTRAL_API_KEY"],
            "Google Cloud": ["GCP_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"],
            "Databases": ["REDIS_URL"],
            "Test Settings": ["MAX_COST_PER_TEST", "MAX_PARALLEL_TESTS"]
        }
        
        for category, keys in categories.items():
            print(f"\n{Colors.BOLD}{category}:{Colors.ENDC}")
            for key in keys:
                if key in self.config_values:
                    config = self.config_values[key]
                    if config.value:
                        if config.sensitive:
                            masked = config.value[:4] + "*" * (len(config.value) - 8) + config.value[-4:]
                            print(f"  {config.key}: {Colors.GREEN}{masked}{Colors.ENDC}")
                        else:
                            print(f"  {config.key}: {Colors.GREEN}{config.value}{Colors.ENDC}")
                    else:
                        status = f"{Colors.RED}Not set{Colors.ENDC}"
                        if config.required:
                            status += f" {Colors.YELLOW}(Required){Colors.ENDC}"
                        print(f"  {config.key}: {status}")
    
    def prompt_configuration(self):
        """Prompt user to update configuration."""
        self.print_header("Configuration Setup")
        
        # Check if user wants to modify
        response = input(f"\nWould you like to modify any configuration values? ({Colors.GREEN}y{Colors.ENDC}/n): ").strip().lower()
        
        if response != 'y' and response != 'yes':
            self.print_info("Keeping existing configuration")
            return
        
        # Prompt for categories
        print(f"\n{Colors.BOLD}Select what to configure:{Colors.ENDC}")
        print("1. AI Provider API Keys (Required)")
        print("2. Google Cloud Platform")
        print("3. Database URLs")
        print("4. Test Settings")
        print("5. Configure All")
        print("0. Skip")
        
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == "0":
            return
            
        # Map choices to config keys
        choice_map = {
            "1": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "COHERE_API_KEY", "MISTRAL_API_KEY"],
            "2": ["GCP_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"],
            "3": ["REDIS_URL"],
            "4": ["MAX_COST_PER_TEST", "MAX_PARALLEL_TESTS"],
            "5": list(self.config_values.keys())
        }
        
        keys_to_configure = choice_map.get(choice, [])
        
        # Prompt for each selected key
        for key in keys_to_configure:
            if key in self.config_values:
                new_value = self.prompt_value(self.config_values[key])
                if new_value:
                    self.config_values[key].value = new_value
    
    def validate_configuration(self) -> bool:
        """Validate the configuration is sufficient for testing."""
        self.print_header("Validating Configuration")
        
        issues = []
        warnings = []
        
        # Check required API keys
        api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        has_api_key = any(self.config_values[key].value for key in api_keys if key in self.config_values)
        
        if not has_api_key:
            issues.append("No AI provider API keys configured (need at least OpenAI or Anthropic)")
        
        # Check GCP if BigQuery tests desired
        if "GCP_PROJECT" in self.config_values:
            if not self.config_values["GCP_PROJECT"].value:
                warnings.append("No GCP project configured - BigQuery tests will be skipped")
        
        # Check Redis
        redis_url = self.config_values.get("REDIS_URL", ConfigValue("", None, "")).value
        if redis_url:
            # Try to validate Redis connection
            try:
                import redis
                client = redis.from_url(redis_url)
                client.ping()
                self.print_success(f"Redis connection verified at {redis_url}")
            except ImportError:
                warnings.append("Redis library not installed - run: pip install redis")
            except Exception:
                warnings.append(f"Cannot connect to Redis at {redis_url}")
        
        # Show results
        if issues:
            for issue in issues:
                self.print_error(issue)
            return False
            
        if warnings:
            for warning in warnings:
                self.print_warning(warning)
                
        self.print_success("Configuration is valid!")
        return True
    
    def save_configuration(self):
        """Save configuration to .env and config files."""
        self.print_header("Saving Configuration")
        
        # Create directories
        Path("tests/e2e/config").mkdir(parents=True, exist_ok=True)
        Path("tests/e2e/credentials").mkdir(parents=True, exist_ok=True)
        
        # Save to .env file
        env_lines = ["# LangSwarm E2E Test Configuration\n"]
        env_lines.append("# Generated by interactive setup\n\n")
        
        categories = {
            "# AI Provider API Keys": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "COHERE_API_KEY", "MISTRAL_API_KEY"],
            "\n# Google Cloud Platform": ["GCP_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"],
            "\n# Database URLs": ["REDIS_URL"],
            "\n# Test Settings": ["MAX_COST_PER_TEST", "MAX_PARALLEL_TESTS"]
        }
        
        for comment, keys in categories.items():
            env_lines.append(f"{comment}\n")
            for key in keys:
                if key in self.config_values and self.config_values[key].value:
                    env_lines.append(f"{key}={self.config_values[key].value}\n")
        
        # Write .env file
        with open(self.env_file, 'w') as f:
            f.writelines(env_lines)
        
        self.print_success(f"Configuration saved to {self.env_file}")
        
        # Create test config JSON
        test_config = {
            "api_keys": {
                "openai": self.config_values.get("OPENAI_API_KEY", ConfigValue("", None, "")).value,
                "anthropic": self.config_values.get("ANTHROPIC_API_KEY", ConfigValue("", None, "")).value,
                "google": self.config_values.get("GOOGLE_API_KEY", ConfigValue("", None, "")).value,
                "cohere": self.config_values.get("COHERE_API_KEY", ConfigValue("", None, "")).value,
                "mistral": self.config_values.get("MISTRAL_API_KEY", ConfigValue("", None, "")).value,
            },
            "cloud": {
                "gcp_project": self.config_values.get("GCP_PROJECT", ConfigValue("", None, "")).value,
                "gcp_credentials": self.config_values.get("GOOGLE_APPLICATION_CREDENTIALS", ConfigValue("", None, "")).value,
            },
            "databases": {
                "redis_url": self.config_values.get("REDIS_URL", ConfigValue("", None, "")).value,
            },
            "limits": {
                "max_cost_per_test": float(self.config_values.get("MAX_COST_PER_TEST", ConfigValue("", "1.0", "")).value),
                "max_parallel_tests": int(self.config_values.get("MAX_PARALLEL_TESTS", ConfigValue("", "3", "")).value),
            }
        }
        
        # Write config JSON
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        self.print_success(f"Test config saved to {self.config_file}")
    
    def setup_gcp_resources(self):
        """Optionally set up GCP resources."""
        if not self.config_values.get("GCP_PROJECT", ConfigValue("", None, "")).value:
            return
            
        response = input(f"\n{Colors.BOLD}Would you like to set up GCP resources (service account, BigQuery)?{Colors.ENDC} (y/n): ").strip().lower()
        
        if response != 'y' and response != 'yes':
            return
            
        self.print_info("Setting up GCP resources...")
        
        # Run comprehensive setup for GCP
        try:
            subprocess.run(
                [sys.executable, "setup_e2e_environment.py", "--gcp-only"],
                check=True
            )
            self.print_success("GCP resources configured successfully")
        except subprocess.CalledProcessError:
            self.print_warning("GCP setup encountered issues - check logs above")
    
    def show_next_steps(self):
        """Show next steps for the user."""
        self.print_header("Setup Complete!")
        
        print("📋 Next steps:\n")
        print(f"1. {Colors.BOLD}Source the environment:{Colors.ENDC}")
        print(f"   {Colors.CYAN}source .env{Colors.ENDC}\n")
        
        print(f"2. {Colors.BOLD}Install dependencies:{Colors.ENDC}")
        print(f"   {Colors.CYAN}pip install -r tests/e2e/requirements.txt{Colors.ENDC}\n")
        
        print(f"3. {Colors.BOLD}Run tests:{Colors.ENDC}")
        print(f"   {Colors.CYAN}cd tests/e2e && make test-basic{Colors.ENDC}\n")
        
        print(f"4. {Colors.BOLD}View available commands:{Colors.ENDC}")
        print(f"   {Colors.CYAN}cd tests/e2e && make help{Colors.ENDC}\n")
        
        # Show test categories available
        has_openai = bool(self.config_values.get("OPENAI_API_KEY", ConfigValue("", None, "")).value)
        has_anthropic = bool(self.config_values.get("ANTHROPIC_API_KEY", ConfigValue("", None, "")).value)
        has_gcp = bool(self.config_values.get("GCP_PROJECT", ConfigValue("", None, "")).value)
        
        print(f"{Colors.BOLD}Available test categories based on your configuration:{Colors.ENDC}")
        print(f"  ✅ SQLite Memory Tests (no API keys required)")
        if has_openai or has_anthropic:
            print(f"  ✅ Orchestration Tests")
            print(f"  ✅ Integration Tests")
        if has_openai:
            print(f"  ✅ ChromaDB Vector Tests")
        if has_gcp and has_openai:
            print(f"  ✅ BigQuery Cloud Tests")
            
    def run(self):
        """Run the interactive setup process."""
        self.print_header("LangSwarm E2E Interactive Setup")
        
        # Load existing configuration
        self.load_existing_config()
        
        # Show current status
        self.show_current_config()
        
        # Prompt for updates
        self.prompt_configuration()
        
        # Validate
        if not self.validate_configuration():
            response = input("\nContinue anyway? (y/n): ").strip().lower()
            if response != 'y' and response != 'yes':
                self.print_error("Setup cancelled")
                return False
        
        # Save configuration
        self.save_configuration()
        
        # Optional GCP setup
        self.setup_gcp_resources()
        
        # Show next steps
        self.show_next_steps()
        
        return True

def main():
    """Main entry point."""
    setup = InteractiveSetup()
    
    try:
        success = setup.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Setup failed: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()