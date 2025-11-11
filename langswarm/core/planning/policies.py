"""
Default Policies and Configuration for Hierarchical Planning System

Defines decision thresholds, retry policies, escalation triggers, and weights
for the controller's decision-making process.
"""

from typing import Dict, Any
from dataclasses import dataclass, field


DEFAULT_POLICIES = {
    "thresholds": {
        "integrity": 0.5,  # max data drift % before replan
        "confidence": 0.8,  # min confidence for critical steps
        "budget_buffer": 0.2  # reserve 20% budget for safety
    },
    "retry": {
        "max_attempts": 2,
        "backoff_sec": 5,
        "transient_errors": ["rate_limit", "timeout", "5xx", "503", "429"]
    },
    "escalation": {
        "s1_triggers": ["policy_violation", "destructive_op", "security_breach"],
        "s2_triggers": ["budget_overrun", "sla_breach", "integrity_critical", "consecutive_failures"],
        "s3_triggers": ["low_confidence", "tool_unavailable", "data_drift"],
        "s4_triggers": ["minor_drift", "alternate_used", "retry_success"]
    },
    "decision_weights": {
        "w_prog": 1.0,   # progress value
        "w_cost": 0.5,   # cost penalty
        "w_risk": 2.0,   # risk penalty
        "w_info": 0.3    # information gain
    },
    "limits": {
        "max_consecutive_failures": 3,
        "max_replans": 5,
        "max_execution_time_sec": 3600  # 1 hour
    }
}


@dataclass
class PolicyConfig:
    """
    Configurable policy settings for the planning system.
    
    Allows customization of decision-making policies while providing
    sensible defaults.
    """
    thresholds: Dict[str, float] = field(default_factory=lambda: DEFAULT_POLICIES["thresholds"].copy())
    retry: Dict[str, Any] = field(default_factory=lambda: DEFAULT_POLICIES["retry"].copy())
    escalation: Dict[str, Any] = field(default_factory=lambda: DEFAULT_POLICIES["escalation"].copy())
    decision_weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_POLICIES["decision_weights"].copy())
    limits: Dict[str, Any] = field(default_factory=lambda: DEFAULT_POLICIES["limits"].copy())
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "PolicyConfig":
        """Create PolicyConfig from dictionary, merging with defaults"""
        return cls(
            thresholds={**DEFAULT_POLICIES["thresholds"], **config.get("thresholds", {})},
            retry={**DEFAULT_POLICIES["retry"], **config.get("retry", {})},
            escalation={**DEFAULT_POLICIES["escalation"], **config.get("escalation", {})},
            decision_weights={**DEFAULT_POLICIES["decision_weights"], **config.get("decision_weights", {})},
            limits={**DEFAULT_POLICIES["limits"], **config.get("limits", {})}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "thresholds": self.thresholds,
            "retry": self.retry,
            "escalation": self.escalation,
            "decision_weights": self.decision_weights,
            "limits": self.limits
        }
    
    def is_transient_error(self, error_type: str) -> bool:
        """Check if error type is transient and retryable"""
        return error_type in self.retry["transient_errors"]
    
    def get_max_retries(self) -> int:
        """Get maximum retry attempts"""
        return self.retry["max_attempts"]
    
    def get_backoff_sec(self) -> float:
        """Get retry backoff in seconds"""
        return self.retry["backoff_sec"]
    
    def get_severity_for_trigger(self, trigger: str) -> str:
        """Determine escalation severity for a trigger"""
        if trigger in self.escalation["s1_triggers"]:
            return "S1"
        elif trigger in self.escalation["s2_triggers"]:
            return "S2"
        elif trigger in self.escalation["s3_triggers"]:
            return "S3"
        elif trigger in self.escalation["s4_triggers"]:
            return "S4"
        return "S3"  # Default to medium





