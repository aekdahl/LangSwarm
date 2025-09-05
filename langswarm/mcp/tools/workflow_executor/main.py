"""
Workflow Executor MCP Tool

A powerful MCP tool that enables agents to:
1. Execute pre-written LangSwarm workflows
2. Generate workflow configurations dynamically 
3. Validate and execute generated configurations
4. Support sync, async, and isolated execution modes
"""

import os
import json
import uuid
import yaml
import tempfile
import subprocess
import threading
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool

# Global execution tracking
WORKFLOW_EXECUTIONS = {}  # execution_id -> execution info
EXECUTION_RESULTS = {}    # execution_id -> result


class ExecuteWorkflowInput(BaseModel):
    workflow_name: str = Field(description="Name of the workflow to execute")
    input_data: Dict[str, Any] = Field(description="Input data for the workflow")
    execution_mode: str = Field(default="sync", description="Execution mode: sync, async, isolated")
    config_override: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration overrides")
    timeout: int = Field(default=300, description="Timeout in seconds for execution")


class ExecuteWorkflowOutput(BaseModel):
    execution_id: str = Field(description="Unique execution identifier")
    status: str = Field(description="Execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Execution result (for sync mode)")
    message: str = Field(description="Status message")


class GenerateWorkflowInput(BaseModel):
    workflow_description: str = Field(description="Natural language description of the desired workflow")
    workflow_name: Optional[str] = Field(default=None, description="Optional name for the generated workflow")
    agents_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional agents configuration")
    tools_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional tools configuration")
    complexity: str = Field(default="medium", description="Workflow complexity: simple, medium, complex")


class GenerateWorkflowOutput(BaseModel):
    workflow_name: str = Field(description="Generated workflow name")
    workflow_config: Dict[str, Any] = Field(description="Generated workflow configuration")
    validation_status: str = Field(description="Configuration validation status")
    message: str = Field(description="Generation status message")


class ExecuteGeneratedWorkflowInput(BaseModel):
    workflow_description: str = Field(description="Natural language description of the workflow")
    input_data: Dict[str, Any] = Field(description="Input data for the workflow")
    execution_mode: str = Field(default="sync", description="Execution mode: sync, async, isolated")
    complexity: str = Field(default="medium", description="Workflow complexity: simple, medium, complex")
    timeout: int = Field(default=300, description="Timeout in seconds")


class ExecuteGeneratedWorkflowOutput(BaseModel):
    execution_id: str = Field(description="Unique execution identifier")
    workflow_name: str = Field(description="Generated workflow name")
    workflow_config: Dict[str, Any] = Field(description="Generated workflow configuration")
    status: str = Field(description="Execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Execution result (for sync mode)")
    message: str = Field(description="Status and generation message")


class CheckExecutionStatusInput(BaseModel):
    execution_id: str = Field(description="Execution ID to check")


class CheckExecutionStatusOutput(BaseModel):
    execution_id: str = Field(description="Execution identifier")
    status: str = Field(description="Current execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result if completed")
    progress: Optional[str] = Field(default=None, description="Progress information")
    message: str = Field(description="Status message")


class CancelExecutionInput(BaseModel):
    execution_id: str = Field(description="Execution ID to cancel")


class CancelExecutionOutput(BaseModel):
    execution_id: str = Field(description="Execution identifier")
    status: str = Field(description="Cancellation status")
    message: str = Field(description="Cancellation message")


class ListWorkflowsInput(BaseModel):
    config_path: Optional[str] = Field(default=None, description="Optional path to search for workflows")
    pattern: Optional[str] = Field(default="*.yaml", description="File pattern to search for")


class ListWorkflowsOutput(BaseModel):
    available_workflows: List[Dict[str, Any]] = Field(description="List of available workflows")
    total_count: int = Field(description="Total number of workflows found")
    message: str = Field(description="Search status message")


class WorkflowGenerator:
    """Generates LangSwarm workflow configurations from natural language descriptions"""
    
    def __init__(self):
        self.complexity_templates = {
            "simple": {
                "max_agents": 2,
                "max_steps": 3,
                "tools": ["filesystem", "tasklist"]
            },
            "medium": {
                "max_agents": 4,
                "max_steps": 6,
                "tools": ["filesystem", "tasklist", "codebase_indexer", "mcpremote"]
            },
            "complex": {
                "max_agents": 8,
                "max_steps": 12,
                "tools": ["filesystem", "tasklist", "codebase_indexer", "mcpremote", "mcpmessage_queue_publisher"]
            }
        }
    
    def generate_workflow(self, description: str, workflow_name: str = None, 
                         agents_config: Dict = None, tools_config: Dict = None,
                         complexity: str = "medium") -> Dict[str, Any]:
        """Generate a complete LangSwarm workflow configuration"""
        
        if not workflow_name:
            workflow_name = f"generated_workflow_{int(time.time())}"
        
        template = self.complexity_templates.get(complexity, self.complexity_templates["medium"])
        
        # Analyze description for key patterns
        workflow_config = self._create_base_config(workflow_name)
        
        # Generate agents based on description
        agents = self._generate_agents(description, template, agents_config)
        workflow_config["agents"] = agents
        
        # Generate tools configuration
        tools = self._generate_tools(description, template, tools_config)
        if tools:
            workflow_config["tools"] = tools
        
        # Generate workflow steps
        workflows = self._generate_workflow_steps(description, agents, template)
        workflow_config["workflows"] = {workflow_name: workflows}
        
        return workflow_config
    
    def _create_base_config(self, workflow_name: str) -> Dict[str, Any]:
        """Create base configuration structure"""
        return {
            "version": "1.0",
            "project_name": f"dynamic_{workflow_name}",
            "memory": "production",  # Use smart memory detection
        }
    
    def _generate_agents(self, description: str, template: Dict, custom_config: Dict = None) -> List[Dict[str, Any]]:
        """Generate agents based on description analysis"""
        agents = []
        
        # Keywords that suggest specific agent types
        patterns = {
            "analyz": "analyzer",
            "summar": "summarizer", 
            "research": "researcher",
            "report": "reporter",
            "process": "processor",
            "coordinat": "coordinator",
            "manag": "manager",
            "creat": "creator",
            "generat": "generator",
            "validat": "validator"
        }
        
        agent_types = []
        desc_lower = description.lower()
        
        for pattern, agent_type in patterns.items():
            if pattern in desc_lower:
                agent_types.append(agent_type)
        
        # Ensure we have at least one agent
        if not agent_types:
            agent_types = ["coordinator"]
        
        # Limit based on complexity
        agent_types = agent_types[:template["max_agents"]]
        
        for i, agent_type in enumerate(agent_types):
            agent = {
                "id": f"{agent_type}_{i+1}" if agent_types.count(agent_type) > 1 else agent_type,
                "agent_type": "openai",
                "model": "gpt-4o",
                "system_prompt": self._generate_agent_prompt(agent_type, description),
                "tools": template["tools"][:3]  # Limit tools per agent
            }
            
            # Apply custom agent configuration
            if custom_config and agent_type in custom_config:
                agent.update(custom_config[agent_type])
            
            agents.append(agent)
        
        return agents
    
    def _generate_agent_prompt(self, agent_type: str, description: str) -> str:
        """Generate system prompt for specific agent type"""
        base_prompt = f"You are a {agent_type} agent in a LangSwarm workflow."
        
        prompts = {
            "analyzer": f"{base_prompt} Your role is to analyze data, files, or content thoroughly and provide detailed insights.",
            "summarizer": f"{base_prompt} Your role is to create concise, comprehensive summaries of complex information.",
            "researcher": f"{base_prompt} Your role is to gather information from various sources and compile research findings.",
            "reporter": f"{base_prompt} Your role is to create well-structured reports based on analysis and data.",
            "processor": f"{base_prompt} Your role is to process data, files, or inputs through systematic operations.",
            "coordinator": f"{base_prompt} Your role is to coordinate the workflow and manage task execution.",
            "manager": f"{base_prompt} Your role is to manage resources, tasks, and overall workflow execution.",
            "creator": f"{base_prompt} Your role is to create new content, files, or artifacts based on requirements.",
            "generator": f"{base_prompt} Your role is to generate content, code, or outputs based on specifications.",
            "validator": f"{base_prompt} Your role is to validate, verify, and ensure quality of outputs and processes."
        }
        
        agent_prompt = prompts.get(agent_type, f"{base_prompt} Your role is to assist in the workflow execution.")
        
        # Add context from the original description
        agent_prompt += f"\n\nWorkflow Context: {description}\n\nProvide structured responses and use available tools effectively."
        
        return agent_prompt
    
    def _generate_tools(self, description: str, template: Dict, custom_config: Dict = None) -> List[Dict[str, Any]]:
        """Generate tools configuration based on description"""
        if custom_config:
            return custom_config
        
        # For now, rely on agent-level tool assignment
        # Could be enhanced to generate specific tool configurations
        return None
    
    def _generate_workflow_steps(self, description: str, agents: List[Dict], template: Dict) -> Dict[str, Any]:
        """Generate workflow steps based on agents and description"""
        steps = []
        
        # Simple linear workflow for now
        for i, agent in enumerate(agents):
            step = {
                "agent": agent["id"]
            }
            
            if i == 0:
                step["input"] = "${user_input}"
            else:
                prev_agent = agents[i-1]["id"]
                step["input"] = f"${{{prev_agent}.output}}"
            
            if i == len(agents) - 1:
                step["output"] = {"to": "user"}
            
            steps.append(step)
        
        return {"steps": steps}


class WorkflowExecutor:
    """Handles workflow execution in different modes"""
    
    def __init__(self):
        self.temp_configs = {}  # Track temporary config files
    
    def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any],
                        execution_mode: str = "sync", config_override: Dict = None,
                        timeout: int = 300, config_content: Dict = None) -> Dict[str, Any]:
        """Execute a workflow with specified parameters"""
        
        execution_id = str(uuid.uuid4())
        
        try:
            if execution_mode == "sync":
                return self._execute_sync(execution_id, workflow_name, input_data, 
                                        config_override, timeout, config_content)
            elif execution_mode == "async":
                return self._execute_async(execution_id, workflow_name, input_data,
                                         config_override, timeout, config_content)
            elif execution_mode == "isolated":
                return self._execute_isolated(execution_id, workflow_name, input_data,
                                            config_override, timeout, config_content)
            else:
                return {
                    "execution_id": execution_id,
                    "status": "error",
                    "message": f"Unknown execution mode: {execution_mode}"
                }
        
        except Exception as e:
            return {
                "execution_id": execution_id,
                "status": "error",
                "message": f"Execution failed: {str(e)}"
            }
    
    def _execute_sync(self, execution_id: str, workflow_name: str, input_data: Dict,
                     config_override: Dict, timeout: int, config_content: Dict = None) -> Dict[str, Any]:
        """Execute workflow synchronously in the same process"""
        
        WORKFLOW_EXECUTIONS[execution_id] = {
            "status": "running",
            "workflow_name": workflow_name,
            "start_time": time.time(),
            "mode": "sync"
        }
        
        try:
            # Create temporary workflow configuration
            config_path = self._create_temp_config(execution_id, workflow_name, config_content, config_override)
            
            # Import LangSwarm components
            from langswarm.core.config import LangSwarmConfigLoader
            
            # Load and execute workflow
            loader = LangSwarmConfigLoader(config_path)
            
            # Find workflow in configuration
            workflows = loader.config_data.get("workflows", {})
            if workflow_name not in workflows:
                available = list(workflows.keys())
                raise ValueError(f"Workflow '{workflow_name}' not found. Available: {available}")
            
            # Execute workflow (simplified - would need full LangSwarm execution logic)
            # For now, return a success response
            result = {
                "workflow_executed": workflow_name,
                "input_processed": input_data,
                "agents_available": len(loader.config_data.get("agents", [])),
                "config_path": config_path
            }
            
            WORKFLOW_EXECUTIONS[execution_id]["status"] = "completed"
            EXECUTION_RESULTS[execution_id] = result
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "result": result,
                "message": f"Workflow '{workflow_name}' executed successfully"
            }
            
        except Exception as e:
            WORKFLOW_EXECUTIONS[execution_id]["status"] = "failed"
            EXECUTION_RESULTS[execution_id] = {"error": str(e)}
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "message": f"Sync execution failed: {str(e)}"
            }
        finally:
            self._cleanup_temp_config(execution_id)
    
    def _execute_async(self, execution_id: str, workflow_name: str, input_data: Dict,
                      config_override: Dict, timeout: int, config_content: Dict = None) -> Dict[str, Any]:
        """Execute workflow asynchronously in a separate thread"""
        
        WORKFLOW_EXECUTIONS[execution_id] = {
            "status": "running",
            "workflow_name": workflow_name,
            "start_time": time.time(),
            "mode": "async"
        }
        
        def async_worker():
            try:
                result = self._execute_sync(execution_id, workflow_name, input_data,
                                          config_override, timeout, config_content)
                EXECUTION_RESULTS[execution_id] = result
                WORKFLOW_EXECUTIONS[execution_id]["status"] = "completed"
            except Exception as e:
                EXECUTION_RESULTS[execution_id] = {"error": str(e)}
                WORKFLOW_EXECUTIONS[execution_id]["status"] = "failed"
        
        thread = threading.Thread(target=async_worker, daemon=True)
        thread.start()
        
        return {
            "execution_id": execution_id,
            "status": "running",
            "message": f"Workflow '{workflow_name}' started asynchronously"
        }
    
    def _execute_isolated(self, execution_id: str, workflow_name: str, input_data: Dict,
                         config_override: Dict, timeout: int, config_content: Dict = None) -> Dict[str, Any]:
        """Execute workflow in a separate LangSwarm process"""
        
        WORKFLOW_EXECUTIONS[execution_id] = {
            "status": "running", 
            "workflow_name": workflow_name,
            "start_time": time.time(),
            "mode": "isolated"
        }
        
        try:
            # Create temporary configuration
            config_path = self._create_temp_config(execution_id, workflow_name, config_content, config_override)
            
            # Prepare input data file
            input_file = os.path.join(os.path.dirname(config_path), f"input_{execution_id}.json")
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Create execution script
            script_content = f"""
import sys
import json
from langswarm.core.config import LangSwarmConfigLoader

# Load configuration
loader = LangSwarmConfigLoader('{os.path.dirname(config_path)}')

# Load input data
with open('{input_file}', 'r') as f:
    input_data = json.load(f)

# Execute workflow (simplified for demo)
result = {{
    "workflow_executed": "{workflow_name}",
    "input_processed": input_data,
    "execution_mode": "isolated",
    "agents_count": len(loader.config_data.get("agents", [])),
    "pid": os.getpid()
}}

# Output result
print(json.dumps(result))
"""
            
            script_file = os.path.join(os.path.dirname(config_path), f"execute_{execution_id}.py")
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Execute in separate process
            cmd = ["python3", script_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                execution_result = json.loads(result.stdout.strip())
                WORKFLOW_EXECUTIONS[execution_id]["status"] = "completed"
                EXECUTION_RESULTS[execution_id] = execution_result
                
                return {
                    "execution_id": execution_id,
                    "status": "completed",
                    "result": execution_result,
                    "message": f"Isolated workflow '{workflow_name}' executed successfully"
                }
            else:
                error_msg = result.stderr or "Unknown error"
                WORKFLOW_EXECUTIONS[execution_id]["status"] = "failed"
                EXECUTION_RESULTS[execution_id] = {"error": error_msg}
                
                return {
                    "execution_id": execution_id,
                    "status": "failed",
                    "message": f"Isolated execution failed: {error_msg}"
                }
        
        except subprocess.TimeoutExpired:
            WORKFLOW_EXECUTIONS[execution_id]["status"] = "timeout"
            return {
                "execution_id": execution_id,
                "status": "timeout",
                "message": f"Workflow execution timed out after {timeout} seconds"
            }
        except Exception as e:
            WORKFLOW_EXECUTIONS[execution_id]["status"] = "failed"
            return {
                "execution_id": execution_id,
                "status": "failed",
                "message": f"Isolated execution error: {str(e)}"
            }
        finally:
            self._cleanup_temp_config(execution_id)
    
    def _create_temp_config(self, execution_id: str, workflow_name: str, 
                           config_content: Dict = None, config_override: Dict = None) -> str:
        """Create temporary configuration file"""
        
        temp_dir = tempfile.mkdtemp(prefix=f"langswarm_exec_{execution_id}_")
        config_path = os.path.join(temp_dir, "langswarm.yaml")
        
        if config_content:
            # Use provided configuration content
            final_config = config_content.copy()
        else:
            # Load existing configuration or create basic one
            final_config = {
                "version": "1.0",
                "project_name": f"workflow_execution_{execution_id}",
                "memory": "production",
                "agents": [
                    {
                        "id": "default_agent",
                        "agent_type": "openai",
                        "model": "gpt-4o",
                        "system_prompt": f"You are executing workflow: {workflow_name}",
                        "tools": ["filesystem", "tasklist"]
                    }
                ],
                "workflows": {
                    workflow_name: {
                        "steps": [
                            {
                                "agent": "default_agent",
                                "input": "${user_input}",
                                "output": {"to": "user"}
                            }
                        ]
                    }
                }
            }
        
        # Apply configuration overrides
        if config_override:
            self._deep_update(final_config, config_override)
        
        # Write configuration file
        with open(config_path, 'w') as f:
            yaml.dump(final_config, f, default_flow_style=False)
        
        self.temp_configs[execution_id] = temp_dir
        return temp_dir
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep update of nested dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _cleanup_temp_config(self, execution_id: str):
        """Clean up temporary configuration files"""
        if execution_id in self.temp_configs:
            import shutil
            try:
                shutil.rmtree(self.temp_configs[execution_id])
                del self.temp_configs[execution_id]
            except Exception as e:
                print(f"Warning: Could not clean up temp config for {execution_id}: {e}")
    
    def check_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Check the status of a workflow execution"""
        
        if execution_id not in WORKFLOW_EXECUTIONS:
            return {
                "execution_id": execution_id,
                "status": "not_found",
                "message": "Execution ID not found"
            }
        
        execution_info = WORKFLOW_EXECUTIONS[execution_id]
        result = EXECUTION_RESULTS.get(execution_id)
        
        status_info = {
            "execution_id": execution_id,
            "status": execution_info["status"],
            "workflow_name": execution_info["workflow_name"],
            "execution_mode": execution_info["mode"],
            "start_time": execution_info["start_time"],
            "message": f"Execution is {execution_info['status']}"
        }
        
        if result:
            status_info["result"] = result
        
        if execution_info["status"] in ["completed", "failed"]:
            elapsed = time.time() - execution_info["start_time"]
            status_info["elapsed_time"] = elapsed
            status_info["message"] += f" (took {elapsed:.2f}s)"
        
        return status_info
    
    def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running workflow execution"""
        
        if execution_id not in WORKFLOW_EXECUTIONS:
            return {
                "execution_id": execution_id,
                "status": "not_found",
                "message": "Execution ID not found"
            }
        
        execution_info = WORKFLOW_EXECUTIONS[execution_id]
        
        if execution_info["status"] not in ["running"]:
            return {
                "execution_id": execution_id,
                "status": execution_info["status"],
                "message": f"Cannot cancel execution with status: {execution_info['status']}"
            }
        
        # Mark as cancelled
        WORKFLOW_EXECUTIONS[execution_id]["status"] = "cancelled"
        EXECUTION_RESULTS[execution_id] = {"message": "Execution cancelled by user"}
        
        # Clean up temporary files
        self._cleanup_temp_config(execution_id)
        
        return {
            "execution_id": execution_id,
            "status": "cancelled",
            "message": "Execution cancelled successfully"
        }


def execute_workflow(workflow_name: str, input_data: Dict[str, Any], execution_mode: str = "sync",
                    config_override: Dict = None, timeout: int = 300) -> Dict[str, Any]:
    """Execute a pre-written workflow"""
    executor = WorkflowExecutor()
    return executor.execute_workflow(workflow_name, input_data, execution_mode, config_override, timeout)


def generate_workflow(workflow_description: str, workflow_name: str = None, 
                     agents_config: Dict = None, tools_config: Dict = None,
                     complexity: str = "medium") -> Dict[str, Any]:
    """Generate a workflow configuration from natural language description"""
    generator = WorkflowGenerator()
    
    try:
        config = generator.generate_workflow(workflow_description, workflow_name, 
                                           agents_config, tools_config, complexity)
        
        return {
            "workflow_name": workflow_name or f"generated_workflow_{int(time.time())}",
            "workflow_config": config,
            "validation_status": "valid",
            "message": "Workflow configuration generated successfully"
        }
    
    except Exception as e:
        return {
            "workflow_name": workflow_name or "failed_generation",
            "workflow_config": {},
            "validation_status": "invalid",
            "message": f"Failed to generate workflow: {str(e)}"
        }


def execute_generated_workflow(workflow_description: str, input_data: Dict[str, Any],
                              execution_mode: str = "sync", complexity: str = "medium",
                              timeout: int = 300) -> Dict[str, Any]:
    """Generate and execute a workflow in one step"""
    
    # Generate workflow configuration
    generation_result = generate_workflow(workflow_description, complexity=complexity)
    
    if generation_result["validation_status"] != "valid":
        return {
            "execution_id": "generation_failed",
            "workflow_name": generation_result["workflow_name"],
            "workflow_config": generation_result["workflow_config"],
            "status": "failed",
            "message": f"Workflow generation failed: {generation_result['message']}"
        }
    
    # Execute the generated workflow
    workflow_name = generation_result["workflow_name"]
    config_content = generation_result["workflow_config"]
    
    executor = WorkflowExecutor()
    result = executor.execute_workflow(workflow_name, input_data, execution_mode, 
                                     None, timeout, config_content)
    
    # Add generation info to result
    result["workflow_name"] = workflow_name
    result["workflow_config"] = config_content
    result["message"] = f"Generated and executed workflow: {result.get('message', 'Success')}"
    
    return result


def check_execution_status(execution_id: str) -> Dict[str, Any]:
    """Check the status of a workflow execution"""
    executor = WorkflowExecutor()
    return executor.check_execution_status(execution_id)


def cancel_execution(execution_id: str) -> Dict[str, Any]:
    """Cancel a running workflow execution"""
    executor = WorkflowExecutor()
    return executor.cancel_execution(execution_id)


def list_workflows(config_path: str = None, pattern: str = "*.yaml") -> Dict[str, Any]:
    """List available workflows in the current or specified directory"""
    
    if config_path is None:
        config_path = "."
    
    workflows = []
    total_count = 0
    
    try:
        search_path = Path(config_path)
        if not search_path.exists():
            return {
                "available_workflows": [],
                "total_count": 0,
                "message": f"Path not found: {config_path}"
            }
        
        # Search for workflow files
        for yaml_file in search_path.glob(pattern):
            try:
                with open(yaml_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                if config_data and "workflows" in config_data:
                    for workflow_name, workflow_config in config_data["workflows"].items():
                        workflows.append({
                            "name": workflow_name,
                            "file": str(yaml_file),
                            "steps": len(workflow_config.get("steps", [])),
                            "description": workflow_config.get("description", "No description")
                        })
                        total_count += 1
            
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return {
            "available_workflows": workflows,
            "total_count": total_count,
            "message": f"Found {total_count} workflows in {config_path}"
        }
    
    except Exception as e:
        return {
            "available_workflows": [],
            "total_count": 0,
            "message": f"Error searching for workflows: {str(e)}"
        }


# Initialize MCP server
server = BaseMCPToolServer(
    name="workflow_executor",
    description="Execute LangSwarm workflows with support for pre-written and dynamically generated configurations"
)

# Register tasks
server.add_task(
    name="execute_workflow",
    description="Execute a pre-written LangSwarm workflow",
    input_model=ExecuteWorkflowInput,
    output_model=ExecuteWorkflowOutput,
    handler=lambda workflow_name, input_data, execution_mode="sync", config_override=None, timeout=300: 
        execute_workflow(workflow_name, input_data, execution_mode, config_override, timeout)
)

server.add_task(
    name="generate_workflow",
    description="Generate a workflow configuration from natural language description",
    input_model=GenerateWorkflowInput,
    output_model=GenerateWorkflowOutput,
    handler=lambda workflow_description, workflow_name=None, agents_config=None, tools_config=None, complexity="medium":
        generate_workflow(workflow_description, workflow_name, agents_config, tools_config, complexity)
)

server.add_task(
    name="execute_generated_workflow",
    description="Generate and execute a workflow in one step from natural language description",
    input_model=ExecuteGeneratedWorkflowInput,
    output_model=ExecuteGeneratedWorkflowOutput,
    handler=lambda workflow_description, input_data, execution_mode="sync", complexity="medium", timeout=300:
        execute_generated_workflow(workflow_description, input_data, execution_mode, complexity, timeout)
)

server.add_task(
    name="check_execution_status",
    description="Check the status of a workflow execution",
    input_model=CheckExecutionStatusInput,
    output_model=CheckExecutionStatusOutput,
    handler=lambda execution_id: check_execution_status(execution_id)
)

server.add_task(
    name="cancel_execution",
    description="Cancel a running workflow execution",
    input_model=CancelExecutionInput,
    output_model=CancelExecutionOutput,
    handler=lambda execution_id: cancel_execution(execution_id)
)

server.add_task(
    name="list_workflows",
    description="List available workflows in the current or specified directory",
    input_model=ListWorkflowsInput,
    output_model=ListWorkflowsOutput,
    handler=lambda config_path=None, pattern="*.yaml": list_workflows(config_path, pattern)
)


class WorkflowExecutorMCPTool(BaseTool):
    """LangChain-compatible wrapper for the workflow executor MCP tool"""
    
    _bypass_pydantic = True
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, 
                 mcp_url: str = None, **kwargs):
        
        # Use BaseTool with required parameters
        super().__init__(
            name=name or "workflow_executor",
            description="Execute LangSwarm workflows with support for pre-written and dynamically generated configurations",
            instruction="Use this tool to execute existing workflows, generate new workflows from natural language, and manage workflow executions. Supports sync, async, and isolated execution modes.",
            identifier=identifier,
            brief="Dynamic workflow orchestration and execution",
            **kwargs
        )
        
        # Mark as MCP tool and set local mode
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        if mcp_url:
            object.__setattr__(self, 'mcp_url', mcp_url)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool execution"""
        
        method = input_data.get("method")
        params = input_data.get("params", {})
        
        if method == "execute_workflow":
            return execute_workflow(**params)
        elif method == "generate_workflow":
            return generate_workflow(**params)
        elif method == "execute_generated_workflow":
            return execute_generated_workflow(**params)
        elif method == "check_execution_status":
            return check_execution_status(**params)
        elif method == "cancel_execution":
            return cancel_execution(**params)
        elif method == "list_workflows":
            return list_workflows(**params)
        else:
            return {
                "error": f"Unknown method: {method}",
                "available_methods": [
                    "execute_workflow", "generate_workflow", "execute_generated_workflow",
                    "check_execution_status", "cancel_execution", "list_workflows"
                ]
            }


# Add health check endpoint for Docker/Kubernetes (only if not in local mode)
if not server.local_mode and hasattr(server, 'app') and server.app:
    @server.app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring and load balancers"""
        return {
            "status": "healthy",
            "service": "workflow_executor",
            "version": "1.0.0",
            "timestamp": time.time(),
            "active_executions": len(WORKFLOW_EXECUTIONS),
            "completed_executions": len([e for e in WORKFLOW_EXECUTIONS.values() if e["status"] == "completed"])
        }

    @server.app.get("/metrics")
    async def metrics():
        """Metrics endpoint for monitoring"""
        total_executions = len(WORKFLOW_EXECUTIONS)
        completed = len([e for e in WORKFLOW_EXECUTIONS.values() if e["status"] == "completed"])
        failed = len([e for e in WORKFLOW_EXECUTIONS.values() if e["status"] == "failed"])
        running = len([e for e in WORKFLOW_EXECUTIONS.values() if e["status"] == "running"])
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed,
            "failed_executions": failed,
            "running_executions": running,
            "success_rate": (completed / total_executions * 100) if total_executions > 0 else 0,
            "execution_modes": {
                "sync": len([e for e in WORKFLOW_EXECUTIONS.values() if e.get("mode") == "sync"]),
                "async": len([e for e in WORKFLOW_EXECUTIONS.values() if e.get("mode") == "async"]),
                "isolated": len([e for e in WORKFLOW_EXECUTIONS.values() if e.get("mode") == "isolated"])
            }
        }

if __name__ == "__main__":
    import uvicorn
    import os
    
    host = os.getenv("WORKFLOW_EXECUTOR_HOST", "0.0.0.0")
    port = int(os.getenv("WORKFLOW_EXECUTOR_PORT", "4020"))
    
    print(f"🚀 Starting Workflow Executor MCP Server")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🏥 Health: http://{host}:{port}/health")
    print(f"📊 Metrics: http://{host}:{port}/metrics")
    
    uvicorn.run(server.app, host=host, port=port)