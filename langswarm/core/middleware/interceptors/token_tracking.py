"""
LangSwarm V2 Token Tracking Middleware Interceptor

Middleware interceptor that automatically tracks token usage and context sizes
for all agent interactions without breaking existing functionality.
"""

import logging
import time
from typing import Callable, Optional, Dict, Any

from ..interfaces import IRequestContext, IResponseContext, ResponseStatus
from ..context import ResponseContext
from .base import BaseInterceptor
from ...observability.token_tracking import (
    TokenUsageEvent, ContextSizeInfo, TokenEventType, TokenUsageAggregator,
    ContextSizeMonitor, TokenBudgetManager, TokenBudgetConfig
)
from ...observability import get_observability_provider
from ...agents.interfaces import IAgentResponse, AgentUsage

logger = logging.getLogger(__name__)


class TokenTrackingInterceptor(BaseInterceptor):
    """
    Middleware interceptor for comprehensive token usage tracking.
    
    This interceptor automatically captures token usage information from
    agent interactions and integrates with the observability system.
    """
    
    def __init__(
        self,
        priority: int = 450,  # Before execution, after validation
        enable_budget_enforcement: bool = False,
        enable_context_monitoring: bool = True
    ):
        """
        Initialize token tracking interceptor.
        
        Args:
            priority: Priority for interceptor ordering
            enable_budget_enforcement: Whether to enforce token budgets
            enable_context_monitoring: Whether to monitor context sizes
        """
        super().__init__(
            name="token_tracking",
            priority=priority,
            timeout_seconds=5.0  # Quick timeout for tracking operations
        )
        
        # Configuration
        self.enable_budget_enforcement = enable_budget_enforcement
        self.enable_context_monitoring = enable_context_monitoring
        
        # Initialize tracking components
        observability = get_observability_provider()
        metrics = observability.metrics if observability else None
        
        self.aggregator = TokenUsageAggregator(metrics)
        self.context_monitor = ContextSizeMonitor()
        self.budget_manager = TokenBudgetManager(self.aggregator) if enable_budget_enforcement else None
        
        # Tracking statistics
        self._events_tracked = 0
        self._budgets_enforced = 0
        self._contexts_monitored = 0
    
    async def _process(
        self,
        context: IRequestContext,
        next_interceptor: Callable[[IRequestContext], IResponseContext]
    ) -> IResponseContext:
        """
        Process request with token tracking.
        
        1. Pre-execution: Check budgets and calculate context size
        2. Execute: Run next interceptor
        3. Post-execution: Extract and track token usage
        """
        
        # Extract request information
        request_info = await self._extract_request_info(context)
        
        # Pre-execution: Budget enforcement
        if self.budget_manager and request_info.get("user_id"):
            budget_allowed = await self._check_budget_limits(request_info, context)
            if not budget_allowed:
                return self._create_budget_exceeded_response(context)
        
        # Pre-execution: Context monitoring
        pre_context_info = None
        if self.enable_context_monitoring:
            pre_context_info = await self._calculate_pre_context_size(request_info, context)
        
        # Execute next interceptor
        start_time = time.time()
        response = await next_interceptor(context)
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Post-execution: Track token usage (only for successful responses)
        if response.is_success():
            try:
                await self._track_token_usage(
                    request_info, response, pre_context_info, execution_time
                )
            except Exception as e:
                logger.warning(f"Failed to track token usage: {e}")
                # Don't fail the response due to tracking errors
        
        return response
    
    async def _extract_request_info(self, context: IRequestContext) -> Dict[str, Any]:
        """Extract relevant information from request context"""
        
        # Get basic request info
        request_info = {
            "request_id": context.request_id,
            "action_id": context.action_id,
            "method": context.method,
            "params": context.params or {},
            "metadata": context.metadata or {}
        }
        
        # Extract agent and session information
        request_info.update({
            "agent_id": context.metadata.get("agent_id"),
            "agent_name": context.metadata.get("agent_name"),
            "session_id": context.metadata.get("session_id"),
            "user_id": context.metadata.get("user_id"),
            "provider": context.metadata.get("provider"),
            "model": context.metadata.get("model")
        })
        
        # Determine event type
        if "tool" in context.action_id.lower():
            request_info["event_type"] = TokenEventType.TOOL_CALL
        elif "function" in context.action_id.lower():
            request_info["event_type"] = TokenEventType.FUNCTION_CALL
        elif "stream" in context.action_id.lower():
            request_info["event_type"] = TokenEventType.STREAM
        else:
            request_info["event_type"] = TokenEventType.CHAT
        
        return request_info
    
    async def _check_budget_limits(
        self,
        request_info: Dict[str, Any],
        context: IRequestContext
    ) -> bool:
        """Check if request is within budget limits"""
        
        if not self.budget_manager:
            return True
        
        user_id = request_info.get("user_id")
        if not user_id:
            return True  # No user ID means no budget enforcement
        
        session_id = request_info.get("session_id")
        
        # Estimate tokens for the request (rough approximation)
        estimated_tokens = await self._estimate_request_tokens(context)
        
        try:
            # Check budget limits
            allowed = await self.budget_manager.enforce_token_limit(
                user_id=user_id,
                session_id=session_id,
                projected_tokens=estimated_tokens
            )
            
            if allowed:
                return True
            else:
                self._budgets_enforced += 1
                logger.info(f"Token budget exceeded for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking budget limits: {e}")
            # Default to allowing the request if budget check fails
            return True
    
    async def _estimate_request_tokens(self, context: IRequestContext) -> int:
        """Estimate tokens needed for the request"""
        
        # Simple estimation based on message content
        params = context.params or {}
        message = params.get("message", "")
        
        if isinstance(message, str):
            # Rough approximation: 1 token ~= 4 characters
            return len(message) // 4 + 50  # Add overhead for response
        
        return 100  # Default estimate
    
    async def _calculate_pre_context_size(
        self,
        request_info: Dict[str, Any],
        context: IRequestContext
    ) -> Optional[ContextSizeInfo]:
        """Calculate context size before request execution"""
        
        if not self.enable_context_monitoring:
            return None
        
        try:
            # Try to get session from request context
            session_id = request_info.get("session_id")
            model = request_info.get("model", "default")
            
            if not session_id:
                return None
            
            # Get session from agent system (this would need to be implemented)
            session = await self._get_session_from_context(session_id, context)
            if not session:
                return None
            
            # Calculate context info
            additional_tokens = await self._estimate_request_tokens(context)
            context_info = await self.context_monitor.calculate_context_info(
                session, model, additional_tokens
            )
            
            self._contexts_monitored += 1
            return context_info
            
        except Exception as e:
            logger.warning(f"Failed to calculate context size: {e}")
            return None
    
    async def _get_session_from_context(
        self,
        session_id: str,
        context: IRequestContext
    ) -> Optional[Any]:
        """Get session object from context (implementation needed)"""
        
        # This would need to be implemented based on how sessions are managed
        # in the specific LangSwarm v2 deployment. For now, return None
        # which will disable context monitoring for this request.
        
        # Example implementation might look like:
        # from langswarm.core.agents import get_agent
        # agent_id = context.metadata.get("agent_id")
        # if agent_id:
        #     agent = await get_agent(agent_id)
        #     return await agent.get_session(session_id)
        
        return None
    
    async def _track_token_usage(
        self,
        request_info: Dict[str, Any],
        response: IResponseContext,
        pre_context_info: Optional[ContextSizeInfo],
        execution_time: float
    ) -> None:
        """Track token usage from the response"""
        
        try:
            # Extract token usage from response
            token_usage = await self._extract_token_usage_from_response(response)
            
            if not token_usage:
                return  # No token usage information available
            
            # Create token usage event
            event = TokenUsageEvent(
                # Identifiers
                session_id=request_info.get("session_id", ""),
                agent_id=request_info.get("agent_id", ""),
                user_id=request_info.get("user_id"),
                request_id=request_info.get("request_id"),
                
                # Model and provider
                model=request_info.get("model", ""),
                provider=request_info.get("provider", ""),
                
                # Token usage
                input_tokens=token_usage.get("input_tokens", 0),
                output_tokens=token_usage.get("output_tokens", 0),
                total_tokens=token_usage.get("total_tokens", 0),
                
                # Context information
                context_size=pre_context_info.current_size if pre_context_info else 0,
                max_context_size=pre_context_info.max_size if pre_context_info else 0,
                context_utilization=pre_context_info.utilization_percent / 100.0 if pre_context_info else 0.0,
                messages_count=pre_context_info.messages_count if pre_context_info else 0,
                
                # Cost and performance
                cost_estimate=token_usage.get("cost_estimate", 0.0),
                processing_time_ms=execution_time,
                
                # Event metadata
                event_type=request_info.get("event_type", TokenEventType.CHAT),
                metadata={
                    "action_id": request_info.get("action_id"),
                    "method": request_info.get("method"),
                    "response_status": response.status.value,
                    "context_compression_recommended": pre_context_info.compression_recommended if pre_context_info else False
                }
            )
            
            # Record the usage event
            await self.aggregator.record_usage(event)
            self._events_tracked += 1
            
            logger.debug(
                f"Tracked token usage: {event.total_tokens} tokens, "
                f"${event.cost_estimate:.4f} cost, {event.event_type.value} type"
            )
            
        except Exception as e:
            logger.error(f"Error tracking token usage: {e}")
    
    async def _extract_token_usage_from_response(
        self,
        response: IResponseContext
    ) -> Optional[Dict[str, Any]]:
        """Extract token usage information from response"""
        
        try:
            # Check if response has token usage in metadata
            if hasattr(response, 'metadata') and response.metadata:
                # Look for token usage in various formats
                token_data = (
                    response.metadata.get('token_usage') or
                    response.metadata.get('usage') or
                    response.metadata.get('tokens')
                )
                
                if token_data:
                    return self._normalize_token_data(token_data)
            
            # Check if response result has token information
            if hasattr(response, 'result') and response.result:
                result = response.result
                
                # If result is an IAgentResponse
                if hasattr(result, 'usage') and result.usage:
                    usage = result.usage
                    return {
                        "input_tokens": getattr(usage, 'prompt_tokens', getattr(usage, 'input_tokens', 0)),
                        "output_tokens": getattr(usage, 'completion_tokens', getattr(usage, 'output_tokens', 0)),
                        "total_tokens": getattr(usage, 'total_tokens', 0),
                        "cost_estimate": getattr(usage, 'cost_estimate', 0.0)
                    }
                
                # If result has metadata with usage
                if hasattr(result, 'metadata') and result.metadata:
                    token_data = result.metadata.get('token_usage')
                    if token_data:
                        return self._normalize_token_data(token_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract token usage from response: {e}")
            return None
    
    def _normalize_token_data(self, token_data: Any) -> Dict[str, Any]:
        """Normalize token data from various formats"""
        
        if isinstance(token_data, dict):
            return {
                "input_tokens": token_data.get("input_tokens") or token_data.get("prompt_tokens", 0),
                "output_tokens": token_data.get("output_tokens") or token_data.get("completion_tokens", 0),
                "total_tokens": token_data.get("total_tokens", 0),
                "cost_estimate": token_data.get("cost_estimate", 0.0)
            }
        
        elif hasattr(token_data, '__dict__'):
            # Handle objects with attributes
            return {
                "input_tokens": getattr(token_data, 'prompt_tokens', getattr(token_data, 'input_tokens', 0)),
                "output_tokens": getattr(token_data, 'completion_tokens', getattr(token_data, 'output_tokens', 0)),
                "total_tokens": getattr(token_data, 'total_tokens', 0),
                "cost_estimate": getattr(token_data, 'cost_estimate', 0.0)
            }
        
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_estimate": 0.0}
    
    def _create_budget_exceeded_response(self, context: IRequestContext) -> IResponseContext:
        """Create response for when budget limits are exceeded"""
        
        return ResponseContext(
            request_id=context.request_id,
            status=ResponseStatus.ERROR,
            result=None,
            error="Token budget limit exceeded. Please check your usage limits.",
            metadata={
                "error_type": "budget_exceeded",
                "interceptor": "token_tracking",
                "budget_enforced": True
            }
        )
    
    async def get_tracking_stats(self) -> Dict[str, Any]:
        """Get statistics about token tracking operations"""
        
        return {
            "events_tracked": self._events_tracked,
            "budgets_enforced": self._budgets_enforced,
            "contexts_monitored": self._contexts_monitored,
            "budget_enforcement_enabled": self.enable_budget_enforcement,
            "context_monitoring_enabled": self.enable_context_monitoring
        }
    
    async def configure_budget(
        self,
        user_id: str,
        budget_config: TokenBudgetConfig
    ) -> None:
        """Configure budget for a user"""
        
        if self.budget_manager:
            await self.budget_manager.set_budget(user_id, budget_config)
    
    async def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        
        return await self.aggregator.get_user_usage(user_id)
    
    async def get_session_usage(self, session_id: str) -> Dict[str, Any]:
        """Get usage statistics for a session"""
        
        return await self.aggregator.get_session_usage(session_id)


# Factory function for easy integration
def create_token_tracking_interceptor(
    enable_budget_enforcement: bool = False,
    enable_context_monitoring: bool = True,
    priority: int = 450
) -> TokenTrackingInterceptor:
    """
    Create a token tracking interceptor with specified configuration.
    
    Args:
        enable_budget_enforcement: Whether to enforce token budgets
        enable_context_monitoring: Whether to monitor context sizes
        priority: Priority for interceptor ordering
    
    Returns:
        Configured TokenTrackingInterceptor
    """
    
    return TokenTrackingInterceptor(
        priority=priority,
        enable_budget_enforcement=enable_budget_enforcement,
        enable_context_monitoring=enable_context_monitoring
    )
