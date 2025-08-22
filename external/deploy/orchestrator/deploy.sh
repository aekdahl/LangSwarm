#!/bin/bash

# AAF Orchestrator Deployment Script

set -e

# Configuration
SERVICE_NAME="aaf-orchestrator-v3"
REGION="europe-west1"
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT environment variable must be set"
    exit 1
fi

if [ -z "$ORCHESTRATOR_API_SECRET" ]; then
    echo "Error: ORCHESTRATOR_API_SECRET environment variable must be set"
    exit 1
fi

if [ -z "$PROJECT_CREATOR_FUNCTION_URL" ]; then
    echo "Error: PROJECT_CREATOR_FUNCTION_URL environment variable must be set"
    exit 1
fi

echo "Building and deploying AAF Orchestrator..."

# Build and push Docker image
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

docker build --platform linux/amd64 -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars \
REGISTRY_PROJECT_ID=$PROJECT_ID,\
ORCHESTRATOR_API_SECRET=$ORCHESTRATOR_API_SECRET,\
PROJECT_CREATOR_FUNCTION_URL=$PROJECT_CREATOR_FUNCTION_URL

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "Orchestrator deployed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Use this URL in your frontend application to manage AAF instances"
