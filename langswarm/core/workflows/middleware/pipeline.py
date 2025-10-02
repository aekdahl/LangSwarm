"""
Enhanced Workflow Middleware Pipeline

Advanced pipeline implementation specifically designed for workflow execution
with V2 middleware integration, routing, validation, and optimization.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from langswarm.core.middleware import (
    Pipeline, PipelineBuilder, IRequestContext, IResponseContext,
    RequestContext, ResponseContext, ResponseStatus
)
from langswarm.core.errors import handle_error, ErrorContext

from .interceptors import (
    WorkflowRoutingInterceptor,
    WorkflowValidationInterceptor, 
    WorkflowContextEnrichmentInterceptor,
    WorkflowResultTransformationInterceptor,
    WorkflowAuditInterceptor,
    WorkflowPolicy,
    WorkflowRoutingConfig,
    create_workflow_interceptors
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPipelineConfig:
    """Configuration for workflow middleware pipeline"""
    enable_routing: bool = True
    enable_validation: bool = True
    enable_context_enrichment: bool = True
    enable_result_transformation: bool = True
    enable_audit_logging: bool = True
    routing_config: Optional[WorkflowRoutingConfig] = None
    policies: Optional[Dict[str, WorkflowPolicy]] = None
    transformation_config: Optional[Dict[str, Any]] = None
    audit_config: Optional[Dict[str, Any]] = None
    performance_monitoring: bool = True
    error_recovery: bool = True


class WorkflowMiddlewarePipeline(Pipeline):
    """
    Enhanced middleware pipeline specifically optimized for workflow execution.
    
    Provides:
    - Workflow-aware request routing and prioritization
    - Comprehensive validation and policy enforcement
    - Context enrichment with workflow metadata
    - Result transformation and formatting
    - Audit logging and compliance tracking
    """
    
    def __init__(self, config: Optional[WorkflowPipelineConfig] = None):
        """
        Initialize workflow-enhanced pipeline.
        
        Args:
            config: Workflow pipeline configuration
        """
        self.config = config or WorkflowPipelineConfig()
        self.performance_metrics = {}
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0
        }
        
        # Initialize with workflow-specific interceptors
        workflow_interceptors = self._create_workflow_interceptors()
        super().__init__(workflow_interceptors)
        
        logger.info(f"Initialized WorkflowMiddlewarePipeline with {len(workflow_interceptors)} interceptors")
    
    def _create_workflow_interceptors(self) -> List:
        """Create workflow-specific interceptors based on configuration"""
        
        interceptors = []
        
        # Add routing interceptor
        if self.config.enable_routing:
            interceptors.append(WorkflowRoutingInterceptor(self.config.routing_config))
        
        # Add validation interceptor
        if self.config.enable_validation:
            interceptors.append(WorkflowValidationInterceptor(self.config.policies))
        
        # Add context enrichment interceptor
        if self.config.enable_context_enrichment:
            interceptors.append(WorkflowContextEnrichmentInterceptor())
        
        # Add result transformation interceptor
        if self.config.enable_result_transformation:
            interceptors.append(WorkflowResultTransformationInterceptor(self.config.transformation_config))
        
        # Add audit interceptor
        if self.config.enable_audit_logging:
            interceptors.append(WorkflowAuditInterceptor(self.config.audit_config))
        
        return interceptors
    
    async def process(self, context: IRequestContext) -> IResponseContext:
        """
        Process workflow request through enhanced middleware pipeline.
        
        Args:
            context: Request context containing workflow execution details
            
        Returns:
            Response context with workflow results and metadata
        """
        
        start_time = time.time()
        execution_id = f"exec-{int(time.time() * 1000000)}"
        
        try:
            # Add pipeline execution metadata
            context.metadata.update({
                "pipeline_type": "workflow_enhanced",
                "pipeline_execution_id": execution_id,
                "pipeline_start_time": start_time,
                "pipeline_config": {
                    "routing_enabled": self.config.enable_routing,
                    "validation_enabled": self.config.enable_validation,
                    "audit_enabled": self.config.enable_audit_logging
                }
            })
            
            # Execute through pipeline
            response = await super().process(context)
            
            # Update performance metrics
            execution_time = time.time() - start_time
            await self._update_performance_metrics(execution_time, response.status)
            
            # Add pipeline metadata to response
            response.metadata.update({
                "pipeline_execution_id": execution_id,
                "pipeline_execution_time": execution_time,
                "pipeline_interceptor_count": self.interceptor_count,
                "pipeline_stats": self.execution_stats.copy()
            })
            
            logger.info(f"Workflow pipeline execution completed in {execution_time:.3f}s")
            return response
            
        except Exception as e:
            # Update error metrics
            await self._update_performance_metrics(time.time() - start_time, ResponseStatus.ERROR)
            
            error_context = ErrorContext(
                operation="workflow_pipeline_execution",
                component="WorkflowMiddlewarePipeline",
                details={
                    "execution_id": execution_id,
                    "workflow_id": context.params.get("workflow_id")
                },
                metadata={"pipeline_type": "workflow_enhanced"}
            )
            
            return await handle_error(e, error_context)
    
    async def _update_performance_metrics(self, execution_time: float, status: ResponseStatus):
        """Update pipeline performance metrics"""
        
        self.execution_stats["total_executions"] += 1
        
        if status == ResponseStatus.SUCCESS:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # Update average execution time
        total_time = (self.execution_stats["average_execution_time"] * 
                     (self.execution_stats["total_executions"] - 1) + execution_time)
        self.execution_stats["average_execution_time"] = total_time / self.execution_stats["total_executions"]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        
        success_rate = (self.execution_stats["successful_executions"] / 
                       max(self.execution_stats["total_executions"], 1)) * 100
        
        return {
            **self.execution_stats,
            "success_rate": success_rate,
            "error_rate": 100 - success_rate,
            "throughput": self.execution_stats["total_executions"] / max(self.execution_stats["average_execution_time"], 0.001)
        }
    
    def add_custom_interceptor(self, interceptor, position: str = "end"):
        """
        Add custom interceptor to pipeline.
        
        Args:
            interceptor: Custom interceptor to add
            position: Where to add ("start", "end", or priority number)
        """
        
        if position == "start":
            # Add at beginning with high priority
            interceptor.priority = 50
        elif position == "end":
            # Add at end with low priority
            interceptor.priority = 1100
        elif isinstance(position, int):
            interceptor.priority = position
        
        self.add_interceptor(interceptor)
        logger.info(f"Added custom interceptor {interceptor.name} at priority {interceptor.priority}")


def create_workflow_pipeline(config: Optional[WorkflowPipelineConfig] = None) -> WorkflowMiddlewarePipeline:
    """
    Create a standard workflow middleware pipeline.
    
    Args:
        config: Optional pipeline configuration
        
    Returns:
        Configured workflow middleware pipeline
    """
    
    return WorkflowMiddlewarePipeline(config)


def create_enhanced_workflow_pipeline(
    enable_all_features: bool = True,
    custom_policies: Optional[Dict[str, WorkflowPolicy]] = None,
    performance_optimized: bool = False
) -> WorkflowMiddlewarePipeline:
    """
    Create an enhanced workflow pipeline with advanced features.
    
    Args:
        enable_all_features: Enable all available features
        custom_policies: Custom workflow policies
        performance_optimized: Optimize for performance over features
        
    Returns:
        Enhanced workflow middleware pipeline
    """
    
    if performance_optimized:
        # Performance-optimized configuration
        config = WorkflowPipelineConfig(
            enable_routing=True,
            enable_validation=True,
            enable_context_enrichment=False,  # Disable for performance
            enable_result_transformation=False,  # Disable for performance
            enable_audit_logging=False,  # Disable for performance
            performance_monitoring=True,
            error_recovery=True
        )
    else:
        # Full-featured configuration
        config = WorkflowPipelineConfig(
            enable_routing=enable_all_features,
            enable_validation=enable_all_features,
            enable_context_enrichment=enable_all_features,
            enable_result_transformation=enable_all_features,
            enable_audit_logging=enable_all_features,
            policies=custom_policies,
            performance_monitoring=True,
            error_recovery=True
        )
    
    pipeline = WorkflowMiddlewarePipeline(config)
    
    logger.info(f"Created enhanced workflow pipeline (performance_optimized={performance_optimized})")
    return pipeline


def create_development_pipeline() -> WorkflowMiddlewarePipeline:
    """Create a development-friendly workflow pipeline with enhanced debugging"""
    
    config = WorkflowPipelineConfig(
        enable_routing=True,
        enable_validation=True,
        enable_context_enrichment=True,
        enable_result_transformation=True,
        enable_audit_logging=True,
        audit_config={"level": "comprehensive", "storage": "console"},
        transformation_config={"include_performance": True, "include_debug": True},
        performance_monitoring=True,
        error_recovery=True
    )
    
    return WorkflowMiddlewarePipeline(config)


def create_production_pipeline() -> WorkflowMiddlewarePipeline:
    """Create a production-ready workflow pipeline with optimized performance"""
    
    # Production-grade policies
    production_policies = {
        "default": WorkflowPolicy(
            max_execution_time=timedelta(minutes=15),
            max_steps=50,
            max_parallel_steps=5,
            retry_attempts=2,
            audit_level="standard",
            security_level="high"
        ),
        "critical": WorkflowPolicy(
            max_execution_time=timedelta(minutes=5),
            max_steps=25,
            max_parallel_steps=3,
            retry_attempts=1,
            require_approval=True,
            audit_level="comprehensive",
            security_level="critical"
        )
    }
    
    config = WorkflowPipelineConfig(
        enable_routing=True,
        enable_validation=True,
        enable_context_enrichment=True,
        enable_result_transformation=True,
        enable_audit_logging=True,
        policies=production_policies,
        audit_config={"level": "detailed", "storage": "database"},
        transformation_config={"include_performance": True},
        performance_monitoring=True,
        error_recovery=True
    )
    
    return WorkflowMiddlewarePipeline(config)


class WorkflowPipelineBuilder:
    """Builder for creating customized workflow pipelines"""
    
    def __init__(self):
        self.config = WorkflowPipelineConfig()
        self._custom_interceptors = []
    
    def with_routing(self, routing_config: Optional[WorkflowRoutingConfig] = None):
        """Enable routing with optional configuration"""
        self.config.enable_routing = True
        self.config.routing_config = routing_config
        return self
    
    def with_validation(self, policies: Optional[Dict[str, WorkflowPolicy]] = None):
        """Enable validation with optional policies"""
        self.config.enable_validation = True
        self.config.policies = policies
        return self
    
    def with_audit(self, audit_config: Optional[Dict[str, Any]] = None):
        """Enable audit logging with optional configuration"""
        self.config.enable_audit_logging = True
        self.config.audit_config = audit_config
        return self
    
    def with_context_enrichment(self, enabled: bool = True):
        """Enable or disable context enrichment"""
        self.config.enable_context_enrichment = enabled
        return self
    
    def with_result_transformation(self, transform_config: Optional[Dict[str, Any]] = None):
        """Enable result transformation with optional configuration"""
        self.config.enable_result_transformation = True
        self.config.transformation_config = transform_config
        return self
    
    def with_performance_monitoring(self, enabled: bool = True):
        """Enable or disable performance monitoring"""
        self.config.performance_monitoring = enabled
        return self
    
    def add_custom_interceptor(self, interceptor):
        """Add custom interceptor to pipeline"""
        self._custom_interceptors.append(interceptor)
        return self
    
    def build(self) -> WorkflowMiddlewarePipeline:
        """Build the configured workflow pipeline"""
        
        pipeline = WorkflowMiddlewarePipeline(self.config)
        
        # Add custom interceptors
        for interceptor in self._custom_interceptors:
            pipeline.add_interceptor(interceptor)
        
        return pipeline
