# ToDo: Add field validation!

import os
import ast
import sys
import time
import json
import yaml
import socket
import asyncio
import inspect
import tempfile
import importlib
import subprocess
import nest_asyncio
from pathlib import Path
from jinja2 import Template
from cerberus import Validator
from simpleeval import SimpleEval
from inspect import signature, Parameter
from typing import Dict, List, Optional, Union, Any

# @v0.0.1
from langswarm.core.factory.agents import AgentFactory
from langswarm.core.utils.workflows.intelligence import WorkflowIntelligence

# @v... Later...

#from langswarm.memory.adapters.langswarm import ChromaDBAdapter
#from langswarm.cortex.plugins.process_toolkit import ProcessToolkit

#from langswarm.cortex.react.agent import ReActAgent
#from langswarm.core.defaults.prompts.system import FormatParseableJSON

#from langswarm.synapse.tools.github.main import GitHubTool,ToolSettings
#from langswarm.synapse.tools.files.main import FilesystemTool
#from langswarm.synapse.tools.tasklist.main import TaskListTool


try:
    from langswarm.cortex.registry.plugins import PluginRegistry
except ImportError:
    PluginRegistry = {}

try:
    from langswarm.synapse.registry.tools import ToolRegistry
except ImportError:
    ToolRegistry = {}

try:
    from langswarm.memory.registry.rags import RAGRegistry
except ImportError:
    RAGRegistry = {}
    

LS_DEFAULT_CONFIG_FILES = [
    "agents.yaml", "tools.yaml", "retrievers.yaml", "plugins.yaml",
    "registries.yaml", "workflows.yaml", "secrets.yaml", "brokers.yaml"
]

LS_SCHEMAS = {
    "agents": {
        "id": {"type": "string", "required": True},
        "agent_type": {"type": "string", "required": True},
        "model": {"type": "string", "required": True},
        "system_prompt": {"type": "string"},
    },
    "tools": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "retrievers": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "plugins": {
        "id": {"type": "string", "required": True},
        "type": {"type": "string", "required": True},
        "settings": {"type": "dict"},
    },
    "workflows": {
        "id": {"type": "string", "required": True},
        "steps": {"type": "list", "required": True},
    },
}

class LangSwarmConfigLoader:
    def __init__(self, config_path="."):
        self.config_path = config_path
        self.config_data = {}
        self.agents = {}
        self.retrievers = {}
        self.tools = {}
        self.plugins = {}
        self.brokers = {}
        # this will hold type_name → class mappings
        self.tool_classes: Dict[str, type] = {}
        self._load_builtin_tool_classes()

    def _load_builtin_tool_classes(self):
        # populate with whatever core tools you know about
        ##from langswarm.mcp.tools.mcpgithubtool.main import MCPGitHubTool
        #from langswarm.synapse.tools.files.main  import FilesystemTool
        # …etc…
        self.tool_classes = {
            ##"mcpgithubtool":   MCPGitHubTool,
        #    "filesystemtool": FilesystemTool,
        #    # add more here (or via register_tool_class below)
        }
        pass

    def register_tool_class(self, _type: str, cls: type):
        """Allow adding new tool classes at runtime."""
        self.tool_classes[_type.lower()] = cls

    def load(self):
        self._load_secrets()
        self._load_config_files()
        self._initialize_brokers()
        self._initialize_retrievers()
        self._initialize_tools()
        self._initialize_plugins()
        self._initialize_agents()
        return self.config_data.get('workflows', {}), self.agents, self.brokers, self.config_data.get('tools', [])

    def _load_secrets(self):
        secrets_path = os.path.join(self.config_path, "secrets.yaml")
        secrets_dict = yaml.safe_load(open(secrets_path)) if os.path.exists(secrets_path) else {}
        yaml.SafeLoader.add_constructor("!secret", self._make_secret_constructor(secrets_dict))

    def _initialize_brokers(self):
        for broker in self.config_data.get("brokers", []):
            if broker["type"] in ["internal", "local"]:
                self.brokers[broker["id"]] = InternalQueueBroker()
            elif broker["type"] == "redis":
                self.brokers[broker["id"]] = RedisMessageBroker(**broker.get("settings", {}))
            elif broker["type"] == "gcp":
                self.brokers[broker["id"]] = GCPMessageBroker(**broker.get("settings", {}))

    def _make_secret_constructor(self, secrets_dict):
        def secret_constructor(loader, node):
            secret_key = loader.construct_scalar(node)
            return secrets_dict.get(secret_key, os.getenv(secret_key, f"<missing:{secret_key}>"))
        return secret_constructor

    def _load_config_files(self):
        for filename in LS_DEFAULT_CONFIG_FILES:
            full_path = os.path.join(self.config_path, filename)
            if os.path.exists(full_path):
                key = filename.replace(".yaml", "")
                self.config_data[key] = self._load_yaml_file(full_path).get(key, {})
                self._validate_yaml_section(key, self.config_data[key])

    def _validate_yaml_section(self, section, entries):
        schema = LS_SCHEMAS.get(section.rstrip("s"))
        if not schema:
            return
        validator = Validator(schema)
        for entry in entries:
            if not validator.validate(entry):
                print(f"❌ Validation failed in section '{section}': {validator.errors}")

    def _load_yaml_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file) or {}

        # 1) resolve any env:FOO → os.getenv("FOO")
        self._resolve_env_vars(data)

        # 2) then pull in any prompt‑file references
        self._resolve_prompts(data, os.path.dirname(filepath))

        return data

    def _resolve_prompts(self, obj, base_path):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str) and ("prompt" in k or "instruction" in k or "description" in k) and v.endswith((".md", ".txt")):
                    file_path = os.path.join(base_path, v)
                    if os.path.isfile(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            obj[k.replace('_file', '')] = f.read()
                            del obj[k]
                elif isinstance(v, list) and ("prompt" in k or "instruction" in k or "description" in k) and all(isinstance(item, str) and item.endswith((".md", ".txt")) for item in v):
                    # 🌟 New: Handle list of prompt files
                    contents = []
                    for item in v:
                        file_path = os.path.join(base_path, item)
                        if os.path.isfile(file_path):
                            with open(file_path, "r", encoding="utf-8") as f:
                                contents.append(f.read())
                    combined = '\n\n---\n\n'.join(contents)
                    obj[k.replace('_file', '')] = combined
                    del obj[k]
                else:
                    self._resolve_prompts(v, base_path)
        elif isinstance(obj, list):
            for item in obj:
                self._resolve_prompts(item, base_path)

    def _resolve_env_vars(self, obj):
        """
        Recursively walk a loaded YAML structure and:
         • replace any string "env:FOO" with os.getenv("FOO", "")  
         • replace any string "setenv:BAR" by setting os.environ[key]=BAR
           where `key` is the dict key, and then obj[key] = BAR.
        """
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str):
                    if v.startswith("env:"):
                        env_key = v.split("env:", 1)[1]
                        obj[k] = os.getenv(env_key, "")
                    elif v.startswith("setenv:"):
                        val = v.split("setenv:", 1)[1]
                        # 1) set the environment variable
                        os.environ[k] = val
                        # 2) replace in our config dict
                        obj[k] = val
                    else:
                        # recurse into nested dict or list
                        # (only if it's neither env: nor setenv:)
                        continue  # leave other strings alone
                else:
                    # recurse into non‑string values
                    self._resolve_env_vars(v)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item.startswith("env:"):
                    env_key = item.split("env:", 1)[1]
                    obj[i] = os.getenv(env_key, "")
                elif isinstance(item, str) and item.startswith("setenv:"):
                    # lists have no “key” name, so we can’t set
                    # os.environ[name] here — skip or log:
                    val = item.split("setenv:", 1)[1]
                    obj[i] = val
                else:
                    self._resolve_env_vars(item)
    
    def _initialize_retrievers(self):
        for retriever in self.config_data.get("retrievers", []):
            self.retrievers[retriever["id"]] = self._initialize_component(retriever, ChromaDBAdapter)
        
    def _initialize_tools(self):
        self.tool_metadata = {}  # New dict for storing metadata explicitly
        for tool_cfg in self.config_data.get("tools", []):
            ttype = tool_cfg.get("type", "unknown").lower()

            # 1) see if user explicitly pointed at a class path
            if "class" in tool_cfg:
                module_path, class_name = tool_cfg["class"].rsplit(".", 1)
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)

            # 2) otherwise fall back to our registry
            else:
                cls = self.tool_classes.get(ttype)

            if not cls:
                print(f"⚠️  Unknown tool type '{ttype}', skipping initialization.")
                continue

            # build the instance
            self.tools[tool_cfg["id"]] = self._initialize_component(tool_cfg, cls)
    
            # explicitly store metadata
            if "metadata" in tool_cfg:
                self.tool_metadata[tool_cfg["id"]] = tool_cfg["metadata"]

    def _initialize_plugins(self):
        for plugin in self.config_data.get("plugins", []):
            if plugin["type"].lower() == "processtoolkit":
                self.plugins[plugin["id"]] = self._initialize_component(plugin, ProcessToolkit)

    def _initialize_component(self, config, cls):
        config_args = {"identifier": config["id"], "name": config["type"], **config.get("settings", {})}
        return self._call_with_valid_args(cls, config_args)

    def _call_with_valid_args(self, func, config):
        sig = signature(func)
        valid_params = sig.parameters
        accepts_kwargs = any(p.kind == Parameter.VAR_KEYWORD for p in valid_params.values())
        filtered_args = {k: v for k, v in config.items() if k in valid_params}
        extra_kwargs = {k: v for k, v in config.items() if k not in valid_params}
        return func(**filtered_args, **extra_kwargs) if accepts_kwargs else func(**filtered_args)

    def _initialize_agents(self):
        for agent in self.config_data.get("agents", []):
            agent_type = agent.get("register_as", "agent")
            agent = self._assign_registries(agent)
            agent = self._setup_memory(agent)
            agent["system_prompt"] = self._render_system_prompt(agent)

            creator = getattr(AgentFactory, f"create_{agent_type}", AgentFactory.create)
            self.agents[agent["id"]] = self._call_with_valid_args(creator, {"name": agent["id"], **agent})

    def _assign_registries(self, agent):
        if "retrievers" in agent:
            reg = RAGRegistry()
            for _id in agent["retrievers"]:
                reg.register_rag(self.retrievers[_id.lower()])
            agent["rag_registry"] = reg
        if "tools" in agent:
            reg = ToolRegistry()
            for _id in agent["tools"]:
                reg.register_tool(self.tools[_id.lower()])
            agent["tool_registry"] = reg
        if "plugins" in agent:
            reg = PluginRegistry()
            for _id in agent["plugins"]:
                reg.register_plugin(self.plugins[_id.lower()])
            agent["plugin_registry"] = reg
        return agent

    def _setup_memory(self, agent):
        if "memory_adapter" in agent:
            agent["memory_adapter"] = self.retrievers.get(agent["memory_adapter"])
        if "memory_summary_adapter" in agent:
            agent["memory_summary_adapter"] = self.retrievers.get(agent["memory_summary_adapter"])
        return agent

    def _render_system_prompt(self, agent):
        template_path = 'templates/system_prompt_template.md'
        if not os.path.exists(template_path):
            return agent.get("system_prompt", "")

        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = Template(template_str)
        def _lookup_many(ids, source):
            return [
                {"id": _id, "description": src.get("description", ""), "instruction": src.get("instruction", "")}
                for _id in ids if (_id in source and (src := source[_id]))
            ]

        return template.render(
            system_prompt=agent.get("system_prompt"),
            retrievers=_lookup_many(agent.get("retrievers", []), self.retrievers),
            tools=_lookup_many(agent.get("tools", []), self.tools),
            plugins=_lookup_many(agent.get("plugins", []), self.plugins)
        )


class WorkflowExecutor:
    def __init__(self, workflows: Dict, agents: Dict):
        self.workflows = workflows
        self.agents = agents
        self.context = {
            'step_outputs': {},
            'visited_steps': set(),
            'retry_counters': {},
            'rollback_counters': {},
            'pending_fanins': {}  # 👈 must be initialized!
        }

    def _run_workflow_inner(self, workflow_id: str, user_input: str):
        workflow = self._get_workflow(workflow_id)
        self.context['user_input'] = user_input
        self.context['previous_output'] = user_input
        self.context['request_id'] = f"req_{os.urandom(4).hex()}"
        self.context["current_workflow_id"] = workflow_id
        self.context['pending_fanins'] = {}  # fan_key → set of step_ids
        self.context['completed_fanouts'] = set()  # Tracks completed fan-out steps

        first_step = workflow.get("steps", [])[0]
        return first_step

    @WorkflowIntelligence.track_workflow
    def run_workflow(self, workflow_id: str, user_input: str, tool_deployer = None):
        """Entry‑point that works BOTH in a normal script and in a notebook."""
        self.context['tool_deployer'] = tool_deployer # Used in MCP flows
        wf = self._get_workflow(workflow_id)
        is_async = wf.get("async", False)

        if not is_async:                       # ◀── sync workflow – nothing fancy
            # 1) initialize and get the very first step
            first = self._run_workflow_inner(workflow_id, user_input)
            # 2) actually execute it
            self._execute_step(first)
            # 3) return whatever ended up as the “user” output or last output
            return self.context.get("user_output", self.context.get("previous_output"))

        # ---------- async path ----------
        coro = self.run_workflow_async(workflow_id, user_input)

        try:                                   # 1️⃣ regular python process
            return asyncio.run(coro)
        except RuntimeError as re:             # 2️⃣ already running loop (Jupyter)
            if "cannot be called from a running event loop" not in str(re):
                raise
            print("⏳ Detected running event loop — using nest_asyncio fallback")
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            if inspect.iscoroutine(coro):
                return loop.run_until_complete(coro)
            return coro                        # defensive – shouldn’t happen

    async def run_workflow_async(self, workflow_id: str, user_input: str):
        first_step = self._run_workflow_inner(workflow_id, user_input) 
        await self._execute_step_async(first_step)
        return self.context.get("user_output", self.context.get("previous_output"))

    def _get_visit_key(self, step: Dict) -> str:
        fan_key = step.get("fan_key", "default")
        request_id = self.context.get("request_id", "")
        return f"{step['id']}@{fan_key}:{request_id}"

    def _resolve_condition_branch(self, condition: dict) -> Optional[Any]:
        if not isinstance(condition, dict) or "if" not in condition:
            return None
        if self._evaluate_condition(condition["if"]):
            return condition.get("then")
        else:
            return condition.get("else")
    
    def _recheck_pending_fanins(self):
        # ▶ First: figure out which fan‑in steps are now ready
        ready_to_run = []  # list of tuples (fan_key, fanin_id, fanin_step)
        for fan_key, fanin_ids in list(self.context['pending_fanins'].items()):
            for fanin_id in list(fanin_ids):
                fanin_step = self._get_step_by_id(fanin_id)

                if not fanin_step.get("is_fan_in"):
                    continue

                required = fanin_step.get("args", {}).get("steps")
                if required is None:
                    # user forgot to declare any .args.steps
                    continue
                if not isinstance(required, list) or not required:
                    continue

                missing = [s for s in required if s not in self.context['step_outputs']]
                if missing:
                    # still waiting
                    continue

                # all done → schedule it
                ready_to_run.append((fan_key, fanin_id, fanin_step))

        # ▶ Now actually fire them (after finishing the scan)
        for fan_key, fanin_id, fanin_step in ready_to_run:
            print(f"✅ Fan‑in '{fanin_id}' ready (key={fan_key}); executing now")
            # remove from pending BEFORE we execute, so it can't re‑queue itself
            self.context['pending_fanins'][fan_key].discard(fanin_id)
            if not self.context['pending_fanins'][fan_key]:
                self.context['pending_fanins'].pop(fan_key, None)

            # and only _then_ execute:
            self._execute_step(fanin_step)

    async def _recheck_pending_fanins_async(self):
        ready_to_run = []
        for fan_key, fanin_ids in list(self.context['pending_fanins'].items()):
            for fanin_id in list(fanin_ids):
                fanin_step = self._get_step_by_id(fanin_id)
                if not fanin_step.get("is_fan_in"):
                    continue

                required = fanin_step.get("args", {}).get("steps")
                if required is None or not isinstance(required, list) or not required:
                    continue

                missing = [s for s in required if s not in self.context['step_outputs']]
                if missing:
                    continue

                ready_to_run.append((fan_key, fanin_id, fanin_step))

        for fan_key, fanin_id, fanin_step in ready_to_run:
            print(f"✅ (async) Fan‑in '{fanin_id}' ready (key={fan_key}); executing now")
            self.context['pending_fanins'][fan_key].discard(fanin_id)
            if not self.context['pending_fanins'][fan_key]:
                self.context['pending_fanins'].pop(fan_key, None)

            await self._execute_step_async(fanin_step)


    def _handle_step_error(self, step: Dict, step_id: str, visit_key: str, error: Exception):
        print(f"❌ Error in step {step_id}: {error}")

        if step.get("retry"):
            retries = self.context["retry_counters"].get(visit_key, 0)
            if retries < step["retry"]:
                print(f"🔄 Retrying step {step_id} (attempt {retries + 1})")
                self.context["retry_counters"][visit_key] = retries + 1
                return self._execute_step(step, mark_visited=False)
            else:
                print(f"⚠️ Retry limit reached for {step_id}")

        if step.get("rollback_to"):
            rollbacks = self.context["rollback_counters"].get(visit_key, 0)
            rollback_limit = step.get("rollback_limit", 1)
            if rollbacks < rollback_limit:
                rollback_step = step["rollback_to"]
                print(f"🔙 Rolling back from {step_id} to {rollback_step} (attempt {rollbacks + 1})")
                self.context["rollback_counters"][visit_key] = rollbacks + 1
                return self._execute_by_step_id(rollback_step, mark_visited=False)
            else:
                print(f"⚠️ Rollback limit reached for {step_id}")

        raise error
        
    # The core loop runner:
    def _run_loop_iteration(self, loop_id, step):
        state = self.context["loops"][loop_id]
        idx   = state["index"]
        var   = step["loop"].get("var", "item")

        # Done?
        if idx >= len(state["values"]) or idx >= state["max"]:
            # collect results into step_outputs
            self.context["step_outputs"][loop_id] = state["results"]
            return self._handle_output(
                loop_id,
                {"collect": step["output"]["collect"], "to": step["output"]["to"]},
                state["results"],
                step
            )

        # bind the next element
        self.context[var] = state["values"][idx]

        # run the body step
        body_step = self._get_step_by_id(step["loop"]["body"])
        self._execute_step(body_step)

        # capture its output and advance
        state["results"].append(self.context["step_outputs"][body_step["id"]])
        state["index"] += 1

        # and recurse
        return self._run_loop_iteration(loop_id, step)

    # New helper to kick off a loop:
    def _start_loop(self, step):
        loop = step["loop"]
        values = self._resolve_input(loop["for_each"])
        var    = loop.get("var", "item")
        max_i  = int(self._resolve_input(loop.get("max", len(values))))

        # Initialize loop state
        self.context.setdefault("loops", {})[step["id"]] = {
            "values": values, "index": 0, "max": max_i, "results": []
        }
        return self._run_loop_iteration(step["id"], step)

    def _build_no_mcp_system_prompt(self, tools_metadata: dict):
        prompt = "You are the Tool Selector. When you know which function to call, return exactly:\n\n"
        prompt += '{ "name": "<function_name>", "args": { /* function args */ } }\n\n'
        prompt += "Available functions:\n\n"
    
        for tid, meta in tools_metadata.items():
            prompt += f"- **{tid}**: {meta['description']}\n"
            prompt += json.dumps(meta['parameters'], indent=2)
            prompt += "\n\n"
    
        return prompt

    def _execute_step(self, step: Dict, mark_visited=True):
        return self._execute_step_inner_sync(step, mark_visited)

    async def _execute_step_async(self, step: Dict, mark_visited=True):
        return await self._execute_step_inner_async(step, mark_visited)

    @WorkflowIntelligence.track_step
    def _execute_step_inner_sync(self, step: Dict, mark_visited: bool = True):
        if not step:
            return
    
        step_id   = step['id']
        visit_key = self._get_visit_key(step)
        print(f"\n▶ Executing step: {step_id} (visit_key={visit_key}) (async=False)")
    
        if visit_key in self.context["visited_steps"]:
            if step.get("retry") and self.context["retry_counters"].get(visit_key, 0) < step["retry"]:
                print(f"🔁 Step {step_id} retry allowed.")
            else:
                print(f"🔁 Step {step_id} already done, skipping.")
                return
    
        if "loop" in step:
            return self._start_loop(step)
    
        if 'invoke_workflow' in step:
            wf_id = step['invoke_workflow']
            inp = self._resolve_input(step.get("input"))
            output = self.run_workflow(wf_id, inp)
        elif 'no_mcp' in step:
            tools_to_use = step['no_mcp']['tools']
            tools_metadata = {tid: self.tools_metadata[tid] for tid in tools_to_use}
        
            system_prompt = self._build_no_mcp_system_prompt(tools_metadata)
        
            # run agent chat
            agent = self.agents[step['agent']]
            agent_input = self._resolve_input(step.get("input"))
            response = agent.chat(agent_input, system_prompt=system_prompt)
        
            # parse and dispatch automatically
            payload = json.loads(response)
            tool_name = payload['name']
            args = payload.get('args', {})
        
            if tool_name in self.tools:
                function = self.tools[tool_name]  # this is the initialized tool instance
                result = function(**args)
            else:
                raise ValueError(f"Unknown tool selected by agent: {tool_name}")
        
            self.context['previous_output'] = result
            self.context['step_outputs'][step['id']] = result
        
            if "output" in step:
                self._handle_output(step['id'], step["output"], result, step)
        
            if mark_visited:
                visit_key = self._get_visit_key(step)
                self.context["visited_steps"].add(visit_key)
        
            return  # explicitly done here
        else:
            try:
                if 'agent' in step:
                    agent = self.agents[step['agent']]
                    raw_input = step.get("input")
                    if isinstance(raw_input, dict):
                        resolved = {k: self._resolve_input(v) for k, v in raw_input.items()}
                        output = agent.chat(f"{resolved}")
                    else:
                        output = agent.chat(self._resolve_input(raw_input))
    
                elif 'function' in step:
                    func = self._resolve_function(step['function'], script=step.get('script'))
                    args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
                    args.setdefault("context", self.context)
                    output = func(**args)
    
                    if output == "__NOT_READY__":
                        fan_key = step.get("fan_key", "default")
                        self.context["pending_fanins"][f"{step_id}@{fan_key}"] = step
                        return
                else:
                    raise ValueError(f"⚠️ Step {step_id} missing 'agent' or 'function'")
    
            except Exception as e:
                self._handle_step_error(step, step_id, visit_key, e)
    
        # Explicitly store outputs regardless of conditional steps:
        self.context['previous_output'] = output
        self.context['step_outputs'][step_id] = output
    
        if "output" in step:
            to_targets = step["output"].get("to", [])
            if not isinstance(to_targets, list):
                to_targets = [to_targets]
    
            if any(isinstance(t, dict) and "condition" in t for t in to_targets):
                self._handle_output(step_id, step["output"], output, step)
                if mark_visited:
                    self.context["visited_steps"].add(visit_key)
                return  # Important: return here explicitly after handling condition
            else:
                self._handle_output(step_id, step["output"], output, step)
    
        if mark_visited:
            self.context["visited_steps"].add(visit_key)
    
        if step.get("fan_key"):
            self._recheck_pending_fanins()

    @WorkflowIntelligence.track_step
    async def _execute_step_inner_async(self, step: Dict, mark_visited: bool = True):
        if not step:
            return
    
        step_id   = step['id']
        visit_key = self._get_visit_key(step)
        print(f"\n▶ Executing step: {step_id} (visit_key={visit_key}) (async=True)")
    
        if visit_key in self.context["visited_steps"]:
            if step.get("retry") and self.context["retry_counters"].get(visit_key, 0) < step["retry"]:
                print(f"🔁 Step {step_id} retry allowed.")
            else:
                print(f"🔁 Step {step_id} already done, skipping.")
                return
    
        if 'invoke_workflow' in step:
            wf_id = step['invoke_workflow']
            inp   = self._resolve_input(step.get("input"))
            output = await self.run_workflow_async(wf_id, inp)
        elif 'no_mcp' in step:
            tools_to_use = step['no_mcp']['tools']
            tools_metadata = {tid: self.tools_metadata[tid] for tid in tools_to_use}
        
            system_prompt = self._build_no_mcp_system_prompt(tools_metadata)
        
            # run agent chat
            agent = self.agents[step['agent']]
            agent_input = self._resolve_input(step.get("input"))
            response = agent.chat(agent_input, system_prompt=system_prompt)
        
            # parse and dispatch automatically
            payload = json.loads(response)
            tool_name = payload['name']
            args = payload.get('args', {})
        
            if tool_name in self.tools:
                function = self.tools[tool_name]  # this is the initialized tool instance
                result = function(**args)
            else:
                raise ValueError(f"Unknown tool selected by agent: {tool_name}")
        
            self.context['previous_output'] = result
            self.context['step_outputs'][step['id']] = result
        
            if "output" in step:
                self._handle_output(step['id'], step["output"], result, step)
        
            if mark_visited:
                visit_key = self._get_visit_key(step)
                self.context["visited_steps"].add(visit_key)
        
            return  # explicitly done here
        else:
            try:
                if 'agent' in step:
                    agent = self.agents[step['agent']]
                    raw_input = step.get("input")
                    if isinstance(raw_input, dict):
                        resolved = {k: self._resolve_input(v) for k, v in raw_input.items()}
                        output = agent.chat(f"{resolved}")
                    else:
                        output = agent.chat(self._resolve_input(raw_input))
    
                elif 'function' in step:
                    func = self._resolve_function(step['function'], script=step.get('script'))
                    args = {k: self._resolve_input(v) for k, v in step.get("args", {}).items()}
                    args.setdefault("context", self.context)
                    if asyncio.iscoroutinefunction(func):
                        output = await func(**args)
                    else:
                        output = func(**args)
    
                    if output == "__NOT_READY__":
                        fan_key = step.get("fan_key", "default")
                        self.context["pending_fanins"][f"{step_id}@{fan_key}"] = step
                        return
                else:
                    raise ValueError(f"⚠️ Step {step_id} missing 'agent' or 'function'")
    
            except Exception as e:
                self._handle_step_error(step, step_id, visit_key, e)
    
        # Explicitly store outputs regardless of conditional steps:
        self.context['previous_output'] = output
        self.context['step_outputs'][step_id] = output
    
        if "output" in step:
            to_targets = step["output"].get("to", [])
            if not isinstance(to_targets, list):
                to_targets = [to_targets]
    
            if any(isinstance(t, dict) and "condition" in t for t in to_targets):
                await self._handle_output_async(step_id, step["output"], output, step)
                if mark_visited:
                    self.context["visited_steps"].add(visit_key)
                return  # Important: return here explicitly after handling condition
            else:
                await self._handle_output_async(step_id, step["output"], output, step)
    
        if mark_visited:
            self.context["visited_steps"].add(visit_key)
    
        if step.get("fan_key"):
            await self._recheck_pending_fanins_async()


    def _handle_output(
        self,
        step_id: str,
        output_def: Dict,
        output: str,
        step: Optional[Dict] = None,
    ) -> None:
        """
        Route the `output` of *step_id* to the targets declared in its YAML.

        • Strings in `to:` are interpreted as step‑ids or the literal `"user"`.
        • Dict targets (`{"step": …}`, `{"condition": …}` …) are handled too.
        • If the target step is a **fan‑in** (marked `is_fan_in = True`) we only
          queue it in `context["pending_fanins"][fan_key]`; it will be executed by
          the periodic re‑check once *all* required fan‑out steps complete.
        """

        print("output_def:", output_def)
        targets = output_def.get("to", [])
        if not isinstance(targets, list):
            targets = [targets]

        print(f"\n🗣  Step “{step_id}” produced output:\n{output}\n")

        fan_key = step.get("fan_key") if step else None

        for target in targets:
            # ────────────────────────────────────────────────────────────────
            # 1️⃣ target supplied as **plain string**
            # ────────────────────────────────────────────────────────────────
            if isinstance(target, str):

                # 1a. send to user ----------------------------------------------------------------
                if target == "user":
                    # ── keep whichever branch you already use ───────────
                    if hasattr(self, "message_broker") and self.message_broker:
                        self.message_broker.return_to_user(
                            output,
                            context={"step_id": step_id,
                                     "request_id": self.context.get("request_id")},
                        )
                    else:                                                # ← fallback
                        self.context["user_output"] = output
                    print("💬  Output was returned to user\n")
                    continue  # nothing else to do for the “user” pseudo‑step

                # 1b. normal step‑id ----------------------------------------------------------------
                    
                print("target:", target)
                target_step = self._get_step_by_id(target)

                # If it’s a fan‑in we just queue it
                if fan_key and target_step.get("is_fan_in"):
                    self.context["pending_fanins"].setdefault(fan_key, set()).add(
                        target_step["id"]
                    )
                    continue
                    
                print("target_step:", target_step)

                # otherwise execute immediately
                self._execute_step(target_step)
                continue  # ----- next target --------------------------------------

            # ────────────────────────────────────────────────────────────────
            # 2️⃣ target supplied as **dict**
            # ────────────────────────────────────────────────────────────────
            if isinstance(target, dict):

                # 2a. {"step": …}
                if "step" in target:
                    target_step = self._get_step_by_id(target["step"])

                    if fan_key and target_step.get("is_fan_in"):
                        self.context["pending_fanins"].setdefault(fan_key, set()).add(
                            target_step["id"]
                        )
                    else:
                        self._execute_step(target_step)

                # 2b. {"invoke": subflow_id}
                elif "invoke" in target:
                    self._run_subflow(
                        subflow_id=target["invoke"],
                        input_text=output,
                        await_response=target.get("await", False),
                    )

                # 2c. {"condition": {...}}
                elif isinstance(target, dict) and "condition" in target:
                    branch = self._resolve_condition_branch(target.get("condition"))
                    if branch:
                        if isinstance(branch, str):
                            # It's a direct step id → load and execute
                            target_step = self._get_step_by_id(branch)
                            self._execute_step(target_step)
                        elif isinstance(branch, dict):
                            # It's a nested output → treat it as another output instruction
                            self._handle_output(step_id, {"to": branch}, output, step)
                    
                    # ✅ VERY IMPORTANT
                    return  # STOP here — don't fall through and save 'True/False' as output

                # 2d. {"generate_steps": ...}
                elif "generate_steps" in target:
                    self._run_generated_subflow(
                        input_text=output,
                        limit=target.get("limit"),
                        return_to=target.get("return_to"),
                    )

    async def _handle_output_async(self, step_id, output_def, output, step):
        targets = output_def.get("to", [])
        if not isinstance(targets, list):
            targets = [targets]

        fan_key = step.get("fan_key")
        tasks = []
        
        # -----------------------------------------------------------
        # inside async _handle_output_async()
        # -----------------------------------------------------------
        for target in targets:

            # ─────────── target is a plain string id ───────────
            if isinstance(target, str):
                if target == "user":
                    if hasattr(self, "message_broker") and self.message_broker:
                        self.message_broker.return_to_user(
                            output,
                            context={"step_id": step_id,
                                     "request_id": self.context.get("request_id")}
                        )
                    else:
                        self.context["user_output"] = output
                    print("\n💬 Output was returned to user")
                    continue

                # normal “step id”
                target_step = self._get_step_by_id(target)
                if fan_key:
                    target_step["fan_key"] = fan_key
                    #  🆕  Only register fan‑in steps – do NOT schedule them here
                    if target_step.get("is_fan_in"):
                        self.context["pending_fanins"].setdefault(fan_key, set()).add(target_step["id"])
                        continue                # <-- do NOT add to tasks
                
                tasks.append(self._execute_step_async(target_step))

            # ─────────── target is a mapping (dict) ───────────
            elif isinstance(target, dict):
                if "step" in target:
                    target_step = self._get_step_by_id(target["step"])
                    if fan_key:
                        target_step["fan_key"] = fan_key
                        if target_step.get("is_fan_in"):
                            self.context["pending_fanins"].setdefault(fan_key, set()).add(target_step["id"])
                            continue                # <-- do NOT add to tasks
                    
                    tasks.append(self._execute_step_async(target_step))

                elif "invoke" in target:
                    await self._run_subflow_async(target['invoke'], output, await_response=target.get("await", False))

                elif isinstance(target, dict) and "condition" in target:
                    branch = self._resolve_condition_branch(target.get("condition"))
                    if branch:
                        if isinstance(branch, str):
                            target_step = self._get_step_by_id(branch)
                            await self._execute_step_async(target_step)
                        elif isinstance(branch, dict):
                            await self._handle_output_async(step_id, {"to": branch}, output, step)
    
                    # ✅ VERY IMPORTANT
                    return  # STOP here — don't fall through and save 'True/False' as output

                elif "generate_steps" in target:
                    await self._run_generated_subflow_async(output, limit=target.get("limit"), return_to=target.get("return_to"))

        # 🚀 Run all async fan-out tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)

    def _get_step_by_id(self, step_id: str) -> Dict:
        step = next((s for s in self._get_workflow(self.context["current_workflow_id"])["steps"] if s["id"] == step_id), None)
        if not step:
            raise ValueError(f"Workflow step '{step_id}' not found in current workflow.")
        return step
    
    def _execute_by_step_id(self, step_id: str, await_response: bool = True, mark_visited: bool = True, fan_key: Optional[str] = None):
        step = self._get_step_by_id(step_id)
        if step:
            self._execute_step(step, mark_visited=mark_visited, fan_key=fan_key)

    def _run_subflow(self, subflow_id: str, input_text: str, await_response: bool = True):
        subflow = next((s for s in self.workflows.get("subflows", []) if s['id'] == subflow_id), None)
        if not subflow:
            print(f"⚠️ Subflow {subflow_id} not found.")
            return

        func = self._resolve_function(subflow['entrypoint'])
        mapped_input = {
            k: self._resolve_input(v) for k, v in subflow.get("input_map", {}).items()
        }
        result = func(**mapped_input)

        if await_response and subflow.get("return_to"):
            self.context['previous_output'] = result
            print(f"\n🔁 Returning output to step: {subflow['return_to']}")
            self._execute_by_step_id(subflow["return_to"])

    def _run_generated_subflow(self, input_text: str, limit: int = 3, return_to: Optional[str] = None):
        for i in range(limit):
            print(f"\n🌀 Iteration {i+1}/{limit}")
            output = f"Step {i+1} based on: {input_text}"
            self.context['previous_output'] = output

        if return_to:
            self._execute_by_step_id(return_to)

    def _evaluate_condition(self, expr: str) -> bool:
        resolved_expr = self._resolve_input(expr)
        s = SimpleEval(names=self.context)
        try:
            return bool(s.eval(resolved_expr))
        except Exception as e:
            print(f"Condition eval error: {e}")
            print(f"Resolved expr was: {resolved_expr}")
            return False

    def _evaluate_expression(self, expr: str):
        """
        Safely resolves dot-separated access into self.context,
        e.g., 'context.step_outputs.fetch' → self.context['step_outputs']['fetch']
        """
        try:
            if not expr.startswith("context."):
                raise ValueError("Only access to 'context.*' is allowed")

            parts = expr.split(".")[1:]  # drop 'context'
            value = self.context
            for part in parts:
                if isinstance(value, dict):
                    value = value[part]
                elif isinstance(value, list):
                    value = value[int(part)]
                else:
                    raise TypeError(f"Cannot access '{part}' on non-container: {value}")
            return value

        except Exception as e:
            print(f"⚠️ Failed to resolve '${{{expr}}}': {e}")
            return f"<error:{expr}>"

    def _resolve_input(self, value):
        if isinstance(value, str):
            value = value.strip()
            # Case 1: Full expression like "${context}" or "${context.step_outputs}"
            if value.startswith("${") and value.endswith("}"):
                expr = value[2:-1]
                return self._evaluate_expression(expr)

            # Case 2: Partial substitution inside a string
            for k, v in self.context.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        placeholder = f"${{{k}.{subk}}}"
                        if placeholder in value:
                            value = value.replace(placeholder, str(subv))
                elif isinstance(v, str):
                    value = value.replace(f"${{{k}}}", v)
            return value
        else:
            return value  # Return non-str inputs unchanged

   
    def _resolve_function(self, path: str, script: Optional[str] = None):
        if script:
            # Compile the script and extract the function
            local_namespace = {}
            exec(script, {}, local_namespace)
            func_name = path.split(".")[-1]
            return local_namespace[func_name]

        # Otherwise, load from module
        parts = path.split(".")
        module_name = ".".join(parts[:-1])
        func_name = parts[-1]
        module = importlib.import_module(module_name)
        return getattr(module, func_name)

    def _get_workflow(self, workflow_id: str) -> Dict:
        workflow = next((wf for wf in self.workflows.get("main_workflow", []) if wf['id'] == workflow_id), None)

        if not workflow:
            workflow = self.workflows.get("main_workflow", [{}])[0]

        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found. Ensure your workflows.yaml file starts with:\n\nworkflows:\n   main_workflow:...")

        # ⬇️ Grab intelligence settings if they exist in the workflow
        settings = workflow.get("settings", {}).get("intelligence", {})
        self.intelligence.config.update(settings)

        # Map fan_keys to steps
        fan_key_to_steps = {}
        explicit_fan_in_map = {}

        for step in workflow.get("steps", []):
            fan_key = step.get("fan_key")
            if fan_key:
                fan_key_to_steps.setdefault(fan_key, []).append(step)

                # Capture explicit fan-in if provided
                if "fan_in_id" in step:
                    explicit_fan_in_map[fan_key] = step["fan_in_id"]

        # Mark fan-in steps
        for fan_key, steps in fan_key_to_steps.items():
            fan_in_id = explicit_fan_in_map.get(fan_key)
            if fan_in_id:
                fan_in_step = next((s for s in steps if s["id"] == fan_in_id), None)
            else:
                fan_in_step = steps[-1]  # Fallback: last one with same fan_key

            if fan_in_step:
                fan_in_step["is_fan_in"] = True

        return workflow

class ToolDeployer:
    """
    Deploy any containerized MCP tool via Terraform.
    Accepts the list of raw tool‑definitions you loaded from tools.yaml.
    """

    def __init__(self, tools):
        # Grab the raw tool‑configs
        if isinstance(tools, list):
            self.tools = {cfg["id"]: cfg for cfg in tools}
        else:
            self.tools = tools
        # map tool_id → {container_name, image_name}
        self._deploy_info = {}
        
    def cleanup(self, tool_id: str) -> None:
        """
        Stop and remove a Cloud Run–emulated Docker container, and optionally
        delete its image.

        :param container_name: the local container you spun up (default: mcp-summarizer-dev)
        :param image_name:  if provided, the name/tag of the image to remove
        """
        import docker
        
        client = docker.from_env()

        info = self._deploy_info.get(tool_id)
        
        tool = self.tools.get(tool_id, {})
        
        print("tool: ", dir(tool))
        
        cfg = (
            (tool.get("settings") if isinstance(tool, dict) else None)
            or getattr(tool, "settings", {})
            or {}
        )
        
        # fallback to defaults if somehow deploy() wasn't called
        container_name = info["container_name"] if info else f"{tool_id}-mcp-container"
        image_name     = info["image_name"]     if info else cfg["image"]

        # stop & remove container
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
            print(f"✅ Stopped and removed container '{container_name}'")
        except docker.errors.NotFound:
            print(f"⚠️ Container '{container_name}' not found")

        # remove image, if asked
        if image_name:
            try:
                client.images.remove(image=image_name, force=True)
                print(f"🗑️ Removed image '{image_name}'")
            except docker.errors.ImageNotFound:
                print(f"⚠️ Image '{image_name}' not found")

    def deploy(
        self,
        tool_id: str,
        state_bucket: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """
        1) look up the tool.yaml entry by tool_id
        2) resolve any env:FOO entries
        3) write terraform.tfvars.json
        4) terraform init/apply (with optional remote GCS state)
        """
        if tool_id not in self.tools:
            raise ValueError(f"Tool '{tool_id}' not found in loaded configs")
        
        tool = self.tools.get(tool_id, {})
        cfg = (
            (tool.get("settings") if isinstance(tool, dict) else None)
            or getattr(tool, "settings", {})
            or {}
        )
        
        if cfg is None:
            raise ValueError(f"Tool '{tool_id}' does not have any settings.")

        env_map = cfg.get("env", {})
        # resolve any env: prefix
        resolved = {
            k: (os.getenv(v.split("env:",1)[1], "") if isinstance(v, str) and v.startswith("env:") else v)
            for k, v in env_map.items()
        }
        
        # pick whatever convention you like:
        container_name = f"{tool_id}-mcp-container"
        
        if cfg.get("image", None) is None:
            image = cfg.get("image")
            github_url = cfg.get("github_url")
            registry_url = cfg.get("to_registry_url")
            context_path = cfg.get("build_context_path", ".")

            # If image is not defined but github_url is present, build locally
            if not image and github_url:
                print(f"🔍 No image defined. Cloning and building from: {github_url}")
                with tempfile.TemporaryDirectory() as tmpdir:
                    repo_path = Path(tmpdir) / "repo"
                    self._clone_repo(github_url, str(repo_path))

                    # Resolve the build context inside the repo
                    build_context = repo_path / context_path
                    if not build_context.exists():
                        print(f"❌ Build context path '{build_context}' does not exist.")
                        sys.exit(1)

                    # Build the image locally
                    self._build_docker_image(str(build_context), tool_id)

                    # If registry is defined, push the image and update YAML
                    if registry_url:
                        cfg["image"] = self._push_docker_image(tool_id, registry_url)
                    else:
                        print(f"✅ Built image '{tool_id}' locally (not pushed).")
            else:
                print(f"❌ Both image and github_url is missing for '{tool_id}'. There is no code to build from.")
        
        mode = cfg.get("mode", "http")  # 🔥 NEW: support 'stdio' mode alongside 'http'

        if mode == 'stdio':  # 🔥 NEW: stdio‐mode deployment
            print(f"🚀 StdIO‐mode tool '{tool_id}' is deployed upon tool call.")
            return
        
        if cfg.get("deployment_target", None) == 'gcp':
            tfvars = {
                "tool_id":    tool_id,
                "image":      cfg["image"],
                "port":       cfg["port"],
                "mode":       cfg.get("mode", "http"),
                "env_vars":   resolved,
                "region":     cfg.get("region", "us-central1"),
                "project_id": project_id or cfg.get("project_id") or os.getenv("GCP_PROJECT_ID",""),
            }

            # dump tfvars into your module folder
            tfvars_path = "terraform/deploy/terraform.tfvars.json"
            with open(tfvars_path, "w") as out:
                json.dump(tfvars, out, indent=2)

            # terraform init
            init_cmd = [
                "terraform", "-chdir=terraform/deploy", "init"
            ]
            
            state_bucket = cfg.get("state_bucket", state_bucket)
            if state_bucket:
                init_cmd += ["-backend-config", f"bucket={state_bucket}"]

            subprocess.run(init_cmd, check=True)

            # terraform apply
            subprocess.run([
                "terraform", "-chdir=terraform/deploy",
                "apply", "-auto-approve"
            ], check=True)
        elif cfg.get("deployment_target", None) == 'docker':
            import docker
            
            if self._running_in_docker():
                print("🚀 Deploying tool via Docker SDK from inside container...")

                client = docker.DockerClient(base_url="unix://var/run/docker.sock")

                # Pull the MCP tool image (if not already present)
                client.images.pull(cfg["image"])

                # Run the MCP tool
                container = client.containers.run(
                    image=cfg["image"],
                    name=container_name,
                    detach=True,
                    ports={f"{cfg['port']}/tcp": cfg["port"]},
                    environment=resolved
                )

                print(f"Started MCP tool: {container.name} (ID: {container.id})")

            else:
                print("💻 Running natively — falling back to local CLI deploy...")
                self._deploy_locally_via_docker(
                    image=cfg["image"],
                    name=container_name,
                    port=cfg["port"],
                    env_vars=resolved,
                    mode=cfg.get("mode", "http")
                )
                
            # remember for cleanup()
            self._deploy_info[tool_id] = {
                "container_name": container_name,
                "image_name": cfg["image"]
            }

    def _running_in_docker(self) -> bool:
        try:
            # Check for .dockerenv file
            if Path("/.dockerenv").exists():
                return True

            # Check if any cgroup contains "docker"
            with open("/proc/1/cgroup", "rt") as f:
                return "docker" in f.read() or "kubepods" in f.read()
        except Exception:
            return False

    def _deploy_locally_via_docker(
        self,
        image: str,
        name: str,
        env_vars: dict,
        port: Optional[int] = None,
        mode: str = "http",
        payload: Optional[str] = None,
    ) -> Union[bool, Dict[str, Any]]:
        """
        • mode="http":  long-running HTTP server on `port`
        • mode="stdio": spin up, send one JSON-RPC call over stdin, tear down
        Returns:
          – in http mode: True/False
          – in stdio mode: {"success": bool, "exit_code": int, "stdout": str, "stderr": str}
        """
        # remove any old container
        subprocess.run(["docker", "rm", "-f", name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # build env args
        env_args = []
        for k, v in env_vars.items():
            env_args += ["-e", f"{k}={v}"]

        if mode == "stdio":
            # one-shot: do not -d, we want to pipe in and capture immediate output
            cmd = [
                "docker", "run", "--rm", "-i",
                "--name", name,
                *env_args,
                image
            ]
        else:
            cmd = ["docker", "run", "-d", "--name", name, *env_args, *port_args, image]

        print("🚀 Launching Docker container:")
        # print("  " + " ".join(cmd)) <-- his exposes tokens, avoid it.

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=(payload + "\n") if mode == "stdio" else None
        )

        # common metadata
        success = proc.returncode == 0
        exit_code = proc.returncode

        if mode == "stdio":
            # ──── STDIO MODE ───────────────────────────────────────────────
            stderr_lines = proc.stderr.splitlines()
            # Usually the first line is the startup banner; drop it
            if stderr_lines and "GitHub MCP Server running on stdio" in stderr_lines[0]:
                banner = stderr_lines.pop(0)
            else:
                banner = None

            raw_out = proc.stdout.strip()
            parsed = None
            parse_error = None

            if raw_out:
                try:
                    parsed = json.loads(raw_out)
                except Exception as e:
                    parse_error = str(e)

            return {
                "success": success,
                "exit_code": exit_code,
                "banner": banner,
                "raw_stdout": raw_out,
                "parsed": parsed,
                "parse_error": parse_error,
                "stderr": "\n".join(stderr_lines),
            }

        # ──── http mode: detached, then poll… (unchanged) ─────
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            msg = proc.stderr.strip() or proc.stdout.strip()
            print(f"❌ Failed to start container:\n{msg}")
            return False

        cid = proc.stdout.strip()
        print(f"✅ Container started (id={cid[:12]})")

        # ──── 2) Poll Docker for “running” state ───────────────────────
        for i in range(5):
            state = subprocess.run(
                ["docker", "inspect", "--format={{.State.Status}}", name],
                capture_output=True, text=True
            ).stdout.strip()
            if state == "running":
                print("🔎 Container status: running")
                break
            print(f"⏳ Waiting for container to be running ({i+1}/5)…")
            time.sleep(1)
        else:
            print("❌ Container never entered running state. Logs:")
            subprocess.run(["docker", "logs", name])
            return False

        # ──── 3) TCP health‑check on the port ──────────────────────────
        sock = socket.socket()
        for i in range(5):
            try:
                sock.connect(("localhost", port))
                print(f"✅ Port {port} is now accepting connections")
                sock.close()
                break
            except Exception:
                print(f"⏳ Waiting for port {port} to open ({i+1}/5)…")
                time.sleep(1)
        else:
            print(f"❌ Port {port} never opened. Check container logs:")
            subprocess.run(["docker", "logs", name])
            return False

        print("🎉 Docker deployment successful and healthy!")
        return True

        
    def _clone_repo(self, git_url, dest_dir):
        subprocess.run(["git", "clone", git_url, dest_dir], check=True)

    def _build_docker_image(self, context_dir: str, tag: str):
        print(f"🔨 Building Docker image '{tag}' from context: {context_dir}")
        subprocess.run(["docker", "build", "-t", tag, context_dir], check=True)

    def _push_docker_image(self, tag: str, registry_url: str):
        full_tag = f"{registry_url}/{tag}"
        print(f"📦 Pushing image '{full_tag}' to registry...")
        subprocess.run(["docker", "tag", tag, full_tag], check=True)
        subprocess.run(["docker", "push", full_tag], check=True)
        return full_tag
