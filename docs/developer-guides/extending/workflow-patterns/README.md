# Building Custom Workflow Patterns for LangSwarm V2

**Complete guide for creating reusable workflow patterns and custom step types**

## 🎯 Overview

LangSwarm V2's workflow system is designed for extensibility, allowing developers to create custom workflow patterns, step types, and execution strategies. This guide shows you how to build reusable workflow components that integrate seamlessly with the V2 system.

**Custom Extension Types:**
- **Custom Step Types**: Implement specialized workflow steps
- **Workflow Patterns**: Create reusable workflow templates
- **Execution Strategies**: Custom execution modes and optimization
- **Validation Rules**: Custom workflow validation logic

---

## 🏗️ Custom Step Types

### **Implementing IWorkflowStep**

```python
from langswarm.core.workflows.interfaces import IWorkflowStep, StepType, StepStatus
from langswarm.core.workflows.base import StepResult
from langswarm.core.errors import WorkflowError, ErrorContext
from typing import Dict, Any, List
import asyncio

class CustomStepType(IWorkflowStep):
    """Custom workflow step implementation"""
    
    def __init__(
        self, 
        step_id: str,
        custom_config: Dict[str, Any],
        depends_on: List[str] = None,
        timeout_seconds: int = 60,
        retry_count: int = 0
    ):
        self.step_id = step_id
        self.step_type = StepType.CUSTOM
        self.custom_config = custom_config
        self.depends_on = depends_on or []
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
    
    async def execute(self, context: WorkflowContext, inputs: Dict[str, Any]) -> StepResult:
        """Execute the custom step logic"""
        start_time = datetime.now()
        
        try:
            # Custom step logic here
            result = await self._perform_custom_operation(context, inputs)
            
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.COMPLETED,
                result=result,
                start_time=start_time,
                end_time=datetime.now(),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def validate(self) -> bool:
        """Validate step configuration"""
        required_config = ["operation_type", "parameters"]
        return all(key in self.custom_config for key in required_config)
    
    async def get_required_inputs(self) -> List[str]:
        """Return list of required input variables"""
        return self.custom_config.get("required_inputs", [])
    
    async def get_output_schema(self) -> Dict[str, Any]:
        """Return expected output schema"""
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "metadata": {"type": "object"},
                "success": {"type": "boolean"}
            }
        }
    
    async def _perform_custom_operation(self, context: WorkflowContext, inputs: Dict[str, Any]) -> Any:
        """Implement your custom operation logic"""
        operation_type = self.custom_config["operation_type"]
        parameters = self.custom_config["parameters"]
        
        if operation_type == "data_processing":
            return await self._process_data(inputs, parameters)
        elif operation_type == "external_api":
            return await self._call_external_api(inputs, parameters)
        elif operation_type == "custom_analysis":
            return await self._perform_analysis(inputs, parameters)
        else:
            raise WorkflowError(f"Unknown operation type: {operation_type}")
```

### **Specialized Step Examples**

#### **Database Step**
```python
class DatabaseStep(IWorkflowStep):
    """Step for database operations"""
    
    def __init__(self, step_id: str, connection_string: str, query: str, **kwargs):
        self.step_id = step_id
        self.step_type = StepType.CUSTOM
        self.connection_string = connection_string
        self.query = query
        self.depends_on = kwargs.get("depends_on", [])
        self.timeout_seconds = kwargs.get("timeout_seconds", 30)
    
    async def execute(self, context: WorkflowContext, inputs: Dict[str, Any]) -> StepResult:
        """Execute database query"""
        start_time = datetime.now()
        
        try:
            # Resolve template variables in query
            resolved_query = self._resolve_template(self.query, inputs)
            
            # Execute database operation
            async with aiopg.create_pool(self.connection_string) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(resolved_query)
                        result = await cursor.fetchall()
            
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.COMPLETED,
                result={"rows": result, "count": len(result)},
                start_time=start_time,
                end_time=datetime.now()
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.FAILED,
                error=f"Database operation failed: {str(e)}",
                start_time=start_time,
                end_time=datetime.now()
            )
    
    def _resolve_template(self, template: str, inputs: Dict[str, Any]) -> str:
        """Resolve template variables in SQL query"""
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(inputs.get(var_name, f"${{{var_name}}}"))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)

# Usage in workflow
database_step = DatabaseStep(
    step_id="user_lookup",
    connection_string="postgresql://user:pass@localhost/db",
    query="SELECT * FROM users WHERE id = ${user_id}",
    depends_on=["extract_user_id"]
)
```

#### **HTTP API Step**
```python
class HTTPAPIStep(IWorkflowStep):
    """Step for HTTP API calls"""
    
    def __init__(self, step_id: str, url: str, method: str = "GET", **kwargs):
        self.step_id = step_id
        self.step_type = StepType.CUSTOM
        self.url = url
        self.method = method.upper()
        self.headers = kwargs.get("headers", {})
        self.timeout_seconds = kwargs.get("timeout_seconds", 30)
        self.depends_on = kwargs.get("depends_on", [])
    
    async def execute(self, context: WorkflowContext, inputs: Dict[str, Any]) -> StepResult:
        """Execute HTTP API call"""
        start_time = datetime.now()
        
        try:
            import httpx
            
            # Resolve URL template
            resolved_url = self._resolve_template(self.url, inputs)
            
            # Prepare request data
            request_data = self._prepare_request_data(inputs)
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                if self.method == "GET":
                    response = await client.get(resolved_url, headers=self.headers)
                elif self.method == "POST":
                    response = await client.post(resolved_url, json=request_data, headers=self.headers)
                elif self.method == "PUT":
                    response = await client.put(resolved_url, json=request_data, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {self.method}")
            
            response.raise_for_status()
            
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.COMPLETED,
                result={
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "headers": dict(response.headers)
                },
                start_time=start_time,
                end_time=datetime.now()
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                step_type=self.step_type,
                status=StepStatus.FAILED,
                error=f"HTTP API call failed: {str(e)}",
                start_time=start_time,
                end_time=datetime.now()
            )

# Usage in workflow
api_step = HTTPAPIStep(
    step_id="fetch_data",
    url="https://api.example.com/data/${category}",
    method="GET",
    headers={"Authorization": "Bearer ${api_token}"},
    depends_on=["prepare_params"]
)
```

---

## 🎨 Custom Workflow Patterns

### **Pattern Builder Base Class**

```python
from langswarm.core.workflows.builder import WorkflowBuilder
from abc import ABC, abstractmethod

class WorkflowPattern(ABC):
    """Base class for reusable workflow patterns"""
    
    def __init__(self, pattern_id: str, name: str):
        self.pattern_id = pattern_id
        self.name = name
        self.builder = WorkflowBuilder(pattern_id, name)
    
    @abstractmethod
    def configure(self, **kwargs) -> 'WorkflowPattern':
        """Configure the pattern with specific parameters"""
        pass
    
    @abstractmethod
    def build(self) -> IWorkflow:
        """Build the workflow from the pattern"""
        pass
    
    def set_common_config(self, **kwargs):
        """Set common workflow configuration"""
        if "timeout" in kwargs:
            self.builder.set_timeout(kwargs["timeout"])
        if "retry_policy" in kwargs:
            self.builder.set_retry_policy(**kwargs["retry_policy"])
        if "error_strategy" in kwargs:
            self.builder.set_error_strategy(kwargs["error_strategy"])
        return self
```

### **Data Processing Pattern**

```python
class DataProcessingPattern(WorkflowPattern):
    """Reusable pattern for data processing workflows"""
    
    def __init__(self, pattern_id: str):
        super().__init__(pattern_id, "Data Processing Pipeline")
        self.extractor = None
        self.validator = None
        self.processors = []
        self.formatter = None
    
    def configure(
        self,
        extractor: str,
        validator: str = None,
        processors: List[str] = None,
        formatter: str = None,
        **kwargs
    ) -> 'DataProcessingPattern':
        """Configure the data processing pipeline"""
        self.extractor = extractor
        self.validator = validator
        self.processors = processors or []
        self.formatter = formatter
        
        # Set common configuration
        self.set_common_config(**kwargs)
        
        return self
    
    def build(self) -> IWorkflow:
        """Build the data processing workflow"""
        # Start with extraction
        self.builder.add_agent_step(
            "extract", 
            self.extractor, 
            "Extract data from: ${input}"
        )
        
        last_step = "extract"
        
        # Add validation if specified
        if self.validator:
            self.builder.add_agent_step(
                "validate",
                self.validator,
                "Validate extracted data: ${extract}",
                depends_on=[last_step]
            )
            last_step = "validate"
        
        # Add processing steps
        for i, processor in enumerate(self.processors):
            step_id = f"process_{i+1}"
            self.builder.add_agent_step(
                step_id,
                processor,
                f"Process data: ${{{last_step}}}",
                depends_on=[last_step]
            )
            last_step = step_id
        
        # Add formatting if specified
        if self.formatter:
            self.builder.add_agent_step(
                "format",
                self.formatter,
                f"Format final output: ${{{last_step}}}",
                depends_on=[last_step]
            )
        
        return self.builder.build()

# Usage
data_pipeline = (DataProcessingPattern("data_analysis")
    .configure(
        extractor="text_extractor",
        validator="data_validator",
        processors=["sentiment_analyzer", "topic_extractor"],
        formatter="report_formatter",
        timeout=300,
        retry_policy={"max_retries": 2}
    )
    .build())
```

### **Approval Workflow Pattern**

```python
class ApprovalWorkflowPattern(WorkflowPattern):
    """Pattern for approval-based workflows"""
    
    def __init__(self, pattern_id: str):
        super().__init__(pattern_id, "Approval Workflow")
        self.reviewer = None
        self.approver = None
        self.threshold = 0.8
        self.auto_approve_condition = None
    
    def configure(
        self,
        reviewer: str,
        approver: str,
        threshold: float = 0.8,
        auto_approve_condition: str = None,
        **kwargs
    ) -> 'ApprovalWorkflowPattern':
        """Configure the approval workflow"""
        self.reviewer = reviewer
        self.approver = approver
        self.threshold = threshold
        self.auto_approve_condition = auto_approve_condition
        
        self.set_common_config(**kwargs)
        return self
    
    def build(self) -> IWorkflow:
        """Build the approval workflow"""
        # Initial review
        self.builder.add_agent_step(
            "review",
            self.reviewer,
            "Review and score (0-1): ${input}"
        )
        
        # Auto-approval check
        if self.auto_approve_condition:
            condition = self.auto_approve_condition
        else:
            condition = f"${{review.score}} >= {self.threshold}"
        
        self.builder.add_condition_step(
            "auto_approve_check",
            condition,
            "auto_approve",
            "manual_approval",
            depends_on=["review"]
        )
        
        # Auto approval path
        self.builder.add_agent_step(
            "auto_approve",
            "auto_approver",
            "Auto-approved based on review: ${review}",
            depends_on=["auto_approve_check"]
        )
        
        # Manual approval path
        self.builder.add_agent_step(
            "manual_approval",
            self.approver,
            "Manual approval needed for: ${input}. Review: ${review}",
            depends_on=["auto_approve_check"]
        )
        
        # Final status
        self.builder.add_transform_step(
            "final_status",
            "${auto_approve || manual_approval}",
            self._determine_final_status,
            depends_on=["auto_approve", "manual_approval"]
        )
        
        return self.builder.build()
    
    def _determine_final_status(self, approval_result):
        """Determine final approval status"""
        if approval_result:
            return {
                "status": "approved",
                "approval_type": "auto" if "auto" in str(approval_result) else "manual",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "rejected",
                "timestamp": datetime.now().isoformat()
            }

# Usage
approval_workflow = (ApprovalWorkflowPattern("document_approval")
    .configure(
        reviewer="document_reviewer",
        approver="manager",
        threshold=0.85,
        auto_approve_condition="${review.score} >= 0.9 and ${review.confidence} >= 0.95"
    )
    .build())
```

### **Multi-Stage Analysis Pattern**

```python
class MultiStageAnalysisPattern(WorkflowPattern):
    """Pattern for multi-stage analysis workflows"""
    
    def __init__(self, pattern_id: str):
        super().__init__(pattern_id, "Multi-Stage Analysis")
        self.analysis_stages = []
        self.synthesizer = None
        self.parallel_execution = True
    
    def configure(
        self,
        analysis_stages: List[Dict[str, str]],
        synthesizer: str,
        parallel_execution: bool = True,
        **kwargs
    ) -> 'MultiStageAnalysisPattern':
        """Configure the multi-stage analysis"""
        self.analysis_stages = analysis_stages
        self.synthesizer = synthesizer
        self.parallel_execution = parallel_execution
        
        self.set_common_config(**kwargs)
        return self
    
    def build(self) -> IWorkflow:
        """Build the multi-stage analysis workflow"""
        # Preparation step
        self.builder.add_agent_step(
            "prepare",
            "data_preparer",
            "Prepare data for analysis: ${input}"
        )
        
        if self.parallel_execution:
            # Parallel analysis
            parallel_steps = []
            for stage in self.analysis_stages:
                step_id = stage["id"]
                agent_id = stage["agent"]
                prompt = stage.get("prompt", f"Analyze with {agent_id}: ${{prepare}}")
                parallel_steps.append((step_id, agent_id, prompt))
            
            self.builder.add_parallel_group(
                parallel_steps,
                depends_on=["prepare"]
            )
            
            # Synthesis step depends on all parallel stages
            analysis_results = ", ".join([f"${{{step['id']}}}" for step in self.analysis_stages])
            
        else:
            # Sequential analysis
            last_step = "prepare"
            for stage in self.analysis_stages:
                step_id = stage["id"]
                agent_id = stage["agent"]
                prompt = stage.get("prompt", f"Analyze: ${{{last_step}}}")
                
                self.builder.add_agent_step(
                    step_id,
                    agent_id,
                    prompt,
                    depends_on=[last_step]
                )
                last_step = step_id
            
            # Use the last analysis result
            analysis_results = f"${{{last_step}}}"
        
        # Synthesis step
        self.builder.add_agent_step(
            "synthesize",
            self.synthesizer,
            f"Synthesize analysis results: {analysis_results}",
            depends_on=[stage["id"] for stage in self.analysis_stages]
        )
        
        return self.builder.build()

# Usage
analysis_workflow = (MultiStageAnalysisPattern("comprehensive_analysis")
    .configure(
        analysis_stages=[
            {"id": "sentiment", "agent": "sentiment_analyzer", "prompt": "Analyze sentiment: ${prepare}"},
            {"id": "topics", "agent": "topic_extractor", "prompt": "Extract topics: ${prepare}"},
            {"id": "entities", "agent": "entity_recognizer", "prompt": "Find entities: ${prepare}"},
            {"id": "summary", "agent": "summarizer", "prompt": "Summarize: ${prepare}"}
        ],
        synthesizer="result_synthesizer",
        parallel_execution=True
    )
    .build())
```

---

## ⚡ Custom Execution Strategies

### **Custom Execution Engine**

```python
from langswarm.core.workflows.interfaces import IWorkflowEngine

class CustomWorkflowEngine(IWorkflowEngine):
    """Custom workflow execution engine with specialized strategies"""
    
    def __init__(self, execution_strategy: str = "default"):
        self.execution_strategy = execution_strategy
        self.execution_history = []
    
    async def execute_workflow(
        self, 
        workflow: IWorkflow, 
        context: WorkflowContext,
        mode: ExecutionMode = ExecutionMode.SYNC
    ) -> WorkflowResult:
        """Execute workflow with custom strategy"""
        
        if self.execution_strategy == "cost_optimized":
            return await self._execute_cost_optimized(workflow, context)
        elif self.execution_strategy == "speed_optimized":
            return await self._execute_speed_optimized(workflow, context)
        elif self.execution_strategy == "reliability_optimized":
            return await self._execute_reliability_optimized(workflow, context)
        else:
            return await self._execute_default(workflow, context, mode)
    
    async def _execute_cost_optimized(self, workflow: IWorkflow, context: WorkflowContext) -> WorkflowResult:
        """Execute with cost optimization"""
        # Group steps by cost estimates
        step_costs = await self._estimate_step_costs(workflow.steps)
        
        # Execute cheap steps first, expensive steps only if necessary
        sorted_steps = sorted(workflow.steps, key=lambda s: step_costs.get(s.step_id, 0))
        
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_id=f"exec_{context.execution_id}",
            status=WorkflowStatus.RUNNING,
            step_results={}
        )
        
        for step in sorted_steps:
            # Check if we can skip this step based on previous results
            if await self._can_skip_step(step, result.step_results):
                continue
            
            step_result = await step.execute(context, self._get_step_inputs(step, result.step_results))
            result.step_results[step.step_id] = step_result
            
            if step_result.status == StepStatus.FAILED:
                result.status = WorkflowStatus.FAILED
                break
        
        if result.status != WorkflowStatus.FAILED:
            result.status = WorkflowStatus.COMPLETED
        
        return result
    
    async def _execute_speed_optimized(self, workflow: IWorkflow, context: WorkflowContext) -> WorkflowResult:
        """Execute with speed optimization"""
        # Aggressive parallelization
        dependency_graph = await self._build_dependency_graph(workflow.steps)
        execution_levels = await self._compute_execution_levels(dependency_graph)
        
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_id=f"exec_{context.execution_id}",
            status=WorkflowStatus.RUNNING,
            step_results={}
        )
        
        for level_steps in execution_levels:
            # Execute all steps in this level in parallel
            tasks = []
            for step in level_steps:
                task = asyncio.create_task(
                    step.execute(context, self._get_step_inputs(step, result.step_results))
                )
                tasks.append((step.step_id, task))
            
            # Wait for all tasks to complete
            for step_id, task in tasks:
                step_result = await task
                result.step_results[step_id] = step_result
                
                if step_result.status == StepStatus.FAILED:
                    result.status = WorkflowStatus.FAILED
                    # Cancel remaining tasks
                    for _, remaining_task in tasks:
                        if not remaining_task.done():
                            remaining_task.cancel()
                    return result
        
        result.status = WorkflowStatus.COMPLETED
        return result
    
    async def _execute_reliability_optimized(self, workflow: IWorkflow, context: WorkflowContext) -> WorkflowResult:
        """Execute with reliability optimization"""
        # Enhanced error handling and recovery
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_id=f"exec_{context.execution_id}",
            status=WorkflowStatus.RUNNING,
            step_results={}
        )
        
        for step in workflow.steps:
            max_attempts = step.retry_count + 1
            
            for attempt in range(max_attempts):
                try:
                    step_result = await step.execute(context, self._get_step_inputs(step, result.step_results))
                    
                    if step_result.status == StepStatus.COMPLETED:
                        result.step_results[step.step_id] = step_result
                        break
                    elif attempt < max_attempts - 1:
                        # Retry with exponential backoff
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        # Final attempt failed, try recovery
                        recovery_result = await self._attempt_step_recovery(step, context, step_result)
                        result.step_results[step.step_id] = recovery_result
                        
                        if recovery_result.status == StepStatus.FAILED:
                            result.status = WorkflowStatus.FAILED
                            return result
                        break
                        
                except Exception as e:
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        result.step_results[step.step_id] = StepResult(
                            step_id=step.step_id,
                            step_type=step.step_type,
                            status=StepStatus.FAILED,
                            error=str(e)
                        )
                        result.status = WorkflowStatus.FAILED
                        return result
        
        result.status = WorkflowStatus.COMPLETED
        return result
```

### **Priority-Based Execution**

```python
class PriorityWorkflowEngine(IWorkflowEngine):
    """Workflow engine that respects step priorities"""
    
    def __init__(self):
        self.priority_queue = asyncio.PriorityQueue()
        self.running_steps = {}
        self.max_concurrent_steps = 5
    
    async def execute_workflow(self, workflow: IWorkflow, context: WorkflowContext, mode: ExecutionMode = ExecutionMode.SYNC) -> WorkflowResult:
        """Execute workflow with priority-based scheduling"""
        
        # Assign priorities to steps
        step_priorities = await self._assign_priorities(workflow.steps)
        
        # Add initial steps to priority queue
        for step in workflow.steps:
            if not step.depends_on:  # Steps with no dependencies
                priority = step_priorities.get(step.step_id, 0)
                await self.priority_queue.put((priority, step))
        
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_id=f"exec_{context.execution_id}",
            status=WorkflowStatus.RUNNING,
            step_results={}
        )
        
        while not self.priority_queue.empty() or self.running_steps:
            # Start new steps if we have capacity
            while (len(self.running_steps) < self.max_concurrent_steps and 
                   not self.priority_queue.empty()):
                
                priority, step = await self.priority_queue.get()
                
                # Check if dependencies are satisfied
                if await self._dependencies_satisfied(step, result.step_results):
                    task = asyncio.create_task(
                        step.execute(context, self._get_step_inputs(step, result.step_results))
                    )
                    self.running_steps[step.step_id] = (step, task)
                else:
                    # Dependencies not satisfied, put back in queue with lower priority
                    await self.priority_queue.put((priority + 1, step))
            
            # Wait for at least one step to complete
            if self.running_steps:
                done, pending = await asyncio.wait(
                    [task for _, task in self.running_steps.values()],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    # Find which step completed
                    completed_step_id = None
                    for step_id, (step, step_task) in self.running_steps.items():
                        if step_task == task:
                            completed_step_id = step_id
                            break
                    
                    if completed_step_id:
                        step, _ = self.running_steps.pop(completed_step_id)
                        step_result = await task
                        result.step_results[completed_step_id] = step_result
                        
                        # Add dependent steps to queue
                        await self._add_dependent_steps(step, workflow.steps, step_priorities)
        
        result.status = WorkflowStatus.COMPLETED
        return result
    
    async def _assign_priorities(self, steps: List[IWorkflowStep]) -> Dict[str, int]:
        """Assign execution priorities to steps"""
        priorities = {}
        
        for step in steps:
            # Base priority on step type and configuration
            if step.step_type == StepType.AGENT:
                priorities[step.step_id] = 1  # High priority for AI steps
            elif step.step_type == StepType.TOOL:
                priorities[step.step_id] = 2  # Medium priority for tools
            elif step.step_type == StepType.CONDITION:
                priorities[step.step_id] = 0  # Highest priority for conditions
            else:
                priorities[step.step_id] = 3  # Lower priority for others
        
        return priorities
```

---

## 🔍 Custom Validation Rules

### **Workflow Validator Extension**

```python
from langswarm.core.workflows.validator import WorkflowValidator

class CustomWorkflowValidator(WorkflowValidator):
    """Extended workflow validator with custom rules"""
    
    def __init__(self, custom_rules: List[str] = None):
        super().__init__()
        self.custom_rules = custom_rules or []
    
    async def validate_workflow(self, workflow: IWorkflow) -> ValidationResult:
        """Validate workflow with custom rules"""
        # Run standard validation first
        result = await super().validate_workflow(workflow)
        
        # Apply custom validation rules
        for rule in self.custom_rules:
            custom_result = await self._apply_custom_rule(rule, workflow)
            result.errors.extend(custom_result.errors)
            result.warnings.extend(custom_result.warnings)
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def _apply_custom_rule(self, rule: str, workflow: IWorkflow) -> ValidationResult:
        """Apply a specific custom validation rule"""
        if rule == "no_single_points_of_failure":
            return await self._validate_no_spof(workflow)
        elif rule == "cost_limit_check":
            return await self._validate_cost_limits(workflow)
        elif rule == "performance_requirements":
            return await self._validate_performance(workflow)
        elif rule == "security_compliance":
            return await self._validate_security(workflow)
        else:
            return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    async def _validate_no_spof(self, workflow: IWorkflow) -> ValidationResult:
        """Validate that workflow has no single points of failure"""
        errors = []
        warnings = []
        
        # Find critical paths
        critical_steps = await self._find_critical_path(workflow.steps)
        
        for step_id in critical_steps:
            step = next(s for s in workflow.steps if s.step_id == step_id)
            
            # Check if critical step has backup or retry
            if step.retry_count == 0 and not await self._has_fallback(step, workflow.steps):
                errors.append(ValidationError(
                    message=f"Critical step '{step_id}' has no retry or fallback mechanism",
                    step_id=step_id,
                    suggestion="Add retry_count > 0 or configure a fallback step"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_cost_limits(self, workflow: IWorkflow) -> ValidationResult:
        """Validate workflow cost estimates"""
        errors = []
        warnings = []
        
        estimated_cost = await self._estimate_workflow_cost(workflow)
        
        if estimated_cost > 10.0:  # $10 limit
            errors.append(ValidationError(
                message=f"Estimated workflow cost ${estimated_cost:.2f} exceeds limit of $10.00",
                suggestion="Reduce number of expensive steps or add cost controls"
            ))
        elif estimated_cost > 5.0:  # $5 warning
            warnings.append(ValidationWarning(
                message=f"Estimated workflow cost ${estimated_cost:.2f} is high",
                suggestion="Consider optimizing expensive steps"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_performance(self, workflow: IWorkflow) -> ValidationResult:
        """Validate performance requirements"""
        errors = []
        warnings = []
        
        estimated_duration = await self._estimate_workflow_duration(workflow)
        
        if estimated_duration > 300:  # 5 minutes
            warnings.append(ValidationWarning(
                message=f"Estimated duration {estimated_duration}s may be too long",
                suggestion="Consider breaking into smaller workflows or adding parallelization"
            ))
        
        # Check for inefficient dependencies
        inefficient_deps = await self._find_inefficient_dependencies(workflow.steps)
        for step_id, suggestion in inefficient_deps.items():
            warnings.append(ValidationWarning(
                message=f"Step '{step_id}' has inefficient dependencies",
                step_id=step_id,
                suggestion=suggestion
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# Usage
custom_validator = CustomWorkflowValidator([
    "no_single_points_of_failure",
    "cost_limit_check", 
    "performance_requirements"
])

validation_result = await custom_validator.validate_workflow(my_workflow)
if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Error: {error.message}")
```

---

## 📚 Best Practices for Extensions

### **Design Principles**
- **Single Responsibility**: Each custom component should have one clear purpose
- **Interface Compliance**: Always implement the required interfaces properly
- **Error Handling**: Provide comprehensive error handling and recovery
- **Documentation**: Document custom components thoroughly

### **Performance Considerations**
- **Async/Await**: Use async patterns for non-blocking operations
- **Resource Management**: Properly manage connections, files, and other resources
- **Timeout Handling**: Implement appropriate timeouts for external operations
- **Memory Usage**: Be mindful of memory usage in long-running workflows

### **Testing Custom Extensions**
```python
import pytest
from langswarm.core.workflows.testing import WorkflowTestCase

class TestCustomStep(WorkflowTestCase):
    async def test_custom_step_execution(self):
        """Test custom step execution"""
        step = CustomStepType(
            step_id="test_step",
            custom_config={"operation_type": "test", "parameters": {}}
        )
        
        context = self.create_test_context()
        inputs = {"test_input": "test_value"}
        
        result = await step.execute(context, inputs)
        
        assert result.status == StepStatus.COMPLETED
        assert result.result is not None
    
    async def test_custom_pattern(self):
        """Test custom workflow pattern"""
        pattern = DataProcessingPattern("test_pattern")
        workflow = pattern.configure(
            extractor="test_extractor",
            processors=["test_processor"]
        ).build()
        
        # Validate pattern structure
        assert len(workflow.steps) >= 2  # Extract + Process
        assert any(step.step_id == "extract" for step in workflow.steps)
```

### **Documentation Template**
```python
class MyCustomStep(IWorkflowStep):
    """
    Custom workflow step for [specific purpose].
    
    This step performs [detailed description of what it does].
    
    Configuration:
        param1 (str): Description of parameter 1
        param2 (int): Description of parameter 2
        
    Inputs:
        input_name (type): Description of expected input
        
    Outputs:
        output_name (type): Description of output format
        
    Example:
        >>> step = MyCustomStep("my_step", param1="value", param2=42)
        >>> result = await step.execute(context, {"input_name": "data"})
        >>> print(result.result["output_name"])
        
    Raises:
        CustomStepError: When [specific error condition]
    """
```

---

**Building custom workflow patterns and step types extends LangSwarm V2's capabilities while maintaining the consistent, type-safe interface that makes complex workflow orchestration manageable and scalable.**
