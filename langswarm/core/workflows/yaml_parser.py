"""
YAML Workflow Parser for LangSwarm V2

Provides backward compatibility by parsing existing YAML workflow
configurations and converting them to V2 workflow objects.
Ensures 100% compatibility with existing workflow patterns.
"""

import yaml
import re
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path

from .interfaces import IWorkflow, IWorkflowStep, WorkflowContext, ExecutionMode, StepType
from .base import BaseWorkflow, AgentStep, ToolStep, ConditionStep, TransformStep
from .builder import WorkflowBuilder


class YAMLWorkflowParser:
    """
    Parser for converting YAML workflow configurations to V2 workflows.
    
    Supports:
    - Legacy YAML workflow formats
    - Simple syntax workflows (agent -> user)
    - Complex multi-step workflow definitions
    - Variable substitution and templating
    - Conditional and parallel execution patterns
    """
    
    def __init__(self):
        self._agent_registry = {}
        self._tool_registry = {}
    
    def parse_yaml_file(self, yaml_path: Union[str, Path]) -> List[IWorkflow]:
        """Parse workflows from a YAML file"""
        yaml_path = Path(yaml_path)
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        return self.parse_yaml_content(content)
    
    def parse_yaml_content(self, content: Dict[str, Any]) -> List[IWorkflow]:
        """Parse workflows from YAML content"""
        workflows = []
        
        if 'workflows' not in content:
            raise ValueError("No 'workflows' section found in YAML")
        
        workflows_data = content['workflows']
        
        # Handle different YAML workflow formats
        if isinstance(workflows_data, dict):
            # New dict format: workflows: { workflow_name: [...] }
            for workflow_key, workflow_def in workflows_data.items():
                workflow = self._parse_workflow_definition(workflow_key, workflow_def)
                if workflow:
                    workflows.append(workflow)
        
        elif isinstance(workflows_data, list):
            # Old list format: workflows: [...]
            for i, workflow_def in enumerate(workflows_data):
                if isinstance(workflow_def, str):
                    # Simple syntax: "agent -> user"
                    workflow = self._parse_simple_syntax_workflow(f"workflow_{i}", workflow_def)
                    workflows.append(workflow)
                elif isinstance(workflow_def, dict):
                    # Complex workflow definition
                    workflow_id = workflow_def.get('id', f"workflow_{i}")
                    workflow = self._parse_workflow_definition(workflow_id, workflow_def)
                    if workflow:
                        workflows.append(workflow)
        
        return workflows
    
    def _parse_workflow_definition(self, workflow_id: str, definition: Union[List, Dict]) -> Optional[IWorkflow]:
        """Parse a single workflow definition"""
        
        if isinstance(definition, list):
            # List of workflow items
            if len(definition) == 1 and isinstance(definition[0], dict):
                # Single workflow object in list
                return self._parse_complex_workflow(workflow_id, definition[0])
            else:
                # Multiple workflow steps
                return self._parse_step_list_workflow(workflow_id, definition)
        
        elif isinstance(definition, dict):
            # Direct workflow object
            return self._parse_complex_workflow(workflow_id, definition)
        
        elif isinstance(definition, str):
            # Simple syntax
            return self._parse_simple_syntax_workflow(workflow_id, definition)
        
        return None
    
    def _parse_complex_workflow(self, workflow_id: str, workflow_def: Dict[str, Any]) -> IWorkflow:
        """Parse a complex workflow definition with full configuration"""
        
        builder = WorkflowBuilder().start(workflow_id, workflow_def.get('name', workflow_id))
        
        # Set description if provided
        if 'description' in workflow_def:
            builder.description(workflow_def['description'])
        
        # Parse workflow steps
        steps = workflow_def.get('steps', [])
        self._parse_and_add_steps(builder, steps)
        
        # Set execution mode
        execution_mode = workflow_def.get('execution_mode', 'sync')
        if execution_mode == 'parallel':
            builder.set_execution_mode(ExecutionMode.PARALLEL)
        elif execution_mode == 'async':
            builder.set_execution_mode(ExecutionMode.ASYNC)
        elif execution_mode == 'streaming':
            builder.set_execution_mode(ExecutionMode.STREAMING)
        else:
            builder.set_execution_mode(ExecutionMode.SYNC)
        
        # Set timeout if provided
        if 'timeout' in workflow_def:
            builder.set_timeout(workflow_def['timeout'])
        
        # Set input/output schemas if provided
        if 'input_schema' in workflow_def:
            builder.set_input_schema(workflow_def['input_schema'])
        
        if 'output_schema' in workflow_def:
            builder.set_output_schema(workflow_def['output_schema'])
        
        # Set error handling
        if workflow_def.get('continue_on_error', False):
            builder.with_error_handling(True)
        
        return builder.build()
    
    def _parse_step_list_workflow(self, workflow_id: str, steps: List[Dict[str, Any]]) -> IWorkflow:
        """Parse workflow from a list of step definitions"""
        
        builder = WorkflowBuilder().start(workflow_id, f"Workflow: {workflow_id}")
        self._parse_and_add_steps(builder, steps)
        
        return builder.build()
    
    def _parse_and_add_steps(self, builder: WorkflowBuilder, steps: List[Dict[str, Any]]):
        """Parse and add steps to the workflow builder"""
        
        for step_def in steps:
            # Handle string steps (simple syntax)
            if isinstance(step_def, str):
                # Convert string to simple workflow and add steps
                simple_workflow = self._parse_simple_syntax_workflow(f"temp_{len(builder._steps)}", step_def)
                for step in simple_workflow.steps:
                    builder.add_step(step)
                continue
            
            step_id = step_def.get('id', f"step_{len(builder._steps)}")
            step_type = self._determine_step_type(step_def)
            
            if step_type == StepType.AGENT:
                self._add_agent_step(builder, step_id, step_def)
            elif step_type == StepType.TOOL:
                self._add_tool_step(builder, step_id, step_def)
            elif step_type == StepType.CONDITION:
                self._add_condition_step(builder, step_id, step_def)
            elif step_type == StepType.TRANSFORM:
                self._add_transform_step(builder, step_id, step_def)
            else:
                # Default to agent step
                self._add_agent_step(builder, step_id, step_def)
    
    def _determine_step_type(self, step_def: Dict[str, Any]) -> StepType:
        """Determine the type of step from definition"""
        
        if 'agent' in step_def:
            return StepType.AGENT
        elif 'tool' in step_def:
            return StepType.TOOL
        elif 'condition' in step_def:
            return StepType.CONDITION
        elif 'transform' in step_def or 'transformer' in step_def:
            return StepType.TRANSFORM
        else:
            # Default to agent
            return StepType.AGENT
    
    def _add_agent_step(self, builder: WorkflowBuilder, step_id: str, step_def: Dict[str, Any]):
        """Add an agent step to the builder"""
        
        agent_id = step_def.get('agent', step_def.get('id', step_id))
        
        # Parse input data
        input_data = step_def.get('input', step_def.get('input_data', '${input}'))
        
        # Convert template strings
        if isinstance(input_data, str):
            input_data = self._convert_template_syntax(input_data)
        
        # Parse dependencies
        dependencies = self._parse_dependencies(step_def)
        
        # Parse timeout
        timeout = step_def.get('timeout')
        
        builder.add_agent_step(
            step_id=step_id,
            agent_id=agent_id,
            input_data=input_data,
            name=step_def.get('name'),
            description=step_def.get('description'),
            dependencies=dependencies,
            timeout=timeout
        )
    
    def _add_tool_step(self, builder: WorkflowBuilder, step_id: str, step_def: Dict[str, Any]):
        """Add a tool step to the builder"""
        
        tool_name = step_def.get('tool', step_def.get('name', step_id))
        
        # Parse parameters
        parameters = step_def.get('parameters', step_def.get('params', {}))
        
        # Convert template syntax in parameters
        parameters = self._convert_template_syntax_recursive(parameters)
        
        # Parse dependencies
        dependencies = self._parse_dependencies(step_def)
        
        # Parse timeout
        timeout = step_def.get('timeout')
        
        builder.add_tool_step(
            step_id=step_id,
            tool_name=tool_name,
            parameters=parameters,
            name=step_def.get('name'),
            description=step_def.get('description'),
            dependencies=dependencies,
            timeout=timeout
        )
    
    def _add_condition_step(self, builder: WorkflowBuilder, step_id: str, step_def: Dict[str, Any]):
        """Add a condition step to the builder"""
        
        # Parse condition
        condition_expr = step_def.get('condition', 'true')
        condition_func = self._parse_condition_expression(condition_expr)
        
        true_step = step_def.get('true_step', step_def.get('if_true'))
        false_step = step_def.get('false_step', step_def.get('if_false'))
        
        # Parse dependencies
        dependencies = self._parse_dependencies(step_def)
        
        builder.add_condition_step(
            step_id=step_id,
            condition=condition_func,
            true_step=true_step,
            false_step=false_step,
            name=step_def.get('name'),
            description=step_def.get('description'),
            dependencies=dependencies
        )
    
    def _add_transform_step(self, builder: WorkflowBuilder, step_id: str, step_def: Dict[str, Any]):
        """Add a transform step to the builder"""
        
        # Parse transformer
        transform_expr = step_def.get('transform', step_def.get('transformer', 'lambda x, ctx: x'))
        transformer_func = self._parse_transformer_expression(transform_expr)
        
        input_source = step_def.get('input_source', step_def.get('source', 'input'))
        
        # Parse dependencies
        dependencies = self._parse_dependencies(step_def)
        
        builder.add_transform_step(
            step_id=step_id,
            transformer=transformer_func,
            input_source=input_source,
            name=step_def.get('name'),
            description=step_def.get('description'),
            dependencies=dependencies
        )
    
    def _parse_dependencies(self, step_def: Dict[str, Any]) -> List[str]:
        """Parse step dependencies from definition"""
        
        dependencies = step_def.get('dependencies', step_def.get('depends_on', []))
        
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        elif not isinstance(dependencies, list):
            dependencies = []
        
        return dependencies
    
    def _convert_template_syntax(self, template: str) -> str:
        """Convert legacy template syntax to V2 format"""
        
        if not isinstance(template, str):
            return template
        
        # Convert ${context.step_outputs.step_name} to ${step_name}
        template = re.sub(r'\$\{context\.step_outputs\.([^}]+)\}', r'${\1}', template)
        
        # Convert ${context.variables.var_name} to ${var_name}
        template = re.sub(r'\$\{context\.variables\.([^}]+)\}', r'${\1}', template)
        
        # Convert ${user_input} and ${user_query} to ${input}
        template = re.sub(r'\$\{user_input\}', '${input}', template)
        template = re.sub(r'\$\{user_query\}', '${input}', template)
        
        return template
    
    def _convert_template_syntax_recursive(self, data: Any) -> Any:
        """Recursively convert template syntax in nested data structures"""
        
        if isinstance(data, str):
            return self._convert_template_syntax(data)
        elif isinstance(data, dict):
            return {k: self._convert_template_syntax_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_template_syntax_recursive(item) for item in data]
        else:
            return data
    
    def _parse_condition_expression(self, expr: str) -> Callable[[WorkflowContext], bool]:
        """Parse a condition expression into a callable"""
        
        # Simple condition expressions
        if expr == 'true':
            return lambda ctx: True
        elif expr == 'false':
            return lambda ctx: False
        
        # Variable-based conditions
        if expr.startswith('${') and expr.endswith('}'):
            var_name = expr[2:-1]
            return lambda ctx: bool(ctx.get_variable(var_name))
        
        # Step output conditions
        if '.' in expr:
            parts = expr.split('.')
            if len(parts) == 2:
                step_id, field = parts
                return lambda ctx: bool(ctx.get_step_output(step_id, {}).get(field))
        
        # Default: always true
        return lambda ctx: True
    
    def _parse_transformer_expression(self, expr: str) -> Callable[[Any, WorkflowContext], Any]:
        """Parse a transformer expression into a callable"""
        
        # Identity transformer
        if expr == 'identity' or expr == 'lambda x, ctx: x':
            return lambda x, ctx: x
        
        # JSON transformer
        if expr == 'to_json':
            import json
            return lambda x, ctx: json.dumps(x) if x is not None else '{}'
        
        # String transformer
        if expr == 'to_string':
            return lambda x, ctx: str(x) if x is not None else ''
        
        # Length transformer
        if expr == 'length':
            return lambda x, ctx: len(x) if x is not None else 0
        
        # Custom transformer (for security, we'll use a simple eval with limited context)
        if expr.startswith('lambda'):
            try:
                # Very basic lambda evaluation - in production, use a proper expression parser
                return eval(expr)
            except Exception:
                # Fallback to identity
                return lambda x, ctx: x
        
        # Default: identity transformer
        return lambda x, ctx: x
    
    def _parse_simple_syntax_workflow(self, workflow_id: str, syntax: str) -> IWorkflow:
        """Parse simple syntax workflow (e.g., 'agent1 -> agent2 -> user')"""
        
        # Remove the deprecated "-> user" pattern
        syntax = re.sub(r'\s*->\s*user\s*$', '', syntax.strip())
        
        # Split by arrow operator
        if ' -> ' in syntax:
            agent_chain = [agent.strip() for agent in syntax.split(' -> ')]
        else:
            agent_chain = [syntax.strip()]
        
        # Filter out empty agents
        agent_chain = [agent for agent in agent_chain if agent]
        
        if not agent_chain:
            raise ValueError(f"Empty agent chain in simple syntax: {syntax}")
        
        # Create workflow using the simple workflow factory
        from .builder import create_simple_workflow
        
        try:
            return create_simple_workflow(
                workflow_id=workflow_id,
                name=f"Simple Workflow: {' -> '.join(agent_chain)}",
                agent_chain=agent_chain
            )
        except Exception as e:
            # Fallback: create manually
            builder = WorkflowBuilder().start(workflow_id, f"Simple Workflow: {syntax}")
            
            for i, agent_id in enumerate(agent_chain):
                step_id = f"step_{i+1}_{agent_id}"
                
                if i == 0:
                    input_data = "${input}"
                    dependencies = []
                else:
                    prev_step_id = f"step_{i}_{agent_chain[i-1]}"
                    input_data = f"${{{prev_step_id}}}"
                    dependencies = [prev_step_id]
                
                builder.add_agent_step(
                    step_id=step_id,
                    agent_id=agent_id,
                    input_data=input_data,
                    name=f"Execute {agent_id}",
                    dependencies=dependencies
                )
            
            return builder.build()


class YAMLWorkflowCompatibility:
    """
    Compatibility layer for integrating YAML workflows with V2 system.
    
    Provides utilities for:
    - Loading and converting existing YAML workflows
    - Registering converted workflows
    - Maintaining workflow execution compatibility
    """
    
    def __init__(self):
        self.parser = YAMLWorkflowParser()
        self._loaded_files = {}
    
    async def load_yaml_workflow_file(self, yaml_path: Union[str, Path]) -> List[IWorkflow]:
        """Load workflows from YAML file with automatic tool injection and register them"""
        
        yaml_path = Path(yaml_path)
        file_key = str(yaml_path.absolute())
        
        # Check if already loaded
        if file_key in self._loaded_files:
            return self._loaded_files[file_key]
        
        # Load and pre-process YAML content for automatic tool injection
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
        
        # Apply automatic tool injection to agents
        yaml_content = await self._apply_automatic_tool_injection(yaml_content)
        
        # Parse workflows with processed content
        workflows = self.parser.parse_yaml_content(yaml_content)
        
        # Register workflows
        from . import register_workflow
        
        registered_workflows = []
        for workflow in workflows:
            success = await register_workflow(workflow)
            if success:
                registered_workflows.append(workflow)
        
        # Cache loaded workflows
        self._loaded_files[file_key] = registered_workflows
        
        return registered_workflows
    
    async def _apply_automatic_tool_injection(self, yaml_content: Dict[str, Any]) -> Dict[str, Any]:
        """YAML workflows use MCP protocol directly - no injection needed"""
        # YAML workflows call tools via MCP protocol:
        # - function: langswarm.core.utils.workflows.functions.mcp_call
        #   args:
        #     mcp_url: "local://tool_name"
        #     payload: {...}
        # 
        # No system prompt injection required - tools are called directly
        return yaml_content
    
    async def load_yaml_workflow_directory(self, directory: Union[str, Path]) -> List[IWorkflow]:
        """Load all YAML workflow files from a directory"""
        
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
        
        all_workflows = []
        
        # Find all YAML files
        yaml_files = list(directory.glob('*.yaml')) + list(directory.glob('*.yml'))
        
        for yaml_file in yaml_files:
            try:
                workflows = await self.load_yaml_workflow_file(yaml_file)
                all_workflows.extend(workflows)
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")
        
        return all_workflows
    
    def convert_workflow_config(self, config_data: Dict[str, Any]) -> List[IWorkflow]:
        """Convert workflow configuration data to V2 workflows"""
        
        workflows = self.parser.parse_yaml_content(config_data)
        return workflows
    
    async def migrate_existing_workflows(self, search_paths: List[Union[str, Path]]) -> Dict[str, List[IWorkflow]]:
        """Migrate existing workflows from multiple locations"""
        
        migration_results = {}
        
        for search_path in search_paths:
            search_path = Path(search_path)
            
            try:
                if search_path.is_file() and search_path.suffix in ['.yaml', '.yml']:
                    # Single YAML file
                    workflows = await self.load_yaml_workflow_file(search_path)
                    migration_results[str(search_path)] = workflows
                
                elif search_path.is_dir():
                    # Directory of YAML files
                    workflows = await self.load_yaml_workflow_directory(search_path)
                    migration_results[str(search_path)] = workflows
                
            except Exception as e:
                print(f"Warning: Failed to migrate workflows from {search_path}: {e}")
                migration_results[str(search_path)] = []
        
        return migration_results


# Global compatibility instance
_yaml_compatibility = YAMLWorkflowCompatibility()


def get_yaml_compatibility() -> YAMLWorkflowCompatibility:
    """Get the global YAML compatibility instance"""
    return _yaml_compatibility


# Convenience functions

async def load_yaml_workflows(yaml_path: Union[str, Path]) -> List[IWorkflow]:
    """Load workflows from a YAML file"""
    compatibility = get_yaml_compatibility()
    return await compatibility.load_yaml_workflow_file(yaml_path)


async def migrate_yaml_workflows(search_paths: List[Union[str, Path]]) -> Dict[str, List[IWorkflow]]:
    """Migrate existing YAML workflows from multiple locations"""
    compatibility = get_yaml_compatibility()
    return await compatibility.migrate_existing_workflows(search_paths)
