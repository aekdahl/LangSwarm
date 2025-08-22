#!/bin/bash

# AAF Instance Management Script
# This script helps manage existing AAF instances (list, update, delete)

set -e

# Default values
PROJECT_ID=""
REGION="europe-west1"
ACTION=""
INSTANCE_NAME=""

# Function to display usage
usage() {
    echo "Usage: $0 --project PROJECT_ID --action ACTION [OPTIONS]"
    echo ""
    echo "Required:"
    echo "  --project PROJECT_ID          GCP project ID"
    echo "  --action ACTION               Action to perform: list, update-key, delete, logs, describe"
    echo ""
    echo "Options:"
    echo "  --region REGION               GCP region (default: europe-west1)"
    echo "  --instance INSTANCE_NAME      Instance name (required for update-key, delete, logs, describe)"
    echo "  --openai-api-key KEY          New OpenAI API key (required for update-key)"
    echo "  --help                        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --project production-pingday --action list"
    echo "  $0 --project production-pingday --action update-key --instance aaf-instance-123 --openai-api-key sk-new-key"
    echo "  $0 --project production-pingday --action delete --instance aaf-instance-123"
    echo "  $0 --project production-pingday --action logs --instance aaf-instance-123"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --instance)
            INSTANCE_NAME="$2"
            shift 2
            ;;
        --openai-api-key)
            OPENAI_API_KEY="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROJECT_ID" ]]; then
    echo "Error: --project is required"
    usage
fi

if [[ -z "$ACTION" ]]; then
    echo "Error: --action is required"
    usage
fi

# Validate action
case $ACTION in
    list)
        echo "📋 Listing AAF instances in project: $PROJECT_ID"
        echo "=================================================="
        gcloud run services list \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --filter="metadata.name~aaf-instance" \
            --format="table(metadata.name,status.url,metadata.creationTimestamp,status.conditions[0].status)" \
            --sort-by="metadata.creationTimestamp"
        ;;
    
    update-key)
        if [[ -z "$INSTANCE_NAME" ]]; then
            echo "Error: --instance is required for update-key action"
            usage
        fi
        if [[ -z "$OPENAI_API_KEY" ]]; then
            echo "Error: --openai-api-key is required for update-key action"
            usage
        fi
        
        echo "🔑 Updating OpenAI API key for instance: $INSTANCE_NAME"
        echo "======================================================"
        gcloud run services update "$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --update-env-vars="OPENAI_API_KEY=$OPENAI_API_KEY"
        
        echo "✅ OpenAI API key updated successfully!"
        ;;
    
    delete)
        if [[ -z "$INSTANCE_NAME" ]]; then
            echo "Error: --instance is required for delete action"
            usage
        fi
        
        echo "🗑️  Deleting instance: $INSTANCE_NAME"
        echo "====================================="
        read -p "Are you sure you want to delete $INSTANCE_NAME? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gcloud run services delete "$INSTANCE_NAME" \
                --project="$PROJECT_ID" \
                --region="$REGION" \
                --quiet
            echo "✅ Instance deleted successfully!"
        else
            echo "❌ Deletion cancelled."
        fi
        ;;
    
    logs)
        if [[ -z "$INSTANCE_NAME" ]]; then
            echo "Error: --instance is required for logs action"
            usage
        fi
        
        echo "📝 Showing logs for instance: $INSTANCE_NAME"
        echo "============================================"
        gcloud logging read \
            "resource.type=cloud_run_revision AND resource.labels.service_name=$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --limit=50 \
            --format="table(timestamp,severity,textPayload)" \
            --sort-by="timestamp"
        ;;
    
    describe)
        if [[ -z "$INSTANCE_NAME" ]]; then
            echo "Error: --instance is required for describe action"
            usage
        fi
        
        echo "ℹ️  Describing instance: $INSTANCE_NAME"
        echo "======================================"
        gcloud run services describe "$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --region="$REGION"
        ;;
    
    health)
        if [[ -z "$INSTANCE_NAME" ]]; then
            echo "Error: --instance is required for health action"
            usage
        fi
        
        echo "🔍 Checking health for instance: $INSTANCE_NAME"
        echo "==============================================="
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe "$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --format="value(status.url)")
        
        if [[ -z "$SERVICE_URL" ]]; then
            echo "❌ Could not get service URL for $INSTANCE_NAME"
            exit 1
        fi
        
        echo "Service URL: $SERVICE_URL"
        echo "Health endpoint: $SERVICE_URL/health"
        echo ""
        
        # Test health endpoint
        if curl -f -s "$SERVICE_URL/health" > /dev/null; then
            echo "✅ Health check passed!"
            echo ""
            echo "📋 Health Details:"
            curl -s "$SERVICE_URL/health" | python3 -m json.tool
        else
            echo "❌ Health check failed!"
            echo "Check logs with: $0 --project $PROJECT_ID --action logs --instance $INSTANCE_NAME"
        fi
        ;;
    
    *)
        echo "Error: Unknown action '$ACTION'"
        echo "Valid actions: list, update-key, delete, logs, describe, health"
        usage
        ;;
esac
