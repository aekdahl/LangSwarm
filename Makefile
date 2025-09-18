# LangSwarm Interactive Workflow Makefile
# ========================================
# This Makefile provides interactive commands for selecting and running workflows

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
BLUE=\033[0;34m
YELLOW=\033[1;33m
CYAN=\033[0;36m
NC=\033[0m # No Color

# Default Python command
PYTHON := python3

# Debug configuration file
DEBUG_CONFIG := langswarm/core/debug/debug_config.yaml

# Extract environment variables from debug_config.yaml
export GOOGLE_CLOUD_PROJECT := $(shell grep -A1 "google_cloud:" $(DEBUG_CONFIG) | grep "project_id:" | cut -d: -f2 | tr -d ' ')
export BIGQUERY_DATASET := $(shell grep -A5 "bigquery:" $(DEBUG_CONFIG) | grep "dataset_id:" | cut -d: -f2 | tr -d ' ')
export BIGQUERY_TABLE := $(shell grep -A5 "bigquery:" $(DEBUG_CONFIG) | grep "table_name:" | cut -d: -f2 | tr -d ' ')

.PHONY: help run-workflow list-workflows debug-workflow create-workflow validate-workflow setup clean

# Default target
help:
	@echo "$(CYAN)🚀 LangSwarm Interactive Workflow Commands$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "$(GREEN)Available Commands:$(NC)"
	@echo "  $(YELLOW)run-workflow$(NC)      🎯 Interactively select and run a workflow"
	@echo "  $(YELLOW)list-workflows$(NC)    📋 List all available workflows"
	@echo "  $(YELLOW)debug-workflow$(NC)    🐛 Run workflow with debug tracing enabled"
	@echo "  $(YELLOW)create-workflow$(NC)   ✨ Generate a new workflow from description"
	@echo "  $(YELLOW)validate-workflow$(NC) ✅ Validate workflow configuration"
	@echo "  $(YELLOW)setup$(NC)             🔧 Setup environment and API keys"
	@echo "  $(YELLOW)clean$(NC)             🧹 Clean debug traces and temporary files"
	@echo "  $(YELLOW)demo$(NC)              🎬 Run interactive system demo"
	@echo "  $(YELLOW)stats$(NC)             📊 Show workflow discovery statistics"
	@echo "  $(YELLOW)check-env$(NC)         🔍 Check environment variables (.env file)"
	@echo ""
	@echo "$(BLUE)Quick Examples:$(NC)"
	@echo "  make run-workflow      # Interactive workflow selection"
	@echo "  make debug-workflow    # Run with debugging enabled"
	@echo "  make create-workflow   # AI-powered workflow generation"
	@echo ""

# Interactive workflow runner
run-workflow:
	@echo "$(CYAN)🎯 LangSwarm Interactive Workflow Runner$(NC)"
	@echo "============================================"
	@$(PYTHON) scripts/interactive_workflow_runner.py

# List available workflows
list-workflows:
	@echo "$(CYAN)📋 Available Workflows$(NC)"
	@echo "========================"
	@$(PYTHON) scripts/interactive_workflow_runner.py --list-only

# Debug workflow with tracing
debug-workflow:
	@echo "$(CYAN)🐛 Debug Workflow Runner$(NC)"
	@echo "============================"
	@$(PYTHON) scripts/interactive_workflow_runner.py --debug

# Create new workflow
create-workflow:
	@echo "$(CYAN)✨ AI-Powered Workflow Creator$(NC)"
	@echo "=================================="
	@$(PYTHON) scripts/interactive_workflow_runner.py --create

# Validate workflow configuration
validate-workflow:
	@echo "$(CYAN)✅ Workflow Validator$(NC)"
	@echo "========================"
	@$(PYTHON) -m langswarm.cli.validate --interactive

# Setup environment
setup:
	@echo "$(CYAN)🔧 LangSwarm Environment Setup$(NC)"
	@echo "=================================="
	@echo "$(YELLOW)Installing python-dotenv for .env file support...$(NC)"
	@pip install python-dotenv
	@echo "$(YELLOW)Setting up Python environment...$(NC)"
	@pip install -e .
	@echo "$(GREEN)✅ Installation complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking API key setup...$(NC)"
	@$(PYTHON) setup_api_key.py
	@echo ""
	@echo "$(GREEN)🎉 Setup complete! Run 'make run-workflow' to get started.$(NC)"

# Clean debug traces and temporary files
clean:
	@echo "$(CYAN)🧹 Cleaning Debug Traces$(NC)"
	@echo "============================"
	@rm -f debug_traces/*.jsonl
	@rm -f *.jsonl
	@rm -f langswarm_debug.jsonl
	@rm -f test_debug.jsonl
	@echo "$(GREEN)✅ Debug traces cleaned!$(NC)"

# Advanced debugging commands
debug-cases:
	@echo "$(CYAN)🧪 Running Debug Test Cases$(NC)"
	@echo "==============================="
	@./run_debug_tests.sh

# Navigation analytics
nav-analytics:
	@echo "$(CYAN)📊 Navigation Analytics$(NC)"
	@echo "=========================="
	@$(PYTHON) -m langswarm.features.intelligent_navigation.cli analytics

# Memory analytics
memory-stats:
	@echo "$(CYAN)🧠 Memory System Analytics$(NC)"
	@echo "=============================="
	@$(PYTHON) -c "from langswarm.memory.analytics import show_memory_stats; show_memory_stats()"

# Install development dependencies
dev-setup: setup
	@echo "$(CYAN)🛠️  Installing Development Dependencies$(NC)"
	@echo "============================================="
	@pip install -r requirements.txt
	@pip install pytest pytest-asyncio
	@echo "$(GREEN)✅ Development setup complete!$(NC)"

# Run tests
test:
	@echo "$(CYAN)🧪 Running Tests$(NC)"
	@echo "==================="
	@pytest tests/ -v

# Quick workflow shortcuts
workflow-bigquery:
	@echo "$(CYAN)📊 Running BigQuery Workflow$(NC)"
	@$(PYTHON) scripts/interactive_workflow_runner.py --preset bigquery

workflow-filesystem:
	@echo "$(CYAN)📁 Running Filesystem Workflow$(NC)"
	@$(PYTHON) scripts/interactive_workflow_runner.py --preset filesystem

workflow-memory:
	@echo "$(CYAN)🧠 Running Memory Demo Workflow$(NC)"
	@$(PYTHON) scripts/interactive_workflow_runner.py --preset memory

# Demo and showcase
demo:
	@echo "$(CYAN)🎬 Interactive Workflow System Demo$(NC)"
	@$(PYTHON) demo_interactive_workflows.py

# Show workflow statistics
stats:
	@echo "$(CYAN)📊 Workflow Discovery Statistics$(NC)"
	@$(PYTHON) scripts/interactive_workflow_runner.py --list-only | grep "Found.*workflows" || echo "Run 'make list-workflows' for detailed statistics"

# Check environment variables
check-env:
	@echo "$(CYAN)🔍 Environment Variables from debug_config.yaml$(NC)"
	@echo "================================================"
	@echo "$(YELLOW)GOOGLE_CLOUD_PROJECT:$(NC) $(GOOGLE_CLOUD_PROJECT)"
	@echo "$(YELLOW)BIGQUERY_DATASET:$(NC) $(BIGQUERY_DATASET)"
	@echo "$(YELLOW)BIGQUERY_TABLE:$(NC) $(BIGQUERY_TABLE)"
	@echo ""
	@echo "$(CYAN)🔍 Full Environment Check$(NC)"
	@echo "=============================="
	@$(PYTHON) scripts/check_env.py
