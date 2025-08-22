#!/bin/bash

# AAF Instance Deployment Script
# This script deploys an AAF backend instance to Google Cloud Run with proper naming and environment variables

set -e

# Default values
PROJECT_ID=""
REGION="europe-west1"
OPENAI_API_KEY=""
MANAGEMENT_API_SECRET=""
MEMORY=""
CPU=""
MAX_INSTANCES=""
IMAGE_TAG="latest"

# Function to display usage
usage() {
    echo "Usage: $0 --project PROJECT_ID [OPTIONS]"
    echo ""
    echo "Required:"
    echo "  --project PROJECT_ID          GCP project ID to deploy to"
    echo ""
    echo "Options:"
    echo "  --region REGION               GCP region (default: europe-west1)"
    echo "  --openai-api-key KEY          OpenAI API key (default: placeholder)"
    echo "  --management-secret SECRET    Management API secret (default: auto-generated)"
    echo "  --memory MEMORY               Memory allocation (default: 2Gi)"
    echo "  --cpu CPU                     CPU allocation (default: 1)"
    echo "  --max-instances COUNT         Maximum instances (default: 10)"
    echo "  --image-tag TAG               Docker image tag (default: latest)"
    echo "  --help                        Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --project production-pingday --openai-api-key sk-your-key-here"
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
        --openai-api-key)
            OPENAI_API_KEY="$2"
            shift 2
            ;;
        --management-secret)
            MANAGEMENT_API_SECRET="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --cpu)
            CPU="$2"
            shift 2
            ;;
        --max-instances)
            MAX_INSTANCES="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
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

# Set defaults for optional parameters
if [[ -z "$OPENAI_API_KEY" ]]; then
    OPENAI_API_KEY="sk-placeholder-openai-key"
    echo "Warning: Using placeholder OpenAI API key. Update after deployment."
fi

if [[ -z "$MANAGEMENT_API_SECRET" ]]; then
    MANAGEMENT_API_SECRET="aaf-mgmt-secret-$(date +%s)"
fi

if [[ -z "$MEMORY" ]]; then
    MEMORY="2Gi"
fi

if [[ -z "$CPU" ]]; then
    CPU="1"
fi

if [[ -z "$MAX_INSTANCES" ]]; then
    MAX_INSTANCES="10"
fi

# Generate instance name with timestamp
INSTANCE_NAME="aaf-instance-$(date +%s)"
SECRET_KEY="aaf-app-secret-$(date +%s)"

# Docker image URL
IMAGE_URL="europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend:${IMAGE_TAG}"

echo "🚀 Deploying AAF Instance"
echo "=========================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Instance Name: $INSTANCE_NAME"
echo "Image: $IMAGE_URL"
echo "Memory: $MEMORY"
echo "CPU: $CPU"
echo "Max Instances: $MAX_INSTANCES"
echo ""

# Build environment variables string
ENV_VARS="OPENAI_API_KEY=$OPENAI_API_KEY"
ENV_VARS="$ENV_VARS,MANAGEMENT_API_SECRET=$MANAGEMENT_API_SECRET"
ENV_VARS="$ENV_VARS,SECRET_KEY=$SECRET_KEY"
ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
ENV_VARS="$ENV_VARS,PROJECT_ID=$PROJECT_ID"
ENV_VARS="$ENV_VARS,REGION=$REGION"
ENV_VARS="$ENV_VARS,BIGQUERY_DATASET_ID=aaf_sessions"
ENV_VARS="$ENV_VARS,BIGQUERY_TABLE_ID=conversations"
ENV_VARS="$ENV_VARS,CRAWL4AI_BASE_URL=https://crawl4ai-dummy.example.com"
ENV_VARS="$ENV_VARS,SESSION_BACKEND=bigquery"
ENV_VARS="$ENV_VARS,SESSION_TTL=3600"
ENV_VARS="$ENV_VARS,MEMORY_ENABLED=true"
ENV_VARS="$ENV_VARS,MEMORY_BACKEND=bigquery"
ENV_VARS="$ENV_VARS,MEMORY_AUTO_STORE=true"
ENV_VARS="$ENV_VARS,DEFAULT_AGENT_MODEL=gpt-4o"
ENV_VARS="$ENV_VARS,DEFAULT_AGENT_BEHAVIOR=helpful"
ENV_VARS="$ENV_VARS,RATE_LIMIT_REQUESTS_PER_MINUTE=60"
ENV_VARS="$ENV_VARS,RATE_LIMIT_BURST=10"
ENV_VARS="$ENV_VARS,LOG_LEVEL=INFO"
ENV_VARS="$ENV_VARS,APP_HOST=0.0.0.0"
ENV_VARS="$ENV_VARS,APP_PORT=8000"
ENV_VARS="$ENV_VARS,MANAGEMENT_API_ENABLED=true"

echo "🔧 Deploying to Cloud Run..."

# Deploy to Cloud Run
gcloud run deploy "$INSTANCE_NAME" \
    --image="$IMAGE_URL" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --max-instances="$MAX_INSTANCES"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format="value(status.url)")

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo "Instance Name: $INSTANCE_NAME"
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/health"
echo ""

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Health check passed!"
    echo ""
    echo "📋 Instance Details:"
    curl -s "$SERVICE_URL/health" | python3 -m json.tool
else
    echo "❌ Health check failed. Check logs:"
    echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$INSTANCE_NAME\" --project=$PROJECT_ID --limit=20"
fi

echo ""
echo "🔑 Environment Variables:"
echo "========================"
echo "To update the OpenAI API key:"
echo "gcloud run services update $INSTANCE_NAME \\"
echo "  --project=$PROJECT_ID \\"
echo "  --region=$REGION \\"
echo "  --update-env-vars=\"OPENAI_API_KEY=your-real-openai-key\""
echo ""
echo "To update other environment variables:"
echo "gcloud run services update $INSTANCE_NAME \\"
echo "  --project=$PROJECT_ID \\"
echo "  --region=$REGION \\"
echo "  --update-env-vars=\"KEY1=value1,KEY2=value2\""
