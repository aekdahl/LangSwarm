#!/bin/bash

# LangSwarm Debug Script - Real testing and debugging with actual API keys and data
# Usage: ./scripts/debug.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${CYAN}🚀 LangSwarm Debug & Test System${NC}"
echo -e "${CYAN}📁 Project: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}⚠️  This system uses REAL API keys and makes REAL API calls${NC}"
echo "=================================================="

# Change to project root
cd "$PROJECT_ROOT"

# Function to show help
show_help() {
    echo -e "${YELLOW}Usage: ./scripts/debug.sh [command] [options]${NC}"
    echo ""
    echo -e "${CYAN}Setup Commands:${NC}"
    echo "  setup         Set up credentials and environment for real testing"
    echo ""
    echo -e "${CYAN}Testing Commands:${NC}"
    echo "  test-bigquery Test BigQuery with real data and API calls"
    echo "  test-v2       Test V2 system with real components"
    echo ""
    echo -e "${CYAN}Validation Commands:${NC}"
    echo "  validate-creds    Validate API credentials"
    echo "  validate-config   Validate configurations with real env vars"
    echo ""
    echo -e "${CYAN}Debug Commands:${NC}"
    echo "  debug-workflow    Debug workflow execution with real data"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --verbose     Show detailed output"
    echo "  --help        Show this help"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/debug.sh setup"
    echo "  ./scripts/debug.sh test-bigquery"
    echo "  ./scripts/debug.sh debug-workflow"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT NOTES:${NC}"
    echo -e "${YELLOW}• This system makes real API calls that may incur costs${NC}"
    echo -e "${YELLOW}• You need valid API keys (OpenAI, Google Cloud)${NC}"
    echo -e "${YELLOW}• Set up .env file with real credentials${NC}"
}

# Function to run Python debug script
run_debug() {
    python scripts/langswarm_debug.py "$@"
}

# Parse command line arguments
COMMAND=""
VERBOSE=""
QUERY=""
WORKFLOW_ID=""
USER_INPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --query)
            QUERY="--query $2"
            shift 2
            ;;
        --workflow-id)
            WORKFLOW_ID="--workflow-id $2"
            shift 2
            ;;
        --input)
            USER_INPUT="--input $2"
            shift 2
            ;;
        setup|test-bigquery|test-v2|validate-creds|validate-config|debug-workflow)
            COMMAND="$1"
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Execute commands
case "$COMMAND" in
    setup)
        echo -e "${CYAN}🔧 Setting up credentials and environment...${NC}"
        echo -e "${YELLOW}This will guide you through setting up real API keys${NC}"
        run_debug setup $VERBOSE
        ;;
    test-bigquery)
        echo -e "${CYAN}🗄️  Testing BigQuery with real data...${NC}"
        if [[ -n "$QUERY" ]]; then
            run_debug test bigquery $QUERY $VERBOSE
        else
            echo -e "${YELLOW}Enter your search query:${NC}"
            read -p "Query: " search_query
            run_debug test bigquery --query "$search_query" $VERBOSE
        fi
        ;;
    test-v2)
        echo -e "${CYAN}🧪 Testing V2 system with real components...${NC}"
        run_debug test v2 $VERBOSE
        ;;
    validate-creds)
        echo -e "${CYAN}🔍 Validating API credentials...${NC}"
        run_debug validate credentials $VERBOSE
        ;;
    validate-config)
        echo -e "${CYAN}📋 Validating configurations...${NC}"
        run_debug validate config $VERBOSE
        ;;
    debug-workflow)
        echo -e "${CYAN}🔧 Debugging workflow execution...${NC}"
        
        if [[ -z "$WORKFLOW_ID" ]]; then
            echo -e "${YELLOW}Available workflows:${NC}"
            echo "  • bigquery_v2_debug_workflow"
            echo "  • bigquery_debug_workflow"
            read -p "Workflow ID [bigquery_v2_debug_workflow]: " wf_id
            if [[ -n "$wf_id" ]]; then
                WORKFLOW_ID="--workflow-id $wf_id"
            else
                WORKFLOW_ID="--workflow-id bigquery_v2_debug_workflow"
            fi
        fi
        
        if [[ -z "$USER_INPUT" ]]; then
            echo -e "${YELLOW}Enter input for workflow:${NC}"
            read -p "Input: " user_input
            if [[ -n "$user_input" ]]; then
                USER_INPUT="--input $user_input"
            else
                USER_INPUT="--input 'Test query for debugging'"
            fi
        fi
        
        run_debug debug workflow $WORKFLOW_ID $USER_INPUT $VERBOSE
        ;;
    "")
        echo -e "${YELLOW}⚠️  No command specified${NC}"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Command completed${NC}"
