#!/usr/bin/env python3
"""
LangSwarm E2E Test Environment Setup Script

Comprehensive setup script that prepares everything needed for E2E testing:
- Cloud resources (GCP BigQuery, Redis, ChromaDB)
- API key validation
- Dependencies installation
- Test configuration
- Service account setup
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SetupResult:
    """Result of setup operation."""
    success: bool
    message: str
    details: Dict[str, Any] = None

class E2EEnvironmentSetup:
    """Comprehensive E2E test environment setup."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "tests/e2e/config/test_config.json"
        self.setup_results: List[SetupResult] = []
        self.config: Dict[str, Any] = {}
        
    def log_result(self, result: SetupResult):
        """Log and store setup result."""
        self.setup_results.append(result)
        if result.success:
            logger.info(f"✅ {result.message}")
        else:
            logger.error(f"❌ {result.message}")
            if result.details:
                logger.error(f"   Details: {result.details}")

    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def run_command(self, command: List[str], description: str) -> SetupResult:
        """Run a command and return the result."""
        try:
            logger.info(f"Running: {description}")
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            return SetupResult(
                success=True,
                message=f"{description} completed successfully",
                details={"stdout": result.stdout, "stderr": result.stderr}
            )
        except subprocess.CalledProcessError as e:
            return SetupResult(
                success=False,
                message=f"{description} failed",
                details={
                    "command": " ".join(command),
                    "return_code": e.returncode,
                    "stdout": e.stdout,
                    "stderr": e.stderr
                }
            )
        except subprocess.TimeoutExpired:
            return SetupResult(
                success=False,
                message=f"{description} timed out after 5 minutes"
            )

    def check_python_dependencies(self) -> SetupResult:
        """Check and install required Python dependencies."""
        logger.info("🔍 Checking Python dependencies...")
        
        required_packages = [
            "google-cloud-bigquery",
            "google-cloud-storage", 
            "redis",
            "chromadb",
            "psutil",
            "openai",
            "anthropic",
            "langswarm"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.info(f"Installing missing packages: {missing_packages}")
            
            # Install missing packages
            install_result = self.run_command(
                [sys.executable, "-m", "pip", "install"] + missing_packages,
                f"Installing Python packages: {', '.join(missing_packages)}"
            )
            
            if not install_result.success:
                return install_result
        
        return SetupResult(
            success=True,
            message="All Python dependencies are available",
            details={"required_packages": required_packages, "missing": missing_packages}
        )

    def check_gcloud_cli(self) -> SetupResult:
        """Check and setup Google Cloud CLI."""
        logger.info("🔍 Checking Google Cloud CLI...")
        
        if not self.check_command_exists("gcloud"):
            return SetupResult(
                success=False,
                message="Google Cloud CLI not found",
                details={
                    "install_instructions": [
                        "Install gcloud CLI:",
                        "1. Visit: https://cloud.google.com/sdk/docs/install",
                        "2. Or run: curl https://sdk.cloud.google.com | bash",
                        "3. Restart terminal and run: gcloud init"
                    ]
                }
            )
        
        # Check if authenticated
        try:
            result = subprocess.run(
                ["gcloud", "auth", "list", "--format=json"],
                check=True,
                capture_output=True,
                text=True
            )
            accounts = json.loads(result.stdout)
            
            if not accounts:
                return SetupResult(
                    success=False,
                    message="No Google Cloud accounts authenticated",
                    details={
                        "action_required": "Run 'gcloud auth login' to authenticate"
                    }
                )
            
            # Get current project
            project_result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True
            )
            
            current_project = project_result.stdout.strip()
            
            return SetupResult(
                success=True,
                message="Google Cloud CLI is configured",
                details={
                    "authenticated_accounts": [acc["account"] for acc in accounts],
                    "current_project": current_project
                }
            )
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return SetupResult(
                success=False,
                message="Failed to check gcloud authentication",
                details={"error": str(e)}
            )

    def setup_gcp_service_account(self) -> SetupResult:
        """Set up GCP service account for testing."""
        logger.info("🔧 Setting up GCP service account...")
        
        try:
            # Get current project
            project_result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                check=True,
                capture_output=True,
                text=True
            )
            project_id = project_result.stdout.strip()
            
            if not project_id or project_id == "(unset)":
                return SetupResult(
                    success=False,
                    message="No GCP project set",
                    details={"action_required": "Run 'gcloud config set project YOUR_PROJECT_ID'"}
                )
            
            service_account_name = "langswarm-e2e-tests"
            service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
            
            # Check if service account exists
            try:
                subprocess.run(
                    ["gcloud", "iam", "service-accounts", "describe", service_account_email],
                    check=True,
                    capture_output=True
                )
                logger.info(f"Service account {service_account_email} already exists")
                
            except subprocess.CalledProcessError:
                # Create service account
                create_result = self.run_command(
                    [
                        "gcloud", "iam", "service-accounts", "create", service_account_name,
                        "--display-name", "LangSwarm E2E Tests",
                        "--description", "Service account for LangSwarm end-to-end testing"
                    ],
                    f"Creating service account: {service_account_name}"
                )
                
                if not create_result.success:
                    return create_result
            
            # Grant required roles
            required_roles = [
                "roles/bigquery.admin",
                "roles/storage.admin", 
                "roles/cloudsql.admin"
            ]
            
            for role in required_roles:
                role_result = self.run_command(
                    [
                        "gcloud", "projects", "add-iam-policy-binding", project_id,
                        "--member", f"serviceAccount:{service_account_email}",
                        "--role", role
                    ],
                    f"Granting role {role} to service account"
                )
                
                if not role_result.success:
                    logger.warning(f"Failed to grant role {role}, continuing...")
            
            # Create and download key
            credentials_dir = Path("tests/e2e/credentials")
            credentials_dir.mkdir(parents=True, exist_ok=True)
            
            key_file = credentials_dir / "gcp-service-account.json"
            
            if not key_file.exists():
                key_result = self.run_command(
                    [
                        "gcloud", "iam", "service-accounts", "keys", "create", str(key_file),
                        "--iam-account", service_account_email
                    ],
                    f"Creating service account key: {key_file}"
                )
                
                if not key_result.success:
                    return key_result
            
            # Set environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file.absolute())
            
            return SetupResult(
                success=True,
                message="GCP service account configured",
                details={
                    "project_id": project_id,
                    "service_account": service_account_email,
                    "credentials_file": str(key_file),
                    "roles_granted": required_roles
                }
            )
            
        except subprocess.CalledProcessError as e:
            return SetupResult(
                success=False,
                message="Failed to setup GCP service account",
                details={"error": str(e)}
            )

    def setup_bigquery_resources(self) -> SetupResult:
        """Set up BigQuery dataset for testing."""
        logger.info("🔧 Setting up BigQuery resources...")
        
        try:
            from google.cloud import bigquery
            
            # Get project ID
            project_result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                check=True,
                capture_output=True,
                text=True
            )
            project_id = project_result.stdout.strip()
            
            client = bigquery.Client(project=project_id)
            dataset_id = "langswarm_e2e_tests"
            
            # Create dataset
            dataset_ref = client.dataset(dataset_id)
            
            try:
                dataset = client.get_dataset(dataset_ref)
                logger.info(f"BigQuery dataset {dataset_id} already exists")
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                dataset.description = "Dataset for LangSwarm E2E testing"
                
                # Set TTL for automatic cleanup
                dataset.default_table_expiration_ms = 7 * 24 * 60 * 60 * 1000  # 7 days
                
                dataset = client.create_dataset(dataset)
                logger.info(f"Created BigQuery dataset: {dataset_id}")
            
            return SetupResult(
                success=True,
                message="BigQuery resources configured",
                details={
                    "project_id": project_id,
                    "dataset_id": dataset_id,
                    "location": "US"
                }
            )
            
        except ImportError:
            return SetupResult(
                success=False,
                message="google-cloud-bigquery not available",
                details={"install_command": "pip install google-cloud-bigquery"}
            )
        except Exception as e:
            return SetupResult(
                success=False,
                message="Failed to setup BigQuery resources",
                details={"error": str(e)}
            )

    def check_redis_instance(self) -> SetupResult:
        """Check Redis availability or provide setup instructions."""
        logger.info("🔍 Checking Redis availability...")
        
        try:
            import redis
            
            # Try to connect to Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url)
            client.ping()
            
            return SetupResult(
                success=True,
                message="Redis is available",
                details={"redis_url": redis_url}
            )
            
        except ImportError:
            return SetupResult(
                success=False,
                message="Redis library not available",
                details={"install_command": "pip install redis"}
            )
        except Exception as e:
            return SetupResult(
                success=False,
                message="Redis connection failed",
                details={
                    "error": str(e),
                    "setup_instructions": [
                        "Install and start Redis:",
                        "1. macOS: brew install redis && brew services start redis",
                        "2. Ubuntu: sudo apt install redis-server",
                        "3. Docker: docker run -d -p 6379:6379 redis:alpine",
                        "4. Or set REDIS_URL environment variable for remote Redis"
                    ]
                }
            )

    def check_api_keys(self) -> SetupResult:
        """Check for required API keys."""
        logger.info("🔍 Checking API keys...")
        
        api_keys = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "COHERE_API_KEY": os.getenv("COHERE_API_KEY"),
            "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY")
        }
        
        available_keys = {k: v for k, v in api_keys.items() if v}
        missing_keys = [k for k, v in api_keys.items() if not v]
        
        if not available_keys:
            return SetupResult(
                success=False,
                message="No API keys found",
                details={
                    "missing_keys": missing_keys,
                    "instructions": [
                        "Set API keys as environment variables:",
                        "export OPENAI_API_KEY='your-key-here'",
                        "export ANTHROPIC_API_KEY='your-key-here'",
                        "Or create a .env file in the project root"
                    ]
                }
            )
        
        return SetupResult(
            success=True,
            message=f"Found {len(available_keys)} API keys",
            details={
                "available_providers": list(available_keys.keys()),
                "missing_keys": missing_keys
            }
        )

    def create_test_config(self) -> SetupResult:
        """Create test configuration file."""
        logger.info("📝 Creating test configuration...")
        
        try:
            # Get project ID
            project_result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True
            )
            project_id = project_result.stdout.strip()
            
            config = {
                "api_keys": {
                    "openai": os.getenv("OPENAI_API_KEY"),
                    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
                    "google": os.getenv("GOOGLE_API_KEY"),
                    "cohere": os.getenv("COHERE_API_KEY"),
                    "mistral": os.getenv("MISTRAL_API_KEY")
                },
                "cloud": {
                    "gcp_project": project_id,
                    "gcp_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                    "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    "azure_subscription": os.getenv("AZURE_SUBSCRIPTION_ID")
                },
                "databases": {
                    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                    "postgres_url": os.getenv("POSTGRES_URL", "postgresql://localhost:5432/langswarm_test"),
                    "bigquery_dataset": "langswarm_e2e_tests"
                },
                "timeouts": {
                    "api_timeout": 30,
                    "workflow_timeout": 300,
                    "resource_setup_timeout": 120
                },
                "limits": {
                    "max_tokens_per_test": 10000,
                    "max_cost_per_test": 1.0,
                    "max_parallel_tests": 3
                },
                "test_settings": {
                    "cleanup_after_tests": True,
                    "save_artifacts": True,
                    "enable_monitoring": True,
                    "log_level": "INFO"
                }
            }
            
            # Create config directory
            config_path = Path(self.config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.config = config
            
            return SetupResult(
                success=True,
                message=f"Test configuration created: {config_path}",
                details={"config_file": str(config_path)}
            )
            
        except Exception as e:
            return SetupResult(
                success=False,
                message="Failed to create test configuration",
                details={"error": str(e)}
            )

    def create_env_file_template(self) -> SetupResult:
        """Create .env file template."""
        logger.info("📝 Creating .env template...")
        
        env_template = """# LangSwarm E2E Test Environment Variables
# Copy this to .env and fill in your actual API keys

# AI Provider API Keys
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
COHERE_API_KEY=your-cohere-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here

# Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS=tests/e2e/credentials/gcp-service-account.json
GCP_PROJECT=your-gcp-project-id

# Database URLs
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/langswarm_test

# AWS (Optional)
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Azure (Optional)
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
"""
        
        try:
            env_file = Path(".env.template")
            with open(env_file, 'w') as f:
                f.write(env_template)
            
            return SetupResult(
                success=True,
                message=f"Environment template created: {env_file}",
                details={
                    "template_file": str(env_file),
                    "instructions": [
                        f"1. Copy {env_file} to .env",
                        "2. Fill in your actual API keys",
                        "3. Source the file: source .env"
                    ]
                }
            )
            
        except Exception as e:
            return SetupResult(
                success=False,
                message="Failed to create environment template",
                details={"error": str(e)}
            )

    def validate_setup(self) -> SetupResult:
        """Validate the complete setup."""
        logger.info("✅ Validating complete setup...")
        
        issues = []
        
        # Check if we can import key modules
        try:
            from langswarm.core.session import create_session
            from langswarm.core.agents import create_openai_agent_sync
        except ImportError as e:
            issues.append(f"LangSwarm import failed: {e}")
        
        # Check GCP credentials
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            issues.append("GOOGLE_APPLICATION_CREDENTIALS not set")
        
        # Check at least one API key
        api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        if not any(os.getenv(key) for key in api_keys):
            issues.append("No AI provider API keys found")
        
        # Check config file
        if not Path(self.config_path).exists():
            issues.append("Test configuration file not found")
        
        if issues:
            return SetupResult(
                success=False,
                message="Setup validation failed",
                details={"issues": issues}
            )
        
        return SetupResult(
            success=True,
            message="Setup validation passed",
            details={"checks_passed": ["langswarm_imports", "gcp_credentials", "api_keys", "config_file"]}
        )

    async def run_setup(self) -> Dict[str, Any]:
        """Run the complete setup process."""
        logger.info("🚀 Starting LangSwarm E2E Test Environment Setup")
        logger.info("=" * 60)
        
        setup_steps = [
            ("Python Dependencies", self.check_python_dependencies),
            ("Google Cloud CLI", self.check_gcloud_cli),
            ("GCP Service Account", self.setup_gcp_service_account),
            ("BigQuery Resources", self.setup_bigquery_resources),
            ("Redis Instance", self.check_redis_instance),
            ("API Keys", self.check_api_keys),
            ("Test Configuration", self.create_test_config),
            ("Environment Template", self.create_env_file_template),
            ("Setup Validation", self.validate_setup)
        ]
        
        for step_name, step_func in setup_steps:
            logger.info(f"\n🔧 {step_name}")
            logger.info("-" * 40)
            
            result = step_func()
            self.log_result(result)
            
            # Continue even if some steps fail, but note them
            if not result.success and step_name in ["GCP Service Account", "BigQuery Resources"]:
                logger.warning(f"⚠️  {step_name} failed but continuing setup...")
        
        # Generate summary
        successful_steps = sum(1 for r in self.setup_results if r.success)
        total_steps = len(self.setup_results)
        
        summary = {
            "setup_complete": True,
            "successful_steps": successful_steps,
            "total_steps": total_steps,
            "success_rate": successful_steps / total_steps * 100,
            "results": [
                {
                    "step": result.message,
                    "success": result.success,
                    "details": result.details
                }
                for result in self.setup_results
            ]
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 SETUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful steps: {successful_steps}/{total_steps}")
        logger.info(f"📊 Success rate: {summary['success_rate']:.1f}%")
        
        if successful_steps == total_steps:
            logger.info("🎉 All setup steps completed successfully!")
            logger.info("\n📋 Next steps:")
            logger.info("1. Run the E2E tests: python -m tests.e2e.runner")
            logger.info("2. Check test results in: tests/e2e/results/")
            logger.info("3. Monitor test execution: tests/e2e/debug/")
        else:
            logger.warning("⚠️  Some setup steps failed. Check the details above.")
            logger.info("\n🔧 Common fixes:")
            logger.info("1. Ensure gcloud CLI is installed and authenticated")
            logger.info("2. Set required API keys in environment variables")
            logger.info("3. Start Redis server or set REDIS_URL")
        
        return summary

def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up LangSwarm E2E test environment")
    parser.add_argument(
        "--config", 
        help="Path to test configuration file",
        default="tests/e2e/config/test_config.json"
    )
    parser.add_argument(
        "--skip-gcp",
        action="store_true",
        help="Skip GCP setup steps"
    )
    
    args = parser.parse_args()
    
    setup = E2EEnvironmentSetup(config_path=args.config)
    
    try:
        summary = asyncio.run(setup.run_setup())
        
        # Save summary
        results_dir = Path("tests/e2e/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        with open(results_dir / "setup_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Exit with appropriate code
        if summary["success_rate"] >= 80:  # 80% success threshold
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()