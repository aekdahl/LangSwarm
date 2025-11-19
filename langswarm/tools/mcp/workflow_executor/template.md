# Workflow Executor Tool

## Description

Workflow automation and orchestration tool with natural language process management for running business logic, pipelines, and automated procedures.

## Instructions

This tool provides workflow execution with two calling approaches:

### Intent-Based Calling (Smart Workflow Management)

Use **`workflow_executor`** with natural language intent for intelligent workflow operations:

**Parameters:**
- `intent`: What workflow or process you want to run
- `context`: Relevant details (data sources, schedules, conditions)

**When to use:**
- Running workflows by description: "Start the data processing pipeline"
- Scheduled operations: "Run monthly report generation"
- Conditional execution: "Process pending customer onboarding"
- Complex orchestration: "Execute the backup and cleanup procedures"

**Examples:**
- "Run data processing pipeline" → intent="execute the data processing pipeline for today's customer analytics", context="daily batch processing, analytics workflow"
- "Start monthly reports" → intent="start the monthly report generation workflow", context="end of month, financial reports"

### Direct Method Calling (Specific Workflows)

**`workflow_executor.execute_workflow`** - Run a specific workflow
- **Parameters:** workflow_id, inputs (dict), wait_for_completion (boolean)
- **Use when:** Running known workflow with exact ID

**`workflow_executor.schedule_workflow`** - Schedule future execution
- **Parameters:** workflow_id, schedule_time, recurring (optional)
- **Use when:** Setting up automated runs

**`workflow_executor.monitor_execution`** - Check workflow status
- **Parameters:** execution_id
- **Use when:** Tracking running workflows

**`workflow_executor.manage_pipelines`** - Pipeline operations
- **Parameters:** action (start/stop/restart), pipeline_name
- **Use when:** Managing data pipelines

**`workflow_executor.get_status`** - Get execution details
- **Parameters:** workflow_id or execution_id
- **Use when:** Checking workflow health or results

### Decision Guide

**Use intent-based** when:
- User describes what needs to happen
- Workflow selection needed
- Complex conditions
- Multi-step processes

**Use direct methods** when:
- Known workflow ID
- Monitoring specific execution
- Scheduled operations
- Pipeline management

### Safety Features

- Workflows run in isolated environments
- Automatic rollback on failure
- Execution history and audit logs
- Resource limits and timeouts

## Brief

Workflow automation with intelligent intent processing for business process orchestration.
