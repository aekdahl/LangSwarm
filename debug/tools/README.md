# LangSwarm Debug Tools Testing System

A comprehensive CLI system for testing debug tools using LangSwarm workflows with full tracing and observability integration.

## 🎯 Overview

This system provides:
- **Two Debug Tools**: BigQuery Vector Search and SQL Database tools
- **LangSwarm Workflow Integration**: Complete workflow orchestration with agents
- **Comprehensive Tracing**: Hierarchical tracing with structured JSON logs
- **CLI Interface**: Easy-to-use command-line interface with interactive mode
- **Automated Testing**: Comprehensive test suite with detailed reporting

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to debug tools directory
cd debug/tools

# Set up directories and check environment
make setup
make check-env
```

### 2. Set Required Environment Variables

```bash
# For BigQuery tool (optional - will use mock data if not available)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# For OpenAI agent functionality (required for workflows)
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Run Health Check

```bash
# Check if all tools are working
make health-check
```

### 4. Test Individual Tools

```bash
# Interactive query selection (NEW!)
make sql-interactive        # Browse pre-written SQL queries or write custom
make bigquery-interactive   # Browse pre-written BigQuery queries or write custom

# Direct query execution
make bigquery QUERY="What is machine learning?"
make sql QUERY="SELECT * FROM employees LIMIT 5"
```

### 5. Run Comprehensive Tests

```bash
# Run full test suite with detailed reporting
make test-all
```

## 🛠️ Available Commands

### Setup & Environment
```bash
make setup          # Set up directories and environment
make health-check   # Check health of all tools
make check-env      # Show environment configuration
make clean          # Clean up logs, traces, and temp files
```

### Testing Commands
```bash
make test-all       # Run comprehensive test suite
make test-bigquery  # Test BigQuery vector search tool
make test-sql       # Test SQL database tool
make test-workflows # Test workflow execution
```

### Interactive Mode
```bash
make interactive    # Start interactive CLI mode
```

### Individual Tool Tests
```bash
make bigquery QUERY='your query'              # Test BigQuery with specific query
make sql QUERY='SELECT * FROM employees'      # Test SQL with specific query
```

### Development Helpers
```bash
make show-logs      # Show recent log files
make show-traces    # Show recent trace files and events
make quick-test     # Run quick development tests
```

## 🔧 CLI Usage

### Direct CLI Commands

```bash
# Interactive query selection (NEW!)
python cli.py --debug test-tool --tool sql        # Browse SQL queries
python cli.py --debug test-tool --tool bigquery   # Browse BigQuery queries

# Test with specific query
python cli.py --debug test-tool --tool bigquery --query "What is AI?"

# Test a workflow
python cli.py test-workflow --workflow single_tool_test --query "Find ML info"

# Health check
python cli.py health-check

# Interactive mode
python cli.py interactive
```

### Interactive Mode Commands

Once in interactive mode (`make interactive`):

```bash
> bigquery                                      # Interactive BigQuery query selection (NEW!)
> bigquery What is artificial intelligence?     # Test BigQuery with specific query
> sql                                           # Interactive SQL query selection (NEW!)
> sql SELECT name, department FROM employees    # Test SQL with specific query
> workflow single_tool_test Find AI information # Test workflow
> health                                        # Check tool health
> help                                          # Show help
> quit                                          # Exit
```

## 🏗️ System Architecture

### Components

1. **Tools** (`bigquery_vector_search/tool.py`, `sql_database/tool.py`)
   - Self-contained debug tools with comprehensive error handling
   - Support for health checks, schema inspection, and performance monitoring
   - Mock data generation for testing without external dependencies

2. **CLI Interface** (`cli.py`)
   - Command-line interface with argument parsing
   - Interactive mode for exploratory testing
   - Colored output and structured result display

3. **Tracing System** (`tracing.py`)
   - Hierarchical span tracing with trace_id/span_id relationships
   - Structured JSON log output for analysis
   - Performance tracking and statistics

4. **Test Runner** (`test_runner.py`)
   - Comprehensive automated test suite
   - Performance testing and error handling validation
   - Detailed reporting with success/failure analysis

5. **Workflow Configuration** (`debug_tools_config.yaml`)
   - LangSwarm configuration with agents, tools, and workflows
   - Observability settings with tracing and logging
   - Memory and security configurations

### Data Flow

```
User Query → CLI → Tool/Workflow → Agent → Tool Execution → Results
     ↓
  Tracing System → JSON Logs → Analysis/Debugging
```

## 📊 Tracing and Observability

### Trace Files

All operations are traced to JSON files in the `traces/` directory:

```bash
# View recent traces
make show-traces

# Analyze trace file manually
cat traces/tool_test_20240101_120000.jsonl | jq '.message'
```

### Trace Event Types

- `SESSION_START/END`: Session boundaries
- `SPAN_START/END`: Operation boundaries with timing
- `TOOL_CALL_SUCCESS/ERROR`: Tool execution results
- `AGENT_RESPONSE`: Agent interactions
- `WORKFLOW_STEP_SUCCESS/ERROR`: Workflow step execution

### Log Files

Detailed logs are written to the `logs/` directory with configurable levels:

```bash
# View recent logs
tail -f logs/debug_tools_*.log
```

## 🧪 Testing

### Automated Test Suite

The comprehensive test suite includes:

1. **Health Checks**: Verify all tools are accessible and configured
2. **BigQuery Tests**: Vector search functionality with various queries
3. **SQL Tests**: Database operations including safety checks
4. **Workflow Tests**: End-to-end workflow execution
5. **Error Handling**: Graceful failure and error reporting
6. **Performance Tests**: Response time and throughput validation

### Test Categories

```bash
# Run specific test categories
python test_runner.py  # Runs all categories:
# - Health Checks
# - BigQuery Tool Tests  
# - SQL Tool Tests
# - Workflow Tests
# - Error Handling Tests
# - Performance Tests
```

### Test Results

Results are saved to `test_results/` with detailed JSON reports including:
- Overall statistics (pass/fail rates, timing)
- Individual test results with error details
- Performance metrics and tracing statistics

## 🔍 Debugging

### Common Issues

1. **BigQuery Tool Fails**
   ```bash
   # Check Google Cloud configuration
   gcloud auth application-default login
   export GOOGLE_CLOUD_PROJECT="your-project"
   
   # Test with health check
   make health-check
   ```

2. **SQL Tool Fails**
   ```bash
   # Check if test database exists
   ls -la test_database.db
   
   # Recreate test data
   rm test_database.db
   python cli.py test-tool --tool sql --query "SELECT 1"
   ```

3. **Workflow Fails**
   ```bash
   # Check OpenAI API key
   echo $OPENAI_API_KEY
   
   # Test individual components
   make health-check
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# CLI with debug logging
python cli.py test-tool --tool sql --query "SELECT * FROM employees" --debug

# Make commands with debug
make bigquery QUERY="test" --debug
```

### Trace Analysis

Analyze traces for debugging:

```bash
# Show trace events for a specific component
cat traces/*.jsonl | jq 'select(.component == "tool")'

# Show error events
cat traces/*.jsonl | jq 'select(.level == "ERROR")'

# Show timing information
cat traces/*.jsonl | jq 'select(.duration_ms != null) | {operation, duration_ms}'
```

## 📈 Performance Monitoring

### Metrics Tracked

- **Tool Execution Time**: Individual tool call performance
- **Workflow Duration**: End-to-end workflow timing
- **Error Rates**: Success/failure statistics
- **Trace Overhead**: Tracing system performance impact

### Performance Thresholds

- SQL queries: < 1000ms
- BigQuery searches: < 5000ms
- Workflow execution: < 10000ms

## 🔧 Configuration

### Tool Configuration

Edit `debug_tools_config.yaml` to modify:
- Agent system prompts and models
- Tool connection settings
- Tracing and logging levels
- Memory and security settings

### Environment Variables

```bash
# Required for workflows
OPENAI_API_KEY=your-openai-key

# Optional for BigQuery (uses mock data if not set)
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Optional for enhanced tracing
LANGSWARM_DEBUG=true
```

## 🤝 Contributing

### Adding New Tools

1. Create tool implementation in new directory
2. Implement `BaseTool` interface with `execute()` method
3. Add tool configuration to `debug_tools_config.yaml`
4. Update CLI to support new tool
5. Add tests to test runner

### Extending Tests

1. Add new test functions to `test_runner.py`
2. Update test categories in `run_comprehensive_tests()`
3. Add new CLI commands if needed
4. Update documentation

---

## 📚 Examples

### Example 1: Basic Tool Testing

```bash
# Test SQL tool with employee data
make sql QUERY="SELECT name, department, salary FROM employees WHERE salary > 80000"

# Expected output: List of high-salary employees with tracing
```

### Example 2: BigQuery Vector Search

```bash
# Test BigQuery vector search
make bigquery QUERY="How does neural network training work?"

# Expected output: Vector search results (or mock results) with metadata
```

### Example 3: Comprehensive Testing

```bash
# Run full test suite
make test-all

# Expected output: 
# - Health checks for all tools
# - Individual tool tests with various queries
# - Workflow execution tests
# - Error handling validation
# - Performance benchmarks
# - Detailed report with pass/fail statistics
```

### Example 4: Interactive Exploration

```bash
# Start interactive mode
make interactive

# Interactive session:
> health                                    # Check all tools
> sql SELECT COUNT(*) FROM employees        # Quick SQL test
> bigquery What is machine learning?        # BigQuery search
> workflow single_tool_test Find AI info    # Test workflow
> quit                                      # Exit
```

This system provides a comprehensive foundation for testing debug tools with LangSwarm integration, complete tracing, and detailed reporting capabilities.
