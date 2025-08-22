#!/bin/bash

# Deployment Verification Script for enkl-saas
# Verifies all components are working correctly

set -e

echo "🔍 Verifying AAF Infrastructure Deployment..."

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

# Configuration
PROJECT_ID="enkl-saas"
REGION="europe-west1"

print_status "Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check 1: Project Creator Function
print_status "Checking Project Creator Function..."
if gcloud functions describe aaf-project-creator --region=$REGION >/dev/null 2>&1; then
    FUNCTION_URL=$(gcloud functions describe aaf-project-creator --region=$REGION --format="value(httpsTrigger.url)")
    print_success "Project Creator Function exists: $FUNCTION_URL"
    
    # Test function health
    if curl -f -s "$FUNCTION_URL" >/dev/null 2>&1; then
        print_success "Function is responding"
    else
        print_warning "Function may not be responding correctly"
    fi
else
    print_error "Project Creator Function not found"
    exit 1
fi

# Check 2: Orchestrator Service
print_status "Checking Orchestrator Service..."
if gcloud run services describe aaf-orchestrator --region=$REGION >/dev/null 2>&1; then
    ORCHESTRATOR_URL=$(gcloud run services describe aaf-orchestrator --region=$REGION --format="value(status.url)")
    print_success "Orchestrator exists: $ORCHESTRATOR_URL"
    
    # Test orchestrator health
    if curl -f -s "$ORCHESTRATOR_URL/health" >/dev/null 2>&1; then
        print_success "Orchestrator is responding"
    else
        print_warning "Orchestrator may not be responding correctly"
    fi
else
    print_error "Orchestrator not found"
    exit 1
fi

# Check 3: Firestore Database
print_status "Checking Firestore Database..."
if gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
    print_success "Firestore database exists"
    
    # Check if collections exist
    if gcloud firestore collections list | grep -q "aaf_projects"; then
        print_success "AAF projects collection exists"
    else
        print_warning "AAF projects collection not yet created (will be created on first use)"
    fi
else
    print_error "Firestore database not found"
    exit 1
fi

# Check 4: Service Accounts
print_status "Checking Service Accounts..."

PROJECT_CREATOR_SA="aaf-project-creator@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $PROJECT_CREATOR_SA >/dev/null 2>&1; then
    print_success "Project Creator service account exists"
else
    print_error "Project Creator service account not found"
fi

ORCHESTRATOR_SA="aaf-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $ORCHESTRATOR_SA >/dev/null 2>&1; then
    print_success "Orchestrator service account exists"
else
    print_error "Orchestrator service account not found"
fi

# Check 5: Container Images
print_status "Checking Container Images..."
if gcloud container images list --repository=gcr.io/$PROJECT_ID | grep -q "aaf-backend"; then
    print_success "AAF backend image exists"
else
    print_warning "AAF backend image not found - may need to be built"
fi

if gcloud container images list --repository=gcr.io/$PROJECT_ID | grep -q "aaf-orchestrator"; then
    print_success "AAF orchestrator image exists"
else
    print_warning "AAF orchestrator image not found - may need to be built"
fi

# Check 6: APIs Enabled
print_status "Checking required APIs..."
REQUIRED_APIS=(
    "cloudfunctions.googleapis.com"
    "run.googleapis.com"
    "firestore.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iam.googleapis.com"
    "containerregistry.googleapis.com"
    "cloudbuild.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        print_success "API enabled: $api"
    else
        print_error "API not enabled: $api"
    fi
done

# Generate test commands
echo ""
echo "📋 Test Commands:"
echo "=================="
echo ""
echo "# Test function directly:"
echo "curl \"$FUNCTION_URL\""
echo ""
echo "# Test orchestrator health:"
echo "curl \"$ORCHESTRATOR_URL/health\""
echo ""
echo "# List projects (requires API secret):"
echo "curl \"$ORCHESTRATOR_URL/projects\" \\"
echo "    -H \"Authorization: Bearer \$ORCHESTRATOR_API_SECRET\""
echo ""
echo "# Create test project (requires API secret):"
echo "curl -X POST \"$ORCHESTRATOR_URL/projects/create\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -H \"Authorization: Bearer \$ORCHESTRATOR_API_SECRET\" \\"
echo "    -d '{"
echo "        \"project_name\": \"Test AAF Project\","
echo "        \"customer_id\": \"test-customer\","
echo "        \"aaf_config\": {"
echo "            \"memory\": \"2Gi\","
echo "            \"max_instances\": 3"
echo "        }"
echo "    }'"
echo ""

# Generate monitoring commands
echo "📊 Monitoring Commands:"
echo "======================="
echo ""
echo "# View function logs:"
echo "gcloud functions logs read aaf-project-creator --region=$REGION --limit=50"
echo ""
echo "# View orchestrator logs:"
echo "gcloud run logs tail aaf-orchestrator --region=$REGION"
echo ""
echo "# View Firestore collections:"
echo "gcloud firestore collections list"
echo ""
echo "# View project registry:"
echo "gcloud firestore documents list aaf_projects"
echo ""

print_success "Deployment verification completed! 🎉"
echo ""
echo "📋 Summary:"
echo "==========="
echo "Project Creator Function: $FUNCTION_URL"
echo "Orchestrator Service: $ORCHESTRATOR_URL"
echo "Region: $REGION"
echo "Firestore: Active"
echo ""
echo "🔗 Next Steps:"
echo "1. Set ORCHESTRATOR_API_SECRET environment variable"
echo "2. Test project creation using the commands above"
echo "3. Configure frontend with orchestrator URL"
echo "4. Set up monitoring and alerting"
