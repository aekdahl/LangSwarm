#!/bin/bash
set -e

# Configuration
PROJECT_ID="langswarm-pro-prod"
REGION="us-central1"
SERVICE_NAME="langswarm-pro-api"
DB_INSTANCE="langswarm-pro-db"
DB_NAME="langswarm_pro_db"

echo "Deploying $SERVICE_NAME to $PROJECT_ID in $REGION..."

# 1. Build the container using Cloud Build
# We submit the build from the root directory to capture all packages
echo "Building container..."
gcloud builds submit .. \
    --project=$PROJECT_ID \
    --config=cloudbuild.yaml \
    --substitutions=_SERVICE_NAME=$SERVICE_NAME

# 2. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --image="gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,DB_INSTANCE=$DB_INSTANCE" \
    --add-cloudsql-instances="$PROJECT_ID:$REGION:$DB_INSTANCE"

echo "Deployment complete!"
