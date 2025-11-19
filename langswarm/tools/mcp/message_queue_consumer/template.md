# Message Queue Consumer Tool

## Description

Consume and process messages from message queues for event handling and asynchronous task processing.

## Instructions

This tool provides message consumption with two calling approaches:

### Intent-Based Calling (Smart Message Consumption)

Use **`message_queue_consumer`** with intent for intelligent message processing:

**Parameters:**
- `intent`: What messages you want to consume or check
- `context`: Relevant details (queue name, filters, processing needs)

**When to use:**
- Checking for messages: "See if there are pending orders"
- Processing events: "Handle all payment notifications"
- Queue monitoring: "Show unprocessed messages in error queue"

**Examples:**
- "Check pending orders" → intent="check for pending order messages in the queue", context="order processing"
- "Process notifications" → intent="consume and handle all pending notification messages", context="user notifications"

### Direct Method Calling

**`message_queue_consumer.consume`** - Read messages from queue
- **Parameters:** queue_name, max_messages, acknowledge (boolean)
- **Use when:** Consuming from specific queue

**`message_queue_consumer.peek`** - View messages without consuming
- **Parameters:** queue_name, count
- **Use when:** Monitoring queue contents

## Brief

Message queue consumption for event handling and asynchronous processing.
