---
title: "LangSwarm Pro Overview"
description: "Enterprise features for LangSwarm agents."
---

# LangSwarm Pro

LangSwarm Pro is a suite of enterprise-grade services designed to enhance your LangSwarm agents with advanced capabilities:

- **Governance**: Human-in-the-loop approval workflows for sensitive actions.
- **Proactive Scheduling**: Intelligent job scheduling and recurring tasks.
- **MemoryPro**: Advanced memory management with prioritization, fading, and AI-powered insights.
- **Action Queue**: Asynchronous task discovery and execution system.

## Components

### Core Services
These services are available to all LangSwarm Pro users:

1. **Governance Engine**
   - Implements `ApprovalQueue` for managing high-stakes tool calls.
   - Provides a review interface for admins.

2. **Scheduler**
   - Managed `JobManager` for executing timed and recurring tasks.
   - Integration with the `schedule_recurring_task` tool.

### Advanced APIs
These features require the LangSwarm Pro SaaS integration:

- [MemoryPro API](/langswarm-pro/memory-pro): Enterprise memory management.
- [Action Queue API](/langswarm-pro/action-queue): Task discovery and Pub/Sub integration.
