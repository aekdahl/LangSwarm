# 🚀 LangSwarm

**LangSwarm** is a modular multi-agent framework that lets you build, orchestrate, and run intelligent workflows using LLM agents. It's designed to get you started in under 3 minutes with minimal setup.

Use YAML + Python to define structured, multi-agent logic that integrates OpenAI, LangChain, LlamaIndex, and more.

---

## ⚡️ Quickstart (3 minutes)

> 💡 Each named example (like `simple_chat`, `review_text`, or `brainstorm_ideas`) can automatically launch its preferred UI or CLI interface depending on its configuration — no extra flags or setup required.

```bash
pip install langswarm

# Run a minimal example
langswarm demo simple_chat
```

Or copy this:

```python
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader()
workflows, agents, *_ = loader.load()

executor = WorkflowExecutor(workflows, agents)
result = executor.run_workflow("my_workflow_id", user_input="Summarize this text...")
```

> ☑️ No complex setup. Just install, define YAML, and run.

---

## ✨ Why LangSwarm?

### 🧠 Multi-Agent Orchestration (Made Simple)

* True multi-agent logic: parallel execution, loops, retries
* Named step routing: pass data between agents with precision
* Async fan-out, sync chaining, and subflow support

### 🔌 Bring Your Stack

* Use OpenAI, Claude, Hugging Face, or LangChain agents
* Embed tools or functions directly as steps
* Drop in LangChain or LlamaIndex components

### 🧩 Modular by Design

* Define workflows in clean YAML
* Mix and match agents, tools, and steps
* Extend easily via Python

### 📃 Unified Logging

* Automatic step logging and tracing
* Easy debugging across agents and retries

---

## 🛠️ Installation

```bash
pip install langswarm
```

For source builds:

```bash
git clone https://github.com/your-org/langswarm.git
cd langswarm
pip install -r requirements.txt
```

Requires Python 3.10+

---

## 🧪 Example Workflow (YAML)

> 📁 This YAML structure can live inside a named folder (e.g. `examples/review_text/`), and LangSwarm will automatically run it using the appropriate interface (CLI or UI) based on that configuration.

```yaml
workflows:
  my_workflow_id:
    description: "Summarize and review articles"
    async: false
    steps:
      - id: summarize_text
        agent: summarizer
        input: |
          Please summarize the article:
          {{ context.user_input }}
        output:
          to: review_summary

      - id: review_summary
        agent: reviewer
        input: |
          Review the summary:
          {{ context.step_outputs.summarize_text }}
        output:
          to: user
```

```yaml
agents:
  - id: summarizer
    type: openai
    model: gpt-4o
    system_prompt: "You are a helpful summarizer."

  - id: reviewer
    type: langchain-openai
    model: gpt-4o-mini
    system_prompt: "You review summaries and flag missing key points."
```

> 🔍 You can specify the YAML folder using `LangSwarmConfigLoader(config_path="./my_yamls")` if your files are outside the default location.

---

## ☁️ Deployment Considerations

LangSwarm is designed to be portable and can run locally, in containers, or in the cloud.
Some use cases (e.g. caching, logging, secure API handling) may benefit from deployment on platforms like **Google Cloud Run**.

> 📆 Deployment examples and Docker/CI templates are coming soon.

---

## 🌱 Branch Strategy

We use a clean, stable Git workflow:

| Branch       | Purpose                              |
| ------------ | ------------------------------------ |
| `main`       | Acts as the master branch            |
| `deployment` | For Cloud Run deployment builds      |
| `feature/*`  | Used for new features or experiments |

> ✅ PRs go from `feature/*` to `main`, and releases come from `main` into `deployment`

---

## 🔭 Roadmap Highlights

| Feature                | Status | Notes                           |
| ---------------------- | ------ | ------------------------------- |
| Agent Registry         | ✅      | Works with OpenAI, Claude, etc. |
| YAML Workflows         | ✅      | Define complex flows in YAML    |
| LangChain / LlamaIndex | ✅      | Integrated as agents or tools   |
| Async Fan-out          | ✅      | Run agents concurrently         |
| Subflows & Loops       | ✅      | Control flow beyond chaining    |
| Visual UI              | 🔜     | Dashboard to manage agents      |
| Usage metering         | 🔜     | For hosted / SaaS agents        |

---

## 🧪 Developer Setup

Run tests:

```bash
pytest tests/
```

Regenerate requirements:

```bash
pip install pipreqs
pipreqs . --force
```

Build package:

```bash
python -m build
```

---

## 📄 License

MIT License. See `LICENSE` for full terms.

---

Built with ❤️ by the LangSwarm team.
