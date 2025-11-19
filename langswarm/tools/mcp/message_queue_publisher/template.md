# Message Queue Publisher Tool

## Description

Publish messages to message queues and event streams for asynchronous communication and event-driven architectures.

## Instructions

This tool provides message publishing with two calling approaches:

### Intent-Based Calling (Smart Message Publishing)

Use **`message_queue_publisher`** with intent for intelligent message operations:

**Parameters:**
- `intent`: What message or event you want to publish
- `context`: Relevant details (queue/topic, priority, routing)

**When to use:**
- Publishing business events: "Send order confirmed notification"
- Broadcasting updates: "Notify all services of config change"
- Event sourcing: "Record customer registration event"

**Examples:**
- "Send order confirmation" → intent="publish order confirmation event for order #12345", context="order processing, customer notifications"
- "Broadcast system update" → intent="notify all services that maintenance will start", context="system-wide announcement"

### Direct Method Calling

**`message_queue_publisher.publish`** - Send message to queue
- **Parameters:** queue_name, message_body, priority (optional)
- **Use when:** Publishing to specific known queue

**`message_queue_publisher.publish_event`** - Publish domain event
- **Parameters:** event_type, event_data, routing_key
- **Use when:** Event sourcing or domain events

## Brief

Message queue publishing for asynchronous communication and event-driven systems.
