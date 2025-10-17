# 🧪 LangSwarm End-to-End Testing Framework

A comprehensive, production-ready E2E testing system for LangSwarm that tests real-world scenarios with actual API integration, cloud resources, and comprehensive monitoring.

## 🎯 **Key Features**

### ✅ **Comprehensive Test Coverage**
- **Multi-Agent Orchestration**: Real API workflows testing agent coordination
- **Memory Systems**: SQLite, Redis, ChromaDB, BigQuery vector search
- **Error Handling**: Validation of error messages and recovery systems
- **Cloud Integration**: BigQuery, GCS, and other cloud resource testing
- **Provider Integration**: OpenAI, Anthropic, Google, Cohere, Mistral

### 🔧 **Intelligent Test Management**
- **Auto-Discovery**: Automatically finds and categorizes tests
- **Smart Filtering**: Filter by cost, providers, categories, or cloud requirements
- **Cost Control**: Built-in cost estimation and limits
- **Parallel Execution**: Configurable parallel/sequential execution
- **Skip Logic**: Intelligent skipping based on missing dependencies

### 📊 **Real-Time Monitoring**
- **System Metrics**: CPU, memory, disk, network monitoring during tests
- **Performance Tracking**: API call counts, token usage, response times
- **Alert System**: Real-time alerts for resource usage and failures
- **Historical Analysis**: SQLite database for trend analysis

### 🔍 **Advanced Debugging**
- **Comprehensive Logging**: Detailed logs for each test execution
- **Artifact Storage**: Automatic capture of test outputs and state
- **Error Context**: Rich error information with actionable suggestions
- **Performance Profiling**: Resource usage and bottleneck identification

## 🚀 **Quick Start**

### 1. Basic Usage
```bash
# Run all available tests
python tests/e2e/runner.py

# Preview tests without executing
python tests/e2e/runner.py --dry-run

# Run simple demo
python simple_e2e_demo.py
```

### 2. Filtered Testing
```bash
# Run only orchestration tests
python tests/e2e/runner.py --category orchestration

# Run tests for specific providers
python tests/e2e/runner.py --providers openai anthropic

# Limit cost to $0.50
python tests/e2e/runner.py --max-cost 0.50

# Skip cloud resource tests
python tests/e2e/runner.py --exclude-cloud

# Run tests sequentially (good for debugging)
python tests/e2e/runner.py --sequential
```

### 3. API Keys Setup
```bash
# For real API testing
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
export COHERE_API_KEY="your-cohere-key"
export MISTRAL_API_KEY="your-mistral-key"

# For cloud resource testing
export GCP_PROJECT="your-gcp-project"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

## 📋 **Available Tests**

### 🤖 **Orchestration Tests**
| Test | Providers | Cost | Description |
|------|-----------|------|-------------|
| **Basic Orchestration** | OpenAI | $0.05 | Two-agent research → summarize workflow |
| **Multi-Provider** | OpenAI + Anthropic | $0.10 | Cross-provider agent coordination |
| **Parallel Execution** | OpenAI | $0.15 | Multiple agents working in parallel |
| **Error Recovery** | OpenAI | $0.02 | Error handling and recovery mechanisms |

### 💾 **Memory Tests**
| Test | Resources | Cost | Description |
|------|-----------|------|-------------|
| **SQLite Memory** | Local | $0.00 | Local file-based memory storage |
| **ChromaDB** | ChromaDB + OpenAI | $0.03 | Vector database with embeddings |
| **Redis Memory** | Redis | $0.00 | Redis-based caching and search |
| **BigQuery** | GCP + OpenAI | $0.05 | Cloud-scale vector search |

### 🔗 **Integration Tests**
| Test | Complexity | Cost | Description |
|------|------------|------|-------------|
| **Full Stack** | High | $0.15 | Complete workflow with config + memory |
| **Error Handling** | Medium | $0.05 | Cross-system error validation |

## 🏗️ **Framework Architecture**

### **Base Classes**
```python
from tests.e2e.framework.base import BaseE2ETest, TestEnvironment

class MyCustomTest(BaseE2ETest):
    @property
    def test_name(self) -> str:
        return "My Custom Test"
    
    @property 
    def required_providers(self) -> List[str]:
        return ["openai"]
    
    @property
    def required_resources(self) -> List[str]:
        return ["redis_instance"]
    
    async def run_test(self) -> Dict[str, Any]:
        # Your test logic here
        return {"success": True}
```

### **Environment Management**
```python
async with test_environment() as env:
    # Access API keys
    openai_key = env.get_api_key("openai")
    
    # Set up cloud resources
    dataset = await env.setup_resource("bigquery_dataset")
    
    # Access configuration
    timeout = env.config["timeouts"]["api_timeout"]
```

### **Monitoring Integration**
```python
from tests.e2e.debug.monitor import monitoring_context

async with monitoring_context() as monitoring:
    # Run tests with real-time monitoring
    monitor = monitoring["monitor"]
    debugger = monitoring["debugger"]
    
    # Tests execute with automatic monitoring
```

## 📈 **Monitoring & Debugging**

### **Real-Time Monitoring**
- **System Metrics**: CPU, memory, disk I/O, network usage
- **Test Metrics**: Duration, API calls, token usage, cost tracking
- **Alert System**: Configurable thresholds for resource usage
- **Performance Profiling**: Bottleneck identification

### **Debugging Tools**
- **Comprehensive Logs**: Structured logging for each test
- **Artifact Storage**: Test outputs, configurations, state snapshots
- **Error Context**: Rich error information with fix suggestions
- **Historical Analysis**: Performance trends over time

### **Report Generation**
```json
{
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 1,
    "errors": 0,
    "skipped": 1,
    "success_rate": 80.0
  },
  "performance": {
    "total_duration_s": 45.2,
    "total_cost_usd": 0.234,
    "total_tokens": 5670,
    "avg_duration_s": 4.52
  }
}
```

## 🔧 **Configuration**

### **Test Configuration**
```yaml
# test_config.yaml
api_keys:
  openai: "${OPENAI_API_KEY}"
  anthropic: "${ANTHROPIC_API_KEY}"

cloud:
  gcp_project: "my-project"
  gcp_credentials: "/path/to/credentials.json"

limits:
  max_cost_per_test: 1.0
  max_parallel_tests: 5
  max_tokens_per_test: 10000

timeouts:
  api_timeout: 30
  workflow_timeout: 300
```

### **Custom Test Environment**
```python
# Using custom config
runner = E2ETestRunner("my_test_config.yaml")
report = await runner.run_tests(
    category="orchestration",
    max_cost=0.50,
    parallel=False
)
```

## 🎯 **Use Cases**

### **Development Testing**
```bash
# Quick local tests during development
python tests/e2e/runner.py --exclude-cloud --max-cost 0.10
```

### **Pre-Release Validation**
```bash
# Comprehensive testing before release
python tests/e2e/runner.py --category integration
```

### **Production Monitoring**
```bash
# Ongoing production health checks
python tests/e2e/runner.py --category orchestration --max-cost 0.05
```

### **Performance Benchmarking**
```bash
# Performance regression testing
python tests/e2e/runner.py --sequential > benchmark_results.txt
```

## 🛠️ **Extending the Framework**

### **Adding New Tests**
1. **Create Test Class**:
   ```python
   class MyNewTest(BaseE2ETest):
       @property
       def test_name(self) -> str:
           return "My New Feature Test"
   ```

2. **Add to Discovery**:
   ```python
   # In tests/e2e/runner.py
   from tests.e2e.tests.my_tests import MyNewTest
   
   # Add to test_classes list
   ```

3. **Run**: Framework automatically discovers and includes new tests

### **Custom Resource Types**
```python
# In TestEnvironment
async def setup_resource(self, resource_type: str, **kwargs):
    if resource_type == "my_custom_resource":
        return await self._setup_my_resource(**kwargs)
```

### **Custom Monitoring**
```python
# Add custom metrics
monitor.add_callback(my_custom_metric_collector)

# Custom alerts
debugger = RealTimeDebugger({
    "my_metric_threshold": 100.0
})
```

## 📊 **Cost Management**

### **Cost Estimation**
- Each test provides cost estimates
- Total cost calculated before execution
- Configurable cost limits and warnings
- Real-time cost tracking during execution

### **Provider Costs** (Approximate)
- **OpenAI GPT-3.5**: ~$0.001-0.002 per test
- **OpenAI GPT-4**: ~$0.03-0.06 per test
- **Anthropic Claude**: ~$0.008-0.024 per test
- **Google Gemini**: ~$0.000125-0.00025 per test
- **BigQuery**: ~$0.005 per test (small datasets)

## 🚨 **Troubleshooting**

### **Common Issues**

**No API Key Found**
```bash
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"
```

**High Cost Warning**
```bash
# Solution: Use cost limits
python tests/e2e/runner.py --max-cost 0.25
```

**Cloud Resource Access**
```bash
# Solution: Check GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

**Test Timeouts**
```bash
# Solution: Run sequentially for debugging
python tests/e2e/runner.py --sequential --category orchestration
```

### **Debug Mode**
```bash
# Enable detailed logging
export LANGSWARM_DEBUG=1
python tests/e2e/runner.py --sequential
```

## 📚 **Best Practices**

### **Test Development**
- ✅ Always include cost estimates
- ✅ Implement proper error handling
- ✅ Use descriptive test names
- ✅ Save relevant artifacts
- ✅ Include validation logic

### **CI/CD Integration**
```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: |
    python tests/e2e/runner.py \
      --exclude-cloud \
      --max-cost 0.50 \
      --category orchestration
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### **Resource Management**
- 🔧 Use test environment context managers
- 🔧 Implement proper cleanup handlers
- 🔧 Monitor resource usage during tests
- 🔧 Set appropriate timeouts

## 🎉 **Success Metrics**

The E2E framework provides comprehensive validation that:

✅ **Multi-agent orchestration works end-to-end**  
✅ **Memory systems handle real data correctly**  
✅ **Error handling provides actionable guidance**  
✅ **Cloud integrations are functional**  
✅ **Performance meets expectations**  
✅ **Cost controls are effective**  
✅ **System resources are managed properly**

---

This E2E testing framework ensures LangSwarm works correctly in real-world scenarios with actual APIs, cloud services, and production-like workloads. It's designed to be **extensible**, **cost-effective**, and **production-ready** for continuous validation of the LangSwarm ecosystem.