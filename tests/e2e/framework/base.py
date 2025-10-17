"""
LangSwarm End-to-End Testing Framework

Comprehensive, extensible testing framework for real-world scenarios
including API integrations, cloud resources, and multi-agent workflows.
"""

import asyncio
import json
import time
import uuid
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Callable, Type
from pathlib import Path
from contextlib import asynccontextmanager
import traceback

# Test result tracking
@dataclass
class TestMetrics:
    """Comprehensive test metrics and timing."""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    api_calls: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    memory_peak_mb: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Complete test result with rich debugging information."""
    test_id: str
    test_name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    metrics: TestMetrics
    details: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)  # file paths
    logs: List[str] = field(default_factory=list)
    stacktrace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status,
            "duration_ms": self.metrics.duration_ms,
            "api_calls": self.metrics.api_calls,
            "tokens_used": self.metrics.tokens_used,
            "cost_estimate": self.metrics.cost_estimate,
            "memory_peak_mb": self.metrics.memory_peak_mb,
            "errors": self.metrics.errors,
            "warnings": self.metrics.warnings,
            "details": self.details,
            "artifacts": self.artifacts,
            "logs": self.logs[-10:],  # Keep last 10 log entries
            "stacktrace": self.stacktrace
        }


class TestEnvironment:
    """Manages test environment configuration and resources."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.resources: Dict[str, Any] = {}
        self.cleanup_handlers: List[Callable] = []
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load test configuration from file or environment."""
        config = {
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY"),
                "anthropic": os.getenv("ANTHROPIC_API_KEY"),
                "google": os.getenv("GOOGLE_API_KEY"),
                "cohere": os.getenv("COHERE_API_KEY"),
                "mistral": os.getenv("MISTRAL_API_KEY"),
            },
            "cloud": {
                "gcp_project": os.getenv("GCP_PROJECT"),
                "gcp_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                "azure_subscription": os.getenv("AZURE_SUBSCRIPTION_ID"),
            },
            "databases": {
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "postgres_url": os.getenv("POSTGRES_URL", "postgresql://localhost:5432/langswarm_test"),
                "bigquery_dataset": os.getenv("BIGQUERY_DATASET", "langswarm_test"),
            },
            "timeouts": {
                "api_timeout": 30,
                "workflow_timeout": 300,
                "resource_setup_timeout": 120,
            },
            "limits": {
                "max_tokens_per_test": 10000,
                "max_cost_per_test": 1.0,  # $1 USD
                "max_parallel_tests": 5,
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider with validation."""
        key = self.config["api_keys"].get(provider)
        if not key:
            logging.warning(f"No API key found for {provider}")
        return key
    
    def has_required_keys(self, providers: List[str]) -> bool:
        """Check if all required API keys are available."""
        return all(self.get_api_key(p) for p in providers)
    
    async def setup_resource(self, resource_type: str, **kwargs) -> Any:
        """Set up cloud or database resources for testing."""
        if resource_type == "bigquery_dataset":
            return await self._setup_bigquery_dataset(**kwargs)
        elif resource_type == "redis_instance":
            return await self._setup_redis_instance(**kwargs)
        elif resource_type == "chromadb_collection":
            return await self._setup_chromadb_collection(**kwargs)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")
    
    async def _setup_bigquery_dataset(self, dataset_id: str = None) -> str:
        """Set up BigQuery dataset for testing."""
        try:
            from google.cloud import bigquery
            
            client = bigquery.Client(project=self.config["cloud"]["gcp_project"])
            dataset_id = dataset_id or f"langswarm_test_{int(time.time())}"
            dataset_ref = client.dataset(dataset_id)
            
            # Create dataset if it doesn't exist
            try:
                client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                dataset = client.create_dataset(dataset)
                
                # Add cleanup handler
                self.cleanup_handlers.append(
                    lambda: client.delete_dataset(dataset_ref, delete_contents=True)
                )
            
            self.resources[f"bigquery_dataset_{dataset_id}"] = dataset_id
            return dataset_id
            
        except ImportError:
            raise ImportError("Google Cloud BigQuery not available. Install with: pip install google-cloud-bigquery")
    
    async def _setup_redis_instance(self, **kwargs) -> Optional[str]:
        """Set up Redis instance for testing."""
        try:
            import redis
            
            url = self.config["databases"]["redis_url"]
            client = redis.from_url(url)
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(None, client.ping)
            
            self.resources["redis_client"] = client
            return url
            
        except ImportError:
            raise ImportError("Redis not available. Install with: pip install redis")
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}. Ensure Redis server is running.")
    
    async def _setup_chromadb_collection(self, collection_name: str = None) -> Optional[str]:
        """Set up ChromaDB collection for testing."""
        try:
            import chromadb
            
            client = chromadb.Client()
            collection_name = collection_name or f"test_collection_{int(time.time())}"
            
            collection = client.create_collection(collection_name)
            
            # Add cleanup handler
            self.cleanup_handlers.append(
                lambda: client.delete_collection(collection_name)
            )
            
            self.resources[f"chromadb_collection_{collection_name}"] = collection
            return collection_name
            
        except ImportError:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
    
    async def cleanup(self):
        """Clean up all test resources."""
        for handler in self.cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logging.error(f"Cleanup error: {e}")
                # Don't raise during cleanup to avoid masking test failures


class BaseE2ETest(ABC):
    """Base class for all end-to-end tests."""
    
    def __init__(self, environment: TestEnvironment):
        self.env = environment
        self.test_id = str(uuid.uuid4())
        self.metrics = TestMetrics()
        self._artifacts_dir = Path(f"test_artifacts/{self.test_id}")
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up test-specific logger."""
        logger = logging.getLogger(f"e2e_test_{self.test_id}")
        logger.setLevel(logging.DEBUG)
        
        # File handler for test logs
        log_file = self._artifacts_dir / "test.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    @property
    @abstractmethod
    def test_name(self) -> str:
        """Human-readable test name."""
        pass
    
    @property
    @abstractmethod
    def required_providers(self) -> List[str]:
        """List of required API providers."""
        pass
    
    @property
    @abstractmethod
    def required_resources(self) -> List[str]:
        """List of required cloud/database resources."""
        pass
    
    def should_skip(self) -> Optional[str]:
        """Check if test should be skipped and return reason."""
        # Check API keys
        missing_keys = [p for p in self.required_providers 
                       if not self.env.get_api_key(p)]
        if missing_keys:
            return f"Missing API keys: {', '.join(missing_keys)}"
        
        # Check cost limits
        if self.estimated_cost() > self.env.config["limits"]["max_cost_per_test"]:
            return f"Test cost estimate ${self.estimated_cost():.2f} exceeds limit"
        
        return None
    
    def estimated_cost(self) -> float:
        """Estimate test cost in USD."""
        return 0.1  # Default conservative estimate
    
    async def setup(self) -> None:
        """Set up test-specific resources."""
        self.logger.info(f"Setting up test: {self.test_name}")
        
        # Set up required resources
        for resource in self.required_resources:
            try:
                result = await self.env.setup_resource(resource)
                self.logger.info(f"Set up {resource}: {result}")
            except Exception as e:
                self.logger.error(f"Failed to set up {resource}: {e}")
                raise
    
    async def teardown(self) -> None:
        """Clean up test-specific resources."""
        self.logger.info(f"Tearing down test: {self.test_name}")
        # Base teardown - subclasses can override
    
    @abstractmethod
    async def run_test(self) -> Dict[str, Any]:
        """Execute the main test logic."""
        pass
    
    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate test results."""
        return result.get("success", False)
    
    def save_artifact(self, name: str, content: str, file_type: str = "txt") -> str:
        """Save test artifact and return file path."""
        file_path = self._artifacts_dir / f"{name}.{file_type}"
        with open(file_path, 'w') as f:
            f.write(content)
        return str(file_path)
    
    def save_json_artifact(self, name: str, data: Any) -> str:
        """Save JSON artifact and return file path."""
        content = json.dumps(data, indent=2, default=str)
        return self.save_artifact(name, content, "json")
    
    def track_api_call(self, provider: str, tokens: int = 0, cost: float = 0.0):
        """Track API usage for cost and rate limiting."""
        self.metrics.api_calls += 1
        self.metrics.tokens_used += tokens
        self.metrics.cost_estimate += cost
        self.logger.debug(f"API call to {provider}: {tokens} tokens, ${cost:.4f}")
    
    async def execute(self) -> TestResult:
        """Execute the complete test with metrics and error handling."""
        self.metrics.start_time = datetime.now(timezone.utc)
        
        try:
            # Check if test should be skipped
            skip_reason = self.should_skip()
            if skip_reason:
                return TestResult(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    status="SKIP",
                    metrics=self.metrics,
                    details={"skip_reason": skip_reason}
                )
            
            # Setup phase
            await self.setup()
            
            # Execute test
            result = await self.run_test()
            
            # Validate results
            is_valid = await self.validate_result(result)
            
            # Create test result
            test_result = TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status="PASS" if is_valid else "FAIL",
                metrics=self.metrics,
                details=result
            )
            
            # Save artifacts
            test_result.artifacts["result"] = self.save_json_artifact("result", result)
            test_result.artifacts["logs"] = str(self._artifacts_dir / "test.log")
            
            return test_result
            
        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            self.metrics.errors.append(str(e))
            
            return TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status="ERROR",
                metrics=self.metrics,
                details={"error": str(e)},
                stacktrace=traceback.format_exc()
            )
            
        finally:
            # Always run teardown
            try:
                await self.teardown()
            except Exception as e:
                self.logger.error(f"Teardown failed: {e}")
            
            # Finalize metrics
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.duration_ms = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds() * 1000


class E2ETestSuite:
    """Manages and executes multiple E2E tests."""
    
    def __init__(self, environment: TestEnvironment):
        self.env = environment
        self.tests: List[BaseE2ETest] = []
        self.results: List[TestResult] = []
    
    def add_test(self, test_class: Type[BaseE2ETest], **kwargs):
        """Add a test to the suite."""
        test = test_class(self.env, **kwargs)
        self.tests.append(test)
    
    async def run_all(self, parallel: bool = True) -> List[TestResult]:
        """Run all tests in the suite."""
        if parallel:
            return await self._run_parallel()
        else:
            return await self._run_sequential()
    
    async def _run_sequential(self) -> List[TestResult]:
        """Run tests sequentially."""
        results = []
        for test in self.tests:
            print(f"🧪 Running: {test.test_name}")
            result = await test.execute()
            results.append(result)
            self._print_result(result)
        return results
    
    async def _run_parallel(self) -> List[TestResult]:
        """Run tests in parallel with concurrency limits."""
        max_concurrent = self.env.config["limits"]["max_parallel_tests"]
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(test):
            async with semaphore:
                print(f"🧪 Running: {test.test_name}")
                result = await test.execute()
                self._print_result(result)
                return result
        
        tasks = [run_with_semaphore(test) for test in self.tests]
        results = await asyncio.gather(*tasks)
        return results
    
    def _print_result(self, result: TestResult):
        """Print test result summary."""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌", 
            "SKIP": "⏭️",
            "ERROR": "💥"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        duration = result.metrics.duration_ms / 1000
        cost = result.metrics.cost_estimate
        
        print(f"{emoji} {result.test_name}: {result.status} "
              f"({duration:.1f}s, ${cost:.3f}, {result.metrics.api_calls} API calls)")
        
        if result.status in ["FAIL", "ERROR"] and result.metrics.errors:
            print(f"   Error: {result.metrics.errors[0]}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        if not self.results:
            return {"error": "No test results available"}
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        total_cost = sum(r.metrics.cost_estimate for r in self.results)
        total_tokens = sum(r.metrics.tokens_used for r in self.results)
        total_duration = sum(r.metrics.duration_ms for r in self.results) / 1000
        
        return {
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0
            },
            "performance": {
                "total_duration_s": total_duration,
                "total_cost_usd": total_cost,
                "total_tokens": total_tokens,
                "avg_duration_s": total_duration / total_tests if total_tests > 0 else 0
            },
            "tests": [r.to_dict() for r in self.results]
        }


@asynccontextmanager
async def test_environment(config_path: Optional[str] = None):
    """Context manager for test environment with automatic cleanup."""
    env = TestEnvironment(config_path)
    try:
        yield env
    finally:
        await env.cleanup()