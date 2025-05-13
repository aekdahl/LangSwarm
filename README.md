# LangSwarm

LangSwarm is a modular multi-agent framework designed to coordinate large language model (LLM) agents in structured, goal-oriented workflows. This early-stage release offers a lightweight version focused on YAML-driven configuration, agent registration, and core workflow execution across multiple communication channels.



## 🚀 Features

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



## 🧭 Feature Map & Road Ahead

LangSwarm is designed to be modular, extensible, and transparent — and we're just getting started.

| Feature                      | Description                                                                      | Status          |
| ---------------------------- | -------------------------------------------------------------------------------- | --------------- |
| 🧠 Agent Registry            | Register and configure agents (OpenAI, Claude, Hugging Face, LangChain, custom)  | ✅ Stable        |
| 🔁 Workflow Engine           | Multi-step orchestration with fan-in/out, retries, async execution, and routing  | ✅ Stable        |
| 🧩 Subflows & Loops          | Define nested workflows, conditionals, and iterative step logic                  | ✅ Stable        |
| ⚡ Async Fan-out              | Run agents and tools in parallel using asyncio                                   | ✅ Stable        |
| 🧠 LangChain Integration     | Use LangChain agents, tools, retrievers, and chains inside workflows             | ✅ Stable        |
| 📚 LlamaIndex Integration    | Add LlamaIndex agents, RAG pipelines, and retrieval tools                        | ✅ Stable        |
| 🛠 Tool System               | Register external tools (functions, APIs, scripts) and invoke them as steps      | 🧪 Experimental  |
| 💬 Messaging Gateways        | Interface with Telegram, Slack, Discord, Twilio, Dialogflow, and more            | 🧪 Experimental  |
| 📦 Memory Adapters           | Build short- and long-term memory for agents (pluggable backends planned)        | 🧪 Experimental  |
| 🔌 Bring Your Own Components | Use your own agents, tools, retrievers, and message queues — minimal boilerplate | ✅ Stable        |
| 📬 Message Broker Layer      | Support for sync/async message brokers (internal, Redis, GCP Pub/Sub planned)    | 🧪 Experimental  |
| 🧪 Auto-Planners & Reviewers | Use LLMs to dynamically plan workflows, review outputs, or reroute steps         | 🔜 Planned       |
| 📊 Visual Dashboard (UI)     | A web-based control panel for managing workflows, agents, and logs               | 🔜 Planned       |
| 📈 Usage Metering & Billing  | Track job usage, credit balance, and enable task pricing for hosted agents       | 🔜 Planned       |
| ✍️ YAML + Python Hybrid Mode | Combine YAML definitions with inline Python for advanced workflows               | 🔜 Planned       |
| 📜 Global Logging System     | Centralized logger across all agents, tools, workflows — with debug output       | ✅ Stable        |

> 🧪 **Experimental**: These features exist in early form and are evolving.
> 🔜 **Planned**: These are on the roadmap but not yet included in this release.



## 🛠 Developer Setup
```bash
pytest tests/
```

To regenerate requirements:
```bash
pip install pipreqs
pipreqs . --force
```

To build distributions:
```bash
python -m build
```

## 📄 License
This project is licensed under the MIT License. See the LICENSE file for more details.

--

Built with ❤️ by the LangSwarm team.
