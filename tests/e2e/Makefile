# LangSwarm E2E Testing Makefile

.PHONY: help setup quick-setup test test-basic test-orchestration test-memory test-integration clean check-deps install-deps

# Default target
help:
	@echo "🚀 LangSwarm E2E Testing Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make interactive-setup - Interactive setup with prompts (Recommended)"
	@echo "  make setup          - Full comprehensive setup"
	@echo "  make quick-setup    - Quick minimal setup"
	@echo "  make install-deps   - Install Python dependencies"
	@echo "  make check-deps     - Check dependencies"
	@echo ""
	@echo "Test Commands:"
	@echo "  make test           - Run all E2E tests"
	@echo "  make test-basic     - Run basic tests only"
	@echo "  make test-orchestration - Run orchestration tests"
	@echo "  make test-memory    - Run memory backend tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-dry-run   - Show what tests would run"
	@echo ""
	@echo "Analysis Commands:"
	@echo "  make show-results   - Show latest test results"
	@echo "  make show-artifacts - Show test artifacts"
	@echo "  make monitor        - Show system monitoring data"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make clean          - Clean test artifacts"
	@echo "  make clean-all      - Clean everything including configs"
	@echo ""
	@echo "Configuration:"
	@echo "  MAX_COST=1.0        - Set maximum cost per test"
	@echo "  PARALLEL=true       - Run tests in parallel"
	@echo "  PROVIDERS=openai    - Filter by providers"

# Configuration variables
MAX_COST ?= 1.0
PARALLEL ?= true
PROVIDERS ?= 
CATEGORY ?=

# Setup targets
setup:
	@echo "🔧 Running comprehensive E2E setup..."
	python3 setup_e2e_environment.py

quick-setup:
	@echo "⚡ Running quick E2E setup..."
	./quick_setup.sh

interactive-setup:
	@echo "🎯 Running interactive E2E setup..."
	python3 interactive_setup.py

install-deps:
	@echo "📦 Installing Python dependencies..."
	pip3 install --upgrade pip
	pip3 install psutil redis openai anthropic google-cloud-bigquery chromadb langswarm

check-deps:
	@echo "🔍 Checking dependencies..."
	@python3 -c "import psutil, redis, openai, anthropic; print('✅ Core dependencies available')" || echo "❌ Missing core dependencies"
	@python3 -c "import chromadb; print('✅ ChromaDB available')" || echo "⚠️  ChromaDB not available"
	@python3 -c "from google.cloud import bigquery; print('✅ BigQuery available')" || echo "⚠️  BigQuery not available"
	@which gcloud > /dev/null && echo "✅ gcloud CLI available" || echo "⚠️  gcloud CLI not available"
	@which redis-cli > /dev/null && echo "✅ Redis CLI available" || echo "⚠️  Redis CLI not available"

# Test execution targets
test:
	@echo "🧪 Running all E2E tests..."
	python3 runner.py \
		$(if $(MAX_COST),--max-cost $(MAX_COST)) \
		$(if $(PROVIDERS),--providers $(PROVIDERS)) \
		$(if $(CATEGORY),--category $(CATEGORY)) \
		$(if $(filter true,$(PARALLEL)),,--sequential)

test-basic:
	@echo "🧪 Running basic E2E tests (low cost)..."
	python3 runner.py --max-cost 0.10 --category basic

test-orchestration:
	@echo "🧪 Running orchestration tests..."
	python3 runner.py --category orchestration

test-memory:
	@echo "🧪 Running memory backend tests..."
	python3 runner.py --category memory

test-integration:
	@echo "🧪 Running integration tests..."
	python3 runner.py --category integration

test-dry-run:
	@echo "🔍 Showing what tests would run..."
	python3 runner.py --dry-run \
		$(if $(MAX_COST),--max-cost $(MAX_COST)) \
		$(if $(PROVIDERS),--providers $(PROVIDERS)) \
		$(if $(CATEGORY),--category $(CATEGORY))

# Single test execution
test-sqlite:
	python3 runner.py --test-name "SQLite Memory Backend"

test-openai:
	python3 runner.py --providers openai --max-cost 0.05

test-bigquery:
	python3 runner.py --test-name "BigQuery Cloud Memory"

# Analysis targets
show-results:
	@echo "📊 Latest test results:"
	@if [ -f "results/latest_run.json" ]; then \
		python3 -c "import json; data=json.load(open('results/latest_run.json')); print(f\"Tests: {data['summary']['total']}, Passed: {data['summary']['passed']}, Failed: {data['summary']['failed']}, Cost: \$${data['performance']['total_cost_usd']:.3f}\")"; \
	else \
		echo "No test results found. Run 'make test' first."; \
	fi

show-artifacts:
	@echo "📁 Test artifacts:"
	@find ../test_artifacts -name "*.json" -exec basename {} \; 2>/dev/null | head -10 || echo "No artifacts found"

monitor:
	@echo "📈 System monitoring data:"
	@if [ -f "debug/e2e_test_history.db" ]; then \
		echo "Database exists - check debug/monitor.py for analysis tools"; \
	else \
		echo "No monitoring data found"; \
	fi

# Cleanup targets
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf ../test_artifacts/*
	rm -rf results/*.json
	rm -rf artifacts/*.log

clean-all: clean
	@echo "🧹 Cleaning all test data..."
	rm -rf config/test_config.json
	rm -rf credentials/*.json
	rm -rf debug/e2e_test_history.db

# Development targets
dev-test:
	@echo "🔧 Running development test (single basic test)..."
	python3 runner.py --test-name "SQLite Memory Backend" --debug

validate-framework:
	@echo "🔍 Validating E2E framework..."
	python3 -c "from framework.base import BaseE2ETest, TestEnvironment; print('✅ Framework imports successful')"
	python3 -c "from tests.memory_tests import SQLiteMemoryTest; print('✅ Test imports successful')"

# Docker targets (optional)
docker-redis:
	@echo "🐳 Starting Redis in Docker..."
	docker run -d --name langswarm-redis -p 6379:6379 redis:alpine

docker-stop:
	@echo "🐳 Stopping Docker containers..."
	docker stop langswarm-redis || true
	docker rm langswarm-redis || true

# Environment targets
env-check:
	@echo "🔍 Environment check:"
	@echo "OPENAI_API_KEY: $(if $(OPENAI_API_KEY),✅ Set,❌ Not set)"
	@echo "ANTHROPIC_API_KEY: $(if $(ANTHROPIC_API_KEY),✅ Set,❌ Not set)"
	@echo "GOOGLE_APPLICATION_CREDENTIALS: $(if $(GOOGLE_APPLICATION_CREDENTIALS),✅ Set,❌ Not set)"
	@echo "GCP_PROJECT: $(if $(GCP_PROJECT),✅ Set,❌ Not set)"
	@echo "REDIS_URL: $(if $(REDIS_URL),$(REDIS_URL),redis://localhost:6379 (default))"

env-template:
	@echo "📝 Creating .env template..."
	@if [ ! -f "../../.env.template" ]; then \
		cp ../quick_setup.sh temp_setup.sh; \
		sed -n '/^cat > \.env\.template/,/^EOF/p' temp_setup.sh | sed '1d;$$d' > ../../.env.template; \
		rm temp_setup.sh; \
		echo "Created .env.template in project root"; \
	else \
		echo ".env.template already exists"; \
	fi

# CI/CD targets
ci-setup:
	make install-deps
	python3 setup_e2e_environment.py --skip-gcp

ci-test:
	make test-basic MAX_COST=0.05