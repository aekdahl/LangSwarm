# GCP Environment MCP Tool

## Description
Provides Google Cloud Platform environment management capabilities for LangSwarm agents. This tool enables creation, management, and interaction with GCP resources including Compute Engine, Cloud Functions, and other GCP services.

## Capabilities
- **GCP Resource Management**: Create and manage GCP compute instances
- **Environment Setup**: Configure development and deployment environments on GCP
- **Service Integration**: Integrate with various GCP services and APIs
- **Resource Monitoring**: Monitor resource usage and performance

## Configuration
Required environment variables:
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account credentials JSON file

Optional configuration:
- Default region: `us-central1`
- Default zone: `us-central1-a`
- Default machine type: `e2-medium`

## Usage Examples

### Intent-Based Calling (Recommended)
Express what you want to accomplish:
```json
{
  "tool": "gcp_environment",
  "intent": "create development environment",
  "context": "need GCP instance for Python development"
}
```

### Direct Parameter Calling
Create a GCP compute instance:
```json
{
  "method": "create_instance",
  "params": {
    "name": "dev-instance",
    "machine_type": "e2-medium",
    "zone": "us-central1-a"
  }
}
```

## Integration
This tool integrates with LangSwarm agents to provide GCP environment management capabilities for cloud-based development and deployment workflows.