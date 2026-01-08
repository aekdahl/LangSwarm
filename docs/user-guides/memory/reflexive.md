---
title: "Reflexive Memory (The Onion Architecture)"
description: "Dynamic few-shot learning that allows frozen agents to self-improve via feedback loops."
---

> [!WARNING]
> **Experimental Feature (Alpha)**
> This feature is currently in experimental status. The APIs described below may change.

# Overview

Reflexive Memory implements a **Dynamic Few-Shot Learning** system. It allows a "frozen" LLM to learn from feedback by dynamically updating its system prompt with relevant past lessons.

This solves the problem where fixing an agent's mistake (e.g., "Always use JSON") usually requires a code deployment. With Reflexive Memory, the agent "remembers" the correction and applies it to future similar scenarios automatically.

## The "Onion" Architecture

We effectively "peel" layers of context to build the perfect system prompt for every interaction.

1.  **Tier 1 (Global)**: Company-wide constraints (e.g., "No profanity", "Output valid JSON").
2.  **Tier 2 (Role)**: Domain-specific behavior (e.g., "Lawyer must disclaim liability").
3.  **Tier 3 (Session)**: User-specific preferences.

## Components

### 1. The Reflector (Write Path)
*   **Trigger**: Asynchronous Human Feedback (Thumbs Down).
*   **Action**: An LLM "System Architect" analyzes the failure.
*   **Decision**: Is this error a GLOBAL policy violation or a ROLE-specific one?
*   **Output**: A concise rule is stored in the Vector Database (e.g., `agent_lessons` namespace).

### 2. The Mixer (Read Path)
*   **Trigger**: Every incoming user message.
*   **Action**:
    1.  Embeds the user's query.
    2.  **Parallel Retrieval**: Fetches top matching Global rules AND top matching Role rules.
    3.  **Assembly**: Constructs a tiered System Prompt.

```text
### SYSTEM CONSTITUTION
You are an AI agent acting as: CustomerSupport

### TIER 1: GLOBAL COMMANDMENTS
1. Always format output as JSON.

### TIER 2: ROLE GUIDELINES
1. Refund policy is 30 days.
```

### 3. The Consolidator (Maintenance)
*   **Trigger**: Nightly Cron.
*   **Action**: Clusters similar rules and merges them to prevent context bloat.

## Usage (Coming Soon)

```python
from langswarm_memory.reflexive import ReflectorAgent, LessonRetriever

# 1. Teach (Async)
reflector = ReflectorAgent()
await reflector.analyze_failure(
    user_query="Refund please",
    agent_response="Sure!",
    user_correction="You must check eligibility first.",
    agent_role="support"
)

# 2. Consult (Inference)
retriever = LessonRetriever(store)
prompt = await retriever.get_system_prompt(
    user_query="I want my money back",
    current_agent_role="support"
)
```
