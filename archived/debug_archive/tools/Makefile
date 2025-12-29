# Debug Tools Makefile
# ====================
# Convenient commands for testing debug tools

.PHONY: help setup test-all test-bigquery test-sql test-workflows health-check interactive clean

# Default target
help:
	@echo "🚀 LangSwarm Debug Tools - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup & Environment:"
	@echo "  make setup          - Set up directories and environment"
	@echo "  make health-check   - Check health of all tools"
	@echo "  make clean          - Clean up logs, traces, and temp files"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test-all       - Run comprehensive test suite"
	@echo "  make test-bigquery  - Test BigQuery vector search tool"
	@echo "  make test-sql       - Test SQL database tool"
	@echo "  make test-workflows - Test workflow execution"
	@echo ""
	@echo "Interactive Mode:"
	@echo "  make interactive    - Start interactive CLI mode"
	@echo ""
	@echo "Individual Tool Tests:"
	@echo "  make bigquery QUERY='your query'  - Test BigQuery with specific query"
	@echo "  make sql QUERY='SELECT * FROM employees'  - Test SQL with specific query"
	@echo "  make bigquery-interactive         - Interactive BigQuery query selection"
	@echo "  make sql-interactive              - Interactive SQL query selection"
	@echo ""
	@echo "Examples:"
	@echo "  make bigquery QUERY='What is machine learning?'"
	@echo "  make sql QUERY='SELECT name, department FROM employees LIMIT 5'"
	@echo "  make test-all"
	@echo ""

# Setup directories and environment
setup:
	@echo "🔧 Setting up debug tools environment..."
	@mkdir -p ../traces
	@echo "✅ Traces directory created (debug/traces/)"
	@python3 -c "import sys; print(f'Python version: {sys.version}')"
	@echo "✅ Setup complete"

# Run comprehensive test suite
test-all:
	@echo "🧪 Running comprehensive test suite..."
	@python3 test_runner.py

# Health check all tools
health-check:
	@echo "🏥 Checking health of all debug tools..."
	@python3 cli.py health-check

# Test BigQuery tool
test-bigquery:
	@echo "🔍 Testing BigQuery vector search tool..."
	@python3 cli.py --debug test-tool --tool bigquery

# Test SQL tool
test-sql:
	@echo "🗄️ Testing SQL database tool..."
	@python3 cli.py --debug test-tool --tool sql

# Test workflows
test-workflows:
	@echo "🔄 Testing workflow execution..."
	@python3 cli.py test-workflow --workflow single_tool_test --query "Test workflow execution"

# Interactive mode
interactive:
	@echo "🎮 Starting interactive mode..."
	@python3 cli.py interactive

# Test BigQuery with custom query
bigquery:
	@echo "🔍 Testing BigQuery with query: $(QUERY)"
	@python3 cli.py --debug --trace test-tool --tool bigquery --query "$(QUERY)"

# Test SQL with custom query
sql:
	@echo "🗄️ Testing SQL with query: $(QUERY)"
	@python3 cli.py --debug --trace test-tool --tool sql --query "$(QUERY)"

# Interactive BigQuery testing
bigquery-interactive:
	@echo "🔍 Interactive BigQuery testing..."
	@python3 cli.py --debug test-tool --tool bigquery

# Interactive SQL testing
sql-interactive:
	@echo "🗄️ Interactive SQL testing..."
	@python3 cli.py --debug test-tool --tool sql

# Clean up generated files
clean:
	@echo "🧹 Cleaning up debug tools files..."
	@rm -rf ../traces/*
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Development helpers
dev-setup: setup
	@echo "🛠️ Setting up development environment..."
	@pip3 install -r ../../../requirements.txt
	@echo "✅ Development setup complete"

# Quick tests for development
quick-test:
	@echo "⚡ Running quick tests..."
	@python3 cli.py health-check
	@python3 cli.py test-tool --tool sql --query "SELECT COUNT(*) FROM employees"

# Show logs
show-logs:
	@echo "📋 Recent log files:"
	@ls -la logs/ | tail -5

# Show traces
show-traces:
	@echo "🔍 Recent trace files:"
	@ls -la traces/ | tail -5
	@echo ""
	@echo "📊 Latest trace events (last 10):"
	@if [ -f traces/*.jsonl ]; then tail -10 traces/*.jsonl | jq -r '.timestamp + " " + .component + "." + .operation + ": " + .message' 2>/dev/null || tail -10 traces/*.jsonl; fi

# Environment check
check-env:
	@echo "🔍 Environment Check:"
	@echo "Python: $(shell python3 --version)"
	@echo "Project root: $(shell pwd)/../../.."
	@echo "Google Cloud Project: $(GOOGLE_CLOUD_PROJECT)"
	@echo "OpenAI API Key: $(if $(OPENAI_API_KEY),✅ Set,❌ Not set)"
	@echo "Current directory: $(shell pwd)"

# Help for specific commands
help-bigquery:
	@echo "🔍 BigQuery Tool Help"
	@echo "===================="
	@echo "Test BigQuery vector search functionality"
	@echo ""
	@echo "Usage:"
	@echo "  make bigquery QUERY='your search query'"
	@echo ""
	@echo "Examples:"
	@echo "  make bigquery QUERY='What is artificial intelligence?'"
	@echo "  make bigquery QUERY='How does machine learning work?'"
	@echo ""
	@echo "Requirements:"
	@echo "  - GOOGLE_CLOUD_PROJECT environment variable"
	@echo "  - Google Cloud credentials configured"
	@echo "  - BigQuery dataset and table set up"

help-sql:
	@echo "🗄️ SQL Tool Help"
	@echo "==============="
	@echo "Test SQL database operations"
	@echo ""
	@echo "Usage:"
	@echo "  make sql QUERY='your SQL query'"
	@echo ""
	@echo "Examples:"
	@echo "  make sql QUERY='SELECT * FROM employees LIMIT 10'"
	@echo "  make sql QUERY='SELECT department, COUNT(*) FROM employees GROUP BY department'"
	@echo "  make sql QUERY='SELECT name FROM employees WHERE department = \"Engineering\"'"
	@echo ""
	@echo "Available tables:"
	@echo "  - employees (id, name, department, salary, hire_date, active)"
	@echo "  - departments (id, name, budget, manager_id)"

# Default query values for testing
QUERY ?= "Default test query"
