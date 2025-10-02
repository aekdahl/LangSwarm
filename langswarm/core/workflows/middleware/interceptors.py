"""
Workflow-Specific V2 Middleware Interceptors

Advanced middleware interceptors specifically designed for workflow execution
with comprehensive policies, routing, validation, and optimization.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from langswarm.core.middleware import (
    BaseInterceptor, IRequestContext, IResponseContext, 
    RequestContext, ResponseContext, ResponseStatus
)
from langswarm.core.errors import handle_error, ErrorContext
from ..interfaces import WorkflowContext, WorkflowResult, WorkflowStatus, ExecutionMode
from ..engine import get_workflow_engine
from ..monitoring import get_workflow_monitor

logger = logging.getLogger(__name__)


class WorkflowRequestType(Enum):
    """Types of workflow requests"""
    WORKFLOW_EXECUTION = "workflow_execution"
    WORKFLOW_STEP = "workflow_step"
    WORKFLOW_MONITORING = "workflow_monitoring"
    WORKFLOW_VALIDATION = "workflow_validation"
    WORKFLOW_TEMPLATE = "workflow_template"


class WorkflowComplexity(Enum):
    """Workflow complexity levels for routing"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class WorkflowPolicy:
    """Workflow execution policy configuration"""
    max_execution_time: timedelta = timedelta(minutes=30)
    max_steps: int = 100
    max_parallel_steps: int = 10
    retry_attempts: int = 3
    require_approval: bool = False
    audit_level: str = "standard"  # none, standard, detailed, comprehensive
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    security_level: str = "standard"  # basic, standard, high, critical


@dataclass 
class WorkflowRoutingConfig:
    """Configuration for workflow request routing"""
    complexity_thresholds: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "simple": {"max_steps": 10, "max_execution_time": 300},
        "medium": {"max_steps": 50, "max_execution_time": 1800},
        "complex": {"max_steps": 100, "max_execution_time": 3600},
        "enterprise": {"max_steps": 500, "max_execution_time": 7200}
    })
    routing_strategies: Dict[str, str] = field(default_factory=lambda: {
        "simple": "fast_lane",
        "medium": "standard_lane", 
        "complex": "heavy_lane",
        "enterprise": "dedicated_cluster"
    })


class WorkflowRoutingInterceptor(BaseInterceptor):
    """
    Advanced workflow request routing based on complexity and type.
    
    Routes workflows to appropriate execution lanes based on:
    - Workflow complexity and step count
    - Resource requirements and constraints
    - Security and compliance requirements
    - Performance and SLA requirements
    """
    
    def __init__(self, config: Optional[WorkflowRoutingConfig] = None):
        super().__init__()
        self.config = config or WorkflowRoutingConfig()
        self.engine = get_workflow_engine()
        
    @property
    def name(self) -> str:
        return "workflow_routing"
    
    @property
    def priority(self) -> int:
        return 100  # High priority - route early
    
    def can_handle(self, context: IRequestContext) -> bool:
        """Check if this is a workflow request"""
        return context.action in ["workflow_execution", "execute_workflow", "run_workflow"]
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """Route workflow requests based on complexity and requirements"""
        
        start_time = time.time()
        
        try:
            # Analyze workflow complexity
            complexity = await self._analyze_workflow_complexity(context)
            
            # Determine routing strategy  
            routing_strategy = self._get_routing_strategy(complexity)
            
            # Enrich context with routing information
            context.metadata.update({
                "workflow_complexity": complexity.value,
                "routing_strategy": routing_strategy,
                "routing_timestamp": datetime.utcnow().isoformat(),
                "estimated_resources": await self._estimate_resources(context, complexity)
            })
            
            # Route to appropriate execution lane
            routed_context = await self._route_to_execution_lane(context, routing_strategy)
            
            # Log routing decision
            logger.info(
                f"Routed workflow {context.params.get('workflow_id', 'unknown')} "
                f"to {routing_strategy} lane (complexity: {complexity.value})"
            )
            
            # Continue to next interceptor
            response = await next_interceptor(routed_context)
            
            # Add routing metrics to response
            response.metadata.update({
                "routing_time": time.time() - start_time,
                "routing_strategy_used": routing_strategy,
                "complexity_detected": complexity.value
            })
            
            return response
            
        except Exception as e:
            error_context = ErrorContext(
                operation="workflow_routing",
                component="WorkflowRoutingInterceptor",
                details={"workflow_id": context.params.get("workflow_id")},
                metadata={"interceptor": self.name}
            )
            return await handle_error(e, error_context)
    
    async def _analyze_workflow_complexity(self, context: IRequestContext) -> WorkflowComplexity:
        """Analyze workflow to determine complexity level"""
        
        workflow_id = context.params.get("workflow_id")
        if not workflow_id:
            return WorkflowComplexity.SIMPLE
        
        try:
            # Get workflow definition
            from .. import get_workflow
            workflow = await get_workflow(workflow_id)
            
            if not workflow:
                return WorkflowComplexity.SIMPLE
            
            # Count steps and analyze structure
            step_count = len(workflow.steps) if hasattr(workflow, 'steps') else 1
            parallel_steps = sum(1 for step in workflow.steps if getattr(step, 'parallel', False)) if hasattr(workflow, 'steps') else 0
            
            # Check for complex patterns
            has_loops = any(getattr(step, 'step_type', '') == 'loop' for step in workflow.steps) if hasattr(workflow, 'steps') else False
            has_conditions = any(getattr(step, 'step_type', '') == 'condition' for step in workflow.steps) if hasattr(workflow, 'steps') else False
            has_agents = any(getattr(step, 'step_type', '') == 'agent' for step in workflow.steps) if hasattr(workflow, 'steps') else False
            
            # Determine complexity
            if step_count <= 10 and not has_loops and not has_agents:
                return WorkflowComplexity.SIMPLE
            elif step_count <= 50 and parallel_steps <= 5:
                return WorkflowComplexity.MEDIUM
            elif step_count <= 100 or has_loops or has_agents:
                return WorkflowComplexity.COMPLEX
            else:
                return WorkflowComplexity.ENTERPRISE
                
        except Exception as e:
            logger.warning(f"Failed to analyze workflow complexity: {e}")
            return WorkflowComplexity.MEDIUM
    
    def _get_routing_strategy(self, complexity: WorkflowComplexity) -> str:
        """Get routing strategy for given complexity"""
        return self.config.routing_strategies.get(complexity.value, "standard_lane")
    
    async def _estimate_resources(self, context: IRequestContext, complexity: WorkflowComplexity) -> Dict[str, Any]:
        """Estimate resource requirements for workflow"""
        
        base_resources = {
            WorkflowComplexity.SIMPLE: {"cpu": 0.1, "memory": "128MB", "timeout": 300},
            WorkflowComplexity.MEDIUM: {"cpu": 0.5, "memory": "512MB", "timeout": 1800},
            WorkflowComplexity.COMPLEX: {"cpu": 1.0, "memory": "1GB", "timeout": 3600},
            WorkflowComplexity.ENTERPRISE: {"cpu": 2.0, "memory": "4GB", "timeout": 7200}
        }
        
        return base_resources.get(complexity, base_resources[WorkflowComplexity.MEDIUM])
    
    async def _route_to_execution_lane(self, context: IRequestContext, strategy: str) -> IRequestContext:
        """Route context to specific execution lane"""
        
        # Add execution lane information
        context.metadata.update({
            "execution_lane": strategy,
            "lane_assignment_time": datetime.utcnow().isoformat()
        })
        
        # Configure execution parameters based on lane
        lane_config = {
            "fast_lane": {"priority": "high", "max_concurrent": 100},
            "standard_lane": {"priority": "normal", "max_concurrent": 50},
            "heavy_lane": {"priority": "low", "max_concurrent": 10},
            "dedicated_cluster": {"priority": "dedicated", "max_concurrent": 5}
        }
        
        config = lane_config.get(strategy, lane_config["standard_lane"])
        context.metadata.update(config)
        
        return context


class WorkflowValidationInterceptor(BaseInterceptor):
    """
    Comprehensive workflow validation and policy enforcement.
    
    Validates:
    - Workflow definition and structure
    - Security policies and permissions
    - Resource limits and quotas
    - Business rules and compliance
    """
    
    def __init__(self, policies: Optional[Dict[str, WorkflowPolicy]] = None):
        super().__init__()
        self.policies = policies or {"default": WorkflowPolicy()}
        
    @property
    def name(self) -> str:
        return "workflow_validation"
    
    @property
    def priority(self) -> int:
        return 200  # Run after routing
    
    def can_handle(self, context: IRequestContext) -> bool:
        """Check if this is a workflow request that needs validation"""
        return context.action in ["workflow_execution", "execute_workflow", "run_workflow"]
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """Validate workflow request against policies"""
        
        start_time = time.time()
        
        try:
            # Get applicable policy
            policy = self._get_policy(context)
            
            # Perform validation checks
            validation_results = await self._validate_workflow_request(context, policy)
            
            if not validation_results["valid"]:
                return ResponseContext(
                    status=ResponseStatus.ERROR,
                    data={"error": "Workflow validation failed", "details": validation_results["errors"]},
                    metadata={
                        "validation_time": time.time() - start_time,
                        "policy_applied": policy.audit_level,
                        "interceptor": self.name
                    }
                )
            
            # Enrich context with validation metadata
            context.metadata.update({
                "validation_passed": True,
                "policy_applied": policy.audit_level,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "security_level": policy.security_level
            })
            
            # Continue to next interceptor
            response = await next_interceptor(context)
            
            # Add validation metrics
            response.metadata.update({
                "validation_time": time.time() - start_time,
                "validation_checks": len(validation_results.get("checks_performed", []))
            })
            
            return response
            
        except Exception as e:
            error_context = ErrorContext(
                operation="workflow_validation",
                component="WorkflowValidationInterceptor",
                details={"workflow_id": context.params.get("workflow_id")},
                metadata={"interceptor": self.name}
            )
            return await handle_error(e, error_context)
    
    def _get_policy(self, context: IRequestContext) -> WorkflowPolicy:
        """Get applicable policy for workflow"""
        
        # Check for specific policy in context
        policy_name = context.metadata.get("policy_name", "default")
        
        # Check for department/user-specific policies
        if "department" in context.metadata:
            dept_policy = f"dept_{context.metadata['department']}"
            if dept_policy in self.policies:
                policy_name = dept_policy
        
        return self.policies.get(policy_name, self.policies["default"])
    
    async def _validate_workflow_request(self, context: IRequestContext, policy: WorkflowPolicy) -> Dict[str, Any]:
        """Perform comprehensive workflow validation"""
        
        errors = []
        checks_performed = []
        
        # Validate workflow exists
        workflow_id = context.params.get("workflow_id")
        if not workflow_id:
            errors.append("Missing workflow_id in request")
        else:
            checks_performed.append("workflow_id_present")
            
            # Validate workflow definition
            try:
                from .. import get_workflow
                workflow = await get_workflow(workflow_id)
                if not workflow:
                    errors.append(f"Workflow {workflow_id} not found")
                else:
                    checks_performed.append("workflow_exists")
                    
                    # Validate against policy limits
                    step_count = len(workflow.steps) if hasattr(workflow, 'steps') else 1
                    if step_count > policy.max_steps:
                        errors.append(f"Workflow exceeds maximum steps: {step_count} > {policy.max_steps}")
                    else:
                        checks_performed.append("step_count_valid")
                        
            except Exception as e:
                errors.append(f"Failed to validate workflow: {str(e)}")
        
        # Validate input data
        input_data = context.params.get("input_data", {})
        if not isinstance(input_data, dict):
            errors.append("Input data must be a dictionary")
        else:
            checks_performed.append("input_data_format")
        
        # Validate execution mode
        execution_mode = context.params.get("execution_mode", "sync")
        if execution_mode not in ["sync", "async", "streaming", "parallel"]:
            errors.append(f"Invalid execution mode: {execution_mode}")
        else:
            checks_performed.append("execution_mode_valid")
        
        # Validate user permissions (if applicable)
        user_id = context.metadata.get("user_id")
        if policy.require_approval and not user_id:
            errors.append("User ID required for workflows requiring approval")
        else:
            checks_performed.append("user_authorization")
        
        # Validate resource constraints
        estimated_resources = context.metadata.get("estimated_resources", {})
        if policy.resource_limits:
            for resource, limit in policy.resource_limits.items():
                if resource in estimated_resources and estimated_resources[resource] > limit:
                    errors.append(f"Resource limit exceeded for {resource}: {estimated_resources[resource]} > {limit}")
            checks_performed.append("resource_limits")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "checks_performed": checks_performed,
            "policy_applied": policy.audit_level
        }


class WorkflowContextEnrichmentInterceptor(BaseInterceptor):
    """
    Enrich workflow context with additional metadata and variables.
    
    Adds:
    - Environment and system information
    - User and session context
    - Performance tracking metadata
    - Security and audit information
    """
    
    def __init__(self):
        super().__init__()
        self.monitor = get_workflow_monitor()
        
    @property
    def name(self) -> str:
        return "workflow_context_enrichment"
    
    @property 
    def priority(self) -> int:
        return 300  # Run after validation
    
    def can_handle(self, context: IRequestContext) -> bool:
        """Check if this is a workflow request"""
        return context.action in ["workflow_execution", "execute_workflow", "run_workflow"]
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """Enrich workflow context with comprehensive metadata"""
        
        start_time = time.time()
        
        try:
            # Enrich with system context
            await self._add_system_context(context)
            
            # Enrich with performance tracking
            await self._add_performance_context(context)
            
            # Enrich with security context
            await self._add_security_context(context)
            
            # Enrich with workflow-specific context
            await self._add_workflow_context(context)
            
            # Continue to next interceptor
            response = await next_interceptor(context)
            
            # Add enrichment metrics
            response.metadata.update({
                "context_enrichment_time": time.time() - start_time,
                "enrichment_items_added": len([k for k in context.metadata.keys() if k.startswith("enriched_")])
            })
            
            return response
            
        except Exception as e:
            error_context = ErrorContext(
                operation="workflow_context_enrichment",
                component="WorkflowContextEnrichmentInterceptor",
                details={"workflow_id": context.params.get("workflow_id")},
                metadata={"interceptor": self.name}
            )
            return await handle_error(e, error_context)
    
    async def _add_system_context(self, context: IRequestContext):
        """Add system and environment context"""
        context.metadata.update({
            "enriched_system_timestamp": datetime.utcnow().isoformat(),
            "enriched_system_version": "v2.0.0",
            "enriched_system_component": "workflow_system",
            "enriched_system_instance_id": f"ws-{int(time.time())}"
        })
    
    async def _add_performance_context(self, context: IRequestContext):
        """Add performance tracking context"""
        context.metadata.update({
            "enriched_perf_start_time": time.time(),
            "enriched_perf_request_id": context.metadata.get("request_id", f"req-{int(time.time())}"),
            "enriched_perf_trace_id": f"trace-{int(time.time() * 1000000)}",
            "enriched_perf_complexity": context.metadata.get("workflow_complexity", "unknown")
        })
    
    async def _add_security_context(self, context: IRequestContext):
        """Add security and audit context"""
        context.metadata.update({
            "enriched_security_level": context.metadata.get("security_level", "standard"),
            "enriched_security_audit_required": context.metadata.get("policy_applied", "standard") in ["detailed", "comprehensive"],
            "enriched_security_user_id": context.metadata.get("user_id", "anonymous"),
            "enriched_security_session_id": context.metadata.get("session_id", f"session-{int(time.time())}")
        })
    
    async def _add_workflow_context(self, context: IRequestContext):
        """Add workflow-specific context"""
        workflow_id = context.params.get("workflow_id")
        if workflow_id:
            context.metadata.update({
                "enriched_workflow_id": workflow_id,
                "enriched_workflow_execution_id": f"exec-{workflow_id}-{int(time.time())}",
                "enriched_workflow_retry_count": 0,
                "enriched_workflow_parent_execution": context.metadata.get("parent_execution_id")
            })


class WorkflowResultTransformationInterceptor(BaseInterceptor):
    """
    Transform and format workflow execution results.
    
    Handles:
    - Result serialization and formatting
    - Output filtering and sanitization
    - Response structure standardization
    - Error result transformation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        
    @property
    def name(self) -> str:
        return "workflow_result_transformation"
    
    @property
    def priority(self) -> int:
        return 900  # Run late in pipeline to transform results
    
    def can_handle(self, context: IRequestContext) -> bool:
        """Check if this is a workflow request"""
        return context.action in ["workflow_execution", "execute_workflow", "run_workflow"]
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """Transform workflow execution results"""
        
        start_time = time.time()
        
        try:
            # Execute workflow through remaining pipeline
            response = await next_interceptor(context)
            
            # Transform the response
            transformed_response = await self._transform_workflow_result(response, context)
            
            # Add transformation metrics
            transformed_response.metadata.update({
                "transformation_time": time.time() - start_time,
                "original_status": response.status.value if hasattr(response.status, 'value') else str(response.status),
                "transformation_applied": True
            })
            
            return transformed_response
            
        except Exception as e:
            error_context = ErrorContext(
                operation="workflow_result_transformation",
                component="WorkflowResultTransformationInterceptor",
                details={"workflow_id": context.params.get("workflow_id")},
                metadata={"interceptor": self.name}
            )
            return await handle_error(e, error_context)
    
    async def _transform_workflow_result(self, response: IResponseContext, context: IRequestContext) -> IResponseContext:
        """Transform workflow result based on configuration and requirements"""
        
        # Get transformation configuration
        transform_config = self.config.get("transform", {})
        output_format = context.params.get("output_format", "standard")
        
        # Create new response with transformed data
        transformed_data = response.data.copy() if isinstance(response.data, dict) else {"result": response.data}
        
        # Add workflow execution metadata
        transformed_data["workflow_execution"] = {
            "workflow_id": context.params.get("workflow_id"),
            "execution_id": context.metadata.get("enriched_workflow_execution_id"),
            "execution_mode": context.params.get("execution_mode", "sync"),
            "complexity": context.metadata.get("workflow_complexity"),
            "routing_strategy": context.metadata.get("routing_strategy"),
            "execution_time": response.metadata.get("execution_time"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add performance metrics
        if transform_config.get("include_performance", True):
            transformed_data["performance"] = {
                "total_execution_time": response.metadata.get("execution_time"),
                "routing_time": response.metadata.get("routing_time"),
                "validation_time": response.metadata.get("validation_time"),
                "context_enrichment_time": response.metadata.get("context_enrichment_time"),
                "step_count": response.metadata.get("step_count"),
                "parallel_steps": response.metadata.get("parallel_steps")
            }
        
        # Add audit trail if required
        audit_level = context.metadata.get("policy_applied", "standard")
        if audit_level in ["detailed", "comprehensive"]:
            transformed_data["audit"] = {
                "user_id": context.metadata.get("enriched_security_user_id"),
                "session_id": context.metadata.get("enriched_security_session_id"),
                "trace_id": context.metadata.get("enriched_perf_trace_id"),
                "validation_checks": response.metadata.get("validation_checks"),
                "security_level": context.metadata.get("enriched_security_level"),
                "compliance_verified": True
            }
        
        # Filter sensitive data based on security level
        if context.metadata.get("enriched_security_level") == "high":
            transformed_data = self._filter_sensitive_data(transformed_data)
        
        # Format output based on requested format
        if output_format == "minimal":
            transformed_data = {"result": transformed_data.get("result"), "status": "success" if response.status == ResponseStatus.SUCCESS else "error"}
        elif output_format == "detailed":
            # Keep all data as is
            pass
        
        return ResponseContext(
            status=response.status,
            data=transformed_data,
            metadata=response.metadata
        )
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive information from response data"""
        
        # List of sensitive fields to remove or mask
        sensitive_fields = ["password", "token", "secret", "key", "credential"]
        
        def filter_dict(d):
            if isinstance(d, dict):
                filtered = {}
                for k, v in d.items():
                    if any(sensitive in k.lower() for sensitive in sensitive_fields):
                        filtered[k] = "[FILTERED]"
                    else:
                        filtered[k] = filter_dict(v)
                return filtered
            elif isinstance(d, list):
                return [filter_dict(item) for item in d]
            else:
                return d
        
        return filter_dict(data)


class WorkflowAuditInterceptor(BaseInterceptor):
    """
    Comprehensive audit logging for workflow execution.
    
    Logs:
    - Workflow execution events and timeline
    - Security and compliance events
    - Performance and resource usage
    - Error and recovery events
    """
    
    def __init__(self, audit_config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.audit_config = audit_config or {"level": "standard", "storage": "database"}
        self.audit_logger = logging.getLogger("workflow_audit")
        
    @property
    def name(self) -> str:
        return "workflow_audit"
    
    @property
    def priority(self) -> int:
        return 1000  # Run last to capture complete execution
    
    def can_handle(self, context: IRequestContext) -> bool:
        """Check if this is a workflow request that needs auditing"""
        audit_level = context.metadata.get("policy_applied", "standard")
        return (context.action in ["workflow_execution", "execute_workflow", "run_workflow"] and 
                audit_level in ["detailed", "comprehensive"])
    
    async def intercept(
        self, 
        context: IRequestContext, 
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """Perform comprehensive audit logging"""
        
        start_time = time.time()
        audit_id = f"audit-{int(time.time() * 1000000)}"
        
        try:
            # Log workflow execution start
            await self._log_audit_event("workflow_execution_start", context, audit_id)
            
            # Execute workflow
            response = await next_interceptor(context)
            
            # Log workflow execution completion
            await self._log_audit_event("workflow_execution_complete", context, audit_id, response)
            
            # Add audit metadata to response
            response.metadata.update({
                "audit_id": audit_id,
                "audit_logged": True,
                "audit_time": time.time() - start_time
            })
            
            return response
            
        except Exception as e:
            # Log workflow execution failure
            await self._log_audit_event("workflow_execution_failed", context, audit_id, error=e)
            
            error_context = ErrorContext(
                operation="workflow_audit",
                component="WorkflowAuditInterceptor",
                details={"workflow_id": context.params.get("workflow_id"), "audit_id": audit_id},
                metadata={"interceptor": self.name}
            )
            return await handle_error(e, error_context)
    
    async def _log_audit_event(
        self, 
        event_type: str, 
        context: IRequestContext, 
        audit_id: str, 
        response: Optional[IResponseContext] = None,
        error: Optional[Exception] = None
    ):
        """Log comprehensive audit event"""
        
        audit_entry = {
            "audit_id": audit_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": context.params.get("workflow_id"),
            "execution_id": context.metadata.get("enriched_workflow_execution_id"),
            "user_id": context.metadata.get("enriched_security_user_id"),
            "session_id": context.metadata.get("enriched_security_session_id"),
            "trace_id": context.metadata.get("enriched_perf_trace_id"),
            "security_level": context.metadata.get("enriched_security_level"),
            "complexity": context.metadata.get("workflow_complexity"),
            "routing_strategy": context.metadata.get("routing_strategy"),
            "validation_passed": context.metadata.get("validation_passed"),
            "execution_mode": context.params.get("execution_mode"),
            "input_data_hash": self._hash_data(context.params.get("input_data", {}))
        }
        
        if response:
            audit_entry.update({
                "response_status": response.status.value if hasattr(response.status, 'value') else str(response.status),
                "execution_time": response.metadata.get("execution_time"),
                "step_count": response.metadata.get("step_count"),
                "parallel_steps": response.metadata.get("parallel_steps"),
                "output_data_hash": self._hash_data(response.data)
            })
        
        if error:
            audit_entry.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_traceback": str(error.__traceback__) if error.__traceback__ else None
            })
        
        # Log audit entry
        self.audit_logger.info(f"WORKFLOW_AUDIT: {audit_entry}")
        
        # Store audit entry based on configuration
        if self.audit_config.get("storage") == "database":
            await self._store_audit_entry(audit_entry)
    
    def _hash_data(self, data: Any) -> str:
        """Create hash of data for audit purposes"""
        import hashlib
        import json
        
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
        except Exception:
            return "hash_failed"
    
    async def _store_audit_entry(self, audit_entry: Dict[str, Any]):
        """Store audit entry in configured storage"""
        
        # This would integrate with your audit storage system
        # For now, we'll just ensure it's logged
        try:
            # TODO: Implement actual storage (database, file, etc.)
            pass
        except Exception as e:
            logger.error(f"Failed to store audit entry: {e}")


# Factory function for creating workflow interceptors
def create_workflow_interceptors(config: Optional[Dict[str, Any]] = None) -> List[BaseInterceptor]:
    """Create standard set of workflow middleware interceptors"""
    
    config = config or {}
    
    interceptors = [
        WorkflowRoutingInterceptor(config.get("routing")),
        WorkflowValidationInterceptor(config.get("policies")),
        WorkflowContextEnrichmentInterceptor(),
        WorkflowResultTransformationInterceptor(config.get("transformation")),
        WorkflowAuditInterceptor(config.get("audit"))
    ]
    
    return interceptors
