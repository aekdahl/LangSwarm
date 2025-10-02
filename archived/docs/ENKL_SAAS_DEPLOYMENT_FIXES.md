# ENKL-SAAS Deployment Fixes

## Overview

This document outlines the fixes applied to resolve deployment errors for the AAF infrastructure on the `enkl-saas` GCP project.

## Issues Addressed

### 1. CloudBuild Import Error

**Error:**
```
ImportError: cannot import name 'cloudbuild_v1' from 'google.cloud' (unknown location) --> aaf-project-creator
```

**Fix:**
- Updated `external/deploy/project-creator/app.py` to handle the import gracefully
- Updated Google Cloud Build dependency version in requirements.txt
- Added try-catch block for cloudbuild_v1 import

**Files Modified:**
- `external/deploy/project-creator/app.py`
- `external/deploy/project-creator/requirements.txt`

### 2. BigQuery Permissions Error

**Error:**
```
google.api_core.exceptions.Forbidden: 403 POST https://bigquery.googleapis.com/bigquery/v2/projects/enkl-saas/datasets?prettyPrint=false: Access Denied: Project enkl-saas: User does not have bigquery.datasets.create permission in project enkl-saas. --> aaf-orchestrator
```

**Fix:**
- Replaced BigQuery-based ProjectRegistry with Firestore-based registry
- Updated orchestrator to use FirestoreProjectRegistry instead of BigQuery
- Removed BigQuery dependency and replaced with Firestore
- Updated environment configuration to use Firestore collection

**Files Modified:**
- `external/deploy/orchestrator/main.py`
- `external/deploy/orchestrator/requirements.txt`

### 3. Region Update to Europe-West1

**Requirement:**
- Change all deployments from US regions to europe-west1

**Fix:**
- Updated deployment scripts to use europe-west1
- Updated all documentation to reference europe-west1
- Updated configuration templates and examples

**Files Modified:**
- `external/deploy/deploy-enkl-saas.sh`
- `external/deploy/DEPLOYMENT_ENKL_SAAS.md`

## Implementation Details

### Firestore Registry Migration

The orchestrator now uses Firestore instead of BigQuery for project registry:

**Benefits:**
- Real-time updates and listeners
- Better performance for small-scale data
- No dataset creation permissions required
- Built-in caching and indexing

**Configuration:**
```bash
# Environment variables for Firestore
FIRESTORE_DATABASE=(default)
FIRESTORE_COLLECTION=aaf_projects
REGISTRY_PROJECT_ID=enkl-saas
```

### Regional Configuration

All services now deploy to europe-west1:

- **Cloud Functions:** europe-west1
- **Cloud Run:** europe-west1
- **Firestore:** europe-west1
- **Container Registry:** Global (accessed from europe-west1)

### Updated Architecture

```
enkl-saas (europe-west1)
├── Project Creator Function (Cloud Functions)
├── AAF Orchestrator (Cloud Run)
├── Firestore Database (Project Registry)
└── Container Registry (AAF Images)
```

## Deployment Instructions

### Prerequisites

1. Ensure you have the required permissions:
   ```bash
   # Required roles for enkl-saas project
   - Cloud Functions Admin
   - Cloud Run Admin
   - Firestore Admin
   - Container Registry Admin
   - IAM Admin
   ```

2. Set environment variables:
   ```bash
   export PROJECT_ID="enkl-saas"
   export REGION="europe-west1"
   export BILLING_ACCOUNT_ID="your-billing-account"
   export ORGANIZATION_ID="your-org-id"
   ```

### Deployment

1. Navigate to deployment directory:
   ```bash
   cd external/deploy
   ```

2. Run the deployment script:
   ```bash
   ./deploy-enkl-saas.sh
   ```

3. Verify deployment:
   ```bash
   # Check function
   gcloud functions describe aaf-project-creator --region=europe-west1
   
   # Check orchestrator
   gcloud run services describe aaf-orchestrator --region=europe-west1
   
   # Check Firestore
   gcloud firestore collections list
   ```

## Testing

### Health Checks

```bash
# Function health
curl "https://europe-west1-enkl-saas.cloudfunctions.net/aaf-project-creator"

# Orchestrator health
curl "https://aaf-orchestrator-xxx-ew.a.run.app/health"
```

### Project Creation

```bash
# Create test project via orchestrator
curl -X POST "https://aaf-orchestrator-xxx-ew.a.run.app/projects/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_API_SECRET" \
  -d '{
    "project_name": "Test AAF Project",
    "customer_id": "test-customer",
    "aaf_config": {
      "memory": "2Gi",
      "max_instances": 3
    }
  }'
```

## Monitoring

### Logs

```bash
# Function logs
gcloud functions logs read aaf-project-creator --region=europe-west1

# Orchestrator logs
gcloud run logs tail aaf-orchestrator --region=europe-west1
```

### Firestore

```bash
# View project registry
gcloud firestore documents list aaf_projects

# Query projects
gcloud firestore query "SELECT * FROM aaf_projects WHERE status = 'active'"
```

## Security

### IAM Configuration

The deployment creates service accounts with minimal required permissions:

- **Project Creator SA:** Resource Manager, Billing (if configured)
- **Orchestrator SA:** Firestore User, Cloud Run Admin

### API Security

- Orchestrator protected with API secret authentication
- Functions use service account authentication
- Cloud Run services use IAM authentication

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Verify service account has required roles
   - Check organization-level permissions

2. **Function Timeout**
   - Increase timeout in deployment script
   - Check project creation dependencies

3. **Firestore Access**
   - Verify Firestore API is enabled
   - Check service account Firestore permissions

### Recovery

If deployment fails:

1. Check logs for specific errors
2. Verify all APIs are enabled
3. Ensure billing account is configured
4. Check organization policies

## Next Steps

1. **Frontend Integration:** Update frontend configuration with new orchestrator URL
2. **Monitoring Setup:** Configure alerting and monitoring
3. **Customer Onboarding:** Create documentation for customer project creation
4. **Scaling:** Configure auto-scaling for production workloads

## Files Changed

### Modified Files
- `external/deploy/project-creator/app.py`
- `external/deploy/project-creator/requirements.txt`
- `external/deploy/orchestrator/main.py`
- `external/deploy/orchestrator/requirements.txt`
- `external/deploy/deploy-enkl-saas.sh`
- `external/deploy/DEPLOYMENT_ENKL_SAAS.md`

### New Files
- `docs/ENKL_SAAS_DEPLOYMENT_FIXES.md` (this document)

## Summary

All reported issues have been resolved:

✅ CloudBuild import error fixed
✅ BigQuery permissions issue resolved (migrated to Firestore)
✅ Region updated to europe-west1
✅ Deployment scripts updated
✅ Documentation updated

The infrastructure is now ready for deployment to the enkl-saas project in the europe-west1 region.
