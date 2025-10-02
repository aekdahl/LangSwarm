"""
Workflow Policy Management

Comprehensive policy management for workflow execution including
security policies, compliance policies, and resource management.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

from .interceptors import WorkflowPolicy

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of workflow policies"""
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RESOURCE = "resource"
    PERFORMANCE = "performance"
    BUSINESS = "business"


@dataclass
class SecurityPolicy(WorkflowPolicy):
    """Security-focused workflow policy"""
    encryption_required: bool = True
    access_logging: bool = True
    user_authentication: bool = True
    role_based_access: bool = True
    data_classification_check: bool = True
    
    def __post_init__(self):
        # Ensure security-appropriate defaults
        self.security_level = "high"
        self.audit_level = "comprehensive"
        self.require_approval = True


@dataclass 
class CompliancePolicy(WorkflowPolicy):
    """Compliance-focused workflow policy"""
    data_retention_days: int = 2555  # 7 years
    audit_trail_required: bool = True
    regulatory_framework: str = "SOX"  # SOX, GDPR, HIPAA, etc.
    data_residency_required: bool = False
    approval_workflow: bool = True
    
    def __post_init__(self):
        # Ensure compliance-appropriate defaults  
        self.audit_level = "comprehensive"
        self.require_approval = True


class PolicyManager:
    """
    Manager for workflow policies with support for policy inheritance,
    composition, and dynamic policy application.
    """
    
    def __init__(self):
        """Initialize policy manager"""
        self.policies: Dict[str, WorkflowPolicy] = {}
        self.policy_hierarchy: Dict[str, List[str]] = {}
        self.default_policies = self._create_default_policies()
        
        # Load default policies
        for name, policy in self.default_policies.items():
            self.add_policy(name, policy)
        
        logger.info("Initialized PolicyManager with default policies")
    
    def _create_default_policies(self) -> Dict[str, WorkflowPolicy]:
        """Create default policy set"""
        
        return {
            "default": WorkflowPolicy(
                max_execution_time=timedelta(minutes=30),
                max_steps=100,
                max_parallel_steps=10,
                retry_attempts=3,
                audit_level="standard",
                security_level="standard"
            ),
            
            "development": WorkflowPolicy(
                max_execution_time=timedelta(hours=2),
                max_steps=500,
                max_parallel_steps=20,
                retry_attempts=5,
                audit_level="basic",
                security_level="basic"
            ),
            
            "production": WorkflowPolicy(
                max_execution_time=timedelta(minutes=15),
                max_steps=50,
                max_parallel_steps=5,
                retry_attempts=2,
                audit_level="detailed",
                security_level="high"
            ),
            
            "security": SecurityPolicy(
                max_execution_time=timedelta(minutes=10),
                max_steps=25,
                max_parallel_steps=3,
                retry_attempts=1,
                encryption_required=True,
                access_logging=True,
                user_authentication=True
            ),
            
            "compliance": CompliancePolicy(
                max_execution_time=timedelta(minutes=20),
                max_steps=40,
                max_parallel_steps=4,
                retry_attempts=2,
                regulatory_framework="SOX",
                audit_trail_required=True
            ),
            
            "performance": WorkflowPolicy(
                max_execution_time=timedelta(minutes=5),
                max_steps=20,
                max_parallel_steps=2,
                retry_attempts=1,
                audit_level="basic",
                security_level="standard",
                resource_limits={"memory": "512MB", "cpu": "1.0"}
            )
        }
    
    def add_policy(self, name: str, policy: WorkflowPolicy):
        """Add or update a policy"""
        
        self.policies[name] = policy
        logger.info(f"Added policy: {name}")
    
    def get_policy(self, name: str) -> Optional[WorkflowPolicy]:
        """Get policy by name"""
        
        return self.policies.get(name)
    
    def remove_policy(self, name: str) -> bool:
        """Remove policy by name"""
        
        if name in self.policies:
            del self.policies[name]
            logger.info(f"Removed policy: {name}")
            return True
        return False
    
    def list_policies(self) -> List[str]:
        """List all available policy names"""
        
        return list(self.policies.keys())
    
    def create_composite_policy(
        self, 
        name: str, 
        base_policies: List[str],
        overrides: Optional[Dict[str, Any]] = None
    ) -> WorkflowPolicy:
        """
        Create composite policy by combining multiple base policies.
        
        Args:
            name: Name for the new composite policy
            base_policies: List of base policy names to combine
            overrides: Optional field overrides
            
        Returns:
            New composite policy
        """
        
        if not base_policies:
            raise ValueError("At least one base policy is required")
        
        # Start with first policy as base
        base_policy = self.get_policy(base_policies[0])
        if not base_policy:
            raise ValueError(f"Base policy not found: {base_policies[0]}")
        
        # Create new policy with base values
        composite = WorkflowPolicy(
            max_execution_time=base_policy.max_execution_time,
            max_steps=base_policy.max_steps,
            max_parallel_steps=base_policy.max_parallel_steps,
            retry_attempts=base_policy.retry_attempts,
            require_approval=base_policy.require_approval,
            audit_level=base_policy.audit_level,
            resource_limits=base_policy.resource_limits.copy(),
            security_level=base_policy.security_level
        )
        
        # Apply additional policies (most restrictive wins)
        for policy_name in base_policies[1:]:
            policy = self.get_policy(policy_name)
            if not policy:
                logger.warning(f"Policy not found: {policy_name}, skipping")
                continue
            
            # Apply most restrictive limits
            if policy.max_execution_time < composite.max_execution_time:
                composite.max_execution_time = policy.max_execution_time
            
            if policy.max_steps < composite.max_steps:
                composite.max_steps = policy.max_steps
            
            if policy.max_parallel_steps < composite.max_parallel_steps:
                composite.max_parallel_steps = policy.max_parallel_steps
            
            if policy.retry_attempts < composite.retry_attempts:
                composite.retry_attempts = policy.retry_attempts
            
            # Combine boolean flags (OR logic for restrictions)
            composite.require_approval = composite.require_approval or policy.require_approval
            
            # Use highest audit/security level
            audit_levels = {"none": 0, "basic": 1, "standard": 2, "detailed": 3, "comprehensive": 4}
            if audit_levels.get(policy.audit_level, 0) > audit_levels.get(composite.audit_level, 0):
                composite.audit_level = policy.audit_level
            
            security_levels = {"basic": 0, "standard": 1, "high": 2, "critical": 3}
            if security_levels.get(policy.security_level, 0) > security_levels.get(composite.security_level, 0):
                composite.security_level = policy.security_level
            
            # Merge resource limits (most restrictive)
            for resource, limit in policy.resource_limits.items():
                if resource not in composite.resource_limits:
                    composite.resource_limits[resource] = limit
                else:
                    # Compare limits (assume lower values are more restrictive)
                    try:
                        if float(str(limit).rstrip('MB GB TB')) < float(str(composite.resource_limits[resource]).rstrip('MB GB TB')):
                            composite.resource_limits[resource] = limit
                    except (ValueError, TypeError):
                        # If can't compare, keep existing
                        pass
        
        # Apply overrides
        if overrides:
            for field, value in overrides.items():
                if hasattr(composite, field):
                    setattr(composite, field, value)
        
        # Add to policy registry
        self.add_policy(name, composite)
        
        logger.info(f"Created composite policy: {name} from {base_policies}")
        return composite
    
    def get_applicable_policy(
        self, 
        context_metadata: Dict[str, Any]
    ) -> WorkflowPolicy:
        """
        Determine applicable policy based on context metadata.
        
        Args:
            context_metadata: Workflow execution context metadata
            
        Returns:
            Most appropriate policy for the context
        """
        
        # Check for explicit policy request
        if "policy_name" in context_metadata:
            policy_name = context_metadata["policy_name"]
            policy = self.get_policy(policy_name)
            if policy:
                logger.info(f"Using explicit policy: {policy_name}")
                return policy
            else:
                logger.warning(f"Requested policy not found: {policy_name}, using default")
        
        # Policy selection based on context
        policy_name = "default"
        
        # Security-sensitive workflows
        if context_metadata.get("data_classification") in ["confidential", "secret"]:
            policy_name = "security"
        elif context_metadata.get("compliance_required"):
            policy_name = "compliance"
        elif context_metadata.get("environment") == "production":
            policy_name = "production"
        elif context_metadata.get("environment") == "development":
            policy_name = "development"
        elif context_metadata.get("priority") == "high":
            policy_name = "performance"
        
        # Department-specific policies
        department = context_metadata.get("department")
        if department:
            dept_policy = f"dept_{department}"
            if dept_policy in self.policies:
                policy_name = dept_policy
        
        policy = self.get_policy(policy_name)
        logger.info(f"Selected policy: {policy_name} based on context")
        return policy or self.get_policy("default")
    
    def validate_policy(self, policy: WorkflowPolicy) -> Dict[str, List[str]]:
        """
        Validate policy configuration.
        
        Args:
            policy: Policy to validate
            
        Returns:
            Dictionary with validation results (errors, warnings)
        """
        
        errors = []
        warnings = []
        
        # Validate execution time
        if policy.max_execution_time.total_seconds() <= 0:
            errors.append("max_execution_time must be positive")
        elif policy.max_execution_time.total_seconds() > 86400:  # 24 hours
            warnings.append("max_execution_time is very long (>24 hours)")
        
        # Validate step limits
        if policy.max_steps <= 0:
            errors.append("max_steps must be positive")
        elif policy.max_steps > 1000:
            warnings.append("max_steps is very high (>1000)")
        
        # Validate parallel steps
        if policy.max_parallel_steps <= 0:
            errors.append("max_parallel_steps must be positive")
        elif policy.max_parallel_steps > policy.max_steps:
            warnings.append("max_parallel_steps exceeds max_steps")
        
        # Validate retry attempts
        if policy.retry_attempts < 0:
            errors.append("retry_attempts cannot be negative")
        elif policy.retry_attempts > 10:
            warnings.append("retry_attempts is very high (>10)")
        
        # Validate security level
        valid_security_levels = ["basic", "standard", "high", "critical"]
        if policy.security_level not in valid_security_levels:
            errors.append(f"security_level must be one of: {valid_security_levels}")
        
        # Validate audit level
        valid_audit_levels = ["none", "basic", "standard", "detailed", "comprehensive"]
        if policy.audit_level not in valid_audit_levels:
            errors.append(f"audit_level must be one of: {valid_audit_levels}")
        
        return {"errors": errors, "warnings": warnings}
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies"""
        
        summary = {
            "total_policies": len(self.policies),
            "policy_names": list(self.policies.keys()),
            "policy_stats": {}
        }
        
        # Collect statistics
        security_levels = {}
        audit_levels = {}
        
        for name, policy in self.policies.items():
            security_levels[policy.security_level] = security_levels.get(policy.security_level, 0) + 1
            audit_levels[policy.audit_level] = audit_levels.get(policy.audit_level, 0) + 1
        
        summary["policy_stats"] = {
            "security_levels": security_levels,
            "audit_levels": audit_levels
        }
        
        return summary


def create_default_policies() -> Dict[str, WorkflowPolicy]:
    """Create standard set of default policies"""
    
    manager = PolicyManager()
    return manager.default_policies


def create_enterprise_policies() -> Dict[str, WorkflowPolicy]:
    """Create enterprise-grade policy set"""
    
    manager = PolicyManager()
    
    # Add enterprise-specific policies
    enterprise_policies = {
        "enterprise_security": SecurityPolicy(
            max_execution_time=timedelta(minutes=10),
            max_steps=20,
            max_parallel_steps=2,
            retry_attempts=1,
            encryption_required=True,
            access_logging=True,
            user_authentication=True,
            role_based_access=True,
            data_classification_check=True
        ),
        
        "enterprise_compliance": CompliancePolicy(
            max_execution_time=timedelta(minutes=15),
            max_steps=30,
            max_parallel_steps=3,
            retry_attempts=2,
            regulatory_framework="SOX",
            data_retention_days=2555,
            audit_trail_required=True,
            data_residency_required=True,
            approval_workflow=True
        ),
        
        "enterprise_critical": manager.create_composite_policy(
            "enterprise_critical",
            ["security", "compliance"],
            overrides={
                "max_execution_time": timedelta(minutes=5),
                "max_steps": 10,
                "retry_attempts": 1,
                "require_approval": True
            }
        )
    }
    
    all_policies = manager.default_policies.copy()
    all_policies.update(enterprise_policies)
    
    return all_policies


# Global policy manager instance
_policy_manager = None


def get_policy_manager() -> PolicyManager:
    """Get global policy manager instance"""
    
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = PolicyManager()
    
    return _policy_manager
