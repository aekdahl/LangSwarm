---
title: "Action Queue API"
description: "Enterprise action item management."
---

# Action Queue API

The Action Queue system provides enterprise-grade action item management using Google Cloud Pub/Sub. It automatically discovers actionable items from memory analysis and supports both pull (polling) and push (webhook) modes for consumption.

## Overview

### Key Features
- **Automatic Action Discovery**: AI-powered analysis of memories identifies actionable items
- **Google Cloud Pub/Sub Integration**: Enterprise messaging for reliable action delivery
- **Dual Consumption Modes**: Both pull (polling) and push (webhook) support
- **Intelligent Action Types**: Categorizes actions (TASK, FOLLOW_UP, RESEARCH, etc.)
- **Priority Management**: URGENT, HIGH, MEDIUM, LOW priority levels

### Action Types
- `TASK`
- `FOLLOW_UP`
- `RESEARCH`
- `MEETING`
- `COMMUNICATION`
- `DEADLINE`

## API Endpoints

### 1. Queue Action

**Endpoint:** `POST /api/v1/actions/queue`

Manually create and queue an action item.

**Request Body:**
```json
{
  "memory_id": "mem_12345",
  "action_type": "TASK",
  "priority": "HIGH",
  "title": "Prepare Q4 budget presentation",
  "description": "Create slides and gather financial data for Q4 budget review meeting",
  "due_date": "2024-01-25T14:00:00Z"
}
```

### 2. Poll Actions (Pull Mode)

**Endpoint:** `GET /api/v1/actions/poll`

Poll for queued action items.

### 3. Set Webhook URL (Push Mode)

**Endpoint:** `POST /api/v1/actions/webhook`

Configure webhook URL for push notifications.

### 4. Create Actions from Memory Recall

**Endpoint:** `POST /api/v1/actions/from-memory-recall`

Internal endpoint for automatically creating actions from memory analysis.

## Google Cloud Pub/Sub Architecture

### Topics and Subscriptions

**Action Queue Topic**: `langswarmpro-{environment}-action-queue`
- Main topic for action items
- Pull subscription for API polling
- Message retention: 7 days
- Dead letter policy: 5 retry attempts

**Webhook Notifications Topic**: `langswarmpro-{environment}-webhook-notifications`
- Push notifications to webhook URLs
- Configurable push endpoints

### Message Format

```json
{
  "data": "base64-encoded-action-json",
  "attributes": {
    "user_id": "user_12345",
    "action_type": "TASK",
    "priority": "HIGH",
    "memory_id": "mem_12345",
    "timestamp": "2024-01-22T10:30:00Z"
  }
}
```
