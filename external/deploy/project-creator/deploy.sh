#!/bin/bash

# Project Creator Cloud Function Deployment Script

set -e

# Configuration
FUNCTION_NAME="aaf-project-creator"
REGION="us-central1"
MEMORY="2GB"
TIMEOUT="3600s"
RUNTIME="python311"

# Environment variables (set these before running)
if [ -z "$BILLING_ACCOUNT_ID" ]; then
    echo "Error: BILLING_ACCOUNT_ID environment variable must be set"
    exit 1
fi

if [ -z "$ORGANIZATION_ID" ] && [ -z "$FOLDER_ID" ]; then
    echo "Warning: Neither ORGANIZATION_ID nor FOLDER_ID is set. Projects will be created without parent."
fi

if [ -z "$REGISTRY_PROJECT_ID" ]; then
    echo "Error: REGISTRY_PROJECT_ID environment variable must be set"
    exit 1
fi

echo "Deploying Project Creator Cloud Function..."

# Deploy the function
gcloud functions deploy $FUNCTION_NAME \
    --runtime $RUNTIME \
    --trigger-http \
    --allow-unauthenticated \
    --memory $MEMORY \
    --timeout $TIMEOUT \
    --region $REGION \
    --source . \
    --entry-point create_project \
    --set-env-vars BILLING_ACCOUNT_ID=$BILLING_ACCOUNT_ID,ORGANIZATION_ID=$ORGANIZATION_ID,FOLDER_ID=$FOLDER_ID,REGISTRY_PROJECT_ID=$REGISTRY_PROJECT_ID

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(httpsTrigger.url)")

echo "Function deployed successfully!"
echo "Function URL: $FUNCTION_URL"
echo ""
echo "Set this URL in your orchestrator's PROJECT_CREATOR_FUNCTION_URL environment variable"
