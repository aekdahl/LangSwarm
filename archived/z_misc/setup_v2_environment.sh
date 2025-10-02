#!/bin/bash

# LangSwarm V2 Environment Setup Script
# This script sets up environment variables for V2 BigQuery configuration testing

echo "🚀 Setting up LangSwarm V2 Environment Variables"
echo "=================================================="

# Core LangSwarm Settings
export LANGSWARM_ENV=development
export LANGSWARM_USE_V2_AGENTS=true
export LANGSWARM_USE_V2_CONFIG=true
export LANGSWARM_USE_V2_TOOLS=true

echo "✅ LangSwarm V2 features enabled"

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set - you'll need to set this for testing"
    echo "   export OPENAI_API_KEY=your_openai_api_key"
else
    echo "✅ OPENAI_API_KEY is set"
fi

# Google Cloud Configuration (using existing values or defaults)
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-production-pingday}
export BIGQUERY_DATASET_ID=${BIGQUERY_DATASET_ID:-vector_search}
export BIGQUERY_TABLE_NAME=${BIGQUERY_TABLE_NAME:-embeddings}
export BIGQUERY_LOCATION=${BIGQUERY_LOCATION:-US}
export GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION:-us-central1}
export VERTEX_AI_LOCATION=${VERTEX_AI_LOCATION:-us-central1}

echo "✅ Google Cloud configuration set:"
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Dataset: $BIGQUERY_DATASET_ID"
echo "   Table: $BIGQUERY_TABLE_NAME"

# Embedding Configuration
export EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-3-small}
export MAX_SEARCH_RESULTS=${MAX_SEARCH_RESULTS:-10}
export SIMILARITY_THRESHOLD=${SIMILARITY_THRESHOLD:-0.01}

echo "✅ Embedding configuration set:"
echo "   Model: $EMBEDDING_MODEL"
echo "   Max Results: $MAX_SEARCH_RESULTS"

# Logging Configuration
export LOG_LEVEL=${LOG_LEVEL:-DEBUG}
export LOG_OUTPUT_DIR=${LOG_OUTPUT_DIR:-debug_traces/v2}
export TRACE_OUTPUT_DIR=${TRACE_OUTPUT_DIR:-debug_traces/v2/traces}
export TRACE_SAMPLE_RATE=${TRACE_SAMPLE_RATE:-1.0}

echo "✅ Logging configuration set:"
echo "   Level: $LOG_LEVEL"
echo "   Output: $LOG_OUTPUT_DIR"

# Database Configuration
export SQLITE_PATH=${SQLITE_PATH:-./debug.db}

echo "✅ Database configuration set"

# Create output directories
mkdir -p debug_traces/v2/{traces,metrics,profiles,tests,migration}
echo "✅ Output directories created"

echo ""
echo "🎯 Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set your OpenAI API key: export OPENAI_API_KEY=your_key"
echo "2. Configure Google Cloud auth: gcloud auth application-default login"
echo "3. Test V2 configs: python test_v2_configs_simple.py"
echo "4. Run BigQuery demo: python demo_v2_bigquery_config.py"
echo ""
echo "🔧 Current environment variables:"
env | grep -E "(LANGSWARM|OPENAI|GOOGLE|BIGQUERY|EMBEDDING|LOG_)" | sort
