# GCP Environment Tool

## Description

Google Cloud Platform environment management for deploying, configuring, and managing GCP resources and services.

## Instructions

This tool provides GCP operations with two calling approaches:

### Intent-Based Calling (Smart Cloud Management)

Use **`gcp_environment`** with intent for intelligent GCP operations:

**Parameters:**
- `intent`: What GCP operation you need
- `context`: Relevant details (project, region, service type)

**When to use:**
- Deploying services: "Deploy the API to Cloud Run"
- Resource management: "Create a storage bucket for backups"
- Monitoring: "Check the status of my compute instances"
- Configuration: "Set up a PostgreSQL database"

**Examples:**
- "Deploy to Cloud Run" → intent="deploy the containerized API to Cloud Run in production", context="prod environment, europe-west1"
- "Create storage bucket" → intent="create a Cloud Storage bucket for application backups", context="backup storage, versioning enabled"

### Direct Method Calling

**`gcp_environment.deploy`** - Deploy to GCP service
- **Parameters:** service_type, configuration, region
- **Use when:** Deploying with exact specs

**`gcp_environment.create_resource`** - Create GCP resource
- **Parameters:** resource_type, name, config
- **Use when:** Creating specific resource

**`gcp_environment.manage_service`** - Service operations
- **Parameters:** service_name, action (start/stop/restart/scale)
- **Use when:** Managing deployed services

**`gcp_environment.monitor`** - Check resource status
- **Parameters:** resource_id or resource_type
- **Use when:** Monitoring specific resources

## Brief

Google Cloud Platform management for deploying and managing cloud resources.
