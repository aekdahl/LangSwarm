# LangSwarm

LangSwarm is a modular multi-agent framework designed to coordinate large language model (LLM) agents in structured, goal-oriented workflows. This early-stage release (v0.0.37) offers a lightweight version focused on YAML-driven configuration, agent registration, and core workflow execution across multiple communication channels.

---

## 🚀 Features

- 🧠 **Agent Management**: Register and instantiate agents from YAML configuration.
- 🔀 **Workflow Engine**: Fan-in and fan-out orchestration, with support for subflows and output routing.
- 🛠️ **Tooling System**: Early support for tools and step-level processing in workflows.
- 📦 **Modular Architecture**:
  - `core/`: Configuration, agent factory, workflow, utilities
  - `memory/`: Memory adapters and wrappers (stubbed for future use)
  - `synapse/`: Tools and MCP
  - `ui/`: Gateway integrations for Slack, Telegram, Discord, Twilio, and more
- 🧪 **Extensible by Design**: Clean separation of agent roles, message protocols, memory, and utilities.
- 🔌 **Multi-Channel Support**: UI gateway code includes integrations for common messaging platforms.

---

## 🗂️ Project Structure

```plaintext
langswarm/
├── core/           # Agent loading, workflow engine, registry
├── memory/         # Placeholder for memory adapters and wrappers
├── synapse/        # Tools and MCP
├── ui/             # Multi-platform gateways (Slack, Telegram, Discord, Twilio, etc.)
tests/              # Pytest-based test suite
```

## ⚙️ Installation
```bash
git clone https://github.com/your-org/langswarm.git
cd langswarm
pip install -r requirements.txt
```
Python 3.10+ recommended

## 🧪 Usage
### 1. Define Your Agents and Workflows
Create or modify YAML configuration files:

- agents.yaml
- workflows.yaml
- tools.yaml
- etc.
  
### 2. Run from Python
```python
from langswarm.core.config import load_config
from langswarm.core.factory.agents import create

# Load agents and workflow from YAML
cfg = load_config("targets/")
agents = create(cfg.agents)
```

### 3. Start a Chatbot Gateway (e.g. Telegram)
```bash
python langswarm/ui/telegram_gateway.py
Other gateways:

slack_gateway.py
discord_gateway.py
twilio_gateway.py
dialogflow.py
...

```
Ensure the appropriate credentials or API keys are set via environment variables.

## 📄 Example YAML
agents.yaml:
```yaml
agents:
  - id: summarizer
    type: openai
    model: gpt-4
    system_prompt: "You are a helpful summarizer."
```

workflows.yaml:
```yaml
workflows:
  - id: summarize_and_reply
    steps:
      - agent: summarizer
        input: user_message
        output_to: user
```

## ✅ Current Status (v0.0.37)
| Component       | Status                                 |
| --------------- | -------------------------------------- |
| Agent Registry  | ✅ Stable                               |
| YAML Support    | ✅ Complete                             |
| Workflow Engine | ✅ Fan-in/out, Routing                  |
| UI Gateways     | 🟡 Working (requires manual key setup) |
| Tools Support   | 🟡 Present but minimal                 |
| Memory Support  | 🔲 Stub only                           |
| Web Dashboard   | 🔲 Not included                        |

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

