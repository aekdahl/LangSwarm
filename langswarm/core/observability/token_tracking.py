"""
LangSwarm V2 Token Tracking System

Comprehensive token usage and context size tracking system that integrates
with the V2 middleware pipeline and observability system.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .interfaces import IMetrics, MetricType
from ..middleware.interfaces import IRequestContext, IResponseContext
from ..agents.interfaces import IAgentSession, IAgentResponse, AgentUsage

logger = logging.getLogger(__name__)


class TokenEventType(Enum):
    """Types of token usage events"""
    CHAT = "chat"
    TOOL_CALL = "tool_call" 
    FUNCTION_CALL = "function_call"
    STREAM = "stream"
    CONTEXT_COMPRESSION = "context_compression"


class CompressionUrgency(Enum):
    """Context compression urgency levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TokenUsageEvent:
    """Token usage event for comprehensive tracking"""
    # Identifiers
    event_id: str = field(default_factory=lambda: f"token_{int(time.time() * 1000)}")
    session_id: str = ""
    agent_id: str = ""
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Model and provider info
    model: str = ""
    provider: str = ""
    
    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Context information
    context_size: int = 0
    max_context_size: int = 0
    context_utilization: float = 0.0
    messages_count: int = 0
    
    # Cost and performance
    cost_estimate: float = 0.0
    processing_time_ms: float = 0.0
    tokens_per_second: float = 0.0
    
    # Event metadata
    event_type: TokenEventType = TokenEventType.CHAT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived fields"""
        if self.max_context_size > 0:
            self.context_utilization = self.context_size / self.max_context_size
        
        if self.processing_time_ms > 0 and self.total_tokens > 0:
            self.tokens_per_second = (self.total_tokens / self.processing_time_ms) * 1000


@dataclass
class ContextSizeInfo:
    """Detailed context size information"""
    current_size: int
    max_size: int
    utilization_percent: float
    messages_count: int
    
    # Compression recommendations
    compression_recommended: bool = False
    compression_urgency: CompressionUrgency = CompressionUrgency.NONE
    recommended_target_size: Optional[int] = None
    compression_strategy: Optional[str] = None
    
    # Efficiency metrics
    tokens_per_message: float = 0.0
    context_efficiency: float = 0.0  # How well context is utilized
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.messages_count > 0:
            self.tokens_per_message = self.current_size / self.messages_count
        
        if self.max_size > 0:
            self.context_efficiency = self.current_size / self.max_size
            
        # Determine compression recommendations
        if self.utilization_percent >= 95:
            self.compression_urgency = CompressionUrgency.CRITICAL
            self.compression_recommended = True
            self.recommended_target_size = int(self.max_size * 0.7)
        elif self.utilization_percent >= 85:
            self.compression_urgency = CompressionUrgency.HIGH
            self.compression_recommended = True
            self.recommended_target_size = int(self.max_size * 0.75)
        elif self.utilization_percent >= 75:
            self.compression_urgency = CompressionUrgency.MEDIUM
            self.compression_recommended = True
            self.recommended_target_size = int(self.max_size * 0.8)
        elif self.utilization_percent >= 65:
            self.compression_urgency = CompressionUrgency.LOW
            self.recommended_target_size = int(self.max_size * 0.85)


@dataclass
class TokenBudgetConfig:
    """Token budget configuration"""
    # Limits
    daily_token_limit: Optional[int] = None
    session_token_limit: Optional[int] = None
    hourly_token_limit: Optional[int] = None
    cost_limit_usd: Optional[float] = None
    
    # Alert thresholds (0.0-1.0)
    token_alert_threshold: float = 0.8
    cost_alert_threshold: float = 0.8
    context_alert_threshold: float = 0.9
    
    # Enforcement
    enforce_limits: bool = True
    auto_compress_context: bool = True
    compression_threshold: float = 0.85


@dataclass
class BudgetCheckResult:
    """Result of budget limit check"""
    within_limit: bool
    reason: Optional[str] = None
    current_usage: Dict[str, Any] = field(default_factory=dict)
    limit_details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class TokenUsageAggregator:
    """Aggregates and analyzes token usage across sessions and time"""
    
    def __init__(self, metrics: Optional[IMetrics] = None):
        """
        Initialize token usage aggregator.
        
        Args:
            metrics: Metrics system for recording aggregated data
        """
        self.metrics = metrics
        self._usage_events: List[TokenUsageEvent] = []
        self._session_totals: Dict[str, Dict[str, Any]] = {}
        self._user_totals: Dict[str, Dict[str, Any]] = {}
        
        # Cleanup old events periodically
        self._last_cleanup = datetime.utcnow()
        self._retention_days = 30
    
    async def record_usage(self, event: TokenUsageEvent) -> None:
        """Record a token usage event"""
        try:
            # Store event
            self._usage_events.append(event)
            
            # Update session totals
            await self._update_session_totals(event)
            
            # Update user totals
            if event.user_id:
                await self._update_user_totals(event)
            
            # Record metrics
            if self.metrics:
                await self._record_metrics(event)
            
            # Periodic cleanup
            await self._periodic_cleanup()
            
        except Exception as e:
            logger.error(f"Error recording token usage: {e}")
    
    async def _update_session_totals(self, event: TokenUsageEvent) -> None:
        """Update session-level totals"""
        if event.session_id not in self._session_totals:
            self._session_totals[event.session_id] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "event_count": 0,
                "first_event": event.timestamp,
                "last_event": event.timestamp,
                "models_used": set(),
                "providers_used": set()
            }
        
        totals = self._session_totals[event.session_id]
        totals["total_tokens"] += event.total_tokens
        totals["input_tokens"] += event.input_tokens
        totals["output_tokens"] += event.output_tokens
        totals["total_cost"] += event.cost_estimate
        totals["event_count"] += 1
        totals["last_event"] = event.timestamp
        totals["models_used"].add(event.model)
        totals["providers_used"].add(event.provider)
    
    async def _update_user_totals(self, event: TokenUsageEvent) -> None:
        """Update user-level totals"""
        if event.user_id not in self._user_totals:
            self._user_totals[event.user_id] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "session_count": 0,
                "event_count": 0,
                "first_event": event.timestamp,
                "last_event": event.timestamp,
                "daily_usage": {},
                "models_used": set(),
                "providers_used": set()
            }
        
        totals = self._user_totals[event.user_id]
        totals["total_tokens"] += event.total_tokens
        totals["input_tokens"] += event.input_tokens
        totals["output_tokens"] += event.output_tokens
        totals["total_cost"] += event.cost_estimate
        totals["event_count"] += 1
        totals["last_event"] = event.timestamp
        totals["models_used"].add(event.model)
        totals["providers_used"].add(event.provider)
        
        # Daily usage tracking
        day_key = event.timestamp.strftime("%Y-%m-%d")
        if day_key not in totals["daily_usage"]:
            totals["daily_usage"][day_key] = {
                "tokens": 0,
                "cost": 0.0,
                "events": 0
            }
        
        daily = totals["daily_usage"][day_key]
        daily["tokens"] += event.total_tokens
        daily["cost"] += event.cost_estimate
        daily["events"] += 1
    
    async def _record_metrics(self, event: TokenUsageEvent) -> None:
        """Record metrics for the token usage event"""
        tags = {
            "provider": event.provider,
            "model": event.model,
            "event_type": event.event_type.value
        }
        
        # Token metrics
        self.metrics.increment_counter("tokens.input", event.input_tokens, **tags)
        self.metrics.increment_counter("tokens.output", event.output_tokens, **tags)
        self.metrics.increment_counter("tokens.total", event.total_tokens, **tags)
        
        # Cost metrics
        if event.cost_estimate > 0:
            self.metrics.increment_counter("tokens.cost", event.cost_estimate, **tags)
            cost_per_token = event.cost_estimate / event.total_tokens if event.total_tokens > 0 else 0
            self.metrics.set_gauge("tokens.cost_per_token", cost_per_token, **tags)
        
        # Performance metrics
        if event.tokens_per_second > 0:
            self.metrics.set_gauge("tokens.rate", event.tokens_per_second, **tags)
        
        # Context metrics
        if event.max_context_size > 0:
            self.metrics.set_gauge("context.utilization", event.context_utilization, **tags)
            self.metrics.set_gauge("context.size", event.context_size, **tags)
    
    async def _periodic_cleanup(self) -> None:
        """Clean up old events periodically"""
        now = datetime.utcnow()
        if (now - self._last_cleanup).days >= 1:  # Daily cleanup
            cutoff = now - timedelta(days=self._retention_days)
            self._usage_events = [e for e in self._usage_events if e.timestamp > cutoff]
            self._last_cleanup = now
    
    async def get_session_usage(self, session_id: str) -> Dict[str, Any]:
        """Get usage totals for a session"""
        return self._session_totals.get(session_id, {})
    
    async def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get usage totals for a user"""
        return self._user_totals.get(user_id, {})
    
    async def get_usage_analytics(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        time_range: Optional[tuple] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        
        # Filter events
        filtered_events = self._usage_events
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        if session_id:
            filtered_events = [e for e in filtered_events if e.session_id == session_id]
        
        if time_range:
            start_time, end_time = time_range
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            filtered_events = [
                e for e in filtered_events
                if start_time <= e.timestamp <= end_time
            ]
        
        if not filtered_events:
            return {}
        
        # Calculate analytics
        total_tokens = sum(e.total_tokens for e in filtered_events)
        total_cost = sum(e.cost_estimate for e in filtered_events)
        total_events = len(filtered_events)
        
        # Group by analysis
        grouped_data = {}
        if group_by == "model":
            grouped_data = self._group_by_model(filtered_events)
        elif group_by == "provider":
            grouped_data = self._group_by_provider(filtered_events)
        elif group_by == "day":
            grouped_data = self._group_by_day(filtered_events)
        
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_events": total_events,
            "avg_tokens_per_event": total_tokens / total_events if total_events > 0 else 0,
            "avg_cost_per_event": total_cost / total_events if total_events > 0 else 0,
            "cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
            "time_range": {
                "start": min(e.timestamp for e in filtered_events),
                "end": max(e.timestamp for e in filtered_events)
            },
            "models_used": list(set(e.model for e in filtered_events)),
            "providers_used": list(set(e.provider for e in filtered_events)),
            "grouped_data": grouped_data
        }
    
    def _group_by_model(self, events: List[TokenUsageEvent]) -> Dict[str, Any]:
        """Group analytics by model"""
        model_data = {}
        for event in events:
            if event.model not in model_data:
                model_data[event.model] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "events": 0
                }
            
            model_data[event.model]["tokens"] += event.total_tokens
            model_data[event.model]["cost"] += event.cost_estimate
            model_data[event.model]["events"] += 1
        
        return model_data
    
    def _group_by_provider(self, events: List[TokenUsageEvent]) -> Dict[str, Any]:
        """Group analytics by provider"""
        provider_data = {}
        for event in events:
            if event.provider not in provider_data:
                provider_data[event.provider] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "events": 0
                }
            
            provider_data[event.provider]["tokens"] += event.total_tokens
            provider_data[event.provider]["cost"] += event.cost_estimate
            provider_data[event.provider]["events"] += 1
        
        return provider_data
    
    def _group_by_day(self, events: List[TokenUsageEvent]) -> Dict[str, Any]:
        """Group analytics by day"""
        daily_data = {}
        for event in events:
            day_key = event.timestamp.strftime("%Y-%m-%d")
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "events": 0
                }
            
            daily_data[day_key]["tokens"] += event.total_tokens
            daily_data[day_key]["cost"] += event.cost_estimate
            daily_data[day_key]["events"] += 1
        
        return daily_data


class ContextSizeMonitor:
    """Monitor conversation context sizes and provide optimization recommendations"""
    
    def __init__(self):
        """Initialize context size monitor"""
        # Model context limits (tokens)
        self._model_limits = {
            # OpenAI models
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-vision-preview": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "o1-preview": 128000,
            "o1-mini": 128000,
            
            # Anthropic models
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
            "claude-3-5-sonnet": 200000,
            
            # Default
            "default": 4096
        }
    
    async def calculate_context_info(
        self,
        session: IAgentSession,
        model: str,
        additional_tokens: int = 0
    ) -> ContextSizeInfo:
        """
        Calculate comprehensive context size information.
        
        Args:
            session: Agent session with conversation history
            model: Model name for context limit lookup
            additional_tokens: Additional tokens to be added (e.g., for next message)
        """
        try:
            # Get context messages
            messages = await session.get_context()
            
            # Calculate current context size
            current_size = await self._calculate_message_tokens(messages)
            current_size += additional_tokens
            
            # Get model limit
            max_size = self._model_limits.get(model, self._model_limits["default"])
            
            # Calculate utilization
            utilization_percent = (current_size / max_size) * 100 if max_size > 0 else 0
            
            # Create context info
            context_info = ContextSizeInfo(
                current_size=current_size,
                max_size=max_size,
                utilization_percent=utilization_percent,
                messages_count=len(messages)
            )
            
            # Add compression strategy
            if context_info.compression_recommended:
                context_info.compression_strategy = await self._get_compression_strategy(
                    context_info, messages
                )
            
            return context_info
            
        except Exception as e:
            logger.error(f"Error calculating context info: {e}")
            # Return safe defaults
            return ContextSizeInfo(
                current_size=0,
                max_size=self._model_limits.get(model, 4096),
                utilization_percent=0.0,
                messages_count=0
            )
    
    async def _calculate_message_tokens(self, messages: List[Any]) -> int:
        """
        Calculate approximate token count for messages.
        
        This is a simplified calculation. For production use, you might want
        to use model-specific tokenizers for accuracy.
        """
        total_tokens = 0
        
        for message in messages:
            # Simple approximation: 1 token ~= 4 characters
            content = getattr(message, 'content', str(message))
            total_tokens += len(content) // 4
            
            # Add overhead for message structure
            total_tokens += 10  # Message overhead
        
        return total_tokens
    
    async def _get_compression_strategy(
        self,
        context_info: ContextSizeInfo,
        messages: List[Any]
    ) -> str:
        """Get recommended compression strategy based on context"""
        
        if context_info.compression_urgency == CompressionUrgency.CRITICAL:
            return "aggressive_summarization"
        elif context_info.compression_urgency == CompressionUrgency.HIGH:
            return "smart_truncation"
        elif context_info.compression_urgency == CompressionUrgency.MEDIUM:
            return "message_pruning"
        else:
            return "sliding_window"
    
    async def should_compress_context(self, context_info: ContextSizeInfo) -> bool:
        """Determine if context compression is needed"""
        return context_info.compression_recommended
    
    async def get_compression_recommendation(
        self,
        context_info: ContextSizeInfo
    ) -> Dict[str, Any]:
        """Get detailed compression recommendation"""
        
        if not context_info.compression_recommended:
            return {"compress": False, "reason": "No compression needed"}
        
        return {
            "compress": True,
            "urgency": context_info.compression_urgency.value,
            "current_size": context_info.current_size,
            "target_size": context_info.recommended_target_size,
            "strategy": context_info.compression_strategy,
            "reduction_needed": context_info.current_size - (context_info.recommended_target_size or 0),
            "reason": f"Context utilization at {context_info.utilization_percent:.1f}%"
        }


class TokenBudgetManager:
    """Manage token budgets and enforce usage limits"""
    
    def __init__(self, aggregator: TokenUsageAggregator):
        """
        Initialize budget manager.
        
        Args:
            aggregator: Token usage aggregator for getting current usage
        """
        self.aggregator = aggregator
        self._user_budgets: Dict[str, TokenBudgetConfig] = {}
        self._budget_alerts_sent: Dict[str, datetime] = {}
    
    async def set_budget(
        self,
        user_id: str,
        budget_config: TokenBudgetConfig
    ) -> None:
        """Set budget configuration for a user"""
        self._user_budgets[user_id] = budget_config
    
    async def check_budget_limit(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        projected_tokens: int = 0,
        projected_cost: float = 0.0
    ) -> BudgetCheckResult:
        """
        Check if operation is within budget limits.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            projected_tokens: Tokens expected to be used
            projected_cost: Cost expected to be incurred
        """
        
        budget_config = self._user_budgets.get(user_id)
        if not budget_config:
            # No budget set - allow operation
            return BudgetCheckResult(within_limit=True)
        
        # Get current usage
        user_usage = await self.aggregator.get_user_usage(user_id)
        if session_id:
            session_usage = await self.aggregator.get_session_usage(session_id)
        else:
            session_usage = {}
        
        # Check daily limit
        if budget_config.daily_token_limit:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_usage = user_usage.get("daily_usage", {}).get(today, {})
            daily_tokens = daily_usage.get("tokens", 0) + projected_tokens
            
            if daily_tokens > budget_config.daily_token_limit:
                return BudgetCheckResult(
                    within_limit=False,
                    reason=f"Daily token limit exceeded ({daily_tokens} > {budget_config.daily_token_limit})",
                    current_usage={"daily_tokens": daily_tokens},
                    limit_details={"daily_limit": budget_config.daily_token_limit}
                )
        
        # Check session limit
        if budget_config.session_token_limit and session_id:
            session_tokens = session_usage.get("total_tokens", 0) + projected_tokens
            
            if session_tokens > budget_config.session_token_limit:
                return BudgetCheckResult(
                    within_limit=False,
                    reason=f"Session token limit exceeded ({session_tokens} > {budget_config.session_token_limit})",
                    current_usage={"session_tokens": session_tokens},
                    limit_details={"session_limit": budget_config.session_token_limit}
                )
        
        # Check cost limit
        if budget_config.cost_limit_usd:
            total_cost = user_usage.get("total_cost", 0.0) + projected_cost
            
            if total_cost > budget_config.cost_limit_usd:
                return BudgetCheckResult(
                    within_limit=False,
                    reason=f"Cost limit exceeded (${total_cost:.2f} > ${budget_config.cost_limit_usd:.2f})",
                    current_usage={"total_cost": total_cost},
                    limit_details={"cost_limit": budget_config.cost_limit_usd}
                )
        
        # Check alert thresholds
        recommendations = []
        if budget_config.daily_token_limit:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_usage = user_usage.get("daily_usage", {}).get(today, {})
            daily_tokens = daily_usage.get("tokens", 0)
            daily_utilization = daily_tokens / budget_config.daily_token_limit
            
            if daily_utilization > budget_config.token_alert_threshold:
                recommendations.append(f"Daily token usage at {daily_utilization*100:.1f}% of limit")
        
        return BudgetCheckResult(
            within_limit=True,
            current_usage={
                "daily_tokens": user_usage.get("daily_usage", {}).get(
                    datetime.utcnow().strftime("%Y-%m-%d"), {}
                ).get("tokens", 0),
                "total_cost": user_usage.get("total_cost", 0.0),
                "session_tokens": session_usage.get("total_tokens", 0) if session_id else 0
            },
            limit_details={
                "daily_limit": budget_config.daily_token_limit,
                "session_limit": budget_config.session_token_limit,
                "cost_limit": budget_config.cost_limit_usd
            },
            recommendations=recommendations
        )
    
    async def enforce_token_limit(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        projected_tokens: int = 0,
        projected_cost: float = 0.0
    ) -> bool:
        """
        Enforce token usage limits.
        
        Returns:
            True if operation should be allowed, False if blocked
        """
        budget_config = self._user_budgets.get(user_id)
        if not budget_config or not budget_config.enforce_limits:
            return True
        
        budget_check = await self.check_budget_limit(
            user_id, session_id, projected_tokens, projected_cost
        )
        
        return budget_check.within_limit
    
    async def get_budget_status(self, user_id: str) -> Dict[str, Any]:
        """Get current budget status for a user"""
        budget_config = self._user_budgets.get(user_id)
        if not budget_config:
            return {"has_budget": False}
        
        user_usage = await self.aggregator.get_user_usage(user_id)
        
        # Calculate utilization percentages
        status = {
            "has_budget": True,
            "config": {
                "daily_token_limit": budget_config.daily_token_limit,
                "session_token_limit": budget_config.session_token_limit,
                "cost_limit_usd": budget_config.cost_limit_usd
            },
            "utilization": {}
        }
        
        if budget_config.daily_token_limit:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_usage = user_usage.get("daily_usage", {}).get(today, {})
            daily_tokens = daily_usage.get("tokens", 0)
            status["utilization"]["daily_tokens"] = {
                "used": daily_tokens,
                "limit": budget_config.daily_token_limit,
                "percentage": (daily_tokens / budget_config.daily_token_limit) * 100
            }
        
        if budget_config.cost_limit_usd:
            total_cost = user_usage.get("total_cost", 0.0)
            status["utilization"]["cost"] = {
                "used": total_cost,
                "limit": budget_config.cost_limit_usd,
                "percentage": (total_cost / budget_config.cost_limit_usd) * 100
            }
        
        return status
    
    async def get_budget_recommendations(
        self,
        user_id: str,
        usage_pattern: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get budget optimization recommendations"""
        
        recommendations = []
        user_usage = await self.aggregator.get_user_usage(user_id)
        
        if not user_usage:
            return ["No usage data available for recommendations"]
        
        # Analyze usage patterns
        total_tokens = user_usage.get("total_tokens", 0)
        total_cost = user_usage.get("total_cost", 0.0)
        event_count = user_usage.get("event_count", 0)
        
        if event_count > 0:
            avg_tokens_per_event = total_tokens / event_count
            avg_cost_per_event = total_cost / event_count
            
            # High token usage per event
            if avg_tokens_per_event > 5000:
                recommendations.append(
                    f"High average token usage ({avg_tokens_per_event:.0f} tokens/request). "
                    "Consider enabling context compression."
                )
            
            # High cost per event
            if avg_cost_per_event > 0.10:
                recommendations.append(
                    f"High average cost (${avg_cost_per_event:.3f}/request). "
                    "Consider using less expensive models for simple tasks."
                )
            
            # Model recommendations
            models_used = user_usage.get("models_used", set())
            if "gpt-4" in models_used and "gpt-3.5-turbo" not in models_used:
                recommendations.append(
                    "Consider using GPT-3.5-turbo for simpler tasks to reduce costs."
                )
        
        return recommendations
