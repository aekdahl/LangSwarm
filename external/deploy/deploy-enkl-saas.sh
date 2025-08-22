#!/bin/bash

# AAF Complete Infrastructure Deployment for enkl-saas
# This script deploys the entire AAF multi-project infrastructure

set -e

echo "🚀 Starting AAF Infrastructure Deployment to enkl-saas..."

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
if [ ! -f "deploy-enkl-saas.sh" ]; then
    print_error "Please run this script from the external/deploy directory"
    exit 1
fi

# Set project
PROJECT_ID="enkl-saas"
REGION="europe-west1"

print_status "Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Please authenticate with GCP first: gcloud auth login"
    exit 1
fi

# Generate orchestrator API secret if not set
if [ -z "$ORCHESTRATOR_API_SECRET" ]; then
    export ORCHESTRATOR_API_SECRET=$(openssl rand -hex 32)
    print_status "Generated orchestrator API secret"
fi

# Check required environment variables
if [ -z "$BILLING_ACCOUNT_ID" ]; then
    print_warning "BILLING_ACCOUNT_ID not set. Please set it for automatic project creation:"
    echo "export BILLING_ACCOUNT_ID=your-billing-account-id"
    read -p "Continue without billing account? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if [ -z "$ORGANIZATION_ID" ]; then
    print_warning "ORGANIZATION_ID not set. Projects will be created without organization parent."
fi

# Step 1: Enable APIs
print_status "Enabling required GCP APIs..."
gcloud services enable cloudfunctions.googleapis.com \
                      run.googleapis.com \
                      firestore.googleapis.com \
                      cloudresourcemanager.googleapis.com \
                      cloudbilling.googleapis.com \
                      iam.googleapis.com \
                      containerregistry.googleapis.com \
                      cloudbuild.googleapis.com

print_success "APIs enabled"

# Step 2: Create service accounts
print_status "Creating service accounts..."

# Project Creator Service Account
PROJECT_CREATOR_SA="aaf-project-creator@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe $PROJECT_CREATOR_SA >/dev/null 2>&1; then
    gcloud iam service-accounts create aaf-project-creator \
        --display-name="AAF Project Creator" \
        --description="Service account for creating customer AAF projects"
    print_success "Created project creator service account"
else
    print_status "Project creator service account already exists"
fi

# Orchestrator Service Account
ORCHESTRATOR_SA="aaf-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe $ORCHESTRATOR_SA >/dev/null 2>&1; then
    gcloud iam service-accounts create aaf-orchestrator \
        --display-name="AAF Orchestrator" \
        --description="Service account for AAF orchestrator"
    print_success "Created orchestrator service account"
else
    print_status "Orchestrator service account already exists"
fi

# Step 3: Grant IAM permissions
print_status "Configuring IAM permissions..."

# Grant Firestore permissions to orchestrator
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_SA}" \
    --role="roles/datastore.user" \
    --quiet

# Grant organization-level permissions if organization ID is set
if [ ! -z "$ORGANIZATION_ID" ]; then
    print_status "Granting organization-level permissions..."
    
    # Project Creator permissions
    gcloud organizations add-iam-policy-binding $ORGANIZATION_ID \
        --member="serviceAccount:${PROJECT_CREATOR_SA}" \
        --role="roles/resourcemanager.projectCreator" \
        --quiet
    
    # Billing permissions
    if [ ! -z "$BILLING_ACCOUNT_ID" ]; then
        gcloud organizations add-iam-policy-binding $ORGANIZATION_ID \
            --member="serviceAccount:${PROJECT_CREATOR_SA}" \
            --role="roles/billing.projectManager" \
            --quiet
    fi
    
    # Orchestrator permissions for managing AAF instances
    gcloud organizations add-iam-policy-binding $ORGANIZATION_ID \
        --member="serviceAccount:${ORCHESTRATOR_SA}" \
        --role="roles/run.admin" \
        --quiet
    
    gcloud organizations add-iam-policy-binding $ORGANIZATION_ID \
        --member="serviceAccount:${ORCHESTRATOR_SA}" \
        --role="roles/iam.serviceAccountUser" \
        --quiet
fi

print_success "IAM permissions configured"

# Step 4: Initialize Firestore
print_status "Initializing Firestore..."
if ! gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
    gcloud firestore databases create --region=$REGION --quiet
    print_success "Firestore database created"
else
    print_status "Firestore database already exists"
fi

# Create Firestore indexes
print_status "Creating Firestore indexes..."
gcloud firestore indexes composite create \
    --collection-group=aaf_projects \
    --field-config field-path=status,order=ascending \
    --field-config field-path=created_at,order=descending \
    --quiet 2>/dev/null || print_status "Firestore indexes may already exist"

# Step 5: Build and push AAF backend image
print_status "Building AAF backend Docker image..."

# Configure Docker for GCP
gcloud auth configure-docker --quiet

# Build AAF backend from project root to include LangSwarm
cd ../../
AAF_IMAGE="gcr.io/${PROJECT_ID}/aaf-backend:latest"
docker build -t $AAF_IMAGE -f external/aaf/Dockerfile.deployment .
docker push $AAF_IMAGE
print_success "AAF backend image built and pushed: $AAF_IMAGE"

cd external/deploy

# Step 6: Deploy Project Creator Function
print_status "Deploying Project Creator Cloud Function..."

cd project-creator

# Set environment variables for deployment
export REGISTRY_PROJECT_ID=$PROJECT_ID

# Deploy function
gcloud functions deploy aaf-project-creator \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --memory 2GB \
    --timeout 3600s \
    --region $REGION \
    --source . \
    --entry-point create_project \
    --service-account $PROJECT_CREATOR_SA \
    --set-env-vars BILLING_ACCOUNT_ID=${BILLING_ACCOUNT_ID:-},ORGANIZATION_ID=${ORGANIZATION_ID:-},FOLDER_ID=${FOLDER_ID:-},REGISTRY_PROJECT_ID=$REGISTRY_PROJECT_ID \
    --quiet

# Get function URL
PROJECT_CREATOR_FUNCTION_URL=$(gcloud functions describe aaf-project-creator --region=$REGION --format="value(httpsTrigger.url)")
print_success "Project Creator Function deployed: $PROJECT_CREATOR_FUNCTION_URL"

cd ../

# Step 7: Deploy Orchestrator
print_status "Deploying AAF Orchestrator..."

cd orchestrator

# Set environment variables for orchestrator deployment
export PROJECT_CREATOR_FUNCTION_URL=$PROJECT_CREATOR_FUNCTION_URL

# Build and deploy orchestrator
ORCHESTRATOR_IMAGE="gcr.io/${PROJECT_ID}/aaf-orchestrator"
docker build --platform linux/amd64 -t $ORCHESTRATOR_IMAGE .
docker push $ORCHESTRATOR_IMAGE

gcloud run deploy aaf-orchestrator \
    --image $ORCHESTRATOR_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --service-account $ORCHESTRATOR_SA \
    --set-env-vars REGISTRY_PROJECT_ID=$PROJECT_ID,ORCHESTRATOR_API_SECRET=$ORCHESTRATOR_API_SECRET,PROJECT_CREATOR_FUNCTION_URL=$PROJECT_CREATOR_FUNCTION_URL,FIRESTORE_DATABASE="(default)",FIRESTORE_COLLECTION=aaf_projects \
    --quiet

# Get orchestrator URL
ORCHESTRATOR_URL=$(gcloud run services describe aaf-orchestrator --region=$REGION --format="value(status.url)")
print_success "Orchestrator deployed: $ORCHESTRATOR_URL"

cd ../

# Step 8: Test deployments
print_status "Testing deployments..."

# Test function health
if curl -f -s "$PROJECT_CREATOR_FUNCTION_URL" >/dev/null; then
    print_success "Project Creator Function is responding"
else
    print_warning "Project Creator Function may not be responding correctly"
fi

# Test orchestrator health
if curl -f -s "$ORCHESTRATOR_URL/health" >/dev/null; then
    print_success "Orchestrator is responding"
else
    print_warning "Orchestrator may not be responding correctly"
fi

# Step 9: Create deployment summary
print_status "Creating deployment summary..."

cat > deployment-summary.txt << EOF
AAF Infrastructure Deployment Summary
=====================================

Project: $PROJECT_ID
Region: $REGION
Deployment Date: $(date)

Service URLs:
- Project Creator Function: $PROJECT_CREATOR_FUNCTION_URL
- Orchestrator: $ORCHESTRATOR_URL

Service Accounts:
- Project Creator: $PROJECT_CREATOR_SA
- Orchestrator: $ORCHESTRATOR_SA

Configuration:
- Orchestrator API Secret: $ORCHESTRATOR_API_SECRET
- AAF Backend Image: $AAF_IMAGE

Frontend Configuration:
Add these to your frontend environment:
REACT_APP_ORCHESTRATOR_URL=$ORCHESTRATOR_URL
REACT_APP_ORCHESTRATOR_SECRET=$ORCHESTRATOR_API_SECRET

Testing Commands:
# Test orchestrator health
curl "$ORCHESTRATOR_URL/health"

# List projects (empty initially)
curl "$ORCHESTRATOR_URL/api/projects" \\
    -H "X-API-Secret: $ORCHESTRATOR_API_SECRET"

# Create test project
curl -X POST "$ORCHESTRATOR_URL/api/projects" \\
    -H "Content-Type: application/json" \\
    -H "X-API-Secret: $ORCHESTRATOR_API_SECRET" \\
    -d '{
        "customer_id": "test-customer",
        "project_name": "Test Customer AAF",
        "aaf_config": {
            "memory": "2Gi",
            "max_instances": 3
        }
    }'

Monitoring:
# View function logs
gcloud functions logs read aaf-project-creator --region=$REGION --limit=50

# View orchestrator logs  
gcloud run logs tail aaf-orchestrator --region=$REGION

# View Firestore data
gcloud firestore collections list
gcloud firestore documents list aaf_projects
EOF

print_success "Deployment completed successfully! 🎉"
echo ""
echo "📋 Deployment Summary:"
echo "======================"
echo "Project Creator Function: $PROJECT_CREATOR_FUNCTION_URL"
echo "Orchestrator: $ORCHESTRATOR_URL"
echo "Orchestrator API Secret: $ORCHESTRATOR_API_SECRET"
echo ""
echo "📁 Full deployment details saved to: deployment-summary.txt"
echo ""
echo "🔗 Next Steps:"
echo "1. Update your frontend with the orchestrator URL and API secret"
echo "2. Test the deployment using the commands in deployment-summary.txt"
echo "3. Create your first customer AAF project via the orchestrator API"
echo ""
echo "📚 View logs:"
echo "- Function logs: gcloud functions logs read aaf-project-creator --region=$REGION"
echo "- Orchestrator logs: gcloud run logs tail aaf-orchestrator --region=$REGION"
