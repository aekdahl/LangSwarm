# Daytona Environment Tool

## Description

Daytona development environment management for creating, configuring, and managing cloud development environments.

## Instructions

This tool provides Daytona operations with two calling approaches:

### Intent-Based Calling (Smart Environment Management)

Use **`daytona_environment`** with intent for intelligent environment operations:

**Parameters:**
- `intent`: What environment operation you need
- `context`: Relevant details (project, configuration, resources)

**When to use:**
- Creating environments: "Set up a Python development environment"
- Managing instances: "Start my Node.js workspace"
- Configuration: "Configure environment for React development"

**Examples:**
- "Create Python dev environment" → intent="create a Python development environment with Django", context="web development, database needed"
- "Start workspace" → intent="start my existing Node.js development workspace", context="project xyz, continue work"

### Direct Method Calling

**`daytona_environment.create`** - Create new environment
- **Parameters:** template, name, resources
- **Use when:** Creating with specific configuration

**`daytona_environment.start`** - Start environment
- **Parameters:** environment_id
- **Use when:** Starting known environment

**`daytona_environment.stop`** - Stop environment
- **Parameters:** environment_id
- **Use when:** Stopping specific environment

**`daytona_environment.configure`** - Update configuration
- **Parameters:** environment_id, config_updates
- **Use when:** Modifying environment settings

## Brief

Daytona development environment management for cloud-based coding workspaces.
