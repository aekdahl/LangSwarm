---
id: getting-started
title: Getting Started with LangSwarm
slug: /
sidebar_label: Getting Started
sidebar_position: 0
---

# Getting Started with LangSwarm

Welcome to **LangSwarm**, a modular Python framework for orchestrating intelligent workflows across multiple AI agents. LangSwarm allows you to create, configure, and connect agents using YAML or Python, and execute workflows via local logic or external gateways like Telegram, Slack, or Twilio.

---

## ⚙️ Installation
Install from PyPI:
```bash
pip install langswarm
```

Install from source:
```bash
git clone https://github.com/your-org/langswarm.git
cd langswarm
pip install -r requirements.txt
```
Python 3.10+ recommended

For production use or custom integrations, you may also want to install platform-specific packages (e.g., openai, slack_sdk, etc.).

## 🚀 Project Structure
LangSwarm makes orchestrating intelligent workflows across AI agents simple, flexible, and scalable. Dive in and start building smarter AI systems today!

```yaml
langswarm/
├── core/        # Agent registry, config, templates, utilities
├── memory/      # Placeholder adapters and memory wrappers
├── synapse/     # Workflow engine, defaults, tool system
├── ui/          # Gateways: Slack, Telegram, Twilio, Discord, etc.
targets/         # YAML config for agents and workflows
```

## 🧱 Basic Concepts

### 🧩 1. **Simple by Design**

LangSwarm is built around clarity and minimal configuration. You can launch full multi-agent workflows using just a few YAML files. No complicated setup, no custom DSLs.

### 🔁 2. **Workflows & Orchestration**

LangSwarm's orchestration engine is its core strength.

Define intelligent, structured multi-agent workflows that go far beyond simple chaining:

* 🧠 **True multi-agent coordination**: parallel agents, fan-in/fan-out steps, and dynamic routing
* 🔁 **Subflows and loops**: support for nested logic, iterative steps, and repeated evaluation
* ⚙️ **Named output routing**: pass outputs between steps with clarity and precision
* ⏳ **Async and sync support**: fan-out to multiple agents concurrently or step through carefully
* ♻️ **Retries and await logic**: intelligent control flow that handles errors, re-tries, and wait conditions
* 🧩 **Tool and agent mix**: steps can invoke tools, agents, or other workflows seamlessly

No custom DSL, no hardcoded logic — just pure YAML orchestration that stays readable and composable.

### 🔗 3. **Plug Into Your Stack**

LangSwarm works with what you're already using:

* **LangChain**: Use LangChain agents, tools, retrievers, and chains inside LangSwarm workflows.
* **LlamaIndex**: Easily incorporate LlamaIndex retrieval pipelines as workflow steps or tool wrappers.
* **Hugging Face**: use any model (Transformer) locally or via the Hugging Face Hub

_You may also use LangSwarm components in LangChain_

### 🧠 4. **Bring Your Own Agent (BYOA)**

LangSwarm is unopinionated:

* Add your own agents using OpenAI, Claude, Hugging Face, LangChain, and more
* Register custom tools with minimal wrapper logic
* Use YAML or Python to inject external logic at any point

### 🔍 5. **Global Logging**
LangSwarm includes a global logging system that unifies output across agents, tools, workflows, and gateways. It automatically captures step context, making debugging and monitoring easier — even in distributed, multi-agent flows.

## 🧪 Usage

### 1. Define Your Agents and Workflows
Create or modify YAML configuration files:

```yaml
# workflows.yaml
workflows:
    main_workflow:
      - id: my_workflow_id
        description: |
            Summarize and review articles.
        async: false

        steps:
          - id: summarize_text
            agent: summarizer
            input: |
                  Please summarize the below article and
                  list the most important key points.

                  Article: {{ context.user_input }}
            output:
                to: review_summary

          - id: review_summary
            agent: reviewer
            input: |
                  Review the summary and make sure no key points are missed.

                  User provided article: {{ context.user_input }}
                  Summary: {{ context.step_outputs.summarize_text }}
            output:
                to: user # Exits the workflow and returns the response.

#---

# agents.yaml (seperate file)
agents:
  - id: summarizer
    type: openai
    model: gpt-4o
    system_prompt: "You are a helpful summarizer."

  - id: reviewer
    agent_type: langchain-openai
    model: gpt-4o-mini-2024-07-18
    system_prompt: |
        You are a summary reviewer.
        You are responsible to flag incorrect summaries.
```
  
### 2. Run from Python
```python
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Initialize LangSwarm loader once at start
loader = LangSwarmConfigLoader()
workflows, agents, *_ = loader.load()

# 2. Set up LangSwarm context
executor = WorkflowExecutor(workflows, agents)

# 3. Run LangSwarm workflow
result = executor.run_workflow("my_workflow_id", user_input=user_message)
```

* _Ensure the appropriate credentials or API keys are set via environment variables._
* _You can of course also use LangSwarm without workflows._
