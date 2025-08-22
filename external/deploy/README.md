# AAF Deployment Scripts

This directory contains scripts for deploying and managing AAF (AI Agent Framework) instances on Google Cloud Run.

## Scripts Overview

### 1. `deploy-aaf-instance.sh` - Deploy New Instances
Deploys a new AAF backend instance with proper naming conventions and comprehensive environment variables.

### 2. `manage-aaf-instances.sh` - Manage Existing Instances
Manages existing AAF instances (list, update, delete, logs, health checks).

## Quick Start

### Deploy a New Instance

```bash
# Basic deployment with placeholder OpenAI key
./deploy-aaf-instance.sh --project production-pingday

# Deployment with real OpenAI API key
./deploy-aaf-instance.sh \
  --project production-pingday \
  --openai-api-key sk-your-real-openai-key-here

# Custom configuration
./deploy-aaf-instance.sh \
  --project production-pingday \
  --openai-api-key sk-your-key \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 20
```

### Manage Existing Instances

```bash
# List all AAF instances
./manage-aaf-instances.sh --project production-pingday --action list

# Check health of an instance
./manage-aaf-instances.sh \
  --project production-pingday \
  --action health \
  --instance aaf-instance-1234567890

# Update OpenAI API key
./manage-aaf-instances.sh \
  --project production-pingday \
  --action update-key \
  --instance aaf-instance-1234567890 \
  --openai-api-key sk-new-key-here

# View logs
./manage-aaf-instances.sh \
  --project production-pingday \
  --action logs \
  --instance aaf-instance-1234567890

# Delete an instance
./manage-aaf-instances.sh \
  --project production-pingday \
  --action delete \
  --instance aaf-instance-1234567890
```

## Environment Variables

The deployment script automatically configures the following environment variables:

### Required
- `OPENAI_API_KEY` - OpenAI API key for LLM functionality
- `MANAGEMENT_API_SECRET` - Secret for management API access
- `SECRET_KEY` - Application secret key
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `PROJECT_ID` - Same as GOOGLE_CLOUD_PROJECT

### BigQuery & Sessions
- `BIGQUERY_DATASET_ID=aaf_sessions` - BigQuery dataset for session storage
- `BIGQUERY_TABLE_ID=conversations` - BigQuery table for conversations
- `SESSION_BACKEND=bigquery` - Use BigQuery for session management
- `SESSION_TTL=3600` - Session timeout in seconds

### LLM Configuration
- `DEFAULT_AGENT_MODEL=gpt-4o` - Default LLM model
- `DEFAULT_AGENT_BEHAVIOR=helpful` - Default agent behavior
- `MEMORY_ENABLED=true` - Enable conversation memory
- `MEMORY_BACKEND=bigquery` - Use BigQuery for memory storage
- `MEMORY_AUTO_STORE=true` - Automatically store conversations

### Application Settings
- `LOG_LEVEL=INFO` - Logging level
- `APP_HOST=0.0.0.0` - Application host
- `APP_PORT=8000` - Application port (internal)
- `RATE_LIMIT_REQUESTS_PER_MINUTE=60` - Rate limiting
- `RATE_LIMIT_BURST=10` - Rate limit burst
- `MANAGEMENT_API_ENABLED=true` - Enable management API

### External Services
- `CRAWL4AI_BASE_URL` - Base URL for Crawl4AI service (placeholder)

## Instance Naming Convention

All instances are named with the pattern: `aaf-instance-{timestamp}`

This naming convention is required for frontend integration.

## Health Monitoring

Every deployed instance exposes a health endpoint at `/health` that returns:

```json
{
    "status": "healthy",
    "version": "1.0.0", 
    "timestamp": "2025-08-19T20:23:12.219542",
    "langswarm_status": "ready",
    "agents_count": 1
}
```

## Frontend Integration

The deployed instances are ready for frontend integration with:

- ✅ Correct `aaf-instance-` naming convention
- ✅ All environment variables configured
- ✅ CORS enabled for web access
- ✅ WebSocket support for real-time chat
- ✅ Health endpoints for monitoring

### Orphaned Services Management

If instances are deployed directly (not through the orchestrator), they become "orphaned services" - they exist in GCP but not in the orchestrator database. Use the adopt functionality to register them:

```bash
# Test and adopt orphaned services
./test-adopt-orphaned.sh production-pingday YOUR_ORCHESTRATOR_SECRET
```

This will:
1. Sync to identify orphaned services
2. Adopt them into the database with proper metadata
3. Verify all services are now properly registered

## Troubleshooting

### Common Issues

1. **OpenAI API Key Issues**
   ```bash
   # Update the API key
   ./manage-aaf-instances.sh \
     --project YOUR_PROJECT \
     --action update-key \
     --instance INSTANCE_NAME \
     --openai-api-key sk-new-key
   ```

2. **Check Logs**
   ```bash
   ./manage-aaf-instances.sh \
     --project YOUR_PROJECT \
     --action logs \
     --instance INSTANCE_NAME
   ```

3. **Health Check Failures**
   ```bash
   ./manage-aaf-instances.sh \
     --project YOUR_PROJECT \
     --action health \
     --instance INSTANCE_NAME
   ```

### Manual Commands

If you need to run gcloud commands manually:

```bash
# List services
gcloud run services list --project=YOUR_PROJECT --region=europe-west1

# Update environment variables
gcloud run services update INSTANCE_NAME \
  --project=YOUR_PROJECT \
  --region=europe-west1 \
  --update-env-vars="KEY1=value1,KEY2=value2"

# View logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=INSTANCE_NAME" \
  --project=YOUR_PROJECT \
  --limit=50

# Delete service
gcloud run services delete INSTANCE_NAME \
  --project=YOUR_PROJECT \
  --region=europe-west1
```

## Docker Image

The scripts deploy from the image:
`europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend:latest`

To build and push a new image, use the existing Dockerfile in `external/aaf/Dockerfile.deployment`.