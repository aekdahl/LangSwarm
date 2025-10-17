#!/bin/bash
set -e

# LangSwarm E2E Quick Setup Script
# Minimal setup for running E2E tests

echo "🚀 LangSwarm E2E Quick Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "tests/e2e/setup_e2e_environment.py" ]; then
    print_error "Please run this script from the LangSwarm root directory"
    exit 1
fi

# Create necessary directories
print_status "Creating test directories..."
mkdir -p tests/e2e/config
mkdir -p tests/e2e/credentials
mkdir -p tests/e2e/results
mkdir -p tests/e2e/artifacts
mkdir -p test_artifacts

# Make setup script executable
chmod +x tests/e2e/setup_e2e_environment.py

# Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    print_success "Python $PYTHON_VERSION is compatible"
else
    print_error "Python 3.8+ is required, found $PYTHON_VERSION"
    exit 1
fi

# Install basic Python dependencies
print_status "Installing basic Python dependencies..."
pip3 install --quiet --upgrade pip
pip3 install --quiet psutil redis openai anthropic google-cloud-bigquery chromadb

# Check for gcloud CLI
print_status "Checking Google Cloud CLI..."
if command -v gcloud &> /dev/null; then
    print_success "gcloud CLI found"
    
    # Check if authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 | grep -q "@"; then
        print_success "gcloud is authenticated"
        
        # Get current project
        PROJECT=$(gcloud config get-value project 2>/dev/null)
        if [ -n "$PROJECT" ] && [ "$PROJECT" != "(unset)" ]; then
            print_success "Current GCP project: $PROJECT"
        else
            print_warning "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
        fi
    else
        print_warning "gcloud not authenticated. Run: gcloud auth login"
    fi
else
    print_warning "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
fi

# Check for Redis
print_status "Checking Redis availability..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis CLI found but server not responding"
        print_status "Start Redis with: redis-server"
    fi
else
    print_warning "Redis not found. Install with:"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt install redis-server"
    echo "  Docker: docker run -d -p 6379:6379 redis:alpine"
fi

# Check API keys
print_status "Checking for API keys..."
API_KEYS_FOUND=0

if [ -n "$OPENAI_API_KEY" ]; then
    print_success "OpenAI API key found"
    ((API_KEYS_FOUND++))
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    print_success "Anthropic API key found"
    ((API_KEYS_FOUND++))
fi

if [ -n "$GOOGLE_API_KEY" ]; then
    print_success "Google API key found"
    ((API_KEYS_FOUND++))
fi

if [ $API_KEYS_FOUND -eq 0 ]; then
    print_warning "No API keys found in environment"
    echo "Set API keys as environment variables:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
else
    print_success "$API_KEYS_FOUND API key(s) found"
fi

# Create .env template if it doesn't exist
if [ ! -f ".env" ] && [ ! -f ".env.template" ]; then
    print_status "Creating .env template..."
    cat > .env.template << 'EOF'
# LangSwarm E2E Test Environment Variables
# Copy this to .env and fill in your actual API keys

# Required AI Provider API Keys (at least one needed)
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional AI Provider API Keys
GOOGLE_API_KEY=your-google-api-key-here
COHERE_API_KEY=your-cohere-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here

# Google Cloud Platform (for BigQuery tests)
GOOGLE_APPLICATION_CREDENTIALS=tests/e2e/credentials/gcp-service-account.json
GCP_PROJECT=your-gcp-project-id

# Database URLs
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/langswarm_test

# Optional: AWS
AWS_DEFAULT_REGION=us-east-1

# Optional: Azure
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
EOF
    print_success "Created .env.template - copy to .env and fill in your keys"
fi

# Run the comprehensive setup
print_status "Running comprehensive setup..."
echo ""
python3 tests/e2e/setup_e2e_environment.py

SETUP_EXIT_CODE=$?

echo ""
echo "================================"
if [ $SETUP_EXIT_CODE -eq 0 ]; then
    print_success "🎉 E2E setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Run tests: python -m tests.e2e.runner"
    echo "2. Or run specific test: python -m tests.e2e.runner --category orchestration"
    echo "3. Check results: ls tests/e2e/results/"
    echo ""
    echo "💡 Quick test commands:"
    echo "  make e2e-test          # Run all E2E tests"
    echo "  make e2e-test-basic    # Run basic tests only"
    echo "  make e2e-setup         # Re-run setup"
else
    print_warning "⚠️  Setup completed with some issues"
    echo ""
    echo "🔧 Common fixes:"
    echo "1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    echo "2. Authenticate: gcloud auth login"
    echo "3. Set project: gcloud config set project YOUR_PROJECT_ID"
    echo "4. Set API keys in .env file"
    echo "5. Start Redis: redis-server"
    echo ""
    echo "📋 You can still run tests that don't require missing components"
fi

echo "================================"