# LangSwarm Debug System Makefile
# Clean interface for debugging different LangSwarm scenarios

.PHONY: help setup check-env debug-v2 debug-v2-registry debug-v2-openai-provider debug-v2-analytics debug-v2-bigquery-tool debug-v2-sql-tool debug-bigquery-knowledge-search debug-bigquery-workflow-integration debug-bigquery-legacy-debug debug-sql-data-analysis debug-sql-workflow-integration debug-sql-performance debug-bigquery debug-bigquery-benchmark clean list-scenarios

# Default target - comprehensive help
help:
	@echo "🚀 LangSwarm Debug System"
	@echo "========================="
	@echo ""
	@echo "Available scenarios:"
	@echo "  v2-system-test          Comprehensive V2 system test (all providers & tools)"
	@echo ""
	@echo "Individual V2 Component Tests:"
	@echo "  v2-registry             V2 tool registry auto-discovery test"
	@echo "  v2-openai-provider      V2 OpenAI provider and tool integration test"
	@echo "  v2-analytics            V2 analytics and monitoring system test"
	@echo "  v2-bigquery-tool        V2 BigQuery tool specific test"
	@echo "  v2-sql-tool             V2 SQL database tool specific test"
	@echo ""
	@echo "Individual BigQuery Tests:"
	@echo "  bigquery-knowledge-search      BigQuery knowledge base search test"
	@echo "  bigquery-workflow-integration  BigQuery LangSwarm workflow integration test"
	@echo "  bigquery-legacy-debug          BigQuery comprehensive legacy debug test"
	@echo ""
	@echo "Individual SQL Tests:"
	@echo "  sql-data-analysis               SQL data analysis and operations test"
	@echo "  sql-workflow-integration        SQL LangSwarm workflow integration test"
	@echo "  sql-performance                 SQL performance and optimization test"
	@echo ""
	@echo "Legacy Scenarios:"
	@echo "  bigquery-vector-search   Legacy BigQuery vector similarity search (replaced by individual tests)"
	@echo "  sql-database            Legacy SQL database tool (replaced by individual tests)"
	@echo "  workflows               Debug workflow execution (coming soon)"
	@echo "  agents                  Debug agent behavior (coming soon)"
	@echo "  tools                   Debug tool integration (coming soon)"
	@echo "  memory                  Debug memory systems (coming soon)"
	@echo ""
	@echo "Quick commands:"
	@echo "  make setup              Set up credentials and environment"
	@echo "  make check-env          Check environment variables and credentials"
	@echo "  make debug-v2           Comprehensive V2 system test"
	@echo "  make debug-bigquery     Debug BigQuery vector search"
	@echo "  make debug-bigquery-workflow  Debug BigQuery workflow integration"
	@echo "  make debug-sql          Debug SQL database tool"
	@echo "  make debug-sql-workflow Debug SQL database workflow integration"
	@echo "  make list-scenarios     List all available debug scenarios"
	@echo "  make clean              Clean up debug traces and temporary files"
	@echo ""
	@echo "Options:"
	@echo "  QUERY='your query'      Custom search query (for applicable scenarios)"
	@echo "  VERBOSE=1               Enable verbose output"
	@echo "  DRY_RUN=1               Show what would be done without executing"
	@echo ""
	@echo "Examples:"
	@echo "  make debug-bigquery"
	@echo "  make debug-bigquery QUERY='AI workflows'"
	@echo "  make debug-bigquery-knowledge-search"
	@echo "  make debug-bigquery-knowledge-search QUERY='What are the main features?'"
	@echo "  make debug-sql-workflow-integration QUERY='Show me all employees'"
	@echo ""
	@echo "Getting started:"
	@echo "  make setup              # First time setup"
	@echo "  make check-env          # Validate your setup"
	@echo "  make debug-bigquery     # Start debugging!"
	@echo ""
	@echo "For more help:"
	@echo "  make help-setup         # Detailed setup instructions"
	@echo "  make help-bigquery      # BigQuery debugging help"
	@echo "  make help-troubleshoot  # Troubleshooting guide"

# Variables
QUERY ?= Pingday_network_services
VERBOSE ?= 0
DRY_RUN ?= 0
PROJECT_ROOT := $(shell pwd)/..
DEBUG_ROOT := $(shell pwd)
ENV_FILE := $(DEBUG_ROOT)/.env

# Color codes
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

# Helper function to check if command exists
define check_command
	@which $(1) > /dev/null || (echo "$(RED)❌ $(1) not found. Please install $(1).$(NC)" && exit 1)
endef

# Helper function to check environment variable
define check_env_var
	@if [ -z "$($(1))" ]; then \
		echo "$(RED)❌ $(1) not set$(NC)"; \
		echo "$(YELLOW)💡 Set it with: export $(1)=your_value$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✅ $(1) is set$(NC)"; \
	fi
endef

# Setup credentials and environment
setup:
	@echo "$(CYAN)🔧 Setting up LangSwarm debug environment$(NC)"
	@echo "==========================================="
	
	# Check if .env file exists in debug folder
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(YELLOW)📝 Creating .env file in debug folder...$(NC)"; \
		cp $(DEBUG_ROOT)/credentials_template.env $(ENV_FILE); \
		echo "$(CYAN)Please edit $(ENV_FILE) with your real credentials$(NC)"; \
		echo "$(YELLOW)Required:$(NC)"; \
		echo "  - OPENAI_API_KEY"; \
		echo "  - GOOGLE_CLOUD_PROJECT"; \
		echo "  - BIGQUERY_DATASET_ID"; \
		echo "  - BIGQUERY_TABLE_NAME"; \
	else \
		echo "$(GREEN)✅ .env file already exists$(NC)"; \
	fi
	
	# Create debug directories
	@mkdir -p debug_traces
	@mkdir -p debug_traces/bigquery
	@mkdir -p debug_traces/workflows
	@mkdir -p debug_traces/agents
	@echo "$(GREEN)✅ Debug directories created$(NC)"
	
	# Check Python dependencies
	@echo "$(CYAN)🐍 Checking Python dependencies...$(NC)"
	@python3 -c "import google.cloud.bigquery, openai, yaml" 2>/dev/null || \
		(echo "$(YELLOW)⚠️  Some Python dependencies missing$(NC)" && \
		 echo "$(CYAN)Install with: pip install google-cloud-bigquery openai pyyaml$(NC)")

# Check environment variables and credentials
check-env:
	@echo "$(CYAN)🔍 Checking Environment & Credentials$(NC)"
	@echo "========================================="
	
	# Load .env if it exists in debug folder
	@if [ -f "$(ENV_FILE)" ]; then \
		echo "$(GREEN)✅ Loading .env file$(NC)"; \
		export $$(cat $(ENV_FILE) | grep -v '^#' | xargs); \
	else \
		echo "$(YELLOW)⚠️  No .env file found$(NC)"; \
	fi
	
	# Check required tools
	@echo "$(CYAN)🛠️  Checking required tools:$(NC)"
	$(call check_command,python3)
	$(call check_command,gcloud)
	@echo "$(GREEN)✅ All required tools found$(NC)"
	
	# Check authentication
	@echo "$(CYAN)🔐 Checking authentication:$(NC)"
	@gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 | \
		(read account; if [ -n "$$account" ]; then \
			echo "$(GREEN)✅ Google Cloud authenticated as: $$account$(NC)"; \
		else \
			echo "$(YELLOW)⚠️  Google Cloud not authenticated$(NC)"; \
			echo "$(CYAN)Run: gcloud auth application-default login$(NC)"; \
		fi)
	
	# Test BigQuery access if project is set
	@if [ -n "$$GOOGLE_CLOUD_PROJECT" ]; then \
		echo "$(CYAN)🗄️  Testing BigQuery access...$(NC)"; \
		bq ls --project_id=$$GOOGLE_CLOUD_PROJECT >/dev/null 2>&1 && \
			echo "$(GREEN)✅ BigQuery access confirmed$(NC)" || \
			echo "$(YELLOW)⚠️  BigQuery access failed$(NC)"; \
	fi

# List all available debug scenarios
list-scenarios:
	@echo "$(CYAN)📋 Available Debug Scenarios$(NC)"
	@echo "================================"
	@echo ""
	@for dir in $(shell find $(DEBUG_ROOT) -maxdepth 1 -type d ! -name "debug" ! -name ".*"); do \
		scenario=$$(basename $$dir); \
		if [ -f "$$dir/README.md" ]; then \
			description=$$(head -3 "$$dir/README.md" | tail -1); \
			echo "$(GREEN)📁 $$scenario$(NC)"; \
			echo "   $$description"; \
			echo ""; \
		fi; \
	done

# V2 System Comprehensive Test
debug-v2:
	@echo "$(CYAN)🚀 LangSwarm V2 System Comprehensive Test$(NC)"
	@echo "===========================================" 
	@echo "Testing all providers, tools, and monitoring"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute V2 system test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 tools/scenario_v2_system_test.py; \
	fi

# V2 Individual Component Tests
debug-v2-registry:
	@echo "$(CYAN)🛠️ V2 Tool Registry Test$(NC)"
	@echo "=========================="
	@echo "Testing auto-discovery and tool registration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute V2 registry test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/v2_registry_test.py; \
	fi

debug-v2-openai-provider:
	@echo "$(CYAN)🤖 V2 OpenAI Provider Test$(NC)"
	@echo "============================"
	@echo "Testing OpenAI provider and tool integration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute OpenAI provider test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/v2_openai_provider_test.py; \
	fi

debug-v2-analytics:
	@echo "$(CYAN)📊 V2 Analytics System Test$(NC)"
	@echo "============================"
	@echo "Testing analytics and monitoring system"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute analytics test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/v2_analytics_test.py; \
	fi

debug-v2-bigquery-tool:
	@echo "$(CYAN)🗄️ V2 BigQuery Tool Test$(NC)"
	@echo "=========================="
	@echo "Testing BigQuery tool integration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery tool test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/v2_bigquery_tool_test.py; \
	fi

debug-v2-sql-tool:
	@echo "$(CYAN)📊 V2 SQL Database Tool Test$(NC)"
	@echo "============================="
	@echo "Testing SQL database tool integration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL tool test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/v2_sql_tool_test.py; \
	fi

# Individual BigQuery Tests
debug-bigquery-knowledge-search: check-bigquery-env
	@echo "$(CYAN)🔍 BigQuery Knowledge Search Test$(NC)"
	@echo "=================================="
	@echo "Testing BigQuery knowledge base search functionality"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery knowledge search test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && $(if $(QUERY),QUERY='$(QUERY)',) python3 scenarios/bigquery_knowledge_search_test.py; \
	fi

debug-bigquery-workflow-integration: check-bigquery-env
	@echo "$(CYAN)🧠 BigQuery Workflow Integration Test$(NC)"
	@echo "======================================="
	@echo "Testing BigQuery LangSwarm workflow system integration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery workflow integration test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && $(if $(QUERY),QUERY='$(QUERY)',) python3 scenarios/bigquery_workflow_integration_test.py; \
	fi

debug-bigquery-legacy-debug: check-bigquery-env
	@echo "$(CYAN)🧪 BigQuery Legacy Debug Test$(NC)"
	@echo "==============================="
	@echo "Testing comprehensive BigQuery legacy debug system (1074 lines)"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery legacy debug test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/bigquery_legacy_debug_test.py; \
	fi

# Individual SQL Tests
debug-sql-data-analysis:
	@echo "$(CYAN)📊 SQL Data Analysis Test$(NC)"
	@echo "=========================="
	@echo "Testing SQL database operations and data analysis"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL data analysis test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/sql_data_analysis_test.py; \
	fi

debug-sql-workflow-integration:
	@echo "$(CYAN)🧠 SQL Workflow Integration Test$(NC)"
	@echo "================================="
	@echo "Testing SQL LangSwarm workflow system integration"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL workflow integration test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && $(if $(QUERY),QUERY='$(QUERY)',) python3 scenarios/sql_workflow_integration_test.py; \
	fi

debug-sql-performance:
	@echo "$(CYAN)⚡ SQL Performance Test$(NC)"
	@echo "======================="
	@echo "Testing SQL database performance and optimization"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL performance test$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 scenarios/sql_performance_test.py; \
	fi

# BigQuery Vector Search Debug (V2 Automatic Tool Injection)
debug-bigquery: check-bigquery-env
	@echo "$(CYAN)🔍 BigQuery Knowledge Search Scenario$(NC)"
	@echo "====================================="
	@echo "Query: $(QUERY)"
	@echo ""

# BigQuery LangSwarm Workflow Integration Debug
debug-bigquery-workflow: check-bigquery-env
	@echo "$(CYAN)🧠 BigQuery LangSwarm Workflow Integration$(NC)"
	@echo "============================================"
	@echo "Testing real workflow system vs BS intent processing"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery scenario debug$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 tools/scenario_bigquery_knowledge_search.py; \
	fi
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery workflow integration debug$(NC)"; \
	else \
		cd $(DEBUG_ROOT) && python3 tools/scenario_bigquery_workflow_integration.py; \
	fi

# Intent-only debugging has been integrated into main scenarios

# BigQuery Vector Search Debug (Legacy)
debug-bigquery-legacy: check-bigquery-env
	@echo "$(CYAN)🗄️  BigQuery Legacy Debug (1074 lines)$(NC)"
	@echo "=============================================="
	@echo "Query: $(QUERY)"
	@echo "Verbose: $(VERBOSE)"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute legacy BigQuery debug with query: $(QUERY)$(NC)"; \
	else \
		cd $(DEBUG_ROOT)/bigquery_vector_search && \
		python3 debug_bigquery.py --query "$(QUERY)" $(if $(filter 1,$(VERBOSE)),--verbose,); \
	fi

# BigQuery benchmark
debug-bigquery-benchmark: check-bigquery-env
	@echo "$(CYAN)⚡ Starting BigQuery Performance Benchmark$(NC)"
	@echo "=============================================="
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute BigQuery benchmark$(NC)"; \
	else \
		cd $(DEBUG_ROOT)/bigquery_vector_search && \
		python3 debug_bigquery.py --benchmark $(if $(filter 1,$(VERBOSE)),--verbose,); \
	fi

# SQL Database Debug
debug-sql:
	@echo "$(CYAN)📊 SQL Data Analysis Scenario$(NC)"
	@echo "=============================="
	@echo ""

# SQL Database LangSwarm Workflow Integration Debug
debug-sql-workflow:
	@echo "$(CYAN)🧠 SQL Database LangSwarm Workflow Integration$(NC)"
	@echo "==============================================="
	@echo "Testing real workflow system vs BS intent processing"
	@echo ""
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL scenario debug$(NC)"; \
	else \
		echo "$(CYAN)Creating temporary SQLite database with test data...$(NC)"; \
		echo "$(CYAN)Scenario: User analyzing customer data with SQL queries$(NC)"; \
		echo ""; \
		cd $(DEBUG_ROOT) && python3 tools/scenario_sql_data_analysis.py; \
	fi
	
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "$(YELLOW)🏃 DRY RUN: Would execute SQL workflow integration debug$(NC)"; \
	else \
		echo "$(CYAN)Testing SQL Database LangSwarm workflow integration...$(NC)"; \
		echo ""; \
		cd $(DEBUG_ROOT) && python3 tools/scenario_sql_workflow_integration.py; \
	fi

# SQL Database Intent debugging integrated into main scenario

# Check BigQuery-specific environment
check-bigquery-env:
	@echo "$(CYAN)🔍 Checking BigQuery Environment$(NC)"
	@if [ -f "$(ENV_FILE)" ]; then \
		set -a; source $(ENV_FILE); set +a; \
	fi; \
	\
	required_vars="GOOGLE_CLOUD_PROJECT BIGQUERY_DATASET_ID BIGQUERY_TABLE_NAME EMBEDDING_MODEL OPENAI_API_KEY"; \
	all_set=true; \
	for var in $$required_vars; do \
		eval value=\$$$$var; \
		if [ -z "$$value" ]; then \
			echo "$(RED)❌ $$var not set$(NC)"; \
			all_set=false; \
		else \
			if echo "$$var" | grep -q "API_KEY"; then \
				masked=$$(echo "$$value" | sed 's/\(.\{8\}\).*/\1.../'); \
				echo "$(GREEN)✅ $$var: $$masked$(NC)"; \
			else \
				echo "$(GREEN)✅ $$var: $$value$(NC)"; \
			fi; \
		fi; \
	done; \
	\
	if [ "$$all_set" = "false" ]; then \
		echo "$(RED)❌ Missing required environment variables$(NC)"; \
		echo "$(CYAN)Run: make setup$(NC)"; \
		exit 1; \
	fi

# Workflow debug (placeholder)
debug-workflows:
	@echo "$(YELLOW)🚧 Workflow debugging coming soon!$(NC)"
	@echo "This will debug workflow execution with real LLM calls."

# Agent debug (placeholder)
debug-agents:
	@echo "$(YELLOW)🚧 Agent debugging coming soon!$(NC)"
	@echo "This will debug agent behavior and responses."

# Tool debug (placeholder)
debug-tools:
	@echo "$(YELLOW)🚧 Tool debugging coming soon!$(NC)"
	@echo "This will debug tool integration and execution."

# Memory debug (placeholder)
debug-memory:
	@echo "$(YELLOW)🚧 Memory debugging coming soon!$(NC)"
	@echo "This will debug memory systems and persistence."

# Clean up debug files
clean:
	@echo "$(CYAN)🧹 Cleaning up debug files$(NC)"
	@echo "============================="
	
	@if [ -d "debug_traces" ]; then \
		echo "$(YELLOW)Removing debug_traces/$(NC)"; \
		rm -rf debug_traces/*; \
		echo "$(GREEN)✅ Debug traces cleaned$(NC)"; \
	else \
		echo "$(GREEN)✅ No debug traces to clean$(NC)"; \
	fi
	
	@find $(DEBUG_ROOT) -name "*.pyc" -delete 2>/dev/null || true
	@find $(DEBUG_ROOT) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Python cache files cleaned$(NC)"

# Show current status
status:
	@echo "$(CYAN)📊 Debug System Status$(NC)"
	@echo "========================="
	@echo ""
	@echo "Project Root: $(PROJECT_ROOT)"
	@echo "Debug Root: $(DEBUG_ROOT)"
	@echo ""
	@echo "Available scenarios:"
	@for dir in $(shell find $(DEBUG_ROOT) -maxdepth 1 -type d ! -name "debug" ! -name ".*"); do \
		scenario=$$(basename $$dir); \
		if [ -f "$$dir/debug_*.py" ] || [ -f "$$dir/config.yaml" ]; then \
			echo "  $(GREEN)✅ $$scenario$(NC)"; \
		else \
			echo "  $(YELLOW)🚧 $$scenario (in development)$(NC)"; \
		fi; \
	done
	@echo ""
	@if [ -f "$(ENV_FILE)" ]; then \
		echo "$(GREEN)✅ Credentials: .env file exists$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Credentials: .env file missing$(NC)"; \
	fi
	@echo ""
	@if [ -d "debug_traces" ] && [ "$$(ls -A debug_traces 2>/dev/null)" ]; then \
		trace_count=$$(find debug_traces -name "*.json" | wc -l); \
		echo "Debug traces: $$trace_count files"; \
	else \
		echo "Debug traces: none"; \
	fi

# Advanced: Run all scenarios
debug-all: debug-bigquery
	@echo "$(GREEN)🎉 All available debug scenarios completed$(NC)"

# Detailed help targets
help-setup:
	@echo "$(CYAN)🔧 Setup Instructions$(NC)"
	@echo "======================"
	@echo ""
	@echo "$(YELLOW)1. Initial Setup$(NC)"
	@echo "   make setup                   # Create .env template and directories"
	@echo ""
	@echo "$(YELLOW)2. Configure Credentials$(NC)"
	@echo "   Edit .env with your real API keys:"
	@echo "   - OPENAI_API_KEY=sk-your-openai-key"
	@echo "   - GOOGLE_CLOUD_PROJECT=your-project"
	@echo "   - BIGQUERY_DATASET_ID=your-dataset"
	@echo "   - BIGQUERY_TABLE_NAME=your-table"
	@echo ""
	@echo "$(YELLOW)3. Authenticate Google Cloud$(NC)"
	@echo "   gcloud auth application-default login"
	@echo "   gcloud config set project your-project-id"
	@echo ""
	@echo "$(YELLOW)4. Validate Setup$(NC)"
	@echo "   make check-env               # Verify everything is working"
	@echo ""
	@echo "$(YELLOW)5. Start Debugging$(NC)"
	@echo "   make debug-bigquery          # Run your first debug session"

help-bigquery:
	@echo "$(CYAN)🗄️  BigQuery V2 Debugging Help$(NC)"
	@echo "================================"
	@echo ""
	@echo "$(YELLOW)V2 Automatic Tool Injection (Recommended):$(NC)"
	@echo "   make debug-bigquery                    # V2 agent with auto tool injection"
	@echo ""
	@echo "$(YELLOW)Legacy Debugging (1074 lines):$(NC)"
	@echo "   make debug-bigquery-legacy QUERY='custom'     # Old complex debug script"
	@echo "   make debug-bigquery-benchmark          # Performance testing"
	@echo ""
	@echo "$(YELLOW)What V2 tests:$(NC)"
	@echo "   ✅ Automatic tool injection into agent system prompts"
	@echo "   ✅ V2 agent creation with BigQuery tools"
	@echo "   ✅ Direct V2 tool execution (5-line test)"
	@echo "   ✅ YAML workflow with auto tool discovery"
	@echo "   ✅ Safety filtering (V2 registry tools only)"
	@echo ""
	@echo "$(YELLOW)What legacy tests:$(NC)"
	@echo "   ✅ BigQuery connectivity and authentication"
	@echo "   ✅ Table schema validation and analysis"
	@echo "   ✅ Vector embedding generation (OpenAI)"
	@echo "   ✅ Similarity search performance"
	@echo "   ✅ Query optimization and benchmarking"
	@echo ""
	@echo "$(YELLOW)Required table schema:$(NC)"
	@echo "   CREATE TABLE \`project.dataset.table\` ("
	@echo "     id STRING,"
	@echo "     text STRING,"
	@echo "     embedding ARRAY<FLOAT64>,"
	@echo "     metadata JSON"
	@echo "   )"
	@echo ""
	@echo "$(YELLOW)Options:$(NC)"
	@echo "   QUERY='search text'          # Custom search query"
	@echo "   VERBOSE=1                    # Detailed output"
	@echo "   DRY_RUN=1                    # Show what would run"
	@echo ""
	@echo "$(YELLOW)Output:$(NC)"
	@echo "   - Real-time progress in console"
	@echo "   - Debug traces saved to debug_traces/"
	@echo "   - Performance metrics and analysis"

help-troubleshoot:
	@echo "$(CYAN)🐛 Troubleshooting Guide$(NC)"
	@echo "========================="
	@echo ""
	@echo "$(YELLOW)Common Issues:$(NC)"
	@echo ""
	@echo "$(RED)❌ Authentication failed$(NC)"
	@echo "   → gcloud auth application-default login"
	@echo "   → gcloud config set project your-project-id"
	@echo "   → Check service account permissions"
	@echo ""
	@echo "$(RED)❌ Environment variables missing$(NC)"
	@echo "   → make setup                 # Create .env template"
	@echo "   → Edit .env with real values"
	@echo "   → make check-env            # Validate"
	@echo ""
	@echo "$(RED)❌ BigQuery table not found$(NC)"
	@echo "   → Verify project/dataset/table names in .env"
	@echo "   → Check BigQuery permissions"
	@echo "   → Ensure table has 'embedding' column"
	@echo ""
	@echo "$(RED)❌ OpenAI API errors$(NC)"
	@echo "   → Check API key format (starts with sk-)"
	@echo "   → Verify account has credits"
	@echo "   → Check rate limits"
	@echo ""
	@echo "$(RED)❌ Poor vector search results$(NC)"
	@echo "   → Check embedding dimensions (1536 for text-embedding-3-small)"
	@echo "   → Verify embeddings are not null"
	@echo "   → Review similarity threshold settings"
	@echo ""
	@echo "$(YELLOW)Getting Help:$(NC)"
	@echo "   → Check debug_traces/ for detailed logs"
	@echo "   → Run with VERBOSE=1 for more output"
	@echo "   → Review README.md in scenario folders"

help-all:
	@echo "$(CYAN)📚 Complete Help Index$(NC)"
	@echo "======================="
	@echo ""
	@echo "$(YELLOW)Main Commands:$(NC)"
	@echo "   make help                    # Main help (this is default)"
	@echo "   make setup                   # Initial setup and configuration"
	@echo "   make check-env               # Validate environment"
	@echo "   make status                  # Show system status"
	@echo "   make clean                   # Clean up files"
	@echo ""
	@echo "$(YELLOW)Debug Scenarios:$(NC)"
	@echo "   make debug-bigquery          # BigQuery vector search (all tests)"
	@echo "   make debug-bigquery-benchmark # Performance testing"
	@echo "   make debug-sql               # SQL database tool (all tests)"
	@echo "   make list-scenarios          # List all scenarios"
	@echo ""
	@echo "$(YELLOW)Detailed Help:$(NC)"
	@echo "   make help-setup              # Setup instructions"
	@echo "   make help-bigquery           # BigQuery debugging"
	@echo "   make help-troubleshoot       # Troubleshooting guide"
	@echo "   make help-all                # This complete index"
	@echo ""
	@echo "$(YELLOW)Options Available:$(NC)"
	@echo "   QUERY='text'                 # Custom search query"
	@echo "   VERBOSE=1                    # Enable verbose output"
	@echo "   DRY_RUN=1                    # Show commands without running"
	@echo ""
	@echo "$(YELLOW)Example Workflows:$(NC)"
	@echo "   # First time setup"
	@echo "   make setup && make check-env"
	@echo ""
	@echo "   # Quick BigQuery test"
	@echo "   make debug-bigquery"
	@echo ""
	@echo "   # Custom query with verbose output"
	@echo "   make debug-bigquery QUERY='AI workflows' VERBOSE=1"
	@echo ""
	@echo "   # Performance benchmark"
	@echo "   make debug-bigquery-benchmark"

# Update phony targets
.PHONY: help setup check-env debug-v2 debug-v2-registry debug-v2-openai-provider debug-v2-analytics debug-v2-bigquery-tool debug-v2-sql-tool debug-bigquery-knowledge-search debug-bigquery-workflow-integration debug-bigquery-legacy-debug debug-sql-data-analysis debug-sql-workflow-integration debug-sql-performance debug-bigquery debug-bigquery-benchmark debug-sql clean list-scenarios help-setup help-bigquery help-troubleshoot help-all

# Show help by default
.DEFAULT_GOAL := help
