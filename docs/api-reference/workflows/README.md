# LangSwarm V2 Workflow System API Reference

**Complete API documentation for the LangSwarm V2 workflow orchestration system**

## 🎯 Overview

LangSwarm V2 introduces a completely modernized workflow system that replaces the complex 814+ line workflow executor with clean, type-safe V2 interfaces and a multi-mode execution engine. The new system provides intuitive workflow creation, comprehensive error handling, and production-ready performance optimization.

**Key Features:**
- **Type-Safe Interfaces**: Complete type coverage with proper generics and unions
- **Fluent Builder API**: Intuitive workflow creation with method chaining
- **Multi-Mode Execution**: Sync, async, streaming, and parallel execution modes
- **Dependency Resolution**: Automatic step ordering and parallel optimization
- **V2 Integration**: Seamless integration with V2 error handling and middleware
- **Production Ready**: Comprehensive monitoring, validation, and error recovery

---

## 🏗️ Workflow Architecture

### **Core Enums**

```python
from langswarm.core.workflows.interfaces import (
    WorkflowStatus, StepStatus, ExecutionMode, StepType
)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"         # Not yet started
    RUNNING = "running"         # Currently executing
    COMPLETED = "completed"     # Successfully finished
    FAILED = "failed"          # Failed with errors
    CANCELLED = "cancelled"     # User cancelled
    TIMEOUT = "timeout"        # Execution timed out

class StepStatus(Enum):
    """Individual step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ExecutionMode(Enum):
    """Workflow execution modes"""
    SYNC = "sync"              # Immediate execution with results
    ASYNC = "async"            # Background processing
    STREAMING = "streaming"    # Real-time step-by-step results
    PARALLEL = "parallel"      # Optimized parallel execution

class StepType(Enum):
    """Workflow step types"""
    AGENT = "agent"            # V2 agent integration
    TOOL = "tool"              # V2 tool system integration
    CONDITION = "condition"    # Conditional branching
    TRANSFORM = "transform"    # Data transformation
    CUSTOM = "custom"          # Custom step implementation
```

### **Data Classes**

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class WorkflowContext:
    """Context for workflow execution"""
    workflow_id: str
    execution_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class StepResult:
    """Result of individual step execution"""
    step_id: str
    step_type: StepType
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    step_results: Dict[str, StepResult]
    final_result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    context: Optional[WorkflowContext] = None
```

---

## 🔧 Core Interfaces

### **IWorkflow Interface**

```python
from langswarm.core.workflows.interfaces import IWorkflow

class IWorkflow:
    """Core workflow interface"""
    
    # Properties
    workflow_id: str
    name: str
    description: str
    steps: List[IWorkflowStep]
    
    # Lifecycle
    async def validate(self) -> bool:
        """Validate workflow configuration"""
        pass
    
    async def prepare(self, context: WorkflowContext) -> None:
        """Prepare workflow for execution"""
        pass
    
    async def execute(self, context: WorkflowContext, mode: ExecutionMode) -> WorkflowResult:
        """Execute the complete workflow"""
        pass
    
    async def get_dependencies(self) -> Dict[str, List[str]]:
        """Get step dependency mapping"""
        pass
```

### **IWorkflowStep Interface**

```python
from langswarm.core.workflows.interfaces import IWorkflowStep

class IWorkflowStep:
    """Base interface for workflow steps"""
    
    # Properties
    step_id: str
    step_type: StepType
    depends_on: List[str]
    timeout_seconds: Optional[int]
    retry_count: int
    
    # Execution
    async def execute(self, context: WorkflowContext, inputs: Dict[str, Any]) -> StepResult:
        """Execute this step with given inputs"""
        pass
    
    async def validate(self) -> bool:
        """Validate step configuration"""
        pass
    
    async def get_required_inputs(self) -> List[str]:
        """Get list of required input variables"""
        pass
    
    async def get_output_schema(self) -> Dict[str, Any]:
        """Get expected output schema"""
        pass
```

### **IWorkflowEngine Interface**

```python
from langswarm.core.workflows.interfaces import IWorkflowEngine

class IWorkflowEngine:
    """Workflow execution engine interface"""
    
    async def execute_workflow(
        self, 
        workflow: IWorkflow, 
        context: WorkflowContext, 
        mode: ExecutionMode = ExecutionMode.SYNC
    ) -> WorkflowResult:
        """Execute workflow in specified mode"""
        pass
    
    async def execute_workflow_stream(
        self, 
        workflow: IWorkflow, 
        context: WorkflowContext
    ) -> AsyncIterator[StepResult]:
        """Execute workflow with streaming results"""
        pass
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running workflow execution"""
        pass
    
    async def get_execution_status(self, execution_id: str) -> WorkflowResult:
        """Get current execution status"""
        pass
```

---

## 🎨 Fluent Builder API

### **WorkflowBuilder**

```python
from langswarm.core.workflows.builder import WorkflowBuilder

# Create workflow builder
builder = WorkflowBuilder(workflow_id="analysis", name="Data Analysis")

# Add steps with fluent API
workflow = (builder
    .add_agent_step("extract", "data_extractor", "${input}")
    .add_tool_step("validate", "data_validator", "${extract}")
    .add_condition_step("check", "${validate.valid}", "process", "error")
    .add_agent_step("process", "data_processor", "${validate.data}")
    .add_transform_step("format", "${process}", transform_function)
    .build())
```

### **Builder Methods**

#### **Step Creation Methods**

```python
# Agent steps - integrate with V2 agent system
builder.add_agent_step(
    step_id="analyze",
    agent_id="analyzer",
    prompt_template="${data}",
    depends_on=["extract"],
    timeout_seconds=30
)

# Tool steps - integrate with V2 tool system
builder.add_tool_step(
    step_id="search",
    tool_name="web_search",
    tool_input="${query}",
    depends_on=["prepare_query"]
)

# Condition steps - conditional workflow branching
builder.add_condition_step(
    step_id="decide",
    condition="${score} > 0.8",
    true_step="approve",
    false_step="review",
    depends_on=["scoring"]
)

# Transform steps - data transformation
builder.add_transform_step(
    step_id="normalize",
    input_template="${raw_data}",
    transform_function=normalize_data,
    depends_on=["extract"]
)

# Custom steps - user-defined step implementations
builder.add_custom_step(
    step_id="custom",
    step_implementation=CustomStepClass(),
    depends_on=["previous_step"]
)
```

#### **Configuration Methods**

```python
# Workflow configuration
builder.set_description("Comprehensive data analysis workflow")
builder.set_timeout(300)  # 5 minutes total timeout
builder.set_retry_policy(max_retries=3, retry_delay=1.0)
builder.set_error_strategy("continue")  # "fail_fast" or "continue"

# Variables and templates
builder.add_variable("threshold", 0.8)
builder.add_variable("output_format", "json")

# Validation
builder.require_input("data")
builder.require_input("config")
```

### **Specialized Builders**

#### **LinearWorkflowBuilder**

```python
from langswarm.core.workflows.builder import LinearWorkflowBuilder

# Create sequential workflow
linear_workflow = (LinearWorkflowBuilder("process_data")
    .then_agent("extract", "extractor", "${input}")
    .then_tool("validate", "validator", "${extract}")
    .then_agent("analyze", "analyzer", "${validate}")
    .then_transform("format", "${analyze}", format_output)
    .build())
```

#### **ParallelWorkflowBuilder**

```python
from langswarm.core.workflows.builder import ParallelWorkflowBuilder

# Create parallel workflow
parallel_workflow = (ParallelWorkflowBuilder("multi_analysis")
    .add_parallel_group([
        ("sentiment", "sentiment_analyzer", "${text}"),
        ("topics", "topic_extractor", "${text}"),
        ("entities", "entity_recognizer", "${text}")
    ])
    .then_agent("summarize", "summarizer", "${sentiment}, ${topics}, ${entities}")
    .build())
```

---

## 🚀 Step Type Implementations

### **AgentStep**

```python
from langswarm.core.workflows.base import AgentStep

# Create agent step
agent_step = AgentStep(
    step_id="analyze",
    agent_id="data_analyzer",
    prompt_template="Analyze this data: ${data}",
    depends_on=["extract"],
    timeout_seconds=60,
    retry_count=2
)

# Agent step features
- **Template Resolution**: `${variable}` syntax for dynamic prompts
- **V2 Agent Integration**: Uses V2 native agents
- **Error Handling**: Comprehensive error recovery
- **Result Caching**: Optional result caching
```

### **ToolStep**

```python
from langswarm.core.workflows.base import ToolStep

# Create tool step
tool_step = ToolStep(
    step_id="search",
    tool_name="web_search",
    tool_input="${query}",
    tool_config={"max_results": 10},
    depends_on=["prepare_query"]
)

# Tool step features
- **V2 Tool Integration**: Uses unified V2 tool system
- **Dynamic Input**: Template-based tool input resolution
- **Tool Configuration**: Per-step tool configuration
- **Result Processing**: Automatic result parsing
```

### **ConditionStep**

```python
from langswarm.core.workflows.base import ConditionStep

# Create condition step
condition_step = ConditionStep(
    step_id="quality_check",
    condition="${score} >= ${threshold}",
    true_step="approve",
    false_step="review",
    depends_on=["scoring"]
)

# Condition step features
- **Expression Evaluation**: Safe expression evaluation
- **Variable Substitution**: Dynamic condition evaluation
- **Branching Logic**: Conditional workflow paths
- **Complex Conditions**: Support for complex boolean logic
```

### **TransformStep**

```python
from langswarm.core.workflows.base import TransformStep

def normalize_data(data):
    """Custom transformation function"""
    return {
        "normalized": data.lower().strip(),
        "length": len(data),
        "timestamp": datetime.now().isoformat()
    }

# Create transform step
transform_step = TransformStep(
    step_id="normalize",
    input_template="${raw_data}",
    transform_function=normalize_data,
    depends_on=["extract"]
)

# Transform step features
- **Custom Functions**: User-defined transformation logic
- **Template Input**: Dynamic input resolution
- **Type Safety**: Input/output type validation
- **Error Handling**: Transformation error recovery
```

---

## ⚡ Execution Engine

### **Multi-Mode Execution**

```python
from langswarm.core.workflows import execute_workflow, execute_workflow_stream

# Synchronous execution - immediate results
result = await execute_workflow(
    workflow_id="analysis",
    inputs={"data": "sample data"},
    mode=ExecutionMode.SYNC
)

# Asynchronous execution - background processing
execution_id = await execute_workflow(
    workflow_id="analysis",
    inputs={"data": "sample data"},
    mode=ExecutionMode.ASYNC
)

# Check async execution status
status = await get_execution_status(execution_id)

# Streaming execution - real-time step results
async for step_result in execute_workflow_stream("analysis", {"data": "sample data"}):
    print(f"Step {step_result.step_id}: {step_result.status}")
    if step_result.status == StepStatus.COMPLETED:
        print(f"Result: {step_result.result}")

# Parallel execution - optimized parallel processing
result = await execute_workflow(
    workflow_id="analysis",
    inputs={"data": "sample data"},
    mode=ExecutionMode.PARALLEL
)
```

### **Execution Features**

#### **Dependency Resolution**
```python
# Automatic step ordering based on dependencies
workflow_engine = WorkflowEngine()

# Engine automatically resolves dependencies and creates execution plan
execution_plan = await workflow_engine.create_execution_plan(workflow)
print(f"Execution levels: {execution_plan.dependency_levels}")
print(f"Parallel groups: {execution_plan.parallel_groups}")
```

#### **Error Recovery**
```python
# Configure error handling strategies
workflow = (WorkflowBuilder("robust_analysis")
    .set_error_strategy("continue")  # Continue on step failures
    .set_retry_policy(max_retries=3, exponential_backoff=True)
    .add_recovery_step("cleanup", cleanup_function)
    .build())

# Error recovery in execution
result = await execute_workflow("robust_analysis", inputs)
if result.status == WorkflowStatus.FAILED:
    # Analyze step-by-step failures
    for step_id, step_result in result.step_results.items():
        if not step_result.status == StepStatus.COMPLETED:
            print(f"Step {step_id} failed: {step_result.error}")
```

#### **Timeout Management**
```python
# Per-step and workflow-level timeouts
workflow = (WorkflowBuilder("time_limited")
    .set_timeout(300)  # 5 minute workflow timeout
    .add_agent_step("fast", "agent1", "${input}", timeout_seconds=30)
    .add_agent_step("slow", "agent2", "${fast}", timeout_seconds=120)
    .build())
```

---

## 📊 Workflow Registry

### **Registration and Discovery**

```python
from langswarm.core.workflows import register_workflow, list_workflows

# Register workflow globally
register_workflow(workflow)

# Discover registered workflows
workflows = list_workflows()
for workflow_info in workflows:
    print(f"ID: {workflow_info.workflow_id}")
    print(f"Name: {workflow_info.name}")
    print(f"Steps: {len(workflow_info.steps)}")

# Get specific workflow
workflow = get_workflow("analysis")
```

### **Registry Features**

```python
from langswarm.core.workflows.base import WorkflowRegistry

# Global registry instance
registry = WorkflowRegistry()

# Thread-safe registration
await registry.register(workflow)

# Workflow discovery with filtering
analysis_workflows = await registry.find_workflows(category="analysis")
recent_workflows = await registry.find_workflows(created_after=datetime.now() - timedelta(days=7))

# Workflow metadata
metadata = await registry.get_workflow_metadata(workflow_id)
print(f"Created: {metadata.created_at}")
print(f"Last executed: {metadata.last_execution}")
print(f"Execution count: {metadata.execution_count}")
```

---

## 🔍 Monitoring and Observability

### **Execution Monitoring**

```python
from langswarm.core.workflows import list_executions, get_execution_status

# List all executions
executions = list_executions()
for execution in executions:
    print(f"Execution {execution.execution_id}: {execution.status}")
    print(f"Duration: {execution.total_duration_ms}ms")

# Monitor specific execution
execution_id = "exec_123"
status = await get_execution_status(execution_id)

# Real-time monitoring
if status.status == WorkflowStatus.RUNNING:
    # Get current step information
    current_steps = [
        step for step in status.step_results.values()
        if step.status == StepStatus.RUNNING
    ]
    print(f"Currently running: {[s.step_id for s in current_steps]}")
```

### **Performance Metrics**

```python
# Get detailed performance metrics
metrics = await workflow_engine.get_performance_metrics(workflow_id)

print(f"Average execution time: {metrics.avg_duration_ms}ms")
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Most common failure step: {metrics.common_failure_step}")
print(f"Parallel efficiency: {metrics.parallel_efficiency:.2%}")

# Step-level metrics
for step_id, step_metrics in metrics.step_metrics.items():
    print(f"Step {step_id}:")
    print(f"  Average duration: {step_metrics.avg_duration_ms}ms")
    print(f"  Success rate: {step_metrics.success_rate:.2%}")
    print(f"  Retry rate: {step_metrics.retry_rate:.2%}")
```

---

## 🧪 Testing and Validation

### **Workflow Validation**

```python
from langswarm.core.workflows.validator import WorkflowValidator

# Validate workflow before execution
validator = WorkflowValidator()
validation_result = await validator.validate_workflow(workflow)

if not validation_result.is_valid:
    print("Workflow validation failed:")
    for error in validation_result.errors:
        print(f"  - {error.message} (Step: {error.step_id})")
        
# Validation features
- **Dependency Validation**: Check for circular dependencies
- **Input Validation**: Verify required inputs are available
- **Type Validation**: Check input/output type compatibility
- **Resource Validation**: Verify agents and tools exist
```

### **Mock Execution**

```python
from langswarm.core.workflows.testing import MockWorkflowEngine

# Create mock engine for testing
mock_engine = MockWorkflowEngine()

# Configure mock step results
mock_engine.add_step_result("extract", StepResult(
    step_id="extract",
    step_type=StepType.AGENT,
    status=StepStatus.COMPLETED,
    result="extracted data"
))

# Test workflow with mocks
result = await mock_engine.execute_workflow(workflow, context)
assert result.status == WorkflowStatus.COMPLETED
```

---

## 📚 Factory Functions

### **Quick Workflow Creation**

```python
from langswarm.core.workflows.builder import (
    create_simple_workflow,
    create_analysis_workflow,
    create_approval_workflow,
    create_linear_workflow,
    create_parallel_workflow
)

# Simple agent chain
simple = create_simple_workflow(
    workflow_id="simple",
    name="Simple Chain",
    agents=["extractor", "analyzer", "formatter"]
)

# Analysis pattern
analysis = create_analysis_workflow(
    workflow_id="analysis",
    data_extractor="extractor",
    analyzer="analyzer",
    validator="validator"
)

# Approval workflow
approval = create_approval_workflow(
    workflow_id="approval",
    reviewer="reviewer",
    approver="approver",
    threshold=0.8
)

# Linear workflow
linear = create_linear_workflow("linear")
linear.then_agent("step1", "agent1", "${input}")
linear.then_tool("step2", "tool1", "${step1}")
workflow = linear.build()

# Parallel workflow
parallel = create_parallel_workflow("parallel")
parallel.add_parallel_agents(["agent1", "agent2", "agent3"])
parallel.then_agent("combine", "combiner", "${agent1}, ${agent2}, ${agent3}")
workflow = parallel.build()
```

---

## 🔄 Migration from V1

### **V1 vs V2 Comparison**

| Aspect | V1 Workflow System | V2 Workflow System | Improvement |
|--------|-------------------|-------------------|-------------|
| **Creation** | Complex YAML editing | `create_workflow().add_agent_step()` | 90% simpler |
| **Type Safety** | Runtime YAML validation | Compile-time type checking | 100% coverage |
| **Execution** | 3 complex modes | 4 clean, optimized modes | Better architecture |
| **Error Handling** | Basic try/catch | Comprehensive error system | Much better debugging |
| **Testing** | Difficult | Easy mocking and testing | 10x easier |
| **Integration** | Complex coupling | Clean V2 integration | Better modularity |

### **Migration Example**

```python
# V1 YAML Configuration (before)
workflow_config = """
workflows:
  analysis:
    name: "Data Analysis"
    steps:
      - id: extract
        type: agent
        agent: data_extractor
        input: "${input}"
      - id: analyze
        type: agent
        agent: analyzer
        input: "${extract}"
        depends_on: [extract]
"""

# V2 Fluent API (after)
workflow = (create_workflow("analysis", "Data Analysis")
    .add_agent_step("extract", "data_extractor", "${input}")
    .add_agent_step("analyze", "analyzer", "${extract}", depends_on=["extract"])
    .build())

# V2 Benefits
- **Type Safety**: Compile-time validation vs runtime YAML parsing
- **IDE Support**: Full autocomplete and error detection
- **Flexibility**: Easy to add complex logic and custom steps
- **Testing**: Built-in mocking and validation capabilities
```

---

**The LangSwarm V2 workflow system provides a modern, type-safe, and highly performant foundation for building complex workflow orchestrations with intuitive APIs and production-ready features.**
