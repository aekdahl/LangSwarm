#!/bin/bash
set -e

PROJECT_ID="langswarm-pro-prod"
TOPIC_NAME="langswarmpro-prod-action-queue"
SUB_NAME="langswarmpro-prod-action-queue-sub"

echo "Setting up Pub/Sub for $PROJECT_ID..."

# Create Topic if it doesn't exist
if ! gcloud pubsub topics describe $TOPIC_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "Creating topic $TOPIC_NAME..."
    gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID
else
    echo "Topic $TOPIC_NAME already exists."
fi

# Create Subscription if it doesn't exist
if ! gcloud pubsub subscriptions describe $SUB_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "Creating subscription $SUB_NAME..."
    gcloud pubsub subscriptions create $SUB_NAME \
        --topic=$TOPIC_NAME \
        --project=$PROJECT_ID \
        --ack-deadline=60 \
        --message-retention-duration=7d
else
    echo "Subscription $SUB_NAME already exists."
fi

echo "Pub/Sub setup complete!"
